import copy
import json
import tempfile
import unittest
from delta_t1.ingestion.financial_price_reference import collect
from delta_t1.ingestion.sources.base import AccessControlError
from delta_t1.ingestion.financial_documents import verify_inventory


class FinancialPriceReferenceTests(unittest.TestCase):
    def config(self):
        return dict(symbols={'VNM':'HOSE','PVS':'HNX'}, target_date='2026-08-28', max_pages_per_symbol=2,
                    financial_features_allowed=False, canonical_market_write_allowed=False)

    def test_bounded_quote_unit_date_and_raw_provenance(self):
        class Adapter:
            def acquire_trade_history_page(self, request):
                raw = dict(Symbol=request['symbol'], TradeDate='2026-08-28T17:00:00+07:00', BasicPrice=60,
                           ClosePrice=62.3, Ceiling=66, Floor=54, AdjustPrice=60.1, Volume=100,
                           TotalValue=6230000, AgreedVolume=0, AgreedValue=0)
                payload = dict(Success=True, Data=[raw])
                return dict(body=json.dumps(payload).encode(), payload=payload, url='https://cafef.vn/public')
        with tempfile.TemporaryDirectory() as out:
            records, quotes = collect(self.config(), out+'/new', Adapter())
            self.assertEqual(len(records), 2)
            self.assertEqual([q['raw_close'] for q in quotes], [62300, 62300])
            self.assertTrue(all(q['trade_date']=='2026-08-28' and not q['canonical_market_accepted'] for q in quotes))
            verify_inventory(out+'/new')

    def test_access_boundary_stops_other_symbol(self):
        class Adapter:
            calls = 0
            def acquire_trade_history_page(self, request):
                self.calls += 1; raise AccessControlError('HTTP 403; path stopped')
        a = Adapter()
        with tempfile.TemporaryDirectory() as out:
            records, quotes = collect(self.config(), out+'/new', a)
            self.assertEqual(a.calls, 1)
            self.assertEqual([r['status'] for r in records], ['HARD_STOP', 'NOT_REQUESTED_HARD_STOP'])
            self.assertEqual(quotes, [])

    def test_no_universe_or_market_mutation(self):
        for key, value in [('financial_features_allowed', True), ('canonical_market_write_allowed', True),
                           ('max_pages_per_symbol', 100), ('symbols', {'FPT':'HOSE'})]:
            c = copy.deepcopy(self.config()); c[key] = value
            with tempfile.TemporaryDirectory() as out:
                with self.assertRaises(ValueError): collect(c, out+'/new')
