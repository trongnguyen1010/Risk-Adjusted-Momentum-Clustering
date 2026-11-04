import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_discovery import discover, profile_context, parse_search_page, search_payload
from delta_t1.ingestion.corporate_action_sources import SourceLimitation

SCOPE = [{"ticker":"PVS","exchange":"HNX"}]


def profile(ticker="PVS", market="NY"):
    return (f'<input id="StockCode" value="{ticker}"><input id="MarketCode" value="{market}">'
            '<input id="txtTuNgayTinCB"><input id="txtDenNgayTinCB">'
            '<script>var url="/ModuleIssuer/List/ThongTinCongBo";</script>')


def listing(article="100", total=1, timestamp="24/09/2019 14:38"):
    return ('<table><tr><th>Ngày đăng tin</th><th>Tiêu đề tin</th></tr>'
            f'<tr><td>1</td><td>{timestamp}</td><td><a onclick="return XemChiTietDetailArticlesByID({article},0)" '
            'href="javascript:;">Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt</a></td></tr>'
            f'</table>Tổng số {total} bản ghi')


class Transport:
    def __init__(self, root, responses, **kwargs):
        self.root, self.responses, self.requests = root, iter(responses), []
        self.limit = kwargs['max_requests']
    def fetch(self, url, payload=None, content_type=None):
        if len(self.requests)>=self.limit:
            raise SourceLimitation('REQUEST_BUDGET_EXHAUSTED')
        body=next(self.responses)
        path=f"raw/{len(self.requests)+1}.bin";(self.root/'raw').mkdir(exist_ok=True)
        (self.root/path).write_bytes(body.encode())
        receipt={'url':url,'request_body':payload.decode() if payload else None,'path':path,
                 'status':200,'fetched_at':'2026-11-01T00:00:00+00:00','source_hash':hashlib.sha256(body.encode()).hexdigest()}
        self.requests.append(receipt)
        return body,receipt


class HnxAnnouncementDiscoveryTests(unittest.TestCase):
    def test_observed_aav_empty_query_is_zero_rows_not_history_attestation(self):
        html=(ROOT/'tests/fixtures/hnx_disclosure_empty_aav_20261101.html').read_text(encoding='utf-8')
        rows,total=parse_search_page(html,'AAV','UPCOM',1)
        self.assertEqual([],rows);self.assertEqual(0,total)
        with tempfile.TemporaryDirectory() as t:
            def factory(root,**kwargs):return Transport(root,[profile('AAV','UC'),html],**kwargs)
            result=discover([{'ticker':'AAV','exchange':'UPCOM'}],'2019-01-31','2025-12-31',Path(t)/'out',transport_factory=factory)
            self.assertEqual([],result['limitations']);self.assertEqual(0,result['discovered_article_ids'])
            self.assertTrue(result['checks'][0]['empty_query_requires_scope_review'])
            self.assertEqual('NOT_CERTIFIED',result['checks'][0]['full_history_coverage'])
            self.assertEqual(0,result['details_fetched']);self.assertFalse(result['canonical_build'])

    def test_incomplete_or_contradictory_empty_layout_still_fails_closed(self):
        html=(ROOT/'tests/fixtures/hnx_disclosure_empty_aav_20261101.html').read_text(encoding='utf-8')
        variants=[html.replace('Không tìm thấy dữ liệu','Unknown error'),
                  html.replace('idCheckLoadTinCBTV','unknown_marker'),
                  html.replace('_tableDatas','other_table'),
                  html.replace("id='d_number_of_page'","id='other_page'"),
                  html.replace('Không tìm thấy dữ liệu','Không tìm thấy dữ liệu Tổng số 1 bản ghi'),
                  html.replace('</tbody>','<tr><td>unexpected data</td></tr></tbody>'),
                  html+'<div id="d_total_rec" class="_clsstotal_rec">Không tìm thấy dữ liệu</div>']
        for variant in variants:
            with self.subTest(variant=variant[-90:]),self.assertRaises(SourceLimitation):
                parse_search_page(variant,'AAV','UPCOM',1)

    def test_profile_requires_both_ticker_market_and_search_controls(self):
        self.assertEqual('NY',profile_context(profile(),'PVS','HNX'))
        with self.assertRaisesRegex(SourceLimitation,'CONTEXT'):
            profile_context(profile('ACV','UC'),'PVS','HNX')
        with self.assertRaisesRegex(SourceLimitation,'LAYOUT'):
            profile_context(profile().replace('txtTuNgayTinCB','other'),'PVS','HNX')

    def test_payload_matches_observed_public_ui_and_date_basis(self):
        q=parse_qs(search_payload('PVS','NY',2,'2019-01-31','2025-12-31').decode(),keep_blank_values=True)
        self.assertEqual(['31/01/2019'],q['pFromDate']);self.assertEqual(['31/12/2025'],q['pToDate'])
        self.assertEqual(["'CORPORATE_NEWS'"],q['pNhomTin']);self.assertEqual(['2'],q['pNumPage'])
        self.assertEqual(['20'],q['pNumRecord'])

    def test_parses_provider_id_and_request_without_inventing_permalink(self):
        rows,total=parse_search_page(listing(),'PVS','HNX',1)
        self.assertEqual(1,total);self.assertEqual('100',rows[0]['provider_article_id'])
        self.assertEqual('2019-09-24',rows[0]['publication_date_candidate'])
        self.assertEqual({'pArticlesID':'100','pFileAttach':'0'},rows[0]['detail_request']['form'])
        self.assertTrue(rows[0]['list_time_not_accepted_for_pit']);self.assertFalse(rows[0]['detail_content_fetched'])
        self.assertIsNone(rows[0]['timezone'])

    def test_shell_or_missing_total_is_not_empty_success(self):
        for html in ['<html>Enable Javascript</html>', listing().replace('Tổng số 1 bản ghi','')]:
            with self.assertRaises(SourceLimitation):parse_search_page(html,'PVS','HNX',1)

    def test_discovery_seals_raw_and_remains_discovery_only(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out'
            def factory(root,**kwargs):return Transport(root,[profile(),listing()],**kwargs)
            result=discover(SCOPE,'2019-01-31','2025-12-31',out,transport_factory=factory)
            self.assertEqual(2,result['network_requests']);self.assertEqual(1,result['discovered_article_ids'])
            self.assertTrue(result['checks'][0]['query_list_exhausted_within_filter'])
            self.assertFalse(result['canonical_build']);self.assertEqual(0,result['details_fetched'])
            manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
            for name,h in manifest['files'].items():self.assertEqual(h,hashlib.sha256((out/name).read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):discover(SCOPE,'2019-01-31','2025-12-31',out)

    def test_date_filter_violation_stops_before_next_ticker(self):
        with tempfile.TemporaryDirectory() as t:
            def factory(root,**kwargs):return Transport(root,[profile(),listing(timestamp='01/01/2026 09:00')],**kwargs)
            result=discover(SCOPE+[{'ticker':'ACV','exchange':'UPCOM'}],'2019-01-31','2025-12-31',Path(t)/'out',transport_factory=factory)
            self.assertEqual(2,result['network_requests'])
            self.assertIn('DATE_FILTER_NOT_HONORED',result['limitations'][0]['reason'])

    def test_repeated_page_detected(self):
        with tempfile.TemporaryDirectory() as t:
            def factory(root,**kwargs):return Transport(root,[profile(),listing(total=2),listing(total=2)],**kwargs)
            result=discover(SCOPE,'2019-01-31','2025-12-31',Path(t)/'out',transport_factory=factory)
            self.assertIn('REPEATED_PAGE',result['limitations'][0]['reason'])

    def test_small_budget_cannot_be_called_query_complete(self):
        with tempfile.TemporaryDirectory() as t:
            def factory(root,**kwargs):return Transport(root,[profile()],**kwargs)
            result=discover(SCOPE,'2019-01-31','2025-12-31',Path(t)/'out',max_requests=1,transport_factory=factory)
            self.assertEqual(1,result['network_requests']);self.assertTrue(result['limitations']);self.assertFalse(result['checks'])

    def test_dry_run_does_not_create_output_or_transport(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out'
            result=discover(SCOPE,'2019-01-31','2025-12-31',out,dry_run=True,transport_factory=lambda *a,**k:self.fail('network'))
            self.assertEqual('DRY_RUN',result['status']);self.assertFalse(out.exists())
            with self.assertRaises(ValueError):discover(SCOPE,'20190131','2025-12-31',out,dry_run=True)


if __name__ == '__main__':unittest.main()
