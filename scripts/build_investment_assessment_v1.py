#!/usr/bin/env python3
"""
scripts/build_investment_assessment_v1.py

CLI xây dựng dữ liệu Investment Assessment Offline (Stage S3: Task R1-18).
Đọc dữ liệu B-PIT Enriched và SQLite Indicators Enriched, xây dựng:
  - assessments.jsonl: Đánh giá đầu tư cho từng mã cổ phiếu (D-ASS-01).
  - peer_benchmarks.csv: Bảng đối chiếu nhóm Peers theo từng chỉ số.
  - coverage.csv: Thống kê độ phủ dữ liệu 18 đặc trưng.
  - feature_history.jsonl: Lịch sử 5-10 năm của từng mã.
  - manifest.json: Khóa toàn diện input hashes, output hashes và siêu dữ liệu.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from delta_t1.experiments.investment_assessment_v1 import (
    OfflineAssessmentBuilder,
    DEFAULT_AS_OF,
)

def main():
    parser = argparse.ArgumentParser(description="Build Investment Assessment Offline Artifacts")
    parser.add_argument(
        "--indicators-db",
        type=Path,
        default=Path("data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite"),
        help="Đường dẫn file indicators.sqlite đã làm giàu",
    )
    parser.add_argument(
        "--availability-csv",
        type=Path,
        default=Path("data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv"),
        help="Đường dẫn file availability.csv",
    )
    parser.add_argument(
        "--bpit-labels",
        type=Path,
        default=Path("data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01/labels.csv"),
        help="Đường dẫn file labels.csv của B-PIT Enriched",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=DEFAULT_AS_OF,
        help="Ngày đánh giá giả lập demo (mặc định 2026-01-02)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/experiments/assessment/assessment_v1_run01"),
        help="Thư mục xuất kết quả đánh giá",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        nargs="*",
        default=[],
        help="Danh sách mã cổ phiếu cần đánh giá (mặc định lấy toàn bộ mã non-financial)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    indicators_db = (repo_root / args.indicators_db).resolve()
    availability_csv = (repo_root / args.availability_csv).resolve()
    bpit_labels = (repo_root / args.bpit_labels).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    print("======================================================================")
    print(" DELTA INVESTMENT ASSESSMENT OFFLINE BUILDER (D-ASS-01)")
    print("======================================================================")
    print(f"As-of Date:       {args.as_of}")
    print(f"Indicators DB:    {indicators_db}")
    print(f"Availability CSV: {availability_csv}")
    print(f"B-PIT Labels:     {bpit_labels}")
    print(f"Output Dir:       {output_dir}")

    if not indicators_db.exists():
        print(f"LỖI: Không tìm thấy indicators database tại {indicators_db}", file=sys.stderr)
        sys.exit(1)
    if not availability_csv.exists():
        print(f"LỖI: Không tìm thấy availability CSV tại {availability_csv}", file=sys.stderr)
        sys.exit(1)
    if not bpit_labels.exists():
        print(f"LỖI: Không tìm thấy B-PIT labels tại {bpit_labels}", file=sys.stderr)
        sys.exit(1)

    # Lấy danh sách tickers nếu không chỉ định
    tickers = args.tickers
    if not tickers:
        db = sqlite3.connect(f"file:{indicators_db}?mode=ro", uri=True)
        try:
            tickers = sorted([t for (t,) in db.execute("SELECT ticker FROM company WHERE sector_group = 'NON_FINANCIAL'").fetchall()])
        finally:
            db.close()

    print(f"\n[1/3] Đang khởi tạo Orchestrator cho {len(tickers)} mã...")
    builder = OfflineAssessmentBuilder(
        indicators_db_path=indicators_db,
        availability_csv_path=availability_csv,
        bpit_labels_path=bpit_labels,
        as_of=args.as_of,
    )

    print(f"[2/3] Đang thực hiện đánh giá và phân loại theo bộ quy tắc D-ASS-01...")
    payloads = builder.build_all(tickers)

    print(f"[3/3] Đang xuất artifact sang {output_dir}...")
    manifest = builder.export_artifacts(payloads, output_dir)

    print("\n----------------------------------------------------------------------")
    print("KẾT QUẢ ĐÁNH GIÁ ĐẦU TƯ:")
    print(f"  - Tổng số mã:                 {manifest['total_tickers']}")
    for verdict, count in manifest["verdict_summary"].items():
        print(f"  - {verdict:30s}: {count}")
    print(f"\nManifest xuất tại: {output_dir / 'manifest.json'}")
    print("======================================================================")

if __name__ == "__main__":
    main()
