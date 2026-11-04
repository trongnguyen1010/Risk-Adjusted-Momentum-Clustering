"""Chuẩn bị offline pause/continuation V2; không mở browser hoặc gọi VSDC."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.corporate_actions.vsdc_resumable_chain import prepare

if __name__=='__main__':print(json.dumps(prepare(ROOT),ensure_ascii=False,indent=2))
