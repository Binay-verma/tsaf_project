"""Date-only checks for the foundation extension (no forecasts)."""
import unittest
import pandas as pd
import longer_panel_stage_a_v1 as A
import longer_panel_foundation_v1 as s
from longer_panel_foundation_analysis_v1 import stored


class FoundationTests(unittest.TestCase):
    def test_cases_are_stage_a_subsets(self):
        for cohort, (source, years, _) in s.COHORTS.items():
            c = s.cohort_cases(cohort)
            self.assertEqual(sorted(c.year.unique()), years)
            full = pd.read_csv(s.STAGE_A/source/'primary_cases.csv')
            self.assertEqual(len(c), int(full.year.isin(years).sum()))

    def test_reproduction_cases_exist_in_store(self):
        c = s.cohort_cases('reproduce_2024'); st = stored('event_window')
        for m in s.MODELS:
            for arm in s.REFERENCE_ARMS:
                x = st[st.model.eq(m) & st.arm.eq(arm) & st.year.eq(2024)]
                self.assertTrue(A.same(c, x), (m, arm))

    def test_stored_later_years_cover_stage_a(self):
        for source in ['event_window', 'ordinary']:
            st = stored(source); full = pd.read_csv(s.STAGE_A/source/'primary_cases.csv')
            late = full[full.year.isin([2024, 2025])]
            for m in s.MODELS:
                for arm in s.ALL_ARMS:
                    self.assertTrue(A.same(late, st[st.model.eq(m) & st.arm.eq(arm) & st.year.isin([2024, 2025])]), (source, m, arm))


if __name__ == '__main__':
    unittest.main()
