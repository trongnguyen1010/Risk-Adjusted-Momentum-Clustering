"""C4 offline evaluation of CafeF TradeHistoryNew for the reviewed M1 universe."""
import csv, hashlib, json, math, sqlite3, sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OLD=Path(r"C:\Projects\Intern\SourceCode")
LEGACY=OLD/"data/raw/cafef"; OUT=ROOT/"artifacts/cafef_primary/cafef-tradehistory-500-evaluation-v1"
OLD_CANON=OLD/"data/canonical/canonical-m1-scale-20260918T141019Z-7c003543"
OLD_QUALITY=OLD/"data/derived/m1_scale_quality/m1-scale-quality-20260918T152429Z-dcbd8e8e"
UNIVERSE=OLD/"configs/data/m1_scale.universe.v1.json"; MASTER=OLD/"configs/data/m1_scale.securities.v1.json"
FEATURE_CONFIG=OLD/"configs/features/market.example.json"; V3=ROOT/"docs/crawl/plans/cafef_c1_history_v3/cafef_c1_history_v3_plan.csv"
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.features.market import build_features, latest_completed_snapshot_rows
from delta_t1.ingestion.sources.cafef import ADAPTER_VERSION, cafef_trade_date, classify_cafef_page_row, map_trade_history_row

def h(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def dump_json(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
def dump_csv(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def validate_universe():
    universe=json.loads(UNIVERSE.read_text(encoding="utf-8")); master=json.loads(MASTER.read_text(encoding="utf-8"))
    rows=universe if isinstance(universe,list) else universe.get("securities",universe.get("universe",[]))
    assert len(rows)==len({x["ticker"] for x in rows})==len({x["security_id"] for x in rows})==500
    assert {x["exchange"] for x in rows}=={"HOSE","HNX","UPCOM"}
    return rows,master
def endpoint_ok(meta): return "TradeHistoryNew.ashx" in str(meta.get("url",""))
def value_signature(row):
    return tuple(row.get(x) for x in ("BasicPrice","ClosePrice","AdjustPrice","Ceiling","Floor","Volume","TotalValue","AgreedVolume","AgreedValue"))
def conflict_kind(signatures):
    varying={name for i,name in enumerate(("reference","raw_close","adj_close","ceiling","floor","matched_volume","matched_value","negotiated_volume","negotiated_value")) if len({s[i] for s in signatures})>1}
    return ("ADJUSTED_PRICE_REVISION_CANDIDATE" if varying=={"adj_close"} else "RAW_MARKET_OBSERVATION_CONFLICT"),"|".join(sorted(varying))
def total(a,b): return a+b if a is not None and b is not None and a>=0 and b>=0 else None
def row_quality(row):
    nums=(row["cafef_adjust_price"],row["cafef_close_price"])
    if any(x is None or not math.isfinite(x) or x<=0 for x in nums): return "INVALID_PRICE"
    for key in ("matched_volume","matched_value","put_through_volume","put_through_value"):
        if row[key] is not None and row[key]<0: return "INVALID_ACTIVITY_COMPONENT"
    bands=(row["floor_price"],row["reference_price"],row["ceiling_price"])
    if all(x is not None for x in bands) and not bands[0]<=bands[1]<=bands[2]: return "INVALID_PRICE_BAND"
    return "VALID"
def canonical_row(row, provenance):
    return {"security_id":row["security_id"],"ticker":row["ticker"],"exchange":row["exchange"],"trade_date":row["trade_date"],
        "raw_open":None,"raw_high":None,"raw_low":None,"raw_close":row["cafef_close_price"],"reference_price":row["reference_price"],
        "ceiling_price":row["ceiling_price"],"floor_price":row["floor_price"],"adj_close":row["cafef_adjust_price"],"adjustment_basis":"vendor_adjusted",
        "matched_volume_shares":row["matched_volume"],"negotiated_volume_shares":row["put_through_volume"],"matched_value_vnd":row["matched_value"],
        "negotiated_value_vnd":row["put_through_value"],"volume":total(row["matched_volume"],row["put_through_volume"]),
        "traded_value":total(row["matched_value"],row["put_through_value"]),"trading_status":"normal" if (row["matched_volume"] or 0)>0 else "unknown",
        "available_at":row["trade_date"]+"T17:00:00+07:00","source":"cafef","source_endpoint":"TradeHistoryNew.ashx",
        "source_run_id":provenance[0]["run_id"],"provenance":provenance,"fetched_at":row["fetched_at"],"data_version":"CAFEF_TRADEHISTORY_500_CANDIDATE_V1"}
def load_identity(old_securities,universe):
    by_ticker=defaultdict(list)
    for r in old_securities: by_ticker[r["ticker"]].append(r)
    reviewed={}
    for r in csv.DictReader(V3.open(encoding="utf-8")): reviewed[r["ticker"]]=json.loads(r["identity_intervals"])
    output=[]; routing={}
    for u in universe:
        base=by_ticker[u["ticker"]][0]; intervals=reviewed.get(u["ticker"])
        if intervals:
            routing[u["ticker"]]=intervals
            for interval in intervals:
                x=dict(base); x.update(exchange=interval["exchange"],valid_from=interval["effective_from"],valid_to=interval["effective_to"],data_version="CAFEF_TRADEHISTORY_500_CANDIDATE_V1"); output.append(x)
        else:
            routing[u["ticker"]]=[{"exchange":base["exchange"],"effective_from":base["valid_from"],"effective_to":base["valid_to"],"evidence_id":"M1_PROVISIONAL_OBSERVED_INTERVAL"}]
            x=dict(base); x["data_version"]="CAFEF_TRADEHISTORY_500_CANDIDATE_V1"; output.append(x)
    return output,routing
def route(routing,ticker,day):
    matches=[x for x in routing[ticker] if x["effective_from"]<=day and (not x.get("effective_to") or day<=x["effective_to"])]
    if len(matches)!=1: return None
    return matches[0]["exchange"]
def latest253(security,calendar,prices,conflicts,invalid,snapshot):
    sessions=sorted(x["trade_date"] for x in calendar if x["exchange"]==security["exchange"] and x["is_open"] and security["valid_from"]<=x["trade_date"]<=(security["valid_to"] or snapshot) and x["trade_date"]<=snapshot)[-253:]
    keys={(security["security_id"],d) for d in sessions}; observed=sum(k in prices for k in keys)
    return sessions,observed,sum(k in conflicts for k in keys),sum(k in invalid for k in keys)

def main():
    universe,_=validate_universe(); tickers={x["ticker"] for x in universe}; uby={x["ticker"]:x for x in universe}
    old_manifest=json.loads((OLD_CANON/"manifest.json").read_text());
    for rel in ("clean/securities.jsonl","clean/trading_calendar.jsonl","clean/benchmark_daily.jsonl","features/monthly.jsonl"):
        assert h(OLD_CANON/rel)==old_manifest["artifacts"][rel]
    quality_manifest=json.loads((OLD_QUALITY/"manifest.json").read_text()); assert h(OLD_QUALITY/"per_symbol.jsonl")==quality_manifest["artifacts"]["per_symbol.jsonl"]
    old_securities=list(jsonl(OLD_CANON/"clean/securities.jsonl")); securities,routing=load_identity(old_securities,universe)
    calendar=list(jsonl(OLD_CANON/"clean/trading_calendar.jsonl")); benchmark=list(jsonl(OLD_CANON/"clean/benchmark_daily.jsonl")); old_kbs={x["security_id"]:x for x in jsonl(OLD_QUALITY/"per_symbol.jsonl")}
    snapshot=json.loads((OLD_QUALITY/"report.json").read_text())["summary"]["latest_completed_snapshot"]
    for d in (OUT,OUT/"clean"): d.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(OUT/"work.sqlite"); db.execute("DROP TABLE IF EXISTS obs"); db.execute("CREATE TABLE obs(sid TEXT,ticker TEXT,day TEXT,sig TEXT,row TEXT,prov TEXT,copies INTEGER,PRIMARY KEY(sid,day,sig))")
    validations=[]; inventory=defaultdict(lambda:{"page_count":0,"pages":[],"dates":[],"checks":set(),"endpoints":set()}); invalid_keys=set(); parse_quarantine=[]
    runs=[p for p in LEGACY.iterdir() if p.is_dir()]
    for run in sorted(runs):
      sidecars={p.name.replace(".metadata.json",".json") for p in run.glob("*.metadata.json")}
      for raw_without_sidecar in (p for p in run.glob("*.json") if not p.name.endswith(".metadata.json") and p.name not in sidecars):
        parts=raw_without_sidecar.stem.split("-"); guessed=parts[1].upper() if len(parts)>2 else ""
        validations.append({"run_id":run.name,"run_family":run.name.rsplit("-",2)[0],"metadata_path":"","raw_path":str(raw_without_sidecar),"ticker":guessed,"page_index":"","classification":"MISSING_METADATA","sha256":""})
      for meta_path in run.glob("*.metadata.json"):
        raw=meta_path.with_name(meta_path.name.replace(".metadata.json",".json")); base={"run_id":run.name,"run_family":run.name.rsplit("-",2)[0],"metadata_path":str(meta_path),"raw_path":str(raw),"ticker":"","page_index":"","classification":"VALID_RAW_PAGE","sha256":""}
        try: meta=json.loads(meta_path.read_text(encoding="utf-8")); req=meta.get("request",{}); ticker=str(req.get("symbol",meta.get("symbol",""))).upper(); base.update(ticker=ticker,page_index=req.get("page_index",""))
        except Exception: base["classification"]="UNPARSEABLE"; validations.append(base); continue
        if ticker not in tickers: base["classification"]="OUT_OF_SCOPE_TICKER"
        elif not raw.exists(): base["classification"]="UNPARSEABLE"
        elif not endpoint_ok(meta): base["classification"]="UNKNOWN_ENDPOINT"
        elif not isinstance(req.get("page_index"),int) or req["page_index"]<1 or req.get("page_size")!=30: base["classification"]="UNPARSEABLE"
        else:
            base["sha256"]=h(raw)
            if base["sha256"]!=meta.get("sha256"): base["classification"]="CHECKSUM_MISMATCH"
        validations.append(base); inv=inventory[(run.name,base["run_family"],ticker)]; inv["page_count"]+=1; inv["pages"].append(base["page_index"]); inv["checks"].add(base["classification"]); inv["endpoints"].add("TradeHistoryNew.ashx" if endpoint_ok(meta) else "UNKNOWN")
        if base["classification"]!="VALID_RAW_PAGE": continue
        try: payload=json.loads(raw.read_text(encoding="utf-8")); rows=payload["Data"]; assert payload.get("Success") is True and isinstance(rows,list)
        except Exception: base["classification"]="UNPARSEABLE"; continue
        for pos,rr in enumerate(rows):
            try:
                if classify_cafef_page_row(rr.get("TradeDate"),req["page_index"],pos)=="CURRENT_SNAPSHOT": continue
                day=cafef_trade_date(rr["TradeDate"]); exchange=route(routing,ticker,day)
                if exchange is None: parse_quarantine.append({"ticker":ticker,"trade_date":day,"reason":"IDENTITY_ROUTING_ERROR"}); invalid_keys.add((uby[ticker]["security_id"],day)); continue
                mapped=map_trade_history_row(rr,ticker,exchange); mapped.update(security_id=uby[ticker]["security_id"],ticker=ticker,exchange=exchange,fetched_at=meta.get("fetched_at"))
                inv["dates"].append(day); sig=hashlib.sha256(json.dumps(value_signature(rr),separators=(",",":"),ensure_ascii=False).encode()).hexdigest(); prov={"run_id":run.name,"relative_path":str(raw.relative_to(LEGACY)),"sha256":base["sha256"],"fetched_at":meta.get("fetched_at")}
                cur=db.execute("SELECT prov,copies FROM obs WHERE sid=? AND day=? AND sig=?",(mapped["security_id"],day,sig)).fetchone()
                if cur:
                    ps=json.loads(cur[0]); ps.append(prov); db.execute("UPDATE obs SET prov=?,copies=? WHERE sid=? AND day=? AND sig=?",(json.dumps(ps),cur[1]+1,mapped["security_id"],day,sig))
                else: db.execute("INSERT INTO obs VALUES(?,?,?,?,?,?,1)",(mapped["security_id"],ticker,day,sig,json.dumps(mapped),json.dumps([prov])))
            except Exception as exc: parse_quarantine.append({"ticker":ticker,"trade_date":"","reason":"UNPARSEABLE_ROW:"+type(exc).__name__})
      db.commit()
    invrows=[]
    for (rid,fam,t),v in inventory.items(): invrows.append({"run_id":rid,"run_family":fam,"ticker":t,"page_count":v["page_count"],"first_page":min((x for x in v["pages"] if isinstance(x,int)),default=""),"last_page":max((x for x in v["pages"] if isinstance(x,int)),default=""),"first_observed_historical_date":min(v["dates"],default=""),"last_observed_historical_date":max(v["dates"],default=""),"checksum_status":"PASS" if v["checks"]=={"VALID_RAW_PAGE"} else "|".join(sorted(v["checks"])),"endpoint_status":"|".join(sorted(v["endpoints"]))})
    dump_csv(OUT/"legacy_raw_inventory.csv",invrows,list(invrows[0])); dump_csv(OUT/"raw_page_validation.csv",validations,list(validations[0]))
    counts={row[0]+"|"+row[1]:row[2] for row in db.execute("SELECT sid,day,COUNT(*) FROM obs GROUP BY sid,day")}; conflict_keys={tuple(k.split("|",1)) for k,v in counts.items() if v>1}
    conflicts=[]; duplicates=Counter(); clean=[]; normalized_count=0; quarantine=list(parse_quarantine)
    with (OUT/"normalized_tradehistory.jsonl").open("w",encoding="utf-8") as nf,(OUT/"clean/prices_daily.jsonl").open("w",encoding="utf-8") as cf,(OUT/"quarantine.jsonl").open("w",encoding="utf-8") as qf:
      for sid,ticker,day,sig,rowj,provj,copies in db.execute("SELECT sid,ticker,day,sig,row,prov,copies FROM obs ORDER BY sid,day,sig"):
        row=json.loads(rowj); prov=json.loads(provj); key=(sid,day); quality=row_quality(row); normalized_count+=1; duplicates[ticker]+=copies-1
        nf.write(json.dumps({**row,"signature":sig,"supporting_provenance":prov,"exact_copy_count":copies,"classification":"CONFLICTING_CAFEF_TRADEHISTORY_OBSERVATION" if key in conflict_keys else "DUPLICATE_EXACT_PROVIDER_EVIDENCE" if copies>1 else "UNIQUE_PROVIDER_EVIDENCE"},ensure_ascii=False,sort_keys=True)+"\n")
        if key in conflict_keys or quality!="VALID":
            if quality!="VALID": invalid_keys.add(key); item={"security_id":sid,"ticker":ticker,"trade_date":day,"reason":quality,"signature":sig}; quarantine.append(item); qf.write(json.dumps(item)+"\n")
            continue
        cr=canonical_row(row,prov); clean.append(cr); cf.write(json.dumps(cr,ensure_ascii=False,sort_keys=True)+"\n")
      for item in parse_quarantine: qf.write(json.dumps(item)+"\n")
    for sid,day in sorted(conflict_keys):
        rows=list(db.execute("SELECT row,prov,sig FROM obs WHERE sid=? AND day=?",(sid,day))); sigs=[value_signature(json.loads(x[0])["raw_fields"]) for x in rows]; kind,fields=conflict_kind(sigs)
        conflicts.append({"security_id":sid,"ticker":json.loads(rows[0][0])["ticker"],"trade_date":day,"classification":kind,"differing_fields":fields,"signatures":"|".join(x[2] for x in rows),"provenance":"|".join(json.loads(x[1])[0]["run_id"] for x in rows)})
    dump_csv(OUT/"conflicting_observations.csv",conflicts,["security_id","ticker","trade_date","classification","differing_fields","signatures","provenance"])
    duperows=[{"ticker":t,"exact_duplicate_observations_collapsed":duplicates[t]} for t in sorted(tickers)]; dump_csv(OUT/"duplicate_evidence_summary.csv",duperows,list(duperows[0]))
    for name,rows in (("securities.jsonl",securities),("trading_calendar.jsonl",calendar),("benchmark_daily.jsonl",benchmark)):
        with (OUT/"clean"/name).open("w",encoding="utf-8") as f:
            for x in rows: f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n")
    config=json.loads(FEATURE_CONFIG.read_text()); config.update(vendor_run_id="C4_OFFLINE",canonical_run_id="CAFEF_TRADEHISTORY_500_CANDIDATE_V1")
    features=build_features({"securities":securities,"prices_daily":clean,"trading_calendar":calendar,"benchmark_daily":benchmark},config,"CAFEF_TRADEHISTORY_500_CANDIDATE_V1")
    with (OUT/"feature_snapshots.jsonl").open("w",encoding="utf-8") as f:
        for x in features: f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n")
    actual_snapshot,latest=latest_completed_snapshot_rows(features,"2026-09-15"); assert actual_snapshot==snapshot
    pricekeys={(x["security_id"],x["trade_date"]) for x in clean}; prices_by_sid=defaultdict(list)
    for x in clean: prices_by_sid[x["security_id"]].append(x)
    sec_current={x["security_id"]:x for x in securities if not x["valid_to"] or x["valid_to"]>=snapshot}
    audit=[]; coverage=[]; readiness=[]; compare=[]; blocker=Counter(); classifications=Counter()
    for u in universe:
        sid=u["security_id"]; sec=sec_current[sid]; sessions,observed,confs,invalid=latest253(sec,calendar,pricekeys,conflict_keys,invalid_keys,snapshot); missing=len(sessions)-observed-confs-invalid
        audit.append({"security_id":sid,"ticker":u["ticker"],"expected_sessions_253":len(sessions),"observed_valid_prices_253":observed,"missing_sessions_253":max(0,missing),"conflicting_sessions_253":confs,"invalid_sessions_253":invalid})
        allrows=prices_by_sid[sid]; coverage.append({"security_id":sid,"ticker":u["ticker"],"first_observed":min((x["trade_date"] for x in allrows),default=""),"last_observed":max((x["trade_date"] for x in allrows),default=""),"valid_rows":len(allrows)})
        feat=latest.get(sid,{}); missing_features=[x for x in config["required_features"] if feat.get(x) is None]
        if feat.get("market_feature_ready"): primary="READY"
        elif confs: primary="CONFLICTING_TRADEHISTORY"
        elif invalid: primary="INVALID_PROVIDER_ROW"
        elif missing: primary="MISSING_EXPECTED_SESSION"
        elif "liquidity_21" in missing_features: primary="MISSING_TRADED_VALUE"
        elif not feat.get("feature_complete"): primary="OTHER_FEATURE_UNDEFINED"
        elif not feat.get("market_feature_ready") and feat.get("na_reason",{}).get("trading_status"): primary="TRADING_STATUS_GATE"
        else: primary="OTHER_FEATURE_UNDEFINED"
        blocker[primary]+=1; readiness.append({"security_id":sid,"ticker":u["ticker"],"feature_complete":feat.get("feature_complete",False),"market_feature_ready":feat.get("market_feature_ready",False),"historical_identity_ready":feat.get("historical_identity_ready",False),"research_ready":feat.get("research_ready",False),"eligibility":feat.get("eligibility",False),"primary_blocker":primary,"missing_required_features":"|".join(missing_features)})
        k=old_kbs[sid]["market_feature_ready"]; c=bool(feat.get("market_feature_ready")); cls="BOTH_READY" if k and c else "CAFEF_ONLY_READY" if c else "KBS_ONLY_READY" if k else "NEITHER_READY"; classifications[cls]+=1
        compare.append({"ticker":u["ticker"],"security_id":sid,"kbs_market_feature_ready":k,"cafef_market_feature_ready":c,"kbs_missing_last_253":old_kbs[sid]["recent_missing_sessions"],"cafef_missing_last_253":max(0,missing),"cafef_conflict_last_253":confs,"cafef_invalid_last_253":invalid,"classification":cls})
    dump_csv(OUT/"session_coverage_by_ticker.csv",coverage,list(coverage[0])); dump_csv(OUT/"latest_253_session_audit.csv",audit,list(audit[0])); dump_csv(OUT/"feature_readiness_500.csv",readiness,list(readiness[0])); dump_csv(OUT/"kbs_vs_cafef_readiness.csv",compare,list(compare[0])); dump_csv(OUT/"feature_blocker_summary.csv",[{"blocker":k,"security_count":v} for k,v in blocker.most_common()],["blocker","security_count"])
    fall=[{"ticker":x["ticker"],"reason":"LOCAL_EVIDENCE_INCOMPLETE","network_required":"YES","suggested_endpoint":"TradeHistoryNew.ashx"} for x in audit if x["missing_sessions_253"] or x["conflicting_sessions_253"] or x["invalid_sessions_253"]]; dump_csv(OUT/"network_fallback_plan.csv",fall,["ticker","reason","network_required","suggested_endpoint"])
    dump_json(OUT/"field_disposition.json",{"raw_open":{"status":"NOT_AVAILABLE_ON_TRADEHISTORYNEW","feature_requirement":"NOT_REQUIRED_BY_CURRENT_FEATURE_SET","future":"FUTURE_SUPPLEMENT_ALLOWED"},"raw_high":{"status":"NOT_AVAILABLE_ON_TRADEHISTORYNEW","feature_requirement":"NOT_REQUIRED_BY_CURRENT_FEATURE_SET","future":"FUTURE_SUPPLEMENT_ALLOWED"},"raw_low":{"status":"NOT_AVAILABLE_ON_TRADEHISTORYNEW","feature_requirement":"NOT_REQUIRED_BY_CURRENT_FEATURE_SET","future":"FUTURE_SUPPLEMENT_ALLOWED"},"raw_close":{"status":"PROVIDER_PUBLISHED_CLOSE","source_field":"ClosePrice"},"adj_close":{"status":"PROVIDER_VENDOR_ADJUSTED","source_field":"AdjustPrice"},"future_version":"CAFEF_MARKET_V2_WITH_SUPPLEMENTAL_OHLC"})
    pilot={r["ticker"] for r in csv.DictReader(V3.open(encoding="utf-8"))}; summary={"stage":"C4","result":"PARTIAL","network_requests":0,"universe":500,"raw_runs_scanned":len(runs),"valid_pages":sum(x["classification"]=="VALID_RAW_PAGE" for x in validations),"securities_with_evidence":sum(bool(x["valid_rows"]) for x in coverage),"normalized_unique_observations":normalized_count,"exact_duplicates_collapsed":sum(duplicates.values()),"conflicting_ticker_days":len(conflict_keys),"quarantined_rows":len(quarantine),"comparison_snapshot_date":snapshot,"complete_253":sum(x["observed_valid_prices_253"]==253 for x in audit),"feature_complete":sum(x["feature_complete"] for x in readiness),"market_feature_ready":sum(x["market_feature_ready"] for x in readiness),"historical_identity_ready":sum(x["historical_identity_ready"] for x in readiness),"research_ready":sum(x["research_ready"] for x in readiness),"kbs_market_feature_ready":sum(x["market_feature_ready"] for x in old_kbs.values()),"comparison":dict(classifications),"blockers":dict(blocker),"pilot_27_market_feature_ready":sum(x["market_feature_ready"] for x in readiness if x["ticker"] in pilot),"canonical_production_mutations":0,"clustering":"NOT_RUN","backtest":"NOT_RUN"}; dump_json(OUT/"quality_report.json",summary)
    outputs=[p for p in OUT.rglob("*") if p.is_file() and p.name!="work.sqlite"]
    dump_json(OUT/"manifest.json",{"stage":"C4 TRADEHISTORYNEW 500-SECURITY MARKET SOURCE EVALUATION","data_version":"CAFEF_TRADEHISTORY_500_CANDIDATE_V1","legacy_evidence_root":str(LEGACY),"external_local_evidence_dependency":True,"universe_hash":h(UNIVERSE),"security_metadata_hash":h(MASTER),"identity_evidence_hash":old_manifest["artifacts"]["clean/securities.jsonl"],"calendar_hash":old_manifest["artifacts"]["clean/trading_calendar.jsonl"],"benchmark_hash":old_manifest["artifacts"]["clean/benchmark_daily.jsonl"],"feature_config_hash":h(FEATURE_CONFIG),"comparison_snapshot_date":snapshot,"tradehistory_adapter_version":ADAPTER_VERSION,"network_requests":0,"canonical_status":"EXPERIMENTAL_CANDIDATE_NOT_PROMOTED","raw_open_high_low_status":"NOT_AVAILABLE_ON_SOURCE","outputs":{str(p.relative_to(OUT)):h(p) for p in outputs}})
    db.close(); (OUT/"work.sqlite").unlink()
if __name__=="__main__": main()
