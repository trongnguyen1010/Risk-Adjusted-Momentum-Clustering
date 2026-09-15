"""Deterministic 6-security/18-month synthetic vendor fixture builder.

Uses the existing synthetic generator's canonical data; no API/import of SDK.
Each envelope, reference and policy is bound with SHA-256 like real promotion.
"""
from pathlib import Path
from delta_t1.ingestion.sources.vnstock import date_batches
from delta_t1.io import digest, encoded, now, write_json, write_rows


def build_vendor(root: Path, tables: dict) -> tuple[Path, Path]:
    vendor = root / "vendor-fixture"
    vendor.mkdir()
    ids = {r["security_id"] for r in tables["securities"][:6]}
    master = [r for r in tables["securities"] if r["security_id"] in ids]
    symbol_map = {r["security_id"]: r["ticker"] for r in master}
    started, fetched, finished = "2026-09-11T00:00:00+00:00", "2026-09-11T01:00:00+00:00", "2026-09-11T02:00:00+00:00"
    config = dict(start="2024-01-01", end="2025-06-30", symbols=sorted(symbol_map.values()), code_hash="synthetic-reviewed-code", vnstock_version="fixture-1", interval=5, attempts=1, timeout=90)
    manifest = dict(run_id=vendor.name, synthetic=True, config=config, config_hash=digest(encoded(config)), status="complete", started_at=started, finished_at=finished, jobs={})
    jobs = [dict(id="listing", kind="listing")]
    for symbol in config["symbols"] + ["VNINDEX"]:
        for a, b in date_batches(config["start"], config["end"]):
            jobs.append(dict(id=f"{symbol}-{a}-{b}", kind="index" if symbol == "VNINDEX" else "equity", symbol=symbol, start=a, end=b))
    observations = []
    for job in jobs:
        if job["kind"] == "listing":
            records = [dict(symbol=r["ticker"], exchange=r["exchange"]) for r in master]
        else:
            selected = [r for r in tables["benchmark_daily"] if job["start"] <= r["trade_date"] <= job["end"]] if job["kind"] == "index" else [r for r in tables["prices_daily"] if r["ticker"] == job["symbol"] and job["start"] <= r["trade_date"] <= job["end"]]
            records = []
            for row in selected:
                record = dict(time=row["trade_date"] + "T07:00:00", close=row.get("adj_close", row.get("close")))
                if job["kind"] == "equity":
                    record.update(open=row["raw_open"], high=row["raw_high"], low=row["raw_low"], volume=row["volume"], va=row["traded_value"])
                records.append(record)
                observations.append(dict(kind=job["kind"], symbol=job["symbol"], trade_date=row["trade_date"], available_at=row["available_at"], trading_status="normal"))
        doc = dict(job=job, columns=list(records[0]), records=records, sdk_metadata=dict(source="SYNTHETIC_FIXTURE", symbol=job.get("symbol"), interval="1D"), source_routing="synthetic_fixture", vnstock_version="fixture-1", fetched_at=fetched)
        path = vendor / "raw" / (job["id"] + ".json")
        write_json(path, doc)
        manifest["jobs"][job["id"]] = dict(status="complete", job=job, rows=len(records), path=path.relative_to(vendor).as_posix(), sha256=digest(path.read_bytes()))
    write_json(vendor / "manifest.json", manifest)
    verified = lambda value: dict(status="verified", value=value, evidence=["explicit synthetic fixture contract; not evidence for KBS"])
    policy = dict(policy_version="1.0", envelope_schema_version="1.0.0", synthetic=True, vnstock_version="fixture-1", source_routing="synthetic_fixture", approved_crawler_hashes=[config["code_hash"]], references={})
    for key, value in dict(timezone_offset_minutes=420, price_multiplier=1, volume_multiplier=1, traded_value_multiplier=1,
                           adjustment_basis="synthetic", availability_policy="reference", index_basis="synthetic", index_multiplier=1, index_exchange="HOSE").items():
        policy[key] = verified(value)
    refs = dict(securities=master, trading_calendar=tables["trading_calendar"], corporate_actions=tables["corporate_actions"], risk_free_rate=tables["risk_free_rate"], observations=observations)
    for name, rows in refs.items():
        path = root / "references" / (name + ".jsonl")
        write_rows(path, rows)
        policy["references"][name] = dict(path=path.relative_to(root).as_posix(), sha256=digest(path.read_bytes()), evidence=["synthetic reference fixture"])
    policy_path = root / "policy.json"
    write_json(policy_path, policy)
    return vendor, policy_path
