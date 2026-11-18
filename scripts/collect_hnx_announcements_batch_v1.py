"""Thu thập bổ sung HNX theo lô: discovery, detail, parse, review và resume."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_batch import run_batch


def main():
    config = json.loads((ROOT / "configs/data/hnx_batch_v1.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tickers", nargs="+")
    parser.add_argument("--exchange", nargs="+", choices=["HNX", "UPCOM"])
    parser.add_argument("--published-start")
    parser.add_argument("--published-end")
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--max-requests", type=int, default=config["max_requests_per_run"])
    parser.add_argument("--max-seconds", type=int, default=config["max_seconds_per_run"])
    parser.add_argument("--seed-discovery", type=Path)
    parser.add_argument("--seed-details", type=Path, nargs="*", default=[])
    parser.add_argument("--seed-batch", type=Path)
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        result = run_batch(ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl", args.output,
                           tickers=args.tickers, exchanges=args.exchange, start=args.published_start, end=args.published_end,
                           max_pages=args.max_pages, max_requests=args.max_requests, max_seconds=args.max_seconds,
                           seed_discovery=args.seed_discovery, seed_details=args.seed_details, seed_batch=args.seed_batch, resume_from=args.resume_from,
                           dry_run=args.dry_run, progress=lambda value: print(json.dumps(value, ensure_ascii=False), flush=True))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("stop_reason") and not result["resumable"] else 0
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
