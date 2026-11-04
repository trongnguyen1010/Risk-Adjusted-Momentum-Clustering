import contextlib
import hashlib
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion import vnstock_environment_diagnostic as module


class EnvironmentDiagnosticTests(unittest.TestCase):
    def test_status_is_allowlisted_device_hashed_and_arbitrary_fields_dropped(self):
        secret = "API_SECRET_MUST_NOT_APPEAR"
        device = "example-device-id"
        result = module.summarize_status({"authenticated": True, "tier": "free",
            "device_id": device, "api_key": secret, "server_message": secret})
        self.assertEqual(hashlib.sha256(device.encode()).hexdigest(), result["device_id_sha256"])
        self.assertNotIn(device, str(result))
        self.assertNotIn(secret, str(result))
        self.assertTrue(result["authenticated"])

    def test_url_credentials_paths_and_profile_are_not_exported(self):
        result = module.summarize_environment({"api_base": "https://SECRET:KEY@vnstocks.com/api?key=SECRET",
            "profile": "SECRET", "state_dir": None, "api_key": "SECRET"})
        self.assertEqual("vnstocks.com", result["api_base_host"])
        self.assertFalse(result["profile_is_default"])
        self.assertNotIn("SECRET", str(result))
        self.assertEqual("OTHER_OR_UNAVAILABLE", module.summarize_environment({"api_base": "https://secret.other"})["api_base_host"])

    def test_reads_environment_and_status_once_without_login_or_calendar(self):
        calls = []
        def environment():
            calls.append("environment")
            print("SDK_SECRET_LOG")
            return {"api_base": "https://vnstocks.com"}
        def status():
            calls.append("status")
            print("SDK_SECRET_LOG")
            return {"tier": "guest", "authenticated": False}
        def forbidden():
            self.fail("login/calendar must never be called")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            report = module.inspect_sdk(SimpleNamespace(environment=environment, status=status,
                                                        login=forbidden, calendar=forbidden))
        self.assertEqual(["environment", "status"], calls)
        self.assertEqual("", stdout.getvalue())
        self.assertFalse(report["status"]["authenticated"])

    def test_error_text_action_traceback_and_unrecognized_codes_are_not_retained(self):
        class EntitlementError(Exception):
            code = "VNSTOCK_AUTH_DEVICE_LIMIT"
            action = "SECRET"
        result = module.safe_error(EntitlementError("SECRET"))
        self.assertEqual("VNSTOCK_AUTH_DEVICE_LIMIT", result["sdk_code"])
        self.assertNotIn("SECRET", str(result))
        error = RuntimeError("SECRET")
        error.code = "VNSTOCK_SECRET_MUST_NOT_APPEAR"
        self.assertEqual("UNRECOGNIZED_ERROR", module.safe_error(error)["sdk_code"])

    def test_wrong_sdk_version_stops_before_import_without_secret_access(self):
        with patch.object(module.importlib.metadata, "version", return_value="4.0.7"):
            result = module.worker()
        self.assertEqual("SDK_VERSION_MISMATCH_NO_IMPORT", result["status"])
        self.assertEqual(0, result["explicit_login_calls"])
        self.assertEqual(0, result["calendar_calls"])
        self.assertFalse(result["secret_read"])

    def test_current_sdk_worker_only_uses_account_inspection_api(self):
        calls = []
        def forbidden(*args, **kwargs):
            self.fail("Worker must not login or collect")
        account = SimpleNamespace(environment=lambda: (calls.append("env") or {}),
                                  status=lambda: (calls.append("status") or {"tier": "guest"}))
        sdk = SimpleNamespace(account=account, login=forbidden, Reference=forbidden)
        with (patch.object(module.importlib.metadata, "version", return_value="5.2.1"),
              patch.dict(sys.modules, {"vnstock": sdk})):
            result = module.worker()
        self.assertEqual(["env", "status"], calls)
        self.assertEqual("READ_ONLY_CHECK_RETURNED", result["status"])
        self.assertEqual(0, result["calendar_calls"])
        self.assertEqual(0, result["explicit_login_calls"])
        self.assertIn("account_status", result)
        self.assertFalse(result["account_status"]["authenticated"])
        self.assertEqual("guest", result["account_status"]["tier"])

    def test_bad_shapes_do_not_expand_sdk_payload(self):
        self.assertEqual("UNEXPECTED_ACCOUNT_STATUS_SHAPE", module.summarize_status("SECRET")["status"])
        self.assertEqual("UNEXPECTED_ENVIRONMENT_SHAPE", module.summarize_environment(["SECRET"])["status"])

    def test_unavailable_api_base_is_not_evidence_of_wrong_server(self):
        missing = module.summarize_environment({"profile": "SDK_DEFAULT_PROFILE"})
        empty = module.summarize_environment({"api_base": None})
        self.assertFalse(missing["api_base_field_present"])
        self.assertTrue(empty["api_base_field_present"])
        self.assertTrue(empty["api_base_is_empty"])
        self.assertEqual("hq.vnstocks.com", module.summarize_environment({"api_base": "https://hq.vnstocks.com"})["api_base_host"])


if __name__ == "__main__":
    unittest.main()
