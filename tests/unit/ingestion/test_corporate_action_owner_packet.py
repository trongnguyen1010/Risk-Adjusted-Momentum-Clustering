from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_owner_packet import assemble_case, exact_ratio, field_choice, owner_template, render_html


def request(ticker="AAA", kind="CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL", n=1, d=6):
    return {"ticker": ticker, "vci_payload_sha256": "payload-" + ticker, "original_record_date_review_view": "2021-01-20",
        "original_sdk_row": {"symbol": ticker, "ratio": .16666667}, "decision_class": kind,
        "observed_price_vnd": "10000", "owner_decision": None, "canonical_written": False, "signature_created": False,
        "sources": [{"document_id": "source1", "ticker_record_supported": True, "primary_unit_explicit": True,
            "price_vnd": "10000", "ratio_exact": {"numerator": n, "denominator": d}}]}


def revision(r, supported=True):
    return {"vci_payload_sha256": r["vci_payload_sha256"], "original_sdk_row": deepcopy(r["original_sdk_row"]),
        "status": "CONTEXTUAL_FIELD_PROPOSAL_PENDING_APPROVAL" if supported else "HOLD_LINEAGE_GAP_OR_ANOMALY",
        "edges": [{"contextual_link_supported": supported}],
        "observed_fields_for_owner_review": {"rights_ratio": {"numerator": 1, "denominator": 6}},
        "hold_reasons": [] if supported else ["CONTRADICTORY_NOTICE_DATE_LITERALS"]}


def primary(r, doc_id="notice"):
    return {"vci_payload_sha256": r["vci_payload_sha256"], "original_sdk_row": deepcopy(r["original_sdk_row"]),
        "record_date": r["original_record_date_review_view"], "observed_rights_ratio": deepcopy(r["sources"][0]["ratio_exact"]),
        "observed_price_vnd_per_share": 10000, "source_documents": [doc_id], "one_third_inferred": False,
        "source_ratio_percent_literal": "33,3333%", "field_approved": False, "canonical_written": False}


DOC = {"id": "notice", "primary_price_vnd": 10000, "primary_price_unit_literal": "đồng/cổ phiếu"}


class OwnerPacketTests(unittest.TestCase):
    def test_case_specific_ratio_and_price_are_dependent_unsigned_requests(self):
        r = request(); saved = deepcopy(r)
        c = assemble_case(r)
        self.assertEqual(saved, r)
        self.assertEqual(["rights_subscription_price", "rights_ratio"], [f["field"] for f in c["proposed_fields"]])
        self.assertEqual(["rights_ratio"], c["proposed_fields"][0]["requires_approval_of_fields_in_same_case"])
        self.assertEqual({"numerator": 1, "denominator": 6}, c["proposed_fields"][1]["observed_value_proposed"])
        self.assertEqual(.16666667, c["original_sdk_row"]["ratio"])
        self.assertTrue(all(f["owner_decision"] is None and not f["applied"] for f in c["proposed_fields"]))

    def test_existing_rule_does_not_silently_replace_sdk_ratio_with_source_fraction(self):
        r = request("CIA", "EXISTING_RULE_PRICE_SELECTION_PROPOSAL", 20, 37)
        r["original_sdk_row"]["ratio"] = .5405405405
        c = assemble_case(r)
        self.assertEqual(1, len(c["proposed_fields"]))
        self.assertEqual(.5405405405, c["sdk_ratio_preserved"])
        self.assertEqual("rights_subscription_price", c["proposed_fields"][0]["field"])

    def test_dtp_literal_is_not_inferred_one_third(self):
        r = request("DTP", "HOLD_RATIO_REQUIRES_ADDITIONAL_PRIMARY_EVIDENCE", 333333, 1000000)
        r["original_sdk_row"]["ratio"] = .33333333
        c = assemble_case(r, primary=primary(r), primary_documents=[DOC])
        self.assertEqual({"numerator": 333333, "denominator": 1000000}, c["proposed_fields"][1]["observed_value_proposed"])
        r["sources"][0]["ratio_exact"] = {"numerator": 1, "denominator": 3}
        with self.assertRaisesRegex(ValueError, "NOT_ONE_THIRD"):
            assemble_case(r, primary=primary(r), primary_documents=[DOC])

    def test_dtp_without_primary_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PRIMARY_RATIO"):
            assemble_case(request("DTP", "HOLD_RATIO_REQUIRES_ADDITIONAL_PRIMARY_EVIDENCE"))

    def test_asg_missing_unit_cannot_borrow_residual_unit(self):
        r = request("ASG", "PRIMARY_UNIT_DOCUMENT_PROPOSAL", 3, 20)
        r["sources"][0]["primary_unit_explicit"] = False
        p = primary(r); p["residual_price_unit_borrowed"] = True
        with self.assertRaises(ValueError):
            assemble_case(r, primary=p, primary_documents=[DOC])
        p["residual_price_unit_borrowed"] = False
        c = assemble_case(r, primary=p, primary_documents=[DOC])
        self.assertEqual(1, len(c["proposed_fields"]))

    def test_pdf_unit_or_price_conflict_fails_closed(self):
        r = request("ASG", "PRIMARY_UNIT_DOCUMENT_PROPOSAL")
        for bad in [dict(DOC, primary_price_vnd=15000), dict(DOC, primary_price_unit_literal="đồng")]:
            with self.assertRaisesRegex(ValueError, "PDF_PRICE_UNIT"):
                assemble_case(r, primary=primary(r), primary_documents=[bad])

    def test_kpf_remains_held_despite_supported_price(self):
        r = request("KPF", "HOLD_LINKED_CHANGE_REVIEW", 2, 1)
        c = assemble_case(r, revision(r, False))
        self.assertEqual([], c["proposed_fields"])
        self.assertEqual(1, len(c["held_fields"]))
        self.assertEqual("H_KPF_NOTICE_DATE_ANOMALY", c["group"])
        t = owner_template([c], "packet")
        self.assertTrue(t["cases"][0]["hold_must_remain"])
        self.assertEqual([], t["cases"][0]["field_decisions"])

    def test_missing_or_false_revision_support_cannot_become_proposal(self):
        r = request("GSP", "HOLD_LINKED_CHANGE_REVIEW")
        with self.assertRaises(ValueError):
            assemble_case(r)
        rv = revision(r); rv["edges"][0]["contextual_link_supported"] = False
        with self.assertRaises(ValueError):
            assemble_case(r, rv)

    def test_revision_payload_or_sdk_mismatch_is_rejected(self):
        r = request("GSP", "HOLD_LINKED_CHANGE_REVIEW")
        rv = revision(r); rv["original_sdk_row"]["ratio"] = .5
        with self.assertRaises(ValueError):
            assemble_case(r, rv)

    def test_source_value_or_record_anchor_conflicts_are_rejected(self):
        r = request(); r["sources"].append(dict(r["sources"][0], price_vnd="12000"))
        with self.assertRaises(ValueError):assemble_case(r)
        r = request(); r["sources"][0]["ticker_record_supported"] = False
        with self.assertRaises(ValueError):assemble_case(r)

    def test_no_approved_or_canonical_inputs_are_inherited(self):
        for key, value in [("owner_decision", "yes"), ("signature_created", True), ("canonical_written", True)]:
            r = request(); r[key] = value
            with self.assertRaises(ValueError):assemble_case(r)

    def test_exact_ratio_rejects_bool_float_and_nonpositive(self):
        for n, d in [(True, 2), (1.0, 2), (1, 0), (-1, 2)]:
            with self.assertRaises(ValueError):exact_ratio({"numerator": n, "denominator": d})

    def test_field_scope_and_units_are_explicit(self):
        for name in ["available_at", "security_id", "adjustment_factor", "cash_dividend_per_share"]:
            with self.assertRaises(ValueError):field_choice("p", name, "1", ["e"])
        for price in ["0", "1.5", "-1", 10000, True]:
            with self.assertRaises(ValueError):field_choice("p", "rights_subscription_price", price, ["e"])

    def test_choice_ids_bind_values_sources_and_payloads(self):
        a = field_choice("p", "rights_subscription_price", "10000", ["a"])
        for other in [field_choice("q", "rights_subscription_price", "10000", ["a"]),
            field_choice("p", "rights_subscription_price", "10001", ["a"]),
            field_choice("p", "rights_subscription_price", "10000", ["b"])]:
            self.assertNotEqual(a["choice_id"], other["choice_id"])

    def test_template_is_blank_unsigned_and_not_importable(self):
        t = owner_template([assemble_case(request())], "packet")
        self.assertFalse(t["importable_as_production_decisions"])
        self.assertIsNone(t["owner_name"]); self.assertIsNone(t["signature"])
        self.assertTrue(all(f["owner_decision"] is None for f in t["cases"][0]["field_decisions"]))

    def test_html_escapes_provider_text_and_has_no_external_scripts(self):
        r = request(); r["ticker"] = '<script>alert("x")</script>'
        c = assemble_case(r)
        html = render_html([c], {"payload_count": 1, "ticker_count": 1, "proposed_case_count": 1, "proposed_field_count": 2}, "packet")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("MANUAL_REVIEW_REQUIRED", html)

    def test_runner_refuses_overwrite_and_path_escape(self):
        spec = importlib.util.spec_from_file_location("owner_packet_runner", ROOT / "scripts/build_corporate_action_owner_packet_v1.py")
        runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
        with self.assertRaises(FileExistsError):runner.run(ROOT)
        with self.assertRaises(ValueError):runner.safe(ROOT, "../outside")


if __name__ == "__main__":unittest.main()
