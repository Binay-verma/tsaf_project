"""Finish document-aligned window and weekday-placebo controls, without retuning."""
import argparse,json
from datetime import datetime,timezone
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha,dump,KEY,FAMILIES
from breadth_study import frames as old_frames,ARMS,MODELS
from calendar_semantics_study_v2 import frames as true_frames,OUT as CORRECTION
from calendar_encoding_study import ARMS as ENCODINGS

OUT=ROOT/'results/calendar_recenter_v1'


def aligned_frames(index,state):
    result={**old_frames(index,state),**true_frames(index,state)}
    fake=pd.read_csv(OUT/'placebo_anchors.csv',parse_dates=['date'])
    for kind in ['day','window']:
        columns={}
        for family in FAMILIES:
            roots=fake[fake.state.eq(state)&fake.family.eq(family)].date
            active=roots if kind=='day' else [d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))]
            columns[f'{family}_{kind}']=index.isin(active).astype(float)
        result['placebo_'+kind+'5']=pd.concat([result['calendar'],pd.DataFrame(columns,index=index)],axis=1)
    return {arm:result[arm] for arm in ARMS}


def prepare():
    if OUT.exists():raise FileExistsError('Preserve prior recenter protocol')
    OUT.mkdir();fake=pd.read_csv(ROOT/'results/festival_features_v1/placebo_anchors.csv')
    hit=fake.state.eq('Karnataka')&fake.year.eq(2025)&fake.family.eq('Dussehra')
    assert hit.sum()==1 and fake.loc[hit,'date'].iloc[0]=='2025-11-06' and fake.loc[hit,'shift_days'].iloc[0]==35
    fake.loc[hit,'date']='2025-11-05';fake.loc[hit,'original_date']='2025-10-01';fake.to_csv(OUT/'placebo_anchors.csv',index=False)
    true=pd.read_csv(CORRECTION/'anchors_2022_2025.csv',parse_dates=['date'])
    for r in fake.itertuples():
        assert (pd.Timestamp(r.date)-pd.Timestamp(r.original_date)).days==r.shift_days and r.shift_days%7==0
        roots=true[true.state.eq(r.state)&true.year.eq(r.year)].date
        assert all(abs((pd.Timestamp(r.date)-root).days)>6 for root in roots)
    parent=ROOT/'results/feature_breadth_v1/event_window';original=pd.read_csv(parent/'primary_cases.csv')
    removed=original.state.eq('Karnataka')&original.year.eq(2025)&original.family.eq('Dussehra')&original.date.eq('2025-10-05')
    assert removed.sum()==3
    added=original[removed].copy();added['date']='2025-09-28';added['origin']=[str((pd.Timestamp('2025-09-28')-pd.Timedelta(days=int(h)-1)).date()) for h in added.horizon]
    recentered=pd.concat([original[~removed],added]).sort_values(KEY);assert len(recentered)==528 and not recentered.duplicated(KEY).any()
    recentered.to_csv(OUT/'event_cases_recentered.csv',index=False);added.to_csv(OUT/'added_cases.csv',index=False);original[removed].to_csv(OUT/'removed_cases.csv',index=False)
    subsets={}
    for cohort in ['event_window','ordinary']:
        c=recentered if cohort=='event_window' else pd.read_csv(ROOT/'results/feature_breadth_v1/ordinary/primary_cases.csv')
        c=c[c.state.eq('Karnataka')&c.year.eq(2025)&c.date.ge('2025-09-01')]
        if cohort=='event_window':c=c[~c.date.eq('2025-09-28')]
        assert len(c)==(45 if cohort=='event_window' else 12);subsets[cohort]=c
    groups={'old_added':('breadth','original',added,ARMS),'aligned_added':('breadth','aligned',added,ARMS),
        'aligned_placebo_event':('breadth','aligned',subsets['event_window'],['placebo_day5','placebo_window5']),
        'aligned_placebo_ordinary':('breadth','aligned',subsets['ordinary'],['placebo_day5','placebo_window5']),
        'old_encoding_added':('encoding','original',added,ENCODINGS),'aligned_encoding_added':('encoding','aligned',added,ENCODINGS)}
    paths=['src/calendar_recenter_study.py','src/test_calendar_recenter_study.py','src/breadth_model_engine_v1.py','src/encoding_model_engine_v1.py','src/semantics_encoding_engine_v2.py',
        'src/calendar_semantics_study_v2.py','src/calendar_encoding_study.py','src/festival_feature_design.py','src/breadth_study.py','src/pooled_festival_experiment.py','src/robust_baselines.py','src/forecasting.py',
        'data/external/latest_state_energy_GWh.csv','results/calendar_semantics_v2/anchors_2022_2025.csv','results/festival_features_v1/anchors_2022_2025.csv','results/festival_features_v1/placebo_anchors.csv',
        'results/calendar_recenter_v1/placebo_anchors.csv','review/used_calendar_v4/all58_named_family_review.csv','results/strong_refit_v1/selected.csv','results/stable_tree_refit_v2/selected.csv',
        'results/strong_refit_v1/protocol.json','results/stable_tree_refit_v2/protocol.json']
    protocols={};rows=0
    for name,(kind,version,cases,arms) in groups.items():
        out=OUT/name;out.mkdir()
        base=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/event_window/protocol.json'
        p=json.loads(base.read_text())
        for f in ['primary_cases.csv','window_cases.csv']:cases.to_csv(out/f,index=False)
        models=MODELS if kind=='breadth' else ['chronos','timesfm'];rows+=len(cases)*len(arms)*len(models)
        p.update(created_utc=datetime.now(timezone.utc).isoformat(),experiment=OUT.name+'/'+name,kind=kind,calendar_version=version,
            status='Exploratory source-defined recenteredwindow/weekdayplacebo amendment; fixedbefore these newoutputs. Same-case trueflag-only sensitivity remains a separate completed/queued v2experiment.',
            cases='Corrected eventpanel replaces only3Karnataka2025Dussehra5Octobercases with3cases28September. Complete affectedwindow now28September–4October around notification1October. Same528casecount, but datesdiffer; do not attribute oldcohort aggregatechanges only tofeatures. Originalfeature baseline also predicts added28Septembercases for a matched correctedcohort.',
            controls='Originalplaceboshift35days retained, moving onlyKarnataka2025Dussehraplacebo6November→5November, preserving correctedoriginalweekday and truewindowseparation. No seedsearch or error-selected shift. Full8breadth/10purearms retained.',
            reuse='Compose full corrected528event/216ordinary matrices from unchangedoriginalworkers, v2trueflag/encodingworkers, and these source-definedadded/placebo rows. Verify source/input/date/parameter/prediction hashes. Originalfeature view uses same correctedcohort with new3case originalfeature forecasts. No re-score of originalfuturefreeze.',
            selection='Exactly unchanged past-selected parameters, fitting/weight/model/dtype/seed/batch/threads. No new hyperparameter/event/embedding/fallback/calibration choice from scores.',
            arms=arms,models=models,regression_extra_arms=[],cases_per_arm=len(cases),expected_tasks=len(cases[['state','origin']].drop_duplicates()),batch=16,threads=2,
            metrics='Same hierarchical MAE/MASE and common9native quantile pinball/80coverage/width/WIS. Report matched originalfeatures versusalignedfeatures on identicalcorrectedcohort, and separately document3datecompositiondifference. Allleads/arms/negativefindings. No rowindependencepvalues, universal or causalclaim.',
            limits='Annual-as-issued document alignment, not final amendments/observance truth. One nameddate mismatch corrected; Maharashtra2022GudiPadwa retained with explicit documentgap, two nationalmain exceptions retained. Mirrors/rights/vintages/human/untouched confirmation remain open.',
            input_hashes={f:sha(ROOT/f) for f in paths},design_hashes={f:sha(out/f) for f in ['primary_cases.csv','window_cases.csv']})
        dump(out/'protocol.json',p);protocols[name]=sha(out/'protocol.json')
    assert rows==1092
    dump(OUT/'registration.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),protocols=protocols,new_forecasts=1092,unchanged_original_cases_count=525,removed_cases=3,added_cases=3,
        corrected_case_count=528,ordinary_cases=216,decision='Document-definedcenter and fixedweekdayplacebo correction, not selectedbyerrors; originalv2same-case flag sensitivity preserved.'))


def run(group,worker):
    reg=json.loads((OUT/'registration.json').read_text());out=OUT/group;p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==reg['protocols'][group] and worker in p['models']
    if p['kind']=='encoding':
        if p['calendar_version']=='original':import encoding_model_engine_v1 as engine
        else:import semantics_encoding_engine_v2 as engine
        engine.OUT=out;engine.ARMS=p['arms'];engine.foundation(worker)
    else:
        import breadth_model_engine_v1 as engine
        engine.OUT=out;engine.ARMS=p['arms'];engine.EXTRA=[];engine.frames=old_frames if p['calendar_version']=='original' else aligned_frames
        if worker in ['chronos','timesfm']:engine.foundation(worker)
        elif worker=='sarimax':engine.sarimax()
        else:engine.regression(worker)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare',*MODELS]);p.add_argument('--group');a=p.parse_args();prepare() if a.action=='prepare' else run(a.group,a.action)
