"""Frozen CafeF expansion planning, acquisition, and handoff contracts for C6."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from delta_t1.ingestion.sources.cafef import ADAPTER_VERSION, TRADE_HISTORY_ENDPOINT, cafef_trade_date

EXPANSION_ID = "cafef-expansion-v1"
EXECUTION_VERSION = "c6-cafef-expansion-v1"
EXCHANGES = ("HOSE", "HNX", "UPCOM")
PAGE_SIZE = 30
TARGET_START = "2021-09-23"
TARGET_COLLECTION_END = "2026-09-23"
COMPARISON_SNAPSHOT = "2026-08-28"
RETRYABLE = {500, 502, 503, 504}
HARD_STOP = {401, 403, 429}
SECRET_NAMES = re.compile(r"(?:cookie|token|secret|password|credential|browser.?profile)", re.I)


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def assignment_digest(assignment: dict) -> str:
    clean = {key: value for key, value in assignment.items() if key != "assignment_sha256"}
    return sha256_bytes(canonical_bytes(clean))


def validate_assignment(root: Path, assignment_path: Path, *, require_git: bool = True) -> tuple[dict, dict, dict]:
    assignment = read_json(assignment_path)
    config_dir = assignment_path.resolve().parent
    index = read_json(config_dir / "index.json")
    universe = read_json(config_dir / "universe.json")
    contract = read_json(config_dir / "crawl_contract.json")
    errors = []
    expected = assignment_digest(assignment)
    if assignment.get("assignment_sha256") != expected:
        errors.append("assignment hash mismatch")
    entry = next((row for row in index["assignments"] if row["assignment_id"] == assignment.get("assignment_id")), None)
    if not entry or entry.get("sha256") != expected:
        errors.append("index assignment hash mismatch")
    if assignment.get("universe_hash") != sha256_file(config_dir / "universe.json"):
        errors.append("universe hash mismatch")
    if assignment.get("crawl_contract_hash") != sha256_file(config_dir / "crawl_contract.json"):
        errors.append("crawl contract hash mismatch")
    if assignment.get("source") != "cafef" or assignment.get("endpoint") != TRADE_HISTORY_ENDPOINT:
        errors.append("source endpoint mismatch")
    if assignment.get("page_size") != PAGE_SIZE or contract.get("page_size") != PAGE_SIZE:
        errors.append("page-size contract mismatch")
    if assignment.get("target_start") != TARGET_START or assignment.get("target_collection_end") != TARGET_COLLECTION_END:
        errors.append("target range mismatch")
    tickers = assignment.get("tickers", [])
    security_ids = assignment.get("security_ids", [])
    if len(tickers) != len(set(tickers)) or len(security_ids) != len(set(security_ids)):
        errors.append("duplicate assignment identity")
    selected = {row["ticker"]: row for row in universe["securities"]}
    if set(tickers) - set(selected):
        errors.append("assignment ticker outside frozen universe")
    if any(selected[t]["security_id"] != sid for t, sid in zip(tickers, security_ids)):
        errors.append("ticker/security ownership mismatch")
    if require_git:
        if git_value(root, "branch", "--show-current") != assignment["git_branch"]:
            errors.append("git branch mismatch")
        if assignment.get("execution_version") != EXECUTION_VERSION:
            errors.append("execution version mismatch")
        if git_value(root, "status", "--short"):
            errors.append("git worktree is not clean")
    if errors:
        raise ValueError("; ".join(errors))
    return assignment, universe, contract


def current_aliases(current_universe: list[dict], identity_rows: list[dict]) -> set[str]:
    aliases = {row["ticker"].upper() for row in current_universe}
    for row in identity_rows:
        current = str(row.get("current_ticker", "")).upper()
        if current:
            aliases.add(current)
        intervals = row.get("historical_identity_intervals", "[]")
        if isinstance(intervals, str):
            try:
                intervals = json.loads(intervals)
            except json.JSONDecodeError:
                intervals = []
        for interval in intervals or []:
            ticker = str(interval.get("ticker", "")).upper()
            if ticker:
                aliases.add(ticker)
    return aliases


def normalized_listing(payload: object) -> tuple[list[dict], list[dict]]:
    if not isinstance(payload, list):
        raise ValueError("KBS listing payload must be an array")
    eligible, excluded = [], []
    seen = set()
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        ticker = str(raw.get("symbol", "")).strip().upper()
        exchange = str(raw.get("exchange", "")).strip().upper()
        name = str(raw.get("name", "")).strip()
        instrument_type = str(raw.get("type", "")).strip().lower()
        evidence = {"ticker": ticker, "exchange": exchange, "company_name": name,
                    "instrument_type": instrument_type or "UNAVAILABLE"}
        if not ticker.isalnum() or exchange not in EXCHANGES or not name:
            evidence["selection_status"] = "INSUFFICIENT_DISCOVERY_EVIDENCE"
            excluded.append(evidence)
        elif instrument_type != "stock":
            evidence["selection_status"] = "INSTRUMENT_TYPE_EXCLUDED"
            excluded.append(evidence)
        elif ticker in seen:
            evidence["selection_status"] = "POSSIBLE_IDENTITY_DUPLICATE"
            excluded.append(evidence)
        else:
            seen.add(ticker)
            eligible.append(evidence)
    return eligible, excluded


def priority_key(row: dict) -> tuple:
    # Only evidence available before acquisition is used. No provider success signal participates.
    return (EXCHANGES.index(row["exchange"]), row["ticker"])


def estimate_pages(row: dict) -> int:
    # 1,260 approximate sessions / 30, plus one overlap page. Listing evidence is unavailable.
    return 43


def freeze_plan(payload: object, current_universe: list[dict], identity_rows: list[dict], *, target: int = 600,
                reserve_target: int = 100) -> dict:
    candidates, excluded = normalized_listing(payload)
    aliases = current_aliases(current_universe, identity_rows)
    current_tickers = {row["ticker"].upper() for row in current_universe}
    current_ids = {row["security_id"] for row in current_universe}
    ranking = []
    for row in candidates:
        security_id = f"KBS:{row['exchange']}:{row['ticker']}"
        if row["ticker"] in current_tickers or security_id in current_ids:
            status = "CURRENT_500_EXCLUDED"
            reason = "current ticker or security_id matches frozen current 500"
        elif row["ticker"] in aliases:
            status = "IDENTITY_DUPLICATE_EXCLUDED"
            reason = "reviewed historical identity interval matches frozen current 500"
        else:
            status = "ELIGIBLE_PRECRAWL"
            reason = "KBS current stock listing; exchange is deterministic pre-crawl priority signal"
        ranking.append({**row, "security_id": security_id, "selection_status": status,
                        "priority_tier": row["exchange"], "index_importance_signal": "UNAVAILABLE",
                        "market_importance_signal": "UNAVAILABLE", "exchange_signal": row["exchange"],
                        "history_signal": "UNAVAILABLE", "identity_signal": "CURRENT_LISTING_ONLY",
                        "known_provider_evidence": "KBS_CURRENT_LISTING",
                        "duplicate_identity_status": ("CURRENT_500_MATCH" if status == "CURRENT_500_EXCLUDED" else
                                                      "REVIEWED_ALIAS_MATCH" if status == "IDENTITY_DUPLICATE_EXCLUDED" else
                                                      "NO_KNOWN_MATCH"),
                        "selection_reason": reason})
    eligible = sorted((r for r in ranking if r["selection_status"] == "ELIGIBLE_PRECRAWL"), key=priority_key)
    if len(eligible) < target:
        raise ValueError(f"only {len(eligible)} eligible candidates for target {target}")
    selected = [dict(row, selection_status="SELECTED_EXPANSION_600") for row in eligible[:target]]
    reserve = [dict(row, selection_status="RESERVE") for row in eligible[target:target + reserve_target]]
    selected_ids = {r["security_id"] for r in selected}
    reserve_ids = {r["security_id"] for r in reserve}
    final_ranking = []
    for row in sorted(ranking, key=lambda r: (0 if r["selection_status"] == "ELIGIBLE_PRECRAWL" else 1, priority_key(r))):
        row = dict(row)
        if row["security_id"] in selected_ids:
            row["selection_status"] = "SELECTED_EXPANSION_600"
        elif row["security_id"] in reserve_ids:
            row["selection_status"] = "RESERVE"
        elif row["selection_status"] == "ELIGIBLE_PRECRAWL":
            row["selection_status"] = "OTHER_EXCLUDED"
        row["priority_rank"] = len(final_ranking) + 1
        final_ranking.append(row)
    for row in excluded:
        row.update(priority_rank=len(final_ranking) + 1, security_id="", priority_tier="EXCLUDED",
                   index_importance_signal="UNAVAILABLE", market_importance_signal="UNAVAILABLE",
                   exchange_signal=row.get("exchange", "UNAVAILABLE"), history_signal="UNAVAILABLE",
                   identity_signal="INSUFFICIENT", known_provider_evidence="KBS_CURRENT_LISTING",
                   duplicate_identity_status=row["selection_status"], selection_reason="listing evidence exclusion")
        final_ranking.append(row)
    estimates = [{"security_id": r["security_id"], "ticker": r["ticker"], "exchange": r["exchange"],
                  "estimated_sessions": 1260, "estimated_pages": estimate_pages(r),
                  "estimated_requests": estimate_pages(r), "estimate_basis": "FULL_BASE_5Y_PLUS_ONE_OVERLAP_PAGE"}
                 for r in selected]
    bins = [{"worker_id": f"worker-{i:02d}", "rows": [], "load": 0} for i in range(1, 6)]
    estimate_by_id = {r["security_id"]: r for r in estimates}
    for row in sorted(selected, key=lambda r: (-estimate_by_id[r["security_id"]]["estimated_requests"], r["ticker"])):
        bucket = min(bins, key=lambda b: (b["load"], b["worker_id"]))
        bucket["rows"].append(row)
        bucket["load"] += estimate_by_id[row["security_id"]]["estimated_requests"]
    return {"ranking": final_ranking, "selected": selected, "reserve": reserve, "estimates": estimates,
            "workers": bins, "excluded_discovery": excluded}


def acquire_page(ticker: str, page_index: int, contract: dict) -> tuple[bytes, int, str]:
    params = {"Symbol": ticker, "PageIndex": page_index, "PageSize": contract["page_size"]}
    url = TRADE_HISTORY_ENDPOINT + "?" + urlencode(params)
    headers = {"User-Agent": "DeltaT1Research/0.2 (academic; non-commercial demo)", "Accept": "application/json"}
    opener = build_opener()
    for attempt in range(contract["attempts"]):
        try:
            with opener.open(Request(url, headers=headers), timeout=contract["timeout_seconds"]) as response:
                body = response.read(contract["max_response_bytes"] + 1)
                if len(body) > contract["max_response_bytes"]:
                    raise ValueError("response too large")
                marker = body[:8192].lower()
                if any(value.encode() in marker for value in ("captcha", "cloudflare", "managed challenge", "access denied")):
                    raise RuntimeError("HARD_STOP_CHALLENGE")
                return body, response.status, url
        except HTTPError as exc:
            if exc.code in HARD_STOP:
                raise RuntimeError(f"HARD_STOP_HTTP_{exc.code}") from None
            if exc.code not in RETRYABLE or attempt + 1 >= contract["attempts"]:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def page_rows(body: bytes) -> list[dict]:
    payload = json.loads(body)
    if not isinstance(payload, dict) or payload.get("Success") is not True or not isinstance(payload.get("Data"), list):
        raise ValueError("invalid CafeF TradeHistoryNew envelope")
    return payload["Data"]


def classify_observation(row: dict) -> str:
    values = [row.get("Volume"), row.get("AgreedVolume")]
    if all(value is None for value in values):
        return "OBSERVED_WITH_NULL_VOLUME_COMPONENTS"
    if all(value == 0 for value in values if value is not None) and any(value is not None for value in values):
        return "OBSERVED_ZERO_VOLUME"
    return "OBSERVED_MARKET_ROW"


def safe_run_directory(root: Path, assignment: dict, run_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", run_id):
        raise ValueError("unsafe run_id")
    base = (root / "data" / "raw" / "cafef_expansion" / assignment["expansion_id"] / assignment["assignment_id"]).resolve()
    result = (base / run_id).resolve()
    if base not in result.parents:
        raise ValueError("unsafe output path")
    return result


def immutable_write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f"immutable collision: {path}")
        return
    path.write_bytes(body)


def verify_existing_raw(run_dir: Path, adapter_version: str) -> None:
    for meta_path in run_dir.glob("raw/*/page-*.metadata.json"):
        meta = read_json(meta_path)
        raw_path = meta_path.with_name(meta_path.name.replace(".metadata.json", ".json"))
        if not raw_path.is_file() or sha256_file(raw_path) != meta.get("sha256"):
            raise ValueError(f"raw checksum mismatch: {raw_path}")
        if meta.get("adapter_version") != adapter_version:
            raise ValueError("adapter version mismatch")


def checksums_for_files(files: dict[str, bytes]) -> bytes:
    return "".join(f"{sha256_bytes(data)}  {name}\n" for name, data in sorted(files.items())).encode("utf-8")


def parse_checksums(body: bytes) -> dict[str, str]:
    result = {}
    for line in body.decode("utf-8").splitlines():
        digest, name = line.split("  ", 1)
        result[name] = digest
    return result


def safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name and not SECRET_NAMES.search(name)


def json_contains_secret_keys(body: bytes) -> bool:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    def visit(item):
        if isinstance(item, dict):
            return any(SECRET_NAMES.search(str(key)) or visit(child) for key, child in item.items())
        if isinstance(item, list):
            return any(visit(child) for child in item)
        return False
    return visit(value)


def validate_handoff_set(assignments: list[dict], index: dict, universe: dict, reserve: set[str]) -> dict[str, str]:
    expected = {row["assignment_id"] for row in index["assignments"]}
    ids = {row["assignment_id"] for row in assignments}
    if len(assignments) != 5 or ids != expected:
        raise ValueError("missing or unexpected shard")
    owners = {}
    for assignment in assignments:
        for ticker in assignment["tickers"]:
            if ticker in owners:
                raise ValueError(f"cross-shard overlap: {ticker}")
            if ticker in reserve:
                raise ValueError(f"reserve ticker assigned: {ticker}")
            owners[ticker] = assignment["assignment_id"]
    frozen = {row["ticker"] for row in universe["securities"]}
    if set(owners) != frozen:
        raise ValueError("handoff union differs from frozen universe")
    return owners
