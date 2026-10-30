import unittest
import numpy as np
import pandas as pd
from robust_baselines import rich_history, design_frame, fitting_cases


class RichBaselineChecks(unittest.TestCase):
    def setUp(self):
        self.idx = pd.date_range('2018-01-01', '2026-12-31')
        self.y = pd.Series(100+np.sin(np.arange(len(self.idx))/9), index=self.idx)

    def test_all_origin_features_ignore_future_targets(self):
        origin = pd.Timestamp('2024-10-20')
        y = self.y.copy()
        y.loc[origin:] = 1e12
        for h in [1, 7, 14]:
            for mode in ['rich_history', 'rich_calendar', 'rich_regional']:
                a, _ = design_frame(self.y, 'Karnataka', h, mode)
                b, _ = design_frame(y, 'Karnataka', h, mode)
                np.testing.assert_array_equal(a.loc[origin], b.loc[origin])

    def test_target_aligned_annual_lag(self):
        origin = pd.Timestamp('2024-10-20')
        for h in [1, 7, 14]:
            x = rich_history(self.y, h)
            for k in [364, 365, 366]:
                self.assertEqual(x.loc[origin, f'target_annual_{k}'],
                                 self.y.loc[origin+pd.Timedelta(days=h-1-k)])

    def test_label_purge_and_missing_fit_labels(self):
        y = self.y.copy()
        y.loc['2023-12-31'] = np.nan
        frame = rich_history(y, 14)
        x, labels, log = fitting_cases(frame, y, 14, '2023-12-31')
        self.assertEqual(len(labels), 730-13-1)
        self.assertEqual(log['training_target_max'], '2023-12-30')
        self.assertLessEqual(pd.Timestamp(log['training_origin_max']), pd.Timestamp('2023-12-18'))
        changed = y.copy()
        changed.loc['2024':] = 1e12
        xx, yy, _ = fitting_cases(rich_history(changed, 14), changed, 14, '2023-12-31')
        np.testing.assert_array_equal(x, xx)
        np.testing.assert_array_equal(labels, yy)


if __name__ == '__main__':
    unittest.main(verbosity=2)
