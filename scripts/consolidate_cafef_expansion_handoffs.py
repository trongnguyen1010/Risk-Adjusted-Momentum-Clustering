"""Verify five immutable handoffs, build C7 inventory, and freeze a supplemental plan."""
import argparse, csv, json, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src")); sys.path.insert(0,str(ROOT/"scripts"))
from delta_t1.ingestion.cafef_consolidation import *
from delta_t1.ingestion.cafef_expansion import *
from verify_cafef_expansion_handoffs import verify_archive

INVENTORY_FIELDS=["ticker","security_id","worker_id","assignment_id","handoff_run_id","status_reported","acquisition_status","raw_page_count","first_page","last_page","oldest_observed_date","newest_observed_date","completion_reason","next_page_if_continuable","action","source_zip","source_zip_sha256","initial_page_sequence_contiguous"]
CANDIDATE_FIELDS=INVENTORY_FIELDS+["start_page","estimated_remaining_requests"]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--incoming",default="data/handoffs/cafef_expansion_v1/incoming"); p.add_argument("--expected-commit",required=True); p.add_argument("--artifact",default=f"artifacts/cafef_primary/{C7_ARTIFACT_ID}"); p.add_argument("--config",default="configs/data/cafef_supplemental_v1"); p.add_argument("--shards",type=int,default=3); a=p.parse_args(argv)
    incoming=ROOT/a.incoming; paths=sorted(incoming.glob("*.zip")); base=ROOT/"configs/data/cafef_expansion_v1"; index=read_json(base/"index.json"); universe=read_json(base/"universe.json"); contract=read_json(base/"crawl_contract.json")
    if len(paths)!=5: raise ValueError(f"expected five ZIPs, found {len(paths)}")
    verified=[verify_archive(path,index,universe,contract) for path in paths]; validate_handoff_commits([item[1] for item in verified],a.expected_commit); reserve={row["ticker"] for row in csv.DictReader((base/"reserve.csv").open(encoding="utf-8"))}; validate_handoff_set([item[0] for item in verified],index,universe,reserve)
    inventory=[]; worker_summaries=[]; provenance=[]
    for path in paths:
        rows,summary,source=inspect_handoff(path); inventory.extend(rows); worker_summaries.append(summary); provenance.append(source)
    if {row["ticker"] for row in inventory}!={row["ticker"] for row in universe["securities"]}: raise ValueError("inventory union mismatch")
    candidates,shards=build_supplemental_plan(inventory,a.shards); counts=Counter(row["acquisition_status"] for row in inventory)
    completion={"stage":"C7","result":"PASS","total_selected":600,"counts":{key:counts.get(key,0) for key in ("COMPLETE","ACQUISITION_PARTIAL","NOT_YET_ACQUIRED","ACQUISITION_FAILED","HARD_STOP_REVIEW")},"total_raw_pages":sum(int(row["raw_page_count"]) for row in inventory),"network_requests_already_spent":sum(row["network_requests"] for row in worker_summaries),"supplemental_candidates":len(candidates),"supplemental_runnable":sum(row["action"]!="MANUAL_REVIEW" for row in candidates),"supplemental_manual_review":sum(row["action"]=="MANUAL_REVIEW" for row in candidates),"supplemental_shards":a.shards,"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"history_policy":HISTORY_POLICY}
    artifact=ROOT/a.artifact; config=ROOT/a.config
    if artifact.exists() or config.exists(): raise ValueError("immutable C7 output already exists")
    artifact.mkdir(parents=True); config.mkdir(parents=True)
    outputs={"acquisition_inventory.csv":csv_bytes(sorted(inventory,key=lambda row:row["ticker"]),INVENTORY_FIELDS),"worker_summary.csv":csv_bytes(sorted(worker_summaries,key=lambda row:row["worker_id"]),list(worker_summaries[0])),"completion_summary.json":canonical_bytes(completion),"supplemental_candidates.csv":csv_bytes(candidates,CANDIDATE_FIELDS),"verification_report.json":canonical_bytes({"handoff_verification":"PASS","expected_commit":a.expected_commit,"source_handoffs":provenance}),"methodology_notes.md":("# C7 acquisition inventory\n\nInventory phân biệt acquisition completeness với market-session completeness. `NOT_YET_ACQUIRED`/`ACQUISITION_PARTIAL` không phải `MISSING_ON_TRADEHISTORYNEW`, suspension, not-listed hoặc confirmed provider gap. Empty provider page chỉ là neutral provider/history boundary. Supplemental crawl giữ null khác zero, không fabricate row, không timeline compression và không overwrite năm ZIP ban đầu.\n").encode("utf-8")}
    for name,body in outputs.items(): (artifact/name).write_bytes(body)
    manifest={"artifact_id":C7_ARTIFACT_ID,"stage":"C7","source_handoffs":provenance,"outputs":{name:sha256_bytes(body) for name,body in sorted(outputs.items())}}; write_json(artifact/"manifest.json",manifest)
    inventory_sha=sha256_file(artifact/"acquisition_inventory.csv"); candidates_sha=sha256_file(artifact/"supplemental_candidates.csv")
    supplemental_contract={"supplemental_id":SUPPLEMENTAL_ID,"execution_version":SUPPLEMENTAL_VERSION,"parent_expansion_id":EXPANSION_ID,"parent_git_commit":a.expected_commit,"parent_inventory_sha256":inventory_sha,"source_handoffs":provenance,"source":"cafef","endpoint":TRADE_HISTORY_ENDPOINT,"history_policy":HISTORY_POLICY,"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"comparison_snapshot":COMPARISON_SNAPSHOT,"page_size":PAGE_SIZE,"concurrency":1,"minimum_interval_seconds":3.0,"timeout_seconds":20,"attempts":2,"retry_http_statuses":sorted(RETRYABLE),"hard_stop_http_statuses":sorted(HARD_STOP),"hard_stop_markers":["CAPTCHA","Cloudflare","managed challenge","access denied"],"maximum_pages_per_ticker":100,"max_response_bytes":5000000,"raw_output_namespace":"data/raw/cafef_supplemental_v1","initial_evidence_mutation":"FORBIDDEN","null_to_zero":False,"zero_volume_observation":"OBSERVED_ZERO_VOLUME","timeline_compression":False,"fabricated_rows":False,"empty_page_semantics":"NEUTRAL_PROVIDER_HISTORY_BOUNDARY"}; write_json(config/"contract.json",supplemental_contract); (config/"supplemental_candidates.csv").write_bytes(outputs["supplemental_candidates.csv"])
    contract_sha=sha256_file(config/"contract.json"); shard_index=[]
    for bucket in shards:
        shard={"supplemental_id":SUPPLEMENTAL_ID,"shard_id":bucket["shard_id"],"execution_version":SUPPLEMENTAL_VERSION,"git_branch":"m1-cafef-primary-experiment","contract_sha256":contract_sha,"inventory_sha256":inventory_sha,"candidates_sha256":candidates_sha,"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"page_size":PAGE_SIZE,"expected_symbol_count":len(bucket["jobs"]),"estimated_requests":bucket["estimated_requests"],"jobs":[{key:row[key] for key in ("ticker","security_id","worker_id","assignment_id","handoff_run_id","source_zip","source_zip_sha256","action","start_page","last_page","estimated_remaining_requests")} for row in bucket["jobs"]]}; shard["shard_sha256"]=sha256_bytes(canonical_bytes({key:value for key,value in shard.items() if key!="shard_sha256"})); path=config/f"{bucket['shard_id']}.json"; write_json(path,shard); shard_index.append({"shard_id":bucket["shard_id"],"path":path.name,"sha256":shard["shard_sha256"],"symbols":len(bucket["jobs"]),"estimated_requests":bucket["estimated_requests"]})
    write_json(config/"index.json",{"supplemental_id":SUPPLEMENTAL_ID,"execution_version":SUPPLEMENTAL_VERSION,"contract_sha256":contract_sha,"inventory_sha256":inventory_sha,"candidates_sha256":candidates_sha,"manual_review_tickers":[row["ticker"] for row in candidates if row["action"]=="MANUAL_REVIEW"],"shards":shard_index})
    print(json.dumps(completion,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
