"""Date-only checks for the Stage B design (no forecasts, no outcomes)."""
import inspect
import unittest
import numpy as np
import pandas as pd
import longer_panel_stage_a_v1 as A
import longer_panel_stage_b_v1 as s
import longer_panel_analysis_stage_b_v1 as an


class StageBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchors = s.anchors(allow_unchecked=True)

    def test_scope_and_diwali_convention(self):
        from extended_validation import MAIN
        a = self.anchors
        for y in s.CAL_YEARS:
            self.assertEqual(set(a[a.year.eq(y)].family), set(A.SCOPE['Maharashtra']))
        main = a[a.role.eq('national_main')]
        self.assertEqual(len(main), len(s.CAL_YEARS))
        for r in main.itertuples():
            if r.year in MAIN:
                self.assertEqual(r.date, MAIN[r.year])

    def test_cases_cover_only_event_years_and_labels(self):
        ev = A.event_cases(self.anchors, s.EVENT_YEARS)
        self.assertEqual(set(ev.year), set(s.EVENT_YEARS))
        self.assertEqual(ev[['family', 'year']].drop_duplicates().shape[0], 15)
        self.assertTrue((pd.to_datetime(ev.date)-pd.to_datetime(ev.origin)).dt.days.eq(ev.horizon-1).all())
        self.assertFalse(ev.duplicated(A.KEY).any())

    def test_placebos_stay_in_year_and_off_true_windows(self):
        p = A.placebos(self.anchors)
        for r in p.itertuples():
            self.assertIn(abs(r.shift_days), (28, 35, 42)); self.assertEqual(pd.Timestamp(r.date).year, r.year)

    def test_frames_and_bound(self):
        A.ARMS = s.ARMS
        fc = A.frames(pd.date_range('2017-01-01', '2021-12-31'), 'Maharashtra', self.anchors, A.placebos(self.anchors))
        self.assertEqual(list(fc), s.ARMS)
        self.assertEqual(fc['day5'].loc['2019-10-27', 'Diwali_day'], 1.)
        self.assertEqual(fc['pooled_day5'].loc['2019-10-27', 'event_day'], 1.)
        s.bound(['2017-01-01', '2021-12-31'])
        with self.assertRaises(AssertionError):
            s.bound(['2016-12-31'])
        with self.assertRaises(AssertionError):
            s.bound(['2022-01-01'])

    def test_regression_reuse_changes_only_ledger_names(self):
        src = inspect.getsource(A.regression)
        self.assertEqual(src.count("'anchors_2020_2025.csv'"), 1)
        self.assertEqual(src.count("'placebo_anchors_2020_2025.csv'"), 1)

    def test_one_sided_sign_flip(self):
        self.assertAlmostEqual(an.one_sided(np.ones(5), +1), 1/32)
        self.assertAlmostEqual(an.one_sided(-np.ones(5), -1), 1/32)
        self.assertEqual(an.one_sided(-np.ones(5), +1), 1.0)

    def test_registered_prepare_requires_checked_calendar(self):
        t = pd.read_csv(A.ENTRIES, dtype=str).fillna('')
        t = t[t.state.eq('Maharashtra') & t.year.isin([str(y) for y in s.CAL_YEARS]) & t.date.ne('')]
        if (t.checked_by == '').any():
            with self.assertRaises(ValueError):
                s.anchors(allow_unchecked=False)


if __name__ == '__main__':
    unittest.main()
