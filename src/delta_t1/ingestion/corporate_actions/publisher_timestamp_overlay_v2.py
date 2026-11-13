"""Overlay pilot V2: kế thừa FireAnt V1 và thêm scoped article/WARC đã duyệt."""
from datetime import datetime, timezone
from io import BytesIO
import base64
import gzip
import hashlib
from pathlib import Path
import re

from bs4 import BeautifulSoup

from . import publisher_timestamp_overlay as v1

FORMAT = "CA_PUBLISHER_TIMESTAMP_OVERLAY_V2"
PURPOSE = v1.PURPOSE
LIVE = "LIVE_SCOPED_ARTICLE_TEXT_V1"
ARCHIVE = "ARCHIVED_SCOPED_ARTICLE_TEXT_V1"


def _archive(group, root, inputs):
    e = group["evidence"]
    raw = v1._verified(root, e["warc_ref"], inputs)
    r = v1._json(v1._verified(root, e["archive_receipt_ref"], inputs))
    index = v1._http(root, e["index_ref"], e["index_receipt_ref"], e["index_url"], inputs)
    records = [v1._json(x) for x in index.splitlines() if x.strip()]
    record = r["target_record"]
    offset, length = int(record["offset"]), int(record["length"])
    requested_range = f"bytes={offset}-{offset + length - 1}"
    filename = record["filename"]
    if not re.fullmatch(r"crawl-data/CC-MAIN-\d{4}-\d{2}/segments/[\d.]+/warc/CC-MAIN-\d{14}-\d{14}-\d{5}\.warc\.gz", filename):
        raise ValueError("ARCHIVE_FILENAME_INVALID")
    cr = r.get("headers", {}).get("Content-Range", "")
    if (r.get("status") != 206 or r.get("method") != "GET" or r.get("challenge", False)
            or r.get("url") != "https://data.commoncrawl.org/" + filename
            or r.get("raw_path") != e["warc_ref"]["path"]
            or r.get("sha256") != e["warc_ref"]["sha256"]
            or r.get("bytes") != len(raw) or offset < 0 or not 0 < length <= 2000000
            or len(raw) != length or r.get("Range") != requested_range
            or not re.fullmatch(rf"bytes {offset}-{offset + length - 1}/\d+", cr)
            or int(cr.rsplit("/", 1)[1]) < offset + length
            or record not in records or record.get("status") != "200"
            or record.get("url") != e["article_url"]
            or r.get("index_ref") != e["index_ref"]):
        raise ValueError("ARCHIVE_RECEIPT_RANGE_OR_INDEX_BINDING")
    decoded = gzip.GzipFile(fileobj=BytesIO(raw)).read(4000001)
    if len(decoded) > 4000000:
        raise ValueError("ARCHIVE_DECOMPRESSED_LIMIT")
    header, rest = decoded.split(b"\r\n\r\n", 1)
    wh = {k.lower(): val.strip() for k, val in
          (line.split(":", 1) for line in header.decode("utf-8").split("\r\n")[1:] if ":" in line)}
    capture = v1._instant(e["capture_at"])
    cdx_capture = datetime.strptime(record["timestamp"], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    if (wh.get("warc-type") != "response" or wh.get("warc-target-uri") != e["article_url"]
            or v1._instant(wh["warc-date"]) != capture or capture != cdx_capture
            or v1._instant(r["archive_capture_at"]) != capture):
        raise ValueError("ARCHIVE_TARGET_OR_CAPTURE_MISMATCH")
    block_size = int(wh["content-length"])
    content = rest[:block_size]
    hh, payload = content.split(b"\r\n\r\n", 1)
    lines = hh.decode("latin-1").split("\r\n")
    http = {k.lower(): val.strip() for k, val in
            (line.split(":", 1) for line in lines[1:] if ":" in line)}
    if (len(content) != block_size or lines[0].split()[1] != "200"
            or http.get("content-encoding") or http.get("transfer-encoding")
            or int(http.get("content-length", len(payload))) != len(payload)):
        raise ValueError("UNSUPPORTED_OR_INVALID_ARCHIVED_HTTP_RESPONSE")
    digest = base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii")
    derived = v1._verified(root, e["article_ref"], inputs)
    if (digest != record["digest"] or wh.get("warc-payload-digest") != "sha1:" + digest
            or derived != payload or r.get("derived_HTML_sha256") != e["article_ref"]["sha256"]):
        raise ValueError("ARCHIVE_PAYLOAD_DIGEST_OR_DERIVED_BODY")
    return derived


def _publication(group, body):
    soup = BeautifulSoup(body, "html.parser")
    articles = [v1._json(x.string) for x in soup.select('script[type="application/ld+json"]')]
    articles = [x for x in articles if isinstance(x, dict) and x.get("@type") == "NewsArticle"]
    if len(articles) != 1:
        raise ValueError("UNIQUE_PUBLICATION_RECORD_REQUIRED")
    a, e = articles[0], group["evidence"]
    instant = v1._instant(group["timestamp"])
    if (a.get("headline") != e["headline"] or a.get("mainEntityOfPage", {}).get("@id") != e["article_url"]
            or a.get("publisher", {}).get("name") != group["publisher"]):
        raise ValueError("SCOPED_ARTICLE_IDENTITY")
    if v1._instant(a["datePublished"]) != instant or v1._instant(a.get("dateModified")) != instant:
        raise ValueError("PUBLICATION_OR_MODIFIED_CONFLICT")
    for selector in ['meta[property="article:published_time"]', 'meta[itemprop="datePublished"]',
                     'meta[property="article:modified_time"]']:
        tags = soup.select(selector)
        if len(tags) != 1 or v1._instant(tags[0].get("content")) != instant:
            raise ValueError("PUBLICATION_META_DISAGREEMENT")
    if e.get("time_selector"):
        tags = soup.select(e["time_selector"])
        if len(tags) != 1 or v1._instant(tags[0].get("datetime")) != instant or int(tags[0]["data-time"]) != int(instant.timestamp()):
            raise ValueError("ARTICLE_TIME_OR_EPOCH_DISAGREEMENT")
    return soup, a["dateModified"]


def _prepare(policy, root, inputs):
    if (policy.get("status") != "OWNER_APPROVED" or policy.get("activated") is not True
            or policy.get("purpose") != PURPOSE or policy.get("DATE_ONLY_enabled") is not False
            or policy.get("canonical_build") is not False or policy.get("strict_research_gate_opened") is not False):
        raise ValueError("SCOPED_OWNER_APPROVAL_REQUIRED")
    approval = v1._json(v1._verified(root, policy["owner_approval_ref"], inputs))
    if approval.get("owner_message") != "hãy thực hiện" or approval.get("purpose") != PURPOSE:
        raise ValueError("OWNER_EXECUTION_INSTRUCTION_REQUIRED")
    v1._verified(root, policy["base_runtime_ref"], inputs)
    base_ref = policy["base_artifact"]
    base_dir = v1._path(root, base_ref["directory"])
    manifest_ref = {"path": (Path(base_ref["directory"]) / "manifest.json").as_posix(), "sha256": base_ref["manifest_sha256"]}
    v1._verified(root, manifest_ref, inputs)
    base_policy = v1._json((base_dir / "approved_policy.json").read_bytes())
    carried = v1.eligible_fields(base_dir, base_policy["timestamp"], root=root)
    base_manifest = v1._json((base_dir / "manifest.json").read_bytes())
    for name, digest in base_manifest["files"].items():
        v1._verified(root, {"path": (Path(base_ref["directory"]) / name).as_posix(), "sha256": digest}, inputs)
    for name, digest in base_manifest["inputs"].items():
        v1._verified(root, {"path": name, "sha256": digest}, inputs)
    rows = [v1._json(x) for x in (base_dir / "field_availability.jsonl").read_bytes().splitlines()]
    if len(carried) != policy["carry_forward_count"] or len(rows) != policy["baseline_rows"]:
        raise ValueError("CARRY_FORWARD_OR_BASELINE_COUNT")
    baseline, packet_refs = {}, {}
    for ref in policy["baseline_packets"]:
        packet = v1._json(v1._verified(root, ref, inputs))
        for row in packet["rows"]:
            if row["row_id"] in baseline:
                raise ValueError("DUPLICATE_BASELINE_ROW")
            baseline[row["row_id"]], packet_refs[row["row_id"]] = row, ref
    if len(baseline) != len(rows) or len({x["row_id"] for x in rows}) != len(rows):
        raise ValueError("BASELINE_ROW_SET")
    for row in rows:
        b = baseline[row["row_id"]]
        if (any(row[k] != b[k] for k in ["event_id", "field", "field_scope"])
                or v1._encoded(row["value"]) != v1._encoded(b["review_value"])):
            raise ValueError("BASELINE_VALUE_OR_SCOPE_CHANGED")
    mappings = v1._json(v1._verified(root, policy["field_mappings_ref"], inputs))
    proposed = v1._json(v1._verified(root, policy["prior_proposed_mappings_ref"], inputs))
    if len(proposed) != len({x["row_id"] for x in proposed}):
        raise ValueError("DUPLICATE_PROPOSED_MAPPING")
    proposed = {x["row_id"]: x for x in proposed}
    ids = [x["row_id"] for x in mappings]
    if len(set(ids)) != len(ids) or len(ids) != policy["new_field_count"]:
        raise ValueError("MAPPING_COUNT_OR_DUPLICATE")
    approved = {x["event_id"]: x for x in approval["approved_groups"]}
    if len(approved) != len(approval["approved_groups"]):
        raise ValueError("DUPLICATE_APPROVAL_GROUP")
    groups = policy["groups"]
    if len(groups) != len({g["event_id"] for g in groups}) or set(approved) != {g["event_id"] for g in groups}:
        raise ValueError("APPROVAL_GROUP_SET")
    updates = {}
    for g in groups:
        selected = [x for x in mappings if x["event_id"] == g["event_id"]]
        selected_ids = sorted(x["row_id"] for x in selected)
        if (g["field_count"] != len(selected) or sorted(g["field_locators"]) != selected_ids
                or approved[g["event_id"]] != {"event_id": g["event_id"], "timestamp": g["timestamp"],
                    "field_count": g["field_count"], "publication_source": g["publication_source"], "row_ids": selected_ids}):
            raise ValueError("OWNER_APPROVAL_GROUP_SCOPE")
        if g["profile"] == LIVE:
            body = v1._http(root, g["evidence"]["article_ref"], g["evidence"]["article_receipt_ref"], g["evidence"]["article_url"], inputs)
            receipt_ref = g["evidence"]["article_receipt_ref"]
        elif g["profile"] == ARCHIVE:
            body = _archive(g, root, inputs)
            receipt_ref = g["evidence"]["archive_receipt_ref"]
        else:
            raise ValueError("UNSUPPORTED_EVIDENCE_PROFILE")
        soup, modified = _publication(g, body)
        for x in selected:
            b, old = baseline[x["row_id"]], proposed[x["row_id"]]
            if x["row_id"] in {r["row_id"] for r in carried}:
                raise ValueError("CANNOT_REPLACE_CARRIED_ADMISSION")
            if (x["exact_ticker"] != policy["exact_ticker"]
                    or any(x[k] != b[k] or x[k] != old[k] for k in ["row_id", "event_id", "field"])
                    or x["field_scope"] != b["field_scope"]
                    or old.get("field_scope") not in [None, x["field_scope"]]
                    or v1._encoded(x["value"]) != v1._encoded(b["review_value"])
                    or v1._encoded(x["value"]) != v1._encoded(old["value"])
                    or x["field_scope_provenance"] != {"packet_ref": packet_refs[x["row_id"]], "row_id": x["row_id"]}
                    or x["source_ref"] != g["evidence"]["article_ref"] or x["source_receipt_ref"] != receipt_ref
                    or v1._instant(x["proposed_source_published_at"]) != v1._instant(g["timestamp"])):
                raise ValueError("REVIEWED_FIELD_VALUE_SCOPE_OR_SOURCE_CHANGED")
            loc = g["field_locators"][x["row_id"]]
            nodes = soup.select(loc["selector"])
            ordinal = loc["ordinal"]
            if not isinstance(ordinal, int) or ordinal < 0 or ordinal >= len(nodes):
                raise ValueError("SCOPED_FIELD_LOCATOR_MISSING")
            text = nodes[ordinal].get_text(" ", strip=True)
            if not text or hashlib.sha256(text.encode()).hexdigest() != loc["text_sha256"]:
                raise ValueError("SCOPED_FIELD_TEXT_HASH")
            updates[x["row_id"]] = {"admission_status": "ADMITTED", "available_at": g["timestamp"],
                "publication_source": g["publisher"], "source_url": g["evidence"]["article_url"],
                "availability_basis": "OWNER_ACCEPTED_PUBLISHER_ASSERTION_SCOPED_TEXT",
                "source_dateModified": modified, "evidence_profile": g["profile"], "policy_id": policy["policy_id"]}
    if set(updates) != set(ids):
        raise ValueError("UNMAPPED_OR_UNAPPROVED_ROWS")
    return [{**r, **updates.get(r["row_id"], {})} for r in rows]


def run(config, output, root="."):
    root = Path(root).resolve()
    config_path = v1._path(root, config)
    body = config_path.read_bytes()
    policy = v1._json(body)
    policy_ref = {"path": config_path.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest()}
    inputs = {policy_ref["path"]: policy_ref["sha256"]}
    rows = _prepare(policy, root, inputs)
    output_path = v1._path(root, output)
    if output_path.exists():
        raise ValueError("IMMUTABLE_OUTPUT_ALREADY_EXISTS")
    summary = {"format": FORMAT, "policy_id": policy["policy_id"], "purpose": PURPOSE,
        "status": "PASS_APPROVED_FIELD_TIMESTAMP_OVERLAY", "rows": len(rows),
        "admitted_rows": sum(x["admission_status"] == "ADMITTED" for x in rows),
        "held_rows": sum(x["available_at"] is None for x in rows),
        "new_admitted_rows": policy["new_field_count"], "carried_rows_unchanged": policy["carry_forward_count"],
        "network_requests": 0, "DATE_ONLY_enabled": False, "canonical_build": False,
        "strict_research_gate_opened": False, "first_exchange_publication_verified": False}
    output_path.mkdir(parents=True, exist_ok=False)
    (output_path / "approved_policy.json").write_bytes(body)
    (output_path / "field_availability.jsonl").write_bytes(b"".join(v1._encoded(x) + b"\n" for x in rows))
    (output_path / "summary.json").write_bytes(v1._encoded(summary) + b"\n")
    files = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in output_path.iterdir()}
    (output_path / "manifest.json").write_bytes(v1._encoded({"format": FORMAT, "files": files, "inputs": inputs, "policy_ref": policy_ref}) + b"\n")
    return summary


def eligible_fields(artifact, decision_at, *, root=".", purpose=PURPOSE):
    if purpose != PURPOSE:
        raise ValueError("OVERLAY_NOT_APPROVED_FOR_RESEARCH_OR_CANONICAL")
    decision = v1._instant(decision_at)
    root = Path(root).resolve()
    directory = v1._path(root, artifact)
    manifest = v1._json((directory / "manifest.json").read_bytes())
    if manifest["format"] != FORMAT or set(manifest["files"]) != {"approved_policy.json", "field_availability.jsonl", "summary.json"}:
        raise ValueError("UNSUPPORTED_OVERLAY_OR_MANIFEST_MEMBERS")
    for name, digest in manifest["files"].items():
        if Path(name).name != name or hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError("OUTPUT_HASH_MISMATCH")
    inputs = {}
    for name, digest in manifest["inputs"].items():
        v1._verified(root, {"path": name, "sha256": digest}, inputs)
    body = v1._verified(root, manifest["policy_ref"], inputs)
    if body != (directory / "approved_policy.json").read_bytes():
        raise ValueError("OUTPUT_POLICY_DIFFERS_FROM_APPROVAL")
    expected = _prepare(v1._json(body), root, inputs)
    actual = [v1._json(x) for x in (directory / "field_availability.jsonl").read_bytes().splitlines()]
    if v1._encoded(actual) != v1._encoded(expected):
        raise ValueError("OVERLAY_CONTENT_DIFFERS_FROM_APPROVED_SCOPE")
    return [x for x in actual if x["admission_status"] == "ADMITTED" and v1._instant(x["available_at"]) <= decision]
