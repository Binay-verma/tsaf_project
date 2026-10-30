"""Exploratory fixed-Ridge controls. Read the versioned protocol before running.

Writes only a fresh run directory; never updates historical forecasts or caches.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import platform
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from extended_validation import MAIN, EXTRA, fast_design
from forecasting import ROOT, STATES, causal_fill, load_data


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def anchors(state, regional=True):
    return {year: sorted(set([pd.Timestamp(date)] +
            ([pd.Timestamp(x) for x in EXTRA.get(state, {}).get(year, [])]
             if regional else []))) for year, date in MAIN.items()}


def window_dates(dates):
    return {d + pd.Timedelta(days=k) for d in dates for k in range(-3, 4)}


def placebo_shifts(protocol):
    """Target-free, weekday-matched shifts retaining cross-state dependence."""
    rng = np.random.default_rng(protocol['placebo']['seed'])
    shifts = {}
    for year in sorted(MAIN):
        valid = []
        for shift in protocol['placebo']['candidate_shifts_days']:
            if all(not (window_dates(anchors(s)[year]) & window_dates(
                    [d + pd.Timedelta(days=shift) for d in anchors(s)[year]]))
                   for s in STATES):
                valid.append(shift)
        if not valid:
            raise ValueError(f'No permissible placebo shift for {year}')
        shifts[year] = int(rng.choice(valid))
    return shifts


def event_channels(index, state, regional=True, shifts=None):
    dates = [d + pd.Timedelta(days=(shifts or {}).get(year, 0))
             for year, ds in anchors(state, regional).items() for d in ds]
    # Compare dates directly rather than shifting a truncated index.
    return np.column_stack([index.isin([d + pd.Timedelta(days=k) for d in dates])
                            for k in range(-3, 4)]).astype(float)


def covariates(index, state, protocol):
    # Same ordinary-calendar definition as the historical code, no library holidays.
    base = pd.DataFrame({f'dow_{i}': (index.dayofweek == i).astype(float)
                         for i in range(7)}, index=index)
    for k in (1, 2, 3):
        base[f'sin_{k}'] = np.sin(2*np.pi*k*index.dayofyear/365.2425)
        base[f'cos_{k}'] = np.cos(2*np.pi*k*index.dayofyear/365.2425)
    generic = event_channels(index, state, regional=False)
    regional = event_channels(index, state)
    placebo = event_channels(index, state, shifts=placebo_shifts(protocol))
    window = lambda a: a.any(axis=1).astype(float)[:, None]
    extras = {'calendar': np.empty((len(index), 0)),
              'zero_1': np.zeros((len(index), 1)),
              'zero_7': np.zeros((len(index), 7)),
              'generic_window': window(generic), 'regional_window': window(regional),
              'generic_7': generic, 'regional_7': regional,
              'placebo_window': window(placebo), 'placebo_7': placebo}
    for shift in (-2, -1, 1, 2):
        a = event_channels(index, state, shifts={y: shift for y in MAIN})
        extras[f'regional_shift_{shift:+d}_window'] = window(a)
        extras[f'regional_shift_{shift:+d}_7'] = a
    assert set(extras) == set(protocol['arms'])
    frames = {name: pd.concat([base, pd.DataFrame(a, index=index,
              columns=[f'event_{i}' for i in range(a.shape[1])])], axis=1)
              for name, a in extras.items()}
    return frames, regional.any(axis=1)


def train_predict(observed, cal, horizon, year, origins):
    cutoff = pd.Timestamp(f'{year-1}-12-31')
    start = cutoff - pd.Timedelta(days=729)
    train_origins = pd.date_range(start, cutoff-pd.Timedelta(days=horizon-1))
    target_dates = train_origins + pd.Timedelta(days=horizon-1)
    assert target_dates.max() <= cutoff < origins.min()
    filled = causal_fill(observed)
    x = fast_design(filled, cal, list(cal), horizon, train_origins)
    labels = observed.reindex(target_dates).to_numpy()
    mask = np.isfinite(x).all(axis=1) & np.isfinite(labels)
    if mask.sum() < 365:
        raise ValueError('Insufficient recorded training labels')
    model = make_pipeline(StandardScaler(), Ridge(alpha=10))
    model.fit(x[mask], labels[mask])
    forecasts = model.predict(fast_design(filled, cal, list(cal), horizon, origins))
    training = observed.loc[start:cutoff]
    scale = float((training - training.shift(7)).abs().mean())
    assert np.isfinite(scale) and scale > 0
    return forecasts, scale, {'training_target_max': str(target_dates[mask].max().date()),
                             'training_n': int(mask.sum()), 'features': x.shape[1]}


def score(predictions, out, protocol):
    d = predictions[predictions.actual.notna()].copy()
    assert np.isfinite(d.prediction).all()
    assert not d.duplicated(['state', 'origin', 'horizon', 'arm']).any()
    assert ((d.date-d.origin).dt.days == d.horizon-1).all()
    reference = None
    for _, g in d.groupby('arm'):
        keys = set(map(tuple, g[['state', 'origin', 'horizon']].to_numpy()))
        if reference is None:
            reference = keys
        assert reference == keys
    d['ae'] = (d.actual-d.prediction).abs()
    d['scaled'] = d.ae / d.mase_scale
    metrics = []
    for scope, mask in [('all', np.ones(len(d), dtype=bool)),
                        ('event', d.event.eq(1)), ('non_event', d.event.eq(0))]:
        g = d.loc[mask].groupby(['year', 'state', 'horizon', 'arm']).agg(
            MAE_GWh=('ae', 'mean'), MASE=('scaled', 'mean'), n=('ae', 'size')).reset_index()
        g['scope'] = scope
        metrics.append(g)
    m = pd.concat(metrics, ignore_index=True)
    m.to_csv(out/'metrics_state_year.csv', index=False)
    macro = m.groupby(['year', 'horizon', 'arm', 'scope']).MASE.mean().reset_index()
    macro.to_csv(out/'metrics_year.csv', index=False)
    primary = macro[macro.year.isin(protocol['primary_scope'])]
    primary = primary.groupby(['horizon', 'scope', 'arm']).MASE.mean().reset_index()
    primary.to_csv(out/'primary_metrics.csv', index=False)
    pivot = d.pivot(index=['state', 'origin', 'horizon'], columns='arm', values='prediction')
    for arm in ['zero_1', 'zero_7']:
        np.testing.assert_allclose(pivot.calendar, pivot[arm], atol=1e-9, rtol=1e-10)
    # Verify common arms reproduce the included historical Ridge forecasts.
    old = pd.read_csv(ROOT/'results/extended_validation/classical_daily.csv', parse_dates=['origin'])
    old = old[old.model.eq('ridge') & old.year.isin(protocol['years'])]
    for arm, mode in [('calendar', 'B_calendar'), ('regional_7', 'D_regional_festival')]:
        a = d[d.arm.eq(arm)].merge(old[old['mode'].eq(mode)],
                on=['state', 'origin', 'horizon'], suffixes=('_new', '_old'), validate='one_to_one')
        assert len(a) == len(d[d.arm.eq(arm)])
        np.testing.assert_allclose(a.prediction_new, a.prediction_old, atol=1e-7, rtol=1e-9)
    return {'scored_rows': len(d), 'matched_cases_per_arm': len(reference),
            'checks': ['unique/finite forecasts', 'matched cases', 'lead-date alignment',
                       'zero controls identical', 'historical B/D Ridge predictions reproduced']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'results/calendar_controls_v1')
    args = parser.parse_args()
    out = args.out
    protocol = json.loads((out/'protocol.json').read_text())
    if (out/'predictions.csv').exists() or (out/'run.json').exists():
        raise FileExistsError('Preserve prior results; use a new versioned directory')
    started = time.perf_counter()
    identities = {str(p.relative_to(ROOT)): sha(p) for p in [
        out/'protocol.json', Path(__file__), ROOT/'src/forecasting.py',
        ROOT/'src/extended_validation.py', ROOT/'data/external/latest_state_energy_GWh.csv']}
    data = load_data('latest')
    rows, fits = [], []
    for state in STATES:
        frames, event = covariates(data.index, state, protocol)
        for year in protocol['years']:
            origins = pd.date_range(f'{year}-01-01', f'{year}-12-18')
            for h in protocol['leads']:
                dates = origins + pd.Timedelta(days=h-1)
                for arm in protocol['arms']:
                    pred, scale, fit = train_predict(data[state], frames[arm], h, year, origins)
                    fits.append(dict(state=state, year=year, horizon=h, arm=arm, **fit))
                    rows.append(pd.DataFrame(dict(state=state, year=year, origin=origins,
                        date=dates, horizon=h, arm=arm, prediction=pred,
                        actual=data[state].reindex(dates).to_numpy(),
                        event=event[data.index.get_indexer(dates)].astype(int), mase_scale=scale)))
            # Completed state-year checkpoint; retained if a later fit fails.
            pd.concat(rows, ignore_index=True).to_csv(out/'checkpoint_predictions.csv', index=False)
            pd.DataFrame(fits).to_csv(out/'fit_log.csv', index=False)
            print('Completed', state, year, flush=True)
    d = pd.concat(rows, ignore_index=True)
    d.to_csv(out/'predictions.csv', index=False)
    checks = score(d, out, protocol)
    protected = json.loads((out/'protected_before.json').read_text())
    assert all(sha(ROOT/name) == digest for name, digest in protected.items())
    checks['historical_data_and_results_unchanged'] = len(protected)
    run = dict(seconds=time.perf_counter()-started, fits=len(fits), rows=len(d),
        python=platform.python_version(), packages={p: importlib.metadata.version(p)
            for p in ['numpy', 'pandas', 'scikit-learn', 'holidays']}, input_hashes=identities,
        placebo_shifts=placebo_shifts(protocol), checks=checks)
    (out/'run.json').write_text(json.dumps(run, indent=2)+'\n')
    print(json.dumps(run, indent=2))


if __name__ == '__main__':
    main()
