import argparse
from pathlib import Path
from delta_t1.experiments.financial_pdf_reference_import import run

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args()
    run(Path(__file__).resolve().parents[1],args.config)
