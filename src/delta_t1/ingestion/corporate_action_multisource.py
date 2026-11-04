"""Version 1.2 field reconciliation; event evidence and PIT timing are independent."""
from __future__ import annotations

import copy
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from delta_t1.contracts import coerce, validate_rows
from . import corporate_actions_v1 as base
from . import corporate_action_collection as legacy
from .corporate_action_sources import PublicTransport, SourceLimitation, hnx_market_context, now, parse_hnx, parse_vsdc, sha
from .corporate_action_hose import collect_hose, parse_hose_document

VERSION = "1.2.0"
DATA_FIELDS = ("ticker", "exchange", "isin", "event_type", "announcement_date", "ex_date", "record_date", "payment_date", "currency", *base.NUMBERS)
CRITICAL = ("ticker", "exchange", "event_type", "ex_date")
QUEUE_FIELDS = ("review_id", "event_id", "ticker", "conflicting_field", "review_reason", "observations",
                "recommended_check", "review_status", "chosen_observation_id", "reviewed_by", "reviewed_at", "review_decision", "review_note")
EDITABLE = {"review_status", "chosen_observation_id", "reviewed_by", "reviewed_at", "review_decision", "review_note"}
SOURCES = ("VSDC", "HNX_LISTED", "HNX_UPCOM", "HOSE", "ISSUER_IR", "CAFEF", "VNDIRECT", "VENDOR")


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def observation(row, observed_at=None, manual=False):
    """One source/component observation; no source value is overwritten by another."""
    if row.get("is_example") is True:
        raise ValueError("EXAMPLE_INPUT_NOT_PRODUCTION: replace example with real evidence")
    if "observation_id" in row and isinstance(row.get("fields"), dict):
        # Reparse enriches an existing observation, rather than acquiring it again.
        # In particular, never reconstruct its receipts or original timing fields.
        if manual or observed_at is not None:
            raise ValueError("NORMALIZED_OBSERVATION: acquisition overrides are not allowed")
        return copy.deepcopy(row)
    source_type = row.get("source_type", row.get("primary_source_type"))
    url = row.get("source_url", row.get("primary_source_url"))
    observed_at = (observed_at or now()) if manual else row.get("observed_at") or observed_at or next((e.get("fetched_at") for e in row.get("evidence", []) if e.get("fetched_at")), None)
    observed_at = observed_at or now()
    base.timestamp(observed_at)
    published_raw = row.get("source_published_at", row.get("primary_source_published_at"))
    published = None
    if published_raw:
        try:
            published = base.timestamp(published_raw).isoformat()
            if base.timestamp(published) > base.timestamp(observed_at):
                published = None
        except (ValueError, TypeError):
            pass
    # Calendar postedDate and unzoned update text are not publication evidence.
    if row.get("available_at_evidence") in {"FIRST_OBSERVED_AT_ONLY", "LATEST_REQUIRED_FIELD_FIRST_OBSERVED_AT"}:
        published = None
    timing = row.get("source_timing")
    if timing is not None and (timing.get("semantic_label") != "PUBLICATION"
                               or timing.get("parse_status") != "VALID"):
        published = None
    if "fields" in row and isinstance(row["fields"], dict) and not row.get("values"):
        fields = dict(row["fields"])
    else:
        values = row.get("values", {k: row.get(k) for k in DATA_FIELDS})
        unknown = set(values) - set(DATA_FIELDS)
        if unknown:
            raise ValueError("unknown observation fields: " + ",".join(sorted(unknown)))
        fields = {}
        for field, raw in values.items():
            if raw is None or raw == "":
                continue
            try:
                if field in base.NUMBERS:
                    value = base.number(str(raw), field, row.get("ratio_semantics", ""))
                elif field == "isin":
                    value = str(raw).strip()
                else:
                    value = coerce(raw, base.schema(base.TABLE)["fields"][field])
                fields[field] = dict(raw_value=row.get("raw_field_values", {}).get(field) or raw,
                                     normalization_input=raw, normalized_value=value, parse_status="VALID")
            except (ValueError, TypeError, OverflowError):
                fields[field] = dict(raw_value=raw, normalized_value=None, parse_status="INVALID")
    text = row.get("raw_terms", "")
    canonical_type = "VENDOR" if source_type in {"CAFEF", "VNDIRECT"} else source_type
    authority = base.authoritative_url(canonical_type, url) and bool(text.strip())
    stable = {"source_type": source_type, "url": url, "fields": fields, "raw_terms": text,
              "event_reference": row.get("event_reference"), "revision_of": row.get("revision_of", row.get("revision_reference_urls", []))}
    return dict(observation_id="OBS-" + sha(encode(stable).encode())[:24], source_type=source_type,
                source_url=url, source_hash=row.get("source_hash") or sha(text.encode()), source_hash_basis="RESPONSE_BYTES" if row.get("source_hash") else "SUPPLIED_TEXT_ONLY",
                source_published_at=published, source_published_at_raw=published_raw,
                source_timing=row.get("source_timing"), observed_at=observed_at,
                raw_terms=text, fields=fields, authority=authority, manual_input=manual,
                parser=row.get("parser", "partial-field-input-v1"), source_evidence=row.get("evidence", []),
                event_reference=row.get("event_reference"), match_evidence=row.get("match_evidence"),
                revision_of=stable["revision_of"], revision_status=row.get("revision_status", "ORIGINAL"),
                revision_number=row.get("revision_number"), parser_issues=row.get("parser_issues", []))


def value(obs, field):
    entry = obs["fields"].get(field, {})
    return entry.get("normalized_value") if entry.get("parse_status") == "VALID" else None


def group_observations(observations):
    unique = {o["observation_id"]: o for o in observations}
    rows = list(unique.values())
    parents = list(range(len(rows)))
    def find(i):
        while parents[i] != i:
            i = parents[i]
        return i
    for i, a in enumerate(rows):
        for j in range(i):
            b = rows[j]
            if any(value(a, k) != value(b, k) for k in ("ticker", "exchange", "event_type")):
                continue
            explicit = a.get("event_reference") and a.get("event_reference") == b.get("event_reference")
            same_record = value(a, "record_date") and value(a, "record_date") == value(b, "record_date")
            refs = a.get("revision_of", []) + b.get("revision_of", [])
            revision_link = a["source_url"] in refs or b["source_url"] in refs
            # Exact ex-date alone is insufficient. Context and overlapping terms must agree.
            overlaps = [k for k in base.NUMBERS if value(a, k) is not None and value(b, k) is not None]
            same_ex_context = (value(a, "ex_date") and value(a, "ex_date") == value(b, "ex_date") and explicit
                               and overlaps and all(value(a, k) == value(b, k) for k in overlaps))
            if explicit or same_record or same_ex_context or revision_link:
                parents[find(i)] = find(j)
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[find(i)].append(row)
    return list(groups.values())


def review_template(event_id, ticker, field, reason, observations):
    return dict(review_id="REV-" + sha(encode([event_id, field, reason]).encode())[:20], event_id=event_id,
                ticker=ticker or "", conflicting_field=field, review_reason=reason,
                observations=encode(observations), recommended_check="Đối chiếu đúng field và source; USE_OBSERVATION chọn observation ID. Thiếu evidence thì bổ sung run mới; PIT warning không sửa terms.",
                review_status="PENDING", chosen_observation_id="", reviewed_by="", reviewed_at="", review_decision="", review_note="")


def reconcile(observations, scope, created_at, choices=None):
    events, queue = [], []
    choices = choices or {}
    for group in group_observations(observations):
        event_id = "CAM-" + sha(encode(sorted(o["observation_id"] for o in group)).encode())[:24]
        ticker = next((value(o, "ticker") for o in group if value(o, "ticker")), "")
        revisions = [o for o in group if o["revision_status"] != "ORIGINAL" or o["revision_of"]]
        active, revision_choice = group, None
        if revisions:
            q = review_template(event_id, ticker, "__revision__", "REVISION_OR_CORRECTION_DETECTED", group)
            queue.append(q)
            decision = choices.get(q["review_id"], {})
            chosen = next((o for o in revisions if o["observation_id"] == decision.get("chosen_observation_id")), None)
            linked = chosen and chosen["authority"] and any(o["source_url"] in chosen["revision_of"] or o["observation_id"] in chosen["revision_of"] for o in group if o is not chosen)
            if chosen:
                ancestors, pending = set(), list(chosen["revision_of"])
                while pending:
                    reference = pending.pop()
                    for prior in group:
                        if reference in {prior["source_url"], prior["observation_id"]} and prior["observation_id"] not in ancestors:
                            ancestors.add(prior["observation_id"])
                            pending.extend(prior["revision_of"])
                linked = linked and chosen["observation_id"] not in ancestors and all(o is chosen or o["observation_id"] in ancestors for o in revisions)
            if decision.get("review_decision") == "USE_REVISION" and decision.get("review_status") == "APPROVED" and linked:
                active, revision_choice = [chosen], chosen["observation_id"]
        fields, provenance, issues = {}, {}, []
        manually_verified = False
        for field in DATA_FIELDS:
            entries = []
            for obs in active:
                if field in obs["fields"]:
                    entries.append(dict(obs["fields"][field], observation_id=obs["observation_id"], source_type=obs["source_type"],
                                        source_url=obs["source_url"], source_hash=obs["source_hash"], authority=obs["authority"],
                                        source_published_at=obs["source_published_at"], observed_at=obs["observed_at"], manual_input=obs["manual_input"]))
            if not entries:
                continue
            normalized = {encode(e["normalized_value"]) for e in entries if e["parse_status"] == "VALID"}
            reason = ("FIELD_CONFLICT" if len(normalized) > 1 or any(e["parse_status"] != "VALID" for e in entries)
                      else "SOURCE_AUTHORITY_UNCLEAR" if not any(e["authority"] for e in entries)
                      else "MANUAL_EVIDENCE_INPUT" if all(e["manual_input"] for e in entries if e["authority"])
                      else None)
            selected = [e for e in entries if e["authority"] and e["parse_status"] == "VALID" and not e["manual_input"]] if reason is None else []
            q = review_template(event_id, ticker, field, reason, entries) if reason else None
            if q:
                queue.append(q)
                decision = choices.get(q["review_id"], {})
                picked = [e for e in entries if e["observation_id"] == decision.get("chosen_observation_id") and e["authority"] and e["parse_status"] == "VALID"]
                if decision.get("review_status") == "APPROVED" and decision.get("review_decision") == "USE_OBSERVATION" and len(picked) == 1:
                    selected, manually_verified = picked, True
            fields[field] = selected[0]["normalized_value"] if selected else next((e["normalized_value"] for e in entries if e["parse_status"] == "VALID"), None)
            provenance[field] = dict(status="VERIFIED" if selected else "UNRESOLVED", value=fields[field],
                                     selected_observation_ids=[e["observation_id"] for e in selected], observations=entries,
                                     reconciliation_rule="SIGNED_FIELD_SELECTION_V1" if q and selected else "NORMALIZED_MATCH_OR_COMPLETION_V1" if selected else "NO_AUTOMATIC_SOURCE_PRIORITY_V1")
            if not selected and field != "announcement_date":
                issues.append(dict(field=field, reason=reason))
        kind = fields.get("event_type")
        required = (*CRITICAL, *base.TERMS.get(kind, ()))
        for field in required:
            if not fields.get(field) and fields.get(field) != 0:
                reason = "MISSING_EX_DATE" if field == "ex_date" else "MISSING_REQUIRED_TERM"
                issues.append(dict(field=field, reason=reason))
                queue.append(review_template(event_id, ticker, field, reason, []))
        if kind not in base.TERMS or kind == "OTHER":
            issues.append(dict(field="event_type", reason="AMBIGUOUS_EVENT_TYPE"))
            queue.append(review_template(event_id, ticker, "event_type", "AMBIGUOUS_EVENT_TYPE", active))
        for field in base.NUMBERS:
            if fields.get(field) is not None and field not in base.TERMS.get(kind, ()):
                issues.append(dict(field=field, reason="MIXED_EVENT_AMBIGUITY"))
                queue.append(review_template(event_id, ticker, field, "MIXED_EVENT_AMBIGUITY", provenance[field]["observations"]))
        for field in base.RATIOS:
            if fields.get(field) is not None and fields[field] > 1:
                q = review_template(event_id, ticker, field, "RATIO_PARSE_AMBIGUITY", provenance[field]["observations"])
                queue.append(q)
                decision = choices.get(q["review_id"], {})
                if not (decision.get("review_status") == "APPROVED" and decision.get("review_decision") == "USE_OBSERVATION" and decision.get("chosen_observation_id") in provenance[field]["selected_observation_ids"]):
                    issues.append(dict(field=field, reason="RATIO_PARSE_AMBIGUITY"))
                else:
                    manually_verified = True
        if kind in {"STOCK_SPLIT", "REVERSE_SPLIT"} and fields.get("split_multiplier") is not None:
            if kind == "STOCK_SPLIT" and fields["split_multiplier"] <= 1 or kind == "REVERSE_SPLIT" and fields["split_multiplier"] >= 1:
                issues.append(dict(field="split_multiplier", reason="SPLIT_DIRECTION"))
        for before, after in (("ex_date", "record_date"), ("record_date", "payment_date")):
            if fields.get(before) and fields.get(after) and fields[before] > fields[after]:
                issues.append(dict(field=before, reason="DATE_ORDER"))
        identity = legacy.resolve_identity(fields, scope)
        identity_ok = identity.get("identity_status") == "VERIFIED" and all(provenance.get(f, {}).get("status", "VERIFIED") == "VERIFIED" for f in ("ticker", "exchange", "isin"))
        if not identity_ok:
            identity = dict(identity, identity_status="UNVERIFIED")
            issues.append(dict(field="security_id", reason="IDENTITY_CONFLICT"))
            queue.append(review_template(event_id, ticker, "security_id", "IDENTITY_CONFLICT", [{"scope": scope, "isin": fields.get("isin")}]))
        else:
            provenance["security_id"] = dict(status="VERIFIED", value=identity["security_id"], selected_observation_ids=[],
                                              reconciliation_rule="REVIEWED_HISTORICAL_INTERVAL_MAPPING_V1", observations=[{"source_type": "REVIEWED_IDENTITY_SCOPE", "source_url": identity["identity_source_url"], "observed_value": identity["security_id"]}])
        source_counts = Counter(o["source_type"] for o in active)
        ambiguous = any(n > 1 for n in source_counts.values()) and not revision_choice
        if ambiguous:
            issues.append(dict(field="__event_match__", reason="EVENT_MATCH_AMBIGUOUS"))
            queue.append(review_template(event_id, ticker, "__event_match__", "EVENT_MATCH_AMBIGUOUS", active))
        if revisions and not revision_choice:
            issues.append(dict(field="__revision__", reason="REVISION_OR_CORRECTION_DETECTED"))
        timing, knowledge = (["announcement_date"] if provenance.get("announcement_date", {}).get("status") == "UNRESOLVED" else []), []
        for field in required:
            p = provenance.get(field, {})
            selected = [e for e in p.get("observations", []) if e.get("observation_id") in p.get("selected_observation_ids", [])]
            dated = [e for e in selected if e["source_published_at"]]
            if dated:
                knowledge.append(min((e["source_published_at"] for e in dated), key=base.timestamp))
            elif selected:
                knowledge.append(min((e["observed_at"] for e in selected), key=base.timestamp))
                timing.append(field)
                queue.append(review_template(event_id, ticker, field, "PIT_TIMESTAMP_INCOMPLETE", selected))
            else:
                timing.append(field)
        available = max(knowledge, key=base.timestamp) if knowledge else max((o["observed_at"] for o in active), key=base.timestamp)
        rejected = any(d.get("event_id") == event_id and d.get("review_status") == "REJECTED" and d.get("review_decision") == "REJECT_EVENT" for d in choices.values())
        data_status = "REJECTED" if rejected else "PARTIAL" if issues else "VERIFIED"
        status = "REJECTED" if rejected else "MANUAL_REVIEW" if issues else "MANUALLY_VERIFIED" if manually_verified or revision_choice else "AUTO_VERIFIED"
        group_id = "CAG-" + sha(encode([identity.get("security_id"), fields.get("ticker"), fields.get("exchange"), fields.get("ex_date") or fields.get("record_date")]).encode())[:24]
        events.append(dict(event_id=event_id, event_group_id=group_id, values=fields, identity=identity,
                           event_data_verification=data_status, pit_timing_verification="PARTIAL" if timing else "COMPLETE",
                           available_at=available, timing_incomplete_fields=sorted(set(timing)), verification_status=status,
                           matching_status="AMBIGUOUS" if ambiguous else "UNIQUE", field_provenance=provenance,
                           issues=issues, observation_ids=[o["observation_id"] for o in group], effective_revision_id=revision_choice,
                           revision_lineage={"observations": [{"observation_id": o["observation_id"], "source_url": o["source_url"], "revision_of": o["revision_of"], "revision_number": o["revision_number"]} for o in group],
                                             "effective_observation_id": revision_choice, "rule": "SIGNED_EXPLICIT_REVISION_SELECTION_ONLY"},
                           created_at=created_at))
    # Keep referenced originals fail-closed even if a correction changes component type.
    effective = {i for e in events if e["event_data_verification"] == "VERIFIED" and e["effective_revision_id"] for i in e["observation_ids"]}
    for revision in [o for o in observations if o["revision_status"] != "ORIGINAL" or o["revision_of"]]:
        if revision["observation_id"] in effective:
            continue
        targets = {p["observation_id"] for p in observations if p is not revision and (p["source_url"] in revision["revision_of"] or p["observation_id"] in revision["revision_of"])}
        for event in events:
            if (targets.intersection(event["observation_ids"]) or not targets and value(revision, "ticker") == event["values"].get("ticker") and value(revision, "exchange") == event["values"].get("exchange")):
                event["event_data_verification"], event["verification_status"] = "PARTIAL", "MANUAL_REVIEW"
                event["issues"].append(dict(field="__revision__", reason="REVISION_OR_CORRECTION_DETECTED"))
                queue.append(review_template(event["event_id"], event["values"].get("ticker"), "__revision__", "REVISION_OR_CORRECTION_DETECTED", [revision]))
    duplicate_keys, mixed_groups = defaultdict(list), defaultdict(list)
    for event in events:
        e = event["values"]
        if e.get("ex_date"):
            duplicate_keys[(e.get("ticker"), e.get("exchange"), e["ex_date"], e.get("event_type"))].append(event)
        mixed_groups[event["event_group_id"]].append(event)
    for members in duplicate_keys.values():
        if len(members) > 1:
            for e in members:
                e.update(event_data_verification="PARTIAL", verification_status="MANUAL_REVIEW", matching_status="AMBIGUOUS")
                e["issues"].append(dict(field="__event_match__", reason="EVENT_MATCH_AMBIGUOUS"))
                queue.append(review_template(e["event_id"], e["values"].get("ticker"), "__event_match__", "EVENT_MATCH_AMBIGUOUS", e["observation_ids"]))
    for members in mixed_groups.values():
        if len({e["values"].get("event_type") for e in members}) > 1 and any(e["event_data_verification"] != "VERIFIED" for e in members):
            for e in members:
                e.update(event_data_verification="PARTIAL", verification_status="MANUAL_REVIEW")
                e["issues"].append(dict(field="__event_group__", reason="MIXED_EVENT_AMBIGUITY"))
                queue.append(review_template(e["event_id"], e["values"].get("ticker"), "__event_group__", "MIXED_EVENT_AMBIGUITY", e["observation_ids"]))
    return events, list({r["review_id"]: r for r in queue}.values())


def source_matrix(observations):
    rows = []
    for name in SOURCES:
        own = [o for o in observations if ("HNX_UPCOM" if o["source_type"] == "HNX" and value(o, "exchange") == "UPCOM" else "HNX_LISTED" if o["source_type"] == "HNX" else o["source_type"]) == name]
        rows.append(dict(source=name, observations=len(own), **{f: sum(value(o, f) is not None and (f != "event_type" or value(o, f) != "OTHER") for o in own) for f in ("event_type", "ex_date", "record_date", "cash_dividend_per_share", "stock_dividend_ratio", "bonus_ratio", "rights_ratio", "rights_subscription_price")},
                         publication_time=sum(o["source_published_at"] is not None for o in own)))
    return rows


def finalize(root, observations, scope, plan):
    events, queue = reconcile(observations, scope, plan["created_at"])
    inside = [e for e in events if not e["values"].get("ex_date") or plan["start"] <= e["values"]["ex_date"] <= plan["end"]]
    inside_ids = {e["event_id"] for e in inside}
    base.write_new(root / "observations.jsonl", legacy.dump_jsonl(observations))
    base.write_new(root / "events.jsonl", legacy.dump_jsonl(inside))
    base.write_new(root / "out_of_window.jsonl", legacy.dump_jsonl([e for e in events if e not in inside]))
    base.write_new(root / "field_review_queue.csv", base.csv_text(QUEUE_FIELDS, [r for r in queue if r["event_id"] in inside_ids]))
    matrix = source_matrix(observations)
    base.write_new(root / "source_completeness_matrix.csv", base.csv_text(tuple(matrix[0]), matrix))
    return inside


def manifest(root, extra):
    extra.setdefault("artifact_type", "corporate-action-multisource")
    extra.update(schema_version=VERSION, q11_status="STILL_OPEN", q17_status="NOT_TOUCHED",
                 price_return_adjusted_series="NOT_BUILT", code_sha256=base.digest(Path(__file__)),
                 code_hashes={name: base.digest(Path(__file__).with_name(name)) for name in ("corporate_action_multisource.py", "corporate_action_sources.py", "corporate_action_collection.py", "corporate_action_hose.py", "corporate_actions_v1.py")},
                 schema_sha256=base.digest(Path(__file__).parents[1] / "schemas/corporate_actions_multisource_v1.json"),
                 files={p.relative_to(root).as_posix(): base.digest(p) for p in sorted(root.rglob("*")) if p.is_file()})
    base.write_new(root / "manifest.json", base.json_text(extra))
    return extra


def collect(scope_path, output, start, end, max_pages=2, max_details=10, max_requests=30, sources=("VSDC", "HNX", "HOSE"),
            manual_input=None, dry_run=False, transport_factory=PublicTransport, transport_options=None, field_input=None):
    if output.exists():
        raise ValueError("OUTPUT_EXISTS")
    if not set(sources) <= {"VSDC", "HNX", "HOSE"}:
        raise ValueError("unsupported multi-source adapter")
    scope = legacy.load_scope(scope_path)
    plan = dict(work_unit="UPGRADE_CORPORATE_ACTIONS_V1_MULTI_SOURCE_COMPLETION", created_at=now(), start=start, end=end, scope_sha256=base.digest(scope_path), sources=list(sources),
                max_pages=max_pages, max_details=max_details, max_requests=max_requests, transport_options=transport_options or {},
                source_request_scope=[(source, s["ticker"]) for s in scope for source in sources if source == "VSDC" or source == "HNX" and s["exchange"] in {"HNX", "UPCOM"} or source == "HOSE" and s["exchange"] == "HOSE"])
    # Reuse existing source collection/validation; preserve its immutable 1.1 child run.
    if dry_run:
        return legacy.collect(scope_path, output, start, end, max_pages, max_details, max_requests, [s for s in sources if s != "HOSE"], dry_run=True) | dict(schema_version=VERSION, sources=list(sources), work_unit=plan["work_unit"])
    output.mkdir(parents=True, exist_ok=False)
    child = output / "source_collection_v1_1"
    plan["source_archive_child"] = "source_collection_v1_1"
    legacy.collect(scope_path, child, start, end, max_pages, max_details, max_requests,
                   [s for s in sources if s != "HOSE"], manual_input, transport_factory=transport_factory, transport_options=transport_options)
    shutil.copyfile(child / "scope.csv", output / "scope.csv")
    raw = legacy.read_jsonl(child / "raw_candidates.jsonl")
    observations = []
    for row in raw:
        row = copy.deepcopy(row)
        for evidence in row.get("evidence", []):
            if evidence.get("path"):
                evidence["path"] = "source_collection_v1_1/" + evidence["path"]
        observations.append(observation(row, manual=row.get("parser") == "manual-input-v1"))
    checks = json.loads((child / "source_checks.json").read_text(encoding="utf-8"))
    requests = json.loads((child / "requests.json").read_text(encoding="utf-8"))
    remaining = max_requests - len(requests)
    client = transport_factory(output, max_requests=max(1, remaining), **(transport_options or {}))
    if "HOSE" in sources:
        for ticker in dict.fromkeys(s["ticker"] for s in scope if s["exchange"] == "HOSE"):
            try:
                if remaining <= 0:
                    raise SourceLimitation("REQUEST_BUDGET_EXHAUSTED")
                rows, check = collect_hose(client, ticker, max_pages, min(max_details, 20))
                checks["checks"].append(check)
                observations.extend(observation(r) for r in rows)
            except SourceLimitation as exc:
                checks["limitations"].append(dict(ticker=ticker, source="HOSE", reason=str(exc)))
    if field_input:
        shutil.copyfile(field_input, output / "field_input.jsonl")
        for row in legacy.read_jsonl(output / "field_input.jsonl"):
            if row.get("document_url"):
                if len(client.requests) >= remaining:
                    checks["limitations"].append(dict(source="HOSE", reason="REQUEST_BUDGET_EXHAUSTED"))
                    continue
                try:
                    data, evidence = client.fetch(row["document_url"], binary=True)
                    observations.extend(observation(r) for r in parse_hose_document(data, evidence, row["ticker"]))
                except SourceLimitation as exc:
                    checks["limitations"].append(dict(source="HOSE", url=row["document_url"], reason=str(exc)))
            else:
                observations.append(observation(row, manual=True))
    base.write_new(output / "plan.json", base.json_text(plan))
    base.write_new(output / "source_checks.json", base.json_text(checks))
    base.write_new(output / "requests.json", base.json_text(requests + client.requests))
    events = finalize(output, observations, scope, plan)
    return manifest(output, dict(status="PARTIAL", network_requests=len(requests) + len(client.requests), event_count=len(events), observation_count=len(observations)))


def load(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if m.get("schema_version") != VERSION or m.get("artifact_type") != "corporate-action-multisource":
        raise ValueError("unsupported multi-source artifact")
    for name, expected in m["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or base.digest(path) != expected:
            raise ValueError("MULTI_SOURCE_CHECKSUM_MISMATCH: " + name)
    observations = legacy.read_jsonl(root / "observations.jsonl")
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    return observations, legacy.load_scope(root / "scope.csv"), plan


def load_choices(root, reviews=None):
    observations, scope, plan = load(root)
    initial, queue = reconcile(observations, scope, plan["created_at"])
    allowed = {r["review_id"]: r for r in queue}
    choices = {}
    if reviews:
        for row in base.read_csv(reviews, QUEUE_FIELDS):
            key = row["review_id"]
            if key not in allowed or key in choices or any(str(allowed[key][f] or "") != row[f] for f in QUEUE_FIELDS if f not in EDITABLE):
                raise ValueError("FIELD_REVIEW_EVIDENCE_CHANGED_OR_UNKNOWN_ID")
            if row["review_status"] not in {"PENDING", "APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"}:
                raise ValueError("invalid field review status")
            if row["review_status"] in {"APPROVED", "REJECTED"}:
                if not all(row[k].strip() for k in ("reviewed_by", "reviewed_at", "review_decision", "review_note")) or base.timestamp(row["reviewed_at"]) < max([base.timestamp(plan["created_at"]), *[base.timestamp(o["observed_at"]) for o in observations]]):
                    raise ValueError("signed field decision and actual review time required")
                if row["review_decision"] not in {"USE_OBSERVATION", "USE_REVISION", "ACKNOWLEDGE_TIMING_LIMITATION", "REJECT_EVENT"}:
                    raise ValueError("unsupported field review decision")
            choices[key] = row
    events, _ = reconcile(observations, scope, plan["created_at"], choices)
    events = [e for e in events if not e["values"].get("ex_date") or plan["start"] <= e["values"]["ex_date"] <= plan["end"]]
    return events, observations, plan, choices


def replay(root, output, scope_override=None, field_input=None, reparse=False):
    observations, scope, plan = load(root)
    if output.exists():
        raise ValueError("OUTPUT_EXISTS")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(root, output / "prior")
    original_child = plan.get("source_archive_child", "source_collection_v1_1")
    if reparse:
        child = (root / original_child).resolve()
        if not child.is_relative_to(root.resolve()):
            raise ValueError("ARCHIVE_PATH_ESCAPE")
        requests = json.loads((child / "requests.json").read_text(encoding="utf-8"))
        observations = [o for o in observations if o["source_type"] not in {"VSDC", "HNX"} or o["manual_input"]]
        markets = {}
        for request in requests:
            if request.get("status") != 200:
                continue
            text = (child / request["path"]).read_text(encoding="utf-8-sig", errors="replace")
            evidence = dict(request, path=original_child + "/" + request["path"])
            if request["url"].startswith("https://vsdc.vn/vi/ad/"):
                observations.extend(observation(r) for r in parse_vsdc(text, evidence))
            elif request["url"].startswith("https://www.hnx.vn/"):
                ticker = request.get("ticker")
                if request.get("method") == "GET" and "m-tim-kiem-" in request["url"]:
                    _, markets[ticker] = hnx_market_context(text, ticker)
                if ticker in markets and ("m-tim-kiem-" in request["url"] or "ChangePageTHQ" in request["url"]):
                    rows, _ = parse_hnx(text, evidence, ticker, markets[ticker])
                    observations.extend(observation(r) for r in rows)
    observations = copy.deepcopy(observations)
    for o in observations:
        # Mixed components can share the same receipt object. Create per-observation
        # references so replay prefixes each archived path exactly once.
        o["source_evidence"] = [dict(evidence, path="prior/" + evidence["path"]) if evidence.get("path") else dict(evidence)
                                for evidence in o["source_evidence"]]
    if scope_override:
        scope = legacy.load_scope(scope_override)
    base.write_new(output / "scope.csv", base.csv_text(tuple(scope[0]), scope))
    if field_input:
        shutil.copyfile(field_input, output / "field_input.jsonl")
        observations.extend(observation(r, manual=True) for r in legacy.read_jsonl(output / "field_input.jsonl"))
    plan = dict(plan, created_at=now(), replay_of_manifest_sha256=base.digest(root / "manifest.json"), source_archive_child="prior/" + original_child,
                scope_sha256=base.digest(output / "scope.csv"))
    base.write_new(output / "plan.json", base.json_text(plan))
    shutil.copyfile(root / "source_checks.json", output / "source_checks.json")
    shutil.copyfile(root / "requests.json", output / "requests.json")
    events = finalize(output, observations, scope, plan)
    return manifest(output, dict(status="PARTIAL", network_requests=0, reparse_archived_responses=reparse,
                                 replay_of_manifest_sha256=plan["replay_of_manifest_sha256"], event_count=len(events)))


def build(root, output, reviews=None):
    review_hash = base.digest(reviews) if reviews else None
    events, observations, plan, choices = load_choices(root, reviews)
    if output.exists():
        raise ValueError("OUTPUT_EXISTS")
    by_id = {o["observation_id"]: o for o in observations}
    rows = []
    for event in events:
        if event["event_data_verification"] != "VERIFIED":
            continue
        e = {k: None for k in base.schema(base.TABLE)["fields"]}
        e.update({k: v for k, v in event["values"].items() if k in e})
        first = by_id[event["effective_revision_id"] or event["observation_ids"][0]]
        e.update(event_id=event["event_id"], event_group_id=event["event_group_id"], security_id=event["identity"]["security_id"],
                 available_at=event["available_at"], raw_terms="\n".join(by_id[i]["raw_terms"] for i in event["observation_ids"]),
                 primary_source_type="VENDOR" if first["source_type"] in {"CAFEF", "VNDIRECT"} else first["source_type"], primary_source_url=first["source_url"],
                 primary_source_published_at=first["source_published_at"], source_hash=first["source_hash"], schema_version=VERSION,
                 verification_status=event["verification_status"], identity_status="VERIFIED", identity_source_url=event["identity"]["identity_source_url"],
                 revision_status="CORRECTION" if event["effective_revision_id"] else "ORIGINAL", normalization_inputs={},
                 created_at=plan["created_at"], updated_at=max([plan["created_at"], *[r["reviewed_at"] for r in choices.values() if r.get("reviewed_at")]], key=base.timestamp),
                 field_provenance=event["field_provenance"], event_data_verification=event["event_data_verification"],
                 pit_timing_verification=event["pit_timing_verification"], event_matching_status=event["matching_status"],
                 timing_incomplete_fields=event["timing_incomplete_fields"], observation_ids=event["observation_ids"],
                 revision_lineage=event["revision_lineage"], effective_revision_id=event["effective_revision_id"],
                 review_lineage=[r for r in choices.values() if r["event_id"] == event["event_id"]])
        rows.append(e)
    validate_rows("corporate_actions_multisource_v1", rows)
    output.mkdir(parents=True, exist_ok=False)
    base.write_new(output / "corporate_actions_v1.jsonl", legacy.dump_jsonl(rows))
    base.write_new(output / "event_decisions.jsonl", legacy.dump_jsonl(events))
    shutil.copyfile(root / "observations.jsonl", output / "observations.jsonl")
    if reviews:
        shutil.copyfile(reviews, output / "field_reviews.csv")
        if base.digest(output / "field_reviews.csv") != review_hash:
            raise ValueError("REVIEWS_CHANGED_DURING_BUILD")
    return manifest(output, dict(artifact_type="corporate-actions-v1-canonical-multisource", status="PASS" if len(rows) == len(events) and all(e["pit_timing_verification"] == "COMPLETE" for e in events) else "PARTIAL",
                                 verified_event_count=len(rows), pit_timing_partial_count=sum(e["pit_timing_verification"] != "COMPLETE" for e in events),
                                 collection_manifest_sha256=base.digest(root / "manifest.json"), collection_path=str(root.resolve())))


def coverage(root, reviews=None, attestation=None):
    review_hash = base.digest(reviews) if reviews else None
    attestation_hash = base.digest(attestation) if attestation else None
    events, observations, plan, _ = load_choices(root, reviews)
    checks = json.loads((root / "source_checks.json").read_text(encoding="utf-8"))
    scope = legacy.load_scope(root / "scope.csv")
    attestations = base.read_csv(attestation, base.COVERAGE_FIELDS) if attestation else []
    rows = []
    for s in scope:
        own = [e for e in events if e["values"].get("ticker") == s["ticker"] and e["values"].get("exchange") == s["exchange"]]
        field_ok = lambda e, f: e["field_provenance"].get(f, {}).get("status") == "VERIFIED"
        confirmed = False
        attested = [a for a in attestations if all((a.get(k) or "") == (s.get(k) or "") for k in ("ticker", "exchange", "security_id"))]
        if len(attested) == 1:
            a = attested[0]
            try:
                from datetime import date
                confirmed = (a["review_status"] == "REVIEWED" and a["reviewed_start_date"] <= plan["start"] <= plan["end"] <= a["reviewed_end_date"]
                             and date.fromisoformat(a["reviewed_start_date"]).isoformat() == a["reviewed_start_date"]
                             and date.fromisoformat(a["reviewed_end_date"]).isoformat() == a["reviewed_end_date"]
                             and base.timestamp(a["last_checked_at"]).date() >= date.fromisoformat(plan["end"])
                             and a["reviewed_event_types"] == "ALL_V1" and bool(a["reviewer"].strip()) and bool(a["coverage_evidence"].strip())
                             and base.authoritative_url(a["primary_source_type"], a["primary_source_url"]) and s.get("identity_status") == "VERIFIED")
            except ValueError:
                pass
        active = [e for e in own if e["event_data_verification"] != "REJECTED"]
        complete = confirmed and all(e["event_data_verification"] == "VERIFIED" and e["pit_timing_verification"] == "COMPLETE" for e in active)
        status = ("NO_EVENT_CONFIRMED" if confirmed and not active else "MANUAL_REVIEW_REQUIRED" if len(attested) > 1 or any(e["event_data_verification"] != "VERIFIED" or e["pit_timing_verification"] != "COMPLETE" for e in active)
                  else "HAS_VERIFIED_EVENTS" if active else "NOT_YET_REVIEWED")
        rows.append(dict(ticker=s["ticker"], exchange=s["exchange"], security_id=s.get("security_id"), required_start_date=plan["start"], required_end_date=plan["end"], events_found=len(own),
                         events_with_verified_type=sum(field_ok(e, "event_type") and e["values"].get("event_type") != "OTHER" for e in own),
                         events_with_verified_ex_date=sum(field_ok(e, "ex_date") for e in own),
                         events_with_verified_terms=sum(all(field_ok(e, f) for f in base.TERMS.get(e["values"].get("event_type"), ())) and e["values"].get("event_type") in base.TERMS and e["values"].get("event_type") != "OTHER" for e in own),
                         events_with_verified_identity=sum(e["identity"].get("identity_status") == "VERIFIED" for e in own),
                         events_with_pit_timing_complete=sum(e["pit_timing_verification"] == "COMPLETE" for e in own),
                         events_with_manual_review=sum(e["event_data_verification"] != "VERIFIED" or e["pit_timing_verification"] != "COMPLETE" for e in own),
                         auto_verified=sum(e["verification_status"] == "AUTO_VERIFIED" for e in own), missing_ex_date=sum(not e["values"].get("ex_date") for e in own),
                         missing_required_terms=sum(any(not e["values"].get(f) and e["values"].get(f) != 0 for f in base.TERMS.get(e["values"].get("event_type"), ())) for e in own),
                         source_hits={name: sum(o["source_type"] == name and value(o, "ticker") == s["ticker"] for o in observations) for name in ("VSDC", "HNX", "HOSE", "ISSUER_IR", "CAFEF", "VNDIRECT")},
                         coverage_status=status, completeness_status="COVERAGE_COMPLETE" if complete else "COVERAGE_INCOMPLETE"))
    unscoped = [e["event_id"] for e in events if not any(e["values"].get("ticker") == s["ticker"] and e["values"].get("exchange") == s["exchange"] for s in scope)]
    attempted = {tuple(item) for item in plan.get("source_request_scope", [])}
    hits = {(o["source_type"], value(o, "ticker")) for o in observations}
    required_count = sum(len((*CRITICAL, *base.TERMS.get(e["values"].get("event_type"), ()))) for e in events)
    verified_count = sum(e["field_provenance"].get(f, {}).get("status") == "VERIFIED" and (f != "event_type" or e["values"].get(f) != "OTHER") for e in events for f in (*CRITICAL, *base.TERMS.get(e["values"].get("event_type"), ())))
    if reviews and base.digest(reviews) != review_hash or attestation and base.digest(attestation) != attestation_hash:
        raise ValueError("REVIEW_OR_ATTESTATION_CHANGED_DURING_COVERAGE")
    return dict(rows=rows, coverage_pass=bool(rows) and not unscoped and all(r["completeness_status"] == "COVERAGE_COMPLETE" for r in rows), unscoped_events=unscoped,
                source_completeness_matrix=source_matrix(observations),
                source_checks=checks, source_hit_count=len({(o["source_type"], value(o, "ticker")) for o in observations}),
                source_hit_rate=len(attempted & hits) / len(attempted) if attempted else None,
                verified_required_field_rate=verified_count / required_count if required_count else None,
                event_data_verified_count=sum(e["event_data_verification"] == "VERIFIED" for e in events),
                reviews_sha256=review_hash, attestation_sha256=attestation_hash,
                required_start_date=plan["start"], required_end_date=plan["end"], runtime_window_status="MANUAL_REVIEW_REQUIRED",
                limitation="BOUNDED_PILOT_NOT_FULL_UNIVERSE; PIT_PARTIAL_NOT_HISTORICAL_ELIGIBILITY", q11_status="STILL_OPEN", q17_status="NOT_TOUCHED")
