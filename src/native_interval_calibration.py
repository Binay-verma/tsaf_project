"""Past-label-only interval expansion; immutable native and prospective parents."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
import traceback
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data
from festival_feature_design import sha, dump
from postweight_daily_panel import inputs
from festival_feature_experiment import scale

OUT = ROOT/'results/native_calibration_v1'
ANNEX = ROOT/'results/prospective_interval_20261030_v1'
PARENT = ROOT/'results/postweight_daily_v1'
ORIGINAL = ROOT/'results/prospective_20261030_v1'
ARMS = ['native', 'frozen_september', 'expanding_past']
KEY = ['configuration', 'state', 'origin', 'date', 'horizon']
GIT_FREEZE = 'cabd5982e1948652b9841d6c31a2380f6f314198'


def calibration_rows(archive, state, configuration, horizon, origin, arm):
    origin = pd.Timestamp(origin)
    d = archive[archive.state.eq(state) & archive.configuration.eq(configuration) & archive.horizon.eq(horizon)].copy()
    d = d[pd.to_datetime(d.date) < origin]
    if arm == 'frozen_september':
        d = d[pd.to_datetime(d.date) <= pd.Timestamp('2026-09-30')]
    elif arm != 'expanding_past':
        raise ValueError('Unknown calibration rule')
    d = d.sort_values('date')
    assert not d.duplicated('date').any()
    if len(d) < 16:
        raise ValueError('Fewer than16available past calibration labels; never borrow future labels')
    assert (pd.to_datetime(d.origin) < pd.to_datetime(d.date)+pd.Timedelta(days=1)).all()
    assert np.isfinite(d[['actual','q_100','q_900']]).all().all()
    assert d.q_100.le(d.q_900).all()
    return d


def adjustment(d, alpha=.2):
    scores = np.maximum(d.q_100.to_numpy()-d.actual.to_numpy(), d.actual.to_numpy()-d.q_900.to_numpy())
    n = len(scores); rank = math.ceil((n+1)*(1-alpha))
    if rank > n:
        raise ValueError('Finite-sample quantile is not finite at this calibration size')
    # A finite-sample order statistic, never interpolated or tuned on coverage.
    raw = float(np.sort(scores)[rank-1])
    return max(0., raw), rank, raw


def check_inputs():
    p = json.loads((OUT/'protocol.json').read_text())
    for name, expected in p['input_hashes'].items():
        assert sha(ROOT/name) == expected, name
    for name, expected in p['design_hashes'].items():
        assert sha(OUT/name) == expected, name
    return p


def prepare():
    if OUT.exists() or ANNEX.exists():
        raise FileExistsError('Preserve registered experiment/annex; version a new study')
    data = load_data('latest'); rows = []
    for state in ['Delhi','Karnataka','Maharashtra']:
        for date in pd.date_range('2026-09-15','2026-10-28'):
            assert pd.notna(data.loc[date,state]) and data.loc[date,state] > 0
            for h in range(1,15):
                rows.append(dict(state=state,year=2026,origin=str((date-pd.Timedelta(days=h-1)).date()),date=str(date.date()),horizon=h))
    cases = pd.DataFrame(rows); assert len(cases) == 1848
    assert len(cases[['state','origin']].drop_duplicates()) == 171
    OUT.mkdir(parents=True); ANNEX.mkdir(parents=True)
    cases.to_csv(OUT/'hindcast_cases.csv',index=False)
    cases[cases.date.ge('2026-10-14')].to_csv(OUT/'evaluation_cases.csv',index=False)
    files = ['src/native_interval_calibration.py','src/test_native_calibration.py','src/postweight_daily_panel.py',
        'src/forecasting.py','src/extended_validation.py','src/festival_feature_experiment.py',
        'data/external/latest_state_energy_GWh.csv','results/postweight_daily_v1/protocol.json',
        'results/postweight_daily_v1/chronos/predictions.csv','results/postweight_daily_v1/timesfm/predictions.csv',
        'results/postweight_daily_v1/independent_audit.json','results/second_model_audit_v1/weight_download.json',
        'results/prospective_20261030_v1/protocol.json','results/prospective_20261030_v1/predictions.csv',
        'results/prospective_20261030_v1/freeze.json']
    protected = {}
    for folder in ['data','results','evidence','presentation','src','manuscript/journal_draft_v1']:
        for f in (ROOT/folder).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts and OUT not in f.parents and ANNEX not in f.parents and f.name not in ['native_interval_calibration.py','test_native_calibration.py']:
                protected[str(f.relative_to(ROOT))] = sha(f)
    dump(OUT/'protected_prior_files.json',protected)
    p = dict(created_utc=datetime.now(timezone.utc).isoformat(),experiment=OUT.name,
        status='Exploratory response to already-inspected native undercoverage; rules fixed before new calibration outcomes. Historical targets remain development data, not clean final tests or external preregistration.',
        method='Expansion-only CQR: score=max(native_lower-actual,actual-native_upper); delta=max(0,sorted_scores[ceil((n+1)*0.8)-1]); return native_lower-delta,native_upper+delta. Native median and point forecasts unchanged.',
        prior_work='Established conformalized quantile regression (Romano,Patterson,Candes2019), not a new algorithm. Temporal dependence/drift violate simple exchangeability; no finite-sample time-series coverage guarantee.',
        alpha=.2,minimum_calibration_labels=16,arms=ARMS,
        calibration='Perconfiguration/state/individual lead. FrozenSeptember uses labels15–30September only. Expanding uses every available label15September through strictly BEFORE query ORIGIN, not merely before target. Both methods reported, no evaluated-outcome selection. No cross-state pooling or fitted features.',
        primary='Same15targets14–28October2026perstate/lead; common leads1/7/14,4foundation configurations,540cases acrossconfigurations x3intervalarms=1620rows.',
        extended='TimesFM history/calendar all14leads on the same targetdates:1260cases x3arms=3780rows, including810overlapping primaryTimesFMrows. Total UNIQUE4590intervalrows. Additional lead coverage supports the separately registered prospective annex, not extra independent events.',
        hindcasts='Fresh TimesFM history/calendar inference on the exact171parent contexts; retain all14lead outputs on registered15September–28October targets,3696native rows. Reproduce all792oldpoint/nativequantile rows at leads1/7/14. Reuse Chronos parent only at those3leads,792native rows. No retraining/new weights or future actual requests.',
        context=730,horizon=14,batch=4,threads=2,seed=42,
        evaluation='15common dates start14October so even lead14firstorigin1October has16calibration labels. Month boundary/maximumlead availability selects dates, never new coverage/errors. Allnative andbothcalibrationarms retained.',
        metrics='Inclusive80%coverage,lower/uppermisses,widthGWh/scaledwidth,scaledintervalscore and one-intervalWIS plus native median. Equalstates withinlead; common3leadfourconfig andextendedTimesFM14lead tables separately. Point/median predictions unchanged. No accuracy tuning or repaired/reordered native quantiles.',
        prospective='Separate annex derives intervals from ORIGINAL already-frozen TimesFM quantiles, all14leads, bothmodes,3states. Native/frozen/expanding arms allretained. Registerrulesnow; actual later issuedUTC recorded atfreeze. Original252forecasts/protocol/freeze neverchanged. Newannex is the SAMEsource/episode, not independentconfirmation. Eligibility strictly after newIndiaissuancedate and inheritedoriginaleligibility. No future scores or workflow reactivation.',
        input_hashes={f:sha(ROOT/f) for f in files},
        design_hashes={f:sha(OUT/f) for f in ['hindcast_cases.csv','evaluation_cases.csv','protected_prior_files.json']})
    dump(OUT/'protocol.json',p)
    dump(ANNEX/'registration.json',dict(registered_utc=datetime.now(timezone.utc).isoformat(),
        status='Rules registered before new historical calibration outcomes; prospective intervals not issued yet.',
        parent_forecast_sha256=sha(ORIGINAL/'predictions.csv'),calibration_protocol_sha256=sha(OUT/'protocol.json'),
        models=['timesfm3_history','timesfm3_calendar'],states=['Delhi','Karnataka','Maharashtra'],leads=list(range(1,15)),
        arms=ARMS,rule='Copy originalnativequantiles/point. Perleadcalibration from registerednativearchive using labeldate<originalorigin29October. RetainbothfixedSeptember andexpandingpast; no selection by newhistoricalerrors. RecordnewissuedUTC/India-dateeligibility; neverbackdate.',
        expected_rows=252,expected_eligible_rows_if_issued_30October=216,
        limitation='Sameepisode/sourceasoriginalfuturefreeze; notindependentreplication. No scoring beforecompletefutureperiod; automationstaypaused.'))
    print('REGISTERED:342newTimesFMcontexts;4590uniquehistoricalintervalrows;separateannexrulesbeforeoutcomes')


def hindcast():
    import torch
    from timesfm3 import TimesFM3Evaluator,ModelConfig
    p=check_inputs();out=OUT/'timesfm_hindcasts';out.mkdir(exist_ok=True)
    if (out/'started.json').exists():raise FileExistsError('Preserveworker')
    dump(out/'started.json',dict(started_utc=datetime.now(timezone.utc).isoformat()))
    torch.set_num_threads(p['threads']);torch.manual_seed(p['seed']);np.random.seed(p['seed'])
    identity=json.loads((ROOT/'results/second_model_audit_v1/weight_download.json').read_text());assert sha(identity['path'])==identity['sha256']
    model=TimesFM3Evaluator(ModelConfig(checkpoint_path=str(Path(identity['path']).parent),device='cpu',per_core_batch_size=p['batch'],local_files_only=True))
    cases=pd.read_csv(OUT/'hindcast_cases.csv',parse_dates=['date','origin']);data=load_data('latest')
    tasks=cases[['state','origin']].drop_duplicates().sort_values(['state','origin'])
    rows,logs,solo=[],[],[];start=time.perf_counter()
    def predict(pairs,mode):
        kw={} if mode=='history' else dict(past_future_covariates=[c for _,c in pairs])
        return list(model.predict_batch([t for t,_ in pairs],horizon=14,return_quantiles=True,use_symmetric_averaging=False,**kw))
    try:
        for mode in ['history','calendar']:
            for offset in range(0,len(tasks),p['batch']):
                group=list(tasks.iloc[offset:offset+p['batch']].itertuples(index=False));pairs=[inputs(data[t.state],t.state,t.origin,mode) for t in group]
                for t,(target,cov) in zip(group,pairs):
                    changed=data[t.state].copy();changed.loc[t.origin:]=1e12
                    tt,cc=inputs(changed,t.state,t.origin,mode);np.testing.assert_array_equal(tt,target);np.testing.assert_array_equal(cc,cov)
                    logs.append(dict(state=t.state,origin=str(t.origin.date()),mode=mode,target_sha256=hashlib.sha256(target.tobytes()).hexdigest(),covariate_sha256=hashlib.sha256(cov.tobytes()).hexdigest(),future_target_invariant=True))
                result=predict(pairs,mode)
                if offset==0:
                    for pair,r in zip(pairs,result):
                        single=predict([pair],mode)[0];delta=float(abs(np.asarray(single.forecast)-np.asarray(r.forecast)).max());assert delta<1e-6;solo.append(dict(mode=mode,maxdifference=delta))
                for task,r in zip(group,result):
                    point=np.asarray(r.forecast).squeeze();q=np.asarray(r.quantiles).squeeze()
                    assert point.shape==(14,) and q.shape==(14,9) and np.isfinite(q).all()
                    for c in cases[cases.state.eq(task.state)&cases.origin.eq(task.origin)].itertuples(index=False):
                        rows.append(dict(configuration='timesfm_'+mode,state=c.state,origin=str(c.origin.date()),date=str(c.date.date()),horizon=c.horizon,prediction=float(point[c.horizon-1]),actual=float(data.loc[c.date,c.state]),mase_scale=scale(data,c.state,2026),**{f'q_{i*100:03d}':float(v) for i,v in enumerate(q[c.horizon-1],1)}))
                pd.DataFrame(rows).to_csv(out/'checkpoint.csv',index=False);dump(out/'inputs.json',logs);dump(out/'solo_batch.json',solo)
                print(mode,offset+len(group),'/',len(tasks),flush=True)
        d=pd.DataFrame(rows);assert len(d)==3696 and not d.duplicated(KEY).any()
        old=pd.read_csv(PARENT/'timesfm/predictions.csv')
        c=d.merge(old[KEY+['prediction']+[f'q_{i*100:03d}' for i in range(1,10)]],on=KEY,suffixes=('_new','_old'),validate='one_to_one');assert len(c)==792
        differences={}
        for name in ['prediction']+[f'q_{i*100:03d}' for i in range(1,10)]:
            delta=float(abs(c[name+'_new']-c[name+'_old']).max());assert delta<1e-6;differences[name]=delta
        d.to_csv(out/'predictions.csv',index=False)
        dump(out/'run.json',dict(status='completed',rows=len(d),tasks=len(logs),seconds=time.perf_counter()-start,weight_sha256=identity['sha256'],native_crossing_pairs=int((np.diff(d[[f'q_{i*100:03d}' for i in range(1,10)]].to_numpy(),axis=1)<0).sum()),original792rows_maxdifferences=differences,predictions_sha256=sha(out/'predictions.csv'),protocol_sha256=sha(OUT/'protocol.json')))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise


def archive():
    check_inputs();r=json.loads((OUT/'timesfm_hindcasts/run.json').read_text());assert sha(OUT/'timesfm_hindcasts/predictions.csv')==r['predictions_sha256']
    t=pd.read_csv(OUT/'timesfm_hindcasts/predictions.csv');c=pd.read_csv(PARENT/'chronos/predictions.csv')
    cols=KEY+['prediction','actual','mase_scale']+[f'q_{i*100:03d}' for i in range(1,10)]
    d=pd.concat([t[cols],c[cols]],ignore_index=True);assert len(d)==4488 and not d.duplicated(KEY).any()
    return d


def analyze():
    p=check_inputs()
    if (OUT/'interval_predictions.csv').exists():raise FileExistsError('Preservecompletedanalysis')
    d=archive();d.to_csv(OUT/'native_archive.csv',index=False)
    queries=d[d.date.ge('2026-10-14')];assert len(queries)==1530
    rows,logs=[],[]
    for q in queries.itertuples(index=False):
        for arm in ARMS:
            delta=0.;n=rank=0;raw=0.;dates=[]
            if arm!='native':
                selected=calibration_rows(d,q.state,q.configuration,q.horizon,q.origin,arm)
                delta,rank,raw=adjustment(selected,p['alpha']);n=len(selected);dates=selected.date.tolist()
                logs.append(dict(configuration=q.configuration,state=q.state,horizon=q.horizon,origin=q.origin,date=q.date,arm=arm,n=n,rank=rank,raw_order_statistic=raw,expansion_GWh=delta,calibration_dates=dates,calibration_labels_sha256=hashlib.sha256(selected.actual.to_numpy(dtype=np.float64).tobytes()).hexdigest()))
            rows.append(dict(**{k:getattr(q,k) for k in KEY},arm=arm,prediction=q.prediction,actual=q.actual,mase_scale=q.mase_scale,native_lower=q.q_100,native_median=q.q_500,native_upper=q.q_900,lower=q.q_100-delta,upper=q.q_900+delta,expansion_GWh=delta,calibration_n=n,calibration_rank=rank))
    result=pd.DataFrame(rows);assert len(result)==4590
    result.to_csv(OUT/'interval_predictions.csv',index=False);dump(OUT/'calibration_log.json',logs)
    dump(OUT/'run.json',dict(status='completed',rows=len(result),primary_rows=int(result.horizon.isin([1,7,14]).sum()),extended_timesfm_rows=int(result.configuration.str.startswith('timesfm').sum()),protocol_sha256=sha(OUT/'protocol.json'),native_archive_sha256=sha(OUT/'native_archive.csv'),interval_predictions_sha256=sha(OUT/'interval_predictions.csv')))
    print('Completed4590uniqueintervalrows;1620primary/3780extendedwith810overlap')


def freeze_annex():
    p=check_inputs();reg=json.loads((ANNEX/'registration.json').read_text())
    assert reg['calibration_protocol_sha256']==sha(OUT/'protocol.json')
    if (ANNEX/'freeze.json').exists() or (ANNEX/'predictions.csv').exists():raise FileExistsError('Neveroverwriteannex')
    assert sha(ORIGINAL/'predictions.csv')==reg['parent_forecast_sha256']
    for name in ['predictions.csv','protocol.json','freeze.json']:
        relative=str((ORIGINAL/name).relative_to(ROOT));assert (ORIGINAL/name).read_bytes()==subprocess.check_output(['git','show',GIT_FREEZE+':'+relative],cwd=ROOT)
    d=archive();parent=pd.read_csv(ORIGINAL/'predictions.csv');parent=parent[parent.model.isin(reg['models'])]
    assert len(parent)==84
    issued=datetime.now(timezone.utc);india_date=issued.astimezone(ZoneInfo('Asia/Kolkata')).date()
    if str(india_date)!='2026-10-30':raise ValueError('Registeredannexdatepassed;versionnewissuance/eligibility,neverbackdate')
    rows,logs=[],[]
    for q in parent.itertuples(index=False):
        configuration=q.model.replace('timesfm3_','timesfm_')
        for arm in ARMS:
            delta=0.;n=rank=0
            if arm!='native':
                selected=calibration_rows(d,q.state,configuration,q.horizon,q.origin,arm);delta,rank,raw=adjustment(selected,p['alpha']);n=len(selected)
                logs.append(dict(state=q.state,model=q.model,horizon=q.horizon,arm=arm,calibration_dates=selected.date.tolist(),n=n,rank=rank,raw_order_statistic=raw,expansion_GWh=delta))
            eligible=bool(q.prospective_eligible) and pd.Timestamp(q.date).date()>india_date
            rows.append(dict(state=q.state,model=q.model,horizon=q.horizon,origin=q.origin,date=q.date,arm=arm,
                prediction=q.prediction,mase_scale=q.mase_scale,native_lower=q.q01,native_median=q.q05,native_upper=q.q09,
                lower=q.q01-delta,upper=q.q09+delta,expansion_GWh=delta,calibration_n=n,calibration_rank=rank,
                parent_issued_utc=q.issued_utc,issued_utc=issued.isoformat(),prospective_eligible=eligible))
    result=pd.DataFrame(rows);assert len(result)==252 and int(result.prospective_eligible.sum())==216
    result.to_csv(ANNEX/'predictions.csv',index=False);dump(ANNEX/'calibration_log.json',logs)
    dump(ANNEX/'freeze.json',dict(issued_utc=issued.isoformat(),issued_india_date=str(india_date),rows=len(result),eligible_rows=216,
        eligible_start='2026-10-31',eligible_end='2026-11-11',new_model_inference_for_future=False,
        native_parent_sha256=sha(ORIGINAL/'predictions.csv'),registration_sha256=sha(ANNEX/'registration.json'),calibration_protocol_sha256=sha(OUT/'protocol.json'),
        calibration_archive_sha256=sha(OUT/'native_archive.csv'),predictions_sha256=sha(ANNEX/'predictions.csv'),calibration_log_sha256=sha(ANNEX/'calibration_log.json'),
        outcomes_fetched=False,scores_status='pendingfutureobservations',automation='paused;noschedulechange',
        interpretation='216intervalrows=72originalTimesFMeligiblecases x3arms, not216independentforecasts. Sameepisode/sourceasoriginalfreeze, originallyissued05:35UTC; newpostprocessingissuedatactualtimeabove.'))
    print('FROZEN separateannex252rows/216eligible;originalforecastsunchanged;nooutcomesretrieved')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','hindcast','analyze','freeze_annex']);args=parser.parse_args()
    {'prepare':prepare,'hindcast':hindcast,'analyze':analyze,'freeze_annex':freeze_annex}[args.action]()
