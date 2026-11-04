"""Chuẩn bị offline pilot đọc HTML sau khi browser render; không mở Chrome."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.vsdc_speed1s_pilot import prepare

if __name__ == "__main__":
    print(json.dumps(prepare(ROOT), ensure_ascii=False, indent=2))
