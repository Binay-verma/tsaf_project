"""Manual, date-gated scoring using the original episode's SAME actual vintage."""
import argparse
from datetime import datetime,timezone,date
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from forecasting import ROOT
from collect_prospective_actuals import complete_result

ANNEX=ROOT/'results/prospective_interval_20261030_v1'
LAST=date(2026,11,11)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics_frame(predictions,actuals,now):
    if now.astimezone(timezone.utc).date()<=LAST:raise ValueError('Completefutureperiodhasnotended')
    if actuals.index.has_duplicates:raise ValueError('Duplicateactualdates')
    d=predictions[predictions.prospective_eligible.eq(True)].copy()
    d['actual']=[actuals.at[pd.Timestamp(r.date),r.state] if pd.Timestamp(r.date) in actuals.index else np.nan for r in d.itertuples(index=False)]
    if not np.isfinite(d.actual).all() or not d.actual.gt(0).all():raise ValueError('Missing/nonpositivelabels;neverimpute/drop')
    if not np.isfinite(d[['lower','upper','native_median','mase_scale']]).all().all() or not d.lower.le(d.upper).all():raise ValueError('Invalidintervals')
    if not d.mase_scale.gt(0).all():raise ValueError('Invalidscales')
    d['coverage80']=((d.lower<=d.actual)&(d.actual<=d.upper)).astype(float)
    d['width80_GWh']=d.upper-d.lower;d['scaled_width80']=d.width80_GWh/d.mase_scale
    score=d.width80_GWh+10*np.maximum(d.lower-d.actual,0)+10*np.maximum(d.actual-d.upper,0)
    d['scaled_interval_score80']=score/d.mase_scale
    d['scaled_WIS80_median']=(.5*abs(d.actual-d.native_median)+.1*score)/(1.5*d.mase_scale)
    return d


def original_annex_commit():
    path=str((ANNEX/'predictions.csv').relative_to(ROOT))
    commits=subprocess.check_output(['git','rev-list','--reverse','HEAD','--',path],cwd=ROOT,text=True).splitlines()
    if not commits:raise ValueError('Annexmustfirstbecommittedbeforeoutcomes')
    commit=commits[0]
    for name in ['registration.json','predictions.csv','freeze.json','calibration_log.json','scoring_registration.json']:
        relative=str((ANNEX/name).relative_to(ROOT))
        original=subprocess.check_output(['git','show',commit+':'+relative],cwd=ROOT)
        if (ANNEX/name).read_bytes()!=original:raise ValueError('AnnexchangedfromfirstGitcommit:'+name)
    return commit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--actuals-dir',type=Path,default=ROOT/'results/prospective_20261030_scoring_v1')
    parser.add_argument('--out',type=Path,default=ROOT/'results/prospective_interval_20261030_scoring_v1')
    args=parser.parse_args();now=datetime.now(timezone.utc)
    if now.date()<=LAST:
        print('PENDING: no future labels opened, no network request and no score before12November2026UTC.');return
    if args.out.exists():raise FileExistsError('Preservefirstscore;do notoverwrite')
    rules=json.loads((ANNEX/'scoring_registration.json').read_text())
    assert sha(__file__)==rules['scoring_source_sha256']
    freeze=json.loads((ANNEX/'freeze.json').read_text());assert sha(ANNEX/'predictions.csv')==freeze['predictions_sha256']
    commit=original_annex_commit()
    if not complete_result(args.actuals_dir):raise ValueError('Requirecompletedoriginalepisodereceipt/snapshot;noalternativevintage')
    collection=json.loads((args.actuals_dir/'collection.json').read_text())
    retrieved=datetime.fromisoformat(collection['retrieved_utc'].replace('Z','+00:00'))
    if retrieved.tzinfo is None or retrieved>now or retrieved.astimezone(timezone.utc).date()<=LAST:raise ValueError('Invalidactualretrievaltime')
    metadata=json.loads((args.actuals_dir/'source_metadata_snapshot.json').read_text());fields={r['name']:r for r in metadata['fields']}
    for state in ['Delhi','Karnataka','Maharashtra']:assert fields[state+': EnergyMet']['units']=='GWh'
    actuals=pd.read_csv(args.actuals_dir/'actuals_snapshot.csv',index_col=0,parse_dates=True)
    assert sha(args.actuals_dir/'actuals_snapshot.csv')==collection['eligible_labels_sha256']
    predictions=pd.read_csv(ANNEX/'predictions.csv');assert len(predictions)==252 and predictions.prospective_eligible.sum()==216
    d=metrics_frame(predictions,actuals,now);assert len(d)==216
    metrics=['coverage80','scaled_width80','scaled_interval_score80','scaled_WIS80_median']
    state=d.groupby(['model','arm','state','horizon'])[metrics].mean().reset_index()
    leads=state.groupby(['model','arm','horizon'])[metrics].mean().reset_index()
    overall=leads.groupby(['model','arm'])[metrics].mean().reset_index()
    args.out.mkdir(parents=True);d.to_csv(args.out/'scored_intervals.csv',index=False);state.to_csv(args.out/'metrics_state_lead.csv',index=False)
    leads.to_csv(args.out/'metrics_lead.csv',index=False);overall.to_csv(args.out/'metrics_macro.csv',index=False)
    audit=dict(scored_utc=now.isoformat(),annex_first_git_commit=commit,frozen_annex_sha256=freeze['predictions_sha256'],
        scored_rows=len(d),actuals_retrieved_utc=retrieved.isoformat(),actuals_sha256=collection['eligible_labels_sha256'],
        collection_receipt_sha256=sha(args.actuals_dir/'collection.json'),same_vintage_as_original_episode=True,
        warning='72originalTimesFMeligiblecases x3intervalarms, sameoneepisode/source;noindependence,guaranteedcoverage,retuningorsubmissionapproval')
    (args.out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(overall.to_string(index=False))


if __name__=='__main__':main()
