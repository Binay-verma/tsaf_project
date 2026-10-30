"""Same frozen scientific analysis; use this environment's soffice entry point.
Only progress filename and renderer command differ from continuation_v2.
"""
from datetime import datetime, timezone
import hashlib,json,shutil,subprocess,time,traceback
from pathlib import Path
from continue_pipeline_recovery_v2 import ROOT,REC,MTA,validate,execute,dump

def main():
    validate()
    path = MTA/'analysis_continuation_v3.json'
    if path.exists():
        raise FileExistsError('Preserve prior analysis continuation')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_complete_recenter', completed=[])
    dump(path, status)
    try:
        reg = json.loads((REC/'registration.json').read_text())
        workers = [REC/group/model for group in reg['protocols']
                   for model in json.loads((REC/group/'protocol.json').read_text())['models']]
        while True:
            for p in MTA.glob('*_continuation_v2.json'):
                if p != path:
                    assert json.loads(p.read_text())['status'] != 'failed', p
            assert not any((p/'failure.txt').exists() for p in workers)
            parent = ROOT/'results/calendar_semantics_v2/analysis/independent_audit.json'
            if all((p/'run.json').exists() for p in workers) and parent.exists() and json.loads(parent.read_text())['status'] == 'pass':
                break
            time.sleep(45)
        for module in ['finalize_calendar_recenter', 'audit_calendar_recenter', 'recenter_contrasts']:
            status['status'] = 'running_'+module
            dump(path, status)
            code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import {module} as m;m.OUT=Path({str(REC)!r});m.main("all")'
            execute(['-c', code], REC/(module+'.execution.log'))
            status['completed'].append(module)
            dump(path, status)
        support = ROOT/'results/event_support_v1'
        code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import event_support_analysis as m;m.RECENTER=Path({str(REC)!r});m.analyze()'
        execute(['-c', code], support/'analysis_recovery.execution.log')
        execute(['src/audit_event_support_recovery_v1.py'], support/'audit_recovery.execution.log')
        status['completed'].append('event_support_scalar_audit')
        status['status'] = 'waiting_for_all_MTA_workers'
        dump(path, status)
        workers = [MTA/cohort/model for cohort in ['event_window', 'ordinary']
                   for model in ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm']]
        while not all((p/'run.json').exists() for p in workers):
            assert not any((p/'failure.txt').exists() for p in workers)
            for p in MTA.glob('*_continuation_v2.json'):
                if p != path:
                    assert json.loads(p.read_text())['status'] != 'failed', p
            time.sleep(45)
        for module in ['finalize_mta_holiday', 'audit_mta_holiday']:
            status['status'] = 'running_'+module
            dump(path, status)
            code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import {module} as m;m.OUT=Path({str(MTA)!r});m.main("all")'
            execute(['-c', code], MTA/(module+'.execution.log'))
            status['completed'].append(module)
            dump(path, status)
        from build_integrated_review_v4 import GATES, OUT as PAPER
        while not all((ROOT/name).exists() and json.loads((ROOT/name).read_text())['status'] == 'pass' for name in GATES):
            time.sleep(45)
        for command in [['src/build_integrated_review_v4.py'], ['src/audit_integrated_review_v4.py']]:
            status['status'] = 'running_'+command[0]
            dump(path, status)
            execute(command, MTA/(command[0].split('/')[-1]+'.execution.log'))
            status['completed'].append(command)
            dump(path, status)
        with (MTA/'libreoffice.execution.log').open('w') as stream:
            subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-integrated-v4-lo',
                '--headless', '--convert-to', 'pdf', '--outdir', str(PAPER), str(PAPER/'Integrated_Review_Binay_Verma.docx')],
                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        assert (PAPER/'Integrated_Review_Binay_Verma.pdf').is_file()
        status.update(status='completed_full_science_reporting_PDF_visual_review_pending', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(path, status)
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        dump(path, status)
        raise

if __name__ == '__main__':
    reg=json.loads((MTA/'analysis_renderer_registration_v3.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==reg['source_sha256']
    assert shutil.which('soffice')==reg['renderer']
    main()
