"""Audit persisted baselines, region transfer and the second-model fixture."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data


def main():
    source = load_data('latest')
    old = ROOT/'results/extended_validation'
    reference = pd.read_csv(old/'chronos_A_history.csv', parse_dates=['origin', 'date'])
    reference = reference[reference.year.isin([2024, 2025, 2026])]
    refkeys = set(map(tuple, reference[['state', 'origin', 'horizon']].to_numpy()))
    for name, identifiers in [('strong_refit_v1', ['model', 'mode', 'schedule']),
                               ('regional_transfer_v1', ['model', 'mode', 'arm'])]:
        out = ROOT/'results'/name
        d = pd.read_csv(out/'predictions.csv', parse_dates=['origin', 'date'])
        assert not d.duplicated(identifiers+['state', 'origin', 'horizon']).any()
        assert np.isfinite(d.prediction).all()
        assert ((d.date-d.origin).dt.days == d.horizon-1).all()
        for _, g in d.groupby(identifiers):
            assert set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy())) == refkeys
        for (state, year), g in d.groupby(['state', 'year']):
            np.testing.assert_allclose(g.actual, source[state].reindex(g.date), equal_nan=True)
            cutoff = pd.Timestamp(f'{year-1}-12-31')
            tr = source[state].loc[cutoff-pd.Timedelta(days=729):cutoff]
            np.testing.assert_allclose(g.mase_scale, (tr-tr.shift(7)).abs().mean())
        d['error'] = abs(d.actual-d.prediction)/d.mase_scale
        recomputed = d.groupby(identifiers+['state', 'year', 'horizon']).error.mean().sort_index()
        saved = pd.read_csv(out/'metrics_state_year.csv')
        a = saved[saved.scope.eq('all')].set_index(identifiers+['state', 'year', 'horizon']).MASE.sort_index()
        np.testing.assert_allclose(recomputed, a, rtol=1e-12)
        if name == 'strong_refit_v1':
            selection = pd.read_csv(out/'selection.csv')
            selected = pd.read_csv(out/'selected.csv')
            keys = ['state', 'year', 'horizon', 'mode', 'model']
            minima = selection.groupby(keys).MAE.min().sort_index()
            np.testing.assert_allclose(minima, selected.set_index(keys).MAE.sort_index())
            assert (pd.to_datetime(selection.training_target_max) <
                    pd.to_datetime(selection.validation_origin_min)).all()
            assert (pd.to_datetime(selection.validation_target_max).dt.year < selection.year).all()
            fits = pd.read_csv(out/'fit_log.csv')
            assert (pd.to_datetime(fits.training_target_max) < pd.to_datetime(fits.refit)).all()
            a = fits.merge(selected[keys+['configuration']], on=keys, suffixes=('', '_selected'), validate='many_to_one')
            assert (a.configuration == a.configuration_selected).all()
            assert pd.to_datetime(fits[fits.schedule.eq('monthly')].refit).dt.day.eq(1).all()
            protected = json.loads((out/'protected_before.json').read_text())
            assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest() == h for n, h in protected.items())
        else:
            fits = json.loads((out/'fits.json').read_text())
            for fit in fits:
                if fit['arm'] == 'leave_region_out':
                    assert fit['held'] not in fit['training_states'] and len(fit['training_states']) == 2
                for log in fit['training']:
                    assert pd.Timestamp(log['training_target_max']) < pd.Timestamp(f"{fit['year']}-01-01")
        (out/'independent_audit.json').write_text(json.dumps(dict(status='passed', rows=len(d),
            exact_matched_chronos_cases=len(refkeys), checks=['source labels', 'fixed pre-year scales',
            'unique finite predictions', 'lead/date alignment', 'saved MASE reconstructed',
            'past-only fit/selection bounds', 'training identities and schedules']), indent=2)+'\n')
    out = ROOT/'results/second_model_audit_v1'
    expected = json.loads((out/'hf_model.json').read_text())
    first = json.loads((out/'first_tree.json').read_text())
    before = json.loads((out/'before_tree.json').read_text())
    download = json.loads((out/'weight_download.json').read_text())
    current_sha = next(x['lfs']['sha256'] for x in expected['siblings'] if x['rfilename'] == 'model.safetensors')
    first_sha = next(x['lfs']['oid'] for x in first if x['path'] == 'model.safetensors')
    assert first_sha == current_sha == download['sha256']
    assert not any(x['path'] == 'model.safetensors' for x in before)
    d = pd.read_csv(out/'fixture_predictions.csv', parse_dates=['origin', 'date'])
    assert len(d) == 252 and not d.duplicated(['state', 'origin', 'mode', 'horizon']).any()
    assert np.isfinite(d[['prediction']+[f'q{i:02d}' for i in range(1, 10)]]).all().all()
    assert (d.origin > pd.Timestamp('2026-08-24')).all()
    for state, g in d.groupby('state'):
        np.testing.assert_allclose(g.actual, source[state].reindex(g.date))
    d['scaled_error'] = abs(d.actual-d.prediction)/d.mase_scale
    d['coverage80'] = ((d.actual >= d.q01) & (d.actual <= d.q09)).astype(float)
    d['scaled_width80'] = (d.q09-d.q01)/d.mase_scale
    pinball = []
    for i in range(1, 10):
        error = d.actual-d[f'q{i:02d}']
        pinball.append(np.maximum((i/10)*error, (i/10-1)*error)/d.mase_scale)
    d['scaled_mean_pinball'] = np.mean(pinball, axis=0)
    d.groupby(['state', 'mode', 'horizon'])[
        ['scaled_error', 'coverage80', 'scaled_width80', 'scaled_mean_pinball']].mean().reset_index().to_csv(
            out/'fixture_metrics.csv', index=False)
    (out/'independent_audit.json').write_text(json.dumps(dict(status='passed',
        first_weight_upload='2026-08-24T22:41:42Z', same_first_and_evaluated_weights=True,
        sha256=current_sha, fixture_forecast_days=len(d), warning='API fixture, not broad model replication'), indent=2)+'\n')
    print('Phase-two persisted-output audits passed.')


if __name__ == '__main__':
    main()
