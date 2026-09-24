import importlib.util, json, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/"src"))
SPEC=importlib.util.spec_from_file_location("c4",ROOT/"scripts/evaluate_cafef_tradehistory_500.py")
C4=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(C4)
from delta_t1.ingestion.sources.cafef import cafef_trade_date, classify_cafef_page_row, map_trade_history_row

class TradeHistory500EvaluationTests(unittest.TestCase):
    def sample(self,**changes):
        row={"Symbol":"ACB","TradeDate":"/Date(1769626800000)/","BasicPrice":20.0,"ClosePrice":21.0,"Volume":0,"AdjustPrice":10.5,"Ceiling":22.0,"Floor":18.0,"TotalValue":0,"AgreedVolume":0,"AgreedValue":0}; row.update(changes); return row

    def test_reviewed_universe_is_exactly_500_unique(self):
        rows,_=C4.validate_universe(); self.assertEqual(500,len(rows)); self.assertEqual(500,len({x["ticker"] for x in rows})); self.assertEqual(500,len({x["security_id"] for x in rows}))
    def test_endpoint_proof_and_date_snapshot_semantics(self):
        self.assertTrue(C4.endpoint_ok({"url":"https://cafef.vn/TradeHistoryNew.ashx?Symbol=ACB"})); self.assertFalse(C4.endpoint_ok({"url":"PriceHistory.ashx"}))
        self.assertEqual("2026-01-29",cafef_trade_date(self.sample()["TradeDate"])); self.assertEqual("CURRENT_SNAPSHOT",classify_cafef_page_row("1/1/0001 12:00:00 AM",1,0))
    def test_exact_duplicate_and_adjusted_revision_classification(self):
        one=self.sample(); two=dict(one); self.assertEqual(C4.value_signature(one),C4.value_signature(two)); two["AdjustPrice"]=10.4
        kind,fields=C4.conflict_kind([C4.value_signature(one),C4.value_signature(two)]); self.assertEqual("ADJUSTED_PRICE_REVISION_CANDIDATE",kind); self.assertEqual("adj_close",fields)
    def test_mapping_ohl_null_and_vendor_adjusted(self):
        mapped=map_trade_history_row(self.sample(),"ACB","HOSE"); mapped.update(security_id="KBS:HOSE:ACB",ticker="ACB",exchange="HOSE",fetched_at="x")
        clean=C4.canonical_row(mapped,[{"run_id":"r"}]); self.assertEqual(21000,clean["raw_close"]); self.assertEqual(10500,clean["adj_close"]); self.assertEqual("vendor_adjusted",clean["adjustment_basis"]); self.assertIsNone(clean["raw_open"]); self.assertIsNone(clean["raw_high"]); self.assertIsNone(clean["raw_low"])
    def test_activity_totals_require_both_components(self):
        self.assertEqual(3,C4.total(1,2)); self.assertIsNone(C4.total(None,2)); self.assertIsNone(C4.total(1,None)); self.assertIsNone(C4.total(-1,2))
    def test_zero_volume_remains_valid_observation(self):
        mapped=map_trade_history_row(self.sample(),"ACB","HOSE"); self.assertEqual("VALID",C4.row_quality(mapped)); mapped.update(security_id="x",ticker="ACB",exchange="HOSE",fetched_at="x")
        self.assertEqual(0,C4.canonical_row(mapped,[{"run_id":"r"}])["volume"]); self.assertEqual("unknown",C4.canonical_row(mapped,[{"run_id":"r"}])["trading_status"])
    def test_identity_routing_is_date_aware_and_fail_closed(self):
        routing={"X":[{"exchange":"HNX","effective_from":"2020-01-01","effective_to":"2021-01-01"},{"exchange":"HOSE","effective_from":"2021-01-02","effective_to":None}]}
        self.assertEqual("HNX",C4.route(routing,"X","2020-06-01")); self.assertEqual("HOSE",C4.route(routing,"X","2022-01-01")); self.assertIsNone(C4.route(routing,"X","2019-01-01"))
    def test_script_has_no_network_client_and_c3_paths_are_inputs_only(self):
        source=(ROOT/"scripts/evaluate_cafef_tradehistory_500.py").read_text(encoding="utf-8"); self.assertNotIn("requests.",source); self.assertNotIn("urllib",source); self.assertNotIn("tradehistory_local_reuse_v1",source)

if __name__=="__main__": unittest.main()
