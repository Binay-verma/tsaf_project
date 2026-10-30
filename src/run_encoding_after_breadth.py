"""Queue a provider after its registered breadth lane, without overlapping its CPU budget."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from calendar_encoding_study import ROOT,OUT
from festival_feature_design import sha,dump


def main(worker):
    path=OUT/(worker+'_queue.json')
    if path.exists():raise FileExistsError('Preserve prior queue; inspect logs before any new version')
    status=dict(created_utc=datetime.now(timezone.utc).isoformat(),worker=worker,status='waiting_for_breadth',completed_cohorts=[])
    dump(path,status)
    try:
        while True:
            failures=[ROOT/f'results/feature_breadth_v1/{c}/{worker}/failure.txt' for c in ['event_window','ordinary']]
            if any(p.exists() for p in failures):raise RuntimeError('Parent worker failed; do not silently rerun')
            done=all((ROOT/f'results/feature_breadth_v1/{c}/{worker}/run.json').exists() for c in ['event_window','ordinary'])
            if done:break
            time.sleep(45)
        for cohort in ['event_window','ordinary']:
            parent=ROOT/f'results/feature_breadth_v1/{cohort}/{worker}'
            run=json.loads((parent/'run.json').read_text());assert sha(parent/'predictions.csv')==run['predictions_sha256']
            status['status']='running_'+cohort;status['started_utc']=datetime.now(timezone.utc).isoformat();dump(path,status)
            with (OUT/cohort/(worker+'.execution.log')).open('w') as log:
                subprocess.run([sys.executable,str(ROOT/'src/calendar_encoding_study.py'),worker,'--cohort',cohort],
                    cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            status['completed_cohorts'].append(cohort);dump(path,status)
        status['status']='completed';status['completed_utc']=datetime.now(timezone.utc).isoformat();dump(path,status)
    except BaseException:
        status['status']='failed';status['traceback']=traceback.format_exc();dump(path,status);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worker',choices=['chronos','timesfm']);main(p.parse_args().worker)
