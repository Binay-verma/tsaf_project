"""Fixed bias/variance/date-error simulation; not a foundation-model mechanism test."""
import argparse,itertools,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from event_comparators import fit_responses
from festival_feature_design import ROOT,sha,dump
from report_multifestival import markdown

OUT=ROOT/'results/pooling_simulation_v1'


def generate(seed,frequency,heterogeneity,date_error,noise):
    rng=np.random.default_rng(seed)
    n=1095;truth=np.zeros((n,5));observed=np.zeros_like(truth)
    events=[]
    for year in range(3):
        centers=np.linspace(14,350,5*frequency).astype(int)+rng.integers(-3,4,size=5*frequency)
        for j,center in enumerate(centers):
            family=j%5;day=year*365+int(center)
            error=int(rng.integers(-date_error,date_error+1)) if date_error else 0
            for k,w in zip(range(-3,4),[.2,.5,.8,1.,.8,.5,.2]):
                truth[day+k,family]=max(truth[day+k,family],w)
                observed[day+error+k,family]=max(observed[day+error+k,family],w)
            events.append((day,family,error))
    beta=-3.+heterogeneity*np.array([-2.,-1.,0.,1.,2.])
    innovation=rng.normal(0,noise*np.sqrt(1-.5**2),n)
    epsilon=np.zeros(n);epsilon[0]=rng.normal(0,noise)
    for i in range(1,n):epsilon[i]=.5*epsilon[i-1]+innovation[i]
    # Known baseline removed exactly to isolate event-effect estimation.
    residual=truth@beta+epsilon
    return truth,observed,residual,beta,events


def prepare():
    if OUT.exists():raise FileExistsError('Preserve registered scenarios/results')
    OUT.mkdir()
    dump(OUT/'protocol.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Controlled exploratory simulation registered before its outputs; informed by earlier real-data hypotheses. Established pooling/shrinkage, no novelty claim.',
        scenarios=[dict(frequency=f,heterogeneity=h,date_error=d,noise=n)
            for f,h,d,n in itertools.product([1,4],[0.,3.],[0,2],[1.,3.])],
        seeds=list(range(20261000,20261032)),train_days=730,test_days=365,
        design='Five event types;1or4occurrences per family per365days. Equally spaced dates with fixed seed jitter+/-3days; no response-based placement. True+/-3triangular response shape [.2,.5,.8,1,.8,.5,.2]. Family amplitudes=-3+heterogeneity*[-2,-1,0,1,2]. Independent per-occurrence registered-date errors uniform integer+/-0or2days, train and test. Noise stationary AR1(phi=.5), marginal SD1or3. Known non-event baseline is removed exactly; no time-series baseline estimation.',
        methods=['no_event','pooled_OLS','typed_OLS','partial_pooling_fixed2','oracle_true_effect'],
        estimation='Only first730days fit. Same noisy dates/labels for all learned methods. Partial penalty2 toward fitted pooled amplitude, fixed before results. Oracle has true amplitudes/dates and is labelled unavailable reference, not competitor. No tuning, TSFM inference or architecture-mechanism conclusion.',
        metrics='Test365daily absolute error, separately trueevent-window/non-event and all days; coefficient mean square error. Complete seed/scenario/method cells. Paired seed differences with mean+/-1.96MCstandarderror across32independent generators describe MonteCarlo precision only; do not use them for Indian event significance.',
        input_hashes={f:sha(ROOT/f) for f in ['src/pooling_simulation.py','src/test_pooling_simulation.py','src/event_comparators.py']}))
    print('FROZEN16scenarios x32seeds x5methods =2560simulation cells')


def run():
    p=json.loads((OUT/'protocol.json').read_text())
    for f,h in p['input_hashes'].items():assert sha(ROOT/f)==h
    if (OUT/'run.json').exists():raise FileExistsError('Preserve completed results')
    rows=[]
    for scenario in p['scenarios']:
        for seed in p['seeds']:
            truth,x,y,beta,events=generate(seed,**scenario)
            typed,pooled,partial,good=fit_responses(x[:730],y[:730])
            coefficients={'no_event':np.zeros(5),'pooled_OLS':np.repeat(pooled,5),
                'typed_OLS':typed,'partial_pooling_fixed2':partial,'oracle_true_effect':beta}
            event=truth[730:].any(axis=1)
            assert 0<event.sum()<365 and good.sum()==730
            for method,b in coefficients.items():
                prediction=(truth if method=='oracle_true_effect' else x)[730:]@b
                error=abs(y[730:]-prediction)
                rows.append(dict(**scenario,seed=seed,method=method,MAE_all=float(error.mean()),
                    MAE_event=float(error[event].mean()),MAE_ordinary=float(error[~event].mean()),
                    coefficient_MSE=float(np.mean((b-beta)**2)),event_test_days=int(event.sum()),
                    train_events=sum(t<730 for t,f,e in events),test_events=sum(t>=730 for t,f,e in events)))
    d=pd.DataFrame(rows);assert len(d)==2560
    d.to_csv(OUT/'seed_results.csv',index=False)
    keys=['frequency','heterogeneity','date_error','noise']
    summary=d.groupby(keys+['method'])[['MAE_all','MAE_event','MAE_ordinary','coefficient_MSE']].mean().reset_index()
    summary.to_csv(OUT/'summary.csv',index=False)
    pairs=[]
    for arm,ref in [('typed_OLS','pooled_OLS'),('partial_pooling_fixed2','pooled_OLS'),('partial_pooling_fixed2','typed_OLS')]:
        a=d[d.method.eq(arm)].merge(d[d.method.eq(ref)],on=keys+['seed'],suffixes=('_arm','_ref'),validate='one_to_one')
        a['difference']=a.MAE_event_arm-a.MAE_event_ref
        for setting,g in a.groupby(keys):
            delta=float(g.difference.mean());se=float(g.difference.std(ddof=1)/np.sqrt(len(g)))
            pairs.append(dict(zip(keys,setting))|dict(arm=arm,reference=ref,n_seeds=len(g),event_MAE_difference=delta,
                MC_standard_error=se,MC95_low=delta-1.96*se,MC95_high=delta+1.96*se))
    contrasts=pd.DataFrame(pairs);contrasts.to_csv(OUT/'paired_seed_contrasts.csv',index=False)
    lines=['# Pooling under sparse support, response heterogeneity and date error','',p['status'],'',
        '512synthetic datasets;2560method cells. The known baseline isolates event-effect estimation. This does not reproduce the behaviour of either foundation model or add independent real-world events. Lower error is better. Oracle is an unavailable reference.','',markdown(summary.round(5)),'',
        '## Paired contrasts','',markdown(contrasts.round(5)),'',p['metrics'],'',
        'Pooling and shrinkage have established bias/variance explanations. Any pattern here is conditional on this declared generator, known shape/baseline and fixed penalty, not evidence of a new method or universal identity mechanism.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(OUT/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),
        rows=len(d),synthetic_datasets=512,protocol_sha256=sha(OUT/'protocol.json'),seed_results_sha256=sha(OUT/'seed_results.csv')))
    print('Complete2560simulation cells; no outcome-based selection')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run'])
    prepare() if p.parse_args().action=='prepare' else run()
