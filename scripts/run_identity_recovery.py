"""Run Stage A6 offline historical identity recovery."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.identity_recovery import build_stage_a6

DEFAULT_CANONICAL = "data/canonical/canonical-m1-scale-20260921T045028Z-19da7c61"
DEFAULT_A1 = "artifacts/data_enrichment/m1-a1-missing-session-audit-20260921T045214Z-b0e8d931"
DEFAULT_A2 = "artifacts/data_enrichment/m1-a2-local-salvage-20260921T055528Z-fa20fb55"
DEFAULT_A3 = "artifacts/data_enrichment/m1-a3-primary-recovery-20260921T063753Z-83435f0d"
DEFAULT_A4 = "artifacts/data_enrichment/m1-a4-secondary-recovery-20260921T071048Z-bf7619eb"


def _path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", default=DEFAULT_CANONICAL)
    parser.add_argument("--a1-artifact", default=DEFAULT_A1)
    parser.add_argument("--a2-artifact", default=DEFAULT_A2)
    parser.add_argument("--a3-artifact", default=DEFAULT_A3)
    parser.add_argument("--a4-artifact", default=DEFAULT_A4)
    parser.add_argument("--evidence-file",
                        help="Reviewed local JSON/JSONL/CSV transitions; referenced documents must sit beside it.")
    parser.add_argument("--review-manifest",
                        help="Independent A6_MANUAL_IDENTITY_REVIEW_V1 JSON manifest covering the evidence file.")
    parser.add_argument("--candidate-scope",
                        help="Independent JSON/JSONL/CSV inventory of identity-recovery candidates.")
    parser.add_argument("--output-dir",
                        help="Optional m1-a6-identity-recovery-* directory below artifacts/data_enrichment.")
    parser.add_argument("--execute", action="store_true",
                        help="Required acknowledgement. Stage A6 remains offline (network_requests=0).")
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to run offline Stage A6", file=sys.stderr)
        return 2
    try:
        output, manifest = build_stage_a6(
            _path(args.canonical), _path(args.a1_artifact), _path(args.a2_artifact),
            _path(args.a3_artifact), _path(args.a4_artifact), root=ROOT,
            evidence_path=_path(args.evidence_file) if args.evidence_file else None,
            review_manifest_path=_path(args.review_manifest) if args.review_manifest else None,
            candidate_scope_path=_path(args.candidate_scope) if args.candidate_scope else None,
            output_dir=_path(args.output_dir) if args.output_dir else None,
            progress=print)
        metrics = manifest["metrics"]
        print(f"A6={manifest['status']} verified={metrics['verified_transition_events']} "
              f"rejected={metrics['rejected_transition_events']} "
              "network_requests=0 canonical_mutations=0")
        print(output)
        return 0 if manifest["status"] in {"PASS", "PARTIAL"} else 2
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
