"""Contract fixtures only; test securities are never shipped to the demo."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/backend'))
from app.repository import TerminalRepository, MissingData
from app.fundamentals import FundamentalsRepository, price_summary
try:
    from app.main import create_app
    from fastapi.testclient import TestClient
except ImportError as error:
    raise unittest.SkipTest('Optional terminal API dependencies unavailable: '+str(error))
from delta_t1.product.terminal_export import schema,encoded,numeric,quantiles

def build_bundle(bundle,extra_prices=(),illiquid=()):
    db=sqlite3.connect(bundle/'terminal.sqlite');schema(db)
    config={k:dict(k=2,features=['mom_21'],scaling='test',frequency='test',version='fixture') for k in ['market','financial','combined']}
    db.execute('INSERT INTO metadata VALUES (?,?)',('overview',encoded(dict(version='delta-intelligence-v1',model_configs=config,definitions={'mom_21':{'label':'Momentum','unit':'percent','formula':'fixture','family':'market'}}))))
    db.executemany('INSERT INTO securities VALUES (?,?,?,?,?)',[('TESTA','Test A','HOSE','s1',0),('TESTB','Test B','HNX','s2',0),('AMB','Ambiguous','HOSE','s3',1)])
    for kind,date,rows in [('market','2024-12-31',[('TESTA',0),('TESTB',1)]),('market','2025-12-31',[('TESTA',1)]),('financial','2025',[('TESTA',0),('TESTB',1)]),('combined','2025-12-31',[('TESTA',0)])]:
        db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?,?)',(kind,date,len(rows),2,'{}','{}','REFERENCE'))
        for ticker,c in rows:db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?)',(kind,date,ticker,'s1' if ticker=='TESTA' else 's2',c,encoded({'mom_21':.12}), 'REFERENCE'))
    db.execute('INSERT INTO prices VALUES (?,?,?,?,?,?,?,?,?)',('TESTA','s1','2025-01-02',None,123,100,'RAW','2025-01-02',0))
    db.execute('INSERT INTO relations VALUES (?,?,?,?,?,?)',('2025-12-31','TESTA',1,0,0,'BOTH'))
    db.executemany('INSERT INTO prices VALUES (?,?,?,?,?,?,?,?,?)',extra_prices)
    if illiquid:  # Bundle v3 schema: per-observation liquidity flag.
        db.execute('ALTER TABLE observations ADD COLUMN liquidity TEXT')
        db.execute("UPDATE observations SET liquidity='LIQUID' WHERE kind='market'")
        db.executemany("UPDATE observations SET liquidity='ILLIQUID' WHERE kind='market' AND ticker=?",[(x,) for x in illiquid])
    db.commit();db.close()
    with (bundle/'terminal.sqlite').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    (bundle/'manifest.json').write_text(encoded(dict(version='delta-intelligence-v1',database_sha256=digest,sources={})),encoding='utf8')
    return TerminalRepository(bundle)

class TerminalContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.bundle=Path(self.temp.name)
        self.repo=build_bundle(self.bundle)
        self.context=TestClient(create_app(self.repo));self.client=self.context.__enter__()
    def tearDown(self):self.context.__exit__(None,None,None);self.temp.cleanup()
    def test_read_only_database(self):
        with self.repo.connect() as db:
            with self.assertRaises(sqlite3.OperationalError):db.execute('DELETE FROM securities')
    def test_database_tampering_rejected(self):
        with (self.bundle/'terminal.sqlite').open('ab') as f:f.write(b'tamper')
        with self.assertRaises(MissingData):TerminalRepository(self.bundle)
    def test_exact_snapshot_missing_does_not_forward_fill(self):
        self.assertEqual(self.client.get('/api/v2/snapshots/market?date=2025-06-30').status_code,404)
        body=self.client.get('/api/v2/stocks/TESTB?kind=market&date=2025-12-31').json()
        self.assertIsNone(body['current']);self.assertTrue(body['current_missing_reason'])
    def test_compare_uses_one_date_with_explicit_missing(self):
        body=self.client.get('/api/v2/compare?tickers=TESTA,TESTB&date=2025-12-31').json()
        self.assertIsNone(body['items'][1]['observation'])
        self.assertEqual(self.client.get('/api/v2/compare?tickers=A,B,C,D,E').status_code,400)
    def test_invalid_queries_and_ambiguous_identity_fail_closed(self):
        for path,status in [('/snapshots/unknown',422),('/stocks/AMB',409),('/stocks/MISSING',404),('/members/market?sort=DROP%20TABLE',400),('/members/market?page=0',422),('/members/market?page_size=1000',422),('/prices/TESTA?basis=mixed',400),('/prices/TESTA?end=2025-02-30',400),('/prices/TESTA?end=20250101',400),('/prices/TESTA?end=2025-W01-1',400),('/matrix/invalid',400)]:
            with self.subTest(path=path):self.assertEqual(self.client.get('/api/v2'+path).status_code,status)
    def test_filters_sort_and_pagination(self):
        body=self.client.get('/api/v2/members/market?date=2024-12-31&exchange=HOSE&page_size=1').json()
        self.assertEqual(body['total'],1);self.assertEqual(body['items'][0]['ticker'],'TESTA')
        self.assertEqual(self.client.get('/api/v2/members/market?q=%27%20OR%201=1--').json()['total'],0)
    def test_prices_keep_missing_basis_and_observed_end(self):
        self.assertIsNone(self.client.get('/api/v2/prices/TESTA').json()['points'][0]['close'])
        self.assertEqual(self.client.get('/api/v2/prices/TESTA?basis=raw_close').json()['points'][0]['close'],123)
        self.assertFalse(self.client.get('/api/v2/prices/TESTA?end=2024-12-31').json()['available'])
    def test_migration_aligns_labels_without_mutation(self):
        body=self.client.get('/api/v2/migration/market?source=2024-12-31&target=2025-12-31').json()
        self.assertEqual((body['common'],body['stayed'],body['exited']),(1,1,1))
        self.assertEqual(body['mapping']['1'],0)
        self.assertEqual(self.repo.snapshot('market','2025-12-31')['points'][0]['cluster'],1)
    def test_matrix_common_cohort_and_expost_scope(self):
        body=self.client.get('/api/v2/matrix/2025').json();self.assertEqual(body['total'],1);self.assertIn('NOT_PIT',body['scope'])
        self.assertFalse(self.client.get('/api/v2/matrix/2016').json()['available'])
        members=self.client.get('/api/v2/members/financial?date=2025&matrix_market=1&matrix_financial=0').json()
        self.assertEqual(members['total'],1)
    def test_numeric_null_and_quartile_presentation(self):
        self.assertIsNone(numeric('nan'));self.assertIsNone(numeric(True));self.assertEqual(quantiles([1,2,3]),[1,1.5,2,2.5,3])

    def test_profiles_payload_explicitly_omits_points_without_mutating_cached_snapshot(self):
        small=self.client.get('/api/v2/snapshots/market?date=2024-12-31&include_points=false').json()
        self.assertFalse(small['points_included']);self.assertEqual(small['points'],[])
        complete=self.client.get('/api/v2/snapshots/market?date=2024-12-31').json()
        self.assertTrue(complete['points_included']);self.assertEqual(len(complete['points']),2)

    def test_revision_and_model_version_mismatch_fail_closed(self):
        revision=self.client.get('/api/v2/catalog').json()['metadata']['bundle_revision']
        self.assertEqual(self.client.get('/api/v2/snapshots/market',params={'revision':revision,'version':'fixture'}).status_code,200)
        self.assertEqual(self.client.get('/api/v2/snapshots/market?revision=other').status_code,409)
        self.assertEqual(self.client.get('/api/v2/snapshots/market?version=other').status_code,409)
        self.assertEqual(self.client.get('/api/v2/indicators/TESTA?revision=other').status_code,409)

def build_indicators(path):
    db=sqlite3.connect(path)
    db.executescript("""
        create table company(ticker text primary key, name text, exchange text, template_family text, sector_group text);
        create table indicator_values(ticker text, fiscal_year integer, metric text, value real, status text,
                                      inputs_json text, primary key(ticker, fiscal_year, metric));
        create table latest(ticker text primary key, latest_fiscal_year integer, last_price real, last_price_date text,
                            shares real, market_cap_last real, metrics_json text);
        create table metadata(key text primary key, value text);""")
    db.executemany('insert into company values (?,?,?,?,?)',[('TESTA','Test A','HOSE','Regular','NON_FINANCIAL'),
        ('TESTB','Test B','HNX','Bank','BANK'),('TESTC','Test C','HOSE','Regular','NON_FINANCIAL')])
    signals=dict(roa_positive=True,cfo_positive=True,roa_improving=True,accruals=True,leverage_falling=True,
                 liquidity_improving=True,no_dilution=True,gross_margin_improving=False,turnover_improving=None)
    rows=[('TESTA',2025,'eps',2000.0,'OK',{}),('TESTA',2025,'pe',15.0,'OK',{}),('TESTA',2025,'pb',2.0,'OK',{}),
          ('TESTA',2025,'roe',.2,'OK',{}),('TESTA',2024,'roe',.18,'OK',{}),('TESTA',2023,'roe',.16,'OK',{}),
          ('TESTA',2025,'revenue_growth',-.1,'OK',{}),
          ('TESTA',2025,'f_score',None,'MISSING_INPUT',dict(signals=signals,known_signals=8,missing=['turnover_improving'])),
          ('TESTA',2025,'m_score',-2.5,'OK',dict(variables=dict(DSRI=1.0,GMI=1.1))),
          ('TESTA',2025,'z_score',1.5,'OK',dict(variables=dict(X1=.1,X4=.5),variant='ALTMAN_1968')),
          ('TESTA',2025,'z_score_dp',2.0,'OK',{}),
          ('TESTA',2016,'eps',None,'MISSING_INPUT',dict(missing=['NO_ANNUAL_REPORT'])),
          ('TESTA',2024,'pe',None,'NEGATIVE_EARNINGS',{}),
          ('TESTB',2025,'eps',3000.0,'OK',{}),('TESTB',2025,'roa',.015,'OK',{}),('TESTB',2025,'bvps',20000.0,'OK',{}),
          ('TESTB',2025,'f_score',None,'NOT_APPLICABLE',dict(sector='BANK')),('TESTB',2025,'m_score',None,'NOT_APPLICABLE',{}),
          ('TESTB',2025,'z_score',None,'NOT_APPLICABLE',{}),('TESTB',2025,'z_score_dp',None,'NOT_APPLICABLE',{}),
          ('TESTC',2025,'roe',.3,'OK',{})]
    db.executemany('insert into indicator_values values (?,?,?,?,?,?)',[(t,y,m,v,s,json.dumps(i)) for t,y,m,v,s,i in rows])
    db.executemany('insert into latest values (?,?,?,?,?,?,?)',[
        ('TESTA',2025,30000.0,'2025-12-31',1e9,3e13,json.dumps(dict(pe=dict(value=15.0,status='OK'),roe=dict(value=.2,status='OK')))),
        ('TESTB',2025,40000.0,'2025-12-31',2e9,8e13,json.dumps(dict(pe=dict(value=None,status='NO_PRICE')))),
        ('TESTC',2025,10000.0,'2025-12-31',1e9,1e13,json.dumps({}))])
    db.execute("insert into metadata values ('run_id','fixture')")
    db.commit();db.close()
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

class FundamentalsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();folder=Path(self.temp.name)
        prices=[('TESTB','s2',d,adj,raw,1,'vendor_adjusted',d,0) for d,raw,adj in
                [('2024-12-31',50000,25000),('2025-11-28',41000,41000),('2025-12-30',39000,39000),('2025-12-31',40000,40000)]]
        repo=build_bundle(folder,prices,illiquid=('TESTB',))
        digest=build_indicators(folder/'indicators.sqlite')
        self.source=FundamentalsRepository(folder/'indicators.sqlite',digest)
        self.context=TestClient(create_app(repo,self.source));self.client=self.context.__enter__()
    def tearDown(self):self.context.__exit__(None,None,None);self.temp.cleanup()
    def get(self,path,status=200):
        response=self.client.get('/api/v2/stocks/'+path);self.assertEqual(response.status_code,status,response.text);return response.json()
    def test_overview_cards_and_ratings(self):
        body=self.get('TESTA/overview')
        self.assertEqual([c['metric'] for c in body['cards']],['eps','pe','pb','roe','f_score','z_score'])
        cards={c['metric']:c for c in body['cards']}
        self.assertEqual(cards['z_score']['rating'],'Nguy hiểm')
        self.assertIsNone(cards['f_score']['value']);self.assertEqual(cards['f_score']['status'],'MISSING_INPUT')
        self.assertIn('= Giá / EPS',cards['pe']['description'])
        self.assertEqual(body['market_cap'],3e13)
        self.assertEqual(body['price']['close'],123);self.assertIsNone(body['price']['change_1d'])  # no adjusted close: no change shown
        self.assertTrue(any('ROE 3 năm' in line for line in body['summary']))
        self.assertTrue(any('giảm 10%' in line for line in body['summary']))
    def test_groups_without_story_columns_have_no_names(self):
        groups=self.get('TESTA/overview')['groups']
        self.assertEqual({g['kind'] for g in groups},{'market','financial','combined'})
        self.assertTrue(all(g['name'] is None for g in groups))  # pre-v4 bundle: no name column, no error
        market=[g for g in groups if g['kind']=='market'][0]
        self.assertEqual((market['date'],market['cluster']),('2025-12-31',1))
        self.assertEqual(self.get('TESTC/overview')['groups'],[])
    def test_liquidity_flag_from_latest_market_observation(self):
        self.assertEqual(self.get('TESTB/overview')['liquidity'],dict(status='ILLIQUID',date='2024-12-31'))
        self.assertEqual(self.get('TESTA/overview')['liquidity']['status'],'LIQUID')
        self.assertIsNone(self.get('TESTC/overview')['liquidity'])  # not in the market model
        members=self.client.get('/api/v2/members/market?date=2024-12-31').json()['items']
        self.assertEqual({m['ticker']:m['liquidity'] for m in members}['TESTB'],'ILLIQUID')
    def test_bank_overview_swaps_scores_for_roa_and_bvps(self):
        body=self.get('TESTB/overview')
        self.assertEqual([c['metric'] for c in body['cards']],['eps','pe','pb','roe','roa','bvps'])
        self.assertEqual(body['sector_label'],'Ngân hàng')
        price=body['price']
        self.assertEqual(price['close'],40000)
        self.assertAlmostEqual(price['change_ytd'],40000/25000-1)  # adjusted basis, not raw 50000
        self.assertAlmostEqual(price['change_1d'],40000/39000-1)
        self.assertAlmostEqual(price['change_1m'],40000/41000-1)
    def test_fundamentals_table_keeps_statuses(self):
        body=self.get('TESTA/fundamentals?from=2016&to=2025')
        self.assertEqual(body['years'][0],2016);self.assertEqual(len(body['years']),10)
        self.assertEqual(body['metrics']['eps']['2016'],dict(value=None,status='MISSING_INPUT',reason='NO_ANNUAL_REPORT'))
        self.assertEqual(body['metrics']['pe']['2024']['status'],'NEGATIVE_EARNINGS')
        self.assertEqual(body['metrics']['gross_margin']['2025']['status'],'MISSING_INPUT')  # absent cell is never zero
        self.assertEqual([g['name'] for g in body['groups']][0],'Định giá')
        for path in ('TESTA/fundamentals?from=2015','TESTA/fundamentals?from=2025&to=2020'):
            with self.subTest(path=path):self.get(path,400)
        self.get('NOPE/fundamentals',404)
    def test_scores_detail(self):
        body=self.get('TESTA/scores/2025')
        self.assertEqual(body['f_score']['known_signals'],8);self.assertEqual(len(body['f_score']['signals']),9)
        self.assertIsNone({s['name']:s['passed'] for s in body['f_score']['signals']}['turnover_improving'])
        self.assertEqual(body['m_score']['rating'],'Bình thường')
        self.assertEqual(len(body['m_score']['variables']),8);self.assertEqual(len(body['z_score']['components']),5)
        bank=self.get('TESTB/scores/2025');self.assertFalse(bank['applicable']);self.assertEqual(bank['f_score']['status'],'NOT_APPLICABLE')
        self.get('TESTA/scores/2030',400);self.get('TESTA/scores/2019',404)
    def test_peers_use_cluster_then_sector(self):
        body=self.get('TESTA/peers')
        self.assertTrue(body['basis'].startswith('CLUSTER_COMBINED'));self.assertEqual(body['items'][0]['ticker'],'TESTA')
        self.assertEqual(body['items'][0]['pe'],15.0)
        body=self.get('TESTC/peers')  # not in any model cluster
        self.assertEqual(body['basis'],'SECTOR');self.assertEqual([r['ticker'] for r in body['items']],['TESTC','TESTA'])
    def test_tampered_file_and_missing_build_fail_closed(self):
        with self.assertRaises(MissingData):FundamentalsRepository(Path(self.temp.name)/'indicators.sqlite','0'*64)
        with self.assertRaises(MissingData):FundamentalsRepository(Path(self.temp.name)/'absent.sqlite')
        db=self.source.connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):db.execute('DELETE FROM company')
        finally:db.close()
    def test_coverage_counts_only_ok_cells(self):
        body=self.client.get('/api/v2/fundamentals-coverage').json()
        self.assertEqual(body['total_tickers'],3)
        rows={m['metric']:m['counts'] for m in body['metrics']}
        self.assertEqual(rows['roe']['2025'],2);self.assertNotIn('2024',rows['pe'])  # NEGATIVE_EARNINGS is not a value
    def test_price_summary_handles_empty(self):
        self.assertIsNone(price_summary([]))

if __name__=='__main__':unittest.main()
