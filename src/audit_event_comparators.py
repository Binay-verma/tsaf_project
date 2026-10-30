"""Separate scalar/calendar reconstruction of all daily comparator forecasts."""
from collections import defaultdict
import csv
from datetime import date,timedelta
import hashlib,json,math
from pathlib import Path
from statistics import mean
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/event_comparators_v1'
FAMILIES=['Holi','Dussehra','Ganesh_Chaturthi','Ugadi_Gudi_Padwa','Diwali']


def read(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=json.loads((OUT/'protocol.json').read_text())
    for f,h in p['input_hashes'].items():assert sha(ROOT/f)==h,f
    run=json.loads((OUT/'run.json').read_text())
    assert sha(OUT/'predictions.csv')==run['predictions_sha256']
    assert sha(OUT/'protocol.json')==run['protocol_sha256']
    source=read(ROOT/'data/external/latest_state_energy_GWh.csv')
    dc=next(iter(source[0])); labels={}
    for r in source:
        for state in ['Delhi','Karnataka','Maharashtra']:
            if r[state] and float(r[state])>0:labels[state,date.fromisoformat(r[dc])]=float(r[state])
    ledger=defaultdict(set)
    for r in read(ROOT/'results/festival_features_v1/anchors_2022_2025.csv'):
        ledger[r['state'],r['family']].add(date.fromisoformat(r['date']))
    def vector(day,state):
        return [max([weight for k,weight in zip(range(-3,4),[.2,.5,.8,1.,.8,.5,.2])
                    if day-timedelta(days=k) in ledger[state,family]] or [0.]) for family in FAMILIES]
    def holiday(day,state):return any(day in ledger[state,f] for f in FAMILIES)
    residuals={}
    for (state,day),value in labels.items():
        prev=[labels[state,day-timedelta(days=k)] for k in [7,14,21,28] if (state,day-timedelta(days=k)) in labels]
        if prev:residuals[state,day]=value-mean(prev)
    forecasts=read(OUT/'predictions.csv')
    expected={}
    for cohort in p['cohorts']:
        expected[cohort]={(r['family'],r['state'],r['year'],r['origin'],r['date'],r['horizon'])
            for r in read(ROOT/f'results/feature_breadth_v1/{cohort}/primary_cases.csv')}
    contexts={};maxdiff=0.;groups=defaultdict(set);cells=defaultdict(list)
    for r in forecasts:
        cohort,state,method=r['cohort'],r['state'],r['method']
        origin,day=date.fromisoformat(r['origin']),date.fromisoformat(r['date'])
        key=(r['family'],state,r['year'],r['origin'],r['date'],r['horizon'])
        assert key in expected[cohort] and day-origin==timedelta(days=int(r['horizon'])-1)
        assert key not in groups[cohort,method];groups[cohort,method].add(key)
        actual=float(r['actual']);assert actual==labels[state,day]
        scale_end=date(int(r['year'])-1,12,31);scale_start=scale_end-timedelta(days=729)
        scale=mean(abs(labels[state,d]-labels[state,d-timedelta(days=7)])
            for i in range(7,730) if (state,(d:=scale_start+timedelta(days=i))) in labels and (state,d-timedelta(days=7)) in labels)
        assert math.isclose(scale,float(r['mase_scale']),rel_tol=1e-12,abs_tol=1e-10)
        ck=(cohort,state,origin)
        if ck not in contexts:
            days=[origin-timedelta(days=i) for i in range(730,0,-1)]
            valid=[d for d in days if (state,d) in labels]
            rr=[d for d in days if (state,d) in residuals]
            x=np.array([vector(d,state) for d in rr]);y=np.array([residuals[state,d] for d in rr])
            xx=x.sum(axis=1);denom=xx@xx
            pooled=float(xx@y/denom) if denom else 0.
            typed=np.linalg.lstsq(x,y,rcond=None)[0]
            partial=np.linalg.solve(x.T@x+2*np.eye(5),x.T@y+2*pooled*np.ones(5))
            contexts[ck]=(valid,rr,typed,pooled,partial)
        valid,rr,typed,pooled,partial=contexts[ck]
        assert max(valid)<origin and max(rr)<origin
        past=sorted(d for (s,d) in labels if s==state and d<origin and d.weekday()==day.weekday())[-4:]
        baseline=mean(labels[state,d] for d in past)
        assert math.isclose(baseline,float(r['baseline_GWh']),abs_tol=1e-8,rel_tol=1e-11)
        if method.startswith('response_'):
            query=np.array(vector(day,state))
            prediction=baseline+{'response_none':0.,'response_typed':float(query@typed),
                'response_pooled':float(query.sum()*pooled),'response_partial':float(query@partial)}[method]
        else:
            def code(d):
                w,h=d.weekday(),holiday(d,state)
                return w if method=='weekday_mean' else 6 if method=='holiday_as_sunday_mean' and h else w if method=='holiday_as_sunday_mean' else 7 if method=='holiday_separate_mean' and h else w if method=='holiday_separate_mean' else w+7*int(h)
            selected=[d for d in valid if code(d)==code(day)]
            rule='exact_category'
            if not selected:selected=[d for d in valid if d.weekday()==day.weekday()];rule='weekday_fallback'
            if not selected:selected=valid;rule='global_fallback'
            assert len(selected)==int(r['encoding_category_n']) and rule==r['encoding_backoff']
            prediction=mean(labels[state,d] for d in selected)
        diff=abs(prediction-float(r['prediction']));maxdiff=max(maxdiff,diff)
        assert diff<1e-7,(method,state,day,diff)
        cells[cohort,r['family'],method,state,r['year'],r['horizon']].append(abs(float(r['prediction'])-actual)/scale)
    assert len(forecasts)==p['planned_rows']==5952
    assert all(groups[c,m]==expected[c] for c in p['cohorts'] for m in p['methods'])
    logs=json.loads((OUT/'fit_log.json').read_text())
    assert len(logs)==len(contexts)==run['fit_contexts']
    for r in logs:
        origin=date.fromisoformat(r['origin']);v,rr,t,pool,part=contexts[r['cohort'],r['state'],origin]
        assert date.fromisoformat(r['max_encoding_label'])==max(v)<origin
        assert date.fromisoformat(r['max_profile_label'])==max(rr)<origin
        np.testing.assert_allclose(r['typed'],t,atol=1e-8,rtol=1e-10)
        np.testing.assert_allclose(r['partial'],part,atol=1e-8,rtol=1e-10)
        assert abs(r['pooled']-pool)<1e-8
    ys,fs,ms=defaultdict(list),defaultdict(list),defaultdict(list)
    for (c,f,m,s,y,h),values in cells.items():ys[c,f,m,y,h].append(mean(values))
    for (c,f,m,y,h),values in ys.items():fs[c,f,m,h].append(mean(values))
    for (c,f,m,h),values in fs.items():ms[c,m,h].append(mean(values))
    for r in read(OUT/'metrics_balanced.csv'):
        assert math.isclose(float(r['MASE']),mean(ms[r['cohort'],r['method'],r['horizon']]),abs_tol=1e-10,rel_tol=1e-10)
    result=dict(status='pass',scope='Internal separately implemented scalar/calendar forecast, cutoff and metric audit; not independent human review or exact closest-paper replication.',
        rows=len(forecasts),contexts=len(contexts),max_scalar_prediction_difference_GWh=maxdiff,tolerance_GWh=1e-7,
        no_future_labels=True,recorded_labels_only=True,all_planned_cases=True)
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
