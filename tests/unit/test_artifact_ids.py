from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.ingestion.crawler import code_hash, crawl
from delta_t1.io import digest, encoded, write_json


class ArtifactIdTests(unittest.TestCase):
    def test_fixed_utc_datetime_and_token(self):
        at = datetime(2026, 9, 16, 4, 15, 30, tzinfo=timezone.utc)
        self.assertEqual("run-20260916T041530Z-a1b2c3d4",
                         new_artifact_id("run", at=at, token="a1b2c3d4"))

    def test_non_utc_datetime_converts_to_utc(self):
        at = datetime(2026, 9, 16, 11, 15, 30,
                      tzinfo=timezone(timedelta(hours=7)))
        self.assertEqual("run-20260916T041530Z-0123abcd",
                         new_artifact_id("run", at=at, token="0123abcd"))

    def test_naive_datetime_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            new_artifact_id("run", at=datetime(2026, 9, 16), token="0123abcd")

    def test_invalid_prefix_is_rejected(self):
        for prefix in ("Run", "run id", "run_id"):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                new_artifact_id(prefix, token="0123abcd")

    def test_invalid_token_is_rejected(self):
        for token in ("0123abc", "0123ABCDE", "0123abcg"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                new_artifact_id("run", token=token)

    def test_generated_id_matches_structure(self):
        self.assertRegex(new_artifact_id("vendor-pilot"),
                         re.compile(r"^vendor-pilot-\d{8}T\d{6}Z-[0-9a-f]{8}$"))

    def test_old_style_resume_id_remains_accepted(self):
        config = {"jobs": []}
        fingerprint = {"config": config, "csv_hashes": {}}
        old_id = "run-c10574e177a6"
        with tempfile.TemporaryDirectory() as temp:
            manifest_path = Path(temp) / "data/runs" / old_id / "manifest.json"
            write_json(manifest_path, {
                "run_id": old_id,
                "data_version": old_id,
                "config_hash": digest(encoded(fingerprint)),
                "code_hash": code_hash(),
                "jobs": {},
                "status": "running",
            })
            directory, manifest, _ = crawl(config, temp, resume=old_id)
        self.assertEqual(old_id, directory.name)
        self.assertEqual(old_id, manifest["run_id"])


if __name__ == "__main__":
    unittest.main()
