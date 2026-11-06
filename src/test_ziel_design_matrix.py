"""Rebuild logged Ziel-comparator training matrices and check their definitions.

Added after the registered runs (the registered test files are hash-locked by their protocols).
For sampled fits, the training design is rebuilt exactly as the registered regression builds it,
its SHA-256 must equal the logged training_X_sha256, and its calendar columns must follow the
arm definition at the target date (origin + h - 1).
"""
import hashlib
import json
import unittest
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from robust_baselines import design_frame, fitting_cases
import ziel_replacing_v1 as v1
import ziel_replacing_v2 as v2

DOW = [f'dow_{i}' for i in range(7)]


def rebuild(frames_fn, state, horizon, arm, refit, worker='ridge'):
    data = load_data('latest')
    observed = data[state]
    fc = frames_fn(data.index, state)
    base, _ = design_frame(observed, state, horizon, 'rich_calendar')
    shifted = fc[arm].reindex(data.index+pd.Timedelta(days=horizon-1)).copy()
    shifted.index = data.index
    x = base.copy()
    x[list(fc['calendar'].columns)] = shifted.iloc[:, :13].to_numpy()
    x = pd.concat([x, shifted.iloc[:, 13:]], axis=1)
    if worker != 'ridge':
        x = x.astype(np.float32)
    cutoff = pd.Timestamp(refit)-pd.Timedelta(days=1)
    xx, yy, log = fitting_cases(x, observed, horizon, cutoff)
    return x, xx, fc, log


class DesignMatrixTests(unittest.TestCase):
    CASES = [(v1, 'ziel_replacing_v1', 'Karnataka', 7, 'sunday_day'),
             (v2, 'ziel_replacing_v2', 'Maharashtra', 1, 'replace_typed'),
             (v2, 'ziel_replacing_v2', 'Delhi', 14, 'replace_pooled')]

    def test_logged_training_matrix_and_definition(self):
        for module, folder, state, h, arm in self.CASES:
            log = json.loads((ROOT/f'results/{folder}/event_window/ridge/fit_log.json').read_text())
            fit = next(f for f in log if f['state'] == state and f['horizon'] == h and f['arm'] == arm)
            frames_fn = module.frames
            x, xx, fc, _ = rebuild(frames_fn, state, h, arm, fit['refit'])
            self.assertEqual(hashlib.sha256(xx.tobytes()).hexdigest(), fit['training_X_sha256'], (folder, state, h, arm))
            flag = fc['pooled_day5']['event_day'].astype(bool)
            target_flag = flag.reindex(x.index+pd.Timedelta(days=h-1), fill_value=False).to_numpy()
            rows = x.loc[target_flag, DOW]
            self.assertGreater(len(rows), 0)
            if arm == 'sunday_day':
                self.assertTrue((rows['dow_6'] == 1).all() and (rows[DOW[:6]] == 0).all().all())
            else:
                self.assertTrue((rows == 0).all().all())
            other = x.loc[~target_flag, DOW].dropna()
            self.assertTrue((other.sum(axis=1) == 1).all())


if __name__ == '__main__':
    unittest.main()
