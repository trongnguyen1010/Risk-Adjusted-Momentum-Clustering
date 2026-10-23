from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_recovery_readiness import cli
if __name__ == '__main__':
    cli(ROOT)
