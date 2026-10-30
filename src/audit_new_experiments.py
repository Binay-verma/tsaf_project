"""Check persisted experiment artifacts, independently of their scoring functions."""
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data


def main():
    out = ROOT/'results/calendar_controls_v1'
    protected = json.loads((out/'protected_before.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in protected.items())
    source = load_data('latest')
    d = pd.read_csv(out/'predictions.csv', parse_dates=['origin', 'date'])
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, source[state].reindex(g.date), equal_nan=True)
    p = d.pivot(index=['state', 'origin', 'horizon'], columns='arm', values='prediction')
    delhi = p.loc['Delhi']
    for a, b in [('generic_window', 'regional_window'), ('generic_7', 'regional_7')]:
        np.testing.assert_array_equal(delhi[a], delhi[b])
    d['scaled'] = (d.actual-d.prediction).abs()/d.mase_scale
    expected = d[d.event.eq(1)].groupby(['year', 'state', 'horizon', 'arm']).scaled.mean()
    saved = pd.read_csv(out/'metrics_state_year.csv')
    saved = saved[saved.scope.eq('event')].set_index(['year', 'state', 'horizon', 'arm']).MASE
    np.testing.assert_allclose(expected.sort_index(), saved.sort_index(), rtol=1e-12)
    (out/'independent_audit.json').write_text(json.dumps({
        'passed': ['labels match frozen source', 'Delhi generic/regional identity',
                   'event metrics recomputed', f'{len(protected)} historical files unchanged']}, indent=2)+'\n')

    out = ROOT/'results/residual_intervals_v1'
    d = pd.read_csv(out/'predictions.csv', parse_dates=['origin', 'date', 'calibration_target_max'])
    assert (d.calibration_target_max < d.origin).all()
    assert ((d.date-d.origin).dt.days == d.horizon-1).all()
    assert (d.q05 <= d.q50).all() and (d.q50 <= d.q95).all()
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, source[state].reindex(g.date))
    history = pd.read_csv(ROOT/'results/extended_validation/all_verified_predictions.csv',
                          parse_dates=['date', 'origin'])
    checked = 0
    # Both first-origin and event-origin examples per state/year/model/mode/lead.
    for keys, group in d.groupby(['state', 'year', 'model', 'mode', 'horizon']):
        state, year, model, mode, h = keys
        pool = history[history.state.eq(state) & history.model.eq(model) &
                       history['mode'].eq(mode) & history.horizon.eq(h)]
        for row in [group.iloc[0], group[group.event.eq(1)].iloc[0]]:
            prior = pool[pool.date.lt(row.origin) & pool.date.ge(row.origin-pd.Timedelta(days=730))]
            q = row.point + np.quantile(prior.actual-prior.prediction, [.05, .5, .95], method='linear')
            np.testing.assert_allclose(q, row[['q05', 'q50', 'q95']].to_numpy(dtype=float), rtol=1e-12)
            assert len(prior) == row.calibration_n
            checked += 1
    coverage = ((d.actual >= d.q05) & (d.actual <= d.q95)).astype(float)
    width = d.q95-d.q05
    score = width + 20*(d.q05-d.actual).clip(lower=0) + 20*(d.actual-d.q95).clip(lower=0)
    np.testing.assert_array_equal(coverage, d.covered)
    np.testing.assert_allclose(score/d.mase_scale, d.scaled_interval_score, rtol=1e-12)
    np.testing.assert_allclose(width/d.mase_scale, d.scaled_width, rtol=1e-12)
    report = {'rows': len(d), 'residual_quantile_reconstructions': checked,
              'passed': ['source labels', 'lead/date alignment', 'noncrossing quantiles',
                         'strict pre-origin calibration dates', 'coverage/width/interval score recomputed',
                         'first/event-origin calibration examples independently reconstructed']}
    (out/'independent_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Both experiments independently checked;', checked, 'calibration examples reconstructed.')


if __name__ == '__main__':
    main()
