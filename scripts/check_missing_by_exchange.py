"""Analyze missing data breakdown across exchanges (HOSE, HNX, UPCOM)."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = ROOT / "data" / "canonical" / "canonical-m1-scale-enriched-v2-20260921T141356Z-ec87b5d8"

sec_file = CANONICAL_DIR / "clean" / "securities.jsonl"
feat_file = CANONICAL_DIR / "features" / "monthly.jsonl"

sec_exchange = {}
for line in open(sec_file, encoding="utf-8"):
    r = json.loads(line)
    sec_exchange[r["security_id"]] = r["exchange"]

latest_feats = {}
for line in open(feat_file, encoding="utf-8"):
    r = json.loads(line)
    if r["as_of_date"] == "2026-08-28":
        latest_feats[r["security_id"]] = r

by_ex = defaultdict(lambda: {
    "total": 0, "ready": 0, "missing": 0,
    "g1_le5": 0, "g1_6to20": 0, "g2_gt20": 0,
    "missing_counts": [], "tickers_missing": []
})

for sid, f in latest_feats.items():
    ex = sec_exchange.get(sid, "UNKNOWN")
    mc = f.get("missing_count", 0)
    ready = f.get("market_feature_ready", False)
    ticker = f.get("ticker", "")
    
    st = by_ex[ex]
    st["total"] += 1
    st["missing_counts"].append(mc)
    if ready:
        st["ready"] += 1
    else:
        st["missing"] += 1
        st["tickers_missing"].append((ticker, mc))
        if mc <= 5:
            st["g1_le5"] += 1
        elif mc <= 20:
            st["g1_6to20"] += 1
        else:
            st["g2_gt20"] += 1

print("| Sàn | Tổng số mã | Sẵn sàng (Ready) | Thiếu (Non-Ready) | Tỷ lệ thiếu mã | Thiếu 1-5 phiên | Thiếu 6-20 phiên | Thiếu >20 phiên | TB số phiên thiếu |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for ex in ["HOSE", "HNX", "UPCOM"]:
    st = by_ex[ex]
    avg_mc = sum(st["missing_counts"]) / len(st["missing_counts"]) if st["missing_counts"] else 0
    pct_missing = (st["missing"] / st["total"]) * 100 if st["total"] else 0
    print(f"| {ex} | {st['total']} | {st['ready']} | {st['missing']} | {pct_missing:.1f}% | {st['g1_le5']} | {st['g1_6to20']} | {st['g2_gt20']} | {avg_mc:.1f} |")

print("\n--- Chi tiết tổng 331 mã thiếu phân bổ theo sàn: ---")
total_non_ready = sum(by_ex[ex]["missing"] for ex in ["HOSE", "HNX", "UPCOM"])
for ex in ["HOSE", "HNX", "UPCOM"]:
    cnt = by_ex[ex]["missing"]
    pct_of_all_missing = (cnt / total_non_ready) * 100
    print(f"- {ex}: {cnt} mã (chiếm {pct_of_all_missing:.1f}% trong tổng số 331 mã thiếu)")

print("\n--- Nhóm thiếu nặng (> 20 phiên, tức 261 mã): ---")
total_g2 = sum(by_ex[ex]["g2_gt20"] for ex in ["HOSE", "HNX", "UPCOM"])
for ex in ["HOSE", "HNX", "UPCOM"]:
    cnt = by_ex[ex]["g2_gt20"]
    pct = (cnt / total_g2) * 100
    print(f"- {ex}: {cnt} mã (chiếm {pct:.1f}% của nhóm thiếu nặng)")

print("\n--- Top 5 mã thiếu nhiều nhất từng sàn: ---")
for ex in ["HOSE", "HNX", "UPCOM"]:
    top5 = sorted(by_ex[ex]["tickers_missing"], key=lambda x: x[1], reverse=True)[:5]
    top5_str = ", ".join([f"{t} ({mc}p)" for t, mc in top5])
    print(f"- {ex}: {top5_str}")
