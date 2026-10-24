"""Execute the explicitly approved, bounded R1 protocol. Preserve baseline artifacts."""
import json
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.upgrade_reference import run
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--recover');args=parser.parse_args()
    print(json.dumps(run(ROOT,recover=args.recover),indent=2,ensure_ascii=False))
