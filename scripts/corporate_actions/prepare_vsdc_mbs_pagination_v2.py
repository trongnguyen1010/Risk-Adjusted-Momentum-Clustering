"""Chuẩn bị offline pilot V2; không gọi nguồn hoặc sửa artifact V1."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.vsdc_mbs_pilot_v2 import prepare

if __name__ == "__main__":
    print(json.dumps(prepare(ROOT), ensure_ascii=False, indent=2))
