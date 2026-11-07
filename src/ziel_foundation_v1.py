"""Ziel (2018) hSun and replacing (Rph, RpH) channels through Chronos-2 and TimesFM-3 (India).

Exploratory; same 528 event-window and 216 ordinary document-aligned cases, context (730 days),
14-day horizon, pinned weights, threads, seed and batch as the parent breadth study. Arms are the
18-channel frames of ziel_replacing_v1 (sunday_day) and ziel_replacing_v2 (replace_pooled,
replace_typed), plus the reference arms calendar, day5 and pooled_day5, which must reproduce the
stored document-aligned foundation forecasts within the parent's batch tolerance.

Colab steps (see docs/reproduction/ZIEL_FOUNDATION_COLAB.md):
  python src/ziel_foundation_v1.py weights            # download pinned weights, verify SHA-256
  python src/ziel_foundation_v1.py chronos --cohort event_window   (and ordinary; then timesfm)
  python src/ziel_foundation_analysis_v1.py
The protocol was committed before any forecast of this study existed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from calendar_semantics_study_v2 import frames as aligned_frames
import ziel_replacing_v1 as v1
import ziel_replacing_v2 as v2

OUT = ROOT/'results/ziel_foundation_v1'
ARMS = ['calendar', 'day5', 'pooled_day5', 'sunday_day', 'replace_pooled', 'replace_typed']
REFERENCE_ARMS = ['calendar', 'day5', 'pooled_day5']
MODELS = ['chronos', 'timesfm']
COHORTS = ['event_window', 'ordinary']
CHRONOS_REV = '29ec3766d36d6f73f0696f85560a422f50e8498c'
TIMESFM_REV = '43046b85ec22d584a13f8098c2ed39c889e129c2'
TIMESFM_CODE = 'e51928e27119cb17bebc005be2696b75e0a9e688'
CACHE = Path('/content/model-cache')


def frames(index, state):
    a = v1.frames(index, state)
    b = v2.frames(index, state)
    for arm in REFERENCE_ARMS:
        assert a[arm].equals(b[arm])
    out = {arm: a[arm] for arm in REFERENCE_ARMS}
    out['sunday_day'] = a['sunday_day']
    out['replace_pooled'] = b['replace_pooled']
    out['replace_typed'] = b['replace_typed']
    return {arm: out[arm] for arm in ARMS}


INPUTS = ['src/ziel_foundation_v1.py', 'src/ziel_foundation_analysis_v1.py', 'src/test_ziel_foundation_v1.py',
          'src/ziel_replacing_v1.py', 'src/ziel_replacing_v2.py', 'src/breadth_model_engine_v1.py',
          'src/calendar_semantics_study_v2.py', 'src/festival_feature_design.py', 'src/forecasting.py',
          'data/external/latest_state_energy_GWh.csv', 'results/calendar_semantics_v2/anchors_2022_2025.csv',
          'results/mechanism_controls_v1/chronos_download.json', 'results/second_model_audit_v1/weight_download.json',
          'results/feature_breadth_v1/event_window/protocol.json',
          'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv',
          'results/calendar_recenter_recovery_v1/analysis/breadth/ordinary/predictions_compared.csv']


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    parent = json.loads((ROOT/'results/feature_breadth_v1/event_window/protocol.json').read_text())
    protocols = {}
    for cohort in COHORTS:
        out = OUT/cohort; out.mkdir()
        cases = v1.cohort_cases(cohort)
        for name in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(out/name, index=False)
        tasks = len(cases[['state', 'year', 'origin']].drop_duplicates())
        p = dict(experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Exploratory. Registered and committed before any forecast of this study existed; the reference arms and the '
                    'local-model Ziel results were already inspected. To be run by the author in Google Colab.'),
            question='Do the Ziel hSun and replacing channel designs change foundation-model event MASE or the typed-versus-pooled ordering?',
            arms=ARMS, new_arms=['sunday_day', 'replace_pooled', 'replace_typed'], reference_arms=REFERENCE_ARMS, models=MODELS,
            new_arm_definition='Identical frames to results/ziel_replacing_v1 (sunday_day) and results/ziel_replacing_v2 (replace_pooled, replace_typed); all 18 channels passed as past and future covariates.',
            threads=parent['threads'], seed=parent['seed'], batch=parent['batch'], expected_tasks=tasks,
            weights=dict(chronos_revision=CHRONOS_REV, timesfm_revision=TIMESFM_REV, timesfm_code_revision=TIMESFM_CODE,
                         sha256_must_equal='results/mechanism_controls_v1/chronos_download.json and results/second_model_audit_v1/weight_download.json'),
            reproduction_check=('Reference-arm predictions must match the stored document_aligned foundation predictions within rtol 2e-4, '
                                'atol 1e-3 GWh (the parent solo-versus-batch tolerance). Failure is reported and the new arms are not interpreted.'),
            metrics='As results/ziel_replacing_v1 (row MASE, fixed pre-year scale, family-year-state balanced hierarchy).',
            contrasts=['sunday_day - pooled_day5', 'replace_pooled - pooled_day5', 'replace_typed - day5', 'replace_typed - replace_pooled',
                       'sunday_day - calendar', 'replace_pooled - calendar', 'replace_typed - calendar'],
            interpretation='As results/ziel_replacing_v1: consistent / negligible (< 0.005) / unstable; no p-values; failures and nulls reported.',
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={name: sha(out/name) for name in ['primary_cases.csv', 'window_cases.csv']})
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma', protocols=protocols,
        statement='Protocol fixed before any forecast of this study was produced. Commit before running.'))


def weights():
    from huggingface_hub import snapshot_download
    ident = {}
    c = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
    path = Path(snapshot_download('amazon/chronos-2', revision=CHRONOS_REV, local_dir=str(CACHE/'chronos2'/CHRONOS_REV),
                                  allow_patterns=[f['name'] for f in c['files']]))
    files = []
    for f in c['files']:
        local = path/f['name']; got = sha(local)
        assert got == f['sha256'], ('chronos', f['name'], got)
        files.append(dict(name=f['name'], path=str(local), sha256=got))
    ident['chronos'] = dict(revision=CHRONOS_REV, files=files)
    t = json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text())
    path = Path(snapshot_download('google/timesfm-3.0-pytorch', revision=TIMESFM_REV, local_dir=str(CACHE/'timesfm-3.0'/TIMESFM_REV)))
    local = path/'model.safetensors'; got = sha(local)
    assert got == t['sha256'], ('timesfm', got)
    ident['timesfm'] = dict(revision=TIMESFM_REV, path=str(local), sha256=got)
    import importlib.metadata as md
    import timesfm3  # noqa: F401  (must import before any run)
    ident['packages'] = {k: md.version(k) for k in ['timesfm', 'chronos-forecasting', 'torch', 'numpy', 'pandas']}
    assert ident['packages']['timesfm'] == '3.0.2', ident['packages']
    ident['verified_utc'] = datetime.now(timezone.utc).isoformat()
    dump(OUT/'weights_identity.json', ident)
    print(json.dumps(ident, indent=1))


def foundation(engine, worker):
    """Parent engine foundation() with the weight identity taken from weights_identity.json."""
    import torch
    p, out, cases, data = engine.setup(worker, primary=True)
    torch.set_num_threads(p['threads']); torch.manual_seed(p['seed']); np.random.seed(p['seed'])
    ident = json.loads((OUT/'weights_identity.json').read_text())
    if worker == 'chronos':
        from chronos import Chronos2Pipeline
        for f in ident['chronos']['files']:
            assert sha(f['path']) == f['sha256']
        weight = next(f for f in ident['chronos']['files'] if f['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weight['path']).parent), device_map='cpu', local_files_only=True)
        levels = list(model.quantiles); weight_sha = weight['sha256']
    else:
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        assert sha(ident['timesfm']['path']) == ident['timesfm']['sha256']
        model = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(ident['timesfm']['path']).parent), device='cpu',
            per_core_batch_size=p['batch'], local_files_only=True))
        levels = [q/10 for q in range(1, 10)]; weight_sha = ident['timesfm']['sha256']
    all_frames = {s: frames(data.index, s) for s in data}
    tasks = cases[['state', 'year', 'origin']].drop_duplicates().sort_values(['state', 'origin'])
    assert len(tasks) == p['expected_tasks']
    rows, inputs_log, batches = [], [], []
    started = time.perf_counter()

    def predict(inputs, names):
        if worker == 'chronos':
            packed = [dict(target=target, past_covariates={name: cov[i, :730] for i, name in enumerate(names)},
                future_covariates={name: cov[i, 730:] for i, name in enumerate(names)}) for target, cov in inputs]
            output = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            qq = [q[0].detach().cpu().numpy().T for q in output]
            return [(q[:, levels.index(.5)], q) for q in qq]
        output = list(model.predict_batch([x[0] for x in inputs], horizon=14,
            past_future_covariates=[x[1] for x in inputs], return_quantiles=True, use_symmetric_averaging=False))
        return [(np.asarray(x.forecast).squeeze(), np.asarray(x.quantiles).squeeze()) for x in output]

    try:
        for arm in ARMS:
            for offset in range(0, len(tasks), p['batch']):
                group = list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False))
                inputs = [engine.input_pair(data[t.state], all_frames[t.state][arm], t.origin) for t in group]
                names = list(all_frames[group[0].state][arm])
                for task, (target, cov) in zip(group, inputs):
                    changed = data[task.state].copy(); changed.loc[task.origin:] = 1e12
                    tt, cc = engine.input_pair(changed, all_frames[task.state][arm], task.origin)
                    np.testing.assert_array_equal(target, tt); np.testing.assert_array_equal(cov, cc)
                    inputs_log.append(dict(arm=arm, state=task.state, origin=str(task.origin.date()),
                        target_sha256=hashlib.sha256(target.tobytes()).hexdigest(), covariate_sha256=hashlib.sha256(cov.tobytes()).hexdigest()))
                tick = time.perf_counter()
                output = predict(inputs, names)
                for task, (point, quantiles) in zip(group, output):
                    assert point.shape == (14,) and np.isfinite(point).all() and np.isfinite(quantiles).all()
                    for r in cases[cases.state.eq(task.state) & cases.origin.eq(task.origin)].itertuples(index=False):
                        j = r.horizon-1
                        rows.append(dict(family=r.family, state=r.state, year=r.year, origin=str(r.origin.date()), date=str(r.date.date()),
                            horizon=r.horizon, prediction=float(point[j]), actual=float(r.actual), mase_scale=engine.scale(data, r.state, int(r.year)),
                            model=worker, arm=arm, **{f'q_{int(round(level*1000)):03d}': float(v) for level, v in zip(levels, quantiles[j])}))
                batches.append(dict(arm=arm, offset=offset, tasks=len(group), seconds=time.perf_counter()-tick))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv', index=False)
                dump(out/'batches.json', batches); dump(out/'inputs.json', inputs_log)
                print(worker, arm, offset+len(group), '/', len(tasks), flush=True)
        d = pd.DataFrame(rows)
        assert len(d) == len(cases)*len(ARMS)
        d.to_csv(out/'predictions.csv', index=False)
        dump(out/'run.json', dict(model=worker, completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d), arms=ARMS,
            seconds=time.perf_counter()-started, weight_sha256=weight_sha, predictions_sha256=sha(out/'predictions.csv'),
            protocol_sha256=sha(engine.OUT/'protocol.json')))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); dump(out/'inputs.json', inputs_log); raise


def run(cohort, worker):
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(OUT/cohort/'protocol.json') == reg['protocols'][cohort]
    import breadth_model_engine_v1 as engine
    engine.OUT = OUT/cohort; engine.ARMS = ARMS; engine.EXTRA = []; engine.frames = frames
    foundation(engine, worker)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('action', choices=['prepare', 'weights', *MODELS])
    a.add_argument('--cohort', choices=COHORTS, default='event_window')
    args = a.parse_args()
    {'prepare': prepare, 'weights': weights}.get(args.action, lambda: run(args.cohort, args.action))()
