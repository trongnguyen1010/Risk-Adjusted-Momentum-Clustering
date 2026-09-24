"""Offline C3-R2 audit of externally stored CafeF TradeHistoryNew raw pages.

This script deliberately has no HTTP client imports.  It reads external local
evidence, writes only lightweight derived reports, and never promotes data.
"""
import argparse, csv, hashlib, json, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.sources.cafef import (cafef_trade_date,
    classify_cafef_page_row, map_trade_history_row)

LEGACY_ROOT = Path(r"C:\Projects\Intern\SourceCode\data\raw\cafef")
OUT = ROOT / "artifacts/cafef_primary/tradehistory_local_reuse_v1"
PLAN = ROOT / "docs/crawl/plans/cafef_c1_history_v3/cafef_c1_history_v3_plan.csv"
PARENT = ROOT / "artifacts/cafef_primary/cafef-c2-c3-offline-20260924"
QUALITY = ROOT / "artifacts/cafef_primary/cafef-canonical-market-pilot-v1/quality_report.json"
CALENDAR = ROOT / "artifacts/cafef_primary/cafef-canonical-market-pilot-v1/trading_calendar.jsonl"

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
def read_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def quantile(values, p):
    if not values: return None
    values=sorted(values); return values[round((len(values)-1)*p)]

def endpoint_is_tradehistory(metadata):
    """Prove endpoint identity from request provenance, never filename."""
    return "TradeHistoryNew.ashx" in str(metadata.get("url", ""))

def validate_page(raw_path, metadata_path, target_tickers=None):
    result={"raw_path":str(raw_path),"metadata_path":str(metadata_path) if metadata_path else "",
            "classification":"VALID_RAW_PAGE","raw_sha256":"","symbol":"","page_index":"","page_size":""}
    if not metadata_path or not metadata_path.exists(): result["classification"]="MISSING_METADATA"; return result
    try: meta=json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception: result["classification"]="UNPARSEABLE"; return result
    req=meta.get("request", {}); result.update(symbol=req.get("symbol", meta.get("symbol", "")), page_index=req.get("page_index", ""), page_size=req.get("page_size", ""))
    # Endpoint proof is cheap and lets this audit avoid hashing irrelevant
    # PriceHistory pages in the legacy tree.
    if not endpoint_is_tradehistory(meta): result["classification"]="UNKNOWN_ENDPOINT"
    elif target_tickers is not None and str(result["symbol"]).upper() not in target_tickers:
        result["classification"]="OUT_OF_SCOPE_TICKER"
    else: result["raw_sha256"]=sha256(raw_path)
    if result["classification"] == "VALID_RAW_PAGE" and meta.get("sha256") != result["raw_sha256"]: result["classification"]="CHECKSUM_MISMATCH"
    elif not result["symbol"] or not result["page_index"] or not result["page_size"]: result["classification"]="UNPARSEABLE"
    return result, meta

def load_plan():
    result={}
    for r in csv.DictReader(PLAN.open(encoding="utf-8")):
        r["intervals"]=json.loads(r["identity_intervals"]); result[r["ticker"]]=r
    return result
def route(plan, ticker, day):
    matches=[x for x in plan[ticker]["intervals"] if x["effective_from"] <= day and (not x["effective_to"] or day <= x["effective_to"])]
    if len(matches)!=1: raise ValueError("IDENTITY_ROUTING_ERROR")
    return matches[0]["exchange"]
def signature(raw): return tuple(raw.get(k) for k in ("ClosePrice","AdjustPrice","Volume","TotalValue","AgreedVolume","AgreedValue","BasicPrice","Ceiling","Floor"))
def endpoint_date_classification(in_pricehistory, in_tradehistory, conflicting=False):
    if conflicting: return "CONFLICTING_TRADEHISTORY_LOCAL_EVIDENCE"
    if in_pricehistory and in_tradehistory: return "BOTH_ENDPOINTS"
    return "TRADEHISTORY_ONLY" if in_tradehistory else "PRICEHISTORY_ONLY"

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--legacy-root",type=Path,default=LEGACY_ROOT); parser.add_argument("--output",type=Path,default=OUT); args=parser.parse_args()
    out=args.output; out.mkdir(parents=True,exist_ok=True); plan=load_plan(); tickers=set(plan)
    inventory=[]; validation=[]; groups=defaultdict(list); runs=[]
    for run in sorted(p for p in args.legacy_root.iterdir() if p.is_dir()):
        raw=list(run.glob("*.json")); pages=[p for p in raw if not p.name.endswith(".metadata.json")]
        metas=list(run.glob("*.metadata.json")); seen=set(); fetched=[]
        for page in pages:
            # Legacy naming is used only as a cheap scope filter.  Endpoint
            # identity still comes exclusively from the sidecar URL below.
            parts=page.stem.split("-")
            guessed=parts[1].upper() if len(parts) >= 3 else ""
            if guessed not in tickers:
                validation.append({"run_id":run.name,"run_family":run.name.rsplit("-",2)[0],"raw_path":str(page),"metadata_path":"","classification":"OUT_OF_SCOPE_TICKER","raw_sha256":"","symbol":guessed,"page_index":"","page_size":""})
                continue
            meta_path=page.with_name(page.stem+".metadata.json")
            check=validate_page(page, meta_path, tickers); check, meta = check if isinstance(check,tuple) else (check,{})
            check.update(run_id=run.name, run_family=run.name.rsplit("-",2)[0]); validation.append(check)
            if check["classification"]!="VALID_RAW_PAGE" or check["symbol"].upper() not in tickers: continue
            seen.add(check["symbol"].upper()); fetched.append(meta.get("fetched_at", ""))
            try: payload=json.loads(page.read_text(encoding="utf-8")); rows=payload["Data"]
            except Exception: check["classification"]="UNPARSEABLE"; continue
            for i, rawrow in enumerate(rows):
                try:
                    if classify_cafef_page_row(rawrow.get("TradeDate"), int(check["page_index"]), i)=="CURRENT_SNAPSHOT": continue
                    mapped=map_trade_history_row(rawrow, check["symbol"], "UNKNOWN")
                    if mapped["trade_date"] < "2021-09-23" or mapped["trade_date"] > "2026-09-23": continue
                    exch=route(plan, check["symbol"].upper(), mapped["trade_date"])
                except Exception: continue
                mapped.update(security_id=plan[check["symbol"].upper()]["security_id"], ticker=check["symbol"].upper(), historical_exchange=exch,
                    source="cafef",source_endpoint="TradeHistoryNew.ashx",legacy_run_id=run.name,legacy_run_family=run.name.rsplit("-",2)[0],legacy_raw_path=str(page),legacy_metadata_path=str(meta_path),raw_sha256=check["raw_sha256"],fetched_at=meta.get("fetched_at"))
                groups[(mapped["ticker"],mapped["trade_date"])].append((signature(rawrow),mapped))
        inventory.append({"run_id":run.name,"run_family":run.name.rsplit("-",2)[0],"raw_page_count":len(pages),"metadata_page_count":len(metas),"tickers_observed":"|".join(sorted(seen)),"earliest_fetched_at":min(fetched,default=""),"latest_fetched_at":max(fetched,default="")})
    # Collapse exact copies, keep conflicts fail-closed.
    evidence=[]; conflicts=[]; conflict_keys=set()
    for key, entries in groups.items():
        by_sig=defaultdict(list)
        for sig,row in entries: by_sig[sig].append(row)
        if len(by_sig)>1:
            conflict_keys.add(key); values=list(by_sig.values()); a,b=values[0][0],values[1][0]
            conflicts.append({"ticker":key[0],"trade_date":key[1],"run_a":a["legacy_run_id"],"run_b":b["legacy_run_id"],"close_a":a["cafef_close_price"],"close_b":b["cafef_close_price"],"adjust_a":a["cafef_adjust_price"],"adjust_b":b["cafef_adjust_price"],"volume_a":a["matched_volume"],"volume_b":b["matched_volume"],"value_a":a["matched_value"],"value_b":b["matched_value"],"raw_hash_a":a["raw_sha256"],"raw_hash_b":b["raw_sha256"]})
        else:
            row=next(iter(by_sig.values()))[0]; row["supporting_provenance"]=[{"legacy_run_id":x["legacy_run_id"],"raw_sha256":x["raw_sha256"]} for x in next(iter(by_sig.values()))]; evidence.append(row)
    with (out/"tradehistory_evidence_index.jsonl").open("w",encoding="utf-8") as f:
        for r in evidence: f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    write_csv(out/"legacy_run_inventory.csv",inventory,list(inventory[0]) if inventory else ["run_id"])
    write_csv(out/"legacy_page_validation.csv",validation,["run_id","run_family","raw_path","metadata_path","classification","raw_sha256","symbol","page_index","page_size"])
    write_csv(out/"tradehistory_conflicts.csv",conflicts,["ticker","trade_date","run_a","run_b","close_a","close_b","adjust_a","adjust_b","volume_a","volume_b","value_a","value_b","raw_hash_a","raw_hash_b"])
    by_ticker=defaultdict(list)
    for r in evidence: by_ticker[r["ticker"]].append(r)
    coverage=[]
    for ticker,p in plan.items():
        rows=by_ticker[ticker]; dates={x["trade_date"] for x in rows}; coverage.append({"ticker":ticker,"legacy_runs_found":len({x["legacy_run_id"] for x in rows}),"valid_pages":sum(1 for x in validation if x["symbol"]==ticker and x["classification"]=="VALID_RAW_PAGE"),"normalized_rows":len(rows),"first_trade_date":min(dates,default=""),"last_trade_date":max(dates,default=""),"covers_2021_09_23":"2021-09-23" in dates,"covers_2026_09_15":"2026-09-15" in dates,"covers_2026_09_23":"2026-09-23" in dates,"has_2026_01_29":"2026-01-29" in dates,"has_2026_01_30":"2026-01-30" in dates})
    write_csv(out/"tradehistory_local_coverage_27.csv",coverage,list(coverage[0]))
    audits=[]
    for ticker,p in plan.items():
      for day in ("2026-01-29","2026-01-30"):
        rs=[x for x in by_ticker[ticker] if x["trade_date"]==day]; r=rs[0] if rs else {}
        audits.append({"security_id":p["security_id"],"ticker":ticker,"trade_date":day,"historical_exchange":route(plan,ticker,day),"tradehistory_present":bool(rs),"legacy_run_id":r.get("legacy_run_id",""),"ClosePrice":r.get("cafef_close_price",""),"AdjustPrice":r.get("cafef_adjust_price",""),"Volume":r.get("matched_volume",""),"AgreedVolume":r.get("put_through_volume",""),"TotalValue":r.get("matched_value",""),"AgreedValue":r.get("put_through_value",""),"raw_sha256":r.get("raw_sha256","")})
    write_csv(out/"jan_29_30_local_tradehistory_audit.csv",audits,list(audits[0]))
    # Parent integrity and date/semantic comparisons.
    parent_file=PARENT/"normalized_market_candidates.jsonl"; parent_hash=sha256(parent_file); parent_manifest=json.loads((PARENT/"manifest.json").read_text()); assert parent_manifest["output_hashes"]["normalized_market_candidates.jsonl"]==parent_hash
    price=[x for x in read_jsonl(parent_file) if x["ticker"] in tickers]; ph=defaultdict(dict)
    for x in price: ph[x["ticker"]][x["trade_date"]]=x
    feb=[]; missing_by=defaultdict(list)
    for block in json.loads(QUALITY.read_text())["market_feature_blockers"]["latest_253_session_window_missing_observations"]:
        for t in block["tickers"]:
            if t in {"ACV","QNS","VEA","VGI"}: missing_by[t].extend(block["missing_sessions"])
    for t,days in missing_by.items():
        for day in sorted(set(days)):
            rs=[x for x in by_ticker[t] if x["trade_date"]==day]; feb.append({"ticker":t,"trade_date":day,"expected_gap":True,"tradehistory_present":bool(rs),"conflict":(t,day) in conflict_keys,"legacy_run_id":rs[0]["legacy_run_id"] if rs else ""})
    write_csv(out/"upcom_feb_local_tradehistory_audit.csv",feb,list(feb[0]))
    endpoint=[]; diffs=[]; adj=[]; vv=[]; all_adjusted_rel=[]
    for t in plan:
        a=set(ph[t]); b={x["trade_date"] for x in by_ticker[t]}; endpoint.append({"ticker":t,"pricehistory_rows":len(a),"tradehistory_rows":len(b),"both_count":len(a&b),"tradehistory_only_count":len(b-a),"pricehistory_only_count":len(a-b),"union_count":len(a|b),"first_pricehistory_date":min(a,default=""),"last_pricehistory_date":max(a,default=""),"first_tradehistory_date":min(b,default=""),"last_tradehistory_date":max(b,default="")})
        rel=[]; exact=[]; values=[]
        for d in sorted(a|b):
            cls=endpoint_date_classification(d in a, d in b, (t,d) in conflict_keys)
            diagnosis=("MISSING_ON_CAFEF_PRICEHISTORY;AVAILABLE_ON_CAFEF_TRADEHISTORYNEW"
                       if cls=="TRADEHISTORY_ONLY" and d in {"2026-01-29","2026-01-30"} else "")
            diffs.append({"ticker":t,"trade_date":d,"classification":cls,"provider_gap_diagnosis":diagnosis})
            if d in a and d in b:
                tr=next(x for x in by_ticker[t] if x["trade_date"]==d); pr=ph[t][d]; av=tr["cafef_adjust_price"]; pv=pr.get("provider_adjusted_vnd")
                if av is not None and pv not in (None,0):
                    difference=abs(av-pv)/abs(pv); rel.append(difference); all_adjusted_rel.append(difference)
                for fld,tf,pf in (("volume","matched_volume","matched_volume_shares"),("negotiated_volume","put_through_volume","negotiated_volume_shares")):
                    if tr[tf] is not None and pr.get(pf) is not None: exact.append(tr[tf]==pr[pf])
                for tf,pf in (("matched_value","matched_value_vnd"),("put_through_value","negotiated_value_vnd")):
                    if tr[tf] is not None and pr.get(pf) not in (None,0): values.append(abs(tr[tf]-pr[pf])/abs(pr[pf]))
        ratios=[]
        for d in a & b:
            tr=next(x for x in by_ticker[t] if x["trade_date"]==d); pv=ph[t][d].get("provider_adjusted_vnd")
            if tr["cafef_adjust_price"] is not None and pv not in (None,0): ratios.append(tr["cafef_adjust_price"]/pv)
        adj.append({"ticker":t,"count":len(rel),"median_ratio":statistics.median(ratios) if ratios else "","median_relative_difference":statistics.median(rel) if rel else "","p95_relative_difference":quantile(rel,.95) if rel else "","max_relative_difference":max(rel) if rel else "","conflict_count":sum(1 for k in conflict_keys if k[0]==t)})
        vv.append({"ticker":t,"integer_volume_exact_equality_rate":sum(exact)/len(exact) if exact else "","value_median_relative_difference":statistics.median(values) if values else "","value_p95_relative_difference":quantile(values,.95) if values else "","value_max_relative_difference":max(values) if values else ""})
    write_csv(out/"endpoint_coverage_by_ticker.csv",endpoint,list(endpoint[0])); write_csv(out/"endpoint_date_differences.csv",diffs,list(diffs[0])); write_csv(out/"overlap_adjusted_price_summary.csv",adj,list(adj[0])); write_csv(out/"overlap_volume_value_summary.csv",vv,list(vv[0]))
    # Deterministic partial classification and planned-only fallback.
    fallback=[]; classifications=[]
    for c in coverage:
        t=c["ticker"]; status="LOCAL_COMPLETE_FOR_COMPARISON" if c["covers_2021_09_23"] and c["covers_2026_09_15"] else "LOCAL_PARTIAL_BUT_TARGET_GAPS_COVERED" if c["has_2026_01_29"] and c["has_2026_01_30"] else "LOCAL_INSUFFICIENT"
        if any(k[0]==t for k in conflict_keys): status="LOCAL_CONFLICTING"
        classifications.append({"ticker":t,"local_evidence_classification":status})
        if status in ("LOCAL_INSUFFICIENT","LOCAL_CONFLICTING"): fallback.append({"ticker":t,"missing_start":"2021-09-23","missing_end":"2026-09-15","reason":"CONFLICT_REQUIRES_FRESH_VERIFICATION" if status=="LOCAL_CONFLICTING" else "NO_LOCAL_TRADEHISTORY_RAW","suggested_endpoint":"TradeHistoryNew.ashx","estimated_pages":"","network_required":"YES"})
    write_csv(out/"network_fallback_plan.csv",fallback,["ticker","missing_start","missing_end","reason","suggested_endpoint","estimated_pages","network_required"])
    # Calendar report is intentionally denominator-only.
    calendar=[x for x in read_jsonl(CALENDAR) if x["is_open"]]; cal=defaultdict(set)
    for x in calendar: cal[x["exchange"]].add(x["trade_date"])
    calrows=[]
    for t,p in plan.items():
        end=min(max({x["trade_date"] for x in by_ticker[t]},default="2021-09-22"),"2026-09-15"); expected={d for d in cal[p["exchange"]] if "2021-09-23"<=d<=end}; a=set(ph[t])&expected; b={x["trade_date"] for x in by_ticker[t]}&expected
        calrows.append({"ticker":t,"evaluated_end":end,"expected_sessions":len(expected),"pricehistory_observed_sessions":len(a),"tradehistory_observed_sessions":len(b),"pricehistory_missing":len(expected-a),"tradehistory_missing":len(expected-b),"coverage_rate_pricehistory":len(a)/len(expected) if expected else "","coverage_rate_tradehistory":len(b)/len(expected) if expected else ""})
    write_csv(out/"calendar_coverage_by_ticker.csv",calrows,list(calrows[0]))
    decision="ENDPOINTS_REQUIRE_RECONCILIATION" if conflict_keys else "PRICEHISTORY_PRIMARY_TRADEHISTORY_FALLBACK"
    (out/"endpoint_decision.json").write_text(json.dumps({"decision":decision,"reason":"offline local evidence audit; no canonical promotion","network_requests":0},indent=2),encoding="utf-8")
    (out/"quality_report.json").write_text(json.dumps({"stage":"C3-R2","status":"PARTIAL" if fallback or conflict_keys else "PASS","network_requests":0,"canonical_mutations":0,"feature_rebuild":False,"legacy_run_folders_scanned":len(inventory),"valid_tradehistory_pages":sum(x["classification"]=="VALID_RAW_PAGE" for x in validation),"pilot_tickers_found":sum(bool(by_ticker[t]) for t in plan),"tradehistory_rows":len(evidence),"pricehistory_rows_compared":sum(len(ph[t]) for t in plan),"tradehistory_only_dates":sum(x["tradehistory_only_count"] for x in endpoint),"pricehistory_only_dates":sum(x["pricehistory_only_count"] for x in endpoint),"adjusted_price_median_relative_difference":statistics.median(all_adjusted_rel) if all_adjusted_rel else None,"adjusted_price_p95_relative_difference":quantile(all_adjusted_rel,.95),"adjusted_price_max_relative_difference":max(all_adjusted_rel) if all_adjusted_rel else None,"conflicts":len(conflicts),"parent_normalized_hash":parent_hash,"local_evidence_classifications":classifications},indent=2),encoding="utf-8")
    (out/"manifest.json").write_text(json.dumps({"stage":"C3-R2 LOCAL TRADEHISTORY RAW REUSE","legacy_evidence_root":str(args.legacy_root),"external_local_evidence_dependency":True,"network_requests":0,"canonical_mutations":0,"output_files":sorted(x.name for x in out.iterdir())},indent=2),encoding="utf-8")
if __name__ == "__main__": main()
