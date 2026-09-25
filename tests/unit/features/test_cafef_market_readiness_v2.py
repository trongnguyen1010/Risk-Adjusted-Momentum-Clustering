import sys, unittest
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/"src"))
from delta_t1.features.market import build_features
from delta_t1.ingestion.cafef_market_semantics import classify_activity, enrich_observed_row, sum_observed_components

class CafeFMarketReadinessV2Tests(unittest.TestCase):
    def test_activity_contract(self):
        self.assertEqual("ACTIVE",classify_activity(1,0)["trading_activity_status"])
        self.assertEqual("ACTIVE",classify_activity(0,2)["trading_activity_status"])
        zero=classify_activity(0,0); self.assertEqual("OBSERVED_ZERO_VOLUME",zero["trading_activity_status"]); self.assertEqual(0,zero["volume"]); self.assertFalse(zero["tradability_eligible"])
        unknown=classify_activity(None,0); self.assertEqual("UNKNOWN_ACTIVITY_COMPONENTS",unknown["trading_activity_status"]); self.assertIsNone(unknown["volume"]); self.assertIsNone(unknown["tradability_eligible"])
        self.assertEqual(0,sum_observed_components(0,0)); self.assertIsNone(sum_observed_components(None,0))

    def test_zero_value_is_preserved_and_no_suspension_is_inferred(self):
        row=enrich_observed_row({"matched_volume_shares":0,"negotiated_volume_shares":0,"matched_value_vnd":0,"negotiated_value_vnd":0})
        self.assertEqual(0,row["volume"]); self.assertEqual(0,row["traded_value"]); self.assertEqual("OBSERVED_VALID",row["market_observation_status"]); self.assertEqual("illiquid_or_nontraded",row["trading_status"])
        self.assertNotIn(row["trading_status"],{"suspended","halted","delisted"})
        unknown_value=enrich_observed_row({"matched_volume_shares":1,"negotiated_volume_shares":0,"matched_value_vnd":None,"negotiated_value_vnd":0})
        self.assertIsNone(unknown_value["traded_value"])

    def test_zero_volume_observation_is_ready_v2_but_not_legacy(self):
        sid="KBS:HOSE:ZERO"; start=date(2026,1,1); days=[(start+timedelta(days=i)).isoformat() for i in range(21)]
        securities=[{"security_id":sid,"ticker":"ZERO","exchange":"HOSE","valid_from":days[0],"valid_to":None,"listing_date":None,"delisting_date":None,"available_at":days[0]+"T17:00:00+07:00","identity_status":"provisional"}]
        calendar=[{"exchange":"HOSE","trade_date":d,"is_open":True,"is_month_end":i==20,"decision_at":d+"T17:00:00+07:00","available_at":d+"T17:00:00+07:00"} for i,d in enumerate(days)]
        prices=[]
        for i,d in enumerate(days):
            zero=i==20; prices.append({"security_id":sid,"trade_date":d,"adj_close":10000+i,"raw_close":10000+i,"adjustment_basis":"vendor_adjusted","traded_value":0 if zero else 100,"trading_status":"illiquid_or_nontraded" if zero else "normal","available_at":d+"T17:00:00+07:00"})
        base={"required_features":["liquidity_21"],"accepted_adjustments":["vendor_adjusted"],"benchmark_id":"VNINDEX","minimum_history_years":0}
        legacy=build_features({"securities":securities,"prices_daily":prices,"trading_calendar":calendar,"benchmark_daily":[]},base,"legacy")[-1]
        v2=build_features({"securities":securities,"prices_daily":prices,"trading_calendar":calendar,"benchmark_daily":[]},{**base,"readiness_policy":"MARKET_FEATURE_READINESS_V2"},"v2")[-1]
        self.assertTrue(v2["feature_complete"]); self.assertTrue(v2["market_feature_ready"]); self.assertFalse(legacy["market_feature_ready"]); self.assertEqual("1.6.0",v2["feature_version"]); self.assertEqual(0,v2["missing_count"])

if __name__=="__main__": unittest.main()
