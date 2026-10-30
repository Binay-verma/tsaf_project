"""Fixed NYC point/probability scoring with explicit decision/model leads and units."""
import argparse,itertools,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from mta_holiday_study import ROOT,OUT,ARMS,FOUNDATION_ARMS,MODELS,load_source
from festival_feature_design import KEY,sha,dump
from finalize_breadth_study import aggregate
from report_multifestival import markdown


def register():
    path=OUT/'analysis_registration.json'
    if path.exists():raise FileExistsError('Preserve analysis registration')
    dump(path,dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),registration_sha256=sha(OUT/'registration.json'),
        status='Before aggregateevent/ordinaryMTAerrors or naiveforecasts. Source/selectionquality inspected; localworkers mayalready becomplete, no event/ordinaryscores inspected.',
        naive='Last availablepositive source label beforemodelorigin, repeated. Seasonal repeats last7availablecalendar labels: actualmodelstep h uses origin-7+(h-1)%7. Never use unobserved7-daybridge labels. Same730daypre2026weeklyscale asallmodels.',
        metrics='MAE_million_rides/MASE withinfamily/series/year/actualmodellead, equalrelatedmodes thenyears thenfamilies. Effectiveleads8/14/21 corresponddecision1/7/14. All28commonarm paircontrasts; bothTSFMsextra9arm/history contrasts, everyfamily and leave-one-family-out descriptivecomposition. No independentrow significance/methodselection.',
        probability='Unmodified common0.1–0.9 nativequantiles: mean scaledpinball/80coverage/scaledwidth/WIS80median. Anyinvalid80endpoint makes allassociatedintervalaggregates undefined, not silentlydropped. Native21/9quantilecrossings retained. No intervalcalibration trained on theseevents.',
        source='MTAreportedestimates in millionrides, not GWh/uniquepeople/latentdemand. Onecity/tworelatedmodes/twoeventoccurrences, currentrevisedvintage and assumed7daybuffer; not independenthuman/prospective or causal confirmation.'))


def main(part):
    reg=json.loads((OUT/'analysis_registration.json').read_text());assert sha(__file__)==reg['source_sha256'] and sha(OUT/'registration.json')==reg['registration_sha256']
    models=MODELS[:4] if part=='local' else MODELS
    for cohort in ['event_window','ordinary']:
        for model in models:assert (OUT/cohort/model/'run.json').exists() and not (OUT/cohort/model/'failure.txt').exists(),(cohort,model)
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if dest.exists():raise FileExistsError('Preserve previous analysis')
    dest.mkdir();source=load_source();scales={}
    for state in source:
        tr=source.loc['2024-01-02':'2025-12-31',state];scales[state]=float((tr-tr.shift(7)).abs().mean());assert scales[state]>0
    summaries={}
    for cohort in ['event_window','ordinary']:
        out=dest/cohort;out.mkdir();parent=OUT/cohort;cases=pd.read_csv(parent/'primary_cases.csv');expected=set(map(tuple,cases[KEY].to_numpy()));chunks=[]
        for model in models:
            run=json.loads((parent/model/'run.json').read_text());assert run['protocol_sha256']==sha(parent/'protocol.json') and run['predictions_sha256']==sha(parent/model/'predictions.csv')
            d=pd.read_csv(parent/model/'predictions.csv');arms=FOUNDATION_ARMS if model in ['chronos','timesfm'] else ARMS
            assert len(d)==len(cases)*len(arms) and set(d.arm)==set(arms) and set(d.model)=={model}
            for _,g in d.groupby('arm'):assert set(map(tuple,g[KEY].to_numpy()))==expected
            chunks.append(d)
        naives=[]
        for r in cases.itertuples(index=False):
            origin=pd.Timestamp(r.origin)
            for model,day in [('last',origin-pd.Timedelta(days=1)),('seasonal',origin-pd.Timedelta(days=7)+pd.Timedelta(days=(r.horizon-1)%7))]:
                assert day<origin;row=r._asdict();row.update(model=model,arm='history',prediction=float(source.loc[day,r.state]),actual=float(source.loc[pd.Timestamp(r.date),r.state]),mase_scale=scales[r.state],last_label_used=str(day.date()));naives.append(row)
        naive=pd.DataFrame(naives);naive.to_csv(out/'naive_predictions.csv',index=False);d=pd.concat([*chunks,naive],ignore_index=True)
        assert not d.duplicated(KEY+['model','arm']).any() and np.isfinite(d[['actual','prediction','mase_scale']]).all().all()
        assert d.horizon.sub(d.decision_lead).eq(7).all();d['MAE_million_rides']=abs(d.prediction-d.actual);d['MASE']=d.MAE_million_rides/d.mase_scale
        d.to_csv(out/'predictions_compared.csv',index=False)
        cell,family,macro=aggregate(d,['MAE_million_rides','MASE'])
        for table in [cell,family,macro]:table['decision_lead']=table.horizon-7
        cell.to_csv(out/'metrics_series_year.csv',index=False);family.to_csv(out/'metrics_family.csv',index=False);macro.to_csv(out/'metrics_balanced.csv',index=False)
        pairs=[];keys=['family','state','year','horizon']
        for model in models:
            arms=FOUNDATION_ARMS if model in ['chronos','timesfm'] else ARMS;c=cell[cell.model.eq(model)]
            for arm,reference in itertools.combinations(arms,2):
                a=c[c.arm.eq(arm)].merge(c[c.arm.eq(reference)],on=keys,suffixes=('_arm','_reference'),validate='one_to_one')
                a['model']=model;a['arm']=arm;a['reference']=reference;a['MASE_change']=a.MASE_arm-a.MASE_reference;pairs.append(a[keys+['model','arm','reference','MASE_change']])
        pairs=pd.concat(pairs);pairs.to_csv(out/'contrasts_series_year.csv',index=False)
        year=pairs.groupby(['family','model','arm','reference','year','horizon']).MASE_change.mean().reset_index();year.to_csv(out/'contrasts_year.csv',index=False)
        fam=year.groupby(['family','model','arm','reference','horizon']).MASE_change.mean().reset_index();fam.to_csv(out/'contrasts_family.csv',index=False)
        bal=fam.groupby(['model','arm','reference','horizon']).MASE_change.mean().reset_index();bal['decision_lead']=bal.horizon-7;bal.to_csv(out/'contrasts_balanced.csv',index=False)
        if cohort=='event_window':
            omissions=[]
            for omitted in sorted(fam.family.unique()):
                table=fam[~fam.family.eq(omitted)].groupby(['model','arm','reference','horizon']).MASE_change.mean().reset_index();table['omitted_family']=omitted;omissions.append(table)
            pd.concat(omissions).to_csv(out/'leave_family_out.csv',index=False)
        q=d[d.model.isin(['chronos','timesfm'])].copy();invalid_count=0;crossings=0
        if len(q):
            values=q[[f'q_{100*k:03d}' for k in range(1,10)]].to_numpy();assert np.isfinite(values).all();actual=q.actual.to_numpy();scale=q.mase_scale.to_numpy();res=actual[:,None]-values;tau=np.arange(1,10)/10
            q['scaled_mean_pinball']=np.maximum(tau*res,(tau-1)*res).mean(axis=1)/scale
            lo,med,hi=values[:,0],values[:,4],values[:,8];invalid=lo>hi;q['invalid80']=invalid;q['common_crossings']=(np.diff(values,axis=1)<0).sum(axis=1);invalid_count=int(invalid.sum());crossings=int(q.common_crossings.sum())
            q['coverage80']=np.where(invalid,np.nan,((lo<=actual)&(actual<=hi)).astype(float));q['scaled_width80']=np.where(invalid,np.nan,hi-lo)/scale
            q['scaled_WIS80_median']=np.where(invalid,np.nan,(.5*abs(actual-med)+.1*(hi-lo+10*np.maximum(lo-actual,0)+10*np.maximum(actual-hi,0)))/1.5)/scale
            fields=['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median'];qc,qf,qm=aggregate(q,fields)
            for (model,arm,h),bad in q.groupby(['model','arm','horizon']).invalid80.any().items():
                if bad:
                    for table in [qc,qf,qm]:table.loc[table.model.eq(model)&table.arm.eq(arm)&table.horizon.eq(h),fields[1:]]=np.nan
            for table in [qc,qf,qm]:table['decision_lead']=table.horizon-7
            q.to_csv(out/'native_uncertainty_cases.csv',index=False);qc.to_csv(out/'native_uncertainty_series_year.csv',index=False);qf.to_csv(out/'native_uncertainty_family.csv',index=False);qm.to_csv(out/'native_uncertainty_balanced.csv',index=False)
        lines=['# NYC MTA '+part+' checkpoint: '+cohort,'','Providerdailyestimatedridership in millionrides. Fixed7dayobservationbuffer; decisionleads1/7/14 are actualmodelsteps8/14/21. Calendar/typed/pooled/zero/weekdayplacebo comparisons retainallarms; TSFMsadditionalhistory-onlyreference. OneNYCcity/tworelatedmodes/twoeventoccurrences, not independent-row/prospective/causalevidence.','']
        for lead in [1,7,14]:
            table=macro[macro.decision_lead.eq(lead)].pivot(index='model',columns='arm',values='MASE');lines += [f'## Decision lead {lead}, model step {lead+7}: MASE','',markdown(table.round(5).reset_index()),'']
        lines += ['Fullpoint/family/series/contrast/nativeprobabilitytables retained; a scorechange doesnot select futurefeatures or certify a serviceclosure mechanism. Currentvintage/assumedlag/proxy/amendment/human/Indianreuse/futuregates remain.']
        (out/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n');summaries[cohort]=dict(model_rows=sum(len(x) for x in chunks),naive_rows=len(naive),compared_rows=len(d),cases_per_arm=len(cases),common_crossing_pairs=crossings,invalid80=invalid_count,predictions_sha256=sha(out/'predictions_compared.csv'))
    assert sum(s['model_rows'] for s in summaries.values())==(4032 if part=='local' else 6300)
    dump(dest/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),part=part,cohorts=summaries,analysis_registration_sha256=sha(OUT/'analysis_registration.json')));print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze']);p.add_argument('--part',choices=['local','all'],default='all');a=p.parse_args();register() if a.action=='register' else main(a.part)
