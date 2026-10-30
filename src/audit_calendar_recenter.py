"""Separate source-defined cohort/control, actual inputs and scalar metric audit."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd
from audit_breadth_study import read,sha,digest,close,case
from audit_calendar_semantics import macro

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/calendar_recenter_v1'
SEM=ROOT/'results/calendar_semantics_v2'
FAMILIES=['Holi','Dussehra','Ganesh_Chaturthi','Ugadi_Gudi_Padwa','Diwali']


def main(part):
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if (dest/'independent_audit.json').exists():raise FileExistsError('Preserve prior audit')
    run=json.loads((dest/'run.json').read_text());reg=json.loads((OUT/'registration.json').read_text());scoring=json.loads((OUT/'analysis_registration.json').read_text())
    for name,h in scoring['source_hashes'].items():assert sha(ROOT/name)==h
    assert sha(OUT/'registration.json')==scoring['registration_sha256']
    semaudit=SEM/('local_checkpoint_recovery_v1' if part=='local' else 'analysis')/'independent_audit.json';assert json.loads(semaudit.read_text())['status']=='pass'
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D').where(lambda x:x>0)
    ledgers={'original':read(ROOT/'results/festival_features_v1/anchors_2022_2025.csv'),'aligned':read(SEM/'anchors_2022_2025.csv')}
    fakes={'original':read(ROOT/'results/festival_features_v1/placebo_anchors.csv'),'aligned':read(OUT/'placebo_anchors.csv')}
    changed=[(a,b) for a,b in zip(fakes['original'],fakes['aligned']) if a!=b];assert len(changed)==1
    a,b=changed[0];assert a['date']=='2025-11-06' and b['date']=='2025-11-05' and b['original_date']=='2025-10-01' and b['shift_days']=='35'
    for r in fakes['aligned']:
        assert (pd.Timestamp(r['date'])-pd.Timestamp(r['original_date'])).days==int(r['shift_days']) and int(r['shift_days'])%7==0
        true=[pd.Timestamp(x['date']) for x in ledgers['aligned'] if x['state']==r['state'] and x['year']==r['year']]
        assert all(abs((pd.Timestamp(r['date'])-d).days)>6 for d in true)
    placebo_reuse_proofs=0
    for cohort in ['event_window','ordinary']:
        cases_for_reuse=read(OUT/'event_cases_recentered.csv') if cohort=='event_window' else read(ROOT/'results/feature_breadth_v1/ordinary/primary_cases.csv')
        for r in cases_for_reuse:
            if r['state']=='Karnataka' and r['year']=='2025' and r['date']>='2025-09-01':continue
            if r['state']=='Karnataka':
                # Only these day/window positions change in the placebo ledger.
                end=pd.Timestamp(r['origin'])+pd.Timedelta(days=13)
                start=min(pd.Timestamp(r['origin'])-pd.Timedelta(days=730),pd.Timestamp(f'{int(r["year"])-1}-12-31')-pd.Timedelta(days=729))
                assert all(not start<=pd.Timestamp(d)<=end for d in ['2025-11-02','2025-11-05','2025-11-06','2025-11-09'])
            placebo_reuse_proofs+=1
    assert placebo_reuse_proofs==684
    original_cases=read(ROOT/'results/feature_breadth_v1/event_window/primary_cases.csv');recentered=read(OUT/'event_cases_recentered.csv');oldset={case(r) for r in original_cases};newset={case(r) for r in recentered}
    assert len(newset)==len(oldset)==528 and len(oldset-newset)==len(newset-oldset)==3
    for c in oldset-newset:assert c[0:3]==('Dussehra','Karnataka','2025') and c[4]=='2025-10-05'
    for c in newset-oldset:assert c[0:3]==('Dussehra','Karnataka','2025') and c[4]=='2025-09-28'
    dates={r['date'] for r in recentered if r['state']=='Karnataka' and r['year']=='2025' and r['family']=='Dussehra'}
    assert dates=={str(d.date()) for d in pd.date_range('2025-09-28','2025-10-04')}
    filled={};scales={}
    for state in source:
        y=source[state].to_numpy(dtype=float,copy=True)
        for i in range(len(y)):
            if not np.isfinite(y[i]):y[i]=y[i-7] if i>=7 and np.isfinite(y[i-7]) else y[i-1] if i else np.nan
        filled[state]=pd.Series(y,index=source.index)
        for year in [2024,2025]:
            end=pd.Timestamp(f'{year-1}-12-31');ys=source.loc[end-pd.Timedelta(days=729):end,state].to_dict()
            scales[state,str(year)]=mean(abs(v-ys[d-pd.Timedelta(days=7)]) for d,v in ys.items() if d-pd.Timedelta(days=7) in ys and math.isfinite(v) and math.isfinite(ys[d-pd.Timedelta(days=7)]))
    def extras(dates,state,arm,version):
        if arm=='calendar':return np.empty((0,len(dates)))
        if arm=='zero5':return np.zeros((5,len(dates)))
        ledger=fakes[version] if arm.startswith('placebo') else ledgers[version];flags=[]
        for family in FAMILIES:
            roots=[pd.Timestamp(r['date']) for r in ledger if r['state']==state and r['family']==family]
            active=set(roots) if 'window' not in arm else {d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))}
            flags.append(dates.isin(active).astype(float))
        if arm.startswith('pooled'):flags=[np.asarray(flags).any(axis=0).astype(float)]+[np.zeros(len(dates)) for _ in range(4)]
        return np.asarray(flags)
    def covariates(dates,state,arm,version):
        base=[(dates.dayofweek==j).astype(float) for j in range(7)]
        for j in [1,2,3]:base.extend([np.sin(2*np.pi*j*dates.dayofyear/365.2425),np.cos(2*np.pi*j*dates.dayofyear/365.2425)])
        return np.asarray(base+list(extras(dates,state,arm,version)))
    groups={};totalfresh=fitchecks=inputchecks=0;weightcache=set()
    for name,ph in reg['protocols'].items():
        out=OUT/name;p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==ph
        if part=='local' and p['kind']=='encoding':continue
        for name2,h in p['input_hashes'].items():assert sha(ROOT/name2)==h,name2
        for name2,h in p['design_hashes'].items():assert sha(out/name2)==h,name2
        cases=read(out/'primary_cases.csv');expected={case(r) for r in cases};tasks={(r['state'],r['origin']) for r in cases};version=p['calendar_version'];models=p['models'][:4] if part=='local' else p['models'];groupfresh=0
        for model in models:
            worker=json.loads((out/model/'run.json').read_text());assert worker['protocol_sha256']==ph and worker['predictions_sha256']==sha(out/model/'predictions.csv')
            predictions=read(out/model/'predictions.csv');seen=defaultdict(set)
            for r in predictions:
                c=case(r);assert c in expected and c not in seen[r['arm']];seen[r['arm']].add(c)
                assert (pd.Timestamp(r['date'])-pd.Timestamp(r['origin'])).days==int(r['horizon'])-1
                close(source.loc[pd.Timestamp(r['date']),r['state']],r['actual']);close(scales[r['state'],r['year']],r['mase_scale']);assert math.isfinite(float(r['prediction']))
            assert set(seen)==set(p['arms']) and all(s==expected for s in seen.values()) and len(predictions)==len(expected)*len(p['arms']);totalfresh+=len(predictions);groupfresh+=len(predictions)
            if model in ['ridge','lightgbm','lightgbm_capacity2']:
                from robust_baselines import design_frame
                selections=read(ROOT/f'results/{"strong_refit_v1" if model=="ridge" else "stable_tree_refit_v2"}/selected.csv')
                for r in json.loads((out/model/'fit_log.json').read_text()):
                    state,h,arm=r['state'],r['horizon'],r['arm'];base,_=design_frame(source[state],state,h,'rich_calendar')
                    extra=extras(source.index+pd.Timedelta(days=h-1),state,arm,version).T;x=pd.concat([base,pd.DataFrame(extra,index=source.index)],axis=1)
                    if model!='ridge':x=x.astype(np.float32)
                    cutoff=pd.Timestamp(r['refit'])-pd.Timedelta(days=1);origins=pd.date_range(cutoff-pd.Timedelta(days=729),cutoff-pd.Timedelta(days=h-1));dates2=origins+pd.Timedelta(days=h-1)
                    xx=x.reindex(origins).to_numpy();yy=source[state].reindex(dates2).to_numpy();valid=np.isfinite(xx).all(axis=1)&np.isfinite(yy)
                    querycases=[c for c in cases if int(c['horizon'])==h and c['origin'][:7]==r['refit'][:7]];query=x.reindex(pd.DatetimeIndex([c['origin'] for c in querycases])).to_numpy()
                    assert digest(xx[valid])==r['training_X_sha256'] and digest(yy[valid])==r['training_y_sha256'] and digest(query)==r['query_X_sha256']
                    assert dates2[valid].max()<=cutoff<min(pd.Timestamp(c['origin']) for c in querycases)
                    selected=[s for s in selections if s['state']==state and int(s['year'])==r['year'] and int(s['horizon'])==h and s['mode']=='rich_calendar' and s['model']==('ridge' if model=='ridge' else 'lightgbm')];assert len(selected)==1
                    params=json.loads(selected[0]['parameters'])
                    if model=='lightgbm_capacity2':params['min_child_samples']=2
                    assert r['parameters']==params;fitchecks+=1
            elif model=='sarimax':
                logs=json.loads((out/model/'fit_attempts.json').read_text());fits=defaultdict(list)
                for r in logs:assert r['training_end']=='2024-12-31';fits[r['configuration']].append(r)
                assert set(fits)==set(p['arms'])
                for values in fits.values():assert values[-1]['converged'] and all(not r['converged'] for r in values[:-1])
                deployed=json.loads((out/model/'deployments.json').read_text());assert len(deployed)==len(tasks)*len(p['arms'])
                for r in deployed:assert r['fitting_target_max']=='2024-12-31' and pd.Timestamp(r['context_max'])==pd.Timestamp(r['origin'])-pd.Timedelta(days=1)
            else:
                file='results/mechanism_controls_v1/chronos_download.json' if model=='chronos' else 'results/second_model_audit_v1/weight_download.json';identity=json.loads((ROOT/file).read_text());weight=next(f for f in identity['files'] if f['name']=='model.safetensors') if model=='chronos' else identity
                wr=json.loads((OUT/'weight_registration.json').read_text())['weights'][file];assert wr['metadata_sha256']==sha(ROOT/file) and wr['weight_sha256']==worker['weight_sha256']==weight['sha256']
                if model not in weightcache:assert sha(Path(weight['path']))==weight['sha256'];weightcache.add(model)
                seeninputs=defaultdict(set)
                for r in json.loads((out/model/'inputs.json').read_text()):
                    state,arm=r['state'],r['arm'];origin=pd.Timestamp(r['origin']);dates2=pd.date_range(origin-pd.Timedelta(days=730),periods=744);target=filled[state].reindex(dates2[:730]).to_numpy(dtype=np.float32)
                    if p['kind']=='breadth':cov=covariates(dates2,state,arm,version).astype(np.float32);counts=np.count_nonzero(cov[13:,:730],axis=1).tolist()
                    else:
                        y=source[state].reindex(dates2[:730]);good=y.notna().to_numpy();labels=y.to_numpy()[good];w=dates2.dayofweek.to_numpy();holidays={pd.Timestamp(c['date']) for c in ledgers[version] if c['state']==state};h=dates2.isin(holidays).astype(int);tables=[];misses=[0]
                        def encode(code):
                            cells=defaultdict(list)
                            for c,value in zip(code[:730][good],labels):cells[int(c)].append(float(value))
                            means={c:float(np.asarray(v,dtype=float).mean()) for c,v in cells.items()};tables.append(dict(means={str(c):v for c,v in means.items()},support={str(c):len(v) for c,v in cells.items()}));misses[0]+=sum(int(c) not in cells for c in code[730:])
                            return np.array([means.get(int(c),float(np.asarray(labels).mean())) for c in code])
                        if arm=='history':cols=[]
                        elif arm=='zero1':cols=[np.zeros(744)]
                        elif arm=='ordinal':cols=[w,h]
                        elif arm=='onehot':cols=[(w==j).astype(float) for j in range(7)]+[h]
                        elif arm=='cyclic':cols=[np.sin(2*np.pi*w/7),np.cos(2*np.pi*w/7),h]
                        elif arm=='te_weekday':cols=[encode(w)]
                        elif arm=='te_sunday':cols=[encode(np.where(h,6,w))]
                        elif arm=='te_holiday':cols=[encode(np.where(h,7,w))]
                        elif arm=='te_joint':cols=[encode(w+7*h)]
                        elif arm=='te_separate':cols=[encode(w),encode(h)]
                        else:raise AssertionError(arm)
                        cov=np.asarray(cols,dtype=np.float32).reshape(len(cols),744);counts=np.count_nonzero(cov[:,:730],axis=1).tolist();given=r['encoding_diagnostics']
                        assert given['recorded_context_labels']==int(good.sum()) and given['max_encoding_label']==str(y.index[good].max().date()) and given['future_unseen_category_entries']==misses[0] and len(tables)==len(given['category_tables'])
                        for a,b in zip(tables,given['category_tables']):
                            assert a['support']==b['support'] and a['means'].keys()==b['means'].keys()
                            for c,v in a['means'].items():close(v,b['means'][c])
                    assert digest(target)==r['target_sha256'] and digest(cov)==r['covariate_sha256'] and counts==r['past_nonzero_counts'] and len(cov)==r['feature_count'] and r['future_target_perturbation_invariant']
                    task=(state,r['origin']);assert task in tasks and task not in seeninputs[arm];seeninputs[arm].add(task);inputchecks+=1
                assert set(seeninputs)==set(p['arms']) and all(s==tasks for s in seeninputs.values())
                solo=json.loads((out/model/'solo_batch_audit.json').read_text());assert len(solo)==min(16,len(tasks))*len(p['arms'])
                d=pd.read_csv(out/model/'predictions.csv');q=d[sorted(c for c in d if c.startswith('q_'))].to_numpy();assert int((np.diff(q,axis=1)<0).sum())==worker['native_quantile_crossings']
        groups[name]=dict(fresh_rows=groupfresh,cases_per_arm=len(cases))
    assert totalfresh==(648 if part=='local' else 1092)
    composed={};summaries={}
    for key,meta in run['cohorts'].items():
        kind,cohort=key.split('/');out=dest/key;parent=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/{cohort}'
        expected=newset if cohort=='event_window' else {case(r) for r in read(parent/'primary_cases.csv')};models=[r['model'] for r in json.loads((out/'provenance.json').read_text())['workers']]
        references={};oldcohort=[]
        for model in models:
            oldrows=read(parent/model/'predictions.csv');oldcohort.extend(oldrows);old={(r['model'],r['arm'],case(r)):r for r in oldrows if case(r) in expected}
            if cohort=='event_window':
                group='old_added' if kind=='breadth' else 'old_encoding_added'
                for r in read(OUT/group/model/'predictions.csv'):old[r['model'],r['arm'],case(r)]=r
            aligned=dict(old)
            for r in read(SEM/kind/cohort/model/'predictions.csv'):
                if case(r) in expected and (kind=='encoding' or r['arm']!='calendar'):aligned[r['model'],r['arm'],case(r)]=r
            if cohort=='event_window':
                group='aligned_added' if kind=='breadth' else 'aligned_encoding_added'
                for r in read(OUT/group/model/'predictions.csv'):aligned[r['model'],r['arm'],case(r)]=r
            if kind=='breadth':
                for r in read(OUT/('aligned_placebo_event' if cohort=='event_window' else 'aligned_placebo_ordinary')/model/'predictions.csv'):aligned[r['model'],r['arm'],case(r)]=r
            for version,table in [('original',old),('document_aligned',aligned)]:
                for k,r in table.items():references[(version,)+k]=r
        if kind=='encoding':
            for k,r in composed['breadth/'+cohort].items():
                if r['model'] in models and r['arm']=='calendar':references[k]=r
            for model in models:oldcohort.extend(r for r in read(ROOT/f'results/feature_breadth_v1/{cohort}/{model}/predictions.csv') if r['arm']=='calendar')
        rows=read(out/'predictions_compared.csv');seen=set();point=[];mae=[];qfields=defaultdict(list);invalidgroups=set()
        for r in rows:
            k=(r['version'],r['model'],r['arm'],case(r));assert k in references and k not in seen;seen.add(k);reference=references[k]
            fields=['prediction','actual','mase_scale']+([f'q_{100*j:03d}' for j in range(1,10)] if r['model'] in ['chronos','timesfm'] else [])
            for field in fields:close(float(reference[field]),r[field])
            actual=float(source.loc[pd.Timestamp(r['date']),r['state']]);scale=scales[r['state'],r['year']];close(actual,r['actual']);close(scale,r['mase_scale'])
            error=abs(actual-float(r['prediction']));close(error,r['MAE_GWh']);close(error/scale,r['MASE']);point.append((r,error/scale));mae.append((r,error))
        assert seen==set(references) and len(rows)==meta['compared_view_rows'];composed[key]=references
        pm=macro(point,'MASE');am=macro(mae,'MAE_GWh')
        for r in read(out/'metrics_balanced.csv'):
            k=tuple(r[f] for f in ['version','model','arm','horizon']);close(pm[k],r['MASE']);close(am[k],r['MAE_GWh'])
        for r in read(out/'changes_balanced.csv'):close(pm['document_aligned',r['model'],r['arm'],r['horizon']]-pm['original',r['model'],r['arm'],r['horizon']],r['MASE_change'])
        oldpoints=[]
        for r in oldcohort:
            r=dict(r,version='oldcohort');oldpoints.append((r,abs(float(r['actual'])-float(r['prediction']))/float(r['mase_scale'])))
        oldm=macro(oldpoints,'MASE')
        for r in read(out/'composition_changes.csv'):close(pm['original',r['model'],r['arm'],r['horizon']]-oldm['oldcohort',r['model'],r['arm'],r['horizon']],r['MASE_composition_change'])
        if (out/'native_uncertainty_cases.csv').exists():
            for r in read(out/'native_uncertainty_cases.csv'):
                y=float(r['actual']);s=float(r['mase_scale']);q=[float(r[f'q_{100*j:03d}']) for j in range(1,10)];lo,med,hi=q[0],q[4],q[8]
                pin=mean(max(j/10*(y-v),(j/10-1)*(y-v)) for j,v in enumerate(q,1))/s
                coverage=float(lo<=y<=hi);width=(hi-lo)/s;wis=(.5*abs(y-med)+.1*(hi-lo+10*max(lo-y,0)+10*max(y-hi,0)))/1.5/s
                if lo>hi:coverage=width=wis=math.nan;invalidgroups.add(tuple(r[k] for k in ['version','model','arm','horizon']))
                for v,field in zip([pin,coverage,width,wis],['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                    if math.isnan(v):assert not r[field]
                    else:close(v,r[field])
                    qfields[field].append((r,v))
            qm={field:macro(values,field) for field,values in qfields.items()}
            for r in read(out/'native_uncertainty_balanced.csv'):
                k=tuple(r[f] for f in ['version','model','arm','horizon'])
                for field,values in qm.items():
                    if k in invalidgroups and field!='scaled_mean_pinball':assert not r[field]
                    else:close(values[k],r[field])
        summaries[key]=dict(compared_view_rows=len(rows),matched_cases_per_arm=len(expected),point_aggregate_cells=len(pm))
    result=dict(status='pass',scope='Internal separate source/cohort/placeboweekday/NumPyactualinput/selectionreuse/pastlabels/scalarhierarchicalpoint/interval/composition audit. No independenthuman or complete modelimplementation/reproduction claim.',new_forecasts=totalfresh,changed_true_anchors=1,changed_placebo_anchors=1,recentered_target_lead_cases=3,placebo_reuse_block_proofs=placebo_reuse_proofs,local_fit_bytechecks=fitchecks,foundation_input_bytechecks=inputchecks,groups=groups,cohorts=summaries)
    (dest/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--part',choices=['local','all'],default='all');main(p.parse_args().part)
