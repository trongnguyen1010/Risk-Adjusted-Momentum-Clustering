"""VCI/VSDC/HNX/HOSE archived facts -> provisional reconciliation preview; 0 network."""
import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_offline_reconcile import (
    KINDS, key, date_view, category, fact, reconcile_row,
)
from delta_t1.ingestion.vci_calendar_monthly import verify_state, validate_inputs

VCI = ROOT / "data/corporate_actions/work/vci_local_v1/delta-vci-state-local-20261102T024517019426Z.zip"
VCI_SHA = "ce415731d69d46284c99a7b97dcd9b77d8405fd3d667d8ece5ad22e9f49f2eac"
VSDC = ROOT / "tmp/ca_vsdc_reparse_20261101_v3"
VSDC_SHA = "99db3a52868c3996d528756d93356200c7377be2767993749cc3a1832625154c"
BOOTSTRAP = ROOT / "tmp/ca_c8_v2_checkpoint_20261101_v5"


def sha(body):
    return hashlib.sha256(body).hexdigest()


def dump(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def lines(body):
    return [json.loads(line) for line in body.decode("utf-8").splitlines() if line.strip()]


def run(output):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    config = json.loads((ROOT / "configs/data/corporate_actions_offline_reconcile_v1.json").read_text(encoding="utf-8"))
    if (config["automatic_field_approval"] or config["canonical_build"] or config["time_hint_window_days"] != 120
            or set(config["event_types"]) != set(KINDS) or config["vci_date_view_timezone"] != "+07:00"
            or config["numeric_comparison_quantum"] != "0.0000000001"):
        raise ValueError("PREVIEW_POLICY_MISMATCH")
    inputs, raw_index = {}, defaultdict(list)

    def verified_read(path, expected=None):
        body = path.read_bytes()
        digest = sha(body)
        if expected is not None and digest != expected:
            raise ValueError("INPUT_HASH_MISMATCH: " + str(path))
        inputs[str(path)] = {"sha256": digest, "bytes": len(body)}
        return body

    vci_files = verify_state(VCI)
    verified_read(VCI, VCI_SHA)
    plan, scope, gate = [json.loads(vci_files[n]) for n in ("plan.json", "scope.json", "pilot_gate.json")]
    validate_inputs(plan, scope, gate)
    securities = {s["ticker"]: s for s in scope["securities"]}
    vci_by_hash = {}
    vci_refs = defaultdict(list)
    for name in sorted(vci_files):
        if name.endswith("/sdk_export.json"):
            for index, row in enumerate(json.loads(vci_files[name])):
                digest = key(row)
                vci_by_hash[digest] = row
                vci_refs[digest].append({"member": name, "row_index": index})
    assert len(vci_by_hash) == 11202
    target = [r for r in vci_by_hash.values() if r["symbol"] in securities and category(r) in KINDS]
    assert len(target) == 2179 and sum(not r["ex_right_date"] for r in target) == 488

    v3_manifest = json.loads(verified_read(VSDC / "manifest.json"))
    stream = VSDC / "reparsed_vsdc_observations_unique.jsonl"
    vsdc_body = verified_read(stream, VSDC_SHA)
    assert v3_manifest["outputs_created"][stream.name]["sha256"] == VSDC_SHA
    observations = {}
    occurrence_counts = Counter()

    def add(observation, location):
        occurrence_counts[observation["source_type"]] += 1
        item = fact(observation, location)
        digest = item["evidence_id"]
        if digest in observations:
            observations[digest]["locations"].append(location)
            observations[digest]["parser_issues"] = sorted(set(observations[digest]["parser_issues"]) | set(item["parser_issues"]))
        else:
            observations[digest] = item
        for evidence in observation.get("source_evidence", []):
            path = evidence.get("path")
            if not path:
                continue
            resolved = Path(path)
            if not resolved.is_absolute():
                resolved = ROOT / resolved
            resolved = resolved.resolve()
            if resolved.is_relative_to(ROOT.resolve()) and resolved.suffix == ".bin" and "raw" in resolved.parts:
                raw_index[evidence["source_hash"]].append({"path": resolved})

    for i, row in enumerate(lines(vsdc_body), 1):
        add(row, {"path": str(stream), "line": i})
    # Legacy VSDC copies are deliberately replaced by the verified V3 stream;
    # other official sources in the same archived shards remain evidence.
    for base in [ROOT / f"data/corporate_actions/work/outputs/batch_shard_{i}" for i in range(4)] + [BOOTSTRAP]:
        manifest_path = base / "manifest.json"
        manifest_expected = v3_manifest["inputs_read"][manifest_path.relative_to(ROOT).as_posix()]["sha256"]
        manifest = json.loads(verified_read(manifest_path, manifest_expected))
        for relative, digest in manifest["files"].items():
            path = (base / relative).resolve()
            if not path.is_relative_to(base.resolve()):
                raise ValueError("UNSAFE_MANIFEST_PATH")
            if path.suffix == ".bin" and "raw" in path.parts:
                raw_index[digest].append({"path": path})
        paths = list((base / "source_receipts").glob("*/observations.jsonl")) if base != BOOTSTRAP else [base / "normalized_observations/all_observations.jsonl"]
        for path in paths:
            expected = manifest["files"].get(path.relative_to(base).as_posix())
            if expected is None:
                expected = v3_manifest["inputs_read"][path.relative_to(ROOT).as_posix()]["sha256"]
            for index, row in enumerate(lines(verified_read(path, expected)), 1):
                if row["source_type"] != "VSDC":
                    add(row, {"path": str(path), "line": index})
    incident_path = ROOT / "tmp/ca_hnx_round2_four_shard_incident_20261102_v1/audit.json"
    incident = json.loads(verified_read(incident_path))
    raw_proofs, archive_handles = {}, {}
    with ExitStack() as stack:
        for shard in incident["shards"]:
            archive = Path(shard["archive_path"])
            verified_read(archive, shard["archive_sha256"])
            z = stack.enter_context(zipfile.ZipFile(archive))
            archive_handles[str(archive)] = z
            names = set(z.namelist())
            member = max(n for n in names if n.endswith("/collection/observations.jsonl") and "/work/" not in n)
            prefix = member.rsplit("/", 1)[0] + "/"
            group = lines(z.read(member))
            assert len(group) == shard["observations"]
            for index, row in enumerate(group, 1):
                add(row, {"archive": str(archive), "member": member, "line": index})
                for evidence in row["source_evidence"]:
                    candidates = [prefix + evidence["path"]]
                    origin = evidence.get("origin_artifact", "")
                    marker = "/kaggle/working/delta-hnx/"
                    if origin.startswith(marker) and evidence.get("origin_path"):
                        candidates.append(origin[len(marker):] + "/" + evidence["origin_path"])
                    for candidate in candidates:
                        if candidate in names:
                            raw_index[evidence["source_hash"]].append({"archive": str(archive), "member": candidate})

        def raw_proof(digest):
            if digest in raw_proofs:
                return raw_proofs[digest]
            for ref in raw_index.get(digest, []):
                if "path" in ref:
                    path = ref["path"]
                    if not path.is_file():
                        continue
                    body = path.read_bytes()
                    location = {"path": str(path)}
                else:
                    body = archive_handles[ref["archive"]].read(ref["member"])
                    location = ref
                if sha(body) != digest:
                    raise ValueError("RAW_EVIDENCE_HASH_MISMATCH")
                raw_proofs[digest] = {"status": "VERIFIED_CURRENT_BYTES", "sha256": digest, "location": location}
                return raw_proofs[digest]
            raw_proofs[digest] = {"status": "RAW_PAYLOAD_NOT_LOCATED", "sha256": digest}
            return raw_proofs[digest]

        source_index, sibling_index = defaultdict(list), defaultdict(list)
        for item in observations.values():
            if item["ticker"]:
                source_index[(item["ticker"], item["kind"])].append(item)
        for row in target:
            sibling_index[(row["symbol"], category(row))].append(row)
        proposals, used = [], set()
        for row in target:
            index_key = (row["symbol"], category(row))
            item = reconcile_row(row, source_index[index_key], sibling_index[index_key], hint_days=config["time_hint_window_days"])
            item["vci_occurrences"] = vci_refs[key(row)]
            item["scope_security_id_provisional"] = securities[row["symbol"]]["security_id"]
            used.update(x["evidence_id"] for x in item["official_links"])
            used.update(x["evidence_id"] for x in item["economic_term_conflicts"])
            proposals.append(item)
        missing_vci = set(securities) - {r["symbol"] for r in vci_by_hash.values()}
        absent_inventory = []
        for ticker in sorted(missing_vci):
            own = [item for (symbol, _), pool in source_index.items() if symbol == ticker for item in pool]
            candidates = []
            for item in own:
                if item["kind"] not in {*KINDS, "CASH_DIVIDEND", "STOCK_SPLIT", "REVERSE_SPLIT"}:
                    continue
                ex, record = item["values"].get("ex_date"), item["values"].get("record_date")
                basis = "EX_DATE_IN_ENVELOPE" if ex and plan["start"] <= ex <= plan["end"] else (
                    "RECORD_ONLY_IN_ENVELOPE" if not ex and record and plan["start"] <= record <= plan["end"] else None)
                if basis:
                    candidates.append({"evidence_id": item["evidence_id"], "event_type": item["kind"],
                                       "date_basis": basis, "ex_date": ex, "record_date": record,
                                       "parser_issues": item["parser_issues"]})
                    used.add(item["evidence_id"])
            absent_inventory.append({"ticker": ticker, "archived_observations_any_date": len(own),
                "typed_action_candidates_in_envelope": candidates,
                "no_event_confirmed": False, "historical_identity_verified": False})
        evidence = []
        for identifier in sorted(used):
            item = dict(observations[identifier])
            item["primary_raw_verification"] = raw_proof(item["source_hash"])
            # Retain field raw/normalized inputs and source locator, never copy
            # the entire old corpus or alter parser findings.
            evidence.append(item)
    output.mkdir(parents=True)
    def jsonl(name, values):
        with (output / name).open("x", encoding="utf-8") as f:
            for value in values:
                f.write(json.dumps(value, ensure_ascii=False) + "\n")
    jsonl("reconciliation_candidates.jsonl", proposals)
    jsonl("source_evidence_used.jsonl", evidence)
    dump(output / "missing_vci_tickers_archived_inventory.json", absent_inventory)
    date_targets = [p for p in proposals if not p["original_sdk_row"]["ex_right_date"]]
    rights = [p for p in proposals if p["category_candidate"] == "RIGHTS_ISSUE"]
    def has_proposal(p, field):
        return p["fields"][field]["proposed_value_pending_review"] is not None
    evidence_by_id = {e["evidence_id"]: e for e in evidence}
    def verified_support(p, field):
        proposal = p["fields"][field]
        if proposal["proposed_value_pending_review"] is None:
            return False
        refs = [r for value in proposal["candidate_values"] for r in value["evidence"] if "evidence_id" in r]
        return bool(refs) and all(evidence_by_id[r["evidence_id"]]["primary_raw_verification"]["status"] == "VERIFIED_CURRENT_BYTES" for r in refs)
    summary = {"stage": config["stage"], "status": "PARTIAL_MANUAL_REVIEW_REQUIRED",
        "network_requests": 0, "canonical_rows_written": 0, "price_factors_written": 0,
        "scope_tickers": len(securities), "vci_unique_payload_rows": len(vci_by_hash),
        "vci_priority_noncash_rows": len(proposals), "vci_priority_categories": dict(Counter(p["category_candidate"] for p in proposals)),
        "archived_observation_occurrences_by_source": dict(occurrence_counts),
        "archived_distinct_fact_records_by_source": dict(Counter(x["source_type"] for x in observations.values())),
        "missing_ex_date": {"before": len(date_targets), "new_single_value_proposals": sum(has_proposal(p, "ex_date") for p in date_targets),
            "remaining_without_single_value_proposal": sum(not has_proposal(p, "ex_date") for p in date_targets),
            "after_approved_canonical_changes": len(date_targets),
            "with_verified_official_raw_support": sum(verified_support(p, "ex_date") for p in date_targets)},
        "missing_record_date": {"before": sum(not p["original_sdk_row"]["record_date"] for p in proposals),
            "new_single_value_proposals": sum(has_proposal(p, "record_date") for p in proposals)},
        "rights_subscription_price": {"before_missing": len(rights), "new_single_value_proposals": sum(has_proposal(p, "rights_subscription_price") for p in rights),
            "with_verified_official_raw_support": sum(verified_support(p, "rights_subscription_price") for p in rights),
            "remaining_without_single_value_proposal": sum(not has_proposal(p, "rights_subscription_price") for p in rights),
            "after_approved_canonical_changes_missing": len(rights)},
        "matching_review": {"rows_with_official_links": sum(bool(p["official_links"]) for p in proposals),
            "rows_with_sdk_sibling_links": sum(bool(p["sdk_sibling_links"]) for p in proposals),
            "ambiguous_event_rows": sum(p["event_match_ambiguous"] for p in proposals),
            "rows_with_economic_term_conflicts": sum(bool(p["economic_term_conflicts"]) for p in proposals),
            "rows_with_field_value_conflicts": sum(any(len(f["candidate_values"]) > 1 for f in p["fields"].values()) for p in proposals),
            "rows_with_source_parser_warnings": sum(bool(p["all_linked_source_issues"]) for p in proposals)},
        "missing_vci_ticker_inventory": {"before": len(absent_inventory),
            "with_archived_observations_any_date": sum(bool(x["archived_observations_any_date"]) for x in absent_inventory),
            "with_typed_action_candidates_in_envelope": sum(bool(x["typed_action_candidates_in_envelope"]) for x in absent_inventory),
            "without_typed_action_candidates_in_envelope": sum(not x["typed_action_candidates_in_envelope"] for x in absent_inventory),
            "coverage_promoted": 0},
        "raw_evidence": {"used_fact_records": len(evidence), "distinct_raw_hashes_checked": len(raw_proofs),
            "statuses": dict(Counter(x["status"] for x in raw_proofs.values()))},
        "config": config,
        "limitations": ["All links are provisional ticker-based, not historical-security identity joins",
            "Time hints and UTC+7 dates are retrieval/review views only, not publication/PIT approval",
            "Unique proposals are not approved fields or confirmed event identity",
            "Missing-date events can be separate yearly events; ambiguous alternatives are retained",
            "No source priority, averaging, previous-session date inference or canonical deduplication",
            "No reconciliation of effective revisions or mixed components is automatically approved"],
        "inputs_verified": inputs}
    dump(output / "summary.json", summary)
    dump(output / "manifest.json", {"artifact_type": "corporate-action-offline-reconciliation-preview-v1",
        "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()}})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != "inputs_verified"}, ensure_ascii=False, indent=2))
