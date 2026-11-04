import base64
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion import vci_calendar_monthly as module


class Frame:
    def __init__(self, rows=None, source="vci", route="reference.events.calendar", columns=None):
        self.rows = rows if rows is not None else [{
            "symbol": "PVS", "event_name": "cash", "event_title": "cash 700",
            "ex_right_date": "2024-11-12T17:00:00.000Z", "record_date": "2024-11-13T17:00:00.000Z",
            "payout_date": "2024-12-16T17:00:00.000Z", "value": 700,
            "ratio": 0.07, "public_date": "2024-11-05T17:00:00.000Z", "event_type": "DIV"}]
        self.attrs = {"source": source, "route": route}
        self.columns = columns if columns is not None else sorted(module.REQUIRED_COLUMNS | {"event_type"})

    def to_json(self, **kwargs):
        return json.dumps(self.rows)


class MonthlyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = json.loads((ROOT / "configs/data/vci_calendar_monthly_v1.json").read_text(encoding="utf-8"))
        self.scope = {"canonical_sha256": module.SCOPE_SHA,
                      "securities": [{"ticker": "PVS"}] + [{"ticker": f"T{i}"} for i in range(1521)]}
        synthetic_sha = module.digest(json.dumps(self.scope["securities"], ensure_ascii=False,
                                                sort_keys=True, separators=(",", ":")).encode())
        self.pin = patch.object(module, "SCOPE_INVENTORY_SHA", synthetic_sha)
        self.pin.start()
        self.addCleanup(self.pin.stop)
        self.plan["scope_inventory_sha256"] = synthetic_sha
        self.gate = {"access_and_export_gate": "PASS", "input_sha256": module.PILOT_SHA,
                     "zip_crc_pass": True, "manifest_hashes": {str(i): True for i in range(7)}}

    def prepare(self, name="run", resume=None):
        output = self.root / name
        windows, done = module.prepare(output, self.plan, self.scope, self.gate, resume)
        return output, windows, done

    def collect(self, output, windows, done, fetch=None, **kwargs):
        return module.collect(output, fetch or (lambda **kw: Frame()), self.plan,
                              self.scope, windows, done, sleep=lambda _: None, **kwargs)

    def archive(self, output, name="state.zip"):
        target = self.root / name
        module.archive_state(output, target)
        return target

    def test_84_contiguous_nonoverlapping_months_and_clipped_first_day(self):
        windows = module.months(self.plan["start"], self.plan["end"])
        self.assertEqual(84, len(windows))
        self.assertEqual({"id": "2019-01", "start": "2019-01-31", "end": "2019-01-31"}, windows[0])
        self.assertEqual("2020-02-29", windows[13]["end"])
        self.assertEqual("2025-12-31", windows[-1]["end"])
        from datetime import date, timedelta
        for left, right in zip(windows, windows[1:]):
            self.assertEqual(date.fromisoformat(left["end"]) + timedelta(days=1), date.fromisoformat(right["start"]))

    def test_all_windows_export_without_canonical_date_or_pit_changes(self):
        output, windows, done = self.prepare()
        calls, delays = [], []
        def fetch(**kw):
            calls.append(kw)
            print("SDK should not be in progress logs")
            return Frame()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = module.collect(output, fetch, self.plan, self.scope, windows, done, sleep=delays.append)
        self.assertEqual(84, len(calls))
        self.assertEqual([8] * 84, delays)
        self.assertEqual(84, result["completed_window_count"])
        self.assertEqual(84, result["sdk_export_rows_cumulative"])
        self.assertEqual("NOT_PROMOTED", result["pit_status"])
        self.assertFalse(result["canonical_build"])
        self.assertEqual(0, result["hnx_requests"])
        self.assertEqual("NOT_INSTRUMENTED", result["underlying_http_count"])
        raw = module.read_json(output / "months/2019-01/sdk_export.json")
        self.assertEqual(Frame().rows, raw)
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("COLLECTION_EXPORTS_READY_FOR_REVIEW", result["status"])
        module.verify_state(self.archive(output))

    def test_time_budget_resume_preserves_bytes_skips_completed_and_continues_all_pending(self):
        output, windows, done = self.prepare()
        clock = iter([0, 0, 0, 2000])
        first = self.collect(output, windows, done, clock=lambda: next(clock))
        self.assertEqual("STOPPED_TIME_BUDGET", first["status"])
        self.assertEqual(["2019-01"], first["completed_windows"])
        before = {p.name: p.read_bytes() for p in (output / "months/2019-01").iterdir()}
        resumed, all_windows, completed = self.prepare("resume", self.archive(output))
        calls = []
        result = self.collect(resumed, all_windows, completed,
                              fetch=lambda **kw: (calls.append(kw) or Frame()))
        self.assertEqual(83, len(calls))
        self.assertEqual("2019-02-01", calls[0]["start"])
        self.assertEqual(84, result["completed_window_count"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in (resumed / "months/2019-01").iterdir()})
        self.assertTrue((resumed / "predecessor.json").is_file())

    def test_source_errors_stop_once_no_retry_and_resume_refused(self):
        for status in (401, 403, 429, 503):
            with self.subTest(status=status):
                output, windows, done = self.prepare(f"error{status}")
                calls = []
                def fetch(**kw):
                    calls.append(kw)
                    exc = RuntimeError("TOP_SECRET_API_KEY_123456")
                    exc.status_code = status
                    raise exc
                result = self.collect(output, windows, done, fetch, key="TOP_SECRET_API_KEY_123456")
                self.assertEqual(1, len(calls))
                self.assertFalse(result["resumable"])
                self.assertEqual(status, result["diagnostic"]["http_status"])
                self.assertEqual(84, len(result["pending_windows"]))
                archive = self.archive(output, f"error{status}.zip")
                with self.assertRaisesRegex(ValueError, "NO_AUTOMATIC_RESUME"):
                    self.prepare(f"blocked{status}", archive)
                self.assertTrue(all("TOP_SECRET_API_KEY_123456" not in p.read_text() for p in output.rglob("*") if p.is_file()))

    def test_source_route_schema_and_cap_fail_closed_retain_uncommitted_export(self):
        cases = [Frame(source="hnx"), Frame(route="unknown"), Frame(columns=["symbol"]),
                 Frame(rows=[{}]), Frame(rows=Frame().rows * 20000)]
        for index, frame in enumerate(cases):
            with self.subTest(index=index):
                output, windows, done = self.prepare(f"invalid{index}")
                calls = []
                result = self.collect(output, windows, done, lambda **kw: (calls.append(kw) or frame))
                self.assertEqual(1, len(calls))
                self.assertFalse(result["resumable"])
                self.assertEqual(0, result["completed_window_count"])
                self.assertEqual(84, result["total_windows"])
                self.assertTrue((output / "months/2019-01/sdk_export.json").exists())
                self.assertFalse((output / "months/2019-01/commit.json").exists())
                module.verify_state(self.archive(output, f"invalid{index}.zip"))

    def test_missing_dates_duplicates_outside_scope_are_retained_and_reviewed(self):
        output, windows, done = self.prepare()
        row = dict(Frame().rows[0], symbol="OUTSIDE", event_type="ISS", ex_right_date=None, record_date=None)
        result = self.collect(output, windows[:1], done, lambda **kw: Frame(rows=[row, row]))
        self.assertEqual(2, result["sdk_export_rows_cumulative"])
        review = module.read_json(output / "months/2019-01/review.json")
        self.assertEqual(2, review["outside_c8_ticker_inventory_rows"])
        self.assertEqual(1, review["exact_duplicate_excess_rows"])
        self.assertEqual(["ex_right_date", "record_date"], review["field_or_scope_review"][0]["missing_fields"])
        self.assertEqual(0, review["field_or_scope_review"][1]["duplicate_of_row_index"])
        self.assertEqual([row, row], module.read_json(output / "months/2019-01/sdk_export.json"))

    def test_empty_calendar_is_saved_without_claiming_absence_per_ticker(self):
        output, windows, done = self.prepare()
        result = self.collect(output, windows[:1], done, lambda **kw: Frame(rows=[]))
        self.assertEqual(1, result["completed_window_count"])
        review = module.read_json(output / "months/2019-01/review.json")
        self.assertFalse(review["no_events_claim_for_absent_tickers"])

    def test_cross_month_duplicates_are_reported_without_deleting_exports(self):
        output, windows, done = self.prepare()
        result = self.collect(output, windows[:2], done)
        self.assertEqual(2, result["sdk_export_rows_cumulative"])
        self.assertEqual(1, result["exact_payload_matches_across_windows"])
        review = module.read_json(output / "cross_window_review.json")
        self.assertTrue(review["all_rows_retained"])
        self.assertEqual("2019-01", review["exact_payload_matches_across_windows"][0]["same_payload_as"]["month"])

    def test_secret_in_raw_urlencoded_or_base64_export_never_written(self):
        secret = "TOP/SECRET+API_KEY_123456"
        for index, value in enumerate([secret, quote(secret, safe=""), base64.b64encode(secret.encode()).decode()]):
            output, windows, done = self.prepare(f"secret{index}")
            result = self.collect(output, windows, done, lambda **kw: Frame(rows=[dict(Frame().rows[0], event_title=value)]), key=secret)
            self.assertEqual("STOPPED_SDK_OR_EXPORT_ERROR_NO_RETRY", result["status"])
            self.assertFalse((output / "months").exists())
            for p in output.rglob("*"):
                if p.is_file():
                    self.assertNotIn(value, p.read_text())

    def test_resume_hash_tamper_and_zip_traversal_rejected(self):
        output, windows, done = self.prepare()
        self.collect(output, windows, done, clock=lambda: 0, session_seconds=1)
        archive = self.archive(output)
        with zipfile.ZipFile(archive) as z:
            files = {n: z.read(n) for n in z.namelist()}
        for name, injected in [("tamper", {"scope.json": b'{}'}), ("traversal", {"../outside": b'x'})]:
            bad = self.root / f"{name}.zip"
            with zipfile.ZipFile(bad, "x") as z:
                for n, body in (files | injected).items():
                    z.writestr(n, body)
            with self.assertRaises(ValueError):
                self.prepare(name, bad)
            self.assertFalse((self.root / name).exists())

    def test_input_policy_scope_hash_and_pilot_gate_cannot_be_relaxed(self):
        for key, value in [("interval_seconds", 0.1), ("canonical_build", True), ("scope_count", 905), ("start", "2020-01-01")]:
            plan = dict(self.plan, **{key: value})
            with self.assertRaisesRegex(ValueError, "PLAN_REQUIRES_REVIEW"):
                module.validate_inputs(plan, self.scope, self.gate)
        scope = copy.deepcopy(self.scope)
        scope["securities"][0]["ticker"] = "ALTERED"
        with self.assertRaisesRegex(ValueError, "C8_V2_SCOPE_MISMATCH"):
            module.validate_inputs(self.plan, scope, self.gate)
        with self.assertRaisesRegex(ValueError, "SUCCESSFUL_PILOT_REQUIRED"):
            module.validate_inputs(self.plan, self.scope, dict(self.gate, access_and_export_gate="PARTIAL"))

    def test_existing_output_is_never_overwritten(self):
        output, _, _ = self.prepare()
        before = (output / "plan.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(before, (output / "plan.json").read_bytes())

    def test_device_limit_and_guest_stop_before_calendar_and_redact_sdk_output(self):
        for index, guest in enumerate([False, True]):
            inputs = self.root / f"inputs{index}"
            inputs.mkdir()
            for name, value in [("plan.json", self.plan), ("scope.json", self.scope), ("pilot_gate.json", self.gate)]:
                module.write_json(inputs / name, value)
            calls = []
            class DeviceLimit(Exception):
                code = "VNSTOCK_AUTH_DEVICE_LIMIT"
                kind = "entitlement"
                retryable = False
                message_en = "Device limit exceeded"
            def login(key):
                print("TOP_SECRET_API_KEY_123456")
                if not guest:
                    raise DeviceLimit()
                return True
            sdk = SimpleNamespace(login=login, status=lambda: {"tier": "guest"}, Reference=lambda: calls.append(True))
            out = self.root / f"auth{index}"
            stdout = io.StringIO()
            with (patch.object(sys, 'argv', ['monthly', '--inputs', str(inputs), '--output', str(out)]),
                  patch.object(sys, 'stdin', io.StringIO('TOP_SECRET_API_KEY_123456')),
                  patch.dict(sys.modules, {'vnstock': sdk}),
                  patch.object(module.importlib.metadata, 'version', return_value='5.2.1'),
                  contextlib.redirect_stdout(stdout)):
                code = module.main()
            self.assertEqual(2, code)
            self.assertFalse(calls)
            self.assertNotIn('TOP_SECRET', stdout.getvalue())
            result = module.read_json(out / 'result.json')
            self.assertEqual(0, result['logical_calendar_calls_this_run'])
            self.assertFalse(result['resumable'])
            if not guest:
                self.assertEqual('VNSTOCK_AUTH_DEVICE_LIMIT', result['diagnostic']['sdk_code'])


if __name__ == "__main__":
    unittest.main()
