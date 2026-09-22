"""Stage A2: deterministic, network-free salvage of existing local raw rows.

The stage never writes canonical data.  It inspects immutable local payloads,
keeps only rows that target an A1 missing key, and fails closed whenever date,
identity, unit, or price-basis evidence is insufficient.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
import json
from pathlib import Path
import re

from ..artifact_ids import new_artifact_id
from ..io import atomic_write, digest, encoded, now, read_json, read_rows, write_json
from .representative_pilot import _valid_kbs
from .representative_pilot_canonical import AVAILABILITY_TIME
from .session_audit import build_a1_audit
from .sources.base import SemanticValidationError
from .sources.cafef import (
    ADAPTER_VERSION as CAFE_ADAPTER_VERSION,
    apply_invalid_row_policy,
    cafef_trade_date,
    classify_cafef_page_row,
    map_trade_history_row,
)
from .sources.vnstock import (
    ADAPTER_VERSION as KBS_ADAPTER_VERSION,
    map_kbs_wire_ohlcv_row,
)


STAGE = "A2 — Local Raw / Quarantine Salvage"
_WINDOWS = (21, 63, 126, 252)
_KBS_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T].*)?$")
_PAGE = re.compile(r"page[-_](\d+)", re.IGNORECASE)

_PARQUET_COLUMNS = (
    "candidate_id", "provider", "security_id", "ticker", "exchange",
    "trade_date", "raw_trade_date", "raw_path", "raw_sha256",
    "raw_row_sha256", "source_symbol", "source_run_id", "fetched_at",
    "available_at", "decision_at", "eligible_at_latest_snapshot",
    "acquisition_client", "endpoint", "adapter_version", "evidence_kind",
    "date_semantics", "price_basis", "price_unit", "volume_unit",
    "normalized_row_json", "raw_row_json", "quarantine_classifications",
    "recovery_run_id", "recovery_reason", "reconciliation_rule_id",
    "decision", "rejection_reasons", "duplicate_group_size",
)


def _inside(path, parent, label):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError(f"{label} escapes {parent}")
    return path


def _verify_manifest_artifacts(directory, manifest, label):
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError(f"{label} has no artifact checksums")
    for relative, expected in artifacts.items():
        path = _inside(directory / relative, directory, f"{label} artifact")
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"{label} artifact checksum mismatch: {relative}")


def _relative(path, root):
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return Path(path).resolve().as_posix()


def _git_commit(root):
    """Resolve HEAD without invoking git or writing into the repository."""
    dotgit = root / ".git"
    if dotgit.is_file():
        marker = dotgit.read_text(encoding="utf-8").strip()
        if not marker.startswith("gitdir:"):
            return "UNRESOLVED"
        dotgit = (root / marker.split(":", 1)[1].strip()).resolve()
    head = dotgit / "HEAD"
    if not head.is_file():
        return "UNRESOLVED"
    value = head.read_text(encoding="utf-8").strip()
    if not value.startswith("ref: "):
        return value
    ref = value[5:]
    loose = dotgit / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    packed = dotgit / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref:
                    return commit
    return "UNRESOLVED"


def _json_text(value):
    return encoded(value).decode("utf-8")


def _blank_candidate(**values):
    row = {column: "" for column in _PARQUET_COLUMNS}
    row.update(values)
    row["duplicate_group_size"] = str(row.get("duplicate_group_size") or 1)
    return row


def _candidate_id(raw_path, row_index, raw_row):
    return digest(encoded([raw_path, row_index, digest(encoded(raw_row))]))[:24]


def _source_run_id(path, provider):
    parts = Path(path).parts
    try:
        index = [part.lower() for part in parts].index(provider.lower())
    except ValueError:
        return "UNKNOWN_LOCAL_RUN"
    return parts[index + 1] if index + 1 < len(parts) else "UNKNOWN_LOCAL_RUN"


def _metadata_for(path):
    companion = path.with_name(path.stem + ".metadata.json")
    if not companion.is_file():
        return None
    value = read_json(companion)
    return value if isinstance(value, dict) else None


def _page_number(path, metadata):
    value = (metadata or {}).get("request", {}).get("page_index")
    if isinstance(value, int) and value >= 1:
        return value
    match = _PAGE.search(path.stem)
    return int(match.group(1)) if match else None


def _quarantine_index(root):
    """Index local quarantine labels without treating them as replacement raw."""
    result, stats = defaultdict(set), Counter()
    paths = [*(root / "data").glob("**/*quarantin*.jsonl"),
             *(root / "artifacts").glob("**/*quarantin*.jsonl")]
    for path in sorted(set(paths)):
        stats["quarantine_files_scanned"] += 1
        try:
            rows = read_rows(path)
        except (OSError, ValueError, json.JSONDecodeError):
            stats["quarantine_files_unreadable"] += 1
            continue
        for row in rows:
            stats["quarantine_rows_scanned"] += 1
            raw_path = row.get("raw_path")
            if isinstance(raw_path, str):
                result[raw_path].add(str(row.get("classification") or row.get("rule_id") or "QUARANTINED"))
                stats["quarantine_rows_with_raw_reference"] += 1
    return result, stats


def _raw_payload_files(scan_roots):
    seen = set()
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.glob("**/*.json")):
            if path.name.endswith(".metadata.json") or path in seen:
                continue
            lowered = {part.lower() for part in path.parts}
            if not ({"kbs", "cafef"} & lowered) and path.parent.name != "raw":
                continue
            seen.add(path)
            yield path


def _provider_for(path, payload):
    parts = {part.lower() for part in path.parts}
    if "kbs" in parts or (isinstance(payload, dict) and "data_day" in payload):
        return "kbs"
    if "cafef" in parts or (isinstance(payload, dict) and "Data" in payload):
        return "cafef"
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return "legacy_sdk"
    return None


def _base(path, raw_bytes, raw_row, row_index, provider, security, root,
          quarantine, metadata=None, *, trade_date="", raw_trade_date="", normalized=None,
          date_semantics="", price_basis="", price_unit="", volume_unit="",
          adapter_version=""):
    raw_path = _relative(path, root)
    metadata = metadata or {}
    return _blank_candidate(
        candidate_id=_candidate_id(raw_path, row_index, raw_row), provider=provider,
        security_id=security.get("security_id", ""), ticker=security.get("ticker", ""),
        exchange=security.get("exchange", ""), trade_date=trade_date or "",
        raw_trade_date=str(raw_trade_date) if raw_trade_date is not None else "",
        raw_path=raw_path, raw_sha256=digest(raw_bytes),
        raw_row_sha256=digest(encoded(raw_row)),
        source_symbol=str(metadata.get("symbol") or security.get("ticker") or "").upper(),
        source_run_id=_source_run_id(path, provider),
        fetched_at=str(metadata.get("fetched_at") or ""),
        available_at=f"{trade_date}T{AVAILABILITY_TIME}" if trade_date else "",
        acquisition_client=str(metadata.get("acquisition_client") or ""),
        endpoint=str(metadata.get("url") or metadata.get("endpoint") or ""),
        adapter_version=str(metadata.get("adapter_client_version") or adapter_version),
        evidence_kind="REAL_LOCAL_RAW_PAYLOAD", date_semantics=date_semantics,
        price_basis=price_basis, price_unit=price_unit, volume_unit=volume_unit,
        normalized_row_json=_json_text(normalized) if normalized is not None else "",
        raw_row_json=_json_text(raw_row),
        quarantine_classifications=";".join(sorted(quarantine.get(raw_path, ()))),
        recovery_reason="A1_MISSING_KEY_WITH_LOCAL_RAW_EVIDENCE",
        reconciliation_rule_id="A2_EXACT_IDENTITY_DATE_UNIT_BASIS_V1",
        decision="PENDING",
    )


def _reject(row, *reasons):
    values = sorted({reason for reason in reasons if reason})
    row["decision"] = "REJECT"
    row["rejection_reasons"] = ";".join(values)
    return row


def _kbs_candidates(path, raw_bytes, payload, securities, missing_keys, root,
                    quarantine, metadata):
    symbol = str(payload.get("symbol") or "").upper()
    security = securities.get(symbol)
    if not security or not isinstance(payload.get("data_day"), list):
        return []
    rows = []
    for index, raw in enumerate(payload["data_day"]):
        raw_date = raw.get("t") if isinstance(raw, dict) else None
        try:
            if not isinstance(raw_date, str) or not _KBS_DATE.match(raw_date):
                raise SemanticValidationError("KBS local trading date format unsupported")
            trade_date = date.fromisoformat(raw_date[:10]).isoformat()
            mapped = map_kbs_wire_ohlcv_row(raw, symbol, security["exchange"])
        except (KeyError, OSError, OverflowError, TypeError, ValueError, SemanticValidationError) as exc:
            row = _base(path, raw_bytes, raw, index, "kbs", security, root, quarantine,
                        metadata,
                        raw_trade_date=raw_date, adapter_version=KBS_ADAPTER_VERSION)
            rows.append(_reject(row, "DATE_OR_SCHEMA_UNSUPPORTED", type(exc).__name__))
            continue
        key = (security["security_id"], trade_date)
        if key not in missing_keys:
            continue
        row = _base(
            path, raw_bytes, raw, index, "kbs", security, root, quarantine, metadata,
            trade_date=trade_date, raw_trade_date=raw_date, normalized=mapped,
            date_semantics="KBS_T_LOCAL_TRADING_DATE", price_basis=mapped["price_basis"],
            price_unit=mapped["price_unit"], volume_unit=mapped["volume_unit"],
            adapter_version=KBS_ADAPTER_VERSION,
        )
        reasons = []
        if mapped["symbol"] != symbol:
            reasons.append("IDENTITY_CONFLICT")
        if mapped["price_unit"] != "VND_PER_SHARE" or mapped["volume_unit"] != "SHARES":
            reasons.append("UNIT_CONFLICT")
        if mapped["price_basis"] != "VENDOR_ADJUSTED":
            reasons.append("PRICE_BASIS_CONFLICT")
        if not _valid_kbs([mapped]):
            reasons.append("INVALID_REQUIRED_MARKET_ROW")
        if metadata is None:
            reasons.append("PROVENANCE_METADATA_MISSING")
        else:
            if str(metadata.get("provider") or "").lower() != "kbs":
                reasons.append("PROVENANCE_PROVIDER_CONFLICT")
            if str(metadata.get("symbol") or "").upper() != symbol:
                reasons.append("PROVENANCE_IDENTITY_CONFLICT")
            expected_raw_path = _relative(path, root)
            if metadata.get("raw_path") != expected_raw_path:
                reasons.append("PROVENANCE_RAW_PATH_CONFLICT")
            if (not metadata.get("fetched_at") or not metadata.get("acquisition_client")
                    or not metadata.get("url") or not metadata.get("adapter_client_version")):
                reasons.append("PROVENANCE_METADATA_INCOMPLETE")
            else:
                try:
                    fetched = datetime.fromisoformat(str(metadata["fetched_at"]).replace("Z", "+00:00"))
                    if fetched.tzinfo is None:
                        reasons.append("PROVENANCE_FETCHED_AT_UNZONED")
                except ValueError:
                    reasons.append("PROVENANCE_FETCHED_AT_INVALID")
        rows.append(_reject(row, *reasons) if reasons else row)
    return rows


def _cafef_candidates(path, raw_bytes, payload, securities, missing_keys, root,
                      quarantine, metadata):
    values = payload.get("Data")
    page = _page_number(path, metadata)
    if not isinstance(values, list):
        return []
    rows = []
    for index, raw in enumerate(values):
        symbol = str(raw.get("Symbol") or "").upper() if isinstance(raw, dict) else ""
        security = securities.get(symbol)
        if not security:
            continue
        raw_date = raw.get("TradeDate") if isinstance(raw, dict) else None
        if page is None:
            row = _base(path, raw_bytes, raw, index, "cafef", security, root, quarantine,
                        metadata,
                        raw_trade_date=raw_date, adapter_version=CAFE_ADAPTER_VERSION)
            rows.append(_reject(row, "SNAPSHOT_POSITION_UNSUPPORTED"))
            continue
        if classify_cafef_page_row(raw_date, page=page, row_index=index) == "CURRENT_SNAPSHOT":
            row = _base(path, raw_bytes, raw, index, "cafef", security, root, quarantine,
                        metadata,
                        raw_trade_date=raw_date, date_semantics="POSITION_AWARE_CURRENT_SNAPSHOT",
                        adapter_version=CAFE_ADAPTER_VERSION)
            rows.append(_reject(row, "SNAPSHOT_ROW_NOT_HISTORICAL"))
            continue
        try:
            trade_date = cafef_trade_date(raw_date)
            mapped = map_trade_history_row(raw, symbol, security["exchange"])
        except (KeyError, OSError, OverflowError, TypeError, ValueError, SemanticValidationError) as exc:
            row = _base(path, raw_bytes, raw, index, "cafef", security, root, quarantine,
                        metadata,
                        raw_trade_date=raw_date, adapter_version=CAFE_ADAPTER_VERSION)
            rows.append(_reject(row, "DATE_OR_SCHEMA_UNSUPPORTED", type(exc).__name__))
            continue
        key = (security["security_id"], trade_date)
        if key not in missing_keys:
            continue
        row = _base(
            path, raw_bytes, raw, index, "cafef", security, root, quarantine, metadata,
            trade_date=trade_date, raw_trade_date=raw_date, normalized=mapped,
            date_semantics="CAFEF_TIMESTAMP_TO_ASIA_HO_CHI_MINH_DATE",
            price_basis="UNSUPPORTED_FOR_CANONICAL_ADJ_CLOSE",
            price_unit=mapped["price_unit"], volume_unit="SHARES_MATCHED_ONLY",
            adapter_version=CAFE_ADAPTER_VERSION,
        )
        policy = {"provider": None}
        eligible, findings = apply_invalid_row_policy([mapped], policy)
        reasons = ["PRICE_BASIS_UNSUPPORTED"]
        if not eligible or findings:
            reasons.append("INVALID_REQUIRED_MARKET_ROW")
        rows.append(_reject(row, *reasons))
    return rows


def _legacy_candidates(path, raw_bytes, payload, securities, missing_keys, root,
                       quarantine):
    job, values = payload.get("job", {}), payload.get("records")
    symbol = str(job.get("symbol") or "").upper()
    security = securities.get(symbol)
    if not security or not isinstance(values, list):
        return []
    rows = []
    for index, raw in enumerate(values):
        raw_date = raw.get("time") if isinstance(raw, dict) else None
        try:
            trade_date = date.fromisoformat(str(raw_date)[:10]).isoformat()
        except (TypeError, ValueError):
            trade_date = ""
        if trade_date and (security["security_id"], trade_date) not in missing_keys:
            continue
        row = _base(path, raw_bytes, raw, index, "legacy_sdk", security, root, quarantine,
                    None,
                    trade_date=trade_date, raw_trade_date=raw_date,
                    date_semantics="LEGACY_SDK_DATE_UNREVIEWED",
                    price_basis="UNRESOLVED", adapter_version=str(payload.get("vnstock_version") or ""))
        rows.append(_reject(row, "PRICE_BASIS_UNSUPPORTED_LEGACY_SDK"))
    return rows


def _scan(scan_roots, securities, missing_keys, root, quarantine):
    candidates, stats, scanned_hashes = [], Counter(), []
    for path in _raw_payload_files(scan_roots):
        stats["files_scanned"] += 1
        try:
            raw_bytes = path.read_bytes()
            raw_hash = digest(raw_bytes)
            scanned_hashes.append((_relative(path, root), raw_hash))
            payload = json.loads(raw_bytes)
            metadata = _metadata_for(path)
            if metadata is not None and metadata.get("sha256") not in (None, raw_hash):
                stats["files_hash_mismatch"] += 1
                continue
            provider = _provider_for(path, payload)
            if provider == "kbs":
                found = _kbs_candidates(path, raw_bytes, payload, securities, missing_keys,
                                        root, quarantine, metadata)
            elif provider == "cafef":
                found = _cafef_candidates(path, raw_bytes, payload, securities, missing_keys,
                                          root, quarantine, metadata)
            elif provider == "legacy_sdk":
                found = _legacy_candidates(path, raw_bytes, payload, securities, missing_keys,
                                           root, quarantine)
            else:
                stats["files_non_market_envelope"] += 1
                continue
            candidates.extend(found)
            stats[f"files_{provider}"] += 1
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            stats["files_unreadable"] += 1
    return candidates, stats, digest(encoded(sorted(scanned_hashes)))


def _resolve_candidates(candidates, canonical_basis):
    pending = defaultdict(list)
    for row in candidates:
        if row["decision"] == "PENDING":
            pending[(row["security_id"], row["trade_date"])].append(row)
    for key, rows in pending.items():
        allowed_basis = canonical_basis.get(key[0], {"vendor_adjusted"})
        for row in rows:
            if row["price_basis"].lower() not in allowed_basis:
                _reject(row, "PRICE_BASIS_CONFLICT")
        eligible = [row for row in rows if row["decision"] == "PENDING"]
        fingerprints = defaultdict(list)
        for row in eligible:
            normalized = json.loads(row["normalized_row_json"])
            fingerprint = _json_text({key: normalized.get(key) for key in (
                "trade_date", "close", "volume", "price_basis", "price_unit", "volume_unit")})
            fingerprints[fingerprint].append(row)
        if len(fingerprints) > 1:
            for row in eligible:
                row["duplicate_group_size"] = str(len(eligible))
                _reject(row, "VALUE_CONFLICT_BETWEEN_LOCAL_RAW_ROWS")
            continue
        if eligible:
            ordered = sorted(eligible, key=lambda row: (row["raw_path"], row["candidate_id"]))
            ordered[0]["decision"] = "ACCEPT"
            ordered[0]["duplicate_group_size"] = str(len(ordered))
            for row in ordered[1:]:
                row["duplicate_group_size"] = str(len(ordered))
                _reject(row, "DUPLICATE_REAL_RAW_EVIDENCE")
    return candidates


def _enforce_availability(candidates, decision_by_key, latest_decision_by_exchange):
    """Apply the canonical market PIT rule before duplicate reconciliation."""
    for row in candidates:
        if row["decision"] != "PENDING":
            continue
        decision_at = decision_by_key.get((row["exchange"], row["trade_date"]))
        row["decision_at"] = decision_at or ""
        if not row["available_at"] or not decision_at:
            _reject(row, "PIT_AVAILABILITY_OR_DECISION_MISSING")
            continue
        try:
            available = datetime.fromisoformat(row["available_at"].replace("Z", "+00:00"))
            decision = datetime.fromisoformat(decision_at.replace("Z", "+00:00"))
        except ValueError:
            _reject(row, "PIT_AVAILABILITY_OR_DECISION_INVALID")
            continue
        if available.tzinfo is None or decision.tzinfo is None:
            _reject(row, "PIT_AVAILABILITY_OR_DECISION_UNZONED")
            continue
        if available > decision:
            _reject(row, "PROVENANCE_AVAILABLE_AFTER_DECISION")
            continue
        latest = latest_decision_by_exchange.get(row["exchange"])
        if latest:
            latest_parsed = datetime.fromisoformat(latest.replace("Z", "+00:00"))
            row["eligible_at_latest_snapshot"] = str(available <= latest_parsed).lower()
        else:
            row["eligible_at_latest_snapshot"] = "false"


# Tiny text-only Parquet writer.  Values that can be absent or provider-specific
# remain JSON/text rather than being silently converted to numeric zero.
_STOP, _I32, _I64, _BINARY, _LIST, _STRUCT = 0, 5, 6, 8, 9, 12


def _varint(value):
    value, output = int(value), bytearray()
    while value > 127:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def _zigzag(value):
    return _varint((int(value) << 1) ^ (int(value) >> 63))


def _thrift_struct(fields):
    output, previous = bytearray(), 0
    for field_id, field_type, payload in fields:
        delta = field_id - previous
        output.append((delta << 4 | field_type) if 0 < delta <= 15 else field_type)
        if not 0 < delta <= 15:
            output.extend(_varint(field_id))
        output.extend(payload)
        previous = field_id
    output.append(_STOP)
    return bytes(output)


def _thrift_binary(value):
    data = str(value).encode("utf-8")
    return _varint(len(data)) + data


def _thrift_list(kind, values):
    values = list(values)
    header = bytes([(len(values) << 4) | kind]) if len(values) <= 14 else bytes([0xF0 | kind]) + _varint(len(values))
    return header + b"".join(values)


def _schema_element(name, children=None):
    fields = []
    if children is None:
        fields.extend(((1, _I32, _zigzag(6)), (3, _I32, _zigzag(0))))  # BYTE_ARRAY, REQUIRED
    fields.append((4, _BINARY, _thrift_binary(name)))
    if children is not None:
        fields.append((5, _I32, _zigzag(children)))
    else:
        fields.append((6, _I32, _zigzag(0)))  # UTF8
    return _thrift_struct(fields)


def write_text_parquet(path, rows, columns, *, creator="delta-t1-stdlib-parquet"):
    """Write deterministic Parquet with a stable, non-null text audit schema."""
    rows = list(rows)
    columns = tuple(columns)
    chunks, metadata, offset = [], [], 4
    for name in columns:
        values = [str(row.get(name, "")) for row in rows]
        raw = b"".join(len(value.encode("utf-8")).to_bytes(4, "little", signed=True)
                       + value.encode("utf-8") for value in values)
        data_header = _thrift_struct(((1, _I32, _zigzag(len(values))),
                                      (2, _I32, _zigzag(0)), (3, _I32, _zigzag(3)),
                                      (4, _I32, _zigzag(3))))
        page = _thrift_struct(((1, _I32, _zigzag(0)), (2, _I32, _zigzag(len(raw))),
                               (3, _I32, _zigzag(len(raw))),
                               (5, _STRUCT, data_header))) + raw
        chunks.append(page)
        column_meta = _thrift_struct((
            (1, _I32, _zigzag(6)),
            (2, _LIST, _thrift_list(_I32, [_zigzag(0)])),
            (3, _LIST, _thrift_list(_BINARY, [_thrift_binary(name)])),
            (4, _I32, _zigzag(0)), (5, _I64, _zigzag(len(values))),
            (6, _I64, _zigzag(len(page))), (7, _I64, _zigzag(len(page))),
            (9, _I64, _zigzag(offset)),
        ))
        metadata.append(_thrift_struct(((2, _I64, _zigzag(offset)),
                                        (3, _STRUCT, column_meta))))
        offset += len(page)
    row_group = _thrift_struct(((1, _LIST, _thrift_list(_STRUCT, metadata)),
                                (2, _I64, _zigzag(sum(map(len, chunks)))),
                                (3, _I64, _zigzag(len(rows)))))
    schema = [_schema_element("schema", children=len(columns))]
    schema.extend(_schema_element(name) for name in columns)
    footer = _thrift_struct(((1, _I32, _zigzag(1)),
                             (2, _LIST, _thrift_list(_STRUCT, schema)),
                             (3, _I64, _zigzag(len(rows))),
                             (4, _LIST, _thrift_list(_STRUCT, [row_group])),
                             (6, _BINARY, _thrift_binary(creator))))
    atomic_write(path, b"PAR1" + b"".join(chunks) + footer
                 + len(footer).to_bytes(4, "little") + b"PAR1")


def write_salvage_parquet(path, rows):
    """Write the fixed A2 salvage Parquet schema."""
    write_text_parquet(path, rows, _PARQUET_COLUMNS,
                       creator="delta-t1-a2-stdlib-parquet")


def _window_gains(per_symbol, observed, accepted_keys, latest_date):
    gains = {window: [] for window in _WINDOWS}
    for row in per_symbol:
        security_id = row["security_id"]
        expected = sorted(observed["expected"][security_id])
        before = observed["observed"][security_id]
        after = before | {day for sid, day in accepted_keys if sid == security_id}
        for window in _WINDOWS:
            required = set([day for day in expected if day <= latest_date][-window:])
            if len(required) == window and not required <= before and required <= after:
                gains[window].append(row["ticker"])
    return gains


def _report_markdown(manifest):
    metrics, roots = manifest["metrics"], manifest["root_causes"]
    lines = [
        "# A2 — Local Raw / Quarantine Salvage", "",
        f"Run: `{manifest['run_id']}`  ",
        f"Generated: `{manifest['generated_at']}`  ",
        f"Canonical baseline (read-only): `{manifest['canonical_run_id']}`  ",
        f"A1 evidence: `{manifest['a1_run_id']}`", "",
        "## Scope", "",
        "Stage A2 chỉ đọc raw/quarantine evidence đã tồn tại local. Không có network request, "
        "không crawl, không imputation, không forward-fill, không zero-fill và không ghi canonical.", "",
        "## Metrics", "",
        "| Metric | Count |", "|---|---:|",
        f"| Candidate rows | {metrics['candidate_rows']} |",
        f"| Accepted rows | {metrics['accepted_rows']} |",
        f"| Rejected rows | {metrics['rejected_rows']} |",
        f"| Symbols improved | {metrics['symbols_improved']} |",
        f"| Files scanned | {metrics['files_scanned']} |", "",
        "## Newly complete momentum windows", "",
        "| Window | Newly complete securities | Tickers |", "|---:|---:|---|",
    ]
    for window in _WINDOWS:
        values = manifest["newly_complete_windows"][str(window)]
        lines.append(f"| {window} | {len(values)} | {', '.join(values) or '—'} |")
    lines.extend(["", "## Root causes", "", "| Reason | Rows |", "|---|---:|"])
    for reason, count in roots.items():
        lines.append(f"| {reason} | {count} |")
    lines.extend([
        "", "## Artifacts", "",
        "- `local_salvage_candidates.parquet`", "- `local_salvage_accepted.parquet`",
        "- `local_salvage_rejected.parquet`", "- `manifest.json`", "",
        "## Tests", "",
    ])
    if manifest["validation_results"]:
        lines.extend(f"- {value}" for value in manifest["validation_results"])
    else:
        lines.append("- Không ghi nhận lệnh validation trong lần chạy này.")
    lines.extend([
        "", "## Unresolved Issues", "",
        "- CafeF không được dùng để cứu `adj_close`: adapter hiện chưa cung cấp price-basis "
        "evidence tương thích với canonical `vendor_adjusted`.",
        "- Legacy SDK rows bị reject khi price basis chưa được phê duyệt.",
        "- Historical identity và official exchange calendar vẫn giữ nguyên trạng thái provisional.",
        "", "## Stage Result", "", "`PASS`", "", "## STOP", "",
        "Chờ independent audit trước Stage A3.",
    ])
    return "\n".join(lines).encode("utf-8")


def build_stage_a2(canonical_path, a1_artifact_path, *, root, scan_roots=None,
                   validation_results=()):
    """Build one immutable A2 artifact exclusively from local evidence."""
    root = Path(root).resolve()
    canonical_path = _inside(canonical_path, root / "data" / "canonical", "canonical path")
    a1_artifact_path = _inside(a1_artifact_path, root / "artifacts" / "data_enrichment",
                               "A1 artifact path")
    canonical_manifest = read_json(canonical_path / "manifest.json")
    if (canonical_manifest.get("run_id") != canonical_path.name
            or canonical_manifest.get("canonical_promotion_status") != "PASS"
            or canonical_manifest.get("network_requests") != 0
            or canonical_manifest.get("synthetic") is not False):
        raise ValueError("A2 requires a real, completed offline canonical baseline")
    _verify_manifest_artifacts(canonical_path, canonical_manifest, "canonical baseline")
    a1_manifest = read_json(a1_artifact_path / "manifest.json")
    if (a1_manifest.get("run_id") != a1_artifact_path.name
            or a1_manifest.get("stage") != "A1 — Missing Session Audit"
            or a1_manifest.get("status") != "PASS"
            or a1_manifest.get("network_requests") != 0
            or a1_manifest.get("canonical_run_id") != canonical_manifest["run_id"]):
        raise ValueError("A2 requires matching A1 PASS evidence")
    _verify_manifest_artifacts(a1_artifact_path, a1_manifest, "A1 evidence")

    if scan_roots is None:
        scan_roots = [root / "data", root / "artifacts"]
    scan_roots = [_inside(path, root, "scan root") for path in scan_roots]

    securities_rows = read_rows(canonical_path / "clean" / "securities.jsonl")
    prices = read_rows(canonical_path / "clean" / "prices_daily.jsonl")
    calendar = read_rows(canonical_path / "clean" / "trading_calendar.jsonl")
    features = read_rows(canonical_path / "features" / "monthly.jsonl")
    detail, per_symbol, _, latest_date = build_a1_audit(
        securities_rows, prices, calendar, features,
        collection_end=canonical_manifest["collection_end"],
    )
    missing_keys = {(row["security_id"], row["trading_date"]) for row in detail}
    securities = {row["ticker"].upper(): row for row in securities_rows}
    canonical_basis = defaultdict(set)
    observed = defaultdict(set)
    for row in prices:
        canonical_basis[row["security_id"]].add(str(row["adjustment_basis"]).lower())
        observed[row["security_id"]].add(row["trade_date"])
    expected = defaultdict(set)
    for row in detail:
        expected[row["security_id"]].add(row["trading_date"])
    for row in prices:
        expected[row["security_id"]].add(row["trade_date"])

    decision_by_key = {}
    for row in calendar:
        if row.get("is_open"):
            key = (row["exchange"], row["trade_date"])
            value = row.get("decision_at")
            if not isinstance(value, str) or not value:
                raise ValueError(f"canonical calendar decision_at missing: {key}")
            if key in decision_by_key and decision_by_key[key] != value:
                raise ValueError(f"canonical calendar decision_at conflict: {key}")
            decision_by_key[key] = value
    latest_decision_by_exchange = {
        exchange: decision_by_key[(exchange, latest_date)]
        for exchange in {row["exchange"] for row in securities_rows}
        if (exchange, latest_date) in decision_by_key
    }

    quarantine, quarantine_stats = _quarantine_index(root)
    candidates, scan_stats, scanned_raw_digest = _scan(
        scan_roots, securities, missing_keys, root, quarantine)
    _enforce_availability(candidates, decision_by_key, latest_decision_by_exchange)
    _resolve_candidates(candidates, canonical_basis)
    candidates.sort(key=lambda row: (
        row["ticker"], row["trade_date"], row["provider"], row["raw_path"], row["candidate_id"]))
    accepted = [row for row in candidates if row["decision"] == "ACCEPT"]
    rejected = [row for row in candidates if row["decision"] == "REJECT"]
    if len(accepted) + len(rejected) != len(candidates):
        raise ValueError("A2 candidate resolution left a non-final decision")
    accepted_keys = {(row["security_id"], row["trade_date"]) for row in accepted}
    readiness_keys = {(row["security_id"], row["trade_date"]) for row in accepted
                      if row["eligible_at_latest_snapshot"] == "true"}
    if len(accepted_keys) != len(accepted):
        raise ValueError("A2 accepted output contains duplicate canonical keys")
    if not accepted_keys <= missing_keys:
        raise ValueError("A2 attempted to overwrite an existing canonical key")
    gains = _window_gains(per_symbol, {"expected": expected, "observed": observed},
                          readiness_keys, latest_date)
    root_causes = Counter()
    for row in rejected:
        for reason in filter(None, row["rejection_reasons"].split(";")):
            root_causes[reason] += 1

    run_id = new_artifact_id("m1-a2-local-salvage")
    for row in candidates:
        row["recovery_run_id"] = run_id
    output = root / "artifacts" / "data_enrichment" / run_id
    output.mkdir(parents=True, exist_ok=False)
    created_at = now()
    policy_config = {
        "stage": "A2", "network_allowed": False, "canonical_mutation_allowed": False,
        "forward_fill_allowed": False, "missing_zero_allowed": False,
        "accepted_price_basis": "canonical-compatible VENDOR_ADJUSTED",
        "scan_roots": [_relative(path, root) for path in scan_roots],
    }
    manifest = {
        "run_id": run_id, "created_at": created_at, "generated_at": created_at,
        "stage": STAGE, "status": "PASS", "git_commit": _git_commit(root),
        "config_hash": digest(encoded(policy_config)),
        "network_requests": 0, "canonical_mutations": 0, "synthetic_rows": 0,
        "imputed_rows": 0, "canonical_run_id": canonical_manifest["run_id"],
        "a1_run_id": a1_manifest["run_id"], "latest_completed_snapshot": latest_date,
        "scan_roots": [_relative(path, root) for path in scan_roots],
        "metrics": {
            "candidate_rows": len(candidates), "accepted_rows": len(accepted),
            "rejected_rows": len(rejected),
            "symbols_improved": len({row["security_id"] for row in accepted}),
            **dict(scan_stats), **dict(quarantine_stats),
        },
        "newly_complete_windows": {str(window): sorted(gains[window]) for window in _WINDOWS},
        "root_causes": dict(sorted(root_causes.items(), key=lambda item: (-item[1], item[0]))),
        "input_hashes": {
            "canonical_manifest": digest((canonical_path / "manifest.json").read_bytes()),
            "a1_manifest": digest((a1_artifact_path / "manifest.json").read_bytes()),
            "scanned_raw_set": scanned_raw_digest,
        },
        "input_artifact_ids": [canonical_manifest["run_id"], a1_manifest["run_id"]],
        "provider_versions": {
            "kbs": KBS_ADAPTER_VERSION, "cafef": CAFE_ADAPTER_VERSION,
            "legacy_sdk": "FROM_EACH_RAW_ENVELOPE",
        },
        "adapter_versions": {"kbs": KBS_ADAPTER_VERSION, "cafef": CAFE_ADAPTER_VERSION},
        "validation_results": list(validation_results),
        "limitations": [
            "CafeF adjusted-price basis is not approved for canonical adj_close salvage",
            "legacy SDK price basis remains unresolved",
            "calendar and historical identity evidence remain provisional",
        ],
    }
    write_salvage_parquet(output / "local_salvage_candidates.parquet", candidates)
    write_salvage_parquet(output / "local_salvage_accepted.parquet", accepted)
    write_salvage_parquet(output / "local_salvage_rejected.parquet", rejected)
    atomic_write(output / "stage_a2_report.md", _report_markdown(manifest))
    manifest["artifacts"] = {
        path.name: digest(path.read_bytes()) for path in sorted(output.iterdir()) if path.is_file()
    }
    write_json(output / "manifest.json", manifest)
    return output, manifest
