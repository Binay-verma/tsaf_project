"""Availability, exclusion and undefined-association guards, using synthetic data."""
import unittest
import numpy as np

from event_support_analysis import past_residuals, association


class EventSupportTests(unittest.TestCase):
    def test_four_prior_weekday_records_required(self):
        y = np.full(42, 100.)
        r = past_residuals(y, np.arange(42)%7, np.zeros(42, bool), 10.)
        self.assertTrue(np.isnan(r[:28]).all())
        self.assertTrue((r[28:] == 0).all())

    def test_future_labels_cannot_change_earlier_proxy(self):
        y = np.arange(42, dtype=float)+100.
        a = past_residuals(y, np.arange(42)%7, np.zeros(42, bool), 10.)
        y[35:] = 1e12
        b = past_residuals(y, np.arange(42)%7, np.zeros(42, bool), 10.)
        np.testing.assert_equal(a[:35], b[:35])

    def test_event_labels_do_not_enter_ordinary_baseline(self):
        y = np.full(42, 100.)
        y[28] = 200.
        excluded = np.zeros(42, bool)
        excluded[28] = True
        r = past_residuals(y, np.arange(42)%7, excluded, 10.)
        self.assertEqual(r[28], 10.)
        self.assertEqual(r[35], 0.)

    def test_constant_tiny_variance_and_missing_values_are_not_zero_effects(self):
        for x in [np.ones(5), np.ones(5)+np.arange(5)*1e-12, np.array([1, 2, np.nan, np.nan, np.nan])]:
            n, p, s = association(x, np.arange(5))
            self.assertTrue(np.isnan(p) and np.isnan(s))
        self.assertEqual(n, 2)

    def test_spearman_ties_use_average_ranks(self):
        n, p, s = association(np.array([1., 1., 2., 3.]), np.array([4., 3., 2., 1.]))
        self.assertEqual(n, 4)
        self.assertAlmostEqual(s, -0.9486832980505138)


if __name__ == '__main__':
    unittest.main()
