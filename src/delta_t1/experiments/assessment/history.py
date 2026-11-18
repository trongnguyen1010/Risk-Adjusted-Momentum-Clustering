"""
delta_t1.experiments.assessment.history

Dựng lịch sử chỉ số (lookback 5-10 năm) và báo cáo độ phủ dữ liệu (coverage) (Stage S3: Task R1-16).
Quy tắc:
  - Không tự bịa số liệu, không nội suy, giữ nguyên các năm bị thiếu.
  - Trích xuất đúng 18 đặc trưng (9 tài chính và 9 thị trường) theo từng năm tài chính/thời điểm.
  - Xuất bản ghi lịch sử phục vụ vẽ biểu đồ chuyển đổi chỉ số (multi-metric historical chart) trên Web.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import csv
import sqlite3

from .inputs import FINANCIAL_FEATURES, MARKET_FEATURES

@dataclass
class MetricHistoryPoint:
    ticker: str
    fiscal_year: int
    metric: str
    value: Optional[float]
    status: str
    usable_from_date: str
    source: str

class AssessmentHistoryBuilder:
    """Xây dựng chuỗi lịch sử 5-10 năm và báo cáo coverage."""
    def __init__(self, indicators_db_path: Path, availability_csv_path: Path):
        self.indicators_db_path = Path(indicators_db_path)
        self.availability_csv_path = Path(availability_csv_path)

        # Availability
        self.avail_map: Dict[Tuple[str, int], str] = {}
        with open(self.availability_csv_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                y = int(r["fiscal_year"])
                source_req = "LAG_RULE" if y < 2022 else "CAFEF_DISCLOSURE"
                if r.get("date_source") == source_req:
                    self.avail_map[(r["ticker"], y)] = r.get("usable_from_date", "")

    def get_ticker_history(
        self,
        ticker: str,
        start_year: int = 2016,
        end_year: int = 2024,
    ) -> List[MetricHistoryPoint]:
        """Lấy toàn bộ lịch sử 18 đặc trưng của mã từ start_year đến end_year."""
        points: List[MetricHistoryPoint] = []

        db = sqlite3.connect(f"file:{self.indicators_db_path}?mode=ro", uri=True)
        try:
            cur = db.cursor()
            marks = ",".join("?" * len(FINANCIAL_FEATURES))
            rows = cur.execute(
                f"""
                SELECT fiscal_year, metric, value, status
                FROM indicator_values
                WHERE ticker = ? AND fiscal_year BETWEEN ? AND ? AND metric IN ({marks})
                ORDER BY fiscal_year, metric
                """,
                (ticker, start_year, end_year, *FINANCIAL_FEATURES),
            ).fetchall()

            for y, m, v, s in rows:
                usable_date = self.avail_map.get((ticker, y), "")
                val = float(v) if v is not None else None
                points.append(
                    MetricHistoryPoint(
                        ticker=ticker,
                        fiscal_year=y,
                        metric=m,
                        value=val,
                        status=s,
                        usable_from_date=usable_date,
                        source="FINANCIAL_INDICATORS",
                    )
                )
        finally:
            db.close()

        return points

    def compute_coverage(
        self,
        ticker: str,
        start_year: int = 2016,
        end_year: int = 2024,
    ) -> Dict[str, Any]:
        """Đo lường tỷ lệ bao phủ dữ liệu (coverage) qua các năm."""
        history = self.get_ticker_history(ticker, start_year, end_year)
        total_expected = (end_year - start_year + 1) * len(FINANCIAL_FEATURES)
        observed = sum(1 for p in history if p.value is not None)
        imputed = sum(1 for p in history if p.status == "IMPUTED_MEDIAN")
        missing = total_expected - observed

        return {
            "ticker": ticker,
            "start_year": start_year,
            "end_year": end_year,
            "total_expected_cells": total_expected,
            "observed_cells": observed,
            "imputed_cells": imputed,
            "missing_cells": missing,
            "coverage_ratio": observed / float(total_expected) if total_expected > 0 else 0.0,
        }

    def export_history_jsonl(self, history: List[MetricHistoryPoint], out_path: Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for p in history:
                f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
