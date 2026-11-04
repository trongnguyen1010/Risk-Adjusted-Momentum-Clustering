"""Fixed MBS AJAX-header diagnostic; frozen V1 sources and states stay unchanged."""
from pathlib import Path
import json
import ssl
import time
from urllib.request import build_opener, HTTPSHandler

from ..corporate_action_sources import PublicTransport, NoRedirect, sha, search_url
from ..hnx_announcement_batch import RunBudget, verify_artifact
from .hnx_local_supplement import read, rows, write, hashes
from .hnx_local_pvs import seal
from . import vsdc_mbs_pilot as v1

CONFIG = "configs/data/corporate_actions/vsdc_mbs_pagination_pilot_v2.json"
TYPE = "vsdc-mbs-two-request-pagination-pilot-v2"
PREPARATION_TYPE = "vsdc-mbs-pagination-preparation-v2"
AJAX_HEADER = {"X-Requested-With": "XMLHttpRequest"}
USER_AGENT = "DeltaT1Research/0.2 (bounded corporate-action research)"
source_contract, page = v1.source_contract, v1.page


def validate(config):
    v1.validate({**config, "stage": "VSDC_MBS_TWO_REQUEST_PAGINATION_PILOT_V1"})
    expected = {
        "stage": "VSDC_MBS_TWO_REQUEST_PAGINATION_PILOT_V2",
        "post_headers": AJAX_HEADER,
        "output_base": "data/corporate_actions/work/vsdc_mbs_pagination_pilot_v2",
        "preparation": "data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v2",
        "v1_preparation": "data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v1",
        "v1_preparation_manifest_sha256": "f00f41d9a46ca601d4e91cbeb966fd6df5b659423a710063ba6d8d8003b3f0e7",
        "v1_run": "data/corporate_actions/work/vsdc_mbs_pagination_pilot_v1/run-20261103T043616143951Z/state",
        "v1_run_manifest_sha256": "88fffcab03f3e71dd168d84d32d6ca9fc0b248a604136d1e39ddcc1e5f69f4d5",
        "browser_evidence": "data/corporate_actions/work/vsdc_mbs_request_metadata_comparison_20261103_v2",
        "browser_evidence_manifest_sha256": "61b917f6f84d66202abdf0eba60fc3bc4f9acaf141e390a8b91a4fc8a93655a1",
    }
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("EXACT_V2_AJAX_DIAGNOSTIC_CONTRACT_REQUIRED")


def runtime(project):
    names = [CONFIG, "scripts/corporate_actions/probe_vsdc_mbs_pagination_v2.py",
             "scripts/corporate_actions/prepare_vsdc_mbs_pagination_v2.py",
             "src/delta_t1/ingestion/corporate_actions/vsdc_mbs_pilot_v2.py"]
    return {**v1.runtime(project), **{name: sha((project / name).read_bytes()) for name in names}}


def verify_parents(project, config):
    _, old_prep = v1.load_preparation(project)
    if old_prep != project / config["v1_preparation"]:
        raise ValueError("V1_PREPARATION_PATH_CHANGED")
    for key, kind in [("v1_preparation", "vsdc-mbs-pagination-preparation-v1"),
                      ("v1_run", v1.TYPE),
                      ("browser_evidence", "vsdc-mbs-request-metadata-comparison-v2")]:
        folder = project / config[key]
        if sha((folder / "manifest.json").read_bytes()) != config[key + "_manifest_sha256"]:
            raise ValueError("PARENT_MANIFEST_CHANGED: " + key)
        verify_artifact(folder, {kind})
    result = read(project / config["v1_run"] / "result.json")
    if result["http_statuses"] != [200, 400] or result["resumable"] or result["page2_verified"]:
        raise ValueError("V1_STOP_EVIDENCE_CHANGED")
    headers = read(project / config["browser_evidence"] / "user_request_headers.json")
    if (headers["browser_x_requested_with"] != "XMLHttpRequest"
            or headers["browser_request_content_type"] != "application/json;charset=UTF-8"
            or headers["full_browser_capture_obtained"] is not False):
        raise ValueError("USER_TRANSCRIBED_HEADER_EVIDENCE_CHANGED")
    return old_prep


def load_preparation(project):
    config = read(project / CONFIG)
    validate(config)
    verify_parents(project, config)
    prep = project / config["preparation"]
    verify_artifact(prep, {PREPARATION_TYPE})
    if read(prep / "runtime.json") != runtime(project):
        raise ValueError("PREPARED_RUNTIME_CHANGED")
    if read(prep / "plan.json")["config"] != config:
        raise ValueError("PREPARED_PLAN_CHANGED")
    for name, digest in read(prep / "protected_old_files.json").items():
        if sha((project / name).read_bytes()) != digest:
            raise ValueError("PROTECTED_OLD_STATE_CHANGED: " + name)
    return config, prep


def prepare(project):
    project = Path(project).resolve()
    config = read(project / CONFIG)
    validate(config)
    old_prep = verify_parents(project, config)
    out = project / config["preparation"]
    if out.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    protected = read(old_prep / "protected_old_files.json")
    for key in ["v1_preparation", "v1_run", "browser_evidence"]:
        folder = project / config[key]
        for name in ["manifest.json", *read(folder / "manifest.json")["files"]]:
            path = folder / name
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    protected.update(v1.runtime(project))
    ids = read(old_prep / "cached_article_ids.json")
    if len(ids) != 27730 or len(ids) != len(set(ids)):
        raise ValueError("AUDITED_CACHE_ID_COUNT_CHANGED")
    out.mkdir(parents=True)
    for name in ["cached_article_ids.json", "source_contract.json"]:
        (out / name).write_bytes((old_prep / name).read_bytes())
    (out / "browser_request_headers.json").write_bytes(
        (project / config["browser_evidence"] / "user_request_headers.json").read_bytes())
    write(out / "plan.json", {"config": config, "status": "PREPARED_NOT_EXECUTED",
        "network_requests": 0, "cached_provider_article_ids": len(ids),
        "only_wire_change_from_v1": "X-Requested-With: XMLHttpRequest on fixed page2 POST",
        "evidence_level": "USER_TRANSCRIBED_DEVTOOLS_HEADERS_NOT_RAW_BROWSER_CAPTURE",
        "proven_cause_or_fix": False, "old_v1_immutable": True})
    write(out / "protected_old_files.json", protected)
    write(out / "runtime.json", runtime(project))
    write(out / "manifest.json", {"artifact_type": PREPARATION_TYPE, "files": hashes(out)})
    load_preparation(project)
    return {"output": str(out), "status": "PREPARED_NOT_EXECUTED", "network_requests": 0,
            "max_requests_user_run": 2, "protected_old_files": len(protected), "cached_article_ids": len(ids)}


class AjaxPostOpener:
    """One source-observed functional header, never cookies/auth or header rotation."""
    def __init__(self, inner, output):
        self.inner, self.output, self.count = inner, output, 0

    def open(self, request, timeout=None):
        expected_method = "GET" if self.count == 0 else "POST"
        headers = {k.casefold(): v for k, v in request.header_items()}
        if (self.count >= 2 or request.full_url != search_url("MBS")
                or request.get_method() != expected_method or timeout != 15
                or set(headers) != {"user-agent", "accept", "content-type"}
                or headers["user-agent"] != USER_AGENT or headers["accept"] != "text/html"):
            raise ValueError("FIXED_V2_REQUEST_CONSTRUCTION_REQUIRED")
        if expected_method == "GET":
            if request.data is not None or headers["content-type"] != "text/html":
                raise ValueError("FIXED_V2_PAGE1_GET_REQUIRED")
        else:
            if (request.data != b'{"SearchKey":4,"CurrentPage":2}'
                    or headers["content-type"] != "application/json;charset=utf-8"):
                raise ValueError("FIXED_V2_PAGE2_POST_REQUIRED")
            request.add_header("X-Requested-With", "XMLHttpRequest")
        self.count += 1
        with (self.output / "request_construction.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"method": request.get_method(), "url": request.full_url,
                "body_utf8": request.data.decode() if request.data is not None else None,
                "headers": dict(request.header_items()),
                "capture_stage": "BEFORE_URLLIB_HANDLERS_NOT_FULL_WIRE_CAPTURE"}) + "\n")
        return self.inner.open(request, timeout=timeout)


def run(project, output, *, dry_run=False, transport_factory=PublicTransport, clock=time.monotonic, emit=print):
    project, output = Path(project).resolve(), Path(output).resolve()
    config, prep = load_preparation(project)
    if output.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    if dry_run:
        return {"status": "OFFLINE_CHECK_PASS", "network_requests": 0, "ticker": "MBS", "max_requests": 2,
            "steps": ["GET_FRESH_PAGE1_VALIDATE_PUBLIC_CONTRACT", "POST_PAGE2_ONCE"], "max_seconds": 90,
            "interval_seconds": 8, "timeout_seconds": 15, "details_allowed": 0, "resume_allowed": False,
            "post_only_headers": AJAX_HEADER, "causal_fix_proven": False}
    output.mkdir(parents=True)
    write(output / "plan.json", config)
    write(output / "runtime.json", runtime(project))
    # Store the evidence needed for offline ZIP review without copying large old datasets.
    for name in ["source_contract.json", "protected_old_files.json", "cached_article_ids.json", "browser_request_headers.json"]:
        (output / name).write_bytes((prep / name).read_bytes())
    write(output / "input_provenance.json", {"preparation_path": str(prep),
        "preparation_manifest_sha256": sha((prep / "manifest.json").read_bytes()),
        "cached_article_ids_sha256": sha((prep / "cached_article_ids.json").read_bytes()),
        "scope_audit_manifest_sha256": config["scope_audit_manifest_sha256"],
        "canonical_sha256": config["canonical_sha256"],
        "browser_evidence_manifest_sha256": config["browser_evidence_manifest_sha256"],
        "v1_run_manifest_sha256": config["v1_run_manifest_sha256"],
        "v1_preparation_manifest_sha256": config["v1_preparation_manifest_sha256"]})
    (output / "request_log.jsonl").touch()
    (output / "request_construction.jsonl").touch()
    result = {"stage": config["stage"], "status": "PILOT_STOPPED_SETUP_OR_REVIEW_REQUIRED", "network_requests": 0,
        "successful_complete_responses": 0, "page2_verified": False, "resumable": False, "source_stopped": False,
        "detail_requests": 0, "normalized_observations": 0, "canonical_fields_applied": 0,
        "bulk_collection_ready": False, "pit_or_identity_promoted": False, "openai_api_calls": 0, "causal_fix_proven": False}
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
            opener = AjaxPostOpener(build_opener(NoRedirect(), HTTPSHandler(context=context)), path)
            return transport_factory(path, opener=opener, **options)
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
                "content_type": config["post_content_type"], "post_headers": AJAX_HEADER,
                "basis": "FRESH_PUBLIC_JS_AND_USER_TRANSCRIBED_BROWSER_AJAX_HEADER"})
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
