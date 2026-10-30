"""Meaningful pooling and temporal invariants, independent of model outcomes."""
import unittest
import numpy as np
import pandas as pd
from pooled_festival_experiment import frames
from festival_feature_design import frames as typed
from festival_feature_experiment import input_pair
from forecasting import load_data


class PooledFestivalTests(unittest.TestCase):
    def test_exact_state_scoped_union_and_padding(self):
        dates = pd.date_range('2022-01-01', '2025-12-31')
        for state in ['Delhi', 'Karnataka', 'Maharashtra']:
            pooled, prior = frames(dates, state), typed(dates, state)
            for kind in ['day', 'window']:
                for width in [1, 5]:
                    x = pooled[f'pooled_{kind}{width}']
                    self.assertEqual(x.shape[1], 13+width)
                    np.testing.assert_array_equal(x.iloc[:, :13], prior['calendar'])
                    np.testing.assert_array_equal(x.iloc[:, 13], prior[kind+'5'].iloc[:, 13:].any(axis=1).astype(float))
                    self.assertEqual(np.count_nonzero(x.iloc[:, 14:]), 0)
            self.assertEqual(np.count_nonzero(pooled['zero1'].iloc[:, 13:]), 0)
            self.assertEqual(pooled['zero1'].shape[1], 14)
        self.assertEqual(frames(dates, 'Karnataka')['pooled_day1'].loc['2023-09-18'].iloc[-1], 1)
        self.assertEqual(frames(dates, 'Maharashtra')['pooled_day1'].loc['2023-09-18'].iloc[-1], 0)
        self.assertEqual(frames(dates, 'Delhi')['pooled_day1'].loc['2023-09-18'].iloc[-1], 0)

    def test_pooling_is_binary_when_windows_overlap(self):
        dates = pd.date_range('2024-10-25', '2024-11-08')
        prior = typed(dates, 'Karnataka')['window5'].iloc[:, 13:]
        pooled = frames(dates, 'Karnataka')['pooled_window1'].iloc[:, -1]
        self.assertTrue(set(pooled) <= {0., 1.})
        np.testing.assert_array_equal(pooled, prior.any(axis=1).astype(float))

    def test_future_targets_cannot_affect_pooled_inputs(self):
        data = load_data('latest')['Maharashtra']
        origin = pd.Timestamp('2024-03-12')
        altered = data.copy(); altered.loc[origin:] = -1e10
        for arm, frame in frames(data.index, 'Maharashtra').items():
            target, cov = input_pair(data, frame, origin)
            changed, cov2 = input_pair(altered, frame, origin)
            np.testing.assert_array_equal(target, changed)
            np.testing.assert_array_equal(cov, cov2)


if __name__ == '__main__':
    unittest.main()
