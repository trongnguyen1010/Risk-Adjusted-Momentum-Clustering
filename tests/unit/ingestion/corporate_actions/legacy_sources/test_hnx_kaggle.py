import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_kaggle import audit_assignments, build_bundle, preflight, export_state, make_notebook, run_kaggle, CANONICAL
from delta_t1.ingestion.corporate_action_sources import SourceLimitation, sha
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def seal(root):
    save(root / "manifest.json", {"files": {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"}})


def fixture(root):
    members = [{"ticker": f"TT{i}", "security_id": f"SEC{i:02}", "exchange": ["HOSE","HNX","UPCOM"][i % 3]} for i in range(9)]
    path = root / CANONICAL; path.parent.mkdir(parents=True)
    path.write_text('\n'.join(json.dumps(r) for r in members))
    for index in range(4):
        folder = root / f"data/corporate_actions/work/outputs/batch_shard_{index}"
        rows = [{"ticker": r["ticker"]} for i, r in enumerate(members) if i > 0 and (i - 1) % 4 == index]
        save(folder / "batch_results.json", {"results":rows,"physical_requests":len(rows)})
        for row in rows:
            receipts = [{"url":"https://vsdc.vn/vi/ad/1","status":200}] if index else [{"url":"https://www.hnx.vn/vi-vn/m-tim-kiem-TT1.html","error":"SSL: CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate"}]
            save(folder / f"source_receipts/{row['ticker']}/requests.json", receipts)
        seal(folder)
    bootstrap = root / 'tmp/ca_c8_v2_checkpoint_20261101_v5'
    save(bootstrap / 'resume_state.json', {"processed_securities":["TT0"]}); seal(bootstrap)
    (root / 'src').mkdir(); (root / 'src/example.py').write_text('# fixture\n')
    (root / 'scripts').mkdir(); (root / 'scripts/run_hnx_kaggle_v1.py').write_text('# fixture\n')
    save(root / 'configs/data/hnx_batch_v1.json', {})
    for name in ['hnx_tls_chain_v1.json','certificates/globalsign_gcc_r3_ev_tls_ca_2025.pem']:
        target=root/'configs/data'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'configs/data'/name,target)


class Transport:
    def __init__(self, root, **kwargs): self.root, self.requests = root, []
    def fetch(self, url):
        body = ('<input id="StockCode" value="PVS"><input id="MarketCode" value="NY">'
                '<input id="txtTuNgayTinCB"><input id="txtDenNgayTinCB">/ModuleIssuer/List/ThongTinCongBo')
        (self.root / 'raw').mkdir(); (self.root / 'raw/response.bin').write_text(body)
        self.requests.append({"status":200,"path":"raw/response.bin","url":url})
        return body, self.requests[-1]


class HnxKaggleTests(unittest.TestCase):
    def test_ownership_union_no_bootstrap_duplication_and_ssl_cause_is_not_assumed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);fixture(root);report,assignments=audit_assignments(root)
            self.assertEqual(9, report['union_tickers']);self.assertEqual(8,report['new_unique_tickers']);self.assertEqual(1,report['bootstrap_tickers'])
            union=[ticker for a in assignments for ticker in a['all_tickers']]
            self.assertEqual(9,len(union));self.assertEqual(9,len(set(union)))
            self.assertEqual(6,sum(len(a['hnx_tickers']) for a in assignments))
            self.assertEqual(2,report['ssl_failed_requests']);self.assertIn('not_proven',report['diagnosis'])
            for index,a in enumerate(assignments):
                self.assertIn(f'TT{index+1}',a['all_tickers'])

    def test_tampered_old_requests_rejected_without_overwriting_inputs(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);fixture(root)
            (root/'data/corporate_actions/work/outputs/batch_shard_0/source_receipts/TT1/requests.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'CHECKSUM'):audit_assignments(root)

    def test_preflight_pass_verifies_raw_and_is_not_historical_cause_proof(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'check';result=preflight(out,transport_factory=Transport)
            self.assertEqual('PASS_CURRENT_ENVIRONMENT_ONLY',result['status']);self.assertEqual(1,result['network_requests'])
            self.assertEqual('NOT_DETERMINED',result['historical_kaggle_cause'])
            verify_artifact(out,{'hnx-kaggle-preflight-v1'})
            env=json.loads((out/'environment.json').read_text())
            self.assertTrue(env['check_hostname']);self.assertNotIn('HTTPS_PROXY',env)

    def test_ssl_failure_is_preserved_and_no_retry(self):
        class Blocked(Transport):
            def fetch(self,url):
                self.requests.append({'url':url,'error':'CERTIFICATE_VERIFY_FAILED'})
                raise SourceLimitation('CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'check';result=preflight(out,transport_factory=Blocked)
            self.assertEqual('BLOCKED_PREFLIGHT',result['status']);self.assertEqual(1,result['network_requests'])
            self.assertTrue((out/'environment.json').is_file());verify_artifact(out)

    def test_context_creation_failure_still_exports_environment_without_network(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'check'
            with patch('delta_t1.ingestion.hnx_kaggle.ssl.create_default_context',side_effect=OSError('invalid CA path')):
                result=preflight(out,transport_factory=Transport)
            self.assertEqual('BLOCKED_PREFLIGHT',result['status']);self.assertEqual(0,result['network_requests'])
            self.assertIn('context_creation_error',json.loads((out/'environment.json').read_text()))

    def test_bundle_contains_only_code_canonical_assignments_and_compilable_notebooks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'repo';root.mkdir();fixture(root);out=Path(t)/'package'
            result=build_bundle(root,out)
            self.assertEqual(6,result['scope_tickers'])
            with zipfile.ZipFile(result['bundle']) as z:
                names=z.namelist();self.assertIn('assignments/shard_3.json',names)
                self.assertFalse(any('batch_shard_' in n or '.venv' in n for n in names))
            for index in range(4):
                nb=json.loads((out/f'DELTA_HNX_Shard_{index}.ipynb').read_text())
                for cell in nb['cells']:
                    if cell['cell_type']=='code':compile(''.join(cell['source']),'<notebook>','exec')
                self.assertIn(f'SHARD_INDEX = {index}',''.join(nb['cells'][1]['source']))
                self.assertIn('RUN_COLLECTION = False',''.join(nb['cells'][1]['source']))
            with self.assertRaises(FileExistsError):build_bundle(root,out)

    def test_export_state_excludes_prior_state_manifest_and_preserves_code_pin(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'project';root.mkdir();save(root/'bundle_manifest.json',{'files':{}});save(root/'state_manifest.json',{'old':True})
            save(root/'raw/result.json',{'value':1});out=Path(t)/'state.zip';export_state(root,out,2)
            with zipfile.ZipFile(out) as z:
                self.assertEqual(1,z.namelist().count('state_manifest.json'))
                state=json.loads(z.read('state_manifest.json'));self.assertEqual(2,state['shard_index'])
                self.assertEqual(sha((root/'bundle_manifest.json').read_bytes()),state['bundle_manifest_sha256'])
                for name,h in state['files'].items():self.assertEqual(h,sha(z.read(name)))

    def test_bootstrap_executes_for_zip_expanded_dataset_and_state_restore(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t);root=temp/'repo';root.mkdir();fixture(root);package=temp/'package'
            result=build_bundle(root,package)
            code=''.join(make_notebook(0,result['bundle_manifest_sha256'])['cells'][2]['source']).replace("Path('/kaggle/input')","Path(INPUT_DIR)")
            for expanded in [False,True]:
                inp=temp/('expanded' if expanded else 'zipped');inp.mkdir()
                if expanded:
                    with zipfile.ZipFile(result['bundle']) as z:z.extractall(inp/'dataset')
                else:shutil.copyfile(result['bundle'],inp/'delta-hnx-kaggle.zip')
                work=temp/('work-expanded' if expanded else 'work-zipped')
                namespace={'Path':Path,'SHARD_INDEX':0,'WORK':work,'EXPECTED_BUNDLE_SHA256':result['bundle_manifest_sha256'],'INPUT_DIR':inp}
                with patch('builtins.print'):exec(code,namespace)
                self.assertTrue((work/'assignments/shard_0.json').is_file())
                if not expanded:
                    export_state(work,inp/'delta-hnx-state-s0-test.zip',0)
                    old=temp/'old-work-zipped'
                    self.assertTrue(work.resolve().is_relative_to(temp));self.assertTrue(old.resolve().is_relative_to(temp))
                    work.rename(old)
                    with patch('builtins.print'):exec(code,namespace)
                    self.assertEqual((old/'bundle_manifest.json').read_bytes(),(work/'bundle_manifest.json').read_bytes())

    def test_blocked_kaggle_preflight_cannot_start_collection(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);fixture(root);_,assignments=audit_assignments(root)
            save(root/'assignments/shard_0.json',assignments[0])
            with patch('delta_t1.ingestion.hnx_kaggle.run_batch',return_value={'scope_tickers':1}) as batch, patch('delta_t1.ingestion.hnx_kaggle.preflight',return_value={'status':'BLOCKED_PREFLIGHT','limitation':'SSL'}) as probe, patch('delta_t1.ingestion.hnx_kaggle.validated_hnx_context',return_value=(object(),{})):
                result=run_kaggle(root,0,collect=True)
                self.assertFalse(result['collection_started']);self.assertEqual(1,batch.call_count)
                self.assertTrue(batch.call_args.kwargs['dry_run']);self.assertEqual(1,probe.call_count)

    def test_failed_intermediate_validation_starts_no_https_preflight(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);fixture(root);_,assignments=audit_assignments(root)
            save(root/'assignments/shard_0.json',assignments[0])
            with patch('delta_t1.ingestion.hnx_kaggle.run_batch',return_value={'scope_tickers':1}), patch('delta_t1.ingestion.hnx_kaggle.validated_hnx_context',side_effect=SourceLimitation('invalid chain')), patch('delta_t1.ingestion.hnx_kaggle.preflight') as probe:
                result=run_kaggle(root,0,collect=True)
                self.assertFalse(result['collection_started']);self.assertEqual(0,probe.call_count)


if __name__=='__main__':unittest.main()
