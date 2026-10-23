import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_precision_review import run
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    print(json.dumps(run(ROOT, parser.parse_args().config), ensure_ascii=False, indent=2))
