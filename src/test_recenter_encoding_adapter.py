"""Regression for the missing all-arm integration, without model inference."""
import unittest
import numpy as np
import pandas as pd

from calendar_encoding_study import ARMS, encoded_input as original
from calendar_semantics_study_v2 import encoded_input as aligned
from recenter_encoding_adapter_v1 import encoded_input, INDEPENDENT, feature_names


class RecenterEncodingAdapterTests(unittest.TestCase):
    def fixture(self):
        days = pd.date_range('2022-01-01', '2025-12-31')
        return pd.Series(100.+np.arange(len(days))*.01, index=days), pd.Timestamp('2025-09-28')

    def test_all_ten_arms_match_their_registered_numeric_contract(self):
        observed, origin = self.fixture()
        for arm in ARMS:
            with self.subTest(arm=arm):
                a, b, log = encoded_input(observed, 'Karnataka', arm, origin)
                x, y, expected = (original if arm in INDEPENDENT else aligned)(observed, 'Karnataka', arm, origin)
                np.testing.assert_array_equal(a, x)
                np.testing.assert_array_equal(b, y)
                self.assertEqual(log, expected)
                self.assertEqual(b.shape, (len(feature_names(arm)), 744))

    def test_every_arm_is_invariant_to_future_target_perturbation(self):
        observed, origin = self.fixture()
        changed = observed.copy()
        changed.loc[origin:] = 1e12
        for arm in ARMS:
            with self.subTest(arm=arm):
                a, b, log = encoded_input(observed, 'Karnataka', arm, origin)
                x, y, expected = encoded_input(changed, 'Karnataka', arm, origin)
                np.testing.assert_array_equal(a, x)
                np.testing.assert_array_equal(b, y)
                self.assertEqual(log, expected)


if __name__ == '__main__':
    unittest.main()
