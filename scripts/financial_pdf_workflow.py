from pathlib import Path
from delta_t1.experiments.financial_pdf_workflow import cli

if __name__ == '__main__':
    cli(Path(__file__).resolve().parents[1])
