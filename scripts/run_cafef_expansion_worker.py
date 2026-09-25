"""Run one frozen C6 CafeF acquisition shard or validate it with zero network."""
import argparse, json, sys, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.cafef_expansion import *

def now(): return datetime.now(timezone.utc).isoformat()
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assignment",required=True); mode=p.add_mutually_exclusive_group(required=True); mode.add_argument("--dry-run",action="store_true"); mode.add_argument("--execute",action="store_true"); p.add_argument("--resume"); a=p.parse_args(argv)
    ap=(ROOT/a.assignment).resolve(); assignment,universe,contract=validate_assignment(ROOT,ap)
    if a.dry_run:
        print("READINESS=PASS\nnetwork_requests=0"); return 0
    run_id=a.resume or ("run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]); run_dir=safe_run_directory(ROOT,assignment,run_id)
    if a.resume:
        if not run_dir.is_dir(): raise ValueError("resume run does not exist")
        run=read_json(run_dir/"run.json")
        for key,value in (("assignment_sha256",assignment["assignment_sha256"]),("universe_sha256",assignment["universe_hash"]),("crawl_contract_sha256",assignment["crawl_contract_hash"]),("adapter_version",ADAPTER_VERSION)):
            if run.get(key)!=value: raise ValueError(f"resume {key} mismatch")
        verify_existing_raw(run_dir,ADAPTER_VERSION); state=read_json(run_dir/"state.json")
    else:
        run_dir.mkdir(parents=True,exist_ok=False); started=now(); run={"run_id":run_id,"started_at":started,"finished_at":None,"status":"RUNNING","assignment_sha256":assignment["assignment_sha256"],"universe_sha256":assignment["universe_hash"],"crawl_contract_sha256":assignment["crawl_contract_hash"],"adapter_version":ADAPTER_VERSION,"network_requests":0}; write_json(run_dir/"run.json",run); write_json(run_dir/"assignment.json",assignment); write_json(run_dir/"crawl_contract.json",contract); state={"tickers":{ticker:{"status":"NOT_STARTED","next_page":1,"pages":0} for ticker in assignment["tickers"]},"hard_stop_events":[]}; write_json(run_dir/"state.json",state)
    last_request=0.0; stop_all=False
    for ticker in assignment["tickers"]:
        item=state["tickers"][ticker]
        if item["status"]=="COMPLETE": continue
        item["status"]="RUNNING"; write_json(run_dir/"state.json",state)
        while True:
            page=item["next_page"]; time.sleep(max(0,contract["minimum_interval_seconds"]-(time.monotonic()-last_request))); last_request=time.monotonic()
            if page>contract["maximum_pages_per_ticker"]:
                item["status"]="FAILED"; item["error"]="MAXIMUM_PAGES_EXCEEDED_WITHOUT_BOUNDARY"; break
            try: body,status,url=acquire_page(ticker,page,contract)
            except RuntimeError as exc:
                item["status"]="HARD_STOP"; state["hard_stop_events"].append({"ticker":ticker,"page_index":page,"event":str(exc),"at":now()}); stop_all=True; break
            except Exception as exc:
                item["status"]="FAILED"; item["error"]=f"{type(exc).__name__}: {exc}"; break
            run["network_requests"]+=1; rows=page_rows(body); raw=run_dir/"raw"/ticker/f"page-{page:03d}.json"; immutable_write(raw,body)
            dates=[]
            for row in rows:
                try: dates.append(cafef_trade_date(row["TradeDate"]))
                except Exception: pass
            meta={"ticker":ticker,"page_index":page,"page_size":PAGE_SIZE,"url":url,"http_status":status,"fetched_at":now(),"sha256":sha256_bytes(body),"bytes":len(body),"adapter_version":ADAPTER_VERSION,"source_endpoint":TRADE_HISTORY_ENDPOINT,"observation_semantics":[classify_observation(row) for row in rows]}; immutable_write(raw.with_name(raw.stem+".metadata.json"),canonical_bytes(meta))
            item.update(next_page=page+1,pages=item["pages"]+1,oldest_observed=min(dates) if dates else item.get("oldest_observed")); write_json(run_dir/"run.json",run); write_json(run_dir/"state.json",state)
            if not rows or (dates and min(dates)<=TARGET_START): item["status"]="COMPLETE"; item["completion_reason"]="EMPTY_PROVIDER_BOUNDARY" if not rows else "TARGET_START_REACHED"; break
        write_json(run_dir/"state.json",state)
        if stop_all: break
    for item in state["tickers"].values():
        if item["status"]=="RUNNING": item["status"]="PARTIAL"
    run.update(finished_at=now(),status="HARD_STOP" if stop_all else ("COMPLETE" if all(x["status"]=="COMPLETE" for x in state["tickers"].values()) else "PARTIAL")); write_json(run_dir/"state.json",state); write_json(run_dir/"run.json",run)
    files={str(p.relative_to(run_dir)).replace("\\","/"):sha256_file(p) for p in run_dir.rglob("*") if p.is_file() and p.name!="manifest.json"}; write_json(run_dir/"manifest.json",{"run_id":run_id,"files":files}); print(json.dumps({"run_id":run_id,"status":run["status"],"network_requests":run["network_requests"]},indent=2)); return 0 if run["status"]=="COMPLETE" else 2
if __name__=="__main__": raise SystemExit(main())
