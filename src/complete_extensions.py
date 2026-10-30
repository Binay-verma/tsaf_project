"""Wait for registered extension workers, then score and audit once."""
import argparse,json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main(study):
    out=ROOT/'results'/('calendar_encoding_v1' if study=='encoding' else 'neso_replication_v1')
    cohorts=['event_window','ordinary'] if study=='encoding' else ['ideal','lag21']
    models=['chronos','timesfm'] if study=='encoding' else ['ridge','lightgbm','lightgbm_capacity2','sarimax','chronos','timesfm']
    path=out/'pipeline_status.json'
    if path.exists():raise FileExistsError('Preserve prior manager status')
    status=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_workers',completed_steps=[])
    def save():path.write_text(json.dumps(status,indent=2)+'\n')
    save()
    try:
        while True:
            if list(out.glob('*/*/failure.txt')) or any(json.loads(p.read_text())['status']=='failed' for p in out.glob('*_queue.json')):raise RuntimeError('Worker/queue failure: inspect saved evidence')
            done=[f'{c}/{m}' for c in cohorts for m in models if (out/c/m/'run.json').exists()]
            status.update(completed_workers=done,observed_utc=datetime.now(timezone.utc).isoformat());save()
            parent=ROOT/'results/feature_breadth_v1/independent_audit.json'
            ready=study!='encoding' or parent.exists() and json.loads(parent.read_text())['status']=='pass'
            if len(done)==len(cohorts)*len(models) and ready:break
            time.sleep(45)
        commands=([['src/finalize_calendar_encoding.py','analyze'],['src/audit_calendar_encoding.py']] if study=='encoding' else
                  [['src/finalize_neso_replication.py','analyze'],['src/audit_neso_replication.py']])
        for command in commands:
            status['status']='running_'+command[0];save()
            with (out/(Path(command[0]).name+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,*command],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_steps'].append(command);save()
        status.update(status='completed_analysis_audit',completed_utc=datetime.now(timezone.utc).isoformat());save()
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());save();raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('study',choices=['encoding','neso']);main(p.parse_args().study)
