"""Finish the recentered matrix after all registered workers and parent audits."""
import json,subprocess,sys,time,traceback
from datetime import datetime,timezone
from calendar_recenter_study import ROOT,OUT,CORRECTION
from festival_feature_design import dump


def main():
    path=OUT/'pipeline_status.json'
    if path.exists():raise FileExistsError('Preserve previous manager')
    status=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_workers_and_parent_audit',completed_steps=[]);dump(path,status)
    reg=json.loads((OUT/'registration.json').read_text());workers=[]
    for group in reg['protocols']:
        p=json.loads((OUT/group/'protocol.json').read_text());workers.extend(OUT/group/m for m in p['models'])
    assert len(workers)==28
    try:
        while True:
            if any((p/'failure.txt').exists() for p in workers):raise RuntimeError('Registered worker failure')
            for p in OUT.glob('*_queue.json'):
                if json.loads(p.read_text())['status']=='failed':raise RuntimeError('Provider queue failed')
            parent=CORRECTION/'pipeline_status.json'
            if parent.exists() and json.loads(parent.read_text())['status']=='failed':raise RuntimeError('Parent correction pipeline failed')
            done=[str(p.relative_to(OUT)) for p in workers if (p/'run.json').exists()];audit=CORRECTION/'analysis/independent_audit.json'
            status.update(completed_workers=done,observed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
            if len(done)==28 and audit.exists() and json.loads(audit.read_text())['status']=='pass':break
            time.sleep(45)
        for cmd in [['src/finalize_calendar_recenter.py','analyze'],['src/audit_calendar_recenter.py'],['src/recenter_contrasts.py','analyze']]:
            status['status']='running_'+cmd[0];dump(path,status)
            with (OUT/(cmd[0].split('/')[-1]+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable,*cmd],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_steps'].append(cmd);dump(path,status)
        status.update(status='completed_analysis_audit_contrasts',completed_utc=datetime.now(timezone.utc).isoformat());dump(path,status)
    except BaseException:
        status.update(status='failed',traceback=traceback.format_exc());dump(path,status);raise


if __name__=='__main__':main()
