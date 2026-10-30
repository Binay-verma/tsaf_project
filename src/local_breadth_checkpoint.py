"""Completed local panel only; never writes the pending six-model final analysis."""
from collections import defaultdict
from statistics import mean
from datetime import datetime,timezone
import json,math
import numpy as np
import pandas as pd
from breadth_study import ROOT,OUT,KEY,ARMS
from festival_feature_design import sha,dump
from finalize_festival_features import score
from report_multifestival import markdown


def main():
    dest=OUT/'local_checkpoint'
    if dest.exists():raise FileExistsError('Preserve completed checkpoint')
    dest.mkdir()
    source=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True)
    models=['ridge','lightgbm','lightgbm_capacity2','sarimax']
    summaries={};lines=['# Completed classical breadth checkpoint','',
        'The four registered local variants are complete. Both foundation-model lanes are still running; this is not the final six-model table. All eightarms are retained, with no outcome-selected configuration. Historical/exploratory.','']
    for cohort in ['event_window','ordinary']:
        out=dest/cohort;out.mkdir()
        parent=OUT/cohort;protocol=json.loads((parent/'protocol.json').read_text())
        for name,h in protocol['input_hashes'].items():assert sha(ROOT/name)==h
        expected=pd.read_csv(parent/'primary_cases.csv')[KEY];chunks=[]
        for model in models:
            run=json.loads((parent/model/'run.json').read_text())
            assert sha(parent/'protocol.json')==run['protocol_sha256']
            assert sha(parent/model/'predictions.csv')==run['predictions_sha256']
            d=pd.read_csv(parent/model/'predictions.csv')
            assert len(d)==len(expected)*8 and set(d.model)=={model}
            for arm,g in d.groupby('arm'):
                assert arm in ARMS and len(g)==len(expected)
                assert set(map(tuple,g[KEY].to_numpy()))==set(map(tuple,expected.to_numpy()))
            chunks.append(d)
        d=pd.concat(chunks,ignore_index=True)
        assert not d.duplicated(KEY+['model','arm']).any()
        assert np.isfinite(d[['actual','prediction','mase_scale']]).all().all()
        # Independently scalar-reconstruct source/scale and hierarchy from saved rows.
        scales={};cells=defaultdict(list)
        for r in d.itertuples(index=False):
            assert float(source.loc[pd.Timestamp(r.date),r.state])==r.actual
            k=r.state,r.year
            if k not in scales:
                end=pd.Timestamp(f'{r.year-1}-12-31');start=end-pd.Timedelta(days=729)
                obs=source.loc[start:end,r.state].to_dict()
                scales[k]=mean(abs(v-obs[t-pd.Timedelta(days=7)]) for t,v in obs.items() if t-pd.Timedelta(days=7) in obs and math.isfinite(v) and math.isfinite(obs[t-pd.Timedelta(days=7)]))
            assert math.isclose(r.mase_scale,scales[k],abs_tol=1e-9,rel_tol=1e-10)
            cells[r.family,r.model,r.arm,r.state,r.year,r.horizon].append(abs(r.prediction-r.actual)/r.mase_scale)
        d.to_csv(out/'predictions.csv',index=False);score(d,out,'primary')
        years,families,macro=defaultdict(list),defaultdict(list),defaultdict(list)
        for (f,m,a,s,y,h),values in cells.items():years[f,m,a,y,h].append(mean(values))
        for (f,m,a,y,h),values in years.items():families[f,m,a,h].append(mean(values))
        for (f,m,a,h),values in families.items():macro[m,a,h].append(mean(values))
        m=pd.read_csv(out/'primary_metrics_balanced.csv')
        for r in m.itertuples(index=False):assert math.isclose(r.MASE,mean(macro[r.model,r.arm,r.horizon]),abs_tol=1e-10,rel_tol=1e-10)
        lines += ['## '+cohort,'']
        for h in [1,7,14]:
            table=m[m.horizon.eq(h)].pivot(index='model',columns='arm',values='MASE').reindex(index=models,columns=ARMS)
            lines += [f'### Lead {h}','',markdown(table.round(5).reset_index()),'']
        summaries[cohort]=dict(rows=len(d),cases_per_arm=len(expected),models=models,source_scale_metric_audit='pass',predictions_sha256=sha(out/'predictions.csv'))
    (dest/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n')
    dump(dest/'run.json',dict(status='completed_local_only',completed_utc=datetime.now(timezone.utc).isoformat(),
        rows=sum(d['rows'] for d in summaries.values()),cohorts=summaries,note='Independent scalar metric/source check; full fitting/support/input audit runs after all six models finish. Not complete main comparison.'))
    print('Completed23808local forecasts; source/cases/scales/metrics reconstructed;foundationresultsPENDING')


if __name__=='__main__':main()
