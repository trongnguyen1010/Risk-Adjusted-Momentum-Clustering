"""Overlay timestamp được owner duyệt theo field cho Product/M3 pilot, offline."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup


PURPOSE = "PRODUCT_M3_PILOT"
FORMAT = "CA_PUBLISHER_TIMESTAMP_OVERLAY_V1"


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _json(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY:" + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("NON_FINITE_JSON:" + value)
    return json.loads(body, object_pairs_hook=unique, parse_constant=invalid)


def _path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("PATH_OUTSIDE_ROOT")
    return path


def _instant(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("EXPLICIT_TIMESTAMP_REQUIRED")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("EXPLICIT_OFFSET_REQUIRED")
    return result


def _verified(root, ref, inputs):
    body = _path(root, ref["path"]).read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if not body or digest != ref["sha256"]:
        raise ValueError("INPUT_HASH_MISMATCH:" + ref["path"])
    if ref["path"] in inputs and inputs[ref["path"]] != digest:
        raise ValueError("INCONSISTENT_INPUT_PIN")
    inputs[ref["path"]] = digest
    return body


def _http(root, raw_ref, receipt_ref, url, inputs):
    body = _verified(root, raw_ref, inputs)
    receipt = _json(_verified(root, receipt_ref, inputs))
    if (receipt.get("status") != 200 or receipt.get("method") != "GET"
            or receipt.get("challenge") is not False or receipt.get("url") != url
            or receipt.get("raw_path") != raw_ref["path"]
            or receipt.get("sha256") != raw_ref["sha256"]
            or receipt.get("bytes") != len(body)):
        raise ValueError("HTTP_RECEIPT_BINDING_OR_ACCESS_CONTROL")
    return body


def _prepare(policy, root, inputs):
    if (policy.get("status") != "OWNER_APPROVED" or policy.get("activated") is not True
            or policy.get("purpose") != PURPOSE or policy.get("DATE_ONLY_enabled") is not False
            or policy.get("canonical_build") is not False
            or policy.get("strict_research_gate_opened") is not False):
        raise ValueError("SCOPED_OWNER_APPROVAL_REQUIRED")
    approval = _json(_verified(root, policy["owner_approval_ref"], inputs))
    if any(approval.get(k) != policy[k] for k in ("event_id", "timestamp", "purpose", "field_count")):
        raise ValueError("OWNER_APPROVAL_SCOPE_MISMATCH")
    if approval.get("owner_message") != "hãy thực hiện":
        raise ValueError("OWNER_EXECUTION_INSTRUCTION_REQUIRED")
    accepted_at = _instant(policy["timestamp"])
    mappings = _json(_verified(root, policy["field_mappings_ref"], inputs))
    ids = [x["row_id"] for x in mappings]
    if len(ids) != len(set(ids)) or len(ids) != policy["field_count"]:
        raise ValueError("MAPPING_COUNT_OR_DUPLICATE")
    prior = _json(_verified(root, policy["prior_proposed_mappings_ref"], inputs))
    prior = {x["row_id"]: x for x in prior}
    baseline = {}
    for ref in policy["baseline_packets"]:
        packet = _json(_verified(root, ref, inputs))
        for row in packet["rows"]:
            if row["row_id"] in baseline:
                raise ValueError("DUPLICATE_BASELINE_ROW")
            baseline[row["row_id"]] = row
    if len(baseline) != policy["baseline_rows"]:
        raise ValueError("BASELINE_ROW_COUNT")
    for row in mappings:
        old = baseline.get(row["row_id"], {})
        candidate = prior.get(row["row_id"], {})
        if row["event_id"] != policy["event_id"] or row["exact_ticker"] != policy["exact_ticker"]:
            raise ValueError("EVENT_OR_TICKER_OUTSIDE_APPROVAL")
        for key in ("row_id", "event_id", "field", "field_scope"):
            if old.get(key) != row[key] or candidate.get(key) != row[key]:
                raise ValueError("FIELD_SCOPE_CHANGED:" + key)
        if (_encoded(old.get("review_value")) != _encoded(row["value"])
                or _encoded(candidate.get("value")) != _encoded(row["value"])):
            raise ValueError("REVIEWED_VALUE_CHANGED")
    evidence = policy["evidence"]
    html = _http(root, evidence["article_ref"], evidence["article_receipt_ref"],
                 evidence["article_url"], inputs)
    soup = BeautifulSoup(html, "html.parser")
    next_data = soup.select_one("script#__NEXT_DATA__")
    if next_data is None:
        raise ValueError("PUBLIC_ARTICLE_METADATA_MISSING")
    post = _json(next_data.string)["props"]["pageProps"]["initialPost"]
    articles = [_json(x.string) for x in soup.select('script[type="application/ld+json"]')]
    articles = [x for x in articles if x.get("@type") == "NewsArticle"]
    if len(articles) != 1:
        raise ValueError("UNIQUE_PUBLICATION_RECORD_REQUIRED")
    article = articles[0]
    if (post["postID"] != evidence["post_id"] or post["title"] != evidence["headline"]
            or article.get("headline") != evidence["headline"]
            or article.get("publisher", {}).get("name") != policy["publisher"]
            or not any(x["symbol"] == policy["exact_ticker"] for x in post["taggedSymbols"])):
        raise ValueError("ARTICLE_IDENTITY_MISMATCH")
    if _instant(post["date"]) != accepted_at or _instant(article["datePublished"]) != accepted_at:
        raise ValueError("PUBLICATION_TIMESTAMP_DISAGREEMENT")
    modified = article.get("dateModified")
    if "dateModified" in article:
        if _instant(modified) != accepted_at:
            raise ValueError("MODIFIED_PUBLICATION_CONFLICT")
    elif policy.get("allow_missing_modified_only_for_pinned_mappings") is not True:
        raise ValueError("SCOPED_MISSING_MODIFIED_ACCEPTANCE_REQUIRED")
    file_url = evidence["attachment_url"]
    if (not any(x.get("fileContentUrl") == file_url for x in post["files"])
            or not any(x.get("href") == file_url for x in soup.select("a[href]"))):
        raise ValueError("DIRECT_ATTACHMENT_LINK_MISSING")
    pdf = _http(root, evidence["attachment_ref"], evidence["attachment_receipt_ref"], file_url, inputs)
    original = _verified(root, evidence["original_HOSE_PDF_ref"], inputs)
    if not pdf.startswith(b"%PDF") or pdf != original:
        raise ValueError("ORIGINAL_PDF_BINDING_MISMATCH")
    rows = []
    selected = set(ids)
    for key, old in sorted(baseline.items()):
        accepted = key in selected
        rows.append({"row_id": key, "event_id": old["event_id"], "field": old["field"],
                     "field_scope": old["field_scope"], "value": old["review_value"],
                     "purpose": PURPOSE, "admission_status": "ADMITTED" if accepted else "DEFERRED_NOT_APPROVED_IN_THIS_SCOPE",
                     "available_at": policy["timestamp"] if accepted else None,
                     "usable_from_date": None, "publication_source": policy["publisher"] if accepted else None,
                     "source_url": evidence["article_url"] if accepted else None,
                     "availability_basis": "OWNER_ACCEPTED_PUBLISHER_ASSERTION_DIRECT_PDF" if accepted else None,
                     "source_dateModified": modified if accepted else None,
                     "historical_content_at_publication_certified": False,
                     "first_exchange_publication_proved": False, "canonical_applied": False,
                     "strict_research_eligible": False, "policy_id": policy["policy_id"] if accepted else None})
    return rows


def run(config, output, root="."):
    root = Path(root).resolve()
    config_path = _path(root, config)
    body = config_path.read_bytes()
    inputs = {config_path.relative_to(root).as_posix(): hashlib.sha256(body).hexdigest()}
    policy = _json(body)
    rows = _prepare(policy, root, inputs)
    output_path = _path(root, output)
    if output_path.exists():
        raise ValueError("IMMUTABLE_OUTPUT_ALREADY_EXISTS")
    summary = {"format": FORMAT, "policy_id": policy["policy_id"], "purpose": PURPOSE,
               "status": "PASS_APPROVED_FIELD_TIMESTAMP_OVERLAY", "rows": len(rows),
               "admitted_rows": sum(x["admission_status"] == "ADMITTED" for x in rows),
               "held_rows": sum(x["available_at"] is None for x in rows), "network_requests": 0,
               "canonical_build": False, "strict_research_gate_opened": False,
               "DATE_ONLY_enabled": False, "HOSE_clock_resolved": False}
    output_path.mkdir(parents=True, exist_ok=False)
    (output_path / "approved_policy.json").write_bytes(body)
    (output_path / "field_availability.jsonl").write_bytes(b"".join(_encoded(x) + b"\n" for x in rows))
    (output_path / "summary.json").write_bytes(_encoded(summary) + b"\n")
    files = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in output_path.iterdir()}
    policy_ref = {"path": config_path.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest()}
    (output_path / "manifest.json").write_bytes(_encoded({"format": FORMAT, "files": files, "inputs": inputs,
                                                       "policy_ref": policy_ref}) + b"\n")
    return summary


def eligible_fields(artifact, decision_at, *, root=".", purpose=PURPOSE):
    """Chỉ đọc artifact đã pin; không đưa dữ liệu ra trước publication instant."""
    if purpose != PURPOSE:
        raise ValueError("OVERLAY_NOT_APPROVED_FOR_RESEARCH_OR_CANONICAL")
    decision = _instant(decision_at)
    root = Path(root).resolve()
    directory = _path(root, artifact)
    manifest = _json((directory / "manifest.json").read_bytes())
    if manifest["format"] != FORMAT:
        raise ValueError("UNSUPPORTED_OVERLAY_FORMAT")
    if set(manifest["files"]) != {"approved_policy.json", "field_availability.jsonl", "summary.json"}:
        raise ValueError("REQUIRED_OUTPUT_MANIFEST_MEMBERS")
    for name, digest in manifest["files"].items():
        if Path(name).name != name or hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError("OUTPUT_HASH_MISMATCH")
    inputs = {}
    for name, digest in manifest["inputs"].items():
        _verified(root, {"path": name, "sha256": digest}, inputs)
    approved_body = _verified(root, manifest["policy_ref"], inputs)
    if approved_body != (directory / "approved_policy.json").read_bytes():
        raise ValueError("OUTPUT_POLICY_DIFFERS_FROM_APPROVAL")
    policy = _json(approved_body)
    expected = _prepare(policy, root, inputs)
    actual = [_json(line) for line in (directory / "field_availability.jsonl").read_bytes().splitlines()]
    if _encoded(actual) != _encoded(expected):
        raise ValueError("OVERLAY_CONTENT_DIFFERS_FROM_APPROVED_SCOPE")
    return [x for x in actual if x["admission_status"] == "ADMITTED" and _instant(x["available_at"]) <= decision]
