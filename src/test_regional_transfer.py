import unittest
import numpy as np
import pandas as pd
from regional_transfer import fit_transfer
from forecasting import STATES


class TransferChecks(unittest.TestCase):
    def setUp(self):
        idx = pd.date_range('2018-01-01', '2025-12-31')
        self.data = pd.DataFrame({s: (i+1)*(100+np.sin(np.arange(len(idx))/9))
                                  for i, s in enumerate(STATES)}, index=idx)

    def test_held_region_cannot_change_source_fit(self):
        changed = self.data.copy()
        changed.Delhi = changed.Delhi*2 + np.cos(np.arange(len(changed)))
        a, _, _, logs = fit_transfer(self.data, 'Delhi', 2024, 14, 'rich_regional', 'leave_region_out')
        b, _, _, _ = fit_transfer(changed, 'Delhi', 2024, 14, 'rich_regional', 'leave_region_out')
        self.assertNotIn('Delhi', [log['state'] for log in logs])
        np.testing.assert_array_equal(a[-1].coef_, b[-1].coef_)
        np.testing.assert_array_equal(a[0].mean_, b[0].mean_)

    def test_future_years_cannot_change_fit_or_normalization(self):
        changed = self.data.copy()
        changed.loc['2024':] = 1e12
        for arm in ['local', 'pooled_all', 'leave_region_out']:
            a, _, na, logs = fit_transfer(self.data, 'Delhi', 2024, 14, 'rich_regional', arm)
            b, _, nb, _ = fit_transfer(changed, 'Delhi', 2024, 14, 'rich_regional', arm)
            self.assertEqual(na, nb)
            np.testing.assert_array_equal(a[-1].coef_, b[-1].coef_)
            self.assertTrue(all(log['training_target_max'] <= '2023-12-31' for log in logs))


if __name__ == '__main__':
    unittest.main(verbosity=2)
