import unittest
import numpy as np
import pandas as pd
from residual_intervals import calibrate


class CalibrationChecks(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range('2020-01-01', periods=1000)
        self.history = pd.DataFrame({'date': dates, 'actual': np.arange(1000.) % 19,
                                     'prediction': np.zeros(1000)})
        self.origin = dates[800]

    def test_future_labels_and_overlapping_future_targets_excluded(self):
        a, n, end = calibrate(self.history, self.origin, 100., [.05, .5, .95])
        changed = self.history.copy()
        changed.loc[changed.date.ge(self.origin), 'actual'] = 1e12
        b, _, _ = calibrate(changed, self.origin, 100., [.05, .5, .95])
        np.testing.assert_array_equal(a, b)
        self.assertEqual(n, 730)
        self.assertLess(end, self.origin)

    def test_missing_and_insufficient_residuals(self):
        history = self.history.copy()
        history.loc[100:109, 'actual'] = np.nan
        _, n, _ = calibrate(history, self.origin, 100., [.05, .5, .95])
        self.assertEqual(n, 720)
        with self.assertRaises(ValueError):
            calibrate(history, pd.Timestamp('2020-02-01'), 0., [.05, .5, .95])

    def test_quantiles_use_signed_past_errors(self):
        history = self.history.copy()
        history.actual = history.prediction + 5
        q, _, _ = calibrate(history, self.origin, 100., [.05, .5, .95])
        np.testing.assert_array_equal(q, [105, 105, 105])


if __name__ == '__main__':
    unittest.main(verbosity=2)
