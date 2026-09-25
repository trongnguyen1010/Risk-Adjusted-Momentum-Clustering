"""Package one immutable CafeF expansion worker run as exactly one portable ZIP."""
import argparse, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.cafef_expansion import *

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--assignment",required=True); p.add_argument("--run-id",required=True); p.add_argument("--output-root",default="handoff"); a=p.parse_args(argv)
    assignment,universe,contract=validate_assignment(ROOT,(ROOT/a.assignment).resolve()); run_dir=safe_run_directory(ROOT,assignment,a.run_id); verify_existing_raw(run_dir,ADAPTER_VERSION); run=read_json(run_dir/"run.json"); state=read_json(run_dir/"state.json")
    files={}
    for fixed in ("run.json","assignment.json","crawl_contract.json"):
        files[fixed]=(run_dir/fixed).read_bytes()
    for path in sorted((run_dir/"raw").rglob("*")):
        if path.is_file(): files[path.relative_to(run_dir).as_posix()]=path.read_bytes()
    statuses={name:item["status"] for name,item in state["tickers"].items()}; report={"statuses":statuses,"completion_reasons":{name:item.get("completion_reason") for name,item in state["tickers"].items()}}
    files["worker_report.json"]=canonical_bytes(report)
    manifest={"expansion_id":assignment["expansion_id"],"assignment_id":assignment["assignment_id"],"worker_id":assignment["worker_id"],"git_commit":assignment["git_commit"],"execution_version":assignment["execution_version"],"assignment_sha256":assignment["assignment_sha256"],"universe_sha256":assignment["universe_hash"],"crawl_contract_sha256":assignment["crawl_contract_hash"],"run_id":run["run_id"],"started_at":run["started_at"],"finished_at":run["finished_at"],"ticker_count":len(statuses),"complete_tickers":sum(v=="COMPLETE" for v in statuses.values()),"partial_tickers":sum(v=="PARTIAL" for v in statuses.values()),"failed_tickers":sum(v=="FAILED" for v in statuses.values()),"hard_stop_events":state["hard_stop_events"],"network_requests":run["network_requests"],"raw_page_count":sum(n.endswith(".json") and not n.endswith("metadata.json") for n in files if n.startswith("raw/")),"archive_content_hash":{"algorithm":"sha256","scope":"all included files except checksums.sha256 and handoff_manifest.json","sha256":sha256_bytes(checksums_for_files(files))},"adapter_version":ADAPTER_VERSION}
    files["handoff_manifest.json"]=canonical_bytes(manifest); files["checksums.sha256"]=checksums_for_files(files)
    if any(not safe_archive_name(name) for name in files): raise ValueError("unsafe or secret-like archive path")
    if any(name.endswith(".json") and json_contains_secret_keys(body) for name,body in files.items()): raise ValueError("secret-like JSON key in handoff")
    out=(ROOT/a.output_root/assignment["expansion_id"]/(assignment["assignment_id"]+".zip")).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists(): raise ValueError("handoff archive already exists")
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o600<<16; z.writestr(info,body)
    print(out); return 0
if __name__=="__main__": raise SystemExit(main())
