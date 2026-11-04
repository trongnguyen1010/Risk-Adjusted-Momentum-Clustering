import json
from pathlib import Path

ROOT = Path(r"C:\Users\HP\Downloads\Phân cụm động lượng TTCK")
WORK_DIR = ROOT / "data" / "corporate_actions" / "work"
OUTPUTS_DIR = WORK_DIR / "outputs"
BOOTSTRAP_OBS = ROOT / "tmp" / "ca_single_file_handoff_20261101" / "data" / "checkpoints" / "bootstrap" / "origin_observations.jsonl"

bootstrap_count = 0
if BOOTSTRAP_OBS.is_file():
    with open(BOOTSTRAP_OBS, "r", encoding="utf-8") as f:
        bootstrap_count = sum(1 for l in f if l.strip())

print(f"Bootstrap observations: {bootstrap_count}")

shard_obs_count = 0
tickers = set()
for shard_idx in range(4):
    shard_dir = OUTPUTS_DIR / f"batch_shard_{shard_idx}"
    receipts_dir = shard_dir / "source_receipts"
    if receipts_dir.is_dir():
        for t_dir in receipts_dir.iterdir():
            if t_dir.is_dir() and (t_dir / "observations.jsonl").is_file():
                tickers.add(t_dir.name)
                with open(t_dir / "observations.jsonl", "r", encoding="utf-8") as f:
                    shard_obs_count += sum(1 for l in f if l.strip())

print(f"Crawled tickers: {len(tickers)}")
print(f"Crawled observations: {shard_obs_count}")
print(f"Total observations combined: {bootstrap_count + shard_obs_count}")
