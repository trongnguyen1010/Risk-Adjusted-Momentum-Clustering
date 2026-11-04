import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from delta_t1.ingestion.corporate_actions import hnx_local_pvs as p
from delta_t1.ingestion.corporate_action_sources import SourceLimitation
from tests.unit.ingestion.test_hnx_announcement_discovery import profile
from tests.unit.ingestion.test_hnx_detail_parser import listing, popup, Transport

ROOT = Path(__file__).resolve().parents[4]
CONFIG = json.loads((ROOT / 'configs/data/corporate_actions/hnx_pvs_local_pilot_v1.json').read_text(encoding='utf-8'))


def quiet(*args, **kwargs): pass
def tls(*args, **kwargs): return ssl.create_default_context(), {'status': 'VALIDATED'}


class PvsLocalTests(unittest.TestCase):
    def test_exact_scope_and_no_expansion_or_resume(self):
        p.validate(CONFIG)
        for key, value in [('ticker', 'ACV'), ('max_requests', 100), ('max_pages', 2),
            ('interval_seconds', 2), ('published_start', '2019-01-31'), ('canonical_build', True),
            ('resume_old_checkpoint', True), ('retry', True)]:
            with self.subTest(key=key), self.assertRaises(ValueError): p.validate(dict(CONFIG, **{key:value}))

    def test_dry_run_never_prepares_tls_calls_source_or_creates_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            target=Path(tmp)/'out'
            result=p.run(ROOT,target,CONFIG,dry_run=True,prepare_tls=lambda *a,**kw: self.fail('no TLS'))
            self.assertEqual(0,result['network_requests']);self.assertFalse(target.exists())

    def test_actual_existing_discovery_detail_parser_chain_uses_three_requests(self):
        bodies=iter([profile(),listing('537190'),popup()]); options=[]
        def factory(path,**kwargs): options.append(kwargs);return Transport(path,bodies,**kwargs)
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            output=Path(tmp)/'out'
            result=p.run(ROOT,output,CONFIG,transport_factory=factory,prepare_tls=tls,emit=quiet)
            self.assertEqual('PILOT_FINISHED_REVIEW_REQUIRED',result['status'])
            self.assertEqual(3,result['network_requests']);self.assertEqual(1,result['successful_details'])
            self.assertEqual(1,result['preview_observations']);self.assertEqual('537190',result['selected_article_id'])
            self.assertTrue(all(o['interval']==8 for o in options))
            self.assertFalse(result['canonical_build']);self.assertFalse(result['bulk_collection_ready'])
            p.seal(output,Path(tmp)/'pilot.zip')
            with zipfile.ZipFile(Path(tmp)/'pilot.zip') as z:
                m=json.loads(z.read('manifest.json'));self.assertEqual('hnx-pvs-local-known-event-pilot-v1',m['artifact_type'])
                for name,digest in m['files'].items(): self.assertEqual(digest,p.sha(z.read(name)))

    def test_source_denial_at_list_prevents_detail_or_further_tickers(self):
        bodies=iter([profile(),listing()])
        class Denied(Transport):
            def fetch(self,url,payload=None,content_type=None):
                response=super().fetch(url,payload,content_type)
                if payload:
                    self.requests[-1].update(status=403,error='SOURCE_ACCESS_LIMITATION')
                    raise SourceLimitation('SOURCE_ACCESS_LIMITATION: HTTP403; no retry')
                return response
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            output=Path(tmp)/'out'
            result=p.run(ROOT,output,CONFIG,transport_factory=lambda path,**kw:Denied(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual(2,result['network_requests']);self.assertEqual(0,result['successful_details'])
            self.assertFalse((output/'detail').exists());self.assertTrue(result['limitations'])

    def test_no_title_candidate_stops_after_one_list_page(self):
        bodies=iter([profile(),listing(title='Thông tin khác')])
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            result=p.run(ROOT,Path(tmp)/'out',CONFIG,transport_factory=lambda path,**kw:Transport(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual(2,result['network_requests']);self.assertEqual('PARTIAL_NO_PRICE_ACTION_CANDIDATE_IN_ONE_PAGE',result['status'])

    def test_tls_setup_failure_is_saved_without_source_requests(self):
        def broken(*args,**kwargs):raise SourceLimitation('TLS_CHAIN_PREPARATION_FAILED')
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            result=p.run(ROOT,Path(tmp)/'out',CONFIG,prepare_tls=broken,emit=quiet)
            self.assertEqual(0,result['network_requests']);self.assertEqual('SourceLimitation',result['error_type'])

    def test_global_request_budget_is_three_across_clients(self):
        bodies=iter([profile(),listing(),popup()])
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp);(out/'request_log.jsonl').touch()
            budget=p.RunBudget(out,3,120,lambda path,**kw:Transport(path,bodies,**kw),lambda:0)
            client=budget.transport(out,max_requests=3,interval=8,timeout=15)
            for _ in range(3):client.fetch('https://www.hnx.vn/test')
            with self.assertRaisesRegex(SourceLimitation,'REQUEST_BUDGET'):client.fetch('https://www.hnx.vn/test')
            self.assertEqual(3,budget.count)


if __name__=='__main__':unittest.main()
