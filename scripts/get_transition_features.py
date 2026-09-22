"""Extract detailed features for transition tickers."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
feat_file = ROOT / "data/canonical/canonical-m1-scale-enriched-v2-20260921T141356Z-ec87b5d8/features/monthly.jsonl"
tickers = ["BCM", "CTR", "LPB", "SHB", "VCG"]

rows = []
for line in open(feat_file, encoding="utf-8"):
    r = json.loads(line)
    if r["as_of_date"] == "2026-08-28" and r["ticker"] in tickers:
        rows.append(r)

rows.sort(key=lambda x: x["ticker"])

print("| Mã | Sàn Hiện Tại | mom_21 | mom_63 | mom_126 | mom_252 | vol_63 (năm) | beta_126 | mdd_126 | GTGD TB 21 ngày (VND) | Identity Ready | Market Ready |")
print("|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|")
for r in rows:
    m21 = f"{r.get('mom_21'):.2%}" if r.get('mom_21') is not None else "-"
    m63 = f"{r.get('mom_63'):.2%}" if r.get('mom_63') is not None else "-"
    m126 = f"{r.get('mom_126'):.2%}" if r.get('mom_126') is not None else "-"
    m252 = f"{r.get('mom_252'):.2%}" if r.get('mom_252') is not None else "-"
    v63 = f"{r.get('vol_63'):.2%}" if r.get('vol_63') is not None else "-"
    b126 = f"{r.get('beta_126'):.2f}" if r.get('beta_126') is not None else "-"
    mdd = f"{r.get('mdd_126'):.2%}" if r.get('mdd_126') is not None else "-"
    liq = f"{r.get('liquidity_21'):,.0f}" if r.get('liquidity_21') is not None else "-"
    id_ready = "YES" if r.get("historical_identity_ready") else "NO"
    m_ready = "YES" if r.get("market_feature_ready") else "NO"
    print(f"| **{r['ticker']}** | HOSE | {m21} | {m63} | {m126} | {m252} | {v63} | {b126} | {mdd} | {liq} | {id_ready} | {m_ready} |")
