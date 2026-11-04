"""Tải thử một thông báo HNX công khai, tối đa một request, không đổi PIT."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_probe import probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", help="Public HNX article URL; default is verified PVS 2024 discovery sample")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    config = json.loads((ROOT / "configs/data/hnx_announcement_probe_v1.json").read_text(encoding="utf-8"))
    try:
        result = probe(args.url or config["sample_url"], args.output, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "DRY_RUN" or result["public_response_received"] else 2
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
