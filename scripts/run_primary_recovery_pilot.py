"""Execute Stage A3 bounded KBS primary-provider recovery pilot."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.primary_recovery import build_stage_a3
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.vnstock import KBSPublicHttpSource


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--a1-artifact", required=True)
    parser.add_argument("--a2-artifact", required=True)
    parser.add_argument("--sample-size", type=int, default=12)
    parser.add_argument("--symbol", action="append", default=[],
                        help="Explicit pilot ticker; repeat 10–20 times. Omit for deterministic auto-selection.")
    parser.add_argument("--high-priority-symbol", action="append", default=[],
                        help="User-declared HIGH acquisition-priority ticker; repeatable.")
    parser.add_argument("--max-dates-per-range", type=int, default=5)
    parser.add_argument("--max-calendar-span-days", type=int, default=10)
    parser.add_argument("--max-ranges-per-symbol", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--min-interval", type=float, default=2.0)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--execute", action="store_true",
                        help="Required acknowledgement: perform bounded KBS network requests.")
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to acknowledge bounded KBS network requests", file=sys.stderr)
        return 2
    client = PublicJsonClient(timeout=args.timeout, attempts=args.attempts,
                              min_interval=args.min_interval, max_bytes=args.max_bytes)
    provider = KBSPublicHttpSource(client=client)
    try:
        output, report = build_stage_a3(
            args.canonical, args.a1_artifact, args.a2_artifact,
            root=ROOT, provider=provider, sample_size=args.sample_size,
            explicit_symbols=args.symbol, high_priority_symbols=args.high_priority_symbol,
            max_dates_per_range=args.max_dates_per_range,
            max_calendar_span_days=args.max_calendar_span_days,
            max_ranges_per_symbol=args.max_ranges_per_symbol,
            progress=print,
        )
        metrics = report["metrics"]
        print(f"A3={report['status']} requests={metrics['requests_successful']}/"
              f"{metrics['requests_attempted']} recovered={metrics['rows_recovered']}/"
              f"{metrics['rows_requested']} canonical_mutations=0")
        print(output)
        return 0 if report["status"] in ("PASS", "PARTIAL") else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
