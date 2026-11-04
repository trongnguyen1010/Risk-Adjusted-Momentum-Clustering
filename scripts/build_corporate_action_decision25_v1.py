"""Build unsigned field-selection packet for5 price +20 ratio cases, offline."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
import argparse
import hashlib
import json
from pathlib import Path,PureWindowsPath
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_decision_packet import inspect_history_document,link_history,make_request,RIGHTS_CODE
from delta_t1.ingestion.corporate_action_cached_review import parse_scoped_article
from delta_t1.ingestion.corporate_action_cache_audit import provider_id
from delta_t1.ingestion.corporate_action_sources import now

BASE=ROOT/"tmp/ca_cached26_review_20261102_v1"
CACHE=ROOT/"tmp/ca_cache_inventory_20261102_v4"
CONFIG=ROOT/"configs/data/corporate_action_decision25_v1.json"
sha=lambda body:hashlib.sha256(body).hexdigest()


def safe(base,name):
    rel=PureWindowsPath(name)
    if rel.drive or rel.root or ".." in rel.parts:raise ValueError("PATH_ESCAPE")
    return base.joinpath(*rel.parts)


def run(output):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    inputs={}
    def pin(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError(f"INPUT_HASH_MISMATCH: {path}")
        inputs[path.relative_to(ROOT).as_posix()]=digest
        return body
    c=json.loads(pin(CONFIG))
    if any(c[k] for k in ["network_requests","automatic_field_approval","canonical_build","global_ratio_tolerance_change"]):raise ValueError("UNSIGNED_OFFLINE_PROPOSALS_ONLY")
    bm=json.loads(pin(BASE/"manifest.json",c["cached26_manifest_sha256"]))
    cm=json.loads(pin(CACHE/"manifest.json",c["cache_inventory_manifest_sha256"]))
    files={name:pin(safe(BASE,name),digest) for name,digest in bm["files"].items()}
    rows=[json.loads(l) for l in files["reviewed_payloads_26.jsonl"].splitlines() if l.strip()]
    rows=[r for r in rows if r["field_data_supported_pending_review"] or "RATIO_TERM_REVIEW_REQUIRED" in r["blockers"]]
    if len(rows)!=c["payload_count"] or len({r["vci_payload_sha256"] for r in rows})!=25:raise ValueError("EXACT25_SCOPE_REQUIRED")
    if sum(r["field_data_supported_pending_review"] for r in rows)!=c["existing_compatible_price_candidates"]:raise ValueError("EXISTING_CANDIDATE_COUNT_MISMATCH")
    if sum("RATIO_TERM_REVIEW_REQUIRED" in r["blockers"] for r in rows)!=c["ratio_review_payloads"]:raise ValueError("RATIO_CASE_COUNT_MISMATCH")
    parsed={d["document_id"]:d for d in (json.loads(l) for l in files["reparsed_documents.jsonl"].splitlines() if l.strip())}
    tickers={r["ticker"] for r in rows};index=pin(CACHE/"raw_document_index.jsonl",cm["files"]["raw_document_index.jsonl"])
    selected=[]
    for line in index.splitlines():
        if not line.strip():continue
        d=json.loads(line)
        if d.get("ticker") in tickers or d.get("title_ticker_hint") in tickers:selected.append(d)
    def load(d):
        body=pin(safe(ROOT,d["raw_path"]),d["source_hash"])
        history=inspect_history_document(body,d["source_url"])
        scoped=parse_scoped_article(body,d["source_url"]) if "RIGHTS_ISSUE" in history["kinds"] else None
        return history|{k:d[k] for k in ["document_id","source_url","source_hash","raw_path"]},scoped
    print(json.dumps({"stage":"CACHED_HISTORY_REVIEW","payloads":len(rows),"ticker_contexts":len(tickers),"cached_responses":len(selected),"network_requests":0}),flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:loaded=list(pool.map(load,selected))
    histories=[x[0] for x in loaded];scoped_by_id={h["document_id"]:s for h,s in loaded}
    requests=[]
    for row in rows:
        sources=[];codes=set();providers=set()
        for candidate in row["candidate_sources"]:
            d=parsed[candidate["document_id"]];component=d["components"]["RIGHTS_ISSUE"]
            providers.add(provider_id(d["source_url"]));codes.update(RIGHTS_CODE.findall(component["text"]))
            sources.append({"document_id":d["document_id"],"source_url":d["source_url"],"source_hash":d["source_hash"],"raw_path":d["raw_path"],
                "ticker_record_supported":candidate["ticker_date_anchor_supported"],"record_dates":d["record_dates"],
                "price_vnd":candidate["candidate_price_vnd_pending_review"],"primary_unit_explicit":candidate["primary_unit_explicit"],
                "ratio_exact":candidate["source_ratio_exact"],"rights_codes":sorted(set(RIGHTS_CODE.findall(component["text"]))),
                "component_heading":component["heading"],"component_span":{"start":component["start"],"end":component["end"]},
                "primary_price_quotes":component["primary_prices"],"ratio_evidence":component["ratio"]})
        checks=[]
        price_values={s["price_vnd"] for s in sources}
        exact_ratios={Fraction(s["ratio_exact"]["numerator"],s["ratio_exact"]["denominator"]) for s in sources}
        for h in histories:
            if h["ticker"]!=row["ticker"] and h["title_ticker_hint"]!=row["ticker"]:continue
            link=link_history(row,h,providers,codes);other=scoped_by_id[h["document_id"]]
            conflict=False
            if link["strong_event_reference"] and other:
                section=other["components"].get("RIGHTS_ISSUE")
                if section:
                    values={p["value_vnd"] for p in section["primary_prices"]}
                    ratios=section["ratio"]["values"]
                    conflict=bool(values and not values.issubset(price_values)) or bool(ratios and any(Fraction(v["numerator"],v["denominator"]) not in exact_ratios for v in ratios))
            checks.append(link|{"document_id":h["document_id"],"source_url":h["source_url"],"source_hash":h["source_hash"],
                "observed_terms_conflict":conflict,"title_change_markers":h["title_change_markers"],"body_change_quotes":h["body_change_quotes"],
                "change_scope_review":h["change_scope_review"] if link["revision_or_cancellation_candidate"] else None})
        request=make_request(row,sources,checks)
        request["proposal_id"]=sha(json.dumps({"payload":row["vci_payload_sha256"],"sources":[s["document_id"] for s in sources],"stage":c["stage"]},sort_keys=True).encode())
        request["target_rights_codes"]=sorted(codes)
        requests.append(request)
    counts=Counter(r["decision_class"] for r in requests)
    packet_rows=[{"ticker":r["ticker"],"record_date":r["original_record_date_review_view"],"vci_payload_sha256":r["vci_payload_sha256"],
        "sdk_ratio":r["original_sdk_row"]["ratio"],"source_ratio_exact":r["sources"][0]["ratio_exact"],"price_vnd":r["observed_price_vnd"],
        "decision_class":r["decision_class"],"rights_codes":r["target_rights_codes"],"source_urls":sorted({s["source_url"] for s in r["sources"]}),
        "linked_change_documents":[h["document_id"] for h in r["cached_history_checks"] if h["revision_or_cancellation_candidate"]],
        "conditional_price_selection_after_lineage_review":r["conditional_price_selection_after_lineage_review"],
        "lifecycle_status":r["lifecycle_status"],"review_status":r["review_status"]} for r in requests]
    summary={"stage":c["stage"],"technical_stage_status":"PASS","decision_status":"MANUAL_REVIEW_REQUIRED",
        "scope_inventory":"C8_V2_1522","payloads_reviewed":len(requests),"ticker_contexts":len(tickers),
        "count_unit":"distinct VCI SDK payload, not canonical economic event",
        "cached_history_response_versions_inspected":len(histories),"cached_history_provider_articles":len({h["provider_article_id"] for h in histories}),
        "decision_class_counts":dict(counts),"linked_change_candidate_payloads":sum(bool(r["linked_change_documents"]) for r in packet_rows),
        "conditional_price_selection_after_lineage_review_payloads":sum(r["conditional_price_selection_after_lineage_review"] is not None for r in requests),
        "change_scope_counts_by_document":dict(Counter(h["change_scope_review"]["scope"] for h in histories if any(h["document_id"]==x["document_id"] and x["revision_or_cancellation_candidate"] for r in requests for x in r["cached_history_checks"]))),
        "linked_source_value_conflict_payloads":sum(r["decision_class"]=="HOLD_SOURCE_VALUE_CONFLICT" for r in requests),
        "terminal_execution_confirmed_payloads":0,"network_requests":0,"hnx_network_requests":0,
        "approved_decisions_before_after":[0,0],"applied_field_changes":0,"canonical_rows_written":0,
        "production_ratio_tolerance":"UNCHANGED","sdk_values_overwritten":0,"pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED",
        "limitations":["All history findings are limited to entity/title-hint documents in the sealed VSDC cache, not all sources or full pagination.",
            "A rights schedule/rights-code expiry does not certify terminal execution or cancellation of the offering.",
            "Rounding consistency is a mathematical diagnostic, not proof of the provider's transformation or economic equality.",
            "This packet is unsigned and not importable as approved production review decisions. ASG and acquisition are outside this stage."]}
    output.mkdir(parents=True)
    def dump(name,value):
        with (output/name).open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2)
    def jsonl(name,values):
        with (output/name).open("x",encoding="utf-8") as f:
            for value in values:f.write(json.dumps(value,ensure_ascii=False)+"\n")
    jsonl("decision_requests_25.jsonl",requests);jsonl("cached_history_evidence.jsonl",histories)
    dump("decision_table.json",packet_rows);dump("summary.json",summary)
    ratio_cases=[r["vci_payload_sha256"] for r in requests if r["case_specific_ratio_selection_approval_required"]]
    dump("approval_proposal.json",{"status":"MANUAL_REVIEW_REQUIRED","owner_approval":None,"applied":False,
        "existing_rule_price_selection_payloads":[r["vci_payload_sha256"] for r in requests if r["decision_class"]=="EXISTING_RULE_PRICE_SELECTION_PROPOSAL"],
        "case_specific_exact_source_ratio_selection_payloads":ratio_cases,
        "conditional_cached_change_review_payloads":[r["vci_payload_sha256"] for r in requests if r["decision_class"]=="HOLD_LINKED_CHANGE_REVIEW"],
        "proposal":"For listed cases only, select the explicitly observed primary-offer price and source exact ratio after reviewing event/component and cached change references. Preserve VCI SDK values and all provenance.",
        "not_authorized":["global tolerance change","provider-wide rounding inference","automatic source priority","canonical/research sample freeze","PIT or identity promotion","executed-event claim","network acquisition"],
        "requires_separate_evidence":[r["vci_payload_sha256"] for r in requests if r["decision_class"].startswith("HOLD_")]})
    dump("cached_change_review_requests.json",[{"ticker":r["ticker"],"record_date_review_view":r["original_record_date_review_view"],"vci_payload_sha256":r["vci_payload_sha256"],
        "change_documents":[h for h in r["cached_history_checks"] if h["revision_or_cancellation_candidate"]],
        "conditional_price_request":r["conditional_price_selection_after_lineage_review"],
        "action":"Review cached original/reference chain and narrow change scope before field selection; no automatic cancellation or latest-source winner.",
        "new_document_acquisition_required":False,"network_request_sent":False} for r in requests if r["decision_class"]=="HOLD_LINKED_CHANGE_REVIEW"])
    dump("missing_document_requests.json",[{"ticker":r["ticker"],"record_date_review_view":r["original_record_date_review_view"],"vci_payload_sha256":r["vci_payload_sha256"],
        "reason":r["decision_class"],"requested_document":"Issuer offering resolution/prospectus or explicit correction linked to this offering; confirm exact new-shares-per-existing-share ratio.",
        "known_source_urls":sorted({s["source_url"] for s in r["sources"]}),"invented_download_url":None,"network_request_sent":False} for r in requests if r["decision_class"]=="HOLD_RATIO_REQUIRES_ADDITIONAL_PRIMARY_EVIDENCE"])
    for name,digest in inputs.items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError("INPUT_CHANGED_DURING_STAGE")
    assert all(r["owner_decision"] is None and not r["signature_created"] and not r["canonical_written"] for r in requests)
    dump("self_review.json",{"status":"PASS","input_hashes_rechecked":len(inputs),"unsigned_payloads":len(requests),
        "source_ratio_selection_proposals":len(ratio_cases),"network_requests":0,"applied_field_changes":0,
        "boundary":"Proposal packet only; approval needed before any field selection or matching change. No ASG collection, PIT/identity/freeze or backtest."})
    code=[Path(__file__),ROOT/"src/delta_t1/ingestion/corporate_action_decision_packet.py",ROOT/"src/delta_t1/ingestion/corporate_action_cached_review.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_cache_audit.py",ROOT/"src/delta_t1/ingestion/corporate_action_evidence_review.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_sources.py",ROOT/"src/delta_t1/ingestion/corporate_action_offline_reconcile.py"]
    dump("manifest.json",{"artifact_type":"corporate-action-decision-packet25-v1","created_at":now(),"inputs_verified":inputs,
        "files":{p.name:sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},"code_hashes":{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code},
        "network_requests":0,"approved_decisions":0,"canonical_build":False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path)
    run(parser.parse_args().output.resolve())
