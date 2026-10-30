"""Complete nearest-encoding matrix, with unchanged main-calendar reference."""
import json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from calendar_encoding_study import ROOT,OUT,ARMS
from festival_feature_design import KEY,sha,dump
from finalize_breadth_study import aggregate
from report_multifestival import markdown


def register():
    dest=OUT/'analysis_registration.json'
    if dest.exists():raise FileExistsError('Preserve prior analysis registration')
    dump(dest,dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Scoring rules fixed before any queued encoding inference/outputs. Historical outcomes already examined.',
        references='Reuse exactly the completed breadth calendar13 outputs on identical cases/weights/source after its separate audit passes; no forecast recomputation.',
        contrasts=[['te_sunday','te_weekday'],['te_holiday','te_weekday'],['te_joint','te_weekday'],
                   ['te_weekday','zero1'],['te_separate','ordinal'],['calendar','history']],
        metrics='Same hierarchy and pre-year weeklyscale; MASE/MAE, nativecommon9quantile pinball and native80coverage/scaledwidth/oneintervalWIS. Nativecrossingsunchanged; any invalidendpoint propagatesundefinedintervalaggregate.',
        source_sha256=sha(__file__),registration_sha256=sha(OUT/'registration.json')))
    print('Registered10pureencodings+unchangedmaincalendar reference; matched cases/probability rules')


def main():
    if (OUT/'run.json').exists():raise FileExistsError('Preserve completed analysis')
    analysis=json.loads((OUT/'analysis_registration.json').read_text())
    assert sha(__file__)==analysis['source_sha256']
    assert sha(OUT/'registration.json')==analysis['registration_sha256']
    parent=ROOT/'results/feature_breadth_v1'
    assert json.loads((parent/'independent_audit.json').read_text())['status']=='pass'
    registration=json.loads((OUT/'registration.json').read_text());summaries={}
    for cohort,ph in registration['protocols'].items():
        out=OUT/cohort;assert sha(out/'protocol.json')==ph
        cases=pd.read_csv(out/'primary_cases.csv');expected=set(map(tuple,cases[KEY].to_numpy()))
        main_data=pd.read_csv(parent/cohort/'predictions_primary.csv')
        ref=main_data[main_data.model.isin(['chronos','timesfm'])&main_data.arm.eq('calendar')]
        assert len(ref)==len(cases)*2
        chunks=[ref]
        for model in ['chronos','timesfm']:
            run=json.loads((out/model/'run.json').read_text())
            assert run['protocol_sha256']==ph and run['predictions_sha256']==sha(out/model/'predictions.csv')
            d=pd.read_csv(out/model/'predictions.csv')
            assert len(d)==len(cases)*10 and set(d.arm)==set(ARMS) and set(d.model)=={model}
            chunks.append(d)
        d=pd.concat(chunks,ignore_index=True)
        assert len(d)==len(cases)*22 and not d.duplicated(KEY+['model','arm']).any()
        for _,g in d.groupby(['model','arm']):assert set(map(tuple,g[KEY].to_numpy()))==expected
        assert np.isfinite(d[['actual','prediction','mase_scale']]).all().all()
        d.to_csv(out/'predictions_compared.csv',index=False)
        d['MAE_GWh']=abs(d.prediction-d.actual);d['MASE']=d.MAE_GWh/d.mase_scale
        cell,family,macro=aggregate(d,['MAE_GWh','MASE'])
        cell.to_csv(out/'metrics_state_year.csv',index=False)
        family.to_csv(out/'metrics_festival.csv',index=False)
        macro.to_csv(out/'metrics_balanced.csv',index=False)
        paired=[]
        for arm,reference in analysis['contrasts']:
            key=['family','model','state','year','horizon']
            a=cell[cell.arm.eq(arm)].merge(cell[cell.arm.eq(reference)],on=key,suffixes=('_arm','_reference'),validate='one_to_one')
            a['arm']=arm;a['reference']=reference;a['MASE_change']=a.MASE_arm-a.MASE_reference
            paired.append(a[key+['arm','reference','MASE_change']])
        paired=pd.concat(paired,ignore_index=True);paired.to_csv(out/'contrasts_state_year.csv',index=False)
        y=paired.groupby(['family','model','arm','reference','year','horizon']).MASE_change.mean().reset_index()
        y.to_csv(out/'contrasts_year.csv',index=False)
        f=y.groupby(['family','model','arm','reference','horizon']).MASE_change.mean().reset_index()
        f.to_csv(out/'contrasts_festival.csv',index=False)
        f.groupby(['model','arm','reference','horizon']).MASE_change.mean().reset_index().to_csv(out/'contrasts_balanced.csv',index=False)
        q=d[[f'q_{100*k:03d}' for k in range(1,10)]].to_numpy();assert np.isfinite(q).all()
        actual=d.actual.to_numpy();scale=d.mase_scale.to_numpy();r=actual[:,None]-q;tau=np.arange(1,10)/10
        d['scaled_mean_pinball']=np.maximum(tau*r,(tau-1)*r).mean(axis=1)/scale
        lo,med,hi=q[:,0],q[:,4],q[:,8];invalid=lo>hi
        intervalscore=hi-lo+10*np.maximum(lo-actual,0)+10*np.maximum(actual-hi,0)
        d['invalid80']=invalid;d['common_crossings']=(np.diff(q,axis=1)<0).sum(axis=1)
        d['coverage80']=np.where(invalid,np.nan,((lo<=actual)&(actual<=hi)).astype(float))
        d['scaled_width80']=np.where(invalid,np.nan,hi-lo)/scale
        d['scaled_WIS80_median']=np.where(invalid,np.nan,(.5*abs(actual-med)+.1*intervalscore)/1.5)/scale
        fields=['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']
        qc,qf,qm=aggregate(d,fields)
        for (model,arm,h),bad in d.groupby(['model','arm','horizon']).invalid80.any().items():
            if bad:
                for table in [qc,qf,qm]:table.loc[table.model.eq(model)&table.arm.eq(arm)&table.horizon.eq(h),fields[1:]]=np.nan
        d.to_csv(out/'native_uncertainty_cases.csv',index=False)
        qc.to_csv(out/'native_uncertainty_state_year.csv',index=False)
        qf.to_csv(out/'native_uncertainty_festival.csv',index=False)
        qm.to_csv(out/'native_uncertainty_balanced.csv',index=False)
        lines=['# Closest calendar-encoding daily adaptations — '+cohort,'',
            'Exploratory historical evaluation. All10newencodings and unchanged13channel maincalendar reference, identical cases. Primary method: context conditional means from Kreusel etal.; daily hour omitted, namedfestivalH and logged globalfallback are explicit adaptations. No exact hourlyexperiment/causalencoding/clean-test claim.','']
        for h in [1,7,14]:
            table=macro[macro.horizon.eq(h)].pivot(index='arm',columns='model',values='MASE').reindex(ARMS+['calendar'])
            lines += [f'## Lead {h}','',markdown(table.round(5).reset_index()),'']
        lines += ['Nativequantiles unchanged; native80coverage accompanies width/pinball/WIS in CSVtables. TEweekday/TEsunday/TEholiday/TEjoint/zero1share1channel; ordinal andTEseparate use2. Comparing13calendar withpureencodings changesdimensions/information. Every support/unseencategory/failure retained; no chosenfuturearm. Nativeintervals are not calibrated. Twoeventyears/source/proxy/rights/amendment/human/confirmation limits unchanged.']
        (out/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n')
        summaries[cohort]=dict(new_rows=len(cases)*20,reused_calendar_rows=len(ref),compared_rows=len(d),invalid80=int(invalid.sum()),
            common_crossing_pairs=int(d.common_crossings.sum()),predictions_sha256=sha(out/'predictions_compared.csv'),parent_predictions_sha256=sha(parent/cohort/'predictions_primary.csv'))
    assert sum(r['new_rows'] for r in summaries.values())==registration['planned_rows']
    dump(OUT/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),cohorts=summaries,analysis_registration_sha256=sha(OUT/'analysis_registration.json')))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze'])
    register() if p.parse_args().action=='register' else main()
