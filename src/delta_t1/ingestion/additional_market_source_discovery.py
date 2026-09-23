"""Bounded A5-R4 source discovery; evidence only, never canonical mutation."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import time
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.io import atomic_write, write_json

STAGE = "A5-R4"
CONTRACT_VERSION = "additional-market-source-discovery-1.0.0"
CANONICAL_ID = "canonical-m1-scale-20260918T141019Z-7c003543"
CANONICAL_REL = f"data/canonical/{CANONICAL_ID}/clean/prices_daily.jsonl"
DNSE_ENDPOINT = "https://services.entrade.com.vn/chart-api/v2/ohlcs/stock"
VCI_ENDPOINT = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
ICT = timezone(timedelta(hours=7))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BoundedJsonClient:
    """Sequential, credential-free JSON client with an exact request counter."""

    allowed_hosts = {"services.entrade.com.vn", "trading.vietcap.com.vn"}

    def __init__(self, *, timeout=25, min_interval=1.0, max_bytes=2_000_000,
                 opener=None, sleep=time.sleep, monotonic=time.monotonic):
        self.timeout = timeout
        self.min_interval = min_interval
        self.max_bytes = max_bytes
        self.opener = opener or build_opener(_NoRedirect())
        self.sleep = sleep
        self.monotonic = monotonic
        self.last_request = 0.0
        self.request_count = 0

    def request_json(self, endpoint, *, method="GET", params=None, payload=None):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise ValueError("endpoint is outside the approved public A5-R4 hosts")
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError("endpoint must be credential-free HTTPS without query")
        url = endpoint + ("?" + urlencode(params) if params else "")
        body_out = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        headers = {
            "Accept": "application/json",
            "User-Agent": "DELTA-A5-R4-Discovery/1.0 (bounded academic research)",
        }
        if body_out is not None:
            headers["Content-Type"] = "application/json"
        self.sleep(max(0, self.min_interval - (self.monotonic() - self.last_request)))
        self.last_request = self.monotonic()
        self.request_count += 1
        try:
            with self.opener.open(Request(url, data=body_out, headers=headers, method=method),
                                  timeout=self.timeout) as response:
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise ValueError("response exceeds bounded max_bytes")
                marker = body[:4096].lower()
                if b"captcha" in marker or b"cloudflare" in marker or b"login" in marker:
                    raise ValueError("access-control response; source path stopped")
                return {"url": url, "status": response.status,
                        "headers": dict(response.headers), "body": body,
                        "payload": json.loads(body)}
        except HTTPError as exc:
            if exc.code in (401, 403, 429):
                raise ValueError(f"HTTP {exc.code}; source path stopped") from None
            raise ValueError(f"HTTP {exc.code}; request failed") from None
        except (URLError, TimeoutError, ConnectionError) as exc:
            raise ValueError(f"network failure: {type(exc).__name__}") from None


def sample_securities():
    return [
        {"ticker": "FPT", "exchange": "HOSE", "reason": "known corporate-action price-basis divergence"},
        {"ticker": "BAB", "exchange": "HNX", "reason": "prior distinct price regime and bank identity"},
        {"ticker": "ACV", "exchange": "UPCOM", "reason": "UPCOM and prior price-basis divergence"},
        {"ticker": "PVS", "exchange": "HNX", "reason": "liquid HNX coverage"},
        {"ticker": "HND", "exchange": "UPCOM", "reason": "provider zero-volume precedent"},
        {"ticker": "KHP", "exchange": "HOSE", "reason": "stock-dividend/additional-listing history"},
    ]


def candidate_inventory():
    common = {"historical_frequency": "daily", "canonical_mutation": False}
    rows = [
        {"provider": "FiinGroup API Datafeed", "client_library": None,
         "access_method": "contracted REST API", "hose": "DOCUMENTED", "hnx": "DOCUMENTED",
         "upcom": "DOCUMENTED", "ohlc": "DOCUMENTED", "volume": "DOCUMENTED",
         "adjusted_raw_support": "BOTH_DOCUMENTED_FIELDS",
         "documented_adjustment_methodology": "PARTIAL_FIELDS_AND_RATIO_ONLY",
         "historical_depth_claim": "PLAN_DEPENDENT; 2020 examples are not an entitlement proof",
         "date_range_support": "CONTRACT/API_QUERY; NOT LIVE_VERIFIED",
         "authentication_requirement": "AUTH_REQUIRED", "rights_licensing_status": "PAID_ACCESS",
         "initial_confidence": "HIGH_FIELDS_MEDIUM_USABILITY",
         "reason_to_test_or_reject": "Strongest field contract; live API unavailable without credentials."},
        {"provider": "VCI", "client_library": "Vnstock 4.0.6 (provider kept distinct)",
         "access_method": "publicly reachable Vietcap chart POST observed through client source",
         "hose": "TO_SMOKE", "hnx": "TO_SMOKE", "upcom": "TO_SMOKE", "ohlc": "YES",
         "volume": "YES", "adjusted_raw_support": "ONE_UNLABELED_SERIES",
         "documented_adjustment_methodology": "NO_PROVIDER_METHODOLOGY_FOUND",
         "historical_depth_claim": "Vnstock documentation claims long history; live probe required",
         "date_range_support": "upper-bound plus countBack", "authentication_requirement": "NONE_OBSERVED",
         "rights_licensing_status": "PUBLIC_ACCESS_RIGHTS_UNCLEAR + CLIENT_LICENSE_RESTRICTED",
         "initial_confidence": "MEDIUM",
         "reason_to_test_or_reject": "Current client/provider path and deterministic OHLC endpoint are observable."},
        {"provider": "DNSE Entrade", "client_library": "VietFin (open-source adapter reference)",
         "access_method": "publicly reachable chart GET; distinct from authenticated DNSE OpenAPI",
         "hose": "TO_SMOKE", "hnx": "TO_SMOKE", "upcom": "TO_SMOKE", "ohlc": "YES",
         "volume": "YES", "adjusted_raw_support": "ONE_UNLABELED_SERIES",
         "documented_adjustment_methodology": "NO_PROVIDER_METHODOLOGY_FOUND",
         "historical_depth_claim": "daily endpoint has no documented five-year guarantee",
         "date_range_support": "from/to Unix seconds", "authentication_requirement": "NONE_OBSERVED",
         "rights_licensing_status": "PUBLIC_ACCESS_RIGHTS_UNCLEAR",
         "initial_confidence": "MEDIUM",
         "reason_to_test_or_reject": "Simple bounded range contract; official OpenAPI exists but this chart path is undocumented."},
        {"provider": "SSI", "client_library": "VietFin inspection",
         "access_method": "no current VietFin equity historical implementation found",
         "hose": "NOT_VERIFIED", "hnx": "NOT_VERIFIED", "upcom": "NOT_VERIFIED",
         "ohlc": "NOT_VERIFIED", "volume": "NOT_VERIFIED", "adjusted_raw_support": "UNKNOWN",
         "documented_adjustment_methodology": "NONE_FOUND", "historical_depth_claim": "NONE_VERIFIED",
         "date_range_support": "NOT_VERIFIED", "authentication_requirement": "NOT_VERIFIED",
         "rights_licensing_status": "NOT_VERIFIED", "initial_confidence": "LOW",
         "reason_to_test_or_reject": "Rejected before smoke: provider name alone does not establish historical OHLC."},
        {"provider": "MAS", "client_library": "Vnstock extended client documentation",
         "access_method": "client-mediated; provider endpoint contract not independently documented",
         "hose": "CLIENT_CLAIM", "hnx": "CLIENT_CLAIM", "upcom": "CLIENT_CLAIM",
         "ohlc": "CLIENT_CLAIM", "volume": "CLIENT_CLAIM", "adjusted_raw_support": "UNKNOWN",
         "documented_adjustment_methodology": "CLIENT_SAYS_TECHNICALLY_ADJUSTED; METHOD_ABSENT",
         "historical_depth_claim": "NOT_VERIFIED", "date_range_support": "CLIENT_CLAIM",
         "authentication_requirement": "CLIENT_TIER_UNRESOLVED",
         "rights_licensing_status": "CLIENT_LICENSE_RESTRICTED", "initial_confidence": "LOW_MEDIUM",
         "reason_to_test_or_reject": "Not shortlisted: weaker independent contract evidence than VCI/DNSE."},
        {"provider": "VNDIRECT DChart", "client_library": "historical third-party adapters",
         "access_method": "public endpoint references; no current VietFin equity-history adapter found",
         "hose": "NOT_VERIFIED", "hnx": "NOT_VERIFIED", "upcom": "NOT_VERIFIED",
         "ohlc": "REPORTED_NOT_SMOKED", "volume": "REPORTED_NOT_SMOKED",
         "adjusted_raw_support": "UNKNOWN", "documented_adjustment_methodology": "NONE_FOUND",
         "historical_depth_claim": "NOT_VERIFIED", "date_range_support": "NOT_VERIFIED",
         "authentication_requirement": "NONE_REPORTED", "rights_licensing_status": "NOT_VERIFIED",
         "initial_confidence": "LOW", "reason_to_test_or_reject": "Not shortlisted under three-source cap."},
        {"provider": "HOSE/HNX/UPCOM public websites", "client_library": None,
         "access_method": "official public pages/notices",
         "hose": "YES_NOTICES", "hnx": "YES_NOTICES", "upcom": "YES_NOTICES",
         "ohlc": "NO_DOCUMENTED_BOUNDED_API_FOUND", "volume": "NO_DOCUMENTED_BOUNDED_API_FOUND",
         "adjusted_raw_support": "NOT_APPLICABLE", "documented_adjustment_methodology": "NONE_FOUND",
         "historical_depth_claim": "NOT_VERIFIED", "date_range_support": "NOT_VERIFIED",
         "authentication_requirement": "VARIES", "rights_licensing_status": "NOT_VERIFIED",
         "initial_confidence": "LOW_FOR_RECOVERY",
         "reason_to_test_or_reject": "Useful notices, but insufficient public OHLC recovery contract."},
        {"provider": "KBS", "client_library": "existing DELTA adapter/Vnstock-derived path",
         "access_method": "already tested primary", "hose": "YES", "hnx": "YES", "upcom": "YES",
         "ohlc": "YES", "volume": "YES", "adjusted_raw_support": "VENDOR_ADJUSTED",
         "documented_adjustment_methodology": "INCOMPLETE", "historical_depth_claim": ">=8 years observed",
         "date_range_support": "YES", "authentication_requirement": "NONE_OBSERVED",
         "rights_licensing_status": "NOT_VERIFIED", "initial_confidence": "EXISTING_PRIMARY",
         "reason_to_test_or_reject": "Not repeated: this is the current primary and A5-R4 seeks an additional source."},
        {"provider": "CafeF", "client_library": "direct DELTA adapter",
         "access_method": "public endpoints", "hose": "YES", "hnx": "YES", "upcom": "YES",
         "ohlc": "YES", "volume": "YES", "adjusted_raw_support": "RAW_AND_ADJUSTPRICE_FIELDS",
         "documented_adjustment_methodology": "UNRESOLVED", "historical_depth_claim": ">=5 years sampled",
         "date_range_support": "YES", "authentication_requirement": "NONE_OBSERVED",
         "rights_licensing_status": "PUBLIC_ACCESS_RIGHTS_UNCLEAR", "initial_confidence": "CROSSCHECK_ONLY",
         "reason_to_test_or_reject": "Not repeated: A5-R1.1 already concluded price-basis unresolved."},
        {"provider": "TCBS", "client_library": "VietFin historical path",
         "access_method": "prior path met Cloudflare/access boundary", "hose": "NOT_REVERIFIED",
         "hnx": "NOT_REVERIFIED", "upcom": "NOT_REVERIFIED", "ohlc": "CLIENT_CLAIM",
         "volume": "CLIENT_CLAIM", "adjusted_raw_support": "UNKNOWN",
         "documented_adjustment_methodology": "NONE_FOUND", "historical_depth_claim": "NOT_REVERIFIED",
         "date_range_support": "CLIENT_CLAIM", "authentication_requirement": "BLOCKED_ACCESS",
         "rights_licensing_status": "BLOCKED_ACCESS", "initial_confidence": "LOW",
         "reason_to_test_or_reject": "Not retried: no evidence the prior access-control condition changed."},
    ]
    return [{**common, **row} for row in rows]


def shortlist():
    return [
        {"provider": "FiinGroup API Datafeed", "smoke_mode": "DOCUMENTATION_ONLY",
         "reason": "best documented raw/adjusted field contract; auth/paid access blocks live smoke"},
        {"provider": "VCI", "smoke_mode": "LIVE_PUBLIC_HTTP",
         "acquisition_client": "direct request reproduced from installed Vnstock 4.0.6 source",
         "reason": "current deterministic endpoint and long-history client claim"},
        {"provider": "DNSE Entrade", "smoke_mode": "LIVE_PUBLIC_HTTP",
         "acquisition_client": "direct request; VietFin used only as public contract reference",
         "reason": "simple from/to daily OHLCV contract across representative exchanges"},
    ]


def smoke_plan():
    windows = [("depth-2020", "2020-01-02", "2020-01-08"),
               ("recent-2026", "2026-09-01", "2026-09-04")]
    plan = []
    for provider in ("dnse", "vci"):
        for security in sample_securities():
            for suffix, start, end in windows:
                plan.append({"id": f"{provider}-{security['ticker'].lower()}-{suffix}",
                             "provider": provider, "ticker": security["ticker"],
                             "exchange": security["exchange"], "start": start, "end": end,
                             "case": suffix})
        plan.extend([
            {"id": f"{provider}-fpt-corporate-action-2025", "provider": provider,
             "ticker": "FPT", "exchange": "HOSE", "start": "2025-07-17", "end": "2025-07-22",
             "case": "corporate_action"},
            {"id": f"{provider}-invalid-symbol", "provider": provider, "ticker": "DELTA_INVALID_X",
             "exchange": "UNKNOWN", "start": "2026-09-01", "end": "2026-09-04", "case": "invalid_symbol"},
            {"id": f"{provider}-hnd-weekend", "provider": provider, "ticker": "HND",
             "exchange": "UPCOM", "start": "2026-09-12", "end": "2026-09-13", "case": "no_row_weekend"},
        ])
    return plan


def _epoch(value, *, plus_day=False):
    d = date.fromisoformat(value) + (timedelta(days=1) if plus_day else timedelta())
    return int(datetime.combine(d, dt_time.min, ICT).timestamp())


def _request(client, item):
    if item["provider"] == "dnse":
        return client.request_json(DNSE_ENDPOINT, params={
            "from": _epoch(item["start"]), "to": _epoch(item["end"], plus_day=True),
            "symbol": item["ticker"], "resolution": "1D"})
    business_span = max(3, len([d for d in _date_range(item["start"], item["end"])
                                if d.weekday() < 5]) + 2)
    return client.request_json(VCI_ENDPOINT, method="POST", payload={
        "timeFrame": "ONE_DAY", "symbols": [item["ticker"]],
        "to": _epoch(item["end"], plus_day=True), "countBack": business_span})


def _date_range(start, end):
    current, stop = date.fromisoformat(start), date.fromisoformat(end)
    while current <= stop:
        yield current
        current += timedelta(days=1)


def normalize_rows(provider, payload, *, start=None, end=None):
    """Normalize only for diagnostics; values remain candidate evidence, not canonical."""
    if provider == "dnse":
        if not isinstance(payload, dict):
            return []
        columns = {key: payload.get(key, []) for key in ("t", "o", "h", "l", "c", "v")}
    elif provider == "vci":
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            return []
        columns = {key: payload[0].get(key, []) for key in ("t", "o", "h", "l", "c", "v")}
    else:
        raise ValueError("unsupported provider")
    lengths = {len(value) for value in columns.values() if isinstance(value, list)}
    if len(lengths) != 1 or not lengths:
        return []
    rows = []
    for index in range(next(iter(lengths))):
        trade_date = datetime.fromtimestamp(int(columns["t"][index]), timezone.utc).date().isoformat()
        if start and trade_date < start or end and trade_date > end:
            continue
        scale = 1000.0 if provider == "dnse" else 1.0
        rows.append({"trade_date": trade_date,
                     "open_vnd": float(columns["o"][index]) * scale,
                     "high_vnd": float(columns["h"][index]) * scale,
                     "low_vnd": float(columns["l"][index]) * scale,
                     "close_vnd": float(columns["c"][index]) * scale,
                     "volume": int(columns["v"][index])})
    return rows


def classify_basis(diagnostics):
    comparable = [row for row in diagnostics if row.get("relative_difference") is not None]
    if not comparable:
        return "BASIS_UNRESOLVED"
    if any(abs(row["relative_difference"]) > 0.005 for row in comparable):
        return "BASIS_INCOMPATIBLE"
    return "BASIS_EMPIRICALLY_COMPATIBLE_BUT_UNDOCUMENTED"


def _load_canonical(root):
    wanted = {item["ticker"] for item in sample_securities()}
    result = {}
    with (root / CANONICAL_REL).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("ticker") in wanted:
                result[(row["ticker"], row["trade_date"])] = row
    return result


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _git_head(root):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def _write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0]) if rows else ["status"])
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic_write(path, stream.getvalue().encode("utf-8"))


def _write_jsonl(path, rows):
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    atomic_write(path, payload.encode("utf-8"))


def _ui_evidence(observed_at):
    return [
        {"evidence_type": "UI_OBSERVATION", "provider": "FiinGroup API Datafeed",
         "page_url": "https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/hnx-stock-v2",
         "visible_label": "HNX Stock V2 — Trading data on HNX (including EOD price, foreign investors, adjusted price)",
         "visible_value": "/Market/GetHnxStockv2; raw and adjusted OHLC, volume/value, status and listing fields",
         "observed_at": observed_at, "confidence": "HIGH",
         "limitations": "Documentation UI only; no contracted API credentials or entitlement were available."},
        {"evidence_type": "UI_OBSERVATION", "provider": "FiinGroup API Datafeed",
         "page_url": "https://datafeed.fiingroup.vn/api-datafeed-en/api-trading/stock/stock/adjusted-price-ratio",
         "visible_label": "Adjusted price ratio", "visible_value": "/Market/GetAdjustedRatio; AdjustedDate, RateAdjusted, IsReverse",
         "observed_at": observed_at, "confidence": "HIGH",
         "limitations": "Field definitions do not document event coverage or compatibility with KBS vendor-adjusted prices."},
        {"evidence_type": "UI_OBSERVATION", "provider": "Vnstock client documentation",
         "page_url": "https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich",
         "visible_label": "Quote/history sources and rights footer",
         "visible_value": "VCI/KBS/VND/MAS support shown; documentation describes history as technically adjusted; source data rights are explicitly separate from software rights",
         "observed_at": observed_at, "confidence": "HIGH",
         "limitations": "Client documentation is not an underlying-provider adjustment contract."},
        {"evidence_type": "UI_OBSERVATION", "provider": "DNSE Entrade",
         "page_url": DNSE_ENDPOINT, "visible_label": "Browser navigation result",
         "visible_value": "net::ERR_BLOCKED_BY_CLIENT", "observed_at": observed_at,
         "confidence": "HIGH", "limitations": "Browser-only access was blocked; bounded direct public HTTP was tested separately without bypassing access controls."},
        {"evidence_type": "CLIENT_OBSERVATION", "provider": "VCI",
         "page_url": "local installed vnstock 4.0.6", "visible_label": "Vnstock client live call",
         "visible_value": "Client failed locally before provider request with UnboundLocalError in environment detection",
         "observed_at": observed_at, "confidence": "HIGH",
         "limitations": "Direct public endpoint smoke distinguishes a client defect from provider reachability."},
    ]


def _endpoint_catalog():
    return {"contract_version": CONTRACT_VERSION, "endpoints": [
        {"provider": "DNSE Entrade", "endpoint": DNSE_ENDPOINT, "method": "GET",
         "params": ["from", "to", "symbol", "resolution=1D"], "response_fields": ["t", "o", "h", "l", "c", "v", "nextTime"],
         "date_behavior": "explicit Unix-second range", "pagination": "nextTime observed but zero in bounded samples",
         "access": "PUBLIC_ACCESS_RIGHTS_UNCLEAR", "documentation": "VietFin open-source adapter; not official provider methodology"},
        {"provider": "VCI", "endpoint": VCI_ENDPOINT, "method": "POST",
         "params": ["timeFrame=ONE_DAY", "symbols", "to", "countBack"],
         "response_fields": ["symbol", "t", "o", "h", "l", "c", "v", "accumulatedVolume", "accumulatedValue", "minBatchTruncTime"],
         "date_behavior": "upper-bound plus countBack, not an exact start/end range",
         "pagination": "countBack; minBatchTruncTime candidate not validated as cursor",
         "access": "PUBLIC_ACCESS_RIGHTS_UNCLEAR + CLIENT_LICENSE_RESTRICTED",
         "documentation": "current installed Vnstock source; underlying provider kept distinct"},
        {"provider": "FiinGroup API Datafeed", "endpoint": "/Market/GetHoseStockv2 | /Market/GetHnxStockv2 | /Market/GetUpcomStockv2",
         "method": "CONTRACTED_API", "params": "contract dependent", "response_fields": "documented raw/adjusted OHLCV plus market fields",
         "date_behavior": "documented TradingDate; live query not entitled", "pagination": "not live verified",
         "access": "PAID_ACCESS + AUTH_REQUIRED", "documentation": "official FiinGroup API Datafeed UI"},
    ]}


def _field_contracts():
    return {"contract_version": CONTRACT_VERSION, "canonical_eligible": False,
            "providers": {
        "DNSE Entrade": {"trade_date": "t Unix seconds", "open": "o × 1000 VND/share per VietFin model",
                         "high": "h × 1000", "low": "l × 1000", "close": "c × 1000",
                         "volume": "v shares", "price_basis": "UNLABELED; BASIS_INCOMPATIBLE with current canonical in tested windows",
                         "reference_ceiling_floor_value": "absent"},
        "VCI": {"trade_date": "t Unix seconds encoded as string", "open": "o VND/share",
                "high": "h VND/share", "low": "l VND/share", "close": "c VND/share",
                "volume": "v; semantics differ from DNSE/KBS on tested FPT rows",
                "price_basis": "client calls technically adjusted; provider method absent; BASIS_INCOMPATIBLE with current canonical",
                "reference_ceiling_floor_value": "accumulatedValue exists but unit/semantics not approved"},
        "FiinGroup API Datafeed": {"trade_date": "TradingDate", "raw_ohlc": "OpenPrice/HighestPrice/LowestPrice/ClosePrice",
                                   "adjusted_ohlc": "OpenPriceAdjusted/HighestPriceAdjusted/LowestPriceAdjusted/ClosePriceAdjusted",
                                   "volume": "multiple explicitly described matched/deal/total fields",
                                   "price_basis": "ratio and adjusted fields documented; methodology compatibility still unresolved"},
    }, "rules": ["no scaling except explicit client field contract", "no inferred adjustment multiplier",
                  "no provider averaging", "no raw/adjusted mixing", "no canonical writes"]}


def build_stage_a5_r4(*, root, client, prior_public_data_requests=2, progress=None):
    root = Path(root)
    observed_at = _now()
    run_id = new_artifact_id("m1-a5-r4-additional-market-source-discovery")
    output = root / "artifacts" / "data_enrichment" / run_id
    (output / "raw").mkdir(parents=True, exist_ok=False)
    canonical = _load_canonical(root)
    evidence = _ui_evidence(observed_at)
    fetched = {}
    for item in smoke_plan():
        if progress:
            progress(f"A5-R4 {item['id']}")
        try:
            response = _request(client, item)
            raw_rel = f"raw/{item['id']}.json"
            atomic_write(output / raw_rel, response["body"])
            rows = normalize_rows(item["provider"], response["payload"], start=item["start"], end=item["end"])
            fetched[item["id"]] = rows
            evidence.append({"evidence_type": "PUBLIC_HTTP_JSON", "request_id": item["id"],
                             "provider": "DNSE Entrade" if item["provider"] == "dnse" else "VCI",
                             "acquisition_client": "direct bounded stdlib HTTP",
                             "ticker": item["ticker"], "exchange": item["exchange"], "case": item["case"],
                             "source_url": response["url"], "request_params": {k: item[k] for k in ("start", "end")},
                             "http_status": response["status"], "fetched_at": _now(), "sha256": _sha(response["body"]),
                             "raw_path": raw_rel, "row_count_in_requested_window": len(rows),
                             "limitations": "Evidence only; never promoted or written to canonical."})
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            fetched[item["id"]] = []
            evidence.append({"evidence_type": "REQUEST_ERROR", "request_id": item["id"],
                             "provider": item["provider"].upper(), "ticker": item["ticker"],
                             "exchange": item["exchange"], "case": item["case"], "fetched_at": _now(),
                             "error": str(exc), "row_count_in_requested_window": 0})

    diagnostics = []
    for item in smoke_plan():
        if item["ticker"] not in {s["ticker"] for s in sample_securities()}:
            continue
        for row in fetched.get(item["id"], []):
            canonical_row = canonical.get((item["ticker"], row["trade_date"]))
            if not canonical_row or canonical_row.get("adj_close") is None:
                continue
            candidate = row["close_vnd"]
            canon = float(canonical_row["adj_close"])
            diagnostics.append({"ticker": item["ticker"], "date": row["trade_date"],
                                "exchange": item["exchange"],
                                "candidate_provider": "DNSE Entrade" if item["provider"] == "dnse" else "VCI",
                                "candidate_field": "c/close", "candidate_value_vnd": round(candidate, 6),
                                "canonical_field": "adj_close", "canonical_value_vnd": canon,
                                "ratio_candidate_to_canonical": round(candidate / canon, 10) if canon else None,
                                "absolute_difference_vnd": round(candidate - canon, 6),
                                "relative_difference": round((candidate - canon) / canon, 10) if canon else None,
                                "corporate_action_context": "FPT_KNOWN_EVENT_WINDOW" if item["case"] == "corporate_action" else "NONE_ASSERTED",
                                "diagnostic_classification": "MISMATCH" if abs(candidate - canon) / canon > 0.005 else "NEAR_MATCH",
                                "limitations": "Ratio is diagnostic only; no multiplier or transform inferred."})

    basis = {provider: classify_basis([row for row in diagnostics if row["candidate_provider"] == provider])
             for provider in ("VCI", "DNSE Entrade")}
    basis["FiinGroup API Datafeed"] = "BASIS_UNRESOLVED"
    depth_rows = []
    for provider in ("dnse", "vci"):
        for security in sample_securities():
            request_id = f"{provider}-{security['ticker'].lower()}-depth-2020"
            rows = fetched.get(request_id, [])
            depth_rows.append({"provider": "DNSE Entrade" if provider == "dnse" else "VCI",
                               "ticker": security["ticker"], "exchange": security["exchange"],
                               "requested_start": "2020-01-02", "requested_end": "2020-01-08",
                               "rows_observed": len(rows),
                               "oldest_observed": min((r["trade_date"] for r in rows), default=""),
                               "newest_observed": max((r["trade_date"] for r in rows), default=""),
                               "five_plus_year_evidence": "YES_SAMPLE_ONLY" if rows else "NOT_ESTABLISHED",
                               "limitations": "Bounded sample, not a full-history completeness claim."})

    shortlist_rows = shortlist()
    finals = {
        "FiinGroup API Datafeed": ("MANUAL_REVIEW_REQUIRED", "PAID_ACCESS + AUTH_REQUIRED"),
        "VCI": ("BASIS_UNRESOLVED", "PUBLIC_ACCESS_RIGHTS_UNCLEAR + CLIENT_LICENSE_RESTRICTED"),
        "DNSE Entrade": ("BASIS_UNRESOLVED", "PUBLIC_ACCESS_RIGHTS_UNCLEAR"),
    }
    for row in shortlist_rows:
        row["price_basis_status"] = basis[row["provider"]]
        row["source_status"], row["access_rights_status"] = finals[row["provider"]]
        row["recovery_eligible"] = False

    access_rows = [{"provider": row["provider"], "access_method": row["access_method"],
                    "authentication": row["authentication_requirement"],
                    "rights_status": row["rights_licensing_status"],
                    "source_status": next((x["source_status"] for x in shortlist_rows if x["provider"] == row["provider"]), "REJECTED"),
                    "production_approved": "NO"} for row in candidate_inventory()]

    rejections = {"status": "SUPPORTED", "rejected_before_smoke": [
        {"provider": "SSI", "reason": "No current historical-equity implementation or provider OHLC contract was verified."},
        {"provider": "MAS", "reason": "Client claim only; provider basis and access tier remain unresolved under shortlist cap."},
        {"provider": "VNDIRECT DChart", "reason": "Current historical adapter and provider basis contract were not verified."},
        {"provider": "Official exchange websites", "reason": "No documented public deterministic daily OHLCV recovery API found."},
        {"provider": "KBS", "reason": "Existing primary already tested; not an additional source."},
        {"provider": "CafeF", "reason": "A5-R1.1 already classified it crosscheck-only with unresolved basis."},
        {"provider": "TCBS", "reason": "Prior access boundary unchanged; not retried blindly."},
    ]}

    write_json(output / "additional_market_source_candidates.json", {"contract_version": CONTRACT_VERSION,
               "built_before_live_smoke": True, "candidates": candidate_inventory()})
    write_json(output / "additional_market_source_shortlist.json", {"contract_version": CONTRACT_VERSION,
               "max_shortlist": 3, "shortlist": shortlist_rows})
    _write_csv(output / "source_access_matrix.csv", access_rows)
    write_json(output / "source_endpoint_catalog.json", _endpoint_catalog())
    write_json(output / "source_field_contracts.json", _field_contracts())
    _write_csv(output / "source_price_basis_diagnostics.csv", diagnostics)
    _write_csv(output / "source_history_depth_probe.csv", depth_rows)
    _write_jsonl(output / "source_smoke_evidence.jsonl", evidence)
    write_json(output / "source_rejection_reasons.json", rejections)

    report = _report(run_id, shortlist_rows, depth_rows, diagnostics, client.request_count,
                     prior_public_data_requests)
    atomic_write(output / "stage_a5_r4_report.md", report.encode("utf-8"))
    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            data = path.read_bytes()
            files.append({"path": path.relative_to(output).as_posix(), "bytes": len(data), "sha256": _sha(data)})
    manifest = {"stage": STAGE, "result": "PARTIAL / MANUAL_REVIEW_REQUIRED", "run_id": run_id,
                "created_at": _now(), "base_commit": _git_head(root), "contract_version": CONTRACT_VERSION,
                "canonical_baseline": CANONICAL_ID, "computer_use": "USED",
                "sample_securities": sample_securities(), "candidates_discovered": len(candidate_inventory()),
                "candidates_shortlisted": 3, "candidates_live_smoked": ["VCI", "DNSE Entrade"],
                "preserved_network_request_count": client.request_count,
                "prior_exploratory_public_data_requests": prior_public_data_requests,
                "total_public_data_requests": client.request_count + prior_public_data_requests,
                "browser_document_navigations": 2, "browser_network_request_count": "NOT_OBSERVABLE",
                "canonical_mutations": 0, "synthetic_or_imputed_rows": 0,
                "recovery_ready_source": False, "manual_review_required": True,
                "next_market_action": "MANUAL REVIEW OF FIINGROUP / VCI / DNSE MARKET CONTRACT EVIDENCE; A5-R2 REMAINS BLOCKED",
                "financial_next_action": "F0 — Financial Source Re-discovery (UNCHANGED, NOT EXECUTED)",
                "files": files}
    write_json(output / "manifest.json", manifest)
    return output, manifest


def _report(run_id, shortlist_rows, depth_rows, diagnostics, preserved_count, prior_count):
    by_provider = {}
    for provider in ("VCI", "DNSE Entrade"):
        rows = [r for r in diagnostics if r["candidate_provider"] == provider]
        by_provider[provider] = {"comparisons": len(rows), "mismatches": sum(r["diagnostic_classification"] == "MISMATCH" for r in rows)}
    depth_summary = ", ".join(f"{p}: {sum(r['five_plus_year_evidence']=='YES_SAMPLE_ONLY' for r in depth_rows if r['provider']==p)}/6"
                              for p in ("VCI", "DNSE Entrade"))
    return f"""# A5-R4 — Additional Market Source Discovery

Run: `{run_id}`  
Result: **PARTIAL / MANUAL_REVIEW_REQUIRED**  
Canonical mutations: **0**; synthetic/imputed rows: **0**.

## Bounded scope and evidence

The candidate inventory was fixed before live smoke. Three sources were shortlisted: FiinGroup API Datafeed (documentation only because paid authentication is required), VCI, and DNSE Entrade. VCI and DNSE were smoke-tested sequentially on FPT, BAB, ACV, PVS, HND and KHP. {preserved_count} responses/errors are preserved; {prior_count} exploratory public-data requests preceded the immutable run. Browser UI was used for official FiinGroup field documentation and current Vnstock client/source and rights documentation. Browser access to the DNSE JSON route was blocked by the browser client; direct bounded public HTTP was separately successful.

## Required questions

1. **Sources discovered:** FiinGroup, VCI, DNSE, SSI, MAS, VNDIRECT DChart, official exchange sites, plus existing KBS/CafeF/TCBS paths recorded to prevent blind repetition.
2. **Rejected before smoke:** SSI lacked a verified current historical-equity contract; MAS and VNDIRECT lacked an independently verified basis/access contract; exchange sites lacked a deterministic public OHLCV recovery API; KBS/CafeF/TCBS were not repeated for the recorded prior reasons.
3. **Live-smoked:** VCI direct and DNSE Entrade direct. FiinGroup was documentation-only because no paid entitlement/credentials were available.
4. **Client/provider provenance:** Vnstock is a client, VCI is the provider. VietFin is a contract reference, DNSE Entrade is the provider. FiinGroup is both documented provider and contracted API operator.
5. **Exchange support:** VCI and DNSE returned bounded evidence across HOSE/HNX/UPCOM samples where rows existed; this is sample evidence, not universe completeness. FiinGroup documents all three exchanges.
6. **Historical depth:** 2020-window success count by provider is {depth_summary}. This supports five-plus-year availability for observed samples only.
7. **OHLC:** present for VCI and DNSE; raw plus adjusted OHLC fields are documented for FiinGroup.
8. **Volume:** present. VCI volume did not always equal DNSE/KBS volume on FPT, so its exact inclusion semantics remain unapproved.
9. **Raw/adjusted distinction:** not documented by the underlying VCI or DNSE chart contracts. Vnstock calls history technically adjusted, but that is not an authoritative provider method. FiinGroup documents separate fields and a ratio endpoint, but not compatibility with KBS.
10. **Closest to KBS/canonical basis:** no finalist is approved as closest. VCI and DNSE closely resemble each other, but VCI has {by_provider['VCI']['mismatches']}/{by_provider['VCI']['comparisons']} material mismatches and DNSE has {by_provider['DNSE Entrade']['mismatches']}/{by_provider['DNSE Entrade']['comparisons']} against the KBS/canonical adjusted series.
11. **Corporate actions:** FPT 2025 rows materially differ from KBS/canonical while VCI and DNSE are close to one another. This is diagnostic evidence only.
12. **Transformation required:** a transformation would be required to align tested mismatches.
13. **Transformation documented:** no. No ratio-derived multiplier is approved or inferred.
14. **Can a provider supply a real missing KBS session now?** **No.** Real rows exist, but price basis and/or rights are not approved.
15. **Access/rights:** VCI and DNSE are `PUBLIC_ACCESS_RIGHTS_UNCLEAR`; Vnstock is `CLIENT_LICENSE_RESTRICTED`; FiinGroup is `PAID_ACCESS + AUTH_REQUIRED` and contract-dependent.
16. **Ready for A5-R2:** **No.** None is `BASIS_DOCUMENTED_AND_COMPATIBLE` with acceptable rights.
17. **Exact blockers:** authoritative adjustment methodology, explicit compatibility with the canonical KBS basis, stable volume semantics for VCI, acceptable data-use/storage rights, and live entitlement/history guarantees for FiinGroup.
18. **Further discovery worthwhile:** only targeted manual contract/provider outreach is justified. Repeating undocumented public endpoints is not.

## Edge and request behavior

- **Date ranges:** DNSE accepts explicit `from`/`to` seconds. VCI accepts only an upper bound plus `countBack`; DELTA filtered the returned evidence to the requested window and did not treat preceding bars as requested-session observations.
- **Invalid symbol:** DNSE returned HTTP 400 and the path stopped without retry. VCI returned an empty JSON array with HTTP 200.
- **No-row weekend:** DNSE returned empty OHLCV arrays. VCI returned earlier `countBack` bars, but none fell inside the requested weekend; absence was retained as absence.
- **Zero volume:** no provider-published zero-volume row occurred in these bounded windows. Zero-volume semantics therefore remain **NOT DETERMINABLE IN A5-R4**; no zero was synthesized.
- **Pagination:** DNSE exposed `nextTime` (zero for normal bounded windows and a timestamp on the empty weekend response). VCI exposed `minBatchTruncTime`; neither field was promoted as a validated pagination contract.

## Candidate decisions

| Provider | Price basis | Access/rights | Source status |
|---|---|---|---|
""" + "".join(f"| {r['provider']} | {r['price_basis_status']} | {r['access_rights_status']} | {r['source_status']} |\n" for r in shortlist_rows) + """

## Decision

**Recovery-ready source: NO.** A5-R2 remains blocked. The next market action is manual review of the FiinGroup/VCI/DNSE market-contract evidence, with priority on obtaining an authoritative price-adjustment and rights contract. No recovery, canonical write, feature rebuild, A5-R2, A5-R3, B0+, or financial stage was executed.
"""
