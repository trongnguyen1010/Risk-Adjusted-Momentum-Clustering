"""Compatibility orchestration from verified source envelopes to canonical runs.

Source verification, normalization and reconciliation live in separate generic
layers. This module only coordinates the retained legacy promotion command.
"""
from pathlib import Path
import uuid

from ..contracts import validate_rows
from ..io import digest, encoded, now, read_json, read_rows, write_json, write_rows
from .crawler import code_hash
from .normalization.market import map_record
from .quality import clean_tables
from .reconciliation.candidates import candidate_from_row
from .reconciliation.rules import SourcePriorityPolicy, reconcile_candidates
from .sources.vnstock import verify_vendor


TABLES = ("securities", "prices_daily", "benchmark_daily", "trading_calendar",
          "corporate_actions", "risk_free_rate")


def promote(vendor: Path, policy_path: Path, root: Path) -> tuple[Path, dict]:
    """Create a new canonical run or persistent blocked/quarantine report."""
    policy_path, vendor = Path(policy_path).resolve(), Path(vendor).resolve()
    policy = read_json(policy_path)
    run_id = "canonical-" + uuid.uuid4().hex[:12]
    target = Path(root).resolve() / "data" / "canonical" / run_id
    target.mkdir(parents=True, exist_ok=False)
    manifest = dict(run_id=run_id, data_version=run_id, vendor_run_id=vendor.name,
                    status="running", started_at=now(), synthetic=policy.get("synthetic"),
                    data_mode="synthetic" if policy.get("synthetic") else "real",
                    methodology=policy.get("methodology", {}), policy=policy,
                    policy_hash=digest(encoded(policy)), code_hash=code_hash(), schema_version="1.4.0")
    errors, quarantine, tables = [], [], {}
    records_input = 0
    try:
        vendor_manifest, documents = verify_vendor(vendor, policy)
        records_input = sum(len(document["records"]) for document in documents
                            if document["job"]["kind"] != "listing")
        manifest["vendor_manifest_sha256"] = digest((vendor / "manifest.json").read_bytes())
        manifest["vendor_config"] = vendor_manifest["config"]
        references = {}
        manifest["reference_hashes"] = {}
        for name in ("securities", "trading_calendar", "corporate_actions", "risk_free_rate", "observations"):
            spec = policy.get("references", {}).get(name)
            if spec is None:
                if name in ("securities", "trading_calendar"):
                    raise ValueError("missing reference: " + name)
                references[name] = []
                continue
            if not spec.get("evidence"):
                raise ValueError("reference evidence missing: " + name)
            path = (policy_path.parent / spec["path"]).resolve()
            if digest(path.read_bytes()) != spec["sha256"]:
                raise ValueError("reference checksum mismatch: " + name)
            references[name] = read_rows(path)
            manifest["reference_hashes"][name] = spec["sha256"]
        if not policy["synthetic"]:
            if any(row["identity_status"] == "synthetic" for row in references["securities"]):
                raise ValueError("synthetic identity in real references")
            if any(not row.get("available_at") for row in references["trading_calendar"]):
                raise ValueError("real calendar requires historical availability")
        observations = {}
        for row in references["observations"]:
            key = (row["kind"], row["symbol"], row["trade_date"])
            if key in observations:
                raise ValueError("duplicate observation reference")
            observations[key] = row
        raw = {name: [(row, {"source": row["source"]}, row["fetched_at"])
                      for row in references[name]]
               for name in references if name != "observations"}
        candidates = []
        for document in documents:
            if document["job"]["kind"] == "listing":
                manifest["listing_decision"] = "current listing retained in vendor; historical master required"
                continue
            for record in document["records"]:
                try:
                    name, row = map_record(record, document, policy, references["securities"], observations)
                    candidates.append(candidate_from_row(
                        name, row, raw_hash=digest(encoded(record)), transform_version="vnstock-policy-1.0"
                    ))
                except (ValueError, KeyError, TypeError) as exc:
                    quarantine.append(dict(record=record, error_code="PROMOTION_MAPPING",
                                           error_message=str(exc), source=document["source_routing"],
                                           vendor_run_id=vendor.name, job=document["job"], detected_at=now()))
        priority_spec = policy.get("source_priority_policy")
        priority_policy = SourcePriorityPolicy.from_dict(priority_spec) if priority_spec else None
        reconciled, decisions, conflicts = reconcile_candidates(candidates, priority_policy)
        write_rows(target / "reconciliation" / "decisions.jsonl", decisions)
        write_rows(target / "reconciliation" / "conflicts.jsonl", conflicts)
        manifest["reconciliation"] = dict(rule_version="2.0", decisions=len(decisions), conflicts=len(conflicts))
        for conflict in conflicts:
            quarantine.append(dict(record=conflict, error_code="RECONCILIATION_CONFLICT",
                                   error_message=conflict["reason"], source="multi_source",
                                   vendor_run_id=vendor.name, detected_at=now()))
        for name, rows in reconciled.items():
            raw.setdefault(name, []).extend((row, {"source": row["source"]}, row["fetched_at"])
                                            for row in rows)
        tables, issues, rejected = clean_tables(raw, run_id)
        quarantine.extend(dict(row, vendor_run_id=vendor.name) for row in rejected)
        errors.extend(issues)
        for name in ("securities", "trading_calendar", "prices_daily", "benchmark_daily"):
            if not tables.get(name):
                errors.append({"error_code": "EMPTY_TABLE", "error_message": name})
        for name in TABLES:
            validate_rows(name, tables.get(name, []))
            write_rows(target / "clean" / (name + ".jsonl"), tables.get(name, []))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(dict(error_code="PROMOTION_BLOCKED", error_message=str(exc)))
    write_rows(target / "quarantine" / "records.jsonl", quarantine)
    manifest.update(status="blocked" if errors or quarantine else "complete", finished_at=now(),
                    quality="QC ERROR" if errors or quarantine else "QC PASS", errors=errors,
                    quarantined=len(quarantine), clean_rows={key: len(value) for key, value in tables.items()},
                    real_pilot_accepted=False, records_input=records_input,
                    records_accepted=sum(len(tables.get(table, [])) for table in ("prices_daily", "benchmark_daily")),
                    records_quarantined=len(quarantine), warnings=policy.get("warnings", []),
                    blocking_errors=len(errors))
    manifest["artifacts"] = {path.relative_to(target).as_posix(): digest(path.read_bytes())
                             for path in sorted(target.rglob("*.jsonl"))}
    write_json(target / "manifest.json", manifest)
    return target, manifest
