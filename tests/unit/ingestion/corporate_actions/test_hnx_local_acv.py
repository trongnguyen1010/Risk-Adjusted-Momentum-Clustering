import json
from pathlib import Path
import ssl
import tempfile
import unittest
import zipfile

from delta_t1.ingestion.corporate_actions import hnx_local_pvs as p
from delta_t1.ingestion.corporate_action_sources import SourceLimitation
from tests.unit.ingestion.test_hnx_announcement_discovery import profile
from tests.unit.ingestion.test_hnx_detail_parser import listing, popup, Transport, STOCK_TITLE, STOCK

ROOT=Path(__file__).resolve().parents[4]
CONFIG=json.loads((ROOT/'configs/data/corporate_actions/hnx_acv_local_pilot_v1.json').read_text(encoding='utf-8'))

def quiet(*args,**kwargs):pass
def tls(*args,**kwargs):return ssl.create_default_context(),{'status':'VALIDATED'}
def page(aid='573433',title=STOCK_TITLE):
    return listing(aid,title).replace('06/11/2024 15:40','30/07/2025 16:59')
def detail():
    return popup('ACV',STOCK_TITLE,STOCK).replace('14/11/2024','08/08/2025').replace('13/11/2024','07/08/2025')


class AcvLocalTests(unittest.TestCase):
    def test_fixed_acv_scope_requires_known_noncash_article_and_small_budget(self):
        p.validate(CONFIG)
        for key,value in [('ticker','PVS'),('exchange','HNX'),('max_requests',100),('interval_seconds',2),
            ('known_article_id','537190'),('require_known_article',False),('expected_event_type','CASH_DIVIDEND'),
            ('published_start','2019-01-31'),('resume_old_checkpoint',True)]:
            with self.subTest(key=key),self.assertRaises(ValueError):p.validate(dict(CONFIG,**{key:value}))

    def test_dry_run_is_upcom_and_does_not_prepare_tls_or_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp)/'out'
            result=p.run(ROOT,out,CONFIG,dry_run=True,prepare_tls=lambda *a,**kw:self.fail('no TLS'))
            self.assertEqual('UPCOM',result['exchange']);self.assertEqual(0,result['network_requests']);self.assertFalse(out.exists())

    def test_real_parser_chain_extracts_stock_ratio_without_filling_payment_date(self):
        bodies=iter([profile('ACV','UC'),page(),detail()])
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp)/'out'
            result=p.run(ROOT,out,CONFIG,transport_factory=lambda path,**kw:Transport(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual('PILOT_FINISHED_REVIEW_REQUIRED',result['status']);self.assertEqual(3,result['network_requests'])
            parsed=json.loads((out/'parsed/result.json').read_text(encoding='utf-8'));fields=parsed['samples'][0]['fields']
            self.assertEqual('STOCK_DIVIDEND',fields['event_type']);self.assertEqual(.6458,fields['stock_dividend_ratio'])
            self.assertEqual('2025-08-07',fields['ex_date']);self.assertEqual('2025-08-08',fields['record_date'])
            self.assertNotIn('payment_date',fields);self.assertFalse(result['canonical_build'])
            runtime=json.loads((out/'runtime.json').read_text(encoding='utf-8'))
            self.assertIn('probe_hnx_acv_local_v1.py',runtime['code_config_hashes'])
            p.seal(out,Path(tmp)/'acv.zip',artifact_type='hnx-acv-local-known-event-pilot-v1')
            with zipfile.ZipFile(Path(tmp)/'acv.zip') as z:
                manifest=json.loads(z.read('manifest.json'));self.assertEqual('hnx-acv-local-known-event-pilot-v1',manifest['artifact_type'])
                for name,digest in manifest['files'].items():self.assertEqual(digest,p.sha(z.read(name)))

    def test_wrong_article_is_not_used_as_fallback(self):
        bodies=iter([profile('ACV','UC'),page('123')])
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp)/'out';result=p.run(ROOT,out,CONFIG,transport_factory=lambda path,**kw:Transport(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual(2,result['network_requests']);self.assertEqual('PARTIAL_KNOWN_ARTICLE_NOT_IN_ONE_PAGE',result['status'])
            self.assertFalse((out/'detail').exists())

    def test_wrong_event_type_retains_raw_but_does_not_report_pilot_success(self):
        bodies=iter([profile('ACV','UC'),page(title='Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt'),popup('ACV')])
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp)/'out';result=p.run(ROOT,out,CONFIG,transport_factory=lambda path,**kw:Transport(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual(3,result['network_requests']);self.assertEqual('STOPPED_SETUP_OR_SOURCE_REVIEW_REQUIRED',result['status'])
            self.assertEqual('KNOWN_ARTICLE_EVENT_TYPE_REQUIRES_REVIEW',result['reason']);self.assertTrue((out/'detail/raw').is_dir())

    def test_denied_profile_stops_before_list_and_detail(self):
        class Denied(Transport):
            def fetch(self,url,payload=None,content_type=None):
                super().fetch(url,payload,content_type);self.requests[-1].update(status=403,error='SOURCE_ACCESS_LIMITATION')
                raise SourceLimitation('SOURCE_ACCESS_LIMITATION: HTTP403')
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as tmp:
            out=Path(tmp)/'out';bodies=iter([profile('ACV','UC')])
            result=p.run(ROOT,out,CONFIG,transport_factory=lambda path,**kw:Denied(path,bodies,**kw),prepare_tls=tls,emit=quiet)
            self.assertEqual(1,result['network_requests']);self.assertFalse((out/'detail').exists());self.assertTrue(result['limitations'])


if __name__=='__main__':unittest.main()
