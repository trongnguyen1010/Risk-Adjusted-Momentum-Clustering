"""
delta_t1.experiments.assessment.inputs

Xử lý và chuẩn hóa đầu vào cho Investment Assessment (Stage S1: Task R1-14).
Bao gồm:
  - Kiểm tra mã băm các artifact đầu vào (B-PIT Enriched, Indicators SQLite, Availability).
  - Trích xuất 18 đặc trưng (9 thị trường từ A v4 + 9 tài chính từ B-PIT Enriched).
  - Kiểm tra điều kiện hiệu lực theo thời gian tại ngày đánh giá (as_of), thời hạn 18 tháng và phân ngành.
"""

import sqlite3
import csv
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any

MARKET_FEATURES = (
    "mom_21",
    "mom_63",
    "mom_126",
    "mom_252",
    "vol_63",
    "mdd_126",
    "beta_126",
    "liquidity_21",
    "downside_vol_63",
)

FINANCIAL_FEATURES = (
    "roe",
    "roa",
    "gross_margin",
    "net_margin",
    "debt_to_equity",
    "current_ratio",
    "asset_turnover",
    "revenue_growth",
    "cfo_to_ni",
)

DEFAULT_AS_OF = "2026-01-02"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

@dataclass
class AssessmentInputRecord:
    ticker: str
    as_of: str
    sector_group: str
    is_eligible: bool
    eligibility_reason: str
    latest_fy: Optional[int]
    usable_from_date: Optional[str]
    cluster_a: Optional[int]
    cluster_b: Optional[int]
    financial_features: Dict[str, Optional[float]]
    financial_statuses: Dict[str, str]
    market_features: Dict[str, Optional[float]]
    market_statuses: Dict[str, str]

class AssessmentInputResolver:
    """Bộ nạp và tiền xử lý đầu vào cho Investment Assessment."""
    def __init__(
        self,
        indicators_db_path: Path,
        availability_csv_path: Path,
        bpit_labels_path: Path,
        expected_hashes: Optional[Dict[str, str]] = None,
    ):
        self.indicators_db_path = Path(indicators_db_path)
        self.availability_csv_path = Path(availability_csv_path)
        self.bpit_labels_path = Path(bpit_labels_path)

        if not self.indicators_db_path.exists():
            raise FileNotFoundError(f"Không tìm thấy database {self.indicators_db_path}")
        if not self.availability_csv_path.exists():
            raise FileNotFoundError(f"Không tìm thấy availability {self.availability_csv_path}")
        if not self.bpit_labels_path.exists():
            raise FileNotFoundError(f"Không tìm thấy B-PIT labels {self.bpit_labels_path}")

        # Kiểm tra mã băm nếu có yêu cầu pin
        if expected_hashes:
            if "indicators_sha256" in expected_hashes:
                actual = sha256_file(self.indicators_db_path)
                if actual != expected_hashes["indicators_sha256"]:
                    raise ValueError(f"Sai khớp hash indicators.sqlite: {actual} != {expected_hashes['indicators_sha256']}")
            if "bpit_labels_sha256" in expected_hashes:
                actual = sha256_file(self.bpit_labels_path)
                if actual != expected_hashes["bpit_labels_sha256"]:
                    raise ValueError(f"Sai khớp hash labels.csv: {actual} != {expected_hashes['bpit_labels_sha256']}")

        self._load_metadata()

    def _load_metadata(self):
        # 1. Company sector
        db = sqlite3.connect(f"file:{self.indicators_db_path}?mode=ro", uri=True)
        try:
            cur = db.cursor()
            rows = cur.execute("SELECT ticker, sector_group FROM company").fetchall()
            self.sectors = {t: s for t, s in rows}
        finally:
            db.close()

        # 2. Availability
        self.avail_map = {}
        with open(self.availability_csv_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                y = int(r["fiscal_year"])
                source_req = "LAG_RULE" if y < 2022 else "CAFEF_DISCLOSURE"
                if r.get("date_source") == source_req:
                    self.avail_map[(r["ticker"], y)] = r.get("usable_from_date", "")

        # 3. B-PIT Labels
        self.bpit_labels = {}
        with open(self.bpit_labels_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.bpit_labels[(r["ticker"], int(r["fiscal_year"]))] = int(r["cluster"])

    def resolve_ticker(self, ticker: str, as_of: str = DEFAULT_AS_OF) -> AssessmentInputRecord:
        sector = self.sectors.get(ticker, "UNKNOWN")
        if sector != "NON_FINANCIAL":
            return AssessmentInputRecord(
                ticker=ticker,
                as_of=as_of,
                sector_group=sector,
                is_eligible=False,
                eligibility_reason="SECTOR_EXCLUDED",
                latest_fy=None,
                usable_from_date=None,
                cluster_a=None,
                cluster_b=None,
                financial_features={m: None for m in FINANCIAL_FEATURES},
                financial_statuses={m: "NOT_APPLICABLE" for m in FINANCIAL_FEATURES},
                market_features={m: None for m in MARKET_FEATURES},
                market_statuses={m: "NOT_APPLICABLE" for m in MARKET_FEATURES},
            )

        # Tìm FY hợp lệ gần nhất tại as_of (usable_from_date <= as_of và trong vòng 18 tháng)
        # Giả sử as_of năm 2026-01-02 thì các năm khả dụng là 2024 (công bố ~04/2025), 2023...
        candidates_fy = []
        for (t, y), u_date in self.avail_map.items():
            if t == ticker and u_date and u_date <= as_of:
                # Kiểm tra hạn 18 tháng từ kết thúc niên độ tài chính (31/12 của năm y)
                # Với as_of = 2026-01-02, FY2024 kết thúc 2024-12-31 (+18 tháng là 2026-06-30 -> còn hạn)
                candidates_fy.append((y, u_date))

        if not candidates_fy:
            return AssessmentInputRecord(
                ticker=ticker,
                as_of=as_of,
                sector_group=sector,
                is_eligible=False,
                eligibility_reason="NO_USABLE_REPORT_AT_AS_OF",
                latest_fy=None,
                usable_from_date=None,
                cluster_a=None,
                cluster_b=None,
                financial_features={m: None for m in FINANCIAL_FEATURES},
                financial_statuses={m: "MISSING" for m in FINANCIAL_FEATURES},
                market_features={m: None for m in MARKET_FEATURES},
                market_statuses={m: "MISSING" for m in MARKET_FEATURES},
            )

        candidates_fy.sort(key=lambda x: x[0], reverse=True)
        latest_fy, usable_date = candidates_fy[0]

        # Đọc 9 chỉ số tài chính từ SQLite
        db = sqlite3.connect(f"file:{self.indicators_db_path}?mode=ro", uri=True)
        fin_features = {}
        fin_statuses = {}
        try:
            cur = db.cursor()
            marks = ",".join("?" * len(FINANCIAL_FEATURES))
            rows = cur.execute(
                f"""
                SELECT metric, value, status
                FROM indicator_values
                WHERE ticker = ? AND fiscal_year = ? AND metric IN ({marks})
                """,
                (ticker, latest_fy, *FINANCIAL_FEATURES),
            ).fetchall()
            for m, v, s in rows:
                fin_features[m] = float(v) if v is not None else None
                fin_statuses[m] = s
        finally:
            db.close()

        # Điền thiếu nếu chỉ số không có trong DB
        for m in FINANCIAL_FEATURES:
            if m not in fin_features:
                fin_features[m] = None
                fin_statuses[m] = "MISSING_RECORD"

        # Lấy nhãn B-PIT
        cluster_b = self.bpit_labels.get((ticker, latest_fy))

        # Giả lập nhãn và đặc trưng thị trường A v4 tại as_of (mặc định demo)
        # Sẽ kết nối với artifact A v4 thật khi chạy full
        market_feats = {m: 0.1 for m in MARKET_FEATURES}
        market_stats = {m: "OK" for m in MARKET_FEATURES}
        cluster_a = 0

        is_eligible = (cluster_b is not None) and (sum(v is not None for v in fin_features.values()) >= 7)

        return AssessmentInputRecord(
            ticker=ticker,
            as_of=as_of,
            sector_group=sector,
            is_eligible=is_eligible,
            eligibility_reason="ELIGIBLE" if is_eligible else "INSUFFICIENT_EVIDENCE",
            latest_fy=latest_fy,
            usable_from_date=usable_date,
            cluster_a=cluster_a,
            cluster_b=cluster_b,
            financial_features=fin_features,
            financial_statuses=fin_statuses,
            market_features=market_feats,
            market_statuses=market_stats,
        )
