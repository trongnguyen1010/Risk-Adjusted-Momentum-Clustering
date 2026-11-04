"""Build one offline, unsigned owner-review packet from five sealed artifacts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_owner_packet import assemble_case, digest, exact_ratio, owner_template, render_html
from delta_t1.ingestion.corporate_action_offline_reconcile import date_view

CONFIG = ROOT / "configs/data/corporate_action_owner_packet_v1.json"
sha = lambda body: hashlib.sha256(body).hexdigest()


def safe(base, name):
    relative = PureWindowsPath(name)
    if relative.drive or relative.root or ".." in relative.parts:
        raise ValueError("PATH_ESCAPE")
    return base.joinpath(*relative.parts)


def run(output):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    inputs = {}
    def pin(path, expected=None):
        body = path.read_bytes()
        actual = sha(body)
        if expected and actual != expected:
            raise ValueError("INPUT_HASH_MISMATCH:" + str(path))
        inputs[path.relative_to(ROOT).as_posix()] = actual
        return body
    config = json.loads(pin(CONFIG))
    if config["network_requests"] != 0 or config["automatic_field_approval"] or config["canonical_build"]:
        raise ValueError("UNSIGNED_OFFLINE_ONLY")
    manifests = {}
    for key, spec in config["inputs"].items():
        manifests[key] = json.loads(pin(safe(ROOT, spec["folder"]) / "manifest.json", spec["manifest_sha256"]))
    def data(key, name, jsonl=False):
        folder = safe(ROOT, config["inputs"][key]["folder"])
        body = pin(safe(folder, name), manifests[key]["files"][name])
        return [json.loads(l) for l in body.splitlines() if l.strip()] if jsonl else json.loads(body)
    reviewed = data("cached26", "reviewed_payloads_26.jsonl", True)
    parsed = {d["document_id"]: d for d in data("cached26", "reparsed_documents.jsonl", True)}
    requests = data("packet25", "decision_requests_25.jsonl", True)
    revisions = {r["vci_payload_sha256"]: r for r in data("revision6", "case_reviews.json")}
    followup = data("followup2", "case_reviews.json")
    # Later scoped evidence supersedes the review view, never the old artifact.
    for r in followup:
        payload = r["vci_payload_sha256"]
        if payload not in revisions or revisions[payload]["original_sdk_row"] != r["original_sdk_row"]:
            raise ValueError("FOLLOWUP_PAYLOAD_NOT_IN_REVISION_SCOPE")
        revisions[payload] = r
    primary = {r["vci_payload_sha256"]: r for r in data("primary2", "field_proposals.json")}
    documents = data("primary2", "documents_reviewed.json")
    revision_documents = data("revision6", "verified_documents.json")
    followup_documents = data("followup2", "verified_cached_documents.json")
    kpf_pdf = data("followup2", "kpf_pdf_review.json")
    by_payload = {r["vci_payload_sha256"]: r for r in reviewed}
    if len(by_payload) != 26 or len(requests) != 25 or len(revisions) != 6 or len(primary) != 2:
        raise ValueError("EXACT_REVIEW_COHORT_COUNTS_REQUIRED")
    for r in requests:
        prior = by_payload[r["vci_payload_sha256"]]
        if prior["original_sdk_row"] != r["original_sdk_row"] or prior["ticker"] != r["ticker"]:
            raise ValueError("SDK_PAYLOAD_OR_TICKER_DRIFT")
    additional = [r for payload, r in by_payload.items() if payload not in {p["vci_payload_sha256"] for p in requests}]
    if len(additional) != 1 or additional[0]["ticker"] != "ASG":
        raise ValueError("ASG_IS_ONLY_ADDITIONAL_CASE")
    asg = additional[0]
    if len(asg["candidate_sources"]) != 1:
        raise ValueError("ASG_UNIQUE_PRIMARY_CONTEXT_REQUIRED")
    candidate = asg["candidate_sources"][0]
    article = parsed[candidate["document_id"]]
    section = article["components"]["RIGHTS_ISSUE"]
    asg_source = {k: article[k] for k in ["document_id", "source_url", "source_hash", "raw_path"]}
    asg_source.update(ticker_record_supported=candidate["ticker_date_anchor_supported"],
        record_dates=article["record_dates"], price_vnd=candidate["candidate_price_vnd_pending_review"],
        primary_unit_explicit=candidate["primary_unit_explicit"], ratio_exact=candidate["source_ratio_exact"],
        component_heading=section["heading"], component_span={"start": section["start"], "end": section["end"]},
        primary_price_quotes=section["primary_prices"], ratio_evidence=section["ratio"])
    requests.append({"ticker": "ASG", "vci_payload_sha256": asg["vci_payload_sha256"],
        "original_sdk_row": asg["original_sdk_row"], "original_record_date_review_view": date_view(asg["original_sdk_row"]["record_date"]),
        "decision_class": "PRIMARY_UNIT_DOCUMENT_PROPOSAL", "sources": [asg_source],
        "observed_price_vnd": candidate["candidate_price_vnd_pending_review"], "owner_decision": None,
        "canonical_written": False, "signature_created": False})
    cases = []
    for r in requests:
        payload = r["vci_payload_sha256"]
        p = primary.get(payload)
        source_docs = [documents[key] for key in p["source_documents"]] if p else []
        cases.append(assemble_case(r, revisions.get(payload), p, source_docs))
    cases.sort(key=lambda c: (c["group"], c["ticker"], c["record_date_review_view"], c["case_id"]))
    if {c["vci_payload_sha256"] for c in cases} != set(by_payload):
        raise ValueError("NO_COHORT_DROP_OR_ADDITION_ALLOWED")
    prices = [f for c in cases for f in c["proposed_fields"] if f["field"] == "rights_subscription_price"]
    ratios = [f for c in cases for f in c["proposed_fields"] if f["field"] == "rights_ratio"]
    held = [c for c in cases if c["held_fields"]]
    if len(prices) != 25 or len(ratios) != 20 or len(held) != 1 or held[0]["ticker"] != "KPF":
        raise ValueError("EXACT_OWNER_REVIEW_FIELD_COUNTS_REQUIRED")
    catalog = {}
    def add_evidence(identifier, evidence):
        if identifier in catalog and catalog[identifier] != evidence:
            raise ValueError("EVIDENCE_ID_COLLISION")
        catalog[identifier] = evidence
    for c in cases:
        for s in c["source_evidence"]:
            pin(safe(ROOT, s["raw_path"]), s["source_hash"])
            add_evidence(s["document_id"], {"type": "VSDC_ARTICLE", **s})
        for d in c["primary_document_evidence"]:
            pin(safe(ROOT, d["raw_path"]), d["raw_sha256"])
            add_evidence(d["id"], {"type": "PRIMARY_DOCUMENT_COPY_ALREADY_VISUALLY_REVIEWED", **d})
        revision = c["revision_review"]
        if revision:
            for edge in revision["edges"]:
                for key in ["previous_source_url", "revision_source_url"]:
                    url = edge[key]
                    all_docs = followup_documents if c["ticker"] in {"GSP", "KPF"} else revision_documents
                    matched = [d for d in all_docs if d["source_url"] == url]
                    if len(matched) != 1:
                        raise ValueError("UNIQUE_REVISION_DOCUMENT_REQUIRED")
                    d = matched[0]
                    pin(safe(ROOT, d["raw_path"]), d["source_hash"])
                    # Preserve the full cached article text for quote verification.
                    add_evidence("history:" + d["document_id"], {"type": "CACHED_REVISION_CONTEXT", **d})
    pin(safe(ROOT, kpf_pdf["pdf_path"]), kpf_pdf["pdf_sha256"])
    summary = {"stage": config["stage"], "technical_status": "PASS", "decision_status": "MANUAL_REVIEW_REQUIRED",
        "c8_v2_inventory": 1522, "payload_count": len(cases), "ticker_count": len({c["ticker"] for c in cases}),
        "count_unit": "Distinct VCI SDK payload, not canonical economic event or full dataset",
        "proposed_case_count": 25, "proposed_field_count": len(prices) + len(ratios),
        "price_proposals": len(prices), "case_specific_ratio_proposals": len(ratios),
        "held_case_count": len(held), "held_field_count": sum(len(c["held_fields"]) for c in cases),
        "group_counts": dict(Counter(c["group"] for c in cases)), "input_sealed_artifacts": len(manifests),
        "approved_fields_before_after": [0, 0], "applied_fields": 0, "canonical_rows_written": 0,
        "network_requests": 0, "signature_created": False, "importable_as_production_decisions": False,
        "pit_status": "NOT_PROMOTED", "historical_identity": "UNVERIFIED", "research_readiness_promoted": False,
        "stopped_sources_preserved": ["HNX", "www.kpf.com.vn"],
        "next_step": "Owner review of this exact packet and field choices; subsequent approved reconciliation preview only after explicit owner decisions. KPF remains HOLD."}
    for key in ["payload_count", "proposed_case_count", "proposed_field_count", "held_case_count", "held_field_count"]:
        if summary[key] != config[key]:
            raise ValueError("CONFIGURED_SCOPE_COUNT_MISMATCH:" + key)
    packet_id = digest({"cases": cases, "input_manifests": {k: spec["manifest_sha256"] for k, spec in config["inputs"].items()}})
    packet = {"artifact_type": "unsigned-corporate-action-owner-packet26-v1", "packet_content_id": packet_id,
        "status": "MANUAL_REVIEW_REQUIRED", "owner_decision": None, "applied": False,
        "approval_scope": "Only the listed observed price and case-specific ratio choices; no provider-wide transformation, PIT, identity, final freeze, price basis or backtest approval.",
        "cases": cases}
    for name, value in inputs.items():
        if sha((ROOT / name).read_bytes()) != value:
            raise ValueError("INPUT_CHANGED_DURING_ASSEMBLY")
    output.mkdir(parents=True)
    def dump(name, value):
        with (output / name).open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    dump("owner_packet.json", packet)
    dump("owner_review_template.json", owner_template(cases, packet_id))
    dump("evidence_catalog.json", catalog)
    dump("held_cases.json", {"KPF": held[0], "corroborating_hose62_pdf": kpf_pdf, "source_stop_preserved": True})
    dump("summary.json", summary)
    (output / "approval_review.html").write_text(render_html(cases, summary, packet_id), encoding="utf-8")
    code = [Path(__file__), ROOT / "src/delta_t1/ingestion/corporate_action_owner_packet.py"]
    dump("manifest.json", {"artifact_type": "corporate-action-consolidated-owner-review-v1", "packet_content_id": packet_id,
        "inputs_verified": inputs, "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "code_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in code},
        "network_requests": 0, "approved_fields": 0, "canonical_build": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output.resolve())
