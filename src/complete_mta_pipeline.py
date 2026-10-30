"""Wait for the fixed NYC matrix, then run its registered score and audit once."""
import json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from mta_holiday_study import ROOT,OUT,MODELS
from festival_feature_design import dump


def main():
    path=OUT/'pipeline_status.json'
    if path.exists():raise FileExistsError('Preserve prior MTA manager')
    status=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_workers',completed_steps=[]);dump(path,status)
    try:
        workers=[OUT/c/m for c in ['event_window','ordinary'] for m in MODELS]
        while True:
            if any((p/'failure.txt').exists() for p in workers):raise RuntimeError('Registered MTA worker failed')
            for p in OUT.glob('*_queue.json'):
                if json.loads(p.read_text())['status']=='failed':raise RuntimeError('MTA provider queue failed')
            done=[str(p.relative_to(OUT)) for p in workers if (p/'run.json').exists()];status.update(completed_workers=done,observed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
            if len(done)==12:break
            time.sleep(45)
        for command in [['src/finalize_mta_holiday.py','analyze'],['src/audit_mta_holiday.py']]:
            status['status']='running_'+command[0];dump(path,status)
            with (OUT/(command[0].split('/')[-1]+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,*command],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_steps'].append(command);dump(path,status)
        status.update(status='completed_analysis_audit',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':main()
