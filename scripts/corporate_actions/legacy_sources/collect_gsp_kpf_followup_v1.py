"""Reuse one overlooked GSP cache article and acquire one exact public KPF PDF."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_sources import PublicTransport, SourceLimitation, now
from delta_t1.ingestion.corporate_action_decision_packet import inspect_history_document

CONFIG = ROOT / "configs/data/corporate_action_gsp_kpf_followup_v1.json"
sha = lambda body: hashlib.sha256(body).hexdigest()


class KpfNoticeTransport(PublicTransport):
    HOSTS = {"static2.vietstock.vn"}

    def __init__(self, output, config, **kwargs):
        if (config["max_requests"] != 1 or config["interval_seconds"] < 2
                or not config["tls_verification"] or config["follow_redirects"]
                or config["hnx_requests_allowed"] or config["canonical_build"]
                or config["automatic_field_approval"]):
            raise ValueError("ONE_PUBLIC_PDF_STRICT_ONLY")
        self.target_url = config["kpf_pdf"]
        super().__init__(output, max_requests=1, interval=config["interval_seconds"],
                         timeout=config["timeout_seconds"], max_bytes=config["max_bytes"], **kwargs)

    def fetch(self, url, payload=None, content_type="application/json", binary=False):
        if url != self.target_url or payload is not None or not binary:
            raise SourceLimitation("EXACT_PUBLIC_KPF_PDF_GET_ONLY")
        return super().fetch(url, binary=True)


def safe(base, name):
    relative = PureWindowsPath(name)
    if relative.drive or relative.root or ".." in relative.parts:
        raise ValueError("PATH_ESCAPE")
    return base.joinpath(*relative.parts)


def run(output, collect=False):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    inputs = {}
    def pin(path, expected=None):
        body = path.read_bytes()
        digest = sha(body)
        if expected and digest != expected:
            raise ValueError("INPUT_HASH_MISMATCH:" + str(path))
        inputs[path.relative_to(ROOT).as_posix()] = digest
        return body
    config = json.loads(pin(CONFIG))
    prior = ROOT / "tmp/ca_revision6_20261102_v3"
    pm = json.loads(pin(prior / "manifest.json", config["revision6_manifest_sha256"]))
    prior_docs = json.loads(pin(prior / "verified_documents.json", pm["files"]["verified_documents.json"]))
    cache = ROOT / "tmp/ca_cache_inventory_20261102_v4"
    cm = json.loads(pin(cache / "manifest.json", config["cache_manifest_sha256"]))
    index = pin(cache / "raw_document_index.jsonl", cm["files"]["raw_document_index.jsonl"])
    candidates = [d for d in (json.loads(l) for l in index.splitlines() if l.strip())
                  if d["source_url"] == "https://vsdc.vn/vi/ad/" + config["gsp_cached_provider_id"]]
    if len(candidates) != 1:
        raise ValueError("EXACT_ONE_CACHED_GSP_VERSION_REQUIRED")
    d = candidates[0]
    fresh = inspect_history_document(pin(safe(ROOT, d["raw_path"]), d["source_hash"]), d["source_url"])
    if fresh["ticker"] != "GSP" or fresh["record_dates"] != ["2021-08-23"]:
        raise ValueError("GSP_TARGET_MISMATCH")
    cached = fresh | {k: d[k] for k in ["document_id", "source_url", "source_hash", "raw_path"]}
    # Re-extract only the six documents for these two targets, never the entire
    # cache. The old sealed scope classification is preserved in prior output.
    selected = []
    for saved in prior_docs:
        if saved["title_ticker_hint"] not in {"GSP", "KPF"}:
            continue
        body = pin(safe(ROOT, saved["raw_path"]), saved["source_hash"])
        current = inspect_history_document(body, saved["source_url"])
        selected.append(current | {k: saved[k] for k in ["document_id", "source_url", "source_hash", "raw_path"]})
    if len(selected) != 5:
        raise ValueError("EXACT_FIVE_PRIOR_GSP_KPF_DOCUMENTS_REQUIRED")
    output.mkdir(parents=True)
    transport = KpfNoticeTransport(output, config)
    docs = []
    if collect:
        try:
            body, receipt = transport.fetch(config["kpf_pdf"], binary=True)
            docs.append({"status": "PUBLIC_PDF_RECEIVED", "receipt": receipt, "size_bytes": len(body),
                "source_role": "HOSE_AUTHORED_NOTICE_COPY_ON_MARKET_ARCHIVE_PENDING_VISUAL_REVIEW"})
        except SourceLimitation as exc:
            docs.append({"status": "SOURCE_STOP", "reason": str(exc)})
    def dump(name, value):
        with (output / name).open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    dump("cached_documents.json", [cached, *selected])
    dump("requests.json", transport.requests)
    dump("documents.json", docs)
    summary = {"stage": config["stage"], "status": "DOCUMENT_REVIEW_PENDING" if docs and docs[0]["status"] == "PUBLIC_PDF_RECEIVED" else "PARTIAL",
        "cached_documents_verified": 6, "overlooked_gsp_articles_recovered": 1,
        "network_request_attempts": len(transport.requests), "public_pdf_documents": sum(d["status"] == "PUBLIC_PDF_RECEIVED" for d in docs),
        "web_discovery_requests": "Separate uninstrumented search/open calls; not included in formal acquisition attempts.",
        "hnx_network_requests": 0, "accepted_fields": 0, "canonical_build": False,
        "review_status": "MANUAL_REVIEW_REQUIRED", "tls_verification": True, "follow_redirects": False}
    dump("summary.json", summary)
    for name, digest in inputs.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("INPUT_CHANGED")
    code = [Path(__file__), ROOT / "src/delta_t1/ingestion/corporate_action_decision_packet.py", ROOT / "src/delta_t1/ingestion/corporate_action_sources.py"]
    dump("manifest.json", {"artifact_type": "gsp-kpf-targeted-followup-v1", "created_at": now(), "inputs_verified": inputs,
        "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()},
        "code_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in code},
        "network_request_attempts": len(transport.requests), "canonical_build": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    run(args.output.resolve(), args.collect)
