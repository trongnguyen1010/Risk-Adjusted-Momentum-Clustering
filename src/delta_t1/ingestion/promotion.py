"""Evidence-gated, immutable SDK snapshot to canonical promotion.

Policies attest source semantics; the converter verifies their binding and never
infers missing evidence from plausible prices. All failures remain auditable.
"""
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import uuid

from ..contracts import validate_rows
from ..io import digest, encoded, now, read_json, read_rows, write_json, write_rows
from .crawler import code_hash
from .quality import clean_tables
from .vnstock import date_batches

TABLES = ("securities", "prices_daily", "benchmark_daily", "trading_calendar", "corporate_actions", "risk_free_rate")


def contained_file(root: Path, relative: str) -> Path:
    """Reject paths escaping a manifest's root, including symlinks."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("manifest path escapes run directory")
    return path


def verify_vendor(directory: Path, policy: dict) -> tuple[dict, list[dict]]:
    """Verify all bytes and metadata before interpreting any vendor record."""
    directory = Path(directory).resolve()
    manifest = read_json(directory / "manifest.json")
    if manifest["status"] != "complete" or manifest["run_id"] != directory.name:
        raise ValueError("vendor run must be complete and match directory")
    config = manifest["config"]
    if digest(encoded(config)) != manifest["config_hash"]:
        raise ValueError("vendor config checksum mismatch")
    if config["code_hash"] not in policy.get("approved_crawler_hashes", []):
        raise ValueError("unreviewed crawler code hash")
    if policy.get("policy_version") != "1.0" or policy.get("envelope_schema_version") != "1.0.0":
        raise ValueError("unsupported policy/envelope schema version")
    if bool(manifest["synthetic"]) != policy.get("synthetic"):
        raise ValueError("synthetic/real policy mismatch")
    if config["vnstock_version"] != policy.get("vnstock_version"):
        raise ValueError("unreviewed SDK version")
    started, finished = datetime.fromisoformat(manifest["started_at"]), datetime.fromisoformat(manifest["finished_at"])
    documents = []
    expected = {"listing"}
    for symbol in sorted(set(config["symbols"]) | {"VNINDEX"}):
        expected.update(f"{symbol}-{a}-{b}" for a, b in date_batches(config["start"], config["end"]))
    if set(manifest["jobs"]) != expected:
        raise ValueError("vendor job plan incomplete or unexpected")
    for key, state in sorted(manifest["jobs"].items()):
        path = contained_file(directory, state["path"])
        if state["status"] != "complete" or digest(path.read_bytes()) != state["sha256"]:
            raise ValueError("vendor raw checksum/status mismatch: " + key)
        doc = read_json(path)
        validate_rows("vendor_snapshot", [doc])
        if doc["job"] != state["job"] or doc["job"]["id"] != key or len(doc["records"]) != state["rows"]:
            raise ValueError("vendor job/row count mismatch: " + key)
        if doc["source_routing"] != policy.get("source_routing") or doc["vnstock_version"] != config["vnstock_version"]:
            raise ValueError("vendor source/SDK mismatch")
        stamp = datetime.fromisoformat(doc["fetched_at"])
        if not started <= stamp <= finished:
            raise ValueError("crawl timestamp outside manifest interval")
        if doc["sdk_metadata"].get("source", "").lower() != doc["source_routing"]:
            raise ValueError("SDK metadata source mismatch")
        if len(doc["columns"]) != len(set(doc["columns"])) or any(not isinstance(r, dict) or set(r) != set(doc["columns"]) for r in doc["records"]):
            raise ValueError("record columns differ from envelope")
        if doc["job"]["kind"] != "listing":
            if doc["sdk_metadata"].get("symbol") != doc["job"]["symbol"] or doc["sdk_metadata"].get("interval") != "1D":
                raise ValueError("SDK symbol/interval mismatch")
        documents.append(doc)
    if not documents:
        raise ValueError("empty vendor manifest")
    return manifest, documents


def evidence_value(policy: dict, key: str, optional: bool = False):
    item = policy.get(key, {})
    allowed = ("verified", "research_assumption") if key == "availability_policy" else ("verified",)
    if item.get("status") not in allowed or not item.get("evidence") or item.get("value") is None:
        if optional:
            return None
        raise ValueError("unresolved semantic: " + key)
    return item["value"]


def trade_date(value: str, offset_minutes: int) -> str:
    """Localize naive vendor times only with an explicitly evidenced offset."""
    if isinstance(offset_minutes, bool) or not isinstance(offset_minutes, int) or abs(offset_minutes) > 840:
        raise ValueError("invalid timezone offset")
    zone = timezone(timedelta(minutes=offset_minutes))
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=zone)
    return stamp.astimezone(zone).date().isoformat()


def resolve_security(master: list[dict], ticker: str, day: str) -> dict:
    matches = [m for m in master if m["ticker"] == ticker and m["valid_from"] <= day < (m.get("valid_to") or "9999-12-31")]
    if len(matches) != 1:
        raise ValueError("no unique temporal security mapping: " + ticker + " " + day)
    return matches[0]


def multiplier(policy: dict, key: str, optional: bool = False):
    value = evidence_value(policy, key, optional)
    if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0):
        raise ValueError("invalid multiplier: " + key)
    return value


def map_record(record: dict, doc: dict, policy: dict, master: list[dict], observations: dict) -> tuple[str, dict]:
    job = doc["job"]
    day = trade_date(record["time"], evidence_value(policy, "timezone_offset_minutes"))
    if not job["start"] <= day <= job["end"]:
        raise ValueError("record outside requested date range")
    info = observations.get((job["kind"], job["symbol"], day), {})
    mode = evidence_value(policy, "availability_policy")
    if mode == "fetched_at":
        available = doc["fetched_at"]
    elif mode == "reference":
        available = info["available_at"]
    elif mode == "market_close_plus_delay":
        assumption = policy["availability_policy"]
        if assumption.get("status") != "research_assumption":
            raise ValueError("historical availability must be labeled research_assumption")
        delay = assumption["safety_delay_minutes"]
        if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0:
            raise ValueError("invalid availability safety delay")
        available = (datetime.fromisoformat(day + "T" + assumption["market_close_time"]) + timedelta(minutes=delay)).isoformat()
    else:
        raise ValueError("unsupported availability policy")
    common = dict(trade_date=day, available_at=available, fetched_at=doc["fetched_at"], source=doc["source_routing"])
    if job["kind"] == "index":
        basis = evidence_value(policy, "index_basis")
        if basis not in ("price", "total_return", "synthetic") or (basis == "synthetic" and not policy["synthetic"]):
            raise ValueError("invalid index basis")
        return "benchmark_daily", dict(common, index_id=job["symbol"], close=record["close"] * multiplier(policy, "index_multiplier"),
                                       index_basis=basis, exchange=evidence_value(policy, "index_exchange"))
    if job["kind"] != "equity":
        raise ValueError("unsupported vendor job kind")
    meta = resolve_security(master, job["symbol"], day)
    basis = evidence_value(policy, "adjustment_basis")
    if basis not in ("unadjusted", "split_adjusted", "vendor_adjusted", "total_return", "unknown", "synthetic") or (basis == "synthetic" and not policy["synthetic"]):
        raise ValueError("invalid adjustment basis")
    scale = multiplier(policy, "price_multiplier")
    volume_scale, value_scale = multiplier(policy, "volume_multiplier", True), multiplier(policy, "traded_value_multiplier", True)
    row = dict(common, security_id=meta["security_id"], ticker=meta["ticker"], exchange=meta["exchange"],
               adjustment_basis=basis, trading_status=info.get("trading_status", "unknown"),
               volume=record["volume"] * volume_scale if volume_scale is not None else None,
               traded_value=record["va"] * value_scale if value_scale is not None and record.get("va") is not None else None,
               adj_close=record["close"] * scale if basis in ("split_adjusted", "vendor_adjusted", "total_return", "synthetic") else None)
    # Validate vendor OHLC even when adjusted OHLC is retained only in staging.
    o, h, l, c = (record[f] for f in ("open", "high", "low", "close"))
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in (o,h,l,c)) or not l <= min(o,c) <= max(o,c) <= h:
        raise ValueError("corrupt vendor OHLC")
    for field in ("open", "high", "low", "close"):
        row["raw_" + field] = record[field] * scale if basis in ("unadjusted", "synthetic") else None
    return "prices_daily", row


def promote(vendor: Path, policy_path: Path, root: Path) -> tuple[Path, dict]:
    """Create a new canonical run or a persistent blocked/quarantine report."""
    policy_path, vendor = Path(policy_path).resolve(), Path(vendor).resolve()
    policy = read_json(policy_path)
    run_id = "canonical-" + uuid.uuid4().hex[:12]
    target = Path(root).resolve() / "data" / "canonical" / run_id
    target.mkdir(parents=True, exist_ok=False)
    manifest = dict(run_id=run_id, data_version=run_id, vendor_run_id=vendor.name, status="running", started_at=now(),
                    synthetic=policy.get("synthetic"), data_mode="synthetic" if policy.get("synthetic") else "real",
                    methodology=policy.get("methodology", {}), policy=policy, policy_hash=digest(encoded(policy)), code_hash=code_hash(), schema_version="1.3.0")
    errors, quarantine, tables = [], [], {}
    records_input = 0
    try:
        vendor_manifest, documents = verify_vendor(vendor, policy)
        records_input = sum(len(d["records"]) for d in documents if d["job"]["kind"] != "listing")
        manifest["vendor_manifest_sha256"] = digest((vendor / "manifest.json").read_bytes())
        manifest["vendor_config"] = vendor_manifest["config"]
        references = {}
        manifest["reference_hashes"] = {}
        for name in ("securities", "trading_calendar", "corporate_actions", "risk_free_rate", "observations"):
            spec = policy.get("references", {}).get(name)
            if spec is None:
                if name in ("securities", "trading_calendar"):
                    raise ValueError("missing reference: " + name)
                references[name] = []
                continue
            if not spec.get("evidence"):
                raise ValueError("reference evidence missing: " + name)
            path = (policy_path.parent / spec["path"]).resolve()
            if digest(path.read_bytes()) != spec["sha256"]:
                raise ValueError("reference checksum mismatch: " + name)
            references[name] = read_rows(path)
            manifest["reference_hashes"][name] = spec["sha256"]
        if not policy["synthetic"]:
            for r in references["securities"]:
                if r["identity_status"] == "synthetic":
                    raise ValueError("synthetic identity in real references")
            if any(not r.get("available_at") for r in references["trading_calendar"]):
                raise ValueError("real calendar requires historical availability")
        observations = {}
        for r in references["observations"]:
            key = (r["kind"], r["symbol"], r["trade_date"])
            if key in observations:
                raise ValueError("duplicate observation reference")
            observations[key] = r
        raw = {name: [(r, {"source": r["source"]}, r["fetched_at"]) for r in references[name]] for name in references if name != "observations"}
        for doc in documents:
            if doc["job"]["kind"] == "listing":
                manifest["listing_decision"] = "current listing retained in vendor; historical master required"
                continue
            for record in doc["records"]:
                try:
                    name, row = map_record(record, doc, policy, references["securities"], observations)
                    raw.setdefault(name, []).append((row, {"source": row["source"]}, row["fetched_at"]))
                except (ValueError, KeyError, TypeError) as exc:
                    quarantine.append(dict(record=record, error_code="PROMOTION_MAPPING", error_message=str(exc), source=doc["source_routing"],
                                           vendor_run_id=vendor.name, job=doc["job"], detected_at=now()))
        tables, issues, rejected = clean_tables(raw, run_id)
        quarantine.extend(dict(r, vendor_run_id=vendor.name) for r in rejected)
        errors.extend(issues)
        for name in ("securities", "trading_calendar", "prices_daily", "benchmark_daily"):
            if not tables.get(name):
                errors.append({"error_code": "EMPTY_TABLE", "error_message": name})
        for name in TABLES:
            validate_rows(name, tables.get(name, []))
            write_rows(target / "clean" / (name + ".jsonl"), tables.get(name, []))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(dict(error_code="PROMOTION_BLOCKED", error_message=str(exc)))
    write_rows(target / "quarantine" / "records.jsonl", quarantine)
    manifest.update(status="blocked" if errors or quarantine else "complete", finished_at=now(),
                    quality="QC ERROR" if errors or quarantine else "QC PASS", errors=errors, quarantined=len(quarantine),
                    clean_rows={k: len(v) for k, v in tables.items()}, real_pilot_accepted=False,
                    records_input=records_input, records_accepted=sum(len(tables.get(t, [])) for t in ("prices_daily", "benchmark_daily")),
                    records_quarantined=len(quarantine), warnings=policy.get("warnings", []), blocking_errors=len(errors))
    manifest["artifacts"] = {p.relative_to(target).as_posix(): digest(p.read_bytes()) for p in sorted(target.rglob("*.jsonl"))}
    write_json(target / "manifest.json", manifest)
    return target, manifest
