"""Registered analysis for results/ziel_foundation_v1 (run after both foundation workers finish, in Colab).

Reuses the registered v1 analysis aggregation and labelling unchanged; only the reproduction
tolerance differs (rtol 2e-4, atol 1e-3 GWh, as registered for foundation reruns).
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import ziel_replacing_analysis_v1 as a
import ziel_foundation_v1 as f
from festival_feature_design import sha, dump

a.OUT = f.OUT
a.MODELS = f.MODELS
a.CONTRASTS = [('sunday_day', 'pooled_day5'), ('replace_pooled', 'pooled_day5'), ('replace_typed', 'day5'),
               ('replace_typed', 'replace_pooled'), ('sunday_day', 'calendar'), ('replace_pooled', 'calendar'), ('replace_typed', 'calendar')]


def reproduction(d, cohort):
    stored = pd.read_csv(a.COMPOSED/cohort/'predictions_compared.csv')
    stored = stored[stored.version.eq('document_aligned') & stored.model.isin(f.MODELS) & stored.arm.isin(f.REFERENCE_ARMS)]
    ref = d[d.arm.isin(f.REFERENCE_ARMS)]
    m = ref.merge(stored[a.KEY+['prediction']], on=a.KEY, suffixes=('', '_stored'), validate='one_to_one')
    assert len(m) == len(ref) == len(stored)
    ok = bool(np.allclose(m.prediction, m.prediction_stored, rtol=2e-4, atol=1e-3))
    return dict(reference_predictions_within_tolerance=ok, max_abs_diff_GWh=float((m.prediction-m.prediction_stored).abs().max()), rows=len(m))


def main():
    out = f.OUT/'analysis'
    if out.exists():
        raise FileExistsError('Analysis already written')
    loaded = {c: a.load(c) for c in f.COHORTS}
    checks = {c: reproduction(d, c) for c, d in loaded.items()}
    out.mkdir(); dump(out/'checks.json', checks)
    if not all(v['reference_predictions_within_tolerance'] for v in checks.values()):
        raise SystemExit('Reference arms outside tolerance; new arms not interpreted. See checks.json')
    summary = {}
    for c, d in loaded.items():
        b, contrasts, cells = a.describe(d)
        b.rename('MASE').reset_index().to_csv(out/f'{c}_balanced.csv', index=False)
        contrasts.to_csv(out/f'{c}_contrasts.csv', index=False); cells.to_csv(out/f'{c}_family_year_cells.csv', index=False)
        summary[c] = dict(labels=contrasts.groupby(['contrast', 'label']).size().unstack(fill_value=0).to_dict('index'))
    summary['created_utc'] = datetime.now(timezone.utc).isoformat()
    summary['inputs'] = {f'{c}/{m}': sha(f.OUT/c/m/'predictions.csv') for c in f.COHORTS for m in f.MODELS}
    dump(out/'summary.json', summary)
    print(json.dumps(checks, indent=1)); print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
