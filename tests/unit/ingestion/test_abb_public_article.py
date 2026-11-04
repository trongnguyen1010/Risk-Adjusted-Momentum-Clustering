import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/"src"))
from delta_t1.ingestion.abb_public_article import ARTICLE_URL, ARTICLE_TITLE, BENIGN_HELPER_SHA256, classify_article, AbbPublicArticleTransport
from delta_t1.ingestion.corporate_action_sources import PublicTransport, SourceLimitation, sha

HELPER = ''' var verifyCallback = function (response) { document.getElementById("btn-register").disabled = false; document.getElementById("btn-register").style.opacity = "1"; document.getElementById("is_true").setAttribute('value', 1); }; var verifyExpriteCallback = function (response) { document.getElementById("btn-register").disabled = true; document.getElementById("btn-register").style.opacity = "0.5"; document.getElementById("is_true").setAttribute('value', 0); }; var onloadCallback = function () { grecaptcha.render('g-recaptcha', { 'sitekey': '', 'callback': verifyCallback, 'expired-callback': verifyExpriteCallback, }); }; '''


def public_page(extra=""):
    return f'<html><head><script>{HELPER}</script></head><body><h1>{ARTICLE_TITLE}</h1><div id="pageNewsDetail"><div class="dynamic-content">Mã cổ phiếu: ABB Giá chào bán: 10.000 đồng/cổ phiếu Ngày đăng ký cuối cùng: 10/11/2021 Tỷ lệ thực hiện quyền: 5:1</div></div>{extra}</body></html>'


class Response(io.BytesIO):
    def __init__(self, body, code):super().__init__(body);self.code=code;self.headers={"Content-Type":"text/html"}


class Opener:
    def __init__(self, body, code=200):self.body=body;self.code=code;self.calls=0
    def open(self, request, timeout):self.calls+=1;return Response(self.body.encode(),self.code)


class AbbAccessTests(unittest.TestCase):
    def test_only_pinned_inert_script_in_complete_article_is_a_false_positive(self):
        self.assertEqual(BENIGN_HELPER_SHA256,sha(HELPER.encode()))
        result=classify_article(public_page(),ARTICLE_URL)
        self.assertFalse(result["challenge"])
        self.assertEqual(2,result["marker_count"])
        self.assertTrue(classify_article(public_page().replace("var verifyCallback","var otherCallback"),ARTICLE_URL)["challenge"])
    def test_default_shared_transport_stays_conservative(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(PublicTransport(Path(folder)).access_challenge(public_page(),ARTICLE_URL))
    def test_active_widgets_or_any_extra_challenge_signal_remain_blocked(self):
        for extra in ['<div id="g-recaptcha"></div>','<div data-sitekey="key"></div>','<p>Verify you are human</p>',
                      '<script src="/cdn-cgi/challenge-platform/x"></script>','<input type="password">',
                      '<form action="/captcha"></form>','<!-- captcha challenge -->','<script>grecaptcha.execute()</script>']:
            with self.subTest(extra=extra):self.assertTrue(classify_article(public_page(extra),ARTICLE_URL)["challenge"])
    def test_other_urls_and_ambiguous_or_missing_article_are_blocked(self):
        for url in [ARTICLE_URL+"?x=1",ARTICLE_URL.replace("abbank.vn","www.abbank.vn"),"https://other.example/"]:
            self.assertTrue(classify_article(public_page(),url)["challenge"])
        for html in [public_page().replace('id="pageNewsDetail"','id="other"'),public_page().replace('Mã cổ phiếu: ABB','Mã cổ phiếu: BBB'),public_page('<div class="dynamic-content">Other</div>')]:
            self.assertTrue(classify_article(html,ARTICLE_URL)["challenge"])
    def test_http_deny_or_rate_limit_wins_even_with_full_article(self):
        for code in [401,403,429]:
            with self.subTest(code=code),tempfile.TemporaryDirectory() as folder:
                opener=Opener(public_page(),code);t=AbbPublicArticleTransport(Path(folder),opener=opener,sleep=lambda _:None,max_requests=2)
                with self.assertRaises(SourceLimitation):t.fetch(ARTICLE_URL)
                with self.assertRaises(SourceLimitation):t.fetch(ARTICLE_URL)
                self.assertEqual(1,opener.calls)
    def test_redirect_is_not_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            opener=Opener(public_page(),302);t=AbbPublicArticleTransport(Path(folder),opener=opener,sleep=lambda _:None)
            with self.assertRaises(SourceLimitation):t.fetch(ARTICLE_URL)
            self.assertEqual(1,opener.calls)
    def test_public_article_raw_bytes_are_not_sanitized_or_changed(self):
        with tempfile.TemporaryDirectory() as folder:
            body=public_page();t=AbbPublicArticleTransport(Path(folder),opener=Opener(body),sleep=lambda _:None)
            text,receipt=t.fetch(ARTICLE_URL)
            self.assertEqual(body,text)
            self.assertEqual(body.encode(),(Path(folder)/receipt["path"]).read_bytes())
            self.assertEqual(sha(body.encode()),receipt["source_hash"])
    def test_one_article_transport_refuses_other_paths_before_network(self):
        with tempfile.TemporaryDirectory() as folder:
            opener=Opener(public_page());t=AbbPublicArticleTransport(Path(folder),opener=opener,sleep=lambda _:None)
            with self.assertRaises(ValueError):t.fetch("https://abbank.vn/other.pdf")
            self.assertEqual(0,opener.calls)


if __name__=="__main__":unittest.main()
