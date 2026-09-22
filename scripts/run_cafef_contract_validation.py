"""Run bounded Stage A5-R1 CafeF contract and endpoint validation."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.cafef_contract_validation import build_stage_a5_r1
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.cafef import CafeFSource


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: add --execute to acknowledge exactly 11 bounded CafeF requests", file=sys.stderr)
        return 2
    provider = CafeFSource(PublicJsonClient(timeout=20, attempts=2, min_interval=2.0, max_bytes=5_000_000))
    try:
        output, manifest = build_stage_a5_r1(args.canonical, root=ROOT, provider=provider, progress=print)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"A5-R1={manifest['status']} requests={manifest['request_count']} canonical_mutations=0")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
