"""Invariants for the Ziel replacing (Rph/RpH) arms. Feature and date checks only; no forecast outcomes."""
import unittest
import numpy as np
import pandas as pd
import ziel_replacing_v2 as z
from forecasting import load_data
from festival_feature_experiment import input_pair


class ZielReplacingV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data('latest')
        cls.frames = {s: z.frames(cls.data.index, s) for s in ['Delhi', 'Karnataka', 'Maharashtra']}

    def test_synthetic_zeroing(self):
        idx = pd.date_range('2024-01-01', periods=7)
        f = pd.DataFrame({f'dow_{i}': (idx.dayofweek == i).astype(float) for i in range(7)}, index=idx)
        f['event_day'] = 0.; f.loc[idx[3], 'event_day'] = 1.
        out = z.zero_weekdays(f, f['event_day'])
        self.assertEqual(out.loc[idx[3], z.DOW].sum(), 0)
        self.assertEqual(out.loc[idx[3], 'event_day'], 1)
        self.assertTrue(out.drop(idx[3]).equals(f.drop(idx[3])))

    def test_definitions_against_reference_arms(self):
        for state, fc in self.frames.items():
            self.assertEqual(list(fc), z.ARMS)
            flag = fc['pooled_day5']['event_day'].astype(bool)
            for new, ref in [('replace_pooled', 'pooled_day5'), ('replace_typed', 'day5')]:
                self.assertEqual(list(fc[new].columns), list(fc[ref].columns))
                self.assertEqual(fc[new].shape[1], 18)
                self.assertTrue((fc[new].loc[flag, z.DOW] == 0).all().all())
                self.assertTrue(fc[new].loc[~flag].equals(fc[ref].loc[~flag]))
                other = [c for c in fc[ref].columns if c not in z.DOW]
                self.assertTrue(fc[new][other].equals(fc[ref][other]))
                self.assertTrue((fc[new].loc[~flag, z.DOW].sum(axis=1) == 1).all())

    def test_inputs_ignore_future_targets(self):
        series = self.data['Maharashtra']; origin = pd.Timestamp('2025-10-15')
        changed = series.copy(); changed.loc[origin:] = 1e12
        for arm in z.ARMS:
            a = input_pair(series, self.frames['Maharashtra'][arm], origin)
            b = input_pair(changed, self.frames['Maharashtra'][arm], origin)
            np.testing.assert_array_equal(a[0], b[0]); np.testing.assert_array_equal(a[1], b[1])


if __name__ == '__main__':
    unittest.main()
