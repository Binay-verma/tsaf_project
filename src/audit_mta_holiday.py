"""Separate NYC source/calendar/selection-fit/input-byte and scalar-score audit."""
import argparse,base64,hashlib,itertools,json,math,re,subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRegressor
from audit_breadth_study import read,sha,digest,close,case
from audit_calendar_semantics import macro

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mta_holiday_v1'
FAMILIES=['Labor_Day','Yom_Kippur','Columbus_Day','Thanksgiving','Christmas']
SERIES={'Subway':'MTA_Subway','Bus':'MTA_Bus'}
ARMS=['calendar','zero5','day5','pooled_day5','window5','pooled_window5','placebo_day5','placebo_window5']


def main(part):
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if (dest/'independent_audit.json').exists():raise FileExistsError('Preserve prior audit')
    snapshot=json.loads((OUT/'snapshot.json').read_text());assert sha(OUT/'source_records.json')==snapshot['raw_sha256'] and sha(OUT/'source_snapshot_million_rides.csv')==snapshot['daily_sha256']
    records=json.loads((OUT/'source_records.json').read_text());assert len(records)==snapshot['source_rows']==2780 and len(records)<5000
    values={}
    for r in records:
        day=datetime.fromisoformat(r['date']);assert (day.hour,day.minute,day.second)==(0,0,0)
        assert r['mode'] in SERIES and datetime(2023,1,1)<=day<datetime(2026,10,22)
        key=pd.Timestamp(day.date()),SERIES[r['mode']];assert key not in values
        values[key]=float(r['count'])/1_000_000.;assert math.isfinite(values[key]) and values[key]>0
    source=pd.read_csv(OUT/'source_snapshot_million_rides.csv',index_col=0,parse_dates=True).asfreq('D');assert len(source)==1390 and source.notna().all().all()
    assert set(values)=={(day,state) for day in source.index for state in source}
    for state in source:
        for day,value in source[state].items():close(values[day,state],value)
    # Parse the selected names from the actual captured PDFs, not an application
    # date helper. Full annual amendment certification remains outside this audit.
    anchors=read(OUT/'anchors.csv');fake=read(OUT/'placebos.csv');verified={};sepoct=set()
    labels={'Labor_Day':'Labor Day','Yom_Kippur':'Yom Kippur','Columbus_Day':'Columbus Day','Thanksgiving':'Thanksgiving','Christmas':'Christmas'}
    for year in [2024,2025,2026]:
        pdf=OUT/f'evidence/nyc_dot_{year}_preyear.pdf';meta=json.loads((OUT/f'evidence/nyc_dot_{year}_preyear_retrieval.json').read_text())
        assert sha(pdf)==meta['pdf_sha256'] and base64.b32encode(hashlib.sha1(pdf.read_bytes()).digest()).decode()==meta['cdx_sha1'] and int(meta['archive_timestamp'][:4])<year
        text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True,stderr=subprocess.DEVNULL)
        for family,label in labels.items():
            lines=[line for line in text.splitlines() if label in line];assert len(lines)==1
            found=re.search(r'(Sept?|Oct|Nov|Dec)\s+(\d{1,2})',lines[0]);assert found,(family,year,lines)
            month={'Sep':9,'Sept':9,'Oct':10,'Nov':11,'Dec':12}[found[1]];verified[year,family]=f'{year}-{month:02d}-{int(found[2]):02d}'
        if year==2026:
            for match in re.finditer(r'(Sept?|Oct)\s+(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?',text):
                month=9 if match[1].startswith('Sep') else 10
                for day in range(int(match[2]),int(match[3] or match[2])+1):sepoct.add(pd.Timestamp(year,month,day))
    assert len(anchors)==15 and all(r['date']==verified[int(r['year']),r['family']] for r in anchors)
    assert len(sepoct)==9,sepoct
    rng=np.random.default_rng(42)
    for a,r in zip(anchors,fake):
        assert (a['year'],a['family'])==(r['year'],r['family']);root=pd.Timestamp(a['date']);year=int(a['year']);roots=[pd.Timestamp(t['date']) for t in anchors if int(t['year'])==year]
        choices=[]
        for shift in [-42,-35,-28,28,35,42]:
            day=root+pd.Timedelta(days=shift)
            if (day-pd.Timedelta(days=3)).year==year==(day+pd.Timedelta(days=3)).year and all(abs((day-d).days)>6 for d in roots):choices.append(shift)
        expected=int(rng.choice(choices));assert expected==int(r['shift_days']) and r['original_date']==a['date'] and pd.Timestamp(r['date'])==root+pd.Timedelta(days=expected)
    blocked={day for root in sepoct for day in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))};ordinary_dates=[]
    for weekday in range(7):ordinary_dates.append(next(d for d in pd.date_range('2026-09-15','2026-10-28') if d.weekday()==weekday and d not in blocked))
    expected_cases={}
    for cohort in ['event_window','ordinary']:
        targets=[(f,d) for f in ['Yom_Kippur','Columbus_Day'] for d in pd.date_range(pd.Timestamp(verified[2026,f])-pd.Timedelta(days=3),periods=7)] if cohort=='event_window' else [('Ordinary',d) for d in ordinary_dates]
        rows=[]
        for f,d in targets:
            for state in SERIES.values():
                for lead in [1,7,14]:
                    origin=d-pd.Timedelta(days=lead+6);rows.append((f,state,'2026',str(origin.date()),str(d.date()),str(lead+7)))
        expected_cases[cohort]=set(rows);assert {case(r) for r in read(OUT/cohort/'primary_cases.csv')}==set(rows)
    def extras(index,arm):
        if arm in ['calendar','history']:return np.empty((0,len(index)))
        if arm=='zero5':return np.zeros((5,len(index)))
        ledger=fake if arm.startswith('placebo') else anchors;flags=[]
        for family in FAMILIES:
            roots=[pd.Timestamp(r['date']) for r in ledger if r['family']==family]
            active=set(roots) if 'window' not in arm else {d for root in roots for d in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))}
            flags.append(index.isin(active).astype(float))
        if arm.startswith('pooled'):flags=[np.asarray(flags).any(axis=0).astype(float)]+[np.zeros(len(index)) for _ in range(4)]
        return np.asarray(flags)
    def covariance(index,arm):
        if arm=='history':return np.empty((0,len(index)))
        base=[(index.dayofweek==j).astype(float) for j in range(7)]
        for j in [1,2,3]:base.extend([np.sin(2*np.pi*j*index.dayofyear/365.2425),np.cos(2*np.pi*j*index.dayofyear/365.2425)])
        return np.asarray(base+list(extras(index,arm)))
    def design(state,h,arm):
        observed=source[state];x=pd.DataFrame({f'lag_{k}':observed.shift(k) for k in [1,2,3,7,14,21,28,56,364,365,366]})
        for w in [7,28,56]:
            roll=observed.shift(1).rolling(w)
            for name in ['mean','std','min','max']:x[f'{name}_{w}']=getattr(roll,name)()
        x['trend_7_28']=x.mean_7-x.mean_28
        for lag in [364,365,366]:x[f'target_annual_{lag}']=observed.shift(lag-h+1)
        return pd.concat([x,pd.DataFrame(covariance(source.index+pd.Timedelta(days=h-1),arm).T,index=source.index)],axis=1)
    def fitting(x,state,h,cutoff):
        origins=pd.date_range(cutoff-pd.Timedelta(days=729),cutoff-pd.Timedelta(days=h-1));dates=origins+pd.Timedelta(days=h-1);xx=x.reindex(origins).to_numpy();yy=source[state].reindex(dates).to_numpy();valid=np.isfinite(xx).all(axis=1)&np.isfinite(yy)
        assert dates[valid].max()<=cutoff;return xx[valid],yy[valid],origins[valid],dates[valid]
    selection=json.loads((OUT/'selection.json').read_text());assert selection['snapshot_sha256']==sha(OUT/'snapshot.json') and len(selection['attempts'])==72
    fixed=json.loads((OUT/'event_window/protocol.json').read_text())['lightgbm_fixed'];trials=defaultdict(list);selection_cache={};max_val_difference=0.
    for r in selection['attempts']:
        state,model,h=r['state'],r['model'],r['horizon'];key=(state,model,h)
        if key not in selection_cache:
            x=design(state,h,'calendar');x=x.astype(np.float32) if model=='lightgbm' else x;xx,yy,origins,dates=fitting(x,state,h,pd.Timestamp('2025-12-31'))
            vo=pd.date_range('2026-01-01',pd.Timestamp('2026-06-30')-pd.Timedelta(days=h-1));vd=vo+pd.Timedelta(days=h-1);vx=x.reindex(vo).to_numpy();vy=source[state].reindex(vd).to_numpy();good=np.isfinite(vx).all(axis=1)&np.isfinite(vy);selection_cache[key]=(xx,yy,origins,dates,vx[good],vy[good],vd[good])
        xx,yy,origins,dates,vx,vy,vd=selection_cache[key]
        assert digest(xx)==r['training_X_sha256'] and digest(yy)==r['training_y_sha256'] and len(yy)==r['training_n'] and r['training_target_max']==str(dates.max().date()) and r['training_origin_max']==str(origins.max().date())
        assert r['validation_n']==182-h==len(vy) and r['validation_target_max']==str(vd.max().date())=='2026-06-30'
        fitted=(make_pipeline(StandardScaler(),Ridge(**r['parameters'])) if model=='ridge' else LGBMRegressor(**r['parameters'],**fixed)).fit(xx,yy)
        value=float(np.mean(abs(fitted.predict(vx)-vy)));close(value,r['validation_MAE_million_rides']);max_val_difference=max(max_val_difference,abs(value-r['validation_MAE_million_rides']));trials[key].append(r)
    assert len(trials)==12
    for (state,model,h),rows in trials.items():
        assert len(rows)==(4 if model=='ridge' else 8);winner=min(rows,key=lambda r:(r['validation_MAE_million_rides'],r['configuration']));assert selection['parameters'][f'{state}:{model}:{h}']==winner['parameters']
    scales={}
    for state in source:
        ys=source.loc['2024-01-02':'2025-12-31',state].to_dict();scales[state]=mean(abs(v-ys[d-pd.Timedelta(days=7)]) for d,v in ys.items() if d-pd.Timedelta(days=7) in ys)
    registration=json.loads((OUT/'registration.json').read_text());analysis=json.loads((OUT/'analysis_registration.json').read_text());assert sha(ROOT/'src/finalize_mta_holiday.py')==analysis['source_sha256']
    summaries={};fitchecks=inputchecks=0;weights_checked=set()
    for cohort,ph in registration['protocols'].items():
        out=OUT/cohort;p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==ph
        for name,h in p['input_hashes'].items():assert sha(ROOT/name)==h,name
        for name,h in p['design_hashes'].items():assert sha(out/name)==h,name
        cases=read(out/'primary_cases.csv');expected=expected_cases[cohort];tasks={(r['state'],r['origin']) for r in cases};models=p['models'][:4] if part=='local' else p['models'];nativecross=0
        for model in models:
            worker=json.loads((out/model/'run.json').read_text());assert worker['protocol_sha256']==ph and worker['predictions_sha256']==sha(out/model/'predictions.csv')
            if model in ['ridge','lightgbm','lightgbm_capacity2']:
                for r in json.loads((out/model/'fit_log.json').read_text()):
                    state,h=r['state'],r['horizon'];x=design(state,h,r['arm']);x=x.astype(np.float32) if model!='ridge' else x;cutoff=pd.Timestamp(r['refit'])-pd.Timedelta(days=1);xx,yy,origins,dates=fitting(x,state,h,cutoff)
                    group=[c for c in cases if c['state']==state and int(c['horizon'])==h and c['origin'][:7]==r['refit'][:7]];query=x.reindex(pd.DatetimeIndex([c['origin'] for c in group])).to_numpy()
                    assert digest(xx)==r['training_X_sha256'] and digest(yy)==r['training_y_sha256'] and digest(query)==r['query_X_sha256'] and r['extra_nonzero_counts']==np.count_nonzero(xx[:,40:],axis=0).tolist()
                    assert dates.max()<=cutoff<min(pd.Timestamp(c['origin']) for c in group) and len(yy)==r['training_n'] and r['feature_count']==xx.shape[1]
                    params=selection['parameters'][f'{state}:{"ridge" if model=="ridge" else "lightgbm"}:{h}'].copy()
                    if model=='lightgbm_capacity2':params['min_child_samples']=2
                    assert params==r['parameters'];fitchecks+=1
            elif model=='sarimax':
                logs=json.loads((out/model/'fit_attempts.json').read_text());fits=defaultdict(list)
                for r in logs:fits[r['state'],r['configuration'],r['refit']].append(r);assert pd.Timestamp(r['training_end'])<pd.Timestamp(r['refit'])
                assert set(fits)=={(state,arm,origin[:7]+'-01') for state,origin in tasks for arm in ARMS}
                for rows in fits.values():assert rows[-1]['converged'] and all(not r['converged'] for r in rows[:-1])
                deployed=json.loads((out/model/'deployments.json').read_text());assert len(deployed)==len(tasks)*8
                for r in deployed:assert pd.Timestamp(r['training_end'])<pd.Timestamp(r['origin']) and pd.Timestamp(r['context_end'])==pd.Timestamp(r['origin'])-pd.Timedelta(days=1)
            else:
                file=ROOT/('results/mechanism_controls_v1/chronos_download.json' if model=='chronos' else 'results/second_model_audit_v1/weight_download.json');identity=json.loads(file.read_text());weight=next(f for f in identity['files'] if f['name']=='model.safetensors') if model=='chronos' else identity
                assert worker['weight_sha256']==weight['sha256']
                if model not in weights_checked:assert sha(Path(weight['path']))==weight['sha256'];weights_checked.add(model)
                seen=defaultdict(set)
                for r in json.loads((out/model/'inputs.json').read_text()):
                    origin=pd.Timestamp(r['origin']);dates=pd.date_range(origin-pd.Timedelta(days=730),periods=751);target=source[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32);cov=covariance(dates,r['arm']).astype(np.float32)
                    assert digest(target)==r['target_sha256'] and digest(cov)==r['covariate_sha256'] and r['feature_count']==len(cov) and r['past_nonzero_counts']==np.count_nonzero(cov[13:,:730],axis=1).tolist() and r['future_target_perturbation_invariant']
                    assert r['context_start']==str(dates.min().date()) and r['context_end']==str((origin-pd.Timedelta(days=1)).date());task=(r['state'],r['origin']);assert task in tasks and task not in seen[r['arm']];seen[r['arm']].add(task);inputchecks+=1
                assert set(seen)==set(['history']+ARMS) and all(s==tasks for s in seen.values())
                solo=json.loads((out/model/'solo_batch_audit.json').read_text());assert len(solo)==min(16,len(tasks))*9
                d=pd.read_csv(out/model/'predictions.csv');q=d[sorted(c for c in d if c.startswith('q_'))].to_numpy();count=int((np.diff(q,axis=1)<0).sum());assert count==worker['native_quantile_crossings'];nativecross+=count
        result=dest/cohort;rows=read(result/'predictions_compared.csv');seen=defaultdict(set);point=[];absolute=[];bycell=defaultdict(list)
        for r in rows:
            c=case(r);assert c in expected and c not in seen[r['model'],r['arm']];seen[r['model'],r['arm']].add(c)
            assert int(r['horizon'])==int(r['decision_lead'])+7 and (pd.Timestamp(r['decision_origin'])-pd.Timestamp(r['origin'])).days==7 and pd.Timestamp(r['decision_origin'])>pd.Timestamp('2026-08-31')
            y=float(source.loc[pd.Timestamp(r['date']),r['state']]);s=scales[r['state']];close(y,r['actual']);close(s,r['mase_scale']);error=abs(y-float(r['prediction']));close(error,r['MAE_million_rides']);close(error/s,r['MASE'])
            r['version']='MTA';point.append((r,error/s));absolute.append((r,error));bycell[tuple(r[k] for k in ['family','state','year','model','arm','horizon'])].append(error/s)
            if r['model'] in ['last','seasonal']:
                origin=pd.Timestamp(r['origin']);day=origin-pd.Timedelta(days=1 if r['model']=='last' else 7)
                if r['model']=='seasonal':day+=pd.Timedelta(days=(int(r['horizon'])-1)%7)
                assert day<origin;close(source.loc[day,r['state']],r['prediction'])
        configs={(m,arm) for m in models for arm in (['history']+ARMS if m in ['chronos','timesfm'] else ARMS)}|{(m,'history') for m in ['last','seasonal']}
        assert set(seen)==configs and all(c==expected for c in seen.values());pm=macro(point,'MASE');am=macro(absolute,'MAE_million_rides')
        for r in read(result/'metrics_balanced.csv'):
            k=('MTA',r['model'],r['arm'],r['horizon']);close(pm[k],r['MASE']);close(am[k],r['MAE_million_rides']);assert int(r['decision_lead'])==int(r['horizon'])-7 and 'MAE_GWh' not in r
        pairyears=defaultdict(list);pairfamilies=defaultdict(list);pairmacro=defaultdict(list)
        for r in read(result/'contrasts_series_year.csv'):
            key=tuple(r[k] for k in ['family','state','year','model']);h=r['horizon'];value=mean(bycell[key+(r['arm'],h)])-mean(bycell[key+(r['reference'],h)]);close(value,r['MASE_change']);pairyears[r['family'],r['model'],r['arm'],r['reference'],r['year'],h].append(value)
        for k,v in pairyears.items():pairfamilies[k[:4]+(k[-1],)].append(mean(v))
        for k,v in pairfamilies.items():pairmacro[k[1:]].append(mean(v))
        for r in read(result/'contrasts_balanced.csv'):close(mean(pairmacro[tuple(r[k] for k in ['model','arm','reference','horizon'])]),r['MASE_change'])
        if cohort=='event_window':
            for r in read(result/'leave_family_out.csv'):
                key=tuple(r[k] for k in ['model','arm','reference','horizon']);close(mean(mean(v) for k,v in pairfamilies.items() if k[0]!=r['omitted_family'] and k[1:]==key),r['MASE_change'])
        qfields=defaultdict(list);invalidgroups=set()
        if (result/'native_uncertainty_cases.csv').exists():
            for r in read(result/'native_uncertainty_cases.csv'):
                y=float(r['actual']);s=float(r['mase_scale']);q=[float(r[f'q_{100*k:03d}']) for k in range(1,10)];lo,med,hi=q[0],q[4],q[8];pin=mean(max(k/10*(y-v),(k/10-1)*(y-v)) for k,v in enumerate(q,1))/s
                cov=float(lo<=y<=hi);width=(hi-lo)/s;wis=(.5*abs(y-med)+.1*(hi-lo+10*max(lo-y,0)+10*max(y-hi,0)))/1.5/s
                if lo>hi:cov=width=wis=math.nan;invalidgroups.add(('MTA',r['model'],r['arm'],r['horizon']))
                r['version']='MTA'
                for value,field in zip([pin,cov,width,wis],['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                    if math.isnan(value):assert not r[field]
                    else:close(value,r[field])
                    qfields[field].append((r,value))
            qm={field:macro(values,field) for field,values in qfields.items()}
            for r in read(result/'native_uncertainty_balanced.csv'):
                key=('MTA',r['model'],r['arm'],r['horizon'])
                for field,table in qm.items():
                    if key in invalidgroups and field!='scaled_mean_pinball':assert not r[field]
                    else:close(table[key],r[field])
        summaries[cohort]=dict(compared_rows=len(rows),cases_per_arm=len(expected),native_all_grid_crossing_pairs=nativecross)
    result=dict(status='pass',scope='Internal separate rawcountconversion/preyearPDFdate/digest/weekdayplacebo/case/actualfeaturebyte/labelpurge/parameter/scalarpoint/probability/composition audit. All72past-onlyselectionfits rerun with separately constructed matrices and same numerical model libraries. Not independenthuman or independent modelimplementation; complete source means no realmissinglabel imputation case exercised.',source_days=1390,source_records=2780,verified_calendar_anchors=15,reproduced_selection_fits=72,max_validation_MAE_difference_million_rides=max_val_difference,local_fit_bytechecks=fitchecks,foundation_input_bytechecks=inputchecks,cohorts=summaries)
    (dest/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--part',choices=['local','all'],default='all');main(p.parse_args().part)
