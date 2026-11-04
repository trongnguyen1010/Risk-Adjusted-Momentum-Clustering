"""Orchestrate fixed PVS/ACV user-run pilots with existing fail-closed adapters."""
import json
from pathlib import Path
import shutil
import ssl
import time
from urllib.request import build_opener, HTTPSHandler
import zipfile

from delta_t1.ingestion.corporate_action_sources import PublicTransport, NoRedirect, sha
from delta_t1.ingestion.hnx_tls import validated_hnx_context
from delta_t1.ingestion.hnx_announcement_batch import RunBudget
from delta_t1.ingestion.hnx_announcement_discovery import discover
from delta_t1.ingestion.hnx_announcement_details import acquire_details
from delta_t1.ingestion.hnx_detail_parser import parse_details
from .kbs_pilot import write_json


def validate(config):
    profiles = {
        ("PVS", "HNX"): ("2024-10-01", "2024-11-30", "537190"),
        ("ACV", "UPCOM"): ("2025-07-01", "2025-08-31", "573433"),
    }
    profile = profiles.get((config.get("ticker"), config.get("exchange")))
    if profile is None:
        raise ValueError("EXACT_BOUNDED_KNOWN_EVENT_PROFILE_REQUIRED")
    start, end, article = profile
    expected = {"published_start": start, "published_end": end, "max_pages": 1, "max_requests": 3,
        "interval_seconds": 8, "timeout_seconds": 15, "max_seconds": 120, "known_article_id": article,
        "canonical_build": False, "retry": False, "resume_old_checkpoint": False}
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("EXACT_BOUNDED_KNOWN_EVENT_PILOT_REQUIRED")
    if config["ticker"] == "ACV" and (config.get("require_known_article") is not True
            or config.get("expected_event_type") != "STOCK_DIVIDEND"):
        raise ValueError("EXACT_ACV_NONCASH_ARTICLE_REQUIRED")


def run(project, output, config, *, dry_run=False, transport_factory=PublicTransport,
        prepare_tls=validated_hnx_context, clock=time.monotonic, emit=print):
    validate(config)
    ticker, exchange = config["ticker"], config["exchange"]
    canonical = project / "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl"
    body = canonical.read_bytes()
    securities = [json.loads(s) for s in body.decode("utf-8").splitlines() if s]
    matches = [s for s in securities if s["ticker"] == ticker]
    if len(matches) != 1 or matches[0]["exchange"] != exchange:
        raise ValueError("KNOWN_EVENT_C8_V2_SCOPE_MISMATCH")
    plan = {**config, "c8_v2_sha256": sha(body), "canonical_path": str(canonical),
        "canonical_scope_is_not_historical_identity_proof": True, "openai_api_calls": 0,
        "authorization_scope": "User requested this known-event pilot; no reuse of exhausted HLA authorization or checkpoint resume"}
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    if dry_run:
        return {**plan, "status": "DRY_RUN", "network_requests": 0}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output, "plan.json", plan)
    code_paths = [Path(__file__), project / f"scripts/corporate_actions/probe_hnx_{ticker.lower()}_local_v1.py",
        project / f"configs/data/corporate_actions/hnx_{ticker.lower()}_local_pilot_v1.json"]
    write_json(output, "runtime.json", {"code_config_hashes": {p.name: sha(p.read_bytes()) for p in code_paths},
        "openai_api_calls": 0})
    (output / "request_log.jsonl").touch()
    budget = None
    result = {"stage": config["stage"], "status": "STOPPED_SETUP_OR_SOURCE_REVIEW_REQUIRED",
        "network_requests": 0, "discovered_article_ids": 0, "selected_article_id": None,
        "successful_details": 0, "preview_observations": 0, "canonical_build": False,
        "bulk_collection_ready": False, "pit_or_identity_promoted": False, "openai_api_calls": 0}
    try:
        binary = shutil.which("openssl")
        git_binary = Path("C:/Program Files/Git/usr/bin/openssl.exe")
        if not binary and git_binary.is_file():
            binary = str(git_binary)
        context, tls = prepare_tls(project, output / "tls_chain", openssl_binary=binary)
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname or tls["status"] != "VALIDATED":
            raise ValueError("STRICT_VALIDATED_TLS_REQUIRED")
        def factory(path, **options):
            options["interval"] = config["interval_seconds"]
            return transport_factory(path, opener=build_opener(NoRedirect(), HTTPSHandler(context=context)), **options)
        budget = RunBudget(output, config["max_requests"], config["max_seconds"], factory, clock)
        emit(json.dumps({"event": "DISCOVERY_STARTED", "ticker": ticker, "max_requests": 3}), flush=True)
        discovery = discover([{"ticker": ticker, "exchange": exchange}], config["published_start"],
            config["published_end"], output / "discovery", max_pages=1, max_requests=2,
            transport_factory=budget.transport, scope_evidence={"canonical_path": str(canonical), "sha256": sha(body)})
        result["discovered_article_ids"] = discovery["discovered_article_ids"]
        emit(json.dumps({"event": "DISCOVERY_SAVED", "article_ids": discovery["discovered_article_ids"]}), flush=True)
        if discovery["limitations"]:
            result["limitations"] = discovery["limitations"]
        else:
            articles = [json.loads(s) for s in (output / "discovery/discovered_articles.jsonl").read_text(encoding="utf-8").splitlines() if s]
            candidates = [a for a in articles if a["price_action_title_candidate"]]
            if config.get("require_known_article"):
                candidates = [a for a in candidates if a["provider_article_id"] == config["known_article_id"]]
            candidates.sort(key=lambda a: a["provider_article_id"] != config["known_article_id"])
            if not candidates:
                result["status"] = ("PARTIAL_KNOWN_ARTICLE_NOT_IN_ONE_PAGE" if config.get("require_known_article")
                    else "PARTIAL_NO_PRICE_ACTION_CANDIDATE_IN_ONE_PAGE")
            else:
                aid = candidates[0]["provider_article_id"]
                result["selected_article_id"] = aid
                emit(json.dumps({"event": "DETAIL_STARTED", "article_id": aid}), flush=True)
                detail = acquire_details(output / "discovery", [aid], output / "detail", transport_factory=budget.transport)
                result["successful_details"] = detail["successful_public_responses"]
                if detail["limitations"]:
                    result["limitations"] = detail["limitations"]
                elif detail["successful_public_responses"]:
                    parsed = parse_details(output / "detail", output / "parsed")
                    if config.get("expected_event_type") and (len(parsed["samples"]) != 1 or any(
                            s["fields"].get("event_type") != config["expected_event_type"] for s in parsed["samples"])):
                        raise ValueError("KNOWN_ARTICLE_EVENT_TYPE_REQUIRES_REVIEW")
                    result.update(status="PILOT_FINISHED_REVIEW_REQUIRED", preview_observations=parsed["observation_count"],
                        extraction_gate=parsed["extraction_gate"], parser_status=parsed["status"])
    except KeyboardInterrupt:
        result["status"] = "CANCELLED_BY_USER"
    except Exception as exc:
        # These adapters use fixed public forms; no keys, cookies or auth replies.
        result.update(error_type=type(exc).__name__, reason=str(exc))
    finally:
        result["network_requests"] = budget.count if budget else 0
        write_json(output, "result.json", result)
    return result


def seal(output, archive, *, artifact_type="hnx-pvs-local-known-event-pilot-v1"):
    files = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()}
    write_json(output, "manifest.json", {"artifact_type": artifact_type, "files": files,
        "classification": "PUBLIC_RAW_AND_EXTRACTION_PREVIEW_NOT_CANONICAL", "canonical_build": False})
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob("*")):
            if p.is_file(): z.write(p, p.relative_to(output).as_posix())
