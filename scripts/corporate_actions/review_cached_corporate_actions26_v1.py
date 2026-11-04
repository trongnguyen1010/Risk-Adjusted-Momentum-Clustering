"""Entrypoint tương thích cho runner corporate actions đã lưu."""
from pathlib import Path
import runpy
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
if __name__ == "__main__":
    runpy.run_path(str(ROOT / "scripts" / 'review_cached_corporate_actions26_v1.py'), run_name="__main__")
