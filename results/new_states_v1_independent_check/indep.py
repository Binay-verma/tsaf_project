import pandas as pd, numpy as np, hashlib, json
R='/home/claude/handoff/repo/results/new_states_v1/'
OUT='/tmp/claude-0/-home-claude/35b207ff-6d9f-5312-a4ab-62082b85f7c3/scratchpad/independent/'
paths={'sarimax':'event_window/sarimax','timesfm_2017_2020':'fm_2017_2020/timesfm','timesfm_2021_2025':'fm_2021_2025/timesfm',
       'lightgbm_capacity2':'event_window/lightgbm_capacity2'}
def load(p):
    d=R+p
    assert hashlib.sha256(open(d+'/predictions.csv','rb').read()).hexdigest()==json.load(open(d+'/run.json'))['predictions_sha256']
    return pd.read_csv(d+'/predictions.csv')
dfs={'sarimax':load(paths['sarimax']),'lightgbm_capacity2':load(paths['lightgbm_capacity2']),
     'timesfm':pd.concat([load(paths['timesfm_2017_2020']),load(paths['timesfm_2021_2025'])])}
cal=pd.read_csv('/home/claude/handoff/repo/review/new_states_v1/calendar_entries_2015_2025.csv')
src=cal.groupby(['state','family','year']).candidate_source.agg(lambda s:set(s))
official_cells={k for k,v in src.items() if v<= {'official','government reproduction'}}
def cellvals(df):
    df=df[(df.horizon==1)&(df.arm.isin(['day5','pooled_day5']))&(df.year.between(2017,2025))].copy()
    assert df[['actual','prediction','mase_scale']].notna().all().all() and (df.mase_scale>0).all()
    df['mase']=(df.prediction-df.actual).abs()/df.mase_scale
    t=df.groupby(['state','family','year','arm']).mase.mean().unstack()
    assert t.notna().all().all()
    t['d']=t.day5-t.pooled_day5
    # check balance
    return t['d'].reset_index()
def clusters(cv,drop_years=(),cells=None):
    cv=cv[~cv.year.isin(drop_years)]
    if cells is not None: cv=cv[[ (s,f,y) in cells for s,f,y in zip(cv.state,cv.family,cv.year)]]
    return cv.groupby(['family','year']).d.mean().reset_index()   # equal weight over states
def test(cl,sign,N=1_000_000,seed=20261113):
    v=cl.d.values*sign   # sign=+1 for positive hypothesis, -1 for negative -> test statistic in hypothesised direction
    obs=v.mean()
    rng=np.random.default_rng(seed)
    k=0; B=100_000; done=0
    while done<N:
        b=min(B,N-done)
        s=rng.choice([-1.0,1.0],size=(b,len(v)))
        k+=int(((s*v).mean(1)>=obs-1e-15).sum()); done+=b
    return obs,(k+1)/(N+1)
def run(drop=(),cells=None,tag=''):
    rows=[]
    for h,m,sg in [('H1','sarimax',-1),('H2','timesfm',1),('H3','lightgbm_capacity2',1)]:
        cv=cellvals(dfs[m]); cl=clusters(cv,drop,cells)
        eff,p=test(cl,sg)
        opp=test(cl,-sg)[1]
        yr=cl.groupby('year').d.mean()
        ny=int(((yr*sg)>0).sum())
        rows.append(dict(h=h,model=m,n_clusters=len(cl),n_years=len(yr),effect=eff*sg,p=p,p_opp=opp,years_in_dir=ny,
                         n_states_cells=int(len(cv if cells is None else [1 for s,f,y in zip(cv.state,cv.family,cv.year) if (s,f,y) in cells]))))
    t=pd.DataFrame(rows)
    # Holm
    order=t.p.argsort().values; m=len(t); adj=np.zeros(m); run_max=0
    for i,idx in enumerate(order):
        run_max=max(run_max,(m-i)*t.p[idx]); adj[idx]=min(1,run_max)
    t['p_holm']=adj
    need=6 if not drop else None
    return t
def decide(t,need):
    out=[]
    for _,r in t.iterrows():
        if r.p_holm<0.05 and r.years_in_dir>=need: out.append('CONFIRMED')
        elif r.effect*(-1 if r.h=='H1' else 1)<0 and r.p_opp<0.05: out.append('CONTRADICTED')
        else: out.append('NOT CONFIRMED')
    return out
res={}
res['primary']=run(); res['no2020_2021']=run(drop=(2020,2021)); res['official_only']=run(cells=official_cells)
for k,t in res.items():
    nyears=t.n_years.iloc[0]
    t['decision_6of9']=decide(t,6)
    t['decision_two_thirds_of_years_present']=decide(t,int(np.ceil(2/3*nyears)))
    t.to_csv(OUT+f'results_{k}.csv',index=False)
    print(k); print(t.round(6).to_string())
