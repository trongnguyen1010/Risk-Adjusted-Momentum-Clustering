"""Bounded supplemental job; existing discovery/detail/parser contracts stay intact."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import ssl
import time
from urllib.request import build_opener, HTTPSHandler

from ..corporate_action_sources import PublicTransport, SourceLimitation, sha, kinds, NoRedirect
from ..hnx_announcement_batch import RunBudget, verify_artifact, reviewable_receipt
from ..hnx_announcement_discovery import discover_for_batch
from ..hnx_announcement_details import acquire_details
from ..hnx_detail_parser import parse_details
from ..hnx_tls import validated_hnx_context
from .hnx_local_pvs import seal

TYPE = "hnx-local-supplement10-state-v1"
CONFIG = "configs/data/corporate_actions/hnx_local_supplement10_v1.json"
PREP = "data/corporate_actions/work/hnx_local_supplement10_preparation_20261103_v3"
BASE = "data/corporate_actions/work/hnx_local_supplement10_v1"
TICKERS = ("VE3", "TNG", "IDJ", "MBS", "RGG", "VTZ", "HKT", "PGN", "TIG", "VEF")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s]


def write(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)


def hashes(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


def runtime(project):
    names = [CONFIG, "scripts/corporate_actions/collect_hnx_local_supplement10_v1.py",
        "scripts/corporate_actions/prepare_hnx_local_supplement10_v1.py",
        "src/delta_t1/ingestion/corporate_actions/hnx_local_supplement.py",
        "src/delta_t1/ingestion/corporate_actions/hnx_local_pvs.py",
        "src/delta_t1/ingestion/corporate_action_sources.py",
        "src/delta_t1/ingestion/hnx_announcement_batch.py",
        "src/delta_t1/ingestion/hnx_announcement_discovery.py",
        "src/delta_t1/ingestion/hnx_announcement_details.py",
        "src/delta_t1/ingestion/hnx_detail_parser.py",
        "src/delta_t1/ingestion/hnx_announcement_parser.py",
        "src/delta_t1/ingestion/corporate_action_multisource.py",
        "src/delta_t1/ingestion/corporate_actions_v1.py",
        "src/delta_t1/ingestion/hnx_tls.py", "configs/data/hnx_tls_chain_v1.json",
        "configs/data/certificates/globalsign_gcc_r3_ev_tls_ca_2025.pem"]
    return {name: sha((project / name).read_bytes()) for name in names}


def validate(config, plan):
    exact = {"stage": "HNX_LOCAL_SUPPLEMENT10_V1", "workers": 1, "interval_seconds": 8,
        "timeout_seconds": 15, "max_bytes": 2000000, "max_pages_per_ticker": 2,
        "max_details_per_ticker": 2, "max_requests_job": 50, "max_seconds_run": 1200,
        "max_seconds_job": 2400, "canonical_build": False, "retry": False}
    if any(config.get(k) != v for k, v in exact.items()):
        raise ValueError("FROZEN_BOUNDED_SUPPLEMENT_CONTRACT_REQUIRED")
    targets = plan["targets"]
    if tuple(t["ticker"] for t in targets) != TICKERS:
        raise ValueError("EXACT_PREPARED_TEN_TARGETS_REQUIRED")
    for t in targets:
        if (t["exchange"] not in {"HNX", "UPCOM"} or not t["missing_fields"]
                or t["hnx_cached_discovery_articles"] or t["hnx_cached_successful_details"]
                or any(s != "ONLY_OTHER_OR_UNLINKED_CACHED_DOCUMENTS" for s in t["cache_field_status"].values())):
            raise ValueError("CACHE_FIRST_TARGET_EVIDENCE_REQUIRED")


def classify(reason, receipt):
    if reason.startswith(("RUN_REQUEST_BUDGET", "RUN_TIME_BUDGET")):
        return "BUDGET"
    # Access/TLS/unknown errors dominate any ticker-data error or stale receipt.
    if receipt and (receipt.get("status") in {401, 403, 429}
            or receipt.get("error") == "SOURCE_ACCESS_LIMITATION"
            or receipt.get("error_category") == "REQUEST_TIMEOUT"
            or receipt.get("response_headers", {}).get("Retry-After")):
        return "SOURCE_STOP"
    if receipt and reviewable_receipt(receipt):
        return "QUARANTINE"
    if reason.startswith(("HNX_DESKTOP_", "HNX_DISCLOSURE_", "UNSUPPORTED_CONTENT_TYPE",
                          "RESPONSE_SIZE_LIMIT")):
        return "QUARANTINE"
    return "SOURCE_STOP"


def candidates(discovery, target):
    from datetime import date
    records = rows(discovery / "discovered_articles.jsonl")
    seen = set(target.get("cached_successful_article_ids", []))
    eligible = [a for a in records if a["price_action_title_candidate"] and a["provider_article_id"] not in seen]
    hint = date.fromisoformat(target["search_hint_date"])
    eligible.sort(key=lambda a: (target["event_type_hint"] not in kinds(a["title"]),
        abs((date.fromisoformat(a["publication_date_candidate"]) - hint).days), a["provider_article_id"]))
    return [a["provider_article_id"] for a in eligible[:2]]


def load_preparation(project):
    prep = project / PREP
    verify_artifact(prep, {"hnx-local-supplement10-preparation-v1"})
    plan = read(prep / "plan.json")
    config = read(project / CONFIG)
    validate(config, plan)
    if read(prep / "runtime.json") != runtime(project):
        raise ValueError("PREPARED_RUNTIME_CHANGED_REVIEW_REQUIRED")
    canonical = project / plan["canonical_path"]
    if sha(canonical.read_bytes()) != plan["canonical_sha256"]:
        raise ValueError("C8_V2_CHANGED")
    securities = rows(canonical)
    if len(securities) != 1522:
        raise ValueError("C8_V2_INVENTORY_1522_REQUIRED")
    for target in plan["targets"]:
        matches = [s for s in securities if s["ticker"] == target["ticker"]]
        if len(matches) != 1 or matches[0]["exchange"] != target["exchange"]:
            raise ValueError("C8_V2_SOURCE_ASSIGNMENT_MISMATCH")
    return config, plan


def run(project, output, *, resume=None, dry_run=False, transport_factory=PublicTransport,
        prepare_tls=validated_hnx_context, clock=time.monotonic, emit=print):
    project, output = Path(project).resolve(), Path(output).resolve()
    config, plan = load_preparation(project)
    contract = sha(json.dumps([config, plan, runtime(project)], sort_keys=True).encode())
    parent = None
    state = {"contract_sha256": contract, "status": "PREPARED", "resumable": False,
        "requests_total": 0, "elapsed_seconds_total": 0, "completed_units": [], "targets": {},
        "source_stopped": False, "canonical_fields_applied": 0}
    if resume:
        resume = Path(resume).resolve()
        if not resume.is_relative_to((project / BASE).resolve()):
            raise ValueError("ONLY_NEW_LOCAL_SUPPLEMENT_STATE_CAN_RESUME")
        parent = verify_artifact(resume, {TYPE})
        state = read(resume / "checkpoint.json")
        if (state.get("contract_sha256") != contract or not state.get("resumable")
                or state.get("source_stopped") or state.get("inflight") is not None
                or state["requests_total"] >= config["max_requests_job"]
                or state["elapsed_seconds_total"] >= config["max_seconds_job"]):
            raise ValueError("CHECKPOINT_NOT_ELIGIBLE_NO_FORCE_RESUME")
        # Parser plans keep immutable absolute origins. Recheck pinned originals
        # as well as the sealed parent copy before permitting another request.
        for target_state in state["targets"].values():
            for ref in target_state.get("artifact_refs", []):
                origin = Path(ref["path"]).resolve()
                if not origin.is_relative_to((project / BASE).resolve()):
                    raise ValueError("RESUME_ORIGIN_OUTSIDE_NEW_JOB")
                actual = verify_artifact(origin)
                if actual["manifest_sha256"] != ref["manifest_sha256"]:
                    raise ValueError("RESUME_ORIGIN_MANIFEST_CHANGED")
    if dry_run:
        return {"status": "OFFLINE_CHECK_PASS", "network_requests": 0, "targets": plan["targets"], "budget": config}
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    output.mkdir(parents=True)
    if resume:
        # Preserve every parent byte, including partial units and request journal.
        shutil.copytree(resume, output / "parent")
    write(output / "plan.json", plan)
    write(output / "runtime.json", runtime(project))
    write(output / "lineage.json", {"parent": parent, "prior_requests": state["requests_total"]})
    shutil.copytree(project / PREP, output / "preparation")
    (output / "request_log.jsonl").touch()
    budget, started, prior_elapsed = None, clock(), state["elapsed_seconds_total"]
    prior_requests = state["requests_total"]
    seq = 0

    def checkpoint():
        nonlocal seq
        state["requests_total"] = prior_requests + (budget.count if budget else 0)
        state["elapsed_seconds_total"] = prior_elapsed + clock() - started
        seq += 1
        folder = output / "checkpoints"
        folder.mkdir(exist_ok=True)
        write(folder / f"{seq:04}.json", state)

    def unit(key, needed, operation):
        if key in state["completed_units"]:
            return
        if budget.count + needed > budget.max_requests:
            raise SourceLimitation("RUN_REQUEST_BUDGET_EXHAUSTED")
        if needed:
            budget.check()
        state["inflight"] = key
        checkpoint()  # A killed/uncertain unit is never silently retried.
        operation()
        state["completed_units"].append(key)
        state["inflight"] = None
        checkpoint()

    try:
        binary = shutil.which("openssl")
        if not binary and Path("C:/Program Files/Git/usr/bin/openssl.exe").is_file():
            binary = "C:/Program Files/Git/usr/bin/openssl.exe"
        context, tls = prepare_tls(project, output / "tls_chain", openssl_binary=binary)
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname or tls["status"] != "VALIDATED":
            raise ValueError("STRICT_VALIDATED_TLS_REQUIRED")

        def factory(path, **options):
            options.update(interval=8, timeout=15, max_bytes=config["max_bytes"])
            return transport_factory(path, opener=build_opener(NoRedirect(), HTTPSHandler(context=context)), **options)

        remaining_time = config["max_seconds_job"] - prior_elapsed - (clock() - started)
        budget = RunBudget(output, config["max_requests_job"] - prior_requests,
            min(config["max_seconds_run"], remaining_time), factory, clock)
        # First request after resume also waits at least 8s; preserve cross-client limiter.
        budget.last = time.monotonic()
        state.update(status="RUNNING", resumable=False, inflight=None)

        def transport(path, **options):
            client = budget.transport(path, **options)
            class Durable:
                @property
                def requests(self):
                    return client.requests

                def fetch(self, *args, **kwargs):
                    before = budget.count
                    try:
                        return client.fetch(*args, **kwargs)
                    finally:
                        if budget.count > before:
                            with (output / "request_timing.jsonl").open("a", encoding="utf-8") as stream:
                                stream.write(json.dumps({"request_number_this_run": budget.count,
                                    "unit": state["inflight"], "start_monotonic": budget.last,
                                    "end_monotonic": clock(), "artifact": str(path)}) + "\n")
                            checkpoint()
            return Durable()

        for target in plan["targets"]:
            ticker = target["ticker"]
            target_state = state["targets"].setdefault(ticker, {})
            if target_state.get("finished"):
                continue
            work = output / "work" / ticker
            work.mkdir(parents=True, exist_ok=True)
            emit(json.dumps({"ticker": ticker, "event": "START_OR_RESUME"}), flush=True)

            def discovery():
                dest = work / "discovery"
                result = discover_for_batch({"ticker": ticker, "exchange": target["exchange"]},
                    target["published_start"], target["published_end"], dest, max_pages=2, max_requests=3,
                    transport_factory=transport, scope_evidence={"c8_sha256": plan["canonical_sha256"]})
                target_state["discovery"] = str(dest)
                target_state.setdefault("artifact_refs", []).append(verify_artifact(dest))
                target_state["discovery_result"] = result
                if result["limitations"]:
                    reason = result["limitations"][0]["reason"]
                    action = classify(reason, budget.last_receipt)
                    target_state.update(review_reason=reason, action=action)
                    if action != "QUARANTINE":
                        raise SourceLimitation(reason)
                    target_state["finished"] = True
                else:
                    target_state["selected_ids"] = candidates(dest, target)
                    if not target_state["selected_ids"]:
                        target_state.update(finished=True, action="REVIEW_NO_CANDIDATE_WITHIN_CAP")

            unit(ticker + ":discovery", 3, discovery)
            if target_state.get("finished"):
                continue
            for aid in target_state["selected_ids"]:
                def detail():
                    dest = work / ("detail-" + aid)
                    result = acquire_details(Path(target_state["discovery"]), [aid], dest, transport_factory=transport)
                    target_state.setdefault("details", {})[aid] = str(dest)
                    target_state.setdefault("artifact_refs", []).append(verify_artifact(dest))
                    target_state.setdefault("detail_results", {})[aid] = result
                    if result["limitations"]:
                        reason = result["limitations"][0]["reason"]
                        action = classify(reason, budget.last_receipt)
                        target_state.update(review_reason=reason, action=action)
                        if action != "QUARANTINE":
                            raise SourceLimitation(reason)
                        target_state["finished"] = True

                unit(ticker + ":detail:" + aid, 1, detail)
                if target_state.get("finished"):
                    break

                def parse():
                    dest = work / ("parsed-" + aid)
                    result = parse_details(Path(target_state["details"][aid]), dest)
                    target_state.setdefault("artifact_refs", []).append(verify_artifact(dest))
                    target_state.setdefault("parsed", {})[aid] = {"path": str(dest), "result": result}
                    # Parser rejects are retained per article, never interpreted as zero/missing events.

                unit(ticker + ":parse:" + aid, 0, parse)
            target_state["finished"] = True
            checkpoint()
        state.update(status="FINISHED_BOUNDED_REVIEW_REQUIRED", resumable=False)
    except KeyboardInterrupt:
        state.update(status="INTERRUPTED_REVIEW_REQUIRED", resumable=state.get("inflight") is None)
    except SourceLimitation as exc:
        action = classify(str(exc), budget.last_receipt if budget else None)
        if action == "BUDGET":
            # A partially attempted discovery cannot be replayed safely; keep it for review.
            state.update(status="BUDGET_STOP", resumable=state.get("inflight") is None)
        else:
            state.update(status="SOURCE_OR_INTEGRITY_STOP", source_stopped=True, resumable=False)
        state["stop_reason"] = str(exc)
    except Exception as exc:
        state.update(status="SETUP_OR_INTEGRITY_STOP", source_stopped=True, resumable=False,
            stop_reason=str(exc), error_type=type(exc).__name__)
    finally:
        checkpoint()
        if state["requests_total"] >= config["max_requests_job"] or state["elapsed_seconds_total"] >= config["max_seconds_job"]:
            state["resumable"] = False
        write(output / "checkpoint.json", state)
        parsed = [p["result"] for t in state["targets"].values() for p in t.get("parsed", {}).values()]
        result = {"status": state["status"], "resumable": state["resumable"],
            "requests_this_run": budget.count if budget else 0, "requests_total": state["requests_total"],
            "tickers_finished": sum(t.get("finished", False) for t in state["targets"].values()),
            "discovered_articles": sum(t.get("discovery_result", {}).get("discovered_article_ids", 0) for t in state["targets"].values()),
            "successful_detail_articles": sum(d["successful_public_responses"] for t in state["targets"].values()
                for d in t.get("detail_results", {}).values()),
            "preview_observations": sum(p["observation_count"] for p in parsed),
            "review_rows": sum(p["review_queue_rows"] for p in parsed), "canonical_fields_applied": 0,
            "pit_or_identity_promoted": False, "full_history_certified": False, "openai_api_calls": 0}
        write(output / "result.json", result)
    return result
