"""Serial provider queue: preserve the two-thread lane and every failure."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from neso_replication import ROOT,OUT
from festival_feature_design import sha,dump


def main(worker):
    path=OUT/(worker+'_queue.json')
    if path.exists():raise FileExistsError('Preserve previous queue')
    status=dict(created_utc=datetime.now(timezone.utc).isoformat(),worker=worker,status='waiting_for_encoding',completed_scenarios=[])
    dump(path,status)
    try:
        while True:
            parent=ROOT/'results/calendar_encoding_v1'
            q=parent/(worker+'_queue.json')
            if q.exists() and json.loads(q.read_text())['status']=='failed':raise RuntimeError('Encoding provider queue failed')
            if any((parent/c/worker/'failure.txt').exists() for c in ['event_window','ordinary']):raise RuntimeError('Encoding worker failed')
            if all((parent/c/worker/'run.json').exists() for c in ['event_window','ordinary']):break
            time.sleep(45)
        for cohort in ['event_window','ordinary']:
            p=parent/cohort/worker;run=json.loads((p/'run.json').read_text())
            assert sha(p/'predictions.csv')==run['predictions_sha256']
        assert (OUT/'selection.json').exists() and (OUT/'snapshot.json').exists()
        for scenario in ['ideal','lag21']:
            status['status']='running_'+scenario;dump(path,status)
            with (OUT/scenario/(worker+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,str(ROOT/'src/neso_replication.py'),worker,'--scenario',scenario],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_scenarios'].append(scenario);dump(path,status)
        status.update(status='completed',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worker',choices=['chronos','timesfm']);main(p.parse_args().worker)
