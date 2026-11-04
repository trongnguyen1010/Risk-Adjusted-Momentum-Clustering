"""Parse archived HNX notices for review; no network, timezone inference or PIT promotion."""
from __future__ import annotations

import copy
from datetime import datetime
import json
from pathlib import Path
import re

from .corporate_action_multisource import observation
from .corporate_action_sources import Document, SourceLimitation, kinds, now, sha, terms, vn_date


def parse_notice(html, evidence, ticker, exchange):
    if not re.fullmatch(r"[A-Z0-9]{2,10}", ticker) or exchange not in {"HNX", "UPCOM"}:
        raise ValueError("INVALID_EXPECTED_SCOPE")
    root = Document(html).root
    containers = root.find(cls="news-container")
    if len(containers) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX news container")
    article = containers[0]
    bodies, titles = article.find(cls="news-content"), article.find(cls="news-title")
    if len(bodies) != 1 or len(titles) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX title/content")
    raw, title = bodies[0].text(), titles[0].text()
    nodes = article.find(cls="news-public-time")
    raw_time = nodes[0].text() if len(nodes) == 1 else ""
    return _parse_content(raw, title, raw_time, evidence, ticker, exchange)


def _parse_content(raw, title, raw_time, evidence, ticker, exchange, *, timing_evidence=None,
                   parser_version="hnx-announcement-html-v1", event_reference=None, term_parser=terms):
    """Shared terms/date parsing; source layout and clock receipt stay explicit."""
    if not re.fullmatch(r"[A-Z0-9]{2,10}", ticker) or exchange not in {"HNX", "UPCOM"}:
        raise ValueError("INVALID_EXPECTED_SCOPE")
    codes = set(re.findall(r"(?i:đối với cổ phiếu)\s+([A-Z0-9]{2,10})\b", raw))
    if codes != {ticker}:
        raise SourceLimitation("HNX_NOTICE_TICKER_NOT_UNIQUE_OR_MISMATCH")
    detected = kinds(title + " " + raw)
    kind = detected[0] if len(detected) == 1 else "OTHER"
    issues = ["SOURCE_PUBLIC_TIME_UNVERIFIED", "HISTORICAL_IDENTITY_NOT_CERTIFIED"]
    values = {"ticker": ticker, "exchange": exchange, "event_type": kind}
    raw_values = {"ticker": ticker}
    ratio_semantics = ""
    date_labels = [("Ngày đăng ký cuối cùng", "record_date"),
                   ("Ngày giao dịch không hưởng quyền", "ex_date"), ("Ngày thanh toán", "payment_date")]
    if kind == "CASH_DIVIDEND":
        date_labels.append(("Thời gian thực hiện", "payment_date"))
    for field in {field for _, field in date_labels}:
        matches = [x for label, target in date_labels if target == field
                   for x in re.findall(re.escape(label) + r"\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", raw, re.I)]
        if len(set(matches)) == 1:
            values[field] = vn_date(matches[0])
            raw_values[field] = matches[0]
            if values[field] is None:
                issues.append("INVALID_DATE:" + field)
        elif len(set(matches)) > 1:
            issues.append("DATE_PARSE_AMBIGUITY:" + field)
    if kind != "OTHER":
        parsed_terms, problems = term_parser(kind, raw, raw_values)
        ratio_semantics = parsed_terms.pop("ratio_semantics", "")
        values.update(parsed_terms)
        issues.extend(problems)
    else:
        issues.append("MIXED_OR_UNKNOWN_EVENT_TYPE")
    parsed, time_precision = None, None
    for fmt, precision in [("%d/%m/%Y %H:%M:%S", "SECOND"), ("%d/%m/%Y %H:%M", "MINUTE"), ("%d/%m/%Y", "DATE")]:
        try:
            parsed, time_precision = datetime.strptime(raw_time, fmt), precision
            break
        except ValueError:
            pass
    clock_evidence = timing_evidence or evidence
    semantics = ("HNX list clock joined by exact provider article ID; provider semantics not independently certified"
                 if timing_evidence else "HNX news-public-time DOM class; provider semantics not independently certified")
    timing = {"raw_text": raw_time, "parsed_date": parsed.date().isoformat() if parsed else None,
              "parsed_time": parsed.strftime("%H:%M:%S" if time_precision == "SECOND" else "%H:%M") if parsed and time_precision != "DATE" else None,
              "precision": "DATE" if time_precision == "DATE" else "DATETIME" if parsed else "UNKNOWN",
              "time_precision": time_precision, "parse_status": "VALID" if parsed else "UNKNOWN",
              "semantic_label": "PUBLICATION_CANDIDATE", "semantic_evidence": semantics,
              "timezone": None, "timezone_evidence": "NO_VERIFIED_TIMEZONE", "source_url": clock_evidence["url"],
              "raw_path": clock_evidence["path"], "source_hash": clock_evidence["source_hash"], "parser_version": parser_version}
    timing["parsed_datetime"] = timing["parsed_date"] + "T" + timing["parsed_time"] if timing["parsed_time"] else None
    if parsed:
        values["announcement_date"] = parsed.date().isoformat()
    revision = bool(re.search(r"đính chính|điều chỉnh|sửa đổi|hủy bỏ|thay đổi", title, re.I))
    if revision:
        issues.append("REVISION_OR_CORRECTION_DETECTED")
    return observation({"source_type": "HNX", "source_url": evidence["url"], "source_hash": evidence["source_hash"],
                        "raw_terms": raw, "values": values, "ratio_semantics": ratio_semantics,
                        "raw_field_values": raw_values,
                        "primary_source_published_at": timing["parsed_date"], "publication_time_raw": raw_time,
                        "source_timing": timing, "observed_at": evidence["fetched_at"],
                        "available_at_evidence": "FIRST_OBSERVED_AT_ONLY",
                        "evidence": copy.deepcopy([evidence, timing_evidence] if timing_evidence else [evidence]),
                        "event_reference": event_reference,
                        "parser": parser_version, "parser_issues": issues,
                        "revision_status": "UNRESOLVED" if revision else "ORIGINAL"})


def parse_probe(probe_root, output, ticker, exchange):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    probe_root = probe_root.resolve()
    manifest_path = probe_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != "hnx-announcement-access-pilot-v1":
        raise ValueError("UNSUPPORTED_PROBE_ARTIFACT")
    for name, digest in manifest["files"].items():
        path = (probe_root / name).resolve()
        if not path.is_relative_to(probe_root) or sha(path.read_bytes()) != digest:
            raise ValueError("PROBE_CHECKSUM_MISMATCH: " + name)
    request = json.loads((probe_root / "requests.json").read_text(encoding="utf-8"))
    result = json.loads((probe_root / "result.json").read_text(encoding="utf-8"))
    if not result.get("public_response_received") or len(request) != 1 or request[0].get("status") != 200:
        raise ValueError("PROBE_HAS_NO_SUCCESSFUL_PUBLIC_RESPONSE")
    receipt = copy.deepcopy(request[0])
    path = (probe_root / receipt["path"]).resolve()
    if not path.is_relative_to(probe_root):
        raise ValueError("PROBE_RAW_PATH_ESCAPE")
    body = path.read_bytes()
    if sha(body) != receipt["source_hash"]:
        raise ValueError("PROBE_RAW_HASH_MISMATCH")
    receipt["path"] = "raw/source.bin"
    obs = parse_notice(body.decode("utf-8", errors="replace"), receipt, ticker, exchange)
    output.mkdir(parents=True, exist_ok=False)
    (output / "raw").mkdir()
    (output / receipt["path"]).write_bytes(body)
    (output / "observations.jsonl").write_text(json.dumps(obs, ensure_ascii=False) + "\n", encoding="utf-8")
    preview = {"status": "PARSED_FOR_REVIEW", "network_requests": 0, "observation_count": 1,
               "fields": {k: v.get("normalized_value") for k, v in obs["fields"].items()},
               "source_timing": obs["source_timing"], "accepted_publication_timestamp": obs["source_published_at"],
               "observed_at": obs["observed_at"], "data_verification": "NOT_EVALUATED",
               "pit_verification": "NOT_PROMOTED", "historical_identity": "NOT_CERTIFIED", "canonical_build": False}
    (output / "result.json").write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    new_manifest = {"artifact_type": "hnx-announcement-offline-parse-v1", "created_at": now(),
                    "origin_probe": str(probe_root), "origin_manifest_sha256": sha(manifest_path.read_bytes()),
                    "code_hashes": {p.name: sha(p.read_bytes()) for p in [Path(__file__), Path(__file__).with_name("corporate_action_sources.py"), Path(__file__).with_name("corporate_action_multisource.py")]},
                    "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    (output / "manifest.json").write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return preview
