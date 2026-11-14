"""TimesFM-3 encoding control for the new-states study (EXPLORATORY; written after the registered analysis).

Question: is TimesFM-3's typed advantage at leads 7 and 14 (results/new_states_v1_diagnostics) caused by the four all-zero
padding channels in the registered pooled arm? The registered foundation runs had no zero or placebo arm.

Arms (same registered code, weights, cases, calendar base and cohorts; nothing registered is changed):
  pooled_day5  registered pooled arm (event flag + 4 zero channels), rerun in the same environment as the others
  pooled1      the same event flag without the padding channels
  zero5        calendar + five zero channels (no festival information)
Outputs: results/new_states_v1_fm_control/<cohort>/timesfm/ (the cohort's protocol and case files are copied unchanged,
so the engine's hash checks still pass); weights_identity.json in results/new_states_v1_fm_control/.

Run on the hosted notebook (docs/reproduction/NEW_STATES_FM_CONTROL_KAGGLE.md):
  python src/new_states_fm_control_v1.py weights
  python src/new_states_fm_control_v1.py run --cohort fm_2017_2020     (and fm_2021_2025)
Then locally: python src/new_states_fm_control_v1.py analyse
"""
import argparse
import json
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import new_states_v1 as s                 # noqa: E402  (patches the shared modules to the seven states)
import longer_panel_stage_a_v1 as A       # noqa: E402

OUT = ROOT/'results/new_states_v1_fm_control'
ARMS = ['pooled_day5', 'pooled1', 'zero5']
COHORTS = ['fm_2017_2020', 'fm_2021_2025']


def frames_fn(a, fake):
    def f(index, state):
        fr = A.frames(index, state, a, fake)
        pooled = fr['pooled_day5']
        return {'pooled_day5': pooled, 'pooled1': pooled[[c for c in pooled.columns if not c.startswith('padding_')]], 'zero5': fr['zero5']}
    return f


def prepare(cohort):
    """Copy the cohort's protocol and every design file it hashes, at the same relative paths, unchanged."""
    src, dst = s.OUT/cohort, OUT/cohort
    dst.mkdir(parents=True, exist_ok=True)
    proto = json.loads((src/'protocol.json').read_text())
    for rel in ['protocol.json', 'primary_cases.csv', 'window_cases.csv', *proto['design_hashes']]:
        target = (dst/rel).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if (src/rel).exists() and not target.exists():
            shutil.copy2(src/rel, target)


def run(cohort):
    import breadth_model_engine_v1 as engine
    import ziel_foundation_v1 as zf
    prepare(cohort)
    a = pd.read_csv(s.OUT/s.LEDGER); fake = pd.read_csv(s.OUT/s.PLACEBO)
    engine.OUT = OUT/cohort; engine.ARMS = ARMS; engine.EXTRA = []; engine.ledger_bound = s.bound
    fr = frames_fn(a, fake)
    engine.frames = fr
    zf.OUT = OUT; zf.ARMS = ARMS; zf.frames = fr
    zf.foundation(engine, 'timesfm')


def weights():
    import ziel_foundation_v1 as zf
    OUT.mkdir(parents=True, exist_ok=True)
    zf.OUT = OUT
    zf.weights()


def analyse():
    from festival_feature_design import sha
    rows = []
    for c in COHORTS:
        for base, name in [(s.OUT/c/'timesfm', 'registered'), (OUT/c/'timesfm', 'control')]:
            run_ = json.loads((base/'run.json').read_text())
            assert sha(base/'predictions.csv') == run_['predictions_sha256']
            d = pd.read_csv(base/'predictions.csv')
            d['source'] = name
            rows.append(d[['family', 'state', 'year', 'date', 'horizon', 'origin', 'actual', 'prediction', 'mase_scale', 'arm', 'source']])
    d = pd.concat(rows, ignore_index=True)
    d['MASE'] = (d.prediction - d.actual).abs()/d.mase_scale
    d['key'] = d.source + ':' + d.arm
    rep = d[d.key.isin(['registered:pooled_day5', 'control:pooled_day5'])].pivot_table(
        index=['state', 'origin', 'date', 'horizon'], columns='key', values='prediction')
    reproduction = dict(rows=len(rep), max_abs_diff=float((rep['registered:pooled_day5'] - rep['control:pooled_day5']).abs().max()),
                        median_rel_diff=float(((rep['registered:pooled_day5'] - rep['control:pooled_day5']).abs()/rep['registered:pooled_day5'].abs()).median()))
    out = []
    contrasts = {'padding effect (pooled_day5 - pooled1, control run)': ('control:pooled_day5', 'control:pooled1'),
                 'typed - pooled1 (typed from registered run)': ('registered:day5', 'control:pooled1'),
                 'typed - pooled_day5 (registered, as in diagnostics)': ('registered:day5', 'registered:pooled_day5'),
                 'zero5 - calendar (zero-channel effect)': ('control:zero5', 'registered:calendar'),
                 'typed - zero5': ('registered:day5', 'control:zero5'),
                 'pooled1 - zero5': ('control:pooled1', 'control:zero5')}
    import new_states_analysis_v1 as an
    for hz in [1, 7, 14]:
        x = d[d.horizon == hz]
        cell = x.groupby(['family', 'year', 'state', 'key']).MASE.mean().unstack('key')
        for label, (p, q) in contrasts.items():
            c = (cell[p] - cell[q]).groupby(['family', 'year']).mean().dropna()
            out.append(dict(horizon=hz, contrast=label, clusters=len(c), mean=float(c.mean()),
                            p_two_sided=min(1, 2*min(an.signflip(c.values, 1, 100_000), an.signflip(c.values, -1, 100_000)))))
    res = pd.DataFrame(out)
    (OUT/'analysis').mkdir(exist_ok=False)
    res.to_csv(OUT/'analysis'/'contrasts.csv', index=False)
    (OUT/'analysis'/'reproduction.json').write_text(json.dumps(reproduction, indent=1))
    print(json.dumps(reproduction, indent=1)); print(res.round(4).to_string(index=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['weights', 'run', 'analyse'])
    ap.add_argument('--cohort', choices=COHORTS)
    x = ap.parse_args()
    {'weights': weights, 'analyse': analyse}.get(x.action, lambda: run(x.cohort))()
