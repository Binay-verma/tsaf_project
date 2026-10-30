"""Development-only one-day rolling pilot. Run from project root."""
from pathlib import Path
import hashlib, json, platform, importlib.metadata
import numpy as np
import pandas as pd
import holidays
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
STATES={'Karnataka':'KA','Delhi':'DL','Maharashtra':'MH'}
RAW=ROOT/'data/raw/corrected_daily_energy_met_MU.csv'
assert hashlib.md5(RAW.read_bytes()).hexdigest()=='172540c2c13282cc3dd4c9679b537aa0'
raw=pd.read_csv(RAW,parse_dates=['Date'])
assert not raw.Date.isna().any()
idx=pd.date_range(raw.Date.min(),raw.Date.max(),freq='D')
clean=pd.DataFrame(index=idx)
conflicts=[]
for state in STATES:
    for date,g in raw.groupby('Date'):
        vals=g[state].dropna().unique()
        if len(vals)>1: conflicts.append({'date':str(date.date()),'state':state,'values':vals.tolist()})
        clean.loc[date,state]=vals[0] if len(vals)==1 and vals[0]>0 else np.nan
clean.index.name='date'
clean.to_csv(ROOT/'data/clean_daily_energy_GWh.csv')
# Preserve observed labels. Input-only fills use history, never later values.
filled=clean.copy()
for state in STATES:
    for i in range(len(filled)):
        if pd.isna(filled.iloc[i][state]):
            prior=filled[state].iloc[:i]
            filled.loc[idx[i],state]=prior.iloc[-7] if len(prior)>=7 and pd.notna(prior.iloc[-7]) else (prior.iloc[-1] if len(prior) else np.nan)
quality=[]
for state in STATES:
    for year,g in clean.groupby(clean.index.year):
        quality.append({'state':state,'year':year,'calendar_days':len(g),'observed':int(g[state].notna().sum()),'missing_or_conflicting':int(g[state].isna().sum())})
pd.DataFrame(quality).to_csv(OUT/'coverage.csv',index=False)
(OUT/'audit.json').write_text(json.dumps({'raw_rows':len(raw),'unique_dates':raw.Date.nunique(),'duplicate_extra_rows':int(raw.Date.duplicated().sum()),'missing_dates':len(idx.difference(raw.Date)),'conflicts':conflicts,'start':str(idx.min().date()),'end':str(idx.max().date())},indent=2))
records=[]; calendar_rows=[]; checks=[]
fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
for ax,(state,subdiv) in zip(axes,STATES.items()):
    target=clean[state]; y=filled[state]
    cal=holidays.country_holidays('IN',subdiv=subdiv,years=range(2013,2025))
    names=pd.Series([cal.get(d.date(),'') for d in idx],index=idx)
    event=names.str.contains('diwali|deepavali',case=False,regex=True)
    # Fixed +/-3-day exploratory Diwali window; no target-dependent selection.
    offsets=np.arange(-3,4)
    event_features=pd.DataFrame({f'diwali_offset_{k}':event.shift(k,fill_value=False).astype(int) for k in offsets},index=idx)
    ordinary=pd.DataFrame({f'weekday_{k}':(idx.dayofweek==k).astype(int) for k in range(7)},index=idx)
    for k in (1,2,3):
        ordinary[f'annual_sin_{k}']=np.sin(2*np.pi*k*idx.dayofyear/365.2425)
        ordinary[f'annual_cos_{k}']=np.cos(2*np.pi*k*idx.dayofyear/365.2425)
    lag=pd.DataFrame({f'lag_{k}':y.shift(k) for k in (1,2,7,14,28)},index=idx)
    lag['past_7_mean']=y.shift(1).rolling(7).mean()
    holiday=pd.DataFrame({'public_holiday':names.ne('').astype(int)},index=idx)
    for date in idx:
        calendar_rows.append({'date':date.date(),'state':state,'holiday_name':names.loc[date],'diwali_day':int(event.loc[date]),'diwali_window':int(event_features.loc[date].any()),'verification':'library_generated_not_officially_verified'})
    # Restrict fit labels to observed pre-2022 values. Lag inputs can be causally imputed.
    train=(idx>='2015-01-01')&(idx<'2022-01-01')&target.notna()&lag.notna().all(axis=1)
    validation=(idx>='2022-01-01')&(idx<'2023-01-01')&target.notna()&lag.notna().all(axis=1)
    scale_pairs=(idx>='2015-01-01')&(idx<'2022-01-01')&target.notna()&target.shift(7).notna()
    denom=float((target-target.shift(7)).abs()[scale_pairs].mean())
    assert denom>0 and idx[train].max()<idx[validation].min()
    predictions={'seasonal_naive_7':y.shift(7),'last_value':y.shift(1)}
    inputs={'ridge_A_history':lag,'ridge_B_calendar':pd.concat([lag,ordinary],axis=1),'ridge_C_holiday':pd.concat([lag,ordinary,holiday],axis=1),'ridge_D_diwali_window':pd.concat([lag,ordinary,holiday,event_features],axis=1)}
    for model,X in inputs.items():
        est=make_pipeline(StandardScaler(),Ridge(alpha=10))
        est.fit(X.loc[train],target.loc[train])
        predictions[model]=pd.Series(est.predict(X.loc[validation]),index=idx[validation])
    # Training-only fit over last two years; update state with past observations.
    series=y.loc['2020-01-01':'2021-12-31']/100
    fit=SARIMAX(series,order=(1,0,0),seasonal_order=(1,0,0,7),trend='c',enforce_stationarity=False).fit(disp=False,maxiter=100)
    checks.append({'state':state,'sarimax_converged':bool(fit.mle_retvals['converged'])})
    sp={}
    for date in pd.date_range('2022-01-01','2022-12-31'):
        sp[date]=float(fit.forecast(1).iloc[0]*100)
        fit=fit.extend(pd.Series([y.loc[date]/100],index=pd.DatetimeIndex([date],freq='D')))
    predictions['sarimax_A_history']=pd.Series(sp)
    for model,pred in predictions.items():
        for date in idx[validation]:
            records.append({'state':state,'date':date,'model':model,'actual':target.loc[date],'prediction':pred.loc[date],'training_mase_scale':denom,'public_holiday':int(holiday.loc[date].iloc[0]),'diwali_window':int(event_features.loc[date].any())})
    ax.plot(target.loc['2015':],lw=.6); ax.set_title(state); ax.set_ylabel('GWh/day'); ax.axvspan(pd.Timestamp('2022-01-01'),pd.Timestamp('2022-12-31'),alpha=.12,color='orange')
fig.suptitle('Observed electricity supplied; orange = development year'); fig.tight_layout(); fig.savefig(OUT/'observed_series.png',dpi=160); plt.close(fig)
pred=pd.DataFrame(records); assert pred.prediction.notna().all(); assert pred.date.max()<pd.Timestamp('2023-01-01')
pred['absolute_error']=(pred.actual-pred.prediction).abs(); pred.to_csv(OUT/'validation_predictions.csv',index=False)
rows=[]
for subset,mask in {'all':np.ones(len(pred),dtype=bool),'diwali_window':pred.diwali_window.eq(1),'outside_diwali_window':pred.diwali_window.eq(0)}.items():
    for (state,model),g in pred.loc[mask].groupby(['state','model']):
        rows.append({'state':state,'model':model,'subset':subset,'n_scored':len(g),'MAE_GWh':g.absolute_error.mean(),'MASE':(g.absolute_error/g.training_mase_scale).mean()})
pd.DataFrame(rows).to_csv(OUT/'validation_metrics.csv',index=False)
pd.DataFrame(calendar_rows).to_csv(ROOT/'data/exploratory_calendar.csv',index=False)
(OUT/'checks.json').write_text(json.dumps({'assertions_passed':['raw_checksum','chronological_split','positive_training_mase_scale','no_missing_predictions','no_2023_holdout_predictions'],'model_checks':checks},indent=2))
versions={x:importlib.metadata.version(x) for x in ['numpy','pandas','scikit-learn','statsmodels','holidays','matplotlib']}
(OUT/'versions.json').write_text(json.dumps({'python':platform.python_version(),**versions},indent=2))
print(pd.DataFrame(rows).query("subset=='all'").round(3).to_string(index=False))
