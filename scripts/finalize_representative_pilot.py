"""Finalize a completed representative pilot by checksummed offline QC replay."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.representative_pilot_finalize import finalize_real_run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--gate-report", required=True)
    parser.add_argument("--qc-policy", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        output, assessment, gate = finalize_real_run(
            args.config, args.gate_report, args.qc_policy, args.run_id, root=ROOT)
        print(f"{gate['gate']}={gate['status']} network_requests=0")
        print(f"usable_5y={assessment['aggregate']['usable_5y_symbols']}/"
              f"{assessment['aggregate']['selected_symbols']}")
        print(output / "assessment.json")
        return 0 if gate["status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
