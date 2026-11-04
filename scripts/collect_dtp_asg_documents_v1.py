"""Cache-first, maximum6 public requests for DTP2021 and ASG2020 documents."""
import argparse
import hashlib
import json
from pathlib import Path,PureWindowsPath
import sys
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_sources import now,SourceLimitation
from delta_t1.ingestion.corporate_action_target_documents import TargetDocumentTransport,public_document_links
from delta_t1.ingestion.corporate_action_offline_reconcile import date_view,valid_fields
CONFIG=ROOT/"configs/data/corporate_action_dtp_asg_documents_v1.json"
sha=lambda b:hashlib.sha256(b).hexdigest()


def safe(base,name):
    rel=PureWindowsPath(name)
    if rel.drive or rel.root or ".." in rel.parts:raise ValueError("PATH_ESCAPE")
    return base.joinpath(*rel.parts)


def run(output,collect=False):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    inputs={}
    def pin(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError("INPUT_HASH_MISMATCH: "+str(path))
        inputs[path.relative_to(ROOT).as_posix()]=digest
        return body
    c=json.loads(pin(CONFIG))
    base=ROOT/"tmp/ca_cached26_review_20261102_v1";decision=ROOT/"tmp/ca_decision25_20261102_v2";cache=ROOT/"tmp/ca_cache_inventory_20261102_v4"
    bm=json.loads(pin(base/"manifest.json",c["cached26_manifest_sha256"]))
    pin(decision/"manifest.json",c["decision25_manifest_sha256"])
    cm=json.loads(pin(cache/"manifest.json",c["cache_inventory_manifest_sha256"]))
    by_hash={r["vci_payload_sha256"]:r for r in (json.loads(l) for l in pin(base/"reviewed_payloads_26.jsonl",bm["files"]["reviewed_payloads_26.jsonl"]).splitlines() if l.strip())}
    targets=[]
    for ticker,target in c["targets"].items():
        row=by_hash[target["payload_sha256"]]
        if row["ticker"]!=ticker or date_view(row["original_sdk_row"]["record_date"])!=target["record_date"]:raise ValueError("TARGET_EVENT_MISMATCH")
        targets.append(row)
    cached=[]
    for line in pin(cache/"raw_document_index.jsonl",cm["files"]["raw_document_index.jsonl"]).splitlines():
        if not line.strip():continue
        d=json.loads(line)
        if d.get("ticker") in c["targets"] or d.get("title_ticker_hint") in c["targets"]:cached.append(d)
    other=[]
    for ticker,shard in [("DTP",2),("ASG",0)]:
        folder=ROOT/f"data/corporate_actions/work/outputs/batch_shard_{shard}"
        rel=(folder/"manifest.json").relative_to(ROOT).as_posix();manifest=json.loads(pin(ROOT/rel,cm["inputs_verified"][rel]["sha256"]))
        name=f"source_receipts/{ticker}/observations.jsonl"
        for line in pin(folder/name,manifest["files"][name]).splitlines():
            if not line.strip():continue
            r=json.loads(line)
            if r.get("source_type")!="VSDC":other.append({"ticker_context":ticker,"source_type":r.get("source_type"),"source_url":r.get("source_url"),"valid_fields":valid_fields(r)})
    output.mkdir(parents=True)
    def dump(name,value):
        with (output/name).open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2)
    dump("cache_review.json",{"targets":targets,"prior_verified_vsdc_cached_article_responses":len(cached),
        "cached_articles":[{k:d[k] for k in ["document_id","source_url","source_hash","raw_path","ticker","title","record_dates","attachments"]} for d in cached],
        "other_normalized_source_rows":other,"cache_scope":"Pinned legacy VSDC index plus original DTP/ASG normalized source receipts; not all workspace documents.",
        "result":"No additional target field established by this cache review; acquire only scoped public document candidates."})
    docs=[];discovery=[];transport=TargetDocumentTransport(output,c);stops=set()
    def fetch(identifier,ticker,url,binary=False,role="PUBLIC_DISCLOSURE_PAGE"):
        host=urlsplit(url).hostname
        if host in stops or len(transport.requests)>=c["max_requests"]:
            docs.append({"id":identifier,"ticker":ticker,"url":url,"status":"SKIPPED_HOST_STOP_OR_BUDGET"});return None
        try:
            value,receipt=transport.fetch(url,binary=binary)
            docs.append({"id":identifier,"ticker":ticker,"url":url,"status":"PUBLIC_DOCUMENT_RECEIVED","format":"pdf" if binary else "html","role":role,"receipt":receipt})
            return value
        except SourceLimitation as exc:
            stops.add(host);docs.append({"id":identifier,"ticker":ticker,"url":url,"status":"SOURCE_STOP","reason":str(exc)})
            return None
    if collect:
        page=fetch("dtp_disclosure","DTP",c["dtp_page"])
        if page:
            links=public_document_links(page,c["dtp_page"],c);discovery.append({"source_url":c["dtp_page"],"links":links})
            for filename in c["dtp_attachment_names"]:
                eligible=sorted({l["url"] for l in links if l["allowed_target_document"] and urlsplit(l["url"]).path.rsplit("/",1)[-1]==filename})
                if len(eligible)==1:fetch("dtp_"+("offering_notice" if filename.startswith("TB-") else "schedule_resolution"),"DTP",eligible[0],True,"ISSUER_DOCUMENT_COPY_ON_BROKER_DISCLOSURE")
        page=fetch("asg_disclosure","ASG",c["asg_page"])
        if page:discovery.append({"source_url":c["asg_page"],"links":public_document_links(page,c["asg_page"],c),"sharepoint_links_followed":False})
        fetch("asg_offering_prospectus_copy","ASG",c["asg_prospectus_copy"],True,"ISSUER_PROSPECTUS_COPY_ON_MARKET_ARCHIVE")
    dump("requests.json",transport.requests);dump("documents.json",docs);dump("discovery.json",discovery)
    summary={"stage":c["stage"],"status":"DOCUMENTS_ACQUIRED_REVIEW_PENDING" if any(d.get("format")=="pdf" for d in docs) else "PARTIAL" if collect else "OFFLINE_CACHE_REVIEW_ONLY",
        "target_payloads":len(targets),"vsdc_cache_article_responses_reused":len(cached),"other_normalized_source_rows":len(other),
        "network_request_attempts":len(transport.requests),"discovery_web_requests":"Separate search/browser-tool discovery; not included in formal acquisition attempts and not instrumented as physical source requests.",
        "successful_pdf_documents":sum(d.get("format")=="pdf" for d in docs),"source_stops":sorted(stops),
        "tls_verification":True,"follow_redirects":False,"hnx_network_requests":0,"canonical_build":False,"accepted_field_changes":0,
        "pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED","prior_decision_packet_applied":False}
    dump("summary.json",summary)
    for name,digest in inputs.items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError("INPUT_CHANGED")
    code=[Path(__file__),ROOT/"src/delta_t1/ingestion/corporate_action_target_documents.py",ROOT/"src/delta_t1/ingestion/corporate_action_sources.py"]
    dump("manifest.json",{"artifact_type":"dtp-asg-target-document-acquisition-v1","created_at":now(),"inputs_verified":inputs,
        "files":{p.relative_to(output).as_posix():sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()},
        "code_hashes":{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code},"network_request_attempts":len(transport.requests),"canonical_build":False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);p.add_argument("--collect",action="store_true")
    a=p.parse_args();run(a.output.resolve(),a.collect)
