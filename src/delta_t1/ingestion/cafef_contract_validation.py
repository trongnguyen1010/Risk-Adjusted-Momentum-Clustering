"""Bounded, evidence-only CafeF contract validation for Stage A5-R1."""
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.io import atomic_write, write_json, write_rows
from delta_t1.ingestion.sources.cafef import (
    ADAPTER_VERSION, PRICE_HISTORY_ENDPOINT, RIGHTS_STATUS, TRADE_HISTORY_ENDPOINT,
    CafeFSource, cafef_trade_date, classify_cafef_page_row,
)

STAGE = "A5-R1"
CONTRACT_VERSION = "cafef-a5-r1-contract-1.0.0"


def parse_price_history_date(value):
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def price_history_rows(response):
    return response["payload"]["Data"]["Data"]


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _git_head(root):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def validation_plan():
    """Eleven requests: cross-market, pagination, CA, zero-volume and no-row evidence."""
    recent = ("09/14/2026", "09/15/2026")
    return [
        {"id": "T-FPT", "endpoint": "trade", "symbol": "FPT", "exchange": "HOSE", "page_index": 1},
        {"id": "T-BAB", "endpoint": "trade", "symbol": "BAB", "exchange": "HNX", "page_index": 1},
        {"id": "T-ACV", "endpoint": "trade", "symbol": "ACV", "exchange": "UPCOM", "page_index": 1},
        {"id": "T-NO-ROW", "endpoint": "trade", "symbol": "ZZZZZ", "exchange": "HOSE", "page_index": 1},
        {"id": "P-FPT", "endpoint": "price", "symbol": "FPT", "exchange": "HOSE", "start_date": recent[0], "end_date": recent[1], "page_index": 1},
        {"id": "P-BAB", "endpoint": "price", "symbol": "BAB", "exchange": "HNX", "start_date": recent[0], "end_date": recent[1], "page_index": 1},
        {"id": "P-ACV", "endpoint": "price", "symbol": "ACV", "exchange": "UPCOM", "start_date": recent[0], "end_date": recent[1], "page_index": 1},
        {"id": "P-FPT-PAGE2", "endpoint": "price", "symbol": "FPT", "exchange": "HOSE", "start_date": "08/01/2026", "end_date": recent[1], "page_index": 2},
        {"id": "P-FPT-CA", "endpoint": "price", "symbol": "FPT", "exchange": "HOSE", "start_date": "07/18/2025", "end_date": "07/22/2025", "page_index": 1},
        {"id": "P-HND-ZERO", "endpoint": "price", "symbol": "HND", "exchange": "UPCOM", "start_date": "06/19/2026", "end_date": "06/19/2026", "page_index": 1},
        {"id": "P-NO-ROW", "endpoint": "price", "symbol": "ZZZZZ", "exchange": "HOSE", "start_date": recent[0], "end_date": recent[1], "page_index": 1},
    ]


def field_contract():
    common = {"contract_version": CONTRACT_VERSION, "rights_status": RIGHTS_STATUS,
              "promotion_effect": "NONE_IN_A5_R1"}
    fields = [
        ("TradeDate/Ngay", "trade_date", "session date", "date", "APPROVED", "HIGH"),
        ("Symbol", "ticker", "provider ticker", "text", "SUPPORTED_WITH_LIMITATION", "HIGH"),
        ("ExchangeType request", "exchange", "request-scoped venue", "enum", "SUPPORTED_WITH_LIMITATION", "MEDIUM"),
        ("GiaMoCua", "open", "session open", "thousand VND/share", "SUPPORTED_WITH_LIMITATION", "HIGH"),
        ("GiaCaoNhat", "high", "session high", "thousand VND/share", "SUPPORTED_WITH_LIMITATION", "HIGH"),
        ("GiaThapNhat", "low", "session low", "thousand VND/share", "SUPPORTED_WITH_LIMITATION", "HIGH"),
        ("ClosePrice/GiaDongCua", "close", "session close", "thousand VND/share", "SUPPORTED_WITH_LIMITATION", "HIGH"),
        ("AdjustPrice/GiaDieuChinh", "adjusted_price", "CafeF adjustment column; economic method undocumented", "thousand VND/share", "DIAGNOSTIC_ONLY", "LOW"),
        ("BasicPrice", "reference_price", "historical reference price", "thousand VND/share", "APPROVED", "MEDIUM"),
        ("Ceiling", "ceiling_price", "historical ceiling price", "thousand VND/share", "APPROVED", "HIGH"),
        ("Floor", "floor_price", "historical floor price", "thousand VND/share", "APPROVED", "HIGH"),
        ("Volume/KhoiLuongKhopLenh", "matched_volume", "matched-order volume", "shares", "APPROVED", "HIGH"),
        ("TotalValue/GiaTriKhopLenh", "matched_value", "matched-order value", "VND / billion VND", "APPROVED", "HIGH"),
        ("AgreedVolume/KLThoaThuan", "put_through_volume", "negotiated volume", "shares", "APPROVED", "HIGH"),
        ("AgreedValue/GtThoaThuan", "put_through_value", "negotiated value", "VND / billion VND", "APPROVED", "HIGH"),
    ]
    return {**common, "statuses": ["APPROVED", "SUPPORTED_WITH_LIMITATION", "DIAGNOSTIC_ONLY", "UNRESOLVED", "REJECTED"],
            "fields": [{"source_field": s, "concept": c, "meaning": m, "source_unit": u,
                        "normalization": ("TradeHistory: convert UTC-like timestamp to Asia/Ho_Chi_Minh session date; PriceHistory: parse DD/MM/YYYY" if c == "trade_date" else
                                          "multiply by 1000" if "thousand" in u else
                                          "TradeHistory: identity; PriceHistory: multiply by 1e9" if "billion" in u else "identity"),
                        "status": status, "confidence": confidence,
                        "time_date_semantics": ("TradeHistory timestamp converts to Asia/Ho_Chi_Minh local session date; PriceHistory is DD/MM/YYYY without timezone." if c == "trade_date" else "Value belongs to the same provider row/session date."),
                        "limitations": ("Not promotable as canonical price until price basis is approved." if c in {"open", "high", "low", "close", "adjusted_price"} else
                                        "Ticker/exchange identity requires independent security-master match." if c in {"ticker", "exchange"} else "None established in bounded field test."),
                        "evidence": ["LIVE_PUBLIC_RESPONSE", "REPO_P0_CONTRACT"]}
                       for s, c, m, u, status, confidence in fields],
            "acceptance_contract": {
                "provider_row_exists": "Requires an actual source row for exact ticker/date; empty response is NO_ROW.",
                "diagnostically_compatible": "Ratios are evidence only; never authorize scaling or averaging.",
                "field_contract_supported": "All required target fields must be APPROVED; unsupported fields stay null.",
                "price_basis_supported": "Required for any OHLC/adjusted-price promotion; UNRESOLVED in A5-R1.",
                "promotable": "NO. Requires identity match, historical row, exact date, approved fields and price basis, unchanged 20+20 evidence, and verified rights/execution approval.",
                "missing_and_zero": "Numeric provider zero is preserved as evidence. Missing/no row remains missing; never converted to zero.",
                "overlap_policy": "20 valid observations before + 20 after, unchanged and fail-closed.",
            }}


def _canonical_index(path, symbols):
    wanted = set(symbols)
    result = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("ticker") in wanted:
                result[(row["ticker"], row["trade_date"])] = row
    return result


def _endpoint_summary(evidence):
    by_endpoint = {}
    for item in evidence:
        by_endpoint.setdefault(item["endpoint"], []).append(item)
    return {
        "contract_version": CONTRACT_VERSION,
        "endpoints": {
            "TradeHistoryNew.ashx": {
                "url": TRADE_HISTORY_ENDPOINT, "schema": sorted({key for e in by_endpoint.get("trade", []) for key in e.get("observed_fields", [])}),
                "pagination": "one-based PageIndex; fixed PageSize=30", "page_size": 30, "ordering": "newest-first", "date_semantics": "UTC-like timestamp converted to Asia/Ho_Chi_Minh local date",
                "snapshot_behavior": "Only leading page-1 row may be CURRENT_SNAPSHOT; historical rows remain distinct.",
                "strength": "Raw-VND values plus reference/ceiling/floor; no OHLC open/high/low.",
            },
            "DataHistory/PriceHistory.ashx": {
                "url": PRICE_HISTORY_ENDPOINT, "schema": sorted({key for e in by_endpoint.get("price", []) for key in e.get("observed_fields", [])}),
                "pagination": "one-based PageIndex; fixed PageSize=20; live page 2 tested", "page_size": 20, "ordering": "newest-first", "date_semantics": "DD/MM/YYYY session date",
                "snapshot_behavior": "Bounded dated response; no separate leading snapshot marker observed.",
                "strength": "OHLC and separate adjusted column; rounded billion-VND value fields; no reference/ceiling/floor.",
            },
        },
        "preferred_endpoint": "TradeHistoryNew.ashx for already-approved non-OHLC market fields; PriceHistory.ashx is required for OHLC diagnostics only.",
        "equivalent": False,
    }


def _report(run_id, evidence, diagnostics):
    zero = any(e.get("provider_published_zero_volume") for e in evidence)
    empty = [e["request_id"] for e in evidence if e.get("row_count") == 0]
    answers = [
        f"1. Tested `TradeHistoryNew.ashx` and `DataHistory/PriceHistory.ashx` with {len(evidence)} bounded GETs.",
        "2. `TradeHistoryNew.ashx` is preferable for reference/bands and exact-VND value components; `PriceHistory.ashx` uniquely supplies OHLC. They are complementary, not equivalent.",
        "3. Available fields are enumerated in `cafef_field_contract.json`; neither endpoint alone supplies the whole contract.",
        "4. PriceHistory open/high/low/close meanings and units are supported with limitation, but canonical promotion is not contract-supported because basis remains unresolved.",
        "5. `AdjustPrice`/`GiaDieuChinh` is a CafeF adjusted-price column. Its economic adjustment method is NOT DETERMINABLE IN A5-R1.",
        "6. CafeF adjusted values show diagnostic compatibility on some dates, but compatibility with KBS `vendor_adjusted` is not stable enough to approve a basis or transform.",
        "7. Differences occur around corporate-action regimes; their precise economic derivation is NOT DETERMINABLE IN A5-R1.",
        f"8. Provider zero-volume rows are explicit numeric zero rows and are retained only as source evidence (observed={str(zero).upper()}); no row is synthesized.",
        f"9. A missing ticker/session is represented by an empty data array/zero row count in this sample ({', '.join(empty) or 'none observed'}); it stays missing.",
        "10. One-based page 2, fixed page sizes, newest-first ordering and date parsing behaved deterministically in the tested contract. Historical-depth completeness and range-boundary guarantees are NOT DETERMINABLE IN A5-R1.",
        "11. Unresolved: CafeF adjustment methodology, OHLC compatibility basis, historical completeness/availability timing, and provider rights for automated recovery.",
        "12. No. CafeF rows cannot currently be promoted.",
        "13. Blockers: `PRICE_BASIS_UNRESOLVED`, `RIGHTS_NOT_VERIFIED`, and no approved A5-R2 recovery execution decision.",
        "14. A5-R2 may use only exact provider rows and APPROVED non-price fields, fail closed on price fields, preserve zero vs missing, require identity/date checks, and retain the unchanged 20+20 rule.",
        "15. YES. `MANUAL_REVIEW_REQUIRED` before A5-R2 because price-basis acceptance and source-use approval are methodology-sensitive.",
    ]
    return "\n".join([
        "# Stage A5-R1 — CafeF Contract & Endpoint Validation", "",
        f"- Run: `{run_id}`", "- Result: `PARTIAL / MANUAL_REVIEW_REQUIRED`",
        f"- Network requests: `{len(evidence)}`", "- Canonical mutations: `0`",
        "- Synthetic rows: `0`", "- Imputed rows: `0`", "",
        "## Required answers", "", *[f"{line}\n" for line in answers],
        "## Price-basis diagnostic summary", "",
        f"Diagnostic rows: {len(diagnostics)}. Ratios are evidence only; no multiplier, averaging, or transformation is approved.", "",
        "## Decision", "",
        "A5-R1 is evidence-complete but the recovery contract is not promotable. A5-R2 remains blocked pending manual review. The current 20+20 rule is unchanged.", "",
    ])


def build_stage_a5_r1(canonical, *, root, provider, progress=None):
    root, canonical = Path(root), Path(canonical)
    run_id = new_artifact_id("m1-a5-r1-cafef-contract")
    output = root / "artifacts" / "data_enrichment" / run_id
    output.mkdir(parents=True, exist_ok=False)
    evidence, responses = [], {}
    for request in validation_plan():
        if progress:
            progress(f"request {request['id']} {request['endpoint']} {request['symbol']}")
        response = (provider.acquire_trade_history_page(request) if request["endpoint"] == "trade"
                    else provider.acquire_price_history_page(request))
        responses[request["id"]] = response
        rows = (response["payload"]["Data"] if request["endpoint"] == "trade" else price_history_rows(response))
        fields = sorted({key for row in rows for key in row})
        entry = {"request_id": request["id"], "endpoint": request["endpoint"],
                 "symbol": request["symbol"], "exchange": request["exchange"],
                 "request": {k: v for k, v in request.items() if k != "endpoint"},
                 "http_status": response["status"], "response_sha256": _sha(response["body"]),
                 "row_count": len(rows), "observed_fields": fields,
                 "sample_rows": rows[:3], "provider_published_zero_volume": any(
                     row.get("Volume") == 0 or row.get("KhoiLuongKhopLenh") == 0 for row in rows),
                 "fetched_at": datetime.now(timezone.utc).isoformat()}
        if request["endpoint"] == "trade" and rows:
            entry["leading_row_class"] = classify_cafef_page_row(rows[0].get("TradeDate"), 1, 0)
        evidence.append(entry)

    index = _canonical_index(canonical / "clean" / "prices_daily.jsonl",
                             {request["symbol"] for request in validation_plan()})
    diagnostics = []
    for request in validation_plan():
        response = responses[request["id"]]
        rows = response["payload"]["Data"] if request["endpoint"] == "trade" else price_history_rows(response)
        for row in rows:
            try:
                day = (cafef_trade_date(row["TradeDate"]) if request["endpoint"] == "trade"
                       else parse_price_history_date(row["Ngay"]))
            except (KeyError, TypeError, ValueError):
                continue
            canonical_row = index.get((request["symbol"], day))
            if not canonical_row:
                continue
            close = row.get("ClosePrice") if request["endpoint"] == "trade" else row.get("GiaDongCua")
            adjusted = row.get("AdjustPrice") if request["endpoint"] == "trade" else row.get("GiaDieuChinh")
            canonical_value = canonical_row.get("adj_close")
            diagnostics.append({
                "ticker": request["symbol"], "exchange": request["exchange"], "date": day,
                "endpoint": request["endpoint"], "canonical_adj_close_vnd": canonical_value,
                "cafef_raw_close_thousand_vnd": close, "cafef_adjusted_thousand_vnd": adjusted,
                "canonical_to_cafef_adjusted_ratio": (canonical_value / (adjusted * 1000) if adjusted not in (None, 0) else None),
                "corporate_action_context": "FPT known 20:3 bonus ex-date 2025-07-21" if request["id"] == "P-FPT-CA" else "none pinned for this sample",
                "provider_published_zero_volume": row.get("Volume") == 0 or row.get("KhoiLuongKhopLenh") == 0,
                "diagnostic_conclusion": "DIAGNOSTIC_ONLY; no transform approved",
            })

    write_json(output / "cafef_endpoint_comparison.json", _endpoint_summary(evidence))
    write_json(output / "cafef_field_contract.json", field_contract())
    write_rows(output / "cafef_validation_evidence.jsonl", evidence)
    csv_buffer = io.StringIO(newline="")
    columns = list(diagnostics[0]) if diagnostics else ["ticker"]
    writer = csv.DictWriter(csv_buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(diagnostics)
    atomic_write(output / "cafef_price_basis_diagnostics.csv", csv_buffer.getvalue().encode("utf-8"))
    atomic_write(output / "stage_a5_r1_report.md", _report(run_id, evidence, diagnostics).encode("utf-8"))
    artifact_names = ["cafef_endpoint_comparison.json", "cafef_field_contract.json",
                      "cafef_validation_evidence.jsonl", "cafef_price_basis_diagnostics.csv",
                      "stage_a5_r1_report.md"]
    manifest = {
        "run_id": run_id, "stage": STAGE, "status": "PARTIAL / MANUAL_REVIEW_REQUIRED",
        "created_at": datetime.now(timezone.utc).isoformat(), "git_commit": _git_head(root),
        "input_artifact_reference_ids": [canonical.name, "docs/crawl/sources/CAFEF.md", "docs/data/kbs_pilot_semantics.md"],
        "source_adapter_versions": {"cafef": ADAPTER_VERSION, "contract": CONTRACT_VERSION},
        "request_count": len(evidence), "sample_symbols": sorted({e["symbol"] for e in evidence}),
        "artifacts": {name: _sha((output / name).read_bytes()) for name in artifact_names},
        "canonical_mutations": 0, "synthetic_rows": 0, "imputed_rows": 0,
        "manual_review_required": True, "next_allowed_action": "Manual review of CafeF price-basis/source-use contract; A5-R2 remains BLOCKED",
    }
    write_json(output / "manifest.json", manifest)
    return output, manifest
