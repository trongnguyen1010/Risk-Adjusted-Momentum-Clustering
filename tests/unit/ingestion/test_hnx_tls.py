import json
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.hnx_tls import validated_hnx_context
from delta_t1.ingestion.corporate_action_sources import SourceLimitation


class Context:
    def __init__(self):
        self.verify_mode=ssl.CERT_REQUIRED;self.check_hostname=True;self.verify_flags=557088;self.loaded=[]
    def get_ca_certs(self,binary_form=False):
        return [ssl.PEM_cert_to_DER_cert((ROOT/'tests/fixtures/hnx_tls/globalsign_root_r3.pem').read_text())]
    def load_verify_locations(self,**kwargs):self.loaded.append(kwargs)
    def cert_store_stats(self):return {'x509_ca':1+len(self.loaded)}


def project(root):
    for name in ['hnx_tls_chain_v1.json','certificates/globalsign_gcc_r3_ev_tls_ca_2025.pem']:
        target=root/'configs/data'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'configs/data'/name,target)


def success(command,**kwargs):return subprocess.CompletedProcess(command,0,'intermediate: OK','')


class HnxTlsTests(unittest.TestCase):
    def test_intermediate_loaded_only_after_offline_validation_to_existing_root(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);project(root);context=Context();calls=[]
            def checked(command,**kwargs):
                self.assertFalse(context.loaded);calls.append(command);return success(command,**kwargs)
            out=root/'check';actual,report=validated_hnx_context(root,out,context=context,openssl_binary='openssl',run=checked)
            self.assertIs(actual,context);self.assertEqual('VALIDATED',report['status'])
            self.assertEqual(557088,context.verify_flags);self.assertTrue(context.check_hostname);self.assertEqual(ssl.CERT_REQUIRED,context.verify_mode)
            self.assertFalse(report['new_root_trust']);self.assertEqual(0,report['network_requests'])
            self.assertIn('-x509_strict',calls[0]);self.assertIn('-no-CAstore',calls[0]);self.assertEqual(1,len(context.loaded))

    def test_failed_signature_or_expiry_validation_adds_no_trust(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);project(root);context=Context()
            def failed(command,**kwargs):return subprocess.CompletedProcess(command,2,'','certificate signature failure')
            with self.assertRaisesRegex(SourceLimitation,'OFFLINE_CHAIN'):
                validated_hnx_context(root,root/'check',context=context,openssl_binary='openssl',run=failed)
            self.assertFalse(context.loaded);self.assertEqual('BLOCKED',json.loads((root/'check/result.json').read_text())['status'])

    def test_missing_baseline_root_does_not_install_a_new_root(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);project(root);context=Context();context.get_ca_certs=lambda **kw:[]
            with self.assertRaisesRegex(SourceLimitation,'NOT_ALREADY_TRUSTED'):
                validated_hnx_context(root,root/'check',context=context,openssl_binary='openssl',run=lambda *a,**k:self.fail('verify invoked'))
            self.assertFalse(context.loaded)

    def test_corruption_or_second_certificate_cannot_be_loaded(self):
        for append in [b'corrupt', (ROOT/'tests/fixtures/hnx_tls/globalsign_root_r3.pem').read_bytes()]:
            with tempfile.TemporaryDirectory() as t:
                root=Path(t);project(root);context=Context()
                path=root/'configs/data/certificates/globalsign_gcc_r3_ev_tls_ca_2025.pem';path.write_bytes(path.read_bytes()+append)
                with self.assertRaises(SourceLimitation):validated_hnx_context(root,root/'check',context=context,openssl_binary='openssl',run=success)
                self.assertFalse(context.loaded)

    def test_unverified_baseline_context_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);project(root);context=Context();context.check_hostname=False
            with self.assertRaisesRegex(SourceLimitation,'NOT_STRICT'):
                validated_hnx_context(root,root/'check',context=context,openssl_binary='openssl',run=success)
            self.assertFalse(context.loaded)

    def test_timeout_or_missing_verifier_blocks_and_preserves_report(self):
        for missing in [True,False]:
            with tempfile.TemporaryDirectory() as t:
                root=Path(t);project(root);context=Context()
                with patch('delta_t1.ingestion.hnx_tls.shutil.which',return_value=None):
                    def timeout(*a,**kw):raise subprocess.TimeoutExpired('openssl',15)
                    with self.assertRaises(SourceLimitation):
                        validated_hnx_context(root,root/'check',context=context,openssl_binary=None if missing else 'openssl',run=timeout)
                self.assertFalse(context.loaded);self.assertTrue((root/'check/result.json').is_file())


if __name__=='__main__':unittest.main()
