import unittest
import numpy as np
import pandas as pd
from timesfm_fixture import build_input


class FoundationInputChecks(unittest.TestCase):
    def test_inputs_exclude_all_unseen_targets(self):
        index = pd.date_range('2022-01-01', '2026-10-28')
        y = pd.Series(100+np.sin(np.arange(len(index))/20), index=index)
        origin = pd.Timestamp('2026-09-01')
        changed = y.copy()
        changed.loc[origin:] = 1e12
        for mode in ['history', 'calendar', 'regional']:
            a, ac = build_input(y, 'Karnataka', origin, mode)
            b, bc = build_input(changed, 'Karnataka', origin, mode)
            np.testing.assert_array_equal(a, b)
            self.assertEqual(a.shape, (730,))
            if ac is not None:
                np.testing.assert_array_equal(ac, bc)
                self.assertEqual(ac.shape, (13 if mode == 'calendar' else 20, 744))


if __name__ == '__main__':
    unittest.main(verbosity=2)
