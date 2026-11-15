"""Festival-window demand profile on the three original states (supports simulation_typed_pooled_v3's PROFILE and the
festival-day effect quoted in the paper). Same log-demand regression as simulation_calibration_v1, but with one pooled
indicator for each offset -3..+3 from every festival anchor instead of per-family festival-day flags.
Writes results/window_profile_v1/ (profile_by_state.csv, summary.json). Descriptive; no forecasts involved.
"""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import simulation_calibration_v1 as c1  # noqa: E402

OUT = ROOT/'results/window_profile_v1'


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    a = c1.anchors()
    rows = []
    for st in ['Delhi', 'Karnataka', 'Maharashtra']:
        ly, X, fams = c1.frame(st, a)
        X = X.drop(columns=fams)
        dates = pd.to_datetime(a[a.state == st].date)
        for k in range(-3, 4):
            X[f'o{k}'] = X.index.isin(dates + pd.Timedelta(days=k)).astype(float)
        ok = ly.notna()
        b, *_ = np.linalg.lstsq(X[ok].to_numpy(), ly[ok].to_numpy(), rcond=None)
        cols = list(X.columns)
        rows.append(dict(state=st, **{f'offset_{k}': float(np.exp(b[cols.index(f'o{k}')]) - 1) for k in range(-3, 4)}))
    P = pd.DataFrame(rows)
    P.to_csv(OUT/'profile_by_state.csv', index=False)
    m = P.drop(columns='state').mean()
    s = dict(mean_effect_by_offset={k: float(v) for k, v in m.items()},
             relative_to_festival_day={k: float(v/m['offset_0']) for k, v in m.items()},
             festival_day_effect_three_state_mean=float(m['offset_0']))
    (OUT/'summary.json').write_text(json.dumps(s, indent=1))
    print(P.round(4).to_string(index=False)); print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
