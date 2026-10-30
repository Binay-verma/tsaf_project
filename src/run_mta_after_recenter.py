"""Retain one two-thread lane per provider; MTA follows completed recentering."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from mta_holiday_study import ROOT,OUT
from festival_feature_design import sha,dump


def main(worker):
    path=OUT/(worker+'_queue.json')
    if path.exists():raise FileExistsError('Preserve previous MTA queue')
    status=dict(created_utc=datetime.now(timezone.utc).isoformat(),worker=worker,status='waiting_for_recenter',completed=[]);dump(path,status)
    parent=ROOT/'results/calendar_recenter_v1'
    try:
        reg=json.loads((parent/'registration.json').read_text());parents=[parent/g/worker for g in reg['protocols']]
        while True:
            if any((p/'failure.txt').exists() for p in parents):raise RuntimeError('Parent recenter worker failed')
            q=parent/(worker+'_queue.json')
            if q.exists() and json.loads(q.read_text())['status']=='failed':raise RuntimeError('Parent provider queue failed')
            if all((p/'run.json').exists() for p in parents):break
            time.sleep(45)
        for p in parents:
            r=json.loads((p/'run.json').read_text());assert r['predictions_sha256']==sha(p/'predictions.csv')
        assert (OUT/'selection.json').exists() and (OUT/'snapshot.json').exists()
        for cohort in ['event_window','ordinary']:
            status['status']='running_'+cohort;dump(path,status)
            with (OUT/cohort/(worker+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,'src/mta_holiday_study.py',worker,'--cohort',cohort],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed'].append(cohort);dump(path,status)
        status.update(status='completed',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worker',choices=['chronos','timesfm']);main(p.parse_args().worker)
