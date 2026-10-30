"""Read-only reconstruction of checkpoint scoring and key leakage boundaries."""
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from extended_validation import features


def main():
    old = ROOT/'results/extended_validation'
    out = ROOT/'results/calendar_controls_v1'
    data = load_data('latest')
    d = pd.concat([pd.read_csv(old/name, parse_dates=['origin', 'date']) for name in
                   ['predictions.csv', 'sarimax_events.csv', 'lightgbm_daily.csv']], ignore_index=True)
    assert not d.duplicated(['state', 'origin', 'horizon', 'model', 'mode']).any()
    assert np.isfinite(d.prediction).all()
    assert ((d.date-d.origin).dt.days == d.horizon-1).all()
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, data[state].reindex(g.date), equal_nan=True)
        np.testing.assert_array_equal(g.observed.eq(1), data[state].reindex(g.date).notna())
        _, _, event = features(data.index, state)
        np.testing.assert_array_equal(g.festival_window, event.reindex(g.date).astype(int))
        for year, sub in g.groupby('year'):
            cutoff = pd.Timestamp(f'{year-1}-12-31')
            training = data[state].loc[cutoff-pd.Timedelta(days=729):cutoff]
            scale = float((training-training.shift(7)).abs().mean())
            np.testing.assert_allclose(sub.mase_scale, scale, atol=1e-12)
    d = d[d.observed.eq(1)].copy()
    d['ae'] = (d.actual-d.prediction).abs()
    d['scaled'] = d.ae/d.mase_scale
    keys = ['year', 'state', 'horizon', 'model', 'mode']
    daily = d[d.cohort.eq('daily')]
    for year, g in daily.groupby('year'):
        sets = [set(map(tuple, a[['state', 'origin', 'horizon']].to_numpy()))
                for _, a in g.groupby(['model', 'mode'])]
        assert all(s == sets[0] for s in sets), year
    event = d[d.festival_window.eq(1) & d.year.le(2025)]
    sets = [set(map(tuple, a[['state', 'origin', 'horizon']].to_numpy()))
            for _, a in event.groupby(['model', 'mode'])]
    assert all(s == sets[0] for s in sets)
    for name, subset in [('daily_state_metrics.csv', daily), ('festival_state_metrics.csv', event)]:
        recomputed = subset.groupby(keys).agg(MAE_GWh=('ae', 'mean'),
                        MASE=('scaled', 'mean'), n=('ae', 'size')).sort_index()
        recorded = pd.read_csv(old/name).set_index(keys).sort_index()
        pd.testing.assert_index_equal(recomputed.index, recorded.index)
        np.testing.assert_allclose(recomputed[['MAE_GWh', 'MASE', 'n']],
                                   recorded[['MAE_GWh', 'MASE', 'n']], rtol=1e-10, atol=1e-10)
    selected = pd.read_csv(old/'lightgbm_selected.csv')
    search = pd.read_csv(old/'lightgbm_validation_search.csv')
    k = ['state', 'mode', 'horizon']
    assert not selected.duplicated(k).any()
    np.testing.assert_allclose(selected.set_index(k).validation_MAE_GWh.sort_index(),
                               search.groupby(k).validation_MAE_GWh.min().sort_index())
    assert pd.to_datetime(selected.training_target_max).max() < pd.Timestamp('2025-07-05')
    assert pd.to_datetime(selected.validation_target_max).max() < pd.Timestamp('2026-01-01')
    report = {'status': 'passed', 'scored_rows': len(d), 'raw_rows': len(d),
              'checks': ['unique/finite predictions', 'date and lead alignment',
              'actual labels and observed flags match frozen source', 'event membership matches ledger',
              'scales reconstructed from pre-year data', 'identical daily and event cases',
              'state-year MAE and MASE independently reproduced',
              'LightGBM validation minima and date purge'],
              'limits': ['Does not rerun model inference', 'Does not clear pretraining overlap',
                         'Does not reconstruct real-time data vintages']}
    (out/'checkpoint_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
