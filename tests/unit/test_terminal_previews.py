from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
import unit.test_terminal_api as fixtures
from app.previews import PreviewRepository
from app.main import create_app
from app.repository import MissingData
from fastapi.testclient import TestClient


class PreviewContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.TerminalContractTests('test_read_only_database');self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.base=self.fixture.repo;root=self.fixture.bundle;variants={}
        for kind,dataset in self.base.catalog()['datasets'].items():
            snapshots={}
            for day in dataset['dates']:
                data=self.base.snapshot(kind,day);points=data['points'];labels=[7 if i==0 else 11 for i in range(len(points))];counts=Counter(labels)
                profiles=[dict(kind=kind,date=day,cluster=c,size=n,means={'mom_21':.12},medians={'mom_21':.12},quartiles={'mom_21':[.12]*5}) for c,n in counts.items()]
                snapshot=dict(data['snapshot'],k=len(counts),sizes={str(c):n for c,n in counts.items()},version='preview',scope='SYNTHETIC_NOT_PROMOTED')
                snapshots[day]=dict(snapshot=snapshot,profiles=profiles,symbols=[p['ticker'] for p in points],security_ids=[p['security_id'] for p in points],labels=labels,peer_examples=[])
            variants[kind]={'preview':dict(version='preview',label='Fixture preview',status='NOT_PROMOTED',features=['mom_21'],frequency='test',scaling='test',k=2,snapshots=snapshots)}
        payload=dict(version='delta-r1-preview-v1',default='BASELINE_UNCHANGED',promotion_status='NOT_PROMOTED',variants=variants)
        (root/'preview.json').write_text(json.dumps(payload),encoding='utf8')
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        seal=dict(version='delta-r1-preview-v1',data_sha256=sha(root/'preview.json'),database_sha256=self.base.manifest['database_sha256'],sources={})
        (root/'preview-manifest.json').write_text(json.dumps(seal),encoding='utf8')
        pointer=dict(file='preview.json',file_sha256=sha(root/'preview.json'),manifest='preview-manifest.json',manifest_sha256=sha(root/'preview-manifest.json'))
        (root/'preview-config.json').write_text(json.dumps(pointer),encoding='utf8')
        self.repo=PreviewRepository(self.base,root,'preview-config.json');self.context=TestClient(create_app(self.repo));self.client=self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)

    def test_baseline_stays_default_and_preview_is_explicit(self):
        original=self.client.get('/api/v2/snapshots/market?date=2025-12-31').json()
        candidate=self.client.get('/api/v2/snapshots/market?date=2025-12-31&version=preview').json()
        self.assertEqual(original['points'][0]['cluster'],1);self.assertEqual(candidate['points'][0]['cluster'],7)
        self.assertEqual(self.base.snapshot('market','2025-12-31')['points'][0]['cluster'],1)
        catalog=self.client.get('/api/v2/catalog').json();self.assertEqual(catalog['variants']['market'][0]['status'],'NOT_PROMOTED')
        self.assertNotEqual(catalog['metadata']['bundle_revision'],self.base.manifest['database_sha256'])

    def test_members_stock_compare_and_migration_use_one_version(self):
        members=self.client.get('/api/v2/members/market?date=2024-12-31&version=preview&cluster=11').json()
        self.assertEqual(members['items'][0]['ticker'],'TESTB')
        stock=self.client.get('/api/v2/stocks/TESTA?date=2025-12-31&version=preview').json()
        self.assertEqual(stock['current']['cluster'],7);self.assertEqual(stock['history_versions']['market'],'preview')
        compare=self.client.get('/api/v2/compare?tickers=TESTA,TESTB&date=2025-12-31&version=preview').json()
        self.assertEqual(compare['items'][0]['observation']['cluster'],7);self.assertIsNone(compare['items'][1]['observation'])
        migration=self.client.get('/api/v2/migration/market?source=2024-12-31&target=2025-12-31&version=preview').json()
        self.assertEqual(migration['stayed'],1);self.assertEqual(migration['unmatched_source'],[11])

    def test_rectangular_matrix_filters_match_explicit_versions(self):
        matrix=self.client.get('/api/v2/matrix/2025?version=preview&market_version=preview').json()
        self.assertEqual(matrix['cells'],[dict(market_cluster=7,financial_cluster=7,n=1)])
        members=self.client.get('/api/v2/members/financial?date=2025&version=preview&matrix_market_version=preview&matrix_market=7&matrix_financial=7').json()
        self.assertEqual(members['total'],1);self.assertEqual(members['items'][0]['ticker'],'TESTA')

    def test_unknown_versions_dates_and_old_revision_fail_closed(self):
        for route in ('/snapshots/market?version=missing','/matrix/2025?market_version=missing'):
            self.assertEqual(self.client.get('/api/v2'+route).status_code,409)
        self.assertEqual(self.client.get('/api/v2/snapshots/market?version=preview&date=1999').status_code,404)
        self.assertEqual(self.client.get('/api/v2/snapshots/market',params={'revision':self.base.manifest['database_sha256']}).status_code,409)

    def test_preview_checksum_failure_does_not_substitute_baseline(self):
        (self.fixture.bundle/'preview.json').write_text('{}',encoding='utf8')
        with self.assertRaises(MissingData):PreviewRepository(self.base,self.fixture.bundle,'preview-config.json')

if __name__=='__main__':unittest.main()
