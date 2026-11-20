"""
delta_t1.experiments.assessment.inputs

Xử lý và chuẩn hóa đầu vào cho Investment Assessment (Stage S1: Task R1-14).
Bao gồm:
  - Kiểm tra mã băm các artifact đầu vào (B-PIT Enriched, Indicators SQLite, Availability).
  - Trích xuất 18 đặc trưng (9 thị trường từ A v4 thật + 9 tài chính từ B-PIT Enriched).
  - Kiểm tra điều kiện hiệu lực theo thời gian tại ngày đánh giá (as_of), thời hạn 18 tháng và phân ngành.
"""

import sqlite3
import csv
import json
import hashlib
import math
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any

from delta_t1.m3.universe import stale_after

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

MANDATORY_MARKET_FEATURES = (
    "mom_21",
    "mom_63",
    "mom_126",
    "mom_252",
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
DEFAULT_MARKET_SNAPSHOT_DATE = "2025-12-31"
FINANCIAL_STALE_MONTHS = 18

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TERMINAL_SQLITE = REPO_ROOT / "data/web/delta-intelligence-v4/terminal.sqlite"
DEFAULT_MARKET_OBSERVATIONS_JSONL = REPO_ROOT / "data/web/delta-intelligence-v4/market_observations_v4.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_a_v4_market_observations(
    market_data_path: Optional[Path] = None,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Đọc dữ liệu phân cụm và 9 đặc trưng thị trường A v4 thật theo từng (ticker, snapshot_date).
    Ưu tiên đọc từ bundle v4 `terminal.sqlite` nếu có sẵn trên đĩa, hoặc đọc từ bản trích xuất
    chuẩn xác `market_observations_v4.jsonl` của bundle v4.
    """
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    chosen_path = Path(market_data_path) if market_data_path is not None else None
    if chosen_path is None:
        if DEFAULT_TERMINAL_SQLITE.is_file():
            chosen_path = DEFAULT_TERMINAL_SQLITE
        elif DEFAULT_MARKET_OBSERVATIONS_JSONL.is_file():
            chosen_path = DEFAULT_MARKET_OBSERVATIONS_JSONL

    if chosen_path is None or not chosen_path.is_file():
        return out

    if chosen_path.suffix == ".sqlite":
        db = sqlite3.connect(f"file:{chosen_path}?mode=ro", uri=True)
        try:
            rows = db.execute(
                "SELECT date, ticker, cluster, features, liquidity FROM observations WHERE kind='market'"
            ).fetchall()
            for snap_date, ticker, cluster, feats_raw, liquidity in rows:
                parsed_feats = json.loads(feats_raw) if isinstance(feats_raw, str) else (feats_raw or {})
                clean_feats = {}
                for m in MARKET_FEATURES:
                    val = parsed_feats.get(m)
                    clean_feats[m] = float(val) if (val is not None and math.isfinite(float(val))) else None
                out[(str(ticker).strip().upper(), str(snap_date))] = {
                    "date": str(snap_date),
                    "ticker": str(ticker).strip().upper(),
                    "cluster": int(cluster) if cluster is not None else None,
                    "liquidity": str(liquidity) if liquidity in ("LIQUID", "ILLIQUID") else None,
                    "features": clean_feats,
                }
        finally:
            db.close()
    else:
        with open(chosen_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                t = str(r["ticker"]).strip().upper()
                d = str(r["date"])
                raw_feats = r.get("features") or {}
                clean_feats = {}
                for m in MARKET_FEATURES:
                    val = raw_feats.get(m)
                    clean_feats[m] = float(val) if (val is not None and math.isfinite(float(val))) else None
                cluster_val = r.get("cluster")
                liq_val = r.get("liquidity")
                out[(t, d)] = {
                    "date": d,
                    "ticker": t,
                    "cluster": int(cluster_val) if cluster_val is not None else None,
                    "liquidity": str(liq_val) if liq_val in ("LIQUID", "ILLIQUID") else None,
                    "features": clean_feats,
                }
    return out


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
    liquidity_flag: Optional[str] = "LIQUID"
    ni_denominator: Optional[float] = None
    cfo_ratio_valid: Optional[bool] = None
    market_snapshot_date: Optional[str] = DEFAULT_MARKET_SNAPSHOT_DATE


class AssessmentInputResolver:
    """Bộ nạp và tiền xử lý đầu vào cho Investment Assessment."""

    def __init__(
        self,
        indicators_db_path: Path,
        availability_csv_path: Path,
        bpit_labels_path: Path,
        expected_hashes: Optional[Dict[str, str]] = None,
        market_data_path: Optional[Path] = None,
    ):
        self.indicators_db_path = Path(indicators_db_path)
        self.availability_csv_path = Path(availability_csv_path)
        self.bpit_labels_path = Path(bpit_labels_path)
        self.market_data_path = market_data_path

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
        # 1. Company sector & table schema check
        db = sqlite3.connect(f"file:{self.indicators_db_path}?mode=ro", uri=True)
        try:
            cur = db.cursor()
            rows = cur.execute("SELECT ticker, sector_group FROM company").fetchall()
            self.sectors = {t: s for t, s in rows}
            col_names = {r[1] for r in cur.execute("PRAGMA table_info(indicator_values)").fetchall()}
            self._has_inputs_json = "inputs_json" in col_names
        finally:
            db.close()

        # 2. Availability
        self.avail_map: Dict[Tuple[str, int], str] = {}
        with open(self.availability_csv_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                y = int(r["fiscal_year"])
                source_req = "LAG_RULE" if y < 2022 else "CAFEF_DISCLOSURE"
                if r.get("date_source") == source_req:
                    self.avail_map[(r["ticker"], y)] = r.get("usable_from_date", "")

        # 3. B-PIT Labels
        self.bpit_labels: Dict[Tuple[str, int], int] = {}
        with open(self.bpit_labels_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.bpit_labels[(r["ticker"], int(r["fiscal_year"]))] = int(r["cluster"])

        # 4. A v4 Market Observations
        self.market_obs = load_a_v4_market_observations(self.market_data_path)
        self.market_dates = sorted({d for (_, d) in self.market_obs.keys()})

    def _resolve_market_snapshot_date(self, as_of: str) -> str:
        eligible_dates = [d for d in self.market_dates if d <= as_of]
        return eligible_dates[-1] if eligible_dates else DEFAULT_MARKET_SNAPSHOT_DATE

    def resolve_ticker(self, ticker: str, as_of: str = DEFAULT_AS_OF) -> AssessmentInputRecord:
        sector = self.sectors.get(ticker, "UNKNOWN")
        mkt_snap_date = self._resolve_market_snapshot_date(as_of)

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
                liquidity_flag=None,
                ni_denominator=None,
                cfo_ratio_valid=False,
                market_snapshot_date=mkt_snap_date,
            )

        # Lấy dữ liệu thị trường A v4 thật tại snapshot <= as_of
        m_obs = self.market_obs.get((ticker, mkt_snap_date))
        if m_obs is not None:
            cluster_a = m_obs.get("cluster")
            liquidity_flag = m_obs.get("liquidity")
            market_feats = {m: m_obs["features"].get(m) for m in MARKET_FEATURES}
            market_stats = {
                m: ("OK" if market_feats[m] is not None else "MISSING_INPUT")
                for m in MARKET_FEATURES
            }
        else:
            cluster_a = None
            liquidity_flag = None
            market_feats = {m: None for m in MARKET_FEATURES}
            market_stats = {m: "MISSING_INPUT" for m in MARKET_FEATURES}

        # Tìm tất cả các FY đã công bố tại hoặc trước as_of
        candidates_fy = [
            (y, u_date)
            for (t, y), u_date in self.avail_map.items()
            if t == ticker and u_date and u_date <= as_of
        ]

        if not candidates_fy:
            return AssessmentInputRecord(
                ticker=ticker,
                as_of=as_of,
                sector_group=sector,
                is_eligible=False,
                eligibility_reason="NO_USABLE_REPORT_AT_AS_OF",
                latest_fy=None,
                usable_from_date=None,
                cluster_a=cluster_a,
                cluster_b=None,
                financial_features={m: None for m in FINANCIAL_FEATURES},
                financial_statuses={m: "MISSING_INPUT" for m in FINANCIAL_FEATURES},
                market_features=market_feats,
                market_statuses=market_stats,
                liquidity_flag=liquidity_flag,
                ni_denominator=None,
                cfo_ratio_valid=False,
                market_snapshot_date=mkt_snap_date,
            )

        # Chọn FY mới nhất đã khả dụng tại as_of (không fallback về năm cũ nếu năm mới nhất thiếu model)
        candidates_fy.sort(key=lambda x: x[0], reverse=True)
        latest_fy, usable_date = candidates_fy[0]

        # Kiểm tra hạn hiệu lực 18 tháng kể từ ngày kết thúc niên độ tài chính
        is_fresh = as_of <= stale_after(latest_fy, FINANCIAL_STALE_MONTHS)

        # Đọc 9 chỉ số tài chính và mẫu số LNST (net_profit@t) từ SQLite
        db = sqlite3.connect(f"file:{self.indicators_db_path}?mode=ro", uri=True)
        fin_features: Dict[str, Optional[float]] = {}
        fin_statuses: Dict[str, str] = {}
        ni_denominator: Optional[float] = None
        try:
            cur = db.cursor()
            marks = ",".join("?" * len(FINANCIAL_FEATURES))
            if self._has_inputs_json:
                rows = cur.execute(
                    f"""
                    SELECT metric, value, status, inputs_json
                    FROM indicator_values
                    WHERE ticker = ? AND fiscal_year = ? AND metric IN ({marks})
                    """,
                    (ticker, latest_fy, *FINANCIAL_FEATURES),
                ).fetchall()
                for m, v, s, ij in rows:
                    fin_features[m] = float(v) if v is not None else None
                    fin_statuses[m] = s
                    if ij and ni_denominator is None and m in ("cfo_to_ni", "roa", "net_margin"):
                        try:
                            parsed = json.loads(ij)
                            if "net_profit@t" in parsed and parsed["net_profit@t"] is not None:
                                ni_denominator = float(parsed["net_profit@t"])
                        except Exception:
                            pass
            else:
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
                if fin_features.get("roa") is not None or fin_features.get("net_margin") is not None:
                    roa_v = fin_features.get("roa") or 0.0
                    nm_v = fin_features.get("net_margin") or 0.0
                    ni_denominator = 1.0 if (roa_v > 0 or nm_v > 0 or fin_features.get("cfo_to_ni") is not None) else -1.0
        finally:
            db.close()

        # Điền thiếu nếu chỉ số không có trong DB
        for m in FINANCIAL_FEATURES:
            if m not in fin_features:
                fin_features[m] = None
                fin_statuses[m] = "MISSING_INPUT"

        # Lấy nhãn B-PIT của đúng latest_fy
        cluster_b = self.bpit_labels.get((ticker, latest_fy))

        cfo_val = fin_features.get("cfo_to_ni")
        cfo_st = fin_statuses.get("cfo_to_ni", "MISSING_INPUT")
        cfo_ratio_valid = bool(
            ni_denominator is not None
            and ni_denominator > 0
            and cfo_val is not None
            and cfo_st in ("OK", "IMPUTED_MEDIAN")
        )

        # Kiểm tra đầy đủ cổng G1 Eligibility theo D-ASS-01
        mandatory_mkt_ok = (
            cluster_a is not None
            and liquidity_flag in ("LIQUID", "ILLIQUID")
            and all(
                market_feats.get(m) is not None and market_stats.get(m) == "OK"
                for m in MANDATORY_MARKET_FEATURES
            )
        )
        mandatory_fin_ok = (
            cluster_b is not None
            and fin_features.get("roa") is not None
            and fin_statuses.get("roa") in ("OK", "IMPUTED_MEDIAN")
            and fin_features.get("net_margin") is not None
            and fin_statuses.get("net_margin") in ("OK", "IMPUTED_MEDIAN")
            and ni_denominator is not None
            and (ni_denominator <= 0 or cfo_ratio_valid)
        )

        if not is_fresh:
            is_eligible = False
            eligibility_reason = "INSUFFICIENT_EVIDENCE: Báo cáo tài chính đã quá hạn 18 tháng (FINANCIAL_STALE)"
        elif cluster_b is None:
            is_eligible = False
            eligibility_reason = "INSUFFICIENT_EVIDENCE: Chưa có nhãn phân cụm tài chính B-PIT hợp lệ cho kỳ báo cáo mới nhất"
        elif not mandatory_mkt_ok:
            is_eligible = False
            eligibility_reason = "INSUFFICIENT_EVIDENCE: Thiếu dữ liệu hoặc nhãn phân cụm thị trường A v4 tại ngày chốt"
        elif not mandatory_fin_ok:
            is_eligible = False
            eligibility_reason = "INSUFFICIENT_EVIDENCE: Thiếu chỉ số tài chính bắt buộc (ROA, biên lợi nhuận ròng hoặc dòng tiền CFO/LNST)"
        else:
            is_eligible = True
            eligibility_reason = "ELIGIBLE"

        return AssessmentInputRecord(
            ticker=ticker,
            as_of=as_of,
            sector_group=sector,
            is_eligible=is_eligible,
            eligibility_reason=eligibility_reason,
            latest_fy=latest_fy,
            usable_from_date=usable_date,
            cluster_a=cluster_a,
            cluster_b=cluster_b,
            financial_features=fin_features,
            financial_statuses=fin_statuses,
            market_features=market_feats,
            market_statuses=market_stats,
            liquidity_flag=liquidity_flag,
            ni_denominator=ni_denominator,
            cfo_ratio_valid=cfo_ratio_valid,
            market_snapshot_date=mkt_snap_date,
        )
