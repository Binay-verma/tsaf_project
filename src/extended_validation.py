"""Predeclared dense daily evaluation plus matched calendar/festival stress tests.
No hyperparameter search. Does not modify the earlier pilot or holdout results.
"""
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from forecasting import ROOT,STATES,load_data,causal_fill,calendar
OUT=ROOT/'results/extended_validation';OUT.mkdir(exist_ok=True)
MAIN={2020:'2020-11-14',2021:'2021-11-04',2022:'2022-10-24',2023:'2023-11-12',2024:'2024-10-31',2025:'2025-10-20'}
# Explicit state holiday dates (not inferred from electricity outcomes).
EXTRA={'Karnataka':{2022:['2022-10-26'],2023:['2023-11-14'],2024:['2024-11-02'],2025:['2025-10-22']},'Delhi':{},'Maharashtra':{2022:['2022-10-26'],2023:['2023-11-14'],2024:['2024-11-01','2024-11-02'],2025:['2025-10-21','2025-10-22']}}
MODES=['A_history','B_calendar','D_regional_festival']

_FEATURE_CACHE={}

def features(idx,state):
 key=(state,idx.min(),idx.max(),len(idx))
 if key in _FEATURE_CACHE:return _FEATURE_CACHE[key]
 c,oldcols,_,_=calendar(idx,state);b=oldcols['B_calendar'];event=pd.Series(False,index=idx)
 for year,date in MAIN.items():
  for date in [date]+EXTRA.get(state,{}).get(year,[]):
   if pd.Timestamp(date) in idx:event.loc[date]=True
 festival=pd.DataFrame({f'event_{k}':event.shift(k,fill_value=False).astype(float) for k in range(-3,4)},index=idx)
 result=(pd.concat([c[b],festival],axis=1),{'A_history':[],'B_calendar':b,'D_regional_festival':b+list(festival)},festival.any(axis=1))
 _FEATURE_CACHE[key]=result
 return result

def fast_design(y,cal,cols,h,origins):
 lag=pd.DataFrame({f'lag_{k}':y.shift(k) for k in [1,2,7,14,28]});lag['mean']=y.shift(1).rolling(7).mean()
 return np.concatenate([lag.reindex(origins).to_numpy(),cal.reindex(origins+pd.Timedelta(days=h-1))[cols].to_numpy()],axis=1)

def add(rows,state,o,h,model,mode,pred,observed,event,scale,cohort):
 date=o+pd.Timedelta(days=h-1);actual=observed.loc[date]
 rows.append({'state':state,'origin':str(o.date()),'date':str(date.date()),'year':o.year,'horizon':h,'model':model,'mode':mode,'prediction':float(pred),'actual':actual,'observed':int(pd.notna(actual)),'festival_window':int(event.loc[date]),'mase_scale':scale,'cohort':cohort})

def execute():
 from cache_identity import guard
 guard()
 t=time.perf_counter();data=load_data('latest');rows=[];tasks=[];classfile=OUT/'classical_daily.csv'
 for state in STATES:
  observed=data[state];y=causal_fill(observed);cal,cols,event=features(y.index,state)
  for year in [2022,2023,2024,2025,2026]:
   end=min(pd.Timestamp(f'{year}-12-18'),y.index.max()-pd.Timedelta(days=13));orig=pd.date_range(f'{year}-01-01',end)
   trainend=pd.Timestamp(f'{year-1}-12-31');trainstart=trainend-pd.Timedelta(days=729)
   tr=observed.loc[trainstart:trainend];scale=float((tr-tr.shift(7)).abs().mean());assert scale>0
   for mode in MODES:
    for h in [1,7,14]:
     trorig=pd.date_range(trainstart,trainend-pd.Timedelta(days=h-1));X=fast_design(y,cal,cols[mode],h,trorig);target=observed.reindex(trorig+pd.Timedelta(days=h-1)).to_numpy();valid=np.isfinite(target)&np.isfinite(X).all(axis=1)
     if mode=='D_regional_festival':assert cal.loc[trainstart:trainend,cols[mode][-7:]].to_numpy().sum()>0, 'Festival training history is missing'
     model=make_pipeline(StandardScaler(),Ridge(alpha=10)).fit(X[valid],target[valid]);pred=model.predict(fast_design(y,cal,cols[mode],h,orig))
     for o,v in zip(orig,pred):add(rows,state,o,h,'ridge',mode,v,observed,event,scale,'daily')
   for o in orig:
    i=y.index.get_loc(o);a=y.iloc[:i].tail(730).to_numpy(dtype=np.float32)
    for h in [1,7,14]:
     add(rows,state,o,h,'last_value','A_history',a[-1],observed,event,scale,'daily');add(rows,state,o,h,'seasonal_naive','A_history',a[-7+(h-1)%7],observed,event,scale,'daily')
    # Calendar evaluation at EVERY event-window target for EACH horizon: o = event day - h + 1.
    selected=any(bool(event.get(o+pd.Timedelta(days=h-1),False)) for h in [1,7,14])
    tasks.append((state,o,i,a,scale,selected))
   print('Prepared',state,year,len(orig),flush=True)
 pd.DataFrame(rows).to_csv(classfile,index=False)
 import torch
 from chronos import Chronos2Pipeline
 torch.set_num_threads(4);pipeline=Chronos2Pipeline.from_pretrained('amazon/chronos-2',revision='29ec3766d36d6f73f0696f85560a422f50e8498c',device_map='cpu');median=pipeline.quantiles.index(.5)
 for mode in MODES:
  cache=OUT/f'chronos_{mode}.csv'
  if cache.exists():
   cached=pd.read_csv(cache)
   for state in STATES:
    _,_,ev=features(data.index,state);mask=cached.state.eq(state);cached.loc[mask,'festival_window']=ev.reindex(pd.to_datetime(cached.loc[mask,'date'])).astype(int).to_numpy()
   rows.extend(cached.to_dict('records'));print('Reused',mode,flush=True);continue
  selected=tasks if mode=='A_history' else [x for x in tasks if x[-1]];cr=[];batch=64 if mode=='A_history' else 4
  for j in range(0,len(selected),batch):
   group=selected[j:j+batch];inputs=[]
   for state,o,i,a,scale,flag in group:
    if mode=='A_history':inputs.append(a)
    else:
     cal,cols,event=features(data.index,state);ci=cols[mode];past=cal.loc[:o-pd.Timedelta(days=1)].tail(730);future=cal.reindex(pd.date_range(o,periods=14))
     inputs.append({'target':a,'past_covariates':{c:past[c].to_numpy(dtype=np.float32) for c in ci},'future_covariates':{c:future[c].to_numpy(dtype=np.float32) for c in ci}})
   predictions=pipeline.predict(inputs,prediction_length=14,batch_size=128,context_length=730,cross_learning=False)
   for (state,o,i,a,scale,flag),q in zip(group,predictions):
    _,_,event=features(data.index,state)
    for h in [1,7,14]:add(cr,state,o,h,'chronos2',mode,float(q[0,median,h-1]),data[state],event,scale,'daily' if mode=='A_history' else 'event_matched')
   if j% (batch*5)==0:print('Chronos',mode,j+len(group),'/',len(selected),flush=True)
  pd.DataFrame(cr).to_csv(cache,index=False);rows.extend(cr);print('COMPLETE',mode,flush=True)
 pd.DataFrame(rows).to_csv(OUT/'predictions.csv',index=False)
 (OUT/'run.json').write_text(json.dumps({'seconds':time.perf_counter()-t,'rows':len(rows),'years':[2022,2023,2024,2025,2026],'no_tuning':True,'source':'latest snapshot','daily_chronos':'history only','calendar_chronos':'event matched subset only'},indent=2))
 print('DONE',len(rows),flush=True)
if __name__=='__main__':execute()
