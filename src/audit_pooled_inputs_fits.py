"""Reconstruct input bytes and check fitted budgets without experiment helpers."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/pooled_festival_v1'


def digest(x):
    return hashlib.sha256(x.tobytes()).hexdigest()


def main():
    source = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    ledger = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv', parse_dates=['date'])
    filled = {}
    for state in source:
        values = source[state].to_numpy(dtype=float, copy=True)
        for i in range(len(values)):
            if not np.isfinite(values[i]) or values[i] <= 0:
                values[i] = values[i-7] if i >= 7 and np.isfinite(values[i-7]) else values[i-1] if i else np.nan
        filled[state] = pd.Series(values, index=source.index)

    def extra(dates, state, arm):
        width = 5 if arm.endswith('5') else 1
        anchors = ledger[ledger.state.eq(state)].date
        active = list(anchors)
        if 'window' in arm:
            active = [d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))]
        flag = np.zeros(len(dates)) if arm == 'zero1' else dates.isin(active).astype(float)
        return [flag]+[np.zeros(len(dates)) for _ in range(width-1)]

    summaries, crossings, support = {}, [], []
    for cohort in ['event', 'non_event']:
        out = OUT/cohort
        protocol = json.loads((out/'protocol.json').read_text())
        cases = pd.read_csv(out/'primary_cases.csv', parse_dates=['date', 'origin'])
        tasks = {(r.state, str(r.origin.date())) for r in cases.itertuples(index=False)}
        checked = {}
        for model in ['chronos', 'timesfm']:
            run = json.loads((out/model/'run.json').read_text())
            inputs = json.loads((out/model/'inputs.json').read_text())
            assert len(inputs) == 360
            for arm in protocol['arms']:
                selected = [r for r in inputs if r['arm'] == arm]
                assert {(r['state'], r['origin']) for r in selected} == tasks
                for r in selected:
                    origin = pd.Timestamp(r['origin'])
                    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=744)
                    assert dates.min() >= pd.Timestamp('2022-01-01') and dates.max() <= pd.Timestamp('2025-12-31')
                    target = filled[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32)
                    columns = [(dates.dayofweek == k).astype(float) for k in range(7)]
                    for k in [1, 2, 3]:
                        columns += [np.sin(2*np.pi*k*dates.dayofyear/365.2425), np.cos(2*np.pi*k*dates.dayofyear/365.2425)]
                    columns += extra(dates, r['state'], arm)
                    cov = np.asarray(columns, dtype=np.float32)
                    assert digest(target) == r['target_sha256'], (cohort, model, arm, r['origin'], 'target')
                    assert digest(cov) == r['covariate_sha256'], (cohort, model, arm, r['origin'], 'covariates')
                    assert r['feature_count'] == len(columns)
                    assert r['context_end'] == str((origin-pd.Timedelta(days=1)).date())
                    assert r['future_target_perturbation_invariant']
                    assert np.count_nonzero(cov[13:, :730], axis=1).tolist() == r['past_nonzero_counts']
            solo = json.loads((out/model/'solo_batch_audit.json').read_text())
            assert len(solo) == 20
            assert all(r['max_abs_difference'] < .01 for r in solo)
            predicted = pd.read_csv(out/model/'predictions.csv')
            qcols = sorted(c for c in predicted if c.startswith('q_'))
            q = predicted[qcols].to_numpy()
            assert np.isfinite(q).all()
            bad = np.diff(q, axis=1) < 0
            assert int(bad.sum()) == run['native_quantile_crossings']
            for i, j in zip(*np.where(bad)):
                r = predicted.iloc[i]
                crossings.append(dict(cohort=cohort, model=model, arm=r.arm, family=r.family,
                    state=r.state, origin=r.origin, date=r.date, horizon=int(r.horizon),
                    lower_level=qcols[j], upper_level=qcols[j+1],
                    lower_prediction=float(q[i, j]), upper_prediction=float(q[i, j+1])))
            prior_name = 'festival_features_v1' if cohort == 'event' else 'festival_feature_spillover_v2'
            prior = json.loads((ROOT/'results'/prior_name/model/'run.json').read_text())
            assert run['weight_sha256'] == prior['weight_sha256']
            checked[model] = dict(reconstructed_input_tasks=len(inputs), native_quantile_crossings=int(bad.sum()),
                max_solo_batch_difference=max(r['max_abs_difference'] for r in solo), weight_sha256=run['weight_sha256'])
        for worker in ['ridge', 'lightgbm', 'lightgbm_capacity2']:
            old = 'strong_refit_v1' if worker == 'ridge' else 'stable_tree_refit_v2'
            model = 'ridge' if worker == 'ridge' else 'lightgbm'
            selected = pd.read_csv(ROOT/f'results/{old}/selected.csv')
            selected = selected[selected.model.eq(model) & selected['mode'].eq('rich_calendar')]
            budget = {}
            for r in selected.itertuples(index=False):
                params = json.loads(r.parameters)
                if worker == 'lightgbm_capacity2':
                    params['min_child_samples'] = 2
                budget[r.state, r.year, r.horizon] = params
            fits = json.loads((out/worker/'fit_log.json').read_text())
            assert len(fits) == json.loads((out/worker/'run.json').read_text())['fits']
            groups = defaultdict(list)
            parent = ROOT/'results'/('festival_features_v1' if cohort == 'event' else 'festival_feature_spillover_v2')
            parentfits = json.loads((parent/worker/'fit_log.json').read_text())
            parent_y = {(r['state'], r['year'], r['horizon'], r['refit']): r['training_y_sha256'] for r in parentfits}
            for r in fits:
                assert r['parameters'] == budget[r['state'], r['year'], r['horizon']]
                cutoff = pd.Timestamp(r['refit'])-pd.Timedelta(days=1)
                assert pd.Timestamp(r['training_target_max']) <= cutoff and pd.Timestamp(r['refit']).day == 1
                segment = cases[cases.state.eq(r['state']) & cases.year.eq(r['year']) & cases.horizon.eq(r['horizon']) & cases.origin.dt.to_period('M').eq(pd.Timestamp(r['refit']).to_period('M'))]
                assert len(segment) and segment.origin.min() > cutoff
                width = 5 if r['arm'].endswith('5') else 1
                assert r['feature_count'] == 40+width
                dates = pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=r['horizon']-1), cutoff)
                labels = source[r['state']].reindex(dates)
                dates = dates[labels.notna() & labels.gt(0)]
                assert len(dates) == r['training_n']
                counts = np.count_nonzero(extra(dates, r['state'], r['arm']), axis=1).astype(int).tolist()
                assert counts == list(r['feature_nonzero_training_counts'].values())
                k = r['state'], r['year'], r['horizon'], r['refit']
                assert r['training_y_sha256'] == parent_y[k]
                groups[k].append(r)
                support.append(dict(cohort=cohort, model=worker, arm=r['arm'], state=r['state'], year=r['year'],
                    horizon=r['horizon'], refit=r['refit'], event_active_training_rows=counts[0],
                    padding_nonzero_rows=sum(counts[1:]), min_child_samples=r['parameters'].get('min_child_samples')))
            assert all({r['arm'] for r in values} == set(protocol['arms']) for values in groups.values())
            checked[worker] = dict(fits=len(fits), unchanged_original_parameters_and_labels=True,
                independently_reconstructed_support=True, chronological_cutoffs=True,
                baseline_reuse_note='No calendar refit; exact parent labels and fixed budgets verified against all fitting groups')
        attempts = json.loads((out/'sarimax/fit_attempts.json').read_text())
        groups = defaultdict(list)
        for r in attempts:
            assert pd.Timestamp(r['training_end']) == pd.Timestamp(f"{r['year']-1}-12-31")
            assert np.isfinite(r['training_loglikelihood'])
            groups[r['state'], r['year'], r['configuration']].append(r)
        assert len(groups) == 30 and all(v[-1]['converged'] for v in groups.values())
        assert all(not r['converged'] for v in groups.values() for r in v[:-1])
        deployments = json.loads((out/'sarimax/deployments.json').read_text())
        assert len(deployments) == 360
        for r in deployments:
            origin = pd.Timestamp(r['origin'])
            assert pd.Timestamp(r['fitting_target_max']) < origin
            assert pd.Timestamp(r['context_max']) == origin-pd.Timedelta(days=1)
        checked['sarimax'] = dict(converged_parameter_fits=len(groups), optimizer_attempts=len(attempts),
            unsuccessful_attempts_retained=sum(not r['converged'] for r in attempts), past_only_state_updates=True)
        summaries[cohort] = checked
    pd.DataFrame(support).to_csv(OUT/'training_support.csv', index=False)
    pd.DataFrame(crossings, columns=['cohort', 'model', 'arm', 'family', 'state', 'origin', 'date', 'horizon',
        'lower_level', 'upper_level', 'lower_prediction', 'upper_prediction']).to_csv(OUT/'native_quantile_crossings.csv', index=False)
    result = dict(status='pass', scope='Internal separate date/NumPy byte reconstruction and saved-log audit; not independent human review',
        cohorts=summaries, total_native_quantile_crossing_pairs=len(crossings), quantile_treatment='Native outputs unchanged; no sorting/clipping')
    (OUT/'inputs_fits_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
