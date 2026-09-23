import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/plan_cafef_c1_workers.py"
SPEC = importlib.util.spec_from_file_location("plan_cafef_c1_workers", SCRIPT)
PLANNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PLANNER
SPEC.loader.exec_module(PLANNER)


class CafeFC1PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = ROOT / "tmp" / "cafef_c1_planner_tests"
        cls.temp_root.mkdir(parents=True, exist_ok=True)

    def _output_directory(self, name):
        path = self.temp_root / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _generate(self, directory):
        return PLANNER.build_plan(ROOT, Path(directory))

    def test_plan_is_deterministic_and_partition_is_complete(self):
        first = self._output_directory("deterministic_first")
        second = self._output_directory("deterministic_second")
        first_result = self._generate(first)
        second_result = self._generate(second)
        self.assertEqual(71, first_result["manifest"]["pilot_security_count"])
        self.assertEqual(5, first_result["manifest"]["worker_count"])
        self.assertTrue(all(first_result["summary"]["checks"].values()))
        first_files = {path.name: path.read_bytes() for path in Path(first).iterdir()}
        second_files = {path.name: path.read_bytes() for path in Path(second).iterdir()}
        self.assertEqual(first_files, second_files)

    def test_selected_security_is_assigned_once_and_high_runs_first(self):
        directory = self._output_directory("assignment")
        self._generate(directory)
        selected_path = Path(directory) / "cafef_c1_selected_pilot.csv"
        with selected_path.open(encoding="utf-8", newline="") as stream:
            selected = list(csv.DictReader(stream))
        assigned = []
        for worker in PLANNER.WORKERS:
            path = Path(directory) / f"cafef_c1_{worker}_assignment.csv"
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            assigned.extend(row["security_id"] for row in rows)
            waves = [int(row["wave"]) for row in rows]
            self.assertEqual(sorted(waves), waves)
        self.assertEqual(sorted(row["security_id"] for row in selected), sorted(assigned))
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_history_and_exchange_policy(self):
        directory = self._output_directory("history")
        result = self._generate(directory)
        summary = result["summary"]
        self.assertLessEqual(summary["estimated_work_unit_max_to_min_ratio"], 1.02)
        with (Path(directory) / "cafef_c1_selected_pilot.csv").open(encoding="utf-8", newline="") as stream:
            selected = list(csv.DictReader(stream))
        self.assertEqual({"HOSE", "HNX", "UPCOM"}, {row["current_exchange"] for row in selected})
        self.assertTrue(all(row["target_start"] >= "2011-09-23" for row in selected))
        acv = next(row for row in selected if row["current_ticker"] == "ACV")
        self.assertEqual("HIGH", acv["priority_tier"])
        self.assertEqual("NONE_ACQUISITION_ORDER_ONLY", acv["research_eligibility_effect"])

    def test_contract_is_raw_only_and_records_unresolved_inputs(self):
        directory = self._output_directory("contract")
        self._generate(directory)
        contract = json.loads((Path(directory) / "cafef_c1_crawl_contract.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["raw_only"]["canonical_write"])
        self.assertEqual("VALIDATION_ONLY", contract["raw_only"]["adjust_price_role"])
        self.assertEqual("PLAN_INPUT_UNRESOLVED", contract["approved_execution_commit"])
        self.assertEqual(0, json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8"))["actual_market_data_requests"])

    def test_script_has_no_network_client_import(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("import requests", "import httpx", "import urllib", "from requests", "from httpx"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
