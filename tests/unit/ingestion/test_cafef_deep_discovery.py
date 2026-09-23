import unittest

from delta_t1.ingestion.cafef_deep_discovery import (
    CONTRACT_VERSION, _assurance, _edge_period, _filename_token, _financial_periods, _scope,
    document_plan, financial_initial_plan, market_plan, sample_securities,
)


class CafeFDeepDiscoveryTests(unittest.TestCase):
    def test_plan_is_bounded_representative_and_sequential_ready(self):
        self.assertEqual(7, len(sample_securities()))
        self.assertEqual({"HOSE", "HNX", "UPCOM"}, {x["exchange"] for x in sample_securities()})
        self.assertEqual(14, len(market_plan()))
        self.assertEqual(15, len(financial_initial_plan()))
        self.assertEqual(6, len(document_plan()))
        self.assertTrue(all(x["page_size"] in {20, 30} for x in market_plan()))

    def test_document_metadata_is_not_promoted_to_pit(self):
        self.assertEqual("CONSOLIDATED", _scope("Báo cáo tài chính hợp nhất quý 2"))
        self.assertEqual("SEPARATE_OR_PARENT", _scope("Báo cáo tài chính công ty mẹ quý 2"))
        self.assertEqual("REVIEWED", _assurance("Báo cáo quý 2 (đã soát xét)"))
        self.assertEqual("AUDITED", _assurance("Báo cáo năm (đã kiểm toán)"))
        self.assertEqual("28072026095429", _filename_token("https://x/FPT_28072026095429.pdf?v=1"))

    def test_financial_period_parser_keeps_provider_metadata(self):
        payload = {"value": {"data": [{"code": "KQKD", "data": [
            {"time": "Q2-2026", "year": 2026, "quater": 2, "type": "H"}
        ]}]}}
        self.assertEqual([{"statement": "KQKD", "time": "Q2-2026", "year": 2026,
                           "quarter": 2, "type": "H"}], _financial_periods(payload))
        self.assertTrue(CONTRACT_VERSION.startswith("cafef-a5-r1-1"))

    def test_period_edges_use_year_and_quarter_not_lexical_label(self):
        periods = [{"time": "Q4-2025", "year": 2025, "quarter": 4},
                   {"time": "Q2-2026", "year": 2026, "quarter": 2}]
        self.assertEqual("Q2-2026", _edge_period(periods, newest=True))
        self.assertEqual("Q4-2025", _edge_period(periods, newest=False))


if __name__ == "__main__":
    unittest.main()
