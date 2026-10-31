"""Historical API checks only: no outcomes, score, issuance, or source retrieval."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import numpy as np
import pandas as pd

from forecasting import causal_fill
from rolling_evidence_v1 import ROOT, STATES, ARMS, covariates, dump, sha
from rolling_models_v1 import provider, digest

OUT = ROOT/'review/rolling_runtime_smoke_v1'


def register():
    if OUT.exists():
        raise FileExistsError('Preserve earlier smoke attempt')
    inputs = ['src/smoke_rolling_runtime_v1.py', 'src/rolling_models_v1.py',
        'src/rolling_evidence_v1.py', 'src/rolling_execution_v1.py',
        'results/rolling_confirmation_runtime_v1/registration.json',
        'data/external/latest_state_energy_GWh.csv',
        'results/calendar_semantics_v2/anchors_2022_2025.csv',
        'results/calendar_recenter_recovery_v1/placebo_anchors.csv']
    OUT.mkdir()
    dump(OUT/'registration.json', dict(registered_utc=datetime.now(timezone.utc).isoformat(),
        scope='No new scientific performance experiment or future issuance. Actual pinned model API on cached730-day historical inputs ending30September2025, horizon16, all8arms/3states/bothproviders. No targetactuals or errors computed; retain hashes, shapes andsolobatch consistency. Additional actualSARIMAXcalendar fit/get_forecast API check, no scoring.',
        tolerance='UNCHANGED rtol2e-4/atol1e-3GWh forsolo/batch, no repairs or score-based choices',
        inputs={name: sha(ROOT/name) for name in inputs}))


def run():
    if (OUT/'started.json').exists():
        raise FileExistsError('Preserve prior smoke execution')
    registration = json.loads((OUT/'registration.json').read_text())
    for name, expected in registration['inputs'].items():
        assert sha(ROOT/name) == expected, name
    from rolling_execution_v1 import validate_registration
    validate_registration()
    dump(OUT/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat()))
    records, fits = [], []
    try:
        origin = pd.Timestamp('2025-10-01')
        dates = pd.date_range(origin-pd.Timedelta(days=730), periods=746)
        # Trim BEFORE constructing inputs; no historical future labels loaded into models.
        source = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).loc[:origin-pd.Timedelta(days=1)]
        anchors = pd.read_csv(ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv')
        fake = pd.read_csv(ROOT/'results/calendar_recenter_recovery_v1/placebo_anchors.csv')
        for name in ['chronos', 'timesfm']:
            predict, levels, weight = provider(name)
            for arm in ARMS:
                inputs = [(causal_fill(source[state]).reindex(dates[:730]).to_numpy(dtype=np.float32),
                           covariates(dates, state, arm, anchors, fake).to_numpy(dtype=np.float32).T) for state in STATES]
                results = predict(inputs)
                assert len(results) == 3
                for state, (target, cov), (point, q) in zip(STATES, inputs, results):
                    individual_point, individual_q = predict([(target, cov)])[0]
                    assert point.shape == (16,) and q.shape == (16, len(levels))
                    assert np.isfinite(point).all() and np.isfinite(q).all()
                    np.testing.assert_allclose(point, individual_point, rtol=2e-4, atol=1e-3)
                    np.testing.assert_allclose(q, individual_q, rtol=2e-4, atol=1e-3)
                    records.append(dict(model=name, arm=arm, state=state, weight_sha256=weight,
                        target=digest(target), covariates=digest(cov), point=digest(point), quantiles=digest(q),
                        native_crossing_pairs=int((np.diff(q, axis=1) < 0).sum()),
                        max_solo_batch_difference_GWh=float(max(abs(point-individual_point).max(), abs(q-individual_q).max()))))
                dump(OUT/'provider_checks.json', records)
                print(name, arm, 'API/solo pass', flush=True)
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from multifestival_models import fit_checked
        target = causal_fill(source['Delhi']).reindex(dates[:730])/100
        cov = covariates(dates, 'Delhi', 'calendar', anchors, fake)
        fitted = fit_checked(SARIMAX(target, exog=cov.iloc[:730], order=(1, 0, 0),
            seasonal_order=(1, 0, 0, 7), trend='n', enforce_stationarity=False),
            'sarimax', fits, dict(scope='historicalAPIonly', state='Delhi', training_end='2025-09-30'))
        prediction = np.asarray(fitted.get_forecast(16, exog=cov.iloc[730:]).predicted_mean)*100
        assert prediction.shape == (16,) and np.isfinite(prediction).all()
        dump(OUT/'sarimax_fit.json', fits)
        dump(OUT/'result.json', dict(status='pass', completed_utc=datetime.now(timezone.utc).isoformat(),
            provider_input_blocks=len(records), all_arms=8, states=3, providers=2, horizon=16,
            actual_sarimax_converged=bool(fitted.mle_retvals['converged']), sarimax_output=digest(prediction),
            scope='CachedhistoricalAPI/actualweight/shape/finiteness/solobatch check, no performance scores, independenthumanreview or futureissuance. No network/actualoutcomes/scheduleractivation.',
            registration_sha256=sha(OUT/'registration.json')))
    except BaseException:
        dump(OUT/'sarimax_fit.json', fits)
        (OUT/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'run'])
    register() if parser.parse_args().action == 'register' else run()
