import unittest
import subprocess
import sys
from pathlib import Path

class TestAssessmentBuildCli(unittest.TestCase):
    def test_cli_help(self):
        res = subprocess.run(
            [sys.executable, "scripts/build_investment_assessment_v1.py", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Build Investment Assessment", res.stdout)

    def test_cli_missing_input_fails_gracefully(self):
        res = subprocess.run(
            [
                sys.executable,
                "scripts/build_investment_assessment_v1.py",
                "--indicators-db", "non_existent_file.sqlite",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Không tìm thấy", res.stderr)

if __name__ == "__main__":
    unittest.main()
