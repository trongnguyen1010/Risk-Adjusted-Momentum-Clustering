"""Review six cached original/revision chains, without acquisition or application."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_decision_packet import inspect_history_document
from delta_t1.ingestion.corporate_action_revision_review import review_case

BASE = ROOT / "tmp/ca_decision25_20261102_v2"
CONFIG = ROOT / "configs/data/corporate_action_revision6_v1.json"
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
        digest = sha(body)
        if expected and digest != expected:
            raise ValueError(f"INPUT_HASH_MISMATCH: {path}")
        inputs[path.relative_to(ROOT).as_posix()] = digest
        return body
    config = json.loads(pin(CONFIG))
    if config["network_requests"] != 0 or config["canonical_build"] or config["automatic_approval"]:
        raise ValueError("OFFLINE_UNSIGNED_ONLY")
    manifest = json.loads(pin(BASE / "manifest.json", config["packet_manifest_sha256"]))
    files = {name: pin(safe(BASE, name), digest) for name, digest in manifest["files"].items()}
    requests = [json.loads(l) for l in files["decision_requests_25.jsonl"].splitlines() if l.strip()]
    requests = {(r["ticker"], r["original_record_date_review_view"]): r for r in requests if r["decision_class"] == "HOLD_LINKED_CHANGE_REVIEW"}
    cases = config["cases"]
    if len(cases) != 6 or set(requests) != {(c["ticker"], c["record_date"]) for c in cases}:
        raise ValueError("EXACT_SIX_CASE_SCOPE_REQUIRED")
    history = [json.loads(l) for l in files["cached_history_evidence.jsonl"].splitlines() if l.strip()]
    wanted = {p for c in cases for p in [c["original"], *c["revisions"]]}
    documents = {}
    for saved in history:
        if saved["provider_article_id"] not in wanted:
            continue
        raw = pin(safe(ROOT, saved["raw_path"]), saved["source_hash"])
        fresh = inspect_history_document(raw, saved["source_url"])
        if any(fresh[k] != saved[k] for k in fresh):
            raise ValueError("SAVED_REVIEW_NO_LONGER_REPRODUCES")
        if saved["provider_article_id"] in documents:
            raise ValueError("AMBIGUOUS_PROVIDER_RESPONSE_VERSION")
        documents[saved["provider_article_id"]] = saved
    if set(documents) != wanted or len(wanted) != 14:
        raise ValueError("EXACT_FOURTEEN_RAW_DOCUMENTS_REQUIRED")
    results = []
    for case in cases:
        request = requests[case["ticker"], case["record_date"]]
        original = documents[case["original"]]
        if {s["document_id"] for s in request["sources"]} != {original["document_id"]}:
            raise ValueError("ORIGINAL_SOURCE_MISMATCH")
        expected_changes = {h["document_id"] for h in request["cached_history_checks"] if h["revision_or_cancellation_candidate"]}
        if expected_changes != {documents[p]["document_id"] for p in case["revisions"]}:
            raise ValueError("REVISION_SET_MISMATCH")
        results.append(review_case(request, original, [documents[p] for p in case["revisions"]]))
    counts = Counter(r["status"] for r in results)
    summary = {"stage": config["stage"], "technical_status": "PASS", "decision_status": "MANUAL_REVIEW_REQUIRED",
        "data_resolution_status": "PARTIAL", "c8_v2_inventory": 1522,
        "reviewed_payloads": 6, "reviewed_tickers": 6, "raw_response_versions_verified": 14,
        "original_documents": 6, "revision_documents": 8,
        "case_status_counts": dict(counts),
        "context_supported_revision_edges": sum(e["contextual_link_supported"] for r in results for e in r["edges"]),
        "total_reviewed_edges": 8,
        "field_requests_context_supported": sum(len(r["observed_fields_for_owner_review"]) for r in results if r["status"].startswith("CONTEXTUAL_")),
        "field_requests_held": sum(len(r["observed_fields_for_owner_review"]) for r in results if r["status"].startswith("HOLD_")),
        "approved_fields_before_after": [0, 0], "applied_field_changes": 0,
        "network_requests": 0, "canonical_rows_written": 0,
        "official_notice_bindings_verified": 0, "terminal_execution_confirmed": 0,
        "pit_status": "NOT_PROMOTED", "historical_identity": "UNVERIFIED",
        "limitations": ["Context links and unchanged clauses support owner review only; no signed notice number binding is certified.",
            "GSP original schedule differs from predecessor 1203 referenced by cached extension; chain remains incomplete.",
            "KPF notice44 has conflicting date literals 07/01/2021 and 08/01/2021; neither is corrected automatically.",
            "No full archive, later revisions, publication PIT, or offering execution completeness claim."]}
    followups = [
        {"ticker": "GSP", "record_date": "2021-08-23", "needed": "Thông báo1203/TB-CNVSD ngày01/09/2021 và mắt xích nối lịch16/09–20/09 sang12/10–15/10; đối chiếu original143831, revision145371/145572.", "download_url": None},
        {"ticker": "KPF", "record_date": "2021-01-20", "needed": "Bản gốc thông báo44/TB-VSD hoặc evidence issuer/VSDC xác nhận ngày; giữ cả07/01/2021 và08/01/2021 cho đến khi có chứng từ.", "download_url": None},
    ]
    for name, digest in inputs.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("INPUT_CHANGED_DURING_REVIEW")
    output.mkdir(parents=True)
    def dump(name, value):
        with (output / name).open("x", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
    dump("case_reviews.json", results)
    dump("summary.json", summary)
    dump("verified_documents.json", list(documents.values()))
    dump("followup_evidence_requests.json", {"network_requests": 0, "requests": followups})
    dump("approval_proposal.json", {"status": "MANUAL_REVIEW_REQUIRED", "owner_decision": None, "applied": False,
        "context_supported_cases": [{"ticker": r["ticker"], "record_date": r["record_date_review_view"], "payload": r["vci_payload_sha256"], "fields": r["observed_fields_for_owner_review"]} for r in results if r["status"].startswith("CONTEXTUAL_")],
        "held_cases": [r["ticker"] for r in results if r["status"].startswith("HOLD_")],
        "scope": "Case-specific observed price/ratio proposals only, not approval of PIT/identity/provider transformation or canonical freeze."})
    code = [Path(__file__), ROOT / "src/delta_t1/ingestion/corporate_action_revision_review.py"]
    dump("manifest.json", {"artifact_type": "corporate-action-cached-revision6-v1", "inputs_verified": inputs,
        "code_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in code},
        "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "network_requests": 0, "canonical_build": False, "approved_fields": 0})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output.resolve())
