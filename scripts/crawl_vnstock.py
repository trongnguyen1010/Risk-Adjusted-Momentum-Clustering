"""Collect a small vendor sample; expand explicitly after reviewing source semantics."""
import argparse
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
# Worker processes must resolve the same checkout without an editable install.
os.environ["PYTHONPATH"] = str(root / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
from delta_t1.ingestion.sources.vnstock import collect

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-08-01")
    parser.add_argument("--end", default="2026-08-31")
    parser.add_argument("--symbols", nargs="+", default=["FPT", "VNM", "PVS"])
    parser.add_argument("--gate-report", help="PASS SOURCE_SMOKE for 6–60 symbols; PASS REPRESENTATIVE_PILOT above 60")
    parser.add_argument("--resume")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    try:
        path, manifest = collect(root, args.start, args.end, args.symbols, args.resume, args.interval, gate_report_path=args.gate_report)
        print(f"{manifest['status']}: {path / 'manifest.json'}")
        raise SystemExit(0 if manifest["status"] == "complete" else 2)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
