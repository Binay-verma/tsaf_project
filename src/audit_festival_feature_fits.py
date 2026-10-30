"""Check fixed budgets, fitting cutoffs and sparse-event support in saved logs."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main(out):
    summaries, support_rows = {}, []
    source = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True)
    ledger = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv', parse_dates=['date'])
    families = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']
    for worker in ['ridge', 'lightgbm', 'lightgbm_capacity2']:
        fit = json.loads((out/worker/'fit_log.json').read_text())
        old = 'strong_refit_v1' if worker == 'ridge' else 'stable_tree_refit_v2'
        selected = pd.read_csv(ROOT/f'results/{old}/selected.csv')
        model = 'ridge' if worker == 'ridge' else 'lightgbm'
        budget = {}
        for r in selected[selected.model.eq(model) & selected['mode'].eq('rich_calendar')].itertuples(index=False):
            params = json.loads(r.parameters)
            if worker == 'lightgbm_capacity2':
                params['min_child_samples'] = 2
            budget[r.state, r.year, r.horizon] = params
        targets = defaultdict(set)
        for r in fit:
            assert r['parameters'] == budget[r['state'], r['year'], r['horizon']]
            assert pd.Timestamp(r['training_target_max']) < pd.Timestamp(r['refit'])
            assert int(r['training_n']) >= 365
            assert pd.Timestamp(r['refit']).day == 1
            expected_features = 40 if r['arm'] == 'calendar' else 75 if '35' in r['arm'] else 45
            assert r['feature_count'] == expected_features
            k = r['state'], r['year'], r['horizon'], r['refit']
            targets[k].add(r['training_y_sha256'])
            support = r.get('feature_nonzero_training_counts', {})
            reconstructed = False
            if not support and r['arm'] in ['day5', 'window5']:
                cutoff = pd.Timestamp(r['refit'])-pd.Timedelta(days=1)
                dates = pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=r['horizon']-1), cutoff)
                labels = source[r['state']].reindex(dates)
                dates = dates[labels.notna() & labels.gt(0)]
                assert len(dates) == r['training_n']
                for family in families:
                    anchors = ledger[ledger.state.eq(r['state']) & ledger.family.eq(family)].date
                    active_dates = list(anchors) if r['arm'] == 'day5' else [d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))]
                    support[family+('_day' if r['arm'] == 'day5' else '_window')] = int(dates.isin(active_dates).sum())
                reconstructed = True
            for name, n in support.items():
                minimum = r['parameters'].get('min_child_samples')
                support_rows.append(dict(model=worker, arm=r['arm'], state=r['state'], year=r['year'], horizon=r['horizon'],
                    refit=r['refit'], feature=name, nonzero_training_rows=n,
                    min_child_samples=minimum, active_support_below_leaf_minimum=bool(minimum and 0 < n < minimum),
                    support_source='Independent date/recorded-label reconstruction' if reconstructed else 'Recorded actual fitting-matrix nonzero counts'))
        assert all(len(v) == 1 for v in targets.values()), 'Adding covariates changed fitting-label cohorts'
        reproduction = json.loads((out/worker/'baseline_reproduction.json').read_text())
        if worker != 'lightgbm_capacity2':
            assert len(reproduction) == 18
        summaries[worker] = dict(fits=len(fit), fixed_parameters_across_arms=True,
            original_preyear_parameters_reused=worker != 'lightgbm_capacity2',
            prespecified_leaf_minimum_override=2 if worker == 'lightgbm_capacity2' else None,
            matching_fitting_label_hashes_across_arms=True,
            old_baseline_checked_groups=len(reproduction),
            max_old_baseline_difference=max((r.get('baseline_old_prediction_maxdiff', r.get('maxdiff', 0.)) for r in reproduction), default=None))
    attempts = json.loads((out/'sarimax/fit_attempts.json').read_text())
    fits = defaultdict(list)
    for r in attempts:
        fits[r['state'], r['year'], r['configuration']].append(r)
        assert pd.Timestamp(r['training_end']) == pd.Timestamp(f"{r['year']-1}-12-31")
        assert np.isfinite(r['training_loglikelihood'])
    assert all(v[-1]['converged'] for v in fits.values())
    assert all(not r['converged'] for values in fits.values() for r in values[:-1])
    deployments = json.loads((out/'sarimax/deployments.json').read_text())
    for r in deployments:
        origin = pd.Timestamp(r['origin'])
        assert pd.Timestamp(r['fitting_target_max']) < origin
        assert pd.Timestamp(r['context_max']) == origin-pd.Timedelta(days=1)
    summaries['sarimax'] = dict(converged_parameter_fits=len(fits), optimizer_attempts=len(attempts),
        unsuccessful_attempts_retained=sum(not r['converged'] for r in attempts), deployment_tasks=len(deployments), past_only_state_updates=True)
    pd.DataFrame(support_rows).to_csv(out/'training_feature_support.csv', index=False)
    result = dict(status='pass', model_checks=summaries,
        sparse_capacity_note='Features with fewer active fitting rows than a tree leaf minimum cannot isolate those rare rows in a valid split. This is a capacity limitation, not proof of intrinsic event irrelevance. Capacity2 remains a separately reported sensitivity, not a selected winner.',
        scope='Internal budget/log audit, not independent human review or exhaustive implementation proof')
    (out/'fitting_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=ROOT/'results/festival_features_v1')
    main(p.parse_args().out.resolve())
