"""Date-only and synthetic checks for the new-states study (no forecasts, no outcomes)."""
import unittest
import numpy as np
import pandas as pd
import new_states_v1 as s
import longer_panel_stage_a_v1 as A
import new_states_analysis_v1 as an


class NewStatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = s.anchors()

    def test_patch_points_shared_code_at_new_states(self):
        import forecasting, extended_validation, robust_baselines
        self.assertEqual(list(forecasting.STATES), list(s.NEW_STATES))
        self.assertEqual(list(robust_baselines.STATES), list(s.NEW_STATES))
        self.assertEqual(list(extended_validation.STATES), list(s.NEW_STATES))
        self.assertEqual(list(robust_baselines.load_data('latest').columns), list(s.NEW_STATES))

    def test_scope_and_years(self):
        for st, fams in s.SCOPE.items():
            self.assertTrue(set(self.a[self.a.state == st].family) <= set(fams))
        self.assertEqual(set(self.a.year), set(s.CAL_YEARS))

    def test_cases(self):
        ev, dropped = s.event_cases(self.a)
        self.assertEqual(set(ev.year), set(s.EVENT_YEARS))
        self.assertTrue((pd.to_datetime(ev.date)-pd.to_datetime(ev.origin)).dt.days.eq(ev.horizon-1).all())
        self.assertFalse(ev.duplicated(A.KEY).any())
        self.assertGreaterEqual(ev[['family', 'year']].drop_duplicates().shape[0], 40)

    def test_frames_new_state(self):
        fake = A.placebos(self.a)
        fc = A.frames(pd.date_range('2015-01-01', '2025-12-31'), 'Telangana', self.a, fake)
        d = self.a[(self.a.state == 'Telangana') & (self.a.family == 'Ganesh_Chaturthi')].date.iloc[0]
        self.assertEqual(fc['day5'].loc[d, 'Ganesh_Chaturthi_day'], 1.)
        self.assertEqual(fc['pooled_day5'].loc[d, 'event_day'], 1.)
        self.assertEqual(list(fc['calendar'].columns), list(fc['day5'].columns[:13]))

    def test_regression_reuse(self):
        import inspect
        src = inspect.getsource(A.regression)
        self.assertEqual(src.count("'anchors_2020_2025.csv'"), 1)
        self.assertEqual(src.count("'placebo_anchors_2020_2025.csv'"), 1)

    def test_signflip_synthetic(self):
        rng = np.random.default_rng(1)
        self.assertLess(an.signflip(rng.normal(0.5, 1, 40), +1, draws=20000), 0.05)
        self.assertGreater(an.signflip(rng.normal(0, 1, 40), +1, draws=20000), 0.01)
        self.assertGreater(an.signflip(-np.ones(10), +1, draws=20000), 0.99)

    def test_bound(self):
        s.bound(['2015-01-01', '2025-12-31'])
        with self.assertRaises(AssertionError):
            s.bound(['2014-12-31'])


if __name__ == '__main__':
    unittest.main()
