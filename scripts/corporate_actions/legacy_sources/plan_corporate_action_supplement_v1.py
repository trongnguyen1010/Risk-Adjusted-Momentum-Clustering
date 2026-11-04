"""Lập queue từ sealed review và pilot tối đa sáu public documents; không bulk."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_sources import PublicTransport, SourceLimitation, Document, now, sha

CONFIG = ROOT / "configs/data/corporate_action_supplement_pilot_v1.json"
REVIEW = ROOT / "tmp/ca_raw_evidence_review_20261102_v4"
HOSTS = {"abbank.vn", "www.abbank.vn", "fitgroup.com.vn", "www.aas.com.vn", "www.angia.com.vn", "vsdc.vn"}


class SupplementPilotTransport(PublicTransport):
    HOSTS = HOSTS


def config():
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    if (c["max_requests"] != 6 or c["interval_seconds"] < 2 or c["timeout_seconds"] > 15
            or c["max_bytes"] > 2000000 or not c["tls_verification"] or c["follow_redirects"]
            or any(c[k] for k in ("hnx_requests_allowed", "bulk_collection_allowed", "automatic_field_approval", "canonical_build"))
            or len(c["samples"]) > 6):
        raise ValueError("PILOT_ONLY_CONTRACT_REQUIRED")
    seen = set()
    for s in c["samples"]:
        u = urlsplit(s["url"])
        if (u.scheme != "https" or u.hostname not in HOSTS or u.username or u.password
                or u.port not in {None,443} or u.fragment or s["format"] not in {"html","pdf"}
                or not re.fullmatch(r"[a-z0-9_]+",s["id"]) or s["url"] in seen):
            raise ValueError("UNAPPROVED_OR_DUPLICATE_PUBLIC_URL")
        seen.add(s["url"])
    return c


def write(root, name, value):
    with (root/name).open("x",encoding="utf-8") as f:
        json.dump(value,f,ensure_ascii=False,indent=2)


def jsonl(root,name,values):
    with (root/name).open("x",encoding="utf-8") as f:
        for value in values:
            f.write(json.dumps(value,ensure_ascii=False)+"\n")


def seal(root,kind):
    write(root,"manifest.json",{"artifact_type":kind,"created_at":now(),
        "code_sha256":sha(Path(__file__).read_bytes()),"config_sha256":sha(CONFIG.read_bytes()),
        "files":{p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}})


def make_plan(output):
    if output.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    c=config()
    manifest_body=(REVIEW/"manifest.json").read_bytes()
    if sha(manifest_body)!=c["review_manifest_sha256"]:raise ValueError("REVIEW_MANIFEST_HASH_MISMATCH")
    manifest=json.loads(manifest_body)
    bodies={}
    for name,digest in manifest["files"].items():
        bodies[name]=(REVIEW/name).read_bytes()
        if sha(bodies[name])!=digest:raise ValueError("REVIEW_OUTPUT_HASH_MISMATCH")
    prices=list(map(json.loads,bodies["price_proposal_reviews.jsonl"].decode().splitlines()))
    ready=[p for p in prices if p["raw_review"]["status"]=="RAW_PRICE_SUPPORTED_EVENT_TERMS_SUPPORTED"]
    more=[p for p in prices if p["raw_review"]["status"]!="RAW_PRICE_SUPPORTED_EVENT_TERMS_SUPPORTED"]
    queue=json.loads(bodies["remaining_field_queue_by_ticker.json"])
    grouped={}
    for ticker,jobs in queue.items():
        for job in jobs:
            if job["proposed_value_pending_review"] is not None:continue
            h=job["vci_payload_sha256"]
            item=grouped.setdefault(h,{"ticker":ticker,"vci_payload_sha256":h,"original_sdk_row":job["original_sdk_row"],
                "missing_fields":[],"archived_evidence_ids":job["archived_official_evidence_ids"],
                "event_lifecycle":"UNVERIFIED_PLAN_VS_EXECUTED_EVENT","historical_identity":"UNVERIFIED",
                "discovery_channels":[],"canonical_approved":False})
            item["missing_fields"].append(job["field"])
    for item in grouped.values():
        needed=set(item["missing_fields"])
        if "ex_date" in needed:item["discovery_channels"].append("ISSUER_RECORD_DATE_NOTICE_OR_OFFICIAL_EX_DATE_CALENDAR_HNX_STOPPED")
        if needed & {"record_date","rights_subscription_price"}:item["discovery_channels"].append("VSDC_OR_ISSUER_OFFERING_DOCUMENT")
        row=item["original_sdk_row"]
        item["search_query_hint"]=f'{item["ticker"]} {row["public_date"][:4]} {"ngày giao dịch không hưởng quyền" if "ex_date" in needed else "giá chào bán cổ đông hiện hữu"}'
        item["search_hint_not_event_identity_or_publication_proof"]=True
    coverage=json.loads(bodies["missing_vci_coverage_queue.json"])
    summary={"stage":c["stage"],"status":"PLAN_READY_PILOT_PENDING","network_requests":0,
        "scope_tickers":1522,"well_supported_price_payload_rows":len(ready),"price_payload_rows_for_additional_review":len(more),
        "missing_field_payload_rows":len(grouped),"missing_field_tickers":len({x["ticker"] for x in grouped.values()}),
        "missing_field_tasks":dict(Counter(f for x in grouped.values() for f in x["missing_fields"])),
        "coverage_tickers":len(coverage),"pilot_samples":len(c["samples"]),
        "canonical_rows_written":0,"accepted_field_changes":0,"hnx_requests":0,
        "note":"Sources are discovery channels, not reconciliation priority. Missing dates do not establish that an action executed.",
        "input_review":str(REVIEW),"input_review_manifest_sha256":sha(manifest_body)}
    if len(ready)!=195 or len(more)!=49 or len(grouped)!=602 or len(coverage)!=182:raise ValueError("PLAN_SCOPE_MISMATCH")
    output.mkdir(parents=True)
    jsonl(output,"well_supported_price_candidates_195.jsonl",ready)
    jsonl(output,"additional_price_review_49.jsonl",more)
    jsonl(output,"missing_event_fields_602.jsonl",sorted(grouped.values(),key=lambda x:(x["ticker"],x["vci_payload_sha256"])))
    write(output,"coverage_review_182.json",coverage)
    write(output,"pilot_plan.json",c)
    write(output,"summary.json",summary)
    seal(output,"corporate-action-supplement-plan-v1")
    return summary


def pilot(plan,output,*,transport_factory=SupplementPilotTransport):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    c=config()
    m=json.loads((plan/"manifest.json").read_text(encoding="utf-8"))
    if m["config_sha256"]!=sha(CONFIG.read_bytes()):raise ValueError("PLAN_CONFIG_MISMATCH")
    for name,digest in m["files"].items():
        member=(plan/name).resolve()
        if not member.is_relative_to(plan.resolve()):raise ValueError("UNSAFE_PLAN_MEMBER")
        if sha(member.read_bytes())!=digest:raise ValueError("PLAN_FILE_HASH_MISMATCH")
    if json.loads((plan/"pilot_plan.json").read_text(encoding="utf-8"))!=c:raise ValueError("FROZEN_PLAN_CHANGED")
    output.mkdir(parents=True)
    t=transport_factory(output,max_requests=c["max_requests"],interval=c["interval_seconds"],timeout=c["timeout_seconds"],max_bytes=c["max_bytes"])
    results=[]
    stopped=set()
    for s in c["samples"]:
        family=urlsplit(s["url"]).hostname.removeprefix("www.")
        if family in stopped:
            results.append(s|{"status":"SKIPPED_SOURCE_STOP","request_attempted":False});continue
        result=s|{"request_attempted":True}
        try:
            value,receipt=t.fetch(s["url"],binary=s["format"]=="pdf")
            result.update(status="PUBLIC_DOCUMENT_RECEIVED",receipt=receipt,field_sufficiency="NOT_YET_EVALUATED")
            if s["format"]=="html":
                text=Document(value).root.text()
                with (output/f'{s["id"]}_text.txt').open("x",encoding="utf-8") as f:f.write(text)
        except SourceLimitation as exc:
            stopped.add(family)
            result.update(status="SOURCE_OR_TRANSPORT_LIMITATION",limitation=str(exc),field_sufficiency="UNDETERMINED")
        results.append(result)
        write(output,f'{s["id"]}_result.json',result)
        print(json.dumps({"sample":s["id"],"status":result["status"]}),flush=True)
    summary={"stage":c["stage"],"status":"PARTIAL_SOURCE_CAPABILITY_REVIEW_REQUIRED",
        "network_request_attempts":len(t.requests),"public_documents_received":sum(r["status"]=="PUBLIC_DOCUMENT_RECEIVED" for r in results),
        "results":results,"hnx_requests":0,"bulk_collection_started":False,
        "canonical_rows_written":0,"accepted_field_changes":0,"pit_status":"NOT_PROMOTED","identity_status":"UNVERIFIED",
        "plan_manifest_sha256":sha((plan/"manifest.json").read_bytes()),"discovery_search_queries_not_in_network_request_attempts":True}
    write(output,"requests.json",t.requests)
    write(output,"summary.json",summary)
    seal(output,"corporate-action-supplement-source-pilot-v1")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest="mode",required=True)
    p=subs.add_parser("plan");p.add_argument("--output",type=Path,required=True)
    p=subs.add_parser("pilot");p.add_argument("--plan",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    result=make_plan(a.output.resolve()) if a.mode=="plan" else pilot(a.plan.resolve(),a.output.resolve())
    print(json.dumps(result,ensure_ascii=False,indent=2))
