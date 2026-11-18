import unittest
import copy

from delta_t1.experiments.investment_assessment_v1 import (
    SingleAssessmentPayload,
    compute_payload_content_hash,
    VERDICT_WORTH_CONSIDERING,
    VERDICT_MONITOR,
)

def make_payload(ticker, verdict):
    return SingleAssessmentPayload(
        ticker=ticker,
        as_of="2026-01-02",
        verdict=verdict,
        verdict_label_vi="label",
        rationale="rationale",
        cluster_a=0,
        cluster_b=1,
        latest_fy=2024,
        usable_from_date="2025-04-15",
        favorable_signals=["ROE tốt"],
        caution_signals=[],
        financial_features={"roe": 0.2},
        market_features={"mom_21": 0.05},
        peer_comparisons={},
    )

class TestAssessmentReproducibility(unittest.TestCase):
    def test_deterministic_content_hash(self):
        p1 = make_payload("FPT", VERDICT_WORTH_CONSIDERING)
        p2 = make_payload("HPG", VERDICT_MONITOR)

        # 1. Thứ tự khác nhau -> Cùng ra 1 hash duy nhất
        hash_order_1 = compute_payload_content_hash([p1, p2])
        hash_order_2 = compute_payload_content_hash([p2, p1])
        self.assertEqual(hash_order_1, hash_order_2)

        # 2. Thay đổi nội dung (ví dụ verdict) -> Hash đổi
        p2_mod = copy.deepcopy(p2)
        p2_mod.verdict = VERDICT_WORTH_CONSIDERING
        hash_mod = compute_payload_content_hash([p1, p2_mod])
        self.assertNotEqual(hash_order_1, hash_mod)

if __name__ == "__main__":
    unittest.main()
