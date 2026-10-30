"""Inputs stay past-only even when deterministic future dates exceed the snapshot."""
import unittest
import numpy as np
import pandas as pd
from postweight_daily_panel import inputs
from forecasting import load_data


class PostweightTests(unittest.TestCase):
    def test_known_calendar_beyond_source_end_never_uses_targets(self):
        data = load_data('latest')['Karnataka']
        origin = pd.Timestamp('2026-10-28')
        altered = data.copy(); altered.loc[origin:] = 1e12
        for mode, width in [('history', 0), ('calendar', 13)]:
            target, cov = inputs(data, 'Karnataka', origin, mode)
            changed, other = inputs(altered, 'Karnataka', origin, mode)
            np.testing.assert_array_equal(target, changed); np.testing.assert_array_equal(cov, other)
            self.assertEqual(cov.shape, (width, 744)); self.assertEqual(target.shape, (730,))
        expected = (pd.date_range(origin, periods=14).dayofweek == 0).astype(np.float32)
        np.testing.assert_array_equal(inputs(data, 'Karnataka', origin, 'calendar')[1][0, 730:], expected)


if __name__ == '__main__': unittest.main()
