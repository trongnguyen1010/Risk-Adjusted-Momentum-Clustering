"""Khắc phục parser trên bốn cached articles; không acquisition hoặc approve fields."""
from collections import Counter
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_components import parse_details_v2, VERSION
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, rows, write, hashes
from delta_t1.ingestion.corporate_action_sources import sha
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact
from delta_t1.ingestion.hnx_detail_parser import parse_details


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8")
    config_path = ROOT / "configs/data/corporate_actions/hnx_cached_parser_remediation_v2.json"
    config = read(config_path)
    if (config["network_requests"] != 0 or config["canonical_build"] is not False
            or config["automatic_field_approval"] is not False or config["parser_version"] != VERSION):
        raise ValueError("OFFLINE_REVIEW_ONLY_CONTRACT_REQUIRED")
    state, out, archive, review = [ROOT / config[key] for key in ("input_state", "output", "input_zip", "input_review")]
    if (out / "result.json").exists():
        raise FileExistsError("REFUSE_OVERWRITE_IMMUTABLE_REPARSE")
    origin = verify_artifact(state, {"hnx-local-supplement10-state-v1"})
    verify_artifact(review)
    zip_hash = sha(archive.read_bytes())
    if zip_hash != read(review / "audit.json")["input_zip_sha256"]:
        raise ValueError("ORIGINAL_ZIP_CHANGED")
    checkpoint = read(state / "checkpoint.json")
    assert checkpoint["source_stopped"] and checkpoint["resumable"] is False
    checkpoint_hash = sha((state / "checkpoint.json").read_bytes())
    before_sources = read(out / "before_hashes.json")
    for name, digest in before_sources.items():
        assert sha((out / "source_before" / name).read_bytes()) == digest
    inputs = list(state.glob("work/*/detail-*"))
    if sorted(d.name.removeprefix("detail-") for d in inputs) != config["article_ids"]:
        raise ValueError("EXACT_FOUR_CACHED_ARTICLES_REQUIRED")
    results, all_new, queue = [], [], []
    for detail in sorted(inputs):
        aid = detail.name.removeprefix("detail-")
        old_path = detail.with_name("parsed-" + aid)
        # Legacy default must remain byte-equivalent for observations/reviews.
        old_result = parse_details(detail, out / "legacy_replay" / aid)
        assert old_result == read(old_path / "result.json")
        for filename in ("observations.jsonl", "review_queue.csv"):
            assert (out / "legacy_replay" / aid / filename).read_bytes() == (old_path / filename).read_bytes()
        new_path = out / "reparsed_v2" / aid
        new_result = parse_details_v2(detail, new_path)
        old_obs, new_obs = rows(old_path / "observations.jsonl"), rows(new_path / "observations.jsonl")
        assert len(old_obs) == 1
        for obs in new_obs:
            assert obs["source_evidence"] == old_obs[0]["source_evidence"]
            assert obs["source_hash"] == old_obs[0]["source_hash"]
            assert obs["observed_at"] == old_obs[0]["observed_at"]
            assert obs["event_reference"] == old_obs[0]["event_reference"]
            assert obs["source_published_at"] is None and obs["source_timing"]["timezone"] is None
            for reason in ("SOURCE_PUBLIC_TIME_UNVERIFIED", "HISTORICAL_IDENTITY_NOT_CERTIFIED"):
                assert reason in obs["parser_issues"]
        if aid in {"497771", "575367"}:
            assert new_obs[0]["fields"] == old_obs[0]["fields"]
            assert new_obs[0]["observation_id"] == old_obs[0]["observation_id"]
        with (new_path / "review_queue.csv").open(encoding="utf-8", newline="") as stream:
            queue.extend(csv.DictReader(stream))
        all_new.extend(new_obs)
        results.append({"article_id": aid, "before": old_result, "after": new_result})
    assert len(all_new) == 5 and len({o["observation_id"] for o in all_new}) == 5
    def val(obs): return {k: v["normalized_value"] for k, v in obs["fields"].items()}
    stock = next(o for o in all_new if o["source_timing"]["provider_article_id"] == "523090")
    assert val(stock)["stock_dividend_ratio"] == .08
    mbs = [o for o in all_new if o["source_timing"]["provider_article_id"] == "581051"]
    bonus = next(o for o in mbs if val(o)["event_type"] == "BONUS_SHARE")
    rights = next(o for o in mbs if val(o)["event_type"] == "RIGHTS_ISSUE")
    assert val(bonus)["bonus_ratio"] == .03 and "rights_subscription_price" not in bonus["fields"]
    assert val(rights)["rights_ratio"] == .12 and val(rights)["rights_subscription_price"] == 10000
    assert "bonus_ratio" not in rights["fields"]
    assert all(r["after"]["extraction_gate"] == "PASS_FOR_INPUT_ARTICLES" for r in results)
    assert sha(archive.read_bytes()) == zip_hash and sha((state / "checkpoint.json").read_bytes()) == checkpoint_hash
    verify_artifact(state)
    runtime_files = [Path(__file__), config_path, ROOT / "src/delta_t1/ingestion/corporate_actions/hnx_components.py",
        ROOT / "src/delta_t1/ingestion/hnx_detail_parser.py", ROOT / "src/delta_t1/ingestion/hnx_announcement_parser.py"]
    result = {"stage": config["stage"], "status": "PASS_OFFLINE_PARSER_REMEDIATION_SOURCE_TIMEOUT_UNRESOLVED",
        "network_requests": 0, "input_zip_sha256": zip_hash, "origin": origin,
        "original_checkpoint_sha256": checkpoint_hash, "original_checkpoint_resumable": False,
        "timeout_diagnosis": {"request": "VTZ profile GET", "phase": "RESPONSE_BODY_READ",
            "http_headers_status": 200, "error_category": "REQUEST_TIMEOUT", "configured_timeout_seconds": 15,
            "complete_body_saved": False, "http_401_403_429_observed": False,
            "root_external_cause": "UNDETERMINED_FROM_EXISTING_LOGS",
            "remedy": "Preserve STOP/no auto retry; no timeout increase or live health claim"},
        "parser_causes": {"TNG_523090": "Legacy allocation regex omits optional word them before quantity",
            "MBS_581051": "Legacy single-type parser maps mixed bonus+rights to OTHER without component boundaries"},
        "before_after": {"detail_articles": [4, 4], "observations": [4, 5],
            "extraction_pass_articles": [2, 4], "review_rows": [14, len(queue)],
            "selected_missing_field_tasks_not_approved": [25, 25], "canonical_fields_applied": [0, 0]},
        "review_severity_counts": dict(Counter(r["severity"] for r in queue)),
        "articles": results, "limits": ["Five source components are not five new canonical events",
            "TNG stock dividend 8% is not the selected rights issue 10%", "MBS candidate price still requires owner field/event review",
            "PIT/historical identity/source selection/final freeze MANUAL_REVIEW_REQUIRED; 45 choices unchanged",
            "Acquisition remains STOPPED; old frozen runner runtime pins are stale after source change"],
        "runtime_hashes": {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in runtime_files}}
    write(out / "config.json", config)
    write(out / "result.json", result)
    print(json.dumps({"status": result["status"], "before_after": result["before_after"],
        "reviews": result["review_severity_counts"], "output": str(out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
