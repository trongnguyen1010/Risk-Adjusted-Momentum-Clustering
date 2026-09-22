"""Execute bounded recovery of historical prices for verified transition securities."""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
import io
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..artifact_ids import new_artifact_id
from ..io import atomic_write, digest, encoded, now, read_json, write_json, write_rows
from .sources.base import PublicJsonClient, SemanticValidationError
from .sources.vnstock import KBSPublicHttpSource, map_kbs_wire_ohlcv_row, date_batches

STAGE = "A6.1 — Historical Identity Price Recovery"
KBS_ADAPTER_VERSION = "kbs-delta-public-http-transition-recovery-1"
AVAILABILITY_TIME = "17:00:00+07:00"

SUMMARY_COLUMNS = (
    "candidate_id", "security_id", "ticker", "from_exchange", "to_exchange",
    "effective_date", "fetch_start", "fetch_end", "requests_attempted",
    "requests_successful", "rows_recovered", "status",
)


def _iso(value: str) -> date:
    return date.fromisoformat(value)


def _inside(path: Path | str, parent: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} outside expected root: {resolved}") from exc
    return resolved


def plan_transition_requests(
    candidates_path: Path,
    collection_start: str = "2020-01-01",
    batch_days: int = 180,
) -> List[Dict[str, Any]]:
    """Build bounded KBS request chunks for each verified candidate from collection_start to effective_date - 1."""
    with candidates_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)

    start_limit = _iso(collection_start)
    plan = []
    for row in rows:
        if row.get("decision") != "VERIFIED":
            continue
        effective = _iso(row["effective_date"])
        last_date = effective - timedelta(days=1)
        if last_date < start_limit:
            continue

        ticker = row["from_ticker"].upper()
        security_id = row["security_id"]
        from_exchange = row["from_exchange"].upper()
        to_exchange = row["to_exchange"].upper()

        batches = list(date_batches(start_limit.isoformat(), last_date.isoformat(), days=batch_days))
        for batch_index, (b_start, b_end) in enumerate(batches, 1):
            request_id = f"req-{ticker}-{from_exchange}-{b_start}-{b_end}"
            plan.append({
                "request_id": request_id,
                "candidate_id": row.get("candidate_id", f"CAND-{ticker}"),
                "security_id": security_id,
                "ticker": ticker,
                "from_exchange": from_exchange,
                "to_exchange": to_exchange,
                "effective_date": row["effective_date"],
                "start": b_start,
                "end": b_end,
                "batch_index": batch_index,
                "total_batches": len(batches),
            })
    return plan


def build_transition_recovery(
    a6_artifact_dir: Path | str,
    *,
    root: Path | str,
    provider: Optional[Any] = None,
    collection_start: str = "2020-01-01",
    batch_days: int = 180,
    output_dir: Optional[Path | str] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """Fetch and normalize historical prices for verified transition securities."""
    root = Path(root).resolve()
    base = root / "artifacts" / "data_enrichment"
    a6_dir = _inside(a6_artifact_dir, base, "A6 artifact directory")

    a6_manifest = read_json(a6_dir / "manifest.json")
    if a6_manifest.get("status") != "PASS":
        raise ValueError("Transition price recovery requires a PASS A6 artifact")

    candidates_path = a6_dir / "identity_recovery_candidates.csv"
    if not candidates_path.is_file():
        raise FileNotFoundError(f"Missing candidates file: {candidates_path}")

    requests = plan_transition_requests(candidates_path, collection_start=collection_start, batch_days=batch_days)
    if not requests:
        raise ValueError("No verified transition candidates to recover")

    if provider is None:
        client = PublicJsonClient(timeout=20.0, attempts=3, min_interval=1.0)
        provider = KBSPublicHttpSource(client=client)

    run_id = new_artifact_id("m1-transition-recovery")
    output = base / run_id if output_dir is None else _inside(output_dir, base, "output directory")
    output.mkdir(parents=True, exist_ok=False)

    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    recovered_rows = []
    seen_dates = set()
    summary_by_cand = {}

    for req in requests:
        cand_id = req["candidate_id"]
        if cand_id not in summary_by_cand:
            summary_by_cand[cand_id] = {
                "candidate_id": cand_id,
                "security_id": req["security_id"],
                "ticker": req["ticker"],
                "from_exchange": req["from_exchange"],
                "to_exchange": req["to_exchange"],
                "effective_date": req["effective_date"],
                "fetch_start": req["start"],
                "fetch_end": req["end"],
                "requests_attempted": 0,
                "requests_successful": 0,
                "rows_recovered": 0,
                "status": "IN_PROGRESS",
            }
        summary_by_cand[cand_id]["fetch_end"] = req["end"]
        summary_by_cand[cand_id]["requests_attempted"] += 1

        if progress:
            progress(f"Fetching {req['ticker']} ({req['from_exchange']}) [{req['start']} to {req['end']}]")

        response = provider.acquire_ohlcv(req["ticker"], req["start"], req["end"], is_index=False)
        summary_by_cand[cand_id]["requests_successful"] += 1

        raw_filename = f"{req['request_id']}.json"
        raw_path = raw_dir / raw_filename
        if "body" in response and isinstance(response["body"], bytes):
            body_bytes = response["body"]
        else:
            body_bytes = encoded(response.get("payload", response))
        atomic_write(raw_path, body_bytes)

        payload = response.get("payload", {})
        data_day = payload.get("data_day", [])

        for item in data_day:
            mapped = map_kbs_wire_ohlcv_row(item, req["ticker"], req["from_exchange"])
            t_date = mapped["trade_date"]
            if t_date < req["start"] or t_date > req["end"]:
                continue
            key = (req["security_id"], t_date)
            if key in seen_dates:
                continue
            seen_dates.add(key)

            # Map to canonical daily schema
            row = {
                "security_id": req["security_id"],
                "ticker": req["ticker"],
                "exchange": req["from_exchange"],
                "trade_date": t_date,
                "adj_close": mapped["close"],
                "volume": mapped["volume"],
                "raw_open": mapped["open"],
                "raw_high": mapped["high"],
                "raw_low": mapped["low"],
                "raw_close": mapped["close"],
                "traded_value": None,
                "adjustment_basis": mapped["price_basis"].lower(),
                "price_unit": mapped["price_unit"],
                "volume_unit": mapped["volume_unit"],
                "trading_status": "normal",
                "available_at": f"{t_date}T{AVAILABILITY_TIME}",
                "source": "kbs_delta_public_http",
                "fetched_at": response.get("fetched_at", now()),
                "raw_path": raw_path.relative_to(output).as_posix(),
                "raw_sha256": digest(body_bytes),
            }
            recovered_rows.append(row)
            summary_by_cand[cand_id]["rows_recovered"] += 1

    recovered_rows.sort(key=lambda r: (r["security_id"], r["trade_date"]))

    # Finalize candidate statuses
    for cand in summary_by_cand.values():
        cand["status"] = "SUCCESS" if cand["rows_recovered"] > 0 else "NO_DATA"

    # Write outputs
    jsonl_path = output / "recovered_transition_rows.jsonl"
    write_rows(jsonl_path, recovered_rows)

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        parquet_path = output / "recovered_transition_rows.parquet"
        pq.write_table(pa.Table.from_pylist(recovered_rows), parquet_path, compression="snappy")
    except ImportError:
        parquet_path = None

    summary_rows = list(summary_by_cand.values())
    summary_path = output / "transition_recovery_summary.csv"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=SUMMARY_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(summary_rows)
    atomic_write(summary_path, stream.getvalue().encode("utf-8"))

    report_content = [
        "# Historical Identity Transition Price Recovery Report", "",
        f"- Run ID: `{run_id}`",
        f"- Generated at: `{now()}`",
        f"- Stage: `{STAGE}`",
        f"- Candidates processed: `{len(summary_rows)}`",
        f"- Total rows recovered: `{len(recovered_rows)}`",
        "- Canonical mutations: `0`",
        "",
        "## Summary by Security", "",
        "| Ticker | From Exchange | To Exchange | Start Date | Effective Date | Recovered Rows | Status |",
        "|---|---|---|---|---|---:|---|",
    ]
    for s in summary_rows:
        report_content.append(
            f"| {s['ticker']} | {s['from_exchange']} | {s['to_exchange']} | {s['fetch_start']} | "
            f"{s['effective_date']} | {s['rows_recovered']} | {s['status']} |"
        )
    atomic_write(output / "stage_report.md", "\n".join(report_content).encode("utf-8"))

    manifest = {
        "run_id": run_id,
        "stage": STAGE,
        "status": "PASS",
        "created_at": now(),
        "a6_artifact_id": a6_manifest["run_id"],
        "input_artifacts": [a6_manifest["run_id"]],
        "candidates_count": len(summary_rows),
        "total_requests": len(requests),
        "rows_recovered": len(recovered_rows),
        "network_requests": len(requests),
        "canonical_mutations": 0,
        "artifacts": {
            path.relative_to(output).as_posix(): digest(path.read_bytes())
            for path in sorted(output.rglob("*")) if path.is_file()
        },
    }
    write_json(output / "manifest.json", manifest)

    return output, manifest
