"""Leakage and negative-control checks for the new exploratory experiment."""
import json
import unittest
import numpy as np
import pandas as pd
from calendar_controls import (ROOT, STATES, anchors, covariates, placebo_shifts,
                               train_predict, window_dates)


class ControlChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT/'results/calendar_controls_v1/protocol.json').read_text())
        cls.index = pd.date_range('2019-01-01', '2025-12-31')
        cls.frames, cls.event = covariates(cls.index, 'Karnataka', cls.protocol)
        cls.y = pd.Series(100 + np.sin(np.arange(len(cls.index))/10), index=cls.index)

    def test_future_outcomes_cannot_change_earlier_forecast(self):
        origins = pd.date_range('2024-01-01', periods=3)
        changed = self.y.copy()
        changed.loc[origins[0]:] = 1e9
        for horizon in [1, 7, 14]:
            a, _, _ = train_predict(self.y, self.frames['regional_7'], horizon, 2024, origins[:1])
            b, _, _ = train_predict(changed, self.frames['regional_7'], horizon, 2024, origins[:1])
            np.testing.assert_allclose(a, b, atol=0, rtol=0)

    def test_missing_labels_are_not_fitted_and_purge_is_strict(self):
        y = self.y.copy()
        y.loc['2023-12-31'] = np.nan
        _, _, log = train_predict(y, self.frames['regional_window'], 14, 2024,
                                  pd.date_range('2024-01-01', periods=1))
        self.assertLess(pd.Timestamp(log['training_target_max']), pd.Timestamp('2023-12-31'))
        self.assertEqual(log['training_n'], 730-13-1)

    def test_placebo_is_weekday_matched_disjoint_and_shared(self):
        shifts = placebo_shifts(self.protocol)
        self.assertEqual(shifts, placebo_shifts(self.protocol))
        for state in STATES:
            for year, ds in anchors(state).items():
                shifted = [d+pd.Timedelta(days=shifts[year]) for d in ds]
                self.assertFalse(window_dates(ds) & window_dates(shifted))
                self.assertEqual([d.dayofweek for d in ds], [d.dayofweek for d in shifted])
                self.assertLessEqual(abs(shifts[year]), 42)

    def test_equal_dimensions_and_information(self):
        f = self.frames
        for dim, arms in [(1, ['zero_1', 'generic_window', 'regional_window', 'placebo_window']),
                          (7, ['zero_7', 'generic_7', 'regional_7', 'placebo_7'])]:
            for arm in arms:
                self.assertEqual(f[arm].shape[1]-f['calendar'].shape[1], dim)
        np.testing.assert_array_equal(f['regional_window'].event_0, self.event)
        np.testing.assert_array_equal(f['regional_7'].iloc[:, -7:].any(axis=1), self.event)

    def test_zero_control_and_date_perturbation(self):
        o = pd.date_range('2024-10-25', periods=4)
        a, _, _ = train_predict(self.y, self.frames['calendar'], 7, 2024, o)
        b, _, _ = train_predict(self.y, self.frames['zero_7'], 7, 2024, o)
        np.testing.assert_allclose(a, b, atol=1e-9)
        actual = self.frames['regional_window'].event_0
        shifted = self.frames['regional_shift_+2_window'].event_0
        np.testing.assert_array_equal(actual.shift(2).iloc[2:], shifted.iloc[2:])


if __name__ == '__main__':
    unittest.main(verbosity=2)
