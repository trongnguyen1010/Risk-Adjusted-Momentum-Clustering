"""Promote an immutable vendor run using an evidence-bound policy."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.promotion import promote

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vendor_run", help="Run ID or path")
    parser.add_argument("--policy", required=True)
    args = parser.parse_args()
    vendor = Path(args.vendor_run)
    if not vendor.exists():
        vendor = ROOT / "data/vendor" / args.vendor_run
    path, manifest = promote(vendor, Path(args.policy), ROOT)
    print(f"{manifest['status']}: {path / 'manifest.json'}")
    raise SystemExit(0 if manifest["status"] == "complete" else 2)
