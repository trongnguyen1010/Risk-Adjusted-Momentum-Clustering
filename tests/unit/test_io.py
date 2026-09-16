"""Tests for atomic file operations and Windows transient PermissionError retries."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.io import (
    REPLACE_BACKOFF_DELAYS,
    REPLACE_MAX_ATTEMPTS,
    atomic_write,
    read_json,
    write_json,
)


class AtomicWriteTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test-io-"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_immediate_success(self):
        """atomic_write succeeds on the first attempt without retrying."""
        target = self.test_dir / "file.txt"
        atomic_write(target, b"hello world")
        self.assertEqual(target.read_bytes(), b"hello world")
        leftovers = list(self.test_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])

    def test_immediate_success_overwriting_existing(self):
        """atomic_write atomically overwrites an existing file."""
        target = self.test_dir / "overwrite.txt"
        target.write_bytes(b"initial")
        atomic_write(target, b"updated")
        self.assertEqual(target.read_bytes(), b"updated")
        leftovers = list(self.test_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])

    @patch("delta_t1.io.time.sleep")
    def test_transient_permission_error_then_success(self, mock_sleep):
        """Simulate transient PermissionError on attempts 0 and 1, then success on attempt 2."""
        target = self.test_dir / "transient.txt"
        target.write_bytes(b"prior content")

        real_replace = os.replace
        calls = []

        def fake_replace(src, dst):
            calls.append((src, dst))
            if len(calls) < 3:
                raise PermissionError(13, "Access is denied")
            return real_replace(src, dst)

        with patch("delta_t1.io.os.replace", side_effect=fake_replace):
            atomic_write(target, b"new content")

        self.assertEqual(len(calls), 3)
        self.assertEqual(mock_sleep.call_args_list, [call(0.05), call(0.10)])
        self.assertEqual(target.read_bytes(), b"new content")
        leftovers = list(self.test_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])

    @patch("delta_t1.io.time.sleep")
    def test_persistent_permission_error_re_raised_after_bounded_retries(self, mock_sleep):
        """Persistent PermissionError across all 6 attempts is re-raised; sleep called 5 times."""
        target = self.test_dir / "persistent.txt"
        target.write_bytes(b"original content")

        attempts = []

        def failing_replace(src, dst):
            attempts.append((src, dst))
            raise PermissionError(13, "Access is denied")

        with patch("delta_t1.io.os.replace", side_effect=failing_replace):
            with self.assertRaises(PermissionError):
                atomic_write(target, b"unwritten content")

        self.assertEqual(len(attempts), REPLACE_MAX_ATTEMPTS)
        self.assertEqual(REPLACE_MAX_ATTEMPTS, 6)
        expected_sleeps = [call(d) for d in REPLACE_BACKOFF_DELAYS]
        self.assertEqual(mock_sleep.call_args_list, expected_sleeps)
        self.assertEqual(REPLACE_BACKOFF_DELAYS, (0.05, 0.10, 0.20, 0.40, 0.80))

    @patch("delta_t1.io.time.sleep")
    def test_destination_remains_intact_when_replace_never_succeeds(self, _mock_sleep):
        """Existing destination file remains untouched when replace persistently fails."""
        target = self.test_dir / "intact.txt"
        target.write_bytes(b"pristine content")

        with patch("delta_t1.io.os.replace", side_effect=PermissionError(13, "Access is denied")):
            with self.assertRaises(PermissionError):
                atomic_write(target, b"corrupted attempt")

        self.assertEqual(target.read_bytes(), b"pristine content")

    @patch("delta_t1.io.time.sleep")
    def test_tempfile_cleanup_on_replace_failure(self, _mock_sleep):
        """Temporary file is cleaned up in finally even if os.replace fails persistently."""
        target = self.test_dir / "target.txt"

        with patch("delta_t1.io.os.replace", side_effect=PermissionError(13, "Access is denied")):
            with self.assertRaises(PermissionError):
                atomic_write(target, b"some data")

        leftovers = list(self.test_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])

    def test_non_permission_error_is_not_retried(self):
        """Errors other than PermissionError (e.g. OSError) are raised immediately without retry."""
        target = self.test_dir / "target.txt"
        calls = []

        def other_error(src, dst):
            calls.append(src)
            raise OSError("Some other OS error")

        with patch("delta_t1.io.os.replace", side_effect=other_error):
            with self.assertRaises(OSError):
                atomic_write(target, b"data")

        self.assertEqual(len(calls), 1)
        leftovers = list(self.test_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
