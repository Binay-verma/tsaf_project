"""Output-directory-only recovery of prematurely started local analysis; methods unchanged.
Original source and partial files remain frozen; compare completed partial CSV hashes.
"""
import argparse,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from calendar_semantics_study_v2 import ROOT,OUT,ARMS,ENCODINGS,MODELS
from festival_feature_design import KEY,sha,dump
from finalize_breadth_study import aggregate
from report_multifestival import markdown


def register():
    path=OUT/'analysis_registration.json'
    if path.exists():raise FileExistsError('Preserve analysis registration')
    dump(path,dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),registration_sha256=sha(OUT/'registration.json'),
        policy='Registeredbefore correctedaggregateerrors. Same originalcase/windowlabels, allleads/arms, unchanged originalprotocols. No error-driven selection.',
        paired='Corrected-minus-original MASE at each identicalcase. Report subsetandcompleteoriginalmatrix with identicalstate/year/family hierarchy. No inference of independentdays, no refit/tuning basedonchange.',
        numerical_check='Repeatedcalendar point/nativecommonquantiles compared with exactparent using originalsolo tolerance rtol2e-4/atol1e-3. Originalcalendar predictions retained in fullmatrices; record allrepeatdifferences rather than claim byteequivalent inference.',
        reuse='Original worker hashes/protocols validated. Outside fixed60case subset and arms, no forecasts recomputed. Independent audit verifies unchanged data/covariates and train/update blocks; sources and hyperparameters unchanged.',
        probability='Same common9native quantiles; scaledmeanpinball,80coverage/scaledwidth/WISmedian. Anyinvalid80endpoint makes wholeassociatedinterval aggregate undefined. Never repair crossings.',
        limits='One document-aligned family/date change. Indexedmirror/firstpublication/amendmentchain unresolved. Same oldtargetdates, not complete newly centered eventwindows. Pureencodings use namedH rather than allpublicholidays. Historical/exploratory, not newuntouched confirmation.'))


def metrics(d,dest):
    d=d.copy();d['MAE_GWh']=abs(d.prediction-d.actual);d['MASE']=d.MAE_GWh/d.mase_scale
    cells=[];families=[];macros=[]
    for version,g in d.groupby('version'):
        c,f,m=aggregate(g,['MAE_GWh','MASE'])
        for table in [c,f,m]:table['version']=version
        cells.append(c);families.append(f);macros.append(m)
    c=pd.concat(cells);f=pd.concat(families);m=pd.concat(macros)
    c.to_csv(dest/'metrics_state_year.csv',index=False);f.to_csv(dest/'metrics_family.csv',index=False);m.to_csv(dest/'metrics_balanced.csv',index=False)
    join=['model','arm','horizon'];p=m[m.version.eq('document_aligned')].merge(m[m.version.eq('original')],on=join,suffixes=('_new','_old'),validate='one_to_one')
    p['MASE_change']=p.MASE_new-p.MASE_old;p[join+['MASE_change']].to_csv(dest/'changes_balanced.csv',index=False)
    d.to_csv(dest/'predictions_compared.csv',index=False)
    q=d[d.model.isin(['chronos','timesfm'])].copy()
    if len(q):
        values=q[[f'q_{100*k:03d}' for k in range(1,10)]].to_numpy();assert np.isfinite(values).all()
        y=q.actual.to_numpy();scale=q.mase_scale.to_numpy();r=y[:,None]-values;tau=np.arange(1,10)/10
        q['scaled_mean_pinball']=np.maximum(tau*r,(tau-1)*r).mean(axis=1)/scale
        lo,med,hi=values[:,0],values[:,4],values[:,8];invalid=lo>hi;q['invalid80']=invalid;q['common_crossings']=(np.diff(values,axis=1)<0).sum(axis=1)
        q['coverage80']=np.where(invalid,np.nan,((lo<=y)&(y<=hi)).astype(float));q['scaled_width80']=np.where(invalid,np.nan,hi-lo)/scale
        q['scaled_WIS80_median']=np.where(invalid,np.nan,(.5*abs(y-med)+.1*(hi-lo+10*np.maximum(lo-y,0)+10*np.maximum(y-hi,0)))/1.5)/scale
        fields=['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median'];tables=[]
        for version,g in q.groupby('version'):
            _,_,table=aggregate(g,fields);table['version']=version
            for (model,arm,h),bad in g.groupby(join).invalid80.any().items():
                if bad:table.loc[table.model.eq(model)&table.arm.eq(arm)&table.horizon.eq(h),fields[1:]]=np.nan
            tables.append(table)
        q.to_csv(dest/'native_uncertainty_cases.csv',index=False);pd.concat(tables).to_csv(dest/'native_uncertainty_balanced.csv',index=False)
    return m


def main(part):
    reg=json.loads((OUT/'analysis_registration.json').read_text());assert sha(ROOT/'src/finalize_calendar_semantics.py')==reg['source_sha256'] and sha(OUT/'registration.json')==reg['registration_sha256']
    dest=OUT/'local_checkpoint_recovery_v1'
    if dest.exists():raise FileExistsError('Preserve prior analysis')
    dest.mkdir();summaries={}
    for kind in (['breadth'] if part=='local' else ['breadth','encoding']):
        models=MODELS[:4] if part=='local' else MODELS if kind=='breadth' else ['chronos','timesfm']
        for cohort in ['event_window','ordinary']:
            out=dest/kind/cohort;out.mkdir(parents=True);newroot=OUT/kind/cohort;oldroot=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/{cohort}'
            p=json.loads((newroot/'protocol.json').read_text());assert sha(oldroot/'protocol.json')==p['parent_protocol_sha256'] and sha(oldroot/'primary_cases.csv')==p['parent_cases_sha256']
            subset=pd.read_csv(newroot/'primary_cases.csv');expected=set(map(tuple,subset[KEY].to_numpy()));chunks=[];repeats=[];provenance=[]
            for model in models:
                oldrun=json.loads((oldroot/model/'run.json').read_text());newrun=json.loads((newroot/model/'run.json').read_text())
                assert sha(oldroot/model/'predictions.csv')==oldrun['predictions_sha256'] and sha(newroot/model/'predictions.csv')==newrun['predictions_sha256']
                assert oldrun['protocol_sha256']==p['parent_protocol_sha256'] and newrun['protocol_sha256']==sha(newroot/'protocol.json')
                old=pd.read_csv(oldroot/model/'predictions.csv');new=pd.read_csv(newroot/model/'predictions.csv')
                assert len(new)==len(subset)*len(p['arms']) and set(new.arm)==set(p['arms'])
                for arm,g in new.groupby('arm'):assert set(map(tuple,g[KEY].to_numpy()))==expected
                pair=new.merge(old,on=KEY+['model','arm'],suffixes=('_new','_old'),validate='one_to_one');assert len(pair)==len(new)
                np.testing.assert_allclose(pair.actual_new,pair.actual_old,rtol=0,atol=1e-9);np.testing.assert_allclose(pair.mase_scale_new,pair.mase_scale_old,rtol=0,atol=1e-9)
                if kind=='breadth':
                    c=pair[pair.arm.eq('calendar')];cols=['prediction']+[f'q_{100*k:03d}' for k in range(1,10)] if model in ['chronos','timesfm'] else ['prediction']
                    for col in cols:np.testing.assert_allclose(c[col+'_new'],c[col+'_old'],rtol=2e-4,atol=1e-3)
                    repeats.append(dict(model=model,calendar_max_point_difference_GWh=float(abs(c.prediction_new-c.prediction_old).max())))
                pair['MASE_change']=(abs(pair.prediction_new-pair.actual_new)-abs(pair.prediction_old-pair.actual_old))/pair.mase_scale_old
                pair.to_csv(out/(model+'_subset_pairs.csv'),index=False)
                changed=new[~new.arm.eq('calendar')].copy();key=KEY+['model','arm'];remove=set(map(tuple,changed[key].to_numpy()))
                keep=np.array([tuple(r) not in remove for r in old[key].to_numpy()]);corrected=pd.concat([old[keep],changed],ignore_index=True)
                assert len(corrected)==len(old) and not corrected.duplicated(key).any()
                old['version']='original';corrected['version']='document_aligned';chunks.extend([old,corrected])
                provenance.append(dict(model=model,parent_prediction_sha256=sha(oldroot/model/'predictions.csv'),new_prediction_sha256=sha(newroot/model/'predictions.csv'),new_rows=len(new),replacement_rows=len(changed),reused_rows_per_corrected_view=int(keep.sum())))
            d=pd.concat(chunks,ignore_index=True);m=metrics(d,out)
            dump(out/'provenance.json',dict(workers=provenance,repeated_calendar=repeats,scope='Same complete originalcases; only60case subsetrecomputed. Not a newly centeredwindow cohort.'))
            lines=['# Document-aligned '+kind+' date sensitivity: '+cohort,'','Original fixedcases and allarms/leads retained. OnlyKarnataka2025Dussehra flag moves2October→notification1October; oldledger/results unchanged. No date/parameter chosen using scores. Completeparentmatrix uses exactunaffected forecasts with provenance. Not a complete new-centeredwindow cohort or finalamendment certification.','']
            changes=pd.read_csv(out/'changes_balanced.csv')
            for h in [1,7,14]:
                table=changes[changes.horizon.eq(h)].pivot(index='model',columns='arm',values='MASE_change')
                lines += [f'## Lead {h}: corrected minus original MASE','',markdown(table.round(7).reset_index()),'']
            (out/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n');summaries[kind+'/'+cohort]=dict(compared_view_rows=len(d),new_rows=sum(r['new_rows'] for r in provenance),predictions_sha256=sha(out/'predictions_compared.csv'))
    dump(dest/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),part=part,cohorts=summaries,analysis_registration_sha256=sha(OUT/'analysis_registration.json')))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze']);p.add_argument('--part',choices=['local','all'],default='all');a=p.parse_args();register() if a.action=='register' else main(a.part)
