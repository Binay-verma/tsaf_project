"""Resume after the MTA writer's missing single-scenario metadata field.

No numerical model change: mta_model_engine_v2 differs by one p.get default
for the already fixed seven-day buffer. Recenter recovery, old local models,
frozen future code and all failed attempts remain intact.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from continue_pipeline_recovery_v1 import validate as validate_recenter, sha, dump, execute

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT/'results/calendar_recenter_recovery_v1'
OLD = ROOT/'results/mta_holiday_v1'
MTA = ROOT/'results/mta_holiday_recovery_v1'


def register():
    validate_recenter()
    if MTA.exists():
        raise FileExistsError('Preserve prior MTA recovery')
    failed = OLD/'event_window/chronos'
    assert "KeyError: 'scenario'" in (failed/'failure.txt').read_text()
    assert not (failed/'predictions.csv').exists()
    MTA.mkdir()
    for p in OLD.iterdir():
        if p.is_file() and p.suffix in ['.json', '.csv'] and not ('queue' in p.name or p.name.startswith('pipeline')):
            shutil.copy2(p, MTA/p.name)
    shutil.copytree(OLD/'evidence', MTA/'evidence')
    retained = {}
    for cohort in ['event_window', 'ordinary']:
        target = MTA/cohort
        target.mkdir()
        for name in ['protocol.json', 'primary_cases.csv', 'window_cases.csv']:
            shutil.copy2(OLD/cohort/name, target/name)
        for worker in ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']:
            source = OLD/cohort/worker
            r = json.loads((source/'run.json').read_text())
            assert sha(source/'predictions.csv') == r['predictions_sha256']
            shutil.copytree(source, target/worker)
            retained[cohort+'/'+worker] = dict(rows=r['rows'],
                files={str(p.relative_to(ROOT)): sha(p) for p in source.rglob('*') if p.is_file()})
    assert sum(item['rows'] for item in retained.values()) == 4032
    paths = ['src/continue_pipeline_recovery_v2.py', 'src/continue_pipeline_recovery_v1.py',
             'src/mta_model_engine_v2.py', 'src/mta_model_engine_v1.py',
             'src/test_mta_foundation_schema.py', 'src/mta_holiday_study.py',
             'src/build_integrated_review_v4.py', 'src/audit_integrated_review_v4.py',
             'src/audit_event_support_recovery_v1.py', 'src/event_support_analysis.py',
             'src/finalize_mta_holiday.py', 'src/audit_mta_holiday.py',
             'src/freeze_chronos_competitor.py', 'src/audit_chronos_competitor.py']
    completed = {}
    reg = json.loads((REC/'registration.json').read_text())
    for group in reg['protocols']:
        for model in json.loads((REC/group/'protocol.json').read_text())['models']:
            folder = REC/group/model
            if (folder/'run.json').exists():
                r = json.loads((folder/'run.json').read_text())
                assert sha(folder/'predictions.csv') == r['predictions_sha256']
                completed[str(folder.relative_to(ROOT))] = dict(rows=r['rows'], predictions_sha256=r['predictions_sha256'])
    assert sum(item['rows'] for item in completed.values()) == 870
    dump(MTA/'recovery_registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        reason='CopiedNESOmetadatawriter requiredscenario althoughMTAhasonefixed7daybuffer. Firstbatchforward/solo succeeded but serializationfailedBEFORE completedforecastCSV. Oldfailure/inputs retained; newenginechangesONLYscenario=p.get(scenario,lag7), no numericalinput/model change.',
        retained_local_forecasts=4032, missing_foundation_forecasts=2268, planned_model_forecasts=6300,
        retained_workers=retained, recenter_retained_workers=completed,
        source_hashes={name: sha(ROOT/name) for name in paths},
        old_failure_sha256=sha(failed/'failure.txt'),
        policy='Originalprotocols/cases/source/evidence/selection/scoringregistration copiedbyte-identically. Runonlymissingrec222rows andMTA4foundationworkers; unchangedscorer/auditor redirectOUTtonewMTAroot. Frozenfuturecode/actualissuance/fullIndia-day/publicdeadline/sourcevintage rules unchanged. Oldfailedqueues/statuses remain; newschedulingstate explicit. Papernewv4 preservesallolderdrafts/programs.'))
    print('Registered4032retained/2268missingMTAforecasts; recenter870retained/222missing')


def validate():
    validate_recenter()
    r = json.loads((MTA/'recovery_registration.json').read_text())
    for name, expected in r['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    for item in r['retained_workers'].values():
        for name, expected in item['files'].items():
            assert sha(ROOT/name) == expected, name
    for name, item in r['recenter_retained_workers'].items():
        assert sha(ROOT/name/'predictions.csv') == item['predictions_sha256']


def lane(worker):
    validate()
    path = MTA/(worker+'_continuation_v2.json')
    if path.exists():
        raise FileExistsError('Preserve prior continuation')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_semantics', completed=[])
    dump(path, status)
    try:
        parents = [ROOT/'results/calendar_semantics_v2'/kind/cohort/worker
                   for kind in ['breadth', 'encoding'] for cohort in ['event_window', 'ordinary']]
        while not all((p/'run.json').exists() for p in parents):
            assert not any((p/'failure.txt').exists() for p in parents)
            time.sleep(45)
        for p in parents:
            assert sha(p/'predictions.csv') == json.loads((p/'run.json').read_text())['predictions_sha256']
        reg = json.loads((REC/'registration.json').read_text())
        for group in reg['protocols']:
            folder = REC/group/worker
            if (folder/'run.json').exists():
                status['completed'].append(group+' (retained)')
                dump(path, status)
                continue
            status['status'] = 'running_recenter_'+group
            dump(path, status)
            if group == 'aligned_encoding_added':
                code = f'import sys,json;sys.path.insert(0,"src");from pathlib import Path;import recenter_encoding_engine_v2 as e;e.OUT=Path({str(REC/group)!r});e.ARMS=json.loads((e.OUT/"protocol.json").read_text())["arms"];e.foundation({worker!r})'
            else:
                code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import calendar_recenter_study as m;m.OUT=Path({str(REC)!r});m.run({group!r},{worker!r})'
            execute(['-c', code], REC/group/(worker+'.execution.log'))
            dump(folder/'execution_recovery.json', dict(recovery_registration_sha256=sha(MTA/'recovery_registration.json'),
                completed_utc=datetime.now(timezone.utc).isoformat()))
            status['completed'].append(group)
            dump(path, status)
        for cohort in ['event_window', 'ordinary']:
            status['status'] = 'running_MTA_'+cohort
            dump(path, status)
            folder = MTA/cohort/worker
            assert not (folder/'started.json').exists()
            code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import mta_holiday_study as s;import mta_model_engine_v2 as e;e.OUT=Path({str(MTA/cohort)!r});e.ARMS=s.FOUNDATION_ARMS;e.frames=s.frames;e.foundation({worker!r})'
            execute(['-c', code], MTA/cohort/(worker+'.execution.log'))
            dump(folder/'execution_recovery.json', dict(recovery_registration_sha256=sha(MTA/'recovery_registration.json'),
                engine='src/mta_model_engine_v2.py', numerical_settings_unchanged=True))
            status['completed'].append('MTA/'+cohort)
            dump(path, status)
        if worker == 'chronos':
            future = ROOT/'results/prospective_chronos_20261031_v1'
            dump(future/'execution_recovery_registration_v2.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
                source_registration_sha256=sha(MTA/'recovery_registration.json'),
                policy='Scheduling-onlycontinuation aftertwoancestorintegrationfailures; exactoriginalfuturealgorithm/sourcehashes/completion/India-day/publicdeadline/vintageguardsunchanged. BothrecoveredMTAChronosworkerscomplete; no addedproviderlane.'))
            for command in [['src/freeze_chronos_competitor.py', 'freeze'], ['src/audit_chronos_competitor.py']]:
                status['status'] = 'running_future_'+command[0]
                dump(path, status)
                execute(command, future/(command[0].split('/')[-1]+'.execution.log'))
                status['completed'].append(command)
        status.update(status='completed_provider_continuation_v2', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(path, status)
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        dump(path, status)
        raise


def analysis():
    validate()
    path = MTA/'analysis_continuation_v2.json'
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
            subprocess.run(['libreoffice', '-env:UserInstallation=file:///tmp/tsfm-integrated-v4-lo',
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
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'chronos', 'timesfm', 'analysis'])
    action = parser.parse_args().action
    register() if action == 'register' else analysis() if action == 'analysis' else lane(action)
