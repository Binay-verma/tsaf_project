"""Frame and input invariants for the foundation Ziel study (no model weights, no outcomes)."""
import unittest
import numpy as np
import pandas as pd
import ziel_foundation_v1 as z
import breadth_model_engine_v1 as engine
from forecasting import load_data


class ZielFoundationTests(unittest.TestCase):
    def test_frames_and_inputs(self):
        data = load_data('latest')
        cases = z.v1.cohort_cases('event_window')
        for state in ['Delhi', 'Karnataka', 'Maharashtra']:
            fc = z.frames(data.index, state)
            self.assertEqual(list(fc), z.ARMS)
            self.assertTrue(all(fc[a].shape[1] == 18 for a in z.ARMS if a != 'calendar'))
            origin = pd.Timestamp(cases[cases.state.eq(state)].origin.iloc[0])
            for arm in z.ARMS:
                t, c = engine.input_pair(data[state], fc[arm], origin)
                changed = data[state].copy(); changed.loc[origin:] = 1e12
                t2, c2 = engine.input_pair(changed, fc[arm], origin)
                np.testing.assert_array_equal(t, t2); np.testing.assert_array_equal(c, c2)
                self.assertEqual(c.shape, (fc[arm].shape[1], 744))


if __name__ == '__main__':
    unittest.main()
