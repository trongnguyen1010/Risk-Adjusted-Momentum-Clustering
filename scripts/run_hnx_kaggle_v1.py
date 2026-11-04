"""Chạy preflight hoặc HNX supplement trên Kaggle, theo ownership shard đã freeze."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_kaggle import run_kaggle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-requests", type=int, default=1000)
    parser.add_argument("--max-seconds", type=int, default=3600)
    args = parser.parse_args()
    try:
        result = run_kaggle(ROOT, args.shard_index, collect=args.collect, max_requests=args.max_requests, max_seconds=args.max_seconds)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        check = result.get("preflight")
        if isinstance(check, dict) and check.get("limitation"):
            return 2
        return 2 if result.get("result", {}).get("resumable") is False else 0
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
