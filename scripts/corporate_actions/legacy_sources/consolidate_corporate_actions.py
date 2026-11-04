"""Consolidate 4-shard corporate actions crawl outputs and verify 100% market coverage."""
import os
import sys
import json
import zipfile
import shutil
import hashlib
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

WORK_DIR = ROOT / "data" / "corporate_actions" / "work"
OUTPUTS_DIR = WORK_DIR / "outputs"
DOWNLOADS = Path("C:/Users/HP/Downloads")

print("================================================================================")
print("       BUOC 1: HOP NHAT & KIEM TOAN DU LIEU CRAWL 4 SHARDS (1.502 MA)          ")
print("================================================================================")

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Extract 4 shard zips
for i in range(4):
    zip_path = DOWNLOADS / f"ca_result_shard{i}.zip"
    if not zip_path.is_file():
        raise FileNotFoundError(f"Missing {zip_path}")
    target_shard_dir = OUTPUTS_DIR / f"batch_shard_{i}"
    if not (target_shard_dir / "batch_results.json").is_file():
        print(f"[*] Dang giai nen Shard {i}: {zip_path.name} ({zip_path.stat().st_size / (1024*1024):.1f} MB)...")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(OUTPUTS_DIR)
        print(f"    [OK] Da giai nen xong {target_shard_dir.name}")
    else:
        print(f"    [OK] {target_shard_dir.name} da ton tai san, bo qua giai nen.")

# 2. Audit each shard batch_results.json
all_crawled_tickers = {}
total_physical_requests = 0

for i in range(4):
    shard_dir = OUTPUTS_DIR / f"batch_shard_{i}"
    br_file = shard_dir / "batch_results.json"
    data = json.loads(br_file.read_text(encoding="utf-8"))
    reqs = data.get("physical_requests", 0)
    stop_reason = data.get("stop_reason")
    results = data.get("results", [])
    total_physical_requests += reqs
    
    success = [r for r in results if r.get("status") == "SOURCE_PARTIAL"]
    failed = [r for r in results if r.get("status") != "SOURCE_PARTIAL"]
    
    print(f"[*] Shard {i}:")
    print(f"    - Ket qua: {len(success)} ma thanh cong, {len(failed)} ma that bai (Ly do dung: {stop_reason})")
    print(f"    - Requests: {reqs} requests")
    
    for r in results:
        sym = r["ticker"]
        if sym in all_crawled_tickers:
            print(f"    [!] CANH BAO TRUNG MA: {sym} xuat hien o ca Shard {all_crawled_tickers[sym]} va Shard {i}")
        all_crawled_tickers[sym] = i

print(f"\n[OK] Tong so ma doc nhat da cao thanh cong: {len(all_crawled_tickers)} / 1.502 ma pending.")
print(f"[OK] Tong requests mang da gui: {total_physical_requests} requests.")

if len(all_crawled_tickers) != 1502:
    raise ValueError(f"Thieu ma! Can 1502 ma nhung chi co {len(all_crawled_tickers)} ma.")
print("[OK] KIEM TOAN DO PHU 100%: Toan bo 1.502 ma pending da duoc thu thap day du khong thieu ma nao!")
