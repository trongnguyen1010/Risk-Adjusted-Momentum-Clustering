import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_kaggle_session import run_session
from delta_t1.ingestion.hnx_kaggle import export_state
from scripts.package_hnx_resume_notebooks_v1 import build, PIN
from tests.unit.ingestion.test_hnx_batch import Clock, Source, universe, run


def setup(root):
    (root / "assignments").mkdir()
    (root / "assignments/shard_1.json").write_text(json.dumps({"shard_index": 1, "hnx_tickers": ["ACV", "PVS"]}))
    (root / "bundle_manifest.json").write_text('{}')


def result(*, pending=("PVS",), reason="RUN_REQUEST_BUDGET_EXHAUSTED", resumable=True, requests=1000, quarantined=()):
    return {"status": "PARTIAL" if reason else "COLLECTED_WITH_REVIEWS", "stop_reason": reason,
            "resumable": resumable, "scope_tickers": 2, "handled_tickers": 2-len(pending)-len(quarantined),
            "pending_tickers": list(pending), "quarantined_tickers": list(quarantined),
            "network_requests_this_run": requests}


def seal_result(root, index, value):
    output = root / f"kaggle_runs/shard_1/run-{index:03}/collection"
    output.mkdir(parents=True)
    body = json.dumps(value).encode()
    (output / "result.json").write_bytes(body)
    (output / "manifest.json").write_text(json.dumps({"files": {"result.json": hashlib.sha256(body).hexdigest()}}))
    return output


class SessionTests(unittest.TestCase):
    def test_request_budget_auto_continues_and_exports_before_next_chunk(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'project';root.mkdir();setup(root);calls=[];exports=[]
            def export(project, destination, index):
                export_state(project,destination,index);exports.append(destination)
            def runner(command, **kwargs):
                if calls:self.assertEqual(1,len(exports));self.assertTrue(exports[0].is_file())
                calls.append(command);seal_result(root,len(calls),result() if len(calls)==1 else result(pending=(),reason=None))
                return subprocess.CompletedProcess(command,0)
            summary=run_session(root,1,exporter=export,runner=runner,sleep=lambda seconds:None)
            self.assertEqual('NO_PENDING_TICKERS_REVIEWS_REMAIN',summary['status'])
            self.assertEqual(2,len(calls));self.assertEqual(2,len(exports))
            self.assertTrue(all(c[c.index('--max-requests')+1]=='1000' for c in calls))

    def test_one_global_deadline_is_not_reset_for_new_chunks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root);clock=Clock();calls=[]
            def runner(command,**kwargs):
                calls.append(command);clock.value+=min(60,int(command[command.index('--max-seconds')+1]))
                seal_result(root,len(calls),result(reason='RUN_TIME_BUDGET_EXHAUSTED'))
                return subprocess.CompletedProcess(command,0)
            summary=run_session(root,1,exporter=lambda *a:None,runner=runner,clock=clock.now,max_seconds=100,sleep=clock.sleep)
            self.assertEqual(['100','32'],[c[c.index('--max-seconds')+1] for c in calls])
            self.assertEqual([8,8],clock.delays)
            self.assertEqual('SESSION_TIME_LIMIT_REACHED',summary['status'])

    def test_source_ssl_integrity_preflight_exit_and_interrupt_never_auto_resume(self):
        cases=[('SOURCE_ACCESS_LIMITATION: HTTP 403',False,0),('SSL_CERTIFICATE_VERIFY_FAILED',False,0),
               ('SOURCE_ACCESS_LIMITATION: HTTP 429',False,2),('RETRY_AFTER',False,2),
               ('INTERRUPTED_BY_USER',True,0)]
        for reason,resumable,code in cases:
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as t:
                root=Path(t);setup(root);calls=[]
                def runner(command,**kwargs):
                    calls.append(command);seal_result(root,1,result(reason=reason,resumable=resumable))
                    return subprocess.CompletedProcess(command,code)
                summary=run_session(root,1,exporter=lambda *a:None,runner=runner)
                self.assertEqual(1,len(calls));self.assertNotEqual('NO_PENDING_TICKERS_REVIEWS_REMAIN',summary['status'])
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root);calls=[]
            def failed(command,**kwargs):calls.append(command);return subprocess.CompletedProcess(command,2)
            summary=run_session(root,1,exporter=lambda *a:None,runner=failed)
            self.assertEqual(1,len(calls));self.assertEqual('STOPPED_COLLECTOR_ERROR',summary['status'])

    def test_zero_requests_and_unexpected_pending_do_not_loop(self):
        for value in [result(requests=0),result(reason=None)]:
            with tempfile.TemporaryDirectory() as t:
                root=Path(t);setup(root);calls=[]
                def runner(command,**kwargs):
                    calls.append(command);seal_result(root,len(calls),value);return subprocess.CompletedProcess(command,0)
                run_session(root,1,exporter=lambda *a:None,runner=runner)
                self.assertEqual(1,len(calls))

    def test_checksum_or_scope_failure_stops_without_next_network_chunk(self):
        for tamper in ['checksum','scope']:
            with tempfile.TemporaryDirectory() as t:
                root=Path(t);setup(root);calls=[]
                def runner(command,**kwargs):
                    calls.append(command);value=result()
                    if tamper=='scope':value['pending_tickers']=['AAA']
                    output=seal_result(root,1,value)
                    if tamper=='checksum':(output/'result.json').write_text('{}')
                    return subprocess.CompletedProcess(command,0)
                summary=run_session(root,1,exporter=lambda *a:None,runner=runner)
                self.assertEqual(1,len(calls));self.assertEqual('STOPPED_SESSION_ERROR',summary['status'])

    def test_no_pending_with_quarantine_is_finished_workflow_not_approved_data(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root)
            def runner(command,**kwargs):
                seal_result(root,1,result(pending=(),reason=None,quarantined=('ACV',)))
                return subprocess.CompletedProcess(command,0)
            summary=run_session(root,1,exporter=lambda *a:None,runner=runner)
            self.assertEqual('NO_PENDING_TICKERS_REVIEWS_REMAIN',summary['status'])
            self.assertFalse(summary['canonical_build']);self.assertFalse(summary['historical_coverage_certified'])
            self.assertEqual(['ACV'],summary['last_result']['quarantined_tickers'])

    def test_actual_batch_resumes_partial_detail_without_recollecting_old_requests(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root);universe(root);clock=Clock();source=Source(clock);calls=[]
            previous=None
            def runner(command,**kwargs):
                nonlocal previous
                calls.append(command);name=f'kaggle_runs/shard_1/run-{len(calls):03}/collection'
                out=root/name;out.parent.mkdir(parents=True)
                with patch('delta_t1.ingestion.corporate_action_sources.time.monotonic',clock.now):
                    value=run(root,source,name,max_requests=3,resume_from=previous)
                previous=out
                return subprocess.CompletedProcess(command,0 if value['resumable'] else 2)
            summary=run_session(root,1,exporter=lambda *a:None,runner=runner,clock=clock.now,sleep=clock.sleep)
            self.assertEqual('NO_PENDING_TICKERS_REVIEWS_REMAIN',summary['status'])
            self.assertEqual(3,len(calls));self.assertEqual(8,len(source.calls))
            self.assertEqual(4,summary['last_result']['observation_count'])
            self.assertEqual(1,sum(c['form'].get('pArticlesID')==['200'] for c in source.calls))
            self.assertEqual(0,summary['last_result']['accepted_publication_timestamps'])

    def test_notebooks_embed_tested_wrapper_keep_exact_v5_bootstrap_and_do_not_change_state_code(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'notebooks';build(out)
            source=ROOT/'tmp/hnx_kaggle_export_20261102_v5'
            wrapper=(ROOT/'src/delta_t1/ingestion/hnx_kaggle_session.py').read_text(encoding='utf-8')
            for index in range(4):
                old=json.loads((source/f'DELTA_HNX_Shard_{index}.ipynb').read_text(encoding='utf-8'))
                new=json.loads((out/f'DELTA_HNX_Resume_Shard_{index}.ipynb').read_text(encoding='utf-8'))
                self.assertEqual(old['cells'][2]['source'],new['cells'][2]['source'])
                config={};exec(''.join(new['cells'][1]['source']),config)
                self.assertEqual(index,config['SHARD_INDEX']);self.assertTrue(config['RUN_COLLECTION'])
                self.assertEqual(21600,config['MAX_SECONDS']);self.assertEqual(1000,config['MAX_REQUESTS'])
                self.assertEqual(PIN,config['EXPECTED_BUNDLE_SHA256'])
                self.assertTrue(''.join(new['cells'][3]['source']).startswith(wrapper))
                for cell in new['cells']:
                    if cell['cell_type']=='code':ast.parse(''.join(cell['source']))


if __name__=='__main__':unittest.main()
