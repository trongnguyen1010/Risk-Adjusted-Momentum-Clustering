import unittest

from delta_t1.ingestion.m1_scale_quality import _five_calendar_years, _three_calendar_years


class M1ScaleQualityTests(unittest.TestCase):
    def test_calendar_year_coverage_is_not_approximated_by_row_count(self):
        self.assertTrue(_three_calendar_years("2021-09-15", "2024-09-15"))
        self.assertFalse(_three_calendar_years("2021-09-16", "2024-09-15"))
        self.assertTrue(_five_calendar_years("2020-02-29", "2025-02-28"))
        self.assertFalse(_five_calendar_years("2020-03-01", "2025-02-28"))


if __name__ == "__main__":
    unittest.main()
