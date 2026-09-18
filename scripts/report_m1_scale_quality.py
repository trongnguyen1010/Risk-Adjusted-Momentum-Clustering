"""Generate an offline M1 scale EDA and data-quality report."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale_quality import build_m1_scale_quality_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--feature-config", required=True)
    args = parser.parse_args(argv)
    try:
        output, report = build_m1_scale_quality_report(
            args.canonical, args.feature_config, root=ROOT)
        print(f"M1_EDA_QC={report['m1_deadline_status']} network_requests=0")
        print(output / "report.md")
        return 0 if report["m1_deadline_status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
