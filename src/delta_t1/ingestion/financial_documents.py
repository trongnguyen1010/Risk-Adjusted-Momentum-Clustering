"""Bounded consolidated document vintages. No publication-time inference."""
import json
import re
from pathlib import Path
from uuid import uuid4

from .cafef_financial import digest, encoded, immutable_write, now
from .cafef_financial_detail import PublicEvidenceClient, verify as verify_detail
from .sources.base import AccessControlError, RateLimitError, SemanticValidationError

VERSION = "financial-document-vintages-v1"


def verify_inventory(run):
    run = Path(run).resolve()
    manifest = json.loads((run / "manifest.json").read_bytes())
    actual = {p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file() and p != run / "manifest.json"}
    if actual != set(manifest["files"]):
        raise ValueError("document inventory mismatch")
    for name, sha in manifest["files"].items():
        path = (run / name).resolve()
        if not path.is_relative_to(run) or digest(path.read_bytes()) != sha:
            raise ValueError("document hash/path mismatch")
    inventory_path = run / "inventory.json"
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_bytes())
        for record in inventory.get("documents", inventory.get("requests", inventory.get("gaps", []))):
            if record.get("status") in {"DOWNLOADED", "REUSED_VERIFIED_RAW"}:
                path = Path(record["path"])
                path = path if path.is_absolute() else run / path
                if digest(path.read_bytes()) != record["sha256"]:
                    raise ValueError("referenced document hash mismatch")
            if record.get("source_list_path"):
                if digest(Path(record["source_list_path"]).read_bytes()) != record["source_list_sha256"]:
                    raise ValueError("referenced document list hash mismatch")
    return manifest


def consolidated_rows(body, year):
    payload = json.loads(body)
    if not isinstance(payload, dict) or payload.get("Success") is not True or not isinstance(payload.get("Data"), list):
        raise SemanticValidationError("invalid document envelope")
    rows = []
    seen = set()
    for row in payload["Data"]:
        if row.get("Year") != year or "hợp nhất" not in row.get("Name", "").casefold():
            continue
        if (row.get("Quarter") not in {1, 2, 3, 4, 5} or
                not isinstance(row.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]+", row["id"])):
            raise SemanticValidationError("invalid report identity/period")
        if row["id"] in seen:
            raise SemanticValidationError("duplicate report identity")
        seen.add(row["id"])
        rows.append(row)
    return sorted(rows, key=lambda r: (r["Quarter"], r["id"]))


def collect_vintages(detail_run, gap_run, output_root, start_year=2019, end_year=2025, max_downloads=80, client=None):
    coverage = verify_detail(detail_run)
    verify_inventory(gap_run)
    detail, gap = Path(detail_run).resolve(), Path(gap_run).resolve()
    config = json.loads((detail / "config.json").read_bytes())
    if not 1900 <= start_year <= end_year <= 2100 or end_year - start_year > 9 or not 1 <= max_downloads <= 80:
        raise ValueError("invalid bounded document plan")
    symbols = config["symbols"]
    gaps = {(s["symbol"], y, q) for s in coverage["streams"] for y, q in s["missing_periods"]}
    cache = {r["selected"]["Link"]: (gap / r["path"], r["sha256"])
             for r in json.loads((gap / "inventory.json").read_bytes())["gaps"] if r["status"] == "DOWNLOADED"}
    client = client or PublicEvidenceClient()
    run = Path(output_root) / ("run-" + now().replace(":", "").replace("+", "-") + "-" + uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    immutable_write(run / "config.json", encoded({"version": VERSION, "symbols": symbols, "start_year": start_year,
                    "end_year": end_year, "max_downloads": max_downloads, "scope": "ANNUAL_ALL_VINTAGES_AND_QUARTERLY_GAPS",
                    "financial_features_allowed": False, "pit_status": "NOT_READY"}))
    inventory, lists, stopped, calls, downloads = [], [], False, 0, 0
    for symbol in symbols:
        for year in range(start_year, end_year + 1):
            if stopped:
                lists.append({"symbol": symbol, "year": year, "status": "NOT_REQUESTED_HARD_STOP"})
                continue
            existing = detail / "documents" / symbol / f"{year}.json"
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={symbol.lower()}&Type=1&Year={year}"
            try:
                if existing.exists():
                    body = existing.read_bytes()
                    list_path = existing
                else:
                    calls += 1
                    body, status = client.get(url)
                    list_path = run / "lists" / symbol / f"{year}.json"
                    immutable_write(list_path, body)
                    immutable_write(list_path.with_suffix(".metadata.json"), encoded({"url": url, "http_status": status,
                                    "fetched_at": now(), "sha256": digest(body)}))
                rows = consolidated_rows(body, year)
                lists.append({"symbol": symbol, "year": year, "status": "PARSED", "path": str(list_path), "sha256": digest(body)})
            except (AccessControlError, RateLimitError) as exc:
                stopped = True
                lists.append({"symbol": symbol, "year": year, "status": "HARD_STOP", "error": str(exc)})
                continue
            except (ValueError, OSError) as exc:
                lists.append({"symbol": symbol, "year": year, "status": "FAILED", "error": str(exc)})
                continue
            for row in rows:
                quarter = 0 if row["Quarter"] == 5 else row["Quarter"]
                if quarter != 0 and (symbol, year, quarter) not in gaps:
                    continue
                item = {"symbol": symbol, "year": year, "quarter": quarter, "provider_report": row,
                        "source_list_path": str(list_path), "source_list_sha256": digest(body),
                        "published_at": None, "available_at": None, "scope_status": "PROVIDER_LABEL_CONSOLIDATED",
                        "period_semantics": "UNVERIFIED_PDF", "financial_features_allowed": False}
                if row["Link"] in cache:
                    path, sha = cache[row["Link"]]
                    item.update(status="REUSED_VERIFIED_RAW", path=str(path), sha256=sha)
                elif stopped or downloads >= max_downloads:
                    item["status"] = "NOT_REQUESTED_HARD_STOP" if stopped else "NOT_REQUESTED_CAP"
                else:
                    downloads += 1
                    calls += 1
                    try:
                        pdf, status = client.get(row["Link"])
                        if not pdf.startswith(b"%PDF"):
                            raise SemanticValidationError("not a PDF document")
                        path = run / "pdf" / f"{symbol}-{year}-q{quarter}-{row['id']}.pdf"
                        immutable_write(path, pdf)
                        item.update(status="DOWNLOADED", path=str(path.resolve()), sha256=digest(pdf),
                                    http_status=status, fetched_at=now())
                    except (AccessControlError, RateLimitError) as exc:
                        stopped = True
                        item.update(status="HARD_STOP", error=str(exc))
                    except (ValueError, OSError) as exc:
                        item.update(status="FAILED", error=str(exc))
                inventory.append(item)
    result = {"version": VERSION, "detail_run": str(detail), "gap_run": str(gap), "lists": lists,
              "documents": inventory, "logical_requests": calls, "download_attempts": downloads,
              "execution_status": "HARD_STOP" if stopped else ("PARTIAL" if any(r["status"] not in {"DOWNLOADED", "REUSED_VERIFIED_RAW"} for r in inventory) or any(r["status"] != "PARSED" for r in lists) else "COMPLETE"),
              "financial_pit_gate": "NOT_READY", "financial_features_allowed": False}
    immutable_write(run / "inventory.json", encoded(result))
    immutable_write(run / "collector.py", Path(__file__).read_bytes())
    immutable_write(run / "manifest.json", encoded({"files": {p.relative_to(run).as_posix(): digest(p.read_bytes())
                    for p in sorted(run.rglob("*")) if p.is_file()}}))
    return run, result
