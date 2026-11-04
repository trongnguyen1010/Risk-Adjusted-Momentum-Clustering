"""Đối chiếu offline năm HNX components với archived SDK và missing queue."""
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, rows, write, hashes
from delta_t1.ingestion.corporate_actions.hnx_queue_review import (
    review_observations, field_queue, price_proposal, disposition_counts, PENDING, MISSING,
)
from delta_t1.ingestion.corporate_action_offline_reconcile import key, valid_fields
from delta_t1.ingestion.corporate_action_sources import sha, Document
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact


def jsonl(path, values):
    with path.open("x", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8")
    config_path = ROOT / "configs/data/corporate_actions/hnx_component_queue_review_v1.json"
    config = read(config_path)
    if (config["network_requests"] != 0 or config["canonical_build"] is not False
            or config["automatic_field_approval"] is not False or config["tickers"] != ["MBS", "TNG"]):
        raise ValueError("EXACT_OFFLINE_REVIEW_SCOPE_REQUIRED")
    output = ROOT / config["output"]
    if output.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    inputs, directories = {}, {}
    for name, definition in config["input_directories"].items():
        path = ROOT / definition["path"]
        digest = sha((path / "manifest.json").read_bytes())
        if digest != definition["manifest_sha256"]: raise ValueError("INPUT_MANIFEST_CHANGED: " + name)
        verify_artifact(path)
        inputs[name] = {"path": str(path), "manifest_sha256": digest}
        directories[name] = path
    state = directories["state"]
    checkpoint_hash = sha((state / "checkpoint.json").read_bytes())
    checkpoint = read(state / "checkpoint.json")
    if checkpoint["resumable"] is not False or not checkpoint["source_stopped"]:
        raise ValueError("SOURCE_STOP_MUST_REMAIN_UNCHANGED")
    archive = ROOT / config["vci_zip"]
    if sha(archive.read_bytes()) != config["vci_zip_sha256"]: raise ValueError("VCI_ARCHIVE_CHANGED")
    sdk, occurrences, export_hashes = {}, defaultdict(list), {}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)): raise ValueError("DUPLICATE_ZIP_MEMBER")
        manifest = json.loads(z.read("manifest.json"))
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
                raise ValueError("UNSAFE_ZIP_MEMBER")
            if not name.endswith("/sdk_export.json"): continue
            body = z.read(name)
            if sha(body) != manifest["files"][name]: raise ValueError("SDK_EXPORT_CHANGED")
            export_hashes[name] = sha(body)
            for index, row in enumerate(json.loads(body)):
                if row["symbol"] not in config["tickers"]: continue
                digest = key(row)
                sdk[digest] = row
                occurrences[digest].append({"member": name, "row_index": index})
    observations, locations, raw_proofs = [], {}, {}
    components = directories["components"]
    if sorted(p.name for p in (components / "reparsed_v2").iterdir()) != config["article_ids"]:
        raise ValueError("EXACT_FOUR_ARTICLE_INPUTS_REQUIRED")
    canonical_path = ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl"
    plan = read(state / "plan.json")
    if sha(canonical_path.read_bytes()) != plan["canonical_sha256"]: raise ValueError("C8_CHANGED")
    scope = {r["ticker"]: r for r in rows(canonical_path)}
    for aid in config["article_ids"]:
        folder = components / "reparsed_v2" / aid
        verify_artifact(folder)
        if read(folder / "result.json")["extraction_gate"] != "PASS_FOR_INPUT_ARTICLES":
            raise ValueError("INPUT_EXTRACTION_REVIEW_REQUIRED")
        for index, observation in enumerate(rows(folder / "observations.jsonl"), 1):
            values = valid_fields(observation)
            if values["ticker"] not in config["tickers"] or scope[values["ticker"]]["exchange"] != values["exchange"]:
                raise ValueError("OBSERVATION_OUTSIDE_C8_SCOPE")
            for receipt in observation["source_evidence"]:
                raw = (folder / receipt["path"]).resolve()
                if not raw.is_relative_to(folder.resolve()) or sha(raw.read_bytes()) != receipt["source_hash"]:
                    raise ValueError("SOURCE_RAW_CHANGED")
                raw_proofs[receipt["source_hash"]] = {"path": str(raw), "sha256": receipt["source_hash"]}
            if observation["source_published_at"] is not None:
                raise ValueError("PIT_NOT_APPROVED")
            observations.append(observation)
            locations[observation["observation_id"]] = {"path": str(folder / "observations.jsonl"), "line": index}
    if len(observations) != config["expected_observations"] or len(locations) != 5:
        raise ValueError("EXACT_FIVE_COMPONENTS_REQUIRED")
    queue = rows(directories["queue"] / "missing_event_fields_602.jsonl")
    preview = {r["vci_payload_sha256"]: r for r in rows(directories["prior_preview"] / "reconciliation_candidates.jsonl")}
    owner = read(directories["owner_packet"] / "owner_packet.json")
    owner_summary = read(directories["owner_packet"] / "summary.json")
    reviews = review_observations(observations, list(sdk.values()), {r["vci_payload_sha256"] for r in queue})
    updated, tasks = field_queue(queue, observations, reviews)
    by_id = {o["observation_id"]: o for o in observations}
    queue_index = {r["vci_payload_sha256"]: r for r in queue}
    proposals = []
    for task in tasks:
        if task["status"] != PENDING: continue
        obs_id, = {c["observation_id"] for c in task["candidates"]}
        obs = by_id[obs_id]
        proposal = price_proposal(task, obs, locations[obs_id], queue_index[task["vci_payload_sha256"]]["original_sdk_row"])
        proposal["original_sdk_row"] = deepcopy(sdk[task["vci_payload_sha256"]])
        proposal["vci_occurrences"] = occurrences[task["vci_payload_sha256"]]
        proposal["original_queue_fields_unchanged"] = queue_index[task["vci_payload_sha256"]]["missing_fields"]
        proposal["already_in_owner_packet45"] = any(c["vci_payload_sha256"] == task["vci_payload_sha256"] for c in owner["cases"])
        proposals.append(proposal)
    selected = {t["queue_payload_sha256"] for t in plan["targets"]}
    selected_tasks = [t for t in tasks if t["vci_payload_sha256"] in selected]
    for original, changed in zip(queue, updated):
        if {k: v for k, v in changed.items() if k != "scoped_hnx_review_v2"} != original:
            raise ValueError("ORIGINAL_QUEUE_VALUES_CHANGED")
    for review in reviews:
        for digest in review["candidate_payload_hashes"]:
            review.setdefault("counterpart_context", []).append({"vci_payload_sha256": digest,
                "vci_occurrences": occurrences[digest], "in_selected_ten_payloads": digest in selected,
                "in_missing_queue": digest in queue_index,
                "prior_preview": preview.get(digest), "original_sdk_row": sdk[digest]})
    # Verify the primary unit quote directly against the saved response bytes.
    for proposal in proposals:
        evidence = proposal["evidence"]
        raw = next(r for r in evidence["source_evidence"] if r.get("evidence_role") == "detail")
        obs = by_id[evidence["observation_id"]]
        folder = Path(locations[obs["observation_id"]]["path"]).parent
        text = Document((folder / raw["path"]).read_bytes().decode("utf-8-sig")).root.text()
        if any(quote not in text for quote in evidence["primary_price_quotes"]):
            raise ValueError("PRIMARY_PRICE_QUOTE_NOT_IN_RAW")
    if (len(reviews) != 5 or any(r["status"] != "UNIQUE_PAYLOAD_COUNTERPART_CANDIDATE" for r in reviews)
            or len(proposals) != 1 or proposals[0]["ticker"] != "MBS"
            or proposals[0]["already_in_owner_packet45"] or len(tasks) != 1373 or len(queue) != 602
            or len(selected_tasks) != 25 or len(sdk) != 56):
        raise ValueError("FROZEN_REAL_EVIDENCE_COUNTS_REQUIRE_REVIEW")
    summary = {"stage": config["stage"], "technical_status": "PASS_OFFLINE_REVIEW",
        "decision_status": "MANUAL_REVIEW_REQUIRED", "network_requests": 0,
        "vci_scope_distinct_payloads": len(sdk), "vci_scope_occurrences": sum(map(len, occurrences.values())),
        "sdk_exports_hash_verified": len(export_hashes), "input_component_observations": len(observations),
        "unique_counterpart_candidates": 5, "counterparts_in_missing_queue": 1,
        "counterparts_already_complete_for_queue_fields": 4,
        "queue_payloads_before_after": [602, len(updated)], "queue_missing_fields_before_after": [1373, len(tasks)],
        "review_dispositions": disposition_counts(tasks), "selected_25_dispositions": disposition_counts(selected_tasks),
        "new_unsigned_price_choices": 1, "old_owner_choices_unchanged": owner_summary["proposed_field_count"],
        "approved_fields": 0, "applied_fields": 0, "canonical_rows_written": 0,
        "source_stop_preserved": True, "raw_response_hashes_verified": len(raw_proofs),
        "pit_promoted": False, "historical_identity_certified": False,
        "next_stage_proposal": "Owner review of the one MBS price proposal; any VTZ diagnostic requires separately scoped authorization; do not resume source STOP"}
    output.mkdir(parents=True, exist_ok=False)
    jsonl(output / "observation_payload_review.jsonl", reviews)
    jsonl(output / "missing_event_fields_review_v2.jsonl", updated)
    jsonl(output / "field_tasks_review_v2.jsonl", tasks)
    jsonl(output / "selected_25_field_tasks_review_v2.jsonl", selected_tasks)
    jsonl(output / "unsigned_mbs_price_proposal.jsonl", proposals)
    jsonl(output / "scoped_sdk_payloads.jsonl", [{"vci_payload_sha256": digest, "original_sdk_row": row,
        "occurrences": occurrences[digest]} for digest, row in sorted(sdk.items())])
    write(output / "config.json", config)
    write(output / "inputs.json", {"directories": inputs, "vci_zip": {"path": str(archive), "sha256": config["vci_zip_sha256"],
        "export_hashes": export_hashes}, "raw_proofs": raw_proofs, "checkpoint_sha256": checkpoint_hash})
    write(output / "summary.json", summary)
    if sha((state / "checkpoint.json").read_bytes()) != checkpoint_hash: raise ValueError("CHECKPOINT_CHANGED")
    write(output / "runtime.json", {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [Path(__file__), config_path,
        ROOT / "src/delta_t1/ingestion/corporate_actions/hnx_queue_review.py",
        ROOT / "src/delta_t1/ingestion/corporate_action_offline_reconcile.py",
        ROOT / "src/delta_t1/ingestion/corporate_action_owner_packet.py"]})
    write(output / "manifest.json", {"artifact_type": "hnx-component-queue-offline-review-v1", "files": hashes(output)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
