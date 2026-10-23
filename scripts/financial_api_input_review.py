"""Run offline expanded financial API input review with durable checkpoints."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_api_input_review import run
from delta_t1.experiments.financial_acquisition_overnight import state_file

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(run(ROOT,args.config),ensure_ascii=False,indent=2))
    except Exception as error:
        config=json.loads((ROOT/args.config).read_bytes())
        state_file(ROOT/config['output_root']/'pipeline-status.json','HELD_REVIEW_REQUIRED',reason=str(error))
        raise
