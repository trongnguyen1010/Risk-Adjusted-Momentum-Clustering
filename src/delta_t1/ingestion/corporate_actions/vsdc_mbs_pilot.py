"""Two-request public pagination diagnostic, kept separate from deferred old jobs."""
from pathlib import Path
import json
import re
import ssl
import time
from urllib.request import build_opener, HTTPSHandler

from ..corporate_action_sources import PublicTransport, NoRedirect, SourceLimitation, Document, sha, search_url
from ..corporate_action_cache_audit import search_links
from ..hnx_announcement_batch import RunBudget, verify_artifact
from .hnx_local_supplement import read, rows, write
from .hnx_local_pvs import seal
from .vsdc_pagination_audit import snapshot_coverage

CONFIG = "configs/data/corporate_actions/vsdc_mbs_pagination_pilot_v1.json"
TYPE = "vsdc-mbs-two-request-pagination-pilot-v1"


def validate(config):
    expected = {"stage": "VSDC_MBS_TWO_REQUEST_PAGINATION_PILOT_V1", "ticker": "MBS", "url": search_url("MBS"),
        "page2_payload": {"SearchKey": 4, "CurrentPage": 2}, "post_content_type": "application/json;charset=utf-8",
        "max_requests": 2, "max_seconds": 90, "interval_seconds": 8, "timeout_seconds": 15,
        "max_bytes": 2000000, "workers": 1, "retry": False, "resume": False, "detail_requests": 0,
        "canonical_build": False, "automatic_approval": False}
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("EXACT_TWO_REQUEST_PUBLIC_QUERY_CONTRACT_REQUIRED")


def source_contract(html):
    root = Document(html).root
    if [n.text() for n in root.find("p")].count("Kết quả tìm kiếm với từ: MBS") != 1:
        raise ValueError("FRESH_QUERY_SCOPE_ECHO_REQUIRED")
    if len(root.find(id="divGlSearchArticles")) != 1:
        raise ValueError("FRESH_ARTICLES_CONTAINER_REQUIRED")
    start = html.find("function searchGlSearch(type)")
    end = html.find("</script>", start)
    if start < 0 or end < start: raise ValueError("FIRST_PARTY_PAGINATION_SCRIPT_REQUIRED")
    script = html[start:end]
    patterns = [r'type\s*:\s*"POST"', r'url\s*:\s*window\.location\.pathname\s*\+\s*window\.location\.search',
        r'contentType\s*:\s*"application/json;charset=utf-8"', r'data\s*:\s*JSON\.stringify\s*\(',
        r'SearchKey\s*:\s*type', r'CurrentPage\s*:\s*Number\(_spage\)',
        r'type\s*==\s*4[\s\S]*?_spage\s*=\s*crrPageArticles']
    if any(not re.search(p, script) for p in patterns):
        raise ValueError("FIRST_PARTY_PAGINATION_CONTRACT_CHANGED")
    return {"script": script, "script_sha256": sha(script.encode()), "query_echo": "Kết quả tìm kiếm với từ: MBS"}


def page(html, number, total=None, prior_ids=()):
    links = search_links(html.encode("utf-8"), search_url("MBS"))
    ids = [r["provider_article_id"] for r in links]
    if len(ids) != len(set(ids)): raise ValueError("DUPLICATE_ARTICLE_IDS_WITHIN_PAGE")
    coverage = snapshot_coverage(html.encode("utf-8"), ids)
    if coverage["query_status"] in {"SEARCH_LAYOUT_UNVERIFIED", "SEARCH_COUNT_OR_LINKS_INCONSISTENT"}:
        raise ValueError("PUBLIC_SEARCH_FRAGMENT_REQUIRES_REVIEW")
    if number == 1:
        if coverage.get("first") != 1 or not ids:
            raise ValueError("FRESH_NONEMPTY_PAGE_ONE_REQUIRED")
    else:
        if (coverage.get("first") != 21 or coverage.get("last") != min(40, total)
                or coverage["reported_total"] != total or set(ids) & set(prior_ids)):
            raise ValueError("PAGE_TWO_RANGE_TOTAL_OR_ID_OVERLAP_REQUIRES_REVIEW")
    return {"page": number, "coverage": coverage, "articles": links, "article_ids": ids}


def runtime(project):
    names = [CONFIG, "scripts/corporate_actions/probe_vsdc_mbs_pagination_v1.py",
        "scripts/corporate_actions/prepare_vsdc_mbs_pagination_v1.py",
        "src/delta_t1/ingestion/corporate_actions/vsdc_mbs_pilot.py",
        "src/delta_t1/ingestion/corporate_actions/vsdc_pagination_audit.py",
        "src/delta_t1/ingestion/corporate_actions/hnx_local_supplement.py",
        "src/delta_t1/ingestion/corporate_actions/hnx_local_pvs.py",
        "src/delta_t1/ingestion/corporate_action_sources.py",
        "src/delta_t1/ingestion/corporate_action_cache_audit.py",
        "src/delta_t1/ingestion/hnx_announcement_batch.py"]
    return {name: sha((project / name).read_bytes()) for name in names}


def load_preparation(project):
    config = read(project / CONFIG); validate(config)
    prep = project / config["preparation"]
    verify_artifact(prep, {"vsdc-mbs-pagination-preparation-v1"})
    if read(prep / "runtime.json") != runtime(project): raise ValueError("PREPARED_RUNTIME_CHANGED")
    for name, digest in read(prep / "protected_old_files.json").items():
        if sha((project / name).read_bytes()) != digest: raise ValueError("PROTECTED_OLD_STATE_CHANGED")
    canonical = project / config["canonical"]
    if sha(canonical.read_bytes()) != config["canonical_sha256"]: raise ValueError("C8_SOURCE_ASSIGNMENT_CHANGED")
    securities = rows(canonical)
    if len(securities) != 1522 or [(s["ticker"], s["exchange"]) for s in securities if s["ticker"] == "MBS"] != [("MBS", "HNX")]:
        raise ValueError("C8_V2_MBS_SCOPE_REQUIRED")
    return config, prep


def run(project, output, *, dry_run=False, transport_factory=PublicTransport, clock=time.monotonic, emit=print):
    project, output = Path(project).resolve(), Path(output).resolve()
    config, prep = load_preparation(project)
    if output.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    if dry_run:
        return {"status": "OFFLINE_CHECK_PASS", "network_requests": 0, "ticker": "MBS", "max_requests": 2,
            "steps": ["GET_FRESH_PAGE1_VALIDATE_PUBLIC_CONTRACT", "POST_PAGE2_ONCE"], "max_seconds": 90,
            "interval_seconds": 8, "timeout_seconds": 15, "details_allowed": 0, "resume_allowed": False}
    output.mkdir(parents=True)
    write(output / "plan.json", config)
    write(output / "runtime.json", runtime(project))
    # Store the evidence needed for offline ZIP review without copying large old datasets.
    for name in ["source_contract.json", "protected_old_files.json", "cached_article_ids.json"]:
        (output / name).write_bytes((prep / name).read_bytes())
    write(output / "input_provenance.json", {"preparation_path": str(prep),
        "preparation_manifest_sha256": sha((prep / "manifest.json").read_bytes()),
        "cached_article_ids_sha256": sha((prep / "cached_article_ids.json").read_bytes()),
        "scope_audit_manifest_sha256": config["scope_audit_manifest_sha256"],
        "canonical_sha256": config["canonical_sha256"]})
    (output / "request_log.jsonl").touch()
    result = {"stage": config["stage"], "status": "PILOT_STOPPED_SETUP_OR_REVIEW_REQUIRED", "network_requests": 0,
        "successful_complete_responses": 0, "page2_verified": False, "resumable": False, "source_stopped": False,
        "detail_requests": 0, "normalized_observations": 0, "canonical_fields_applied": 0,
        "bulk_collection_ready": False, "pit_or_identity_promoted": False, "openai_api_calls": 0}
    budget, client, seq = None, None, 0
    protected = read(prep / "protected_old_files.json")
    def changed_protected_files():
        changed = []
        for name, digest in protected.items():
            try:
                if sha((project / name).read_bytes()) != digest: changed.append(name)
            except OSError:
                changed.append(name)
        return changed
    def checkpoint(event):
        nonlocal seq
        seq += 1
        folder = output / "checkpoints";folder.mkdir(exist_ok=True)
        write(folder / f"{seq:03}.json", {"event": event, "requests": budget.count if budget else 0,
            "resumable": False, "status": result["status"], "at_monotonic": clock()})
    try:
        context = ssl.create_default_context()
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname: raise ValueError("STRICT_TLS_REQUIRED")
        write(output / "tls.json", {"hostname_verification": context.check_hostname, "certificate_verification": "CERT_REQUIRED",
            "verify_flags": context.verify_flags, "new_root_trust": False, "HNX_intermediate_not_used_for_VSDC": True})
        def factory(path, **options):
            return transport_factory(path, opener=build_opener(NoRedirect(), HTTPSHandler(context=context)), **options)
        budget = RunBudget(output, 2, 90, factory, clock)
        client = budget.transport(output, max_requests=2, interval=8, timeout=15, max_bytes=2000000)
        def fetch(stage, payload=None):
            if changed_protected_files(): raise ValueError("PROTECTED_OLD_STATE_CHANGED_BEFORE_REQUEST")
            checkpoint(stage + "_INFLIGHT")
            before = budget.count
            try:
                response = client.fetch(config["url"], payload, content_type=config["post_content_type"] if payload else "text/html")
                result["successful_complete_responses"] += 1
                return response
            finally:
                if budget.count > before:
                    with (output / "request_timing.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({"stage": stage, "start_monotonic": budget.last, "end_monotonic": clock()}) + "\n")
                checkpoint(stage + "_RETURNED_OR_FAILED")
        emit(json.dumps({"event": "FRESH_MBS_PAGE1", "max_requests": 2}), flush=True)
        html, receipt = fetch("PAGE1_GET")
        contract = source_contract(html)
        write(output / "fresh_source_contract.json", contract)
        first = page(html, 1)
        write(output / "page1.json", first)
        total = first["coverage"]["reported_total"]
        if total <= 20:
            result["status"] = "PARTIAL_FRESH_QUERY_HAS_NO_SECOND_PAGE"
        else:
            if first["coverage"]["last"] != 20: raise ValueError("FRESH_PAGE_SIZE_20_REQUIRED")
            payload = json.dumps(config["page2_payload"], separators=(",", ":")).encode("utf-8")
            write(output / "page2_request.json", {"url": config["url"], "method": "POST", "body_utf8": payload.decode(),
                "content_type": config["post_content_type"], "basis": "FRESH_PUBLIC_FIRST_PARTY_JS_CONTRACT"})
            emit(json.dumps({"event": "MBS_PAGE2_ONCE", "reported_total": total}), flush=True)
            html, receipt = fetch("PAGE2_POST", payload)
            second = page(html, 2, total, first["article_ids"])
            cached_ids = set(read(prep / "cached_article_ids.json"))
            for article in second["articles"]:
                article.update(provider_id_already_in_audited_cache=article["provider_article_id"] in cached_ids,
                    detail_download_authorized=False, event_identity_verified=False)
            write(output / "page2.json", second)
            result.update(status="PASS_PAGE2_ACCESS_AND_LAYOUT_REVIEW_REQUIRED", page2_verified=True,
                page1_article_ids=len(first["article_ids"]), page2_article_ids=len(second["article_ids"]),
                pair_distinct_article_ids=len(set(first["article_ids"]) | set(second["article_ids"])),
                cached_page2_provider_ids=sum(a["provider_id_already_in_audited_cache"] for a in second["articles"]),
                reported_total=total, remaining_query_rows_after_pair=total - len(first["article_ids"]) - len(second["article_ids"]))
    except KeyboardInterrupt:
        result.update(status="CANCELLED_REVIEW_REQUIRED", stop_reason="USER_INTERRUPT_NO_AUTOMATIC_REPLAY")
    except Exception as exc:
        result.update(status="STOPPED_SOURCE_OR_LAYOUT_REVIEW_REQUIRED", source_stopped=True,
            error_type=type(exc).__name__, stop_reason=str(exc))
    finally:
        result["network_requests"] = budget.count if budget else 0
        request_rows = client.requests if client else []
        write(output / "requests.json", request_rows)
        result["http_statuses"] = [r.get("status") for r in request_rows]
        changed = changed_protected_files()
        if changed:
            result.update(status="PROTECTED_OLD_STATE_CHANGED_REVIEW_REQUIRED", source_stopped=True,
                stop_reason="; ".join(changed))
        checkpoint("FINAL_NONRESUMABLE")
        write(output / "checkpoint.json", {"status": result["status"], "resumable": False,
            "requests_total": result["network_requests"], "no_old_checkpoint_resume": True})
        write(output / "result.json", result)
    return result
