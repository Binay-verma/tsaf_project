"""Wait for every registered worker, then run fixed analysis/audit/draft in order."""
from datetime import datetime,timezone
import json,subprocess,sys,time
from breadth_study import ROOT,OUT,MODELS
from festival_feature_design import dump


def main():
    path=OUT/'pipeline_status.json'
    if path.exists():raise FileExistsError('Preserve prior manager; inspect completion/failure before restart')
    status=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='waiting_for_workers',completed_steps=[])
    dump(path,status)
    try:
        while True:
            failures=[str(p.relative_to(ROOT)) for p in OUT.glob('*/*/failure.txt')]
            if failures:raise RuntimeError('Registered worker failure; preserve outputs: '+str(failures))
            done=[f'{c}/{m}' for c in ['event_window','ordinary'] for m in MODELS if (OUT/c/m/'run.json').exists()]
            status['completed_workers']=done;status['observed_utc']=datetime.now(timezone.utc).isoformat();dump(path,status)
            print(len(done),'/12workers complete',status['observed_utc'],flush=True)
            if len(done)==12:break
            time.sleep(45)
        for source in ['src/finalize_breadth_study.py','src/audit_breadth_study.py','src/build_ijf_focus.py']:
            status['status']='running_'+source;dump(path,status)
            log=OUT/(source.split('/')[-1]+'.execution.log')
            with log.open('w') as stream:
                subprocess.run([sys.executable,str(ROOT/source)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
            status['completed_steps'].append(source);dump(path,status)
            print('COMPLETE',source,flush=True)
        status['status']='completed_analysis_audit_DOCX';status['completed_utc']=datetime.now(timezone.utc).isoformat();dump(path,status)
        print('Completed analysis/audit/MD-DOCX; PDF render/visual QA and GitHub push still require final checks',flush=True)
    except BaseException as exc:
        status['status']='stopped_with_failure';status['error']=repr(exc);status['failure_utc']=datetime.now(timezone.utc).isoformat();dump(path,status)
        raise


if __name__=='__main__':main()
