"""Check six date-selected ETS deployments using independent scalar recursion."""
import json
import numpy as np
import pandas as pd
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from forecasting import ROOT, load_data, causal_fill

OUT = ROOT/'results/multifestival_models_v1'


def main():
    cases = pd.read_csv(OUT/'expected_cases.csv', parse_dates=['origin'])
    predictions = pd.read_csv(OUT/'classical/predictions.csv', parse_dates=['origin'])
    source = load_data('latest')
    checks = []
    for (state, year), group in cases.groupby(['state', 'year']):
        origin = group.origin.min()
        end = origin.replace(day=1)-pd.Timedelta(days=1)
        start = end-pd.Timedelta(days=729)
        y = causal_fill(source[state])/100.
        fit = ETSModel(y.loc[start:end], error='add', trend=None, seasonal='add', seasonal_periods=7,
            initialization_method='estimated').fit(maxiter=200, disp=False)
        assert fit.mle_retvals['converged']
        alpha, gamma = fit.smoothing_level, fit.smoothing_seasonal
        level = float(fit.initial_level)
        seasonal = list(map(float, fit.initial_seasonal))
        context = y.loc[start:origin-pd.Timedelta(days=1)].to_numpy()
        fitted = []
        for i, actual in enumerate(context):
            index = i % 7
            expected = level+seasonal[index]
            fitted.append(expected)
            residual = actual-expected
            level += alpha*residual
            seasonal[index] += gamma*residual
        train_n = len(y.loc[start:end])
        np.testing.assert_allclose(fitted[:train_n], fit.fittedvalues, rtol=1e-9, atol=1e-10)
        forecast = [100*(level+seasonal[(len(context)+j) % 7]) for j in range(14)]
        saved = predictions[predictions.state.eq(state) & predictions.origin.eq(origin) & predictions.configuration.eq('ets_weekly_monthly')]
        assert len(saved) > 0
        difference = max(abs(float(r.prediction)-forecast[r.horizon-1]) for r in saved.itertuples(index=False))
        np.testing.assert_allclose(saved.prediction, [forecast[h-1] for h in saved.horizon], rtol=1e-8, atol=1e-7)
        checks.append(dict(state=state, year=int(year), origin=str(origin.date()),
            training_end=str(end.date()), scored_rows=len(saved), max_prediction_difference_GWh=float(difference),
            method='Scalar ETS(A,N,A) innovation recurrence; first origin per state/year selected by date',
            parameters=dict(zip(fit.model.param_names, map(float, fit.params)))))
    result = dict(status='pass', checks=checks, scope='Six date-selected internal software checks, not a full independent human rerun')
    (OUT/'ets_scalar_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
