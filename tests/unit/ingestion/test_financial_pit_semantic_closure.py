from __future__ import annotations

import json
from pathlib import Path

from delta_t1.ingestion.financial_pit_semantic_closure import (
    LOW_OCR_IDS,
    normalize_quarantine_reasons,
    open11_scope,
    period_from_text,
)


ROOT = Path(__file__).resolve().parents[3]
R2 = ROOT / "artifacts/financial_pit/fin-pit-2-r2-period-scope-remediation-v2"
R3 = ROOT / "artifacts/financial_pit/fin-pit-2-r3-semantic-closure-v1"


def load_json(name: str) -> dict:
    return json.loads((R3 / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(x) for x in (R3 / name).read_text(encoding="utf-8").splitlines() if x]


def test_period_heading_rules_do_not_use_quarter_number_alone() -> None:
    assert period_from_text("Cho kỳ ba tháng kết thúc ngày 30/06/2025") == "STANDALONE"
    assert period_from_text("Cho kỳ sáu tháng kết thúc ngày 30/06/2025") == "YTD"
    assert period_from_text("Cho kỳ chín tháng kết thúc ngày 30/09/2025") == "YTD"
    assert period_from_text("Báo cáo quý 2 năm 2025") is None


def test_open11_mapping_is_exact_and_not_generalized() -> None:
    exact = {"ticker": "ACV", "document_role": "PRIMARY_FINANCIAL_REPORT",
             "document_hash": "138014cf7cc322e166a49bf0defa05af41b7c97e41d72485467cc1732bda2ee2"}
    assert open11_scope(exact) == "SEPARATE"
    assert open11_scope({**exact, "ticker": "PVS"}) is None
    assert open11_scope({**exact, "document_role": "SUPPORTING_ATTACHMENT"}) is None
    assert open11_scope({**exact, "document_hash": "0" * 64}) is None


def test_reason_normalization_never_emits_unknown() -> None:
    reasons = normalize_quarantine_reasons(
        {"reasons": ["PERIOD_UNRESOLVED", "unmapped legacy marker"]},
        {"report_candidate_id": "report-test", "document_role": "PRIMARY_FINANCIAL_REPORT"},
    )
    assert reasons[0] == {"reason": "PERIOD_UNRESOLVED"}
    assert reasons[1]["reason"] == "OTHER"
    assert reasons[1]["reason_detail"] == "unmapped legacy marker"


def test_targeted_ocr_is_bounded_and_preserves_raw_hashes() -> None:
    rows = load_jsonl("ocr_targeted_remediation.jsonl")
    assert {x["candidate_id"] for x in rows} == LOW_OCR_IDS
    assert len(rows) == 4
    assert all(len(x["attempts"]) == 4 for x in rows)
    assert all(x["raw_pdf_unchanged"] for x in rows)
    assert {x["ocr_final_status"] for x in rows} <= {
        "RECOVERED", "IRRECOVERABLE_LOW_CONFIDENCE", "NOT_REQUIRED_FOR_SEMANTIC_DECISION"
    }
    assert sum(x["ocr_final_status"] == "RECOVERED" for x in rows) == 0
    assert sum(x["ocr_final_status"] == "IRRECOVERABLE_LOW_CONFIDENCE" for x in rows) == 4


def test_scope_and_linkage_close_without_force_matching() -> None:
    scope = load_jsonl("scope_closure_review.jsonl")
    assert len(scope) == 5
    assert all(x["classification"] == "SUPPORTING_ATTACHMENT_NOT_SCOPE_BEARING" for x in scope)
    assert all(x["scope_final"] == "NOT_APPLICABLE" for x in scope)
    linkage = load_jsonl("linkage_closure_review.jsonl")
    assert len(linkage) == 24
    assert all(x["force_matched"] is False for x in linkage)
    assert {x["linkage_final"] for x in linkage} <= {
        "VERIFIED", "EXCLUDED_LINKAGE_UNRESOLVED", "NOT_APPLICABLE"
    }


def test_every_candidate_and_fact_has_explained_final_state() -> None:
    dispositions = load_jsonl("final_dispositions.jsonl")
    assert len(dispositions) == 24
    assert all(x["final_disposition"] and x["final_reason"] for x in dispositions)
    assert not {"UNKNOWN", "AMBIGUOUS", "QUARANTINE"} & {
        x["final_disposition"] for x in dispositions
    }
    facts = load_jsonl("fact_candidates_updated.jsonl")
    assert len(facts) == 242
    assert all(x.get("semantic_ready") or (x.get("final_disposition") and x.get("final_reason")) for x in facts)


def test_stage_boundaries_timing_and_revision_are_preserved() -> None:
    gate = load_json("gate.json")
    assert gate["status"] == "PASS"
    assert gate["revision_groups_changed"] == 0
    assert gate["timing_preserved"] is True
    assert gate["canonical_rows_written"] == 0
    assert gate["financial_features_written"] == 0
    before = [json.loads(x) for x in (R2 / "report_candidates_updated.jsonl").read_text(encoding="utf-8").splitlines()]
    after = load_jsonl("report_candidates_updated.jsonl")
    timing = ("publication_date", "eligible_from", "timing_grade", "timing_policy_version", "timing_evidence_source")
    assert [[x.get(k) for k in timing] for x in before] == [[x.get(k) for k in timing] for x in after]
    assert load_json("semantic_closure_report.json")["revision_groups_changed"] == 0
