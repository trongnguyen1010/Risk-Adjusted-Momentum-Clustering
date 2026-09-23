"""Run the bounded, evidence-only A5-R4 additional market source smoke."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.additional_market_source_discovery import BoundedJsonClient, build_stage_a5_r4


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--prior-public-data-requests", type=int, default=2)
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to acknowledge the 30-request sequential public smoke", file=sys.stderr)
        return 2
    client = BoundedJsonClient(timeout=25, min_interval=1.0, max_bytes=2_000_000)
    try:
        output, manifest = build_stage_a5_r4(root=ROOT, client=client,
                                             prior_public_data_requests=args.prior_public_data_requests,
                                             progress=print)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"A5-R4={manifest['result']} requests={manifest['total_public_data_requests']} canonical_mutations=0")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
