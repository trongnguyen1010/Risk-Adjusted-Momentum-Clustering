"""CLI runner to build Canonical Enriched Dataset v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.canonical_enriched_v2 import build_canonical_enriched_v2

DEFAULT_CANONICAL = "data/canonical/canonical-m1-scale-20260921T045028Z-19da7c61"


def _find_latest_pass_dir(base_dir: Path, prefix: str) -> Path:
    candidates = sorted(base_dir.glob(f"{prefix}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        manifest_file = c / "manifest.json"
        if manifest_file.is_file():
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if data.get("status") == "PASS":
                return c
    raise FileNotFoundError(f"No PASS {prefix}* artifact found in {base_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", default=DEFAULT_CANONICAL, help="Baseline canonical directory")
    parser.add_argument("--a6-artifact", help="Path to PASS Stage A6 artifact (defaults to latest PASS)")
    parser.add_argument("--transition-artifact", help="Path to PASS transition recovery artifact (defaults to latest PASS)")
    parser.add_argument("--execute", action="store_true", help="Required acknowledgement flag to build Canonical v2")

    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: Add --execute flag to acknowledge building Canonical Enriched Dataset v2.", file=sys.stderr)
        return 2

    canonical_dir = ROOT / args.canonical if not Path(args.canonical).is_absolute() else Path(args.canonical)
    base_enrichment = ROOT / "artifacts" / "data_enrichment"

    a6_dir = Path(args.a6_artifact) if args.a6_artifact else _find_latest_pass_dir(base_enrichment, "m1-a6-identity-recovery-")
    if not a6_dir.is_absolute():
        a6_dir = ROOT / a6_dir

    trans_dir = Path(args.transition_artifact) if args.transition_artifact else _find_latest_pass_dir(base_enrichment, "m1-transition-recovery-")
    if not trans_dir.is_absolute():
        trans_dir = ROOT / trans_dir

    print(f"Canonical baseline: {canonical_dir.name}")
    print(f"Stage A6 artifact:  {a6_dir.name}")
    print(f"Transition artifact: {trans_dir.name}")

    try:
        output_dir, manifest = build_canonical_enriched_v2(
            canonical_dir,
            a6_dir,
            trans_dir,
            root=ROOT,
            progress=print,
        )
        print(f"\nSUCCESS: Canonical Enriched Dataset v2 created successfully!")
        print(f"Canonical ID: {manifest['canonical_id']}")
        print(f"Total Securities: {manifest['total_security_count']}")
        print(f"Total Price Rows: {manifest['total_price_rows']} (Updated with true exchange: {manifest['identity_updated_rows']})")
        print(f"Output Directory: {output_dir}")
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
