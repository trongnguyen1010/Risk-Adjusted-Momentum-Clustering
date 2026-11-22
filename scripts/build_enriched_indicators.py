#!/usr/bin/env python3
"""
scripts/build_enriched_indicators.py

Pipeline làm giàu dữ liệu tài chính (Stage C: Task R1-06).
Thực hiện:
  1. Phân loại các ô đủ điều kiện làm giàu (FinancialEnrichmentEligibility).
  2. Tính trung vị (median) từ tập FIT baseline cho 9 chỉ số FY2017-FY2024.
  3. Điền giá trị trung vị vào các ô khuyết thiếu hợp lệ với status = 'IMPUTED_MEDIAN'.
  4. Xuất SQLite dẫn xuất, các file audit CSV, summary JSON và manifest.json.
  5. Đảm bảo bất biến (immutability) cho dữ liệu gốc.
"""

import argparse
import subprocess
from pathlib import Path
import shutil

from delta_t1.features.financial_enrichment.eligibility import (
    FinancialEnrichmentEligibility,
    FEATURES,
)
from delta_t1.features.financial_enrichment.medians import compute_medians_from_fit
from delta_t1.features.financial_enrichment.imputation import impute_cells
from delta_t1.features.financial_enrichment.export import export_enriched_dataset, sha256_file

def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"

def main():
    parser = argparse.ArgumentParser(description="Làm giàu dữ liệu tài chính B-PIT M3")
    parser.add_argument(
        "--indicators-db",
        type=Path,
        default=Path("data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite"),
        help="Đường dẫn file indicators.sqlite gốc",
    )
    parser.add_argument(
        "--availability-csv",
        type=Path,
        default=Path("data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv"),
        help="Đường dẫn file availability.csv gốc",
    )
    parser.add_argument(
        "--baseline-bpit-dir",
        type=Path,
        default=Path("data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec"),
        help="Đường dẫn thư mục B-PIT baseline chứa labels.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/financial/indicators_enriched_v1/indicators_enriched_v1_run01"),
        help="Thư mục xuất dữ liệu làm giàu",
    )
    parser.add_argument(
        "--backup-downloads-dir",
        type=Path,
        default=Path.home() / "Downloads" / "delta_enriched_backup",
        help="Thư mục sao lưu ra Downloads để người dùng đối chiếu",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    indicators_db = (repo_root / args.indicators_db).resolve()
    availability_csv = (repo_root / args.availability_csv).resolve()
    baseline_bpit_dir = (repo_root / args.baseline_bpit_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    backup_downloads_dir = args.backup_downloads_dir.resolve()

    print("======================================================================")
    print(" B-PIT FINANCIAL DATA ENRICHMENT PIPELINE")
    print("======================================================================")
    print(f"Inputs:")
    print(f"  - Indicators DB:      {indicators_db}")
    print(f"  - Availability CSV:   {availability_csv}")
    print(f"  - Baseline B-PIT:     {baseline_bpit_dir}")
    print(f"Outputs:")
    print(f"  - Enriched Run Dir:   {output_dir}")
    print(f"  - Backup Downloads:   {backup_downloads_dir}")
    print("----------------------------------------------------------------------")

    assert indicators_db.exists(), f"Không tìm thấy {indicators_db}"
    assert availability_csv.exists(), f"Không tìm thấy {availability_csv}"
    assert baseline_bpit_dir.exists(), f"Không tìm thấy {baseline_bpit_dir}"

    input_hashes = {
        "indicators_db_sha256": sha256_file(indicators_db),
        "availability_csv_sha256": sha256_file(availability_csv),
    }

    # Bước 1: Phân loại ô đủ điều kiện
    print("[1/4] Đang quét và phân loại các ô đủ điều kiện làm giàu...")
    eligibility_svc = FinancialEnrichmentEligibility(
        indicators_path=indicators_db,
        availability_path=availability_csv,
    )
    analysis_res = eligibility_svc.analyze(start_year=2017, end_year=2024)
    eligible_cells = analysis_res["eligible_cells"]
    print(f"  -> Tìm thấy {len(eligible_cells)} ô đủ điều kiện làm giàu từ {analysis_res['eligible_rows_count']} dòng.")

    # Bước 2: Tính median từ tập FIT baseline
    print("[2/4] Đang tính trung vị (median) từ tập FIT baseline (FY2017-FY2024)...")
    labels_csv = baseline_bpit_dir / "labels.csv"
    medians_map, medians_records = compute_medians_from_fit(
        indicators_db_path=indicators_db,
        labels_csv_path=labels_csv,
        features=FEATURES,
        years=range(2017, 2025),
    )
    donor_counts = {(r["fiscal_year"], r["metric"]): r["n_observations"] for r in medians_records}
    print(f"  -> Đã tính {len(medians_records)} cặp (năm, chỉ số).")

    # Bước 3: Điền giá trị
    print("[3/4] Đang thực hiện điền giá trị trung vị...")
    imputed_records = impute_cells(
        eligible_cells=eligible_cells,
        medians_map=medians_map,
        donor_counts=donor_counts,
    )
    print(f"  -> Đã sinh {len(imputed_records)} bản ghi lineage.")

    # Bước 4: Xuất dữ liệu và manifest
    print("[4/4] Đang xuất database dẫn xuất và file audit...")
    git_sha = get_git_commit()
    manifest = export_enriched_dataset(
        original_db_path=indicators_db,
        output_dir=output_dir,
        imputed_records=imputed_records,
        medians_records=medians_records,
        input_hashes=input_hashes,
        git_commit_sha=git_sha,
    )

    print("----------------------------------------------------------------------")
    print("HOÀN THÀNH LÀM GIÀU DỮ LIỆU:")
    print(f"  - Database mới:       {output_dir / 'indicators.sqlite'}")
    print(f"  - SHA-256 SQLite mới: {manifest['outputs']['indicators_sqlite_sha256']}")
    print(f"  - Tổng số ô điền:     {manifest['stats']['total_imputed_cells']}")
    print(f"  - Số mã cổ phiếu:     {manifest['stats']['unique_imputed_tickers']}")
    print(f"  - Số dòng (mã-năm):   {manifest['stats']['unique_imputed_rows']}")

    # Sao lưu sang Downloads để người dùng tiện đối chiếu trực tiếp
    print(f"\nĐang sao lưu sang {backup_downloads_dir}...")
    backup_downloads_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_dir / "indicators.sqlite", backup_downloads_dir / "indicators.sqlite")
    shutil.copy2(output_dir / "imputed_cells.csv", backup_downloads_dir / "imputed_cells.csv")
    shutil.copy2(output_dir / "medians_by_year_metric.csv", backup_downloads_dir / "medians_by_year_metric.csv")
    shutil.copy2(output_dir / "imputation_summary.json", backup_downloads_dir / "imputation_summary.json")
    shutil.copy2(output_dir / "manifest.json", backup_downloads_dir / "manifest.json")
    print(f"  -> Đã sao lưu thành công toàn bộ vào {backup_downloads_dir}")
    print("======================================================================")

if __name__ == "__main__":
    main()
