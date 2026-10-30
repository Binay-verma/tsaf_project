"""Repair numerical convergence using training likelihood, never evaluation loss."""
from extended_validation import *
from statsmodels.tsa.statespace.sarimax import SARIMAX
import shutil

def main():
 statuses=json.loads((OUT/'sarimax_status.json').read_text());table=pd.read_csv(OUT/'sarimax_events.csv');data=load_data('latest')
 for item in statuses:
  if item['converged']:continue
  state,year,mode=item['state'],item['year'],item['mode'];y=causal_fill(data[state]);cal,cols,event=features(data.index,state);cs=cols[mode];tr=y.loc[:f'{year-1}-12-31'].tail(730)/100
  model=SARIMAX(tr,exog=cal.loc[tr.index,cs] if cs else None,order=(1,0,0),seasonal_order=(1,0,0,7),trend='n' if cs else 'c',enforce_stationarity=False)
  first=model.fit(disp=False,maxiter=150)
  # Independent derivative-free training-only likelihood optimisation.
  fit=model.fit(start_params=first.params,method='powell',disp=False,maxiter=500)
  item['powell_training_only_retry']=True;item['powell_converged']=bool(fit.mle_retvals['converged']);item['training_loglik_initial']=float(first.llf);item['training_loglik_powell']=float(fit.llf)
  if not item['powell_converged'] or fit.llf<first.llf-1e-5:continue
  item['converged']=True;item['final_optimizer']='powell'
  mask=table.state.eq(state)&table.year.eq(year)&table['mode'].eq(mode);old=table[mask].copy();old.to_csv(OUT/f'unconverged_{state}_{year}_{mode}.csv',index=False)
  origins=sorted(pd.to_datetime(old.origin.unique()));cutoff=tr.index.max()+pd.Timedelta(days=1);obs=data[state].reindex(tr.index);scale=float((obs-obs.shift(7)).abs().mean());rows=[]
  for o in origins:
   upd=y.loc[cutoff:o-pd.Timedelta(days=1)]/100
   if len(upd):fit=fit.extend(upd,exog=cal.loc[upd.index,cs] if cs else None)
   pred=fit.forecast(14,exog=cal.loc[pd.date_range(o,periods=14),cs] if cs else None)*100
   for h in [1,7,14]:add(rows,state,o,h,'sarimax',mode,pred.iloc[h-1],data[state],event,scale,'event_matched')
   cutoff=o
  table=pd.concat([table[~mask],pd.DataFrame(rows)],ignore_index=True)
 table.to_csv(OUT/'sarimax_events.csv',index=False);(OUT/'sarimax_status.json').write_text(json.dumps(statuses,indent=2));print([x for x in statuses if x.get('powell_training_only_retry')],flush=True)
if __name__=='__main__':main()
