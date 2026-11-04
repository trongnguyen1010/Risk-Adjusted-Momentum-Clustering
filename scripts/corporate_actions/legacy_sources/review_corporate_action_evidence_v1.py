"""Review raw evidence của preview đã seal; chỉ offline, output mới."""
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
from delta_t1.ingestion.corporate_action_evidence_review import inspect_article, inspect_hose_calendar, review_price, ratio_relation, diagnose_conflict


def sha(body):
    return hashlib.sha256(body).hexdigest()


def run(output):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    config_path = ROOT / "configs/data/corporate_action_evidence_review_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["automatic_field_approval"] or config["canonical_build"] or config["network_requests"] != 0:
        raise ValueError("REVIEW_ONLY_CONTRACT_REQUIRED")
    base = ROOT / "tmp/ca_offline_reconciliation_20261102_v1"
    inputs = {}

    def read(path, expected=None):
        data = path.read_bytes()
        digest = sha(data)
        if expected is not None and digest != expected:
            raise ValueError("INPUT_HASH_MISMATCH: " + str(path))
        inputs[str(path)] = digest
        return data

    manifest = json.loads(read(base / "manifest.json", config["preview_manifest_sha256"]))
    files = {name: read(base / name, digest) for name, digest in manifest["files"].items()}
    upstream = json.loads(files["summary.json"])
    for name, entry in upstream["inputs_verified"].items():
        read(Path(name), entry["sha256"])
    rows = [json.loads(line) for line in files["reconciliation_candidates.jsonl"].decode().splitlines()]
    evidence = {e["evidence_id"]: e for e in map(json.loads, files["source_evidence_used.jsonl"].decode().splitlines())}
    by_hash = {r["vci_payload_sha256"]: r for r in rows}
    targets = [r for r in rows if r["economic_term_conflicts"] or any(f["proposed_value_pending_review"] is not None for f in r["fields"].values())]
    selected_ids = {ref["evidence_id"] for r in targets for ref in r["official_links"] + r["economic_term_conflicts"]}
    articles, archives = {}, {}
    with ExitStack() as stack:
        for identifier in sorted(selected_ids):
            e = evidence[identifier]
            proof = e["primary_raw_verification"]
            if proof["status"] != "VERIFIED_CURRENT_BYTES":
                raise ValueError("UNVERIFIED_RAW_EVIDENCE")
            loc = proof["location"]
            if "path" in loc:
                path = Path(loc["path"]).resolve()
                if not path.is_relative_to(ROOT.resolve()):
                    raise ValueError("RAW_PATH_OUTSIDE_WORKSPACE")
                body = read(path, e["source_hash"])
            else:
                archive = loc["archive"]
                if archive not in archives:
                    if archive not in inputs:
                        raise ValueError("ARCHIVE_NOT_IN_VERIFIED_INPUT_CHAIN")
                    archives[archive] = stack.enter_context(zipfile.ZipFile(archive))
                body = archives[archive].read(loc["member"])
                if sha(body) != e["source_hash"]:
                    raise ValueError("RAW_MEMBER_HASH_MISMATCH")
            result = inspect_hose_calendar(body, e) if e["source_type"] == "HOSE" else inspect_article(body, e["source_type"], e["kind"], e["source_url"])
            result.update(evidence_id=identifier, source_type=e["source_type"], kind=e["kind"],
                source_url=e["source_url"], source_hash=e["source_hash"], raw_location=loc,
                archived_parser_issues=e["parser_issues"], archived_normalized_values=e["values"],
                canonical_approved=False, review_status="MANUAL_REVIEW_REQUIRED")
            articles[identifier] = result

    prices, dates, conflicts = [], [], []
    cohorts = defaultdict(list)
    for row in rows:
        cohorts[(row["ticker"], row["category_candidate"], row["fields"]["ex_date"]["original_review_value"], row["fields"]["record_date"]["original_review_value"])].append(row)
    for row in targets:
        common = {"vci_payload_sha256": row["vci_payload_sha256"], "ticker": row["ticker"],
            "category": row["category_candidate"], "original_sdk_row": row["original_sdk_row"],
            "vci_occurrences": row["vci_occurrences"], "review_status": "MANUAL_REVIEW_REQUIRED",
            "canonical_approved": False, "pit_status": "NOT_PROMOTED", "identity_status": "UNVERIFIED"}
        if row["fields"]["rights_subscription_price"]["proposed_value_pending_review"] is not None:
            prices.append(common | {"proposed_price_vnd": row["fields"]["rights_subscription_price"]["proposed_value_pending_review"],
                                    "raw_review": review_price(row, articles)})
        for name in ("ex_date", "record_date"):
            field = row["fields"][name]
            if field["proposed_value_pending_review"] is None:
                continue
            checks = []
            for value in field["candidate_values"]:
                for ref in value["evidence"]:
                    if "evidence_id" in ref:
                        article = articles[ref["evidence_id"]]
                        supported = {x["value"] for x in article["dates"][name]} == {value["value"]} and {x["value"] for x in article["tickers"]} == {row["ticker"]}
                        checks.append(ref | {"raw_date_and_ticker_supported": supported,
                            "ratio_relation": ratio_relation(row["original_sdk_row"]["ratio"], article["ratio"])})
                    elif "vci_payload_sha256" in ref:
                        sibling = by_hash[ref["vci_payload_sha256"]]
                        if sibling["fields"][name]["original_review_value"] != value["value"]:
                            raise ValueError("SDK_SIBLING_REFERENCE_MISMATCH")
                        checks.append(ref | {"sdk_payload_date_supported": True, "primary_source": False})
            official = [c for c in checks if "evidence_id" in c]
            status = "EXPLICIT_OFFICIAL_DATE_SUPPORTED" if official and all(c["raw_date_and_ticker_supported"] for c in official) else "SDK_SIBLING_ONLY_EVENT_LINK_UNVERIFIED" if not official else "RAW_DATE_NOT_CONFIRMED"
            dates.append(common | {"field": name, "proposed_date": field["proposed_value_pending_review"],
                "status": status, "evidence_checks": checks,
                "event_link_approval": "NOT_APPROVED_TIME_HINT_OR_SIBLING_MATCH"})
        if row["economic_term_conflicts"]:
            checks = []
            for identifier in sorted({c["evidence_id"] for c in row["economic_term_conflicts"]}):
                article = articles[identifier]
                peers = cohorts[(row["ticker"], row["category_candidate"], row["fields"]["ex_date"]["original_review_value"], row["fields"]["record_date"]["original_review_value"])]
                diagnosis = diagnose_conflict(row["original_sdk_row"]["ratio"], article["ratio"], [p["original_sdk_row"]["ratio"] for p in peers])
                checks.append(diagnosis | {"evidence_id": identifier,
                    "cohort_payloads": [p["vci_payload_sha256"] for p in peers],
                    "no_aggregation_or_tolerance_applied": True})
            conflicts.append(common | {"checks": checks, "conflict_resolved": False})

    price_index = {r["vci_payload_sha256"]: r for r in prices}
    date_index = {(r["vci_payload_sha256"], r["field"]): r for r in dates}
    queue = defaultdict(list)
    for row in rows:
        for name, field in row["fields"].items():
            if name == "rights_subscription_price" and row["category_candidate"] != "RIGHTS_ISSUE":
                continue
            if field["original_review_value"] is not None:
                continue
            review = price_index.get(row["vci_payload_sha256"]) if name == "rights_subscription_price" else date_index.get((row["vci_payload_sha256"], name))
            queue[row["ticker"]].append({"vci_payload_sha256": row["vci_payload_sha256"], "field": name,
                "category": row["category_candidate"], "original_sdk_row": row["original_sdk_row"],
                "proposed_value_pending_review": field["proposed_value_pending_review"],
                "current_review": review["raw_review"]["status"] if review and name == "rights_subscription_price" else review["status"] if review else "NOT_REVIEWED_NO_SINGLE_VALUE_PROPOSAL",
                "next_action": "REVIEW_EVIDENCE_BEFORE_FIELD_ACCEPTANCE" if review else "FIND_EXPLICIT_OFFICIAL_DATE_NOTICE" if name == "ex_date" else "READ_OFFICIAL_TERMS_OR_ATTACHMENT",
                "archived_official_evidence_ids": [x["evidence_id"] for x in row["official_links"]],
                "canonical_approved": False})
    summary = {"stage": config["stage"], "status": "PARTIAL_MANUAL_REVIEW_REQUIRED", "network_requests": 0,
        "scope_tickers": 1522, "vci_noncash_payload_rows": len(rows), "reviewed_payload_rows_union": len(targets),
        "raw_fact_records_inspected": len(articles), "distinct_raw_hashes_inspected": len({a["source_hash"] for a in articles.values()}),
        "price_reviews": {"before_proposals": 244, "reviewed": len(prices),
            "statuses": dict(Counter(r["raw_review"]["status"] for r in prices)),
            "source_raw_ratio_relations": dict(Counter(c["ratio_relation"] for r in prices for c in r["raw_review"]["evidence_checks"])),
            "previous_ratio_warning_rows": sum("RATIO_PARSE_AMBIGUITY" in by_hash[r["vci_payload_sha256"]]["all_linked_source_issues"] for r in prices),
            "previous_ratio_warning_rows_now_raw_terms_supported": sum("RATIO_PARSE_AMBIGUITY" in by_hash[r["vci_payload_sha256"]]["all_linked_source_issues"] and r["raw_review"]["status"] == "RAW_PRICE_SUPPORTED_EVENT_TERMS_SUPPORTED" for r in prices)},
        "date_reviews": {"reviewed_field_proposals": len(dates), "statuses_by_field": {name: dict(Counter(d["status"] for d in dates if d["field"] == name)) for name in ("ex_date", "record_date")}},
        "conflict_reviews": {"before_conflicting_payload_rows": 36, "reviewed": len(conflicts),
            "diagnoses_by_row": dict(Counter("|".join(sorted({c["diagnosis"] for c in r["checks"]})) for r in conflicts)), "automatically_resolved": 0},
        "missing_fields_before_and_after_approved_changes": {"ex_date": [488,488], "record_date": [488,488], "rights_subscription_price": [654,654]},
        "remaining_queue": {"tickers": len(queue), "payload_field_tasks": sum(map(len,queue.values())),
            "no_single_value_proposal_by_field": dict(Counter(task["field"] for tasks in queue.values() for task in tasks if task["proposed_value_pending_review"] is None)),
            "missing_vci_coverage_tickers": 182},
        "attachment_links_seen_not_fetched": len({url for a in articles.values() for url in a["attachment_links_not_fetched"]}),
        "canonical_rows_written": 0, "price_factors_written": 0, "accepted_field_changes": 0,
        "pit_status": "NOT_PROMOTED", "identity_status": "UNVERIFIED", "config": config,
        "input_sha256": inputs}
    if len(prices) != 244 or len(dates) != 13 or len(conflicts) != 36 or sum(map(len, queue.values())) != 1630:
        raise ValueError("REVIEW_SCOPE_COUNT_MISMATCH")
    output.mkdir(parents=True)

    def write(name, obj):
        with (output / name).open("x", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    for name, items in [("raw_article_reviews.jsonl", articles.values()), ("price_proposal_reviews.jsonl", prices),
                        ("date_proposal_reviews.jsonl", dates), ("ratio_conflict_reviews.jsonl", conflicts)]:
        with (output / name).open("x", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    write("remaining_field_queue_by_ticker.json", dict(sorted(queue.items())))
    write("missing_vci_coverage_queue.json", [item | {"next_action": "VERIFY_HISTORICAL_SOURCE_COVERAGE_NO_NO_EVENT_CLAIM", "coverage_promoted": False}
        for item in json.loads(files["missing_vci_tickers_archived_inventory.json"])])
    write("summary.json", summary)
    code = [str(Path(__file__).relative_to(ROOT)), "src/delta_t1/ingestion/corporate_action_evidence_review.py", str(config_path.relative_to(ROOT))]
    write("manifest.json", {"artifact_type": "corporate-action-raw-evidence-review-v1",
        "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "code_and_config_sha256": {p: sha((ROOT / p).read_bytes()) for p in code}})
    return {k: v for k, v in summary.items() if k != "input_sha256"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output.resolve()), ensure_ascii=False, indent=2))
