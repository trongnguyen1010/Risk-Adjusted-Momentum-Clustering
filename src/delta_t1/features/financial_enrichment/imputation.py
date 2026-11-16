"""
Điền giá trị trung vị và ghi nhận truy vết (lineage) cho từng ô (Stage C: Task R1-05).
Quy tắc:
  - Chỉ điền các ô đã được xác định đủ điều kiện ở module eligibility.
  - Giá trị điền lấy chính xác từ bảng medians của cùng FY và cùng metric.
  - Status mới được gán là 'IMPUTED_MEDIAN'.
  - Ghi đầy đủ metadata truy xuất nguồn gốc (provenance).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from pathlib import Path
import csv

from .eligibility import EligibleCell

@dataclass
class ImputedCellRecord:
    ticker: str
    fiscal_year: int
    metric: str
    original_status: str
    new_status: str
    imputed_value: float
    usable_from_date: str
    cutoff: str
    method: str
    reason: str
    n_donor_observations: int

def impute_cells(
    eligible_cells: List[EligibleCell],
    medians_map: Dict[Tuple[int, str], float],
    donor_counts: Dict[Tuple[int, str], int],
) -> List[ImputedCellRecord]:
    """
    Thực hiện điền giá trị trung vị cho từng ô đủ điều kiện và sinh bản ghi lineage.
    """
    imputed_records: List[ImputedCellRecord] = []
    
    for cell in eligible_cells:
        key = (cell.fiscal_year, cell.metric)
        if key not in medians_map:
            raise ValueError(f"Không tìm thấy trung vị cho {cell.metric} năm {cell.fiscal_year}")
            
        med_val = medians_map[key]
        n_obs = donor_counts.get(key, 0)
        
        imputed_records.append(
            ImputedCellRecord(
                ticker=cell.ticker,
                fiscal_year=cell.fiscal_year,
                metric=cell.metric,
                original_status=cell.original_status,
                new_status="IMPUTED_MEDIAN",
                imputed_value=med_val,
                usable_from_date=cell.usable_from_date,
                cutoff=cell.cutoff,
                method="MEDIAN_SAME_FY_FIT",
                reason=cell.reason,
                n_donor_observations=n_obs,
            )
        )
    return imputed_records

def export_imputed_cells_csv(records: List[ImputedCellRecord], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "ticker",
            "fiscal_year",
            "metric",
            "original_status",
            "new_status",
            "imputed_value",
            "usable_from_date",
            "cutoff",
            "method",
            "reason",
            "n_donor_observations",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "ticker": r.ticker,
                "fiscal_year": r.fiscal_year,
                "metric": r.metric,
                "original_status": r.original_status,
                "new_status": r.new_status,
                "imputed_value": r.imputed_value,
                "usable_from_date": r.usable_from_date,
                "cutoff": r.cutoff,
                "method": r.method,
                "reason": r.reason,
                "n_donor_observations": r.n_donor_observations,
            })

