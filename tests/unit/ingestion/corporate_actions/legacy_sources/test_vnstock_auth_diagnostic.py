import base64
import io
import contextlib
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.vnstock_auth_diagnostic import diagnose, scrub


class AuthDiagnosticTests(unittest.TestCase):
    def test_known_key_encodings_urls_bearer_and_long_tokens_are_removed(self):
        key='TEST-PRIVATE-KEY-12345678/+=end'
        message=' '.join([key,quote(key,safe=''),base64.b64encode(key.encode()).decode(),
                          'https://service.example/path?token='+key,'Bearer ANOTHER_PRIVATE_TOKEN_12345678'])
        result=scrub(message,key)
        for token in [key,quote(key,safe=''),base64.b64encode(key.encode()).decode(),'ANOTHER_PRIVATE_TOKEN_12345678']:
            self.assertNotIn(token,result)
        self.assertNotIn('service.example',result)

    def test_internal_sdk_code_and_redacted_message_are_retained_after_one_login(self):
        calls=[];key='TEST-PRIVATE-KEY-12345678'
        class InternalError(Exception):
            code='VNSTOCK_INTERNAL_ERROR';kind='internal';status=None;retryable=False
            message_en='Storage failed for '+key
            action_en='Check credential storage. '
        def login(k):calls.append(k);print('SDK prints '+k);raise InternalError('hidden '+k)
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):result=diagnose(SimpleNamespace(login=login),key)
        self.assertEqual([key],calls);self.assertEqual('',stdout.getvalue())
        self.assertEqual('VNSTOCK_INTERNAL_ERROR',result['diagnostic']['sdk_code'])
        self.assertIn('Storage failed',result['diagnostic']['message_redacted'])
        self.assertNotIn(key,str(result));self.assertEqual(0,result['calendar_calls'])

    def test_auth_denial_is_not_retried(self):
        calls=[]
        class AuthError(Exception):
            code='VNSTOCK_AUTH_CREDENTIAL_INVALID';kind='auth';status=401;retryable=False
        def login(k):calls.append(k);raise AuthError('Invalid key')
        result=diagnose(SimpleNamespace(login=login),'test-key')
        self.assertEqual(1,len(calls));self.assertEqual(401,result['diagnostic']['http_status'])
        self.assertEqual(0,result['calendar_calls']);self.assertFalse(result['automatic_retry'])

    def test_command_or_quoted_secret_stops_without_auth_attempt(self):
        for key in ['', 'vnstock register --key xxx', '"quoted-key"']:
            calls=[];r=diagnose(SimpleNamespace(login=lambda k:calls.append(k)),key)
            self.assertEqual('KEY_INPUT_REVIEW_REQUIRED',r['status']);self.assertFalse(calls)

    def test_success_is_not_a_calendar_or_readiness_gate(self):
        result=diagnose(SimpleNamespace(login=lambda k:None),'valid-shape-key')
        self.assertEqual('LOGIN_RETURNED_WITHOUT_EXCEPTION_NOT_A_DATA_GATE',result['status'])
        self.assertEqual(0,result['calendar_calls'])
