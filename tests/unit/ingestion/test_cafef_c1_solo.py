import csv
import importlib.util
import json
import shutil
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PLANNER = _load("plan_cafef_c1_solo", "scripts/plan_cafef_c1_solo.py")
RUNNER = _load("run_cafef_c1_solo", "scripts/run_cafef_c1_solo.py")
PLAN_DIR = ROOT / "docs/crawl/plans/cafef_c1_solo_v2"


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.requests = []

    def get(self, url, params, timeout, max_bytes):
        self.calls += 1
        self.requests.append({"url": url, "params": dict(params), "timeout": timeout, "max_bytes": max_bytes})
        item = self.responses[min(self.calls - 1, len(self.responses) - 1)]
        if isinstance(item, Exception):
            raise item
        status, body = item
        return RUNNER.HttpResponse(status, {}, body, f"{url}?fake={self.calls}")


RAW_BODY = json.dumps({
    "Success": True,
    "Data": {
        "Data": [{"Ngay": "23/09/2011", "GiaDongCua": 10.0, "GiaDieuChinh": 9.5}],
        "TotalCount": 1,
    }
}, separators=(",", ":")).encode("utf-8")


class CafeFC1SoloPlanTests(unittest.TestCase):
    def test_plan_loads_and_execution_order_is_deterministic(self):
        rows, manifest, contract, _failure, _resume = RUNNER.load_frozen_plan(PLAN_DIR)
        self.assertEqual(27, len(rows))
        self.assertEqual(list(range(1, 28)), [int(row["execution_order"]) for row in rows])
        self.assertEqual("CAFEF_C1_SOLO_PRIORITY_V2", manifest["priority_policy"])
        self.assertEqual("2026-09-23", contract["collection_end_date"])
        self.assertEqual("CAFEF_C1_SOLO_RAW_CONTRACT_V2_1", contract["contract_version"])
        self.assertTrue(all(RUNNER.identity_request_segments(row) for row in rows))

    def test_planner_outputs_are_byte_deterministic(self):
        first = ROOT / "tmp/cafef_c1_solo_deterministic_first"
        second = ROOT / "tmp/cafef_c1_solo_deterministic_second"
        shutil.rmtree(first, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)
        PLANNER.build_plan(ROOT, first)
        PLANNER.build_plan(ROOT, second)
        first_files = {path.name: path.read_bytes() for path in first.iterdir()}
        second_files = {path.name: path.read_bytes() for path in second.iterdir()}
        self.assertEqual(first_files, second_files)

    def test_history_is_at_most_fifteen_calendar_years_and_end_is_frozen(self):
        with (PLAN_DIR / "cafef_c1_solo_execution_order.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            start = datetime.fromisoformat(row["target_start"]).date()
            end = datetime.fromisoformat(row["target_end"]).date()
            self.assertEqual(datetime(2026, 9, 23).date(), end)
            self.assertGreaterEqual(start, datetime(end.year - 15, end.month, end.day).date())
            self.assertEqual("YES", row["crawl_allowed"])
        by_ticker = {row["ticker"]: row for row in rows}
        self.assertEqual("2018-07-10", by_ticker["BCM"]["target_start"])
        self.assertEqual("2018-12-06", by_ticker["CTR"]["target_start"])
        self.assertEqual("2011-09-23", by_ticker["SHB"]["target_start"])

    def test_raw_output_path_is_deterministic_and_not_canonical(self):
        base = Path("X:/run")
        path = RUNNER.raw_output_path(
            base, "FPT", "HOSE", datetime(2006, 12, 13).date(), None,
            datetime(2011, 9, 23).date(), datetime(2011, 12, 31).date(), 1,
        )
        self.assertEqual(
            Path("X:/run/raw/FPT/HOSE/identity_2006-12-13_OPEN/2011-09-23_2011-12-31/page_0001.json"),
            path,
        )
        self.assertNotIn("canonical", path.parts)

    def test_literal_exchange_type_for_all_supported_exchanges(self):
        start = datetime(2026, 1, 1).date()
        end = datetime(2026, 1, 31).date()
        for exchange in ("HOSE", "HNX", "UPCOM"):
            with self.subTest(exchange=exchange):
                params = RUNNER.build_request_params(
                    {"exchange": exchange, "ticker": "ABC"}, start, end, 1, 20
                )
                self.assertEqual(exchange, params["ExchangeType"])
                self.assertNotIn(params["ExchangeType"], {"1", "2", "3"})

    def test_transfer_identity_intervals_control_bcm_ctr_and_shb_routing(self):
        with (PLAN_DIR / "cafef_c1_solo_execution_order.csv").open(encoding="utf-8", newline="") as stream:
            by_ticker = {row["ticker"]: row for row in csv.DictReader(stream)}
        bcm = RUNNER.identity_request_segments(by_ticker["BCM"])
        self.assertEqual(
            [("UPCOM", "2018-07-10", "2020-08-30"), ("HOSE", "2020-08-31", "2026-09-23")],
            [(item["exchange"], item["request_start"].isoformat(), item["request_end"].isoformat()) for item in bcm],
        )
        ctr = RUNNER.identity_request_segments(by_ticker["CTR"])
        self.assertEqual(
            [("UPCOM", "2018-12-06", "2022-02-22"), ("HOSE", "2022-02-23", "2026-09-23")],
            [(item["exchange"], item["request_start"].isoformat(), item["request_end"].isoformat()) for item in ctr],
        )
        shb = RUNNER.identity_request_segments(by_ticker["SHB"])
        self.assertEqual(
            [("HNX", "2011-09-23", "2021-10-10"), ("HOSE", "2021-10-11", "2026-09-23")],
            [(item["exchange"], item["request_start"].isoformat(), item["request_end"].isoformat()) for item in shb],
        )

    def test_request_key_and_raw_path_include_interval_context(self):
        row = {"security_id": "SEC-1"}
        common = {
            "ticker": "ABC", "interval_effective_from": datetime(2020, 1, 1).date(),
            "interval_effective_to": datetime(2020, 12, 31).date(),
        }
        hnx = {**common, "exchange": "HNX"}
        hose = {**common, "exchange": "HOSE"}
        later_hose = {
            **hose,
            "interval_effective_from": datetime(2021, 1, 1).date(),
            "interval_effective_to": datetime(2021, 12, 31).date(),
        }
        start, end = datetime(2020, 6, 1).date(), datetime(2020, 6, 30).date()
        self.assertNotEqual(RUNNER.request_key(row, hnx, start, end, 1), RUNNER.request_key(row, hose, start, end, 1))
        self.assertNotEqual(RUNNER.request_key(row, hose, start, end, 1), RUNNER.request_key(row, later_hose, start, end, 1))
        self.assertNotEqual(
            RUNNER.raw_output_path(Path("X:/run"), "ABC", "HNX", common["interval_effective_from"], common["interval_effective_to"], start, end, 1),
            RUNNER.raw_output_path(Path("X:/run"), "ABC", "HOSE", common["interval_effective_from"], common["interval_effective_to"], start, end, 1),
        )
        self.assertNotEqual(
            RUNNER.raw_output_path(Path("X:/run"), "ABC", "HOSE", common["interval_effective_from"], common["interval_effective_to"], start, end, 1),
            RUNNER.raw_output_path(Path("X:/run"), "ABC", "HOSE", later_hose["interval_effective_from"], later_hose["interval_effective_to"], start, end, 1),
        )

    def test_empty_identity_intervals_fail_closed(self):
        row = {"ticker": "ABC", "target_start": "2020-01-01", "target_end": "2020-12-31", "identity_intervals": "[]"}
        with self.assertRaisesRegex(RUNNER.RunnerError, "no identity intervals"):
            RUNNER.identity_request_segments(row)

    def test_price_history_envelope_validation(self):
        rows, total = RUNNER._parse_envelope(RAW_BODY)
        self.assertEqual(1, len(rows))
        self.assertEqual(1, total)
        invalid_success = json.dumps({"Success": False, "Data": {"Data": [], "TotalCount": 0}}).encode()
        with self.assertRaisesRegex(RUNNER.RunnerError, "Success=true"):
            RUNNER._parse_envelope(invalid_success)
        for payload in (
            {"Success": True, "Data": {"Data": [], "TotalCount": -1}},
            {"Success": True, "Data": {"Data": [{"Ngay": "01/01/2020"}], "TotalCount": 0}},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(RUNNER.RunnerError):
                    RUNNER._parse_envelope(json.dumps(payload).encode())
        empty_rows, empty_total = RUNNER._parse_envelope(
            json.dumps({"Success": True, "Data": {"Data": [], "TotalCount": 0}}).encode()
        )
        self.assertEqual([], empty_rows)
        self.assertEqual(0, empty_total)


class CafeFC1SoloRunnerTests(unittest.TestCase):
    def setUp(self):
        self.test_root = ROOT / "tmp/cafef_c1_solo_runner_tests"
        shutil.rmtree(self.test_root, ignore_errors=True)
        self.artifact_root = self.test_root / "artifacts" / "cafef_primary"
        self.now = lambda: datetime(2026, 9, 23, 1, 2, 3, tzinfo=timezone.utc)

    def tearDown(self):
        shutil.rmtree(self.test_root, ignore_errors=True)

    def _run_one(self, run_id="test-run"):
        client = FakeClient([(200, RAW_BODY)])
        run_dir = RUNNER.run_solo(
            plan_dir=PLAN_DIR,
            artifact_root=self.artifact_root,
            execute=True,
            run_id=run_id,
            max_requests=1,
            only_ticker="FPT",
            client=client,
            sleep=lambda _seconds: None,
            now=self.now,
        )
        return run_dir, client

    def test_refuses_without_execute(self):
        with self.assertRaisesRegex(RUNNER.RunnerError, "--execute"):
            RUNNER.run_solo(plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=False)

    def test_raw_bytes_preserve_adjust_price_and_no_canonical_output(self):
        run_dir, _client = self._run_one()
        raw_files = [path for path in (run_dir / "raw").rglob("*.json") if not path.name.endswith(".meta.json")]
        self.assertEqual(1, len(raw_files))
        self.assertEqual(RAW_BODY, raw_files[0].read_bytes())
        self.assertIn(b"GiaDieuChinh", raw_files[0].read_bytes())
        self.assertFalse((run_dir / "canonical").exists())
        self.assertFalse((run_dir / "features").exists())
        entry = json.loads((run_dir / "request_log.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual("HOSE", entry["exchange"])
        self.assertEqual("HOSE", entry["request_params"]["ExchangeType"])
        self.assertEqual("2006-12-13", entry["identity_interval_effective_from"])
        self.assertIsNone(entry["identity_interval_effective_to"])

    def test_resume_skips_checksum_valid_completed_request(self):
        run_dir, _client = self._run_one()
        first_raw = next(path for path in (run_dir / "raw").rglob("*.json") if not path.name.endswith(".meta.json"))
        first_hash = RUNNER.sha256_file(first_raw)
        resumed_client = FakeClient([(200, RAW_BODY)])
        RUNNER.run_solo(
            plan_dir=PLAN_DIR,
            artifact_root=self.artifact_root,
            execute=True,
            resume=True,
            run_id=run_dir.name,
            max_requests=1,
            only_ticker="FPT",
            client=resumed_client,
            sleep=lambda _seconds: None,
            now=self.now,
        )
        self.assertEqual(1, resumed_client.calls)
        self.assertEqual(first_hash, RUNNER.sha256_file(first_raw))
        progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(progress["completed"]))

    def test_resume_rejects_corrected_contract_version_mismatch(self):
        run_dir, _client = self._run_one()
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["resume_contract_version"] = "CAFEF_C1_SOLO_RESUME_V2"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(RUNNER.RunnerError, "resume identity mismatch"):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                resume=True, run_id=run_dir.name, max_requests=1, only_ticker="FPT",
                client=FakeClient([(200, RAW_BODY)]), sleep=lambda _seconds: None, now=self.now,
            )

    def test_access_control_stops_safely(self):
        for status in (403, 429):
            with self.subTest(status=status):
                client = FakeClient([(status, b"Access denied")])
                run_id = f"access-stop-{status}"
                with self.assertRaises(RUNNER.AccessControlStop):
                    RUNNER.run_solo(
                        plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                        run_id=run_id, max_requests=1, only_ticker="FPT", client=client,
                        sleep=lambda _seconds: None, now=self.now,
                    )
                progress = json.loads((self.artifact_root / run_id / "progress.json").read_text(encoding="utf-8"))
                self.assertEqual("STOPPED_ACCESS_CONTROL", progress["status"])
                self.assertEqual(1, client.calls)

    def test_live_request_builder_sends_literal_exchange_labels(self):
        for ticker, exchange in (("FPT", "HOSE"), ("PVS", "HNX"), ("ACV", "UPCOM")):
            with self.subTest(ticker=ticker):
                client = FakeClient([(200, RAW_BODY)])
                RUNNER.run_solo(
                    plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                    run_id=f"literal-{ticker}", max_requests=1, only_ticker=ticker,
                    client=client, sleep=lambda _seconds: None, now=self.now,
                )
                self.assertEqual(exchange, client.requests[0]["params"]["ExchangeType"])

    def test_valid_empty_response_is_logged_as_unresolved(self):
        empty = json.dumps({"Success": True, "Data": {"Data": [], "TotalCount": 0}}).encode()
        client = FakeClient([(200, empty)])
        run_dir = RUNNER.run_solo(
            plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
            run_id="valid-empty", max_requests=1, only_ticker="FPT", client=client,
            sleep=lambda _seconds: None, now=self.now,
        )
        entry = json.loads((run_dir / "request_log.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual("PROVIDER_EMPTY_RESPONSE_UNRESOLVED", entry["empty_classification"])
        self.assertEqual(0, entry["expected_pages"])

    def test_invalid_success_is_not_saved_as_completed_raw(self):
        invalid = json.dumps({"Success": False, "Data": {"Data": [], "TotalCount": 0}}).encode()
        with self.assertRaisesRegex(RUNNER.RunnerError, "Success=true"):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                run_id="invalid-success", max_requests=1, only_ticker="FPT",
                client=FakeClient([(200, invalid)]), sleep=lambda _seconds: None, now=self.now,
            )
        run_dir = self.artifact_root / "invalid-success"
        self.assertFalse((run_dir / "raw").exists())
        progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
        self.assertEqual({}, progress["completed"])

    def test_positive_total_with_empty_page_fails_closed(self):
        invalid = json.dumps({"Success": True, "Data": {"Data": [], "TotalCount": 1}}).encode()
        with self.assertRaisesRegex(RUNNER.RunnerError, "empty page"):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                run_id="invalid-empty-page", max_requests=1, only_ticker="FPT",
                client=FakeClient([(200, invalid)]), sleep=lambda _seconds: None, now=self.now,
            )
        self.assertFalse((self.artifact_root / "invalid-empty-page/raw").exists())

    def test_transient_retry_is_bounded(self):
        client = FakeClient([(503, b"temporary"), (503, b"temporary")])
        with self.assertRaises(RUNNER.TransientRequestError):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                run_id="bounded-retry", max_requests=1, only_ticker="FPT", client=client,
                sleep=lambda _seconds: None, now=self.now,
            )
        self.assertEqual(2, client.calls)

    def test_duplicate_untracked_raw_is_not_overwritten(self):
        rows, manifest, contract, _failure, _resume = RUNNER.load_frozen_plan(PLAN_DIR)
        run_dir = self.artifact_root / "duplicate-raw"
        resume_contract = json.loads((PLAN_DIR / "cafef_c1_solo_resume_contract.json").read_text(encoding="utf-8"))
        RUNNER._initialize_run(run_dir, PLAN_DIR, manifest, contract, resume_contract, self.now())
        fpt = next(row for row in rows if row["ticker"] == "FPT")
        segment = RUNNER.identity_request_segments(fpt)[0]
        range_start, range_end = next(iter(RUNNER.iter_calendar_year_ranges(segment["request_start"], segment["request_end"])))
        raw_path = RUNNER.raw_output_path(
            run_dir, segment["ticker"], segment["exchange"],
            segment["interval_effective_from"], segment["interval_effective_to"],
            range_start, range_end, 1,
        )
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"existing-immutable-bytes")
        client = FakeClient([(200, RAW_BODY)])
        with self.assertRaisesRegex(RUNNER.RunnerError, "refusing to overwrite"):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                resume=True, run_id=run_dir.name, max_requests=1, only_ticker="FPT",
                client=client, sleep=lambda _seconds: None, now=self.now,
            )
        self.assertEqual(b"existing-immutable-bytes", raw_path.read_bytes())
        self.assertEqual(0, client.calls)


if __name__ == "__main__":
    unittest.main()
