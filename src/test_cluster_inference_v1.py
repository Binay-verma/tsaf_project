"""Synthetic checks of the sign-flip test, Holm adjustment and t interval (no project outcomes)."""
import unittest
import numpy as np
import cluster_inference_v1 as c


class ClusterInferenceTests(unittest.TestCase):
    def test_all_positive_gives_minimum_p(self):
        p, n = c.sign_flip_p([1., 2., 3., 4., 5.])
        self.assertEqual(n, 32); self.assertAlmostEqual(p, 2/32)

    def test_symmetric_values_give_p_one(self):
        p, _ = c.sign_flip_p([1., -1., 2., -2.])
        self.assertEqual(p, 1.)

    def test_ties_counted(self):
        p, n = c.sign_flip_p([1., 1., 1., 1.])
        self.assertEqual(n, 16); self.assertAlmostEqual(p, 2/16)

    def test_holm(self):
        adj = c.holm([0.01, 0.04, 0.03])
        np.testing.assert_allclose(adj, [0.03, 0.06, 0.06])
        self.assertTrue((c.holm([0.5, 0.9]) <= 1).all())

    def test_t_interval_contains_mean(self):
        lo, hi = c.t_interval([0.1, 0.2, 0.3])
        self.assertLess(lo, 0.2); self.assertGreater(hi, 0.2)


if __name__ == '__main__':
    unittest.main()
