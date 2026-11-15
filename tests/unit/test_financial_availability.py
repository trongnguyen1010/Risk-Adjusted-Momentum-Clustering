import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'web' / 'backend'))
from app.availability import FinancialAvailability  # noqa: E402
from app.repository import MissingData  # noqa: E402

CSV = ('ticker,fiscal_year,publication_date,date_source,report_type,provider_report_id,usable_from_date,status,'
       'crawl_status,non_december_fye\n'
       'AAA,2021,2022-06-30,LAG_RULE,,,2022-07-01,OK,DONE,\n'
       'AAA,2024,2025-03-17,CAFEF_DISCLOSURE,HK,x1,2025-03-18,OK,DONE,\n'
       'BBB,2024,2025-06-30,LAG_RULE,,,2025-07-01,OK,DONE,\n'
       'CCC,2025,2026-03-20,CAFEF_DISCLOSURE,HK,x2,,CALENDAR_PENDING,DONE,\n')


class FinancialAvailabilityTests(unittest.TestCase):
    def build(self, sha=None):
        root = Path(tempfile.mkdtemp())
        (root / 'configs/product').mkdir(parents=True)
        (root / 'data').mkdir()
        (root / 'data/availability.csv').write_bytes(CSV.encode())
        digest = sha or hashlib.sha256(CSV.encode()).hexdigest()
        (root / 'configs/product/financial_availability_v1.json').write_text(json.dumps(
            dict(version='t', file='data/availability.csv', file_sha256=digest, rule='r')), encoding='utf-8')
        return FinancialAvailability.from_config(root)

    def test_summary_counts_sources_per_year(self):
        out = self.build().summary({2021: ['AAA'], 2024: ['AAA', 'BBB', 'ZZZ'], 2025: ['CCC']})
        years = {y['year']: y for y in out['years']}
        self.assertEqual(years[2021]['lag_rule'], 1)
        self.assertEqual((years[2024]['cafef'], years[2024]['lag_rule'], years[2024]['missing']), (1, 1, 1))
        self.assertEqual(years[2025]['calendar_pending'], 1)

    def test_checksum_mismatch_fails_closed(self):
        with self.assertRaises(MissingData):
            self.build(sha='0' * 64)


if __name__ == '__main__':
    unittest.main()
