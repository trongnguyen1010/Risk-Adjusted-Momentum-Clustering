"""Kiểm toán shard cũ và đóng gói code/assignment/notebook HNX bổ sung; zero network."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_kaggle import build_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_bundle(ROOT, args.output.resolve())
        result.pop("audit")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
