from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_offline_reconcile import (
    reconcile_row, term_agreement, fact, valid_fields,
)


def vci(**kwargs):
    return {"symbol": "AAA", "event_type": "ISS", "event_title": "Phát hành cổ phiếu - Quyền mua CP tỉ lệ 25%",
            "ratio": .25, "value": None, "ex_right_date": "2024-03-19T17:00:00.000Z",
            "record_date": "2024-03-20T17:00:00.000Z", "public_date": "2024-03-04T17:00:00.000Z", **kwargs}


def official(identifier="one", **values):
    base = {"ticker": "AAA", "event_type": "RIGHTS_ISSUE", "record_date": "2024-03-21",
            "rights_ratio": .25, "rights_subscription_price": 10000, "currency": "VND", "announcement_date": "2024-03-06"}
    base.update(values)
    observation = {"source_type": "VSDC", "observation_id": identifier, "source_hash": identifier,
        "source_url": "https://vsdc.vn/vi/ad/1", "parser": "fixture", "parser_issues": [],
        "fields": {k: {"parse_status": "VALID", "normalized_value": v, "raw_value": str(v)} for k, v in base.items()}}
    return fact(observation, {"fixture": identifier})


class ReconciliationTests(unittest.TestCase):
    def test_exact_record_terms_proposes_price_without_modifying_any_input(self):
        row = vci(); before = deepcopy(row)
        result = reconcile_row(row, [official()], [])
        self.assertEqual(10000, result["fields"]["rights_subscription_price"]["proposed_value_pending_review"])
        self.assertEqual(before, row)
        self.assertFalse(result["canonical_promoted"])
        self.assertEqual("MANUAL_REVIEW_REQUIRED", result["review_status"])
        self.assertEqual("NOT_PROMOTED", result["pit_status"])
        self.assertNotIn("available_at", result)

    def test_same_price_int_float_metadata_do_not_create_value_conflict(self):
        result = reconcile_row(vci(), [official(), official("two", rights_subscription_price=10000.0)], [])
        field = result["fields"]["rights_subscription_price"]
        self.assertEqual(1, len(field["candidate_values"]))
        self.assertEqual(2, len(field["candidate_values"][0]["evidence"]))

    def test_conflicting_prices_are_retained_not_averaged_or_source_prioritized(self):
        result = reconcile_row(vci(), [official(), official("two", rights_subscription_price=20000)], [])
        field = result["fields"]["rights_subscription_price"]
        self.assertIsNone(field["proposed_value_pending_review"])
        self.assertEqual({10000, 20000}, {x["value"] for x in field["candidate_values"]})

    def test_different_ratio_on_same_dated_event_blocks_otherwise_matching_proposals(self):
        result = reconcile_row(vci(), [official(), official("two", rights_ratio=.5)], [])
        self.assertTrue(result["event_match_ambiguous"])
        self.assertIsNone(result["fields"]["rights_subscription_price"]["proposed_value_pending_review"])

    def test_missing_dates_only_record_supported_never_infers_previous_session(self):
        result = reconcile_row(vci(ex_right_date=None, record_date=None), [official()], [])
        self.assertEqual("2024-03-21", result["fields"]["record_date"]["proposed_value_pending_review"])
        self.assertIsNone(result["fields"]["ex_date"]["proposed_value_pending_review"])
        self.assertFalse(result["time_hint_is_publication_or_available_at"])

    def test_missing_dates_sdk_sibling_can_be_corroborated_by_explicit_official_ex_date(self):
        target = vci(ex_right_date=None, record_date=None)
        calendar = official(event_type="RIGHTS_ISSUE", ex_date="2024-03-20", record_date=None, rights_ratio=None, rights_subscription_price=None)
        result = reconcile_row(target, [calendar], [vci()])
        self.assertEqual("2024-03-20", result["fields"]["ex_date"]["proposed_value_pending_review"])
        self.assertTrue(result["official_links"])
        self.assertTrue(result["sdk_sibling_links"])

    def test_two_possible_event_dates_do_not_select_the_nearest_or_partial_pair(self):
        result = reconcile_row(vci(ex_right_date=None, record_date=None),
            [official(), official("other_event", record_date="2024-04-10", announcement_date="2024-03-07")], [vci()])
        self.assertTrue(result["event_match_ambiguous"])
        self.assertIsNone(result["fields"]["ex_date"]["proposed_value_pending_review"])
        self.assertIsNone(result["fields"]["record_date"]["proposed_value_pending_review"])

    def test_previous_year_same_ticker_ratio_is_not_enough_for_missing_dates(self):
        result = reconcile_row(vci(ex_right_date=None, record_date=None),
            [official(record_date="2023-03-21", announcement_date="2023-03-06")], [])
        self.assertFalse(result["official_links"])
        self.assertIsNone(result["fields"]["record_date"]["proposed_value_pending_review"])

    def test_dated_anchor_does_not_treat_later_update_timestamp_as_pit(self):
        result = reconcile_row(vci(), [official(announcement_date="2026-01-01")], [])
        self.assertEqual(10000, result["fields"]["rights_subscription_price"]["proposed_value_pending_review"])
        self.assertEqual("NOT_PROMOTED", result["pit_status"])

    def test_explicit_zero_subscription_price_is_preserved_not_filled_from_missing(self):
        zero = reconcile_row(vci(), [official(rights_subscription_price=0)], [])
        missing = reconcile_row(vci(), [official(rights_subscription_price=None)], [])
        self.assertEqual(0, zero["fields"]["rights_subscription_price"]["proposed_value_pending_review"])
        self.assertIsNone(missing["fields"]["rights_subscription_price"]["proposed_value_pending_review"])

    def test_other_type_or_other_ticker_is_not_associated(self):
        result = reconcile_row(vci(), [official(ticker="BBB"), official("other", event_type="OTHER")], [])
        self.assertFalse(result["official_links"])

    def test_invalid_ticker_is_not_replaced_by_job_assignment(self):
        observation = {"source_type": "VSDC", "observation_id": "id", "source_hash": "hash", "source_url": "url", "parser": "fixture",
            "fields": {"ticker": {"parse_status": "INVALID", "normalized_value": "AAA"}}, "parser_issues": []}
        self.assertNotIn("ticker", valid_fields(observation))
        self.assertIsNone(fact(observation, {})["ticker"])

    def test_serialization_precision_match_does_not_rewrite_economic_values(self):
        self.assertEqual("SDK_SERIALIZATION_PRECISION_COMPATIBLE", term_agreement(.8571428571, 30/35))
        self.assertEqual("DIFFERENT", term_agreement(.8571428571, .85715))
        self.assertEqual("NOT_COMPARABLE", term_agreement(0, None))


if __name__ == "__main__":
    unittest.main()
