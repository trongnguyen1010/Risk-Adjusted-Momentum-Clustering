"""Verify and map five M1 shard handoffs into one canonical candidate offline."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale import map_scale_handoff_candidates


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--pilot-gate", required=True)
    parser.add_argument("--assignment-index", required=True)
    parser.add_argument("--run-index", required=True)
    args = parser.parse_args(argv)
    try:
        output, manifest = map_scale_handoff_candidates(
            args.config, args.pilot_gate, args.assignment_index, args.run_index,
            root=ROOT)
        print(f"MAPPING={manifest['mapping_status']} network_requests=0")
        print(output / "manifest.json")
        return 0
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
