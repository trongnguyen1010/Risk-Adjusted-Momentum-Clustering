"""Compare feature snapshots over time between baseline and enriched v2."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base_feat = ROOT / "data/canonical/canonical-m1-scale-20260921T045028Z-19da7c61/features/monthly.jsonl"
v2_feat = ROOT / "data/canonical/canonical-m1-scale-enriched-v2-20260921T141356Z-ec87b5d8/features/monthly.jsonl"
tickers = ["BCM", "CTR", "LPB", "SHB", "VCG"]

base_by_date = defaultdict(dict)
for line in open(base_feat, encoding="utf-8"):
    r = json.loads(line)
    if r["ticker"] in tickers:
        base_by_date[r["as_of_date"]][r["ticker"]] = r

v2_by_date = defaultdict(dict)
for line in open(v2_feat, encoding="utf-8"):
    r = json.loads(line)
    if r["ticker"] in tickers:
        v2_by_date[r["as_of_date"]][r["ticker"]] = r

# Let's count total historical_identity_ready across all snapshots in baseline vs v2!
base_total_id_ready = 0
for line in open(base_feat, encoding="utf-8"):
    r = json.loads(line)
    if r.get("historical_identity_ready") is True:
        base_total_id_ready += 1

v2_total_id_ready = 0
for line in open(v2_feat, encoding="utf-8"):
    r = json.loads(line)
    if r.get("historical_identity_ready") is True:
        v2_total_id_ready += 1

print(f"Tổng số bản ghi đạt Historical Identity Ready trên toàn bộ lịch sử 5 năm:")
print(f"- Baseline:    {base_total_id_ready} bản ghi")
print(f"- Enriched v2: {v2_total_id_ready} bản ghi (tăng thêm {v2_total_id_ready - base_total_id_ready} bản ghi!)")

print("\n--- Chi tiết so sánh theo từng năm cho 5 mã A6: ---")
dates = ["2020-06-30", "2020-12-31", "2021-06-30", "2021-12-31", "2022-06-30", "2026-08-28"]
for d in dates:
    print(f"\n[Snapshot Date: {d}]")
    for t in tickers:
        b = base_by_date.get(d, {}).get(t, {})
        v = v2_by_date.get(d, {}).get(t, {})
        b_id = b.get("historical_identity_ready")
        v_id = v.get("historical_identity_ready")
        b_m252 = f"{b.get('mom_252'):.2%}" if b.get('mom_252') is not None else "None"
        v_m252 = f"{v.get('mom_252'):.2%}" if v.get('mom_252') is not None else "None"
        b_ex = b.get("adjustment_basis")
        v_ex = v.get("adjustment_basis")
        print(f"  {t:4s} -> Baseline IdentityReady: {str(b_id):5s} | Enriched v2 IdentityReady: {str(v_id):5s} | mom_252: {v_m252}")
