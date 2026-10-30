"""Wait for the existing registered studies, then build/audit a new paper once.

No model selection, future-outcome retrieval, outreach, Git push, environment
publication or workflow activation. An interrupted attempt is preserved.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from build_integrated_review import ROOT, OUT, GATES

STATE = ROOT/'review/integrated_review_v3_pipeline'
STUDIES = ['feature_breadth_v1', 'calendar_encoding_v1', 'neso_replication_v1',
           'calendar_semantics_v2', 'calendar_recenter_v1', 'mta_holiday_v1']


def main():
    if STATE.exists():
        raise FileExistsError('Preserve prior integrated manager; inspect before versioned recovery')
    STATE.mkdir(parents=True)
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  status='waiting_for_complete_audits', completed_steps=[])

    def save():
        (STATE/'status.json').write_text(json.dumps(status, indent=2)+'\n')

    save()
    try:
        while True:
            ready = []
            for name in GATES:
                path = ROOT/name
                if path.exists():
                    assert json.loads(path.read_text())['status'] == 'pass', name
                    ready.append(name)
            for study in STUDIES:
                folder = ROOT/'results'/study
                for name in ['pipeline_status.json', 'chronos_queue.json', 'timesfm_queue.json']:
                    path = folder/name
                    if path.exists() and json.loads(path.read_text())['status'] == 'failed':
                        raise RuntimeError('Inspect retained study failure: '+str(path))
            status.update(observed_utc=datetime.now(timezone.utc).isoformat(), completed_gates=ready)
            save()
            if len(ready) == len(GATES):
                break
            time.sleep(45)
        commands = [
            [sys.executable, 'src/build_integrated_review.py'],
            [sys.executable, 'src/audit_integrated_review.py'],
            ['libreoffice', '-env:UserInstallation=file:///tmp/tsfm-integrated-review-lo',
             '--headless', '--convert-to', 'pdf', '--outdir', str(OUT),
             str(OUT/'Integrated_Review_Binay_Verma.docx')],
        ]
        for index, command in enumerate(commands):
            status['status'] = 'running_step_'+str(index)
            save()
            with (STATE/f'step_{index}.log').open('w') as stream:
                subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
            status['completed_steps'].append(command)
            save()
        pdf = OUT/'Integrated_Review_Binay_Verma.pdf'
        assert pdf.is_file() and pdf.stat().st_size > 10_000
        status.update(status='numeric_audit_and_PDF_complete_visual_review_pending',
                      completed_utc=datetime.now(timezone.utc).isoformat())
        save()
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
