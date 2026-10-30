"""Past-only calibration of archived point forecasts; no coverage guarantee."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import ROOT


OUT = ROOT/'results/residual_intervals_v1'


def calibrate(history, origin, point, quantiles):
    a = history[history.date.ge(origin-pd.Timedelta(days=730)) & history.date.lt(origin)]
    residuals = (a.actual-a.prediction).dropna().to_numpy()
    if len(residuals) < 365:
        raise ValueError(f'Only {len(residuals)} preceding recorded residuals')
    q = point + np.quantile(residuals, quantiles, method='linear')
    assert np.isfinite(q).all() and (np.diff(q) >= 0).all()
    return q, len(residuals), a.loc[a.actual.notna(), 'date'].max()


def main():
    protocol = json.loads((OUT/'protocol.json').read_text())
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Preserve this run; version a new output directory')
    path = ROOT/'results/extended_validation/all_verified_predictions.csv'
    data = pd.read_csv(path, parse_dates=['origin', 'date'])
    rows = []
    for (state, model, mode, h), g in data.groupby(['state', 'model', 'mode', 'horizon']):
        if mode not in protocol['models'].get(model, []) or not g.cohort.eq('daily').all():
            continue
        for row in g[g.year.isin(protocol['years'])].itertuples():
            q, n, end = calibrate(g, row.origin, row.prediction, protocol['quantiles'])
            assert end < row.origin
            rows.append(dict(state=state, model=model, mode=mode, horizon=h,
                origin=row.origin, date=row.date, year=row.year, actual=row.actual,
                point=row.prediction, mase_scale=row.mase_scale, event=row.festival_window,
                q05=q[0], q50=q[1], q95=q[2], calibration_n=n, calibration_target_max=end))
        print('Calibrated', state, model, mode, h, flush=True)
    d = pd.DataFrame(rows)
    sets = [set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy()))
            for _, g in d.groupby(['model', 'mode'])]
    assert len(sets) == 4 and all(s == sets[0] for s in sets)
    assert not d.duplicated(['state', 'model', 'mode', 'horizon', 'origin']).any()
    d['covered'] = ((d.actual >= d.q05) & (d.actual <= d.q95)).astype(float)
    d['scaled_width'] = (d.q95-d.q05)/d.mase_scale
    d['scaled_interval_score'] = (d.q95-d.q05 + 20*np.maximum(d.q05-d.actual, 0)
                                  + 20*np.maximum(d.actual-d.q95, 0))/d.mase_scale
    scores = []
    for q, column in [(0.05, 'q05'), (0.5, 'q50'), (0.95, 'q95')]:
        error = d.actual-d[column]
        scores.append(np.maximum(q*error, (q-1)*error)/d.mase_scale)
    d['scaled_mean_pinball'] = np.mean(scores, axis=0)
    d.to_csv(OUT/'predictions.csv', index=False)
    metrics = []
    for scope, mask in [('all', np.ones(len(d), bool)), ('event', d.event.eq(1)),
                        ('non_event', d.event.eq(0))]:
        m = d[mask].groupby(['state', 'year', 'model', 'mode', 'horizon']).agg(
            coverage=('covered', 'mean'), scaled_width=('scaled_width', 'mean'),
            scaled_interval_score=('scaled_interval_score', 'mean'),
            scaled_mean_pinball=('scaled_mean_pinball', 'mean'), n=('actual', 'size')).reset_index()
        m['scope'] = scope
        metrics.append(m)
    m = pd.concat(metrics, ignore_index=True)
    m.to_csv(OUT/'metrics_state_year.csv', index=False)
    # Equal state/year weighting; do not pool event days as independent trials.
    macro = m.groupby(['model', 'mode', 'horizon', 'scope'])[
        ['coverage', 'scaled_width', 'scaled_interval_score', 'scaled_mean_pinball']].mean().reset_index()
    macro.to_csv(OUT/'metrics_macro.csv', index=False)
    info = {'rows': len(d), 'cases_per_configuration': len(sets[0]),
        'protocol_sha256': hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest(),
        'source_predictions_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'calibration_min_n': int(d.calibration_n.min()),
        'checks': ['strictly past target residuals', 'matched cases across four configurations',
                   'finite noncrossing quantiles', 'unique cases'],
        'warning': 'Retrospective exploratory residual intervals; not native TSFM distributions or guaranteed coverage'}
    (OUT/'run.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
