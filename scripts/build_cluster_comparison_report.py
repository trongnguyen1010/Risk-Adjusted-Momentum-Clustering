"""Build read-only A/B/C tables from verified immutable artifacts."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.reporting.cluster_comparison import build

if __name__ == '__main__':
    path,summary=build(ROOT)
    print(path)
    print(json.dumps(summary,indent=2))
