"""Sequential, bounded HNX supplemental acquisition; never promotes research gates."""
from __future__ import annotations

import copy
import csv
from datetime import date
import json
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.parse import urlsplit

from .corporate_action_sources import PublicTransport, SourceLimitation, now, sha
from .hnx_announcement_discovery import discover_for_batch, GROUP
from .hnx_announcement_details import acquire_details
from .hnx_detail_parser import parse_details

CONFIG = Path(__file__).resolve().parents[3] / "configs/data/hnx_batch_v1.json"
REVIEWABLE_HTTP = {404, 410, 500, 502, 503, 504}
SYMBOL_ERROR_PREFIXES = ("HNX_DESKTOP_", "HNX_DISCLOSURE_", "UNSUPPORTED_CONTENT_TYPE", "RESPONSE_SIZE_LIMIT")


def reviewable_receipt(receipt):
    """Only explicit URL/server failures or typed timeouts; never an access boundary."""
    if (receipt.get("response_headers", {}).get("Retry-After") or receipt.get("error") == "SOURCE_ACCESS_LIMITATION"
            or receipt.get("status") in {401, 403, 429}):
        return False
    status = receipt.get("status")
    return ((status in REVIEWABLE_HTTP and receipt.get("error") == f"HTTP_{status}")
            or receipt.get("error_category") == "REQUEST_TIMEOUT" and status in REVIEWABLE_HTTP | {None, 200})


def state_artifacts(state):
    return [state["discovery"], *state["details"].values(), *state["parsed"].values(),
            *[issue.get("artifact") for issue in state.get("issues", [])]]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def verify_artifact(path, expected=None):
    path = Path(path).resolve()
    manifest = read(path / "manifest.json")
    if expected and manifest.get("artifact_type") not in expected:
        raise ValueError("UNSUPPORTED_BATCH_INPUT_ARTIFACT")
    for name, digest in manifest["files"].items():
        target = (path / name).resolve()
        if not target.is_relative_to(path) or sha(target.read_bytes()) != digest:
            raise ValueError("BATCH_INPUT_CHECKSUM_MISMATCH: " + name)
    return {"path": str(path), "manifest_sha256": sha((path / "manifest.json").read_bytes())}


class RunBudget:
    def __init__(self, output, max_requests, max_seconds, factory, clock):
        self.output, self.max_requests, self.max_seconds = output, max_requests, max_seconds
        self.factory, self.clock, self.started = factory, clock, clock()
        self.count, self.last, self.stopped_hosts, self.last_receipt = 0, 0.0, set(), None

    def check(self):
        if self.count >= self.max_requests:
            raise SourceLimitation("RUN_REQUEST_BUDGET_EXHAUSTED")
        if self.clock() - self.started >= self.max_seconds:
            raise SourceLimitation("RUN_TIME_BUDGET_EXHAUSTED")

    def transport(self, root, **kwargs):
        budget = self
        client = self.factory(root, **kwargs)
        if hasattr(client, "sleep"):
            original_sleep = client.sleep
            def bounded_sleep(seconds):
                original_sleep(seconds)
                budget.check()  # Do not start an HTTP request after the delay exhausts runtime.
            client.sleep = bounded_sleep
        class Shared:
            @property
            def requests(self):
                return client.requests

            def fetch(self, *args, **options):
                budget.check()
                budget.last_receipt = None  # Never classify a new failure using a previous ticker's receipt.
                client.last = budget.last
                client.stopped_hosts = budget.stopped_hosts
                before = len(client.requests)
                try:
                    result = client.fetch(*args, **options)
                    if result[1].get("response_headers", {}).get("Retry-After"):
                        client.stopped_hosts.add(urlsplit(result[1]["url"]).hostname)
                        result[1]["error"] = "SOURCE_ACCESS_LIMITATION"
                        raise SourceLimitation("SOURCE_ACCESS_LIMITATION: RETRY_AFTER; no retry")
                    return result
                except SourceLimitation as exc:
                    cause = exc.__cause__
                    if isinstance(cause, TimeoutError) or isinstance(cause, URLError) and isinstance(cause.reason, TimeoutError):
                        if len(client.requests) > before:
                            client.requests[-1]["error_category"] = "REQUEST_TIMEOUT"
                    raise
                except TimeoutError as exc:
                    if len(client.requests) > before:
                        client.requests[-1].update(error=str(exc), error_category="REQUEST_TIMEOUT")
                        if client.requests[-1].get("status") in {401, 403, 429}:
                            raise SourceLimitation(f"SOURCE_ACCESS_LIMITATION: HTTP {client.requests[-1]['status']}; body timeout; no retry") from exc
                    raise SourceLimitation("REQUEST_TIMEOUT: " + str(exc)) from exc
                finally:
                    budget.last = client.last
                    budget.stopped_hosts = client.stopped_hosts
                    for receipt in client.requests[before:]:
                        budget.count += 1
                        budget.last_receipt = receipt
                        with (budget.output / "request_log.jsonl").open("a", encoding="utf-8") as stream:
                            stream.write(json.dumps({"artifact": str(root), "receipt": receipt}, ensure_ascii=False) + "\n")
        return Shared()


def run_batch(canonical, output, *, tickers=None, exchanges=None, start=None, end=None, max_pages=None,
              max_requests=1000, max_seconds=3600, seed_discovery=None, seed_details=(), seed_batch=None, resume_from=None,
              dry_run=False, transport_factory=PublicTransport, clock=time.monotonic, progress=None):
    output = output.resolve()
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    if not 1 <= max_requests <= 1000 or not 1 <= max_seconds <= 21600:
        raise ValueError("INVALID_RUN_BUDGET")
    config = read(CONFIG)
    if config["interval_seconds"] != 2 or config["max_detail_requests_per_unit"] != 2:
        raise ValueError("BATCH_CONTRACT_REQUIRES_REVIEW")
    universe_bytes = canonical.read_bytes()
    universe = [json.loads(s) for s in universe_bytes.decode("utf-8").splitlines() if s]
    by_ticker = {r["ticker"]: r for r in universe}
    if len(by_ticker) != len(universe):
        raise ValueError("C8_V2_TICKER_NOT_UNIQUE")
    previous = None
    if resume_from:
        resume_from = resume_from.resolve()
        # Sealed runs are verified fully. Abrupt process kills use the append-only journal.
        if (resume_from / "manifest.json").exists():
            verify_artifact(resume_from, {"hnx-supplemental-batch-v1"})
        previous = read(resume_from / "plan.json")
        if seed_discovery or seed_details or seed_batch:
            raise ValueError("RESUME_CANNOT_ADD_NEW_SEEDS")
        if (resume_from / "result.json").exists() and not read(resume_from / "result.json")["resumable"]:
            raise ValueError("PREVIOUS_SOURCE_OR_PARSER_STOP_REQUIRES_REVIEW_NOT_AUTOMATIC_RETRY")
        if (resume_from / "request_log.jsonl").exists():
            for entry in lines(resume_from / "request_log.jsonl"):
                receipt = entry["receipt"]
                if (receipt.get("error") or receipt.get("status") not in {None, 200}) and not reviewable_receipt(receipt):
                    raise ValueError("PRIOR_SOURCE_FAILURE_REQUIRES_REVIEW_NOT_AUTOMATIC_RETRY")
        if tickers is None and exchanges is None:
            tickers = [s["ticker"] for s in previous["scopes"]]
    selected_exchanges = set(exchanges or ["HNX", "UPCOM"])
    if not selected_exchanges <= {"HNX", "UPCOM"}:
        raise ValueError("HNX_BATCH_ONLY_HNX_UPCOM")
    if tickers is not None and (len(set(tickers)) != len(tickers) or not tickers):
        raise ValueError("TICKERS_MUST_BE_DISTINCT")
    selected = [by_ticker[t] for t in tickers] if tickers is not None else universe
    if tickers and any(r["exchange"] not in selected_exchanges for r in selected):
        raise ValueError("TICKER_OUTSIDE_HNX_UPCOM_SCOPE")
    scopes = sorted([{"ticker": r["ticker"], "exchange": r["exchange"]} for r in selected if r["exchange"] in selected_exchanges], key=lambda s: s["ticker"])
    if not scopes:
        raise ValueError("EMPTY_BATCH_SCOPE")
    if any(not re.fullmatch(r"[A-Z0-9]{2,10}", s["ticker"]) for s in scopes):
        raise ValueError("INVALID_C8_SOURCE_TICKER")
    start = start or (previous["start"] if previous else config["published_start"])
    end = end or (previous["end"] if previous else config["published_end"])
    max_pages = max_pages or (previous["max_pages"] if previous else config["max_pages_per_ticker"])
    if (date.fromisoformat(start).isoformat() != start or date.fromisoformat(end).isoformat() != end
            or start > end or not 1 <= max_pages <= 50):
        raise ValueError("INVALID_PUBLICATION_DATES_OR_PAGE_LIMIT")
    code_files = [Path(__file__), *[Path(__file__).with_name(n) for n in
                  ["hnx_announcement_discovery.py", "hnx_announcement_details.py", "hnx_detail_parser.py",
                   "hnx_announcement_parser.py", "corporate_action_sources.py", "corporate_action_multisource.py", "corporate_actions_v1.py"]], CONFIG]
    contract = {"universe_sha256": sha(universe_bytes), "scopes": scopes, "start": start, "end": end,
                "max_pages": max_pages, "group": GROUP, "code_hashes": {p.name: sha(p.read_bytes()) for p in code_files}}
    fingerprint = sha(json.dumps(contract, sort_keys=True).encode())
    if previous and fingerprint != previous["contract_sha256"]:
        raise ValueError("RESUME_SCOPE_SOURCE_CODE_OR_CONTRACT_CHANGED_REQUIRES_REVIEW")
    plan = dict(contract, stage="HNX_SUPPLEMENTAL_BATCH_V1", contract_sha256=fingerprint,
                canonical_path=str(canonical.resolve()), universe_rows=len(universe), max_requests=max_requests,
                max_seconds=max_seconds, interval_seconds=2, resume_from=str(resume_from) if resume_from else None,
                scope_limit="CURRENT_C8_SOURCE_ASSIGNMENT_NOT_HISTORICAL_IDENTITY; ONE_NEWS_GROUP; PUBLICATION_DATE_WINDOW",
                canonical_build=False)
    states = {s["ticker"]: {"scope": s, "discovery": None, "details": {}, "parsed": {},
                            "handled": False, "quarantined": False, "issues": []} for s in scopes}
    cache = {}
    def ref(path, expected=None):
        key = str(Path(path).resolve())
        if key not in cache:
            cache[key] = verify_artifact(Path(key), expected)
        return cache[key]
    if previous:
        if (resume_from / "checkpoint.json").exists():
            checkpoint = read(resume_from / "checkpoint.json")
            if checkpoint["contract_sha256"] != fingerprint:
                raise ValueError("CHECKPOINT_CONTRACT_MISMATCH")
            states = checkpoint["states"]
        else:
            raw_journal = (resume_from / "progress.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
            for index, line in enumerate(raw_journal):
                try:
                    event = json.loads(line)
                except ValueError:
                    if index == len(raw_journal) - 1 and not line.endswith("\n"):
                        break
                    raise ValueError("CORRUPT_PROGRESS_JOURNAL")
                states[event["ticker"]] = event["state"]
        if set(states) != {s["ticker"] for s in scopes}:
            raise ValueError("CHECKPOINT_SCOPE_MISMATCH")
        for state in states.values():
            for stored in state_artifacts(state):
                if stored and ref(stored["path"]) != stored:
                    raise ValueError("CHECKPOINT_ARTIFACT_HASH_MISMATCH")
    if seed_batch:
        if seed_discovery or seed_details:
            raise ValueError("SEED_BATCH_CANNOT_MIX_OTHER_SEEDS")
        seed_ref = ref(seed_batch, {"hnx-supplemental-batch-v1"})
        source_plan = read(seed_batch / "plan.json")
        if (not read(seed_batch / "result.json")["resumable"]
                or any(source_plan[k] != contract[k] for k in contract if k != "scopes")):
            raise ValueError("SEED_BATCH_CONTRACT_OR_SOURCE_STOP_REQUIRES_REVIEW")
        seed_states = read(seed_batch / "checkpoint.json")["states"]
        for ticker, state in seed_states.items():
            if ticker in states:
                if state["scope"] != states[ticker]["scope"]:
                    raise ValueError("SEED_BATCH_SCOPE_MISMATCH")
                for stored in state_artifacts(state):
                    if stored and ref(stored["path"]) != stored:
                        raise ValueError("SEED_BATCH_ARTIFACT_HASH_MISMATCH")
                states[ticker] = copy.deepcopy(state)
        plan["seed_batch"] = seed_ref
    if seed_discovery:
        dref = ref(seed_discovery, {"hnx-disclosure-discovery-pilot-v1", "hnx-disclosure-discovery-v1"})
        seed_plan, seed_result = read(seed_discovery / "plan.json"), read(seed_discovery / "result.json")
        if (seed_plan["published_start"] != start or seed_plan["published_end"] != end or seed_plan["group"] != GROUP
                or seed_plan.get("scope_evidence", {}).get("sha256") != contract["universe_sha256"] or seed_result["limitations"]):
            raise ValueError("SEED_DISCOVERY_SCOPE_OR_CONTRACT_MISMATCH")
        for s in seed_plan["scopes"]:
            if s["ticker"] in states:
                if states[s["ticker"]]["scope"] != s:
                    raise ValueError("SEED_DISCOVERY_MARKET_MISMATCH")
                states[s["ticker"]]["discovery"] = dref
    for path in seed_details:
        dref = ref(path, {"hnx-discovered-detail-access-pilot-v1"})
        origin_plan = read(path / "plan.json")
        if read(path / "result.json").get("limitations"):
            raise ValueError("SEED_DETAIL_SOURCE_LIMITATION_REQUIRES_REVIEW")
        for row in lines(path / "detail_responses.jsonl"):
            ticker, aid = row["ticker_filter"], row["provider_article_id"]
            if ticker in states:
                if not states[ticker]["discovery"] or origin_plan["origin_manifest_sha256"] != states[ticker]["discovery"]["manifest_sha256"]:
                    raise ValueError("SEED_DETAIL_DISCOVERY_MISMATCH")
                states[ticker]["details"][aid] = dref
    if dry_run:
        return dict(plan, status="DRY_RUN", network_requests=0, scope_tickers=len(scopes),
                    cached_discovery_tickers=sum(s["discovery"] is not None for s in states.values()),
                    cached_detail_article_ids=sum(len(s["details"]) for s in states.values()))
    output.mkdir(parents=True, exist_ok=False)
    write(output / "plan.json", plan)
    (output / "request_log.jsonl").touch(); (output / "progress.jsonl").touch()
    budget = RunBudget(output, max_requests, max_seconds, transport_factory, clock)
    sequence = 0
    def work(kind):
        nonlocal sequence
        sequence += 1
        return output / "work" / (f"{sequence:05d}-" + kind)
    def record(ticker):
        with (output / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"ticker": ticker, "state": states[ticker], "at": now()}, ensure_ascii=False) + "\n")
    def quarantine(ticker, stage, reason, artifact=None):
        state = states[ticker]
        state["quarantined"], state["handled"] = True, False
        issue = {"stage": stage, "reason": reason, "artifact": artifact, "review_status": "PENDING"}
        if issue not in state.setdefault("issues", []):
            state["issues"].append(issue)
        record(ticker)
    # Persist inherited references too, so a second abrupt interruption loses no history.
    for ticker in states:
        if states[ticker]["discovery"] or states[ticker].get("quarantined"):
            record(ticker)
    def parse_unit(detail_ref):
        parsed_path = work("parsed")
        parsed_result = parse_details(Path(detail_ref["path"]), parsed_path)
        pref = ref(parsed_path, {"hnx-desktop-detail-offline-parse-v1"})
        for row in lines(Path(detail_ref["path"]) / "detail_responses.jsonl"):
            ticker, aid = row["ticker_filter"], row["provider_article_id"]
            if ticker in states and states[ticker]["details"].get(aid) == detail_ref:
                states[ticker]["parsed"][aid] = pref
                record(ticker)
        rejected = {r["provider_article_id"]: r["reason"] for r in parsed_result["rejected_articles"]}
        for row in lines(Path(detail_ref["path"]) / "detail_responses.jsonl"):
            ticker, aid = row["ticker_filter"], row["provider_article_id"]
            if ticker in states and aid in rejected and states[ticker]["details"].get(aid) == detail_ref:
                quarantine(ticker, "PARSE", "PARSER_REJECTED_ARTICLE_REQUIRES_REVIEW: " + aid + ": " + rejected[aid], pref)
    stop_reason, current_stage, current_ref, ticker = None, "INITIALIZE", None, None
    run_issues = []
    try:
        for scope in scopes:
            ticker = scope["ticker"]; state = states[ticker]
            if state["handled"] or state.get("quarantined"):
                continue
            current_stage, current_ref, ids = "DISCOVERY", None, []
            try:
                if not state["discovery"]:
                    budget.check()
                    path = work("discovery-" + ticker)
                    discovered = discover_for_batch(scope, start, end, path, max_pages=max_pages,
                                                    max_requests=max_pages + 1, transport_factory=budget.transport,
                                                    scope_evidence={"canonical_path": str(canonical.resolve()), "sha256": contract["universe_sha256"],
                                                                    "purpose": "SOURCE_WORK_ASSIGNMENT_NOT_HISTORICAL_IDENTITY_PROOF"})
                    current_ref = ref(path)
                    if discovered["limitations"]:
                        raise SourceLimitation(discovered["limitations"][0]["reason"])
                    state["discovery"] = current_ref; record(ticker)
                discovery_path = Path(state["discovery"]["path"])
                articles = [r for r in lines(discovery_path / "discovered_articles.jsonl")
                            if r["ticker_filter"] == ticker and r["price_action_title_candidate"]]
                ids = [r["provider_article_id"] for r in articles]
                for aid in ids:
                    if aid in state["details"] and aid not in state["parsed"]:
                        current_stage, current_ref = "PARSE", state["details"][aid]
                        parse_unit(current_ref)
                        if state.get("quarantined"):
                            break
                if not state.get("quarantined"):
                    pending = [aid for aid in ids if aid not in state["parsed"]]
                    for offset in range(0, len(pending), 2):
                        current_stage, current_ref = "DETAIL", None
                        budget.check()
                        chunk = pending[offset:offset + 2]; path = work("details-" + ticker)
                        acquired = acquire_details(discovery_path, chunk, path, transport_factory=budget.transport)
                        dref = ref(path); current_ref = dref
                        for row in lines(path / "detail_responses.jsonl"):
                            state["details"][row["provider_article_id"]] = dref
                        record(ticker)
                        if acquired["successful_public_responses"]:
                            current_stage = "PARSE"
                            parse_unit(dref)
                        if acquired["limitations"]:
                            current_stage, current_ref = "DETAIL", dref
                            raise SourceLimitation(acquired["limitations"][0]["reason"])
                        if state.get("quarantined"):
                            break
                if not state.get("quarantined"):
                    state["handled"] = set(ids) <= set(state["parsed"]); record(ticker)
            except SourceLimitation as exc:
                reason = str(exc)
                receipt = budget.last_receipt or {}
                url_failure = (reviewable_receipt(receipt)
                               and (reason.startswith("REQUEST_TIMEOUT:") or reason.startswith("SOURCE_ACCESS_LIMITATION:")))
                if not budget.stopped_hosts and (reason.startswith(SYMBOL_ERROR_PREFIXES) or url_failure):
                    quarantine(ticker, current_stage, reason, current_ref)
                else:
                    raise
            if progress:
                progress({"ticker": ticker, "handled": state["handled"], "quarantined": state.get("quarantined", False),
                          "candidate_articles": len(ids), "physical_requests": budget.count})
    except KeyboardInterrupt:
        stop_reason = "INTERRUPTED_BY_USER"
    except (SourceLimitation, ValueError, OSError) as exc:
        stop_reason = str(exc)
        if stop_reason not in {"RUN_REQUEST_BUDGET_EXHAUSTED", "RUN_TIME_BUDGET_EXHAUSTED"}:
            run_issues.append({"ticker": ticker or "", "stage": current_stage, "reason": stop_reason,
                               "artifact": current_ref, "review_status": "PENDING", "action": "STOP_RUN"})
    # A new self-contained observation bundle; child artifacts and all inputs stay immutable.
    parsed_refs = {p["path"]: p for s in states.values() for p in s["parsed"].values()}
    observations, review_rows, seen_reviews = {}, [], set()
    for path in parsed_refs:
        parsed_path = Path(path)
        for obs in lines(parsed_path / "observations.jsonl"):
            obs = copy.deepcopy(obs)
            if obs["observation_id"] in observations:
                continue
            aid = obs["source_timing"]["provider_article_id"]
            ticker = obs["fields"]["ticker"]["normalized_value"]
            if ticker not in states or aid not in states[ticker]["parsed"]:
                continue
            remap = {}
            for evidence in obs["source_evidence"]:
                old_path = evidence["path"]
                new_path = "raw/" + ticker + "/" + aid + "/" + evidence["evidence_role"] + ".bin"
                destination = output / new_path; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((parsed_path / old_path).read_bytes())
                remap[old_path] = new_path; evidence["path"] = new_path
            obs["source_timing"]["raw_path"] = remap[obs["source_timing"]["raw_path"]]
            observations[obs["observation_id"]] = obs
        with (parsed_path / "review_queue.csv").open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["ticker"] not in states or row["provider_article_id"] not in states[row["ticker"]]["parsed"]:
                    continue
                key = tuple(row.values())
                if key not in seen_reviews:
                    review_rows.append(row); seen_reviews.add(key)
    index_partial, empty_queries = [], []
    for ticker, state in states.items():
        if state["discovery"]:
            checks = read(Path(state["discovery"]["path"]) / "result.json")["checks"]
            own_checks = [c for c in checks if c["ticker"] == ticker]
            if not any(c["query_list_exhausted_within_filter"] for c in own_checks):
                index_partial.append(ticker)
            if any(c["reported_query_total"] == 0 and c["query_list_exhausted_within_filter"] for c in own_checks):
                empty_queries.append(ticker)
                review_rows.append({"provider_article_id": "", "ticker": ticker, "observation_id": "",
                                    "field": "__query_scope__", "reason": "EMPTY_QUERY_NOT_HISTORICAL_COVERAGE", "severity": "REVIEW"})
    with (output / "observations.jsonl").open("x", encoding="utf-8") as stream:
        for obs in observations.values():
            stream.write(json.dumps(obs, ensure_ascii=False) + "\n")
    with (output / "review_queue.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["provider_article_id", "ticker", "observation_id", "field", "reason", "severity"])
        writer.writeheader(); writer.writerows(review_rows)
    collection_issues = [dict(issue, ticker=t, action="SKIP_TICKER_KEEP_EVIDENCE")
                         for t, s in states.items() for issue in s.get("issues", [])] + run_issues
    with (output / "collection_issues.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["ticker", "stage", "reason", "artifact_path", "artifact_manifest_sha256", "review_status", "action"])
        writer.writeheader()
        for issue in collection_issues:
            artifact = issue["artifact"] or {}
            writer.writerow({**{k: v for k, v in issue.items() if k != "artifact"},
                             "artifact_path": artifact.get("path", ""), "artifact_manifest_sha256": artifact.get("manifest_sha256", "")})
    write(output / "checkpoint.json", {"contract_sha256": fingerprint, "states": states})
    resumable = stop_reason is None or stop_reason in {"RUN_REQUEST_BUDGET_EXHAUSTED", "RUN_TIME_BUDGET_EXHAUSTED", "INTERRUPTED_BY_USER"}
    quarantined = [t for t, s in states.items() if s.get("quarantined")]
    result = {"status": ("COLLECTED_WITH_QUARANTINED_TICKERS" if quarantined else "COLLECTED_WITH_REVIEWS") if stop_reason is None else "PARTIAL" if resumable else "STOPPED_REVIEW_REQUIRED",
              "stop_reason": stop_reason, "resumable": resumable, "network_requests_this_run": budget.count,
              "scope_tickers": len(states), "handled_tickers": sum(s["handled"] for s in states.values()),
              "pending_tickers": [t for t, s in states.items() if not s["handled"] and not s.get("quarantined")],
              "quarantined_tickers": quarantined, "quarantined_count": len(quarantined), "collection_issue_rows": len(collection_issues),
              "discovery_page_limit_tickers": index_partial, "empty_query_tickers": empty_queries, "observation_count": len(observations),
              "review_queue_rows": len(review_rows), "accepted_publication_timestamps": 0,
              "source_history_coverage": "INCOMPLETE_NOT_CERTIFIED", "canonical_build": False,
              "pit_status": "NOT_PROMOTED", "historical_identity": "NOT_CERTIFIED",
              "limits": ["CORPORATE_NEWS only", "Publication-list dates, not ex-date window", "Title candidates only; all list rows preserved",
                         "Current C8 HNX/UPCOM source assignment does not prove historical identity or cover transferred/delisted issuers"]}
    write(output / "result.json", result)
    files = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    write(output / "manifest.json", {"artifact_type": "hnx-supplemental-batch-v1", "created_at": now(),
                                     "contract_sha256": fingerprint, "files": files})
    return result
