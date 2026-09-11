"""Optional source discovery using the documented vnstock 4.x Unified UI.

Keep SDK-returned columns intact. These are vendor staging records, not canonical
prices: raw/adjusted semantics and historical identities require a separate audit.
"""
import importlib.metadata
import json
import subprocess
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path
from ..io import now, digest, encoded, read_json, write_json, atomic_write
from .crawler import code_hash
from ..contracts import validate_rows


def date_batches(start, end, days=180):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or days < 1:
        raise ValueError("invalid date range/batch size")
    while first <= last:
        stop = min(first + timedelta(days=days - 1), last)
        yield first.isoformat(), stop.isoformat()
        first = stop + timedelta(days=1)


def worker(job_path, output_path):
    # Isolating SDK calls prevents SDK retries, exits or hangs from killing a run.
    from vnstock import Market, Reference
    job = read_json(job_path)
    if job["kind"] == "listing":
        df = Reference().equity.list_by_exchange(source="kbs")
    else:
        market = Market()
        asset = market.index(job["symbol"]) if job["kind"] == "index" else market.equity(job["symbol"])
        # Unified UI defaults count=100 even with explicit dates; disable that cap.
        df = asset.ohlcv(start=job["start"], end=job["end"], interval="1D", count=None,
                         source="kbs", get_all=True, floating=None)
    if df is None or not hasattr(df, "to_json"):
        raise ValueError("SDK did not return a DataFrame")
    records = json.loads(df.to_json(orient="records", date_format="iso"))
    if not records:
        raise ValueError("empty vendor result; review listing dates/range")
    document = {"job": job, "fetched_at": now(), "vnstock_version": importlib.metadata.version("vnstock"),
                "source_routing": "kbs", "sdk_metadata": {str(k): str(v) for k,v in df.attrs.items()},
                "columns": list(df.columns), "records": records}
    validate_rows("vendor_snapshot", [document])
    write_json(output_path, document)


def collect(root, start, end, symbols, resume=None, interval=5.0, timeout=90, attempts=3):
    import time
    if interval < 1 or timeout < 1 or not 1 <= attempts <= 5:
        raise ValueError("interval >= 1 second, timeout > 0, attempts between 1 and 5")
    try:
        version = importlib.metadata.version("vnstock")
    except importlib.metadata.PackageNotFoundError:
        raise ValueError('Install optional dependency: python -m pip install "vnstock==4.0.6"') from None
    if version != "4.0.6":
        raise ValueError("Adapter targets vnstock 4.0.6; verify another version before changing the pin")
    if not symbols or any(not s.isalnum() or len(s) > 12 for s in symbols):
        raise ValueError("provide explicit alphanumeric symbols")
    config = dict(start=start, end=end, symbols=sorted(set(symbols)), interval=interval, timeout=timeout, attempts=attempts, vnstock_version=version, code_hash=code_hash())
    config_hash = digest(encoded(config))
    run_id = resume or "vendor-" + uuid.uuid4().hex[:12]
    if not run_id.replace("-", "").isalnum():
        raise ValueError("invalid run id")
    target = Path(root).resolve() / "data" / "vendor" / run_id
    manifest_path = target / "manifest.json"
    if resume:
        manifest = read_json(manifest_path)
        if manifest["config_hash"] != config_hash:
            raise ValueError("vendor config/code changed; start a new run")
    else:
        manifest = dict(run_id=run_id, config=config, config_hash=config_hash, started_at=now(), status="running", synthetic=False, jobs={})
    write_json(manifest_path, manifest)
    jobs = [{"id": "listing", "kind": "listing"}]
    for symbol in [*sorted(set(symbols)), "VNINDEX"]:
        for a,b in date_batches(start,end):
            jobs.append(dict(id=f"{symbol}-{a}-{b}",kind="index" if symbol=='VNINDEX' else 'equity',symbol=symbol,start=a,end=b))
    for job in jobs:
        output = target / "raw" / (job["id"] + ".json")
        state = manifest["jobs"].setdefault(job["id"], {})
        if state.get("status") == "complete":
            if not output.exists() or digest(output.read_bytes()) != state["sha256"]:
                raise ValueError("vendor raw checksum mismatch")
            continue
        job_path, work_output = target / "work" / (job["id"] + ".json"), target / "work" / (job["id"] + "-result.json")
        write_json(job_path, job)
        state.update(status="failed", job=job)
        for attempt in range(attempts):
            time.sleep(interval if attempt == 0 else max(interval, 2 ** attempt))
            try:
                result = subprocess.run([sys.executable, "-m", "delta_t1.ingestion.vnstock", str(job_path), str(work_output)], timeout=timeout,
                                        cwd=job_path.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode != 0:
                    state["error"] = f"SDK worker exit {result.returncode}; inspect SDK installation/access separately"
                    continue
                payload = work_output.read_bytes()
                doc = json.loads(payload)
                if not doc["records"]:
                    raise ValueError("empty SDK result")
                if output.exists() and output.read_bytes() != payload:
                    raise ValueError("uncheckpointed raw exists; create a new vendor run")
                atomic_write(output, payload)
                state.update(status="complete", sha256=digest(payload), path=output.relative_to(target).as_posix(), rows=len(doc["records"]), fetched_at=doc["fetched_at"])
                state.pop("error", None)
                break
            except subprocess.TimeoutExpired:
                state["error"] = "SDK request exceeded timeout"
        write_json(manifest_path, manifest)
    manifest.update(status="complete" if all(s["status"] == "complete" for s in manifest["jobs"].values()) else "failed", finished_at=now(),
                    limitations=["SDK snapshot, not HTTP wire response", "Raw/adjusted price meaning not yet audited", "Current listing is not historical universe", "No automatic canonical promotion"])
    write_json(manifest_path, manifest)
    return target, manifest


if __name__ == "__main__":
    worker(sys.argv[1], sys.argv[2])
