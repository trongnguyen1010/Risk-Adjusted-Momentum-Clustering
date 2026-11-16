"""
Tính toán trung vị (Median) các chỉ số tài chính từ tập FIT gốc (Stage C: Task R1-04).
Quy tắc:
  - Chỉ tính trên các mã thuộc vai trò FIT trong artifact B-PIT gốc.
  - Tính trên giá trị quan sát thô (status = 'OK', chưa winsorize hoặc chuẩn hóa z-score).
  - Không bao gồm các ô được điền hoặc các mã gán sau cutoff.
"""

import csv
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
import numpy as np

from .eligibility import FEATURES

def load_baseline_fit_tickers(labels_csv_path: Path) -> Dict[int, Set[str]]:
    """Đọc danh sách các mã có role = 'FIT' theo từng FY từ labels.csv của B-PIT gốc."""
    fit_by_fy: Dict[int, Set[str]] = {}
    with open(labels_csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("role") == "FIT":
                y = int(r["fiscal_year"])
                fit_by_fy.setdefault(y, set()).add(r["ticker"])
    return fit_by_fy

def compute_medians_from_fit(
    indicators_db_path: Path,
    labels_csv_path: Path,
    features: Tuple[str, ...] = FEATURES,
    years: range = range(2017, 2025),
) -> Tuple[Dict[Tuple[int, str], float], List[Dict]]:
    """
    Tính trung vị từng chỉ số theo FY từ tập FIT gốc.
    Trả về:
      - dict mapping (fiscal_year, metric) -> median_value
      - list of records để xuất CSV medians_by_year_metric.csv
    """
    fit_tickers_map = load_baseline_fit_tickers(Path(labels_csv_path))
    
    db = sqlite3.connect(f"file:{indicators_db_path}?mode=ro", uri=True)
    try:
        cur = db.cursor()
        medians_map: Dict[Tuple[int, str], float] = {}
        records: List[Dict] = []
        
        for y in years:
            tickers = fit_tickers_map.get(y, set())
            if not tickers:
                continue
            
            # Đọc toàn bộ giá trị OK của FY đó một lần để tối ưu tốc độ
            marks = ",".join("?" * len(features))
            query = f"""
                SELECT ticker, metric, value 
                FROM indicator_values 
                WHERE fiscal_year = ? AND status = 'OK' AND value IS NOT NULL AND metric IN ({marks})
            """
            rows = cur.execute(query, (y, *features)).fetchall()
            
            values_by_metric: Dict[str, List[float]] = {m: [] for m in features}
            for t, m, v in rows:
                if t in tickers:
                    values_by_metric[m].append(float(v))
                    
            for m in features:
                vals = values_by_metric[m]
                if not vals:
                    continue
                med = float(np.median(vals))
                medians_map[(y, m)] = med
                records.append({
                    "fiscal_year": y,
                    "metric": m,
                    "median": med,
                    "n_observations": len(vals),
                    "n_fit_cohort": len(tickers),
                })
        return medians_map, records
    finally:
        db.close()

def export_medians_csv(records: List[Dict], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["fiscal_year", "metric", "median", "n_observations", "n_fit_cohort"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
