"""Immutable M1 scale shard acquisition and multi-machine handoff verification."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..contracts import validate_rows
from ..io import digest, encoded, now, read_json, read_rows, write_json, write_rows
from ..features.market import build_features
from .crawler import code_hash
from .planning import M1_SCALE, REPRESENTATIVE_PILOT
from .representative_pilot import (
    CAFE_VERSION, FINANCIAL_PIT_UNRESOLVED, KBS_VERSION, OFFICIAL_MARKET_SOURCES,
    PilotRawStore, PublicJsonClient, CafeFSource, KBSPublicHttpSource,
    _build_real_manifest, _execute_job, _years, utc_now, validate_config,
    validate_resume_run, _valid_kbs,
)
from .representative_pilot_canonical import (
    AVAILABILITY_TIME, _calendar, _fetched_at, _latest_stamp,
)
from .representative_pilot_finalize import _raw_payload
from .sources.cafef import (
    apply_invalid_row_policy, classify_cafef_page_row, map_trade_history_row,
)
from .sources.vnstock import map_kbs_wire_ohlcv_row


M1_SCALE_SHARD = "M1_SCALE_SHARD"
IDENTITY_FIELDS = (
    "config_hash", "universe_hash", "source_gate_hash", "assignment_hash",
    "code_hash", "job_plan_hash", "kbs_adapter_version", "cafef_adapter_version",
)


def _compatible_text_hashes(path):
    """Return byte hashes for the original, LF and CRLF forms of a text file."""
    data = Path(path).read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {digest(data), digest(normalized), digest(normalized.replace(b"\n", b"\r\n"))}


def _require_portable_hash(path, stored_hash, label):
    if stored_hash not in _compatible_text_hashes(path):
        raise ValueError(f"handoff {label} hash mismatch")


def _sha256(value):
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


def _resolve(base, value, label):
    if not isinstance(value, str) or not value or "LOCAL_OR_REVIEWED_PATH" in value:
        raise ValueError(f"reviewed {label} is required")
    path = Path(value)
    if not path.is_absolute():
        path = (Path(base) / path).resolve()
    else:
        path = path.resolve()
    if not path.is_file():
        raise ValueError(f"{label} does not exist")
    return path


def validate_pilot_gate(gate):
    if not (
        gate.get("gate") == REPRESENTATIVE_PILOT
        and gate.get("status") == "PASS"
        and M1_SCALE in gate.get("unlocks", [])
        and gate.get("checks", {}).get("real_data") is True
        and bool(gate.get("input_evidence_hashes"))
    ):
        raise ValueError("a real PASS REPRESENTATIVE_PILOT gate unlocking M1_SCALE is required")


def validate_master_universe(rows, config):
    if not isinstance(rows, list):
        raise ValueError("M1 master universe must be a JSON array")
    validate_rows("representative_pilot_universe", rows)
    expected = config.get("expected_total_symbols")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 300:
        raise ValueError("expected_total_symbols must be an integer >=300")
    if len(rows) != expected:
        raise ValueError(f"M1 master universe must contain exactly {expected} rows")
    security_ids = [row.get("security_id") for row in rows]
    tickers = [row["ticker"] for row in rows]
    if any(not isinstance(value, str) or not value for value in security_ids):
        raise ValueError("every M1 universe row requires a stable security_id")
    if len(security_ids) != len(set(security_ids)) or len(tickers) != len(set(tickers)):
        raise ValueError("M1 security_id and ticker values must be unique")
    if {row["exchange"] for row in rows} != {"HOSE", "HNX", "UPCOM"}:
        raise ValueError("M1 master universe must cover HOSE, HNX and UPCOM")


def validate_assignment(assignment, config, universe_by_id):
    required = {
        "scale_id", "assignment_id", "collector", "shard_index", "security_ids",
        "start", "end", "include_benchmark",
    }
    if set(assignment) != required:
        raise ValueError("M1 assignment fields differ from the frozen contract")
    if not isinstance(assignment["scale_id"], str) or not assignment["scale_id"].startswith("m1-scale-"):
        raise ValueError("M1 scale_id must start with m1-scale-")
    if not isinstance(assignment["assignment_id"], str) or not assignment["assignment_id"]:
        raise ValueError("M1 assignment_id is required")
    if not isinstance(assignment["collector"], str) or not assignment["collector"].strip():
        raise ValueError("M1 collector is required")
    if not isinstance(assignment["shard_index"], int) or isinstance(assignment["shard_index"], bool):
        raise ValueError("M1 shard_index must be an integer")
    shard_size = config.get("symbols_per_shard")
    expected_shards = config.get("expected_shards")
    if (not isinstance(shard_size, int) or isinstance(shard_size, bool) or shard_size < 1
            or not isinstance(expected_shards, int) or isinstance(expected_shards, bool)
            or expected_shards < 1
            or config["expected_total_symbols"] != shard_size * expected_shards):
        raise ValueError("M1 shard count/size must exactly cover expected_total_symbols")
    if not 1 <= assignment["shard_index"] <= expected_shards:
        raise ValueError("M1 shard_index is outside the configured range")
    security_ids = assignment["security_ids"]
    if (not isinstance(security_ids, list) or len(security_ids) != shard_size
            or len(security_ids) != len(set(security_ids))):
        raise ValueError(f"M1 assignment requires exactly {shard_size} unique security_ids")
    missing = sorted(set(security_ids) - set(universe_by_id))
    if missing:
        raise ValueError(f"M1 assignment contains unknown security_ids: {missing[:3]}")
    if assignment["start"] != config["start"] or assignment["end"] != config["end"]:
        raise ValueError("M1 assignment date range must equal the frozen config")
    if type(assignment["include_benchmark"]) is not bool:
        raise ValueError("include_benchmark must be boolean")


def load_scale_readiness(config_path, pilot_gate_path, assignment_path, *, root):
    root = Path(root).resolve()
    config_path = Path(config_path).resolve()
    pilot_gate_path = Path(pilot_gate_path).resolve()
    assignment_path = Path(assignment_path).resolve()
    config = read_json(config_path)
    if config.get("template_type") != M1_SCALE:
        raise ValueError("M1 config template_type must be M1_SCALE")
    thresholds = config.get("coverage_thresholds", {})
    minimum_three_year_ratio = thresholds.get("minimum_usable_three_year_ratio")
    maximum_failed_symbols = thresholds.get("maximum_failed_symbols")
    if (not isinstance(minimum_three_year_ratio, (int, float))
            or isinstance(minimum_three_year_ratio, bool)
            or not 0 < minimum_three_year_ratio <= 1):
        raise ValueError("minimum_usable_three_year_ratio must be in (0,1]")
    if (not isinstance(maximum_failed_symbols, int)
            or isinstance(maximum_failed_symbols, bool)
            or maximum_failed_symbols < 0):
        raise ValueError("maximum_failed_symbols must be a non-negative integer")
    pilot_compatible = dict(
        config,
        template_type=REPRESENTATIVE_PILOT,
        coverage_thresholds={
            "minimum_usable_five_year_ratio": 1.0,
            "maximum_failed_symbols": maximum_failed_symbols,
        },
    )
    validate_config(pilot_compatible, root=root)
    if _years(config["start"], config["end"]) < 5:
        raise ValueError("M1 scale must request at least five years")
    gate = read_json(pilot_gate_path)
    validate_pilot_gate(gate)
    universe_path = _resolve(config_path.parent, config.get("universe_file"), "M1 universe_file")
    universe = read_json(universe_path)
    validate_master_universe(universe, config)
    universe_by_id = {row["security_id"]: row for row in universe}
    assignment = read_json(assignment_path)
    validate_assignment(assignment, config, universe_by_id)
    shard_universe = [universe_by_id[value] for value in assignment["security_ids"]]
    return {
        "root": root, "config_path": config_path, "gate_report_path": pilot_gate_path,
        "assignment_path": assignment_path, "universe_path": universe_path,
        "config": config, "source_gate": gate, "assignment": assignment,
        "master_universe": universe, "universe": shard_universe,
        "config_hash": digest(config_path.read_bytes()),
        "source_gate_hash": digest(pilot_gate_path.read_bytes()),
        "universe_hash": digest(universe_path.read_bytes()),
        "assignment_hash": digest(assignment_path.read_bytes()),
    }


def build_scale_job_plan(prepared):
    from .representative_pilot import build_job_plan

    plan = build_job_plan(prepared)
    if not prepared["assignment"]["include_benchmark"]:
        plan["jobs"] = [job for job in plan["jobs"] if job["kind"] != "index"]
    plan.update({
        "template_type": M1_SCALE_SHARD,
        "scale_id": prepared["assignment"]["scale_id"],
        "assignment_id": prepared["assignment"]["assignment_id"],
        "shard_index": prepared["assignment"]["shard_index"],
        "include_benchmark": prepared["assignment"]["include_benchmark"],
        "requests_lower_bound": len(plan["jobs"]),
    })
    return plan


def build_scale_identity(prepared, plan):
    return {
        "config_hash": prepared["config_hash"],
        "universe_hash": prepared["universe_hash"],
        "source_gate_hash": prepared["source_gate_hash"],
        "assignment_hash": prepared["assignment_hash"],
        "code_hash": code_hash(), "job_plan_hash": digest(encoded(plan)),
        "kbs_adapter_version": KBS_VERSION, "cafef_adapter_version": CAFE_VERSION,
    }


def evaluate_scale_shard_checks(manifest, config, *, include_benchmark):
    """Evaluate M1 shard coverage without treating five years as a per-symbol minimum."""
    aggregate = manifest["aggregate"]
    threshold = config["coverage_thresholds"]
    ratio = aggregate["usable_3y_clustering_symbols"] / aggregate["selected_symbols"]
    benchmark_ok = manifest["benchmark"]["valid"] if include_benchmark else True
    return {
        "all_jobs_complete": all(state["status"] == "COMPLETE"
                                 for state in manifest["jobs"].values()),
        "failed_symbols_within_threshold": len(aggregate["failed_symbols"])
        <= threshold["maximum_failed_symbols"],
        "three_year_ratio_passed": ratio >= threshold["minimum_usable_three_year_ratio"],
        "benchmark_passed_if_owned": benchmark_ok,
        "reference_source_not_exhausted": not aggregate["reference_source_exhausted_symbols"],
        "financial_safety_lock_active": manifest["financial"]["features_allowed"] is False,
    }


def shard_run_directory(root, scale_id, assignment_id, run_id):
    return (Path(root) / "data" / "raw" / "m1_scale" / scale_id
            / "shards" / assignment_id / run_id)


def _write_headers(prepared, plan, run_id, *, dry_run):
    assignment = prepared["assignment"]
    directory = shard_run_directory(
        prepared["root"], assignment["scale_id"], assignment["assignment_id"], run_id)
    if directory.exists():
        raise ValueError("immutable M1 shard run already exists")
    identity = build_scale_identity(prepared, plan)
    write_json(directory / "run.json", {
        "run_id": run_id, "scale_id": assignment["scale_id"],
        "assignment_id": assignment["assignment_id"], "template_type": M1_SCALE_SHARD,
        "mode": "DRY_RUN" if dry_run else "REAL_EXECUTION", "started_at": utc_now(),
        "network_requests": 0, **identity,
    })
    write_json(directory / "assignment.json", assignment)
    write_json(directory / "source_gate_reference.json", {
        "gate": REPRESENTATIVE_PILOT, "status": "PASS", "unlocks": [M1_SCALE],
        "path": prepared["gate_report_path"].as_posix(),
        "sha256": prepared["source_gate_hash"],
    })
    write_json(directory / "job_plan.json", plan)
    return directory


def dry_run_shard(config_path, pilot_gate_path, assignment_path, *, root, run_id=None):
    prepared = load_scale_readiness(config_path, pilot_gate_path, assignment_path, root=root)
    plan = build_scale_job_plan(prepared)
    run_id = run_id or new_artifact_id("m1-shard-dry-run")
    directory = _write_headers(prepared, plan, run_id, dry_run=True)
    manifest = {
        "run_id": run_id, "scale_id": prepared["assignment"]["scale_id"],
        "assignment_id": prepared["assignment"]["assignment_id"], "mode": "DRY_RUN",
        "status": "DRY_RUN_READINESS_PASS", "readiness": "PASS", "network_requests": 0,
        "execution_started": False, "gate_emitted": False, "unlocks": [],
        "checks": {"representative_pilot_passed": True, "assignment_exact": True,
                   "at_least_five_years": True, "source_routing_frozen": True,
                   "financial_safety_lock_active": True},
        "job_count": len(plan["jobs"]), "requests_lower_bound": len(plan["jobs"]),
        "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
        "financial_features_allowed": False,
    }
    write_json(directory / "manifest.json", manifest)
    return directory, manifest


def _validate_scale_resume(directory, run_id, prepared, plan, identity):
    manifest = validate_resume_run(directory, run_id, plan, identity)
    header = read_json(directory / "run.json")
    for field in IDENTITY_FIELDS:
        if header.get(field) != identity[field]:
            raise ValueError(f"resume {field} mismatch; start a new immutable run")
    if (header.get("scale_id") != prepared["assignment"]["scale_id"]
            or header.get("assignment_id") != prepared["assignment"]["assignment_id"]):
        raise ValueError("resume scale/assignment identity mismatch")
    if read_json(directory / "assignment.json") != prepared["assignment"]:
        raise ValueError("resume stored assignment mismatch")
    return manifest


def run_real_shard(config_path, pilot_gate_path, assignment_path, *, root, resume=None):
    prepared = load_scale_readiness(config_path, pilot_gate_path, assignment_path, root=root)
    plan = build_scale_job_plan(prepared)
    identity = build_scale_identity(prepared, plan)
    assignment = prepared["assignment"]
    run_id = resume or new_artifact_id("m1-shard")
    directory = shard_run_directory(
        prepared["root"], assignment["scale_id"], assignment["assignment_id"], run_id)
    if resume:
        if not run_id.startswith("m1-shard-") or not directory.is_dir():
            raise ValueError("resume requires an existing M1 shard run")
        manifest = _validate_scale_resume(directory, run_id, prepared, plan, identity)
    else:
        directory = _write_headers(prepared, plan, run_id, dry_run=False)
        manifest = {
            "run_id": run_id, "scale_id": assignment["scale_id"],
            "assignment_id": assignment["assignment_id"], "mode": "REAL_EXECUTION",
            "status": "RUNNING", "started_at": utc_now(),
            "jobs": {job["id"]: {"status": "PENDING", "job": job, "artifacts": []}
                     for job in plan["jobs"]},
        }
        write_json(directory / "manifest.json", manifest)
    client = PublicJsonClient(**{
        key: value for key, value in prepared["config"]["http"].items()
        if key != "concurrency"
    })
    kbs, cafef = KBSPublicHttpSource(client), CafeFSource(client)
    store = PilotRawStore(prepared["root"], run_id)
    try:
        for state in manifest["jobs"].values():
            if state["status"] == "COMPLETE":
                if not all(store.verify(artifact) for artifact in state["artifacts"]):
                    raise ValueError("resume artifact checksum mismatch")
                continue
            state.update(status="RUNNING", error=None)
            write_json(directory / "manifest.json", manifest)
            artifacts = _execute_job(state["job"], prepared["config"], kbs, cafef, store)
            state.update(status="COMPLETE", artifacts=artifacts)
            write_json(directory / "manifest.json", manifest)
        manifest = _build_real_manifest(prepared, plan, manifest)
        checks = evaluate_scale_shard_checks(
            manifest, prepared["config"],
            include_benchmark=assignment["include_benchmark"])
        status = "PASS" if all(checks.values()) else "FAIL"
        gate = {
            "gate": M1_SCALE_SHARD, "status": status, "checks": checks,
            "blocking_reasons": [key for key, value in checks.items() if not value],
            "scale_id": assignment["scale_id"], "assignment_id": assignment["assignment_id"],
            "run_id": run_id, "unlocks": [],
            "input_evidence_hashes": {**identity, **manifest["provider_artifact_hashes"]},
        }
        manifest.update(status="COMPLETE" if status == "PASS" else "FAILED_GATE",
                        finished_at=utc_now(), gate_status=status)
        write_json(directory / "manifest.json", manifest)
        write_json(directory / "gate.json", gate)
        return directory, manifest, gate
    except Exception as exc:
        manifest.update(status="FAILED", finished_at=utc_now(),
                        error=f"{type(exc).__name__}: {exc}")
        write_json(directory / "manifest.json", manifest)
        raise


def validate_completed_shard(prepared, run_id):
    """Validate an immutable completed acquisition for cross-machine handoff.

    Resume remains byte-identity strict.  Handoff additionally accepts the two
    normal text checkout encodings, but replays the stored plan, manifest job
    definitions and every provider artifact before any row can be selected.
    """
    plan = build_scale_job_plan(prepared)
    assignment = prepared["assignment"]
    directory = shard_run_directory(
        prepared["root"], assignment["scale_id"], assignment["assignment_id"], run_id)
    if not directory.is_dir():
        raise ValueError("handoff shard run directory is missing")
    header = read_json(directory / "run.json")
    manifest = read_json(directory / "manifest.json")
    if (header.get("run_id") != run_id or manifest.get("run_id") != run_id
            or header.get("mode") != "REAL_EXECUTION"
            or manifest.get("mode") != "REAL_EXECUTION"):
        raise ValueError("handoff requires matching REAL_EXECUTION run identity")
    if (header.get("template_type") != M1_SCALE_SHARD
            or header.get("scale_id") != assignment["scale_id"]
            or header.get("assignment_id") != assignment["assignment_id"]
            or manifest.get("scale_id") != assignment["scale_id"]
            or manifest.get("assignment_id") != assignment["assignment_id"]):
        raise ValueError("handoff scale/assignment identity mismatch")
    stored_assignment = read_json(directory / "assignment.json")
    if stored_assignment != assignment:
        raise ValueError("handoff stored assignment mismatch")
    stored_plan = read_json(directory / "job_plan.json")
    if digest(encoded(stored_plan)) != header.get("job_plan_hash"):
        raise ValueError("handoff stored job-plan hash mismatch")
    if stored_plan != plan:
        raise ValueError("handoff stored job plan differs from the frozen assignment")
    expected_jobs = {job["id"]: job for job in plan["jobs"]}
    stored_jobs = manifest.get("jobs")
    if not isinstance(stored_jobs, dict) or set(stored_jobs) != set(expected_jobs):
        raise ValueError("handoff manifest job set mismatch")
    if any(not isinstance(stored_jobs[job_id], dict)
           or stored_jobs[job_id].get("job") != expected_jobs[job_id]
           for job_id in expected_jobs):
        raise ValueError("handoff manifest job definition mismatch")
    for path, field in ((prepared["config_path"], "config_hash"),
                        (prepared["universe_path"], "universe_hash"),
                        (prepared["assignment_path"], "assignment_hash"),
                        (prepared["gate_report_path"], "source_gate_hash")):
        _require_portable_hash(path, header.get(field), field)
    if (header.get("kbs_adapter_version") != KBS_VERSION
            or header.get("cafef_adapter_version") != CAFE_VERSION
            or not _sha256(header.get("code_hash"))):
        raise ValueError("handoff adapter/code provenance is invalid")
    if manifest.get("status") not in ("COMPLETE", "FAILED_GATE"):
        raise ValueError("handoff source run acquisition is not complete")
    store = PilotRawStore(prepared["root"], run_id)
    if any(state.get("status") != "COMPLETE" for state in manifest["jobs"].values()):
        raise ValueError("handoff contains an incomplete job")
    if any(not store.verify(artifact) for state in manifest["jobs"].values()
           for artifact in state["artifacts"]):
        raise ValueError("handoff provider artifact checksum mismatch")
    gate = read_json(directory / "gate.json")
    if (gate.get("run_id") != run_id or gate.get("gate") != M1_SCALE_SHARD
            or gate.get("scale_id") != assignment["scale_id"]
            or gate.get("assignment_id") != assignment["assignment_id"]):
        raise ValueError("handoff shard gate identity mismatch")
    return directory, manifest, gate


def load_assignment_index(config_path, pilot_gate_path, index_path, *, root):
    """Verify frozen assignment files form one exact partition of the master universe."""
    root = Path(root).resolve()
    config_path = Path(config_path).resolve()
    pilot_gate_path = Path(pilot_gate_path).resolve()
    index_path = Path(index_path).resolve()
    config = read_json(config_path)
    gate = read_json(pilot_gate_path)
    validate_pilot_gate(gate)
    index = read_json(index_path)
    required = {
        "scale_id", "status", "config_sha256", "universe_sha256",
        "pilot_gate_sha256", "expected_total_symbols", "expected_shards",
        "symbols_per_shard", "assignments",
    }
    if set(index) != required or index.get("status") != "FROZEN":
        raise ValueError("assignment index fields/status differ from the frozen contract")
    if index.get("config_sha256") != digest(config_path.read_bytes()):
        raise ValueError("assignment index config hash mismatch")
    if index.get("pilot_gate_sha256") != digest(pilot_gate_path.read_bytes()):
        raise ValueError("assignment index pilot gate hash mismatch")
    universe_path = _resolve(config_path.parent, config.get("universe_file"), "M1 universe_file")
    if index.get("universe_sha256") != digest(universe_path.read_bytes()):
        raise ValueError("assignment index universe hash mismatch")
    if any(index.get(key) != config.get(key) for key in (
            "expected_total_symbols", "expected_shards", "symbols_per_shard")):
        raise ValueError("assignment index scale dimensions mismatch")
    entries = index.get("assignments")
    if not isinstance(entries, list) or len(entries) != config["expected_shards"]:
        raise ValueError("assignment index must contain exactly expected_shards entries")
    prepared_shards, seen_ids, seen_assignment_ids, seen_indexes = [], set(), set(), set()
    benchmark_owners = 0
    for entry in entries:
        if set(entry) != {"assignment_id", "path", "sha256"}:
            raise ValueError("assignment index entry fields differ from contract")
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("assignment path must remain inside the index directory")
        path = (index_path.parent / relative).resolve()
        if not path.is_relative_to(index_path.parent.resolve()):
            raise ValueError("assignment path escapes the index directory")
        if not path.is_file() or digest(path.read_bytes()) != entry["sha256"]:
            raise ValueError("assignment file checksum mismatch")
        prepared = load_scale_readiness(config_path, pilot_gate_path, path, root=root)
        assignment = prepared["assignment"]
        if (assignment["scale_id"] != index["scale_id"]
                or assignment["assignment_id"] != entry["assignment_id"]):
            raise ValueError("assignment identity differs from index")
        overlap = seen_ids & set(assignment["security_ids"])
        if overlap:
            raise ValueError(f"assignment shards overlap: {sorted(overlap)[:3]}")
        if assignment["assignment_id"] in seen_assignment_ids:
            raise ValueError("duplicate assignment_id in index")
        if assignment["shard_index"] in seen_indexes:
            raise ValueError("duplicate shard_index in index")
        seen_ids.update(assignment["security_ids"])
        seen_assignment_ids.add(assignment["assignment_id"])
        seen_indexes.add(assignment["shard_index"])
        benchmark_owners += int(assignment["include_benchmark"])
        prepared_shards.append(prepared)
    master_ids = {row["security_id"] for row in prepared_shards[0]["master_universe"]}
    if seen_ids != master_ids:
        missing, extra = sorted(master_ids - seen_ids), sorted(seen_ids - master_ids)
        raise ValueError(f"assignment union mismatch (missing={missing[:3]}, extra={extra[:3]})")
    if seen_indexes != set(range(1, config["expected_shards"] + 1)):
        raise ValueError("assignment shard_index set is incomplete")
    if benchmark_owners != 1:
        raise ValueError("exactly one assignment must own the benchmark")
    return index, prepared_shards


def verify_scale_handoff(config_path, pilot_gate_path, assignment_index_path,
                         run_index_path, *, root):
    """Verify five copied shard runs and raw checksums before canonical mapping."""
    root = Path(root).resolve()
    assignment_index, prepared_shards = load_assignment_index(
        config_path, pilot_gate_path, assignment_index_path, root=root)
    run_index_path = Path(run_index_path).resolve()
    run_index = read_json(run_index_path)
    if set(run_index) != {"scale_id", "runs"}:
        raise ValueError("run index fields differ from contract")
    if run_index["scale_id"] != assignment_index["scale_id"]:
        raise ValueError("run index scale_id mismatch")
    runs = run_index["runs"]
    if not isinstance(runs, list):
        raise ValueError("run index runs must be an array")
    run_by_assignment = {}
    run_ids = set()
    for item in runs:
        if set(item) != {"assignment_id", "run_id"}:
            raise ValueError("run index item fields differ from contract")
        if item["assignment_id"] in run_by_assignment or item["run_id"] in run_ids:
            raise ValueError("run index contains duplicate assignment_id or run_id")
        run_by_assignment[item["assignment_id"]] = item["run_id"]
        run_ids.add(item["run_id"])
    expected = {item["assignment_id"] for item in assignment_index["assignments"]}
    if set(run_by_assignment) != expected:
        raise ValueError("run index assignment set mismatch")
    shard_results, artifact_hashes = [], {}
    all_acquisition_complete = True
    for prepared in prepared_shards:
        assignment_id = prepared["assignment"]["assignment_id"]
        run_id = run_by_assignment[assignment_id]
        directory, manifest, gate = validate_completed_shard(prepared, run_id)
        all_acquisition_complete = all_acquisition_complete and manifest.get("status") in (
            "COMPLETE", "FAILED_GATE")
        for state in manifest["jobs"].values():
            for artifact in state["artifacts"]:
                artifact_hashes[artifact["raw_path"]] = artifact["sha256"]
        shard_results.append({
            "assignment_id": assignment_id, "run_id": run_id,
            "gate_status": gate.get("status"),
            "manifest_sha256": digest((directory / "manifest.json").read_bytes()),
            "gate_sha256": digest((directory / "gate.json").read_bytes()),
            "selected_symbols": manifest["aggregate"]["selected_symbols"],
            "usable_5y_symbols": manifest["aggregate"]["usable_5y_symbols"],
            "failed_symbols": manifest["aggregate"]["failed_symbols"],
        })
    handoff_id = new_artifact_id("m1-scale-handoff")
    output = root / "data" / "derived" / "m1_scale_handoff" / handoff_id
    checks = {
        "assignment_partition_exact": True, "run_set_exact": True,
        "job_definitions_exact": True, "provider_checksums_valid": True,
        "all_shard_acquisitions_complete": all_acquisition_complete,
        "central_qc_replay_required": True,
    }
    result = {
        "handoff_id": handoff_id, "scale_id": assignment_index["scale_id"],
        "status": "READY_FOR_CANONICAL_MAPPING" if all(checks.values()) else "BLOCKED",
        "created_at": utc_now(), "network_requests": 0, "checks": checks,
        "blocking_reasons": [key for key, value in checks.items() if not value],
        "config_sha256": assignment_index["config_sha256"],
        "universe_sha256": assignment_index["universe_sha256"],
        "pilot_gate_sha256": assignment_index["pilot_gate_sha256"],
        "assignment_index_sha256": digest(Path(assignment_index_path).read_bytes()),
        "run_index_sha256": digest(run_index_path.read_bytes()),
        "shards": sorted(shard_results, key=lambda item: item["assignment_id"]),
        "provider_artifact_hashes": dict(sorted(artifact_hashes.items())),
        "financial": {"pit_status": FINANCIAL_PIT_UNRESOLVED, "features_allowed": False},
    }
    write_json(output / "manifest.json", result)
    return output, result


def _unique_rows(rows, key, label):
    seen = {}
    for row in rows:
        value = key(row)
        if value in seen:
            raise ValueError(f"duplicate {label} key cannot be silently selected: {value}")
        seen[value] = row
    return [seen[value] for value in sorted(seen)]


def map_scale_handoff_candidates(config_path, pilot_gate_path, assignment_index_path,
                                  run_index_path, *, root):
    """Map verified shard raw artifacts into one offline canonical candidate set."""
    root = Path(root).resolve()
    handoff_dir, handoff = verify_scale_handoff(
        config_path, pilot_gate_path, assignment_index_path, run_index_path, root=root)
    if handoff["status"] != "READY_FOR_CANONICAL_MAPPING":
        raise ValueError("M1 handoff is not ready for canonical mapping")
    _, prepared_shards = load_assignment_index(
        config_path, pilot_gate_path, assignment_index_path, root=root)
    run_index = read_json(Path(run_index_path).resolve())
    run_by_assignment = {item["assignment_id"]: item["run_id"]
                         for item in run_index["runs"]}
    config = prepared_shards[0]["config"]
    universe_rows = prepared_shards[0]["master_universe"]
    universe = {row["ticker"]: row for row in universe_rows}
    kbs, cafef = defaultdict(list), defaultdict(list)
    raw_hashes, findings = {}, []
    latest_fetch = None
    for prepared in prepared_shards:
        assignment_id = prepared["assignment"]["assignment_id"]
        run_id = run_by_assignment[assignment_id]
        _, manifest, _ = validate_completed_shard(prepared, run_id)
        for state in manifest["jobs"].values():
            job = state["job"]
            for artifact in state["artifacts"]:
                payload = _raw_payload(root, run_id, artifact)
                raw_hashes[artifact["raw_path"]] = artifact["sha256"]
                latest_fetch = _latest_stamp(latest_fetch, _fetched_at(artifact))
                if job["kind"] in ("equity", "index"):
                    for raw in payload["data_day"]:
                        mapped = map_kbs_wire_ohlcv_row(
                            raw, job["symbol"], job["exchange"],
                            is_index=job["kind"] == "index")
                        if not _valid_kbs([mapped], index=job["kind"] == "index"):
                            findings.append({
                                "provider": "kbs", "symbol": job["symbol"],
                                "trade_date": mapped["trade_date"],
                                "row_status": "INVALID_REQUIRED_MARKET_ROW",
                                "classification": "PROVIDER_CONSTRAINT_VIOLATION",
                                "policy": "EXCLUDE_ROW", "safe": True,
                                "raw_path": artifact["raw_path"],
                                "raw_sha256": artifact["sha256"],
                                "mapped_row": mapped,
                            })
                            continue
                        kbs[job["symbol"]].append((mapped, artifact))
                elif job["kind"] == "reference_limits_value":
                    page = artifact.get("request", {}).get("page_index")
                    if not isinstance(page, int) or page < 1:
                        raise ValueError("CafeF replay artifact lacks page_index")
                    for row_index, raw in enumerate(payload["Data"]):
                        if classify_cafef_page_row(
                                raw.get("TradeDate"), page=page,
                                row_index=row_index) == "CURRENT_SNAPSHOT":
                            continue
                        mapped = map_trade_history_row(raw, job["symbol"], job["exchange"])
                        if not job["start"] <= mapped["trade_date"] <= job["end"]:
                            continue
                        eligible, row_findings = apply_invalid_row_policy(
                            [mapped], config["invalid_market_row_policy"])
                        findings.extend({
                            **item, "provider": "cafef",
                            "classification": (item["classification"] if item["safe"]
                                               else "AUXILIARY_PROVIDER_CONSTRAINT_VIOLATION"),
                            "policy": "EXCLUDE_ROW", "safe": True,
                            "raw_path": artifact["raw_path"],
                            "raw_sha256": artifact["sha256"],
                        } for item in row_findings)
                        cafef[job["symbol"]].extend((row, artifact) for row in eligible)

    run_id_out = new_artifact_id("m1-scale-candidate")
    target = root / "data" / "canonical" / run_id_out
    cafef_pairs = []
    for symbol, values in cafef.items():
        cafef_pairs.extend(((symbol, row["trade_date"]), row, artifact)
                           for row, artifact in values)
    cafef_by_key = {}
    for key, row, artifact in cafef_pairs:
        if key in cafef_by_key:
            raise ValueError(f"duplicate CafeF symbol/date cannot be selected: {key}")
        cafef_by_key[key] = (row, artifact)
    prices, benchmark, lineage = [], [], []
    for symbol, meta in sorted(universe.items()):
        values = kbs.get(symbol, [])
        if not values:
            raise ValueError(f"M1 symbol has no accepted KBS rows: {symbol}")
        observed_dates = [row["trade_date"] for row, _ in values]
        if _years(min(observed_dates), max(observed_dates)) < 3:
            raise ValueError(f"M1 symbol lacks three years after central QC: {symbol}")
        seen_dates = set()
        for row, artifact in values:
            if row["trade_date"] in seen_dates:
                raise ValueError(f"duplicate KBS symbol/date cannot be selected: {symbol}")
            seen_dates.add(row["trade_date"])
            reference = cafef_by_key.get((symbol, row["trade_date"]))
            cafe_row, cafe_artifact = reference if reference else (None, None)
            fetched = _fetched_at(artifact)
            raw_inputs = [{"provider": "kbs", "raw_path": artifact["raw_path"],
                           "sha256": artifact["sha256"], "fields": ["adj_close", "volume"]}]
            source_name = "kbs_delta_public_http"
            if cafe_row is not None:
                fetched = _latest_stamp(fetched, _fetched_at(cafe_artifact))
                source_name += "+cafef_direct"
                raw_inputs.append({"provider": "cafef", "raw_path": cafe_artifact["raw_path"],
                                   "sha256": cafe_artifact["sha256"],
                                   "fields": ["traded_value"]})
            prices.append({
                "security_id": meta["security_id"], "ticker": symbol,
                "exchange": meta["exchange"], "trade_date": row["trade_date"],
                "raw_open": None, "raw_high": None, "raw_low": None, "raw_close": None,
                "reference_price": None, "ceiling_price": None, "floor_price": None,
                "adj_close": row["close"], "adjustment_basis": "vendor_adjusted",
                "volume": row["volume"],
                "traded_value": cafe_row["traded_value"] if cafe_row else None,
                "trading_status": "normal" if row["volume"] is not None and row["volume"] > 0
                else "unknown", "available_at": f"{row['trade_date']}T{AVAILABILITY_TIME}",
                "source": source_name, "fetched_at": fetched, "data_version": run_id_out,
            })
            lineage.append({"table": "prices_daily",
                            "canonical_key": [meta["security_id"], row["trade_date"]],
                            "raw_inputs": raw_inputs})
    for row, artifact in kbs.get("VNINDEX", []):
        benchmark.append({
            "index_id": "VNINDEX", "trade_date": row["trade_date"], "close": row["close"],
            "total_return_level": None,
            "available_at": f"{row['trade_date']}T{AVAILABILITY_TIME}",
            "source": "kbs_delta_public_http", "fetched_at": _fetched_at(artifact),
            "data_version": run_id_out, "exchange": "HOSE", "index_basis": "price",
        })
        lineage.append({"table": "benchmark_daily",
                        "canonical_key": ["VNINDEX", row["trade_date"]],
                        "raw_inputs": [{"provider": "kbs", "raw_path": artifact["raw_path"],
                                        "sha256": artifact["sha256"], "fields": ["close"]}]})
    prices = _unique_rows(prices, lambda row: (row["security_id"], row["trade_date"]),
                          "prices_daily")
    benchmark = _unique_rows(benchmark, lambda row: (row["index_id"], row["trade_date"]),
                             "benchmark_daily")
    if not benchmark:
        raise ValueError("coordinator benchmark evidence is missing")
    calendar = _calendar(prices, run_id_out, latest_fetch)
    for name, rows in (("prices_daily", prices), ("benchmark_daily", benchmark),
                       ("trading_calendar", calendar)):
        validate_rows(name, rows)
    open_days = {(row["exchange"], row["trade_date"]) for row in calendar if row["is_open"]}
    if any((row["exchange"], row["trade_date"]) not in open_days for row in prices):
        raise ValueError("mapped price lacks an observed-session calendar row")
    identity_candidates = [{
        "security_id": row["security_id"], "ticker": row["ticker"],
        "exchange": row["exchange"], "sector": row["sector"],
        "listing_date": row["listing_date"], "company_name": None,
        "identity_status": "provisional", "canonical_eligible": False,
        "blocking_fields": ["company_name", "historical_exchange_interval_evidence"],
    } for row in universe_rows]
    write_rows(target / "candidates" / "prices_daily.jsonl", prices)
    write_rows(target / "candidates" / "benchmark_daily.jsonl", benchmark)
    write_rows(target / "candidates" / "trading_calendar.jsonl", calendar)
    write_rows(target / "candidates" / "identity_candidates.jsonl", identity_candidates)
    write_rows(target / "lineage" / "market.jsonl", lineage)
    write_rows(target / "quality" / "quarantined_rows.jsonl", findings)
    manifest = {
        "run_id": run_id_out, "scale_id": handoff["scale_id"],
        "source_handoff_id": handoff["handoff_id"], "status": "MAPPED_NOT_PROMOTED",
        "mapping_status": "PASS", "canonical_promotion_status": "BLOCKED",
        "feature_stage_ready": False, "network_requests": 0,
        "started_at": now(), "finished_at": now(), "schema_version": "1.4.0",
        "synthetic": False, "config_hash": prepared_shards[0]["config_hash"],
        "universe_hash": prepared_shards[0]["universe_hash"],
        "pilot_gate_hash": prepared_shards[0]["source_gate_hash"],
        "handoff_manifest_hash": digest((handoff_dir / "manifest.json").read_bytes()),
        "counts": {"selected_symbols": len(universe), "prices_daily": len(prices),
                   "benchmark_daily": len(benchmark), "trading_calendar": len(calendar),
                   "identity_candidates": len(identity_candidates),
                   "qc_rows_excluded": len(findings),
                   "kbs_rows_excluded": sum(item["provider"] == "kbs" for item in findings),
                   "cafef_rows_excluded": sum(item["provider"] == "cafef" for item in findings)},
        "checks": {"handoff_verified": True, "standard_market_schemas_valid": True,
                   "unique_price_keys": True, "calendar_relation_valid": True,
                   "raw_ohl_not_fabricated": True, "missing_preserved": True,
                   "invalid_rows_quarantined_with_raw_evidence": True,
                   "every_symbol_retains_three_years": True,
                   "network_zero": True, "canonical_securities_valid": False},
        "blocking_reasons": [
            "reviewed scale security master is required before canonical promotion",
            "historical identity remains observed-interval only",
        ],
        "financial": {"pit_status": FINANCIAL_PIT_UNRESOLVED, "features_allowed": False},
        "raw_artifact_hashes": dict(sorted(raw_hashes.items())),
    }
    manifest["artifacts"] = {
        path.relative_to(target).as_posix(): digest(path.read_bytes())
        for path in sorted(target.rglob("*.jsonl"))
    }
    write_json(target / "manifest.json", manifest)
    return target, manifest


def _load_scale_security_master(path, universe):
    path = Path(path).resolve()
    document = read_json(path)
    if (document.get("schema_version") != "1.0.0"
            or document.get("purpose") != "M1_SCALE_SECURITY_MASTER"
            or document.get("identity_scope") != "M1_OBSERVED_INTERVAL_ONLY"
            or document.get("identity_status") != "provisional"):
        raise ValueError("invalid M1 scale security-master identity contract")
    evidence = document.get("source_evidence", {})
    if (evidence.get("selected_row_count") != len(universe)
            or not isinstance(evidence.get("response_sha256"), str)
            or len(evidence["response_sha256"]) != 64
            or not isinstance(evidence.get("fetched_at"), str)):
        raise ValueError("invalid M1 security-master source evidence")
    datetime.fromisoformat(evidence["fetched_at"])
    rows = document.get("securities")
    if not isinstance(rows, list) or len(rows) != len(universe):
        raise ValueError("security master must contain the exact M1 universe")
    by_ticker = {}
    for row in rows:
        if set(row) != {"ticker", "company_name", "exchange", "instrument_type"}:
            raise ValueError("M1 security-master row fields differ from contract")
        if (row["ticker"] in by_ticker or row["instrument_type"] != "stock"
                or not isinstance(row["company_name"], str) or not row["company_name"].strip()):
            raise ValueError(f"invalid M1 security-master row: {row.get('ticker')}")
        by_ticker[row["ticker"]] = row
    expected = {row["ticker"]: row for row in universe}
    if set(by_ticker) != set(expected):
        raise ValueError("security-master ticker set differs from M1 universe")
    if any(row["exchange"] != expected[ticker]["exchange"]
           for ticker, row in by_ticker.items()):
        raise ValueError("security-master exchange differs from M1 universe")
    return path, document, by_ticker


def promote_scale_candidate(candidate_path, config_path, securities_path,
                            feature_config_path, *, root):
    """Promote one verified M1 candidate and build features centrally once."""
    root = Path(root).resolve()
    candidate_path = Path(candidate_path).resolve()
    canonical_root = (root / "data" / "canonical").resolve()
    if not candidate_path.is_relative_to(canonical_root):
        raise ValueError("M1 candidate path escapes data/canonical")
    parent_path = candidate_path / "manifest.json"
    parent = read_json(parent_path)
    if (parent.get("run_id") != candidate_path.name
            or parent.get("mapping_status") != "PASS"
            or parent.get("status") != "MAPPED_NOT_PROMOTED"
            or parent.get("network_requests") != 0):
        raise ValueError("promotion requires one immutable PASS M1 candidate")
    for relative, expected_hash in parent.get("artifacts", {}).items():
        path = candidate_path / relative
        if not path.is_file() or digest(path.read_bytes()) != expected_hash:
            raise ValueError(f"M1 candidate artifact checksum mismatch: {relative}")
    config_path = Path(config_path).resolve()
    config = read_json(config_path)
    if digest(config_path.read_bytes()) != parent["config_hash"]:
        raise ValueError("M1 promotion config hash mismatch")
    universe_path = _resolve(config_path.parent, config.get("universe_file"), "M1 universe_file")
    universe = read_json(universe_path)
    if digest(universe_path.read_bytes()) != parent["universe_hash"]:
        raise ValueError("M1 promotion universe hash mismatch")
    securities_path, security_master, by_ticker = _load_scale_security_master(
        securities_path, universe)
    prices = read_rows(candidate_path / "candidates" / "prices_daily.jsonl")
    benchmark = read_rows(candidate_path / "candidates" / "benchmark_daily.jsonl")
    calendar = read_rows(candidate_path / "candidates" / "trading_calendar.jsonl")
    run_id_out = new_artifact_id("canonical-m1-scale")
    target = canonical_root / run_id_out
    prices = [dict(row, data_version=run_id_out) for row in prices]
    benchmark = [dict(row, data_version=run_id_out) for row in benchmark]
    calendar = [dict(row, data_version=run_id_out) for row in calendar]
    for name, rows in (("prices_daily", prices), ("benchmark_daily", benchmark),
                       ("trading_calendar", calendar)):
        validate_rows(name, rows)
    first_observed = {}
    for row in prices:
        first_observed[row["security_id"]] = min(
            row["trade_date"], first_observed.get(row["security_id"], row["trade_date"]))
    fetched_at = datetime.fromisoformat(security_master["source_evidence"]["fetched_at"]).isoformat()
    securities = []
    for meta in universe:
        first_day = first_observed.get(meta["security_id"])
        if not first_day:
            raise ValueError(f"security lacks accepted market observation: {meta['ticker']}")
        master = by_ticker[meta["ticker"]]
        securities.append({
            "security_id": meta["security_id"], "ticker": meta["ticker"],
            "company_name": master["company_name"], "exchange": meta["exchange"],
            "listing_date": meta["listing_date"], "delisting_date": None,
            "valid_from": first_day, "valid_to": None,
            "available_at": f"{first_day}T{AVAILABILITY_TIME}", "sector": meta["sector"],
            "industry": None, "currency": "VND", "price_unit": "VND",
            "identity_status": "provisional",
            "source": "reviewed_scale_master+accepted_m1_market_observation",
            "fetched_at": fetched_at, "data_version": run_id_out,
        })
    securities.sort(key=lambda row: (row["security_id"], row["valid_from"]))
    validate_rows("securities", securities)
    feature_config_path = Path(feature_config_path).resolve()
    feature_config = read_json(feature_config_path)
    feature_config.update({"data_mode": "real", "vendor_run_id": parent["scale_id"],
                           "canonical_run_id": run_id_out})
    features = build_features({"securities": securities, "prices_daily": prices,
                               "benchmark_daily": benchmark,
                               "trading_calendar": calendar}, feature_config, run_id_out)
    validate_rows("feature_snapshots", features)
    latest = {}
    for row in features:
        if row["security_id"] not in latest or row["as_of_date"] > latest[row["security_id"]]["as_of_date"]:
            latest[row["security_id"]] = row
    required_features = feature_config["required_features"]
    latest_feature_complete = sum(
        all(row.get(name) is not None for name in required_features)
        for row in latest.values())
    latest_eligible = sum(row["universe_segment"] == "ELIGIBLE_FOR_CLUSTERING"
                          for row in latest.values())
    write_rows(target / "clean" / "securities.jsonl", securities)
    write_rows(target / "clean" / "prices_daily.jsonl", prices)
    write_rows(target / "clean" / "benchmark_daily.jsonl", benchmark)
    write_rows(target / "clean" / "trading_calendar.jsonl", calendar)
    write_rows(target / "features" / "monthly.jsonl", features)
    write_rows(target / "lineage" / "market.jsonl",
               read_rows(candidate_path / "lineage" / "market.jsonl"))
    checks = {
        "candidate_artifacts_valid": True, "standard_market_schemas_valid": True,
        "canonical_securities_valid": True,
        "exact_security_master_coverage": len(securities) == len(universe),
        "at_least_300_latest_features_eligible": latest_eligible >= 300,
        "network_zero": True,
    }
    gate_status = "PASS" if all(checks.values()) else "FAIL"
    manifest = {
        "run_id": run_id_out, "scale_id": parent["scale_id"],
        "parent_candidate_id": parent["run_id"], "status": "COMPLETE" if gate_status == "PASS"
        else "FAILED_GATE", "canonical_promotion_status": gate_status,
        "feature_stage_ready": gate_status == "PASS", "network_requests": 0,
        "started_at": now(), "finished_at": now(), "schema_version": "1.4.0",
        "synthetic": False, "config_hash": parent["config_hash"],
        "universe_hash": parent["universe_hash"], "pilot_gate_hash": parent["pilot_gate_hash"],
        "parent_manifest_hash": digest(parent_path.read_bytes()),
        "security_master_hash": digest(securities_path.read_bytes()),
        "feature_config_hash": digest(feature_config_path.read_bytes()),
        "counts": {"securities": len(securities), "prices_daily": len(prices),
                   "benchmark_daily": len(benchmark), "trading_calendar": len(calendar),
                   "feature_snapshots": len(features),
                   "latest_feature_complete_before_identity": latest_feature_complete,
                   "latest_feature_eligible": latest_eligible},
        "checks": checks,
        "remaining_limitations": [
            "identity intervals are retrospective observed intervals, not complete historical membership",
            "financial PIT remains unresolved and financial features remain disabled",
        ],
        "financial": {"pit_status": FINANCIAL_PIT_UNRESOLVED, "features_allowed": False},
    }
    manifest["artifacts"] = {
        path.relative_to(target).as_posix(): digest(path.read_bytes())
        for path in sorted(target.rglob("*.jsonl"))
    }
    write_json(target / "manifest.json", manifest)
    write_json(target / "gate.json", {
        "gate": M1_SCALE, "status": gate_status, "checks": checks,
        "blocking_reasons": [key for key, value in checks.items() if not value],
        "unlocks": [], "canonical_run_id": run_id_out,
        "financial_pit_status": FINANCIAL_PIT_UNRESOLVED,
        "financial_features_allowed": False,
    })
    return target, manifest
