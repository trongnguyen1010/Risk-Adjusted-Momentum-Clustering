"""Discover and freeze the C6 CafeF expansion universe without crawling history."""
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.cafef_expansion import *
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.vnstock import KBS_BASE

LISTING_ENDPOINT = f"{KBS_BASE}/stock/search/data"

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--discover",action="store_true"); p.add_argument("--listing-json"); p.add_argument("--discovery-snapshot"); p.add_argument("--output",default="configs/data/cafef_expansion_v1"); a=p.parse_args(argv)
    if sum((a.discover, bool(a.listing_json), bool(a.discovery_snapshot))) != 1: p.error("choose exactly one discovery input")
    if a.discover:
        response=PublicJsonClient(timeout=20,attempts=2,min_interval=3.0,max_bytes=10_000_000).get_json(LISTING_ENDPOINT); payload=response["payload"]; evidence={"source":"kbs","endpoint":LISTING_ENDPOINT,"fetched_at":datetime.now(timezone.utc).isoformat(),"http_status":response["status"],"response_sha256":sha256_bytes(response["body"]),"response_bytes":len(response["body"]),"use":"ticker_exchange_display_name_instrument_type_discovery_only"}
    elif a.listing_json:
        source=Path(a.listing_json); body=source.read_bytes(); payload=json.loads(body); evidence={"source":"kbs","endpoint":LISTING_ENDPOINT,"fetched_at":None,"http_status":None,"response_sha256":sha256_bytes(body),"response_bytes":len(body),"use":"offline_listing_input"}
    else:
        snapshot=read_json(Path(a.discovery_snapshot)); evidence=snapshot["evidence"]
        rows=snapshot["normalized_current_stock_candidates"]+snapshot["excluded_listing_rows"]
        payload=[{"symbol":row.get("ticker"),"exchange":row.get("exchange"),"name":row.get("company_name"),"type":row.get("instrument_type")} for row in rows]
    current=read_json(ROOT/"configs/data/m1_scale.universe.v1.json")
    with (ROOT/"docs/crawl/plans/cafef_c1_prep_v1/cafef_c1_candidate_universe.csv").open(encoding="utf-8") as h: identities=list(csv.DictReader(h))
    plan=freeze_plan(payload,current,identities); out=ROOT/a.output; out.mkdir(parents=True,exist_ok=True)
    contract={"expansion_id":EXPANSION_ID,"execution_version":EXECUTION_VERSION,"source":"cafef","endpoint":TRADE_HISTORY_ENDPOINT,"page_size":PAGE_SIZE,"concurrency":1,"minimum_interval_seconds":3.0,"timeout_seconds":20,"attempts":2,"retry_http_statuses":sorted(RETRYABLE),"hard_stop_http_statuses":sorted(HARD_STOP),"hard_stop_markers":["CAPTCHA","Cloudflare","managed challenge","access denied"],"max_response_bytes":5000000,"maximum_pages_per_ticker":100,"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"comparison_snapshot":COMPARISON_SNAPSHOT,"safety_overlap_pages":1,"normalization":"CENTRAL_C8_ONLY","null_to_zero":False,"zero_volume_observation":"OBSERVED_ZERO_VOLUME"}
    write_json(out/"crawl_contract.json",contract)
    universe={"expansion_id":EXPANSION_ID,"execution_version":EXECUTION_VERSION,"selection_frozen_pre_crawl":True,"target_count":600,"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"comparison_snapshot":COMPARISON_SNAPSHOT,"discovery_evidence":evidence,"importance_evidence":"UNAVAILABLE_NOT_INVENTED","securities":plan["selected"]}
    write_json(out/"universe.json",universe); write_json(out/"discovery_evidence.json",evidence)
    discovered, discovery_excluded = normalized_listing(payload)
    write_json(out/"discovery_snapshot.json",{"evidence":evidence,"normalized_current_stock_candidates":discovered,"excluded_listing_rows":discovery_excluded})
    rank_fields=["priority_rank","security_id","ticker","exchange","company_name","instrument_type","selection_status","priority_tier","index_importance_signal","market_importance_signal","exchange_signal","history_signal","identity_signal","known_provider_evidence","duplicate_identity_status","selection_reason"]
    write_csv(out/"priority_ranking.csv",plan["ranking"],rank_fields); write_csv(out/"reserve.csv",plan["reserve"],["security_id","ticker","exchange","company_name","instrument_type","selection_status","priority_tier","index_importance_signal","market_importance_signal","exchange_signal","history_signal","identity_signal","known_provider_evidence","duplicate_identity_status","selection_reason"]); write_csv(out/"request_estimates.csv",plan["estimates"],list(plan["estimates"][0]))
    uh=sha256_file(out/"universe.json"); ch=sha256_file(out/"crawl_contract.json"); assignments=[]
    for index,bucket in enumerate(plan["workers"],1):
        aid=f"{EXPANSION_ID}-{bucket['worker_id']}"; rows=bucket["rows"]
        assignment={"expansion_id":EXPANSION_ID,"assignment_id":aid,"worker_id":bucket["worker_id"],"shard_index":index,"source":"cafef","endpoint":TRADE_HISTORY_ENDPOINT,"git_branch":"m1-cafef-primary-experiment","git_commit":"FROZEN_BY_EXECUTION_VERSION","execution_version":EXECUTION_VERSION,"universe_hash":uh,"crawl_contract_hash":ch,"security_ids":[r["security_id"] for r in rows],"tickers":[r["ticker"] for r in rows],"expected_symbol_count":len(rows),"estimated_pages":bucket["load"],"estimated_requests":bucket["load"],"target_start":TARGET_START,"target_collection_end":TARGET_COLLECTION_END,"comparison_snapshot":COMPARISON_SNAPSHOT,"page_size":PAGE_SIZE,"minimum_interval_seconds":3.0,"timeout_seconds":20,"attempts":2}
        assignment["assignment_sha256"]=assignment_digest(assignment); path=out/f"worker-{index:02d}.json"; write_json(path,assignment); assignments.append({"assignment_id":aid,"worker_id":bucket["worker_id"],"path":path.name,"sha256":assignment["assignment_sha256"],"symbols":len(rows),"estimated_requests":bucket["load"]})
    write_json(out/"index.json",{"expansion_id":EXPANSION_ID,"execution_version":EXECUTION_VERSION,"git_branch":"m1-cafef-primary-experiment","git_commit_contract":"FROZEN_EXECUTION_VERSION_AVOIDS_RECURSIVE_COMMIT_HASH","universe_sha256":uh,"crawl_contract_sha256":ch,"expected_assignment_count":5,"assignments":assignments})
    print(json.dumps({"selected":len(plan["selected"]),"reserve":len(plan["reserve"]),"ranking":len(plan["ranking"]),"current_excluded":sum(r["selection_status"]=="CURRENT_500_EXCLUDED" for r in plan["ranking"]),"identity_duplicate_excluded":sum(r["selection_status"]=="IDENTITY_DUPLICATE_EXCLUDED" for r in plan["ranking"]),"workers":assignments,"network_requests":1 if a.discover else 0},indent=2))
if __name__=="__main__": raise SystemExit(main())
