"""Checkpoint each page; resume validates raw hashes and exact input configuration."""
import platform
import subprocess
import sys
import uuid
from pathlib import Path
from ..io import digest, encoded, read_json, write_json, atomic_write, now
from .. import __version__
from .sources.base import HttpClient, parse_csv, json_page, page_url


def crawl(config, root, resume=None):
    root = Path(root).resolve()
    jobs = config["jobs"]
    fingerprint = {"config": config, "csv_hashes": {j["id"]: digest((root / j["path"]).read_bytes()) for j in jobs if j["provider"] == "csv"}}
    config_hash = digest(encoded(fingerprint))
    run_id = resume or ("run-" + uuid.uuid4().hex[:12])
    if not run_id.replace("-", "").isalnum():
        raise ValueError("invalid run id")
    run_dir = root / "data" / "runs" / run_id
    manifest_path = run_dir / "manifest.json"
    if resume:
        manifest = read_json(manifest_path)
        if manifest["config_hash"] != config_hash:
            raise ValueError("resume config or CSV changed; create a new run")
        if manifest["code_hash"] != code_hash():
            raise ValueError("code changed; create a new run")
    else:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            commit = "unversioned"
        manifest = {"run_id": run_id, "data_version": run_id, "schema_version": "1.4.0", "started_at": now(), "config_hash": config_hash, "config": config,
                    "code_hash": code_hash(), "git_commit": commit, "python": sys.version, "platform": platform.platform(), "package_version": __version__,
                    "synthetic": config.get("synthetic", False), "jobs": {}, "status": "running"}
    manifest["status"] = "running"
    write_json(manifest_path, manifest)
    client = HttpClient(**config.get("http", {}))
    tables = {}
    for job in jobs:
        state = manifest["jobs"].setdefault(job["id"], {"pages": [], "status": "pending"})
        rows, cursor, visited = [], None, set()
        try:
            max_pages = 1 if job["provider"] == "csv" else job.get("max_pages", 100)
            for page in range(max_pages):
                if page < len(state["pages"]):
                    entry = state["pages"][page]
                    payload = (run_dir / entry["path"]).read_bytes()
                    if digest(payload) != entry["sha256"]:
                        raise ValueError("raw checksum mismatch; original snapshot has been modified")
                else:
                    if job["provider"] == "csv":
                        payload = (root / job["path"]).read_bytes()
                    elif job["provider"] == "http_json":
                        payload = client.get(page_url(job["endpoint"], job.get("params", {}), cursor, job.get("cursor_param", "cursor")), job.get("token_env"))
                    else:
                        raise ValueError("unsupported provider")
                    rel = f"raw/{job['id']}/page-{page:05d}.{'csv' if job['provider'] == 'csv' else 'json'}"
                    entry = {"path": rel, "sha256": digest(payload), "fetched_at": now(), "cursor": cursor, "bytes": len(payload)}
                    target = run_dir / rel
                    if target.exists() and digest(target.read_bytes()) != entry["sha256"]:
                        raise ValueError("uncheckpointed raw exists; create a new run")
                    atomic_write(target, payload)
                    state["pages"].append(entry)
                    write_json(manifest_path, manifest)
                if job["provider"] == "csv":
                    batch, cursor = parse_csv(payload), None
                else:
                    batch, cursor = json_page(payload, job.get("items_key", "items"), job.get("next_key", "next_cursor"))
                entry["rows"] = len(batch)
                rows.extend((row, job, entry["fetched_at"]) for row in batch)
                if cursor is None or cursor == "":
                    break
                if str(cursor) in visited:
                    raise ValueError("pagination cursor repeated")
                visited.add(str(cursor))
            else:
                raise ValueError("max_pages reached before pagination completed")
            if not rows and not job.get("allow_empty", False):
                raise ValueError("empty response for required job")
            state.update(status="complete", rows=len(rows))
            state.pop("error", None)
            tables.setdefault(job["table"], []).extend(rows)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            state.update(status="failed", error=type(exc).__name__ + ": " + str(exc))
        write_json(manifest_path, manifest)
    manifest["status"] = "downloaded" if all(j["status"] == "complete" for j in manifest["jobs"].values()) else "failed"
    manifest["finished_at"] = now()
    manifest["data_hash"] = digest(encoded({key: [p["sha256"] for p in value["pages"]] for key, value in sorted(manifest["jobs"].items())}))
    write_json(manifest_path, manifest)
    return run_dir, manifest, tables


def code_hash():
    package = Path(__file__).resolve().parents[1]
    return digest(b"".join(p.relative_to(package).as_posix().encode() + p.read_bytes() for p in sorted(package.rglob("*")) if p.suffix in (".py", ".json")))
