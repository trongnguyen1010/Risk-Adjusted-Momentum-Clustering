import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.sources.cafef import CafeFSource
from delta_t1.ingestion.sources.vietfin import VietFinSource


class SourceBoundaryTests(unittest.TestCase):
    def test_unverified_sources_fail_closed(self):
        for source in (CafeFSource(), VietFinSource()):
            with self.assertRaisesRegex(ValueError, "not verified"):
                source.acquire({"symbol": "FPT"})


if __name__ == "__main__":
    unittest.main()
