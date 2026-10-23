from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_presentation_sign_audit import cli
if __name__=='__main__':cli(ROOT)
