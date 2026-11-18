"""Đọc offline HNX desktop details và list clock cùng ID; chưa canonical/PIT."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_detail_parser import parse_details
from delta_t1.ingestion.corporate_action_sources import SourceLimitation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        result = parse_details(args.details, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["extraction_gate"] == "PASS_FOR_INPUT_ARTICLES" else 2
    except (ValueError, OSError, KeyError, SourceLimitation) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
