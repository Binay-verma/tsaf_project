"""Localise the retained scalar-review discrepancy; never refit or alter output."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from robust_baselines import design_frame, fitting_cases
from forecasting import load_data
from pooled_festival_experiment import OUT, frames


def main():
    if (OUT/'numerical_localization.json').exists():
        raise FileExistsError('Preserve diagnostic')
    data = load_data('latest')
    source = pd.read_csv(Path(__file__).resolve().parents[1]/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    summaries, feature_rows = [], []
    for state in ['Delhi', 'Karnataka', 'Maharashtra']:
        raw = source[state].where(source[state] > 0)
        vals = raw.to_numpy(copy=True)
        for i in range(len(vals)):
            if not np.isfinite(vals[i]):
                vals[i] = vals[i-7] if i >= 7 and np.isfinite(vals[i-7]) else vals[i-1] if i else np.nan
        history = pd.Series(vals, index=source.index)
        cases = pd.read_csv(OUT/'event/primary_cases.csv', parse_dates=['date', 'origin'])
        first = cases[cases.state.eq(state) & cases.year.eq(2024)].date.min()
        for h in [1, 7, 14]:
            origin = first-pd.Timedelta(days=h-1)
            cutoff = origin.replace(day=1)-pd.Timedelta(days=1)
            def independent(o):
                target = o+pd.Timedelta(days=h-1)
                a = [history.at[o-pd.Timedelta(days=k)] for k in [1, 2, 3, 7, 14, 21, 28, 56, 364, 365, 366]]
                means = {}
                for width in [7, 28, 56]:
                    z = history.loc[o-pd.Timedelta(days=width):o-pd.Timedelta(days=1)].to_numpy()
                    means[width] = z.mean(); a += [z.mean(), z.std(ddof=1), z.min(), z.max()]
                a += [means[7]-means[28]]
                a += [history.at[target-pd.Timedelta(days=k)] for k in [364, 365, 366]]
                a += [float(target.dayofweek == k) for k in range(7)]
                for k in [1, 2, 3]:
                    angle = 2*np.pi*k*target.dayofyear/365.2425
                    a += [np.sin(angle), np.cos(angle)]
                return a
            application, _ = design_frame(data[state], state, h, 'rich_calendar')
            origins = pd.date_range(cutoff-pd.Timedelta(days=729), cutoff-pd.Timedelta(days=h-1))
            independent_x = np.asarray([independent(o) for o in origins])
            yy = raw.reindex(origins+pd.Timedelta(days=h-1)).to_numpy()
            valid = np.isfinite(yy) & np.isfinite(independent_x).all(axis=1)
            expected, y, _ = fitting_cases(application, data[state], h, cutoff)
            actual = independent_x[valid]
            np.testing.assert_array_equal(yy[valid], y)
            diff = abs(actual-expected)
            cast_diff = actual.astype(np.float32) != expected.astype(np.float32)
            for j, column in enumerate(application.columns):
                if diff[:, j].max() > 0 or cast_diff[:, j].any():
                    feature_rows.append(dict(state=state, horizon=h, feature=column,
                        max_float64_difference=float(diff[:, j].max()),
                        float32_differing_entries=int(cast_diff[:, j].sum()),
                        max_float32_difference=float(abs(actual[:, j].astype(np.float32)-expected[:, j].astype(np.float32)).max())))
            summaries.append(dict(state=state, horizon=h, rows=len(actual),
                max_float64_difference=float(diff.max()),
                float32_differing_entries=int(cast_diff.sum()),
                max_float32_difference=float(abs(actual.astype(np.float32)-expected.astype(np.float32)).max())))
    pd.DataFrame(feature_rows).to_csv(OUT/'numerical_feature_differences.csv', index=False)
    result = dict(status='diagnostic_completed_not_a_replacement_pass', scope='All9date-selected state/lead training blocks; separate scalar histories versus application history/calendar construction. No fits, selection or predictions changed.',
        interpretation='The original strict clean-review discrepancy remains retained. Forecast tolerance agreement does not imply byte-identical implementations or guarantee agreement on every case.', summaries=summaries)
    (OUT/'numerical_localization.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
