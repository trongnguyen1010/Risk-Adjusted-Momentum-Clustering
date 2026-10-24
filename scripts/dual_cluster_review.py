"""Review both existing cluster families and prepare descriptive comparison tables."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.dual_cluster_review import run

if __name__ == '__main__':
    path, summary = run(ROOT)
    print(path)
    print(json.dumps(summary, indent=2))
