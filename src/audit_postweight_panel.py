"""Independent daily case/source/point/probability/input/log reconstruction."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/postweight_daily_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(x):
    return hashlib.sha256(x.tobytes()).hexdigest()


def close(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-9), (a, b)


def main():
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    protection = json.loads((ROOT/'results/pooled_festival_v1/protected_prior_files.json').read_text())
    for f, h in protection.items():
        assert sha(ROOT/f) == h, f
    source = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    filled, scales = {}, {}
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        y = source[state].to_numpy(copy=True)
        for i in range(len(y)):
            if not np.isfinite(y[i]) or y[i] <= 0:
                y[i] = y[i-7] if i >= 7 and np.isfinite(y[i-7]) else y[i-1] if i else np.nan
        filled[state] = pd.Series(y, index=source.index)
        tr = source[state].loc['2024-01-02':'2025-12-31'].to_numpy()
        assert len(tr) == 730
        scales[state] = mean(abs(tr[i]-tr[i-7]) for i in range(7, 730) if np.isfinite(tr[i]) and np.isfinite(tr[i-7]))
    cases = pd.read_csv(OUT/'cases.csv')
    keys = ['state', 'year', 'origin', 'date', 'horizon']
    reference = set(map(tuple, cases[keys].to_numpy()))
    assert len(reference) == 396
    for (state, h), group in cases.groupby(['state', 'horizon']):
        assert list(sorted(group.date)) == [str(d.date()) for d in pd.date_range('2026-09-15', '2026-10-28')]
        assert (pd.to_datetime(group.origin) >= pd.Timestamp('2026-09-02')).all()
    taskset = set(map(tuple, cases[['state', 'origin']].drop_duplicates().to_numpy()))
    assert len(taskset) == 171
    summary, crossings = {}, []
    for model in ['chronos', 'timesfm']:
        run = json.loads((OUT/model/'run.json').read_text())
        assert run['predictions_sha256'] == sha(OUT/model/'predictions.csv')
        assert run['protocol_sha256'] == sha(OUT/'protocol.json')
        records = json.loads((OUT/model/'inputs.json').read_text())
        assert len(records) == run['inference_tasks'] == 342
        for mode in ['history', 'calendar']:
            selected = [r for r in records if r['mode'] == mode]
            assert {(r['state'], r['origin']) for r in selected} == taskset
            for r in selected:
                origin = pd.Timestamp(r['origin']); dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
                target = filled[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32)
                if mode == 'history':
                    cov = np.empty((0, 744), dtype=np.float32)
                else:
                    columns = [(dates.dayofweek == k).astype(float) for k in range(7)]
                    for k in [1, 2, 3]:
                        columns += [np.sin(2*np.pi*k*dates.dayofyear/365.2425), np.cos(2*np.pi*k*dates.dayofyear/365.2425)]
                    cov = np.asarray(columns, dtype=np.float32)
                assert digest(target) == r['target_sha256'] and digest(cov) == r['covariate_sha256']
                assert r['feature_count'] == (0 if mode == 'history' else 13)
                assert r['future_target_perturbation_invariant'] and pd.Timestamp(r['context_end']) < origin
        solo = json.loads((OUT/model/'solo_batch_audit.json').read_text())
        assert len(solo) == 8
        predicted = pd.read_csv(OUT/model/'predictions.csv')
        qcols = sorted(c for c in predicted if c.startswith('q_'))
        q = predicted[qcols].to_numpy(); assert np.isfinite(q).all()
        bad = np.diff(q, axis=1) < 0
        assert int(bad.sum()) == run['native_quantile_crossings']
        for i, j in zip(*np.where(bad)):
            r = predicted.iloc[i]
            crossings.append(dict(configuration=r.configuration, state=r.state, origin=r.origin, date=r.date, horizon=int(r.horizon),
                lower_level=qcols[j], upper_level=qcols[j+1], lower_prediction=float(q[i,j]), upper_prediction=float(q[i,j+1])))
        prior = json.loads((ROOT/'results/festival_features_v1'/model/'run.json').read_text())
        assert run['weight_sha256'] == prior['weight_sha256']
        summary[model] = dict(reconstructed_input_tasks=len(records), native_crossing_pairs=int(bad.sum()),
            solo_batch_max_difference=max(r['max_difference'] for r in solo), weight_sha256=run['weight_sha256'])
    fit = json.loads((OUT/'classical/fit_log.json').read_text())
    assert len(fit) == 36
    for r in fit:
        old = ROOT/'results'/('strong_refit_v1' if r['model'] == 'ridge' else 'stable_tree_refit_v2')
        selected = pd.read_csv(old/'selected.csv')
        selected = selected[selected.state.eq(r['state']) & selected.year.eq(2026) & selected.horizon.eq(r['horizon']) & selected.model.eq(r['model']) & selected['mode'].eq('rich_calendar')]
        assert len(selected) == 1 and json.loads(selected.parameters.iloc[0]) == r['parameters']
        refit = pd.Timestamp(r['refit']); cutoff = refit-pd.Timedelta(days=1)
        assert refit in [pd.Timestamp('2026-09-01'), pd.Timestamp('2026-10-01')]
        assert pd.Timestamp(r['training_target_max']) <= cutoff
        dates = pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=r['horizon']-1), cutoff)
        labels = source[r['state']].reindex(dates); yy = labels[labels.notna() & labels.gt(0)].to_numpy()
        assert len(yy) == r['training_n'] and digest(yy) == r['training_y_sha256']
    reproduction = json.loads((OUT/'classical/baseline_reproduction.json').read_text())
    assert len(reproduction) == 18 and all(r['common_rows'] > 0 and r['maxdifference'] < 1e-7 for r in reproduction)
    d = pd.read_csv(OUT/'predictions.csv')
    assert len(d) == 3168 and not d.duplicated(['configuration']+keys).any()
    for _, group in d.groupby('configuration'):
        assert set(map(tuple, group[keys].to_numpy())) == reference
    point = defaultdict(list)
    for r in d.itertuples(index=False):
        origin, target = pd.Timestamp(r.origin), pd.Timestamp(r.date)
        assert (target-origin).days == r.horizon-1
        close(r.actual, source.loc[target, r.state]); close(r.mase_scale, scales[r.state])
        if r.configuration in ['last_value', 'weekly_repeat']:
            lag = 1 if r.configuration == 'last_value' else 7-((r.horizon-1)%7)
            close(r.prediction, filled[r.state].loc[origin-pd.Timedelta(days=lag)])
        point[r.configuration, r.state, r.horizon].append(abs(r.actual-r.prediction))
    macro = defaultdict(list)
    for r in pd.read_csv(OUT/'metrics_state.csv').itertuples(index=False):
        errors = point[r.configuration, r.state, r.horizon]
        assert r.n == len(errors) == 44
        close(mean(errors), r.MAE_GWh); close(mean(errors)/scales[r.state], r.MASE)
        macro[r.configuration, r.horizon].append(mean(errors)/scales[r.state])
    for r in pd.read_csv(OUT/'metrics_macro.csv').itertuples(index=False):
        assert len(macro[r.configuration, r.horizon]) == 3
        close(mean(macro[r.configuration, r.horizon]), r.MASE)
    us = defaultdict(lambda: defaultdict(list)); invalid_groups = set()
    for r in pd.read_csv(OUT/'native_uncertainty_cases.csv').to_dict('records'):
        y, scale = r['actual'], r['mase_scale']; q = [r[f'q_{i*100:03d}'] for i in range(1, 10)]
        low, median, high = q[0], q[4], q[8]; invalid = low > high
        assert invalid == r['invalid80']
        loss = mean((i/10)*(y-v) if y >= v else (i/10-1)*(y-v) for i,v in enumerate(q,1))/scale
        width = high-low; interval = width+10*max(low-y, 0)+10*max(y-high, 0)
        values = dict(scaled_mean_pinball=loss, coverage80=float(low <= y <= high), below80=float(y < low), above80=float(y > high),
            scaled_width80=width/scale, scaled_interval_score80=interval/scale, scaled_WIS80_median=(.5*abs(y-median)+.1*interval)/(1.5*scale))
        if invalid:
            invalid_groups.add((r['configuration'], r['horizon']))
        for metric, value in values.items():
            if invalid and metric != 'scaled_mean_pinball':
                assert pd.isna(r[metric])
            else:
                close(value, r[metric])
            us[r['configuration'], r['state'], r['horizon']][metric].append(value)
    um = defaultdict(lambda: defaultdict(list))
    for (configuration, state, h), values in us.items():
        for metric, numbers in values.items():
            assert len(numbers) == 44
            um[configuration, h][metric].append(mean(numbers))
    for r in pd.read_csv(OUT/'native_uncertainty_macro.csv').to_dict('records'):
        for metric, values in um[r['configuration'], r['horizon']].items():
            if (r['configuration'], r['horizon']) in invalid_groups and metric != 'scaled_mean_pinball':
                assert pd.isna(r[metric])
            else: close(mean(values), r[metric])
    pd.DataFrame(crossings, columns=['configuration', 'state', 'origin', 'date', 'horizon', 'lower_level', 'upper_level', 'lower_prediction', 'upper_prediction']).to_csv(OUT/'native_quantile_crossings.csv', index=False)
    result = dict(status='pass', scope='Separate internal source/date/NumPy/point/probability/log audit; not independent human review, full real-time reconstruction or untouched confirmation',
        rows=len(d), cases_per_configuration=396, protected_prior_hashes_unchanged=len(protection),
        models=summary, local_fits=len(fit), matching_original_baseline_groups=len(reproduction),
        native_uncertainty_arithmetic_and_state_weights=True, predictions_sha256=sha(OUT/'predictions.csv'))
    (OUT/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
