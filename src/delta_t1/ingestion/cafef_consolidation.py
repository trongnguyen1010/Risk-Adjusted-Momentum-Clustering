"""Offline C7 inventory and supplemental planning for CafeF expansion handoffs."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

from delta_t1.ingestion.cafef_expansion import (
    HISTORY_POLICY, PAGE_SIZE, TARGET_COLLECTION_END, TARGET_START,
    cafef_trade_date, canonical_bytes, estimate_pages, page_rows, sha256_file,
)

C7_ARTIFACT_ID = "cafef-expansion-c7-partial-consolidation-v1"
SUPPLEMENTAL_ID = "cafef-supplemental-v1"
SUPPLEMENTAL_VERSION = "c7-cafef-supplemental-v1"
_META_RE = re.compile(r"^raw/([^/]+)/page-(\d+)\.metadata\.json$")


def _zip_json(archive: zipfile.ZipFile, name: str) -> dict:
    return json.loads(archive.read(name))


def _page_dates(body: bytes) -> list[str]:
    dates = []
    for row in page_rows(body):
        try:
            dates.append(cafef_trade_date(row["TradeDate"]))
        except (KeyError, TypeError, ValueError):
            continue
    return dates


def classify_acquisition(*, reported: str, pages: list[int], oldest: str | None,
                         completion_reason: str | None, last_page_empty: bool,
                         hard_stop: bool = False) -> tuple[str, str, int | None]:
    contiguous = pages == list(range(1, max(pages) + 1)) if pages else True
    if not contiguous:
        return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None
    if hard_stop or reported == "HARD_STOP":
        return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None
    if reported == "COMPLETE":
        reached = completion_reason == "TARGET_START_REACHED" and oldest is not None and oldest <= TARGET_START
        boundary = completion_reason == "EMPTY_PROVIDER_BOUNDARY" and last_page_empty
        if reached or boundary:
            return "COMPLETE", "COMPLETE_RETAINED", None
        return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None
    if reported in {"RUNNING", "PARTIAL"}:
        if pages:
            return "ACQUISITION_PARTIAL", "CONTINUE_FROM_PAGE_N", max(pages) + 1
        return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None
    if reported == "NOT_STARTED":
        if not pages:
            return "NOT_YET_ACQUIRED", "START_FROM_1", 1
        return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None
    if reported == "FAILED":
        return "ACQUISITION_FAILED", "MANUAL_REVIEW", None
    return "HARD_STOP_REVIEW", "MANUAL_REVIEW", None


def inspect_handoff(path: Path) -> tuple[list[dict], dict, dict]:
    zip_sha = sha256_file(path)
    with zipfile.ZipFile(path) as archive:
        manifest = _zip_json(archive, "handoff_manifest.json")
        assignment = _zip_json(archive, "assignment.json")
        report = _zip_json(archive, "worker_report.json")
        names = set(archive.namelist())
        pages_by_ticker: dict[str, list[tuple[int, dict, bytes]]] = {ticker: [] for ticker in assignment["tickers"]}
        for name in sorted(names):
            match = _META_RE.match(name)
            if not match:
                continue
            ticker, page_text = match.groups()
            if ticker not in pages_by_ticker:
                raise ValueError(f"unexpected raw ticker {ticker} in {path.name}")
            raw_name = name.replace(".metadata.json", ".json")
            if raw_name not in names:
                raise ValueError(f"metadata without raw page: {name}")
            pages_by_ticker[ticker].append((int(page_text), json.loads(archive.read(name)), archive.read(raw_name)))
        hard_stop_tickers = {event.get("ticker") for event in manifest.get("hard_stop_events", [])}
        security_by_ticker = dict(zip(assignment["tickers"], assignment["security_ids"]))
        rows = []
        for ticker in assignment["tickers"]:
            evidence = sorted(pages_by_ticker[ticker], key=lambda item: item[0])
            pages = [item[0] for item in evidence]
            dates = [date for _, _, body in evidence for date in _page_dates(body)]
            last_empty = bool(evidence and not page_rows(evidence[-1][2]))
            reported = report["statuses"].get(ticker, "UNREPORTED")
            reason = report.get("completion_reasons", {}).get(ticker)
            status, action, next_page = classify_acquisition(
                reported=reported, pages=pages, oldest=min(dates) if dates else None,
                completion_reason=reason, last_page_empty=last_empty,
                hard_stop=ticker in hard_stop_tickers,
            )
            rows.append({
                "ticker": ticker, "security_id": security_by_ticker[ticker],
                "worker_id": assignment["worker_id"], "assignment_id": assignment["assignment_id"],
                "handoff_run_id": manifest["run_id"], "status_reported": reported,
                "acquisition_status": status, "raw_page_count": len(pages),
                "first_page": min(pages) if pages else "", "last_page": max(pages) if pages else "",
                "oldest_observed_date": min(dates) if dates else "",
                "newest_observed_date": max(dates) if dates else "",
                "completion_reason": reason or "", "next_page_if_continuable": next_page or "",
                "action": action, "source_zip": path.name, "source_zip_sha256": zip_sha,
                "initial_page_sequence_contiguous": pages == list(range(1, max(pages) + 1)) if pages else True,
            })
        counts = Counter(row["acquisition_status"] for row in rows)
        summary = {
            "worker_id": assignment["worker_id"], "assignment_id": assignment["assignment_id"],
            "handoff_run_id": manifest["run_id"], "source_zip": path.name,
            "source_zip_sha256": zip_sha, "network_requests": manifest["network_requests"],
            "raw_page_count": sum(row["raw_page_count"] for row in rows),
            **{status: counts.get(status, 0) for status in (
                "COMPLETE", "ACQUISITION_PARTIAL", "NOT_YET_ACQUIRED",
                "ACQUISITION_FAILED", "HARD_STOP_REVIEW")},
        }
        provenance = {"worker_id": assignment["worker_id"], "assignment_id": assignment["assignment_id"],
                      "run_id": manifest["run_id"], "zip": path.name, "zip_sha256": zip_sha,
                      "git_commit": manifest["git_commit"]}
        return rows, summary, provenance


def build_supplemental_plan(inventory: list[dict], shard_count: int = 3) -> tuple[list[dict], list[dict]]:
    if len(inventory) != 600 or len({row["ticker"] for row in inventory}) != 600:
        raise ValueError("inventory must be exact 600-security union")
    candidates = [dict(row) for row in inventory if row["acquisition_status"] != "COMPLETE"]
    runnable = [row for row in candidates if row["action"] in {"START_FROM_1", "CONTINUE_FROM_PAGE_N"}]
    bins = [{"shard_id": f"supplemental-{index:02d}", "jobs": [], "estimated_requests": 0}
            for index in range(1, shard_count + 1)]
    for row in runnable:
        if row["action"] == "START_FROM_1":
            start_page = 1
        else:
            start_page = int(row["next_page_if_continuable"])
            if not row["initial_page_sequence_contiguous"] or start_page != int(row["last_page"]) + 1:
                raise ValueError(f"unsafe continuation for {row['ticker']}")
        remaining = max(1, estimate_pages(row) - start_page + 1)
        row.update(start_page=start_page, estimated_remaining_requests=remaining)
    manual = [row for row in candidates if row["action"] == "MANUAL_REVIEW"]
    ordered = sorted(runnable, key=lambda row: (-row["estimated_remaining_requests"], row["ticker"]))
    for row in ordered:
        bucket = min(bins, key=lambda value: (value["estimated_requests"], value["shard_id"]))
        bucket["jobs"].append(row)
        bucket["estimated_requests"] += row["estimated_remaining_requests"]
    for row in manual:
        row.update(start_page="", estimated_remaining_requests=0)
    if len({row["ticker"] for bucket in bins for row in bucket["jobs"]}) != len(runnable):
        raise ValueError("duplicate supplemental ticker ownership")
    return sorted(candidates, key=lambda row: row["ticker"]), bins


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")
