import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PLANNER = _load("plan_cafef_c1_history_v3", SCRIPTS / "plan_cafef_c1_history_v3.py")
COMPACTOR = _load("compact_cafef_raw", SCRIPTS / "compact_cafef_raw.py")
V2_PLAN_DIR = ROOT / "docs/crawl/plans/cafef_c1_solo_v2"


class HistoryPolicyV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp_root = ROOT / "tmp/cafef_history_policy_v3_tests"
        shutil.rmtree(self.temp_root, ignore_errors=True)
        self.temp_root.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _make_run(self, name, *, mode="complete"):
        run_dir = self.temp_root / name
        snapshot = run_dir / "plan_snapshot"
        snapshot.mkdir(parents=True)
        security_id = "SEC-ABC"
        ticker = "ABC"
        interval_json = json.dumps([{
            "effective_from": "2012-01-01", "effective_to": None,
            "exchange": "HOSE", "ticker": ticker, "evidence_id": "TEST",
        }], separators=(",", ":"))
        columns = ["execution_order", "security_id", "ticker", "exchange", "target_start", "target_end", "identity_intervals"]
        with (snapshot / "cafef_c1_solo_execution_order.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerow({
                "execution_order": 1, "security_id": security_id, "ticker": ticker, "exchange": "HOSE",
                "target_start": "2012-01-01", "target_end": "2012-03-31", "identity_intervals": interval_json,
            })
        (snapshot / "cafef_c1_solo_contract.json").write_text(json.dumps({
            "request_surface": {"range_iteration": "NON_OVERLAPPING_CALENDAR_QUARTER_INTERSECTIONS_OLDEST_TO_NEWEST"}
        }), encoding="utf-8")
        (run_dir / "manifest.json").write_text(json.dumps({
            "contract_version": PLANNER.SOURCE_CONTRACT_VERSION
        }), encoding="utf-8")
        raw_path = run_dir / "raw/ABC/HOSE/identity_2012-01-01_OPEN/2012-01-01_2012-03-31/page_0001.json"
        raw_path.parent.mkdir(parents=True)
        body = b'{"Success":true,"Data":{"Data":[],"TotalCount":0}}'
        digest = hashlib.sha256(body).hexdigest()
        key = "SEC-ABC|ABC|HOSE|2012-01-01|OPEN|2012-01-01|2012-03-31|0001"
        entry = {
            "request_key": key, "security_id": security_id, "ticker": ticker, "exchange": "HOSE",
            "identity_interval_effective_from": "2012-01-01", "identity_interval_effective_to": None,
            "requested_start": "2012-01-01", "requested_end": "2012-03-31", "page": 1,
            "expected_pages": 1 if mode != "partial" else 2, "total_count": 0,
            "raw_path": raw_path.relative_to(run_dir).as_posix(), "sha256": digest,
        }
        completed = {}
        if mode in {"complete", "partial", "checksum_mismatch"}:
            raw_path.write_bytes(body if mode != "checksum_mismatch" else b"corrupt")
            raw_path.with_suffix(".meta.json").write_text(json.dumps(entry), encoding="utf-8")
            completed[key] = entry
        elif mode == "folder_only":
            raw_path.write_bytes(body)
        (run_dir / "progress.json").write_text(json.dumps({
            "status": "RUNNING", "request_count": len(completed), "completed": completed
        }), encoding="utf-8")
        return run_dir

    def test_base_target_uses_five_year_bound_or_later_legitimate_start(self):
        old = {"identity_intervals": '[{"effective_from":"2000-01-01","effective_to":null}]'}
        new = {"identity_intervals": '[{"effective_from":"2024-05-20","effective_to":null}]'}
        self.assertEqual(date(2021, 9, 23), PLANNER.base_target_start(old))
        self.assertEqual(date(2024, 5, 20), PLANNER.base_target_start(new))
        self.assertLessEqual((PLANNER.COLLECTION_END - PLANNER.base_target_start(old)).days, 1827)

    def test_acquisition_depth_is_not_research_eligibility(self):
        output = self.temp_root / "plan"
        result = PLANNER.build_plan(V2_PLAN_DIR, output, [], None)
        self.assertEqual(3, result["contract"]["minimum_research_history_years"])
        self.assertFalse(result["contract"]["acquisition_history_depth_is_research_eligibility"])

    def test_audit_requires_all_ranges_pages_sidecars_and_checksums(self):
        complete, _ = PLANNER.audit_v23_run(self._make_run("complete"))
        partial, _ = PLANNER.audit_v23_run(self._make_run("partial", mode="partial"))
        folder_only, _ = PLANNER.audit_v23_run(self._make_run("folder", mode="folder_only"))
        mismatch, _ = PLANNER.audit_v23_run(self._make_run("mismatch", mode="checksum_mismatch"))
        self.assertEqual("LONG_HISTORY_COMPLETE", complete[0]["audit_status"])
        self.assertEqual("PARTIAL", partial[0]["audit_status"])
        self.assertEqual("PARTIAL", folder_only[0]["audit_status"])
        self.assertEqual("PARTIAL", mismatch[0]["audit_status"])
        self.assertEqual("FAIL", mismatch[0]["raw_checksum_validation_status"])

    def test_complete_history_is_reused_but_partial_is_crawled(self):
        record = {
            "security_id": "VCI:57", "ticker": "ACB", "audit_status": "LONG_HISTORY_COMPLETE",
            "source_run_id": "cafef-c1-solo-main-v2", "source_contract_version": PLANNER.SOURCE_CONTRACT_VERSION,
            "history_start": "2011-09-23", "history_end": "2026-09-23",
            "identity_intervals": "[]", "quarter_range_count": 61, "completed_request_count": 225,
            "raw_checksum_validation_status": "PASS", "history_tier": "LONG_15Y_VALIDATION",
            "reuse_status": "ELIGIBLE_FOR_BASE5Y_REUSE",
        }
        result = PLANNER.build_plan(V2_PLAN_DIR, self.temp_root / "reuse-plan", [record], {"version": 1})
        by_ticker = {row["ticker"]: row for row in result["rows"]}
        self.assertEqual("REUSE_EXISTING_VALID_RAW", by_ticker["ACB"]["acquisition_action"])
        self.assertEqual("NO", by_ticker["ACB"]["crawl_required"])
        self.assertEqual("SATISFIED_BY_EXISTING_LONG_HISTORY", by_ticker["ACB"]["base_5y_status"])
        self.assertEqual("CRAWL_BASE_5Y", by_ticker["MBB"]["acquisition_action"])
        self.assertEqual("YES", by_ticker["MBB"]["crawl_required"])
        self.assertEqual("ACQUISITION_REQUIRED", by_ticker["MBB"]["base_5y_status"])

    def test_deep_selector_is_deterministic_order_independent_and_exchange_stratified(self):
        rows = []
        starts = ["2010-01-01", "2013-01-01", "2016-01-01"]
        for index, exchange in enumerate(["HOSE"] * 10 + ["HNX"] * 10 + ["UPCOM"] * 10):
            rows.append({
                "security_id": f"SEC-{index:02d}", "exchange": exchange,
                "pilot_role": "CORE_MARKET" if index % 2 else "METHODOLOGY_EDGE_CASE",
                "methodology_edge_case": "YES" if index % 2 == 0 else "NO",
                "legitimate_history_start": starts[index % len(starts)],
            })
        selected = PLANNER.select_deep_10y(rows)
        reversed_selected = PLANNER.select_deep_10y(list(reversed(rows)))
        self.assertEqual(selected, reversed_selected)
        selected_exchanges = {row["exchange"] for row in rows if row["security_id"] in selected}
        self.assertEqual({"HOSE", "HNX", "UPCOM"}, selected_exchanges)
        selected_starts = {row["legitimate_history_start"] for row in rows if row["security_id"] in selected}
        self.assertEqual(set(starts), selected_starts)
        too_new = [{
            "security_id": "NEW", "exchange": "HOSE", "pilot_role": "CORE_MARKET",
            "legitimate_history_start": "2024-01-01",
        }]
        self.assertEqual([], PLANNER.select_deep_10y(too_new))

    def test_compaction_is_optional_and_delete_requires_verified_archive(self):
        complete = self._make_run("compact-complete")
        packed = COMPACTOR.compact_ticker(complete, "ABC")
        self.assertTrue((packed / "cafef_raw.tar.gz").is_file())
        self.assertTrue((complete / "raw/ABC").is_dir())

        delete_run = self._make_run("compact-delete")
        COMPACTOR.compact_ticker(delete_run, "ABC")
        COMPACTOR.compact_ticker(delete_run, "ABC", delete_source=True)
        self.assertFalse((delete_run / "raw/ABC").exists())

        corrupt_run = self._make_run("compact-corrupt")
        corrupt_pack = COMPACTOR.compact_ticker(corrupt_run, "ABC")
        (corrupt_pack / "cafef_raw.tar.gz").write_bytes(b"corrupt")
        with self.assertRaises(COMPACTOR.CompactionError):
            COMPACTOR.compact_ticker(corrupt_run, "ABC", delete_source=True)
        self.assertTrue((corrupt_run / "raw/ABC").is_dir())

        partial = self._make_run("compact-partial", mode="partial")
        with self.assertRaises(COMPACTOR.CompactionError):
            COMPACTOR.compact_ticker(partial, "ABC")


if __name__ == "__main__":
    unittest.main()
