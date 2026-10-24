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
try:
    from app.main import create_app
    from fastapi.testclient import TestClient
except ImportError as error:
    raise unittest.SkipTest('Optional terminal API dependencies unavailable: '+str(error))
from delta_t1.product.terminal_export import schema,encoded,numeric,quantiles

class TerminalContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.bundle=Path(self.temp.name)
        db=sqlite3.connect(self.bundle/'terminal.sqlite');schema(db)
        config={k:dict(k=2,features=['mom_21'],scaling='test',frequency='test',version='fixture') for k in ['market','financial','combined']}
        db.execute('INSERT INTO metadata VALUES (?,?)',('overview',encoded(dict(version='delta-intelligence-v1',model_configs=config,definitions={'mom_21':{'label':'Momentum','unit':'percent','formula':'fixture','family':'market'}}))))
        db.executemany('INSERT INTO securities VALUES (?,?,?,?,?)',[('TESTA','Test A','HOSE','s1',0),('TESTB','Test B','HNX','s2',0),('AMB','Ambiguous','HOSE','s3',1)])
        for kind,date,rows in [('market','2024-12-31',[('TESTA',0),('TESTB',1)]),('market','2025-12-31',[('TESTA',1)]),('financial','2025',[('TESTA',0),('TESTB',1)]),('combined','2025-12-31',[('TESTA',0)])]:
            db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?,?)',(kind,date,len(rows),2,'{}','{}','REFERENCE'))
            for ticker,c in rows:db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?)',(kind,date,ticker,'s1' if ticker=='TESTA' else 's2',c,encoded({'mom_21':.12}), 'REFERENCE'))
        db.execute('INSERT INTO prices VALUES (?,?,?,?,?,?,?,?,?)',('TESTA','s1','2025-01-02',None,123,100,'RAW','2025-01-02',0))
        db.execute('INSERT INTO relations VALUES (?,?,?,?,?,?)',('2025-12-31','TESTA',1,0,0,'BOTH'))
        db.commit();db.close()
        with (self.bundle/'terminal.sqlite').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        (self.bundle/'manifest.json').write_text(encoded(dict(version='delta-intelligence-v1',database_sha256=digest,sources={})),encoding='utf8')
        self.repo=TerminalRepository(self.bundle)
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
        for path,status in [('/snapshots/unknown',422),('/stocks/AMB',409),('/stocks/MISSING',404),('/members/market?sort=DROP%20TABLE',400),('/members/market?page=0',422),('/members/market?page_size=1000',422),('/prices/TESTA?basis=mixed',400)]:
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

if __name__=='__main__':unittest.main()
