"""Document-aligned date correction; old ledgers and experiments stay immutable."""
import argparse,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from forecasting import ROOT,causal_fill
from festival_feature_design import sha,dump,KEY,FAMILIES
from breadth_study import frames as original_frames,MODELS
from calendar_encoding_study import feature_names

OUT=ROOT/'results/calendar_semantics_v1'
ARMS=['calendar','day5','pooled_day5','window5','pooled_window5']
ENCODINGS=['ordinal','onehot','cyclic','te_sunday','te_holiday','te_joint','te_separate']


def frames(index,state):
    result=original_frames(index,state)
    true=pd.read_csv(OUT/'anchors_2022_2025.csv',parse_dates=['date'])
    for kind in ['day','window']:
        event={}
        for family in FAMILIES:
            roots=true[true.state.eq(state)&true.family.eq(family)].date
            dates=roots if kind=='day' else [d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))]
            event[f'{family}_{kind}']=index.isin(dates).astype(float)
        typed=pd.DataFrame(event,index=index);pooled=pd.DataFrame({'pooled_'+kind:typed.any(axis=1).astype(float)},index=index)
        for j in range(1,5):pooled['padding_'+str(j)]=0.
        result[kind+'5']=pd.concat([result['calendar'],typed],axis=1)
        result['pooled_'+kind+'5']=pd.concat([result['calendar'],pooled],axis=1)
    return {arm:result[arm] for arm in ARMS}


def encoded_input(observed,state,arm,origin):
    dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
    assert dates.min()>=pd.Timestamp('2022-01-01') and dates.max()<=pd.Timestamp('2025-12-31')
    training=observed.reindex(dates[:730]);good=training.notna().to_numpy()&training.gt(0).to_numpy();labels=training.to_numpy()[good]
    assert len(labels)>=365 and training.index[good].max()<origin
    target=causal_fill(observed).reindex(dates[:730]).to_numpy(dtype=np.float32)
    ledger=pd.read_csv(OUT/'anchors_2022_2025.csv',parse_dates=['date'])
    holiday=dates.isin(ledger[ledger.state.eq(state)].date).astype(int);weekday=dates.dayofweek.to_numpy()
    diagnostics=dict(recorded_context_labels=int(good.sum()),max_encoding_label=str(training.index[good].max().date()),category_tables=[],future_unseen_category_entries=0)
    def encode(codes):
        context=codes[:730][good];means={int(c):float(np.mean(labels[context==c])) for c in np.unique(context)}
        support={str(int(c)):int(np.sum(context==c)) for c in np.unique(context)}
        diagnostics['category_tables'].append(dict(means={str(k):v for k,v in means.items()},support=support))
        diagnostics['future_unseen_category_entries']+=sum(int(c) not in means for c in codes[730:])
        return np.asarray([means.get(int(c),float(np.mean(labels))) for c in codes])
    if arm=='ordinal':columns=[weekday,holiday]
    elif arm=='onehot':columns=[(weekday==j).astype(float) for j in range(7)]+[holiday]
    elif arm=='cyclic':columns=[np.sin(2*np.pi*weekday/7),np.cos(2*np.pi*weekday/7),holiday]
    elif arm=='te_sunday':columns=[encode(np.where(holiday,6,weekday))]
    elif arm=='te_holiday':columns=[encode(np.where(holiday,7,weekday))]
    elif arm=='te_joint':columns=[encode(weekday+7*holiday)]
    elif arm=='te_separate':columns=[encode(weekday),encode(holiday)]
    else:raise ValueError(arm)
    cov=np.asarray(columns,dtype=np.float32).reshape(len(columns),744)
    assert np.isfinite(target).all() and np.isfinite(cov).all() and len(cov)==len(feature_names(arm))
    return target,cov,diagnostics


def prepare():
    if OUT.exists():raise FileExistsError('Preserve prior correction protocol/results')
    OUT.mkdir();ledger=pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv')
    hit=ledger.state.eq('Karnataka')&ledger.year.eq(2025)&ledger.family.eq('Dussehra')
    assert hit.sum()==1 and ledger.loc[hit,'date'].iloc[0]=='2025-10-02'
    ledger.loc[hit,'date']='2025-10-01';ledger.loc[hit,'label']='Mahanavami/Ayudhapooja, Vijayadasami'
    ledger.loc[hit,'source']='review/used_calendar_v3/KA2025_indexed_mirror.pdf'
    ledger.loc[hit,'evidence']='Page1 visually checked: DPAR16HHL2024 dated21Nov2024; indexedmirror with unverified hostingaffiliation; no finalamendment certification'
    ledger.to_csv(OUT/'anchors_2022_2025.csv',index=False)
    paths=['src/calendar_semantics_study.py','src/semantics_encoding_engine_v1.py','src/test_calendar_semantics_study.py',
        'src/breadth_model_engine_v1.py','src/calendar_encoding_study.py','src/forecasting.py','src/robust_baselines.py',
        'src/festival_feature_design.py','src/pooled_festival_experiment.py','src/breadth_study.py',
        'results/calendar_semantics_v1/anchors_2022_2025.csv','results/festival_features_v1/anchors_2022_2025.csv',
        'results/festival_features_v1/placebo_anchors.csv','data/external/latest_state_energy_GWh.csv',
        'results/strong_refit_v1/selected.csv','results/stable_tree_refit_v2/selected.csv',
        'results/strong_refit_v1/protocol.json','results/stable_tree_refit_v2/protocol.json',
        'review/used_calendar_v3/KA2025_indexed_mirror.pdf','review/used_calendar_v3/all58_used_anchor_review.csv']
    protocols={}
    for kind in ['breadth','encoding']:
        for cohort in ['event_window','ordinary']:
            out=OUT/kind/cohort;out.mkdir(parents=True)
            parent=ROOT/f'results/{"feature_breadth_v1" if kind=="breadth" else "calendar_encoding_v1"}/{cohort}'
            allcases=pd.read_csv(parent/'primary_cases.csv');cases=allcases[allcases.state.eq('Karnataka')&allcases.year.eq(2025)&allcases.date.ge('2025-09-01')]
            assert len(cases)==(48 if cohort=='event_window' else 12)
            for name in ['primary_cases.csv','window_cases.csv']:cases.to_csv(out/name,index=False)
            p=json.loads((parent/'protocol.json').read_text());arms=ARMS if kind=='breadth' else ENCODINGS
            p.update(created_utc=datetime.now(timezone.utc).isoformat(),experiment=f'{OUT.name}/{kind}/{cohort}',
                status='Exploratory document-aligned correction fixed before correctedoutcomes. Preserve original known-mismatch results, no result-driven date selection.',
                correction='Exactly one namedanchor: Karnataka2025Dussehra2October to notificationVijayadasami1October. Distinct religiousobservance/officeholiday definitions; mirrorhost/authenticity and finalamendments require review. No claim of final corrected groundtruth.',
                cases='Keep original case/family labels and targetdates. Recompute all Karnataka2025 targetdates>=1September for the fixedarms. All other rows reuse original forecasts only after source/protocol and completeinput equality checks. This is feature-date sensitivity on SAME oldwindow sample, not a newly centered completewindow cohort.',
                reuse='Outside this subset, no source target/covariate changes in730+14foundation blocks, nor localtraining/query blocks or preyearSARIMAXstate-updateexog. Purehistory/zero1/weekdayTE and breadthcalendar/zero/placebos unaffected. Copy unchanged parent predictions with exacthash provenance; do not call them fresh inference.',
                selection='No search/refallback/recalibration. Same weights/context/batch16/2threads/seed42, unchanged past-selected localparameters. Retain five breadtharms including repeatedcalendar as a source/numerical check; seven H-dependent pureencodings.',
                arms=arms,regression_extra_arms=[],cases_per_arm=len(cases),expected_tasks=len(cases[['state','origin']].drop_duplicates()),batch=16,threads=2,
                metrics='Same original hierarchical MAE/MASE and nativecommon9quantile/80coverage/width/WIS, allleads/arms. Report paired corrected-minus-original on fixedsubset AND fullreusedmatrix; no choosing date fromerrors, no causal/effectiveness/finalamendmentclaim.',
                input_hashes={name:sha(ROOT/name) for name in paths},design_hashes={name:sha(out/name) for name in ['primary_cases.csv','window_cases.csv']},parent_protocol_sha256=sha(parent/'protocol.json'),parent_cases_sha256=sha(parent/'primary_cases.csv'))
            dump(out/'protocol.json',p);protocols[f'{kind}/{cohort}']=sha(out/'protocol.json')
    dump(OUT/'registration.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),protocols=protocols,new_breadth_rows=1800,new_encoding_rows=840,new_rows=2640,old_forecasts_unchanged=True,
        decision='Source/date-only correction following visualgovernment-document review; no correctedscore inspected. Originalprimarycohort/windowlabels stayfixed; boundedoldwindow limitation explicit.'))


def run(kind,cohort,worker):
    reg=json.loads((OUT/'registration.json').read_text());out=OUT/kind/cohort
    assert sha(out/'protocol.json')==reg['protocols'][kind+'/'+cohort]
    if kind=='encoding':
        import semantics_encoding_engine_v1 as engine
        engine.OUT=out;engine.ARMS=ENCODINGS;engine.foundation(worker)
    else:
        import breadth_model_engine_v1 as engine
        engine.OUT=out;engine.ARMS=ARMS;engine.EXTRA=[];engine.frames=frames
        if worker in ['chronos','timesfm']:engine.foundation(worker)
        elif worker=='sarimax':engine.sarimax()
        else:engine.regression(worker)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare',*MODELS]);p.add_argument('--kind',choices=['breadth','encoding'],default='breadth');p.add_argument('--cohort',choices=['event_window','ordinary'],default='event_window');a=p.parse_args()
    prepare() if a.action=='prepare' else run(a.kind,a.cohort,a.action)
