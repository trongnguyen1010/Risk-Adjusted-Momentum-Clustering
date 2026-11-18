"""
Phân loại các ô đủ điều kiện làm giàu dữ liệu tài chính (Stage C: Task R1-03).
Quy tắc:
  - FY2017–FY2024, doanh nghiệp phi tài chính (sector_group = 'NON_FINANCIAL').
  - Có usable_from_date <= cutoff của B-PIT gốc.
  - Chỉ điền các ô thiếu có status = 'MISSING_INPUT'.
  - CFO thiếu chỉ điền khi LNST (NI) quan sát được và dương (ni > 0).
  - Giữ nguyên các ô trống theo công thức: NEGATIVE_EARNINGS, NEGATIVE_EQUITY, NOT_APPLICABLE.
"""

import sqlite3
import csv
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional

FEATURES = (
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

@dataclass(frozen=True)
class EligibleCell:
    ticker: str
    fiscal_year: int
    metric: str
    original_status: str
    usable_from_date: str
    cutoff: str
    reason: str

class FinancialEnrichmentEligibility:
    def __init__(
        self,
        indicators_path: Path,
        availability_path: Path,
        bpit_models_path: Optional[Path] = None,
        cutoffs: Optional[Dict[int, str]] = None,
    ):
        self.indicators_path = Path(indicators_path)
        self.availability_path = Path(availability_path)
        self.bpit_models_path = Path(bpit_models_path) if bpit_models_path else None
        self.cutoffs = cutoffs or self._load_cutoffs()

    def _load_cutoffs(self) -> Dict[int, str]:
        if self.bpit_models_path and self.bpit_models_path.exists():
            models = json.loads(self.bpit_models_path.read_text(encoding="utf-8"))
            return {int(y): m["cutoff"] for y, m in models.items() if "cutoff" in m}
        # Fallback standard cutoffs
        return {
            2016: "2017-07-03",
            2017: "2018-07-02",
            2018: "2019-07-01",
            2019: "2020-07-01",
            2020: "2021-07-01",
            2021: "2022-07-01",
            2022: "2023-04-30",
            2023: "2024-04-30",
            2024: "2025-04-30",
        }

    def load_availability(self) -> Dict[Tuple[str, int], str]:
        avail = {}
        with open(self.availability_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                year = int(row["fiscal_year"])
                req_source = "LAG_RULE" if year < 2022 else "CAFEF_DISCLOSURE"
                if row.get("date_source") == req_source:
                    avail[(row["ticker"], year)] = row.get("usable_from_date", "")
        return avail

    def analyze(self, start_year: int = 2017, end_year: int = 2024) -> Dict:
        avail = self.load_availability()

        db = sqlite3.connect(f"file:{self.indicators_path}?mode=ro", uri=True)
        try:
            allowed = {t for (t,) in db.execute("select ticker from company where sector_group = 'NON_FINANCIAL'")}
            marks = ",".join("?" * len(FEATURES))
            query = f"""
                select ticker, fiscal_year, metric, value, status, inputs_json
                from indicator_values
                where fiscal_year between ? and ? and metric in ({marks})
            """
            rows = db.execute(query, (start_year, end_year, *FEATURES)).fetchall()
        finally:
            db.close()

        # Tổ chức theo (ticker, fiscal_year)
        grouped = {}
        for t, y, m, v, s, inp in rows:
            if t not in allowed:
                continue
            key = (t, y)
            if key not in grouped:
                grouped[key] = {}
            grouped[key][m] = {"value": v, "status": s, "inputs_json": inp}

        fit_complete_9 = []
        eligible_rows = []
        eligible_cells: List[EligibleCell] = []
        ineligible_rows = []

        for (t, y), feats in grouped.items():
            usable_date = avail.get((t, y), "")
            cutoff = self.cutoffs.get(y, "")
            is_usable_at_cutoff = bool(usable_date and cutoff and usable_date <= cutoff)

            ok_metrics = []
            imputable_metrics = []
            formula_gap_metrics = []

            for m in FEATURES:
                f_info = feats.get(m)
                if not f_info:
                    formula_gap_metrics.append((m, "MISSING_RECORD"))
                    continue

                status = f_info["status"]
                val = f_info["value"]
                inp_str = f_info.get("inputs_json", "")

                if status == "OK" and val is not None:
                    ok_metrics.append(m)
                elif status == "MISSING_INPUT":
                    if inp_str and "NO_ANNUAL_REPORT" in inp_str:
                        formula_gap_metrics.append((m, "NO_ANNUAL_REPORT"))
                        continue
                    # Quy tắc đặc thù cfo_to_ni
                    if m == "cfo_to_ni":
                        try:
                            inp_data = json.loads(inp_str) if inp_str else {}
                            ni = inp_data.get("net_profit@t", inp_data.get("ni"))
                            if ni is not None and ni > 0:
                                imputable_metrics.append((m, "CFO_MISSING_POSITIVE_NI"))
                            else:
                                formula_gap_metrics.append((m, "CFO_NON_POSITIVE_NI"))
                        except Exception:
                            formula_gap_metrics.append((m, "CFO_INVALID_INPUTS_JSON"))
                    else:
                        imputable_metrics.append((m, "MISSING_INPUT"))
                else:
                    formula_gap_metrics.append((m, status))

            if len(ok_metrics) == 9:
                fit_complete_9.append({
                    "ticker": t,
                    "fiscal_year": y,
                    "usable_from_date": usable_date,
                    "cutoff": cutoff,
                    "usable_at_cutoff": is_usable_at_cutoff,
                })
            elif not formula_gap_metrics and imputable_metrics and is_usable_at_cutoff:
                # Dòng có thể hoàn tất 9/9 sau khi điền
                eligible_rows.append({
                    "ticker": t,
                    "fiscal_year": y,
                    "usable_from_date": usable_date,
                    "cutoff": cutoff,
                    "missing_count": len(imputable_metrics),
                    "missing_metrics": [m for m, _ in imputable_metrics],
                })
                for m, r in imputable_metrics:
                    eligible_cells.append(
                        EligibleCell(
                            ticker=t,
                            fiscal_year=y,
                            metric=m,
                            original_status="MISSING_INPUT",
                            usable_from_date=usable_date,
                            cutoff=cutoff,
                            reason=r,
                        )
                    )
            else:
                ineligible_rows.append({
                    "ticker": t,
                    "fiscal_year": y,
                    "formula_gaps": formula_gap_metrics,
                    "usable_at_cutoff": is_usable_at_cutoff,
                })

        return {
            "total_rows": len(grouped),
            "fit_complete_9_count": len(fit_complete_9),
            "eligible_rows_count": len(eligible_rows),
            "eligible_cells_count": len(eligible_cells),
            "eligible_rows": eligible_rows,
            "eligible_cells": eligible_cells,
            "fit_complete_9": fit_complete_9,
        }
