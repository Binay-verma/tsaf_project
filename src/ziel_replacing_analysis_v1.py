"""Registered analysis for results/ziel_replacing_v1 (see each cohort's protocol.json).

Checks first, then descriptive contrasts. Writes only to results/ziel_replacing_v1/analysis.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
from ziel_replacing_v1 import OUT, ARMS, REFERENCE_ARMS, MODELS, COHORTS, COMPOSED

KEY = ['model', 'arm', 'family', 'state', 'year', 'date', 'horizon', 'origin']
CONTRASTS = [('sunday_day', 'pooled_day5'), ('sunday_day', 'day5'), ('sunday_day', 'calendar')]
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
    for c in ['date', 'origin']:
        d[c] = pd.to_datetime(d[c]).dt.strftime('%Y-%m-%d')
    d['MASE'] = (d.prediction-d.actual).abs()/d.mase_scale
    return d


def reproduction(d, cohort):
    stored = pd.read_csv(COMPOSED/cohort/'predictions_compared.csv')
    stored = stored[stored.version.eq('document_aligned') & stored.model.isin(MODELS) & stored.arm.isin(REFERENCE_ARMS)]
    ref = d[d.arm.isin(REFERENCE_ARMS)]
    m = ref.merge(stored[KEY+['prediction', 'actual', 'mase_scale']], on=KEY, suffixes=('', '_stored'), validate='one_to_one')
    assert len(m) == len(ref) == len(stored), (len(m), len(ref), len(stored))
    diff = (m.prediction-m.prediction_stored).abs()
    ok = bool(np.allclose(m.prediction, m.prediction_stored, rtol=1e-9, atol=1e-7)
              and np.allclose(m.actual, m.actual_stored, rtol=0, atol=1e-9)
              and np.allclose(m.mase_scale, m.mase_scale_stored, rtol=0, atol=1e-9))
    per = m.assign(diff=diff).groupby(['model', 'arm'])['diff'].max().reset_index()
    return ok, float(diff.max()), per


def balanced(d, years=None, families=None):
    x = d
    if years is not None:
        x = x[x.year.isin(years)]
    if families is not None:
        x = x[x.family.isin(families)]
    s = x.groupby(['model', 'arm', 'horizon', 'family', 'year', 'state']).MASE.mean()
    y = s.groupby(['model', 'arm', 'horizon', 'family', 'year']).mean()
    f = y.groupby(['model', 'arm', 'horizon', 'family']).mean()
    return f.groupby(['model', 'arm', 'horizon']).mean()


def stored_metric_check(d, cohort):
    m = pd.read_csv(COMPOSED/cohort/'metrics_balanced.csv')
    m = m[m.version.eq('document_aligned') & m.model.isin(MODELS) & m.arm.isin(REFERENCE_ARMS)]
    b = balanced(d)
    worst = 0.
    for r in m.itertuples(index=False):
        worst = max(worst, abs(b[(r.model, r.arm, r.horizon)]-r.MASE))
    return worst


def describe(d):
    b = balanced(d)
    fams = sorted(d.family.unique()); years = sorted(d.year.unique())
    clusters = d.groupby(['model', 'arm', 'horizon', 'family', 'year', 'state']).MASE.mean().groupby(
        ['model', 'arm', 'horizon', 'family', 'year']).mean()
    rows, cells = [], []
    for model in MODELS:
        for new, ref in CONTRASTS:
            for h in [1, 7, 14]:
                full = b[(model, new, h)]-b[(model, ref, h)]
                yv = {y: balanced(d, years=[y])[(model, new, h)]-balanced(d, years=[y])[(model, ref, h)] for y in years}
                lofo = [balanced(d, families=[f for f in fams if f != x])[(model, new, h)]
                        - balanced(d, families=[f for f in fams if f != x])[(model, ref, h)] for x in fams] if len(fams) > 1 else []
                fy = {}
                for f in fams:
                    for y in years:
                        if (model, new, h, f, y) in clusters:
                            fy[(f, y)] = clusters[(model, new, h, f, y)]-clusters[(model, ref, h, f, y)]
                            cells.append(dict(model=model, contrast=f'{new} - {ref}', horizon=h, family=f, year=y, value=fy[(f, y)]))
                same_years = len({np.sign(v) for v in yv.values()}) == 1 and 0 not in [np.sign(v) for v in yv.values()]
                lofo_flips = sum(np.sign(v) != np.sign(full) for v in lofo)
                if abs(full) < NEGLIGIBLE:
                    label = 'negligible'
                elif same_years and lofo_flips == 0:
                    label = 'consistent'
                else:
                    label = 'unstable'
                rows.append(dict(model=model, contrast=f'{new} - {ref}', horizon=h, balanced=full,
                                 **{f'year_{y}': v for y, v in yv.items()},
                                 lofo_min=min(lofo) if lofo else np.nan, lofo_max=max(lofo) if lofo else np.nan,
                                 lofo_sign_flips=lofo_flips, clusters=len(fy),
                                 clusters_new_better=sum(v < 0 for v in fy.values()),
                                 clusters_reference_better=sum(v > 0 for v in fy.values()),
                                 clusters_tied=sum(v == 0 for v in fy.values()), label=label))
    return b, pd.DataFrame(rows), pd.DataFrame(cells)


def main():
    out = OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written; version a new one')
    loaded = {c: load(c) for c in COHORTS}
    checks = {}
    for c, d in loaded.items():
        ok, worst, per = reproduction(d, c)
        checks[c] = dict(reference_predictions_match=ok, reference_max_abs_diff_GWh=worst,
                         stored_balanced_MASE_max_abs_diff=stored_metric_check(d, c),
                         rows=len(d), arms=sorted(d.arm.unique()), models=sorted(d.model.unique()))
        checks[c]['per_model_arm'] = per.to_dict('records')
    out.mkdir()
    dump(out/'checks.json', checks)
    if not all(v['reference_predictions_match'] and v['stored_balanced_MASE_max_abs_diff'] < 1e-12 for v in checks.values()):
        raise SystemExit('Reproduction check failed; new arm not interpreted. See checks.json')
    summary = {}
    for c, d in loaded.items():
        b, contrasts, cells = describe(d)
        b.rename('MASE').reset_index().to_csv(out/f'{c}_balanced.csv', index=False)
        contrasts.to_csv(out/f'{c}_contrasts.csv', index=False)
        cells.to_csv(out/f'{c}_family_year_cells.csv', index=False)
        summary[c] = dict(labels=contrasts.groupby(['contrast', 'label']).size().unstack(fill_value=0).to_dict('index'))
    summary['created_utc'] = datetime.now(timezone.utc).isoformat()
    summary['inputs'] = {f'{c}/{m}': sha(OUT/c/m/'predictions.csv') for c in COHORTS for m in MODELS}
    dump(out/'summary.json', summary)
    print(json.dumps(checks, indent=1, default=str)[:1500])
    print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
