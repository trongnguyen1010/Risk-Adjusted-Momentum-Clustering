from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_target_documents import allowed_url,public_document_links,TargetDocumentTransport,validate_saved_public_article,ScopedPdfTransport
from delta_t1.ingestion.corporate_action_sources import SourceLimitation,sha
C=json.loads((ROOT/"configs/data/corporate_action_dtp_asg_documents_v1.json").read_bytes())
PDF='https://www.aseansc.com.vn/uploads/2021/12/TB-chao-ban-CP-ra-cong-chung.pdf'


class Response(io.BytesIO):
    def __init__(self,body,code=200):
        super().__init__(body);self.code=code;self.headers={"Content-Type":"application/pdf" if body.startswith(b'%PDF-') else "text/html"}


class Opener:
    def __init__(self,body=b'%PDF-1.4\npublic',code=200,error=None):self.body=body;self.code=code;self.error=error;self.calls=0
    def open(self,request,timeout):
        self.calls+=1
        if self.error:raise self.error
        return Response(self.body,self.code)


class TargetDocumentTests(unittest.TestCase):
    def transport(self,folder,opener,config=None):return TargetDocumentTransport(Path(folder),config or C,opener=opener,sleep=lambda _:None)
    def test_only_scoped_seeds_and_discovered_attachment_names_are_allowed(self):
        for u in [C['dtp_page'],C['asg_page'],C['asg_prospectus_copy'],PDF]:self.assertTrue(allowed_url(u,C))
        for u in [PDF.replace('2021/12','2024/01'),PDF.replace('TB-chao-ban-CP-ra-cong-chung','other'),PDF+'?download=1','https://hnx.vn/vi/ad/1','https://login.microsoftonline.com/','https://asgcorpn-my.sharepoint.com/a.pdf']:
            self.assertFalse(allowed_url(u,C))
    def test_credentials_redirect_helpers_and_path_traversal_are_not_allowed(self):
        for u in [PDF.replace('www.aseansc.com.vn','user@www.aseansc.com.vn'),PDF+'#fragment',PDF.replace('/uploads/','/uploads/../uploads/'),PDF.replace('/uploads/','/uploads/%2e%2e/uploads/'),PDF.replace('https:','http:')]:
            self.assertFalse(allowed_url(u,C))
    def test_link_extraction_preserves_unfollowed_sharepoint_and_filters_arbitrary_pdfs(self):
        html='<a href="/uploads/2021/12/TB-chao-ban-CP-ra-cong-chung.pdf">Thông báo</a><iframe src="/uploads/2021/12/other.pdf"></iframe><a href="https://asgcorpn-my.sharepoint.com/doc">Hồ sơ</a>'
        links=public_document_links(html,C['dtp_page'],C)
        self.assertEqual(3,len(links));self.assertEqual(1,sum(x['allowed_target_document'] for x in links))
    def test_pdf_bytes_and_hash_are_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            t=self.transport(f,Opener());body,receipt=t.fetch(PDF,binary=True)
            self.assertEqual(body,(Path(f)/receipt['path']).read_bytes());self.assertEqual(sha(body),receipt['source_hash'])
    def test_denied_requests_stop_host_without_retry(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=Opener(b'access denied',403);t=self.transport(f,opener)
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
            self.assertEqual(1,opener.calls)
    def test_challenge_page_is_not_a_public_document(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=Opener(b'<html>captcha verify you are human</html>');t=self.transport(f,opener)
            with self.assertRaises(SourceLimitation):t.fetch(C['asg_page'])
            self.assertTrue((Path(f)/'raw/response-0001.bin').exists())
    def test_redirect_is_not_followed(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=Opener(b'<html>redirect</html>',302);t=self.transport(f,opener)
            with self.assertRaises(SourceLimitation):t.fetch(C['asg_page'])
            self.assertEqual(1,opener.calls)
    def test_ssl_failure_is_reported_not_bypassed(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=Opener(error=URLError(ssl.SSLCertVerificationError('certificate verify failed')));t=self.transport(f,opener)
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
            self.assertEqual(1,opener.calls);self.assertIn('certificate',t.requests[0]['error'])
    def test_non_pdf_html_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            t=self.transport(f,Opener(b'<html>not a PDF</html>'))
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
    def test_policy_and_budget_relaxation_is_rejected(self):
        for key,value in [('tls_verification',False),('follow_redirects',True),('hnx_requests_allowed',True),('max_requests',7),('interval_seconds',.25)]:
            c=deepcopy(C);c[key]=value
            with self.assertRaises(ValueError):self.transport(ROOT/'tmp',Opener(),c)
    def test_disallowed_url_makes_no_network_attempt(self):
        opener=Opener();t=self.transport(ROOT/'tmp',opener)
        with self.assertRaises(SourceLimitation):t.fetch('https://hnx.vn/')
        self.assertEqual(0,opener.calls)
    def test_runner_refuses_overwrite_and_escaping_paths(self):
        spec=importlib.util.spec_from_file_location('target_docs_runner',ROOT/'scripts/collect_dtp_asg_documents_v1.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with self.assertRaises(FileExistsError):runner.run(ROOT,True)
        with self.assertRaises(ValueError):runner.safe(ROOT,'../outside')

    def test_saved_public_article_is_hash_and_script_pinned_without_live_exception(self):
        follow=json.loads((ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json').read_bytes())
        scripts={
            'google-recaptcha-js':'<script id="google-recaptcha-js" src="https://www.google.com/recaptcha/api.js"></script>',
            'wpcf7-recaptcha-js-extra':'<script id="wpcf7-recaptcha-js-extra">var wpcf7_recaptcha = {};</script>',
            'wpcf7-recaptcha-js':'<script id="wpcf7-recaptcha-js" src="/contact-form-7/recaptcha/index.js"></script>'}
        body=(f'<h1>{follow["dtp_exact_h1"]}</h1>'+''.join(f'<a href="/uploads/2021/12/{name}">{name}</a>' for name in C['dtp_attachment_names'])+''.join(scripts.values())).encode()
        follow['dtp_saved_page_sha256']=sha(body)
        follow['contact_form_script_hashes']={k:sha(v.encode()) for k,v in scripts.items()}
        proof=validate_saved_public_article(body,C,follow)
        self.assertEqual(6,proof['marker_count']);self.assertEqual(2,len(proof['public_pdf_links']))
        self.assertFalse(proof['scripts_executed']);self.assertFalse(proof['default_live_access_challenge_gate_changed'])
        with self.assertRaises(ValueError):validate_saved_public_article(body+b'<!-- captcha -->',C,follow)
        with_widget=body+b'<div class="g-recaptcha" data-sitekey="public"></div>'
        c2=follow|{'dtp_saved_page_sha256':sha(with_widget)}
        with self.assertRaises(ValueError):validate_saved_public_article(with_widget,C,c2)
        changed=deepcopy(follow);changed['contact_form_script_hashes']['google-recaptcha-js']='bad'
        with self.assertRaises(ValueError):validate_saved_public_article(body,C,changed)
        t=self.transport(ROOT/'tmp',Opener())
        self.assertTrue(t.access_challenge(body.decode('utf-8-sig'),C['dtp_page']))

    def test_20mb_cap_is_only_for_exact_asg_pdf_and_restored_after_fetch(self):
        follow=json.loads((ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json').read_bytes())
        class InspectOpener(Opener):
            def open(self,request,timeout):
                response=super().open(request,timeout);base_read=response.read
                def read(n=-1):self.last_read_bound=n;return base_read(n)
                response.read=read;return response
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=InspectOpener();t=ScopedPdfTransport(Path(f),C,follow,opener=opener,sleep=lambda _:None)
            t.fetch(C['asg_prospectus_copy'],binary=True);self.assertEqual(20000001,opener.last_read_bound)
            self.assertEqual(5000000,t.max_bytes)
            t.fetch(PDF,binary=True);self.assertEqual(5000001,opener.last_read_bound)
            with self.assertRaises(SourceLimitation):t.fetch(C['dtp_page'])

    def test_followup_does_not_relax_http_denial_or_ssl_flags(self):
        follow=json.loads((ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json').read_bytes())
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as f:
            opener=Opener(b'access denied',403);t=ScopedPdfTransport(Path(f),C,follow,opener=opener,sleep=lambda _:None)
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
            with self.assertRaises(SourceLimitation):t.fetch(PDF,binary=True)
            self.assertEqual(1,opener.calls)

    def test_exact_prospectus_still_has_a_hard_64mb_ceiling(self):
        follow=json.loads((ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json').read_bytes())
        follow['one_asg_prospectus_max_bytes']=64000001
        with self.assertRaises(ValueError):ScopedPdfTransport(ROOT/'tmp',C,follow,opener=Opener(),sleep=lambda _:None)

    def test_head_denial_redirect_or_oversize_never_starts_pdf_get(self):
        spec=importlib.util.spec_from_file_location('size_bound_runner',ROOT/'scripts/fetch_asg_prospectus_by_length_v1.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        for status,length in [(403,'100'),(302,'100'),(200,'64000001')]:
            with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
                response=Response(b'',status);response.headers={'Content-Type':'application/pdf','Content-Length':length}
                opener=Opener();opener.open=lambda *args,**kwargs:response
                with patch.object(runner,'build_opener',return_value=opener),patch.object(runner,'ScopedPdfTransport') as transport,patch('sys.stdout',new=io.StringIO()):
                    runner.run(Path(folder)/'new',True)
                transport.assert_not_called()
                summary=json.loads((Path(folder)/'new/summary.json').read_bytes())
                self.assertEqual('PARTIAL',summary['status']);self.assertEqual(1,summary['network_request_attempts'])


if __name__=='__main__':unittest.main()
