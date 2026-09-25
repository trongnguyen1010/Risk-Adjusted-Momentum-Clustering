"""Build and verify the machine-readable R1 repository-consolidation artifact."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

PARENT = "e149198986345bb02610e53d8a330f641b89df22"
ARTIFACT = Path("artifacts/repository/r1-consolidation-v1")
OUTPUTS = (
    "inventory_before.json",
    "deletion_inventory.csv",
    "inventory_after.json",
    "verification_summary.json",
)
ALL_ARTIFACT_PATHS = tuple(f"{ARTIFACT.as_posix()}/{name}" for name in (*OUTPUTS, "manifest.json"))
PROTECTED_PATHS = (
    "configs/data/cafef_c8_complete_only_v1.json",
    "configs/data/cafef_expansion_v1/index.json",
    "configs/data/cafef_supplemental_v1/index.json",
    "configs/data/identity_review_v1.json",
    "docs/CURRENT_STATUS.md",
    "scripts/build_cafef_c5_data_gate.py",
    "scripts/run_cafef_c8_complete_only.py",
    "scripts/verify_cafef_c8_results.py",
    "src/delta_t1/ingestion/cafef_c8.py",
    "src/delta_t1/ingestion/cafef_c8_verify.py",
    "tests/unit/ingestion/test_cafef_c8.py",
    "tests/unit/ingestion/test_cafef_c8_verify.py",
)


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8").strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def inventory(paths: set[str], label: str) -> dict:
    top = Counter(path.split("/", 1)[0] for path in paths)
    extensions = Counter(Path(path).suffix.lower() or "<none>" for path in paths)
    return {
        "label": label,
        "tracked_files": len(paths),
        "markdown_files": sum(path.lower().endswith(".md") for path in paths),
        "python_files": sum(path.lower().endswith(".py") for path in paths),
        "test_files": sum(path.startswith("tests/") for path in paths),
        "config_files": sum(path.startswith("configs/") for path in paths),
        "artifact_files": sum(path.startswith("artifacts/") for path in paths),
        "by_top_level": dict(sorted(top.items())),
        "by_extension": dict(sorted(extensions.items())),
        "paths": sorted(paths),
    }


def deletion_metadata(path: str) -> tuple[str, str]:
    if path == "tests/unit/ingestion/test_research_demo_sources.py":
        return "TEST_RENAME", "renamed to test_cafef_source.py and reduced to active CafeF coverage"
    if path.startswith("docs/crawl/plans/"):
        return "CRAWL_PLAN_HISTORY", "superseded execution plan; retained in Git history"
    if path.startswith("docs/crawl/m1_scale/"):
        return "WORKER_RUNBOOK_HISTORY", "completed worker handoff documentation"
    if path.startswith("docs/crawl/sources/"):
        return "SOURCE_DISCOVERY_HISTORY", "superseded source comparison/discovery note"
    if path.startswith("docs/"):
        return "DOCUMENTATION_CONSOLIDATION", "duplicate or superseded active documentation"
    if path.startswith("configs/"):
        return "OBSOLETE_CONFIG", "completed or superseded stage configuration"
    if path.startswith("scripts/"):
        return "OBSOLETE_RUNNER", "completed stage runner or one-off diagnostic"
    if path.startswith("src/"):
        return "SUPERSEDED_IMPLEMENTATION", "implementation no longer used by active paths"
    if path.startswith("tests/"):
        return "OBSOLETE_TEST", "test dedicated to retired implementation"
    if path.startswith("notebooks/"):
        return "EDA_NOTEBOOK", "superseded generated EDA notebook"
    if path.startswith("evidence/"):
        return "LEGACY_RECOVERY_EVIDENCE", "completed recovery evidence retained in Git history"
    if path.startswith("requirements-"):
        return "LEGACY_DEPENDENCY_LOCK", "dependency lock for retired legacy collector"
    return "OTHER_SUPERSEDED", "not required by active post-C8 repository"


def verify_manifest_directory(directory: Path) -> int:
    manifest = read_json(directory / "manifest.json")
    outputs = manifest.get("outputs", {})
    failures = [
        relative for relative, expected in outputs.items()
        if not (directory / relative).is_file()
        or sha256_file(directory / relative) != expected
    ]
    if failures:
        raise ValueError(f"artifact hash mismatch in {directory}: {failures}")
    return len(outputs)


def verify_c8_integrity(root: Path) -> dict:
    heavy = root / "artifacts/cafef_primary/cafef-c8-complete-only-v1"
    compact = root / "artifacts/cafef_primary/cafef-c8-verify-v1"
    heavy_manifest_path = heavy / "manifest.json"
    heavy_manifest = read_json(heavy_manifest_path)
    if heavy_manifest.get("git_commit") != "d60c8cba49c90b3b36c346dfea463a1e4f659ee1":
        raise ValueError("unexpected C8 implementation commit")
    heavy_count = verify_manifest_directory(heavy)
    compact_count = verify_manifest_directory(compact)
    compact_manifest = read_json(compact / "manifest.json")
    heavy_hash = sha256_file(heavy_manifest_path)
    if compact_manifest.get("parent_c8_manifest_sha256") != heavy_hash:
        raise ValueError("compact verifier parent C8 manifest hash mismatch")
    references = {
        "artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2/manifest.json":
            heavy_manifest["c5_manifest_sha256"],
        "artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/manifest.json":
            heavy_manifest["c7_manifest_sha256"],
        "configs/data/identity_review_v1.json": heavy_manifest["identity_review_sha256"],
    }
    for relative, expected in references.items():
        if sha256_file(root / relative) != expected:
            raise ValueError(f"C8 reference hash mismatch: {relative}")
    incoming = root / "data/handoffs/cafef_expansion_v1/incoming"
    zip_checks = {}
    for name, expected in sorted(heavy_manifest["source_zip_sha256"].items()):
        actual = sha256_file(incoming / name)
        if actual != expected:
            raise ValueError(f"source ZIP hash mismatch: {name}")
        zip_checks[name] = actual
    if len(zip_checks) != 5:
        raise ValueError("expected exactly five immutable source ZIPs")
    summary = read_json(compact / "verification_summary.json")
    expected_headline = {
        "candidate_count": 952,
        "feature_complete": 922,
        "market_feature_ready_v2": 905,
        "latest253_incomplete": 30,
        "historical_identity_ready": 0,
        "research_ready": 0,
        "deferred_expansion_count": 148,
    }
    for key, expected in expected_headline.items():
        if summary["headline"].get(key) != expected:
            raise ValueError(f"C8 headline changed: {key}")
    return {
        "status": "PASS",
        "heavy_manifest_sha256": heavy_hash,
        "heavy_output_hashes_verified": heavy_count,
        "compact_output_hashes_verified": compact_count,
        "source_zip_hashes": zip_checks,
        "headline": expected_headline,
    }


def build(root: Path) -> None:
    before = set(run_git("ls-tree", "-r", "--name-only", PARENT).splitlines())
    after = set(filter(None, run_git("ls-files").splitlines()))
    after.update(ALL_ARTIFACT_PATHS)
    deleted = sorted(before - after)
    added = sorted(after - before)
    if len(before) != 400:
        raise ValueError(f"unexpected before count: {len(before)}")
    if len(deleted) != 193:
        raise ValueError(f"unexpected deletion count: {len(deleted)}")
    missing = [path for path in PROTECTED_PATHS if path not in after]
    if missing:
        raise ValueError(f"protected active paths missing: {missing}")

    ARTIFACT.mkdir(parents=True, exist_ok=True)
    write_json(ARTIFACT / "inventory_before.json", inventory(before, f"git:{PARENT}"))
    with (ARTIFACT / "deletion_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "category", "reason"), lineterminator="\n")
        writer.writeheader()
        for path in deleted:
            category, reason = deletion_metadata(path)
            writer.writerow({"path": path, "category": category, "reason": reason})
    write_json(ARTIFACT / "inventory_after.json", inventory(after, "R1 intended index"))

    c8 = verify_c8_integrity(root)
    category_counts = Counter(deletion_metadata(path)[0] for path in deleted)
    summary = {
        "stage": "R1_REPOSITORY_CONSOLIDATION",
        "status": "PASS",
        "parent_commit": PARENT,
        "before_tracked_files": len(before),
        "after_tracked_files": len(after),
        "removed_paths": len(deleted),
        "retired_files": len(deleted) - 1,
        "renamed_test_files": 1,
        "added_files": len(added),
        "deletion_categories": dict(sorted(category_counts.items())),
        "protected_paths_present": True,
        "c8_integrity": c8,
        "results_unchanged": True,
        "scope_confirmations": {
            "methodology_changed": False,
            "heavy_c8_rerun": False,
            "network_requests": 0,
            "supplemental_acquisition_run": False,
            "clustering_run": False,
            "backtest_run": False,
            "git_history_is_archive": True,
        },
        "next_stage": "M2-PREP — MARKET-ONLY EXPERIMENT PROTOCOL",
    }
    write_json(ARTIFACT / "verification_summary.json", summary)
    manifest = {
        "artifact_id": "r1-consolidation-v1",
        "stage": "R1_REPOSITORY_CONSOLIDATION",
        "parent_commit": PARENT,
        "outputs": {name: sha256_file(ARTIFACT / name) for name in OUTPUTS},
    }
    write_json(ARTIFACT / "manifest.json", manifest)


def verify_existing(root: Path) -> None:
    manifest = read_json(ARTIFACT / "manifest.json")
    if manifest.get("parent_commit") != PARENT:
        raise ValueError("R1 parent commit mismatch")
    for name, expected in manifest.get("outputs", {}).items():
        if sha256_file(ARTIFACT / name) != expected:
            raise ValueError(f"R1 artifact hash mismatch: {name}")
    summary = read_json(ARTIFACT / "verification_summary.json")
    if summary.get("status") != "PASS" or summary.get("removed_paths") != 193:
        raise ValueError("R1 verification summary is not PASS")
    expected_paths = set(read_json(ARTIFACT / "inventory_after.json")["paths"])
    actual_paths = set(filter(None, run_git("ls-files").splitlines()))
    if actual_paths != expected_paths:
        raise ValueError("R1 after-inventory no longer matches the Git index")
    verify_c8_integrity(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        raise SystemExit(f"run from repository root: {root}")
    if args.verify_existing:
        verify_existing(root)
        print("R1 verification: PASS")
    else:
        build(root)
        print(f"R1 artifact written: {ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
