"""Reusable, causal forecasting components. No jobs run on import."""
from pathlib import Path
import numpy as np
import pandas as pd
import holidays
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
ROOT=Path(__file__).resolve().parents[1]
STATES={'Karnataka':'KA','Delhi':'DL','Maharashtra':'MH'}
MODES=['A_history','B_calendar','C_holiday','D_festival']

def load_data(source='original'):
    f=ROOT/('data/clean_daily_energy_GWh.csv' if source=='original' else 'data/external/latest_state_energy_GWh.csv')
    d=pd.read_csv(f,index_col=0,parse_dates=True).sort_index()
    if d.index.has_duplicates: raise ValueError('Duplicate dates are not permitted')
    d=d[list(STATES)].asfreq('D')
    return d.where(d>0)

def causal_fill(series):
    a=series.to_numpy(dtype=float,copy=True)
    for i in range(len(a)):
        if not np.isfinite(a[i]):
            a[i]=a[i-7] if i>=7 and np.isfinite(a[i-7]) else (a[i-1] if i else np.nan)
    return pd.Series(a,index=series.index,name=series.name)

def calendar(index,state):
    """Known calendar features only. +/- shifts of scheduled dates are causal inputs."""
    h=holidays.country_holidays('IN',subdiv=STATES[state],years=range(index.min().year-1,index.max().year+2))
    names=pd.Series([h.get(d.date(),'') for d in index],index=index)
    ordinary=pd.DataFrame({f'dow_{i}':(index.dayofweek==i).astype(float) for i in range(7)},index=index)
    for k in [1,2,3]:
        ordinary[f'sin_{k}']=np.sin(2*np.pi*k*index.dayofyear/365.2425)
        ordinary[f'cos_{k}']=np.cos(2*np.pi*k*index.dayofyear/365.2425)
    # A single main festival anchor avoids different window lengths from subsidiary holidays.
    diwali=names.str.fullmatch(r'Diwali \(Deepavali\)',case=False).astype(float)
    festival=pd.DataFrame({f'diwali_{k}':diwali.shift(k,fill_value=0.) for k in range(-3,4)},index=index)
    full=pd.concat([ordinary,names.ne('').astype(float).rename('holiday'),festival],axis=1)
    cols={'A_history':[],'B_calendar':list(ordinary),'C_holiday':list(ordinary)+['holiday'],'D_festival':list(full)}
    return full,cols,festival.any(axis=1),names

def history_vector(y,origin):
    """Features at a forecast origin use targets strictly before that origin."""
    a=y.loc[:origin-pd.Timedelta(days=1)]
    return np.array([a.iloc[-k] for k in [1,2,7,14,28]]+[a.iloc[-7:].mean()],dtype=float)

def design(y,cal,cols,horizon,origins):
    return np.vstack([np.r_[history_vector(y,o),cal.loc[o+pd.Timedelta(days=horizon-1),cols].to_numpy(dtype=float)] for o in origins])

def fit_direct(y,observed,cal,cols,horizon,train_end='2021-12-31',context=730):
    end=pd.Timestamp(train_end); start=end-pd.Timedelta(days=context-1)
    origins=pd.date_range(start,end-pd.Timedelta(days=horizon-1))
    origins=pd.DatetimeIndex([o for o in origins if o-pd.Timedelta(days=28)>=y.index.min() and pd.notna(observed.get(o+pd.Timedelta(days=horizon-1)))])
    X=design(y,cal,cols,horizon,origins); target=observed.reindex(origins+pd.Timedelta(days=horizon-1)).to_numpy()
    valid=np.isfinite(X).all(axis=1)&np.isfinite(target)
    return make_pipeline(StandardScaler(),Ridge(alpha=10)).fit(X[valid],target[valid])

def mase_scale(observed,train_end='2021-12-31',context=730):
    a=observed.loc[:train_end].tail(context)
    scale=float((a-a.shift(7)).abs().mean())
    if not np.isfinite(scale) or scale<=0: raise ValueError('Invalid training scale')
    return scale

def choose_origins(year,stride=28):
    # Predeclared regular schedule plus one origin covering main Diwali +/-3 window.
    extra={2022:'2022-10-21',2023:'2023-11-09',2024:'2024-10-29',2025:'2025-10-17'}
    dates=list(pd.date_range(f'{year}-01-01',f'{year}-12-18',freq=f'{stride}D'))
    if year in extra: dates.append(pd.Timestamp(extra[year]))
    return sorted(set(dates))
