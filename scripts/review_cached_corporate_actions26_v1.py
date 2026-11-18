"""Review offline 18 precision cases + 8 mixed-component cached articles."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path,PureWindowsPath
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_cached_review import parse_scoped_article,review_link
from delta_t1.ingestion.corporate_action_sources import now

CONFIG=ROOT/"configs/data/corporate_action_cached26_review_v1.json"
FINDINGS=ROOT/"tmp/ca_cache_findings_20261102_v2"
CACHE=ROOT/"tmp/ca_cache_inventory_20261102_v4"
sha=lambda b:hashlib.sha256(b).hexdigest()


def safe(base,name):
    rel=PureWindowsPath(name)
    if rel.drive or rel.root or ".." in rel.parts:raise ValueError("INPUT_PATH_ESCAPE")
    return base.joinpath(*rel.parts)


def run(output):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    inputs={}
    def pin(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError(f"INPUT_HASH_MISMATCH: {path}")
        inputs[path.relative_to(ROOT).as_posix()]=digest
        return body
    config=json.loads(pin(CONFIG))
    if config["network_requests"]!=0 or config["automatic_field_approval"] or config["canonical_build"]:
        raise ValueError("OFFLINE_MANUAL_REVIEW_ONLY")
    fm=json.loads(pin(FINDINGS/"manifest.json",config["findings_manifest_sha256"]))
    cm=json.loads(pin(CACHE/"manifest.json",config["cache_manifest_sha256"]))
    if fm["audit_manifest_sha256"]!=config["cache_manifest_sha256"]:raise ValueError("AUDIT_LINEAGE_MISMATCH")
    files={name:pin(safe(FINDINGS,name),digest) for name,digest in fm["files"].items()}
    precision=[json.loads(l) for l in files["cached_price_match_review_18.jsonl"].splitlines() if l.strip()]
    mixed=[json.loads(l) for l in files["mixed_component_review_8.jsonl"].splitlines() if l.strip()]
    if len(precision)!=config["precision_payloads"] or len(mixed)!=config["mixed_component_payloads"]:raise ValueError("STAGE_SCOPE_COUNT_MISMATCH")
    selected={}
    for row in precision:
        for c in row["review_candidates"]:selected[c["document_id"]]=None
    for row in mixed:
        for c in row["global_text_review"]:selected[c["document_id"]]=None
    index=pin(CACHE/"raw_document_index.jsonl",cm["files"]["raw_document_index.jsonl"])
    for line in index.splitlines():
        if not line.strip():continue
        d=json.loads(line)
        if d["document_id"] in selected:selected[d["document_id"]]=d
    if any(d is None for d in selected.values()):raise ValueError("SELECTED_DOCUMENT_NOT_IN_SEALED_INDEX")
    parsed={};body_cache={}
    for identifier,d in selected.items():
        path=safe(ROOT,d["raw_path"])
        if d["source_hash"] not in body_cache:body_cache[d["source_hash"]]=pin(path,d["source_hash"])
        article=parse_scoped_article(body_cache[d["source_hash"]],d["source_url"])
        parsed[identifier]=article|{"document_id":identifier,"source_url":d["source_url"],"raw_path":d["raw_path"],"source_hash":d["source_hash"]}
    reviewed=[];components=[]
    for identifier,article in parsed.items():
        for kind,section in article["components"].items():
            components.append({"document_id":identifier,"source_url":article["source_url"],"source_hash":article["source_hash"],
                "ticker":article["ticker"],"event_type":kind,"section":section,"canonical_approved":False})
    for cohort,rows in [("PRECISION_18",precision),("MIXED_COMPONENT_8",mixed)]:
        for row in rows:
            identifiers=[c["document_id"] for c in row["review_candidates" if cohort=="PRECISION_18" else "global_text_review"]]
            results=[review_link(row,parsed[identifier])|{"document_id":identifier} for identifier in identifiers]
            # All selected raw versions must support the same candidate before
            # a data-supported preview is emitted. Never choose a source winner.
            prices={v for r in results for v in r["primary_price_values_vnd"]}
            blockers=sorted({b for r in results for b in r["blockers"]})
            if len(prices)>1:blockers.append("SELECTED_SOURCE_PRICE_CONFLICT")
            supported=bool(results) and not blockers and all(r["field_data_supported_pending_review"] for r in results)
            reviewed.append({"ticker":row["ticker"],"vci_payload_sha256":row["vci_payload_sha256"],"cohort":cohort,
                "original_sdk_row":row["original_sdk_row"],"prior_field_review_unchanged":row["fields"],
                "candidate_sources":results,"candidate_price_vnd_pending_review":next(iter(prices)) if len(prices)==1 else None,
                "field_data_supported_pending_review":supported,"blockers":blockers,
                "review_status":"MANUAL_REVIEW_REQUIRED","canonical_approved":False,
                "next_action":"REVIEW_EVENT_AND_FIELD_SELECTION" if supported else "CHECK_CACHED_OR_ISSUER_PRIMARY_UNIT_EVIDENCE" if "PRIMARY_PRICE_UNIT_EVIDENCE_REQUIRED" in blockers else "OFFLINE_EXACT_RATIO_AND_EVENT_TERM_REVIEW",
                "automatic_tolerance_or_source_selection_applied":False})
    if len({r["vci_payload_sha256"] for r in reviewed})!=26:raise ValueError("PAYLOAD_SCOPE_OVERLAP_OR_COUNT")
    ready=[r for r in reviewed if r["field_data_supported_pending_review"]]
    remaining=[r for r in reviewed if not r["field_data_supported_pending_review"]]
    summary={"stage":config["stage"],"technical_stage_status":"PASS","data_readiness":"PARTIAL_MANUAL_REVIEW_REQUIRED",
        "scope_inventory":"C8_V2_1522","count_unit":"distinct VCI SDK payload; not canonical event",
        "network_requests":0,"hnx_network_requests":0,"reviewed_payloads":len(reviewed),
        "precision_cohort_payloads":len(precision),"mixed_cohort_payloads":len(mixed),"raw_documents_reparsed":len(parsed),
        "mixed_component_scopes_before":0,"mixed_component_scopes_after":sum("RIGHTS_ISSUE" in parsed[c["document_id"]]["components"] for r in mixed for c in r["global_text_review"]),
        "parsed_component_records":len(components),"data_supported_price_candidates":len(ready),"payloads_still_requiring_term_or_unit_review":len(remaining),
        "supported_by_cohort":dict(Counter(r["cohort"] for r in ready)),
        "blocker_payload_counts_overlap":dict(Counter(b for r in remaining for b in r["blockers"])),
        "ratio_relations_by_cohort":{cohort:dict(Counter(s["raw_ratio_relation"] for r in reviewed if r["cohort"]==cohort for s in r["candidate_sources"])) for cohort in ["PRECISION_18","MIXED_COMPONENT_8"]},
        "ratio_relation_count_unit":"raw document versions; duplicate versions do not create extra payloads",
        "accepted_field_changes":0,"canonical_rows_written":0,"price_factors_written":0,
        "baseline_missing_queue_before_after":{"payloads":[602,602],"field_tasks":[1373,1373],"note":"No approved fills; supported candidates are a separate preview, not queue removal."},
        "pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED","price_policy":"UNCHANGED",
        "production_parser_and_matching_policy":"UNCHANGED; new scoped parser is used only by this offline review runner",
        "other_source_need":"TARGETED_DOCUMENT_DISCOVERY_AFTER_CACHE_REVIEW; NO_NETWORK_AUTHORIZED_BY_THIS_OUTPUT",
        "untouched_work":["49 prior price reviews","remaining576 of602 missing-payload cohort","182 coverage cases","historical identity/PIT","production canonical and prices"]}
    output.mkdir(parents=True)
    def dump(name,value):
        with (output/name).open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2)
    def jsonl(name,values):
        with (output/name).open("x",encoding="utf-8") as f:
            for value in values:f.write(json.dumps(value,ensure_ascii=False)+"\n")
    jsonl("reparsed_documents.jsonl",parsed.values());jsonl("scoped_component_candidates.jsonl",components)
    jsonl("reviewed_payloads_26.jsonl",reviewed);jsonl("supported_price_candidates.jsonl",ready);jsonl("remaining_review.jsonl",remaining)
    dump("summary.json",summary)
    dump("next_actions.json",{"review_status":"MANUAL_REVIEW_REQUIRED","network_requests":0,
        "actions":[{"queue":"supported_price_candidates.jsonl","action":"Review event/lifecycle and observed field selection; do not promote PIT/identity."},
            {"queue":"remaining_review.jsonl","action":"Review exact source ratio vs SDK serialization; any relaxed comparison/provider transformation requires explicit approval."},
            {"queue":"remaining_review.jsonl","filter":"PRIMARY_PRICE_UNIT_EVIDENCE_REQUIRED","action":"Search existing other-source cache first, then identify issuer offering document with explicit primary price unit; do not borrow residual placement unit."}],
        "larger_missing_cohort":"No bulk recrawl from this stage. Build exact missing-document requests separately after event linkage review."})
    quote_checks=0
    for article in parsed.values():
        for section in article["components"].values():
            assert article["article_text"][section["start"]:section["end"]]==section["text"]
            for p in section["primary_prices"]:
                q=p["quote"];assert section["text"][q["start"]:q["end"]]==q["text"];quote_checks+=1
            for e in section["ratio"]["evidence"]:
                if "quote" in e:
                    q=e["quote"];assert section["ratio"]["evidence_text"][q["start"]:q["end"]]==q["text"];quote_checks+=1
    for name,digest in inputs.items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError("INPUT_CHANGED_DURING_REVIEW")
    assert all(not r["canonical_approved"] and not r["automatic_tolerance_or_source_selection_applied"] for r in reviewed)
    dump("self_review.json",{"status":"PASS","input_file_hashes_rechecked":len(inputs),"section_price_ratio_quote_checks":quote_checks,
        "payloads":len(reviewed),"accepted_field_changes":0,"network_requests":0,
        "stage_boundary":"Only26 cached payloads; no policy relaxation/canonical/PIT/identity/production parser changes."})
    code_paths=[Path(__file__),ROOT/"src/delta_t1/ingestion/corporate_action_cached_review.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_cache_audit.py",ROOT/"src/delta_t1/ingestion/corporate_action_evidence_review.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_offline_reconcile.py",ROOT/"src/delta_t1/ingestion/corporate_action_sources.py"]
    dump("manifest.json",{"artifact_type":"cached-corporate-actions26-offline-review-v1","created_at":now(),
        "inputs_verified":inputs,"files":{p.name:sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        "code_hashes":{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code_paths},"network_requests":0,"canonical_build":False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args().output.resolve())
