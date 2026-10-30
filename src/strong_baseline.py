"""Exploratory 2026 comparison: LightGBM selected on pre-2026 validation only."""
import json
from itertools import product
from lightgbm import LGBMRegressor
from extended_validation import *

def main():
 grid=[dict(num_leaves=l,n_estimators=n,reg_lambda=r) for l,n,r in product([7,15],[100,300],[1.,10.])]
 protocol={'status':'exploratory: 2026 outcomes were already examined before adding this baseline','grid':grid,'fixed':{'learning_rate':.05,'min_child_samples':20,'random_state':42},'selection':'lowest pre-2026 temporal validation MAE; no test-based selection','training_window':['2024-01-02','2025-12-31'],'validation_start':'2025-07-05','purge':'training target strictly before validation start','test_origins':['2026-01-01','2026-10-15']}
 (OUT/'lightgbm_protocol.json').write_text(json.dumps(protocol,indent=2))
 data=load_data('latest');rows=[];search=[];selected=[]
 start=pd.Timestamp('2024-01-02');end=pd.Timestamp('2025-12-31');vs=pd.Timestamp('2025-07-05')
 for state in STATES:
  observed=data[state];y=causal_fill(observed);cal,cols,event=features(y.index,state);scale=float((observed.loc[start:end]-observed.loc[start:end].shift(7)).abs().mean())
  for mode in MODES:
   for h in [1,7,14]:
    train=pd.date_range(start,vs-pd.Timedelta(days=h));val=pd.date_range(vs,end-pd.Timedelta(days=h-1));full=pd.date_range(start,end-pd.Timedelta(days=h-1));test=pd.date_range('2026-01-01',min(pd.Timestamp('2026-12-18'),y.index.max()-pd.Timedelta(days=13)))
    assert train.max()+pd.Timedelta(days=h-1)<val.min()
    def design(orig):
     X=fast_design(y,cal,cols[mode],h,orig);t=observed.reindex(orig+pd.Timedelta(days=h-1)).to_numpy();valid=np.isfinite(t)&np.isfinite(X).all(axis=1);return X[valid],t[valid]
    X,t=design(train);V,vt=design(val);best=None
    def model(p):return LGBMRegressor(**p,learning_rate=.05,min_child_samples=20,random_state=42,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    for i,p in enumerate(grid):
     m=model(p).fit(X,t);score=float(np.mean(np.abs(vt-m.predict(V))));search.append(dict(state=state,mode=mode,horizon=h,configuration=i,validation_MAE_GWh=score,**p))
     if best is None or score<best[0]:best=(score,i,p)
    selected.append(dict(state=state,mode=mode,horizon=h,configuration=best[1],validation_MAE_GWh=best[0],training_target_max=str((train.max()+pd.Timedelta(days=h-1)).date()),validation_target_max=str((val.max()+pd.Timedelta(days=h-1)).date()),**best[2]))
    X,t=design(full);m=model(best[2]).fit(X,t);pred=m.predict(fast_design(y,cal,cols[mode],h,test))
    for o,p in zip(test,pred):add(rows,state,o,h,'lightgbm',mode,p,observed,event,scale,'daily')
   print('LightGBM complete',state,mode,flush=True)
 pd.DataFrame(rows).to_csv(OUT/'lightgbm_daily.csv',index=False);pd.DataFrame(search).to_csv(OUT/'lightgbm_validation_search.csv',index=False);pd.DataFrame(selected).to_csv(OUT/'lightgbm_selected.csv',index=False)
 print('DONE',len(rows),flush=True)
if __name__=='__main__':main()
