"""Leakage, date-scope and matched-control checks for the intervention."""
import unittest
import numpy as np
import pandas as pd
from forecasting import load_data
from robust_baselines import design_frame, fitting_cases
from festival_feature_design import frames
from festival_feature_experiment import input_pair, ledger_bound


class FestivalFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data('latest')
        cls.fc = {s: frames(cls.data.index, s) for s in cls.data}

    def test_state_specific_training_dates(self):
        ka, mh = self.fc['Karnataka']['day5'], self.fc['Maharashtra']['day5']
        self.assertEqual(ka.loc['2023-09-18', 'Ganesh_Chaturthi_day'], 1)
        self.assertEqual(ka.loc['2023-09-19', 'Ganesh_Chaturthi_day'], 0)
        self.assertEqual(mh.loc['2023-09-19', 'Ganesh_Chaturthi_day'], 1)
        self.assertEqual(mh.loc['2023-09-18', 'Ganesh_Chaturthi_day'], 0)
        self.assertEqual(mh.loc['2023-03-07', 'Holi_day'], 1)
        self.assertEqual(mh.loc['2023-03-08', 'Holi_day'], 0)
        self.assertEqual(self.fc['Delhi']['day5']['Ganesh_Chaturthi_day'].sum(), 0)

    def test_dimensions_zero_and_active_placebos(self):
        for state, f in self.fc.items():
            for arm in ['zero5', 'day5', 'window5', 'placebo_day5', 'placebo_window5']:
                self.assertEqual(f[arm].shape[1], 18)
            for arm in ['offset35', 'zero35', 'placebo_offset35']:
                self.assertEqual(f[arm].shape[1], 48)
            self.assertEqual(f['zero5'].iloc[:, 13:].to_numpy().sum(), 0)
            self.assertEqual(f['zero35'].iloc[:, 13:].to_numpy().sum(), 0)
            true = f['window5'].iloc[:, 13:].any(axis=1)
            fake = f['placebo_window5'].iloc[:, 13:].any(axis=1)
            self.assertFalse((true & fake).any(), state)
            self.assertTrue(fake.any())

    def test_relative_day_orientation(self):
        f = self.fc['Delhi']['offset35']
        self.assertEqual(f.loc['2024-03-24', 'Holi_offset_-1'], 1)
        self.assertEqual(f.loc['2024-03-25', 'Holi_offset_0'], 1)
        self.assertEqual(f.loc['2024-03-26', 'Holi_offset_1'], 1)
        self.assertEqual(f.loc['2024-03-24', 'Holi_offset_1'], 0)

    def test_foundation_future_targets_cannot_change_inputs(self):
        origin = pd.Timestamp('2024-03-12')
        observed = self.data['Delhi']
        altered = observed.copy(); altered.loc[origin:] = 1e12
        for arm in ['calendar', 'day5', 'window5', 'placebo_day5']:
            x, c = input_pair(observed, self.fc['Delhi'][arm], origin)
            xx, cc = input_pair(altered, self.fc['Delhi'][arm], origin)
            np.testing.assert_array_equal(x, xx)
            np.testing.assert_array_equal(c, cc)
            self.assertEqual(c.shape[1], 744)
        with self.assertRaises(AssertionError):
            ledger_bound(pd.date_range('2021-12-31', periods=2))

    def test_direct_regression_purges_multistep_labels(self):
        origin = pd.Timestamp('2024-03-12')
        cutoff = pd.Timestamp('2024-02-29')
        observed = self.data['Delhi']
        changed = observed.copy(); changed.loc[origin:] = 1e12
        original, _ = design_frame(observed, 'Delhi', 14, 'rich_calendar')
        altered, _ = design_frame(changed, 'Delhi', 14, 'rich_calendar')
        np.testing.assert_array_equal(original.loc[origin], altered.loc[origin])
        x, y, log = fitting_cases(original, observed, 14, cutoff)
        xx, yy, other = fitting_cases(altered, changed, 14, cutoff)
        np.testing.assert_array_equal(x, xx); np.testing.assert_array_equal(y, yy)
        self.assertEqual(log, other)
        self.assertLess(pd.Timestamp(log['training_target_max']), origin)


if __name__ == '__main__':
    unittest.main()
