"""Run offline history QA independently of the frozen acquisition runner."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_history_qa import cli

if __name__ == '__main__':
    cli(ROOT)
