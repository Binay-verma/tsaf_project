"""Analyze only after the full recentered point/source audit passes."""
from datetime import datetime, timezone
import json
import subprocess
import sys
import time
import traceback

from event_support_analysis import ROOT, OUT, RECENTER
from festival_feature_design import dump


def main():
    status_path = OUT/'pipeline_status.json'
    if status_path.exists():
        raise FileExistsError('Preserve prior moderator pipeline')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_complete_recenter_audit')
    dump(status_path, status)
    try:
        while True:
            p = RECENTER/'analysis/independent_audit.json'
            if p.exists() and json.loads(p.read_text())['status'] == 'pass':
                break
            parent = RECENTER/'pipeline_status.json'
            if parent.exists() and json.loads(parent.read_text())['status'] == 'failed':
                raise RuntimeError('Preserve parent recenter failure')
            time.sleep(45)
        for command in [['src/event_support_analysis.py', 'analyze'], ['src/audit_event_support.py']]:
            status['status'] = 'running_'+command[0]
            dump(status_path, status)
            with (OUT/(command[0].split('/')[-1]+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable, *command], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        status.update(status='completed_analysis_and_separate_audit', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(status_path, status)
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        dump(status_path, status)
        raise


if __name__ == '__main__':
    main()
