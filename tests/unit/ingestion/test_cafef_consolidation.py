import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from delta_t1.ingestion.cafef_consolidation import (
    build_supplemental_plan,
    classify_acquisition,
)
from delta_t1.ingestion import cafef_expansion as c6


ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / "configs/data/cafef_supplemental_v1"


def inventory_row(index: int, status: str = "COMPLETE", action: str = "COMPLETE_RETAINED") -> dict:
    ticker = f"T{index:03d}"
    return {
        "ticker": ticker,
        "security_id": f"KBS:HOSE:{ticker}",
        "worker_id": "worker-01",
        "assignment_id": "cafef-expansion-v1-worker-01",
        "handoff_run_id": "run-01",
        "acquisition_status": status,
        "action": action,
        "next_page_if_continuable": "",
        "last_page": "",
        "initial_page_sequence_contiguous": True,
        "source_zip": "worker-01.zip",
        "source_zip_sha256": "a" * 64,
    }


class CafeFConsolidationTests(unittest.TestCase):
    def test_complete_requires_target_or_real_empty_boundary(self):
        self.assertEqual(
            ("COMPLETE", "COMPLETE_RETAINED", None),
            classify_acquisition(
                reported="COMPLETE", pages=[1, 2], oldest="2019-12-31",
                completion_reason="TARGET_START_REACHED", last_page_empty=False,
            ),
        )
        self.assertEqual(
            ("COMPLETE", "COMPLETE_RETAINED", None),
            classify_acquisition(
                reported="COMPLETE", pages=[1], oldest="2024-01-02",
                completion_reason="EMPTY_PROVIDER_BOUNDARY", last_page_empty=True,
            ),
        )

    def test_not_started_begins_at_page_one(self):
        self.assertEqual(
            ("NOT_YET_ACQUIRED", "START_FROM_1", 1),
            classify_acquisition(
                reported="NOT_STARTED", pages=[], oldest=None,
                completion_reason=None, last_page_empty=False,
            ),
        )

    def test_partial_continues_after_last_contiguous_page(self):
        self.assertEqual(
            ("ACQUISITION_PARTIAL", "CONTINUE_FROM_PAGE_N", 4),
            classify_acquisition(
                reported="RUNNING", pages=[1, 2, 3], oldest="2023-01-01",
                completion_reason=None, last_page_empty=False,
            ),
        )

    def test_gap_and_hard_stop_fail_closed(self):
        for result in (
            classify_acquisition(
                reported="RUNNING", pages=[1, 3], oldest="2023-01-01",
                completion_reason=None, last_page_empty=False,
            ),
            classify_acquisition(
                reported="RUNNING", pages=[1], oldest="2023-01-01",
                completion_reason=None, last_page_empty=False, hard_stop=True,
            ),
        ):
            self.assertEqual(("HARD_STOP_REVIEW", "MANUAL_REVIEW", None), result)

    def test_plan_has_exact_union_no_duplicate_and_preserves_provenance(self):
        rows = [inventory_row(index) for index in range(600)]
        rows[0].update(
            acquisition_status="NOT_YET_ACQUIRED", action="START_FROM_1",
        )
        rows[1].update(
            acquisition_status="ACQUISITION_PARTIAL", action="CONTINUE_FROM_PAGE_N",
            next_page_if_continuable=8, last_page=7,
        )
        rows[2].update(
            acquisition_status="ACQUISITION_FAILED", action="MANUAL_REVIEW",
        )
        candidates, shards = build_supplemental_plan(rows, 3)
        self.assertEqual(3, len(candidates))
        assigned = [job for shard in shards for job in shard["jobs"]]
        self.assertEqual({"T000", "T001"}, {job["ticker"] for job in assigned})
        self.assertEqual(len(assigned), len({job["ticker"] for job in assigned}))
        self.assertEqual(1, next(job for job in assigned if job["ticker"] == "T000")["start_page"])
        continued = next(job for job in assigned if job["ticker"] == "T001")
        self.assertEqual(8, continued["start_page"])
        self.assertEqual("worker-01.zip", continued["source_zip"])
        self.assertEqual("a" * 64, continued["source_zip_sha256"])

    def test_plan_rejects_non_600_or_duplicate_union(self):
        with self.assertRaisesRegex(ValueError, "exact 600-security union"):
            build_supplemental_plan([inventory_row(index) for index in range(599)])
        rows = [inventory_row(index) for index in range(600)]
        rows[-1]["ticker"] = rows[0]["ticker"]
        with self.assertRaisesRegex(ValueError, "exact 600-security union"):
            build_supplemental_plan(rows)

    def test_frozen_supplemental_shards_are_disjoint_and_never_overwrite_initial_raw(self):
        index = c6.read_json(CFG / "index.json")
        assigned = []
        for entry in index["shards"]:
            shard = c6.read_json(CFG / entry["path"])
            self.assertEqual(entry["sha256"], shard["shard_sha256"])
            for job in shard["jobs"]:
                assigned.append(job["ticker"])
                if job["action"] == "CONTINUE_FROM_PAGE_N":
                    self.assertEqual(int(job["last_page"]) + 1, int(job["start_page"]))
                else:
                    self.assertEqual(1, int(job["start_page"]))
        self.assertEqual(141, len(assigned))
        self.assertEqual(len(assigned), len(set(assigned)))
        contract = c6.read_json(CFG / "contract.json")
        self.assertEqual("data/raw/cafef_supplemental_v1", contract["raw_output_namespace"])
        self.assertEqual("FORBIDDEN", contract["initial_evidence_mutation"])

    def test_supplemental_dry_run_preserves_zero_null_and_hard_stop_contract(self):
        spec = importlib.util.spec_from_file_location(
            "cafef_supplemental_runner", ROOT / "scripts/run_cafef_supplemental_worker.py"
        )
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        commit = "a" * 40
        output = io.StringIO()
        with patch.object(runner, "validate_git_state", return_value=commit), \
                patch.object(runner, "acquire_page", side_effect=AssertionError("network called")), \
                redirect_stdout(output):
            result = runner.main([
                "--shard", "configs/data/cafef_supplemental_v1/supplemental-01.json",
                "--expected-commit", commit, "--dry-run",
            ])
        self.assertEqual(0, result)
        self.assertIn("network_requests=0", output.getvalue())
        contract = c6.read_json(CFG / "contract.json")
        self.assertFalse(contract["null_to_zero"])
        self.assertEqual("OBSERVED_ZERO_VOLUME", contract["zero_volume_observation"])
        self.assertEqual([401, 403, 429], contract["hard_stop_http_statuses"])
        self.assertEqual(
            "OBSERVED_WITH_NULL_VOLUME_COMPONENTS",
            runner.classify_observation({"Volume": 0, "AgreedVolume": None}),
        )


if __name__ == "__main__":
    unittest.main()
