from extended_validation import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 d=pd.read_csv(OUT/'predictions.csv',parse_dates=['origin','date']);s=pd.read_csv(OUT/'sarimax_events.csv',parse_dates=['origin','date']);d=pd.concat([d,s],ignore_index=True)
 if (OUT/'lightgbm_daily.csv').exists():d=pd.concat([d,pd.read_csv(OUT/'lightgbm_daily.csv',parse_dates=['origin','date'])],ignore_index=True)
 # Refresh membership from the declared anchors (no numerical forecast changes).
 source=load_data('latest')
 for state in STATES:
  _,_,event=features(source.index,state);mask=d.state.eq(state);d.loc[mask,'festival_window']=event.reindex(d.loc[mask,'date']).astype(int).to_numpy()
 assert not d.duplicated(['state','origin','horizon','model','mode']).any()
 assert ((d.date-d.origin).dt.days==d.horizon-1).all();assert np.isfinite(d.prediction).all()
 for state,g in d.groupby('state'):np.testing.assert_allclose(g.actual,source[state].reindex(g.date),equal_nan=True)
 for year,yr in d[d.cohort.eq('daily')].groupby('year'):
  ref=None
  for _,g in yr.groupby(['model','mode']):
   keys=set(map(tuple,g[['state','origin','horizon']].to_numpy()))
   if ref is None:ref=keys
   else:assert keys==ref,f'Mismatched daily cases in {year}'
 if (OUT/'lightgbm_selected.csv').exists():
  chosen=pd.read_csv(OUT/'lightgbm_selected.csv');searched=pd.read_csv(OUT/'lightgbm_validation_search.csv');keys=['state','mode','horizon']
  minima=searched.groupby(keys).validation_MAE_GWh.min();np.testing.assert_allclose(chosen.set_index(keys).validation_MAE_GWh.sort_index(),minima.sort_index())
  assert pd.to_datetime(chosen.validation_target_max).max()<pd.Timestamp('2026-01-01')
  assert (pd.to_datetime(chosen.training_target_max)<pd.Timestamp('2025-07-05')).all()
 d=d[d.observed.eq(1)].copy();d['ae']=(d.actual-d.prediction).abs();d['scaled']=d.ae/d.mase_scale
 d.to_csv(OUT/'all_verified_predictions.csv',index=False)
 group=['year','state','horizon','model','mode']
 daily=d[d.cohort.eq('daily')].groupby(group).agg(MAE_GWh=('ae','mean'),MASE=('scaled','mean'),n=('ae','size')).reset_index();daily.to_csv(OUT/'daily_state_metrics.csv',index=False)
 macro=daily.groupby(['year','horizon','model','mode']).agg(MASE=('MASE','mean'),n_each_state_min=('n','min')).reset_index();macro.to_csv(OUT/'daily_macro_metrics.csv',index=False)
 event=d[d.festival_window.eq(1)&d.year.le(2025)].copy()
 # Each model/mode must cover the same event-target cases. Counts alone are insufficient.
 reference=None
 for _,g in event.groupby(['model','mode']):
  keys=set(map(tuple,g[['state','origin','horizon']].to_numpy()))
  if reference is None:reference=keys
  else:assert keys==reference,'Mismatched event evaluation cases'
 ev=event.groupby(group).agg(MAE_GWh=('ae','mean'),MASE=('scaled','mean'),n=('ae','size')).reset_index();ev.to_csv(OUT/'festival_state_metrics.csv',index=False)
 em=ev.groupby(['year','horizon','model','mode']).MASE.mean().reset_index();em.to_csv(OUT/'festival_macro_metrics.csv',index=False)
 # Improvements compare matched errors per state/year; never average raw GWh across states.
 z=ev.pivot(index=['year','state','horizon','model'],columns='mode',values='MAE_GWh').reset_index();z['festival_improvement_pct']=100*(z.B_calendar-z.D_regional_festival)/z.B_calendar;z.to_csv(OUT/'festival_effects.csv',index=False)
 # Four event years are the resampling units; states/days are not independent events.
 rng=np.random.default_rng(42);rows=[]
 for (model,h),g in z.dropna(subset=['B_calendar','D_regional_festival']).groupby(['model','horizon']):
  v=g.groupby('year').festival_improvement_pct.mean();samples=np.array([rng.choice(v.to_numpy(),len(v),replace=True).mean() for _ in range(2000)])
  rows.append({'model':model,'horizon':h,'mean_state_year_improvement_pct':v.mean(),'year_bootstrap_low':np.quantile(samples,.025),'year_bootstrap_high':np.quantile(samples,.975),'independent_years':len(v),'warning':'Only four years; descriptive uncertainty, not strong generalisation evidence'})
 pd.DataFrame(rows).to_csv(OUT/'festival_year_uncertainty.csv',index=False)
 checks={'rows':len(d),'daily_forecast_origins_per_state':d[d.model.eq('chronos2')&d['mode'].eq('A_history')].groupby('state').origin.nunique().to_dict(),'event_years':sorted(event.year.unique().tolist()),'passed':['unique cases','finite predictions','date/horizon alignment','actuals match source','identical matched event cases'],'calendar_scope':'Twelve annual state-year schedules audited for 2022-2025 against publications; not a complete amendment timeline or all training-year holidays','model_training':'No hyperparameter tuning; annual pre-year fitting; pinned Chronos inference only'}
 checks['model_training']='Fixed Ridge/SARIMAX annual pre-year fits; pinned Chronos inference; exploratory LightGBM hyperparameters selected only on pre-2026 validation'
 checks['passed']+=['identical daily cases within each year','LightGBM selection equals pre-2026 validation minimum','purged LightGBM training/validation target dates']
 (OUT/'verification.json').write_text(json.dumps(checks,indent=2))
 fig,axs=plt.subplots(1,2,figsize=(12,5))
 for ax,h in zip(axs,[1,14]):
  q=macro[(macro.year==2026)&(macro.horizon==h)].copy();q['label']=q.model+' / '+q['mode'];q.sort_values('MASE').plot.barh(x='label',y='MASE',legend=False,ax=ax);ax.set_title(f'2026 post-upload / day {h}');ax.set_xlabel('Macro MASE (lower is better)')
 fig.tight_layout();fig.savefig(OUT/'post_upload_comparison.png',dpi=160);plt.close(fig)
 print('DAILY 2025/26\n',macro[macro.year.ge(2025)].round(4).to_string(index=False));print('FESTIVAL EFFECTS\n',pd.DataFrame(rows).round(3).to_string(index=False));print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
