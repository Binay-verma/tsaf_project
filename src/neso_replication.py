"""New-primary-source retrospective replication; protocol precedes target download."""
import argparse,hashlib,itertools,json,time,traceback,urllib.request
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from forecasting import ROOT,causal_fill
from festival_feature_design import sha,dump,KEY

OUT=ROOT/'results/neso_replication_v1'
CACHE=Path('/workspace/neso-replication-v1')
PROBES=Path('/workspace/independent-source-cache')
STATE='England_Wales'
FAMILIES=['New_Year','Easter','Early_May','Spring','Summer','Christmas']
ARMS=['calendar','zero6','day6','pooled_day6','window6','pooled_window6','placebo_day6','placebo_window6']
MODELS=['ridge','lightgbm','lightgbm_capacity2','sarimax','chronos','timesfm']
SCENARIOS={'ideal':0,'lag21':21}


def periods_for_day(day):
    z=ZoneInfo('Europe/London')
    a=datetime.combine(day,datetime.min.time(),z).astimezone(timezone.utc)
    b=datetime.combine(day+timedelta(days=1),datetime.min.time(),z).astimezone(timezone.utc)
    return int((b-a).total_seconds()/1800)


def aggregate_daily(raw):
    r=raw.copy();r.columns=[str(c).strip().upper() for c in r.columns]
    needed={'SETTLEMENT_DATE','SETTLEMENT_PERIOD','ENGLAND_WALES_DEMAND'}
    if not needed<=set(r):raise ValueError('Missing registered regional target/schema')
    r['day']=pd.to_datetime(r.SETTLEMENT_DATE,format='mixed',dayfirst=True).dt.date
    if 'FORECAST_ACTUAL_INDICATOR' in r:
        r=r[r.FORECAST_ACTUAL_INDICATOR.astype(str).str.strip().str.upper().eq('A')].copy()
    r['value']=pd.to_numeric(r.ENGLAND_WALES_DEMAND,errors='coerce')
    r['period']=pd.to_numeric(r.SETTLEMENT_PERIOD,errors='coerce')
    rows=[]
    for day,g in r.groupby('day'):
        n=periods_for_day(day)
        complete=len(g)==n and set(g.period)==set(range(1,n+1)) and g.value.gt(0).all() and np.isfinite(g.value).all()
        rows.append(dict(date=day,**{STATE:float(g.value.sum()/2000.) if complete else np.nan},
            periods=len(g),expected_periods=n,complete=bool(complete)))
    return pd.DataFrame(rows)


def cases_for(scenario):
    lag=SCENARIOS[scenario];rows=[]
    for target in pd.date_range('2026-09-15','2026-09-30'):
        for lead in [1,7,14]:
            decision=target-pd.Timedelta(days=lead-1)
            origin=decision-pd.Timedelta(days=lag)
            rows.append(dict(family='Ordinary_September',state=STATE,year=2026,date=str(target.date()),
                origin=str(origin.date()),horizon=lead+lag,decision_lead=lead,
                decision_origin=str(decision.date()),scenario=scenario))
    return pd.DataFrame(rows).sort_values(KEY)


def prepare():
    if OUT.exists():raise FileExistsError('Preserve original source protocol/outputs')
    provider=json.loads((PROBES/'neso_metadata.json').read_text())['result']
    schema=json.loads((PROBES/'neso_fields.json').read_text())['result']
    assert schema['records']==[]
    field=next(f for f in schema['fields'] if f['id']=='ENGLAND_WALES_DEMAND')
    assert field['info']['unit']=='MW' and 'England and Wales' in field['info']['description']
    faq=(PROBES/'neso_faq.txt').read_text()
    assert 'Answer: MW' in faq and 'All values are an average over the half hour' in faq
    gov=json.loads((PROBES/'gov_uk_calendar.json').read_text())['england-and-wales']['events']
    mapping={"new year's day":'New_Year','good friday':'Easter','easter monday':'Easter',
        'early may bank holiday':'Early_May','spring bank holiday':'Spring',
        'summer bank holiday':'Summer','christmas day':'Christmas','boxing day':'Christmas'}
    anchors=[]
    for event in gov:
        year=int(event['date'][:4])
        if year not in [2024,2025,2026]:continue
        label=event['title'].lower().replace('’',"'").split(' (')[0]
        if label not in mapping:raise ValueError(('Unregistered holiday title',event))
        anchors.append(dict(state=STATE,year=year,family=mapping[label],date=event['date'],label=event['title'],source='https://www.gov.uk/bank-holidays.json'))
    a=pd.DataFrame(anchors).sort_values(['year','family','date'])
    assert len(a)==24 and len(a[['family','year']].drop_duplicates())==18
    rng=np.random.default_rng(42);fake=[]
    for (year,family),g in a.groupby(['year','family']):
        roots=pd.to_datetime(g.date);all_roots=pd.to_datetime(a[a.year.eq(year)].date)
        blocked={d for r in all_roots for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))}
        choices=[]
        for shift in [-42,-35,-28,28,35,42]:
            moved=roots+pd.Timedelta(days=shift)
            windows={d for r in moved for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))}
            if all(d.year==year for d in windows) and not windows&blocked:choices.append(shift)
        if not choices:raise ValueError(('No date-only placebo',year,family))
        shift=int(rng.choice(choices))
        for r in g.itertuples():fake.append(dict(state=STATE,year=int(year),family=family,date=str((pd.Timestamp(r.date)+pd.Timedelta(days=shift)).date()),shift_days=shift,original_date=r.date))
    OUT.mkdir();a.to_csv(OUT/'anchors.csv',index=False);pd.DataFrame(fake).to_csv(OUT/'placebos.csv',index=False)
    resources={str(y):next(r for r in provider['resources'] if r['name']==f'Historic Demand Data {y}')['url'] for y in [2023,2024,2025,2026]}
    dump(OUT/'provider_metadata.json',dict(title=provider['title'],metadata_url='https://api.neso.energy/api/3/action/package_show?id=historic-demand-data',
        license_id=provider['license_id'],license_title=provider['license_title'],license_url=provider['license_url'],notes=provider['notes'],resources=resources,
        regional_field=field,faq_url=json.loads((PROBES/'neso_faq_retrieval.json').read_text())['url'],
        evidence_hashes={f:sha(PROBES/f) for f in ['neso_metadata.json','neso_fields.json','neso_faq.docx','gov_uk_calendar.json']},
        rights='Provider identifies customNESOOpenDataLicence; licence body403 and catalogOKDflagfalse. Do not claim OGL/CCBY or unrestricted redistribution. Raw/complete derived source remain outsideGit; source link/code and ownminimalresult facts retained.'))
    fixed=json.loads((ROOT/'results/stable_tree_refit_v2/protocol.json').read_text())['lightgbm_fixed']
    paths=['src/neso_replication.py','src/neso_model_engine_v1.py','src/test_neso_replication.py',
        'src/forecasting.py','src/robust_baselines.py','src/multifestival_models.py',
        'results/mechanism_controls_v1/chronos_download.json','results/second_model_audit_v1/weight_download.json',
        'results/neso_replication_v1/provider_metadata.json','results/neso_replication_v1/anchors.csv','results/neso_replication_v1/placebos.csv']
    protocols={}
    for scenario,lag in SCENARIOS.items():
        out=OUT/scenario;out.mkdir();c=cases_for(scenario)
        for name in ['primary_cases.csv','window_cases.csv']:c.to_csv(out/name,index=False)
        p=dict(created_utc=datetime.now(timezone.utc).isoformat(),experiment=f'{OUT.name}/{scenario}',scenario=scenario,lag_days=lag,
            status='New-to-analyst primary-source retrospective replication; methods/cases fixed BEFORE downloading anyNESO2026targetseries. Not publicly issued historical forecasts, clean prospective evidence or exact first-vintage reconstruction.',
            target='Daily GWh=0.5/1000 times sum of complete positive actual half-hour ENGLAND_WALES_DEMAND(MW). OfficialFAQ verifies half-hour average/UKlocaltime; daylightdays require46/48/50distinctsettlementperiods. Filter2026Aactual indicator, neverFforecasts. Oldyears withoutflag are labelled historicoutturn perprovider, not independently certified first releases. Freeze derivedsource through30September2026only.',
            cases='Exactly16targets15–30September2026atdecisionleads1/7/14,48cases/scenario, oneEngland/Walesseries. Targetspostdatebothactualweightuploads; earliestdecisionorigin2September followsTimesFMannouncement. No festival target in this bounded cohort: it tests ordinary-day costs/source replication, not independent festival enhancement.',
            availability='ideal:contextthroughdecisionorigin-1. lag21:21additionalcalendar-days of delay, contextthroughdecisionorigin-22; modelorigin=decisionorigin-21, effectiveleads22/28/35. Calendarbridge predictionsunscored. This sensitivity addresses statedarchivearrears, not unknown corrections/first-release vintages. Decisionorigin is firstunseen targetdate, not a real recorded issuance.',
            calendar='England/Wales officialbankholidaydates2024–2026, sixfamilies:NewYear,Easter(GoodFriday+EasterMonday),EarlyMay,Spring,Summer,Christmas(Xmas+Boxing). Logicalunionswithinmulti-anchor family, not independentholidays. NotIndianreligiouslabels or proof of whole-economyclosure. Frozenone-seedweekdayplacebos avoidtruewindows.',
            arms=ARMS,models=MODELS,context=730,horizon=14+lag,batch=16,threads=2,seed=42,
            expected_tasks=len(c[['state','origin']].drop_duplicates()),cases_per_arm=48,
            local='Rich27pastfeatures+13calendar+0/6eventcovariates, float32trees. Monthlyrefits bymodeloriginmonth, cutoffpreviousday; directeffectiveleadpurging. Samepast-selected richcalendarparameters acrossallarms; leaf2overrideonly. SARIMAXfixed(1,0,0)x(1,0,0,7), monthly730dayparameterfitsandpastupdates; convergence-onlyretries retained.',
            selection='Ridgealpha[.1,1,10,100], treeleaves[7,15]xestimators[100,300]xL2[1,10], minleaf20. Foreachactualmodellead1/7/14/22/28/35, fitbefore1January2026, validateorigins whose target<=30June2026; allvalidationlabels available before earliestqueriedcontextcutoff11August2026. Stabletie-order/noSeptembertargetselection. No eventfeature-specific search.',
            lightgbm_fixed=fixed,metrics='Same pre2026weeklydifference scale from730calendar days ending31December2025; recordedderivedlabels only, samecasesforallmethods. Report scenariosseparately bydecisionlead, MAE/MASE, nativecommon9quantile pinball/80coverage/width/WIS. Noindependentrowtests or yeargeneralisation from16days.',
            limits='Oneadditionalprimarygeography,16alreadyhistoricaltargetdates andnofestivals. Post-weight chronologynot contamination-free claim; revisions/measurementdefinition remain. Providercustomlicencefullconditionsunverified; oldIndianrights/human/calendar/prospectivegatesunchanged. No futureIndianactuals, oldforecastmodification or workflowactivation.',
            input_hashes={f:sha(ROOT/f) for f in paths},design_hashes={f:sha(out/f) for f in ['primary_cases.csv','window_cases.csv']})
        dump(out/'protocol.json',p);protocols[scenario]=sha(out/'protocol.json')
    dump(OUT/'registration.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),status='BEFORE_TARGET_DOWNLOAD',protocols=protocols,
        target_dates=['2026-09-15','2026-09-30'],planned_model_rows=4608,planned_naive_rows=192,raw_cache=str(CACHE),
        source_independence='NESOEngland/Walesprimarylineage independent ofIndianGRID/POSOCO; not a sharedsource derivative. No independentholidayoutcome claim.'))
    print('FROZEN independent-source cases/methods BEFORE targetdownload:4608model+192naive forecasts')


def acquire():
    reg=json.loads((OUT/'registration.json').read_text());assert reg['status']=='BEFORE_TARGET_DOWNLOAD'
    if CACHE.exists() or (OUT/'snapshot.json').exists():raise FileExistsError('Preserve firstsource snapshot; no replacement')
    CACHE.mkdir();provider=json.loads((OUT/'provider_metadata.json').read_text());frames=[];downloads={};quality=[]
    for year,url in provider['resources'].items():
        tick=datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(url,timeout=60) as response:raw=response.read(16*1024*1024+1);assert response.status==200
        assert len(raw)<=16*1024*1024
        path=CACHE/f'{year}.csv';path.write_bytes(raw)
        downloads[year]=dict(url=url,sha256=sha(path),bytes=len(raw),retrieved_utc=tick)
        table=pd.read_csv(path);flag='FORECAST_ACTUAL_INDICATOR'
        flags=table[flag].value_counts(dropna=False).astype(int).to_dict() if flag in table else {'absent_historic_outturn':len(table)}
        if year=='2026' and flag not in table:raise ValueError('2026actual/forecastflagmissing:do not assumeactual')
        daily=aggregate_daily(table)
        daily=daily[(daily.date>=date(int(year),1,1))&(daily.date<=min(date(int(year),12,31),date(2026,9,30)))]
        quality.append(dict(year=int(year),flags={str(k):int(v) for k,v in flags.items()},complete_days=int(daily.complete.sum()),incomplete_days=int((~daily.complete).sum()),
            period_counts={str(k):int(v) for k,v in daily.expected_periods.value_counts().items()}))
        frames.append(daily[['date',STATE]])
    daily=pd.concat(frames).set_index('date').sort_index();assert not daily.index.duplicated().any()
    daily.to_csv(CACHE/'daily_energy_GWh.csv')
    for day in pd.date_range('2026-09-15','2026-09-30'):assert np.isfinite(daily.loc[day.date(),STATE]) and daily.loc[day.date(),STATE]>0
    dump(OUT/'snapshot.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),raw_cache=str(CACHE),downloads=downloads,quality=quality,
        daily_sha256=sha(CACHE/'daily_energy_GWh.csv'),date_min=str(daily.index.min()),date_max=str(daily.index.max()),
        raw_redistributed=False,conversion='sumpositivecompleteactualhalf-hourMW/2000; missing/incompletedays remainunscoredNaN',
        notice='Currentrevisedarchive; bothdelaycasesretrospective, no first-vintage/permissions grant inferred.'))
    print('Acquired/auditedsource; actual-only targetscomplete; no targetvalues printed')


def load_source():
    snapshot=json.loads((OUT/'snapshot.json').read_text())
    assert sha(CACHE/'daily_energy_GWh.csv')==snapshot['daily_sha256']
    for year,entry in snapshot['downloads'].items():assert sha(CACHE/f'{year}.csv')==entry['sha256']
    return pd.read_csv(CACHE/'daily_energy_GWh.csv',index_col=0,parse_dates=True).asfreq('D').where(lambda x:x>0)


def calendar13(index):
    columns={f'dow_{j}':(index.dayofweek==j).astype(float) for j in range(7)}
    for j in [1,2,3]:columns.update({f'sin_{j}':np.sin(2*np.pi*j*index.dayofyear/365.2425),f'cos_{j}':np.cos(2*np.pi*j*index.dayofyear/365.2425)})
    return pd.DataFrame(columns,index=index)


def frames(index,state=STATE):
    base=calendar13(index);true=pd.read_csv(OUT/'anchors.csv',parse_dates=['date']);fake=pd.read_csv(OUT/'placebos.csv',parse_dates=['date'])
    result={'calendar':base,'zero6':pd.concat([base,pd.DataFrame(0.,index=index,columns=[f'zero_{j}' for j in range(6)])],axis=1)}
    for prefix,ledger in [('',true),('placebo_',fake)]:
        for kind in ['day','window']:
            cols={}
            for family in FAMILIES:
                roots=ledger[ledger.family.eq(family)].date
                dates=roots if kind=='day' else [d for root in roots for d in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))]
                cols[family+'_'+kind]=index.isin(dates).astype(float)
            event=pd.DataFrame(cols,index=index);result[prefix+kind+'6']=pd.concat([base,event],axis=1)
            if not prefix:
                pooled=pd.DataFrame({'event_'+kind:event.any(axis=1).astype(float)},index=index)
                for j in range(1,6):pooled['padding_'+str(j)]=0.
                result['pooled_'+kind+'6']=pd.concat([base,pooled],axis=1)
    return {arm:result[arm] for arm in ARMS}


def build_input(observed,frame,origin,horizon):
    dates=pd.date_range(origin-pd.Timedelta(days=730),periods=730+horizon)
    assert pd.Timestamp('2024-01-01')<=dates.min()<=dates.max()<=pd.Timestamp('2026-12-31')
    target=causal_fill(observed).reindex(dates[:730]).to_numpy(dtype=np.float32)
    cov=frame.reindex(dates).to_numpy(dtype=np.float32).T
    assert np.isfinite(target).all() and np.isfinite(cov).all()
    return target,cov


def design(observed,horizon,arm):
    from robust_baselines import rich_history
    index=pd.date_range(observed.index.min(),observed.index.max()+pd.Timedelta(days=34))
    f=frames(index)[arm].reindex(observed.index+pd.Timedelta(days=horizon-1)).copy();f.index=observed.index
    return pd.concat([rich_history(observed,horizon),f],axis=1)


def select():
    from robust_baselines import fitting_cases,make_model
    if (OUT/'selection.json').exists() or (OUT/'selection_started.json').exists():raise FileExistsError('Preserve selection attempts')
    dump(OUT/'selection_started.json',dict(started_utc=datetime.now(timezone.utc).isoformat()))
    p=json.loads((OUT/'ideal/protocol.json').read_text());observed=load_source()[STATE]
    selected={};logs=[]
    try:
        for h in [1,7,14,22,28,35]:
            base=design(observed,h,'calendar');vo=pd.date_range('2026-01-01',pd.Timestamp('2026-06-30')-pd.Timedelta(days=h-1));dates=vo+pd.Timedelta(days=h-1)
            for model in ['ridge','lightgbm']:
                x=base if model=='ridge' else base.astype(np.float32)
                xx,yy,log=fitting_cases(x,observed,h,pd.Timestamp('2025-12-31'))
                vx=x.reindex(vo).to_numpy();vy=observed.reindex(dates).to_numpy();valid=np.isfinite(vx).all(axis=1)&np.isfinite(vy)
                grid=[dict(alpha=a) for a in [.1,1.,10.,100.]] if model=='ridge' else [dict(num_leaves=l,n_estimators=n,reg_lambda=z,min_child_samples=20) for l,n,z in itertools.product([7,15],[100,300],[1.,10.])]
                trials=[]
                for j,params in enumerate(grid):
                    fitted=make_model(model,params,p).fit(xx,yy);prediction=fitted.predict(vx[valid]);error=float(np.mean(abs(prediction-vy[valid])))
                    row=dict(model=model,horizon=h,configuration=j,parameters=params,validation_MAE_GWh=error,validation_n=int(valid.sum()),validation_target_max=str(dates[valid].max().date()),
                        training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),**log)
                    logs.append(row);trials.append(row)
                winner=min(trials,key=lambda r:(r['validation_MAE_GWh'],r['configuration']))
                selected[f'{model}:{h}']=winner['parameters']
                dump(OUT/'selection_attempts.json',logs)
        dump(OUT/'selection.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),parameters=selected,attempts=logs,
            policy='Calendar-only January–June2026pastvalidation; unchangedselectedparametersforallnewarms, noSeptembertesttuning',snapshot_sha256=sha(OUT/'snapshot.json')))
    except BaseException:(OUT/'selection_failure.txt').write_text(traceback.format_exc());raise
    print('Complete72past-only selectionfits; Septembertargetsnotused')


def regression(scenario,worker):
    from robust_baselines import fitting_cases,make_model
    import neso_model_engine_v1 as engine
    engine.OUT=OUT/scenario
    p,out,cases,data=engine.setup(worker)
    observed=data[STATE];selected=json.loads((OUT/'selection.json').read_text())['parameters']
    model='ridge' if worker=='ridge' else 'lightgbm';rows=[];fits=[]
    try:
        for horizon,group in cases.groupby('horizon'):
            params=selected[f'{model}:{int(horizon)}'].copy()
            if worker=='lightgbm_capacity2':params['min_child_samples']=2
            for arm in ARMS:
                x=design(observed,int(horizon),arm)
                if model=='lightgbm':x=x.astype(np.float32)
                for month,g in group.groupby(group.origin.dt.to_period('M')):
                    cutoff=pd.Timestamp(month.start_time)-pd.Timedelta(days=1)
                    xx,yy,log=fitting_cases(x,observed,int(horizon),cutoff)
                    assert pd.Timestamp(log['training_target_max'])<=cutoff<g.origin.min()
                    query=x.reindex(pd.DatetimeIndex(g.origin)).to_numpy();pred=make_model(model,params,p).fit(xx,yy).predict(query)
                    a=g.copy();a['prediction']=pred;a['actual']=observed.reindex(pd.DatetimeIndex(g.date)).to_numpy()
                    a['mase_scale']=engine.scale(data,STATE,2026);a['model']=worker;a['arm']=arm;rows.append(a)
                    fits.append(dict(horizon=int(horizon),arm=arm,refit=str((cutoff+pd.Timedelta(days=1)).date()),parameters=params,feature_count=xx.shape[1],
                        training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),query_X_sha256=hashlib.sha256(query.tobytes()).hexdigest(),**log))
                pd.concat(rows).to_csv(out/'checkpoint.csv',index=False);dump(out/'fit_log.json',fits)
        d=pd.concat(rows);assert len(d)==48*8 and np.isfinite(d.prediction).all()
        d.to_csv(out/'predictions.csv',index=False)
        dump(out/'run.json',dict(model=worker,completed_utc=datetime.now(timezone.utc).isoformat(),rows=len(d),fits=len(fits),predictions_sha256=sha(out/'predictions.csv'),protocol_sha256=sha(OUT/scenario/'protocol.json')))
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());dump(out/'fit_log.json',fits);raise


def sarimax(scenario):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from multifestival_models import fit_checked
    import neso_model_engine_v1 as engine
    engine.OUT=OUT/scenario;p,out,cases,data=engine.setup('sarimax')
    observed=data[STATE];y=causal_fill(observed)/100.;index=pd.date_range(data.index.min(),data.index.max()+pd.Timedelta(days=34));fc=frames(index)
    rows=[];attempts=[];updates=[]
    try:
        for month,g in cases.groupby(cases.origin.dt.to_period('M')):
            cutoff=pd.Timestamp(month.start_time)-pd.Timedelta(days=1);tr=y.loc[cutoff-pd.Timedelta(days=729):cutoff]
            for arm in ARMS:
                exog=fc[arm];fit=fit_checked(SARIMAX(tr,exog=exog.reindex(tr.index),order=(1,0,0),seasonal_order=(1,0,0,7),trend='n',enforce_stationarity=False),
                    'sarimax',attempts,dict(configuration=arm,state=STATE,year=2026,refit=str((cutoff+pd.Timedelta(days=1)).date()),training_end=str(cutoff.date())))
                previous=cutoff+pd.Timedelta(days=1)
                for origin in sorted(g.origin.unique()):
                    origin=pd.Timestamp(origin);new=y.loc[previous:origin-pd.Timedelta(days=1)]
                    if len(new):fit=fit.extend(new,exog=exog.reindex(new.index))
                    future=pd.date_range(origin,periods=p['horizon']);pred=np.asarray(fit.forecast(p['horizon'],exog=exog.reindex(future)))*100.
                    a=g[g.origin.eq(origin)].copy();a['prediction']=[pred[int(h)-1] for h in a.horizon];a['actual']=observed.reindex(pd.DatetimeIndex(a.date)).to_numpy()
                    a['mase_scale']=engine.scale(data,STATE,2026);a['model']='sarimax';a['arm']=arm;rows.append(a)
                    updates.append(dict(arm=arm,origin=str(origin.date()),training_end=str(cutoff.date()),context_end=str((origin-pd.Timedelta(days=1)).date())))
                    previous=origin
                pd.concat(rows).to_csv(out/'checkpoint.csv',index=False);dump(out/'fit_attempts.json',attempts);dump(out/'deployments.json',updates)
        d=pd.concat(rows);assert len(d)==384 and np.isfinite(d.prediction).all();d.to_csv(out/'predictions.csv',index=False)
        dump(out/'run.json',dict(model='sarimax',completed_utc=datetime.now(timezone.utc).isoformat(),rows=len(d),attempts=len(attempts),predictions_sha256=sha(out/'predictions.csv'),protocol_sha256=sha(OUT/scenario/'protocol.json')))
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());dump(out/'fit_attempts.json',attempts);raise


def run(scenario,worker):
    reg=json.loads((OUT/'registration.json').read_text());assert sha(OUT/scenario/'protocol.json')==reg['protocols'][scenario]
    if worker in ['chronos','timesfm']:
        import neso_model_engine_v1 as engine
        engine.OUT=OUT/scenario;engine.ARMS=ARMS;engine.frames=frames;engine.foundation(worker)
    elif worker=='sarimax':sarimax(scenario)
    else:regression(scenario,worker)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','acquire','select',*MODELS]);p.add_argument('--scenario',choices=list(SCENARIOS),default='ideal');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='acquire':acquire()
    elif a.action=='select':select()
    else:run(a.scenario,a.action)
