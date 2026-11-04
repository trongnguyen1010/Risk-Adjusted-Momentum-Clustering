import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("local_vci_runner", ROOT / "scripts/run_vci_calendar_local_v1.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class LocalRunnerTests(unittest.TestCase):
    def test_fixed_device_store_and_explicit_stdin_key_do_not_modify_parent_environment(self):
        parent = {"VNSTOCK_API_KEY": "SECRET", "KEEP": "unchanged"}
        home = Path("data/corporate_actions/private/vnstock_vci_local_v1")
        first = runner.child_environment(parent, home)
        second = runner.child_environment(parent, home)
        self.assertNotIn("VNSTOCK_API_KEY", first)
        self.assertEqual(str(home.resolve()), first["VNSTOCK_HOME"])
        self.assertEqual(first["VNSTOCK_HOME"], second["VNSTOCK_HOME"])
        self.assertEqual("SECRET", parent["VNSTOCK_API_KEY"])
        self.assertEqual("unchanged", first["KEEP"])

    def test_custom_server_or_profile_is_not_silently_changed(self):
        for name in ("VNSTOCK_API_BASE", "VNSTOCK_PROFILE"):
            with self.assertRaisesRegex(ValueError, "REQUIRES_REVIEW"):
                runner.child_environment({name: "custom"}, Path("state"))

    def test_progress_filter_retains_expected_events_and_drops_sdk_or_secret_payload(self):
        expected = {"event": "QUERY_SAVED", "month": "2019-01", "rows": 4, "completed": 1, "total": 84}
        self.assertEqual(expected, runner.progress_line(json.dumps(expected), {"2019-01"}))
        for value in ["SECRET", json.dumps({"api_key": "SECRET"}),
                      json.dumps(dict(expected, rows="SECRET")),
                      json.dumps(dict(expected, month="SECRET")),
                      json.dumps(dict(expected, status="SECRET")),
                      json.dumps(dict(expected, device_id="SECRET"))]:
            self.assertIsNone(runner.progress_line(value, {"2019-01"}))

    def test_bundle_pin_and_file_hashes_are_verified_before_sdk_or_key_access(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            values = [{"start": "2019-01-31"}, {"securities": []}, {"gate": "fixture"}]
            for name, value in zip(("plan.json", "scope.json", "pilot_gate.json"), values):
                (p / name).write_text(json.dumps(value), encoding="utf-8")
            manifest = {"files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir()}}
            body = json.dumps(manifest).encode();(p / "manifest.json").write_bytes(body)
            pin = hashlib.sha256(body).hexdigest()
            with patch.object(runner, "validate_inputs") as validate:
                self.assertEqual(values, runner.validate_bundle(p, pin))
                validate.assert_called_once_with(*values)
            (p / "scope.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "FILE_CHANGED"):
                runner.validate_bundle(p, pin)
            with self.assertRaisesRegex(ValueError, "MANIFEST_CHANGED"):
                runner.validate_bundle(p, "0" * 64)

    def test_check_does_not_read_key_or_import_sdk(self):
        with (patch.object(sys, "argv", ["local", "--check"]),
              patch.object(runner, "validate_bundle", return_value=({}, {}, {})),
              patch.object(runner.importlib.metadata, "version", return_value="5.2.1"),
              patch.object(runner.getpass, "getpass", side_effect=AssertionError("must not request key")),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(0, runner.main())
        self.assertIn("LOCAL_CHECK_PASS_AUTH_NOT_TESTED", output.getvalue())

    def test_wrong_version_stops_before_key_prompt_or_device_registration(self):
        with (patch.object(sys, "argv", ["local"]),
              patch.object(runner, "validate_bundle", return_value=({}, {}, {})),
              patch.object(runner.importlib.metadata, "version", return_value="4.0.7"),
              patch.object(runner.getpass, "getpass", side_effect=AssertionError("must not request key")),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(2, runner.main())
        self.assertIn("SDK_VERSION_MISMATCH", output.getvalue())

    def test_missing_sdk_reports_install_needed_without_key_prompt(self):
        with (patch.object(sys, "argv", ["local", "--check"]),
              patch.object(runner, "validate_bundle", return_value=({}, {}, {})),
              patch.object(runner.importlib.metadata, "version", side_effect=runner.importlib.metadata.PackageNotFoundError),
              patch.object(runner.getpass, "getpass", side_effect=AssertionError("must not request key")),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(2, runner.main())
        self.assertIn("SDK_NOT_INSTALLED_RUN_PIP_COMMAND", output.getvalue())


if __name__ == "__main__":
    unittest.main()
