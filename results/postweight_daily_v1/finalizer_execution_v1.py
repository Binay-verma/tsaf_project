"""Complete-case daily point/probability summaries, with no model selection."""
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from postweight_daily_panel import OUT
from festival_feature_design import sha, dump
from report_multifestival import markdown


def main():
    if (OUT/'run.json').exists():
        raise FileExistsError('Preserve completed panel')
    p = json.loads((OUT/'protocol.json').read_text())
    cases = pd.read_csv(OUT/'cases.csv'); keys = ['state', 'year', 'origin', 'date', 'horizon']
    expected = set(map(tuple, cases[keys].to_numpy()))
    rows = []
    for worker in ['classical', 'chronos', 'timesfm']:
        run = json.loads((OUT/worker/'run.json').read_text())
        assert run['protocol_sha256'] == sha(OUT/'protocol.json')
        assert run['predictions_sha256'] == sha(OUT/worker/'predictions.csv')
        rows.append(pd.read_csv(OUT/worker/'predictions.csv'))
    d = pd.concat(rows, ignore_index=True)
    assert len(d) == 3168 and set(d.configuration) == set(p['configurations'])
    assert not d.duplicated(['configuration']+keys).any()
    assert np.isfinite(d[['actual', 'prediction', 'mase_scale']]).all().all()
    for _, g in d.groupby('configuration'):
        assert set(map(tuple, g[keys].to_numpy())) == expected
    d.to_csv(OUT/'predictions.csv', index=False)
    d['MAE_GWh'] = abs(d.actual-d.prediction); d['MASE'] = d.MAE_GWh/d.mase_scale
    state = d.groupby(['configuration', 'state', 'horizon']).agg(MAE_GWh=('MAE_GWh', 'mean'), MASE=('MASE', 'mean'), n=('MASE', 'size')).reset_index()
    assert state.n.eq(44).all()
    state.to_csv(OUT/'metrics_state.csv', index=False)
    macro = state.groupby(['configuration', 'horizon']).MASE.mean().reset_index()
    macro.to_csv(OUT/'metrics_macro.csv', index=False)
    native = d[d.configuration.str.startswith(('chronos_', 'timesfm_'))].copy()
    qcols = [f'q_{100*i:03d}' for i in range(1, 10)]
    q = native[qcols].to_numpy(); y = native.actual.to_numpy()
    assert np.isfinite(q).all()
    residual = y[:, None]-q; levels = np.arange(1, 10)/10.
    native['scaled_mean_pinball'] = np.maximum(levels*residual, (levels-1)*residual).mean(axis=1)/native.mase_scale
    low, median, high = q[:, 0], q[:, 4], q[:, 8]
    invalid = low > high
    native['invalid80'] = invalid
    native['common_adjacent_crossings'] = (np.diff(q, axis=1) < 0).sum(axis=1)
    native['coverage80'] = np.where(invalid, np.nan, ((low <= y) & (y <= high)).astype(float))
    native['below80'] = np.where(invalid, np.nan, (y < low).astype(float))
    native['above80'] = np.where(invalid, np.nan, (y > high).astype(float))
    native['width80_GWh'] = np.where(invalid, np.nan, high-low)
    native['scaled_width80'] = native.width80_GWh/native.mase_scale
    interval = high-low+10*np.maximum(low-y, 0)+10*np.maximum(y-high, 0)
    native['scaled_interval_score80'] = np.where(invalid, np.nan, interval)/native.mase_scale
    native['scaled_WIS80_median'] = np.where(invalid, np.nan, (.5*abs(y-median)+.1*interval)/1.5)/native.mase_scale
    native.to_csv(OUT/'native_uncertainty_cases.csv', index=False)
    metrics = ['scaled_mean_pinball', 'coverage80', 'below80', 'above80', 'scaled_width80', 'scaled_interval_score80', 'scaled_WIS80_median']
    us = native.groupby(['configuration', 'state', 'horizon'])[metrics].mean().reset_index()
    for (configuration, state_name, h), group in native.groupby(['configuration', 'state', 'horizon']):
        if group.invalid80.any():
            us.loc[us.configuration.eq(configuration) & us.state.eq(state_name) & us.horizon.eq(h), metrics[1:]] = np.nan
    us.to_csv(OUT/'native_uncertainty_state.csv', index=False)
    um = us.groupby(['configuration', 'horizon'])[metrics].mean().reset_index()
    for (configuration, h), group in native.groupby(['configuration', 'horizon']):
        if group.invalid80.any():
            um.loc[um.configuration.eq(configuration) & um.horizon.eq(h), metrics[1:]] = np.nan
    um.to_csv(OUT/'native_uncertainty_macro.csv', index=False)
    contrasts = []
    for model in ['chronos', 'timesfm']:
        c = state[state.configuration.eq(model+'_calendar')].merge(state[state.configuration.eq(model+'_history')], on=['state', 'horizon'], suffixes=('_calendar', '_history'), validate='one_to_one')
        c['model'] = model; c['MASE_change'] = c.MASE_calendar-c.MASE_history
        contrasts.append(c[['model', 'state', 'horizon', 'MASE_change']])
    pd.concat(contrasts, ignore_index=True).to_csv(OUT/'calendar_history_contrasts_state.csv', index=False)
    lines = ['# Daily comparison after audited weight uploads', '', p['status'], '',
        'Daily supplied electricity, three states,44identical target dates15September–28October2026at each lead.396cases/configuration and3168compared rows. Every origin starts2September2026or later. Individual leads1/7/14; equal-state macro MASE is error, lower is better.', '',
        'Post-weight chronology, conditional on source dates, rules out direct inclusion of these later observations in unchanged weights. It does not make previously inspected outcomes an untouched test, establish exact training cutoffs/proxy clearance, or reconstruct source publication-time availability.', '',
        markdown(macro.pivot(index='configuration', columns='horizon', values='MASE').reindex(p['configurations']).round(5).reset_index()), '',
        '## Native uncertainty: common quantiles and80%intervals', '',
        'No calibration, sorting or clipping. Mean pinball over native0.1–0.9levels, scaled interval width/score and one-intervalWIS plus the native median. Coverage alone is not a calibration guarantee, and44dates/state are correlated. Invalid endpoints propagate undefined interval summaries.', '']
    for h in [1, 7, 14]:
        lines += ['### Individual lead '+str(h), '', markdown(um[um.horizon.eq(h)].drop(columns='horizon').round(5)), '']
    lines += ['## Boundaries', '',
        'History-only and thirteen ordinary weekday/Fourier covariates are compared, without new event identities. This is not a festival-enhancement study or a full-year two-model ranking. Local rich-calendar parameters remain selected before2026and refit monthly; foundation inference uses730past targets without tuning. Local lag/rolling feature warm-up can precede its730-day label-fitting window, so adaptation/memory budgets are not architecture-identical.', '',
        'Ideal retrospective origin-1inputs are not fully reconstructed operational data vintages. Prior lag/revision sensitivity remains separate. No later actuals are retrieved and no original prospective forecasts are replaced. Source rights, independent human review, calendar amendments and untouched/source-independent confirmation remain open. All positive/negative native/model outcomes and original artifacts are retained.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(OUT/'run.json', dict(status='completed', completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d),
        cases_per_configuration=396, configurations=p['configurations'], native_rows=len(native),
        invalid80=int(invalid.sum()), common_adjacent_crossing_pairs=int(native.common_adjacent_crossings.sum()),
        protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(OUT/'predictions.csv'),
        analysis_source_sha256=sha(__file__)))
    print('COMPLETED postweight daily panel', len(d), 'rows')


if __name__ == '__main__': main()
