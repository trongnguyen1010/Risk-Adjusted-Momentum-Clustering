"""Centrally verify five CafeF expansion worker ZIP handoffs without merging them."""
import argparse, csv, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.cafef_expansion import *

def verify_archive(path,index,universe,contract):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(not safe_archive_name(n) for n in names): raise ValueError(f"unsafe archive paths: {path.name}")
        required={"handoff_manifest.json","run.json","assignment.json","crawl_contract.json","worker_report.json","checksums.sha256"}
        if not required.issubset(names): raise ValueError(f"missing handoff files: {path.name}")
        bodies={n:z.read(n) for n in names}; sums=parse_checksums(bodies["checksums.sha256"])
        if set(sums)!=set(names)-{"checksums.sha256"}: raise ValueError("checksum coverage mismatch")
        for name,digest in sums.items():
            if sha256_bytes(bodies[name])!=digest: raise ValueError(f"modified archive file: {name}")
        manifest=json.loads(bodies["handoff_manifest.json"]); assignment=json.loads(bodies["assignment.json"]); archived_contract=json.loads(bodies["crawl_contract.json"]); run=json.loads(bodies["run.json"]); report=json.loads(bodies["worker_report.json"])
        if assignment_digest(assignment)!=assignment.get("assignment_sha256"): raise ValueError("assignment hash mismatch")
        expected=next((x for x in index["assignments"] if x["assignment_id"]==assignment.get("assignment_id")),None)
        if not expected or expected["worker_id"]!=assignment.get("worker_id") or expected["sha256"]!=assignment.get("assignment_sha256"): raise ValueError("wrong worker or assignment")
        if sha256_bytes(canonical_bytes(archived_contract))!=index["crawl_contract_sha256"]: raise ValueError("crawl contract mismatch")
        if any(manifest.get(k)!=assignment.get(a) for k,a in (("expansion_id","expansion_id"),("assignment_id","assignment_id"),("worker_id","worker_id"),("execution_version","execution_version"),("assignment_sha256","assignment_sha256"),("universe_sha256","universe_hash"),("crawl_contract_sha256","crawl_contract_hash"))): raise ValueError("manifest consistency mismatch")
        statuses=report.get("statuses",{}); raw_pages=sum(name.startswith("raw/") and name.endswith(".json") and not name.endswith("metadata.json") for name in names)
        if (manifest.get("adapter_version")!=ADAPTER_VERSION or manifest.get("run_id")!=run.get("run_id") or manifest.get("git_commit")!=run.get("git_commit")
                or manifest.get("network_requests")!=run.get("network_requests")
                or manifest.get("ticker_count")!=len(statuses)
                or manifest.get("complete_tickers")!=sum(value=="COMPLETE" for value in statuses.values())
                or manifest.get("partial_tickers")!=sum(value=="PARTIAL" for value in statuses.values())
                or manifest.get("failed_tickers")!=sum(value=="FAILED" for value in statuses.values())
                or manifest.get("raw_page_count")!=raw_pages): raise ValueError("handoff manifest/run/report mismatch")
        pages={}
        for name in names:
            if name.startswith("raw/") and name.endswith(".metadata.json"):
                meta=json.loads(bodies[name]); ticker=meta["ticker"]
                if ticker not in assignment["tickers"]: raise ValueError("raw ticker outside assignment")
                if meta["page_size"]!=PAGE_SIZE or meta["source_endpoint"]!=TRADE_HISTORY_ENDPOINT: raise ValueError("raw endpoint/page-size mismatch")
                raw_name=name.replace(".metadata.json",".json")
                if raw_name not in bodies or sha256_bytes(bodies[raw_name])!=meta["sha256"]: raise ValueError("modified raw response")
                pages.setdefault(ticker,[]).append(meta["page_index"])
        for ticker,seq in pages.items():
            if sorted(seq)!=list(range(1,max(seq)+1)): raise ValueError(f"page sequence gap: {ticker}")
        return assignment,manifest["git_commit"]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--incoming",default="data/handoffs/cafef_expansion_v1/incoming"); p.add_argument("--config",default="configs/data/cafef_expansion_v1"); p.add_argument("--expected-commit",required=True); a=p.parse_args(argv); cfg=ROOT/a.config; index=read_json(cfg/"index.json"); universe=read_json(cfg/"universe.json"); contract=read_json(cfg/"crawl_contract.json"); paths=sorted((ROOT/a.incoming).glob("*.zip"))
    if len(paths)!=5: raise ValueError(f"expected exactly five handoffs, found {len(paths)}")
    verified=[verify_archive(path,index,universe,contract) for path in paths]; assignments=[item[0] for item in verified]; validate_handoff_commits([item[1] for item in verified],a.expected_commit)
    reserve={r["ticker"] for r in csv.DictReader((cfg/"reserve.csv").open(encoding="utf-8"))}
    owners=validate_handoff_set(assignments,index,universe,reserve)
    print("HANDOFF_VERIFICATION=PASS\nassignments=5\ntickers=600"); return 0
if __name__=="__main__": raise SystemExit(main())
