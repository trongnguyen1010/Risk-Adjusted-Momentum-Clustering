"""Evidence-preserving acquisition and parsing of public CafeF detail tables."""
import json
import re
import time
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from uuid import uuid4

from .cafef_financial import digest, encoded, immutable_write, now
from .sources.base import AccessControlError, NoRedirect, RateLimitError, SemanticValidationError

VERSION = "cafef-financial-detail-v1"
STATEMENTS = {"bsheet": "balance_sheet", "incsta": "income_statement", "cashflow": "cash_flow_statement"}


class PublicEvidenceClient:
    """Finite low-rate transport; no credentials, redirects or boundary retries."""
    def __init__(self, interval=2, opener=None, sleep=time.sleep, clock=time.monotonic,
                 approved_hosts=None, max_bytes=20_000_000):
        self.approved_hosts = frozenset(approved_hosts if approved_hosts is not None else {"cafef.vn", "cafefnew.mediacdn.vn"})
        if not self.approved_hosts or type(max_bytes) is not int or not 1 <= max_bytes <= 50_000_000:
            raise ValueError("invalid public transport bounds")
        self.max_bytes = max_bytes
        self.interval, self.sleep, self.clock = interval, sleep, clock
        self.opener = opener or build_opener(NoRedirect())
        self.last = 0

    def get(self, url):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.hostname not in self.approved_hosts):
            raise ValueError("unapproved public evidence host")
        for attempt in range(2):
            self.sleep(max(0, self.interval - (self.clock() - self.last)))
            self.last = self.clock()
            try:
                with self.opener.open(Request(url, headers={"User-Agent": "DeltaT1Research/0.2 (academic; non-commercial demo)"}), timeout=20) as response:
                    body = response.read(self.max_bytes + 1)
                    if len(body) > self.max_bytes:
                        raise SemanticValidationError("response size cap exceeded")
                    marker = body[:4096].lower()
                    if any(m in marker for m in (b"captcha", b"managed challenge", b"login wall", b"cloudflare")):
                        raise AccessControlError("challenge boundary")
                    return body, response.status
            except HTTPError as exc:
                if exc.code in (401, 403):
                    raise AccessControlError(f"HTTP {exc.code}") from None
                if exc.code == 429:
                    raise RateLimitError("HTTP 429; defer run") from None
                if exc.code not in (500, 502, 503, 504):
                    raise ValueError(f"HTTP {exc.code}; no redirect/workaround") from None
            except (URLError, TimeoutError, ConnectionError):
                pass
            if attempt == 0:
                self.sleep(2)
        raise ValueError("bounded transport attempts exhausted")


class DetailTableParser(HTMLParser):
    """Read only top-level table cells; exclude nested chart cells/scripts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth, self.target_depth, self.target = 0, None, None
        self.row, self.cell, self.cells, self.rows, self.headers = None, None, [], [], []
        self.units, self.unit_buffer, self.identity = [], None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("id", "").endswith("txtKeyword"):
            self.identity = a.get("value", "").upper()
        if tag == "div" and "dltlonote" in a.get("class", "").split():
            self.unit_buffer = []
        if tag == "table":
            self.depth += 1
            if a.get("id") in {"tblGridData", "tableContent"}:
                if self.target is not None:
                    raise SemanticValidationError("nested target table")
                self.target, self.target_depth = a["id"], self.depth
        if self.target and self.depth == self.target_depth:
            if tag == "tr":
                self.row = {"provider_item_code": a.get("id"), "provider_row_class": a.get("class", "")}
                self.cells = []
            elif tag in {"td", "th"}:
                self.cell = {"class": a.get("class", ""), "text": []}

    def handle_data(self, data):
        if self.unit_buffer is not None:
            self.unit_buffer.append(data)
        if self.cell is not None and self.depth == self.target_depth:
            self.cell["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "div" and self.unit_buffer is not None:
            self.units.append(" ".join("".join(self.unit_buffer).split()))
            self.unit_buffer = None
        if self.target and self.depth == self.target_depth:
            if tag in {"td", "th"} and self.cell is not None:
                self.cell["text"] = " ".join("".join(self.cell["text"]).split())
                self.cells.append(self.cell)
                self.cell = None
            elif tag == "tr" and self.row is not None:
                if self.target == "tblGridData":
                    self.headers.extend(c["text"] for c in self.cells if "h_t" in c["class"].split())
                else:
                    self.rows.append({**self.row, "cells": self.cells})
                self.row = None
            elif tag == "table":
                self.target, self.target_depth = None, None
        if tag == "table":
            self.depth -= 1


def number_candidate(text):
    if text in {"", "-", "--"}:
        return None
    # Vietnamese display grouping/decimal convention; preserve original text.
    if not re.fullmatch(r"-?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?", text):
        raise SemanticValidationError("unknown numeric display: " + text)
    v = Decimal(text.replace(".", "").replace(",", "."))
    return int(v) if v == v.to_integral_value() else str(v)


def parse_detail(body, symbol, statement, year, quarter):
    parser = DetailTableParser()
    parser.feed(body.decode("utf-8-sig"))
    if parser.identity != symbol:
        raise SemanticValidationError("detail symbol identity mismatch")
    if len(parser.headers) != 4 or not parser.rows:
        raise SemanticValidationError("detail header/body contract missing")
    periods = []
    for label in parser.headers:
        annual = re.fullmatch(r"(\d{4})", label)
        quarterly = re.fullmatch(r"Quý\s*([1-4])\s*-\s*(\d{4})", label)
        if annual and quarter == 0:
            periods.append((int(annual[1]), 0))
        elif quarterly and quarter != 0:
            periods.append((int(quarterly[2]), int(quarterly[1])))
        else:
            raise SemanticValidationError("detail period label mismatch")
    if periods != sorted(set(periods)) or periods[-1] != (year, quarter):
        raise SemanticValidationError("detail response did not honor requested anchor")
    facts = []
    for ordinal, row in enumerate(parser.rows):
        cells = row["cells"]
        if len(cells) != 6:
            raise SemanticValidationError("unexpected detail row width")
        for (y, q), cell in zip(periods, cells[1:5]):
            text = cell["text"]
            facts.append({"symbol": symbol, "statement_type": STATEMENTS[statement],
                          "provider_statement": statement, "provider_item_code": row["provider_item_code"],
                          "provider_row_class": row["provider_row_class"], "row_ordinal": ordinal,
                          "item_name": cells[0]["text"], "year": y, "quarter": q,
                          "raw_value_text": text, "display_number_candidate": number_candidate(text),
                          "unit_scale": None, "unit_status": "UNVERIFIED_DETAIL_DISPLAY",
                          "period_semantics": "INSTANT_CANDIDATE" if statement == "bsheet" else "DURATION_UNVERIFIED",
                          "published_at": None, "available_at": None,
                          "pit_status": "PIT_UNRESOLVED", "financial_features_allowed": False})
    return {"symbol": symbol, "statement": statement, "periods": [list(p) for p in periods],
            "display_unit_labels": parser.units, "facts": facts}


def validate_config(c):
    if c.get("contract_version") != VERSION or c.get("financial_features_allowed") is not False or c.get("pit_status") != "PIT_UNRESOLVED":
        raise ValueError("detail must remain raw-only")
    symbols = c.get("symbols")
    types = c.get("statement_types")
    if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 10
            or any(not isinstance(s, str) or not re.fullmatch(r"[A-Z0-9]{1,10}", s) for s in symbols)
            or len(set(symbols)) != len(symbols) or not isinstance(types, list)
            or not types or len(set(types)) != len(types) or not set(types) <= set(STATEMENTS)):
        raise ValueError("invalid detail symbol/type scope")
    if (type(c.get("start_year")) is not int or type(c.get("end_year")) is not int
            or not 1900 <= c["start_year"] <= c["end_year"] <= 2100
            or c["end_year"] - c["start_year"] > 9
            or type(c.get("max_requests")) is not int or not 1 <= c["max_requests"] <= 200
            or type(c.get("min_interval_seconds")) not in (int, float)
            or not 2 <= c["min_interval_seconds"] <= 30):
        raise ValueError("invalid detail bounds")
    return c


def detail_jobs(c):
    jobs = []
    for symbol in c["symbols"]:
        for statement in c["statement_types"]:
            # Annual HTML shows four years; use disjoint anchors.
            for year in range(c["end_year"], c["start_year"] - 1, -4):
                jobs.append((symbol, statement, year, 0))
            for year in range(c["start_year"], c["end_year"] + 1):
                jobs.append((symbol, statement, year, 4))
        # Explicitly recover original summary gap without replacing old evidence.
        if symbol in {"FPT", "VNM"} and c["start_year"] <= 2024 <= c["end_year"]:
            for statement in c["statement_types"]:
                if statement in {"bsheet", "incsta"}:
                    jobs.append((symbol, statement, 2024, 2))
    return jobs


def detail_url(symbol, statement, year, quarter):
    return f"https://cafef.vn/du-lieu/bao-cao-tai-chinh/{symbol.lower()}/{statement}/{year}/{quarter}/0/1/bao-cao-tai-chinh-.chn"


def summarize(c, pages, errors):
    facts = [f for p in pages for f in p["facts"] if c["start_year"] <= f["year"] <= c["end_year"]]
    streams = []
    for symbol in c["symbols"]:
        for statement in c["statement_types"]:
            for mode in ("NAM", "QUY"):
                expected = {(y, q) for y in range(c["start_year"], c["end_year"] + 1)
                            for q in ((0,) if mode == "NAM" else (1, 2, 3, 4))}
                selected = [f for f in facts if f["symbol"] == symbol and f["provider_statement"] == statement
                            and (f["quarter"] == 0) == (mode == "NAM")]
                observed = {(f["year"], f["quarter"]) for f in selected if f["display_number_candidate"] is not None}
                streams.append({"symbol": symbol, "statement": statement, "mode": mode,
                                "observed_periods_with_values": len(observed), "expected_periods": len(expected),
                                "missing_periods": [list(k) for k in sorted(expected - observed)],
                                "coverage_complete": expected <= observed})
    # Multiple anchors may expose different versions: retain all, never prefer a source/page.
    by_key = {}
    for fact in facts:
        key = (fact["symbol"], fact["provider_statement"], fact["year"], fact["quarter"], fact["provider_item_code"], fact["item_name"])
        by_key.setdefault(key, set()).add(fact["raw_value_text"])
    conflicts = [{"key": list(k), "raw_values": sorted(v)} for k, v in sorted(by_key.items(), key=lambda x: str(x[0])) if len(v) > 1]
    return {"contract_version": VERSION, "coverage_status": "PASS" if all(s["coverage_complete"] for s in streams) else "PARTIAL",
            "pages_parsed": len(pages), "fact_observations_in_target": len(facts), "streams": streams,
            "errors": errors, "cross_page_value_conflicts": conflicts,
            "unit_status": "UNVERIFIED_DETAIL_DISPLAY", "financial_pit_gate": "NOT_READY",
            "financial_features_allowed": False}


def collect(c, output_root, client=None):
    validate_config(c)
    client = client or PublicEvidenceClient(c["min_interval_seconds"])
    run = Path(output_root) / ("run-" + now().replace(":", "").replace("+", "-") + "-" + uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    immutable_write(run / "config.json", encoded(c))
    immutable_write(run / "collector.py", Path(__file__).read_bytes())
    pages, errors, calls, stopped = [], [], 0, False
    for symbol, statement, year, quarter in detail_jobs(c):
        if stopped or calls >= c["max_requests"]:
            errors.append({"job": [symbol, statement, year, quarter], "error": "NOT_REQUESTED_HARD_STOP" if stopped else "REQUEST_CAP"})
            continue
        url = detail_url(symbol, statement, year, quarter)
        prefix = run / "raw" / symbol / statement / f"{year}-q{quarter}"
        calls += 1
        try:
            body, status = client.get(url)
            immutable_write(prefix.with_suffix(".html"), body)
            immutable_write(prefix.with_suffix(".metadata.json"), encoded({"url": url, "fetched_at": now(),
                            "sha256": digest(body), "http_status": status, "symbol": symbol,
                            "statement": statement, "year": year, "quarter": quarter,
                            "rights_status": "RIGHTS_NOT_VERIFIED", "execution_policy": "ACCEPTED_RESEARCH_RISK"}))
            parsed = parse_detail(body, symbol, statement, year, quarter)
            for fact in parsed["facts"]:
                fact.update(raw_path=prefix.with_suffix(".html").relative_to(run).as_posix(), raw_sha256=digest(body))
            pages.append(parsed)
            immutable_write(prefix.with_suffix(".parsed.json"), encoded(parsed))
        except (AccessControlError, RateLimitError) as exc:
            stopped = True
            errors.append({"job": [symbol, statement, year, quarter], "error": str(exc), "hard_stop": True})
        except (ValueError, OSError) as exc:
            errors.append({"job": [symbol, statement, year, quarter], "error": str(exc)})
    # Document list metadata is raw evidence, not financial availability.
    for symbol in c["symbols"]:
        for year in range(c["start_year"], c["end_year"] + 1):
            if stopped or calls >= c["max_requests"]:
                errors.append({"document_job": [symbol, year], "error": "NOT_REQUESTED"})
                continue
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={symbol.lower()}&Type=1&Year={year}"
            calls += 1
            try:
                body, status = client.get(url)
                prefix = run / "documents" / symbol / str(year)
                immutable_write(prefix.with_suffix(".json"), body)
                immutable_write(prefix.with_suffix(".metadata.json"), encoded({"url": url, "fetched_at": now(), "sha256": digest(body), "http_status": status}))
                json.loads(body)
            except (AccessControlError, RateLimitError) as exc:
                stopped = True
                errors.append({"document_job": [symbol, year], "error": str(exc), "hard_stop": True})
            except (ValueError, OSError) as exc:
                errors.append({"document_job": [symbol, year], "error": str(exc)})
    result = summarize(c, pages, errors)
    result.update(logical_requests=calls, execution_status="HARD_STOP" if stopped else ("PARTIAL" if errors else "COMPLETE"))
    immutable_write(run / "coverage.json", encoded(result))
    immutable_write(run / "manifest.json", encoded({"version": VERSION, "files": {
        p.relative_to(run).as_posix(): digest(p.read_bytes()) for p in sorted(run.rglob("*")) if p.is_file()}}))
    return run, result


def verify(run):
    run = Path(run).resolve()
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    actual = {p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file() and p != run / "manifest.json"}
    if manifest.get("version") != VERSION or actual != set(manifest["files"]):
        raise ValueError("detail manifest inventory/version mismatch")
    for name, sha in manifest["files"].items():
        path = (run / name).resolve()
        if not path.is_relative_to(run) or digest(path.read_bytes()) != sha:
            raise ValueError("detail manifest path/hash mismatch")
    c = validate_config(json.loads((run / "config.json").read_text(encoding="utf-8")))
    pages = []
    for path in sorted((run / "raw").rglob("*.metadata.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        body = path.with_name(path.name.replace(".metadata.json", ".html")).read_bytes()
        if digest(body) != meta["sha256"]:
            raise ValueError("detail raw hash mismatch")
        parsed_path = path.with_name(path.name.replace(".metadata.json", ".parsed.json"))
        if not parsed_path.exists():
            continue  # Failed parse preserved in coverage errors.
        parsed = parse_detail(body, meta["symbol"], meta["statement"], meta["year"], meta["quarter"])
        for fact in parsed["facts"]:
            fact.update(raw_path=path.with_name(path.name.replace(".metadata.json", ".html")).relative_to(run).as_posix(), raw_sha256=digest(body))
        if parsed != json.loads(parsed_path.read_text(encoding="utf-8")):
            raise ValueError("detail parse replay mismatch")
        pages.append(parsed)
    saved = json.loads((run / "coverage.json").read_text(encoding="utf-8"))
    replay = summarize(c, pages, saved["errors"])
    if encoded(replay) != encoded({k: v for k, v in saved.items() if k not in {"logical_requests", "execution_status"}}):
        raise ValueError("detail coverage replay mismatch")
    return saved


def acquire_gap_documents(detail_run, output_root, client=None):
    """Download a bounded document inspection sample for actual table gaps."""
    result = verify(detail_run)
    source = Path(detail_run).resolve()
    gaps = sorted({(s["symbol"], y, q) for s in result["streams"] for y, q in s["missing_periods"]})
    if len(gaps) > 20:
        raise ValueError("too many document gaps for bounded pilot")
    client = client or PublicEvidenceClient()
    output = Path(output_root) / ("run-" + now().replace(":", "").replace("+", "-") + "-" + uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    inventory, stopped = [], False
    for symbol, year, quarter in gaps:
        document_list = source / "documents" / symbol / f"{year}.json"
        rows = json.loads(document_list.read_bytes())
        if not isinstance(rows, dict) or rows.get("Success") is not True or not isinstance(rows.get("Data"), list):
            raise SemanticValidationError("invalid FileBCTC document envelope")
        candidates = [r for r in rows["Data"] if r.get("Quarter") == (5 if quarter == 0 else quarter)
                      and r.get("Year") == year and "hợp nhất" in r.get("Name", "").casefold()]
        # Inspection selection only: retain all alternative identities in inventory.
        candidates.sort(key=lambda r: ("soát xét" in r.get("Name", "").casefold(), r.get("id", "")))
        item = {"symbol": symbol, "year": year, "quarter": quarter,
                "source_list_path": str(document_list), "source_list_sha256": digest(document_list.read_bytes()),
                "candidates": candidates, "selection_rule": "FIRST_INITIAL_DOCUMENT_FOR_INSPECTION_ONLY",
                "published_at": None, "available_at": None, "financial_features_allowed": False}
        if not candidates or stopped:
            item["status"] = "NO_CONSOLIDATED_DOCUMENT" if not candidates else "NOT_REQUESTED_HARD_STOP"
            inventory.append(item)
            continue
        selected = candidates[0]
        try:
            body, status = client.get(selected["Link"])
            if not body.startswith(b"%PDF"):
                raise SemanticValidationError("document is not PDF")
            name = f"{symbol}-{year}-q{quarter}.pdf"
            immutable_write(output / name, body)
            item.update(status="DOWNLOADED", selected=selected, path=name, sha256=digest(body),
                        http_status=status, fetched_at=now())
        except (AccessControlError, RateLimitError) as exc:
            stopped = True
            item.update(status="HARD_STOP", error=str(exc))
        except (ValueError, OSError) as exc:
            item.update(status="FAILED", error=str(exc))
        inventory.append(item)
    immutable_write(output / "inventory.json", encoded({"detail_run": str(source), "gaps": inventory}))
    immutable_write(output / "collector.py", Path(__file__).read_bytes())
    immutable_write(output / "manifest.json", encoded({"files": {
        p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}))
    return output, inventory
