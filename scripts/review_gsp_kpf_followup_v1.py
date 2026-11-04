"""Seal two-target follow-up findings, keeping unsigned proposals and KPF hold."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_decision_packet import inspect_history_document
from delta_t1.ingestion.corporate_action_revision_review import review_case
from collect_gsp_kpf_followup_v1 import safe

sha = lambda body: hashlib.sha256(body).hexdigest()


def run(output):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    inputs = {}
    def pin(path, expected=None):
        body = path.read_bytes()
        digest = sha(body)
        if expected and expected != digest:
            raise ValueError("INPUT_HASH_MISMATCH:" + str(path))
        inputs[path.relative_to(ROOT).as_posix()] = digest
        return body
    config = json.loads(pin(ROOT / "configs/data/corporate_action_gsp_kpf_followup_v1.json"))
    base = ROOT / "tmp/ca_gsp_kpf_documents_20261102_v1"
    acquired_manifest = json.loads(pin(base / "manifest.json", "3bba20e4d4ca642d105392276e3725b883a978b75958b1ffa96b5b49ca7ab1c3"))
    files = {name: pin(safe(base, name), digest) for name, digest in acquired_manifest["files"].items()}
    for name, digest in acquired_manifest["inputs_verified"].items():
        pin(safe(ROOT, name), digest)
    receipt = json.loads(files["requests.json"])
    if len(receipt) != 1 or receipt[0]["status"] != 200 or receipt[0].get("error"):
        raise ValueError("EXACT_ONE_SUCCESSFUL_ARCHIVE_PDF_REQUIRED")
    pdf = files["raw/response-0001.bin"]
    pdf_hash = sha(pdf)
    if pdf_hash != "55f304ada00fe480e9b634e68b538dc4bb8da30dda89ef0cfdb3adc1537e63db" or len(pdf) != 854618:
        raise ValueError("VISUALLY_REVIEWED_PDF_HASH_REQUIRED")
    if len(PdfReader(base / "raw/response-0001.bin").pages) != 4:
        raise ValueError("PDF_PAGE_COUNT_CHANGED")
    images = {}
    for page in range(1, 5):
        p = ROOT / f"tmp/ca_gsp_kpf_visual_20261102_v1/kpf-hose-{page}.png"
        images[str(page)] = {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(pin(p))}
    docs = {}
    for saved in json.loads(files["cached_documents.json"]):
        current = inspect_history_document(pin(safe(ROOT, saved["raw_path"]), saved["source_hash"]), saved["source_url"])
        docs[current["provider_article_id"]] = current | {k: saved[k] for k in ["document_id", "source_url", "source_hash", "raw_path"]}
    if set(docs) != {"143831", "144289", "145371", "145572", "77498", "139236"}:
        raise ValueError("EXACT_SIX_DOCUMENTS_REQUIRED")
    packet = ROOT / "tmp/ca_decision25_20261102_v2"
    pm = json.loads(pin(packet / "manifest.json", "3449993c5f7bdc2dca7e91279d27cba9ed3b89657a063cd69005c05ecdeef92a"))
    requests = [json.loads(l) for l in pin(packet / "decision_requests_25.jsonl", pm["files"]["decision_requests_25.jsonl"]).splitlines() if l.strip()]
    requests = {r["ticker"]: r for r in requests if r["ticker"] in {"GSP", "KPF"}}
    if len(requests) != 2:
        raise ValueError("TWO_PAYLOADS_ONLY")
    histories = [json.loads(l) for l in pin(packet / "cached_history_evidence.jsonl", pm["files"]["cached_history_evidence.jsonl"]).splitlines() if l.strip()]
    old_gsp = [d for d in histories if d["provider_article_id"] == "144289"]
    if len(old_gsp) != 1:
        raise ValueError("OVERLOOKED_ARTICLE_ALREADY_PRESENT_IN_PRIOR_PACKET_REQUIRED")
    gsp = review_case(requests["GSP"], docs["143831"], [docs[p] for p in ["144289", "145371", "145572"]])
    kpf = review_case(requests["KPF"], docs["77498"], [docs["139236"]])
    assert all(e["contextual_link_supported"] for e in gsp["edges"])
    assert kpf["hold_reasons"] == ["CONTRADICTORY_NOTICE_DATE_LITERALS"]
    # Issue date transcriptions come from visual review, not the filename,
    # existing OCR text, site update timestamp, or chronology inference.
    pdf_review = {"source_url": config["kpf_pdf"], "pdf_path": (base / "raw/response-0001.bin").relative_to(ROOT).as_posix(),
        "pdf_sha256": pdf_hash, "size_bytes": len(pdf), "pdf_pages": 4, "visually_reviewed_pages": [1, 2, 3, 4],
        "images": images, "issuer_authority": "HOSE", "hosting_role": "COPY_ON_MARKET_ARCHIVE",
        "notice_number_literal": "62/TB-SGDHCM", "document_date": "2021-01-13",
        "page1": {"ticker": "KPF", "issuer_name": "CTCP Đầu tư Tài chính Hoàng Minh", "ex_date": "2021-01-19", "record_date": "2021-01-20",
            "stock_dividend_ratio_literal": "10:1", "stock_dividend_component_not_used_as_rights_ratio": True},
        "page2": {"component": "Thực hiện quyền mua cổ phiếu", "offering_quantity": 36035792,
            "primary_price_vnd_per_share": "10000", "primary_price_literal": "Giá phát hành: 10.000 đồng/cổ phiếu",
            "allocation": {"old_shares": 1, "rights": 1}, "execution": {"rights": 1, "new_shares": 2},
            "rights_ratio_exact": {"numerator": 2, "denominator": 1}, "transfer": ["2021-02-01", "2021-02-19"],
            "subscription": ["2021-02-01", "2021-03-01"]},
        "page3": {"signature_facsimile_name": "Trần Anh Đào", "seal_facsimile_visible": True,
            "cryptographic_signature_verified": False},
        "page4": {"visual_status": "BLANK_SCAN_BACKSIDE_WITH_FAINT_BLEED_THROUGH", "no_additional_notice_terms_readable": True},
        "vsd_notice44_reference_observed": False, "vsd_notice44_date_resolved": False,
        "publication_pit_established": False, "ex_date_field_proposed_for_application": False,
        "conclusion": "Corroborates KPF original economic terms and dates; does not settle the date or signed identity of VSD notice44."}
    discovery_receipts = []
    probe_names = ["page10", "page32", "page22", "page23", "page24", "extension"]
    for name in probe_names:
        folder = ROOT / f"tmp/ca_kpf_issuer_{name}_20261102_v1"
        requests_body = pin(folder / "requests.json")
        ledger = json.loads(requests_body)
        if len(ledger) != 1:
            raise ValueError("ONE_REQUEST_PER_PROBE_REQUIRED")
        r = ledger[0]
        pin(safe(folder, r["path"]), r["source_hash"])
        if name.startswith("page"):
            if r["status"] != 200 or r.get("error"):
                raise ValueError("PUBLIC_ISSUER_PAGE_REQUIRED")
            pin(folder / "links.json")
        else:
            if r["status"] != 406 or not r.get("error"):
                raise ValueError("PRESERVE_ISSUER_DOCUMENT_406_STOP")
        if (folder / "manifest.json").exists():
            pin(folder / "manifest.json")
        discovery_receipts.append({"probe": name, "folder": folder.relative_to(ROOT).as_posix(), "request": r})
    stage_requests = [*receipt, *[r["request"] for r in discovery_receipts]]
    scope_change = {"provider_article_id": "144289", "source_url": docs["144289"]["source_url"],
        "source_hash": docs["144289"]["source_hash"], "already_in_prior390_cache": True,
        "title": docs["144289"]["title"], "old_body_change_quotes": old_gsp[0]["body_change_quotes"],
        "new_body_change_quotes": docs["144289"]["body_change_quotes"],
        "old_scope": old_gsp[0]["change_scope_review"]["scope"],
        "new_scope": docs["144289"]["change_scope_review"]["scope"],
        "cause": "Prior preview recognized change keywords in title and cancellation/correction body patterns, but not explicit body schedule-extension purpose under a generic title.",
        "raw_changed": False, "prior_artifacts_overwritten": False}
    gsp_chain = {"ordered_provider_articles": ["143831", "144289", "145371", "145572"], "edges": gsp["edges"],
        "notice_reference_context": [
            {"referencing_article": "144289", "cited_notice": "1133/TB-CNVSD", "cited_date": "11/08/2021", "contextual_predecessor_article": "143831"},
            {"referencing_article": "145371", "cited_notice": "1203/TB-CNVSD", "cited_date": "01/09/2021", "contextual_predecessor_article": "144289"},
            {"referencing_article": "145572", "cited_notice": "1323/TB-CNVSD", "cited_date": "15/10/2021", "contextual_predecessor_article": "145371"}],
        "signed_notice_id_to_article_binding_verified": False,
        "classification": "CONTEXTUAL_CHAIN_SUPPORTED_NOT_SIGNED_NOTICE_BINDING_OR_FULL_ARCHIVE"}
    summary = {"stage": config["stage"], "technical_status": "PASS", "data_resolution_status": "PARTIAL",
        "decision_status": "MANUAL_REVIEW_REQUIRED", "c8_v2_inventory": 1522,
        "target_payloads": 2, "target_tickers": 2, "cached_raw_responses_verified": 6,
        "overlooked_gsp_cached_documents_recovered": 1, "gsp_schedule_edges_supported": 3,
        "target_context_supported_cases_before_after": [0, 1], "target_held_cases_before_after": [2, 1],
        "target_field_requests_context_supported": 2, "target_field_requests_held": 1,
        "six_case_rollup_context_supported_before_after": [4, 5], "six_case_rollup_held_before_after": [2, 1],
        "six_case_rollup_supported_field_requests": 9, "six_case_rollup_held_field_requests": 1,
        "complete_new_pdfs": 1, "visually_reviewed_pdf_pages": 4, "public_issuer_html_pages": 5,
        "formal_network_requests": len(stage_requests), "formal_http200": sum(r["status"] == 200 for r in stage_requests),
        "formal_http406": sum(r["status"] == 406 for r in stage_requests),
        "web_discovery_requests": "Separate search/open/click tool calls; physical source requests not instrumented, not included in the formal7 ledger.",
        "stopped_hosts": ["www.kpf.com.vn"], "host_stop_reason": "HTTP406 on linked extension PDF; no retry, alternate host/IP, header manipulation or SSL relaxation.",
        "hnx_network_requests": 0, "approved_fields_before_after": [0, 0], "applied_fields": 0, "canonical_written": False,
        "pit_status": "NOT_PROMOTED", "historical_identity": "UNVERIFIED",
        "limitations": ["GSP article144289 is a cached contextual predecessor matching1203 references, not a signed notice1203 document.",
            "KPF HOSE62 does not resolve VSD44 date; keep07/01 and08/01/2021 literals and hold.",
            "Only observed issuer pages and linked candidate inspected; no full issuer/source archive completeness claim."]}
    for name, digest in inputs.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("INPUT_CHANGED_DURING_REVIEW")
    output.mkdir(parents=True)
    def dump(name, value):
        with (output / name).open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    dump("case_reviews.json", [gsp, kpf])
    dump("gsp_chain.json", gsp_chain)
    dump("kpf_pdf_review.json", pdf_review)
    dump("scope_reclassification.json", scope_change)
    dump("verified_cached_documents.json", list(docs.values()))
    dump("source_discovery_receipts.json", discovery_receipts)
    dump("summary.json", summary)
    dump("approval_proposal.json", {"status": "MANUAL_REVIEW_REQUIRED", "owner_decision": None, "applied": False,
        "gsp_payload": gsp["vci_payload_sha256"], "gsp_record_date": "2021-08-23",
        "proposed_fields": gsp["observed_fields_for_owner_review"],
        "kpf_payload": kpf["vci_payload_sha256"], "kpf_status": "HOLD_CONTRADICTORY_NOTICE_DATE_LITERALS",
        "not_approved": ["PIT", "historical identity", "global rounding/source priority", "canonical freeze", "executed-event status"],
        "next_stage_proposal": "Consolidate existing field-selection evidence into an unsigned owner-review packet; keep KPF held without blocking other cases. No further source crawl or field application in this stage."})
    code = [Path(__file__), ROOT / "src/delta_t1/ingestion/corporate_action_decision_packet.py",
        ROOT / "src/delta_t1/ingestion/corporate_action_revision_review.py", ROOT / "scripts/collect_gsp_kpf_followup_v1.py"]
    dump("manifest.json", {"artifact_type": "gsp-kpf-followup-review-v1", "inputs_verified": inputs,
        "code_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in code},
        "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "formal_network_requests": len(stage_requests), "approved_fields": 0, "canonical_build": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output.resolve())
