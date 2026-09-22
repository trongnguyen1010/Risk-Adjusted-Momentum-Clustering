"""CLI runner for recovering historical prices for verified transition securities from Stage A6."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.transition_recovery import build_transition_recovery
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.vnstock import KBSPublicHttpSource


def _find_latest_a6_artifact(base_dir: Path) -> Path:
    candidates = sorted(base_dir.glob("m1-a6-identity-recovery-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        manifest_file = c / "manifest.json"
        if manifest_file.is_file():
            import json
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if data.get("status") == "PASS":
                return c
    raise FileNotFoundError("No PASS m1-a6-identity-recovery-* artifact found in artifacts/data_enrichment")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a6-artifact", help="Path to Stage A6 artifact directory (defaults to latest PASS)")
    parser.add_argument("--collection-start", default="2020-01-01", help="Collection start cutoff (default: 2020-01-01)")
    parser.add_argument("--batch-days", type=int, default=180, help="Days per request batch (default: 180)")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP request timeout in seconds")
    parser.add_argument("--min-interval", type=float, default=1.0, help="Minimum delay between HTTP requests in seconds")
    parser.add_argument("--execute", action="store_true", help="Required acknowledgement flag to execute network requests")

    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: Add --execute flag to acknowledge performing bounded KBS network requests.", file=sys.stderr)
        return 2

    base_dir = ROOT / "artifacts" / "data_enrichment"
    if args.a6_artifact:
        a6_dir = Path(args.a6_artifact)
        if not a6_dir.is_absolute():
            a6_dir = ROOT / a6_dir
    else:
        a6_dir = _find_latest_a6_artifact(base_dir)

    print(f"Using Stage A6 artifact: {a6_dir.name}")
    client = PublicJsonClient(timeout=args.timeout, attempts=3, min_interval=args.min_interval)
    provider = KBSPublicHttpSource(client=client)

    try:
        output_dir, manifest = build_transition_recovery(
            a6_dir,
            root=ROOT,
            provider=provider,
            collection_start=args.collection_start,
            batch_days=args.batch_days,
            progress=print,
        )
        print(f"\nSUCCESS: Stage {manifest['stage']} completed with status {manifest['status']}.")
        print(f"Candidates: {manifest['candidates_count']} | Requests: {manifest['total_requests']} | Rows: {manifest['rows_recovered']}")
        print(f"Output artifact directory: {output_dir}")
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
