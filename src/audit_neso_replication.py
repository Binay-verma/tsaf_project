"""Separate source integration, date/feature bytes, selection and scalar scores.
No experiment/forecast/aggregate helpers imported. This is an internal audit,
not independent human review or an independent reimplementation of the models.
"""
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from audit_breadth_study import read,sha,digest,close,case

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/neso_replication_v1'
FAMILIES=['New_Year','Easter','Early_May','Spring','Summer','Christmas']
ARMS=['calendar','zero6','day6','pooled_day6','window6','pooled_window6','placebo_day6','placebo_window6']


def main(part):
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if (dest/'independent_audit.json').exists():raise FileExistsError('Preserve prior audit')
    registration=json.loads((OUT/'registration.json').read_text());snapshot=json.loads((OUT/'snapshot.json').read_text());cache=Path(snapshot['raw_cache'])
    a=json.loads((OUT/'analysis_registration.json').read_text());assert sha(ROOT/'src/finalize_neso_replication.py')==a['source_sha256']
    assert sha(OUT/'registration.json')==a['registration_sha256']
    assert sha(cache/'daily_energy_GWh.csv')==snapshot['daily_sha256']
    # Integrate raw source independently. Explicit timezone durations handle DST.
    raw_daily={};quality={};z=ZoneInfo('Europe/London')
    for year,entry in snapshot['downloads'].items():
        path=cache/(year+'.csv');assert sha(path)==entry['sha256']
        raw=read(path);byday=defaultdict(list);excluded=0
        for r in raw:
            if 'FORECAST_ACTUAL_INDICATOR' in r and r['FORECAST_ACTUAL_INDICATOR'].strip().upper()!='A':excluded+=1;continue
            text=r['SETTLEMENT_DATE'].strip()
            day=None
            for fmt in ['%Y-%m-%d','%d/%m/%Y','%d-%b-%Y','%d-%b-%y']:
                try:day=datetime.strptime(text,fmt).date();break
                except ValueError:continue
            if day is None:raise ValueError(('Unrecognised source date',text))
            if day.year!=int(year) or day>datetime(2026,9,30).date():continue
            byday[day].append(r)
        counts=defaultdict(int)
        for day,rows in byday.items():
            start=datetime.combine(day,datetime.min.time(),z);end=datetime.combine(day+timedelta(days=1),datetime.min.time(),z)
            n=int((end.astimezone(timezone.utc)-start.astimezone(timezone.utc)).total_seconds()/1800)
            values=[float(r['ENGLAND_WALES_DEMAND']) for r in rows];periods=[int(r['SETTLEMENT_PERIOD']) for r in rows]
            valid=len(rows)==n and sorted(periods)==list(range(1,n+1)) and all(math.isfinite(v) and v>0 for v in values)
            raw_daily[pd.Timestamp(day)]=sum(values)*.0005 if valid else math.nan;counts[str(n)]+=1
        quality[year]=dict(days=len(byday),period_counts=dict(counts),nonactual_rows_excluded=excluded)
    source=pd.read_csv(cache/'daily_energy_GWh.csv',index_col=0,parse_dates=True).iloc[:,0].asfreq('D')
    assert set(source.index)==set(raw_daily)
    for day,value in source.items():
        if math.isnan(raw_daily[day]):assert math.isnan(value)
        else:close(raw_daily[day],value)
    assert source.index.max()==pd.Timestamp('2026-09-30') and source.gt(0).all()
    # No missing labels in this snapshot. Thus byte checks use exact recorded
    # values, and do not claim to independently certify causal imputation here.
    true=read(OUT/'anchors.csv');fake=read(OUT/'placebos.csv')
    for r in fake:
        shift=(pd.Timestamp(r['date'])-pd.Timestamp(r['original_date'])).days
        assert shift==int(r['shift_days']) and shift in [-42,-35,-28,28,35,42]
        assert all(abs((pd.Timestamp(r['date'])-pd.Timestamp(t['date'])).days)>3 for t in true)
    def covariates(index,arm):
        base=[(index.dayofweek==j).astype(float) for j in range(7)]
        for j in [1,2,3]:base.extend([np.sin(2*np.pi*j*index.dayofyear/365.2425),np.cos(2*np.pi*j*index.dayofyear/365.2425)])
        extra=[]
        if arm!='calendar':
            if arm=='zero6':extra=[np.zeros(len(index)) for _ in FAMILIES]
            else:
                ledger=fake if arm.startswith('placebo') else true
                for family in FAMILIES:
                    roots=[pd.Timestamp(r['date']) for r in ledger if r['family']==family]
                    dates=set(roots) if 'window' not in arm else {d for root in roots for d in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))}
                    extra.append(np.array([int(d in dates) for d in index],dtype=float))
                if arm.startswith('pooled'):extra=[np.asarray(extra).any(axis=0).astype(float)]+[np.zeros(len(index)) for _ in range(5)]
        return np.asarray(base+extra)
    def design(h,arm):
        x=pd.DataFrame({f'lag_{k}':source.shift(k) for k in [1,2,3,7,14,21,28,56,364,365,366]})
        for w in [7,28,56]:
            roll=source.shift(1).rolling(w)
            for name in ['mean','std','min','max']:x[f'{name}_{w}']=getattr(roll,name)()
        x['trend_7_28']=x.mean_7-x.mean_28
        for lag in [364,365,366]:x[f'target_annual_{lag}']=source.shift(lag-h+1)
        cc=covariates(source.index+pd.Timedelta(days=h-1),arm).T
        return pd.concat([x,pd.DataFrame(cc,index=source.index)],axis=1)
    def fitting(x,h,cutoff):
        origins=pd.date_range(cutoff-pd.Timedelta(days=729),cutoff-pd.Timedelta(days=h-1));dates=origins+pd.Timedelta(days=h-1)
        xx=x.reindex(origins).to_numpy();yy=source.reindex(dates).to_numpy();valid=np.isfinite(xx).all(axis=1)&np.isfinite(yy)
        assert dates[valid].max()<=cutoff
        return xx[valid],yy[valid],origins[valid],dates[valid]
    selection=json.loads((OUT/'selection.json').read_text());assert selection['snapshot_sha256']==sha(OUT/'snapshot.json')
    trials=defaultdict(list);dcache={}
    for r in selection['attempts']:
        model,h=r['model'],r['horizon'];k=(model,h)
        if k not in dcache:
            x=design(h,'calendar');x=x.astype(np.float32) if model=='lightgbm' else x
            xx,yy,origins,dates=fitting(x,h,pd.Timestamp('2025-12-31'));dcache[k]=(xx,yy,origins,dates)
        xx,yy,origins,dates=dcache[k]
        assert digest(xx)==r['training_X_sha256'] and digest(yy)==r['training_y_sha256']
        assert r['training_n']==len(yy) and r['training_target_max']==str(dates.max().date()) and r['training_origin_max']==str(origins.max().date())
        assert pd.Timestamp(r['validation_target_max'])<=pd.Timestamp('2026-06-30')<pd.Timestamp('2026-08-11')
        assert r['validation_n']==181-(h-1)
        trials[k].append(r)
    assert len(selection['attempts'])==72 and len(trials)==12
    for (model,h),rows in trials.items():
        assert len(rows)==(4 if model=='ridge' else 8)
        best=min(rows,key=lambda r:(r['validation_MAE_GWh'],r['configuration']))
        assert selection['parameters'][f'{model}:{h}']==best['parameters']
    scale_values=source.loc[pd.Timestamp('2025-12-31')-pd.Timedelta(days=729):'2025-12-31'].to_dict()
    scale=mean(abs(v-scale_values[d-pd.Timedelta(days=7)]) for d,v in scale_values.items() if d-pd.Timedelta(days=7) in scale_values)
    run=json.loads((dest/'run.json').read_text());models=run['models'];summaries={}
    for scenario,ph in registration['protocols'].items():
        out=OUT/scenario;p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==ph
        for name,hsh in p['input_hashes'].items():assert sha(ROOT/name)==hsh,name
        for name,hsh in p['design_hashes'].items():assert sha(out/name)==hsh,name
        cases=read(out/'primary_cases.csv');expected={case(r) for r in cases};lag=0 if scenario=='ideal' else 21
        tasks={(r['state'],r['origin']) for r in cases};assert len(cases)==48 and len(tasks)==29
        for r in cases:
            assert int(r['horizon'])==int(r['decision_lead'])+lag
            assert (pd.Timestamp(r['date'])-pd.Timestamp(r['origin'])).days==int(r['horizon'])-1
            assert (pd.Timestamp(r['decision_origin'])-pd.Timestamp(r['origin'])).days==lag
        fits_checked=inputs_checked=0;attempts=0
        for model in models:
            worker=json.loads((out/model/'run.json').read_text());assert worker['protocol_sha256']==ph and worker['predictions_sha256']==sha(out/model/'predictions.csv')
            if model in ['ridge','lightgbm','lightgbm_capacity2']:
                for r in json.loads((out/model/'fit_log.json').read_text()):
                    h,arm=r['horizon'],r['arm'];cutoff=pd.Timestamp(r['refit'])-pd.Timedelta(days=1)
                    x=design(h,arm);x=x.astype(np.float32) if model!='ridge' else x
                    xx,yy,origins,dates=fitting(x,h,cutoff)
                    query_cases=[c for c in cases if int(c['horizon'])==h and c['origin'][:7]==r['refit'][:7]]
                    query=x.reindex(pd.DatetimeIndex([c['origin'] for c in query_cases])).to_numpy()
                    assert digest(xx)==r['training_X_sha256'] and digest(yy)==r['training_y_sha256'] and digest(query)==r['query_X_sha256']
                    assert r['training_n']==len(yy) and r['training_target_max']==str(dates.max().date()) and r['training_origin_max']==str(origins.max().date())
                    assert r['feature_count']==xx.shape[1] and cutoff<min(pd.Timestamp(c['origin']) for c in query_cases)
                    params=selection['parameters'][f'{"ridge" if model=="ridge" else "lightgbm"}:{h}'].copy()
                    if model=='lightgbm_capacity2':params['min_child_samples']=2
                    assert r['parameters']==params;fits_checked+=1
            elif model=='sarimax':
                logs=json.loads((out/model/'fit_attempts.json').read_text());attempts+=len(logs)
                groups=defaultdict(list)
                for r in logs:groups[r['configuration'],r['refit']].append(r);assert pd.Timestamp(r['training_end'])<pd.Timestamp(r['refit'])
                assert set(groups)=={(arm,origin[:7]+'-01') for arm in ARMS for _,origin in tasks}
                for rows in groups.values():assert rows[-1]['converged'] and all(not r['converged'] for r in rows[:-1])
                deployed=json.loads((out/model/'deployments.json').read_text());assert len(deployed)==len(tasks)*8
                for r in deployed:assert pd.Timestamp(r['training_end'])<pd.Timestamp(r['origin']) and pd.Timestamp(r['context_end'])==pd.Timestamp(r['origin'])-pd.Timedelta(days=1)
            else:
                identity=ROOT/('results/mechanism_controls_v1/chronos_download.json' if model=='chronos' else 'results/second_model_audit_v1/weight_download.json')
                info=json.loads(identity.read_text());weight=next(f for f in info['files'] if f['name']=='model.safetensors') if model=='chronos' else info
                assert worker['weight_sha256']==weight['sha256'] and sha(Path(weight['path']))==weight['sha256']
                seen=defaultdict(set)
                for r in json.loads((out/model/'inputs.json').read_text()):
                    origin=pd.Timestamp(r['origin']);dates=pd.date_range(origin-pd.Timedelta(days=730),periods=730+p['horizon'])
                    target=source.reindex(dates[:730]).to_numpy(dtype=np.float32);cov=covariates(dates,r['arm']).astype(np.float32)
                    assert digest(target)==r['target_sha256'] and digest(cov)==r['covariate_sha256']
                    assert r['feature_count']==len(cov) and r['past_nonzero_counts']==np.count_nonzero(cov[13:,:730],axis=1).tolist()
                    assert r['future_target_perturbation_invariant'] and r['context_end']==str((origin-pd.Timedelta(days=1)).date())
                    assert r['context_start']==str(dates.min().date())
                    task=(r['state'],r['origin']);assert task in tasks and task not in seen[r['arm']];seen[r['arm']].add(task);inputs_checked+=1
                assert set(seen)==set(ARMS) and all(s==tasks for s in seen.values())
                solo=json.loads((out/model/'solo_batch_audit.json').read_text());assert len(solo)==128 and all(math.isfinite(r['max_abs_difference']) for r in solo)
                table=pd.read_csv(out/model/'predictions.csv');q=table[sorted(c for c in table if c.startswith('q_'))].to_numpy()
                assert int((np.diff(q,axis=1)<0).sum())==worker['native_quantile_crossings']
        summaries[scenario]=dict(fit_input_bytechecks=fits_checked,foundation_input_bytechecks=inputs_checked,sarimax_attempts=attempts,cases_per_arm=48)
    rows=read(dest/'predictions_compared.csv');sets=defaultdict(set);metrics=defaultdict(list);points={}
    for r in rows:
        c=case(r);assert c in {case(x) for x in read(OUT/r['scenario']/'primary_cases.csv')}
        key=(r['scenario'],r['model'],r['arm']);assert c not in sets[key];sets[key].add(c)
        actual=float(source.loc[pd.Timestamp(r['date'])]);close(actual,r['actual']);close(scale,r['mase_scale'])
        assert math.isfinite(float(r['prediction']))
        error=abs(actual-float(r['prediction']));close(error,r['MAE_GWh']);close(error/scale,r['MASE'])
        group=key+(r['decision_lead'],r['horizon']);metrics[group].append((error,error/scale));points[key+(c,)]=error/scale
        if r['model'] in ['last','seasonal']:
            origin=pd.Timestamp(r['origin']);day=origin-pd.Timedelta(days=1 if r['model']=='last' else 7)
            if r['model']=='seasonal':day+=pd.Timedelta(days=(int(r['horizon'])-1)%7)
            assert day<origin;close(source.loc[day],r['prediction'])
    expectedgroups={(s,m,arm) for s in ['ideal','lag21'] for m in models for arm in ARMS}|{(s,m,'history') for s in ['ideal','lag21'] for m in ['last','seasonal']}
    assert set(sets)==expectedgroups and all(len(s)==48 for s in sets.values())
    for r in read(dest/'metrics.csv'):
        group=tuple(r[k] for k in ['scenario','model','arm','decision_lead','horizon']);values=metrics[group]
        assert len(values)==int(r['n'])==16;close(mean(v[0] for v in values),r['MAE_GWh']);close(mean(v[1] for v in values),r['MASE'])
    pairs=defaultdict(list)
    for r in read(dest/'contrasts_cases.csv'):
        # Contrast file keeps date but no origin; within each fixed lead date is unique.
        group=tuple(r[k] for k in ['scenario','model','arm','decision_lead','horizon'])
        vals=[x for x in rows if x['scenario']==r['scenario'] and x['model']==r['model'] and x['arm'] in [r['arm'],'calendar'] and x['date']==r['date'] and x['horizon']==r['horizon']]
        assert len(vals)==2;v={x['arm']:float(x['MASE']) for x in vals};change=v[r['arm']]-v['calendar'];close(change,r['MASE_change']);pairs[group].append(change)
    for r in read(dest/'contrasts.csv'):close(mean(pairs[tuple(r[k] for k in ['scenario','model','arm','decision_lead','horizon'])]),r['MASE_change'])
    qmetrics=defaultdict(list);crossings=0
    if (dest/'native_uncertainty_cases.csv').exists():
        for r in read(dest/'native_uncertainty_cases.csv'):
            q=[float(r[f'q_{100*k:03d}']) for k in range(1,10)];actual=float(r['actual']);lo,med,hi=q[0],q[4],q[8]
            assert all(math.isfinite(v) for v in q);crossings+=sum(a>b for a,b in zip(q,q[1:]))
            pin=mean(max(k/10*(actual-v),(k/10-1)*(actual-v)) for k,v in enumerate(q,1))/scale
            if lo>hi:coverage=width=wis=math.nan
            else:
                coverage=float(lo<=actual<=hi);width=(hi-lo)/scale
                wis=(.5*abs(actual-med)+.1*(hi-lo+10*max(lo-actual,0)+10*max(actual-hi,0)))/1.5/scale
            for value,field in zip([pin,coverage,width,wis],['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                if math.isnan(value):assert not r[field]
                else:close(value,r[field])
            qmetrics[tuple(r[k] for k in ['scenario','model','arm','decision_lead','horizon'])].append((pin,coverage,width,wis))
        for r in read(dest/'native_uncertainty_metrics.csv'):
            values=qmetrics[tuple(r[k] for k in ['scenario','model','arm','decision_lead','horizon'])]
            for j,field in enumerate(['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                value=mean(v[j] for v in values)
                if math.isnan(value):assert not r[field]
                else:close(value,r[field])
    result=dict(status='pass',scope='Internal separate rawintegration/DST/actualflag/source/date/featurebyte/selectioncutoff/parameter/label/scale/point/nativeinterval audit. Same source and libraries, not independent human/fullmodelforecast reproduction. No missingdailylabels in snapshot, so no real missinglabel imputation certification.',
        compared_rows=len(rows),source_days=len(source),source_quality=quality,selection_fits=72,scenarios=summaries,common_crossing_pairs=crossings,predictions_sha256=sha(dest/'predictions_compared.csv'))
    (dest/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--part',choices=['local','all'],default='all');main(p.parse_args().part)
