"""Independent date/category construction, input-byte and native metric checks."""
from collections import defaultdict
from statistics import mean
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
from audit_breadth_study import read,sha,digest,close,case

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/calendar_encoding_v1'


def main():
    registration=json.loads((OUT/'registration.json').read_text())
    assert json.loads((ROOT/'results/feature_breadth_v1/independent_audit.json').read_text())['status']=='pass'
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D')
    source=source.where(source>0)
    ledger=read(ROOT/'results/festival_features_v1/anchors_2022_2025.csv')
    holiday={s:{pd.Timestamp(r['date']) for r in ledger if r['state']==s} for s in source}
    filled={}
    for state in source:
        a=source[state].to_numpy(dtype=float,copy=True)
        for j in range(len(a)):
            if not np.isfinite(a[j]):a[j]=a[j-7] if j>=7 and np.isfinite(a[j-7]) else a[j-1] if j else np.nan
        filled[state]=pd.Series(a,index=source.index)
    summaries,crossings={},[]
    for cohort,ph in registration['protocols'].items():
        out=OUT/cohort;p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==ph
        for name,h in p['input_hashes'].items():assert sha(ROOT/name)==h,name
        for name,h in p['design_hashes'].items():assert sha(out/name)==h,name
        expected={case(r) for r in read(out/'primary_cases.csv')}
        tasks={(r[1],r[3]) for r in expected};scales={}
        for state in source:
            for year in [2024,2025]:
                end=pd.Timestamp(f'{year-1}-12-31');tr=source.loc[end-pd.Timedelta(days=729):end,state]
                yy=tr.to_dict();scales[state,str(year)]=mean(abs(v-yy[d-pd.Timedelta(days=7)]) for d,v in yy.items() if d-pd.Timedelta(days=7) in yy and math.isfinite(v) and math.isfinite(yy[d-pd.Timedelta(days=7)]))
        cache={};input_summaries={}
        for model in ['chronos','timesfm']:
            worker=json.loads((out/model/'run.json').read_text());assert worker['predictions_sha256']==sha(out/model/'predictions.csv') and worker['protocol_sha256']==ph
            parent=json.loads((ROOT/f'results/feature_breadth_v1/{cohort}/{model}/run.json').read_text())
            assert worker['weight_sha256']==parent['weight_sha256']
            logs=json.loads((out/model/'inputs.json').read_text());assert len(logs)==len(tasks)*10
            seen=defaultdict(set);fallback=defaultdict(int)
            for r in logs:
                arm,state,origin=r['arm'],r['state'],pd.Timestamp(r['origin'])
                assert (state,r['origin']) in tasks and (state,r['origin']) not in seen[arm];seen[arm].add((state,r['origin']))
                k=state,r['origin'],arm
                if k not in cache:
                    dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
                    y=source[state].reindex(dates[:730]);valid=y.notna().to_numpy();labels=y.to_numpy()[valid]
                    w=dates.dayofweek.to_numpy();h=np.array([int(d in holiday[state]) for d in dates])
                    target=filled[state].reindex(dates[:730]).to_numpy(dtype=np.float32)
                    tables=[];misses=[0]
                    def encode(code):
                        # Explicit grouping independent of the experiment helper.
                        groups=defaultdict(list)
                        for c,value in zip(code[:730][valid],labels):groups[int(c)].append(float(value))
                        means={c:float(np.asarray(values,dtype=float).mean()) for c,values in groups.items()}
                        counts={str(c):len(values) for c,values in groups.items()}
                        tables.append(dict(means={str(c):v for c,v in means.items()},support=counts))
                        misses[0]+=sum(int(c) not in groups for c in code[730:])
                        fallback_mean=float(np.asarray(labels).mean())
                        return np.array([means.get(int(c),fallback_mean) for c in code])
                    if arm=='history':columns=[]
                    elif arm=='zero1':columns=[np.zeros(744)]
                    elif arm=='ordinal':columns=[w,h]
                    elif arm=='onehot':columns=[(w==j).astype(float) for j in range(7)]+[h]
                    elif arm=='cyclic':columns=[np.sin(2*np.pi*w/7),np.cos(2*np.pi*w/7),h]
                    elif arm=='te_weekday':columns=[encode(w)]
                    elif arm=='te_sunday':columns=[encode(np.where(h,6,w))]
                    elif arm=='te_holiday':columns=[encode(np.where(h,7,w))]
                    elif arm=='te_joint':columns=[encode(w+7*h)]
                    elif arm=='te_separate':columns=[encode(w),encode(h)]
                    else:raise AssertionError(arm)
                    cov=np.asarray(columns,dtype=np.float32).reshape(len(columns),744)
                    meta=dict(recorded_context_labels=int(valid.sum()),max_encoding_label=str(y.index[valid].max().date()),category_tables=tables,future_unseen_category_entries=misses[0])
                    cache[k]=(digest(target),digest(cov),cov.shape[0],np.count_nonzero(cov[:,:730],axis=1).tolist(),meta)
                t,c,n,counts,meta=cache[k]
                assert (r['target_sha256'],r['covariate_sha256'],r['feature_count'],r['past_nonzero_counts'])==(t,c,n,counts)
                assert r['future_target_perturbation_invariant'] and pd.Timestamp(meta['max_encoding_label'])<origin
                given=r['encoding_diagnostics']
                for field in ['recorded_context_labels','max_encoding_label','future_unseen_category_entries']:assert meta[field]==given[field]
                assert len(given['category_tables'])==len(meta['category_tables'])
                for a,b in zip(given['category_tables'],meta['category_tables']):
                    assert a['support']==b['support']
                    assert a['means'].keys()==b['means'].keys()
                    for key in a['means']:close(a['means'][key],b['means'][key])
                fallback[arm]+=meta['future_unseen_category_entries']
            assert set(seen)==set(registration['arms']) and all(v==tasks for v in seen.values())
            solo=json.loads((out/model/'solo_batch_audit.json').read_text());assert len(solo)==160
            d=pd.read_csv(out/model/'predictions.csv');qcols=sorted(c for c in d if c.startswith('q_'))
            q=d[qcols].to_numpy();assert np.isfinite(q).all();bad=np.diff(q,axis=1)<0
            assert int(bad.sum())==worker['native_quantile_crossings']
            for i,j in zip(*np.where(bad)):
                row=d.iloc[i];crossings.append(dict(cohort=cohort,model=model,arm=row.arm,state=row.state,date=row.date,horizon=int(row.horizon),lower=qcols[j],upper=qcols[j+1]))
            input_summaries[model]=dict(reconstructed_inputs=len(logs),new_native_crossing_pairs=int(bad.sum()),future_unseen_covariate_entries_by_arm=dict(fallback),max_solo_batch_difference_GWh=max(r['max_abs_difference'] for r in solo))
        rows=read(out/'predictions_compared.csv');sets=defaultdict(set);cells=defaultdict(list)
        old={(r['model'],case(r)):r for r in read(ROOT/f'results/feature_breadth_v1/{cohort}/predictions_primary.csv') if r['model'] in ['chronos','timesfm'] and r['arm']=='calendar'}
        for r in rows:
            c=case(r);assert c in expected and c not in sets[r['model'],r['arm']];sets[r['model'],r['arm']].add(c)
            assert (pd.Timestamp(r['date'])-pd.Timestamp(r['origin'])).days==int(r['horizon'])-1
            actual=float(source.loc[pd.Timestamp(r['date']),r['state']]);scale=scales[r['state'],r['year']]
            close(actual,r['actual']);close(scale,r['mase_scale'])
            if r['arm']=='calendar':
                prior=old[r['model'],c]
                for field in ['prediction','actual','mase_scale']+[f'q_{100*k:03d}' for k in range(1,10)]:close(float(prior[field]),r[field])
            cells[r['family'],r['model'],r['arm'],r['state'],r['year'],r['horizon']].append(abs(actual-float(r['prediction']))/scale)
        assert len(rows)==len(expected)*22 and set(sets)=={(m,a) for m in ['chronos','timesfm'] for a in registration['arms']+['calendar']}
        assert all(v==expected for v in sets.values())
        years,family,macro=defaultdict(list),defaultdict(list),defaultdict(list)
        for (f,m,a,s,y,h),v in cells.items():years[f,m,a,y,h].append(mean(v))
        for (f,m,a,y,h),v in years.items():family[f,m,a,h].append(mean(v))
        for (f,m,a,h),v in family.items():macro[m,a,h].append(mean(v))
        for r in read(out/'metrics_balanced.csv'):close(mean(macro[r['model'],r['arm'],r['horizon']]),r['MASE'])
        for r in read(out/'contrasts_balanced.csv'):close(mean(macro[r['model'],r['arm'],r['horizon']])-mean(macro[r['model'],r['reference'],r['horizon']]),r['MASE_change'])
        qcells=defaultdict(list)
        for r in read(out/'native_uncertainty_cases.csv'):
            actual=float(r['actual']);scale=float(r['mase_scale']);q=[float(r[f'q_{100*k:03d}']) for k in range(1,10)]
            lo,med,hi=q[0],q[4],q[8];invalid=lo>hi
            pinball=mean(max(k/10*(actual-value),(k/10-1)*(actual-value)) for k,value in enumerate(q,1))/scale
            close(pinball,r['scaled_mean_pinball'])
            if invalid:coverage=width=wis=math.nan
            else:
                coverage=float(lo<=actual<=hi);width=(hi-lo)/scale
                wis=(.5*abs(actual-med)+.1*(hi-lo+10*max(lo-actual,0)+10*max(actual-hi,0)))/1.5/scale
                for value,field in [(coverage,'coverage80'),(width,'scaled_width80'),(wis,'scaled_WIS80_median')]:close(value,r[field])
            qcells[r['family'],r['model'],r['arm'],r['state'],r['year'],r['horizon']].append((pinball,coverage,width,wis))
        ys,fs,ms=defaultdict(list),defaultdict(list),defaultdict(list)
        for (f,m,a,s,y,h),v in qcells.items():ys[f,m,a,y,h].append([mean(row[k] for row in v) for k in range(4)])
        for (f,m,a,y,h),v in ys.items():fs[f,m,a,h].append([mean(row[k] for row in v) for k in range(4)])
        for (f,m,a,h),v in fs.items():ms[m,a,h].append([mean(row[k] for row in v) for k in range(4)])
        for r in read(out/'native_uncertainty_balanced.csv'):
            values=ms[r['model'],r['arm'],r['horizon']]
            for j,field in enumerate(['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']):
                v=mean(row[j] for row in values)
                if math.isnan(v):assert not r[field]
                else:close(v,r[field])
        summaries[cohort]=dict(compared_rows=len(rows),cases_per_arm=len(expected),inputs=input_summaries)
    pd.DataFrame(crossings,columns=['cohort','model','arm','state','date','horizon','lower','upper']).to_csv(OUT/'new_native_quantile_crossings.csv',index=False)
    result=dict(status='pass',scope='Internal separate date/category/NumPy input-byte and scalar metric/interval audit; not independent human or exact hourly benchmark replication.',cohorts=summaries,new_native_crossing_pairs=len(crossings))
    dump=lambda path,d:path.write_text(json.dumps(d,indent=2)+'\n')
    dump(OUT/'independent_audit.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
