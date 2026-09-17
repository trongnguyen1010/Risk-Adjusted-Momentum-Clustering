"""Build a reviewed 500-symbol M1 universe from bounded KBS identity/history probes."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.ingestion.representative_pilot import utc_now
from delta_t1.ingestion.sources.base import AccessControlError, PublicJsonClient, RateLimitError
from delta_t1.ingestion.sources.vnstock import KBS_BASE, KBSPublicHttpSource, map_kbs_wire_ohlcv_row
from delta_t1.io import atomic_write, digest, read_json, write_json


LISTING_ENDPOINT = f"{KBS_BASE}/stock/search/data"
OLD_WINDOW = ("2023-01-03", "2023-01-17")
RECENT_WINDOW = ("2026-09-01", "2026-09-15")
MINIMUM_SPAN_YEARS = 3
EXCHANGES = {"HOSE", "HNX", "UPCOM"}


def _candidate_order(rows):
    candidates = {}
    for row in rows:
        ticker = row.get("symbol")
        exchange = str(row.get("exchange", "")).upper()
        name = row.get("name")
        if (row.get("type") != "stock" or exchange not in EXCHANGES
                or not isinstance(ticker, str) or not ticker.isalnum()
                or ticker != ticker.upper() or not isinstance(name, str) or not name.strip()):
            continue
        if ticker in candidates:
            raise ValueError(f"duplicate KBS stock ticker: {ticker}")
        candidates[ticker] = {"ticker": ticker, "exchange": exchange,
                              "company_name": name.strip()}
    return sorted(candidates.values(), key=lambda row: digest(row["ticker"].encode("ascii")))


def _save_response(directory, name, response, request):
    raw_path = directory / "probes" / f"{name}.json"
    metadata_path = directory / "probes" / f"{name}.metadata.json"
    sha256 = digest(response["body"])
    if raw_path.exists():
        if digest(raw_path.read_bytes()) != sha256:
            raise ValueError("immutable universe-probe collision")
        return read_json(metadata_path)
    atomic_write(raw_path, response["body"])
    metadata = {"provider": "kbs", "acquisition_client": "delta_public_http",
                "endpoint_discovered_via": "vnstock", "request": request,
                "url": response["url"], "http_status": response["status"],
                "fetched_at": utc_now(), "sha256": sha256,
                "bytes": len(response["body"]),
                "raw_path": raw_path.relative_to(ROOT).as_posix()}
    write_json(metadata_path, metadata)
    return metadata


def _load_payload(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _probe(source, directory, candidate, label, window, *, reuse_directory=None):
    name = f"{candidate['ticker']}-{label}"
    raw_path = directory / "probes" / f"{name}.json"
    metadata_path = directory / "probes" / f"{name}.metadata.json"
    if raw_path.is_file() and metadata_path.is_file():
        metadata = read_json(metadata_path)
        if digest(raw_path.read_bytes()) != metadata.get("sha256"):
            raise ValueError(f"stored probe checksum mismatch: {name}")
        return _load_payload(raw_path), metadata
    if reuse_directory is not None:
        reused_raw = reuse_directory / "probes" / f"{name}.json"
        reused_metadata = reuse_directory / "probes" / f"{name}.metadata.json"
        if reused_raw.is_file() and reused_metadata.is_file():
            metadata = read_json(reused_metadata)
            if digest(reused_raw.read_bytes()) != metadata.get("sha256"):
                raise ValueError(f"reused probe checksum mismatch: {name}")
            atomic_write(raw_path, reused_raw.read_bytes())
            copied = dict(metadata, raw_path=raw_path.relative_to(ROOT).as_posix(),
                          reused_from_run=reuse_directory.name)
            write_json(metadata_path, copied)
            return _load_payload(raw_path), copied
    response = source.acquire_ohlcv(candidate["ticker"], *window)
    metadata = _save_response(directory, name, response, {
        "symbol": candidate["ticker"], "exchange": candidate["exchange"],
        "date_range": {"start": window[0], "end": window[1]}, "probe": label,
    })
    return response["payload"], metadata


def _valid_probe(payload, candidate):
    rows = [map_kbs_wire_ohlcv_row(raw, candidate["ticker"], candidate["exchange"])
            for raw in payload.get("data_day", [])]
    if not rows:
        return None
    if len(rows) != len({row["trade_date"] for row in rows}):
        raise ValueError(f"duplicate KBS probe dates: {candidate['ticker']}")
    return min(row["trade_date"] for row in rows), max(row["trade_date"] for row in rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--resume")
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--reuse-recent-from")
    parser.add_argument("--template", default="configs/data/m1_scale.example.json")
    parser.add_argument("--output-universe", required=True)
    parser.add_argument("--output-securities", required=True)
    parser.add_argument("--output-config", required=True)
    args = parser.parse_args(argv)
    run_id = args.resume or new_artifact_id("m1-universe")
    directory = ROOT / "data" / "raw" / "m1_scale_universe" / run_id
    manifest_path = directory / "manifest.json"
    try:
        if args.target < 500:
            raise ValueError("M1 universe target must be at least 500")
        outputs = [Path(args.output_universe).resolve(), Path(args.output_securities).resolve(),
                   Path(args.output_config).resolve()]
        if not args.resume and (directory.exists() or any(path.exists() for path in outputs)):
            raise ValueError("immutable universe run/output already exists")
        client = PublicJsonClient(timeout=20, attempts=2, min_interval=1.0,
                                  max_bytes=10_000_000)
        source = KBSPublicHttpSource(client)
        reuse_directory = (ROOT / "data" / "raw" / "m1_scale_universe"
                           / args.reuse_recent_from if args.reuse_recent_from else None)
        if reuse_directory is not None and not reuse_directory.is_dir():
            raise ValueError("reuse-recent-from run does not exist")
        listing_path = directory / "listing.json"
        listing_metadata_path = directory / "listing.metadata.json"
        if listing_path.is_file() and listing_metadata_path.is_file():
            listing_metadata = read_json(listing_metadata_path)
            if digest(listing_path.read_bytes()) != listing_metadata.get("sha256"):
                raise ValueError("stored KBS listing checksum mismatch")
            listing = _load_payload(listing_path)
        else:
            response = client.get_json(LISTING_ENDPOINT)
            atomic_write(listing_path, response["body"])
            listing_metadata = {"provider": "kbs", "endpoint": LISTING_ENDPOINT,
                                "fetched_at": utc_now(), "http_status": response["status"],
                                "sha256": digest(response["body"]), "bytes": len(response["body"]),
                                "raw_path": listing_path.relative_to(ROOT).as_posix()}
            write_json(listing_metadata_path, listing_metadata)
            listing = response["payload"]
        if not isinstance(listing, list):
            raise ValueError("KBS listing response must be an array")
        candidates = _candidate_order(listing)
        manifest = read_json(manifest_path) if manifest_path.is_file() else {
            "run_id": run_id, "status": "RUNNING", "started_at": utc_now(),
            "target": args.target, "old_window": list(OLD_WINDOW),
            "recent_window": list(RECENT_WINDOW), "listing_sha256": listing_metadata["sha256"],
            "candidate_count": len(candidates), "results": {}, "selected": [],
        }
        if (manifest.get("run_id") != run_id or manifest.get("target") != args.target
                or manifest.get("listing_sha256") != listing_metadata["sha256"]):
            raise ValueError("resume universe identity mismatch")
        selected = list(manifest.get("selected", []))
        selected_set = set(selected)
        for candidate in candidates:
            ticker = candidate["ticker"]
            if len(selected) >= args.target:
                break
            prior = manifest["results"].get(ticker)
            if prior and prior.get("status") in ("ELIGIBLE", "REJECTED"):
                if prior["status"] == "ELIGIBLE" and ticker not in selected_set:
                    selected.append(ticker)
                    selected_set.add(ticker)
                continue
            old_payload, old_meta = _probe(source, directory, candidate, "old", OLD_WINDOW)
            recent_payload, recent_meta = _probe(
                source, directory, candidate, "recent", RECENT_WINDOW,
                reuse_directory=reuse_directory)
            old_dates, recent_dates = _valid_probe(old_payload, candidate), _valid_probe(recent_payload, candidate)
            eligible = bool(old_dates and recent_dates)
            observed_span = ((date.fromisoformat(recent_dates[1]) - date.fromisoformat(old_dates[0])).days
                             / 365.2425 if eligible else 0.0)
            eligible = eligible and observed_span > MINIMUM_SPAN_YEARS
            manifest["results"][ticker] = {
                **candidate, "status": "ELIGIBLE" if eligible else "REJECTED",
                "old_observed": list(old_dates) if old_dates else None,
                "recent_observed": list(recent_dates) if recent_dates else None,
                "observed_span_years": observed_span,
                "probe_hashes": {"old": old_meta["sha256"], "recent": recent_meta["sha256"]},
            }
            if eligible:
                selected.append(ticker)
                selected_set.add(ticker)
            manifest["selected"] = selected
            manifest["selected_count"] = len(selected)
            manifest["processed_count"] = len(manifest["results"])
            write_json(manifest_path, manifest)
        if len(selected) != args.target:
            manifest.update(status="BLOCKED", finished_at=utc_now(),
                            error=f"only {len(selected)}/{args.target} candidates passed")
            write_json(manifest_path, manifest)
            raise ValueError(manifest["error"])
        selected_rows = [manifest["results"][ticker] for ticker in selected]
        universe = [{
            "security_id": f"KBS:{row['exchange']}:{row['ticker']}",
            "ticker": row["ticker"], "exchange": row["exchange"], "sector": None,
            "sector_status": "PENDING_REVIEW", "listing_date": None,
            "history_eligibility": "USABLE_3Y",
            "selection_reason": "KBS current common stock; bounded old+recent observations span >3 years",
            "reference_only": False,
        } for row in selected_rows]
        securities = {
            "schema_version": "1.0.0", "purpose": "M1_SCALE_SECURITY_MASTER",
            "identity_scope": "M1_OBSERVED_INTERVAL_ONLY", "identity_status": "provisional",
            "company_name_semantics": "CURRENT_KBS_DISPLAY_NAME_NOT_HISTORICAL_NAME_CLAIM",
            "source_evidence": {"source": "kbs_delta_public_http",
                                "http_status": listing_metadata["http_status"],
                                "selected_row_count": len(universe),
                                "response_sha256": listing_metadata["sha256"],
                                "fetched_at": listing_metadata["fetched_at"]},
            "securities": [{"ticker": row["ticker"], "company_name": row["company_name"],
                            "exchange": row["exchange"], "instrument_type": "stock"}
                           for row in selected_rows],
        }
        config = read_json(Path(args.template).resolve())
        config.update(universe_file=outputs[0].name,
                      sector_coverage_limitation=(
                          "KBS listing/probe evidence does not provide a reviewed canonical sector; "
                          "selection is identity/history/source-availability based"))
        write_json(outputs[0], universe)
        write_json(outputs[1], securities)
        write_json(outputs[2], config)
        manifest.update(status="COMPLETE", finished_at=utc_now(),
                        universe_sha256=digest(outputs[0].read_bytes()),
                        securities_sha256=digest(outputs[1].read_bytes()),
                        config_sha256=digest(outputs[2].read_bytes()),
                        exchange_counts={exchange: sum(row["exchange"] == exchange for row in universe)
                                         for exchange in sorted(EXCHANGES)})
        write_json(manifest_path, manifest)
        print(f"COMPLETE run_id={run_id} selected={len(universe)}")
        print(f"exchanges={manifest['exchange_counts']}")
        print(outputs[0])
        return 0
    except (AccessControlError, RateLimitError) as exc:
        if directory.exists():
            state = read_json(manifest_path) if manifest_path.is_file() else {"run_id": run_id}
            state.update(status="STOPPED", finished_at=utc_now(), error=f"{type(exc).__name__}: {exc}")
            write_json(manifest_path, state)
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        if directory.exists():
            state = read_json(manifest_path) if manifest_path.is_file() else {"run_id": run_id}
            state.update(status="INTERRUPTED", finished_at=utc_now(), error=f"{type(exc).__name__}: {exc}")
            write_json(manifest_path, state)
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        if directory.exists():
            state = read_json(manifest_path) if manifest_path.is_file() else {"run_id": run_id}
            state.update(status="STOPPED", finished_at=utc_now(),
                         error="KeyboardInterrupt: stopped without changing frozen outputs")
            write_json(manifest_path, state)
        print("STOPPED: interrupted without changing frozen outputs", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
