"""Áp timestamp nguồn đã được owner duyệt vào artifact Product/M3 pilot mới."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.publisher_timestamp_overlay import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    try:
        result = run(args.config, args.output, args.root)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
