"""Pilot tìm thông báo HNX theo mã và ngày đăng; không tải nội dung hoặc build canonical."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_discovery import discover


def main():
    cfg = json.loads((ROOT / "configs/data/hnx_discovery_pilot_v1.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=cfg["pilot_tickers"])
    parser.add_argument("--published-start", default=cfg["published_start"])
    parser.add_argument("--published-end", default=cfg["published_end"])
    parser.add_argument("--max-pages", type=int, default=cfg["max_pages"])
    parser.add_argument("--max-requests", type=int, default=cfg["max_requests"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        canonical_path = ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl"
        canonical_bytes = canonical_path.read_bytes()
        securities = [json.loads(s) for s in canonical_bytes.decode("utf-8").splitlines() if s]
        scopes = []
        for ticker in args.tickers:
            matches = [s for s in securities if s["ticker"] == ticker]
            if len(matches) != 1:
                raise ValueError("TICKER_NOT_UNIQUE_IN_C8_V2: " + ticker)
            scopes.append({"ticker": ticker, "exchange": matches[0]["exchange"]})
        result = discover(scopes, args.published_start, args.published_end, args.output,
                          max_pages=args.max_pages, max_requests=args.max_requests, dry_run=args.dry_run,
                          scope_evidence={"canonical_path": str(canonical_path), "sha256": hashlib.sha256(canonical_bytes).hexdigest(),
                                          "purpose": "SOURCE_WORK_ASSIGNMENT_NOT_HISTORICAL_IDENTITY_PROOF"})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result.get("limitations") else 2
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
