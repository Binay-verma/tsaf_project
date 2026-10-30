"""Separate scalar metric/date and NumPy input reconstruction for the breadth panel."""
from collections import defaultdict
import csv,hashlib,json,math
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/feature_breadth_v1'
FAMILIES=['Holi','Dussehra','Ganesh_Chaturthi','Ugadi_Gudi_Padwa','Diwali']


def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(x.tobytes()).hexdigest()
def close(a,b):assert math.isclose(a,float(b),rel_tol=1e-10,abs_tol=1e-8),(a,b)
def case(r):return tuple(r[k] for k in ['family','state','year','origin','date','horizon'])


def main():
    reg=json.loads((OUT/'registration.json').read_text())
    sr=json.loads((OUT/'scoring_registration.json').read_text())
    assert sha(ROOT/'src/finalize_breadth_study.py')==sr['source_sha256']
    protected=json.loads((OUT/'protected_prior_files.json').read_text())
    for name,h in protected.items():assert sha(ROOT/name)==h,name
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D')
    scales={}
    for state in source:
        for year in [2024,2025]:
            end=pd.Timestamp(f'{year-1}-12-31');a=source.loc[end-pd.Timedelta(days=729):end,state]
            values=a.to_dict()
            scales[state,year]=mean(abs(y-values[d-pd.Timedelta(days=7)]) for d,y in values.items()
                if d-pd.Timedelta(days=7) in values and math.isfinite(y) and math.isfinite(values[d-pd.Timedelta(days=7)]))
    true=pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv',parse_dates=['date'])
    fake=pd.read_csv(ROOT/'results/festival_features_v1/placebo_anchors.csv',parse_dates=['date'])
    filled={}
    for state in source:
        a=source[state].to_numpy(dtype=float,copy=True)
        for i in range(len(a)):
            if not np.isfinite(a[i]) or a[i]<=0:a[i]=a[i-7] if i>=7 and np.isfinite(a[i-7]) else a[i-1] if i else np.nan
        filled[state]=pd.Series(a,index=source.index)
    def extra(dates,state,arm):
        if arm=='calendar':return np.zeros((0,len(dates)))
        if arm=='zero5':return np.zeros((5,len(dates)))
        ledger=fake if arm.startswith('placebo') else true
        flags=[]
        for family in FAMILIES:
            anchors=ledger[ledger.state.eq(state)&ledger.family.eq(family)].date
            active=anchors if 'window' not in arm else [d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3),a+pd.Timedelta(days=3))]
            flags.append(dates.isin(active).astype(float))
        if arm.startswith('pooled'):
            flags=[np.asarray(flags).any(axis=0).astype(float)]+[np.zeros(len(dates)) for _ in range(4)]
        return np.asarray(flags)
    summaries,crossings={},[]
    for cohort,ph in reg['cohorts'].items():
        out=OUT/cohort;p=json.loads((out/'protocol.json').read_text())
        assert sha(out/'protocol.json')==ph
        for name,h in p['input_hashes'].items():assert sha(ROOT/name)==h,name
        for name,h in p['design_hashes'].items():assert sha(out/name)==h,name
        expected={case(r) for r in read(out/'primary_cases.csv')}
        raw=read(out/'predictions_primary.csv');sets=defaultdict(set);cells=defaultdict(list)
        for r in raw:
            model,arm=r['model'],r['arm'];c=case(r)
            assert c in expected and c not in sets[model,arm];sets[model,arm].add(c)
            origin,day=date.fromisoformat(r['origin']),date.fromisoformat(r['date'])
            assert day-origin==timedelta(days=int(r['horizon'])-1)
            y=float(source.loc[pd.Timestamp(day),r['state']]);scale=scales[r['state'],int(r['year'])]
            close(y,r['actual']);close(scale,r['mase_scale'])
            predicted=float(r['prediction']);assert all(math.isfinite(v) for v in [y,predicted,scale])
            cells[r['family'],model,arm,r['state'],r['year'],r['horizon']].append((abs(y-predicted),abs(y-predicted)/scale))
        assert len(raw)==len(expected)*48 and set(sets)=={(m,a) for m in reg['models'] for a in reg['arms']}
        assert all(v==expected for v in sets.values())
        for r in read(out/'primary_metrics_state_year.csv'):
            values=cells[r['family'],r['model'],r['arm'],r['state'],r['year'],r['horizon']]
            assert len(values)==int(r['n']);close(mean(v[0] for v in values),r['MAE_GWh']);close(mean(v[1] for v in values),r['MASE'])
        years,families,macro=defaultdict(list),defaultdict(list),defaultdict(list)
        for (f,m,a,s,y,h),values in cells.items():years[f,m,a,y,h].append(mean(v[1] for v in values))
        for (f,m,a,y,h),values in years.items():families[f,m,a,h].append(mean(values))
        for (f,m,a,h),values in families.items():macro[m,a,h].append(mean(values))
        for r in read(out/'primary_metrics_balanced.csv'):close(mean(macro[r['model'],r['arm'],r['horizon']]),r['MASE'])
        for r in read(out/'contrasts_balanced.csv'):
            close(mean(macro[r['model'],r['arm'],r['horizon']])-mean(macro[r['model'],r['reference'],r['horizon']]),r['MASE_change'])
        cases=pd.read_csv(out/'primary_cases.csv',parse_dates=['date','origin'])
        tasks={(r.state,str(r.origin.date())) for r in cases.itertuples(index=False)}
        checked={};cache={}
        for model in ['chronos','timesfm']:
            inputs=json.loads((out/model/'inputs.json').read_text())
            assert len(inputs)==len(tasks)*8
            for arm in p['arms']:
                group=[r for r in inputs if r['arm']==arm]
                assert {(r['state'],r['origin']) for r in group}==tasks
                for r in group:
                    k=(arm,r['state'],r['origin'])
                    if k not in cache:
                        origin=pd.Timestamp(r['origin']);dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
                        assert pd.Timestamp('2022-01-01')<=dates.min()<=dates.max()<=pd.Timestamp('2025-12-31')
                        target=filled[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32)
                        columns=[(dates.dayofweek==j).astype(float) for j in range(7)]
                        for j in [1,2,3]:columns += [np.sin(2*np.pi*j*dates.dayofyear/365.2425),np.cos(2*np.pi*j*dates.dayofyear/365.2425)]
                        ex=extra(dates,r['state'],arm);cov=np.asarray(columns+list(ex),dtype=np.float32)
                        cache[k]=(digest(target),digest(cov),cov.shape[0],np.count_nonzero(cov[13:,:730],axis=1).tolist())
                    t,c,n,support=cache[k]
                    assert (r['target_sha256'],r['covariate_sha256'],r['feature_count'],r['past_nonzero_counts'])==(t,c,n,support)
                    assert r['future_target_perturbation_invariant']
                    assert pd.Timestamp(r['context_end'])<pd.Timestamp(r['origin'])
            worker=json.loads((out/model/'run.json').read_text())
            assert worker['inference_tasks']==len(inputs)
            parent=json.loads((ROOT/f'results/festival_features_v1/{model}/run.json').read_text())
            assert worker['weight_sha256']==parent['weight_sha256']
            d=pd.read_csv(out/model/'predictions.csv');qcols=sorted(c for c in d if c.startswith('q_'))
            bad=np.diff(d[qcols].to_numpy(),axis=1)<0
            assert int(bad.sum())==worker['native_quantile_crossings']
            for i,j in zip(*np.where(bad)):
                row=d.iloc[i];crossings.append(dict(cohort=cohort,model=model,arm=row.arm,state=row.state,date=row.date,horizon=int(row.horizon),lower=qcols[j],upper=qcols[j+1]))
            solo=json.loads((out/model/'solo_batch_audit.json').read_text())
            assert len(solo)==16*8 and all(math.isfinite(r['max_abs_difference']) for r in solo)
            checked[model]=dict(reconstructed_input_tasks=len(inputs),native_crossing_pairs=int(bad.sum()),max_solo_difference_GWh=max(r['max_abs_difference'] for r in solo))
        for model in ['ridge','lightgbm','lightgbm_capacity2']:
            old='strong_refit_v1' if model=='ridge' else 'stable_tree_refit_v2'
            selected=pd.read_csv(ROOT/f'results/{old}/selected.csv')
            selected=selected[selected['mode'].eq('rich_calendar')&selected.model.eq('ridge' if model=='ridge' else 'lightgbm')]
            budget={(r.state,r.year,r.horizon):json.loads(r.parameters) for r in selected.itertuples()}
            fits=json.loads((out/model/'fit_log.json').read_text());blocks=defaultdict(set)
            for r in fits:
                params=budget[r['state'],r['year'],r['horizon']].copy()
                if model=='lightgbm_capacity2':params['min_child_samples']=2
                assert r['parameters']==params
                cutoff=pd.Timestamp(r['refit'])-pd.Timedelta(days=1)
                assert pd.Timestamp(r['training_target_max'])<=cutoff
                dates=pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=r['horizon']-1),cutoff)
                y=source[r['state']].reindex(dates);valid=y.notna()&y.gt(0)
                assert int(valid.sum())==r['training_n']
                assert digest(y[valid].to_numpy())==r['training_y_sha256']
                support=np.count_nonzero(extra(dates[valid],r['state'],r['arm']),axis=1).tolist()
                assert support==list(r['feature_nonzero_training_counts'].values())
                assert r['feature_count']==(40 if r['arm']=='calendar' else 45)
                segment=cases[cases.state.eq(r['state'])&cases.year.eq(r['year'])&cases.horizon.eq(r['horizon'])&cases.origin.dt.to_period('M').eq(pd.Timestamp(r['refit']).to_period('M'))]
                assert len(segment) and segment.origin.min()>cutoff
                blocks[r['state'],r['year'],r['horizon'],r['refit']].add(r['arm'])
            assert all(v==set(p['arms']) for v in blocks.values())
            checked[model]=dict(fits=len(fits),same_selected_budgets=True,training_label_bytes_exact=True,support_reconstructed=True)
        attempts=json.loads((out/'sarimax/fit_attempts.json').read_text());groups=defaultdict(list)
        for r in attempts:
            assert pd.Timestamp(r['training_end'])==pd.Timestamp(f"{r['year']-1}-12-31")
            groups[r['state'],r['year'],r['configuration']].append(r)
        assert len(groups)==48 and all(v[-1]['converged'] for v in groups.values())
        deployments=json.loads((out/'sarimax/deployments.json').read_text())
        assert len(deployments)==len(tasks)*8
        assert all(pd.Timestamp(r['fitting_target_max'])<pd.Timestamp(r['origin']) and pd.Timestamp(r['context_max'])==pd.Timestamp(r['origin'])-pd.Timedelta(days=1) for r in deployments)
        checked['sarimax']=dict(converged_fits=48,attempts=len(attempts),unsuccessful_attempts_retained=sum(not r['converged'] for r in attempts))
        # Recalculate every native interval/pinball row, then the balanced hierarchy.
        qcells=defaultdict(list)
        for r in read(out/'native_uncertainty_cases.csv'):
            y=float(r['actual']);s=float(r['mase_scale']);qs=[float(r[f'q_{100*k:03d}']) for k in range(1,10)]
            lo,med,hi=qs[0],qs[4],qs[8]
            pb=mean(max(k/10*(y-q),(k/10-1)*(y-q)) for k,q in enumerate(qs,1))/s
            close(pb,r['scaled_mean_pinball'])
            invalid=lo>hi
            if not invalid:
                cover=float(lo<=y<=hi);width=(hi-lo)/s
                wis=(.5*abs(y-med)+.1*(hi-lo+10*max(lo-y,0)+10*max(y-hi,0)))/1.5/s
                for value,name in [(cover,'coverage80'),(width,'scaled_width80'),(wis,'scaled_WIS80_median')]:close(value,r[name])
            else:cover=width=wis=math.nan
            qcells[r['family'],r['model'],r['arm'],r['state'],r['year'],r['horizon']].append((pb,cover,width,wis))
        qyears,qfamilies,qmacro=defaultdict(list),defaultdict(list),defaultdict(list)
        for (f,m,a,s,y,h),v in qcells.items():qyears[f,m,a,y,h].append([mean(t[k] for t in v) for k in range(4)])
        for (f,m,a,y,h),v in qyears.items():qfamilies[f,m,a,h].append([mean(t[k] for t in v) for k in range(4)])
        for (f,m,a,h),v in qfamilies.items():qmacro[m,a,h].append([mean(t[k] for t in v) for k in range(4)])
        for r in read(out/'native_uncertainty_balanced.csv'):
            v=qmacro[r['model'],r['arm'],r['horizon']]
            for k,name in enumerate(['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                value=mean(t[k] for t in v)
                if math.isnan(value):assert not r[name]
                else:close(value,r[name])
        summaries[cohort]=dict(rows=len(raw),cases_per_arm=len(expected),workers=checked)
    pd.DataFrame(crossings,columns=['cohort','model','arm','state','date','horizon','lower','upper']).to_csv(OUT/'native_quantile_crossings.csv',index=False)
    result=dict(status='pass',scope='Internal separately implemented scalar/calendar/NumPy reconstruction; not external human review or full independent model rerun.',protected_prior_files=len(protected),cohorts=summaries,native_crossing_pairs=len(crossings))
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
