"""Queue document-aligned sensitivity after the existing provider lane."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from calendar_semantics_study_v2 import ROOT,OUT
from festival_feature_design import sha,dump


def main(worker):
    path=OUT/(worker+'_queue.json')
    if path.exists():raise FileExistsError('Preserve previous queue')
    status=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_neso',worker=worker,completed=[]);dump(path,status)
    try:
        parent=ROOT/'results/neso_replication_v1'
        while True:
            q=parent/(worker+'_queue.json')
            if q.exists() and json.loads(q.read_text())['status']=='failed':raise RuntimeError('NESO queue failed')
            if any((parent/c/worker/'failure.txt').exists() for c in ['ideal','lag21']):raise RuntimeError('NESO worker failed')
            if all((parent/c/worker/'run.json').exists() for c in ['ideal','lag21']):break
            time.sleep(45)
        for c in ['ideal','lag21']:
            run=json.loads((parent/c/worker/'run.json').read_text());assert run['predictions_sha256']==sha(parent/c/worker/'predictions.csv')
        for kind in ['breadth','encoding']:
            for cohort in ['event_window','ordinary']:
                status['status']='running_'+kind+'_'+cohort;dump(path,status)
                with (OUT/kind/cohort/(worker+'.execution.log')).open('w') as stream:
                    subprocess.run([sys.executable,'src/calendar_semantics_study_v2.py',worker,'--kind',kind,'--cohort',cohort],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
                status['completed'].append(kind+'/'+cohort);dump(path,status)
        status.update(status='completed',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worker',choices=['chronos','timesfm']);main(p.parse_args().worker)
