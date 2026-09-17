"""Verify exact assignment union and checksummed copied M1 shard runs offline."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale import verify_scale_handoff


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--pilot-gate", required=True)
    parser.add_argument("--assignment-index", required=True)
    parser.add_argument("--run-index", required=True)
    args = parser.parse_args(argv)
    try:
        output, result = verify_scale_handoff(
            args.config, args.pilot_gate, args.assignment_index, args.run_index,
            root=ROOT)
        print(f"HANDOFF={result['status']} network_requests=0")
        print(output / "manifest.json")
        return 0 if result["status"] == "READY_FOR_CANONICAL_MAPPING" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
