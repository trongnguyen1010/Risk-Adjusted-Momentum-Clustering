"""Immutable experiment input verification, manifests and source snapshots."""
import importlib.metadata
from pathlib import Path
import platform
import subprocess
import sys
import uuid
import zipfile

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
    run_id = "experiment-" + uuid.uuid4().hex[:12]
    target = Path(root).resolve() / "data/experiments" / run_id
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
