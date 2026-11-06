"""Registered analysis for results/ziel_nyc_v1 (see each cohort's protocol.json).

Reproduction checks first, then descriptive contrasts. Writes only to results/ziel_nyc_v1/analysis.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from ziel_nyc_v1 import OUT, PARENT, REFERENCE_ARMS, MODELS, COHORTS

KEY = ['model', 'arm', 'family', 'state', 'year', 'date', 'origin', 'horizon']
COMPOSED = ROOT/'results/mta_holiday_recovery_v1/analysis'
CONTRASTS = [('sunday_day', 'pooled_day5'), ('replace_pooled', 'pooled_day5'), ('replace_typed', 'day5'),
             ('replace_typed', 'replace_pooled'), ('sunday_day', 'calendar'), ('replace_pooled', 'calendar'),
             ('replace_typed', 'calendar')]
STEPS = [8, 14, 21]
NEGLIGIBLE = 0.005


def load(cohort):
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(OUT/cohort/'protocol.json') == reg['protocols'][cohort]
    parts = []
    for model in MODELS:
        run = json.loads((OUT/cohort/model/'run.json').read_text())
        assert sha(OUT/cohort/model/'predictions.csv') == run['predictions_sha256']
        parts.append(pd.read_csv(OUT/cohort/model/'predictions.csv'))
    d = pd.concat(parts, ignore_index=True)
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def balanced(d, families=None, states=None):
    x = d if families is None else d[d.family.isin(families)]
    x = x if states is None else x[x.state.isin(states)]
    cell = x.groupby(['model', 'arm', 'horizon', 'family', 'state', 'year']).MASE.mean()
    fam = cell.groupby(['model', 'arm', 'horizon', 'family']).mean()
    return fam.groupby(['model', 'arm', 'horizon']).mean()


def checks(d, cohort):
    ref = d[d.arm.isin(REFERENCE_ARMS)]
    parent = pd.concat([pd.read_csv(PARENT/cohort/m/'predictions.csv') for m in MODELS], ignore_index=True)
    parent = parent[parent.arm.isin(REFERENCE_ARMS)]
    m = ref.merge(parent[KEY+['prediction', 'actual', 'mase_scale']], on=KEY, suffixes=('', '_parent'), validate='one_to_one')
    assert len(m) == len(ref) == len(parent)
    ok = bool(np.allclose(m.prediction, m.prediction_parent, rtol=1e-9, atol=1e-7)
              and np.allclose(m.actual, m.actual_parent, rtol=0, atol=1e-12)
              and np.allclose(m.mase_scale, m.mase_scale_parent, rtol=0, atol=1e-12))
    stored = pd.read_csv(COMPOSED/cohort/'metrics_balanced.csv')
    stored = stored[stored.model.isin(MODELS) & stored.arm.isin(REFERENCE_ARMS)]
    b = balanced(d)
    worst = max(abs(b[(r.model, r.arm, r.horizon)]-r.MASE) for r in stored.itertuples(index=False))
    return dict(reference_predictions_match=ok, reference_max_abs_diff=float((m.prediction-m.prediction_parent).abs().max()),
                stored_balanced_MASE_max_abs_diff=float(worst), rows=len(d))


def describe(d):
    b = balanced(d)
    fams = sorted(d.family.unique()); modes = sorted(d.state.unique())
    cell = d.groupby(['model', 'arm', 'horizon', 'family', 'state']).MASE.mean()
    rows, cells = [], []
    for model in MODELS:
        for new, ref in CONTRASTS:
            for h in STEPS:
                full = b[(model, new, h)]-b[(model, ref, h)]
                per_mode = {s: balanced(d, states=[s])[(model, new, h)]-balanced(d, states=[s])[(model, ref, h)] for s in modes}
                lofo = [balanced(d, families=[f for f in fams if f != x])[(model, new, h)]
                        - balanced(d, families=[f for f in fams if f != x])[(model, ref, h)] for x in fams] if len(fams) > 1 else []
                fc = {}
                for f in fams:
                    for s in modes:
                        fc[(f, s)] = cell[(model, new, h, f, s)]-cell[(model, ref, h, f, s)]
                        cells.append(dict(model=model, contrast=f'{new} - {ref}', model_step=h, decision_lead=h-7, family=f, mode=s, value=fc[(f, s)]))
                signs = {np.sign(v) for v in per_mode.values()}
                flips = sum(np.sign(v) != np.sign(full) for v in lofo)
                if abs(full) < NEGLIGIBLE:
                    label = 'negligible'
                elif len(signs) == 1 and 0 not in signs and flips == 0:
                    label = 'consistent'
                else:
                    label = 'unstable'
                rows.append(dict(model=model, contrast=f'{new} - {ref}', model_step=h, decision_lead=h-7, balanced=full,
                                 **{f'mode_{s}': v for s, v in per_mode.items()},
                                 lofo_min=min(lofo) if lofo else np.nan, lofo_max=max(lofo) if lofo else np.nan, lofo_sign_flips=flips,
                                 cells=len(fc), cells_new_better=sum(v < 0 for v in fc.values()),
                                 cells_reference_better=sum(v > 0 for v in fc.values()), cells_tied=sum(v == 0 for v in fc.values()),
                                 label=label))
    return b, pd.DataFrame(rows), pd.DataFrame(cells)


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written; version a new one')
    loaded = {c: load(c) for c in COHORTS}
    result = {c: checks(d, c) for c, d in loaded.items()}
    out.mkdir()
    dump(out/'checks.json', result)
    if not all(v['reference_predictions_match'] and v['stored_balanced_MASE_max_abs_diff'] < 1e-12 for v in result.values()):
        raise SystemExit('Reproduction check failed; new arms not interpreted. See checks.json')
    summary = {}
    for c, d in loaded.items():
        b, contrasts, cells = describe(d)
        b = b.rename('MASE').reset_index(); b['decision_lead'] = b.horizon-7
        b.to_csv(out/f'{c}_balanced.csv', index=False)
        contrasts.to_csv(out/f'{c}_contrasts.csv', index=False)
        cells.to_csv(out/f'{c}_family_mode_cells.csv', index=False)
        summary[c] = dict(labels=contrasts.groupby(['contrast', 'label']).size().unstack(fill_value=0).to_dict('index'))
    summary['created_utc'] = datetime.now(timezone.utc).isoformat()
    summary['inputs'] = {f'{c}/{m}': sha(OUT/c/m/'predictions.csv') for c in COHORTS for m in MODELS}
    dump(out/'summary.json', summary)
    print(json.dumps(result, indent=1)); print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
