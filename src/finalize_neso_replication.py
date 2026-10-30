"""Frozen NESO score rules; partial local checkpoint never substitutes for full results."""
import argparse,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from neso_replication import ROOT,OUT,ARMS,MODELS,STATE,load_source
from festival_feature_design import KEY,sha,dump
from report_multifestival import markdown


def register():
    path=OUT/'analysis_registration.json'
    if path.exists():raise FileExistsError('Preserve registered analysis')
    dump(path,dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),registration_sha256=sha(OUT/'registration.json'),
        policy='No aggregateSeptembererrors inspected before this analysisregistration. Originalprotocol fixed point/probabilitymetrics before sourceacquisition. Allmethods/arms retained; no validationonSeptember.',
        naive='last:latestrecordedlabel before modelorigin, repeated. seasonal:repeat last7available dailylabels, modelstep h uses origin-7+(h-1)%7. No actualbridgeobservations.',
        aggregation='OneEngland/Walesseries,16identical targetdates perdecisionlead. Arithmeticmean over16recordedlabels; scenarios separate. PointMAE/MASE; pairsignedMASEchange tocalendar for all7extraarms; no independencepvalues/bootstrap over16serialdays.',
        quantiles='Unmodified common0.1–0.9: meanscaledpinball; native80coverage/scaledwidth/oneintervalWISwithmedian. Anyinvalid80endpoint propagatesundefined interval aggregate for its group; no crossingsrepair.',
        limits='Oneadditionalgeography/16historicalordinarydates. No independentfestival, vintage, causal, cleanprospective or superiorityclaim. Fixed21additionaldayslag sensitivity is not recreated firstreleaseavailability.'))


def main(part):
    a=json.loads((OUT/'analysis_registration.json').read_text());assert sha(__file__)==a['source_sha256']
    assert sha(OUT/'registration.json')==a['registration_sha256']
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if dest.exists():raise FileExistsError('Preserve completed/interrupted analysis')
    dest.mkdir();source=load_source()[STATE];models=MODELS[:4] if part=='local' else MODELS
    tr=source.loc['2024-01-02':'2025-12-31'];scale=float((tr-tr.shift(7)).abs().mean())
    chunks=[];naives=[]
    for scenario in ['ideal','lag21']:
        out=OUT/scenario;cases=pd.read_csv(out/'primary_cases.csv');expected=set(map(tuple,cases[KEY].to_numpy()))
        for model in models:
            run=json.loads((out/model/'run.json').read_text());assert run['predictions_sha256']==sha(out/model/'predictions.csv')
            assert run['protocol_sha256']==sha(out/'protocol.json')
            d=pd.read_csv(out/model/'predictions.csv');assert len(d)==384 and set(d.arm)==set(ARMS)
            for arm,g in d.groupby('arm'):assert set(map(tuple,g[KEY].to_numpy()))==expected
            assert set(d.model)=={model} and set(d.scenario)=={scenario};chunks.append(d)
        for r in cases.itertuples(index=False):
            origin=pd.Timestamp(r.origin)
            for model,day in [('last',origin-pd.Timedelta(days=1)),('seasonal',origin-pd.Timedelta(days=7)+pd.Timedelta(days=(r.horizon-1)%7))]:
                assert day<origin
                row=r._asdict();row.update(model=model,arm='history',prediction=float(source.loc[day]),actual=float(source.loc[pd.Timestamp(r.date)]),mase_scale=scale,last_label_used=str(day.date()))
                naives.append(row)
    n=pd.DataFrame(naives);assert len(n)==192;n.to_csv(dest/'naive_predictions.csv',index=False)
    d=pd.concat([*chunks,n],ignore_index=True)
    assert not d.duplicated(['scenario','model','arm']+KEY).any()
    assert np.isfinite(d[['prediction','actual','mase_scale']]).all().all()
    d['MAE_GWh']=abs(d.prediction-d.actual);d['MASE']=d.MAE_GWh/d.mase_scale
    d.to_csv(dest/'predictions_compared.csv',index=False)
    groups=['scenario','model','arm','decision_lead','horizon']
    m=d.groupby(groups).agg(MAE_GWh=('MAE_GWh','mean'),MASE=('MASE','mean'),n=('MASE','size')).reset_index();assert m.n.eq(16).all()
    m.to_csv(dest/'metrics.csv',index=False)
    cells=d[d.model.isin(models)];ref=cells[cells.arm.eq('calendar')]
    k=['scenario','model']+KEY
    p=cells[~cells.arm.eq('calendar')].merge(ref[k+['MASE']],on=k,suffixes=('','_calendar'),validate='many_to_one')
    p['MASE_change']=p.MASE-p.MASE_calendar
    p[groups+['date','MASE_change']].to_csv(dest/'contrasts_cases.csv',index=False)
    p.groupby(groups).MASE_change.mean().reset_index().to_csv(dest/'contrasts.csv',index=False)
    q=d[d.model.isin(['chronos','timesfm'])].copy()
    if len(q):
        values=q[[f'q_{100*k:03d}' for k in range(1,10)]].to_numpy();assert np.isfinite(values).all()
        y=q.actual.to_numpy();s=q.mase_scale.to_numpy();res=y[:,None]-values;tau=np.arange(1,10)/10
        q['scaled_mean_pinball']=np.maximum(tau*res,(tau-1)*res).mean(axis=1)/s
        lo,med,hi=values[:,0],values[:,4],values[:,8];invalid=lo>hi
        q['invalid80']=invalid;q['common_crossings']=(np.diff(values,axis=1)<0).sum(axis=1)
        q['coverage80']=np.where(invalid,np.nan,((lo<=y)&(y<=hi)).astype(float))
        q['scaled_width80']=np.where(invalid,np.nan,hi-lo)/s
        q['scaled_WIS80_median']=np.where(invalid,np.nan,(.5*abs(y-med)+.1*(hi-lo+10*np.maximum(lo-y,0)+10*np.maximum(y-hi,0)))/1.5)/s
        fields=['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']
        qm=q.groupby(groups)[fields].mean().reset_index()
        for key,bad in q.groupby(groups).invalid80.any().items():
            if bad:
                mask=np.ones(len(qm),bool)
                for field,value in zip(groups,key):mask&=qm[field].eq(value)
                qm.loc[mask,fields[1:]]=np.nan
        q.to_csv(dest/'native_uncertainty_cases.csv',index=False);qm.to_csv(dest/'native_uncertainty_metrics.csv',index=False)
    lines=['# NESO independent-source '+part+' checkpoint','',
        'Retrospective16ordinarySeptember2026dates in oneEngland/Walesseries. Dailyenergy integrates completeactualMW half-hours. Ideal and21additionalday delays are separate sensitivity scenarios; not first-vintage reconstruction or independent festival confirmation. All8arms/negativefindings retained. Historicalerrors must not select next configurations.','']
    for scenario in ['ideal','lag21']:
        for h in [1,7,14]:
            table=m[m.scenario.eq(scenario)&m.decision_lead.eq(h)].pivot(index='model',columns='arm',values='MASE')
            lines += [f'## {scenario}, decision lead {h}','',markdown(table.round(5).reset_index()),'']
    lines += ['No independent-row significance/yeargeneralisation from16serialdays. Calendarfamily/channel count differs fromIndia. Currentarchive is revised; customNESOlicencebody remainsunverified, raw/complete derivedseries excluded fromGit. Indianreusepermission, amendments, independent humanreview and futureconfirmation are still external gates.']
    (dest/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n')
    dump(dest/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),models=models,model_rows=sum(len(x) for x in chunks),naive_rows=len(n),compared_rows=len(d),
        source_sha256=sha(OUT/'snapshot.json'),analysis_registration_sha256=sha(OUT/'analysis_registration.json'),predictions_sha256=sha(dest/'predictions_compared.csv')))
    print(json.dumps(dict(part=part,compared_rows=len(d),models=models)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze']);p.add_argument('--part',choices=['local','all'],default='all');a=p.parse_args()
    register() if a.action=='register' else main(a.part)
