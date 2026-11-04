"""Kiểm kê VSDC cache offline trước khi đề xuất bất kỳ acquisition bổ sung nào."""
import argparse
from collections import Counter,defaultdict,deque
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path,PureWindowsPath
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_cache_audit import document_view,search_links,provider_id,candidate,assess_field
from delta_t1.ingestion.corporate_action_offline_reconcile import category,valid_fields
from delta_t1.ingestion.corporate_action_sources import now

CONFIG=ROOT/"configs/data/corporate_action_cache_audit_v1.json"
PLAN=ROOT/"tmp/ca_supplement_plan_20261102_v1"
TIMING=ROOT/"tmp/ca_vsdc_reparse_20261101_v3"


def sha(body):return hashlib.sha256(body).hexdigest()


def inside(base,name):
    # Sealed manifests use relative names. Validate lexically rather than
    # resolving every file through Windows filesystem/antivirus middleware.
    rel=PureWindowsPath(name)
    if rel.drive or rel.root or ".." in rel.parts:raise ValueError("INPUT_PATH_ESCAPE")
    return base.joinpath(*rel.parts)


def bounded_reads(function,items,workers=8):
    """Local file I/O only; keep at most 2*workers bodies in flight, in order."""
    iterator=iter(items)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending=deque()
        for _ in range(2*workers):
            item=next(iterator,None)
            if item is not None:pending.append((item,pool.submit(function,item)))
        while pending:
            item,future=pending.popleft()
            yield item,future.result()
            following=next(iterator,None)
            if following is not None:pending.append((following,pool.submit(function,following)))


def run(output):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    inputs={}
    def read(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError(f"INPUT_HASH_MISMATCH: {path}")
        inputs[path.relative_to(ROOT).as_posix()]={"sha256":digest,"size_bytes":len(body)}
        return body
    print(json.dumps({"stage":"OFFLINE_CACHE_START","network_requests":0}),flush=True)
    config=json.loads(read(CONFIG))
    if config["network_requests"]!=0 or config["canonical_build"] or config["automatic_field_approval"]:
        raise ValueError("OFFLINE_DIAGNOSTIC_ONLY")
    pm=json.loads(read(PLAN/"manifest.json",config["plan_manifest_sha256"]))
    tm=json.loads(read(TIMING/"manifest.json",config["vsdc_timing_manifest_sha256"]))
    planfiles={name:read(inside(PLAN,name),digest) for name,digest in pm["files"].items()}
    gaps=[json.loads(x) for x in planfiles["missing_event_fields_602.jsonl"].splitlines() if x.strip()]
    reviews=[json.loads(x) for x in planfiles["additional_price_review_49.jsonl"].splitlines() if x.strip()]
    coverage=json.loads(planfiles["coverage_review_182.json"])
    tasks=[]
    for bucket,rows in [("MISSING_FIELDS",gaps),("ADDITIONAL_PRICE_REVIEW",reviews)]:
        for r in rows:
            tasks.append(r|{"bucket":bucket,"category":category(r["original_sdk_row"]),
                "requested_fields":r.get("missing_fields",["rights_subscription_price"])})
    if len({r["vci_payload_sha256"] for r in tasks})!=len(tasks):raise ValueError("OVERLAPPING_PAYLOAD_TASKS")
    wanted={r["category"] for r in tasks};raw_index=defaultdict(list);ledgers=[];source_manifests=[]
    for name,entry in tm["inputs_read"].items():
        if not name.endswith("/manifest.json"):continue
        path=inside(ROOT,name);manifest=json.loads(read(path,entry["sha256"]));source_manifests.append(name)
        for rel,digest in manifest["files"].items():
            actual=inside(path.parent,rel)
            if rel.endswith(".bin"):raw_index[digest].append(actual)
            if rel.endswith("/requests.json") or rel=="requests.json":ledgers.append((actual,digest))
    receipts={};error_receipts=[]
    print(json.dumps({"stage":"MANIFEST_INDEXED","source_manifests":len(source_manifests),"ledger_files":len(ledgers)}),flush=True)
    for ledger_number,(path,digest) in enumerate(ledgers,1):
        data=json.loads(read(path,digest))
        if not isinstance(data,list):raise ValueError("REQUEST_LEDGER_LIST_REQUIRED")
        for index,r in enumerate(data):
            url=r.get("url","");u=urlsplit(url)
            if u.hostname!="vsdc.vn":continue
            role="ARTICLE" if provider_id(url) else "SEARCH" if u.path=="/vi/search" else "OTHER"
            if role=="OTHER":continue
            if r.get("status")!=200 or not r.get("source_hash"):
                error_receipts.append({"ledger":path.relative_to(ROOT).as_posix(),"index":index,"receipt":r});continue
            key=(url,r["source_hash"])
            if key not in receipts:
                receipts[key]={"url":url,"source_hash":r["source_hash"],"role":role,"ledger_references":[]}
            receipts[key]["ledger_references"].append({"path":path.relative_to(ROOT).as_posix(),"index":index})
        if ledger_number%500==0:print(json.dumps({"stage":"READ_LEDGER","files":ledger_number,"total":len(ledgers)}),flush=True)
    normalized=defaultdict(lambda:defaultdict(list))
    name="reparsed_vsdc_observations_unique.jsonl"
    for line in read(TIMING/name,tm["outputs_created"][name]["sha256"]).splitlines():
        if not line.strip():continue
        r=json.loads(line);fields=valid_fields(r);kind=fields.get("event_type")
        normalized[r["source_hash"]][kind].append({"observation_id":r["observation_id"],**fields})
    output.mkdir(parents=True)
    def write(name,value):
        with (output/name).open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2)
    def jsonl(name,rows):
        with (output/name).open("x",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    views={};docs=[];links=[];integrity=[];parsing=[]
    unique={(r["role"],r["source_hash"]):r for r in receipts.values()}
    def load_raw(r):
        paths=raw_index.get(r["source_hash"],[])
        for path in paths:
            try:return read(path,r["source_hash"]),path,None
            except FileNotFoundError:continue
        return None,None,"RAW_PATH_MISSING" if paths else "NO_RAW_PATH_IN_PINNED_MANIFESTS"
    with (output/"parsed_raw_views.jsonl").open("x",encoding="utf-8") as checkpoint:
        for index,(r,(body,path,error)) in enumerate(bounded_reads(load_raw,unique.values()),1):
            digest=r["source_hash"];cache_key=(r["role"],digest)
            if error:
                integrity.append({"source_hash":digest,"reason":error});views[cache_key]=None;continue
            try:
                view=document_view(body,r["url"],wanted) if r["role"]=="ARTICLE" else search_links(body,r["url"])
            except (UnicodeError,ValueError,IndexError) as exc:
                parsing.append({"source_hash":digest,"url":r["url"],"error":str(exc)});view=None
            views[cache_key]=(view,path.relative_to(ROOT).as_posix())
            checkpoint.write(json.dumps({"role":r["role"],"source_hash":digest,"raw_path":views[cache_key][1],"view":view},ensure_ascii=False)+"\n")
            if index%500==0:
                checkpoint.flush()
                print(json.dumps({"stage":"OFFLINE_CACHE_INDEX","unique_bodies_processed":index,"total":len(unique)}),flush=True)
    for r in receipts.values():
        digest=r["source_hash"];cache_key=(r["role"],digest)
        if views[cache_key] is None:continue
        view,raw_path=views[cache_key]
        if view is None:continue
        if r["role"]=="ARTICLE" and isinstance(view,dict):
            docs.append(view|{"document_id":sha((r["url"]+digest).encode()),"source_url":r["url"],
                "provider_article_id":provider_id(r["url"]),"source_hash":digest,"raw_path":raw_path,
                "ledger_references":r["ledger_references"],"legacy":dict(normalized.get(digest,{}))})
        elif r["role"]=="SEARCH" and isinstance(view,list):
            for link in view:links.append(link|{"search_url":r["url"],"search_source_hash":digest,"raw_path":raw_path})
    cached_ids={d["provider_article_id"] for d in docs};cached_urls={d["source_url"] for d in docs}
    discovered={}
    for link in links:
        if link["url"] in discovered:continue
        discovered[link["url"]]=link|{"exact_url_cached":link["url"] in cached_urls,
            "provider_article_id_cached":link["provider_article_id"] in cached_ids,
            "event_relevance_verified":False,"download_authorized":False}
    by_ticker=defaultdict(list);uncached=defaultdict(list)
    for doc in docs:
        if doc.get("ticker"):by_ticker[doc["ticker"]].append(doc)
    for link in discovered.values():
        if not link["provider_article_id_cached"] and link.get("ticker_title_hint"):
            uncached[link["ticker_title_hint"]].append(link)
    cases=[];counts=defaultdict(Counter)
    for task in tasks:
        candidates=[c for d in by_ticker[task["ticker"]] if (c:=candidate(task,d,config["time_hint_window_days"]))]
        unseen=[x for x in uncached[task["ticker"]] if task["category"] in x["kind_hints"]]
        fields={field:assess_field(field,candidates,len(unseen),len(by_ticker[task["ticker"]])) for field in task["requested_fields"]}
        for field,result in fields.items():counts[task["bucket"]][result["status"]]+=1
        cases.append({"ticker":task["ticker"],"vci_payload_sha256":task["vci_payload_sha256"],"bucket":task["bucket"],
            "category":task["category"],"original_sdk_row":task["original_sdk_row"],"fields":fields,
            "candidate_documents":candidates,"uncached_observed_link_candidates":unseen,
            "prior_raw_review":task.get("raw_review"),"prior_archived_evidence_ids":task.get("archived_evidence_ids",[]),
            "all_declared_ticker_cached_article_count":len(by_ticker[task["ticker"]]),
            "review_status":"MANUAL_REVIEW_REQUIRED","canonical_approved":False})
    coverage_result=[r|{"vsdc_cached_article_responses_with_declared_ticker":len(by_ticker[r["ticker"]]),
        "vsdc_cached_article_kind_counts":dict(Counter(k for d in by_ticker[r["ticker"]] for k in d["kinds"])),
        "observed_uncached_title_hint_links":len(uncached[r["ticker"]]),"no_event_confirmed":False} for r in coverage]
    for name,rows in [("raw_document_index.jsonl",docs),("discovered_article_links.jsonl",discovered.values()),
        ("field_cache_audit.jsonl",cases),("request_inventory.jsonl",receipts.values()),("failed_request_receipts.jsonl",error_receipts)]:jsonl(name,rows)
    write("coverage_cache_inventory_182.json",coverage_result)
    write("integrity_issues.json",integrity);write("parse_issues.json",parsing)
    summary={"stage":config["stage"],"status":"PASS" if not integrity and not parsing else "PARTIAL",
        "review_status":"MANUAL_REVIEW_REQUIRED","network_requests":0,"hnx_network_requests":0,
        "canonical_fields_approved":0,"canonical_build":False,"pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED",
        "scope":"FULL_VSDC_RECEIPTS_IN_FOUR_ORIGINAL_SHARDS_AND_BOOTSTRAP20; OTHER_SOURCE_CACHE_NOT_REAUDITED",
        "count_unit":"response=(URL,SHA256); payload=distinct VCI SDK row hash; field_task=(payload,field)",
        "source_manifest_count":len(source_manifests),"request_ledger_files":len(ledgers),
        "receipt_responses_by_role":dict(Counter(r["role"] for r in receipts.values())),
        "cached_article_responses":len(docs),"cached_article_unique_body_hashes":len({d["source_hash"] for d in docs}),
        "cached_article_unique_provider_ids":len(cached_ids),"raw_layout_counts":dict(Counter(d["layout"] for d in docs)),
        "document_role_counts":dict(Counter(d.get("document_role","UNRECOGNIZED") for d in docs)),
        "articles_without_declared_ticker":sum(not d.get("ticker") for d in docs),
        "article_responses_not_in_prior_normalized_stream":sum(not d["legacy"] for d in docs),
        "integrity_issue_count":len(integrity),"parse_issue_count":len(parsing),
        "distinct_observed_article_urls":len(discovered),"uncached_observed_provider_ids":len({x["provider_article_id"] for x in discovered.values() if not x["provider_article_id_cached"]}),
        "missing_payload_count":len(gaps),"missing_ticker_count":len({r["ticker"] for r in gaps}),
        "missing_fields_before":dict(Counter(f for r in gaps for f in r["missing_fields"])),
        "missing_fields_after_approval":dict(Counter(f for r in gaps for f in r["missing_fields"])),
        "additional_price_review_payloads":len(reviews),"audited_union_payloads":len(cases),
        "field_task_dispositions_by_bucket":{k:dict(v) for k,v in counts.items()},
        "missing_payloads_with_any_raw_field_at_dated_anchor":sum(r["bucket"]=="MISSING_FIELDS" and any(f["raw_field_support_document_ids"] for f in r["fields"].values()) for r in cases),
        "missing_payloads_with_any_weak_field_candidate":sum(r["bucket"]=="MISSING_FIELDS" and any(f["status"]=="CACHED_FIELD_CANDIDATE_EVENT_LINK_UNVERIFIED" for f in r["fields"].values()) for r in cases),
        "missing_payloads_with_observed_uncached_links":sum(r["bucket"]=="MISSING_FIELDS" and bool(r["uncached_observed_link_candidates"]) for r in cases),
        "coverage_tickers_audited":len(coverage_result),"coverage_tickers_with_vsdc_cache":sum(r["vsdc_cached_article_responses_with_declared_ticker"]>0 for r in coverage_result),
        "limitations":["Raw field presence and date anchors do not approve economic event identity, lifecycle, revision or values.",
            "A title hint does not prove ticker identity. Update dates and 120-day window are retrieval hints only.",
            "Unrecognized layout/missing ticker and limited historical search pagination remain coverage gaps.",
            "No relevant cached document does not prove the document is absent on the source or that no event occurred.",
            "Already reviewed ABB/AAS/FIT issuer evidence remains in previous immutable artifacts; not reapproved or downloaded."]}
    write("summary.json",summary)
    files={p.name:sha(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    code_paths=[Path(__file__),ROOT/"src/delta_t1/ingestion/corporate_action_cache_audit.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_sources.py",ROOT/"src/delta_t1/ingestion/corporate_action_evidence_review.py",
        ROOT/"src/delta_t1/ingestion/corporate_action_offline_reconcile.py"]
    write("manifest.json",{"artifact_type":"corporate-action-cache-gap-audit-v1","created_at":now(),
        "inputs_verified":inputs,"files":files,"code_hashes":{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code_paths},
        "config_sha256":sha(CONFIG.read_bytes()),"network_requests":0,"canonical_build":False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path)
    run(parser.parse_args().output.resolve())
