"""Dry-run or execute one immutable 100-symbol M1 scale shard."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale import dry_run_shard, run_real_shard


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--pilot-gate", required=True)
    parser.add_argument("--assignment", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--resume")
    args = parser.parse_args(argv)
    if args.resume and not args.execute:
        parser.error("--resume requires --execute")
    try:
        if args.dry_run:
            directory, manifest = dry_run_shard(
                args.config, args.pilot_gate, args.assignment, root=ROOT)
            print(f"READINESS={manifest['readiness']} network_requests=0")
            print(directory / "manifest.json")
            return 0
        directory, _, gate = run_real_shard(
            args.config, args.pilot_gate, args.assignment, root=ROOT,
            resume=args.resume)
        print(f"M1_SCALE_SHARD={gate['status']} unlocks=NONE")
        print(directory / "manifest.json")
        return 0 if gate["status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
