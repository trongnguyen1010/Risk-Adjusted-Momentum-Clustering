import unittest

from delta_t1.ingestion.additional_market_source_discovery import (
    candidate_inventory,
    classify_basis,
    normalize_rows,
    shortlist,
    smoke_plan,
)


class AdditionalMarketSourceDiscoveryTests(unittest.TestCase):
    def test_inventory_precedes_bounded_three_source_shortlist(self):
        self.assertGreaterEqual(len(candidate_inventory()), 8)
        self.assertEqual(len(shortlist()), 3)
        self.assertEqual({r["provider"] for r in shortlist()},
                         {"FiinGroup API Datafeed", "VCI", "DNSE Entrade"})

    def test_smoke_plan_is_bounded_and_excludes_existing_failed_paths(self):
        plan = smoke_plan()
        self.assertEqual(len(plan), 30)
        self.assertEqual({r["provider"] for r in plan}, {"dnse", "vci"})
        self.assertEqual({r["ticker"] for r in plan if r["case"] == "depth-2020"},
                         {"FPT", "BAB", "ACV", "PVS", "HND", "KHP"})

    def test_dnse_normalization_uses_explicit_client_unit_contract(self):
        payload = {"t": [1752717600], "o": [97.78], "h": [99.63], "l": [97.25],
                   "c": [98.01], "v": [8334200], "nextTime": 0}
        rows = normalize_rows("dnse", payload)
        self.assertEqual(rows[0]["trade_date"], "2025-07-17")
        self.assertEqual(rows[0]["close_vnd"], 98010.0)
        self.assertEqual(rows[0]["volume"], 8334200)

    def test_vci_normalization_preserves_provider_values(self):
        payload = [{"t": ["1752710400"], "o": [97783.24], "h": [99635.49],
                    "l": [97243.0], "c": [98014.77], "v": [8355437]}]
        rows = normalize_rows("vci", payload)
        self.assertEqual(rows[0]["trade_date"], "2025-07-17")
        self.assertEqual(rows[0]["close_vnd"], 98014.77)

    def test_basis_gate_never_promotes_undocumented_near_match(self):
        near = [{"relative_difference": 0.0001}]
        mismatch = [{"relative_difference": -0.09}]
        self.assertEqual(classify_basis(near), "BASIS_EMPIRICALLY_COMPATIBLE_BUT_UNDOCUMENTED")
        self.assertEqual(classify_basis(mismatch), "BASIS_INCOMPATIBLE")
        self.assertEqual(classify_basis([]), "BASIS_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
