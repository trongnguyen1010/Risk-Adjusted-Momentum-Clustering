"""Run the bounded A5-R1.1 CafeF discovery and evidence expansion."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.cafef_deep_discovery import build_stage_a5_r1_1
from delta_t1.ingestion.sources.base import PublicJsonClient


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--prior-public-request-count", type=int, default=0)
    parser.add_argument("--reuse-raw-from")
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to acknowledge the bounded sequential public CafeF probe", file=sys.stderr)
        return 2
    client = None if args.reuse_raw_from else PublicJsonClient(
        timeout=25, attempts=2, min_interval=2.0, max_bytes=8_000_000,
        user_agent="DELTA-A5-R1.1-Discovery/1.0 (bounded public research)")
    try:
        output, manifest = build_stage_a5_r1_1(root=ROOT, client=client,
                                               prior_public_request_count=args.prior_public_request_count,
                                               progress=print,
                                               reuse_raw_from=args.reuse_raw_from)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"A5-R1.1={manifest['result']} requests={manifest['network_request_count']} canonical_mutations=0")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
