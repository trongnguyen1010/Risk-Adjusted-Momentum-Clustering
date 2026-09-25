import csv
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from delta_t1.ingestion import cafef_expansion as c6

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / "configs" / "data" / "cafef_expansion_v1"


class CafeFExpansionPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.universe = c6.read_json(CFG / "universe.json")
        cls.index = c6.read_json(CFG / "index.json")
        cls.assignments = [c6.read_json(CFG / f"worker-{i:02d}.json") for i in range(1, 6)]
        with (CFG / "reserve.csv").open(encoding="utf-8") as handle:
            cls.reserve = list(csv.DictReader(handle))
        with (CFG / "priority_ranking.csv").open(encoding="utf-8") as handle:
            cls.ranking = list(csv.DictReader(handle))

    def test_current_500_and_reviewed_aliases_excluded(self):
        current = {row["ticker"] for row in c6.read_json(ROOT / "configs/data/m1_scale.universe.v1.json")}
        selected = {row["ticker"] for row in self.universe["securities"]}
        self.assertTrue(current.isdisjoint(selected))
        aliases = {row["ticker"] for row in self.ranking if row["selection_status"] == "IDENTITY_DUPLICATE_EXCLUDED"}
        self.assertTrue(aliases.isdisjoint(selected))
        self.assertEqual(500, sum(row["selection_status"] == "CURRENT_500_EXCLUDED" for row in self.ranking))

    def test_exact_count_identity_exchange_and_reserve_exclusion(self):
        rows = self.universe["securities"]
        self.assertEqual(600, len(rows))
        self.assertEqual(600, len({row["security_id"] for row in rows}))
        self.assertEqual({"SELECTED_EXPANSION_600"}, {row["selection_status"] for row in rows})
        self.assertEqual({"RESERVE"}, {row["selection_status"] for row in self.reserve})
        self.assertTrue({row["exchange"] for row in rows} <= set(c6.EXCHANGES))
        self.assertTrue({row["ticker"] for row in rows}.isdisjoint({row["ticker"] for row in self.reserve}))

    def test_priority_and_partition_are_deterministic_balanced_exact(self):
        selected = [row for row in self.ranking if row["selection_status"] == "SELECTED_EXPANSION_600"]
        expected = sorted(selected, key=c6.priority_key)
        self.assertEqual([r["ticker"] for r in expected], [r["ticker"] for r in self.universe["securities"]])
        self.assertEqual(5, len(self.assignments))
        ticker_sets = [set(row["tickers"]) for row in self.assignments]
        for i, left in enumerate(ticker_sets):
            for right in ticker_sets[i + 1:]: self.assertTrue(left.isdisjoint(right))
        self.assertEqual({r["ticker"] for r in self.universe["securities"]}, set().union(*ticker_sets))
        loads = [row["estimated_requests"] for row in self.assignments]
        self.assertLessEqual(max(loads) - min(loads), 1)

    def test_assignment_hash_and_page_size_contract(self):
        for assignment in self.assignments:
            self.assertEqual(assignment["assignment_sha256"], c6.assignment_digest(assignment))
            self.assertEqual(30, assignment["page_size"])


class CafeFExpansionRuntimeTests(unittest.TestCase):
    @staticmethod
    def _verifier_module():
        spec=importlib.util.spec_from_file_location("c6verifier",ROOT/"scripts/verify_cafef_expansion_handoffs.py"); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

    @staticmethod
    def _archive(path, *, worker="worker-01", raw=b"raw"):
        assignment={"expansion_id":c6.EXPANSION_ID,"assignment_id":f"{c6.EXPANSION_ID}-worker-01","worker_id":worker,"git_commit":"frozen","execution_version":c6.EXECUTION_VERSION,"tickers":["AAA"],"security_ids":["KBS:HOSE:AAA"],"universe_hash":"u","crawl_contract_hash":"c"}
        assignment["assignment_sha256"]=c6.assignment_digest(assignment)
        contract={"page_size":30}; meta={"ticker":"AAA","page_index":1,"page_size":30,"source_endpoint":c6.TRADE_HISTORY_ENDPOINT,"sha256":c6.sha256_bytes(b"raw")}
        manifest={"expansion_id":c6.EXPANSION_ID,"assignment_id":assignment["assignment_id"],"worker_id":worker,"git_commit":"frozen","execution_version":c6.EXECUTION_VERSION,"assignment_sha256":assignment["assignment_sha256"],"universe_sha256":"u","crawl_contract_sha256":"c","adapter_version":c6.ADAPTER_VERSION,"run_id":"r","network_requests":1,"ticker_count":1,"complete_tickers":1,"partial_tickers":0,"failed_tickers":0,"raw_page_count":1}
        files={"handoff_manifest.json":c6.canonical_bytes(manifest),"run.json":c6.canonical_bytes({"run_id":"r","network_requests":1}),"assignment.json":c6.canonical_bytes(assignment),"crawl_contract.json":c6.canonical_bytes(contract),"worker_report.json":c6.canonical_bytes({"statuses":{"AAA":"COMPLETE"}}),"raw/AAA/page-001.json":raw,"raw/AAA/page-001.metadata.json":c6.canonical_bytes(meta)}
        files["checksums.sha256"]=c6.checksums_for_files(files)
        with zipfile.ZipFile(path,"w") as z:
            for name,body in files.items(): z.writestr(name,body)
        index={"crawl_contract_sha256":c6.sha256_bytes(c6.canonical_bytes(contract)),"assignments":[{"assignment_id":assignment["assignment_id"],"worker_id":"worker-01","sha256":assignment["assignment_sha256"]}]}
        return index, assignment

    def test_zero_volume_is_observed_and_null_is_not_zero(self):
        self.assertEqual("OBSERVED_ZERO_VOLUME", c6.classify_observation({"Volume": 0, "AgreedVolume": 0}))
        self.assertEqual("OBSERVED_WITH_NULL_VOLUME_COMPONENTS", c6.classify_observation({"Volume": None, "AgreedVolume": None}))

    def test_raw_immutability_and_resume_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw/T/page-001.json"; c6.immutable_write(raw, b"one")
            with self.assertRaises(ValueError): c6.immutable_write(raw, b"two")
            meta = {"sha256": c6.sha256_bytes(b"one"), "adapter_version": c6.ADAPTER_VERSION}
            c6.immutable_write(raw.with_name("page-001.metadata.json"), c6.canonical_bytes(meta))
            c6.verify_existing_raw(Path(tmp), c6.ADAPTER_VERSION)
            raw.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"): c6.verify_existing_raw(Path(tmp), c6.ADAPTER_VERSION)

    def test_hard_stop_http(self):
        class Opener:
            def open(self, *args, **kwargs): raise __import__("urllib.error").error.HTTPError("u", 429, "rate", {}, None)
        contract = {"page_size": 30, "attempts": 2, "timeout_seconds": 20, "max_response_bytes": 1000}
        with patch.object(c6, "build_opener", return_value=Opener()):
            with self.assertRaisesRegex(RuntimeError, "HARD_STOP_HTTP_429"): c6.acquire_page("AAA", 1, contract)

    def test_archive_paths_checksums_and_secret_filter(self):
        self.assertTrue(c6.safe_archive_name("raw/AAA/page-001.json"))
        self.assertFalse(c6.safe_archive_name("../outside")); self.assertFalse(c6.safe_archive_name("cookies.json")); self.assertFalse(c6.safe_archive_name("C:\\absolute"))
        self.assertTrue(c6.json_contains_secret_keys(b'{"api_token":"do-not-package"}'))
        self.assertFalse(c6.json_contains_secret_keys(b'{"ticker":"AAA"}'))
        files={"a.json":b"a","raw/T/page-001.json":b"raw"}; parsed=c6.parse_checksums(c6.checksums_for_files(files))
        self.assertEqual({name:c6.sha256_bytes(body) for name,body in files.items()}, parsed)

    def test_central_set_detects_overlap_missing_and_reserve(self):
        assignments=[{"assignment_id":f"a{i}","tickers":[f"T{i}"]} for i in range(5)]
        index={"assignments":[{"assignment_id":f"a{i}"} for i in range(5)]}; universe={"securities":[{"ticker":f"T{i}"} for i in range(5)]}
        self.assertEqual(5,len(c6.validate_handoff_set(assignments,index,universe,set())))
        broken=json.loads(json.dumps(assignments)); broken[1]["tickers"]=["T0"]
        with self.assertRaisesRegex(ValueError,"overlap"): c6.validate_handoff_set(broken,index,universe,set())
        with self.assertRaisesRegex(ValueError,"missing"): c6.validate_handoff_set(assignments[:-1],index,universe,set())
        with self.assertRaisesRegex(ValueError,"reserve"): c6.validate_handoff_set(assignments,index,universe,{"T0"})

    def test_central_archive_detects_wrong_worker_and_modified_raw(self):
        verifier=self._verifier_module()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"ok.zip"; index,_=self._archive(path)
            assignment=verifier.verify_archive(path,index,{"securities":[{"ticker":"AAA"}]},{"page_size":30})
            self.assertEqual("worker-01",assignment["worker_id"])
            wrong=Path(tmp)/"wrong.zip"; wrong_index,_=self._archive(wrong,worker="worker-99")
            with self.assertRaisesRegex(ValueError,"wrong worker"): verifier.verify_archive(wrong,wrong_index,{}, {})
            modified=Path(tmp)/"modified.zip"; modified_index,_=self._archive(modified,raw=b"tampered")
            with self.assertRaisesRegex(ValueError,"modified raw"): verifier.verify_archive(modified,modified_index,{}, {})

    def test_dry_run_path_makes_zero_network_requests(self):
        spec=importlib.util.spec_from_file_location("c6runner",ROOT/"scripts/run_cafef_expansion_worker.py"); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        assignment={"assignment_id":"a"}
        with patch.object(module,"validate_assignment",return_value=(assignment,{},{})), patch.object(module,"acquire_page",side_effect=AssertionError("network")):
            output=io.StringIO()
            with redirect_stdout(output): rc=module.main(["--assignment","x.json","--dry-run"])
        self.assertEqual(0,rc); self.assertIn("network_requests=0",output.getvalue())


if __name__ == "__main__": unittest.main()
