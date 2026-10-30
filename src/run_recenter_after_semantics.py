"""Serial provider queue for source-defined window/placebo amendment."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from calendar_recenter_study import ROOT,OUT,CORRECTION
from festival_feature_design import sha,dump


def main(worker):
    path=OUT/(worker+'_queue.json')
    if path.exists():raise FileExistsError('Preserve previous queue')
    status=dict(created_utc=datetime.now(timezone.utc).isoformat(),worker=worker,status='waiting_for_semantics',completed=[]);dump(path,status)
    try:
        parents=[CORRECTION/k/c/worker for k in ['breadth','encoding'] for c in ['event_window','ordinary']]
        while True:
            if any((p/'failure.txt').exists() for p in parents):raise RuntimeError('Prior correction worker failed')
            q=CORRECTION/(worker+'_queue.json')
            if q.exists() and json.loads(q.read_text())['status']=='failed':raise RuntimeError('Prior correction queue failed')
            if all((p/'run.json').exists() for p in parents):break
            time.sleep(45)
        for p in parents:
            run=json.loads((p/'run.json').read_text());assert run['predictions_sha256']==sha(p/'predictions.csv')
        reg=json.loads((OUT/'registration.json').read_text())
        for group in reg['protocols']:
            status['status']='running_'+group;dump(path,status)
            with (OUT/group/(worker+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,'src/calendar_recenter_study.py',worker,'--group',group],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed'].append(group);dump(path,status)
        status.update(status='completed',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worker',choices=['chronos','timesfm']);main(p.parse_args().worker)
