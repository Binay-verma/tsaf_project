"""Independent NumPy/date reconstruction of new native hindcast inputs."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_calibration_v1'


def digest(x):return hashlib.sha256(x.tobytes()).hexdigest()


def main():
    out=OUT/'timesfm_hindcasts';run=json.loads((out/'run.json').read_text())
    records=json.loads((out/'inputs.json').read_text());assert len(records)==342
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D')
    filled={}
    for state in source:
        y=source[state].to_numpy(copy=True)
        for i in range(len(y)):
            if not np.isfinite(y[i]) or y[i]<=0:y[i]=y[i-7] if i>=7 and np.isfinite(y[i-7]) else y[i-1] if i else np.nan
        filled[state]=pd.Series(y,index=source.index)
    cases=pd.read_csv(OUT/'hindcast_cases.csv');expected=set(map(tuple,cases[['state','origin']].drop_duplicates().to_numpy()))
    for mode in ['history','calendar']:
        selected=[r for r in records if r['mode']==mode];assert {(r['state'],r['origin']) for r in selected}==expected
        for r in selected:
            origin=pd.Timestamp(r['origin']);dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
            target=filled[r['state']].reindex(dates[:730]).to_numpy(dtype=np.float32)
            if mode=='history':cov=np.empty((0,744),dtype=np.float32)
            else:
                cols=[(dates.dayofweek==i).astype(float) for i in range(7)]
                for k in [1,2,3]:cols+=[np.sin(2*np.pi*k*dates.dayofyear/365.2425),np.cos(2*np.pi*k*dates.dayofyear/365.2425)]
                cov=np.asarray(cols,dtype=np.float32)
            assert digest(target)==r['target_sha256'] and digest(cov)==r['covariate_sha256'] and r['future_target_invariant']
    d=pd.read_csv(out/'predictions.csv');old=pd.read_csv(ROOT/'results/postweight_daily_v1/timesfm/predictions.csv')
    key=['configuration','state','origin','date','horizon'];cols=['prediction']+[f'q_{i*100:03d}' for i in range(1,10)]
    common=d.merge(old[key+cols],on=key,suffixes=('_new','_old'),validate='one_to_one');assert len(common)==792
    differences={c:float(abs(common[c+'_new']-common[c+'_old']).max()) for c in cols};assert max(differences.values())<1e-6
    q=d[[f'q_{i*100:03d}' for i in range(1,10)]].to_numpy();assert np.isfinite(q).all()
    bad=np.diff(q,axis=1)<0;assert int(bad.sum())==run['native_crossing_pairs']
    issues=[]
    for i,j in zip(*np.where(bad)):
        r=d.iloc[i];issues.append(dict(configuration=r.configuration,state=r.state,origin=r.origin,date=r.date,horizon=int(r.horizon),lower_level=(j+1)/10,upper_level=(j+2)/10,lower_prediction=float(q[i,j]),upper_prediction=float(q[i,j+1])))
    pd.DataFrame(issues,columns=key+['lower_level','upper_level','lower_prediction','upper_prediction']).to_csv(OUT/'native_quantile_crossings.csv',index=False)
    solos=json.loads((out/'solo_batch.json').read_text());assert len(solos)==8
    result=dict(status='pass',scope='SeparateinternalNumPy/datebyteaudit;notindependenthumanreview',reconstructed_tasks=len(records),native_rows=len(d),old_rows_reproduced=792,old_point_and_quantile_maxdifferences=differences,native_crossing_pairs=int(bad.sum()),solo_batch_maxdifference=max(r['maxdifference'] for r in solos),weight_sha256=run['weight_sha256'])
    (OUT/'input_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
