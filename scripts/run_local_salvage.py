"""Run Stage A2 using existing local raw/quarantine evidence only."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.local_salvage import build_stage_a2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True,
                        help="Approved canonical baseline directory under data/canonical.")
    parser.add_argument("--a1-artifact", required=True,
                        help="Matching A1 PASS directory under artifacts/data_enrichment.")
    parser.add_argument("--scan-root", action="append", default=None,
                        help="Local repository directory to scan; repeatable. Defaults to data/ and artifacts/.")
    parser.add_argument("--validation-result", action="append", default=[],
                        help="Exact local validation command/outcome to record; repeatable.")
    args = parser.parse_args(argv)
    scan_roots = [Path(value) for value in args.scan_root] if args.scan_root else None
    try:
        output, report = build_stage_a2(
            args.canonical, args.a1_artifact, root=ROOT, scan_roots=scan_roots,
            validation_results=args.validation_result,
        )
        metrics = report["metrics"]
        print("A2=PASS network_requests=0 canonical_mutations=0")
        print(f"candidates={metrics['candidate_rows']} accepted={metrics['accepted_rows']} "
              f"rejected={metrics['rejected_rows']} symbols_improved={metrics['symbols_improved']}")
        print(output)
        return 0
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
