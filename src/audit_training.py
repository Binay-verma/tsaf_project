"""Training diagnostics only. Never tune using evaluation errors."""
import pandas as pd,numpy as np
from forecasting import *
from pathlib import Path
import sys,json
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/benchmark_original_s28';cfg=json.loads((p/'protocol.json').read_text());d=load_data(cfg['source']);records=[]
for state in STATES:
 y=causal_fill(d[state]);cal,cols,_,_=calendar(y.index,state)
 for mode in MODES:
  for h in [1,7,14]:
   model=fit_direct(y,d[state],cal,cols[mode],h)
   end=pd.Timestamp('2021-12-31');start=end-pd.Timedelta(days=729)
   orig=pd.date_range(start,end-pd.Timedelta(days=h-1));target=d[state].reindex(orig+pd.Timedelta(days=h-1)).to_numpy();X=design(y,cal,cols[mode],h,orig);valid=np.isfinite(target)&np.isfinite(X).all(axis=1);yp=model.predict(X[valid])
   records.append({'state':state,'mode':mode,'horizon':h,'train_samples':int(valid.sum()),'train_MAE_GWh':np.mean(np.abs(yp-target[valid])),'feature_count':X.shape[1],'alpha':10})
a=pd.DataFrame(records);m=pd.read_csv(p/'metrics.csv').query("subset=='all' and model=='ridge'")
for year in [2022,2023]:
 q=m[m.year==year][['state','mode','horizon','MAE_GWh']].rename(columns={'MAE_GWh':f'evaluation_{year}_MAE_GWh'});a=a.merge(q,on=['state','mode','horizon'])
a.to_csv(p/'training_diagnostics.csv',index=False)
print(a.round(3).to_string(index=False))
