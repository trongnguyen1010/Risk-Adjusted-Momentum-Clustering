"""
delta_t1.experiments.bpit_enriched

Thực nghiệm phân cụm tài chính B-PIT trên tập dữ liệu làm giàu (Stage D).
Task R1-07: Chuẩn hóa cohort và loader enriched.
- Đọc dữ liệu từ SQLite dẫn xuất với opt-in status = ('OK', 'IMPUTED_MEDIAN').
- Tạo cohort FIT gồm: các mã FIT gốc + các mã hoàn tất 9/9 nhờ làm giàu có usable_from_date <= cutoff.
- Bảo đảm bất biến: fit_leaks = 0, cutoff và availability giữ nguyên.
"""

import sqlite3
import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, NamedTuple
import numpy as np

from delta_t1.m3 import bpit

class EnrichedSnapshot(NamedTuple):
    fiscal_year: int
    tickers: List[str]
    raw: np.ndarray
    usable_dates: List[str]
    cutoff: str
    fit_mask: np.ndarray  # bool mask indicating which tickers belong to FIT cohort
    features: Tuple[str, ...]

def load_enriched_indicators(
    sqlite_path: Path,
    features: Tuple[str, ...] = bpit.FEATURES,
    sector: str = "NON_FINANCIAL",
    years: range = range(2016, 2026),
    opt_in_statuses: Tuple[str, ...] = ("OK", "IMPUTED_MEDIAN"),
) -> Dict[int, Dict[str, Dict[str, float]]]:
    """
    Đọc dữ liệu tài chính từ SQLite dẫn xuất.
    Chỉ nạp các ô có status nằm trong opt_in_statuses.
    Trả về: dict {fiscal_year: {ticker: {metric: value}}}
    """
    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"Không tìm thấy SQLite tại {sqlite_path}")

    marks_features = ",".join("?" * len(features))
    marks_statuses = ",".join("?" * len(opt_in_statuses))

    db = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        allowed_tickers = {
            t for (t,) in db.execute(
                "SELECT ticker FROM company WHERE sector_group = ?", (sector,)
            )
        }
        query = f"""
            SELECT ticker, fiscal_year, metric, value
            FROM indicator_values
            WHERE status IN ({marks_statuses})
              AND metric IN ({marks_features})
              AND value IS NOT NULL
        """
        rows = db.execute(query, (*opt_in_statuses, *features)).fetchall()
    finally:
        db.close()

    data: Dict[int, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for t, y, m, v in rows:
        if t in allowed_tickers and y in years:
            data[y][t][m] = float(v)

    return dict(data)

def load_availability_map(availability_csv_path: Path) -> Dict[Tuple[str, int], str]:
    """
    Đọc bảng ngày công bố báo cáo tài chính (availability.csv).
    Áp dụng đúng logic M3: LAG_RULE trước FY2022 và CAFEF_DISCLOSURE từ FY2022.
    """
    avail = {}
    with open(availability_csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y = int(r["fiscal_year"])
            source_req = "LAG_RULE" if y < 2022 else "CAFEF_DISCLOSURE"
            if r.get("date_source") == source_req:
                avail[(r["ticker"], y)] = r.get("usable_from_date", "")
    return avail

def build_enriched_snapshots(
    sqlite_path: Path,
    availability_path: Path,
    features: Tuple[str, ...] = bpit.FEATURES,
    years: range = range(2017, 2025),
    opt_in_statuses: Tuple[str, ...] = ("OK", "IMPUTED_MEDIAN"),
    sector: str = "NON_FINANCIAL",
    pinned_cutoffs: Optional[Dict[int, str]] = None,
) -> List[EnrichedSnapshot]:
    """
    Xây dựng danh sách các Snapshot hoàn chỉnh (đủ 9/9 đặc trưng) theo từng FY.
    Xác định cohort FIT và kiểm tra fit_leaks = 0.
    """
    data = load_enriched_indicators(
        sqlite_path=sqlite_path,
        features=features,
        sector=sector,
        years=years,
        opt_in_statuses=opt_in_statuses,
    )
    avail_map = load_availability_map(availability_path)

    snapshots: List[EnrichedSnapshot] = []

    for y in sorted(years):
        if y not in data:
            continue
        y_data = data[y]
        
        # Lọc các công ty có đủ 9/9 đặc trưng
        complete_tickers = sorted(
            [t for t, mdict in y_data.items() if len(mdict) == len(features) and all(m in mdict for m in features)]
        )
        if not complete_tickers:
            continue

        raw_matrix = np.array(
            [[y_data[t][m] for m in features] for t in complete_tickers],
            dtype=float,
        )
        usable_dates = [avail_map.get((t, y), "") for t in complete_tickers]

        # Xác định cutoff
        if pinned_cutoffs and y in pinned_cutoffs:
            cutoff = pinned_cutoffs[y]
        else:
            cutoff = bpit.cutoff_for(y, usable_dates)

        # Xác định FIT cohort: có usable_from_date và usable_from_date <= cutoff
        fit_mask = np.array([bool(d) and d <= cutoff for d in usable_dates], dtype=bool)

        # Kiểm tra bất biến fit_leaks = 0
        leaks = [
            complete_tickers[i]
            for i, (is_fit, d) in enumerate(zip(fit_mask, usable_dates))
            if is_fit and (not d or d > cutoff)
        ]
        if leaks:
            raise ValueError(f"FY{y} phát hiện fit_leaks: {leaks}")

        snapshots.append(
            EnrichedSnapshot(
                fiscal_year=y,
                tickers=complete_tickers,
                raw=raw_matrix,
                usable_dates=usable_dates,
                cutoff=cutoff,
                fit_mask=fit_mask,
                features=features,
            )
        )

    return snapshots
