"""Persisted deployment/provenance checks supplement the stdlib metric audit."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import ROOT
from multifestival_cached import KEY, sha, dump

OUT = ROOT/'results/multifestival_models_v1'


def main():
    p = json.loads((OUT/'protocol.json').read_text())
    for f, h in p['input_hashes'].items():
        assert sha(ROOT/f) == h, f
    assert sha(OUT/'expected_cases.csv') == p['cases_sha256']
    cases = pd.read_csv(OUT/'expected_cases.csv')
    tasks = set(map(tuple, cases[['state', 'origin']].drop_duplicates().to_numpy()))
    deployment = pd.read_csv(OUT/'classical/deployments.csv', parse_dates=['origin', 'fitting_target_max', 'context_target_max'])
    assert len(deployment) == len(tasks)*3
    assert (deployment.fitting_target_max < deployment.origin).all()
    assert (deployment.context_target_max == deployment.origin-pd.Timedelta(days=1)).all()
    for r in deployment.itertuples(index=False):
        if r.configuration.startswith('sarimax'):
            assert r.fitting_target_max == pd.Timestamp(f'{r.origin.year-1}-12-31')
        else:
            assert r.fitting_target_max == r.origin.replace(day=1)-pd.Timedelta(days=1)
    attempts = json.loads((OUT/'classical/fit_attempts.json').read_text())
    fits = {}
    for a in attempts:
        key = a['configuration'], a['state'], a['training_end']
        fits.setdefault(key, []).append(a)
        assert np.isfinite(a['training_loglikelihood'])
    assert all(v[-1]['converged'] for v in fits.values())
    assert sum(k[0].startswith('sarimax') for k in fits) == 12
    assert all(not a['converged'] for v in fits.values() for a in v[:-1])
    results = dict(classical_fit_groups=len(fits), classical_attempts=len(attempts),
        unsuccessful_attempts_retained=sum(not a['converged'] for a in attempts),
        deployment_tasks=len(deployment), past_only_deployments=True)
    old = pd.read_csv(ROOT/'results/timesfm_matched_events_v1/predictions.csv')
    old_chronos = pd.read_csv(ROOT/'results/mechanism_controls_v1/chronos2/predictions.csv')
    old_chronos = old_chronos[old_chronos.arm.eq('calendar')]
    comparisons, crossing_rows = [], []
    for worker, modes in [('chronos', ['calendar']), ('timesfm', ['history', 'calendar'])]:
        run = json.loads((OUT/worker/'run.json').read_text())
        assert run['protocol_sha256'] == sha(OUT/'protocol.json')
        assert run['predictions_sha256'] == sha(OUT/worker/'predictions.csv')
        inputs = json.loads((OUT/worker/'inputs.json').read_text())
        for mode in modes:
            g = [x for x in inputs if x['mode'] == mode]
            assert len(g) == len(tasks)
            assert {(x['state'], x['origin']) for x in g} == tasks
            assert all(x['future_target_perturbation_invariant'] for x in g)
            assert all(pd.Timestamp(x['last_context_date']) == pd.Timestamp(x['origin'])-pd.Timedelta(days=1) for x in g)
        solo = json.loads((OUT/worker/'solo_batch_audit.json').read_text())
        assert len(solo) == 4*len(modes)
        new = pd.read_csv(OUT/worker/'predictions.csv')
        qcols = sorted(c for c in new if c.startswith('q_'))
        q = new[qcols].to_numpy()
        assert np.isfinite(q).all()
        crossings = np.diff(q, axis=1) < 0
        assert int(crossings.sum()) == run['native_quantile_crossings']
        for i, j in zip(*np.where(crossings)):
            r = new.iloc[i]
            crossing_rows.append(dict(worker=worker, family=r.family, state=r.state, origin=r.origin,
                date=r.date, horizon=int(r.horizon), lower_level=qcols[j], upper_level=qcols[j+1],
                lower_prediction=float(q[i, j]), upper_prediction=float(q[i, j+1]),
                treatment='Retained unmodified; no sorting or clipping'))
        for mode in modes:
            ng = new[new.configuration.eq(worker+'_'+mode)]
            og = old_chronos if worker == 'chronos' else old[old['mode'].eq(mode)]
            comparison = ng.merge(og[KEY+['prediction']], on=KEY, suffixes=('_new', '_old'), validate='one_to_one')
            assert len(comparison) == 150
            maxdiff = float(abs(comparison.prediction_new-comparison.prediction_old).max())
            # Report differences rather than selecting old/new predictions.
            comparisons.append(dict(worker=worker, mode=mode, same_old_Diwali_cases=len(comparison),
                max_abs_prediction_difference=maxdiff,
                within_batch_tolerance=bool(np.allclose(comparison.prediction_new, comparison.prediction_old, rtol=2e-4, atol=1e-3))))
        results[worker] = dict(inference_tasks=run['inference_tasks'], native_quantile_crossings=run['native_quantile_crossings'],
            weight_sha256=run['weight_sha256'], all_inputs_past_only=True, first_batch_solo_checks=solo)
    results['old_Diwali_reproduction_diagnostics'] = comparisons
    pd.DataFrame(crossing_rows, columns=['worker', 'family', 'state', 'origin', 'date', 'horizon',
        'lower_level', 'upper_level', 'lower_prediction', 'upper_prediction', 'treatment']).to_csv(OUT/'native_quantile_crossings.csv', index=False)
    results['native_quantile_quality'] = dict(crossing_pairs=len(crossing_rows),
        treatment='All native quantiles retained; point-score audit does not establish valid ordered/calibrated uncertainty')
    results['status'] = 'pass'
    results['scope'] = 'Internal software/provenance audit. Not independent human review; historical publication availability and pretraining overlap remain unresolved.'
    dump(OUT/'deployment_audit.json', results)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
