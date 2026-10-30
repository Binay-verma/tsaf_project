"""Wait for the completed Chronos lane, issue/audit once before India deadline."""
from datetime import datetime, timezone
import json
import subprocess
import sys
import time
import traceback

from freeze_chronos_competitor import ROOT, OUT, deadline, sha, dump


def main():
    path = OUT/'queue.json'
    if path.exists():
        raise FileExistsError('Preserve previous future queue')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_Chronos_MTA_lane', completed_steps=[])
    dump(path, status)
    parent = ROOT/'results/mta_holiday_v1'
    try:
        while True:
            deadline(datetime.now(timezone.utc))
            queue = parent/'chronos_queue.json'
            if queue.exists():
                state = json.loads(queue.read_text())['status']
                if state == 'failed':
                    raise RuntimeError('Preserve parent MTA provider failure')
                if state == 'completed':
                    break
            status['observed_utc'] = datetime.now(timezone.utc).isoformat()
            dump(path, status)
            time.sleep(45)
        for cohort in ['event_window', 'ordinary']:
            p = parent/cohort/'chronos'
            r = json.loads((p/'run.json').read_text())
            assert r['predictions_sha256'] == sha(p/'predictions.csv')
        for command in [['src/freeze_chronos_competitor.py', 'freeze'], ['src/audit_chronos_competitor.py']]:
            status['status'] = 'running_'+command[0]
            dump(path, status)
            with (OUT/(command[0].split('/')[-1]+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable, *command], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
            status['completed_steps'].append(command)
            dump(path, status)
        status.update(status='frozen_audited_public_push_required_before_eligible_day', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(path, status)
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        dump(path, status)
        raise


if __name__ == '__main__':
    main()
