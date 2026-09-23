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

    def get(self, url, params, timeout, max_bytes):
        self.calls += 1
        item = self.responses[min(self.calls - 1, len(self.responses) - 1)]
        if isinstance(item, Exception):
            raise item
        status, body = item
        return RUNNER.HttpResponse(status, {}, body, f"{url}?fake={self.calls}")


RAW_BODY = json.dumps({
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
        path = RUNNER.raw_output_path(base, "FPT", datetime(2011, 9, 23).date(), datetime(2011, 12, 31).date(), 1)
        self.assertEqual(Path("X:/run/raw/FPT/2011-09-23_2011-12-31/page_0001.json"), path)
        self.assertNotIn("canonical", path.parts)


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

    def test_resume_skips_checksum_valid_completed_request(self):
        run_dir, _client = self._run_one()
        first_raw = next((run_dir / "raw").rglob("*.json"))
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

    def test_resume_rejects_plan_or_config_mismatch(self):
        run_dir, _client = self._run_one()
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["plan_hash"] = "wrong"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(RUNNER.RunnerError, "resume identity mismatch"):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                resume=True, run_id=run_dir.name, max_requests=1, only_ticker="FPT",
                client=FakeClient([(200, RAW_BODY)]), sleep=lambda _seconds: None, now=self.now,
            )

    def test_access_control_stops_safely(self):
        client = FakeClient([(403, b"Access denied")])
        with self.assertRaises(RUNNER.AccessControlStop):
            RUNNER.run_solo(
                plan_dir=PLAN_DIR, artifact_root=self.artifact_root, execute=True,
                run_id="access-stop", max_requests=1, only_ticker="FPT", client=client,
                sleep=lambda _seconds: None, now=self.now,
            )
        progress = json.loads((self.artifact_root / "access-stop/progress.json").read_text(encoding="utf-8"))
        self.assertEqual("STOPPED_ACCESS_CONTROL", progress["status"])
        self.assertEqual(1, client.calls)

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
        RUNNER._initialize_run(run_dir, PLAN_DIR, manifest, contract, self.now())
        fpt = next(row for row in rows if row["ticker"] == "FPT")
        start = datetime.fromisoformat(fpt["target_start"]).date()
        range_start, range_end = next(iter(RUNNER.iter_calendar_year_ranges(start, datetime.fromisoformat(fpt["target_end"]).date())))
        raw_path = RUNNER.raw_output_path(run_dir, "FPT", range_start, range_end, 1)
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
