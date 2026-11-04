"""Offline HNX popup extraction with exact article/list joins, for review only."""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
from urllib.parse import parse_qs

from . import corporate_actions_v1 as base
from .corporate_action_multisource import CRITICAL
from .corporate_action_sources import Document, SourceLimitation, now, sha
from .hnx_announcement_details import load_selection
from .hnx_announcement_discovery import DETAIL_URL, parse_search_page
from .hnx_announcement_parser import _parse_content

VERSION = "hnx-desktop-popup-v1"


def parse_popup(html, detail_receipt, list_record, list_receipt):
    article_id = list_record["provider_article_id"]
    expected_form = {k: [v] for k, v in list_record["detail_request"]["form"].items()}
    if (detail_receipt.get("url") != DETAIL_URL or detail_receipt.get("method") != "POST"
            or parse_qs(detail_receipt.get("request_body", "")) != expected_form):
        raise ValueError("DETAIL_RECEIPT_ARTICLE_ID_MISMATCH")
    root = Document(html).root
    containers = root.find(cls="divContentArticlesDetail")
    if len(containers) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX desktop container")
    titles, bodies = containers[0].find(cls="Box-TieuDe"), containers[0].find(cls="Box-Noidung")
    if len(titles) != 1 or len(bodies) != 1:
        raise SourceLimitation("PARSER_LAYOUT_CHANGED: HNX desktop title/content")
    if titles[0].text() != list_record["title"]:
        raise SourceLimitation("HNX_LIST_DETAIL_TITLE_MISMATCH")
    obs = _parse_content(bodies[0].text(), titles[0].text(), list_record["list_time_raw"],
                         detail_receipt, list_record["ticker_filter"], list_record["exchange_filter"],
                         timing_evidence=list_receipt, parser_version=VERSION,
                         event_reference="HNX_ARTICLE:" + article_id)
    obs["source_timing"]["provider_article_id"] = article_id
    obs["source_timing"]["clock_location"] = "DISCLOSURE_LIST_NOT_DETAIL_POPUP"
    # Keep each source receipt's fetched_at; never infer earlier content availability.
    obs["observed_at"] = max((detail_receipt["fetched_at"], list_receipt["fetched_at"]), key=base.timestamp)
    return obs


def _verified_artifact(root, artifact_type, required):
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != artifact_type or not set(required).issubset(manifest["files"]):
        raise ValueError("UNSUPPORTED_OR_INCOMPLETE_INPUT_ARTIFACT")
    for name, digest in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or sha(path.read_bytes()) != digest:
            raise ValueError("INPUT_CHECKSUM_MISMATCH: " + name)
    return manifest, sha(manifest_path.read_bytes())


def parse_details(details, output):
    return _parse_details(details, output, popup_parser=parse_popup, version=VERSION)


def _parse_details(details, output, *, popup_parser, version, additional_code_files=()):
    """Shared sealed-input validation/writer; legacy entrypoint retains its parser."""
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    details = details.resolve()
    manifest, input_hash = _verified_artifact(details, "hnx-discovered-detail-access-pilot-v1",
                                             ["plan.json", "requests.json", "result.json", "detail_responses.jsonl"])
    load = lambda name: json.loads((details / name).read_text(encoding="utf-8"))
    plan, requests, source_result = load("plan.json"), load("requests.json"), load("result.json")
    discovery = Path(plan["origin_discovery"]).resolve()
    rows = [json.loads(s) for s in (details / "detail_responses.jsonl").read_text(encoding="utf-8").splitlines() if s]
    ids = [r["provider_article_id"] for r in rows]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("NO_UNIQUE_SUCCESSFUL_DETAIL_RESPONSES")
    selected, discovery_hash = load_selection(discovery, ids)
    if discovery_hash != manifest["origin_manifest_sha256"] or discovery_hash != plan["origin_manifest_sha256"]:
        raise ValueError("ORIGIN_DISCOVERY_MANIFEST_MISMATCH")
    if source_result["successful_public_responses"] != len(rows) or source_result["network_requests"] != len(requests):
        raise ValueError("DETAIL_RECEIPT_COUNT_MISMATCH")
    prepared = []
    for row, article in zip(rows, selected):
        if article not in plan["selected_articles"] or row["ticker_filter"] != article["ticker_filter"] or row["exchange_filter"] != article["exchange_filter"]:
            raise ValueError("DETAIL_SELECTED_SCOPE_MISMATCH")
        receipt = row["receipt"]
        if receipt not in requests or receipt.get("status") != 200:
            raise ValueError("DETAIL_SUCCESS_RECEIPT_MISSING")
        path = (details / receipt["path"]).resolve()
        if (not path.is_relative_to(details) or receipt["path"] not in manifest["files"]
                or sha(path.read_bytes()) != receipt["source_hash"]):
            raise ValueError("DETAIL_RAW_RECEIPT_HASH_MISMATCH")
        clock = article["list_receipt"]
        list_body = (discovery / clock["path"]).read_bytes()
        replay, _ = parse_search_page(list_body.decode("utf-8-sig"), article["ticker_filter"],
                                      article["exchange_filter"], article["search_page"])
        matches = [r for r in replay if r["provider_article_id"] == article["provider_article_id"]]
        if len(matches) != 1 or dict(matches[0], list_receipt=clock) != article:
            raise ValueError("LIST_RAW_ARTICLE_JOIN_MISMATCH")
        prepared.append((article, receipt, path.read_bytes(), clock, list_body))
    observations, reviews, rejected, raw_files = [], [], [], {}
    for article, receipt, body, clock, list_body in prepared:
        aid = article["provider_article_id"]
        detail_ev, clock_ev = copy.deepcopy(receipt), copy.deepcopy(clock)
        for ev, origin, role, blob in [(detail_ev, details, "detail", body), (clock_ev, discovery, "list", list_body)]:
            ev.update(origin_artifact=str(origin), origin_path=ev["path"], evidence_role=role)
            ev["path"] = "raw/" + aid + "/" + role + ".bin"
            raw_files[ev["path"]] = blob
        try:
            extracted = popup_parser(body.decode("utf-8-sig"), detail_ev, article, clock_ev)
        except (SourceLimitation, ValueError) as exc:
            rejected.append({"provider_article_id": aid, "reason": str(exc)})
            reviews.append({"provider_article_id": aid, "ticker": article["ticker_filter"],
                            "observation_id": "", "field": "__article__", "reason": str(exc), "severity": "ERROR"})
            continue
        article_observations = extracted if isinstance(extracted, list) else [extracted]
        for obs in article_observations:
            observations.append(obs)
            _review_observation(obs, article, reviews)
    blocking_reasons = ("MISSING_REQUIRED_FIELD", "INVALID_NORMALIZED_FIELD", "DATE_ORDER_CONFLICT",
                        "DATE_PARSE_AMBIGUITY", "INVALID_DATE", "RATIO_PARSE_AMBIGUITY", "MIXED_OR_UNKNOWN_EVENT_TYPE")
    gate_ok = (bool(observations) and not rejected and not source_result.get("limitations")
               and not any(r["reason"].startswith(blocking_reasons) for r in reviews)
               and all(o["source_timing"]["parse_status"] == "VALID" for o in observations))
    result = {"status": "PARSED_WITH_REJECTIONS" if rejected else "PARSED_FOR_REVIEW", "network_requests": 0,
              "input_detail_responses": len(rows), "observation_count": len(observations), "rejected_articles": rejected,
              "review_queue_rows": len(reviews), "source_limitations": source_result.get("limitations", []),
              "accepted_publication_timestamps": sum(o["source_published_at"] is not None for o in observations),
              "canonical_build": False, "pit_verification": "NOT_PROMOTED", "historical_identity": "NOT_CERTIFIED",
              "extraction_gate": "PASS_FOR_INPUT_ARTICLES" if gate_ok else "REVIEW_REQUIRED",
              "bulk_collection_ready": False, "scope": "OFFLINE_EXTRACTION_OF_ARCHIVED_ACCESS_PILOT_ONLY",
              "samples": [{"provider_article_id": o["source_timing"]["provider_article_id"],
                           "fields": {k: v["normalized_value"] for k, v in o["fields"].items()},
                           "source_timing": o["source_timing"], "observed_at": o["observed_at"]} for o in observations]}
    output.mkdir(parents=True, exist_ok=False)
    for name, body in raw_files.items():
        (output / name).parent.mkdir(parents=True, exist_ok=True)
        (output / name).write_bytes(body)
    with (output / "observations.jsonl").open("x", encoding="utf-8") as stream:
        for obs in observations:
            stream.write(json.dumps(obs, ensure_ascii=False) + "\n")
    with (output / "review_queue.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["provider_article_id", "ticker", "observation_id", "field", "reason", "severity"])
        writer.writeheader(); writer.writerows(reviews)
    (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    code_files = [Path(__file__), Path(__file__).with_name("hnx_announcement_parser.py"),
                  Path(__file__).with_name("hnx_announcement_details.py"), Path(__file__).with_name("hnx_announcement_discovery.py"),
                  Path(__file__).with_name("corporate_action_sources.py"), Path(__file__).with_name("corporate_action_multisource.py"),
                  Path(__file__).with_name("corporate_actions_v1.py"), *additional_code_files]
    new_manifest = {"artifact_type": "hnx-desktop-detail-offline-parse-v1", "parser_version": version, "created_at": now(),
                    "origin_details": str(details), "origin_details_manifest_sha256": input_hash,
                    "origin_discovery": str(discovery), "origin_discovery_manifest_sha256": discovery_hash,
                    "code_hashes": {p.name: sha(p.read_bytes()) for p in code_files},
                    "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    (output / "manifest.json").write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _review_observation(obs, article, reviews):
    """Apply identical field/review gates to each source component."""
    aid = article["provider_article_id"]
    def review(field, reason, severity="REVIEW"):
        reviews.append({"provider_article_id": aid, "ticker": article["ticker_filter"],
                        "observation_id": obs["observation_id"], "field": field, "reason": reason, "severity": severity})
    for issue in obs["parser_issues"]:
        review("__metadata__", issue)
    values = {k: v["normalized_value"] for k, v in obs["fields"].items() if v["parse_status"] == "VALID"}
    required = set(CRITICAL) | set(base.TERMS.get(values.get("event_type"), ()))
    for field in sorted(required):
        if values.get(field) is None or values.get(field) == "":
            review(field, "MISSING_REQUIRED_FIELD")
    for field, entry in obs["fields"].items():
        if entry["parse_status"] != "VALID":
            review(field, "INVALID_NORMALIZED_FIELD")
    for field in ("record_date", "payment_date"):
        if field not in values:
            review(field, "NOT_PRESENT_IN_PARSED_FIELDS", "INFO")
    for first, last in [("ex_date", "record_date"), ("record_date", "payment_date")]:
        if values.get(first) and values.get(last) and values[first] > values[last]:
            review(first, "DATE_ORDER_CONFLICT")
