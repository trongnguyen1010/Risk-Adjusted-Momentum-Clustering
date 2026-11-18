import unittest
from delta_t1.experiments.assessment.inputs import (
    AssessmentInputRecord,
    FINANCIAL_FEATURES,
    MARKET_FEATURES,
)
from delta_t1.experiments.assessment.peers import MetricPeerStats
from delta_t1.experiments.investment_assessment_v1 import (
    InvestmentAssessmentEngine,
    VERDICT_WORTH_CONSIDERING,
    VERDICT_MONITOR,
    VERDICT_LOW_PRIORITY,
    VERDICT_INSUFFICIENT_EVIDENCE,
)

def make_rec(ticker, cluster_a, cluster_b, is_eligible=True, roe=0.25, de=0.8):
    return AssessmentInputRecord(
        ticker=ticker,
        as_of="2026-01-02",
        sector_group="NON_FINANCIAL" if is_eligible else "BANK",
        is_eligible=is_eligible,
        eligibility_reason="ELIGIBLE" if is_eligible else "SECTOR_EXCLUDED",
        latest_fy=2024 if is_eligible else None,
        usable_from_date="2025-04-15" if is_eligible else None,
        cluster_a=cluster_a,
        cluster_b=cluster_b,
        financial_features={m: (roe if m == "roe" else (de if m == "debt_to_equity" else 0.1)) for m in FINANCIAL_FEATURES},
        financial_statuses={m: "OK" for m in FINANCIAL_FEATURES},
        market_features={m: 0.1 for m in MARKET_FEATURES},
        market_statuses={m: "OK" for m in MARKET_FEATURES},
    )

class TestAssessmentOfflineBuilder(unittest.TestCase):
    def setUp(self):
        self.engine = InvestmentAssessmentEngine()
        self.dummy_peers = {
            "roe": MetricPeerStats("roe", "SAME_A_AND_B", 5, 0.15, 0.10, 0.20, ["P1", "P2"]),
            "debt_to_equity": MetricPeerStats("debt_to_equity", "SAME_A_AND_B", 5, 1.2, 0.9, 1.5, ["P1", "P2"]),
        }

    def test_four_verdicts_coverage(self):
        # 1. INSUFFICIENT_EVIDENCE
        rec_ineligible = make_rec("VCB", 0, 0, is_eligible=False)
        res1 = self.engine.evaluate(rec_ineligible, {})
        self.assertEqual(res1.verdict, VERDICT_INSUFFICIENT_EVIDENCE)

        # 2. WORTH_CONSIDERING (A=0, B=0, ROE cao, nợ thấp)
        rec_strong = make_rec("FPT", 0, 0, is_eligible=True, roe=0.25, de=0.5)
        res2 = self.engine.evaluate(rec_strong, self.dummy_peers)
        self.assertEqual(res2.verdict, VERDICT_WORTH_CONSIDERING)

        # 3. LOW_PRIORITY (A=2, B=2 cả tài chính và thị trường yếu)
        rec_weak = make_rec("WEAK", 2, 2, is_eligible=True, roe=0.05, de=2.5)
        res3 = self.engine.evaluate(rec_weak, self.dummy_peers)
        self.assertEqual(res3.verdict, VERDICT_LOW_PRIORITY)

        # 4. MONITOR (Tín hiệu hỗn hợp: B=0 nhưng A=1)
        rec_mixed = make_rec("MIXED", 1, 0, is_eligible=True, roe=0.25, de=0.8)
        res4 = self.engine.evaluate(rec_mixed, self.dummy_peers)
        self.assertEqual(res4.verdict, VERDICT_MONITOR)

if __name__ == "__main__":
    unittest.main()
