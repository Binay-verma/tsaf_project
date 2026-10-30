"""Independent labels/cases/metrics audit and matched historical-model table."""
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data


def main():
    out = ROOT/'results/timesfm_matched_events_v1'
    d = pd.read_csv(out/'predictions.csv', parse_dates=['origin', 'date'])
    cases = pd.read_csv(out/'cases.csv', parse_dates=['origin', 'date'])
    expected = set(map(tuple, cases[['state', 'origin', 'horizon']].to_numpy()))
    assert len(d) == 450 and not d.duplicated(['state', 'origin', 'horizon', 'mode']).any()
    assert ((d.date-d.origin).dt.days == d.horizon-1).all()
    assert np.isfinite(d[['prediction']+[f'q{i:02d}' for i in range(1, 10)]]).all().all()
    source = load_data('latest')
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, source[state].reindex(g.date))
        for year, gg in g.groupby('year'):
            cutoff = pd.Timestamp(f'{year-1}-12-31')
            a = source[state].loc[cutoff-pd.Timedelta(days=729):cutoff]
            np.testing.assert_allclose(gg.mase_scale, (a-a.shift(7)).abs().mean())
    for _, g in d.groupby('mode'):
        assert set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy())) == expected
    d['mode'] = d['mode'].map(dict(history='A_history', calendar='B_calendar', regional='D_regional_festival'))
    d['model'] = 'timesfm3'
    original = pd.read_csv(ROOT/'results/extended_validation/all_verified_predictions.csv', parse_dates=['origin', 'date'])
    matched = original.merge(cases[['state', 'origin', 'horizon']], on=['state', 'origin', 'horizon'], validate='many_to_one')
    for _, g in matched.groupby(['model', 'mode']):
        assert set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy())) == expected
    both = pd.concat([d, matched], ignore_index=True)
    both['ae'] = abs(both.actual-both.prediction)
    both['scaled'] = both.ae/both.mase_scale
    m = both.groupby(['state', 'year', 'horizon', 'model', 'mode']).agg(
        MAE_GWh=('ae', 'mean'), MASE=('scaled', 'mean'), n=('ae', 'size')).reset_index()
    m.to_csv(out/'matched_models_state_year.csv', index=False)
    macro = m.groupby(['year', 'horizon', 'model', 'mode']).MASE.mean().reset_index()
    macro.to_csv(out/'matched_models_macro.csv', index=False)
    macro.groupby(['horizon', 'model', 'mode']).MASE.mean().reset_index().to_csv(out/'matched_models_two_year.csv', index=False)
    effects = m.pivot(index=['state', 'year', 'horizon', 'model'], columns='mode', values='MAE_GWh')
    effects['regional_improvement_pct'] = 100*(effects.B_calendar-effects.D_regional_festival)/effects.B_calendar
    effects.reset_index().to_csv(out/'matched_regional_effects.csv', index=False)
    own = m[m.model.eq('timesfm3')].set_index(['state', 'year', 'horizon', 'mode']).MASE.sort_index()
    saved = pd.read_csv(out/'metrics_state_year.csv')
    saved['mode'] = saved['mode'].map(dict(history='A_history', calendar='B_calendar', regional='D_regional_festival'))
    np.testing.assert_allclose(own, saved.set_index(['state', 'year', 'horizon', 'mode']).MASE.sort_index(), rtol=1e-12)
    protocol = json.loads((out/'protocol.json').read_text())
    assert hashlib.sha256((out/'cases.csv').read_bytes()).hexdigest() == protocol['cases_sha256']
    protected = json.loads((ROOT/'results/calendar_controls_v1/protected_before.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest() == h for n, h in protected.items())
    report = dict(status='passed', scored_rows=len(d), exact_cases_per_mode=len(expected),
        protected_historical_files=len(protected),
        checks=['source labels/scales', 'identical cases across native and historical models',
                'unique/finite forecasts', 'lead-date alignment', 'independent metric reconstruction',
                'frozen case hash', 'original data and expanded results unchanged'],
        warning='Only two historical event years; overlap-uncertain; no independent-day or causal claims')
    (out/'independent_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
