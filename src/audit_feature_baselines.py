"""Report previous-baseline reproduction and same-size zero-channel changes."""
import json
import numpy as np
import pandas as pd
from festival_feature_design import ROOT, OUT, KEY


def main():
    old = pd.read_csv(ROOT/'results/multifestival_models_v1/predictions.csv')
    primary = pd.read_csv(OUT/'predictions_primary.csv')
    config = {'ridge': 'ridge_rich_calendar_monthly', 'lightgbm': 'lightgbm_stable_calendar_monthly',
        'sarimax': 'sarimax_calendar_annual', 'chronos': 'chronos_calendar', 'timesfm': 'timesfm_calendar'}
    rows = []
    for model in sorted(primary.model.unique()):
        group = primary[primary.model.eq(model)]
        calendar = group[group.arm.eq('calendar')]
        zero = group[group.arm.eq('zero5')]
        c = calendar.merge(zero[KEY+['prediction']], on=KEY, suffixes=('_calendar', '_zero'), validate='one_to_one')
        assert len(c) == 72
        result = dict(model=model, primary_cases=72,
            zero_channel_max_prediction_change_GWh=float(abs(c.prediction_calendar-c.prediction_zero).max()),
            zero_channel_mean_prediction_change_GWh=float(abs(c.prediction_calendar-c.prediction_zero).mean()))
        if model in config:
            reference = old[old.configuration.eq(config[model])]
            matched = calendar.merge(reference[KEY+['prediction']], on=KEY, suffixes=('_new', '_old'), validate='one_to_one')
            assert len(matched) == 72
            result.update(old_baseline_reference=config[model],
                max_previous_baseline_prediction_difference_GWh=float(abs(matched.prediction_new-matched.prediction_old).max()),
                exact_previous_baseline_reproduction=bool(np.array_equal(matched.prediction_new.to_numpy(), matched.prediction_old.to_numpy())))
        else:
            result['old_baseline_reference'] = 'Capacity2is a new fixed sensitivity with its own fresh ordinary-calendar baseline'
        rows.append(result)
    report = dict(status='diagnostics_recorded', rows=rows,
        interpretation='Nonzero differences from zero-valued inputs are retained as interface/optimisation sensitivity. They are not event information. Old-model comparisons are descriptive; genuine within-experiment effects use fresh matched calendar/zero/placebo baselines.',
        scope='Not a claim of exact cross-hardware/optimiser reproducibility or causal mechanism')
    (OUT/'baseline_and_zero_diagnostics.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
