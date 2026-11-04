"""Benchmark offline full-SHA256 trên hai protected inventories đã pin;không mở browser/gọi nguồn."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.corporate_actions.vsdc_hash_fastpath import benchmark

if __name__=='__main__':print(json.dumps(benchmark(ROOT),ensure_ascii=False,indent=2))
