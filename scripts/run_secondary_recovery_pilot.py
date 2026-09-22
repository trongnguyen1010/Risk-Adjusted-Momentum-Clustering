"""Execute Stage A4 bounded CafeF secondary-source recovery pilot."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.secondary_recovery import build_stage_a4
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.cafef import CafeFSource


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--a1-artifact", required=True)
    parser.add_argument("--a2-artifact", required=True)
    parser.add_argument("--a3-artifact", required=True)
    parser.add_argument("--symbol", action="append", default=[],
                        help="Optional unresolved A3 ticker subset; repeat per ticker.")
    parser.add_argument("--overlap-sessions", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--max-level-deviation", type=float, default=0.02)
    parser.add_argument("--max-ratio-deviation", type=float, default=0.02)
    parser.add_argument("--max-regime-shift", type=float, default=0.02)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--min-interval", type=float, default=2.0)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--execute", action="store_true",
                        help="Required acknowledgement: perform bounded CafeF network requests.")
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to acknowledge bounded CafeF network requests",
              file=sys.stderr)
        return 2
    client = PublicJsonClient(timeout=args.timeout, attempts=args.attempts,
                              min_interval=args.min_interval, max_bytes=args.max_bytes)
    provider = CafeFSource(client=client)
    try:
        output, report = build_stage_a4(
            args.canonical, args.a1_artifact, args.a2_artifact, args.a3_artifact,
            root=ROOT, provider=provider, symbols=args.symbol,
            overlap_sessions=args.overlap_sessions, max_pages=args.max_pages,
            min_overlap_each_side=20,
            max_level_deviation=args.max_level_deviation,
            max_ratio_deviation=args.max_ratio_deviation,
            max_regime_shift=args.max_regime_shift, progress=print)
        metrics = report["metrics"]
        print(f"A4={report['status']} requests={metrics['requests']} "
              f"pages={metrics['network_page_requests']} "
              f"recovered={metrics['rows_recovered']}/{metrics['rows_requested']} "
              "canonical_mutations=0")
        print(output)
        return 0 if report["status"] in ("PASS", "PARTIAL") else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
