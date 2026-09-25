"""Bounded single-thread C5 recovery for exact latest-window blockers only."""
import argparse, csv, hashlib, json, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.sources.cafef import ADAPTER_VERSION, TRADE_HISTORY_ENDPOINT, cafef_trade_date

PLAN=ROOT/"artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/targeted_recovery_plan.csv"
RAW_ROOT=ROOT/"data/raw/cafef"
RETRYABLE={500,502,503,504}; HARD_STOP={401,403,429}

def acquire(url,timeout=20,attempts=2):
    opener=build_opener(); headers={"User-Agent":"DeltaT1Research/0.2 (academic; non-commercial demo)","Accept":"application/json"}
    for attempt in range(attempts):
        try:
            with opener.open(Request(url,headers=headers),timeout=timeout) as response:
                body=response.read(5_000_001); marker=body[:4096].lower()
                if len(body)>5_000_000: raise ValueError("response too large")
                if any(x in marker for x in (b"captcha",b"cloudflare",b"access denied",b"managed challenge")): raise RuntimeError("HARD_STOP_CHALLENGE")
                payload=json.loads(body); return body,payload,response.status
        except HTTPError as exc:
            if exc.code in HARD_STOP: raise RuntimeError(f"HARD_STOP_HTTP_{exc.code}") from None
            if exc.code not in RETRYABLE or attempt+1>=attempts: raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--ticker"); parser.add_argument("--start-page",type=int,default=1); parser.add_argument("--max-page",type=int)
    args=parser.parse_args()
    targets=list(csv.DictReader(PLAN.open(encoding="utf-8-sig")))
    if args.ticker: targets=[x for x in targets if x["ticker"]==args.ticker.upper()]
    run_id="c5-targeted-recovery-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]
    out=RAW_ROOT/run_id; out.mkdir(parents=True,exist_ok=False); requests=0; hard_stops=[]; pages_by={}; oldest_reached={}
    last_request=0.0; stop_all=False
    for target in targets:
        ticker=target["ticker"]; oldest=target["oldest_required_missing_date"]; max_pages=args.max_page or int(target["max_pages"]); pages_by[ticker]=0; reached=False
        for page in range(args.start_page,max_pages+1):
            time.sleep(max(0,3.0-(time.monotonic()-last_request))); params={"Symbol":ticker,"PageIndex":page,"PageSize":30}; url=TRADE_HISTORY_ENDPOINT+"?"+urlencode(params); last_request=time.monotonic()
            try: body,payload,status=acquire(url)
            except RuntimeError as exc: hard_stops.append({"ticker":ticker,"page":page,"event":str(exc)}); stop_all=True; break
            requests+=1; pages_by[ticker]+=1; stamp=datetime.now(timezone.utc).isoformat(); raw=out/f"cafef-{ticker}-page-{page:03d}.json"; raw.write_bytes(body); digest=hashlib.sha256(body).hexdigest()
            meta={"provider":"cafef","adapter_version":ADAPTER_VERSION,"recovery_stage":"C5","recovery_reason":"LATEST_253_MISSING","fetched_at":stamp,"http_status":status,"url":url,"request":{"symbol":ticker,"page_index":page,"page_size":30},"sha256":digest,"raw_path":str(raw.relative_to(ROOT))}; raw.with_name(raw.stem+".metadata.json").write_text(json.dumps(meta,sort_keys=True),encoding="utf-8")
            data=payload.get("Data") if isinstance(payload,dict) else None
            if payload.get("Success") is not True or not isinstance(data,list): hard_stops.append({"ticker":ticker,"page":page,"event":"INVALID_PAYLOAD"}); break
            days=[]
            for row in data:
                try: days.append(cafef_trade_date(row["TradeDate"]))
                except Exception: pass
            if days: oldest_reached[ticker]=min(days)
            if reached: break
            if days and min(days)<=oldest: reached=True
            if not data: break
        if stop_all: break
    manifest={"run_id":run_id,"stage":"C5","target_tickers":[x["ticker"] for x in targets],"pages_by_ticker":pages_by,"network_requests":requests,"oldest_page_reached":oldest_reached,"hard_stop_events":hard_stops,"concurrency":1,"minimum_interval_seconds":3.0,"timeout_seconds":20,"attempts":2,"retry_statuses":sorted(RETRYABLE)}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(manifest,indent=2))
if __name__=="__main__": main()
