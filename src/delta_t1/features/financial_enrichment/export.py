"""
Xuất SQLite dẫn xuất và file audit/manifest cho dữ liệu làm giàu (Stage C: Task R1-06).
Quy tắc:
  - Giữ nguyên toàn bộ dữ liệu gốc ngoài các ô được làm giàu.
  - Cập nhật đúng các ô với value = imputed_value, status = 'IMPUTED_MEDIAN'.
  - Tính SHA-256 đầu vào và đầu ra, tạo manifest.json chuẩn chỉnh.
"""

import sqlite3
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Tuple

from .imputation import ImputedCellRecord, export_imputed_cells_csv
from .medians import export_medians_csv

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def export_enriched_dataset(
    original_db_path: Path,
    output_dir: Path,
    imputed_records: List[ImputedCellRecord],
    medians_records: List[Dict],
    input_hashes: Dict[str, str],
    git_commit_sha: str = "",
) -> Dict:
    """
    Tạo bộ dữ liệu làm giàu hoàn chỉnh gồm:
      - indicators.sqlite (chứa các ô IMPUTED_MEDIAN)
      - imputed_cells.csv
      - medians_by_year_metric.csv
      - imputation_summary.json
      - manifest.json
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    enriched_db_path = output_dir / "indicators.sqlite"
    
    # 1. Sao chép database gốc
    shutil.copy2(original_db_path, enriched_db_path)
    
    # 2. Cập nhật các ô được làm giàu
    conn = sqlite3.connect(enriched_db_path)
    cur = conn.cursor()
    
    for r in imputed_records:
        cur.execute(
            """
            UPDATE indicator_values
            SET value = ?, status = ?
            WHERE ticker = ? AND fiscal_year = ? AND metric = ?
            """,
            (r.imputed_value, r.new_status, r.ticker, r.fiscal_year, r.metric),
        )
    conn.commit()
    conn.close()
    
    # 3. Xuất các file CSV audit
    imputed_csv_path = output_dir / "imputed_cells.csv"
    export_imputed_cells_csv(imputed_records, imputed_csv_path)
    
    medians_csv_path = output_dir / "medians_by_year_metric.csv"
    export_medians_csv(medians_records, medians_csv_path)
    
    # 4. Thống kê tóm tắt
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_imputed_cells": len(imputed_records),
        "unique_imputed_tickers": len(set(r.ticker for r in imputed_records)),
        "unique_imputed_rows": len(set((r.ticker, r.fiscal_year) for r in imputed_records)),
        "imputed_by_metric": {},
        "imputed_by_year": {},
    }
    for r in imputed_records:
        summary["imputed_by_metric"][r.metric] = summary["imputed_by_metric"].get(r.metric, 0) + 1
        summary["imputed_by_year"][r.fiscal_year] = summary["imputed_by_year"].get(r.fiscal_year, 0) + 1
        
    summary_path = output_dir / "imputation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 5. Xuất manifest.json
    manifest = {
        "version": "indicators_enriched_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit_sha,
        "inputs": input_hashes,
        "outputs": {
            "indicators_sqlite_sha256": sha256_file(enriched_db_path),
            "imputed_cells_sha256": sha256_file(imputed_csv_path),
            "medians_csv_sha256": sha256_file(medians_csv_path),
            "summary_sha256": sha256_file(summary_path),
        },
        "stats": summary,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return manifest

