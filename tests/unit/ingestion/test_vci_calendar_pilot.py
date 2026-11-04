import json
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.vci_calendar_pilot import pilot, main, SDK_VERSION


class Frame:
    def __init__(self, rows=None, source="vci", columns=None):
        self.rows = rows if rows is not None else [{"symbol":"PVS","ex_right_date":"2024-11-13","record_date":"2024-11-14"}]
        self.columns = columns if columns is not None else ["symbol","ex_right_date","record_date"]
        self.attrs = {"source": source, "route": "reference.events.calendar"}
    def to_json(self, **kwargs):return json.dumps(self.rows)


class CalendarPilotTests(unittest.TestCase):
    def test_three_windows_are_bounded_and_exports_do_not_promote_pit_or_canonical(self):
        with tempfile.TemporaryDirectory() as t:
            calls=[];sleeps=[]
            def fetch(**kwargs):calls.append(kwargs);return Frame()
            out=Path(t)/'pilot';r=pilot(out,fetch,sleep=sleeps.append)
            self.assertEqual(3,len(calls));self.assertEqual([8,8],sleeps)
            self.assertEqual('2019-02-01',calls[0]['start'])
            self.assertEqual('PILOT_EXPORTS_READY_FOR_REVIEW',r['status'])
            self.assertEqual(0,r['hnx_requests']);self.assertFalse(r['canonical_build'])
            self.assertEqual('NOT_PROMOTED',r['pit_status']);self.assertEqual('NOT_INSTRUMENTED',r['underlying_http_count'])
            self.assertTrue((out/'manifest.json').is_file())
            self.assertEqual('2024-11-13',json.loads((out/'sdk_export_1.json').read_text())[0]['ex_right_date'])

    def test_error_stops_after_one_call_without_persisting_exception_message(self):
        for message in ['HTTP403 secret-key-value','HTTP429 secret-key-value','timeout secret-key-value']:
            with tempfile.TemporaryDirectory() as t:
                calls=[]
                def fetch(**kwargs):calls.append(kwargs);raise RuntimeError(message)
                out=Path(t)/'pilot';r=pilot(out,fetch)
                self.assertEqual(1,len(calls));self.assertEqual('STOPPED_SDK_ERROR_NO_RETRY',r['status'])
                self.assertTrue(all('secret-key-value' not in p.read_text() for p in out.iterdir()))

    def test_schema_and_source_mismatch_stop_and_retain_export(self):
        for frame in [Frame(source='hnx'),Frame(columns=['symbol'])]:
            with tempfile.TemporaryDirectory() as t:
                calls=[]
                def fetch(**kwargs):calls.append(kwargs);return frame
                out=Path(t)/'pilot';r=pilot(out,fetch)
                self.assertEqual(1,len(calls));self.assertTrue(r['status'].startswith('STOPPED_'))
                self.assertTrue((out/'sdk_export_1.json').is_file())

    def test_row_cap_is_a_stop_not_a_completeness_claim(self):
        with tempfile.TemporaryDirectory() as t:
            calls=[]
            def fetch(**kwargs):calls.append(kwargs);return Frame(rows=[{}]*20000)
            r=pilot(Path(t)/'pilot',fetch)
            self.assertEqual(1,len(calls));self.assertEqual('STOPPED_POSSIBLE_ROW_TRUNCATION',r['status'])

    def test_refuse_overwriting_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileExistsError):pilot(Path(t),lambda **kwargs:Frame())

    def invoke(self, out, fake, version=SDK_VERSION):
        stdout=io.StringIO()
        with (patch.object(sys,'argv',['pilot','--output',str(out)]),patch.object(sys,'stdin',io.StringIO('TOP_SECRET_API_KEY_123456')),
              patch.dict(sys.modules,{'vnstock':fake}),patch('delta_t1.ingestion.vci_calendar_pilot.importlib.metadata.version',return_value=version),contextlib.redirect_stdout(stdout)):
            code=main()
        return code,stdout.getvalue(),json.loads((out/'result.json').read_text(encoding='utf-8'))

    def test_login_exception_keeps_stage_http_status_and_redacts_key_before_retaining_message(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'pilot';calls=[]
            def login(secret):
                calls.append(secret)
                exc=RuntimeError('TOP_SECRET_API_KEY_123456 payload must never be exported');exc.status_code=401;raise exc
            code,stdout,r=self.invoke(out,SimpleNamespace(login=login))
            self.assertEqual(2,code);self.assertEqual(1,len(calls));self.assertEqual(0,r['logical_calls'])
            self.assertEqual('SDK_LOGIN',r['setup_diagnostic']['setup_stage'])
            self.assertEqual('RuntimeError',r['setup_diagnostic']['error_type']);self.assertEqual(401,r['setup_diagnostic']['http_status'])
            self.assertNotIn('TOP_SECRET',stdout)
            self.assertTrue(all('TOP_SECRET' not in p.read_text() for p in out.iterdir()))
            self.assertTrue(all('TOP_SECRET_API_KEY_123456 payload must never be exported' not in p.read_text() for p in out.iterdir()))
            self.assertIn('[KEY_REMOVED]',r['setup_diagnostic']['message_redacted'])

    def test_absent_login_is_diagnosed_without_retry_or_provider_calls(self):
        with tempfile.TemporaryDirectory() as t:
            code,_,r=self.invoke(Path(t)/'pilot',SimpleNamespace())
            self.assertEqual(2,code);self.assertEqual(0,r['logical_calls'])
            self.assertEqual('SDK_LOGIN',r['setup_diagnostic']['setup_stage']);self.assertEqual('login',r['setup_diagnostic']['missing_name'])

    def test_status_shape_and_guest_entitlement_stop_before_reference_initialization(self):
        for value,expected in [(None,'SDK_STATUS_SCHEMA_MISMATCH'),('text','SDK_STATUS_SCHEMA_MISMATCH'),({'tier':'guest'},'AUTHENTICATED_ACCOUNT_REQUIRED')]:
            with tempfile.TemporaryDirectory() as t:
                initialized=[]
                fake=SimpleNamespace(login=lambda key:True,status=lambda:value,Reference=lambda:initialized.append(True))
                code,_,r=self.invoke(Path(t)/'pilot',fake)
                self.assertEqual(2,code);self.assertEqual(expected,r['status']);self.assertFalse(initialized)

    def test_version_mismatch_retains_a_sealed_report_without_import_or_login(self):
        with tempfile.TemporaryDirectory() as t:
            code,_,r=self.invoke(Path(t)/'pilot',SimpleNamespace(),version='4.0.7')
            self.assertEqual(2,code);self.assertEqual('SDK_VERSION_MISMATCH',r['status'])
            self.assertEqual('4.0.7',r['setup_diagnostic']['installed_sdk_version'])

    def test_license_protocol_error_is_retained_and_secret_redacted(self):
        with tempfile.TemporaryDirectory() as t:
            class InternalError(Exception):
                code='VNSTOCK_AUTH_PROTOCOL';kind='internal';retryable=False
                message_en='License service returned unexpected response TOP_SECRET_API_KEY_123456'
                action_en='Update the library'
            def login(key):raise InternalError('TOP_SECRET_API_KEY_123456')
            _,stdout,r=self.invoke(Path(t)/'pilot',SimpleNamespace(login=login))
            detail=r['setup_diagnostic']
            self.assertEqual('VNSTOCK_AUTH_PROTOCOL',detail['sdk_code'])
            self.assertIn('License service',detail['message_redacted'])
            self.assertNotIn('TOP_SECRET_API_KEY_123456',str(r)+stdout)

    def test_old_501_pin_is_refused_without_login(self):
        with tempfile.TemporaryDirectory() as t:
            calls=[]
            _,_,r=self.invoke(Path(t)/'pilot',SimpleNamespace(login=lambda key:calls.append(key)),version='5.0.1')
            self.assertEqual('SDK_VERSION_MISMATCH',r['status']);self.assertFalse(calls)

    def test_export_containing_key_is_not_written(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'pilot'
            r=pilot(out,lambda **kwargs:Frame(rows=[{'secret':'TOP_SECRET_API_KEY_123456'}]),redact_key='TOP_SECRET_API_KEY_123456')
            self.assertEqual('STOPPED_SDK_ERROR_NO_RETRY',r['status']);self.assertEqual(1,r['logical_calls'])
            self.assertFalse((out/'sdk_export_1.json').exists())
            self.assertTrue(all('TOP_SECRET_API_KEY_123456' not in p.read_text() for p in out.iterdir()))


if __name__=='__main__':unittest.main()
