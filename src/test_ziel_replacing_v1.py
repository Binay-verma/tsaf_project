"""Invariants for the Ziel replacing comparator. Feature and date checks only; no forecast outcomes."""
import unittest
import numpy as np
import pandas as pd
import ziel_replacing_v1 as z
from forecasting import load_data
from robust_baselines import design_frame
from festival_feature_experiment import input_pair


class ZielReplacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data('latest')
        cls.frames = {s: z.frames(cls.data.index, s) for s in ['Delhi', 'Karnataka', 'Maharashtra']}

    def test_synthetic_replacement(self):
        idx = pd.date_range('2024-01-01', periods=14)
        cal = pd.DataFrame({f'dow_{i}': (idx.dayofweek == i).astype(float) for i in range(7)}, index=idx)
        flag = pd.Series(0., index=idx); flag.iloc[[2, 6]] = 1.  # a Wednesday and a Sunday
        out = z.replace_with_sunday(cal, flag)
        self.assertEqual(out.iloc[2].tolist(), [0, 0, 0, 0, 0, 0, 1])
        self.assertTrue(out.iloc[6].equals(cal.iloc[6]))
        unchanged = [i for i in range(14) if i not in (2, 6)]
        self.assertTrue(out.iloc[unchanged].equals(cal.iloc[unchanged]))
        self.assertEqual(cal.iloc[2].tolist(), [0, 0, 1, 0, 0, 0, 0])

    def test_arm_shapes_and_onehot(self):
        for state, fc in self.frames.items():
            self.assertEqual(list(fc), z.ARMS)
            self.assertEqual(fc['sunday_day'].shape[1], 18)
            self.assertEqual(fc['pooled_day5'].shape[1], 18)
            self.assertEqual(list(fc['sunday_day'].columns[:13]), list(fc['calendar'].columns))
            self.assertTrue((fc['sunday_day'][z.DOW].sum(axis=1) == 1).all())
            self.assertTrue((fc['sunday_day'].iloc[:, 13:] == 0).all().all())

    def test_only_anchor_days_change_and_match_pooled_dates(self):
        anchors = pd.read_csv(z.ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv', parse_dates=['date'])
        for state, fc in self.frames.items():
            changed = (fc['sunday_day'].iloc[:, :13] != fc['calendar']).any(axis=1)
            event = fc['pooled_day5']['event_day'].astype(bool)
            self.assertFalse((changed & ~event).any())
            expected = event & (fc['calendar']['dow_6'] == 0)
            self.assertTrue(changed.equals(expected))
            own = set(anchors[anchors.state.eq(state)].date)
            self.assertEqual(set(event[event].index), own & set(fc['calendar'].index))
            self.assertTrue((fc['sunday_day'].loc[event, 'dow_6'] == 1).all())

    def test_reference_design_identical_to_parent_base(self):
        for state, fc in self.frames.items():
            for h in [1, 7, 14]:
                base, _ = design_frame(self.data[state], state, h, 'rich_calendar')
                shifted = fc['calendar'].reindex(self.data.index+pd.Timedelta(days=h-1))
                shifted.index = self.data.index
                cols = list(fc['calendar'].columns)
                np.testing.assert_array_equal(base[cols].to_numpy(), shifted.to_numpy())

    def test_inputs_ignore_future_targets(self):
        series = self.data['Karnataka']; origin = pd.Timestamp('2024-10-28')
        changed = series.copy(); changed.loc[origin:] = 1e12
        for arm in z.ARMS:
            a = input_pair(series, self.frames['Karnataka'][arm], origin)
            b = input_pair(changed, self.frames['Karnataka'][arm], origin)
            np.testing.assert_array_equal(a[0], b[0]); np.testing.assert_array_equal(a[1], b[1])

    def test_case_sets(self):
        for cohort, n in [('event_window', 528), ('ordinary', 216)]:
            c = z.cohort_cases(cohort)
            self.assertEqual(len(c), n)
            self.assertFalse(c.duplicated().any())
            d = pd.to_datetime(c.date)-pd.to_datetime(c.origin)
            self.assertTrue((d.dt.days == c.horizon-1).all())


if __name__ == '__main__':
    unittest.main()
