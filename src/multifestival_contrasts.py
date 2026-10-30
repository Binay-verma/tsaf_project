"""Descriptive within-family calendar/history contrasts; no model selection."""
import json
import numpy as np
import pandas as pd
from forecasting import ROOT

OUT = ROOT/'results/multifestival_models_v1'
PAIRS = {
    'chronos': ('chronos_calendar', 'chronos_history'),
    'timesfm': ('timesfm_calendar', 'timesfm_history'),
    'sarimax_annual': ('sarimax_calendar_annual', 'sarimax_history_annual'),
    'ridge_basic_annual': ('ridge_basic_calendar', 'ridge_basic_history'),
    'ridge_rich_monthly': ('ridge_rich_calendar_monthly', 'ridge_rich_history_monthly'),
    'lightgbm_stable_monthly': ('lightgbm_stable_calendar_monthly', 'lightgbm_stable_history_monthly')}


def main():
    if (OUT/'calendar_history_contrasts.csv').exists():
        raise FileExistsError('Preserve existing descriptive contrasts')
    m = pd.read_csv(OUT/'metrics_state_year.csv')
    rows = []
    key = ['family', 'state', 'year', 'horizon']
    for name, (calendar, history) in PAIRS.items():
        c = m[m.configuration.eq(calendar)].merge(m[m.configuration.eq(history)], on=key, suffixes=('_calendar', '_history'), validate='one_to_one')
        assert len(c) == 72 and (c.n_calendar == c.n_history).all()
        assert (c.MAE_GWh_history > 0).all(), 'Undefined relative effect; do not hide zero denominators'
        c['mean_MAE_reduction_pct'] = 100*(1-c.MAE_GWh_calendar/c.MAE_GWh_history)
        c['pair'] = name
        rows.append(c[key+['pair', 'mean_MAE_reduction_pct']])
    d = pd.concat(rows, ignore_index=True)
    assert np.isfinite(d.mean_MAE_reduction_pct).all()
    d.to_csv(OUT/'calendar_history_contrasts_state_year.csv', index=False)
    y = d.groupby(['family', 'pair', 'year', 'horizon']).mean_MAE_reduction_pct.mean().reset_index()
    y.groupby(['family', 'pair', 'horizon']).mean_MAE_reduction_pct.mean().reset_index().to_csv(OUT/'calendar_history_contrasts.csv', index=False)
    (OUT/'calendar_history_contrasts_scope.json').write_text(json.dumps(dict(
        status='Descriptive paired diagnostics; not a causal or prospective contrast', pairs=PAIRS,
        interpretation='Positive values mean lower MAE with ordinary calendar inputs. Mean within-state/year relative effects, equal states then years, not ratio of macro MASE.',
        limits='These inputs are weekdays/Fourier terms, not added festival identities. Small or mixed gains alone do not establish an information mechanism. All cases/years/variants retained; no model, feature or future forecast selected from the results.'), indent=2)+'\n')
    print('Saved90descriptive calendar/history contrasts and432state/year cells')


if __name__ == '__main__':
    main()
