"""Fixed six-model engine for manual future issuance; no selection on scores.

Called only after execution/time/source/calendar gates. Internal fixtures may
inject predictors, without changing the production CLI or creating issuances.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

from forecasting import causal_fill
from robust_baselines import rich_history, fitting_cases
from rolling_evidence_v1 import (
    ROOT, STATES, MODELS, ARMS, LEADS, FAMILIES, covariates,
    available_history, frozen_scales, target_contract, planned, sha)


def digest(array):
    array = np.ascontiguousarray(array)
    import hashlib
    return dict(sha256=hashlib.sha256(array.tobytes()).hexdigest(),
                shape=list(array.shape), dtype=str(array.dtype))


def direct_arrays(history, state, horizon, arm, anchors, fake, number):
    contract = target_contract(planned(number))
    origin, cutoff = pd.Timestamp(contract['model_origin']), pd.Timestamp(contract['context_last_date'])
    index = pd.date_range(history.index.min(), origin+pd.Timedelta(days=15))
    observed = history[state].reindex(index)
    cov = covariates(index, state, arm, anchors, fake)
    frame = rich_history(observed, horizon)
    future_cov = cov.reindex(index+pd.Timedelta(days=horizon-1)).copy()
    future_cov.index = index
    frame = pd.concat([frame, future_cov], axis=1)
    x, y, log = fitting_cases(frame, observed, horizon, cutoff)
    query = frame.reindex([origin]).to_numpy()
    if not np.isfinite(query).all() or log['training_target_max'] > contract['context_last_date']:
        raise ValueError('Nonfinite or future direct-model inputs')
    return x, y, query, log


def fixed_direct(name):
    if name == 'ridge_fixed10':
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import Ridge
        return make_pipeline(StandardScaler(), Ridge(alpha=10))
    from lightgbm import LGBMRegressor
    return LGBMRegressor(num_leaves=7, n_estimators=200, learning_rate=.05,
        reg_lambda=10, min_child_samples=20 if name == 'tree_leaf20_fixed' else 2,
        n_jobs=1, random_state=42, deterministic=True, force_col_wise=True, verbosity=-1)


def foundation_input(history, state, arm, anchors, fake, number):
    contract = target_contract(planned(number))
    origin = pd.Timestamp(contract['model_origin'])
    dates = pd.date_range(origin-pd.Timedelta(days=730), periods=746)
    target = causal_fill(history[state]).reindex(dates[:730]).to_numpy(dtype=np.float32)
    cov = covariates(dates, state, arm, anchors, fake).to_numpy(dtype=np.float32).T
    if target.shape != (730,) or cov.shape != (13 if arm == 'calendar' else 18, 746) or not np.isfinite(target).all() or not np.isfinite(cov).all():
        raise ValueError('Foundation context/covariate contract failed')
    return target, cov


def provider(name):
    import torch
    torch.set_num_threads(2)
    torch.manual_seed(42)
    np.random.seed(42)
    if name == 'chronos':
        from chronos import Chronos2Pipeline
        identity = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
        for item in identity['files']:
            if sha(item['path']) != item['sha256']:
                raise ValueError('Chronos bytes changed')
        weight = next(item for item in identity['files'] if item['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weight['path']).parent), device_map='cpu', local_files_only=True)
        levels = list(model.quantiles)

        def predict(inputs):
            packed = []
            for target, cov in inputs:
                packed.append(dict(target=target,
                    past_covariates={f'c{k}': values[:730] for k, values in enumerate(cov)},
                    future_covariates={f'c{k}': values[730:] for k, values in enumerate(cov)}))
            results = model.predict(packed, prediction_length=16, batch_size=128, context_length=730, cross_learning=False)
            quantiles = [item[0].detach().cpu().numpy().T for item in results]
            return [(q[:, levels.index(.5)], q) for q in quantiles]
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        identity = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
        if sha(identity['path']) != identity['sha256']:
            raise ValueError('TimesFM bytes changed')
        weight = identity
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(weight['path']).parent),
            device='cpu', per_core_batch_size=1, local_files_only=True))
        levels = [k/10 for k in range(1, 10)]

        def predict(inputs):
            output = list(model.predict_batch([item[0] for item in inputs], horizon=16,
                past_future_covariates=[item[1] for item in inputs],
                return_quantiles=True, use_symmetric_averaging=False))
            return [(np.asarray(item.forecast).squeeze(), np.asarray(item.quantiles).squeeze()) for item in output]
    return predict, levels, weight['sha256']


def forecast(source, anchors, fake, number, progress=lambda value: None,
             direct_factory=fixed_direct, provider_factory=provider, sarimax_factory=None):
    history = available_history(source, number)
    scales = frozen_scales(history, number)
    contract = target_contract(planned(number))
    rows, paths, fits, inputs, solos = [], [], [], [], []

    def save():
        progress(dict(fit_log=fits, inputs=inputs, solo_batch_audit=solos))

    def base(model, arm, state, lead):
        day = contract['targets'][str(lead)]
        families = [family for family in FAMILIES if any(abs((pd.Timestamp(day)-date).days) <= 3
            for date in pd.to_datetime(anchors[anchors.state.eq(state)&anchors.family.eq(family)].date))]
        return dict(model=model, arm=arm, state=state, decision_lead=lead,
            model_step=lead+2, date=day, context_last_date=contract['context_last_date'],
            model_origin=contract['model_origin'], mase_scale=scales[state],
            event_families='|'.join(families))

    for state in STATES:
        for arm in ARMS:
            for lead in LEADS:
                x, y, query, log = direct_arrays(history, state, lead+2, arm, anchors, fake, number)
                for name in MODELS[:3]:
                    xx = x.astype(np.float32) if name.startswith('tree_') else x
                    qq = query.astype(np.float32) if name.startswith('tree_') else query
                    model = direct_factory(name)
                    entry = dict(model=name, state=state, arm=arm, model_step=lead+2,
                        **log, training_X=digest(xx), training_y=digest(y), query_X=digest(qq), status='started')
                    fits.append(entry)
                    try:
                        model.fit(xx, y)
                        prediction = float(model.predict(qq)[0])
                        rows.append(dict(base(name, arm, state, lead), prediction=prediction))
                        entry['status'] = 'completed'
                    except BaseException as error:
                        entry.update(status='failed', error=repr(error))
                        raise
                    finally:
                        save()
            cutoff = pd.Timestamp(contract['context_last_date'])
            dates = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff)
            target = causal_fill(history[state]).reindex(dates)/100
            future = pd.date_range(contract['model_origin'], periods=16)
            cov = covariates(dates.append(future), state, arm, anchors, fake)
            if sarimax_factory is None:
                from statsmodels.tsa.statespace.sarimax import SARIMAX
                from multifestival_models import fit_checked
                try:
                    fitted = fit_checked(SARIMAX(target, exog=cov.reindex(dates), order=(1, 0, 0),
                        seasonal_order=(1, 0, 0, 7), trend='n', enforce_stationarity=False),
                        'sarimax', fits, dict(model='sarimax_fixed', state=state, arm=arm,
                            training_target_max=contract['context_last_date'], training_X=digest(cov.reindex(dates).to_numpy()),
                            training_y=digest(target.to_numpy())))
                finally:
                    save()
                prediction = np.asarray(fitted.get_forecast(16, exog=cov.reindex(future)).predicted_mean)*100
            else:
                prediction = np.asarray(sarimax_factory(target.to_numpy(), cov.reindex(dates).to_numpy(), cov.reindex(future).to_numpy()))*100
            if prediction.shape != (16,):
                raise ValueError('SARIMAX horizon contract')
            for lead in LEADS:
                rows.append(dict(base('sarimax_fixed', arm, state, lead), prediction=float(prediction[lead+1])))
            save()
    for name in ['chronos', 'timesfm']:
        predict, levels, weight_sha256 = provider_factory(name)
        if not all(k/10 in levels for k in range(1, 10)):
            raise ValueError('Missing native common quantiles')
        for arm in ARMS:
            packed = [foundation_input(history, state, arm, anchors, fake, number) for state in STATES]
            results = predict(packed)
            if len(results) != 3:
                raise ValueError('Incomplete provider batch')
            for state, (target, cov), (point, q) in zip(STATES, packed, results):
                individual_point, individual_q = predict([(target, cov)])[0]
                if point.shape != (16,) or q.shape != (16, len(levels)) or not np.isfinite(q).all() or not np.isfinite(point).all():
                    raise ValueError('Foundation output shape/finiteness')
                np.testing.assert_allclose(point, individual_point, rtol=2e-4, atol=1e-3)
                np.testing.assert_allclose(q, individual_q, rtol=2e-4, atol=1e-3)
                solos.append(dict(model=name, arm=arm, state=state,
                    maximum_absolute_difference_GWh=float(max(abs(point-individual_point).max(), abs(q-individual_q).max()))))
                inputs.append(dict(model=name, arm=arm, state=state, target=digest(target), covariates=digest(cov),
                    context_end=contract['context_last_date'], weight_sha256=weight_sha256,
                    native_levels=levels, native_crossing_pairs=int((np.diff(q, axis=1) < 0).sum())))
                for step in range(1, 17):
                    record = dict(model=name, arm=arm, state=state, model_step=step,
                        date=str((pd.Timestamp(contract['model_origin'])+pd.Timedelta(days=step-1)).date()),
                        prediction=float(point[step-1]),
                        **{f'q_{round(level*1000):03d}': float(q[step-1, j]) for j, level in enumerate(levels)})
                    paths.append(record)
                    if step in [3, 9, 16]:
                        row = base(name, arm, state, step-2)
                        row.update(prediction=record['prediction'], **{key: value for key, value in record.items() if key.startswith('q_')})
                        rows.append(row)
            save()
    return pd.DataFrame(rows), pd.DataFrame(paths), dict(fit_log=fits, inputs=inputs, solo_batch_audit=solos)
