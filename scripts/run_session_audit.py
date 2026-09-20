"""Create the offline immutable A1 missing-session audit artifact."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.session_audit import build_stage_a1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--quality-report", required=True)
    parser.add_argument("--test-result", action="append", default=[],
                        help="Exact local validation command and observed outcome; repeatable.")
    parser.add_argument("--stage-status", default="PASS", choices=("PASS", "PARTIAL", "FAIL", "BLOCKED"))
    args = parser.parse_args(argv)
    try:
        output, report = build_stage_a1(args.canonical, args.quality_report, root=ROOT,
                                        test_results=args.test_result,
                                        stage_status=args.stage_status)
        print(f"A1={report['status']} network_requests=0")
        print(output)
        return 0
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
