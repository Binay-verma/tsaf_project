"""Independent named-date/reuse/input-byte and hierarchical-score audit."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from statistics import mean
import numpy as np
import pandas as pd
from audit_breadth_study import read,sha,digest,close,case

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/calendar_semantics_v2'
FAMILIES=['Holi','Dussehra','Ganesh_Chaturthi','Ugadi_Gudi_Padwa','Diwali']


def macro(rows,field):
    cell=defaultdict(list);years=defaultdict(list);families=defaultdict(list);result=defaultdict(list)
    for r,value in rows:cell[tuple(r[k] for k in ['version','model','arm','family','state','year','horizon'])].append(value)
    for (v,m,a,f,s,y,h),values in cell.items():years[v,m,a,f,y,h].append(mean(values))
    for (v,m,a,f,y,h),values in years.items():families[v,m,a,f,h].append(mean(values))
    for (v,m,a,f,h),values in families.items():result[v,m,a,h].append(mean(values))
    return {k:mean(values) for k,values in result.items()}


def main(part):
    dest=OUT/('local_checkpoint_recovery_v1' if part=='local' else 'analysis')
    if (dest/'independent_audit.json').exists():raise FileExistsError('Preserve prior audit')
    reg=json.loads((OUT/'registration.json').read_text());run=json.loads((dest/'run.json').read_text())
    registered=json.loads((OUT/'analysis_registration.json').read_text());assert sha(ROOT/'src/finalize_calendar_semantics.py')==registered['source_sha256']
    oldledger=read(ROOT/'results/festival_features_v1/anchors_2022_2025.csv');ledger=read(OUT/'anchors_2022_2025.csv')
    assert len(ledger)==len(oldledger)==58
    changed=[(a,b) for a,b in zip(oldledger,ledger) if a!=b];assert len(changed)==1
    a,b=changed[0];assert (a['state'],a['family'],a['year'],a['date'],b['date'])==('Karnataka','Dussehra','2025','2025-10-02','2025-10-01')
    assert a.keys()==b.keys() and all(a[k]==b[k] for k in a if k not in ['date','label','source','evidence'])
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D').where(lambda x:x>0)
    filled={};scales={}
    for state in source:
        y=source[state].to_numpy(dtype=float,copy=True)
        for i in range(len(y)):
            if not np.isfinite(y[i]):y[i]=y[i-7] if i>=7 and np.isfinite(y[i-7]) else y[i-1] if i else np.nan
        filled[state]=pd.Series(y,index=source.index)
        for year in [2024,2025]:
            end=pd.Timestamp(f'{year-1}-12-31');yy=source.loc[end-pd.Timedelta(days=729):end,state].to_dict()
            scales[state,str(year)]=mean(abs(v-yy[d-pd.Timedelta(days=7)]) for d,v in yy.items() if d-pd.Timedelta(days=7) in yy and math.isfinite(v) and math.isfinite(yy[d-pd.Timedelta(days=7)]))
    def events(index,state,arm,led):
        flags=[]
        for family in FAMILIES:
            roots=[pd.Timestamp(r['date']) for r in led if r['family']==family and r['state']==state]
            active=set(roots) if 'window' not in arm else {d for root in roots for d in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))}
            flags.append(index.isin(active).astype(float))
        if arm.startswith('pooled'):flags=[np.asarray(flags).any(axis=0).astype(float)]+[np.zeros(len(index)) for _ in range(4)]
        return np.asarray(flags)
    def covariates(index,state,arm,led):
        base=[(index.dayofweek==j).astype(float) for j in range(7)]
        for j in [1,2,3]:base.extend([np.sin(2*np.pi*j*index.dayofyear/365.2425),np.cos(2*np.pi*j*index.dayofyear/365.2425)])
        return np.asarray(base if arm=='calendar' else base+list(events(index,state,arm,led)))
    summaries={};reuseproofs=0;allinputchecks=0
    for key,summary in run['cohorts'].items():
        kind,cohort=key.split('/');out=OUT/key;analysis=dest/key
        p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==reg['protocols'][key]
        for name,h in p['input_hashes'].items():assert sha(ROOT/name)==h,name
        for name,h in p['design_hashes'].items():assert sha(out/name)==h,name
        parent=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/{cohort}'
        assert sha(parent/'protocol.json')==p['parent_protocol_sha256'] and sha(parent/'primary_cases.csv')==p['parent_cases_sha256']
        cases=read(out/'primary_cases.csv');expected={case(r) for r in cases};tasks={(r['state'],r['origin']) for r in cases}
        fullcases=read(parent/'primary_cases.csv');fullset={case(r) for r in fullcases}
        for r in fullcases:
            if case(r) in expected:continue
            dates=pd.date_range(pd.Timestamp(r['origin'])-pd.Timedelta(days=730),periods=744)
            if kind=='breadth':
                for arm in ['day5','pooled_day5','window5','pooled_window5']:
                    np.testing.assert_array_equal(events(dates,r['state'],arm,oldledger),events(dates,r['state'],arm,ledger))
                    # Extra regressors use target dates of training and query;
                    # SARIMAX consumes every pre-origin update from preyear fit.
                    refit=pd.Timestamp(r['origin']).to_period('M').start_time;cutoff=refit-pd.Timedelta(days=1)
                    training=pd.date_range(cutoff-pd.Timedelta(days=729)+pd.Timedelta(days=int(r['horizon'])-1),cutoff)
                    update=pd.date_range(f'{int(r["year"])-1}-01-02',pd.Timestamp(r['origin'])+pd.Timedelta(days=13))
                    for block in [training,pd.DatetimeIndex([r['date']]),update]:np.testing.assert_array_equal(events(block,r['state'],arm,oldledger),events(block,r['state'],arm,ledger))
            else:
                before={pd.Timestamp(x['date']) for x in oldledger if x['state']==r['state']};after={pd.Timestamp(x['date']) for x in ledger if x['state']==r['state']}
                np.testing.assert_array_equal(dates.isin(before),dates.isin(after))
            reuseproofs+=1
        provenance=json.loads((analysis/'provenance.json').read_text());models=[r['model'] for r in provenance['workers']];fresh={};old={};fits=inputs=0
        for model in models:
            worker=json.loads((out/model/'run.json').read_text());assert sha(out/model/'predictions.csv')==worker['predictions_sha256'] and worker['protocol_sha256']==sha(out/'protocol.json')
            oldrun=json.loads((parent/model/'run.json').read_text());assert sha(parent/model/'predictions.csv')==oldrun['predictions_sha256']
            for r in read(parent/model/'predictions.csv'):old[model,r['arm'],case(r)]=r
            for r in read(out/model/'predictions.csv'):fresh[model,r['arm'],case(r)]=r
            if model in ['ridge','lightgbm','lightgbm_capacity2']:
                from robust_baselines import design_frame
                selection=read(ROOT/f'results/{"strong_refit_v1" if model=="ridge" else "stable_tree_refit_v2"}/selected.csv')
                for r in json.loads((out/model/'fit_log.json').read_text()):
                    state,h,arm=r['state'],r['horizon'],r['arm'];base,_=design_frame(source[state],state,h,'rich_calendar')
                    extra=events(source.index+pd.Timedelta(days=h-1),state,arm,ledger).T if arm!='calendar' else np.empty((len(source),0))
                    x=pd.concat([base,pd.DataFrame(extra,index=source.index)],axis=1);x=x.astype(np.float32) if model!='ridge' else x
                    cutoff=pd.Timestamp(r['refit'])-pd.Timedelta(days=1);origins=pd.date_range(cutoff-pd.Timedelta(days=729),cutoff-pd.Timedelta(days=h-1));dates=origins+pd.Timedelta(days=h-1)
                    xx=x.reindex(origins).to_numpy();yy=source[state].reindex(dates).to_numpy();valid=np.isfinite(xx).all(axis=1)&np.isfinite(yy);xx=xx[valid];yy=yy[valid]
                    group=[c for c in cases if int(c['horizon'])==h and c['origin'][:7]==r['refit'][:7]];query=x.reindex(pd.DatetimeIndex([c['origin'] for c in group])).to_numpy()
                    assert digest(xx)==r['training_X_sha256'] and digest(yy)==r['training_y_sha256'] and digest(query)==r['query_X_sha256']
                    assert dates[valid].max()<=cutoff<min(pd.Timestamp(c['origin']) for c in group)
                    params=[s for s in selection if s['state']==state and int(s['year'])==r['year'] and int(s['horizon'])==h and s['mode']=='rich_calendar' and s['model']==('ridge' if model=='ridge' else 'lightgbm')];assert len(params)==1
                    expectedparams=json.loads(params[0]['parameters'])
                    if model=='lightgbm_capacity2':expectedparams['min_child_samples']=2
                    assert r['parameters']==expectedparams;fits+=1
            elif model=='sarimax':
                attempts=json.loads((out/model/'fit_attempts.json').read_text());grouped=defaultdict(list)
                for r in attempts:grouped[r['configuration'],r['state'],r['year']].append(r);assert r['training_end']=='2024-12-31'
                for values in grouped.values():assert values[-1]['converged'] and all(not r['converged'] for r in values[:-1])
                deployments=json.loads((out/model/'deployments.json').read_text());assert len(deployments)==len(tasks)*5
                for r in deployments:assert r['fitting_target_max']=='2024-12-31' and pd.Timestamp(r['context_max'])<pd.Timestamp(r['origin'])
            else:
                assert worker['weight_sha256']==oldrun['weight_sha256'];seen=defaultdict(set)
                for r in json.loads((out/model/'inputs.json').read_text()):
                    state,arm=r['state'],r['arm'];origin=pd.Timestamp(r['origin']);dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
                    target=filled[state].reindex(dates[:730]).to_numpy(dtype=np.float32)
                    if kind=='breadth':cov=covariates(dates,state,arm,ledger).astype(np.float32);counts=np.count_nonzero(cov[13:,:730],axis=1).tolist()
                    else:
                        y=source[state].reindex(dates[:730]);good=y.notna().to_numpy();labels=y.to_numpy()[good];w=dates.dayofweek.to_numpy();holidays={pd.Timestamp(c['date']) for c in ledger if c['state']==state};h=dates.isin(holidays).astype(int);tables=[];unseen=[0]
                        def encode(code):
                            groups=defaultdict(list)
                            for c,v in zip(code[:730][good],labels):groups[int(c)].append(float(v))
                            means={c:float(np.asarray(v,dtype=float).mean()) for c,v in groups.items()};tables.append(dict(means={str(c):v for c,v in means.items()},support={str(c):len(v) for c,v in groups.items()}));unseen[0]+=sum(int(c) not in groups for c in code[730:])
                            return np.array([means.get(int(c),float(np.asarray(labels).mean())) for c in code])
                        if arm=='ordinal':cols=[w,h]
                        elif arm=='onehot':cols=[(w==j).astype(float) for j in range(7)]+[h]
                        elif arm=='cyclic':cols=[np.sin(2*np.pi*w/7),np.cos(2*np.pi*w/7),h]
                        elif arm=='te_sunday':cols=[encode(np.where(h,6,w))]
                        elif arm=='te_holiday':cols=[encode(np.where(h,7,w))]
                        elif arm=='te_joint':cols=[encode(w+7*h)]
                        elif arm=='te_separate':cols=[encode(w),encode(h)]
                        else:raise AssertionError(arm)
                        cov=np.asarray(cols,dtype=np.float32);counts=np.count_nonzero(cov[:,:730],axis=1).tolist();given=r['encoding_diagnostics']
                        assert given['future_unseen_category_entries']==unseen[0] and given['recorded_context_labels']==int(good.sum()) and given['max_encoding_label']==str(y.index[good].max().date())
                        assert len(tables)==len(given['category_tables'])
                        for a,b in zip(tables,given['category_tables']):
                            assert a['support']==b['support'] and a['means'].keys()==b['means'].keys()
                            for c,v in a['means'].items():close(v,b['means'][c])
                    assert digest(target)==r['target_sha256'] and digest(cov)==r['covariate_sha256'] and counts==r['past_nonzero_counts'] and len(cov)==r['feature_count']
                    assert r['future_target_perturbation_invariant'];task=(state,r['origin']);assert task in tasks and task not in seen[arm];seen[arm].add(task);inputs+=1
                assert set(seen)==set(p['arms']) and all(v==tasks for v in seen.values())
                solo=json.loads((out/model/'solo_batch_audit.json').read_text());assert len(solo)==min(16,len(tasks))*len(p['arms'])
                table=pd.read_csv(out/model/'predictions.csv');q=table[sorted(c for c in table if c.startswith('q_'))].to_numpy();assert int((np.diff(q,axis=1)<0).sum())==worker['native_quantile_crossings']
        rows=read(analysis/'predictions_compared.csv');seen=defaultdict(set);point=[];mae=[];prob=defaultdict(list)
        for r in rows:
            c=case(r);assert c in fullset and c not in seen[r['version'],r['model'],r['arm']];seen[r['version'],r['model'],r['arm']].add(c)
            usefresh=r['version']=='document_aligned' and r['arm']!='calendar' and (r['model'],r['arm'],c) in fresh
            reference=(fresh if usefresh else old)[r['model'],r['arm'],c]
            fields=['prediction','actual','mase_scale']+([f'q_{100*k:03d}' for k in range(1,10)] if r['model'] in ['chronos','timesfm'] else [])
            for field in fields:close(float(reference[field]),r[field])
            actual=float(source.loc[pd.Timestamp(r['date']),r['state']]);scale=scales[r['state'],r['year']];close(actual,r['actual']);close(scale,r['mase_scale'])
            error=abs(actual-float(r['prediction']));close(error,r['MAE_GWh']);close(error/scale,r['MASE']);point.append((r,error/scale));mae.append((r,error))
        assert all(values==fullset for values in seen.values()) and len(rows)==summary['compared_view_rows']
        pm=macro(point,'MASE');am=macro(mae,'MAE_GWh')
        for r in read(analysis/'metrics_balanced.csv'):
            k=tuple(r[f] for f in ['version','model','arm','horizon']);close(pm[k],r['MASE']);close(am[k],r['MAE_GWh'])
        for r in read(analysis/'changes_balanced.csv'):close(pm['document_aligned',r['model'],r['arm'],r['horizon']]-pm['original',r['model'],r['arm'],r['horizon']],r['MASE_change'])
        invalidgroups=set()
        if (analysis/'native_uncertainty_cases.csv').exists():
            for r in read(analysis/'native_uncertainty_cases.csv'):
                actual=float(r['actual']);scale=float(r['mase_scale']);q=[float(r[f'q_{100*k:03d}']) for k in range(1,10)];lo,med,hi=q[0],q[4],q[8]
                pin=mean(max(k/10*(actual-v),(k/10-1)*(actual-v)) for k,v in enumerate(q,1))/scale
                coverage=float(lo<=actual<=hi);width=(hi-lo)/scale;wis=(.5*abs(actual-med)+.1*(hi-lo+10*max(lo-actual,0)+10*max(actual-hi,0)))/1.5/scale
                if lo>hi:
                    coverage=width=wis=math.nan;invalidgroups.add(tuple(r[k] for k in ['version','model','arm','horizon']))
                for value,field in zip([pin,coverage,width,wis],['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                    if math.isnan(value):assert not r[field]
                    else:close(value,r[field])
                    prob[field].append((r,value))
            qs={field:macro(values,field) for field,values in prob.items()}
            for r in read(analysis/'native_uncertainty_balanced.csv'):
                k=tuple(r[f] for f in ['version','model','arm','horizon'])
                for field,values in qs.items():
                    if k in invalidgroups and field!='scaled_mean_pinball':assert not r[field]
                    else:close(values[k],r[field])
        allinputchecks+=inputs;summaries[key]=dict(new_local_fit_bytechecks=fits,new_foundation_input_bytechecks=inputs,compared_view_rows=len(rows),point_aggregate_cells=len(pm))
    result=dict(status='pass',scope='Internal separate named-date/reuse-block/NumPyfeaturebyte/past-label/parameter/scalarpoint/interval/hierarchy audit. Same source/libraries, not independent human/model reimplementation or amendment certification.',changed_named_dates=1,unchanged_case_block_proofs=reuseproofs,new_foundation_input_checks=allinputchecks,cohorts=summaries)
    (dest/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--part',choices=['local','all'],default='all');main(p.parse_args().part)
