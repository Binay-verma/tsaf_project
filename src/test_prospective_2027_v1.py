"""Synthetic checks for the prospective analysis (no real data)."""
import unittest
import numpy as np
import pandas as pd
import prospective_2027_analysis_v1 as p


def fake(effect_typed_states, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    fams = {'Rajasthan': ['Diwali', 'Dussehra', 'Holi'], 'Gujarat': ['Diwali', 'Dussehra', 'Holi'],
            'Tamil Nadu': ['Diwali', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa'],
            'Uttar Pradesh': ['Diwali', 'Dussehra', 'Holi'], 'Madhya Pradesh': ['Diwali', 'Holi'],
            'Telangana': ['Diwali', 'Holi'], 'Andhra Pradesh': ['Diwali', 'Holi']}
    for st, fs in fams.items():
        for f in fs:
            for y in p.YEARS:
                for m in ['ridge', 'timesfm', 'sarimax']:
                    for h in [1, 7, 14]:
                        base = abs(rng.normal(1, .2))
                        eff = effect_typed_states if st in p.TYPED_STATES else 0.
                        for arm, val in [('pooled_day5', base), ('day5', base + eff + rng.normal(0, .02))]:
                            rows.append(dict(family=f, state=st, year=y, horizon=h, model=m, arm=arm, MASE=val))
    return pd.DataFrame(rows)


class T(unittest.TestCase):
    def test_detects_typed_advantage(self):
        r = p.evaluate(fake(-0.1)).set_index('test')
        self.assertEqual(r.loc['P1', 'decision'], 'CONFIRMED')
        self.assertEqual(r.loc['P2', 'decision'], 'CONFIRMED')

    def test_null_not_confirmed(self):
        r = p.evaluate(fake(0.0, seed=3)).set_index('test')
        self.assertIn(r.loc['P1', 'decision'], ['NOT CONFIRMED'])

    def test_contradiction(self):
        r = p.evaluate(fake(+0.1)).set_index('test')
        self.assertEqual(r.loc['P1', 'decision'], 'CONTRADICTED')

    def test_units(self):
        u = p.units(fake(0.), 'ridge', [1], p.TYPED_STATES)
        self.assertEqual(len(u), 10*2)

    def test_holm(self):
        np.testing.assert_allclose(p.holm([0.01, 0.04]), [0.02, 0.04])


if __name__ == '__main__':
    unittest.main()
