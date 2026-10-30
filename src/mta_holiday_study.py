"""Independent NYC holiday replication: freeze before target date/count records."""
import argparse,hashlib,itertools,json,time,traceback,urllib.request,urllib.parse,importlib.metadata,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import ROOT,causal_fill
from festival_feature_design import sha,dump,KEY

OUT=ROOT/'results/mta_holiday_v1'
METADATA=Path('/workspace/mta-holiday-metadata')
FAMILIES=['Labor_Day','Yom_Kippur','Columbus_Day','Thanksgiving','Christmas']
ARMS=['calendar','zero5','day5','pooled_day5','window5','pooled_window5','placebo_day5','placebo_window5']
FOUNDATION_ARMS=['history',*ARMS]
MODELS=['ridge','lightgbm','lightgbm_capacity2','sarimax','chronos','timesfm']
SERIES={'Subway':'MTA_Subway','Bus':'MTA_Bus'}


def cases_for(cohort):
    rows=[]
    if cohort=='event_window':
        targets=[(f,d) for f,root in [('Yom_Kippur','2026-09-21'),('Columbus_Day','2026-10-12')] for d in pd.date_range(pd.Timestamp(root)-pd.Timedelta(days=3),periods=7)]
    else:
        # All September/October observances in the pre-year2026NYCDOTcalendar,
        # including unmodelled events, are excluded from the ordinary sample.
        roots=pd.to_datetime(['2026-09-07','2026-09-12','2026-09-13','2026-09-21','2026-09-26','2026-09-27','2026-10-03','2026-10-04','2026-10-12'])
        blocked={d for root in roots for d in pd.date_range(root-pd.Timedelta(days=3),root+pd.Timedelta(days=3))}
        targets=[]
        for weekday in range(7):
            possible=[d for d in pd.date_range('2026-09-15','2026-10-28') if d.weekday()==weekday and d not in blocked]
            if not possible:raise ValueError(('No date-only ordinary candidate',weekday))
            targets.append(('Ordinary',possible[0]))
    for family,target in targets:
        for state in SERIES.values():
            for lead in [1,7,14]:
                decision=target-pd.Timedelta(days=lead-1);origin=decision-pd.Timedelta(days=7)
                rows.append(dict(family=family,state=state,year=2026,date=str(target.date()),origin=str(origin.date()),horizon=lead+7,decision_lead=lead,decision_origin=str(decision.date())))
    return pd.DataFrame(rows).sort_values(KEY)


def parse_source(rows):
    d=pd.DataFrame(rows);assert {'date','mode','count'}<=set(d)
    if not set(d['mode'])<=set(SERIES):raise ValueError('Unexpected source mode')
    d['date']=pd.to_datetime(d['date']).dt.normalize();d['value']=pd.to_numeric(d['count'],errors='raise')/1_000_000.
    if d.duplicated(['date','mode']).any():raise ValueError('Duplicate mode/day estimates must not be summed')
    result=d.pivot(index='date',columns='mode',values='value').rename(columns=SERIES).sort_index().asfreq('D')
    return result.reindex(columns=list(SERIES.values())).where(lambda x:x>0)


def prepare():
    if OUT.exists():raise FileExistsError('Preserve earlier MTA protocol/snapshot/results')
    overview=(METADATA/'overview.txt').read_text();assert 'There are no limitations on the data at this time.' in overview
    schema=json.loads((METADATA/'dataset_schema.json').read_text());assert schema['id']=='sayj-mze2'
    assert {c['fieldName']:c['dataTypeName'] for c in schema['columns']}=={'date':'calendar_date','mode':'text','count':'number'}
    observed_modes={r['mode'] for r in json.loads((METADATA/'mode_names.json').read_text())};assert set(SERIES)<=observed_modes
    OUT.mkdir();evidence=OUT/'evidence';evidence.mkdir()
    for name in ['dataset_schema.json','dataset_schema_retrieval.json','overview_retrieval.json','dictionary_retrieval.json','mode_names.json','mode_names_retrieval.json']:(evidence/name).write_bytes((METADATA/name).read_bytes())
    for year in [2024,2025,2026]:
        source=METADATA/(f'nyc_dot_{year}.pdf' if year==2024 else f'nyc_dot_{year}_preyear.pdf')
        retrieval=METADATA/('nyc2024_archive_retrieval.json' if year==2024 else f'nyc{year}_preyear_retrieval.json')
        meta=json.loads(retrieval.read_text());assert sha(source)==meta['pdf_sha256'] and int(meta['archive_timestamp'][:4])<year
        (evidence/f'nyc_dot_{year}_preyear.pdf').write_bytes(source.read_bytes());(evidence/f'nyc_dot_{year}_preyear_retrieval.json').write_bytes(retrieval.read_bytes())
    dates={2024:['09-02','10-12','10-14','11-28','12-25'],2025:['09-01','10-02','10-13','11-27','12-25'],2026:['09-07','09-21','10-12','11-26','12-25']}
    anchors=pd.DataFrame([dict(year=y,family=f,date=f'{y}-{date}',source=f'evidence/nyc_dot_{y}_preyear.pdf',scope='NYCDOTparking-suspensionobservance; not MTAshutdown') for y,ds in dates.items() for f,date in zip(FAMILIES,ds)])
    anchors.to_csv(OUT/'anchors.csv',index=False);rng=np.random.default_rng(42);fake=[]
    for r in anchors.itertuples():
        roots=pd.to_datetime(anchors[anchors.year.eq(r.year)].date);possible=[]
        for shift in [-42,-35,-28,28,35,42]:
            moved=pd.Timestamp(r.date)+pd.Timedelta(days=shift)
            if moved.year==r.year and (moved-pd.Timedelta(days=3)).year==r.year and (moved+pd.Timedelta(days=3)).year==r.year and all(abs((moved-d).days)>6 for d in roots):possible.append(shift)
        if not possible:raise ValueError(('No fixed weekday placebo',r.year,r.family))
        shift=int(rng.choice(possible));fake.append(dict(year=r.year,family=r.family,date=str((pd.Timestamp(r.date)+pd.Timedelta(days=shift)).date()),original_date=r.date,shift_days=shift))
    pd.DataFrame(fake).to_csv(OUT/'placebos.csv',index=False)
    fixed=json.loads((ROOT/'results/stable_tree_refit_v2/protocol.json').read_text())['lightgbm_fixed']
    files=['src/mta_holiday_study.py','src/mta_model_engine_v1.py','src/test_mta_holiday_study.py','src/forecasting.py','src/robust_baselines.py','src/multifestival_models.py',
        'results/mechanism_controls_v1/chronos_download.json','results/second_model_audit_v1/weight_download.json','results/mta_holiday_v1/anchors.csv','results/mta_holiday_v1/placebos.csv']+[str(p.relative_to(ROOT)) for p in evidence.iterdir()]
    protocols={}
    for cohort in ['event_window','ordinary']:
        out=OUT/cohort;out.mkdir();cases=cases_for(cohort)
        for f in ['primary_cases.csv','window_cases.csv']:cases.to_csv(out/f,index=False)
        p=dict(created_utc=datetime.now(timezone.utc).isoformat(),experiment=OUT.name+'/'+cohort,
            status='Methods/cases fixed BEFORE requesting any2026date/count records. Source metadata/mode-onlyenum and calendar PDFs inspected; older deprecated2022–Jan2025probe already seen. New-to-analyst2026outcomes, but globalmethods follow inspectedIndiaresults and remain exploratory; no external preregistration/operationalclean-test claim.',
            target='ProviderdailyestimatedCount for exactlySubway/Bus, dividedby1million. Traveldate, not publicationdate; countswipes/taps/estimatedcashfares, not uniquepeople/latentdemand. Do not add SIR toSubway. ActualAPI ModeTEXT verified despite erroneousNUMERICdictionary. Allmethods samepositive recordedtarget labels, missinglabelsnever scored.',
            source='CanonicalMTA sayj-mze2 ondata.ny.gov; a singlecurrentprimarylineage, no deprecatedseries splice. Completequery2023-01-01 through2026-10-21 forSubway/Busonly, limit5000/orderdate+mode; assertnottruncated/duplicates/coverage/fixedtargetlabels. Currentrevisedestimates/nextdayversusofficialtotals uncertainty retained.',
            reuse='AttachedproviderOverview says There are no limitations on the data at this time. Retainattribution/sourceURL/hash/statement; no newCCBY/OGLlicence invented. Publish minimalfilteredsource records and two-series derived snapshot for reproducibility, excluding unrelatedmodes. This doesnot grant rights forIndiancompilation.',
            cases='84eventcases:two2026eventoccurrences(YomKippur21Sep,ColumbusDay12Oct), seven±3daytargets each, two relatedNYCmodes and3decisionleads.42ordinarycases:firsteligible date perweekday15Sep–28Oct, excluding±3daysaround ALLSeptember/OctoberDOTobservances, not just modelledfamilies. Onecity/year/twoevents, not84independent events or twoindependentgeographies.',
            availability='Sevenadditionalcalendar-day observationbuffer:decisionorigin=firstunseen decisiondateD, modelorigin=D-7, recordedcontextendsD-8. Decisionleads1/7/14 maptoactualmodelsteps8/14/21. Sevenbridge predictionsunscored. Allactualdecisions afterbothmodelreleases; bufferis a fixedsensitivity to nextday/weekdaypublication, not first-vintage reconstruction or certified realtimeavailability.',
            calendar='FiveNYCDOTobservancefamilies2024–2026:LaborDay,YomKippur,ColumbusDay,Thanksgiving,Christmas. Exactselecteddates visuallychecked againstprimaryPDFs; pre-year archivedofficialdocuments have CDXdigestmatches. Parkingobservanceis not MTAserviceclosure or statewide response. H/windowcovers onlythese5families, otherobservances/operationalconfounders remain.',
            arms=ARMS,foundation_arms=FOUNDATION_ARMS,models=MODELS,context=730,horizon=21,batch=16,threads=2,seed=42,
            expected_tasks=len(cases[['state','origin']].drop_duplicates()),cases_per_arm=len(cases),
            features='Same13weekday/annualharmoniccalendar plus5typed/pooled/zero/placebo channels; pooled=union+4zeros. History-only reference additionallyforbothfoundations; localsretain8commonarms. SameNYCcalendar/placeboforbothrelatedmodes. Placebos±28/35/42days avoidregistered5familywindows, not every otherNYCobservance; onefixedseednot randomisationdistribution.',
            local='27pasthistory+samecalendar/eventfeatures; monthlyrefits bymodeloriginmonth, strictactualmodelleadpurging. Ridge/treeparameters selected oncalendarONLYbeforequeriedcontexts, thenunchangedacrossallarms. Fixedleaf2sensitivity; no arm-specificsearch. SARIMAX(1,0,0)x(1,0,0,7), monthly730dayfits/pastupdates, targetinmillionrides(no100GWhnormalisation), convergence-onlyretries retained.',
            selection='Eachmode/effectivelead8/14/21:trainbefore1Jan2026, validateorigin/targets1Jan–30Jun2026; allvalidationlabels strictlybefore earliestmodelcontext cutoff. Ridgealpha[.1,1,10,100]; treeleaves[7,15]xestimators[100,300]xL2[1,10], minleaf20. Stabletieorder;72past-onlyfits, noSeptember/Octobertuning.',
            metrics='Pre2026weeklydifference scale over730calendar days ending31Dec2025, recordedlabels only. MAE_million_rides/MASE perdecisionlead, equalrelatedmodes/year/families. Nativecommon0.1–0.9 pinball/80coverage/scaledwidth/WIS; allcrossings retained, invalid80propagatesundefinedaggregate. Bothfamilies and composition sensitivities, no independent-row significance.',
            exposure='PinnedunchangedChronos2/TimesFM3weights verifiedagainstactualbytes. Targetdates/decisiondates postdate uploads/announcements; unknown historical/proxyoverlap and revisedcontextvintages prevent contamination-free claim. No futureIndianactual retrieval or oldforecast/annex/workflowchange.',
            lightgbm_fixed=fixed,python=sys.version,packages={name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','scikit-learn','lightgbm','statsmodels','torch','chronos-forecasting','timesfm']},
            runtime='CPUonly,4corequota; eachprovider2threads/batch16, serialbehinditspriorregisteredlane. Foundationinputsfloat32, Ridgefloat64, treefloat32. No fine-tuning or resourceconfigurationchange.',
            input_hashes={f:sha(ROOT/f) for f in files},design_hashes={f:sha(out/f) for f in ['primary_cases.csv','window_cases.csv']})
        dump(out/'protocol.json',p);protocols[cohort]=sha(out/'protocol.json')
    dump(OUT/'registration.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),status='BEFORE_TARGET_DATE_COUNT_RECORDS',protocols=protocols,planned_model_rows=6300,planned_naive_rows=252,source_dataset='sayj-mze2',target_unit='millionestimatedrides',source_independence='NYCMTA primarytransportation lineage independent ofIndianGRID andNESOelectricity; two relatedmodes/onecity are not independentgeographies.'))
    print('FROZEN6300model+252naiveforecasts before newtargetrecords')


def acquire():
    if (OUT/'acquisition_started.json').exists():raise FileExistsError('Preserve firstacquisition/failedattempts')
    assert json.loads((OUT/'registration.json').read_text())['status']=='BEFORE_TARGET_DATE_COUNT_RECORDS'
    dump(OUT/'acquisition_started.json',dict(started_utc=datetime.now(timezone.utc).isoformat()))
    query={'$select':'date,mode,count','$where':"date >= '2023-01-01T00:00:00' AND date < '2026-10-22T00:00:00' AND mode in ('Subway','Bus')",'$order':'date,mode','$limit':'5000'}
    url='https://data.ny.gov/resource/sayj-mze2.json?'+urllib.parse.urlencode(query);attempts=[]
    try:
        for attempt in [1,2]:
            try:
                with urllib.request.urlopen(url,timeout=45) as response:raw=response.read(4*1024*1024+1);assert response.status==200
                assert len(raw)<=4*1024*1024;records=json.loads(raw);assert isinstance(records,list) and 0<len(records)<5000
                attempts.append(dict(attempt=attempt,status='downloaded',retrieved_utc=datetime.now(timezone.utc).isoformat()));break
            except Exception as e:
                attempts.append(dict(attempt=attempt,status='failed',error=repr(e),observed_utc=datetime.now(timezone.utc).isoformat()));dump(OUT/'acquisition_attempts.json',attempts)
                if attempt==2:raise
                time.sleep(2)
        (OUT/'source_records.json').write_bytes(raw);d=parse_source(records)
        assert d.index.min()==pd.Timestamp('2023-01-01') and d.index.max()==pd.Timestamp('2026-10-21')
        assert all(d.loc[pd.Timestamp(r.date),r.state]>0 for c in ['event_window','ordinary'] for r in cases_for(c).itertuples())
        d.to_csv(OUT/'source_snapshot_million_rides.csv');dump(OUT/'acquisition_attempts.json',attempts)
        dump(OUT/'snapshot.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),url=url,query=query,raw_sha256=sha(OUT/'source_records.json'),daily_sha256=sha(OUT/'source_snapshot_million_rides.csv'),source_rows=len(records),daily_rows=len(d),date_min=str(d.index.min().date()),date_max=str(d.index.max().date()),missing_by_series=d.isna().sum().astype(int).to_dict(),unit='millionestimatedrides',publication='Minimalfilteredfactualsnapshot underproviderOverview no-limitationsstatement, with attribution; no newstandardlicence granted. Currentrevisedvintage.'))
        print('Acquired filteredsource; fixedrecordedtargets complete, no targetvalues printed')
    except BaseException:(OUT/'acquisition_failure.txt').write_text(traceback.format_exc());raise


def load_source():
    s=json.loads((OUT/'snapshot.json').read_text());assert sha(OUT/'source_records.json')==s['raw_sha256'] and sha(OUT/'source_snapshot_million_rides.csv')==s['daily_sha256']
    return pd.read_csv(OUT/'source_snapshot_million_rides.csv',index_col=0,parse_dates=True).asfreq('D').where(lambda x:x>0)


def frames(index,state):
    columns={f'dow_{j}':(index.dayofweek==j).astype(float) for j in range(7)}
    for j in [1,2,3]:columns.update({f'sin_{j}':np.sin(2*np.pi*j*index.dayofyear/365.2425),f'cos_{j}':np.cos(2*np.pi*j*index.dayofyear/365.2425)})
    base=pd.DataFrame(columns,index=index);result={'history':pd.DataFrame(index=index),'calendar':base,'zero5':pd.concat([base,pd.DataFrame(0.,index=index,columns=[f'zero_{j}' for j in range(5)])],axis=1)}
    for prefix,file in [('',OUT/'anchors.csv'),('placebo_',OUT/'placebos.csv')]:
        ledger=pd.read_csv(file,parse_dates=['date'])
        for kind in ['day','window']:
            event={}
            for family in FAMILIES:
                roots=ledger[ledger.family.eq(family)].date;dates=roots if kind=='day' else [d for r in roots for d in pd.date_range(r-pd.Timedelta(days=3),r+pd.Timedelta(days=3))]
                event[family+'_'+kind]=index.isin(dates).astype(float)
            typed=pd.DataFrame(event,index=index);result[prefix+kind+'5']=pd.concat([base,typed],axis=1)
            if not prefix:
                pooled=pd.DataFrame({'event_'+kind:typed.any(axis=1).astype(float)},index=index)
                for j in range(1,5):pooled['padding_'+str(j)]=0.
                result['pooled_'+kind+'5']=pd.concat([base,pooled],axis=1)
    return result


def build_input(observed,frame,origin,horizon):
    dates=pd.date_range(origin-pd.Timedelta(days=730),periods=730+horizon)
    assert pd.Timestamp('2024-01-01')<=dates.min()<=dates.max()<=pd.Timestamp('2026-12-31')
    target=causal_fill(observed).reindex(dates[:730]).to_numpy(dtype=np.float32);cov=frame.reindex(dates).to_numpy(dtype=np.float32).T
    assert target.shape==(730,) and np.isfinite(target).all() and np.isfinite(cov).all()
    return target,cov


def design(observed,h,arm):
    from robust_baselines import rich_history
    index=pd.date_range(observed.index.min(),observed.index.max()+pd.Timedelta(days=20));f=frames(index,None)[arm].reindex(observed.index+pd.Timedelta(days=h-1)).copy();f.index=observed.index
    return pd.concat([rich_history(observed,h),f],axis=1)


def select():
    from robust_baselines import fitting_cases,make_model
    if (OUT/'selection_started.json').exists():raise FileExistsError('Preserve selection attempts')
    dump(OUT/'selection_started.json',dict(started_utc=datetime.now(timezone.utc).isoformat()));p=json.loads((OUT/'event_window/protocol.json').read_text());data=load_source();selected={};logs=[]
    try:
        for state in data:
            observed=data[state]
            for h in [8,14,21]:
                base=design(observed,h,'calendar');origins=pd.date_range('2026-01-01',pd.Timestamp('2026-06-30')-pd.Timedelta(days=h-1));dates=origins+pd.Timedelta(days=h-1)
                for model in ['ridge','lightgbm']:
                    x=base if model=='ridge' else base.astype(np.float32);xx,yy,log=fitting_cases(x,observed,h,pd.Timestamp('2025-12-31'));vx=x.reindex(origins).to_numpy();vy=observed.reindex(dates).to_numpy();valid=np.isfinite(vx).all(axis=1)&np.isfinite(vy)
                    grid=[dict(alpha=a) for a in [.1,1.,10.,100.]] if model=='ridge' else [dict(num_leaves=l,n_estimators=n,reg_lambda=z,min_child_samples=20) for l,n,z in itertools.product([7,15],[100,300],[1.,10.])];trials=[]
                    for j,params in enumerate(grid):
                        pred=make_model(model,params,p).fit(xx,yy).predict(vx[valid]);r=dict(state=state,model=model,horizon=h,configuration=j,parameters=params,validation_MAE_million_rides=float(np.mean(abs(pred-vy[valid]))),validation_n=int(valid.sum()),validation_target_max=str(dates[valid].max().date()),training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),**log);logs.append(r);trials.append(r)
                    winner=min(trials,key=lambda r:(r['validation_MAE_million_rides'],r['configuration']));selected[f'{state}:{model}:{h}']=winner['parameters'];dump(OUT/'selection_attempts.json',logs)
        assert len(logs)==72;dump(OUT/'selection.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),parameters=selected,attempts=logs,snapshot_sha256=sha(OUT/'snapshot.json'),policy='Calendar-onlypastJanuary–Juneselection; no newevent-cohort search'))
    except BaseException:(OUT/'selection_failure.txt').write_text(traceback.format_exc());raise


def regression(cohort,worker):
    from robust_baselines import fitting_cases,make_model
    import mta_model_engine_v1 as engine
    engine.OUT=OUT/cohort;p,out,cases,data=engine.setup(worker);selected=json.loads((OUT/'selection.json').read_text())['parameters'];model='ridge' if worker=='ridge' else 'lightgbm';rows=[];fits=[]
    try:
        for (state,h),group in cases.groupby(['state','horizon']):
            observed=data[state];params=selected[f'{state}:{model}:{int(h)}'].copy()
            if worker=='lightgbm_capacity2':params['min_child_samples']=2
            for arm in ARMS:
                x=design(observed,int(h),arm);x=x.astype(np.float32) if model=='lightgbm' else x
                for month,g in group.groupby(group.origin.dt.to_period('M')):
                    cutoff=pd.Timestamp(month.start_time)-pd.Timedelta(days=1);xx,yy,log=fitting_cases(x,observed,int(h),cutoff);query=x.reindex(pd.DatetimeIndex(g.origin)).to_numpy();pred=make_model(model,params,p).fit(xx,yy).predict(query)
                    assert pd.Timestamp(log['training_target_max'])<=cutoff<g.origin.min();a=g.copy();a['prediction']=pred;a['actual']=observed.reindex(pd.DatetimeIndex(g.date)).to_numpy();a['mase_scale']=engine.scale(data,state,2026);a['model']=worker;a['arm']=arm;rows.append(a)
                    fits.append(dict(state=state,horizon=int(h),arm=arm,refit=str((cutoff+pd.Timedelta(days=1)).date()),parameters=params,feature_count=xx.shape[1],training_X_sha256=hashlib.sha256(xx.tobytes()).hexdigest(),training_y_sha256=hashlib.sha256(yy.tobytes()).hexdigest(),query_X_sha256=hashlib.sha256(query.tobytes()).hexdigest(),extra_nonzero_counts=np.count_nonzero(xx[:,40:],axis=0).tolist(),**log))
                pd.concat(rows).to_csv(out/'checkpoint.csv',index=False);dump(out/'fit_log.json',fits)
        d=pd.concat(rows);assert len(d)==len(cases)*8 and np.isfinite(d.prediction).all();d.to_csv(out/'predictions.csv',index=False);dump(out/'run.json',dict(model=worker,completed_utc=datetime.now(timezone.utc).isoformat(),rows=len(d),fits=len(fits),predictions_sha256=sha(out/'predictions.csv'),protocol_sha256=sha(OUT/cohort/'protocol.json')))
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());dump(out/'fit_log.json',fits);raise


def sarimax(cohort):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from multifestival_models import fit_checked
    import mta_model_engine_v1 as engine
    engine.OUT=OUT/cohort;p,out,cases,data=engine.setup('sarimax');rows=[];attempts=[];updates=[];index=pd.date_range(data.index.min(),data.index.max()+pd.Timedelta(days=20));fc=frames(index,None)
    try:
        for state,gstate in cases.groupby('state'):
            observed=data[state];y=causal_fill(observed)
            for month,group in gstate.groupby(gstate.origin.dt.to_period('M')):
                cutoff=pd.Timestamp(month.start_time)-pd.Timedelta(days=1);tr=y.loc[cutoff-pd.Timedelta(days=729):cutoff]
                for arm in ARMS:
                    exog=fc[arm];fit=fit_checked(SARIMAX(tr,exog=exog.reindex(tr.index),order=(1,0,0),seasonal_order=(1,0,0,7),trend='n',enforce_stationarity=False),'sarimax',attempts,dict(configuration=arm,state=state,year=2026,refit=str((cutoff+pd.Timedelta(days=1)).date()),training_end=str(cutoff.date())));previous=cutoff+pd.Timedelta(days=1)
                    for origin in sorted(group.origin.unique()):
                        origin=pd.Timestamp(origin);new=y.loc[previous:origin-pd.Timedelta(days=1)]
                        if len(new):fit=fit.extend(new,exog=exog.reindex(new.index))
                        future=pd.date_range(origin,periods=21);pred=np.asarray(fit.forecast(21,exog=exog.reindex(future)));a=group[group.origin.eq(origin)].copy();a['prediction']=[pred[int(h)-1] for h in a.horizon];a['actual']=observed.reindex(pd.DatetimeIndex(a.date)).to_numpy();a['mase_scale']=engine.scale(data,state,2026);a['model']='sarimax';a['arm']=arm;rows.append(a)
                        updates.append(dict(arm=arm,state=state,origin=str(origin.date()),training_end=str(cutoff.date()),context_end=str((origin-pd.Timedelta(days=1)).date())));previous=origin
                    pd.concat(rows).to_csv(out/'checkpoint.csv',index=False);dump(out/'fit_attempts.json',attempts);dump(out/'deployments.json',updates)
        d=pd.concat(rows);assert len(d)==len(cases)*8 and np.isfinite(d.prediction).all();d.to_csv(out/'predictions.csv',index=False);dump(out/'run.json',dict(model='sarimax',completed_utc=datetime.now(timezone.utc).isoformat(),rows=len(d),attempts=len(attempts),predictions_sha256=sha(out/'predictions.csv'),protocol_sha256=sha(OUT/cohort/'protocol.json')))
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());dump(out/'fit_attempts.json',attempts);raise


def run(cohort,worker):
    reg=json.loads((OUT/'registration.json').read_text());assert sha(OUT/cohort/'protocol.json')==reg['protocols'][cohort]
    if worker in ['chronos','timesfm']:
        import mta_model_engine_v1 as engine
        engine.OUT=OUT/cohort;engine.ARMS=FOUNDATION_ARMS;engine.frames=frames;engine.foundation(worker)
    elif worker=='sarimax':sarimax(cohort)
    else:regression(cohort,worker)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','acquire','select',*MODELS]);p.add_argument('--cohort',choices=['event_window','ordinary'],default='event_window');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='acquire':acquire()
    elif a.action=='select':select()
    else:run(a.cohort,a.action)
