"""Run one C7 supplemental CafeF shard into a separate immutable raw namespace."""
import argparse, json, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.cafef_consolidation import SUPPLEMENTAL_ID,SUPPLEMENTAL_VERSION
from delta_t1.ingestion.cafef_expansion import *

def now(): return datetime.now(timezone.utc).isoformat()
def output_dir(run_id,shard_id):
    if not __import__('re').fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}",run_id): raise ValueError("unsafe run id")
    base=(ROOT/"data/raw/cafef_supplemental_v1").resolve(); result=(base/run_id/shard_id).resolve()
    if base not in result.parents: raise ValueError("unsafe supplemental output path")
    return result
def load_shard(path,expected_commit):
    shard=read_json(path); directory=path.parent; index=read_json(directory/"index.json"); contract=read_json(directory/"contract.json")
    clean={key:value for key,value in shard.items() if key!="shard_sha256"}
    if shard.get("shard_sha256")!=sha256_bytes(canonical_bytes(clean)): raise ValueError("shard hash mismatch")
    entry=next((row for row in index["shards"] if row["shard_id"]==shard.get("shard_id")),None)
    if not entry or entry["sha256"]!=shard["shard_sha256"]: raise ValueError("index shard mismatch")
    if shard.get("execution_version")!=SUPPLEMENTAL_VERSION or contract.get("supplemental_id")!=SUPPLEMENTAL_ID: raise ValueError("supplemental version mismatch")
    if shard.get("contract_sha256")!=sha256_file(directory/"contract.json"): raise ValueError("contract hash mismatch")
    tickers=[job["ticker"] for job in shard["jobs"]]
    if len(tickers)!=len(set(tickers)): raise ValueError("duplicate ticker in shard")
    for job in shard["jobs"]:
        if job["action"]=="CONTINUE_FROM_PAGE_N" and int(job["start_page"])!=int(job["last_page"])+1: raise ValueError("supplemental continuation must follow initial evidence exactly")
        if job["action"]=="START_FROM_1" and int(job["start_page"])!=1: raise ValueError("invalid fresh start page")
    commit=validate_git_state(ROOT,expected_commit); return shard,contract,commit
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--shard",required=True);p.add_argument("--expected-commit",required=True);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument("--dry-run",action="store_true");mode.add_argument("--execute",action="store_true");p.add_argument("--resume");a=p.parse_args(argv)
    shard,contract,commit=load_shard((ROOT/a.shard).resolve(),a.expected_commit)
    if a.dry_run: print("READINESS=PASS\nnetwork_requests=0");return 0
    run_id=a.resume or ("supplemental-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]); out=output_dir(run_id,shard["shard_id"])
    if a.resume:
        if not out.is_dir(): raise ValueError("resume run does not exist")
        run=read_json(out/"run.json");state=read_json(out/"state.json")
        if run.get("git_commit")!=commit or run.get("shard_sha256")!=shard["shard_sha256"] or run.get("adapter_version")!=ADAPTER_VERSION: raise ValueError("resume identity mismatch")
        verify_existing_raw(out,ADAPTER_VERSION)
    else:
        out.mkdir(parents=True,exist_ok=False);run={"run_id":run_id,"supplemental_id":SUPPLEMENTAL_ID,"shard_id":shard["shard_id"],"git_commit":commit,"shard_sha256":shard["shard_sha256"],"inventory_sha256":shard["inventory_sha256"],"adapter_version":ADAPTER_VERSION,"started_at":now(),"finished_at":None,"status":"RUNNING","network_requests":0};state={"jobs":{job["ticker"]:{"status":"NOT_STARTED","next_page":job["start_page"],"initial_provenance":{key:job[key] for key in ("worker_id","assignment_id","handoff_run_id","source_zip","source_zip_sha256","action","last_page")}} for job in shard["jobs"]},"hard_stop_events":[]};write_json(out/"run.json",run);write_json(out/"state.json",state);write_json(out/"shard.json",shard);write_json(out/"contract.json",contract)
    last_request=0.0;stop_all=False
    for ticker in [job["ticker"] for job in shard["jobs"]]:
        item=state["jobs"][ticker]
        if item["status"]=="COMPLETE":continue
        item["status"]="RUNNING";write_json(out/"state.json",state)
        while True:
            page=int(item["next_page"])
            if page>contract["maximum_pages_per_ticker"]:item.update(status="FAILED",error="MAXIMUM_PAGES_EXCEEDED_WITHOUT_BOUNDARY");break
            time.sleep(max(0,contract["minimum_interval_seconds"]-(time.monotonic()-last_request)));last_request=time.monotonic()
            try:body,status,url=acquire_page(ticker,page,contract)
            except RuntimeError as exc:item["status"]="HARD_STOP";state["hard_stop_events"].append({"ticker":ticker,"page_index":page,"event":str(exc),"at":now()});stop_all=True;break
            except Exception as exc:item.update(status="FAILED",error=f"{type(exc).__name__}: {exc}");break
            run["network_requests"]+=1;rows=page_rows(body);raw=out/"raw"/ticker/f"page-{page:03d}.json";immutable_write(raw,body);dates=[]
            for row in rows:
                try:dates.append(cafef_trade_date(row["TradeDate"]))
                except Exception:pass
            meta={"ticker":ticker,"page_index":page,"page_size":PAGE_SIZE,"url":url,"http_status":status,"fetched_at":now(),"sha256":sha256_bytes(body),"bytes":len(body),"adapter_version":ADAPTER_VERSION,"source_endpoint":TRADE_HISTORY_ENDPOINT,"supplemental_id":SUPPLEMENTAL_ID,"initial_provenance":item["initial_provenance"],"observation_semantics":[classify_observation(row) for row in rows]};immutable_write(raw.with_name(raw.stem+".metadata.json"),canonical_bytes(meta));item.update(next_page=page+1,oldest_observed=min(dates) if dates else item.get("oldest_observed"));write_json(out/"run.json",run);write_json(out/"state.json",state)
            if not rows or (dates and min(dates)<=TARGET_START):item["status"]="COMPLETE";item["completion_reason"]="EMPTY_PROVIDER_BOUNDARY" if not rows else "TARGET_START_REACHED";break
        write_json(out/"state.json",state)
        if stop_all:break
    for item in state["jobs"].values():
        if item["status"]=="RUNNING":item["status"]="PARTIAL"
    run.update(finished_at=now(),status="HARD_STOP" if stop_all else ("COMPLETE" if all(item["status"]=="COMPLETE" for item in state["jobs"].values()) else "PARTIAL"));write_json(out/"state.json",state);write_json(out/"run.json",run)
    files={str(path.relative_to(out)).replace("\\","/"):sha256_file(path) for path in out.rglob("*") if path.is_file() and path.name!="manifest.json"};write_json(out/"manifest.json",{"run_id":run_id,"supplemental_id":SUPPLEMENTAL_ID,"shard_id":shard["shard_id"],"files":files})
    print(json.dumps({"run_id":run_id,"status":run["status"],"network_requests":run["network_requests"]},indent=2));return 0 if run["status"]=="COMPLETE" else 2
if __name__=="__main__":raise SystemExit(main())
