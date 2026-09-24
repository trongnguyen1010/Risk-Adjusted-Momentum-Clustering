#!/usr/bin/env python3
"""Optionally pack one checksum-validated, fully completed CafeF ticker offline."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from plan_cafef_c1_history_v3 import audit_v23_run, sha256_bytes, sha256_file, stable_json_bytes, atomic_write


class CompactionError(RuntimeError):
    pass


def _ticker_complete(run_dir: Path, ticker: str) -> dict:
    records, _summary = audit_v23_run(run_dir)
    record = next((item for item in records if item["ticker"] == ticker), None)
    if not record or record["audit_status"] != "LONG_HISTORY_COMPLETE":
        raise CompactionError(f"ticker is not fully completed and checksum-valid: {ticker}")
    return record


def _source_entries(run_dir: Path, ticker: str, contract_version: str) -> list[dict]:
    ticker_dir = run_dir / "raw" / ticker
    if not ticker_dir.is_dir():
        raise CompactionError(f"raw ticker directory does not exist: {ticker_dir}")
    entries: list[dict] = []
    for path in sorted(item for item in ticker_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(run_dir).as_posix()
        request_key = None
        if path.name.endswith(".meta.json"):
            request_key = json.loads(path.read_text(encoding="utf-8")).get("request_key")
        else:
            sidecar = path.with_suffix(".meta.json")
            if sidecar.is_file():
                request_key = json.loads(sidecar.read_text(encoding="utf-8")).get("request_key")
        entries.append({
            "original_relative_path": relative,
            "sha256": sha256_file(path),
            "byte_size": path.stat().st_size,
            "request_key": request_key,
            "contract_version": contract_version,
        })
    return entries


def _verify_archive(archive_path: Path, entries: list[dict]) -> None:
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            if set(members) != {entry["original_relative_path"] for entry in entries}:
                raise CompactionError("archive members do not exactly match compaction manifest")
            for entry in entries:
                stream = archive.extractfile(members[entry["original_relative_path"]])
                if stream is None or sha256_bytes(stream.read()) != entry["sha256"]:
                    raise CompactionError(f"archive checksum mismatch: {entry['original_relative_path']}")
    except (tarfile.TarError, OSError) as exc:
        raise CompactionError(f"archive validation failed: {exc}") from exc


def compact_ticker(run_dir: Path, ticker: str, *, delete_source: bool = False) -> Path:
    run_dir = run_dir.resolve()
    ticker = ticker.upper()
    record = _ticker_complete(run_dir, ticker)
    entries = _source_entries(run_dir, ticker, record["source_contract_version"])
    packed_dir = run_dir / "packed" / ticker
    archive_path = packed_dir / "cafef_raw.tar.gz"
    manifest_path = packed_dir / "manifest.json"
    manifest = {
        "compaction_version": "CAFEF_RAW_COMPACTION_V1",
        "source_run_id": run_dir.name,
        "ticker": ticker,
        "source_contract_version": record["source_contract_version"],
        "ticker_completion_status": record["audit_status"],
        "source_deleted": False,
        "members": entries,
    }
    if archive_path.exists() or manifest_path.exists():
        if not archive_path.is_file() or not manifest_path.is_file():
            raise CompactionError("existing pack is incomplete")
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("members") != entries:
            raise CompactionError("existing pack manifest differs from validated source")
        _verify_archive(archive_path, entries)
    else:
        packed_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".tmp.", suffix=".tar.gz", dir=packed_dir)
        os.close(fd)
        try:
            with tarfile.open(temp_name, "w:gz") as archive:
                for entry in entries:
                    source = run_dir / entry["original_relative_path"]
                    archive.add(source, arcname=entry["original_relative_path"], recursive=False)
            os.replace(temp_name, archive_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        _verify_archive(archive_path, entries)
        atomic_write(manifest_path, stable_json_bytes(manifest))
    if delete_source:
        _verify_archive(archive_path, entries)
        for entry in entries:
            source = run_dir / entry["original_relative_path"]
            if not source.is_file() or sha256_file(source) != entry["sha256"]:
                raise CompactionError(f"source changed before deletion: {entry['original_relative_path']}")
        shutil.rmtree(run_dir / "raw" / ticker)
        manifest["source_deleted"] = True
        atomic_write(manifest_path, stable_json_bytes(manifest))
    return packed_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack one completed CafeF ticker after offline verification")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--delete-source", action="store_true")
    args = parser.parse_args()
    result = compact_ticker(args.run_dir, args.ticker, delete_source=args.delete_source)
    print(json.dumps({"packed_directory": str(result), "source_deleted": args.delete_source}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
