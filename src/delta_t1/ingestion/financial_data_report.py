"""Offline financial field inventory and comparison evidence; never ratios."""
import csv
import io
import json
from pathlib import Path

from .cafef_financial import digest, encoded, immutable_write
from .cafef_financial_detail import verify

# Candidate checklist for the four non-bank pilot issuers, not approved taxonomy.
FIELDS = {
    "net_revenue": ("incsta", "10", "doanh thu thuần"),
    "cost_of_sales": ("incsta", "11", "giá vốn"),
    "gross_profit": ("incsta", "20", "lợi nhuận gộp"),
    "interest_expense": ("incsta", "23", "lãi vay"),
    "selling_expense": ("incsta", "25", "bán hàng"),
    "administrative_expense": ("incsta", "26", "quản lý"),
    "profit_before_tax": ("incsta", "50", "trước thuế"),
    "net_profit": ("incsta", "60", "sau thuế"),
    "parent_net_profit": ("incsta", "61", "công ty mẹ"),
    "vendor_basic_eps": ("incsta", "70", "cơ bản"),
    "vendor_diluted_eps": ("incsta", "71", "suy giảm"),
    "current_assets": ("bsheet", "100", "tài sản ngắn hạn"),
    "customer_receivables_short_term": ("bsheet", "131", "khách hàng"),
    "inventory": ("bsheet", "140", "tồn kho"),
    "fixed_assets": ("bsheet", "220", "cố định"),
    "total_assets": ("bsheet", "270", "tài sản"),
    "total_liabilities": ("bsheet", "300", "nợ phải trả"),
    "current_liabilities": ("bsheet", "310", "ngắn hạn"),
    "long_term_borrowings": ("bsheet", "338", "vay"),
    "total_equity": ("bsheet", "400", "vốn chủ sở hữu"),
    "retained_earnings": ("bsheet", "421", "chưa phân phối"),
    "depreciation": ("cashflow", "02", "khấu hao"),
    "operating_cash_flow": ("cashflow", "20", "hoạt động kinh doanh"),
    "ppe_purchase_cash_flow": ("cashflow", "21", "mua sắm"),
    "share_issue_cash_flow": ("cashflow", "31", "phát hành cổ phiếu"),
}

# Field crosswalk for comparison only; mismatches are not resolved or merged.
CROSSWALK = {"incsta": {"KQKD_2": "10", "KQKD_3": "11", "KQKD_4": "20",
                         "KQKD_12": "50", "KQKD_13": "60", "KQKD_14": "61", "KQKD_15": "70"},
             "bsheet": {"CDKT_17": "100", "CDKT_27": "270", "CDKT_28": "300", "CDKT_31": "400"}}


def analyze(detail_run, summary_run):
    run = Path(detail_run).resolve()
    coverage = verify(run)
    config = json.loads((run / "config.json").read_text(encoding="utf-8"))
    facts = [f for p in sorted((run / "raw").rglob("*.parsed.json"))
             for f in json.loads(p.read_text(encoding="utf-8"))["facts"]
             if config["start_year"] <= f["year"] <= config["end_year"]]
    fields = []
    for symbol in config["symbols"]:
        for name, (statement, code, token) in FIELDS.items():
            selected = [f for f in facts if f["symbol"] == symbol and f["provider_statement"] == statement
                        and f["provider_item_code"] == code and token in f["item_name"].casefold()]
            annual = {f["year"] for f in selected if f["quarter"] == 0 and f["display_number_candidate"] is not None}
            quarterly = {(f["year"], f["quarter"]) for f in selected if f["quarter"] != 0 and f["display_number_candidate"] is not None}
            fields.append({"symbol": symbol, "candidate_field": name, "provider_statement": statement,
                           "provider_code": code, "annual_periods_non_null": len(annual),
                           "quarterly_periods_non_null": len(quarterly), "item_names": sorted({f["item_name"] for f in selected}),
                           "status": "CANDIDATE_ONLY", "financial_features_allowed": False})
    comparisons = []
    for typ, crosswalk in CROSSWALK.items():
        detail = {}
        for f in facts:
            if f["provider_statement"] == typ and f["display_number_candidate"] is not None:
                key = (f["symbol"], f["year"], f["quarter"], f["provider_item_code"])
                detail.setdefault(key, set()).add(str(f["display_number_candidate"]))
        for p in sorted((Path(summary_run) / "raw").rglob("page-*.json")):
            if p.name.endswith((".metadata.json", ".error.json")):
                continue
            if p.with_name(p.stem + ".error.json").exists():
                continue  # Preserve failed pages as evidence; do not use in comparison.
            payload = json.loads(p.read_bytes())
            for group in payload.get("value", {}).get("data", []):
                for row in group.get("data", []):
                    if not config["start_year"] <= row["year"] <= config["end_year"]:
                        continue
                    for f in row.get("data", []):
                        if f["code"] not in crosswalk or f["value"] is None:
                            continue
                        key = (row["symbol"], row["year"], row["quater"], crosswalk[f["code"]])
                        vals = detail.get(key, set())
                        if vals:
                            comparisons.append({"key": list(key), "summary_value": f["value"], "detail_display_candidates": sorted(vals),
                                                "status": "NUMERIC_MATCH_ONLY" if vals == {str(f["value"])} else "UNRESOLVED_VALUE_CONFLICT"})
    return {"coverage": coverage, "field_inventory": fields, "comparisons": comparisons,
            "comparison_counts": {status: sum(c["status"] == status for c in comparisons)
                                  for status in ("NUMERIC_MATCH_ONLY", "UNRESOLVED_VALUE_CONFLICT")},
            "meaning": "Numeric comparison does not approve units, timing, scope or report vintage.",
            "financial_features_allowed": False}, facts


def export(detail_run, summary_run, output):
    # Verify legacy raw evidence using its own contract before comparison.
    from .cafef_financial import verify as verify_summary
    verify_summary(summary_run)
    result, facts = analyze(detail_run, summary_run)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    immutable_write(output / "analysis.json", encoded(result))
    stream = io.StringIO(newline="")
    keys = ["symbol", "provider_statement", "year", "quarter", "provider_item_code", "item_name",
            "raw_value_text", "display_number_candidate", "unit_status", "period_semantics", "raw_path", "raw_sha256"]
    writer = csv.DictWriter(stream, fieldnames=keys, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(facts)
    immutable_write(output / "candidate_facts.csv", stream.getvalue().encode("utf-8-sig"))
    immutable_write(output / "inputs.json", encoded({"detail_run": str(Path(detail_run).resolve()),
                    "detail_manifest_sha256": digest((Path(detail_run) / "manifest.json").read_bytes()),
                    "summary_run": str(Path(summary_run).resolve()),
                    "summary_manifest_sha256": digest((Path(summary_run) / "manifest.json").read_bytes())}))
    immutable_write(output / "analyzer.py", Path(__file__).read_bytes())
    immutable_write(output / "manifest.json", encoded({"files": {
        p.name: digest(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()}}))
    return result
