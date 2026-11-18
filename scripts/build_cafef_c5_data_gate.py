"""Build the C5 V2 data gate from immutable C4 evidence and bounded recovery."""
import csv, hashlib, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OLD=Path(r"C:\Projects\Intern\SourceCode")
C4=ROOT/"artifacts/cafef_primary/cafef-tradehistory-500-evaluation-v1"
OUT=ROOT/"artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2"
OLD_CANON=OLD/"data/canonical/canonical-m1-scale-20260918T141019Z-7c003543"
RECOVERY_ROOT=ROOT/"data/raw/cafef"
CONFLICT_FIELDS=("raw_close","adj_close","reference_price","ceiling_price","floor_price","matched_volume_shares","negotiated_volume_shares","matched_value_vnd","negotiated_value_vnd")
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.features.market import build_features, latest_completed_snapshot_rows
from delta_t1.ingestion.cafef_market_semantics import READINESS_POLICY_V2, enrich_observed_row
from delta_t1.ingestion.sources.cafef import cafef_trade_date, classify_cafef_page_row, map_trade_history_row

def h(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def write_json(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False),encoding="utf-8")
def write_csv(path,data,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(data)
def conflict_signature(row):
    payload={field:row.get(field) for field in CONFLICT_FIELDS}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def verify_manifest(root):
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8-sig")); bad=[]
    for rel,want in manifest["outputs"].items():
        if h(root/rel)!=want: bad.append(rel)
    if bad: raise ValueError("C4 hash mismatch: "+",".join(bad))
    return manifest
def json_config():
    cfg=json.loads((OLD/"configs/features/market.example.json").read_text()); cfg.update(readiness_policy=READINESS_POLICY_V2,feature_set="delta_market_1.6.0")
    return cfg
def current_security(securities,sid,day):
    found=[x for x in securities if x["security_id"]==sid and x["valid_from"]<=day<(x["valid_to"] or "9999-12-31")]
    return found[0] if len(found)==1 else None
def latest_windows(securities,calendar,snapshot):
    by_exchange=defaultdict(list)
    for c in calendar:
        if c["is_open"] and c["trade_date"]<=snapshot: by_exchange[c["exchange"]].append(c["trade_date"])
    result={}
    for sid in sorted({x["security_id"] for x in securities}):
        days=set()
        for meta in (x for x in securities if x["security_id"]==sid):
            days.update(d for d in by_exchange[meta["exchange"]] if meta["valid_from"]<=d<(meta["valid_to"] or "9999-12-31"))
        result[sid]=sorted(days)[-253:]
    return result
def recovery_rows(securities):
    accepted=[]; provenance=[]; requests=0; target_tickers=set(); zero=positive=0; pages=Counter(); oldest={}; hard=[]
    for run in sorted(RECOVERY_ROOT.glob("c5-targeted-recovery-*")) if RECOVERY_ROOT.exists() else []:
        manifest_path=run/"manifest.json"
        if manifest_path.exists():
            m=json.loads(manifest_path.read_text()); requests+=m.get("network_requests",0); target_tickers.update(m.get("target_tickers",[])); pages.update(m.get("pages_by_ticker",{})); hard.extend(m.get("hard_stop_events",[]))
            for ticker,day in m.get("oldest_page_reached",{}).items(): oldest[ticker]=min(oldest.get(ticker,day),day)
        for meta_path in run.glob("*.metadata.json"):
            meta=json.loads(meta_path.read_text()); raw=meta_path.with_name(meta_path.name.replace(".metadata.json",".json"))
            if not raw.exists() or h(raw)!=meta.get("sha256") or "TradeHistoryNew.ashx" not in meta.get("url",""): continue
            payload=json.loads(raw.read_text()); ticker=meta["request"]["symbol"]; page=meta["request"]["page_index"]
            for pos,rr in enumerate(payload.get("Data",[])):
                if classify_cafef_page_row(rr.get("TradeDate"),page,pos)=="CURRENT_SNAPSHOT": continue
                day=cafef_trade_date(rr["TradeDate"]); sid=next((x["security_id"] for x in securities if x["ticker"]==ticker),None); sec=current_security(securities,sid,day) if sid else None
                if not sec: continue
                mapped=map_trade_history_row(rr,ticker,sec["exchange"])
                if mapped["cafef_adjust_price"] is None or mapped["cafef_adjust_price"]<=0 or mapped["cafef_close_price"] is None or mapped["cafef_close_price"]<=0: continue
                base={"security_id":sid,"ticker":ticker,"exchange":sec["exchange"],"trade_date":day,"raw_open":None,"raw_high":None,"raw_low":None,"raw_close":mapped["cafef_close_price"],"reference_price":mapped["reference_price"],"ceiling_price":mapped["ceiling_price"],"floor_price":mapped["floor_price"],"adj_close":mapped["cafef_adjust_price"],"adjustment_basis":"vendor_adjusted","matched_volume_shares":mapped["matched_volume"],"negotiated_volume_shares":mapped["put_through_volume"],"matched_value_vnd":mapped["matched_value"],"negotiated_value_vnd":mapped["put_through_value"],"available_at":day+"T17:00:00+07:00","source":"cafef","source_endpoint":"TradeHistoryNew.ashx","source_run_id":run.name,"raw_path":str(raw.relative_to(ROOT)),"raw_sha256":meta["sha256"],"fetched_at":meta.get("fetched_at"),"data_version":"CAFEF_TRADEHISTORY_500_CANDIDATE_V2","recovery_stage":"C5","recovery_reason":"LATEST_253_MISSING"}
                row=enrich_observed_row(base); accepted.append(row); p={"security_id":sid,"ticker":ticker,"trade_date":day,"source_run_id":run.name,"raw_path":str(raw.relative_to(ROOT)),"raw_sha256":meta["sha256"],"fetched_at":meta.get("fetched_at"),"recovery_reason":"LATEST_253_MISSING"}; provenance.append(p)
                if row["trading_activity_status"]=="OBSERVED_ZERO_VOLUME": zero+=1
                elif row["trading_activity_status"]=="ACTIVE": positive+=1
    return accepted,provenance,{"network_requests":requests,"target_tickers":sorted(target_tickers),"zero_rows_observed":zero,"positive_rows_observed":positive,"pages_by_ticker":dict(pages),"oldest_page_reached":oldest,"hard_stop_events":hard}

def main():
    verify_manifest(C4); c4quality=json.loads((C4/"quality_report.json").read_text()); snapshot=c4quality["comparison_snapshot_date"]
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"clean").mkdir(exist_ok=True)
    securities=list(rows(C4/"clean/securities.jsonl")); calendar=list(rows(C4/"clean/trading_calendar.jsonl")); benchmark=list(rows(C4/"clean/benchmark_daily.jsonl")); windows=latest_windows(securities,calendar,snapshot)
    recover,provenance,net=recovery_rows(securities); recovered_by_key=defaultdict(list)
    for r in recover: recovered_by_key[(r["security_id"],r["trade_date"])].append(r)
    prices=[]; existing={}; snapshot_rows={}; conflict_recovery=set()
    for raw in rows(C4/"clean/prices_daily.jsonl"):
        row=enrich_observed_row({**raw,"data_version":"CAFEF_TRADEHISTORY_500_CANDIDATE_V2"}); key=(row["security_id"],row["trade_date"]); existing[key]=row
    for key,candidates in recovered_by_key.items():
        signatures={json.dumps([x.get(k) for k in ("raw_close","adj_close","matched_volume_shares","negotiated_volume_shares","matched_value_vnd","negotiated_value_vnd")]) for x in candidates}
        if key in existing:
            old=existing[key]; oldsig=json.dumps([old.get(k) for k in ("raw_close","adj_close","matched_volume_shares","negotiated_volume_shares","matched_value_vnd","negotiated_value_vnd")])
            if any(s!=oldsig for s in signatures): conflict_recovery.add(key)
        elif len(signatures)==1: existing[key]=candidates[0]
        else: conflict_recovery.add(key)
    prices=[v for k,v in existing.items() if k not in conflict_recovery]
    for r in prices:
        if r["trade_date"]==snapshot: snapshot_rows[r["security_id"]]=r
    with (OUT/"clean/prices_daily.jsonl").open("w",encoding="utf-8") as f:
        for r in sorted(prices,key=lambda x:(x["security_id"],x["trade_date"])): f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    for name,data in (("securities.jsonl",securities),("trading_calendar.jsonl",calendar),("benchmark_daily.jsonl",benchmark)):
        with (OUT/"clean"/name).open("w",encoding="utf-8") as f:
            for r in data: f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    keys=set(existing)-conflict_recovery; before_keys={(r["security_id"],r["trade_date"]) for r in rows(C4/"clean/prices_daily.jsonl")}
    audit=[]; missing_rows=[]; missing_before_count=missing_after_count=0; complete_before=complete_after=0
    sidmeta={sid:current_security(securities,sid,snapshot) for sid in windows}
    for sid,days in windows.items():
        before=[d for d in days if (sid,d) in before_keys]; after=[d for d in days if (sid,d) in keys]
        miss_before=[d for d in days if (sid,d) not in before_keys]; miss_after=[d for d in days if (sid,d) not in keys]
        missing_before_count+=len(miss_before); missing_after_count+=len(miss_after); complete_before+=len(before)==253; complete_after+=len(after)==253
        ticker=sidmeta[sid]["ticker"]
        audit.append({"security_id":sid,"ticker":ticker,"expected_sessions":len(days),"c4_valid":len(before),"c4_missing":len(miss_before),"c5_valid":len(after),"c5_missing":len(miss_after),"c5_conflicting":sum((sid,d) in conflict_recovery for d in days),"c5_invalid":0})
        for d in miss_before: missing_rows.append({"security_id":sid,"ticker":ticker,"exchange":current_security(securities,sid,d)["exchange"] if current_security(securities,sid,d) else "","trade_date":d,"current_classification":"NO_VALID_LOCAL_TRADEHISTORY_ROW"})
    write_csv(OUT/"latest_253_session_audit_before_after.csv",audit,list(audit[0])); write_csv(OUT/"latest_window_missing_keys.csv",missing_rows,list(missing_rows[0]))
    missing_before_keys={(x["security_id"],x["trade_date"]) for x in missing_rows}
    recovered_missing=[existing[k] for k in missing_before_keys if k in keys]
    recovered_provenance=[x for x in provenance if (x["security_id"],x["trade_date"]) in missing_before_keys and (x["security_id"],x["trade_date"]) in keys]
    with (OUT/"recovery_provenance.jsonl").open("w",encoding="utf-8") as f:
        for r in recovered_provenance: f.write(json.dumps(r,sort_keys=True)+"\n")
    gaps=[{**r,"gap_cause":"NO_VALID_LOCAL_TRADEHISTORY_ROW","independent_suspension_evidence":False} for r in missing_rows]; write_csv(OUT/"gap_cause_audit.csv",gaps,list(gaps[0]))
    plan=[]
    bysid=defaultdict(list)
    for r in missing_rows: bysid[r["security_id"]].append(r)
    for sid,items in bysid.items():
        oldest=min(x["trade_date"] for x in items)
        # Pagination depth follows independent calendar sessions, not observed
        # rows; otherwise a long endpoint gap would under-estimate page depth.
        newest_count=sum(1 for d in windows[sid] if d>=oldest); pages=math.ceil(newest_count/30)+1
        plan.append({"security_id":sid,"ticker":items[0]["ticker"],"oldest_required_missing_date":oldest,"newest_required_missing_date":max(x["trade_date"] for x in items),"missing_key_count":len(items),"max_pages":pages,"page_size":30,"network_required":"YES"})
    write_csv(OUT/"targeted_recovery_plan.csv",plan,list(plan[0]))
    results=[]
    for p in plan:
        recovered=sum((p["security_id"],x["trade_date"]) in keys for x in missing_rows if x["security_id"]==p["security_id"])
        results.append({"ticker":p["ticker"],"requested_missing_keys":p["missing_key_count"],"recovered_keys":recovered,"still_unresolved":int(p["missing_key_count"])-recovered,"network_run_present":p["ticker"] in net["target_tickers"]})
    write_csv(OUT/"targeted_recovery_result.csv",results,list(results[0]))
    # Offline V2 feature rebuild.
    config=json_config(); features=build_features({"securities":securities,"prices_daily":prices,"trading_calendar":calendar,"benchmark_daily":benchmark},config,"CAFEF_TRADEHISTORY_500_CANDIDATE_V2")
    with (OUT/"feature_snapshots_v2.jsonl").open("w",encoding="utf-8") as f:
        for r in features: f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    actual,latest=latest_completed_snapshot_rows(features,"2026-09-15"); assert actual==snapshot
    gate_ids={r["security_id"] for r in csv.DictReader((C4/"feature_readiness_500.csv").open(encoding="utf-8-sig")) if r["primary_blocker"]=="TRADING_STATUS_GATE"}
    gate=[]; tradability=[]; readiness=[]; blockers=Counter()
    for sid in sorted(windows):
        meta=sidmeta[sid]; row=snapshot_rows.get(sid); feat=latest[sid]
        status=row["trading_activity_status"] if row else "MISSING_ROW"; eligible=row.get("tradability_eligible") if row else None
        base={"security_id":sid,"ticker":meta["ticker"],"snapshot_date":snapshot,"market_observation_status":row["market_observation_status"] if row else "MISSING","matched_volume":row.get("matched_volume_shares") if row else None,"negotiated_volume":row.get("negotiated_volume_shares") if row else None,"total_volume":row.get("volume") if row else None,"matched_value":row.get("matched_value_vnd") if row else None,"negotiated_value":row.get("negotiated_value_vnd") if row else None,"traded_value":row.get("traded_value") if row else None,"trading_activity_status":status,"tradability_eligible":eligible,"market_feature_ready_v2":feat["market_feature_ready"]}
        tradability.append(base)
        if sid in gate_ids: gate.append(base)
        missing_features=[x for x in config["required_features"] if feat.get(x) is None]
        primary="READY" if feat["market_feature_ready"] else "MISSING_EXPECTED_SESSION" if any(x["security_id"]==sid and x["c5_missing"] for x in audit) else "OTHER_FEATURE_UNDEFINED"
        blockers[primary]+=1; readiness.append({"security_id":sid,"ticker":meta["ticker"],"feature_complete_v2":feat["feature_complete"],"market_feature_ready_v2":feat["market_feature_ready"],"tradability_eligible":eligible,"trading_activity_status":status,"historical_identity_ready":feat["historical_identity_ready"],"research_ready":feat["research_ready"],"missing_required_features":"|".join(missing_features),"primary_blocker":primary})
    write_csv(OUT/"legacy_trading_status_gate_review.csv",gate,list(gate[0])); write_csv(OUT/"tradability_status_500.csv",tradability,list(tradability[0])); write_csv(OUT/"feature_readiness_500_v2.csv",readiness,list(readiness[0])); write_csv(OUT/"feature_blocker_summary_v2.csv",[{"blocker":k,"security_count":v} for k,v in blockers.most_common()],["blocker","security_count"])
    # Quarantine and conflict decomposition relative to the latest windows.
    expected={(sid,d) for sid,days in windows.items() for d in days}; ticker_sid={x["ticker"]:x["security_id"] for x in securities}; qcounts=defaultdict(lambda:[0,set(),0,0])
    for q in rows(C4/"quarantine.jsonl"):
        reason=q.get("reason","OTHER"); category="IDENTITY_OR_METADATA" if reason=="IDENTITY_ROUTING_ERROR" else "INVALID_PRICE_BAND" if reason=="INVALID_PRICE_BAND" else "INVALID_PROVIDER_PRICE" if reason=="INVALID_PRICE" else "INVALID_ACTIVITY" if reason=="INVALID_ACTIVITY_COMPONENT" else "PARSER" if reason.startswith("UNPARSEABLE") else "OTHER"
        inside=(ticker_sid.get(q.get("ticker")),q.get("trade_date")) in expected; v=qcounts[category]; v[0]+=1; v[1].add(q.get("ticker")); v[2]+=inside; v[3]+=not inside
    conflicts=list(csv.DictReader((C4/"conflicting_observations.csv").open(encoding="utf-8-sig")))
    for key in sorted(conflict_recovery):
        observations=([existing[key]] if key in existing else [])+recovered_by_key[key]
        differing=[field for field in CONFLICT_FIELDS if len({json.dumps(row.get(field),sort_keys=True) for row in observations})>1]
        only_adjusted=differing==["adj_close"]
        conflicts.append({"security_id":key[0],"ticker":observations[0]["ticker"],"trade_date":key[1],"classification":"ADJUSTED_PRICE_REVISION_CANDIDATE" if only_adjusted else "RAW_MARKET_OBSERVATION_CONFLICT","differing_fields":"|".join(differing),"signatures":"|".join(sorted({conflict_signature(row) for row in observations})),"provenance":"|".join(sorted({row.get("source_run_id") or "C4_CLEAN_CANDIDATE" for row in observations}))})
    qcounts["CONFLICT"]=[len(conflicts),{x["ticker"] for x in conflicts},sum((x["security_id"],x["trade_date"]) in expected for x in conflicts),sum((x["security_id"],x["trade_date"]) not in expected for x in conflicts)]
    qsummary=[{"reason":k,"row_count":v[0],"ticker_count":len(v[1]),"inside_latest_253_count":v[2],"outside_latest_253_count":v[3]} for k,v in qcounts.items()]; write_csv(OUT/"quarantine_reason_summary.csv",qsummary,list(qsummary[0]))
    creview=[{**x,"inside_latest_253":(x["security_id"],x["trade_date"]) in expected} for x in conflicts]; write_csv(OUT/"conflict_review.csv",creview,list(creview[0]))
    # Fair KBS V2 recomputation after releasing CafeF bulk rows.
    del features,prices
    kbs_prices=list(rows(OLD_CANON/"clean/prices_daily.jsonl")); kbs_features=build_features({"securities":list(rows(OLD_CANON/"clean/securities.jsonl")),"prices_daily":kbs_prices,"trading_calendar":calendar,"benchmark_daily":benchmark},config,"KBS_RECOMPUTED_READINESS_V2")
    _,kbs_latest=latest_completed_snapshot_rows(kbs_features,"2026-09-15"); comparison=[]; cc=Counter()
    for r in readiness:
        sid=r["security_id"]; kr=kbs_latest[sid]["market_feature_ready"]; cr=r["market_feature_ready_v2"]; cls="BOTH_READY_V2" if kr and cr else "CAFEF_ONLY_READY_V2" if cr else "KBS_ONLY_READY_V2" if kr else "NEITHER_READY_V2"; cc[cls]+=1; comparison.append({"security_id":sid,"ticker":r["ticker"],"kbs_market_feature_ready_v2":kr,"cafef_market_feature_ready_v2":cr,"classification":cls})
    write_csv(OUT/"kbs_vs_cafef_v2.csv",comparison,list(comparison[0]))
    methodology={"zero_volume_provider_row_is_observed":True,"zero_volume_is_missing":False,"zero_volume_implies_suspension":False,"zero_volume_blocks_market_feature_ready":False,"zero_volume_blocks_tradability_eligible":True,"null_volume_component_may_be_treated_as_zero":False,"price_imputation_allowed":False,"timeline_compression_allowed":False,"trading_activity_is_separate_from_market_data_readiness":True,"readiness_policy":READINESS_POLICY_V2}; write_json(OUT/"methodology_decision.json",methodology)
    v2={"feature_complete":sum(x["feature_complete_v2"] for x in readiness),"market_feature_ready":sum(x["market_feature_ready_v2"] for x in readiness),"tradability_eligible":sum(x["tradability_eligible"] is True for x in readiness),"zero_volume_snapshot":sum(x["trading_activity_status"]=="OBSERVED_ZERO_VOLUME" for x in readiness),"unknown_activity":sum(x["trading_activity_status"]=="UNKNOWN_ACTIVITY_COMPONENTS" for x in readiness),"complete_253":complete_after}
    report={"stage":"C5","result":"PASS" if missing_after_count==0 else "PARTIAL","network_requests":net["network_requests"],"c4_legacy":{"feature_complete":c4quality["feature_complete"],"market_feature_ready":c4quality["market_feature_ready"],"trading_status_gate":c4quality["blockers"]["TRADING_STATUS_GATE"],"complete_253":c4quality["complete_253"]},"c5_v2_before_network":{"feature_complete":v2["feature_complete"],"market_feature_ready":v2["market_feature_ready"],"tradability_eligible":v2["tradability_eligible"],"complete_253":complete_before},"c5_v2_after_recovery":v2,"missing_ticker_days_before":missing_before_count,"missing_ticker_days_after":missing_after_count,"incomplete_securities_before":len(plan),"target_tickers":net["target_tickers"],"pages_by_ticker":net["pages_by_ticker"],"oldest_page_reached":net["oldest_page_reached"],"hard_stop_events":net["hard_stop_events"],"zero_volume_rows_observed_in_recovery_pages":net["zero_rows_observed"],"positive_volume_rows_observed_in_recovery_pages":net["positive_rows_observed"],"zero_volume_rows_recovered":sum(x["trading_activity_status"]=="OBSERVED_ZERO_VOLUME" for x in recovered_missing),"positive_volume_rows_recovered":sum(x["trading_activity_status"]=="ACTIVE" for x in recovered_missing),"recovery_conflicts":len(conflict_recovery),"historical_identity_ready":sum(x["historical_identity_ready"] for x in readiness),"research_ready":sum(x["research_ready"] for x in readiness),"legacy_kbs_ready":c4quality["kbs_market_feature_ready"],"kbs_v2_ready":sum(x["market_feature_ready"] for x in kbs_latest.values()),"kbs_vs_cafef_v2":dict(cc),"canonical_status":"EXPERIMENTAL_CANDIDATE_NOT_PROMOTED","canonical_production_mutations":0,"imputation":"NONE","ohlc_supplementation":"NOT_RUN"}; write_json(OUT/"quality_report.json",report)
    outputs=[p for p in OUT.rglob("*") if p.is_file() and p.name!="manifest.json"]; write_json(OUT/"manifest.json",{"stage":"C5 MARKET OBSERVATION SEMANTICS + TARGETED DATA RECOVERY","data_version":"CAFEF_TRADEHISTORY_500_CANDIDATE_V2","parent_c4_manifest_hash":h(C4/"manifest.json"),"comparison_snapshot_date":snapshot,"readiness_policy":READINESS_POLICY_V2,"network_requests":net["network_requests"],"canonical_status":"EXPERIMENTAL_CANDIDATE_NOT_PROMOTED","outputs":{str(p.relative_to(OUT)):h(p) for p in outputs}})
if __name__=="__main__": main()
