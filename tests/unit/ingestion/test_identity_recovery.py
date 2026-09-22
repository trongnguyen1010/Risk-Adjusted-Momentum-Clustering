"""Offline tests for Stage A6 historical identity recovery."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.identity_recovery import (
    IDENTITY_HISTORY_COLUMNS, build_identity_history, build_stage_a6,
    load_evidence_bundle, validate_intervals,
)
from delta_t1.io import digest, encoded, write_json, write_rows
from scripts.run_identity_recovery import main as cli_main


def _event(candidate, security_id, old, old_exchange, new, new_exchange,
           start, effective, recovery_type="EXCHANGE_TRANSFER"):
    return {"candidate_id": candidate, "security_id": security_id,
            "from_ticker": old, "from_exchange": old_exchange,
            "to_ticker": new, "to_exchange": new_exchange,
            "from_effective_from": start, "effective_date": effective,
            "recovery_type": recovery_type, "evidence_source": "LISTING_NOTICE",
            "evidence_reference": f"NOTICE-{candidate}", "identity_confidence": "HIGH",
            "evidence_document": "notice.txt", "evidence_sha256": "a" * 64,
            "issuer_identifier": f"ISSUER-{security_id}"}


class IdentityRecoveryTests(unittest.TestCase):
    def test_schema_matches_section_35(self):
        self.assertEqual(IDENTITY_HISTORY_COLUMNS, (
            "security_id", "ticker", "exchange", "effective_from", "effective_to",
            "evidence_source", "evidence_reference", "identity_confidence"))

    def _raw_evidence(self, document):
        return {"evidence_id": "EV-1", "security_id": "S1", "from_ticker": "OLD", "from_exchange": "HOSE",
                "to_ticker": "NEW", "to_exchange": "HOSE", "from_effective_from": "2018-01-01",
                "effective_date": "2020-01-01", "recovery_type": "TICKER_RENAME",
                "evidence_source": "LISTING_NOTICE", "evidence_reference": "NOTICE-1",
                "evidence_document": document.name, "evidence_sha256": digest(document.read_bytes()),
                "match_method": "STABLE_SECURITY_ID_DOCUMENTED"}

    def _review_manifest(self, record, document):
        return {"review_policy_id": "A6_MANUAL_IDENTITY_REVIEW_V1", "scope_complete": True,
                "scope_dispositions": [{"security_id": record["security_id"],
                                        "disposition": "TRANSITION_ASSERTED",
                                        "reviewer_id": "independent-reviewer",
                                        "reason": "Reviewed transition evidence"}], "reviews": [{
                    "evidence_id": record["evidence_id"],
                    "assertion_sha256": digest(encoded(record)),
                    "document_sha256": digest(document.read_bytes()), "decision": "APPROVED",
                    "reviewer_id": "independent-reviewer", "reviewed_at": "2026-01-01",
                    "issuer_identifier": "ISSUER-1", "document_locator": "page 1",
                    "field_bindings": {field: "page 1" for field in (
                        "security_id", "from_ticker", "from_exchange", "to_ticker",
                        "to_exchange", "from_effective_from", "effective_date")}}]}

    def _write_review(self, root, record, document):
        review = root / "review.json"
        review.write_text(json.dumps(self._review_manifest(record, document)), encoding="utf-8")
        return review

    def _write_scope(self, root, security_ids=("S1",)):
        scope = root / "scope.json"
        scope.write_text(json.dumps([{"security_id": security_id,
                                      "scope_reason": "suspected historical identity break",
                                      "scope_source": "A6_REVIEW_QUEUE",
                                      "scope_reference": f"QUEUE-{security_id}"}
                                     for security_id in security_ids]), encoding="utf-8")
        return scope

    def test_ticker_only_and_name_similarity_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "notice.txt"
            document.write_text("official notice", encoding="utf-8")
            record = self._raw_evidence(document)
            record["match_method"] = "CURRENT_TICKER"
            record["evidence_reference"] = "NAME_SIMILARITY"
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps([record]), encoding="utf-8")
            review = self._write_review(root, record, document)
            scope = self._write_scope(root)
            accepted, rejected, _, _ = load_evidence_bundle(
                evidence, review, scope, root=root, canonical_ids={"S1"}, cutoff=date(2026, 9, 1))
            self.assertEqual([], accepted)
            self.assertIn("ticker/name-only", rejected[0]["reason"])

    def test_document_checksum_and_source_are_strict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "notice.txt"
            document.write_text("official notice", encoding="utf-8")
            record = self._raw_evidence(document)
            record["evidence_source"] = "BLOG"
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps([record]), encoding="utf-8")
            review = self._write_review(root, record, document)
            scope = self._write_scope(root)
            accepted, rejected, _, _ = load_evidence_bundle(
                evidence, review, scope, root=root, canonical_ids={"S1"}, cutoff=date(2026, 9, 1))
            self.assertFalse(accepted)
            self.assertIn("unsupported evidence_source", rejected[0]["reason"])

    def test_multi_event_chain_has_non_overlapping_intervals(self):
        securities = [{"security_id": "S1", "ticker": "NEW", "exchange": "HOSE",
                       "valid_from": "2020-01-01", "valid_to": None}]
        events = [
            _event("1", "S1", "OLD", "UPCOM", "MID", "HNX", "2018-01-01", "2020-01-01"),
            _event("2", "S1", "MID", "HNX", "NEW", "HOSE", "2020-01-01", "2022-01-01", "TICKER_RENAME"),
        ]
        rows, confirmed, rejected = build_identity_history(securities, events)
        self.assertEqual({"S1"}, confirmed)
        self.assertFalse(rejected)
        self.assertEqual(["OLD", "MID", "NEW"], [row["ticker"] for row in rows])
        self.assertEqual("2021-12-31", rows[1]["effective_to"])
        self.assertIsNone(rows[2]["effective_to"])

    def test_interval_validation_rejects_shared_inclusive_boundary(self):
        rows = [
            {"security_id": "S1", "ticker": "AAA", "exchange": "HNX",
             "effective_from": "2020-01-01", "effective_to": "2021-01-01",
             "evidence_source": "LISTING_NOTICE", "evidence_reference": "D1", "identity_confidence": "HIGH"},
            {"security_id": "S1", "ticker": "BBB", "exchange": "HOSE",
             "effective_from": "2021-01-01", "effective_to": None,
             "evidence_source": "LISTING_NOTICE", "evidence_reference": "D2", "identity_confidence": "HIGH"},
        ]
        with self.assertRaisesRegex(ValueError, "overlapping"):
            validate_intervals(rows)

    def test_cross_entity_ticker_collision_is_rejected(self):
        rows = [
            {"security_id": "S1", "ticker": "AAA", "exchange": "HOSE",
             "effective_from": "2020-01-01", "effective_to": None,
             "evidence_source": "PROVISIONAL_OBSERVED", "evidence_reference": "C1",
             "identity_confidence": "PROVISIONAL"},
            {"security_id": "S2", "ticker": "AAA", "exchange": "HOSE",
             "effective_from": "2021-01-01", "effective_to": None,
             "evidence_source": "PROVISIONAL_OBSERVED", "evidence_reference": "C2",
             "identity_confidence": "PROVISIONAL"},
        ]
        with self.assertRaisesRegex(ValueError, "cross-entity"):
            validate_intervals(rows)

    def _fixture(self, root):
        canonical = root / "data" / "canonical" / "canonical-test"
        (canonical / "clean").mkdir(parents=True)
        write_rows(canonical / "clean" / "securities.jsonl", [
            {"security_id": "S1", "ticker": "NEW", "exchange": "HOSE",
             "valid_from": "2020-01-01", "valid_to": None, "identity_status": "provisional"}])
        write_json(canonical / "manifest.json", {
            "run_id": canonical.name, "canonical_promotion_status": "PASS", "synthetic": False,
            "collection_end": "2026-08-28",
            "artifacts": {"clean/securities.jsonl": digest((canonical / "clean" / "securities.jsonl").read_bytes())}})
        base = root / "artifacts" / "data_enrichment"
        stages = []
        specs = [("a1", "A1", "PASS"), ("a2", "A2", "PASS"),
                 ("a3", "A3 — Primary Provider Recovery Pilot", "PARTIAL"),
                 ("a4", "A4 — Secondary Source Recovery Pilot", "PARTIAL")]
        for index, (name, stage, status) in enumerate(specs):
            path = base / name
            path.mkdir(parents=True)
            write_json(path / "payload.json", {"stage": stage})
            manifest = {"run_id": name, "stage": stage, "status": status,
                        "canonical_run_id": canonical.name,
                        "artifacts": {"payload.json": digest((path / "payload.json").read_bytes())}}
            if index >= 1:
                manifest["a1_run_id"] = "a1"
            if index >= 2:
                manifest["a2_run_id"] = "a2"
            if index >= 3:
                manifest["a3_run_id"] = "a3"
            write_json(path / "manifest.json", manifest)
            stages.append(path)
        return canonical, stages

    def test_no_evidence_is_partial_and_parquet_has_real_null(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical, stages = self._fixture(root)
            output, manifest = build_stage_a6(canonical, *stages, root=root)
            self.assertEqual("PARTIAL", manifest["status"])
            self.assertEqual(0, manifest["metrics"]["identities_liberated"])
            table = pq.read_table(output / "security_identity_history.parquet")
            self.assertEqual(0, table.num_rows)
            unresolved = [json.loads(line) for line in
                          (output / "identity_recovery_evidence.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual("UNRESOLVED_IDENTITY", unresolved[0]["record_type"])

    def test_reviewed_hashed_evidence_can_liberate_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical, stages = self._fixture(root)
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            document = evidence_dir / "notice.txt"
            document.write_text("official exchange notice", encoding="utf-8")
            evidence = evidence_dir / "transitions.json"
            record = self._raw_evidence(document)
            evidence.write_text(json.dumps([record]), encoding="utf-8")
            review = self._write_review(evidence_dir, record, document)
            scope = self._write_scope(evidence_dir)
            output, manifest = build_stage_a6(canonical, *stages, root=root,
                                              evidence_path=evidence, review_manifest_path=review,
                                              candidate_scope_path=scope)
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(1, manifest["metrics"]["identities_liberated"])
            self.assertEqual(digest(evidence.read_bytes()), manifest["identity_evidence_input"]["sha256"])
            self.assertEqual(digest(document.read_bytes()), manifest["evidence_document_hashes"]["notice.txt"])
            preserved = output / manifest["preserved_evidence_documents"]["notice.txt"]
            self.assertEqual(document.read_bytes(), preserved.read_bytes())

    def _run_mixed_evidence(self, root, disposition):
        canonical, stages = self._fixture(root)
        evidence_dir = root / "evidence"
        evidence_dir.mkdir()
        document = evidence_dir / "notice.txt"
        document.write_text("official exchange notice", encoding="utf-8")
        valid = self._raw_evidence(document)
        invalid = {**valid, "evidence_id": "EV-2", "match_method": "CURRENT_TICKER"}
        evidence = evidence_dir / "transitions.json"
        evidence.write_text(json.dumps([valid, invalid]), encoding="utf-8")
        review_manifest = self._review_manifest(valid, document)
        review_manifest["scope_dispositions"][0]["disposition"] = disposition
        invalid_review = {**review_manifest["reviews"][0],
                          "evidence_id": invalid["evidence_id"],
                          "assertion_sha256": digest(encoded(invalid))}
        review_manifest["reviews"].append(invalid_review)
        review = evidence_dir / "review.json"
        review.write_text(json.dumps(review_manifest), encoding="utf-8")
        scope = self._write_scope(evidence_dir)
        return build_stage_a6(canonical, *stages, root=root, evidence_path=evidence,
                              review_manifest_path=review, candidate_scope_path=scope)

    def test_mixed_evidence_cannot_satisfy_transition_asserted(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self._run_mixed_evidence(Path(temporary), "TRANSITION_ASSERTED")
            self.assertEqual("PARTIAL", manifest["status"])
            self.assertEqual(0, manifest["metrics"]["identities_liberated"])
            self.assertEqual(0, manifest["metrics"]["verified_transition_events"])
            self.assertEqual(0, pq.read_table(output / "security_identity_history.parquet").num_rows)

    def test_mixed_evidence_can_only_resolve_as_rejected_without_liberation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self._run_mixed_evidence(Path(temporary), "REJECTED")
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(0, manifest["metrics"]["identities_liberated"])
            self.assertEqual(0, manifest["metrics"]["verified_transition_events"])
            self.assertEqual(0, pq.read_table(output / "security_identity_history.parquet").num_rows)

    def test_future_effective_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "notice.txt"
            document.write_text("notice", encoding="utf-8")
            record = self._raw_evidence(document)
            record["effective_date"] = "2027-01-01"
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps([record]), encoding="utf-8")
            review, scope = self._write_review(root, record, document), self._write_scope(root)
            accepted, rejected, _, _ = load_evidence_bundle(
                evidence, review, scope, root=root, canonical_ids={"S1"}, cutoff=date(2026, 8, 28))
            self.assertFalse(accepted)
            self.assertIn("exceeds canonical cutoff", rejected[0]["reason"])

    def test_issuer_identifier_must_be_one_to_one(self):
        securities = [
            {"security_id": "S1", "ticker": "A1", "exchange": "HOSE", "valid_to": None},
            {"security_id": "S2", "ticker": "A2", "exchange": "HOSE", "valid_to": None},
        ]
        first = _event("E1", "S1", "X1", "HOSE", "A1", "HOSE", "2018-01-01", "2020-01-01", "TICKER_RENAME")
        second = _event("E2", "S2", "X2", "HOSE", "A2", "HOSE", "2018-01-01", "2020-01-01", "TICKER_RENAME")
        first["issuer_identifier"] = second["issuer_identifier"] = "ISSUER-SAME"
        rows, confirmed, rejected = build_identity_history(securities, [first, second])
        self.assertFalse(rows)
        self.assertFalse(confirmed)
        self.assertEqual(2, len(rejected))
        self.assertTrue(all(row["reason"] == "ISSUER_IDENTIFIER_NOT_ONE_TO_ONE" for row in rejected))

    def test_cli_requires_execute(self):
        self.assertEqual(2, cli_main(["--canonical", "dummy"]))


if __name__ == "__main__":
    unittest.main()
