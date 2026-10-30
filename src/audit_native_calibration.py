"""Separate stdlib reconstruction of calibration/annex intervals and scores."""
from collections import defaultdict
import csv
from datetime import date,datetime,timedelta,timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
import subprocess
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_calibration_v1'
ANNEX=ROOT/'results/prospective_interval_20261030_v1'


def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-9),(a,b)


def key(r):return r['configuration'],r['state'],r['origin'],r['date'],int(r['horizon'])


def main():
    p=json.loads((OUT/'protocol.json').read_text())
    for name,h in p['input_hashes'].items():assert sha(ROOT/name)==h,name
    for name,h in p['design_hashes'].items():assert sha(OUT/name)==h,name
    protected=json.loads((OUT/'protected_prior_files.json').read_text())
    for name,h in protected.items():assert sha(ROOT/name)==h,name
    source=read(ROOT/'data/external/latest_state_energy_GWh.csv');datecol=next(iter(source[0]));labels={}
    for r in source:
        for state in ['Delhi','Karnataka','Maharashtra']:
            if r[state] and math.isfinite(float(r[state])) and float(r[state])>0:labels[state,r[datecol]]=float(r[state])
    scales={}
    start=date(2024,1,2)
    for state in ['Delhi','Karnataka','Maharashtra']:
        diffs=[]
        for i in range(7,730):
            a=(start+timedelta(days=i)).isoformat();b=(start+timedelta(days=i-7)).isoformat()
            if (state,a) in labels and (state,b) in labels:diffs.append(abs(labels[state,a]-labels[state,b]))
        scales[state]=mean(diffs)
    archive=read(OUT/'native_archive.csv');assert len(archive)==4488
    by_group=defaultdict(list);by_case={}
    for r in archive:
        k=key(r);assert k not in by_case;by_case[k]=r
        close(r['actual'],labels[r['state'],r['date']]);assert date.fromisoformat(r['date'])-date.fromisoformat(r['origin'])==timedelta(days=int(r['horizon'])-1)
        close(r['mase_scale'],scales[r['state']])
        by_group[r['configuration'],r['state'],int(r['horizon'])].append(r)
    for values in by_group.values():
        values.sort(key=lambda r:r['date']);assert len(values)==44
        assert [r['date'] for r in values]==[(date(2026,9,15)+timedelta(days=i)).isoformat() for i in range(44)]
    expected_groups={(c,s,h) for c in ['timesfm_history','timesfm_calendar'] for s in ['Delhi','Karnataka','Maharashtra'] for h in range(1,15)}
    expected_groups|={(c,s,h) for c in ['chronos_history','chronos_calendar'] for s in ['Delhi','Karnataka','Maharashtra'] for h in [1,7,14]}
    assert set(by_group)==expected_groups
    memo={}
    def independent_delta(configuration,state,h,origin,arm):
        if arm=='native':return 0.,[],0,0.
        ident=configuration,state,h,origin,arm
        if ident not in memo:
            candidates=[r for r in by_group[configuration,state,h] if r['date']<origin and (arm=='expanding_past' or r['date']<='2026-09-30')]
            assert len(candidates)>=16 and arm in ['frozen_september','expanding_past']
            scores=[max(float(r['q_100'])-float(r['actual']),float(r['actual'])-float(r['q_900'])) for r in candidates]
            n=len(scores);rank=math.ceil((n+1)*.8);assert rank<=n
            raw=sorted(scores)[rank-1];memo[ident]=max(0.,raw),[r['date'] for r in candidates],rank,raw
        return memo[ident]
    logs={(r['configuration'],r['state'],r['origin'],r['date'],r['horizon'],r['arm']):r for r in json.loads((OUT/'calibration_log.json').read_text())}
    rows=read(OUT/'scored_intervals.csv');assert len(rows)==4590
    seen=set();casearms=defaultdict(set);values=defaultdict(lambda:defaultdict(list));ns=[]
    for r in rows:
        k=key(r);arm=r['arm'];assert (k,arm) not in seen;seen.add((k,arm));casearms[k].add(arm)
        original=by_case[k];assert '2026-10-14'<=r['date']<='2026-10-28'
        for field,native in [('prediction','prediction'),('actual','actual'),('mase_scale','mase_scale'),('native_lower','q_100'),('native_median','q_500'),('native_upper','q_900')]:close(r[field],original[native])
        delta,dates,rank,raw=independent_delta(k[0],k[1],k[-1],k[2],arm)
        close(delta,r['expansion_GWh']);assert int(r['calibration_n'])==len(dates) and int(r['calibration_rank'])==rank
        lower=float(original['q_100'])-delta;upper=float(original['q_900'])+delta
        close(lower,r['lower']);close(upper,r['upper']);assert lower<=upper
        if arm!='native':
            log=logs[k+(arm,)];assert log['calibration_dates']==dates and log['n']==len(dates) and log['rank']==rank
            close(log['raw_order_statistic'],raw);close(log['expansion_GWh'],delta);ns.append(len(dates))
            assert max(dates)<r['origin']
            if arm=='frozen_september':assert len(dates)==16 and max(dates)=='2026-09-30'
        y=float(r['actual']);scale=float(r['mase_scale']);median=float(r['native_median'])
        width=upper-lower;iscore=width+10*max(lower-y,0)+10*max(y-upper,0)
        metrics=dict(coverage80=float(lower<=y<=upper),below80=float(y<lower),above80=float(y>upper),width80_GWh=width,
            scaled_width80=width/scale,scaled_interval_score80=iscore/scale,scaled_WIS80_median=(.5*abs(y-median)+.1*iscore)/(1.5*scale))
        for name,x in metrics.items():close(x,r[name]);values[k[0],arm,k[1],k[-1]][name].append(x)
    assert len(casearms)==1530 and all(v=={'native','frozen_september','expanding_past'} for v in casearms.values())
    assert len(logs)==3060
    macro=defaultdict(lambda:defaultdict(list))
    for r in read(OUT/'metrics_state.csv'):
        k=r['configuration'],r['arm'],r['state'],int(r['horizon'])
        for name,v in values[k].items():
            assert len(v)==15;close(mean(v),r[name])
            if name!='width80_GWh':macro[k[0],k[1],k[-1]][name].append(mean(v))
    for r in read(OUT/'metrics_macro.csv'):
        for name,v in macro[r['configuration'],r['arm'],int(r['horizon'])].items():assert len(v)==3;close(mean(v),r[name])
    for r in read(OUT/'contrasts_state.csv'):
        k=r['configuration'],r['arm'],r['state'],int(r['horizon']);baseline=k[0],'native',k[2],k[3]
        for name in ['coverage80','scaled_width80','scaled_interval_score80','scaled_WIS80_median']:close(mean(values[k][name])-mean(values[baseline][name]),r[name+'_change'])
    parent=ROOT/'results/prospective_20261030_v1';original={}
    for name in ['predictions.csv','protocol.json','freeze.json']:
        blob=subprocess.check_output(['git','show','cabd5982e1948652b9841d6c31a2380f6f314198:'+str((parent/name).relative_to(ROOT))],cwd=ROOT)
        assert blob==(parent/name).read_bytes();original[name]=sha(parent/name)
    freeze=json.loads((ANNEX/'freeze.json').read_text());reg=json.loads((ANNEX/'registration.json').read_text());issued=datetime.fromisoformat(freeze['issued_utc'])
    assert issued.tzinfo and datetime.fromisoformat(reg['registered_utc'])<=issued
    assert str(issued.astimezone(ZoneInfo('Asia/Kolkata')).date())==freeze['issued_india_date']
    assert reg['calibration_protocol_sha256']==sha(OUT/'protocol.json')
    assert freeze['predictions_sha256']==sha(ANNEX/'predictions.csv') and freeze['calibration_log_sha256']==sha(ANNEX/'calibration_log.json')
    assert freeze['native_parent_sha256']==original['predictions.csv']
    future=read(ANNEX/'predictions.csv');assert len(future)==252
    future_logs={(r['model'],r['state'],r['horizon'],r['arm']):r for r in json.loads((ANNEX/'calibration_log.json').read_text())};assert len(future_logs)==168
    parents={(r['model'],r['state'],int(r['horizon'])):r for r in read(parent/'predictions.csv') if r['model'] in ['timesfm3_history','timesfm3_calendar']}
    fseen=set();eligible=0
    for r in future:
        ident=r['model'],r['state'],int(r['horizon']);assert ident+(r['arm'],) not in fseen;fseen.add(ident+(r['arm'],))
        old=parents[ident];configuration=r['model'].replace('timesfm3_','timesfm_')
        for field,oldfield in [('prediction','prediction'),('mase_scale','mase_scale'),('native_lower','q01'),('native_median','q05'),('native_upper','q09')]:close(r[field],old[oldfield])
        assert r['origin']==old['origin'] and r['date']==old['date'] and r['parent_issued_utc']==old['issued_utc'] and r['issued_utc']==freeze['issued_utc']
        delta,dates,rank,raw=independent_delta(configuration,r['state'],int(r['horizon']),r['origin'],r['arm'])
        close(float(old['q01'])-delta,r['lower']);close(float(old['q09'])+delta,r['upper'])
        assert int(r['calibration_n'])==len(dates) and int(r['calibration_rank'])==rank
        if dates:assert max(dates)<r['origin'] and len(dates)==(16 if r['arm']=='frozen_september' else 44)
        if dates:
            log=future_logs[ident+(r['arm'],)];assert log['calibration_dates']==dates and log['n']==len(dates) and log['rank']==rank
            close(log['expansion_GWh'],delta);close(log['raw_order_statistic'],raw)
        assert 'actual' not in r
        expected=old['prospective_eligible']=='True' and r['date']>freeze['issued_india_date']
        assert (r['prospective_eligible']=='True')==expected;eligible+=int(expected)
    assert eligible==216 and len(fseen)==252 and not freeze['outcomes_fetched']
    rules=json.loads((ANNEX/'scoring_registration.json').read_text());assert sha(ROOT/'src/score_interval_annex.py')==rules['scoring_source_sha256']
    result=dict(status='pass',scope='Separateinternalstdlibreconstruction;nohumansignoff,exchangeabilityguaranteeorcompletedfuturescore',
        historical_rows=len(rows),common_primary_rows=1620,extended_timesfm_rows=3780,unique_cases_acrossconfigs=len(casearms),
        calibration_log_records=len(logs),calibration_label_count_range=[min(ns),max(ns)],protected_prior_hashes_unchanged=len(protected),
        original_future_blobs_unchanged=original,annex_rows=len(future),annex_eligible_rows=eligible,
        all_native_points_and_medians_unchanged=True,strict_label_date_before_origin=True,all_methods_retained=True,
        annex_prediction_sha256=sha(ANNEX/'predictions.csv'))
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
