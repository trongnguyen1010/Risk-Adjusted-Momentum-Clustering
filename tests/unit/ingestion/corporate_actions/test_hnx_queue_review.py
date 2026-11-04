from copy import deepcopy
import unittest

from delta_t1.ingestion.corporate_actions.hnx_components import parse_popup_components
from delta_t1.ingestion.corporate_actions.hnx_queue_review import (
    compare, review_observations, field_queue, price_proposal, PENDING, MISSING,
)
from delta_t1.ingestion.corporate_action_offline_reconcile import key
from tests.unit.ingestion.corporate_actions.test_hnx_components import sample, MBS_TITLE, TNG_TITLE


def mbs():
    return {"symbol": "MBS", "event_type": "ISS", "event_title": "Phát hành cổ phiếu - Quyền mua CP tỉ lệ 12%",
        "ex_right_date": "2025-09-23T17:00:00.000Z", "record_date": "2025-09-24T17:00:00.000Z",
        "public_date": "2025-09-22T17:00:00.000Z", "ratio": .12, "value": None}


def queue(row):
    return {"ticker": row["symbol"], "vci_payload_sha256": key(row), "original_sdk_row": deepcopy(row),
        "missing_fields": ["rights_subscription_price"], "canonical_approved": False,
        "historical_identity": "UNVERIFIED", "event_lifecycle": "UNVERIFIED_PLAN_VS_EXECUTED_EVENT"}


def rights():
    return parse_popup_components(*sample("MBS", "581051", MBS_TITLE))[1]


class HnxQueueReviewTests(unittest.TestCase):
    def test_both_dates_component_and_terms_must_match(self):
        obs, row = rights(), mbs()
        self.assertEqual("EXACT_DATES_COMPONENT_TERMS_CANDIDATE", compare(obs, row)["status"])
        changes = [{"record_date": None}, {"ex_right_date": None}, {"record_date": "2025-09-25T17:00:00Z"},
            {"ratio": .03}, {"event_title": "Cổ phiếu thưởng", "ratio": .12}, {"symbol": "TNG"}]
        for change in changes:
            with self.subTest(change=change):
                self.assertEqual("NOT_MATCHING_PAYLOAD", compare(obs, dict(row, **change))["status"])

    def test_no_public_date_or_nearest_date_match_for_missing_dates(self):
        row = dict(mbs(), ex_right_date=None, record_date=None)
        result = compare(rights(), row)
        self.assertIn("EX_DATE_NOT_COMPARABLE", result["reasons"])
        self.assertIn("RECORD_DATE_NOT_COMPARABLE", result["reasons"])

    def test_tng_eight_percent_matches_stock_payload_not_ten_percent_rights(self):
        obs, = parse_popup_components(*sample("TNG", "523090", TNG_TITLE))
        row = {"symbol": "TNG", "event_type": "ISS", "event_title": "Trả Cổ tức bằng Cổ phiếu tỉ lệ 8%",
            "ratio": .08, "ex_right_date": "2024-07-11T17:00:00Z", "record_date": "2024-07-14T17:00:00Z"}
        old = dict(row, ex_right_date="2023-06-13T17:00:00Z", record_date="2023-06-14T17:00:00Z")
        target = dict(row, event_title="Quyền mua CP tỉ lệ 10%", ratio=.1)
        result, = review_observations([obs], [row, old, target], {key(target)})
        self.assertEqual([key(row)], result["candidate_payload_hashes"])
        self.assertEqual([], result["candidate_in_missing_queue"])

    def test_cash_compares_cash_amount_instead_of_sdk_ratio(self):
        obs = rights()
        obs["fields"]["event_type"]["normalized_value"] = "CASH_DIVIDEND"
        obs["fields"]["cash_dividend_per_share"] = {"normalized_value": 1200, "parse_status": "VALID"}
        row = dict(mbs(), event_type="DIV", value=1200, ratio=.12)
        self.assertEqual("EXACT_DATES_COMPONENT_TERMS_CANDIDATE", compare(obs, row)["status"])
        self.assertEqual("NOT_MATCHING_PAYLOAD", compare(obs, dict(row, value=400))["status"])

    def test_queue_preserves_original_columns_missing_tasks_and_manual_flags(self):
        row, obs = mbs(), rights(); original = queue(row); before = deepcopy(original)
        review = review_observations([obs], [row], {key(row)})
        changed, tasks = field_queue([original], [obs], review)
        self.assertEqual(before, original)
        self.assertEqual(original, {k: v for k, v in changed[0].items() if k != "scoped_hnx_review_v2"})
        self.assertEqual(PENDING, tasks[0]["status"])
        self.assertFalse(tasks[0]["field_approved"])
        self.assertFalse(tasks[0]["field_applied"])
        self.assertTrue(tasks[0]["canonical_missing_unchanged"])

    def test_two_payload_alternatives_remain_ambiguous_without_field_proposal(self):
        row, obs = mbs(), rights()
        other = dict(row, public_date="2025-09-21T17:00:00Z")
        review = review_observations([obs], [row, other], {key(row)})
        self.assertEqual("AMBIGUOUS_PAYLOAD_COUNTERPART", review[0]["status"])
        _, tasks = field_queue([queue(row)], [obs], review)
        self.assertEqual(MISSING, tasks[0]["status"])
        self.assertEqual([], tasks[0]["candidates"])

    def test_conflicting_prices_retained_without_average_or_source_priority(self):
        row, obs = mbs(), rights()
        other = deepcopy(obs); other["observation_id"] = "alternative"
        other["fields"]["rights_subscription_price"]["normalized_value"] = 20000
        review = review_observations([obs, other], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs, other], review)
        self.assertEqual("CONFLICTING_CANDIDATES_PENDING_REVIEW", tasks[0]["status"])
        self.assertEqual({10000, 20000}, {c["value"] for c in tasks[0]["candidates"]})

    def test_int_float_same_price_with_different_observation_metadata_is_one_value(self):
        row, obs = mbs(), rights()
        other = deepcopy(obs); other["observation_id"] = "alternative"
        other["fields"]["rights_subscription_price"]["normalized_value"] = 10000
        review = review_observations([obs, other], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs, other], review)
        self.assertEqual(PENDING, tasks[0]["status"])
        self.assertEqual(2, len(tasks[0]["candidates"]))

    def test_unsigned_price_choice_requires_exact_primary_unit_and_preserves_evidence(self):
        row, obs = mbs(), rights(); before = deepcopy(obs)
        review = review_observations([obs], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs], review)
        proposal = price_proposal(tasks[0], obs, {"fixture": True}, row)
        choice, = proposal["proposed_fields"]
        self.assertEqual("10000", choice["observed_value_proposed"])
        self.assertEqual("VND/share", choice["unit"])
        self.assertIsNone(choice["owner_decision"])
        self.assertFalse(choice["applied"])
        self.assertFalse(proposal["importable_as_production_decisions"])
        self.assertEqual("NOT_PROMOTED", proposal["pit_status"])
        self.assertEqual(before, obs)
        self.assertTrue(proposal["evidence"]["primary_price_quotes"])

    def test_price_quote_cannot_borrow_unit_from_another_component(self):
        row, obs = mbs(), rights()
        review = review_observations([obs], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs], review)
        obs["component_evidence"]["component_text"] = "Giá phát hành: 10.000 đồng"
        with self.assertRaisesRegex(ValueError, "PRIMARY_PRICE"):
            price_proposal(tasks[0], obs, {}, row)

    def test_payload_hash_tampering_and_wrong_type_are_rejected(self):
        row, obs = mbs(), rights(); original = queue(row)
        original["original_sdk_row"]["ratio"] = .99
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            field_queue([original], [], [])
        review = review_observations([obs], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs], review)
        with self.assertRaisesRegex(ValueError, "EXACT_PAYLOAD"):
            price_proposal(tasks[0], obs, {}, dict(row, symbol="TNG"))

    def test_conflicting_task_price_and_missing_evidence_do_not_generate_choice(self):
        row, obs = mbs(), rights()
        review = review_observations([obs], [row], {key(row)})
        _, tasks = field_queue([queue(row)], [obs], review)
        tasks[0]["candidates"][0]["value"] = 20000
        with self.assertRaisesRegex(ValueError, "TASK_PRICE"):
            price_proposal(tasks[0], obs, {}, row)


if __name__ == "__main__": unittest.main()
