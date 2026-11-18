"""Build a separate R1 preview bundle; baseline SQLite is never rewritten."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.product.research_preview import export
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',default='data/experiments/delta_upgrade_r1_v1/results/09fa9b1ea51d861edbd5');parser.add_argument('--connect',action='store_true');args=parser.parse_args()
    result=export(ROOT,args.run)
    if args.connect:(ROOT/'configs/product/model_previews_v1.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
