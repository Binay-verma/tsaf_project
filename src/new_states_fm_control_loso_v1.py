"""Exploratory: leave-one-state-out for TimesFM-3 typed (registered day5) minus unpadded pooled (control pooled1), leads 7 and 14.
Run from the repository root: python src/new_states_fm_control_loso_v1.py
"""
import sys, json; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import pandas as pd, new_states_analysis_v1 as an, new_states_v1 as s
from pathlib import Path
O=Path('results/new_states_v1_fm_control')
rows=[]
for c in ['fm_2017_2020','fm_2021_2025']:
    for base,name in [(s.OUT/c/'timesfm','registered'),(O/c/'timesfm','control')]:
        d=pd.read_csv(base/'predictions.csv'); d['key']=name+':'+d.arm; rows.append(d)
d=pd.concat(rows); d['MASE']=(d.prediction-d.actual).abs()/d.mase_scale
out=[]
for hz in [7,14]:
    cell=d[d.horizon==hz].groupby(['family','year','state','key']).MASE.mean().unstack('key')
    diff=(cell['registered:day5']-cell['control:pooled1'])
    for st in [None]+sorted(diff.index.get_level_values('state').unique()):
        x=diff if st is None else diff[diff.index.get_level_values('state')!=st]
        c=x.groupby(['family','year']).mean().dropna()
        out.append(dict(horizon=hz,left_out=st or '(none)',clusters=len(c),typed_minus_pooled1=c.mean(),p_one_sided_typed_better=an.signflip(c.values,-1,100_000)))
    st=diff.groupby('state').mean()
    print(hz, st.round(4).to_dict())
r=pd.DataFrame(out); print(r.round(4).to_string(index=False))
r.to_csv(O/'analysis'/'typed_vs_pooled1_leave_one_state_out.csv',index=False)
