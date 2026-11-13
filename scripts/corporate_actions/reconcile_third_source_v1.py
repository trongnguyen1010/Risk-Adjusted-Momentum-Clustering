"""Chạy đối chiếu ba nguồn offline; logic nằm trong ingestion, không gọi network."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.third_source_reconcile import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    try:
        summary = run(args.config, args.output, args.root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary["unresolved_count"] == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
