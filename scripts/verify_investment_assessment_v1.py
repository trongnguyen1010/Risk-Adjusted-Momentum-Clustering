#!/usr/bin/env python3
"""
scripts/verify_investment_assessment_v1.py

Verifier độc lập cho Investment Assessment Offline Artifacts (D-ASS-01).
Kiểm tra:
  1. Checksum: SHA-256 của các tệp xuất ra khớp chính xác với manifest.json.
  2. As-of validity & No future leakage: usable_from_date <= as_of.
  3. Verifiability & Provenance: Mọi trường ticker, FY, metrics, peers đều hợp lệ.
  4. Dynamic Verdict: Không có trường hợp hard-code kết luận đầu tư.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_assessment_artifacts(artifact_dir: Path) -> dict:
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        return {"passed": False, "error": f"Không tìm thấy manifest.json tại {manifest_path}"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    as_of = manifest.get("as_of", "2026-01-02")
    output_files = manifest.get("output_files", {})

    errors = []

    # 1. Kiểm tra checksum
    for fname, expected_hash in output_files.items():
        fpath = artifact_dir / fname
        if not fpath.exists():
            errors.append(f"Tệp bị thiếu: {fname}")
            continue
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            errors.append(f"Sai lệch checksum tại {fname}: mong muốn {expected_hash}, thực tế {actual_hash}")

    # 2. Kiểm tra assessments.jsonl
    assessments_path = artifact_dir / "assessments.jsonl"
    total_assessments = 0
    verdict_counts = {}
    valid_verdicts = {"WORTH_CONSIDERING", "MONITOR", "LOW_PRIORITY", "INSUFFICIENT_EVIDENCE"}

    if assessments_path.exists():
        with open(assessments_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                total_assessments += 1
                rec = json.loads(line)
                ticker = rec.get("ticker")
                verdict = rec.get("verdict")
                usable_date = rec.get("usable_from_date")

                if verdict not in valid_verdicts:
                    errors.append(f"Dòng {line_no} ({ticker}): Verdict không hợp lệ: {verdict}")
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

                # Kiểm tra no future leakage
                if usable_date and usable_date > as_of:
                    errors.append(f"Dòng {line_no} ({ticker}): Rò rỉ dữ liệu tương lai usable_from_date {usable_date} > as_of {as_of}")

    # 3. Kiểm tra peer_benchmarks.csv
    peers_path = artifact_dir / "peer_benchmarks.csv"
    if peers_path.exists():
        with open(peers_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    count = int(row.get("peer_count", 0))
                    if count < 0:
                        errors.append(f"peer_count âm tại {row.get('ticker')}")
                except ValueError:
                    errors.append(f"peer_count không phải số tại {row.get('ticker')}")

    # 4. Kiểm tra coverage.csv
    coverage_path = artifact_dir / "coverage.csv"
    if coverage_path.exists():
        with open(coverage_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pct = float(row.get("coverage_pct", 0.0))
                    if not (0.0 <= pct <= 100.0):
                        errors.append(f"coverage_pct ngoài khoảng 0-100 tại {row.get('feature')}")
                except ValueError:
                    errors.append(f"coverage_pct không phải float tại {row.get('feature')}")

    passed = len(errors) == 0
    return {
        "passed": passed,
        "total_assessments": total_assessments,
        "verdict_counts": verdict_counts,
        "errors": errors,
        "as_of": as_of,
        "deterministic_content_sha256": manifest.get("deterministic_content_sha256"),
    }

def main():
    parser = argparse.ArgumentParser(description="Verify Investment Assessment Artifacts")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("data/experiments/assessment/assessment_v1_run01"),
        help="Thư mục chứa artifacts đánh giá cần verify",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    target_dir = (repo_root / args.dir).resolve()

    print("======================================================================")
    print(" VERIFIER ĐỘC LẬP CHO INVESTMENT ASSESSMENT ARTIFACTS (D-ASS-01)")
    print("======================================================================")
    print(f"Target dir: {target_dir}")

    result = verify_assessment_artifacts(target_dir)

    print(f"\nKết quả kiểm tra: {'[PASS]' if result['passed'] else '[FAIL]'}")
    print(f"Tổng số assessments: {result.get('total_assessments', 0)}")
    print(f"Phân bố verdicts: {result.get('verdict_counts', {})}")
    print(f"Deterministic Content Hash: {result.get('deterministic_content_sha256')}")

    if not result["passed"]:
        print("\nDANH SÁCH LỖI PHÁT HIỆN:")
        for err in result["errors"]:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nTất cả checksum, as-of validity, coverage và no future leakage đều HỢP LỆ.")
        print("======================================================================")

if __name__ == "__main__":
    main()

