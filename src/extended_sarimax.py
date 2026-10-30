from extended_validation import *
from statsmodels.tsa.statespace.sarimax import SARIMAX

def main():
 d=load_data('latest');rows=[];status=[]
 for state in STATES:
  y=causal_fill(d[state]);cal,cols,event=features(d.index,state)
  for year in [2022,2023,2024,2025]:
   dates=pd.date_range(f'{year}-01-01',f'{year}-12-18');orig=[o for o in dates if any(event.loc[o+pd.Timedelta(days=h-1)] for h in [1,7,14])]
   tr=y.loc[:f'{year-1}-12-31'].tail(730)/100;obs=d[state].reindex(tr.index);scale=float((obs-obs.shift(7)).abs().mean())
   for mode in MODES:
    cs=cols[mode];fit=SARIMAX(tr,exog=cal.loc[tr.index,cs] if cs else None,order=(1,0,0),seasonal_order=(1,0,0,7),trend='n' if cs else 'c',enforce_stationarity=False).fit(disp=False,maxiter=150)
    initial_converged=bool(fit.mle_retvals['converged'])
    if not initial_converged:fit=fit.model.fit(start_params=fit.params,disp=False,maxiter=500)
    status.append({'initial_converged_150':initial_converged,'retry_maxiter':500 if not initial_converged else None,'state':state,'year':year,'mode':mode,'converged':bool(fit.mle_retvals['converged'])});cutoff=tr.index.max()+pd.Timedelta(days=1)
    for o in orig:
     upd=y.loc[cutoff:o-pd.Timedelta(days=1)]/100
     if len(upd):fit=fit.extend(upd,exog=cal.loc[upd.index,cs] if cs else None)
     pred=fit.forecast(14,exog=cal.loc[pd.date_range(o,periods=14),cs] if cs else None)*100
     for h in [1,7,14]:add(rows,state,o,h,'sarimax',mode,pred.iloc[h-1],d[state],event,scale,'event_matched')
     cutoff=o
   print('SARIMAX',state,year,flush=True)
 pd.DataFrame(rows).to_csv(OUT/'sarimax_events.csv',index=False);(OUT/'sarimax_status.json').write_text(json.dumps(status,indent=2))
if __name__=='__main__':main()
