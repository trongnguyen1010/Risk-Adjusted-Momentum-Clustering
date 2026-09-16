"""Optional Vnstock 4.x adapter; provider records remain immutable staging data."""
import importlib.metadata
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from ...artifact_ids import new_artifact_id
from ...contracts import validate_rows
from ...io import atomic_write, digest, encoded, now, read_json, write_json
from ..crawler import code_hash
from .base import contained_file


def date_batches(start, end, days=180):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or days < 1:
        raise ValueError("invalid date range/batch size")
    while first <= last:
        stop = min(first + timedelta(days=days - 1), last)
        yield first.isoformat(), stop.isoformat()
        first = stop + timedelta(days=1)


def worker(job_path, output_path):
    from vnstock import Market, Reference
    job = read_json(job_path)
    if job["kind"] == "listing":
        frame = Reference().equity.list_by_exchange(source="kbs")
    else:
        market = Market()
        asset = market.index(job["symbol"]) if job["kind"] == "index" else market.equity(job["symbol"])
        frame = asset.ohlcv(start=job["start"], end=job["end"], interval="1D", count=None,
                            source="kbs", get_all=True, floating=None)
    if frame is None or not hasattr(frame, "to_json"):
        raise ValueError("SDK did not return a DataFrame")
    records = json.loads(frame.to_json(orient="records", date_format="iso"))
    if not records:
        raise ValueError("empty vendor result; review listing dates/range")
    document = {"job": job, "fetched_at": now(),
                "vnstock_version": importlib.metadata.version("vnstock"),
                "source_routing": "kbs",
                "sdk_metadata": {str(key): str(value) for key, value in frame.attrs.items()},
                "columns": list(frame.columns), "records": records}
    validate_rows("vendor_snapshot", [document])
    write_json(output_path, document)


def collect(root, start, end, symbols, resume=None, interval=5.0, timeout=90,
            attempts=3, gate_report_path=None):
    import time
    gate_hash = None
    symbol_count = len(set(symbols))
    if 60 < symbol_count < 300:
        raise ValueError("61–299 symbols is not an M1 gate stage; use 50–60 pilot or >=300 scale")
    if symbol_count > 5:
        if not gate_report_path:
            raise ValueError("more than 5 symbols requires an explicit passing M1 gate report")
        gate_path = Path(gate_report_path).resolve()
        report = read_json(gate_path)
        if symbol_count <= 60:
            accepted = (report.get("gate") == "SOURCE_SMOKE" and report.get("status") == "PASS"
                        and "REPRESENTATIVE_PILOT" in report.get("unlocks", []))
            error = "source smoke has not passed; representative pilot crawl blocked"
        else:
            accepted = (report.get("gate") == "REPRESENTATIVE_PILOT" and report.get("status") == "PASS"
                        and "M1_SCALE" in report.get("unlocks", []))
            error = "representative pilot has not passed; scale crawl blocked"
        if (not accepted or report.get("checks", {}).get("real_data") is not True
                or not report.get("input_evidence_hashes")):
            raise ValueError(error)
        gate_hash = digest(gate_path.read_bytes())
    if interval < 1 or timeout < 1 or not 1 <= attempts <= 5:
        raise ValueError("interval >= 1 second, timeout > 0, attempts between 1 and 5")
    try:
        version = importlib.metadata.version("vnstock")
    except importlib.metadata.PackageNotFoundError:
        raise ValueError('Install optional dependency: python -m pip install "vnstock==4.0.6"') from None
    if version != "4.0.6":
        raise ValueError("Adapter targets vnstock 4.0.6; verify another version before changing the pin")
    if not symbols or any(not symbol.isalnum() or len(symbol) > 12 for symbol in symbols):
        raise ValueError("provide explicit alphanumeric symbols")
    config = dict(start=start, end=end, symbols=sorted(set(symbols)), interval=interval,
                  timeout=timeout, attempts=attempts, vnstock_version=version, code_hash=code_hash())
    if gate_hash:
        config["gate_report_hash"] = gate_hash
    config_hash = digest(encoded(config))
    run_id = resume or new_artifact_id("vendor-pilot")
    if not run_id.replace("-", "").isalnum():
        raise ValueError("invalid run id")
    target = Path(root).resolve() / "data" / "vendor" / run_id
    manifest_path = target / "manifest.json"
    if resume:
        manifest = read_json(manifest_path)
        if manifest["config_hash"] != config_hash:
            raise ValueError("vendor config/code changed; start a new run")
    else:
        manifest = dict(run_id=run_id, config=config, config_hash=config_hash,
                        started_at=now(), status="running", synthetic=False,
                        data_mode="real", jobs={})
    write_json(manifest_path, manifest)
    jobs = [{"id": "listing", "kind": "listing"}]
    for symbol in [*sorted(set(symbols)), "VNINDEX"]:
        for start_day, end_day in date_batches(start, end):
            jobs.append(dict(id=f"{symbol}-{start_day}-{end_day}",
                             kind="index" if symbol == "VNINDEX" else "equity",
                             symbol=symbol, start=start_day, end=end_day))
    for job in jobs:
        output = target / "raw" / (job["id"] + ".json")
        state = manifest["jobs"].setdefault(job["id"], {})
        if state.get("status") == "complete":
            if not output.exists() or digest(output.read_bytes()) != state["sha256"]:
                raise ValueError("vendor raw checksum mismatch")
            continue
        job_path = target / "work" / (job["id"] + ".json")
        work_output = target / "work" / (job["id"] + "-result.json")
        write_json(job_path, job)
        state.update(status="failed", job=job)
        for attempt in range(attempts):
            time.sleep(interval if attempt == 0 else max(interval, 2 ** attempt))
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "delta_t1.ingestion.sources.vnstock", str(job_path), str(work_output)],
                    timeout=timeout, cwd=job_path.parent,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                if result.returncode != 0:
                    state["error"] = f"SDK worker exit {result.returncode}; inspect SDK installation/access separately"
                    continue
                payload = work_output.read_bytes()
                document = json.loads(payload)
                if not document["records"]:
                    raise ValueError("empty SDK result")
                if output.exists() and output.read_bytes() != payload:
                    raise ValueError("uncheckpointed raw exists; create a new vendor run")
                atomic_write(output, payload)
                state.update(status="complete", sha256=digest(payload),
                             path=output.relative_to(target).as_posix(), rows=len(document["records"]),
                             fetched_at=document["fetched_at"])
                state.pop("error", None)
                break
            except subprocess.TimeoutExpired:
                state["error"] = "SDK request exceeded timeout"
        write_json(manifest_path, manifest)
    manifest.update(
        status="complete" if all(state["status"] == "complete" for state in manifest["jobs"].values()) else "failed",
        finished_at=now(),
        limitations=["SDK snapshot, not HTTP wire response", "Raw/adjusted price meaning not yet audited",
                     "Current listing is not historical universe", "No automatic canonical promotion"],
    )
    write_json(manifest_path, manifest)
    return target, manifest


def verify_vendor(directory: Path, policy: dict) -> tuple[dict, list[dict]]:
    """Verify a complete Vnstock envelope before normalization."""
    directory = Path(directory).resolve()
    manifest = read_json(directory / "manifest.json")
    if manifest["status"] != "complete" or manifest["run_id"] != directory.name:
        raise ValueError("vendor run must be complete and match directory")
    config = manifest["config"]
    if digest(encoded(config)) != manifest["config_hash"]:
        raise ValueError("vendor config checksum mismatch")
    if config["code_hash"] not in policy.get("approved_crawler_hashes", []):
        raise ValueError("unreviewed crawler code hash")
    if policy.get("policy_version") != "1.0" or policy.get("envelope_schema_version") != "1.0.0":
        raise ValueError("unsupported policy/envelope schema version")
    if bool(manifest["synthetic"]) != policy.get("synthetic"):
        raise ValueError("synthetic/real policy mismatch")
    if config["vnstock_version"] != policy.get("vnstock_version"):
        raise ValueError("unreviewed SDK version")
    started, finished = datetime.fromisoformat(manifest["started_at"]), datetime.fromisoformat(manifest["finished_at"])
    documents = []
    expected = {"listing"}
    for symbol in sorted(set(config["symbols"]) | {"VNINDEX"}):
        expected.update(f"{symbol}-{first}-{last}" for first, last in date_batches(config["start"], config["end"]))
    if set(manifest["jobs"]) != expected:
        raise ValueError("vendor job plan incomplete or unexpected")
    for key, state in sorted(manifest["jobs"].items()):
        path = contained_file(directory, state["path"])
        if state["status"] != "complete" or digest(path.read_bytes()) != state["sha256"]:
            raise ValueError("vendor raw checksum/status mismatch: " + key)
        document = read_json(path)
        validate_rows("vendor_snapshot", [document])
        if (document["job"] != state["job"] or document["job"]["id"] != key
                or len(document["records"]) != state["rows"]):
            raise ValueError("vendor job/row count mismatch: " + key)
        if (document["source_routing"] != policy.get("source_routing")
                or document["vnstock_version"] != config["vnstock_version"]):
            raise ValueError("vendor source/SDK mismatch")
        stamp = datetime.fromisoformat(document["fetched_at"])
        if not started <= stamp <= finished:
            raise ValueError("crawl timestamp outside manifest interval")
        if document["sdk_metadata"].get("source", "").lower() != document["source_routing"]:
            raise ValueError("SDK metadata source mismatch")
        if (len(document["columns"]) != len(set(document["columns"]))
                or any(not isinstance(record, dict) or set(record) != set(document["columns"])
                       for record in document["records"])):
            raise ValueError("record columns differ from envelope")
        if document["job"]["kind"] != "listing":
            if (document["sdk_metadata"].get("symbol") != document["job"]["symbol"]
                    or document["sdk_metadata"].get("interval") != "1D"):
                raise ValueError("SDK symbol/interval mismatch")
        documents.append(document)
    if not documents:
        raise ValueError("empty vendor manifest")
    return manifest, documents


if __name__ == "__main__":
    worker(sys.argv[1], sys.argv[2])
