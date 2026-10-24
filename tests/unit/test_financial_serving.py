import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/backend'))
spec=importlib.util.spec_from_file_location('serving_builder',ROOT/'scripts/build_financial_serving.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
from app.indicators import IndicatorReferences
from app.repository import MissingData
from app.schemas import IndicatorResponse


class ReportedEPSTests(unittest.TestCase):
    def sample(self):
        label='19. Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)'
        body=dict(isSuccess=True,value=dict(timeType='QUY',type='KQKD',templace=[dict(code='70',name=label)],data=[dict(symbol='TEST',year=2025,quater=2,type='K',data=[dict(code='70',value=120)])]))
        return body,dict(raw_code='70',label=label)

    def test_period_code_and_explicit_unit_required(self):
        p,e=self.sample()
        self.assertTrue(builder.verify_quoted_eps(p,e,'TEST',2025,2,'QUY','K','120'))
        for args in [('TEST',2025,1,'QUY','K','120'),('TEST',2024,2,'QUY','K','120'),('OTHER',2025,2,'QUY','K','120'),('TEST',2025,2,'NAM','K','120'),('TEST',2025,2,'QUY','K','121')]:
            self.assertFalse(builder.verify_quoted_eps(p,e,*args))
        p['value']['templace'][0]['name']='Lãi cơ bản trên cổ phiếu'
        e['label']=p['value']['templace'][0]['name']
        self.assertFalse(builder.verify_quoted_eps(p,e,'TEST',2025,2,'QUY','K','120'))

    def test_ambiguous_code_and_sentinel_never_promoted(self):
        p,e=self.sample();p['value']['templace'].append(p['value']['templace'][0].copy())
        self.assertFalse(builder.verify_quoted_eps(p,e,'TEST',2025,2,'QUY','K','120'))
        p,e=self.sample();p['value']['data'][0]['data'][0]['value']=-1
        self.assertFalse(builder.verify_quoted_eps(p,e,'TEST',2025,2,'QUY','K','-1'))

    def test_sqlite_ticker_isolated_year_normalized_and_source_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);db=sqlite3.connect(root/'eps.sqlite')
            db.executescript('CREATE TABLE observations(symbol TEXT,year INTEGER,payload TEXT);CREATE TABLE metadata(key TEXT,value TEXT);')
            for symbol,value in [('TEST','123.00000000000000001'),('OTHER','456'),('ZERO','0')]:
                payload=dict(symbol=symbol,year=2025,family='EPS',value=value,status='PROVIDER_REPORTED',period_kind='QUARTER_REPORTED',input_period='2025-Q2',cohort_id=symbol+'2025Q2')
                db.execute('INSERT INTO observations VALUES(?,?,?)',(symbol,2025,json.dumps(payload)))
            db.execute('INSERT INTO metadata VALUES(?,?)',('summary',json.dumps(dict(numeric_reported_eps=3,symbols_with_reported_eps=3))))
            db.commit();db.close()
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            (root/'manifest.json').write_text(json.dumps({'eps.sqlite':sha(root/'eps.sqlite')}),encoding='utf-8')
            (root/'config.json').write_text(json.dumps(dict(sources=[dict(id='provider_eps',label='CafeF',format='sqlite',hide_unconfirmed_zero=True,file='eps.sqlite',file_sha256=sha(root/'eps.sqlite'),manifest='manifest.json',manifest_sha256=sha(root/'manifest.json'))])),encoding='utf-8')
            refs=IndicatorReferences(root,'config.json')
            result=IndicatorResponse.model_validate(refs.stock('TEST'))
            self.assertEqual(len(result.groups),1)
            self.assertEqual(result.groups[0].year,'2025')
            metric=result.groups[0].metrics[0]
            self.assertEqual(metric.value,'123.00000000000000001')
            self.assertEqual(metric.availability,'SOURCE_REPORTED')
            self.assertFalse(metric.production_ready)
            self.assertIsNone(result.groups[0].metrics[1].value)
            self.assertFalse(refs.stock("TEST' OR 1=1 --")['available'])
            self.assertEqual(refs.coverage()['packages'][0]['families']['EPS'],2)
            zero=refs.stock('ZERO')
            self.assertFalse(zero['available'])
            self.assertIsNone(zero['groups'][0]['metrics'][0]['value'])
            self.assertEqual(zero['groups'][0]['metrics'][0]['components']['source_reported_value'],'0')
            # Bytes that no longer match the pin cannot be served.
            with (root/'eps.sqlite').open('ab') as stream:stream.write(b'changed')
            with self.assertRaises(MissingData):IndicatorReferences(root,'config.json').stock('TEST')


if __name__=='__main__':unittest.main()
