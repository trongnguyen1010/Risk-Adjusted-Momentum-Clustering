import unittest
from delta_t1.experiments.assessment.inputs import AssessmentInputRecord, FINANCIAL_FEATURES, MARKET_FEATURES
from delta_t1.experiments.assessment.peers import PeerBenchmarkBuilder

def make_dummy_record(ticker, cluster_a, cluster_b, roe_val=0.2, mom_val=0.1):
    return AssessmentInputRecord(
        ticker=ticker,
        as_of="2026-01-02",
        sector_group="NON_FINANCIAL",
        is_eligible=True,
        eligibility_reason="ELIGIBLE",
        latest_fy=2024,
        usable_from_date="2025-04-15",
        cluster_a=cluster_a,
        cluster_b=cluster_b,
        financial_features={m: (roe_val if m == "roe" else 0.1) for m in FINANCIAL_FEATURES},
        financial_statuses={m: "OK" for m in FINANCIAL_FEATURES},
        market_features={m: (mom_val if m == "mom_21" else 0.05) for m in MARKET_FEATURES},
        market_statuses={m: "OK" for m in MARKET_FEATURES},
    )

class TestAssessmentPeers(unittest.TestCase):
    def test_peers_preference_same_both(self):
        # Target T0: A=0, B=1
        # Peers P1, P2, P3: A=0, B=1 (3 peers -> đủ chuẩn SAME_A_AND_B)
        records = {
            "T0": make_dummy_record("T0", 0, 1, roe_val=0.25),
            "P1": make_dummy_record("P1", 0, 1, roe_val=0.10),
            "P2": make_dummy_record("P2", 0, 1, roe_val=0.20),
            "P3": make_dummy_record("P3", 0, 1, roe_val=0.30),
        }
        builder = PeerBenchmarkBuilder(records)
        stats = builder.build_peer_stats_for_ticker("T0")

        self.assertIn("roe", stats)
        roe_stats = stats["roe"]
        self.assertEqual(roe_stats.peer_basis, "SAME_A_AND_B")
        self.assertEqual(roe_stats.peer_count, 3)
        self.assertNotIn("T0", roe_stats.peer_tickers)  # Self excluded
        self.assertEqual(roe_stats.median, 0.20)

    def test_peers_fallback_to_same_b(self):
        # Target T0: A=0, B=1
        # Chỉ có P1 cùng A=0, B=1 (thiếu mẫu < 3)
        # Nhưng có P2, P3, P4 cùng B=1 (A khác) -> Mở rộng financial sang SAME_B_ONLY
        records = {
            "T0": make_dummy_record("T0", 0, 1, roe_val=0.25),
            "P1": make_dummy_record("P1", 0, 1, roe_val=0.15),
            "P2": make_dummy_record("P2", 1, 1, roe_val=0.18),
            "P3": make_dummy_record("P3", 2, 1, roe_val=0.22),
            "P4": make_dummy_record("P4", 2, 1, roe_val=0.24),
        }
        builder = PeerBenchmarkBuilder(records)
        stats = builder.build_peer_stats_for_ticker("T0")

        roe_stats = stats["roe"]
        self.assertEqual(roe_stats.peer_basis, "SAME_B_ONLY")
        self.assertEqual(roe_stats.peer_count, 4)
        self.assertIsNotNone(roe_stats.median)

    def test_peers_under_3_no_median(self):
        # Target T0: A=0, B=1
        # Chỉ có 1 peer P1
        records = {
            "T0": make_dummy_record("T0", 0, 1, roe_val=0.25),
            "P1": make_dummy_record("P1", 0, 1, roe_val=0.15),
        }
        builder = PeerBenchmarkBuilder(records)
        stats = builder.build_peer_stats_for_ticker("T0")

        roe_stats = stats["roe"]
        self.assertEqual(roe_stats.peer_basis, "NONE")
        self.assertIsNone(roe_stats.median)

if __name__ == "__main__":
    unittest.main()
