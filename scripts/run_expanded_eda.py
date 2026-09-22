"""CLI runner to execute Expanded EDA on Canonical Enriched Dataset v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.evaluation.expanded_eda import run_expanded_eda


def _find_latest_canonical_v2(base_dir: Path) -> Path:
    candidates = sorted(base_dir.glob("canonical-m1-scale-enriched-v2-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        manifest_file = c / "manifest.json"
        if manifest_file.is_file():
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if data.get("status") == "PASS":
                return c
    raise FileNotFoundError(f"No PASS canonical-m1-scale-enriched-v2-* found in {base_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", help="Canonical Enriched v2 directory (defaults to latest PASS)")
    parser.add_argument("--execute", action="store_true", help="Required acknowledgement flag to execute Expanded EDA")

    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: Add --execute flag to acknowledge executing Expanded EDA.", file=sys.stderr)
        return 2

    can_base = ROOT / "data" / "canonical"
    canonical_dir = Path(args.canonical) if args.canonical else _find_latest_canonical_v2(can_base)
    if not canonical_dir.is_absolute():
        canonical_dir = ROOT / canonical_dir

    print(f"Canonical Enriched v2: {canonical_dir.name}")

    try:
        out_dir, summary = run_expanded_eda(
            canonical_dir,
            root=ROOT,
            progress=print,
        )
        print("\n" + "="*60)
        print("SUCCESS: Expanded EDA Report Generated Successfully!")
        print(f"Snapshot Date:               {summary['snapshot_date']}")
        print(f"Total Securities Analyzed:   {summary['universe']['total_securities']}")
        print(f"100% Full 5y Clean Tickers:  {summary['session_coverage_breakdown']['full_5y_zero_missing_tickers']}")
        print(f"Market-Feature-Ready (252d): {summary['session_coverage_breakdown']['latest_252_zero_missing_ready_tickers']}")
        print(f"Group 1 (Missing <=20 days): {summary['session_coverage_breakdown']['group_1_missing_1_to_20_days']['total']}")
        print(f"Group 2 (Missing >20 days):  {summary['session_coverage_breakdown']['group_2_missing_gt_20_days']}")
        print(f"Report Location:             {out_dir / 'EXPANDED_EDA_REPORT.md'}")
        print("="*60)
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
