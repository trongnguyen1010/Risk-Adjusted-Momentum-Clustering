"""Bounded public VSDC/HNX adapters and conservative HTML extraction."""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, build_opener

from .sources.base import NoRedirect


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SourceLimitation(ValueError):
    pass


class Node:
    def __init__(self, tag="root", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def find(self, tag=None, cls=None, id=None):
        found = []
        for child in self.children:
            if isinstance(child, Node):
                if ((tag is None or child.tag == tag) and
                        (cls is None or cls in child.attrs.get("class", "").split()) and
                        (id is None or child.attrs.get("id") == id)):
                    found.append(child)
                found.extend(child.find(tag, cls, id))
        return found

    def text(self):
        if self.tag in {"script", "style", "noscript"}:
            return ""
        parts = [child.text() if isinstance(child, Node) else child for child in self.children]
        return " ".join(" ".join(parts).split())


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "source", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class PublicTransport:
    """No auth, cookies or retries at access boundaries; preserve every response."""
    HOSTS = {"vsdc.vn", "www.hnx.vn", "api.hsx.vn", "staticfile.hsx.vn"}

    def access_challenge(self, text, url):
        """Conservative default; source-specific diagnostics may override narrowly."""
        return bool(re.search(r"captcha|verify you are human|access denied|cloudflare challenge|cf-chl-", text, re.I))

    def __init__(self, root, max_requests=30, interval=2, timeout=15, max_bytes=2_000_000,
                 opener=None, sleep=time.sleep):
        if not 1 <= max_requests <= 1000 or not 1 <= timeout <= 30 or interval < 2 or not 1 <= max_bytes <= 5_000_000:
            raise ValueError("invalid bounded HTTP limits")
        self.root, self.max_requests, self.interval = root, max_requests, interval
        self.timeout, self.max_bytes = timeout, max_bytes
        self.opener, self.sleep = opener or build_opener(NoRedirect()), sleep
        self.requests, self.last = [], 0.0
        self.stopped_hosts = set()

    def fetch(self, url, payload=None, content_type="application/json", binary=False):
        host = urlsplit(url).hostname
        if urlsplit(url).scheme != "https" or host not in self.HOSTS or urlsplit(url).username:
            raise SourceLimitation("SOURCE_ACCESS_LIMITATION: URL outside approved public adapters")
        if host in self.stopped_hosts:
            raise SourceLimitation("SOURCE_ACCESS_LIMITATION: host stopped after access/rate-limit boundary")
        if len(self.requests) >= self.max_requests:
            raise SourceLimitation("REQUEST_BUDGET_EXHAUSTED")
        self.sleep(max(0, self.interval - (time.monotonic()-self.last)))
        self.last = time.monotonic()
        entry = {"url": url, "method": "POST" if payload is not None else "GET",
                 "request_body": payload.decode() if payload else None, "fetched_at": now()}
        self.requests.append(entry)
        try:
            response = self.opener.open(Request(url, data=payload, headers={
                "User-Agent": "DeltaT1Research/0.2 (bounded corporate-action research)",
                "Accept": "text/html", "Content-Type": content_type}), timeout=self.timeout)
        except HTTPError as exc:
            response = exc
        except (URLError, TimeoutError, ConnectionError, OSError) as exc:
            entry["error"] = str(exc)
            raise SourceLimitation("SOURCE_ACCESS_LIMITATION: " + str(exc)) from exc
        with response:
            status = response.code
            entry.update(status=status, content_type=response.headers.get("Content-Type", ""),
                         response_headers={k: response.headers.get(k) for k in ("Location", "Retry-After")})
            body = response.read(self.max_bytes + 1)
        path = self.root / "raw" / f"response-{len(self.requests):04}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(body)
        entry.update(path=path.relative_to(self.root).as_posix(), source_hash=sha(body))
        if len(body) > self.max_bytes:
            entry["error"] = "RESPONSE_SIZE_LIMIT"
            raise SourceLimitation("RESPONSE_SIZE_LIMIT")
        text = body.decode("utf-8-sig", errors="replace")
        challenge = self.access_challenge(text, url)
        if status in {401, 403, 429} or challenge:
            self.stopped_hosts.add(host)
            entry["error"] = "SOURCE_ACCESS_LIMITATION"
            raise SourceLimitation(f"SOURCE_ACCESS_LIMITATION: HTTP {status}/challenge; no retry")
        if status != 200:
            entry["error"] = f"HTTP_{status}"
            raise SourceLimitation(f"SOURCE_ACCESS_LIMITATION: HTTP {status}; redirect/login not followed")
        if binary:
            if not body.startswith(b"%PDF-"):
                raise SourceLimitation("UNSUPPORTED_DOCUMENT_FORMAT")
            return body, entry
        if not any(t in entry["content_type"].lower() for t in ("html", "json", "xml")) and not re.search(r"<(?:div|table|html)\b", text, re.I):
            raise SourceLimitation("UNSUPPORTED_CONTENT_TYPE")
        return text, entry


def vn_date(value):
    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", value)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def kinds(text):
    text = text.lower()
    result = []
    for kind, pattern in (
        ("CASH_DIVIDEND", r"cổ tức.{0,80}(?:bằng tiền|tiền mặt)"),
        ("STOCK_DIVIDEND", r"cổ tức.{0,80}bằng (?:cổ phiếu|cp\b)|phát hành cổ phiếu để trả cổ tức"),
        ("BONUS_SHARE", r"(?:cổ phiếu|cp\b) thưởng|thưởng.{0,30}(?:cổ phiếu|cp\b)|tăng vốn.{0,50}nguồn vốn chủ sở hữu"),
        ("REVERSE_SPLIT", r"gộp cổ phiếu|gộp cổ phần"),
        ("STOCK_SPLIT", r"tách cổ phiếu|chia tách cổ phiếu"),
        ("RIGHTS_ISSUE", r"quyền mua|chào bán.{0,70}cổ đông hiện hữu"),
    ):
        if re.search(pattern, text):
            result.append(kind)
    return result


def vi_number(value):
    """Explicit vi-VN display format; never guess a missing scale or repair digits."""
    value = value.strip()
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", value):
        return value.replace(".", "").replace(",", ".")
    if re.fullmatch(r"\d+(?:,\d+)?", value):
        return value.replace(",", ".")
    raise ValueError("RATIO_PARSE_AMBIGUITY")


def terms(kind, fragment, raw_values=None):
    values, problems = {}, []
    raw_values = raw_values if raw_values is not None else {}
    if kind == "CASH_DIVIDEND":
        matches = re.findall(r"(?:cổ phiếu (?:được )?nhận|cổ tức(?: bằng tiền)?\s*[:=])\s*([\d.,]+)\s*đồng", fragment, re.I)
        if len(set(matches)) == 1:
            values.update(cash_dividend_per_share=vi_number(matches[0]), currency="VND")
            raw_values["cash_dividend_per_share"] = matches[0]
    elif kind in {"STOCK_DIVIDEND", "BONUS_SHARE", "RIGHTS_ISSUE"}:
        field = {"STOCK_DIVIDEND": "stock_dividend_ratio", "BONUS_SHARE": "bonus_ratio", "RIGHTS_ISSUE": "rights_ratio"}[kind]
        ratios = re.findall(r"tỷ lệ (?:thực hiện|phát hành|cổ tức|thưởng|quyền mua)\s*[:=]\s*([\d.,]+)\s*%(?![%\d.,])", fragment, re.I)
        colon = re.findall(r"tỷ lệ (?:thực hiện|phát hành|quyền mua)\s*[:=]\s*(\d+(?:,\d+)?)\s*:\s*(\d+(?:,\d+)?)", fragment, re.I)
        if len(set(ratios)) == 1 and not colon:
            values[field] = vi_number(ratios[0]) + "%"
            raw_values[field] = ratios[0] + "%"
        elif len(set(colon)) == 1 and not ratios:
            old, new = colon[0]
            meaning = re.search(r"(?:sở hữu|có)\s*0*" + re.escape(old) + r"\s*cổ phiếu.{0,100}(?:nhận|mua)\s*0*" + re.escape(new) + r"\s*cổ phiếu", fragment, re.I)
            if not meaning and kind == "RIGHTS_ISSUE":
                # Both links must be explicit: one existing share gives one right,
                # and OLD rights buy NEW shares. Never assume the allocation leg.
                allocation = re.search(r"0*1\s*cổ phiếu\s*(?:được\s*)?hưởng\s*0*1\s*quyền", fragment, re.I)
                execution = {(int(a), int(b)) for a,b in re.findall(r"(\d+)\s*quyền\s*được\s*mua\s*(\d+)\s*cổ phiếu",fragment,re.I)}
                if allocation and old.isdigit() and new.isdigit() and execution == {(int(old),int(new))}:
                    meaning = True
            if meaning:
                values.update({field: vi_number(old) + ":" + vi_number(new), "ratio_semantics": "OLD:NEW"})
                raw_values[field] = old + ":" + new
            else:
                problems.append("RATIO_PARSE_AMBIGUITY")
        elif ratios or colon:
            problems.append("RATIO_PARSE_AMBIGUITY")
        if kind == "RIGHTS_ISSUE":
            prices = re.findall(r"giá (?:phát hành|chào bán|đăng ký mua)\s*[:=]\s*([\d.,]+)\s*đồng", fragment, re.I)
            if len(set(prices)) == 1:
                values.update(rights_subscription_price=vi_number(prices[0]), currency="VND")
                raw_values["rights_subscription_price"] = prices[0]
    elif kind in {"STOCK_SPLIT", "REVERSE_SPLIT"}:
        matches = re.findall(r"hệ số (?:tách|gộp|chuyển đổi)\s*[:=]\s*([\d,]+)", fragment, re.I)
        if len(set(matches)) == 1:
            values["split_multiplier"] = vi_number(matches[0])
            raw_values["split_multiplier"] = matches[0]
    return values, problems


def component_sections(raw):
    """Only explicit letter/number headings establish mixed-component boundaries."""
    markers = list(re.finditer(r"(?<!\S)(?:[a-z]|\d{1,2})[.)]\s+(?=(?:trả|chi trả|phát hành|thực hiện|chào bán|tách|gộp|tăng vốn)\b)",raw,re.I))
    sections = {}
    for index, marker in enumerate(markers):
        block = raw[marker.end():markers[index+1].start() if index+1<len(markers) else len(raw)]
        heading = re.split(r":|\s+-\s+|tỷ lệ",block,maxsplit=1,flags=re.I)[0]
        detected = kinds(heading)
        if len(detected)==1:
            sections.setdefault(detected[0],[]).append(block)
    return {kind:blocks[0] for kind,blocks in sections.items() if len(blocks)==1}


def parse_vsdc_time(raw_text: str | None = "", explicit_nodes: list = (), url: str = "",
                    raw_path: str | None = None, source_hash: str | None = None) -> dict:
    """Extract and validate granular timing metadata from VSDC raw strings and tags."""
    raw_str = (raw_text or "").strip()
    tag_stamps = []
    has_pub_attr = False
    has_upd_attr = False

    for n in explicit_nodes:
        if isinstance(n, str):
            val = n.strip()
            if val:
                tag_stamps.append(val)
        elif hasattr(n, "attrs"):
            dt_attr = n.attrs.get("datetime", "").strip()
            if dt_attr:
                tag_stamps.append(dt_attr)
            pub_val = str(n.attrs.get("pubdate", "")).lower()
            cls_val = str(n.attrs.get("class", "")).lower()
            prop_val = str(n.attrs.get("itemprop", "")).lower()
            if pub_val in {"true", "pubdate"} or "publish" in cls_val or "datepublished" in prop_val:
                has_pub_attr = True
            if "update" in cls_val or "datemodified" in prop_val:
                has_upd_attr = True

    unique_stamps = sorted(set(tag_stamps))
    if len(unique_stamps) > 1:
        return {
            "raw_text": raw_str or ("; ".join(unique_stamps)),
            "parsed_date": None,
            "parsed_time": None,
            "parsed_datetime": None,
            "precision": "AMBIGUOUS",
            "semantic_label": "UNKNOWN",
            "parse_status": "AMBIGUOUS",
            "timing_issues": ["CONFLICTING_TIME_TAGS"],
            "timezone": None,
            "timezone_evidence": "NO_TIMEZONE_IN_SOURCE",
            "source_url": url,
            "raw_path": raw_path,
            "source_hash": source_hash,
            "parser_version": "vsdc-timing-recovery-v3",
        }

    lower_text = raw_str.lower()
    if "cập nhật" in lower_text or "chỉnh sửa" in lower_text or "sửa đổi" in lower_text or has_upd_attr:
        semantic_label = "UPDATE"
    elif "công bố" in lower_text or "đăng ngày" in lower_text or "ngày đăng" in lower_text or "phát hành" in lower_text or has_pub_attr:
        semantic_label = "PUBLICATION"
    else:
        semantic_label = "UNKNOWN"

    tz = None
    tz_evidence = "NO_TIMEZONE_IN_SOURCE"
    tz_match = re.search(r"(?:ICT|UTC|[+-]\d{2}:?\d{2}|GMT[+-]\d+)", raw_str, re.I)
    if tz_match:
        tz = tz_match.group(0).upper()
        tz_evidence = "EXPLICIT_TEXT_TIMEZONE"
    elif unique_stamps:
        stamp = unique_stamps[0]
        iso_tz = re.search(r"(?:Z|[+-]\d{2}:\d{2})$", stamp)
        if iso_tz:
            tz = iso_tz.group(0)
            tz_evidence = "EXPLICIT_ISO_TAG"

    candidates = []
    vn_dt_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*[-–—]?\s*(\d{1,2}):(\d{2})(?::(\d{2}))?", raw_str)
    if vn_dt_match:
        day, month, year, hour, minute, second = vn_dt_match.groups()
        candidates.append((int(year), int(month), int(day), int(hour), int(minute), int(second or 0), True, vn_dt_match.group(0)))
    else:
        iso_raw_match = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{1,2}):(\d{2})(?::(\d{2}))?", raw_str)
        if iso_raw_match:
            year, month, day, hour, minute, second = iso_raw_match.groups()
            candidates.append((int(year), int(month), int(day), int(hour), int(minute), int(second or 0), True, iso_raw_match.group(0)))
        else:
            vn_d_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw_str)
            if vn_d_match:
                day, month, year = vn_d_match.groups()
                candidates.append((int(year), int(month), int(day), 0, 0, 0, False, vn_d_match.group(0)))
            else:
                iso_d_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_str)
                if iso_d_match:
                    year, month, day = iso_d_match.groups()
                    candidates.append((int(year), int(month), int(day), 0, 0, 0, False, iso_d_match.group(0)))

    if unique_stamps:
        stamp = unique_stamps[0]
        tag_m = re.search(r"^(\d{4})-(\d{2})-(\d{2})[T\s](\d{1,2}):(\d{2})(?::(\d{2}))?", stamp)
        if tag_m:
            year, month, day, hour, minute, second = tag_m.groups()
            candidates.append((int(year), int(month), int(day), int(hour), int(minute), int(second or 0), True, stamp))
        else:
            tag_d = re.search(r"^(\d{4})-(\d{2})-(\d{2})", stamp)
            if tag_d:
                year, month, day = tag_d.groups()
                candidates.append((int(year), int(month), int(day), 0, 0, 0, False, stamp))

    if not candidates:
        return {
            "raw_text": raw_str,
            "parsed_date": None,
            "parsed_time": None,
            "parsed_datetime": None,
            "precision": "UNKNOWN",
            "semantic_label": semantic_label,
            "parse_status": "NO_DATETIME_FOUND",
            "timing_issues": [],
            "timezone": None,
            "timezone_evidence": "NO_TIMEZONE_IN_SOURCE",
            "source_url": url,
            "raw_path": raw_path,
            "source_hash": source_hash,
            "parser_version": "vsdc-timing-recovery-v3",
        }

    validated = []
    validation_errors = []
    for y, m, d, hh, mm, ss, is_dt, raw_seg in candidates:
        try:
            val_dt = datetime(y, m, d, hh, mm, ss)
            validated.append((val_dt, is_dt, raw_seg))
        except ValueError as err:
            validation_errors.append(f"INVALID_DATETIME: {err} in {raw_seg}")

    if validation_errors or not validated:
        return {
            "raw_text": raw_str or (candidates[0][-1]),
            "parsed_date": None,
            "parsed_time": None,
            "parsed_datetime": None,
            "precision": "UNKNOWN",
            "semantic_label": semantic_label,
            "parse_status": "INVALID_DATETIME",
            "timing_issues": validation_errors,
            "timezone": None,
            "timezone_evidence": "NO_TIMEZONE_IN_SOURCE",
            "source_url": url,
            "raw_path": raw_path,
            "source_hash": source_hash,
            "parser_version": "vsdc-timing-recovery-v3",
        }

    first_dt, first_is_dt, _ = validated[0]
    conflict = False
    for other_dt, other_is_dt, _ in validated[1:]:
        if first_is_dt and other_is_dt:
            if first_dt != other_dt:
                conflict = True
                break
        else:
            if first_dt.date() != other_dt.date():
                conflict = True
                break

    if conflict:
        return {
            "raw_text": raw_str or "; ".join(c[-1] for c in candidates),
            "parsed_date": None,
            "parsed_time": None,
            "parsed_datetime": None,
            "precision": "AMBIGUOUS",
            "semantic_label": "UNKNOWN",
            "parse_status": "AMBIGUOUS",
            "timing_issues": ["CONFLICTING_SOURCE_TIMES"],
            "timezone": None,
            "timezone_evidence": "NO_TIMEZONE_IN_SOURCE",
            "source_url": url,
            "raw_path": raw_path,
            "source_hash": source_hash,
            "parser_version": "vsdc-timing-recovery-v3",
        }

    chosen_dt, chosen_is_dt, _ = next((c for c in validated if c[1]), validated[0])
    p_date = chosen_dt.strftime("%Y-%m-%d")
    p_time = chosen_dt.strftime("%H:%M:%S") if chosen_is_dt else None
    p_datetime = f"{p_date}T{p_time}" if chosen_is_dt else None
    precision = "DATETIME" if chosen_is_dt else "DATE"

    return {
        "raw_text": raw_str or (unique_stamps[0] if unique_stamps else ""),
        "parsed_date": p_date,
        "parsed_time": p_time,
        "parsed_datetime": p_datetime,
        "precision": precision,
        "semantic_label": semantic_label,
        "parse_status": "VALID",
        "timing_issues": validation_errors,
        "timezone": tz,
        "timezone_evidence": tz_evidence,
        "source_url": url,
        "raw_path": raw_path,
        "source_hash": source_hash,
        "parser_version": "vsdc-timing-recovery-v3",
    }


def parse_vsdc(html, evidence):
    root = Document(html).root
    titles, contents = root.find(cls="title-category"), root.find(cls="content-category")
    if len(titles) != 1 or len(contents) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: VSDC article")
    title, content = titles[0].text(), contents[0]
    info = content.find(cls="item-info")
    labels = {info[i].text().rstrip(":").lower(): info[i+1].text() for i in range(0, len(info)-1, 2)}
    ticker = labels.get("mã chứng khoán", "")
    exchange = labels.get("nơi giao dịch", labels.get("sàn giao dịch", "" )).upper()
    if exchange == "HSX":
        exchange = "HOSE"
    raw = content.text()
    detected = kinds(title + " " + labels.get("lý do mục đích", ""))
    if not detected and "cổ tức" in labels.get("lý do mục đích", "").lower() and not kinds(raw):
        # An explicit per-share cash amount resolves an abbreviated dividend label.
        if terms("CASH_DIVIDEND",raw)[0].get("cash_dividend_per_share"):
            detected = ["CASH_DIVIDEND"]
    if not detected and re.search(r"đại hội|lấy ý kiến|họp", title, re.I) and not kinds(raw):
        return []  # recognized non-price-action notice, still archived in raw
    detected = detected or ["OTHER"]
    times = root.find(cls="time-newstcph")
    published_raw = times[0].text() if len(times) == 1 else ""
    explicit = root.find("time")
    timing = parse_vsdc_time(published_raw, explicit, url=evidence.get("url", ""),
                             raw_path=evidence.get("path"), source_hash=evidence.get("source_hash"))
    published = None
    if (timing.get("parse_status") == "VALID"
            and timing.get("semantic_label") == "PUBLICATION"
            and timing.get("timezone_evidence") == "EXPLICIT_ISO_TAG"):
        candidate = timing["parsed_datetime"] + (timing["timezone"] or "")
        try:
            if datetime.fromisoformat(candidate.replace("Z", "+00:00")).utcoffset() is not None:
                published = candidate
        except ValueError:
            pass  # An invalid offset is never evidence of historical availability.
    # Website's unlabeled timezone/update time is never silently backdated.
    known = published or evidence["fetched_at"]
    common = dict(ticker=ticker, exchange=exchange, isin=labels.get("mã isin", ""),
                  record_date=vn_date(labels.get("ngày đăng ký cuối cùng", "")),
                  ex_date=None, payment_date=None, announcement_date=published[:10] if published else vn_date(published_raw),
                  available_at=known, primary_source_published_at=published or vn_date(published_raw),
                  publication_time_raw=published_raw, source_timing=timing, available_at_evidence="EXPLICIT_SOURCE_TIME" if published else "FIRST_OBSERVED_AT_ONLY",
                  raw_terms=raw, primary_source_type="VSDC", primary_source_url=evidence["url"],
                  source_hash=evidence["source_hash"], evidence=[evidence], parser="vsdc-html-v3",
                  revision_reference_urls=[urljoin(evidence["url"], a.attrs["href"]) for a in content.find("a")
                                           if re.fullmatch(r"/vi/ad/\d+", a.attrs.get("href", ""))])
    common_raw = {"event_type": labels.get("lý do mục đích", title), "record_date": labels.get("ngày đăng ký cuối cùng"),
                  "exchange": labels.get("nơi giao dịch", labels.get("sàn giao dịch"))}
    for label, field in (("ngày giao dịch không hưởng quyền", "ex_date"), ("ngày thanh toán", "payment_date")):
        matches = re.findall(label + r"\s*[:=]\s*(\d{1,2}/\d{1,2}/\d{4})", raw, re.I)
        if len(set(matches)) == 1:
            common[field] = vn_date(matches[0])
            common_raw[field] = matches[0]
    rows = []
    for kind in detected:
        problems = [] if published else ["SOURCE_PUBLIC_TIME_UNVERIFIED"]
        if timing.get("parse_status") == "AMBIGUOUS":
            problems.append("TIMING_AMBIGUITY")
        elif timing.get("parse_status") == "INVALID_DATETIME":
            problems.append("INVALID_SOURCE_TIME")
        fragment = raw
        if len(detected) > 1:
            # Parse mixed components only from explicitly marked sections.
            explicit_section = component_sections(raw).get(kind)
            blocks = [n.text() for n in content.find("p") if kinds(n.text()) == [kind]]
            if explicit_section:
                fragment = explicit_section
            elif len(blocks) == 1:
                fragment = blocks[0]
            else:
                problems.append("MIXED_EVENT_AMBIGUITY")
                fragment = ""
        try:
            raw_values = dict(common_raw)
            values, term_problems = terms(kind, fragment, raw_values)
            problems.extend(term_problems)
        except ValueError:
            values = {}
            raw_values = dict(common_raw)
            problems.append("RATIO_PARSE_AMBIGUITY")
        revision = bool(re.search(r"đính chính|điều chỉnh|sửa đổi|hủy bỏ|hủy ngày|hủy\s+(?:thông báo|danh sách)|thay đổi mục đích", title, re.I))
        if revision:
            problems.append("REVISION_OR_CORRECTION_DETECTED")
        rows.append(common | values | dict(event_type=kind, parser_issues=problems,
                                          raw_field_values=raw_values,
                                          revision_status="UNRESOLVED" if revision else "ORIGINAL"))
    return rows


def parse_hnx(html, evidence, ticker, exchange="HNX"):
    root = Document(html).root
    sections = root.find(id="dTHQ")
    root = sections[0] if sections else root
    tables = [t for t in root.find("table") if "Ngày GDKHQ" in t.text() and "Ngày ĐKCC" in t.text()]
    if len(tables) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX rights calendar")
    result = []
    for row in tables[0].find("tr"):
        cells = row.find("td")
        if not cells:
            continue
        if len(cells) != 4:
            raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX calendar columns")
        raw = " | ".join(c.text() for c in cells)
        detected = kinds(cells[0].text())
        if not detected and re.search(r"họp|lấy ý kiến|đại hội", cells[0].text(), re.I):
            continue
        for kind in detected or ["OTHER"]:
            result.append(dict(ticker=ticker, exchange=exchange, event_type=kind,
                               ex_date=vn_date(cells[1].text()), record_date=vn_date(cells[2].text()),
                               payment_date=vn_date(cells[3].text()), raw_terms=raw,
                               available_at=evidence["fetched_at"], available_at_evidence="FIRST_OBSERVED_AT_ONLY",
                               primary_source_type="HNX", primary_source_url=evidence["url"],
                               source_hash=evidence["source_hash"], evidence=[evidence],
                               parser="hnx-calendar-v1", parser_issues=["SOURCE_PUBLIC_TIME_UNVERIFIED"],
                               raw_field_values={"event_type": cells[0].text(), "ex_date": cells[1].text(), "record_date": cells[2].text(), "payment_date": cells[3].text()},
                               revision_status="ORIGINAL"))
    pages = [int(n) for n in re.findall(r"ChangePageTHQ\((\d+)\)", html)]
    return result, max(pages, default=1)


def hnx_market_context(html, ticker):
    codes = re.findall(r"var _stock_code\s*=\s*'([^']+)'", html)
    markets = re.findall(r"var _market_code\s*=\s*'([^']+)'", html)
    if codes != [ticker] or len(markets) != 1 or markets[0] not in {"NY", "UC"}:
        raise SourceLimitation("HNX_IDENTITY_OR_MARKET_CONTEXT_UNVERIFIED")
    return markets[0], {"NY": "HNX", "UC": "UPCOM"}[markets[0]]


def vsdc_links(html):
    root = Document(html).root
    return list(dict.fromkeys(urljoin("https://vsdc.vn", a.attrs["href"]) for a in root.find("a")
                             if re.fullmatch(r"/vi/ad/\d+", a.attrs.get("href", ""))))


def search_url(ticker):
    return "https://vsdc.vn/vi/search?" + urlencode(dict(text=ticker, type=4, obj=110, buss=11021, fdate="", tdate=""))


def discover_vsdc(transport, ticker, max_pages, max_details):
    url, urls, checks, total = search_url(ticker), [], [], None
    pagination_error, failed_page = None, None
    for page in range(1, max_pages+1):
        payload = json.dumps(dict(SearchKey=4, CurrentPage=page)).encode() if page > 1 else None
        try:
            html, evidence = transport.fetch(url, payload)
        except SourceLimitation as exc:
            if not urls:
                raise
            # Preserve public links already acquired. The transport still enforces
            # host stops: a blocked host cannot be retried when fetching details.
            pagination_error, failed_page = str(exc), page
            break
        checks.append(evidence)
        links = vsdc_links(html)
        urls.extend(u for u in links if u not in urls)
        text = Document(html).root.text()
        match = re.search(r"Hiển thị:\s*\d+\s*-\s*\d+\s*/\s*(\d+)\s*bản ghi", text)
        total = int(match.group(1)) if match else None
        if not links or total is not None and len(urls) >= total or len(urls) >= max_details:
            break
    # Search totals describe matched announcements, never prove all historical rights.
    return urls[:max_details], {"source": "VSDC", "ticker": ticker, "status": "PARTIAL",
                                "reason": "BOUNDED_SEARCH_NOT_FULL_WINDOW_PROOF", "reported_total": total,
                                "discovered_urls": len(urls), "search_evidence": checks,
                                "pagination_error": pagination_error, "failed_page": failed_page}
