"""Date-only and synthetic checks for the second test (no forecasts, no outcomes of the new states)."""
import unittest
import numpy as np
import pandas as pd
import new_states_v2 as s
import longer_panel_stage_a_v1 as A
import new_states_v2_analysis as an


def fake_predictions(effects, states, rng, years=an.EVENT_YEARS, families=('Holi', 'Dussehra', 'Diwali')):
    """Synthetic lead-1 predictions; effects maps model -> per-state typed-minus-pooled shift."""
    rows = []
    for m, eff in effects.items():
        for st in states:
            for f in families:
                for y in years:
                    for k in range(3):
                        base = abs(rng.normal(1, .2))
                        for arm, add in [('day5', eff.get(st, 0.)), ('pooled_day5', 0.)]:
                            rows.append(dict(model=m, arm=arm, horizon=1, family=f, year=y, state=st,
                                             prediction=base+add+rng.normal(0, .01), actual=0., mase_scale=1.))
    d = pd.DataFrame(rows)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


class SecondTestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = s.anchors()

    def test_patch_points_shared_code_at_new_states(self):
        import forecasting, extended_validation, robust_baselines
        self.assertEqual(list(forecasting.STATES), list(s.NEW_STATES))
        self.assertEqual(list(robust_baselines.STATES), list(s.NEW_STATES))
        self.assertEqual(list(extended_validation.STATES), list(s.NEW_STATES))
        self.assertEqual(list(robust_baselines.load_data('latest').columns), list(s.NEW_STATES))

    def test_scope_years_and_count(self):
        for st, fams in s.SCOPE.items():
            self.assertEqual(set(self.a[self.a.state == st].family), set(fams))
        self.assertEqual(set(self.a.year), set(s.CAL_YEARS))
        self.assertEqual(len(self.a), 231)
        self.assertFalse(self.a.duplicated(['state', 'family', 'year']).any())

    def test_cases(self):
        ev, dropped = s.event_cases(self.a)
        self.assertEqual(set(ev.year), set(s.EVENT_YEARS))
        self.assertTrue((pd.to_datetime(ev.date)-pd.to_datetime(ev.origin)).dt.days.eq(ev.horizon-1).all())
        self.assertFalse(ev.duplicated(A.KEY).any())
        self.assertEqual(ev[['family', 'year']].drop_duplicates().shape[0], 36)

    def test_frames(self):
        fake = A.placebos(self.a)
        fc = A.frames(pd.date_range('2015-01-01', '2025-12-31'), 'Odisha', self.a, fake)
        d = self.a[(self.a.state == 'Odisha') & (self.a.family == 'Ganesh_Chaturthi')].date.iloc[0]
        self.assertEqual(fc['day5'].loc[d, 'Ganesh_Chaturthi_day'], 1.)
        self.assertEqual(fc['pooled_day5'].loc[d, 'event_day'], 1.)
        k = self.a[(self.a.state == 'Kerala') & (self.a.family == 'Diwali')].date.iloc[0]
        fk = A.frames(pd.date_range('2015-01-01', '2025-12-31'), 'Kerala', self.a, fake)
        self.assertEqual(fk['day5'].loc[k, 'Diwali_day'], 1.)
        self.assertEqual(fk['day5']['Holi_day'].sum(), 0.)

    def test_m1_states_are_top_three_h_abs(self):
        h = an.h_values('h_abs').sort_values(ascending=False)
        self.assertEqual(h.index[:3].tolist(), an.M1_STATES)
        self.assertEqual(set(h.index), set(s.NEW_STATES))

    def test_spearman_exact(self):
        x = np.arange(7.); y = -x
        rho, p_neg, p_pos = an.spearman_exact(x, y)
        self.assertAlmostEqual(rho, -1.); self.assertAlmostEqual(p_neg, 1/5040); self.assertEqual(p_pos, 1.)
        rho, p_neg, _ = an.spearman_exact(np.array([0, 0, 1, 2, 3, 4, 5.]), -np.arange(7.))
        self.assertLess(rho, -0.95); self.assertLess(p_neg, 0.01)

    def test_evaluate_synthetic(self):
        rng = np.random.default_rng(3)
        states = list(s.NEW_STATES)
        h = an.h_values('h_abs')
        ridge = {st: -0.5*h[st] for st in states}
        d = fake_predictions({'sarimax': {st: -0.05 for st in states}, 'lightgbm_capacity2': {st: 0.05 for st in states}, 'ridge': ridge}, states, rng)
        r = an.evaluate(d).set_index('hypothesis')
        an_draws = an.DRAWS
        self.assertEqual(r.loc['R1', 'decision'], 'CONFIRMED'); self.assertEqual(r.loc['R2', 'decision'], 'CONFIRMED')
        self.assertEqual(r.loc['M1', 'decision'], 'CONFIRMED'); self.assertLess(r.loc['M2', 'statistic'], -0.9)
        self.assertEqual(an_draws, 1_000_000)
        d0 = fake_predictions({'sarimax': {}, 'lightgbm_capacity2': {}, 'ridge': {}}, states, rng)
        r0 = an.evaluate(d0).set_index('hypothesis')
        self.assertTrue((r0.decision != 'CONFIRMED').all())

    def test_bound(self):
        s.bound(['2015-01-01', '2025-12-31'])
        with self.assertRaises(AssertionError):
            s.bound(['2014-12-31'])


if __name__ == '__main__':
    unittest.main()
