"""Compose matched recentered panels from hashed originals and fixed additions."""
import argparse,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from calendar_recenter_study import ROOT,OUT,CORRECTION,MODELS
from festival_feature_design import KEY,sha,dump
from finalize_calendar_semantics import metrics
from finalize_breadth_study import aggregate
from report_multifestival import markdown


def register():
    path=OUT/'analysis_registration.json'
    if path.exists():raise FileExistsError('Preserve scoring registration')
    files=['src/finalize_calendar_recenter.py','src/finalize_calendar_semantics.py','src/finalize_breadth_study.py']
    dump(path,dict(created_utc=datetime.now(timezone.utc).isoformat(),source_hashes={f:sha(ROOT/f) for f in files},registration_sha256=sha(OUT/'registration.json'),
        policy='Fixedbefore newrecenteredaggregate scores. Completeoriginalfeature and alignedfeature views on identical528recentered/216ordinarycases. Allmodels/arms/leads retained; no selection by theseerrors.',
        metrics='Same registeredstate/year/family hierarchy, recordedlabels/preyearweeklyscale, MAE/MASE and common9nativequantile pinball/80coverage/width/WISmedian. Invalid80propagatesundefined, no crossingrepair or rowindependenceinference.',
        composition='Compare originalfeatures on recentered528cases versus originalfeatures on old528cases separately. This is3targetdates removed/added atsameleads, not an isolatedcalendarfeatureeffect.',
        reuse='Validate everyworker prediction/protocolhash, source/input contracts and exactcase sets. Trueflag/7Hencodings come from v2exceptremovedcases; addedrows/placebos from thisstudy; allother forecasts unchanged. Encodingview adds unchanged13calendar reference from composedbreadth onexactcases/weights.',
        limits='Document-aligned annual-as-issued sensitivity, not amendment-certified groundtruth. One remainingMH2022nameddate evidencegap/two sharedmainexceptions; no independenthuman/rights/firstvintage/untouchedclaim.'))


def read_worker(folder,model):
    run=json.loads((folder/model/'run.json').read_text());assert sha(folder/model/'predictions.csv')==run['predictions_sha256'] and sha(folder/'protocol.json')==run['protocol_sha256']
    return pd.read_csv(folder/model/'predictions.csv')


def tuples(d,fields=KEY):return set(map(tuple,d[fields].to_numpy()))


def replace(base,addition):
    key=KEY+['model','arm'];keys=tuples(addition,key)
    keep=[tuple(r) not in keys for r in base[key].to_numpy()]
    return pd.concat([base.loc[keep],addition],ignore_index=True)


def main(part):
    a=json.loads((OUT/'analysis_registration.json').read_text())
    for path,h in a['source_hashes'].items():assert sha(ROOT/path)==h
    assert sha(OUT/'registration.json')==a['registration_sha256']
    models=MODELS[:4] if part=='local' else MODELS
    groups=['old_added','aligned_added','aligned_placebo_event','aligned_placebo_ordinary']+([] if part=='local' else ['old_encoding_added','aligned_encoding_added'])
    # Require complete workers before creating any output directory.
    for group in groups:
        p=json.loads((OUT/group/'protocol.json').read_text())
        for model in p['models']:
            if part=='local' and model not in models:continue
            assert (OUT/group/model/'run.json').exists() and not (OUT/group/model/'failure.txt').exists(),(group,model)
    dest=OUT/('local_checkpoint' if part=='local' else 'analysis')
    if dest.exists():raise FileExistsError('Preserve prior complete/interrupted analysis')
    dest.mkdir();summaries={}
    for kind in (['breadth'] if part=='local' else ['breadth','encoding']):
        active=models if kind=='breadth' else ['chronos','timesfm']
        for cohort in ['event_window','ordinary']:
            out=dest/kind/cohort;out.mkdir(parents=True);parent=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/{cohort}'
            cases=pd.read_csv(OUT/'event_cases_recentered.csv') if cohort=='event_window' else pd.read_csv(parent/'primary_cases.csv');expected=tuples(cases)
            chunks=[];oldchunks=[];provenance=[]
            for model in active:
                old=read_worker(parent,model);oldchunks.append(old);matched=old[[tuple(r) in expected for r in old[KEY].to_numpy()]].copy()
                added_group='old_added' if kind=='breadth' else 'old_encoding_added'
                aligned_group='aligned_added' if kind=='breadth' else 'aligned_encoding_added'
                if cohort=='event_window':matched=pd.concat([matched,read_worker(OUT/added_group,model)],ignore_index=True)
                arms=set(old.arm);assert len(matched)==len(cases)*len(arms)
                aligned=matched.copy();fresh=read_worker(CORRECTION/kind/cohort,model)
                if kind=='breadth':fresh=fresh[~fresh.arm.eq('calendar')]
                fresh=fresh[[tuple(r) in expected for r in fresh[KEY].to_numpy()]];aligned=replace(aligned,fresh)
                if cohort=='event_window':aligned=replace(aligned,read_worker(OUT/aligned_group,model))
                if kind=='breadth':aligned=replace(aligned,read_worker(OUT/('aligned_placebo_event' if cohort=='event_window' else 'aligned_placebo_ordinary'),model))
                for table in [matched,aligned]:
                    assert len(table)==len(cases)*len(arms) and not table.duplicated(KEY+['model','arm']).any()
                    for _,g in table.groupby('arm'):assert tuples(g)==expected
                provenance.append(dict(model=model,parent_predictions_sha256=sha(parent/model/'predictions.csv'),v2_predictions_sha256=sha(CORRECTION/kind/cohort/model/'predictions.csv'),cases_per_arm=len(cases),arms=len(arms)))
                matched['version']='original';aligned['version']='document_aligned';chunks.extend([matched,aligned])
            if kind=='encoding':
                calendar=pd.read_csv(dest/'breadth'/cohort/'predictions_compared.csv');calendar=calendar[calendar.model.isin(active)&calendar.arm.eq('calendar')];assert len(calendar)==len(cases)*4;chunks.append(calendar)
                oldcalendar=pd.concat([read_worker(ROOT/f'results/feature_breadth_v1/{cohort}',m) for m in active]);oldchunks.append(oldcalendar[oldcalendar.arm.eq('calendar')])
            d=pd.concat(chunks,ignore_index=True);m=metrics(d,out)
            baseline=pd.concat(oldchunks,ignore_index=True);baseline['MAE_GWh']=abs(baseline.prediction-baseline.actual);baseline['MASE']=baseline.MAE_GWh/baseline.mase_scale
            _,_,oldmetrics=aggregate(baseline,['MAE_GWh','MASE']);oldmetrics.to_csv(out/'original_cohort_metrics.csv',index=False)
            join=['model','arm','horizon'];composition=m[m.version.eq('original')].merge(oldmetrics,on=join,suffixes=('_recentered','_oldcohort'),validate='one_to_one')
            composition['MASE_composition_change']=composition.MASE_recentered-composition.MASE_oldcohort
            composition[join+['MASE_composition_change']].to_csv(out/'composition_changes.csv',index=False)
            dump(out/'provenance.json',dict(workers=provenance,source_registration_sha256=sha(OUT/'registration.json'),case_sha256=sha(OUT/'event_cases_recentered.csv') if cohort=='event_window' else sha(parent/'primary_cases.csv'),calendar_reference='Reuse exactcomposed13calendar breadthforecasts forencoding comparisons' if kind=='encoding' else None))
            lines=['# Recentered document-aligned panel: '+kind+'/'+cohort,'','Same correctedcases fororiginal/alignedfeature views;528completeeventcases/216ordinarycases. Only3KarnatakaDussehratarget/leadcases move5October→28September; actualnewwindow28September–4October. Placeboshift remains+35days oncorrectweekday. No score-selecteddates/settings; allresults exploratory, not finalamendments or independenthuman confirmation.','']
            for h in [1,7,14]:
                table=m[m.version.eq('document_aligned')&m.horizon.eq(h)].pivot(index='arm',columns='model',values='MASE')
                lines += [f'## Lead {h}: aligned-feature MASE','',markdown(table.round(5).reset_index()),'']
            lines += ['changes_balanced.csv is the matchedfeature contrast; composition_changes.csv is the separatedate-cohort change underoriginalfeatures. Do not conflate these effects or select a winning version. Fullsource/case/reuse/input/fit/probability audits required before conclusions. MH2022nameddate evidencegap, sharedmainexceptions, sourcevintages/reuse/human/futurelimitations remain.']
            (out/'REPORT.md').write_text('\n'.join(lines).rstrip()+'\n')
            summaries[kind+'/'+cohort]=dict(compared_view_rows=len(d),cases_per_arm=len(cases),predictions_sha256=sha(out/'predictions_compared.csv'))
    dump(dest/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),part=part,new_forecast_rows=648 if part=='local' else 1092,cohorts=summaries,analysis_registration_sha256=sha(OUT/'analysis_registration.json')))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze']);p.add_argument('--part',choices=['local','all'],default='all');a=p.parse_args();register() if a.action=='register' else main(a.part)
