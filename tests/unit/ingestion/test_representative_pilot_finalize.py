import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "tmp"
TMP_ROOT.mkdir(exist_ok=True)

from delta_t1.ingestion.representative_pilot_finalize import _rule, load_qc_policy
from delta_t1.io import digest, encoded, write_json


class RepresentativePilotFinalizeTests(unittest.TestCase):
    def policy(self, run_id, raw_hash):
        return {
            "policy_id": "REPRESENTATIVE_PILOT_QC_V1",
            "source_run_id": run_id,
            "action": "EXCLUDE_EXACT_RAW_HASH_ONLY",
            "coverage_policy": {
                "primary_ohlcv": {"provider": "kbs", "minimum_years": 5,
                                  "required": True},
                "reference_limits_value": {
                    "provider": "cafef", "partial_source_qualified_allowed": True,
                    "required_nonempty": True,
                },
            },
            "rules": [["kbs", "AAA", "2020-01-02", raw_hash,
                       "PROVIDER_OHLC_INVARIANT_VIOLATION"]],
        }

    def test_exact_raw_hash_rule_matches_and_records_use(self):
        raw = {"t": "2020-01-02", "o": 2, "h": 1, "l": 0, "c": 1, "v": 1}
        key = ("kbs", "AAA", "2020-01-02", digest(encoded(raw)))
        rules = {key: "PROVIDER_OHLC_INVARIANT_VIOLATION"}
        used = set()
        self.assertEqual("PROVIDER_OHLC_INVARIANT_VIOLATION",
                         _rule(rules, used, "kbs", "AAA", "2020-01-02", raw))
        self.assertEqual({key}, used)

    def test_changed_raw_row_does_not_match_policy(self):
        original = {"t": "2020-01-02", "o": 2, "h": 1, "l": 0, "c": 1, "v": 1}
        changed = dict(original, c=0)
        key = ("kbs", "AAA", "2020-01-02", digest(encoded(original)))
        used = set()
        self.assertIsNone(_rule({key: "X"}, used, "kbs", "AAA", "2020-01-02", changed))
        self.assertFalse(used)

    def test_policy_is_bound_to_one_source_run(self):
        run_id = "representative-pilot-20260916T000000Z-1234abcd"
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            path = Path(temp) / "policy.json"
            write_json(path, self.policy(run_id, "a" * 64))
            _, _, rules = load_qc_policy(path, run_id)
            self.assertEqual(1, len(rules))
            with self.assertRaisesRegex(ValueError, "identity/action"):
                load_qc_policy(path, "representative-pilot-other")

    def test_duplicate_exact_hash_rule_is_refused(self):
        run_id = "representative-pilot-20260916T000000Z-1234abcd"
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            path = Path(temp) / "policy.json"
            policy = self.policy(run_id, "a" * 64)
            policy["rules"].append(list(policy["rules"][0]))
            write_json(path, policy)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_qc_policy(path, run_id)

    def test_wrong_provider_classification_is_refused(self):
        run_id = "representative-pilot-20260916T000000Z-1234abcd"
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as temp:
            path = Path(temp) / "policy.json"
            policy = self.policy(run_id, "a" * 64)
            policy["rules"][0][4] = "PROVIDER_PRICE_BAND_INVARIANT_VIOLATION"
            write_json(path, policy)
            with self.assertRaisesRegex(ValueError, "classification"):
                load_qc_policy(path, run_id)


if __name__ == "__main__":
    unittest.main()
