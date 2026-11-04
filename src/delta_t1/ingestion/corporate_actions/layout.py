"""Inventory and verify a non-destructive corporate-action folder consolidation."""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath

TAGS = ("corporate_action", "hnx_", "vci_calendar", "vnstock_auth", "vnstock_env",
        "dtp_asg", "asg_prospectus", "abb_aas", "abb_public", "cached_corporate", "gsp_kpf")
TMP_PREFIXES = ("ca_", "hnx_", "vci_", "vnstock_", "delta-hnx", "delta-vci", "delta-vnstock")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root, relative):
    rel = PureWindowsPath(relative)
    if rel.drive or rel.root or ".." in rel.parts:
        raise ValueError("PATH_OUTSIDE_WORKSPACE")
    return root.joinpath(*rel.parts)


def make_plan(root):
    root = root.resolve()
    entries = []
    groups = [
        ("scripts", "scripts/corporate_actions/legacy_sources"),
        ("src/delta_t1/ingestion", "src/delta_t1/ingestion/corporate_actions/legacy_sources"),
        ("configs/data", "configs/data/corporate_actions"),
        ("src/delta_t1/schemas", "src/delta_t1/schemas/corporate_actions"),
        ("tests/unit/ingestion", "tests/unit/ingestion/corporate_actions/legacy_sources"),
    ]
    for old, new in groups:
        for p in sorted((root / old).iterdir()):
            if p.is_file() and any(tag in p.name.lower() for tag in TAGS):
                target = root / new / p.name
                entries.append({"kind": "MOVE_FILE_KEEP_HARDLINK", "old": p.relative_to(root).as_posix(),
                    "new": target.relative_to(root).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size})
    extra_files = {"audit_ca_pit_20261101.py", "run_ca_c8_v2_full.py", "seal_ca_c8_v2_checkpoint.py"}
    for p in sorted((root / "tmp").iterdir()):
        if p.is_dir() and p.name.startswith(TMP_PREFIXES):
            # Keep immutable artifact directories physically in place. Some
            # sealed helper scripts derive ROOT from __file__.resolve().parents.
            # A new junction points TO that old directory, never the reverse.
            entries.append({"kind": "NEW_DIRECTORY_JUNCTION", "old": p.relative_to(root).as_posix(),
                "new": f"data/corporate_actions/work/legacy_tmp/{p.name}",
                "directory_file_id": p.stat().st_ino,
                "top_manifest_sha256": sha(p / "manifest.json") if (p / "manifest.json").is_file() else None})
        elif p.is_file() and (p.name.startswith("ca_") or p.name in extra_files):
            entries.append({"kind": "MOVE_FILE_KEEP_HARDLINK", "old": p.relative_to(root).as_posix(),
                "new": f"data/corporate_actions/work/legacy_tmp/_loose_files/{p.name}",
                "sha256": sha(p), "bytes": p.stat().st_size})
    for old, new in [("configs/data/certificates", "configs/data/corporate_actions/certificates"),
        ("tests/fixtures/corporate_actions_v1", "tests/fixtures/corporate_actions/corporate_actions_v1"),
        ("tests/fixtures/hnx_tls", "tests/fixtures/corporate_actions/hnx_tls")]:
        p = root / old
        if p.is_dir():
            entries.append({"kind": "NEW_DIRECTORY_JUNCTION", "old": old, "new": new,
                "directory_file_id": p.stat().st_ino,
                "top_manifest_sha256": sha(p / "manifest.json") if (p / "manifest.json").is_file() else None})
    for entry in entries:
        source, target = inside(root, entry["old"]), inside(root, entry["new"])
        if target.exists():
            raise FileExistsError("TARGET_ALREADY_EXISTS:" + entry["new"])
        if source.is_symlink() or source.is_junction():
            raise ValueError("ALREADY_LINKED_SOURCE_REQUIRES_REVIEW:" + entry["old"])
    return {"stage": "CORPORATE_ACTION_FOLDER_CONSOLIDATION_V1", "workspace": str(root),
        "network_requests": 0, "raw_contents_modified": False,
        "strategy": "Move loose code/config files with same-file hardlinks at old paths; expose immutable artifact folders through NEW junctions pointing to unchanged OLD folders.",
        "entries": entries}


def verify_plan(root, plan):
    counts = {"files_verified": 0, "junctions_verified": 0, "top_manifests_verified": 0, "same_file_bytes": 0}
    for entry in plan["entries"]:
        old, new = inside(root, entry["old"]), inside(root, entry["new"])
        if not os.path.samefile(old, new):
            raise ValueError("NOT_SAME_FILE_OR_DIRECTORY:" + entry["old"])
        if entry["kind"] == "MOVE_FILE_KEEP_HARDLINK":
            if sha(old) != entry["sha256"] or sha(new) != entry["sha256"]:
                raise ValueError("CONTENT_CHANGED:" + entry["old"])
            counts["files_verified"] += 1
            counts["same_file_bytes"] += entry["bytes"]
        else:
            if not new.is_junction() or new.resolve() != old.resolve() or old.stat().st_ino != entry["directory_file_id"]:
                raise ValueError("BAD_JUNCTION_DIRECTION_OR_DIRECTORY_ID")
            counts["junctions_verified"] += 1
            if entry["top_manifest_sha256"]:
                if sha(new / "manifest.json") != entry["top_manifest_sha256"]:
                    raise ValueError("ARTIFACT_MANIFEST_CHANGED")
                counts["top_manifests_verified"] += 1
    return {"status": "PASS", **counts, "network_requests": 0, "old_paths_preserved": True,
        "immutable_directories_relocated": 0, "private_state_relocated": False}
