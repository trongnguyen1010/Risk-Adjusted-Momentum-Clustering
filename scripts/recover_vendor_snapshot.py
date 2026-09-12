"""Recover cached original bytes into a new immutable vendor snapshot."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.recovery import recover_vendor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vendor_run")
    parser.add_argument("--policy", required=True)
    args = parser.parse_args()
    source = Path(args.vendor_run)
    if not source.exists():
        source = ROOT / "data/vendor" / args.vendor_run
    try:
        target, manifest = recover_vendor(source, Path(args.policy), ROOT)
        print(f"verified recovery: {target / 'manifest.json'}")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
