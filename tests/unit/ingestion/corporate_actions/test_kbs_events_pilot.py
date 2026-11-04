import contextlib
from decimal import Decimal
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions import kbs_pilot as k
from delta_t1.ingestion.corporate_actions.layout import inside, make_plan

SPEC = importlib.util.spec_from_file_location("kbs_ca_runner", ROOT / "scripts/corporate_actions/run_kbs_events_pilot_v1.py")
runner = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(runner)
CONFIG = json.loads(runner.CONFIG.read_text(encoding="utf-8"))


class Frame:
    def __init__(self, rows=None, columns=None, source="kbs", route="fundamental.company.events"):
        self.columns = columns if columns is not None else ["symbol", "exercise_ratio", "record_date"]
        self.dtypes = ["object"] * len(self.columns)
        self.attrs = {"source": source, "route": route}
        self.rows = rows if rows is not None else [["GSP", .5555555555555556, "2021-08-23"]]

    def itertuples(self, index=False, name=None):
        yield from (tuple(r) for r in self.rows)


def quiet(*args, **kwargs): pass


class KbsPilotTests(unittest.TestCase):
    def test_exact_six_scope_and_no_relaxed_gates(self):
        k.config_check(CONFIG)
        for key, value in [("source", "vci"), ("sdk_version", "999"), ("interval_seconds", .25),
            ("native_route", "reference.company.events"), ("max_logical_queries", 1522), ("automatic_retry", True), ("provider_fallback", True),
            ("tls_verification", False), ("canonical_build", True), ("field_approval", True), ("hnx_requests_allowed", True)]:
            with self.assertRaises(ValueError): k.config_check(dict(CONFIG, **{key: value}))

    def test_six_calls_provenance_and_sdk_float_precision_are_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            output = Path(tmp); calls = []; waits = []
            def fetch(ticker):
                calls.append(ticker)
                return Frame([[ticker, .5555555555555556, "2021-08-23"]])
            report = k.collect(output, CONFIG, fetch, sleep=waits.append, emit=quiet)
            self.assertEqual([t for t, _ in k.TARGETS], calls)
            self.assertEqual([8] * 5, waits)
            self.assertEqual("SDK_EXPORTS_READY_FOR_REVIEW", report["status"])
            exported = json.loads((output / "sdk_exports/GSP.json").read_text(encoding="utf-8"))
            self.assertEqual(.5555555555555556, exported["data"][0][1])
            self.assertFalse(report["raw_http_bytes_captured"])
            self.assertEqual("NOT_INSTRUMENTED_SDK_INTERNALS", report["underlying_http_count"])

    def test_global_access_errors_stop_without_second_ticker_or_retry(self):
        for kind in ["AuthError", "AccessDeniedError", "RateLimitedError", "NetworkError", "ChallengeRequiredError"]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
                calls = []
                def fetch(ticker):
                    calls.append(ticker); raise type(kind, (Exception,), {})("SECRET do not persist")
                r = k.collect(Path(tmp), CONFIG, fetch, sleep=quiet, emit=quiet)
                self.assertEqual(["GSP"], calls)
                self.assertEqual("STOPPED_SDK_OR_ACCESS_ERROR", r["status"])
                self.assertNotIn("SECRET", (Path(tmp) / "result.json").read_text())

    def test_ticker_input_error_is_quarantined_and_others_continue(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            def fetch(ticker):
                if ticker == "GSP": raise type("InputError", (Exception,), {})("bad symbol")
                return Frame([[ticker, .15, "2020-02-13"]])
            r = k.collect(Path(tmp), CONFIG, fetch, sleep=quiet, emit=quiet)
            self.assertEqual(6, r["logical_company_event_calls"])
            self.assertEqual("QUARANTINED_INPUT_ERROR", r["queries"][0]["status"])
            self.assertEqual("PILOT_PARTIAL_FOR_REVIEW", r["status"])

    def test_input_error_with_http_boundary_is_not_quarantined_to_continue(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            def fetch(ticker):
                exc = type("InputError", (Exception,), {})("denied"); exc.status_code = 403; raise exc
            r = k.collect(Path(tmp), CONFIG, fetch, sleep=quiet, emit=quiet)
            self.assertEqual(1, r["logical_company_event_calls"])

    def test_wrong_source_or_missing_route_stops_after_preserving_export(self):
        for frame in [Frame(source="vci"), Frame(route="wrong"), Frame(route=""), Frame(route="reference.company.events")]:
            with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
                r = k.collect(Path(tmp), CONFIG, lambda _: frame, sleep=quiet, emit=quiet)
                self.assertEqual("STOPPED_SOURCE_OR_ROUTE_MISMATCH", r["status"])
                self.assertEqual(1, r["logical_company_event_calls"])
                self.assertTrue((Path(tmp) / "sdk_exports/GSP.json").exists())

    def test_native_route_is_distinct_from_python_method_including_empty_results(self):
        export, _ = k.frame_export(Frame([]), "GSP", CONFIG)
        self.assertEqual("fundamental.company.events", export["route"])
        self.assertEqual("reference.company.events", export["requested_sdk_method"])
        self.assertEqual({"source": "kbs", "route": "fundamental.company.events"}, export["sdk_metadata"])
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            result = k.collect(Path(tmp), CONFIG, lambda _: Frame([]), sleep=quiet, emit=quiet)
            self.assertEqual(6, result["logical_company_event_calls"])
            self.assertTrue(all(q["status"] == "EMPTY_EXPORT_NOT_NO_EVENT_PROOF" for q in result["queries"]))

    def test_observed_metadata_is_preserved_without_arbitrary_attrs_or_secret_values(self):
        frame = Frame(route="reference.events.calendar")
        frame.attrs.update(api_key="SECRET", request_url="https://secret.example", access_token="SECRET")
        export, _ = k.frame_export(frame, "GSP", CONFIG)
        self.assertEqual("UNVERIFIED", export["route"])
        self.assertEqual("reference.events.calendar", export["sdk_metadata"]["route"])
        self.assertNotIn("SECRET", json.dumps(export))
        frame.attrs["route"] = "https://secret.example?token=SECRET"
        self.assertNotIn("route", k.frame_export(frame, "GSP", CONFIG)[0]["sdk_metadata"])

    def test_duplicate_columns_preserved_as_matrix_no_dict_drop(self):
        export, profile = k.frame_export(Frame([[1, 2]], ["ratio", "ratio"]), "GSP", CONFIG)
        self.assertEqual([[1, 2]], export["data"])
        self.assertTrue(export["duplicate_column_names"])
        self.assertEqual([0, 1], [p["column_position"] for p in profile])

    def test_empty_export_does_not_claim_no_event(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            r = k.collect(Path(tmp), CONFIG, lambda _: Frame([]), sleep=quiet, emit=quiet)
            self.assertTrue(all(q["status"] == "EMPTY_EXPORT_NOT_NO_EVENT_PROOF" for q in r["queries"]))

    def test_no_forward_fill_zero_or_decimal_rounding(self):
        export, profile = k.frame_export(Frame([[None, float("nan"), Decimal("0.333333333333333333")]], ["a", "b", "c"]), "GSP", CONFIG)
        self.assertEqual([None, None, {"decimal_literal": "0.333333333333333333"}], export["data"][0])
        self.assertEqual([1, 1, 0], [p["null_count"] for p in profile])

    def test_secret_is_never_written_to_an_export(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            with self.assertRaisesRegex(ValueError, "SECRET_IN_EXPORT"):
                k.write_json(Path(tmp), "x.json", {"data": "SECRET"}, "SECRET")
            self.assertFalse((Path(tmp) / "x.json").exists())

    def test_no_private_state_or_credentials_in_zip_and_all_hashes_match(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            base = Path(tmp); output = base / "state"; output.mkdir()
            (base / "private.json").write_text("SECRET")
            k.write_json(output, "result.json", {"status": "STOPPED_SETUP_ERROR"})
            archive = base / "pilot.zip"
            k.seal_and_zip(output, archive, {"status": "STOPPED_SETUP_ERROR"})
            with zipfile.ZipFile(archive) as z:
                self.assertNotIn("private.json", z.namelist())
                self.assertIsNone(z.testzip())
                manifest = json.loads(z.read("manifest.json"))
                for name, digest in manifest["files"].items(): self.assertEqual(digest, k.sha(z.read(name)))
            with self.assertRaises(FileExistsError): k.seal_and_zip(output, archive, {})

    def test_stable_auth_store_and_no_parent_env_mutation(self):
        parent = {"VNSTOCK_API_KEY": "SECRET", "KEEP": "same"}
        first = k.child_environment(parent, runner.STATE_HOME)
        self.assertNotIn("VNSTOCK_API_KEY", first)
        self.assertEqual(first, k.child_environment(parent, runner.STATE_HOME))
        self.assertEqual("SECRET", parent["VNSTOCK_API_KEY"])
        for key in ["VNSTOCK_API_BASE", "VNSTOCK_PROFILE"]:
            with self.assertRaises(ValueError): k.child_environment({key: "custom"}, runner.STATE_HOME)

    def test_arbitrary_sdk_messages_and_unhashable_codes_are_not_serialized(self):
        exc = ValueError("VNSTOCK_AUTH_CREDENTIAL_INVALID SECRET")
        result = k.safe_error(exc)
        self.assertEqual("VNSTOCK_AUTH_CREDENTIAL_INVALID", result["sdk_code"])
        self.assertNotIn("SECRET", json.dumps(result))
        exc.code = {"SECRET": "x"}
        self.assertNotIn("SECRET", json.dumps(k.safe_error(exc)))

    def test_progress_allowlist_rejects_secret_or_untyped_messages(self):
        valid = {"event": "QUERY_STARTED", "ticker": "GSP", "completed": 0, "total": 6}
        self.assertEqual(valid, runner.progress(json.dumps(valid)))
        for value in ["SECRET", json.dumps({"api_key": "SECRET"}), json.dumps(dict(valid, ticker=[])),
            json.dumps(dict(valid, status={})), json.dumps(dict(valid, completed=True)), json.dumps({"event": []})]:
            self.assertIsNone(runner.progress(value))

    def test_check_does_not_prompt_or_import_sdk(self):
        with patch.object(sys, "argv", ["pilot", "--check"]), patch.object(runner, "sdk_precheck", return_value={"sdk_version": "5.2.1", "network_requests": 0}), patch.object(runner.getpass, "getpass", side_effect=AssertionError("no prompt")), contextlib.redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(0, runner.main())
        self.assertIn("LOCAL_CHECK_PASS_AUTH_NOT_TESTED", captured.getvalue())

    def test_scope_paths_stay_under_corporate_actions(self):
        self.assertIn("data/corporate_actions/work/kbs_pilot_v1", runner.OUTPUT_ROOT.as_posix())
        self.assertIn("data/corporate_actions/private/", runner.STATE_HOME.as_posix())
        with self.assertRaises(ValueError): inside(ROOT, "../outside")
        with self.assertRaises(ValueError): inside(ROOT, "C:/outside")

    def test_worker_uses_explicit_kbs_route_and_does_not_save_login_reply(self):
        calls = []
        def login(key):
            print('SECRET login output must be suppressed')
            return {'authenticated': True, 'api_key': key, 'access_token': 'SECRET'}
        class Company:
            def __init__(self, ticker): self.ticker = ticker
            def events(self, **kwargs):
                calls.append((self.ticker, kwargs))
                return Frame([[self.ticker, .15, '2020-02-13']])
        fake_sdk = types.SimpleNamespace(login=login, Reference=lambda: types.SimpleNamespace(company=Company))
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as tmp, patch.dict(sys.modules, {'vnstock': fake_sdk}), patch.object(sys, 'stdin', io.StringIO('{"api_key":"SECRET"}')), patch.object(k.time, 'sleep', lambda _: None), contextlib.redirect_stdout(io.StringIO()) as captured:
            # collect's default sleep was bound on definition, so inject its call
            # through a wrapper rather than waiting40seconds in this unit test.
            original = runner.collect
            with patch.object(runner, 'collect', side_effect=lambda output, cfg, fetch, secret: original(output, cfg, fetch, secret=secret, sleep=quiet, emit=quiet)):
                self.assertEqual(0, runner.worker(Path(tmp), CONFIG))
            self.assertEqual(6, len(calls))
            self.assertTrue(all(kwargs == {'source': 'kbs', 'lang': 'vi'} for _, kwargs in calls))
            self.assertNotIn('SECRET', captured.getvalue())
            self.assertTrue(all('SECRET' not in p.read_text(encoding='utf-8') for p in Path(tmp).rglob('*.json')))

    def test_worker_login_failure_preserves_safe_report_without_event_calls(self):
        fake_sdk = types.SimpleNamespace(login=lambda key: {'authenticated': False})
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as tmp, patch.dict(sys.modules, {'vnstock': fake_sdk}), patch.object(sys, 'stdin', io.StringIO('{"api_key":"SECRET"}')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(2, runner.worker(Path(tmp), CONFIG))
            report = json.loads((Path(tmp) / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual('SDK_LOGIN', report['setup_stage'])
            self.assertNotIn('SECRET', json.dumps(report))


if __name__ == "__main__": unittest.main()
