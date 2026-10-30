"""Past-only daily adaptations of established target encoding and response profiles."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
import pandas as pd
from breadth_study import ROOT, OUT as BREADTH
from festival_feature_design import KEY, sha, dump, FAMILIES
from forecasting import load_data
from report_multifestival import markdown

OUT=ROOT/'results/event_comparators_v1'
METHODS=['weekday_mean','holiday_as_sunday_mean','holiday_separate_mean',
         'weekday_holiday_joint_mean','response_none','response_typed',
         'response_pooled','response_partial']


def kernel(dates,state,ledger):
    x=np.zeros((len(dates),len(FAMILIES)))
    for j,family in enumerate(FAMILIES):
        anchors=ledger[ledger.state.eq(state)&ledger.family.eq(family)].date
        for offset,weight in zip(range(-3,4),[.2,.5,.8,1.,.8,.5,.2]):
            # Max within family avoids counting overlapping subsidiary windows twice.
            x[:,j]=np.maximum(x[:,j],dates.isin(anchors+pd.Timedelta(days=offset))*weight)
    return x


def fit_responses(x,residual,penalty=2.):
    good=np.isfinite(residual)&np.isfinite(x).all(axis=1)
    xx,yy=x[good],residual[good]
    pooled_x=xx.sum(axis=1)
    denominator=float(pooled_x@pooled_x)
    pooled=float(pooled_x@yy/denominator) if denominator else 0.
    typed=np.linalg.lstsq(xx,yy,rcond=None)[0]
    partial=np.linalg.solve(xx.T@xx+penalty*np.eye(xx.shape[1]),xx.T@yy+penalty*pooled*np.ones(xx.shape[1]))
    return typed,pooled,partial,good


def encoding_prediction(y,holiday,query_weekday,query_holiday,method):
    # y contains only recorded targets STRICTLY before the current origin.
    dow=y.index.dayofweek.to_numpy()
    if method=='weekday_mean':
        codes=dow; query=query_weekday
    elif method=='holiday_as_sunday_mean':
        codes=np.where(holiday,6,dow); query=6 if query_holiday else query_weekday
    elif method=='holiday_separate_mean':
        codes=np.where(holiday,7,dow); query=7 if query_holiday else query_weekday
    elif method=='weekday_holiday_joint_mean':
        codes=dow+7*holiday.astype(int); query=query_weekday+7*int(query_holiday)
    else:
        raise ValueError(method)
    match=y.to_numpy()[codes==query]
    if len(match):
        return float(np.mean(match)),len(match),'exact_category'
    fallback=y.to_numpy()[dow==query_weekday]
    return (float(np.mean(fallback)),len(fallback),'weekday_fallback') if len(fallback) else (float(y.mean()),len(y),'global_fallback')


def prepare():
    if OUT.exists(): raise FileExistsError('Preserve the registered study')
    OUT.mkdir()
    files=['src/event_comparators.py','src/test_event_comparators.py',
        'data/external/latest_state_energy_GWh.csv','results/festival_features_v1/anchors_2022_2025.csv']
    for cohort in ['event_window','ordinary']:
        files.append(f'results/feature_breadth_v1/{cohort}/primary_cases.csv')
    dump(OUT/'protocol.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory; rules fixed before new comparator forecasts; historical outcomes and prior studies already inspected.',
        methods=METHODS,planned_rows=8*(528+216),cohorts=['event_window','ordinary'],
        target='Same recorded daily supplied energy and exact cases/scales as the registered breadth study.',
        literature=[dict(url='https://arxiv.org/html/2610.13676v1',section='3.1 and Appendix A.1.1',
            adaptation='Daily hour omitted; weekday/holiday conditional means, holiday-as-Sunday and separate category. Direct point baselines; not a reproduction of the paper hourly multivariate TSFM experiment.'),
            dict(url='https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models',
            adaptation='Simple past residual event-response profiles, not the published neural/contrastive learned covariate system or an exact paper replication.')],
        target_encoding='Rolling730calendar days, strictly pre-origin, positive recorded labels only; context-mean categories. Holiday=any frozen named family anchor (not every office closure). Joint category falls back to same weekday, then global mean. No future-target encoding, cross-validation or parameter selection.',
        response_profile='Known fixed triangular+/-3day shape [.2,.5,.8,1,.8,.5,.2]. Max across subsidiary windows within each family; sum family effects. Residual at past date=recorded energy minus mean of up to4recorded same-weekday values7/14/21/28days earlier, at least1required. Query baseline=last4recorded same-weekday observations strictly before origin; no unavailable week-ahead values.',
        estimation='OLS separate5family amplitudes; OLS pooled scalar; partial pooling solve(XTX+2I)b=XTr+2*pooled*ones. Fixed penalty2, no error-based choice. No-response uses the exact same four-weekday baseline. Same rolling labels and event information for all3profile methods; no intercept.',
        interpretation='These are established-method daily adaptations and local point comparators, not new TSFM representations or full closest-paper replications. Different fitting assumptions/refit frequencies remain explicit. Historical/proxy/source/rights limits unchanged. Generic encodings/pooling/shrinkage/residual profiles are not new inventions.',
        input_hashes={f:sha(ROOT/f) for f in files}))
    print('FROZEN eight daily comparator specifications,5952forecast rows')


def run():
    p=json.loads((OUT/'protocol.json').read_text())
    for f,h in p['input_hashes'].items(): assert sha(ROOT/f)==h,f
    if (OUT/'started.json').exists(): raise FileExistsError('Preserve started/completed worker')
    dump(OUT/'started.json',dict(started_utc=datetime.now(timezone.utc).isoformat()))
    data=load_data('latest')
    ledger=pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv',parse_dates=['date'])
    rows,logs=[],[]
    for cohort in p['cohorts']:
        cases=pd.read_csv(BREADTH/cohort/'primary_cases.csv',parse_dates=['date','origin'])
        for state,group in cases.groupby('state'):
            observed=data[state].where(data[state].gt(0))
            past=pd.concat([observed.shift(k) for k in [7,14,21,28]],axis=1).mean(axis=1)
            residual=observed-past
            for origin,g in group.groupby('origin'):
                dates=pd.date_range(origin-pd.Timedelta(days=730),periods=730)
                assert dates.min()>=pd.Timestamp('2022-01-01')
                y=observed.reindex(dates).dropna()
                holiday_dates=ledger[ledger.state.eq(state)].date
                holiday=y.index.isin(holiday_dates)
                x=kernel(dates,state,ledger)
                r=residual.reindex(dates).to_numpy()
                typed,pooled,partial,good=fit_responses(x,r)
                assert y.index.max()<origin
                logs.append(dict(cohort=cohort,state=state,origin=str(origin.date()),
                    max_encoding_label=str(y.index.max().date()),max_profile_label=str(dates[good].max().date()),
                    encoding_labels=len(y),profile_labels=int(good.sum()),family_support=np.count_nonzero(x[good],axis=0).tolist(),
                    profile_X_sha256=hashlib.sha256(x[good].tobytes()).hexdigest(),
                    profile_y_sha256=hashlib.sha256(r[good].tobytes()).hexdigest(),
                    typed=typed.tolist(),pooled=pooled,partial=partial.tolist()))
                for row in g.itertuples(index=False):
                    query_holiday=row.date in set(holiday_dates)
                    query=kernel(pd.DatetimeIndex([row.date]),state,ledger)[0]
                    same=observed.loc[:origin-pd.Timedelta(days=1)]
                    same=same[same.index.dayofweek==row.date.weekday()].dropna().tail(4)
                    assert len(same)==4 and same.index.max()<origin
                    base=float(same.mean())
                    end=pd.Timestamp(f'{row.year-1}-12-31')
                    tr=observed.loc[end-pd.Timedelta(days=729):end]
                    scale=float((tr-tr.shift(7)).abs().mean())
                    for method in METHODS:
                        n,backoff=0,'not_target_encoding'
                        if method in METHODS[:4]:
                            predicted,n,backoff=encoding_prediction(y,holiday,row.date.weekday(),query_holiday,method)
                        else:
                            effect={'response_none':0.,'response_typed':float(query@typed),
                                'response_pooled':float(query.sum()*pooled),'response_partial':float(query@partial)}[method]
                            predicted=base+effect
                        rows.append(dict(cohort=cohort,**{k:getattr(row,k) for k in KEY},method=method,
                            prediction=predicted,actual=float(observed.loc[row.date]),mase_scale=scale,
                            encoding_category_n=n,encoding_backoff=backoff,baseline_GWh=base))
        pd.DataFrame(rows).to_csv(OUT/'checkpoint.csv',index=False)
        dump(OUT/'fit_log.json',logs)
        print(cohort,'complete',flush=True)
    d=pd.DataFrame(rows)
    assert len(d)==p['planned_rows'] and np.isfinite(d[['prediction','actual','mase_scale']]).all().all()
    d.to_csv(OUT/'predictions.csv',index=False)
    d['MASE']=abs(d.prediction-d.actual)/d.mase_scale
    cell=d.groupby(['cohort','family','method','state','year','horizon']).MASE.mean().reset_index()
    cell.to_csv(OUT/'metrics_state_year.csv',index=False)
    year=cell.groupby(['cohort','family','method','year','horizon']).MASE.mean().reset_index()
    fam=year.groupby(['cohort','family','method','horizon']).MASE.mean().reset_index()
    macro=fam.groupby(['cohort','method','horizon']).MASE.mean().reset_index()
    year.to_csv(OUT/'metrics_year.csv',index=False)
    fam.to_csv(OUT/'metrics_festival.csv',index=False)
    macro.to_csv(OUT/'metrics_balanced.csv',index=False)
    lines=['# Daily target-encoding and event-response comparators','',p['status'],'',p['interpretation'],'']
    for cohort in p['cohorts']:
        table=macro[macro.cohort.eq(cohort)].pivot(index='method',columns='horizon',values='MASE').reindex(METHODS)
        table.columns=[f'Lead {c}' for c in table.columns]
        lines += ['## '+cohort,'',markdown(table.round(5).reset_index()),'']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(OUT/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),
        rows=len(d),fit_contexts=len(logs),protocol_sha256=sha(OUT/'protocol.json'),predictions_sha256=sha(OUT/'predictions.csv')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','run'])
    prepare() if parser.parse_args().action=='prepare' else run()
