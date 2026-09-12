"""Recover exact original bytes into a NEW snapshot; never repair in place."""
from pathlib import Path
import uuid

from ..io import atomic_write, digest, now, read_json, write_json
from .promotion import contained_file, verify_vendor


def recover_vendor(source: Path, policy_path: Path, root: Path) -> tuple[Path, dict]:
    """Use raw or SDK work cache only if bytes match the ORIGINAL manifest hash.

    Do not reserialize/recompute expected hashes, even for formatting-only changes.
    The original manifest is an audited integrity reference, not a signature.
    """
    source = Path(source).resolve()
    original_bytes = (source / "manifest.json").read_bytes()
    manifest = read_json(source / "manifest.json")
    policy = read_json(policy_path)
    payloads, recovered_from = {}, {}
    for job_id, state in manifest["jobs"].items():
        candidates = [contained_file(source, state["path"]), contained_file(source, "work/" + job_id + "-result.json")]
        match = next((p for p in candidates if p.exists() and digest(p.read_bytes()) == state["sha256"]), None)
        if match is None:
            raise ValueError("no exact verified original bytes available for " + job_id)
        payloads[state["path"]] = match.read_bytes()
        recovered_from[state["path"]] = match.relative_to(source).as_posix()
    run_id = "vendor-recovered-" + uuid.uuid4().hex[:12]
    target = Path(root).resolve() / "data/vendor" / run_id
    target.mkdir(parents=True, exist_ok=False)
    for relative, payload in payloads.items():
        atomic_write(contained_file(target, relative), payload)
    manifest.update(run_id=run_id, recovery=dict(original_run_id=source.name, original_manifest_sha256=digest(original_bytes),
                                                recovered_at=now(), recovered_from=recovered_from, method="copy exact bytes matching original expected SHA-256; no network"))
    write_json(target / "manifest.json", manifest)
    try:
        verify_vendor(target, policy)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        manifest.update(status="recovery_failed", recovery_error=str(exc))
        write_json(target / "manifest.json", manifest)
        raise ValueError("recovered snapshot metadata validation failed: " + str(target)) from exc
    return target, manifest
