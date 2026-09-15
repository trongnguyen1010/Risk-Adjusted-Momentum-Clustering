import copy
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.contracts import coerce, normalize, schema, validate_rows
from delta_t1.features.compute import momentum, returns, drawdown, build_features
from delta_t1.ingestion.crawler import crawl
from delta_t1.ingestion.quality import clean_tables
from delta_t1.ingestion.providers import HttpClient, json_page
from delta_t1.ingestion.vnstock import date_batches, worker, collect
from delta_t1.pipeline import run, load_config
from delta_t1.io import read_json, read_rows, write_json

spec = importlib.util.spec_from_file_location("generate_demo", ROOT / "scripts/generate_demo.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class FormulaTests(unittest.TestCase):
    def test_sdk_worker_runs_in_staging_directory(self):
        directories = []
        def fake_run(args, **kwargs):
            directories.append(Path(kwargs['cwd']))
            write_json(Path(args[-1]), {'records':[{'test':1}], 'fetched_at':'2026-09-11T00:00:00+00:00'})
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as temp:
            with patch('delta_t1.ingestion.vnstock.importlib.metadata.version',return_value='4.0.6'), patch('delta_t1.ingestion.vnstock.subprocess.run',side_effect=fake_run), patch('time.sleep'):
                target, manifest=collect(temp,'2026-08-01','2026-08-02',['FPT'],attempts=1)
            self.assertEqual(manifest['status'],'complete')
            self.assertTrue(all(path == target/'work' for path in directories))
            self.assertEqual(len(directories),3)

    def test_sdk_explicit_range_is_not_truncated_at_100(self):
        calls = []
        class Asset:
            def ohlcv(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(to_json=lambda **kw: '[{"time":"2026-08-03","close":71.7}]', columns=['time','close'], attrs={'source':'KBS'})
        fake = SimpleNamespace(Market=lambda: SimpleNamespace(equity=lambda symbol: Asset()), Reference=lambda: None)
        with tempfile.TemporaryDirectory() as temp:
            inp,out=Path(temp)/'job.json',Path(temp)/'out.json'
            write_json(inp,dict(kind='equity',symbol='FPT',start='2026-01-01',end='2026-08-31'))
            with patch.dict(sys.modules,{'vnstock':fake}), patch('delta_t1.ingestion.vnstock.importlib.metadata.version',return_value='4.0.6'):
                worker(inp,out)
            self.assertIsNone(calls[0]['count'])
            self.assertTrue(calls[0]['get_all'])
            self.assertEqual(read_json(out)['sdk_metadata']['source'],'KBS')

    def test_hand_calculation(self):
        self.assertAlmostEqual(returns([100,110,99])[0], .1)
        self.assertAlmostEqual(returns([100,110,99])[1], -.1)
        self.assertAlmostEqual(momentum([100,110,99], 2), -.01)
        self.assertAlmostEqual(drawdown([100,110,99],3), -.1)

    def test_missing_session_not_compressed(self):
        self.assertIsNone(momentum([100,None,110],2))
        self.assertEqual(returns([100,None,110]), [None,None])

    def test_252_requires_253_prices(self):
        self.assertIsNone(momentum([100]*252,252))
        self.assertEqual(momentum([100]*253,252),0)

    def test_reject_nonfinite_and_bad_date(self):
        for value in ('nan','inf','-inf',True):
            with self.assertRaises(ValueError):
                coerce(value, {'type':'number'})
        with self.assertRaises(ValueError):
            coerce('2026-02-30',{'type':'date'})
        with self.assertRaises(ValueError):
            coerce('2026-01-01T10:00:00',{'type':'datetime'})

    def test_batches_have_no_overlap(self):
        self.assertEqual(list(date_batches('2024-02-28','2024-03-02',2)), [('2024-02-28','2024-02-29'),('2024-03-01','2024-03-02')])


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.config_path = generator.generate(cls.root)
        cls.config = load_config(cls.config_path)
        cls.directory, cls.manifest = run(cls.config_path,cls.root)
        cls.tables = {table: read_rows(cls.directory/'clean'/(table+'.jsonl')) for table in cls.manifest['clean_rows']}
        cls.features = read_rows(cls.directory/'features/monthly.jsonl')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def raw(self,tables):
        return {name:[(r,{'source':'test'},'2026-09-11T00:00:00+00:00') for r in rows] for name,rows in tables.items()}

    def test_end_to_end_and_schema(self):
        self.assertEqual(self.manifest['status'],'complete')
        self.assertEqual(len(self.features),216)
        self.assertTrue(any(r['eligibility'] for r in self.features))
        for name,rows in self.tables.items():
            validate_rows(name,rows)
        validate_rows('feature_snapshots',self.features)
        self.assertFalse(read_json(self.directory/'quality/coverage.json')['m1_accepted'])

    def test_resume_stable(self):
        _, manifest = run(self.config_path,self.root,self.manifest['run_id'])
        self.assertEqual(manifest['data_hash'],self.manifest['data_hash'])
        self.assertEqual(manifest['artifacts'],self.manifest['artifacts'])

    def test_resume_changed_input_rejected(self):
        config=copy.deepcopy(self.config)
        config['features']['rf_annual']=.01
        with self.assertRaisesRegex(ValueError,'config'):
            crawl(config,self.root,self.manifest['run_id'])

    def test_tampered_raw_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=generator.generate(temp)
            directory,manifest,_=crawl(load_config(path),temp)
            entry=next(iter(manifest['jobs'].values()))['pages'][0]
            (directory/entry['path']).write_bytes(b'changed')
            _,second,_=crawl(load_config(path),temp,manifest['run_id'])
            self.assertEqual(second['status'],'failed')

    def test_duplicate_quarantines_both(self):
        tables=copy.deepcopy(self.tables)
        tables['prices_daily'].append(tables['prices_daily'][0])
        cleaned,issues,rejected=clean_tables(self.raw(tables),'v-test')
        self.assertEqual(sum(r['rule_id']=='DUPLICATE_KEY' for r in rejected),2)
        self.assertEqual(len(cleaned['prices_daily']),len(self.tables['prices_daily'])-1)

    def test_ohlc_and_negative_volume(self):
        tables=copy.deepcopy(self.tables)
        tables['prices_daily'][0]['raw_low']=999999
        tables['prices_daily'][1]['volume']=-1
        _,issues,_=clean_tables(self.raw(tables),'v-test')
        self.assertTrue({'OHLC','SCHEMA'} <= {r['rule_id'] for r in issues})

    def test_temporal_identity(self):
        tables=copy.deepcopy(self.tables)
        tables['prices_daily'][0]['ticker']='WRONG'
        _,issues,_=clean_tables(self.raw(tables),'v-test')
        self.assertIn('TEMPORAL_FK',{r['rule_id'] for r in issues})

    def test_metadata_overlap(self):
        tables=copy.deepcopy(self.tables)
        new=copy.deepcopy(tables['securities'][0]);new['valid_from']='2024-02-01'
        tables['securities'].append(new)
        _,issues,_=clean_tables(self.raw(tables),'v-test')
        self.assertIn('METADATA_INTERVAL',{r['rule_id'] for r in issues})

    def test_unit_conversion(self):
        row=self.tables['prices_daily'][0]
        converted=normalize('prices_daily',row,multipliers={'raw_close':1000})
        self.assertAlmostEqual(converted['raw_close'],row['raw_close']*1000)

    def test_future_append_invariance(self):
        cut='2025-03-31'
        truncated=copy.deepcopy(self.tables)
        for name in ('prices_daily','benchmark_daily','trading_calendar'):
            truncated[name]=[r for r in truncated[name] if r['trade_date']<=cut]
        past=build_features(truncated,self.config['features'],self.manifest['data_version'])
        self.assertEqual(past,[r for r in self.features if r['as_of_date']<=cut])

    def test_no_cross_security_rolling(self):
        tables=copy.deepcopy(self.tables)
        sid=tables['securities'][0]['security_id']
        tables['securities']=[r for r in tables['securities'] if r['security_id']==sid]
        tables['prices_daily']=[r for r in tables['prices_daily'] if r['security_id']==sid]
        result=build_features(tables,self.config['features'],self.manifest['data_version'])
        self.assertEqual(result,[r for r in self.features if r['security_id']==sid])

    def test_constant_price_undefined_sharpe_does_not_control_eligibility(self):
        tables=copy.deepcopy(self.tables)
        for r in tables['prices_daily']:
            r['adj_close']=100
        result=build_features(tables,self.config['features'],'constant')
        last=result[-1]
        self.assertEqual(last['vol_63'],0)
        self.assertIsNone(last['sharpe_63'])
        self.assertTrue(last['eligibility'])

    def test_three_year_history_eligibility_uses_observed_data(self):
        tables=copy.deepcopy(self.tables)
        config=dict(self.config['features'], minimum_history_years=3)
        result=build_features(tables,config,'history-test')
        self.assertFalse(any(r['eligibility'] for r in result))
        self.assertEqual({r['universe_segment'] for r in result},{'REFERENCE_ONLY'})
        self.assertTrue(all(r['history_start_date'] == '2024-01-01' for r in result))

    def test_financial_report_contract_and_publication_timing(self):
        report=dict(
            report_id='R1',security_id=self.tables['securities'][0]['security_id'],fiscal_year=2025,
            fiscal_quarter=2,period_start='2025-04-01',period_end='2025-06-30',
            published_at='2025-07-30T09:00:00+07:00',available_at='2025-07-30T10:00:00+07:00',
            statement_scope='consolidated',audit_status='reviewed',accounting_standard='VAS',revision=1,
            is_restated=False,source_document_id='doc-1',source_document_hash='abc',source='fixture',
            fetched_at='2025-07-30T10:00:00+07:00',data_version='v1')
        fact=dict(
            report_id='R1',security_id=report['security_id'],statement_type='income_statement',
            item_code='REVENUE',item_name='Revenue',period_type='duration',value=100,currency='VND',
            unit_scale=1_000_000,source='fixture',fetched_at=report['fetched_at'],data_version='v1')
        validate_rows('financial_reports',[report])
        validate_rows('financial_facts',[fact])
        raw=self.raw(dict(securities=self.tables['securities'],prices_daily=self.tables['prices_daily'],
                          benchmark_daily=self.tables['benchmark_daily'],trading_calendar=self.tables['trading_calendar'],
                          corporate_actions=[],financial_reports=[report],financial_facts=[fact]))
        cleaned,issues,_=clean_tables(raw,'v2')
        self.assertFalse(issues)
        self.assertEqual(len(cleaned['financial_facts']),1)
        bad=copy.deepcopy(report);bad['available_at']='2025-07-29T10:00:00+07:00'
        raw['financial_reports']=self.raw({'financial_reports':[bad]})['financial_reports']
        _,issues,_=clean_tables(raw,'v3')
        self.assertIn('PUBLICATION_TIMING',{r['rule_id'] for r in issues})

    def test_beta_one(self):
        tables=copy.deepcopy(self.tables)
        market={r['trade_date']:r['close'] for r in tables['benchmark_daily']}
        for r in tables['prices_daily']:
            r['adj_close']=market[r['trade_date']]
        result=build_features(tables,self.config['features'],'beta')
        self.assertAlmostEqual(result[-1]['beta_126'],1)

    def test_late_data_and_missing_day(self):
        tables=copy.deepcopy(self.tables)
        for r in tables['prices_daily']:
            if r['trade_date']=='2025-06-20':
                r['available_at']='2025-07-01T17:00:00+07:00'
        result=build_features(tables,self.config['features'],'late')
        self.assertIsNone(result[-1]['mom_21'])
        self.assertFalse(result[-1]['eligibility'])

    def test_bad_qc_blocks_features_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            path=generator.generate(temp)
            prices=Path(temp)/'examples/synthetic/prices_daily.csv'
            with prices.open('a',encoding='utf-8') as f:
                f.write(prices.read_text(encoding='utf-8').splitlines()[1]+'\n')
            directory,manifest=run(path,temp)
            self.assertEqual(manifest['status'],'quality_failed')
            self.assertFalse((directory/'features/monthly.jsonl').exists())


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            calls=0
            def log_message(self,*args):
                pass
            def do_GET(self):
                if self.path.startswith('/denied'):
                    self.send_response(403);self.end_headers();return
                if self.path.startswith('/retry'):
                    Handler.calls+=1
                    if Handler.calls==1:
                        self.send_response(429);self.send_header('Retry-After','0');self.end_headers();return
                self.send_response(200);self.end_headers()
                payload={'items':[{'id':2}], 'next_cursor':None} if 'cursor=' in self.path else {'items':[{'id':1}], 'next_cursor':'page2'}
                self.wfile.write(json.dumps(payload).encode())
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def test_retry_429(self):
        with patch('delta_t1.ingestion.providers.time.sleep'):
            data=HttpClient(min_interval=0).get(self.url+'/retry')
        self.assertEqual(json_page(data)[0][0]['id'],1)

    def test_nonretryable_403(self):
        with self.assertRaisesRegex(ValueError,'403'):
            HttpClient(min_interval=0).get(self.url+'/denied')

    def test_two_pages_and_resume(self):
        config={'jobs':[dict(id='test',table='prices_daily',provider='http_json',endpoint=self.url+'/pages',source='local_test')],'http':{'min_interval':0}}
        with tempfile.TemporaryDirectory() as temp:
            directory,manifest,rows=crawl(config,temp)
            self.assertEqual(manifest['status'],'downloaded')
            self.assertEqual(len(rows['prices_daily']),2)
            with patch.object(HttpClient,'get',side_effect=AssertionError('must not download twice')):
                _,again,_=crawl(config,temp,manifest['run_id'])
            self.assertEqual(again['data_hash'],manifest['data_hash'])

    def test_page_limit_is_failure(self):
        config={'jobs':[dict(id='test',table='prices_daily',provider='http_json',endpoint=self.url+'/pages',source='local_test',max_pages=1)],'http':{'min_interval':0}}
        with tempfile.TemporaryDirectory() as temp:
            _,manifest,_=crawl(config,temp)
            self.assertEqual(manifest['status'],'failed')

    def test_response_size_guard(self):
        with self.assertRaisesRegex(ValueError,'max_bytes'):
            HttpClient(min_interval=0,max_bytes=2).get(self.url+'/pages')


if __name__=='__main__':
    unittest.main()
