"""Chuẩn bị offline pilot 5 full queries ở4s; không gọi nguồn/mở browser."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.corporate_actions.vsdc_five_query4s_pilot import prepare

if __name__ == '__main__': print(json.dumps(prepare(ROOT), ensure_ascii=False, indent=2))
