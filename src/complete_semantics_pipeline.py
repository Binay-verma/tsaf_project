"""Complete correction analysis only after all workers and parent audits."""
import json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from calendar_semantics_study_v2 import ROOT,OUT,MODELS
from festival_feature_design import dump


def main():
    path=OUT/'pipeline_status.json'
    if path.exists():raise FileExistsError('Preserve prior pipeline')
    status=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_workers_and_parent_audits',completed_steps=[]);dump(path,status)
    try:
        workers=[OUT/k/c/m for k in ['breadth','encoding'] for c in ['event_window','ordinary'] for m in (MODELS if k=='breadth' else ['chronos','timesfm'])]
        parents=[ROOT/'results/feature_breadth_v1/independent_audit.json',ROOT/'results/calendar_encoding_v1/independent_audit.json']
        while True:
            if any((p/'failure.txt').exists() for p in workers):raise RuntimeError('Correction worker failure')
            for p in OUT.glob('*_queue.json'):
                if json.loads(p.read_text())['status']=='failed':raise RuntimeError('Correction queue failure')
            for parent in [ROOT/'results/feature_breadth_v1',ROOT/'results/calendar_encoding_v1']:
                p=parent/'pipeline_status.json'
                if p.exists() and json.loads(p.read_text())['status'] in ['failed','stopped_with_failure']:raise RuntimeError('Parent analysis/audit pipeline failed')
            done=[str(p.relative_to(OUT)) for p in workers if (p/'run.json').exists()]
            status.update(completed_workers=done,observed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
            if len(done)==16 and all(p.exists() and json.loads(p.read_text())['status']=='pass' for p in parents):break
            time.sleep(45)
        for cmd in [['src/finalize_calendar_semantics.py','analyze'],['src/audit_calendar_semantics.py']]:
            status['status']='running_'+cmd[0];dump(path,status)
            with (OUT/(cmd[0].split('/')[-1]+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,*cmd],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_steps'].append(cmd);dump(path,status)
        status.update(status='completed_analysis_audit',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':main()
