import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.backtest.portfolio import weights


class PortfolioTests(unittest.TestCase):
    def test_inverse_volatility_weights_are_normalized(self):
        result = weights([{"security_id": "a", "vol": .1}, {"security_id": "b", "vol": .2}],
                         "inverse_volatility", "vol")
        self.assertAlmostEqual(sum(result.values()), 1)
        self.assertGreater(result["a"], result["b"])


if __name__ == "__main__":
    unittest.main()
