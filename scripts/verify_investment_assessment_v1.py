#!/usr/bin/env python3
"""Read-only verifier for ``investment_assessment_v1`` release artifacts.

The verifier validates an immutable offline artifact before a product reader can
pin it. It never builds features, replays the assessment engine, or mutates the
artifact. A report can only be written to an explicit path outside that artifact.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "assessment_release_verifier_v1"
FINANCIAL_FEATURES = frozenset({"roe", "roa", "gross_margin", "net_margin", "debt_to_equity", "current_ratio", "asset_turnover", "revenue_growth", "cfo_to_ni"})
MARKET_FEATURES = frozenset({"mom_21", "mom_63", "mom_126", "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21", "downside_vol_63"})
FEATURES = FINANCIAL_FEATURES | MARKET_FEATURES
VALID_VERDICTS = frozenset({"WORTH_CONSIDERING", "MONITOR", "LOW_PRIORITY", "INSUFFICIENT_EVIDENCE"})
REQUIRED_OUTPUT_FILES = frozenset({"assessments.jsonl", "peer_benchmarks.csv", "coverage.csv", "feature_history.jsonl"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_iso_date(value: Any, label: str, errors: list[str], *, allow_blank: bool = False) -> date | None:
    if allow_blank and value in (None, ""):
        return None
    if not isinstance(value, str):
        errors.append(f"{label} phải là ngày ISO YYYY-MM-DD")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} không phải ngày ISO hợp lệ: {value!r}")
        return None


def _is_number_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)))


def _validate_hash(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        errors.append(f"{label} không phải SHA-256 hợp lệ")


def _load_manifest(artifact_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        errors.append("Thiếu manifest.json")
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"Không đọc được manifest.json: {exc}")
        return None
    if not isinstance(manifest, dict):
        errors.append("manifest.json phải là JSON object")
        return None
    return manifest


def _validate_manifest(artifact_dir: Path, manifest: dict[str, Any], errors: list[str]) -> date | None:
    if manifest.get("version") != "investment_assessment_v1":
        errors.append("manifest.version phải là investment_assessment_v1")
    as_of = _parse_iso_date(manifest.get("as_of"), "manifest.as_of", errors)
    _validate_hash(manifest.get("deterministic_content_sha256"), "manifest.deterministic_content_sha256", errors)

    total_tickers = manifest.get("total_tickers")
    if not isinstance(total_tickers, int) or isinstance(total_tickers, bool) or total_tickers < 0:
        errors.append("manifest.total_tickers phải là số nguyên không âm")

    input_hashes = manifest.get("input_hashes")
    if not isinstance(input_hashes, dict):
        errors.append("manifest.input_hashes phải là object")
    else:
        for name in ("indicators_sqlite_sha256", "availability_csv_sha256", "bpit_labels_csv_sha256"):
            _validate_hash(input_hashes.get(name), f"manifest.input_hashes.{name}", errors)

    output_files = manifest.get("output_files")
    if not isinstance(output_files, dict):
        errors.append("manifest.output_files phải là object")
        return as_of
    missing = REQUIRED_OUTPUT_FILES - set(output_files)
    if missing:
        errors.append(f"manifest.output_files thiếu: {', '.join(sorted(missing))}")
    for filename, expected_hash in output_files.items():
        if not isinstance(filename, str) or Path(filename).name != filename:
            errors.append(f"Tên output không hợp lệ: {filename!r}")
            continue
        _validate_hash(expected_hash, f"manifest.output_files.{filename}", errors)
        output_path = artifact_dir / filename
        if not output_path.is_file():
            errors.append(f"Thiếu output: {filename}")
        elif isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash):
            if sha256_file(output_path) != expected_hash:
                errors.append(f"Checksum không khớp: {filename}")
    return as_of


def _validate_assessments(path: Path, as_of: date | None, errors: list[str]) -> tuple[set[str], dict[str, int]]:
    tickers: set[str] = set()
    verdict_counts: dict[str, int] = {}
    if not path.is_file():
        return tickers, verdict_counts
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                errors.append(f"assessments.jsonl dòng {line_number} trống")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"assessments.jsonl dòng {line_number} không phải JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"assessments.jsonl dòng {line_number} phải là object")
                continue
            ticker = record.get("ticker")
            if not isinstance(ticker, str) or not ticker or ticker != ticker.strip():
                errors.append(f"assessments.jsonl dòng {line_number} có ticker không hợp lệ")
            elif ticker in tickers:
                errors.append(f"assessments.jsonl có ticker trùng: {ticker}")
            else:
                tickers.add(ticker)
            record_as_of = _parse_iso_date(record.get("as_of"), f"assessments.jsonl dòng {line_number}.as_of", errors)
            if as_of is not None and record_as_of is not None and record_as_of != as_of:
                errors.append(f"assessments.jsonl dòng {line_number} có as_of không khớp manifest")
            verdict = record.get("verdict")
            if verdict not in VALID_VERDICTS:
                errors.append(f"assessments.jsonl dòng {line_number} có verdict không hợp lệ: {verdict!r}")
            else:
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            usable_from = record.get("usable_from_date")
            if usable_from is not None:
                usable_date = _parse_iso_date(usable_from, f"assessments.jsonl dòng {line_number}.usable_from_date", errors)
                if as_of is not None and usable_date is not None and usable_date > as_of:
                    errors.append(f"assessments.jsonl dòng {line_number} có future leakage")
            for field, allowed_features in (("financial_features", FINANCIAL_FEATURES), ("market_features", MARKET_FEATURES)):
                values = record.get(field)
                if not isinstance(values, dict) or set(values) != allowed_features:
                    errors.append(f"assessments.jsonl dòng {line_number}.{field} không đúng whitelist")
                    continue
                for feature, value in values.items():
                    if not _is_number_or_null(value):
                        errors.append(f"assessments.jsonl dòng {line_number}.{field}.{feature} không phải số/null")
            peers = record.get("peer_comparisons")
            no_peer_evidence = verdict == "INSUFFICIENT_EVIDENCE" and peers == {}
            if no_peer_evidence:
                continue
            if not isinstance(peers, dict) or set(peers) != FEATURES:
                errors.append(f"assessments.jsonl dòng {line_number}.peer_comparisons không đúng whitelist")
            else:
                for feature, peer in peers.items():
                    if not isinstance(peer, dict):
                        errors.append(f"assessments.jsonl dòng {line_number}.peer_comparisons.{feature} phải là object")
                        continue
                    count = peer.get("peer_count")
                    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                        errors.append(f"assessments.jsonl dòng {line_number}.{feature}.peer_count không hợp lệ")
                    for key in ("peer_median", "p25", "p75"):
                        if not _is_number_or_null(peer.get(key)):
                            errors.append(f"assessments.jsonl dòng {line_number}.{feature}.{key} không phải số/null")
    return tickers, verdict_counts


def _validate_peers(path: Path, known_tickers: set[str], errors: list[str]) -> None:
    if not path.is_file():
        return
    required_columns = {"ticker", "metric", "peer_basis", "peer_count", "peer_median", "p25", "p75"}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            errors.append("peer_benchmarks.csv thiếu cột bắt buộc")
            return
        for line_number, row in enumerate(reader, 2):
            if row.get("ticker") not in known_tickers:
                errors.append(f"peer_benchmarks.csv dòng {line_number} có ticker không thuộc Assessment")
            if row.get("metric") not in FEATURES:
                errors.append(f"peer_benchmarks.csv dòng {line_number} có metric ngoài whitelist")
            if not row.get("peer_basis"):
                errors.append(f"peer_benchmarks.csv dòng {line_number} thiếu peer_basis")
            try:
                count = int(row.get("peer_count", ""))
                if count < 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"peer_benchmarks.csv dòng {line_number} có peer_count không hợp lệ")
            for field in ("peer_median", "p25", "p75"):
                try:
                    value = float(row.get(field, ""))
                    if not math.isfinite(value):
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(f"peer_benchmarks.csv dòng {line_number}.{field} không phải số hữu hạn")


def _validate_coverage(path: Path, total_tickers: Any, errors: list[str]) -> None:
    if not path.is_file():
        return
    required_columns = {"feature", "category", "total_tickers", "valid_count", "coverage_pct"}
    seen_features: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            errors.append("coverage.csv thiếu cột bắt buộc")
            return
        for line_number, row in enumerate(reader, 2):
            feature = row.get("feature")
            if feature not in FEATURES:
                errors.append(f"coverage.csv dòng {line_number} có feature ngoài whitelist")
                continue
            if feature in seen_features:
                errors.append(f"coverage.csv có feature trùng: {feature}")
            seen_features.add(feature)
            expected_category = "FINANCIAL" if feature in FINANCIAL_FEATURES else "MARKET"
            if row.get("category") != expected_category:
                errors.append(f"coverage.csv dòng {line_number} có category không khớp {feature}")
            try:
                row_total = int(row.get("total_tickers", ""))
                valid_count = int(row.get("valid_count", ""))
                coverage_pct = float(row.get("coverage_pct", ""))
                if row_total != total_tickers or not 0 <= valid_count <= row_total:
                    raise ValueError
                expected_coverage = round(valid_count / row_total * 100, 2) if row_total else 0.0
                if not math.isfinite(coverage_pct) or abs(coverage_pct - expected_coverage) > 0.01:
                    raise ValueError
            except (TypeError, ValueError, ZeroDivisionError):
                errors.append(f"coverage.csv dòng {line_number} có counts/coverage không hợp lệ")
    if seen_features != FEATURES:
        errors.append("coverage.csv không bao phủ đúng whitelist 18 features")


def _validate_history(path: Path, as_of: date | None, known_tickers: set[str], errors: list[str]) -> None:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"feature_history.jsonl dòng {line_number} không phải JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"feature_history.jsonl dòng {line_number} phải là object")
                continue
            if record.get("ticker") not in known_tickers:
                errors.append(f"feature_history.jsonl dòng {line_number} có ticker không thuộc Assessment")
            if record.get("metric") not in FEATURES:
                errors.append(f"feature_history.jsonl dòng {line_number} có metric ngoài whitelist")
            if not _is_number_or_null(record.get("value")):
                errors.append(f"feature_history.jsonl dòng {line_number}.value không phải số/null")
            if not isinstance(record.get("status"), str) or not record.get("status"):
                errors.append(f"feature_history.jsonl dòng {line_number} thiếu status")
            if not isinstance(record.get("source"), str) or not record.get("source"):
                errors.append(f"feature_history.jsonl dòng {line_number} thiếu source")
            # Financial history may deliberately retain an evidence gap instead
            # of inventing an availability date. A present date is still PIT-checked.
            usable_date = _parse_iso_date(
                record.get("usable_from_date"),
                f"feature_history.jsonl dòng {line_number}.usable_from_date",
                errors,
                allow_blank=True,
            )
            if as_of is not None and usable_date is not None and usable_date > as_of:
                errors.append(f"feature_history.jsonl dòng {line_number} có future leakage")


def verify_assessment_artifacts(artifact_dir: Path) -> dict[str, Any]:
    """Return a read-only integrity report for one Assessment release artifact."""
    artifact_dir = artifact_dir.resolve()
    errors: list[str] = []
    manifest = _load_manifest(artifact_dir, errors)
    as_of: date | None = None
    tickers: set[str] = set()
    verdict_counts: dict[str, int] = {}
    if manifest is not None:
        as_of = _validate_manifest(artifact_dir, manifest, errors)
        tickers, verdict_counts = _validate_assessments(artifact_dir / "assessments.jsonl", as_of, errors)
        total_tickers = manifest.get("total_tickers")
        if isinstance(total_tickers, int) and not isinstance(total_tickers, bool) and len(tickers) != total_tickers:
            errors.append("Số ticker trong assessments.jsonl không khớp manifest.total_tickers")
        expected_verdicts = manifest.get("verdict_summary")
        if isinstance(expected_verdicts, dict):
            normalized_expected = {key: int(value) for key, value in expected_verdicts.items() if isinstance(value, int)}
            normalized_actual = {verdict: verdict_counts.get(verdict, 0) for verdict in VALID_VERDICTS}
            if normalized_expected != normalized_actual:
                errors.append("verdict_summary không khớp assessments.jsonl")
        else:
            errors.append("manifest.verdict_summary phải là object")
        _validate_peers(artifact_dir / "peer_benchmarks.csv", tickers, errors)
        _validate_coverage(artifact_dir / "coverage.csv", total_tickers, errors)
        _validate_history(artifact_dir / "feature_history.jsonl", as_of, tickers, errors)
    manifest_path = artifact_dir / "manifest.json"
    return {
        "verification_version": VERSION,
        "verification_status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "artifact_manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
        "total_assessments": len(tickers),
        "verdict_counts": {verdict: verdict_counts.get(verdict, 0) for verdict in sorted(VALID_VERDICTS)},
        "errors": errors,
        "as_of": as_of.isoformat() if as_of is not None else None,
        "deterministic_content_sha256": manifest.get("deterministic_content_sha256") if manifest is not None else None,
    }


def write_verification_report(output_path: Path, report: dict[str, Any], artifact_dir: Path) -> None:
    """Write an explicit sidecar report without mutating the immutable artifact."""
    output_path = output_path.resolve()
    artifact_dir = artifact_dir.resolve()
    if output_path == artifact_dir or artifact_dir in output_path.parents:
        raise ValueError("verification report phải nằm ngoài thư mục artifact immutable")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["verified_at"] = datetime.now(timezone.utc).isoformat()
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Investment Assessment release artifacts")
    parser.add_argument("--dir", type=Path, default=Path("data/experiments/assessment/assessment_v1_run01"), help="Thư mục artifact Assessment cần kiểm tra")
    parser.add_argument("--output", type=Path, help="Đường dẫn sidecar verification.json ngoài artifact (tùy chọn)")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    artifact_dir = (repo_root / args.dir).resolve() if not args.dir.is_absolute() else args.dir.resolve()
    report = verify_assessment_artifacts(artifact_dir)
    if args.output is not None:
        output_path = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
        write_verification_report(output_path, report, artifact_dir)
        print(f"Đã ghi sidecar verification: {output_path}")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
