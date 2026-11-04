"""Freeze offline source contract/cache IDs for two-request VSDC MBS pilot."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.vsdc_mbs_pilot import CONFIG, validate, source_contract, page, runtime
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, rows, write, hashes
from delta_t1.ingestion.corporate_action_sources import sha
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact


def main():
    config = read(ROOT / CONFIG);validate(config)
    out = ROOT / config["preparation"]
    if out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    audit = ROOT / config["scope_audit"]
    if sha((audit / "manifest.json").read_bytes()) != config["scope_audit_manifest_sha256"]:
        raise ValueError("SCOPE_AUDIT_CHANGED")
    verify_artifact(audit)
    cache = ROOT / config["cache"]
    if sha((cache / "manifest.json").read_bytes()) != config["cache_manifest_sha256"]:
        raise ValueError("CACHE_MANIFEST_CHANGED")
    index = cache / "raw_document_index.jsonl"
    if sha(index.read_bytes()) != read(cache / "manifest.json")["files"][index.name]:
        raise ValueError("RAW_CACHE_INDEX_CHANGED")
    ids = sorted({r["provider_article_id"] for r in rows(index)})
    if len(ids) != read(audit / "summary.json")["global_cached_article_ids"]:
        raise ValueError("AUDITED_CACHE_ID_COUNT_CHANGED")
    raw = ROOT / config["archived_page1"]
    if sha(raw.read_bytes()) != config["archived_page1_sha256"]: raise ValueError("ARCHIVED_QUERY_CHANGED")
    html = raw.read_bytes().decode("utf-8-sig")
    contract = source_contract(html)
    first = page(html, 1)
    if first["coverage"]["reported_total"] != 63 or len(first["article_ids"]) != 20:
        raise ValueError("ARCHIVED_MBS_QUERY_CONTEXT_CHANGED")
    protected = {}
    for rel in ["tmp/ca_c8_v2_checkpoint_20261101_v5/resume_state.json", *[
        f"data/corporate_actions/work/outputs/batch_shard_{i}/resume_state.json" for i in range(4)]]:
        state = read(ROOT / rel)
        if "vsdc.vn" not in state["deferred_post_hosts"]: raise ValueError("OLD_DEFERRED_GUARD_CHANGED")
        protected[rel] = sha((ROOT / rel).read_bytes())
    rel = "data/corporate_actions/work/hnx_local_supplement10_v1/run-20261103T025523779036Z/state/checkpoint.json"
    state = read(ROOT / rel)
    if state["resumable"] is not False or not state["source_stopped"]:
        raise ValueError("HNX_SOURCE_STOP_CHANGED")
    protected[rel] = sha((ROOT / rel).read_bytes())
    canonical = ROOT / config["canonical"]
    if sha(canonical.read_bytes()) != config["canonical_sha256"] or len(rows(canonical)) != 1522:
        raise ValueError("C8_V2_CHANGED")
    out.mkdir(parents=True)
    write(out / "plan.json", {"config": config, "status": "PREPARED_NOT_EXECUTED", "network_requests": 0,
        "archived_page1_articles": 20, "archived_reported_total": 63, "cached_provider_article_ids": len(ids),
        "live_protocol_ready": False, "new_run_does_not_resume_or_remove_old_deferred_guard": True})
    write(out / "source_contract.json", {**contract, "source_path": config["archived_page1"],
        "source_sha256": config["archived_page1_sha256"], "post_body_utf8": '{"SearchKey":4,"CurrentPage":2}',
        "post_content_type": config["post_content_type"],
        "difference_from_legacy_request": "Observed JS uses compact JSON and explicit charset; not a proven cause/fix of archived HTTP400",
        "fresh_GET_must_revalidate_before_POST": True})
    write(out / "cached_article_ids.json", ids)
    write(out / "protected_old_files.json", protected)
    write(out / "runtime.json", runtime(ROOT))
    write(out / "manifest.json", {"artifact_type": "vsdc-mbs-pagination-preparation-v1", "files": hashes(out)})
    print(json.dumps({"output": str(out), "status": "PREPARED_NOT_EXECUTED", "network_requests": 0,
        "max_requests_user_run": 2, "protected_old_states": len(protected), "cached_article_ids": len(ids)}, ensure_ascii=False))


if __name__ == "__main__": main()
