"""Data-feasibility scan for extending the festival study to more Indian states (no forecasting).

Reads only the existing source file. Writes review/state_expansion_v1/data_feasibility.csv/json.
Run from the repository root: python src/state_expansion_scan_v1.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'data/external/POSOCO_data.csv'
OUT = ROOT/'review/state_expansion_v1'
NON_STATE = {'NR', 'WR', 'SR', 'ER', 'NER', 'India', 'DVC', 'Essar steel', 'AMNSIL', 'DNHDDPDCL', 'BALCO', 'RIL JAMNAGAR', 'DD', 'DNH'}
WINDOW = ('2020-01-01', '2025-12-31')  # 730-day context before 2022 plus the 2022-2025 study years


def main():
    d = pd.read_csv(SRC)
    d.index = pd.to_datetime(d.yyyymmdd.astype(str))
    idx = pd.date_range(*WINDOW)
    rows = []
    for c in d.columns:
        if not c.endswith(': EnergyMet'):
            continue
        name = c.split(':')[0]
        if name in NON_STATE or name.startswith(('Railways', 'Bulk Consumer')):
            continue
        s = d[c].reindex(idx)
        s = s.where(s > 0)
        rows.append(dict(state=name, column=c, missing_days=int(s.isna().sum()), mean_GWh=round(float(s.mean()), 1),
                         first=str(d[c].dropna().index.min().date()), last=str(d[c].dropna().index.max().date())))
    t = pd.DataFrame(rows).sort_values('mean_GWh', ascending=False)
    t['usable'] = (t.missing_days <= 7) & (t.mean_GWh >= 50)
    t['already_in_study'] = t.state.isin(['Delhi', 'Karnataka', 'Maharashtra'])
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT/'data_feasibility.csv', index=False)
    json.dump(dict(created_utc=datetime.now(timezone.utc).isoformat(), source=str(SRC.relative_to(ROOT)), window=WINDOW,
                   rule='usable = at most 7 missing or non-positive days in the window and mean >= 50 GWh/day',
                   usable_new_states=t[t.usable & ~t.already_in_study].state.tolist(), demand_values_inspected='means and missing counts only'),
              open(OUT/'data_feasibility.json', 'w'), indent=1)
    print(t.to_string(index=False))


if __name__ == '__main__':
    main()
