"""Daily adaptations of the closest calendar-encoding study, fixed before outputs."""
import argparse,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from forecasting import ROOT,causal_fill
from festival_feature_design import sha,dump
from festival_feature_experiment import ledger_bound

OUT=ROOT/'results/calendar_encoding_v1'
NAMES={'history':[],'zero1':['zero'],
    'ordinal':['weekday','holiday'],
    'onehot':[f'dow_{j}' for j in range(7)]+['holiday'],
    'cyclic':['weekday_sin','weekday_cos','holiday'],
    'te_weekday':['weekday_target_mean'],
    'te_sunday':['mapped_weekday_target_mean'],
    'te_holiday':['holiday_daytype_target_mean'],
    'te_joint':['weekday_holiday_target_mean'],
    'te_separate':['weekday_target_mean','holiday_target_mean']}
ARMS=list(NAMES)


def feature_names(arm):return NAMES[arm]


def encoded_input(observed,state,arm,origin):
    dates=pd.date_range(origin-pd.Timedelta(days=730),periods=744)
    ledger_bound(dates)
    training=observed.reindex(dates[:730])
    good=training.notna().to_numpy()&training.gt(0).to_numpy()
    labels=training.to_numpy()[good]
    assert len(labels)>=365 and training.index[good].max()<origin
    target=causal_fill(observed).reindex(dates[:730]).to_numpy(dtype=np.float32)
    ledger=pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv',parse_dates=['date'])
    holiday=dates.isin(ledger[ledger.state.eq(state)].date).astype(int)
    weekday=dates.dayofweek.to_numpy()
    diagnostics=dict(recorded_context_labels=int(good.sum()),max_encoding_label=str(training.index[good].max().date()),
        category_tables=[],future_unseen_category_entries=0)
    def encode(codes):
        context=codes[:730][good]
        means={int(c):float(np.mean(labels[context==c])) for c in np.unique(context)}
        support={str(int(c)):int(np.sum(context==c)) for c in np.unique(context)}
        diagnostics['category_tables'].append(dict(means={str(k):v for k,v in means.items()},support=support))
        diagnostics['future_unseen_category_entries']+=sum(int(c) not in means for c in codes[730:])
        return np.asarray([means.get(int(c),float(np.mean(labels))) for c in codes])
    if arm=='history':columns=[]
    elif arm=='zero1':columns=[np.zeros(744)]
    elif arm=='ordinal':columns=[weekday,holiday]
    elif arm=='onehot':columns=[(weekday==j).astype(float) for j in range(7)]+[holiday]
    elif arm=='cyclic':columns=[np.sin(2*np.pi*weekday/7),np.cos(2*np.pi*weekday/7),holiday]
    elif arm=='te_weekday':columns=[encode(weekday)]
    elif arm=='te_sunday':columns=[encode(np.where(holiday,6,weekday))]
    elif arm=='te_holiday':columns=[encode(np.where(holiday,7,weekday))]
    elif arm=='te_joint':columns=[encode(weekday+7*holiday)]
    elif arm=='te_separate':columns=[encode(weekday),encode(holiday)]
    else:raise ValueError(arm)
    cov=np.asarray(columns,dtype=np.float32).reshape(len(columns),744)
    assert target.shape==(730,) and np.isfinite(target).all() and np.isfinite(cov).all()
    assert cov.shape[0]==len(feature_names(arm))
    return target,cov,diagnostics


def prepare():
    if OUT.exists():raise FileExistsError('Preserve existing encoding protocol/results')
    OUT.mkdir()
    files=['src/calendar_encoding_study.py','src/encoding_model_engine_v1.py','src/test_calendar_encoding_study.py',
        'src/forecasting.py','src/festival_feature_experiment.py','data/external/latest_state_energy_GWh.csv',
        'results/festival_features_v1/anchors_2022_2025.csv',
        'results/mechanism_controls_v1/chronos_download.json','results/second_model_audit_v1/weight_download.json']
    protocols={}
    for cohort in ['event_window','ordinary']:
        out=OUT/cohort;out.mkdir()
        parent=ROOT/f'results/feature_breadth_v1/{cohort}'
        for f in ['primary_cases.csv','window_cases.csv']:(out/f).write_bytes((parent/f).read_bytes())
        cases=pd.read_csv(out/'primary_cases.csv')
        p=dict(created_utc=datetime.now(timezone.utc).isoformat(),experiment=f'{OUT.name}/{cohort}',
            status='Exploratory closest-method daily adaptation, frozen before any new encoding inference after earlier historical/local outcomes. No clean-test or exact hourly paper replication claim.',
            literature='Kreusel etal., arXiv:2610.13676v1, Section3.1/Table1/AppendixA.1.1, primary fullHTML reread30October2026. Arithmetic context conditional means; no new method.',
            adaptation='Daily data omit hour. Seven published encoding families: ordinal weekday+H, onehot weekday+H, cyclic weekday+H, target-mean Sunday mapping, separate holiday daytype, jointweekday/H, separateweekday/H channels. Add history, zero1 and weekday-only target-mean controls. H=any frozen state-scoped named festival anchor, not every public holiday. No13annual-calendar channels retained in these pureencodings.',
            rare_categories='Paper assumes each horizon category appears in context. Daily sparse events violate this; fix unseen-category fallback to global mean of positive recorded context labels, and log every support/table/futurefallback count. No error-based smoothing/fallback selection.',
            target_encoding='For each origin, fit category mean from positive recorded labels in preceding730calendar days only. Map each context/future calendar category to that table. Own past targets may contribute because they are already available in model context; no forecast-period target contributes. Model past target may use causal fill; encoding labels are never imputed.',
            controls='Four single-channel target encodings compare with weekday-only and zero1 at identical1channel. Separate target means and ordinal use2channels. Conventional2/8/3channel comparisons versus13calendar/18eventmainarms change dimensions and information, explicitly not causal encoding-only identification.',
            arms=ARMS,feature_names=NAMES,models=['chronos','timesfm'],batch=16,threads=2,seed=42,context=730,horizon=14,
            expected_tasks=len(cases[['state','origin']].drop_duplicates()),cases_per_arm=len(cases),
            weights='Exactly pinned parent weights/no fine-tuning, same source/context/tasks; fresh nativepoint/quantile inference for all10arms. Solo-batch and future-target perturbation checks retained.',
            metrics='Identical source/scales and state/year/family hierarchy as feature_breadth_v1. Score all3individualleads and all8published/control encodings plushistory/zero. Native common9quantiles/80coverage/width/pinball/WIS, crossings retained. No favourable-arm selection; historical results remain exploratory.',
            execution='Queued after corresponding foundation breadth lane finishes to respect CPU quota. Actual started/completed metadata, not assumed background continuation. No local model fits here; local comparators in the complete matched breadth panel.',
            input_hashes={f:sha(ROOT/f) for f in files},design_hashes={f:sha(out/f) for f in ['primary_cases.csv','window_cases.csv']})
        dump(out/'protocol.json',p);protocols[cohort]=sha(out/'protocol.json')
    dump(OUT/'registration.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),protocols=protocols,
        arms=ARMS,models=['chronos','timesfm'],planned_rows=2*10*(528+216),
        main_single_channel_contrast=['te_sunday','te_holiday','te_joint','te_weekday','zero1'],
        notes='Rules fixed before new encoding outputs, original breadth frozen unchanged. Puredaily adaptations, no universal model/novelty or independent-source claim.'))
    print('FROZEN2models x10encodings x744cases =14880forecasts; queuednotstarted')


def run(cohort,worker):
    import encoding_model_engine_v1 as engine
    reg=json.loads((OUT/'registration.json').read_text())
    out=OUT/cohort;assert sha(out/'protocol.json')==reg['protocols'][cohort]
    engine.OUT=out;engine.ARMS=ARMS;engine.foundation(worker)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','chronos','timesfm'])
    p.add_argument('--cohort',choices=['event_window','ordinary'],default='event_window');a=p.parse_args()
    prepare() if a.action=='prepare' else run(a.cohort,a.action)
