"""Offline annual acquisition checklist; presence never grants feature eligibility."""
import csv
import io
import json
from pathlib import Path

from .cafef_financial import digest, encoded, immutable_write
from .cafef_financial_detail import verify
from .financial_data_report import FIELDS

# Raw provider matching only. A full fixed-assets line is not net tangible PPE.
EXTRA = {"net_tangible_ppe": ("bsheet", "221", "hữu hình"),
         "net_finance_lease_assets": ("bsheet", "224", "thuê tài chính"),
         "net_intangible_assets": ("bsheet", "227", "vô hình"),
         "cash_and_equivalents": ("bsheet", "110", "tiền"),
         "non_controlling_interests": ("bsheet", "429", "kiểm soát"),
         "short_term_borrowings_and_leases": ("bsheet", "320", "vay")}
NOTES = ["income_before_extraordinary_items", "long_term_debt_including_current_portion",
         "parent_common_equity_issuance_verified", "ppe_depreciation_excluding_amortization",
         "document_reconciled_ebit", "weighted_average_basic_shares", "weighted_average_diluted_shares",
         "eps_adjusted_earnings_numerator", "historical_common_shares_outstanding",
         "parent_common_equity", "share_basis_adjustment_history"]


def export_requirements(detail_run, policy_path, output):
    source = Path(detail_run).resolve()
    verify(source)
    policy = json.loads(Path(policy_path).read_bytes())
    source_config = json.loads((source / "config.json").read_bytes())
    if (policy.get("contract_version") != "financial-evidence-policy-v1"
            or policy["financial_features_allowed"] is not False or policy["financial_pit_gate"] != "NOT_READY"
            or policy["symbols"] != source_config["symbols"]
            or not 1900 <= policy["annual_document_start_year"] <= policy["annual_document_end_year"] <= 2100
            or policy["annual_document_end_year"] - policy["annual_document_start_year"] > 9):
        raise ValueError("acquisition checklist must not approve financial features")
    years = range(policy["annual_document_start_year"], policy["annual_document_end_year"] + 1)
    facts = [f for p in sorted((source / "raw").rglob("*.parsed.json"))
             for f in json.loads(p.read_bytes())["facts"] if f["quarter"] == 0]
    rows = []
    for symbol in policy["symbols"]:
        for year in years:
            for field, (statement, code, token) in {**FIELDS, **EXTRA}.items():
                candidates = [f for f in facts if f["symbol"] == symbol and f["year"] == year
                              and f["provider_statement"] == statement and f["provider_item_code"] == code
                              and token in f["item_name"].casefold() and f["display_number_candidate"] is not None]
                values = sorted({str(f["display_number_candidate"]) for f in candidates})
                rows.append({"symbol": symbol, "year": year, "field": field,
                             "presence_status": "MISSING" if not values else ("VALUE_CONFLICT" if len(values) > 1 else "RAW_CANDIDATE_PRESENT"),
                             "candidate_values": values, "source_evidence": [{"path": f["raw_path"], "sha256": f["raw_sha256"]} for f in candidates],
                             "unit_status": "UNVERIFIED_DETAIL_DISPLAY", "available_at": None,
                             "financial_features_allowed": False})
            for field in NOTES:
                rows.append({"symbol": symbol, "year": year, "field": field, "presence_status": "DOCUMENT_NOTE_REVIEW_REQUIRED",
                             "candidate_values": [], "source_evidence": [], "available_at": None, "financial_features_allowed": False})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    result = {"version": "financial-annual-requirements-v1", "rows": rows,
              "detail_run": str(source), "detail_manifest_sha256": digest((source / "manifest.json").read_bytes()),
              "policy_sha256": digest(Path(policy_path).read_bytes()), "financial_features_allowed": False,
              "financial_pit_gate": "NOT_READY", "meaning": "Raw field presence includes 2019/2020 columns from preserved HTML; not canonical or PIT approval."}
    immutable_write(output / "requirements.json", encoded(result))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["symbol", "year", "field", "presence_status", "candidate_values", "financial_features_allowed"], extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows)
    immutable_write(output / "requirements.csv", stream.getvalue().encode("utf-8-sig"))
    immutable_write(output / "policy.json", Path(policy_path).read_bytes())
    immutable_write(output / "analyzer.py", Path(__file__).read_bytes())
    immutable_write(output / "manifest.json", encoded({"files": {p.name: digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}}))
    return result
