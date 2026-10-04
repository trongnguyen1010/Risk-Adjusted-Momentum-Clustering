"""Immutable experiment input verification, manifests and source snapshots."""
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

from ..artifact_ids import new_artifact_id
from ..contracts import validate_rows
from ..ingestion.crawler import code_hash
from ..ingestion.sources.base import contained_file
from ..io import digest, encoded, now, read_json, read_rows, write_json


REQUIRED_DATA_ARTIFACTS = {
    "features/monthly.jsonl",
    "clean/prices_daily.jsonl",
    "clean/securities.jsonl",
    "clean/trading_calendar.jsonl",
    "clean/benchmark_daily.jsonl",
}

C8_MARKET_ONLY_FEATURES = "canonical/feature_snapshots.jsonl"
C8_MARKET_ONLY_EXECUTION_VERSION = "c8-complete-only-v1"


def load_verified_market_only_features(
        data_run: Path, snapshot_dates: set[str] | tuple[str, ...] | list[str]) -> tuple[dict, list[dict]]:
    """Load selected C8 feature snapshots without applying the strict M3 identity gate.

    The C8 artifact uses a different immutable layout from legacy data runs.  Its own
    manifest checksum is verified before any rows are returned.  This adapter is
    deliberately limited to feature snapshots and does not claim historical identity,
    point-in-time financial readiness, or strict-research readiness.
    """
    data_run = Path(data_run).resolve()
    manifest_path = contained_file(data_run, "manifest.json")
    source = read_json(manifest_path)
    if (source.get("execution_version") != C8_MARKET_ONLY_EXECUTION_VERSION
            or source.get("artifact_id") != "cafef-c8-complete-only-v1"):
        raise ValueError("verified C8 complete-only artifact required for M2 market-only")
    expected = source.get("outputs", {}).get(C8_MARKET_ONLY_FEATURES)
    if not isinstance(expected, str):
        raise ValueError("C8 manifest missing feature snapshot checksum")
    feature_path = contained_file(data_run, C8_MARKET_ONLY_FEATURES)
    if digest(feature_path.read_bytes()) != expected:
        raise ValueError("data artifact checksum mismatch: " + C8_MARKET_ONLY_FEATURES)

    wanted = set(snapshot_dates)
    rows = []
    with feature_path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("as_of_date") in wanted:
                    rows.append(row)
    validate_rows("feature_snapshots", rows)
    found = {row["as_of_date"] for row in rows}
    if found != wanted:
        raise ValueError("C8 feature snapshot(s) missing: " + ", ".join(sorted(wanted - found)))
    versions = {row["data_version"] for row in rows}
    if len(versions) != 1:
        raise ValueError("C8 market-only input must have one data version")
    normalized_source = dict(
        source,
        run_id=source["artifact_id"],
        data_version=next(iter(versions)),
        synthetic=False,
        market_only=True,
        historical_identity_verified=False,
    )
    return normalized_source, rows


def load_verified_data_run(data_run: Path, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    data_run = Path(data_run).resolve()
    source = read_json(data_run / "manifest.json")
    if source["status"] != "complete" or source["synthetic"] != config["synthetic"]:
        raise ValueError("completed data run with matching synthetic label required")
    feature_rf = source.get("config", {}).get("features", {}).get("rf_annual")
    if feature_rf is not None and feature_rf != config["rf_annual"]:
        raise ValueError("feature and performance risk-free assumptions must agree")
    if not REQUIRED_DATA_ARTIFACTS <= source["artifacts"].keys():
        raise ValueError("data run missing required checksummed artifacts")
    for relative, expected in source["artifacts"].items():
        if digest(contained_file(data_run, relative).read_bytes()) != expected:
            raise ValueError("data artifact checksum mismatch: " + relative)
    tables = {path.stem: read_rows(path) for path in (data_run / "clean").glob("*.jsonl")}
    for name, rows in tables.items():
        validate_rows(name, rows)
    if not source["synthetic"]:
        allowed_identity = {"verified"}
        if config.get("pilot") and config.get("identity_method") == "provisional_verified_for_pilot":
            allowed_identity.add("provisional_verified_for_pilot")
        if (not config.get("point_in_time_evidence")
                or any(row["identity_status"] not in allowed_identity for row in tables["securities"])):
            raise ValueError("real research needs verified historical master and PIT evidence")
        if any(not row.get("available_at") for row in tables["trading_calendar"]):
            raise ValueError("real calendar requires available_at")
        if any(row.get("index_basis") not in ("price", "total_return") for row in tables["benchmark_daily"]):
            raise ValueError("real benchmark convention unresolved")
    return source, tables


def start_experiment(root: Path, data_run: Path, source: dict, config: dict) -> tuple[Path, dict]:
    run_id = config.get("run_id") or new_artifact_id("experiment")
    output_dir = config.get("output_dir") or config.get("output_directory")
    if not output_dir and (
        config.get("protocol_scope") == "m2_market_only_v1"
        or str(config.get("stage", "")).startswith("M2_")
    ):
        algo = config.get("clustering", {}).get("algorithm") or config.get("clustering", {}).get("baseline")
        if config.get("stage") == "M2_TASK_11_HOLDOUT" or (
            config.get("start") == "2026-02-27" and config.get("end") == "2026-08-28"
        ):
            output_dir = "M2/artifacts/m2-final-holdout-v1"
        elif algo == "ward":
            output_dir = "M2/artifacts/m2-task5-ward-v1"
        elif algo == "pca_kmeans":
            output_dir = "M2/artifacts/m2-task6-pca-kmeans-v1"
        elif algo == "kmeans":
            output_dir = "M2/artifacts/m2-task4-kmeans-baseline-v1"

    if output_dir:
        custom = Path(output_dir)
        target = custom if custom.is_absolute() else Path(root).resolve() / custom
    else:
        target = Path(root).resolve() / "data/experiments" / run_id
    # A frozen run, including a notebook-repaired v2, must never be overwritten.
    target.mkdir(parents=True, exist_ok=False)
    package = Path(__file__).parents[1]
    with zipfile.ZipFile(target / "source_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob("*")):
            if path.suffix in (".py", ".json"):
                archive.write(path, "delta_t1/" + path.relative_to(package).as_posix())
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                         stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unversioned"
    manifest = dict(
        run_id=run_id,
        status="running",
        config=config,
        config_hash=digest(encoded(config)),
        data_version=source["data_version"],
        data_run_path=str(Path(data_run).resolve()),
        vendor_run_id=source.get("vendor_run_id"),
        source_manifest_hash=digest((Path(data_run).resolve() / "manifest.json").read_bytes()),
        code_hash=code_hash(),
        git_commit=commit,
        random_seed=config["clustering"].get("seed"),
        timestamp=now(),
        environment=dict(python=sys.version, platform=platform.platform(),
                         packages={item.metadata["Name"]: item.version for item in importlib.metadata.distributions()}),
        synthetic=config["synthetic"],
        data_mode="synthetic" if config["synthetic"] else "real",
        canonical_run_id=source.get("canonical_run_id"),
        methodology=source.get("methodology", {}),
        real_pilot_accepted=False,
    )
    write_json(target / "manifest.json", manifest)
    return target, manifest


def finish_experiment(target: Path, manifest: dict) -> None:
    manifest["finished_at"] = now()
    manifest["artifacts"] = {
        path.relative_to(target).as_posix(): digest(path.read_bytes())
        for path in sorted(target.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    write_json(target / "manifest.json", manifest)
