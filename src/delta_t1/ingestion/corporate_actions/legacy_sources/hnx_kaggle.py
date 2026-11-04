"""Portable HNX work assignments and Kaggle environment diagnostics; no PIT changes."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import platform
import shutil
import ssl
import sys
import time
import zipfile
from urllib.request import build_opener, HTTPSHandler

from .corporate_action_sources import PublicTransport, SourceLimitation, now, sha
from .hnx_announcement_batch import run_batch, write, read, verify_artifact
from .hnx_announcement_discovery import profile_context
from .hnx_tls import validated_hnx_context
from .sources.base import NoRedirect

CANONICAL = Path("artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl")
PROFILE = "https://www.hnx.vn/vi-vn/cophieu-etfs/chi-tiet-chung-khoan-ny-PVS.html"


def audit_assignments(root):
    canonical_bytes = (root / CANONICAL).read_bytes()
    canonical = [json.loads(s) for s in canonical_bytes.decode("utf-8").splitlines() if s]
    tickers = {r["ticker"]: r for r in canonical}
    if len(tickers) != len(canonical):
        raise ValueError("CANONICAL_TICKER_NOT_UNIQUE")
    ownership, reports, references = {}, [], []
    verified_files = 0
    def checked(folder, name, manifest):
        nonlocal verified_files
        body = (folder / name).read_bytes()
        if manifest["files"].get(name) != sha(body):
            raise ValueError("OLD_ARTIFACT_CHECKSUM_MISMATCH: " + str(folder / name))
        verified_files += 1
        return json.loads(body.decode("utf-8"))
    for index in range(4):
        folder = root / f"data/corporate_actions/work/outputs/batch_shard_{index}"
        manifest = read(folder / "manifest.json")
        results = checked(folder, "batch_results.json", manifest)
        counts, errors, examples = Counter(), Counter(), []
        for item in results["results"]:
            ticker = item["ticker"]
            if ticker not in tickers or ticker in ownership:
                raise ValueError("OLD_SHARD_DUPLICATE_OR_UNKNOWN_TICKER: " + ticker)
            ownership[ticker] = index
            for receipt in checked(folder, f"source_receipts/{ticker}/requests.json", manifest):
                from urllib.parse import urlsplit
                host = urlsplit(receipt["url"]).hostname
                counts[host + ":" + str(receipt.get("status", "NO_HTTP_RESPONSE"))] += 1
                if receipt.get("error"):
                    reason = "SSL_CERTIFICATE_VERIFY_FAILED" if "CERTIFICATE_VERIFY_FAILED" in receipt["error"] else receipt["error"]
                    errors[host + ":" + reason] += 1
                    if len(examples) < 2:
                        examples.append({"ticker": ticker, **receipt})
        reports.append({"shard_index": index, "new_tickers": len(results["results"]),
                        "physical_requests": results["physical_requests"], "cache_hits": results.get("cache_hits", 0),
                        "receipt_occurrences": sum(counts.values()), "request_statuses": dict(counts),
                        "request_errors": dict(errors), "error_examples": examples})
        references.append({"path": str(folder), "manifest_sha256": sha((folder / "manifest.json").read_bytes())})
    bootstrap = root / "tmp/ca_c8_v2_checkpoint_20261101_v5"
    manifest = read(bootstrap / "manifest.json")
    initial = checked(bootstrap, "resume_state.json", manifest)["processed_securities"]
    references.append({"path": str(bootstrap), "manifest_sha256": sha((bootstrap / "manifest.json").read_bytes())})
    if len(initial) != len(set(initial)) or set(initial) & ownership.keys() or set(initial) | ownership.keys() != tickers.keys():
        raise ValueError("BOOTSTRAP_SHARD_UNION_NOT_EXACT_CANONICAL")
    original_new = len(ownership)
    order = sorted(canonical, key=lambda r: (r["security_id"], r.get("valid_from") or "", r.get("valid_to") or "", r["exchange"]))
    positions = {r["ticker"]: i for i, r in enumerate(order)}
    for ticker in initial:
        ownership[ticker] = positions[ticker] % 4
    assignments = []
    for index in range(4):
        members = sorted(t for t, owner in ownership.items() if owner == index)
        hnx = [t for t in members if tickers[t]["exchange"] in {"HNX", "UPCOM"}]
        assignments.append({"schema_version": "1.0.0", "shard_index": index, "shard_count": 4,
                            "canonical_sha256": sha(canonical_bytes), "all_tickers": members, "hnx_tickers": hnx,
                            "legacy_manifest_sha256s": {Path(r["path"]).name: r["manifest_sha256"] for r in references},
                            "bootstrap_tickers": sorted(set(members) & set(initial)),
                            "meaning": "Old shard ownership preserved; bootstrap assigned once by full canonical security_id order. Source work only, not historical identity."})
    ssl_errors = sum(sum(v for k, v in r["request_errors"].items() if k.endswith(":SSL_CERTIFICATE_VERIFY_FAILED")) for r in reports)
    audit = {"scope": "Four legacy shards; bootstrap counted separately once", "canonical_rows": len(canonical),
             "new_unique_tickers": original_new, "bootstrap_tickers": len(initial), "union_tickers": len(ownership),
             "duplicate_new_tickers": 0, "inspected_file_hashes_verified": verified_files, "references": references,
             "by_shard": reports, "ssl_failed_requests": ssl_errors,
             "physical_requests_reported": sum(r["physical_requests"] for r in reports),
             "cache_hits_reported": sum(r["cache_hits"] for r in reports),
             "request_receipt_occurrences": sum(r["receipt_occurrences"] for r in reports),
             "diagnosis": {"confirmed": "HNX TLS local-issuer validation failures before HTTP; VSDC/HOSE success in same shards.",
                           "not_proven": "Kaggle platform causality, old image/OpenSSL/CA configuration, server chain or route-specific certificate differences.",
                           "collector_gaps": "Old HNX/HOSE calendars did not provide full notices; VSDC clock parsing and source time semantics are independent of platform.",
                           "environment_evidence_missing": "Historical Python/OpenSSL/CA paths and image metadata; current preflight cannot reconstruct old environment."},
             "decision": "Keep all raw/checkpoints separate; union ownership index only, no canonical/data merge."}
    return audit, assignments


def preflight(output, *, transport_factory=PublicTransport, tls_report=None):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    output.mkdir(parents=True)
    environment = {"recorded_at": now(), "python": sys.version, "platform": platform.platform(), "openssl": ssl.OPENSSL_VERSION,
                   "default_verify_paths": ssl.get_default_verify_paths()._asdict(),
                   "ca_environment": {k: os.environ.get(k) for k in ["SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE"]},
                   "proxy_configured": any(os.environ.get(k) for k in ["HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"]),
                   "account_ip_relationship": "Not inferred; no external public-IP service contacted."}
    environment["tls_chain_configuration"] = tls_report or {"mode": "SYSTEM_DEFAULT"}
    context_error = None
    try:
        context = ssl.create_default_context()
        environment.update(verify_mode=int(context.verify_mode), check_hostname=context.check_hostname,
                           verify_flags=int(context.verify_flags), cert_store_stats=context.cert_store_stats())
    except (OSError, ValueError) as exc:
        context_error = str(exc)
        environment["context_creation_error"] = context_error
    try:
        import certifi
        environment["certifi"] = {"path": certifi.where(), "sha256": sha(Path(certifi.where()).read_bytes()), "used_as_override": False}
    except (ImportError, OSError):
        environment["certifi"] = None
    write(output / "environment.json", environment)
    client = transport_factory(output, max_requests=1, interval=2, timeout=15)
    limitation = context_error
    try:
        if context_error:
            raise SourceLimitation("SSL_CONTEXT_CREATION_FAILED: " + context_error)
        html, _ = client.fetch(PROFILE)
        profile_context(html, "PVS", "HNX")
    except (SourceLimitation, OSError, ValueError) as exc:
        limitation = str(exc)
    result = {"status": "PASS_CURRENT_ENVIRONMENT_ONLY" if limitation is None else "BLOCKED_PREFLIGHT",
              "limitation": limitation, "network_requests": len(client.requests), "url": PROFILE,
              "tls_verification": True, "historical_kaggle_cause": "NOT_DETERMINED", "canonical_build": False}
    write(output / "requests.json", client.requests); write(output / "result.json", result)
    write(output / "manifest.json", {"artifact_type": "hnx-kaggle-preflight-v1",
                                     "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()}})
    return result


def run_kaggle(project, index, *, collect=False, max_requests=1000, max_seconds=3600):
    """Fixed Linux work root keeps archived absolute references valid on session restore."""
    project = project.resolve()
    if index not in range(4):
        raise ValueError("INVALID_SHARD_INDEX")
    assignment = read(project / f"assignments/shard_{index}.json")
    if sha((project / CANONICAL).read_bytes()) != assignment["canonical_sha256"] or assignment["shard_index"] != index:
        raise ValueError("ASSIGNMENT_CANONICAL_MISMATCH")
    interval = 8  # Four independent job slots keep average offered load conservative; not a shared stop mechanism.
    parents = sorted((project / f"kaggle_runs/shard_{index}").glob("run-*/collection"))
    previous = parents[-1] if parents else None
    kwargs = {"tickers": assignment["hnx_tickers"], "max_requests": max_requests, "max_seconds": max_seconds}
    if previous:
        kwargs["resume_from"] = previous
    # Validate prior source-stop/contract/checksum state before any new preflight request.
    dry = run_batch(project / CANONICAL, project / "unused-dry-run", dry_run=True, **kwargs)
    parent = project / f"kaggle_runs/shard_{index}" / ("run-" + now().replace(":", "").replace("+", "_"))
    parent.mkdir(parents=True, exist_ok=False)
    write(parent / "context.json", {"shard_index": index, "assignment": assignment,
                                   "actual_minimum_interval_seconds": interval, "dry_run_scope_tickers": dry["scope_tickers"],
                                   "old_raw_inputs": "Not uploaded; retained locally; fresh HNX detail supplementation only."})
    try:
        tls_context, tls_report = validated_hnx_context(project, parent / "tls_chain")
    except SourceLimitation as exc:
        return {"preflight": {"status": "BLOCKED_TLS_CHAIN_PREPARATION", "limitation": str(exc), "network_requests": 0},
                "collection_started": False, "output": str(parent)}
    def factory(path, **options):
        options["interval"] = interval
        return PublicTransport(path, opener=build_opener(NoRedirect(), HTTPSHandler(context=tls_context)), **options)
    result = preflight(parent / "preflight", transport_factory=factory, tls_report=tls_report)
    if result["limitation"] or not collect:
        return {"preflight": result, "collection_started": False, "output": str(parent)}
    time.sleep(interval)
    result = run_batch(project / CANONICAL, parent / "collection", transport_factory=factory,
                       progress=lambda item: print(json.dumps(item, ensure_ascii=False), flush=True), **kwargs)
    return {"preflight": "PASS", "collection_started": True, "output": str(parent / "collection"), "result": result}


def build_bundle(root, output):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    audit, assignments = audit_assignments(root)
    output.mkdir(parents=True)
    project = output / "project"; project.mkdir()
    shutil.copytree(root / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (project / "scripts").mkdir()
    shutil.copyfile(root / "scripts/run_hnx_kaggle_v1.py", project / "scripts/run_hnx_kaggle_v1.py")
    for relative in [CANONICAL, Path("configs/data/hnx_batch_v1.json"), Path("configs/data/hnx_tls_chain_v1.json"),
                     Path("configs/data/certificates/globalsign_gcc_r3_ev_tls_ca_2025.pem")]:
        (project / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, project / relative)
    (project / "assignments").mkdir()
    for index, assignment in enumerate(assignments):
        write(project / f"assignments/shard_{index}.json", assignment)
    write(output / "audit.json", audit)
    write(project / "ownership_summary.json", {"canonical_rows": audit["canonical_rows"], "legacy_new_unique": audit["new_unique_tickers"],
                                               "legacy_bootstrap": audit["bootstrap_tickers"], "shards": [
                                                   {"index": a["shard_index"], "all": len(a["all_tickers"]), "hnx": len(a["hnx_tickers"]), "bootstrap": a["bootstrap_tickers"]} for a in assignments]})
    write(project / "bundle_manifest.json", {"artifact_type": "hnx-kaggle-input-v1",
                                             "files": {p.relative_to(project).as_posix(): sha(p.read_bytes()) for p in sorted(project.rglob("*")) if p.is_file()}})
    pinned = sha((project / "bundle_manifest.json").read_bytes())
    archive = output / "delta-hnx-kaggle.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(project.rglob("*")):
            if path.is_file(): z.write(path, path.relative_to(project).as_posix())
    for index in range(4):
        notebook = make_notebook(index, pinned)
        write(output / f"DELTA_HNX_Shard_{index}.ipynb", notebook)
    return {"output": str(output), "bundle": str(archive), "bundle_manifest_sha256": pinned,
            "scope_tickers": sum(len(a["hnx_tickers"]) for a in assignments), "audit": audit,
            "assignments": [{"shard_index": a["shard_index"], "all": len(a["all_tickers"]), "hnx": len(a["hnx_tickers"]), "bootstrap": len(a["bootstrap_tickers"])} for a in assignments]}


def export_state(project, destination, index):
    if destination.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(destination))
    files = {p.relative_to(project).as_posix(): sha(p.read_bytes()) for p in project.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p != project / "state_manifest.json"}
    state = {"artifact_type": "hnx-kaggle-state-v1", "shard_index": index, "project_root": str(project.resolve()),
             "bundle_manifest_sha256": sha((project / "bundle_manifest.json").read_bytes()), "files": files}
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files): archive.write(project / name, name)
        archive.writestr("state_manifest.json", json.dumps(state, ensure_ascii=False, indent=2))


def make_notebook(index, pinned):
    config = f'''from pathlib import Path
SHARD_INDEX = {index}
RUN_COLLECTION = False  # False: chẩn đoán môi trường; True: thu thập sau khi preflight PASS
MAX_REQUESTS = 1000
MAX_SECONDS = 3600
WORK = Path('/kaggle/working/delta-hnx')
EXPECTED_BUNDLE_SHA256 = {pinned!r}
'''
    bootstrap = '''import hashlib, json, sys, zipfile
from pathlib import PurePosixPath
digest = lambda data: hashlib.sha256(data).hexdigest()
if not WORK.exists():
    all_states = list(Path('/kaggle/input').rglob('delta-hnx-state-s*-*.zip'))
    states = list(Path('/kaggle/input').rglob(f'delta-hnx-state-s{SHARD_INDEX}-*.zip'))
    if all_states and not states:
        raise RuntimeError('INPUT_STATE_BELONGS_TO_ANOTHER_SHARD')
    archives = states or list(Path('/kaggle/input').rglob('delta-hnx-kaggle.zip'))
    z = None
    if archives:
        if len(archives) != 1:
            raise RuntimeError('Attach đúng một input ZIP hoặc một state ZIP gần nhất của shard này.')
        z = zipfile.ZipFile(archives[0])
        if len(z.namelist()) != len(set(z.namelist())):
            raise RuntimeError('ZIP_DUPLICATE_NAMES_REJECTED')
        for info in z.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or '..' in name.parts or chr(92) in info.filename or ':' in info.filename or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise RuntimeError('ZIP_PATH_OR_SYMLINK_REJECTED')
        names = set(z.namelist())
        read_blob = z.read
    else:
        roots = [p.parent for p in Path('/kaggle/input').rglob('bundle_manifest.json')]
        state_roots = [p for p in roots if (p/'state_manifest.json').is_file()]
        own_states = [p for p in state_roots if json.loads((p/'state_manifest.json').read_text())['shard_index'] == SHARD_INDEX]
        if state_roots and not own_states:
            raise RuntimeError('INPUT_STATE_BELONGS_TO_ANOTHER_SHARD')
        roots = own_states or roots
        if len(roots) != 1:
            raise RuntimeError('Không tìm được một input/state root duy nhất; kiểm tra Add Input.')
        source_root = roots[0]
        names = {p.relative_to(source_root).as_posix() for p in source_root.rglob('*') if p.is_file()}
        read_blob = lambda name: (source_root/name).read_bytes()
    manifest_bytes = read_blob('bundle_manifest.json')
    if digest(manifest_bytes) != EXPECTED_BUNDLE_SHA256:
        raise RuntimeError('BUNDLE_MANIFEST_MISMATCH')
    manifest = json.loads(manifest_bytes)
    files = dict(manifest['files'])
    if 'state_manifest.json' in names:
        state = json.loads(read_blob('state_manifest.json'))
        if state['shard_index'] != SHARD_INDEX or state['project_root'] != str(WORK) or state['bundle_manifest_sha256'] != EXPECTED_BUNDLE_SHA256:
            raise RuntimeError('STATE_SHARD_OR_ROOT_MISMATCH')
        for name, expected in manifest['files'].items():
            if digest(read_blob(name)) != expected:
                raise RuntimeError('INPUT_CHECKSUM_MISMATCH: ' + name)
        files = state['files']
    for name, expected in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or ':' in name or chr(92) in name:
            raise RuntimeError('MANIFEST_PATH_REJECTED')
        if name.endswith('.py') and name not in manifest['files']:
            raise RuntimeError('UNPINNED_CODE_IN_STATE_REJECTED')
        if digest(read_blob(name)) != expected:
            raise RuntimeError('CHECKSUM_MISMATCH: ' + name)
    WORK.mkdir(parents=True, exist_ok=False)
    for name in set(files) | {'bundle_manifest.json'}:
        target = WORK/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(read_blob(name))
    if z is not None:
        z.close()
if digest((WORK/'bundle_manifest.json').read_bytes()) != EXPECTED_BUNDLE_SHA256:
    raise RuntimeError('EXISTING_WORKSPACE_BUNDLE_MISMATCH')
for name, expected in json.loads((WORK/'bundle_manifest.json').read_text())['files'].items():
    if digest((WORK/name).read_bytes()) != expected:
        raise RuntimeError('WORKSPACE_INPUT_CHECKSUM_MISMATCH: ' + name)
assignment = json.loads((WORK/f'assignments/shard_{SHARD_INDEX}.json').read_text())
print({'shard': SHARD_INDEX, 'full_assignment': len(assignment['all_tickers']), 'hnx_upcom_jobs': len(assignment['hnx_tickers'])})
'''
    execute = '''import subprocess
from datetime import datetime, timezone
sys.path.insert(0, str(WORK/'src'))
from delta_t1.ingestion.hnx_kaggle import export_state
command = [sys.executable, str(WORK/'scripts/run_hnx_kaggle_v1.py'), '--shard-index', str(SHARD_INDEX),
           '--max-requests', str(MAX_REQUESTS), '--max-seconds', str(MAX_SECONDS)]
if RUN_COLLECTION:
    command.append('--collect')
try:
    result = subprocess.run(command, cwd=WORK)
    print('Collector exit code:', result.returncode)
finally:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    exported = Path(f'/kaggle/working/delta-hnx-state-s{SHARD_INDEX}-{stamp}.zip')
    export_state(WORK, exported, SHARD_INDEX)
    print('TẢI FILE NÀY VỀ / ATTACH CHO LƯỢT TIẾP:', exported)
'''
    intro = (f"# DELTA — HNX supplemental shard {index}\n\n"
             "CPU, Internet ON. Lần đầu để RUN_COLLECTION=False để chẩn đoán TLS. "
             "Sau khi PASS mới đổi True. Mỗi notebook xử lý shard riêng; giữ nguyên index. "
             "Tuân thủ hạn mức tài khoản; không đổi IP để retry source block. "
             "Delay thực tế 8 giây/job; không có shared limiter/stop giữa các notebook. "
             "Nếu một job gặp 401/403/429/challenge, dừng các job HNX còn lại. "
             "Mỗi state ZIP cần giữ nguyên để resume; không bật GPU hoặc cài thêm package.\n")
    cells = [{"cell_type": "markdown", "metadata": {}, "source": intro.splitlines(keepends=True)}]
    for source in [config, bootstrap, execute]:
        cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)})
    return {"nbformat": 4, "nbformat_minor": 4, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "cells": cells}
