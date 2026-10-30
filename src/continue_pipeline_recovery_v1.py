"""Resume missing registered work after the ten-arm dispatch failure.

Old failures, scripts, protocols and closed forecasts remain untouched. New
root carries closed workers byte-for-byte; a one-import engine adapter repairs
only three previously unsupported H-independent arms. No method/parameter,
case, metric, tolerance or future issuance rule is selected on errors.
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

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'results/calendar_recenter_v1'
OUT = ROOT/'results/calendar_recenter_recovery_v1'


def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def register():
    if OUT.exists():
        raise FileExistsError('Preserve previous recovery root')
    failed = OLD/'aligned_encoding_added/chronos'
    assert (failed/'failure.txt').exists() and not (failed/'predictions.csv').exists()
    original = json.loads((OLD/'registration.json').read_text())
    OUT.mkdir()
    for p in OLD.iterdir():
        if p.is_file() and p.suffix in ['.csv', '.json'] and p.name != 'pipeline_status.json' and not p.name.endswith('_queue.json'):
            shutil.copy2(p, OUT/p.name)
    carried = {}
    for group in original['protocols']:
        source = OLD/group
        target = OUT/group
        target.mkdir()
        for name in ['protocol.json', 'primary_cases.csv', 'window_cases.csv']:
            shutil.copy2(source/name, target/name)
        p = json.loads((source/'protocol.json').read_text())
        for worker in p['models']:
            folder = source/worker
            if (folder/'run.json').exists():
                assert not (folder/'failure.txt').exists()
                run = json.loads((folder/'run.json').read_text())
                assert sha(folder/'predictions.csv') == run['predictions_sha256']
                shutil.copytree(folder, target/worker)
                carried[group+'/'+worker] = dict(rows=run['rows'], predictions_sha256=run['predictions_sha256'],
                    source_files={str(f.relative_to(ROOT)): sha(f) for f in folder.rglob('*') if f.is_file()})
    retained = sum(item['rows'] for item in carried.values())
    assert retained == 840, retained
    names = ['src/continue_pipeline_recovery_v1.py', 'src/recenter_encoding_adapter_v1.py',
             'src/recenter_encoding_engine_v2.py', 'src/test_recenter_encoding_adapter.py',
             'src/audit_event_support_recovery_v1.py', 'src/calendar_recenter_study.py',
             'src/semantics_encoding_engine_v2.py', 'src/calendar_semantics_study_v2.py',
             'src/calendar_encoding_study.py', 'src/finalize_calendar_recenter.py',
             'src/audit_calendar_recenter.py', 'src/recenter_contrasts.py',
             'src/finalize_mta_holiday.py', 'src/audit_mta_holiday.py',
             'src/event_support_analysis.py', 'src/audit_event_support.py',
             'src/freeze_chronos_competitor.py', 'src/audit_chronos_competitor.py']
    names += ['src/build_integrated_review.py', 'src/audit_integrated_review.py']
    dump(OUT/'recovery_registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        reason='Finalalignedencoding group dispatched all10arms to7Hdependent-onlyencoder; history failedBEFORE anyforecast. Originalfailure/propagatedqueuestops retained. Originalprogrambytes/protocols unchanged; one-import versionedengine delegates3H-independentarms unchangedoriginal,7H-dependentarms unchangedaligned. No new method/settings/cases/scoring/tolerance.',
        retained_closed_forecasts=840, missing_forecasts=252, full_registered_forecasts=1092,
        carried_workers=carried, source_hashes={name: sha(ROOT/name) for name in names},
        derived_root='Allparentprotocols/registration/scoring/contrast/cases/ledgers copiedbyte-identically. Originalfrozenfinalizer/auditor redirectOUT only. Newsource/provenance sidecar validated beforemissinginference. Neverreplacefailedoriginalworker.',
        downstream='Newqueues resume MTAunchanged methods after eachrecoveredproviderlane, thenunchangedfutureChronosfreeze/inputaudit afteritsMTA lane. Keepoldfailedstatuses; recordnewrecoveryexecution. Sourceprotocols/stalecontext/actualIndia-day/publicdeadline guards remain binding. Event-support pointsource redirectonly, moderatorsunchanged.'))
    print('Registered840retained/252missing forecasts; no old failure/source overwritten')


def validate():
    r = json.loads((OUT/'recovery_registration.json').read_text())
    for name, expected in r['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    for item in r['carried_workers'].values():
        for name, expected in item['source_files'].items():
            assert sha(ROOT/name) == expected, name
    return r


def execute(command, log):
    with Path(log).open('w') as stream:
        subprocess.run([sys.executable, *command], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)


def lane(worker):
    validate()
    status_path = OUT/(worker+'_queue_recovery_v1.json')
    if status_path.exists():
        raise FileExistsError('Preserve previous recovery queue')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_semantics_workers', worker=worker, completed=[])
    dump(status_path, status)
    try:
        semantic = ROOT/'results/calendar_semantics_v2'
        paths = [semantic/kind/cohort/worker for kind in ['breadth', 'encoding'] for cohort in ['event_window', 'ordinary']]
        while not all((p/'run.json').exists() for p in paths):
            assert not any((p/'failure.txt').exists() for p in paths)
            time.sleep(45)
        for p in paths:
            assert sha(p/'predictions.csv') == json.loads((p/'run.json').read_text())['predictions_sha256']
        reg = json.loads((OUT/'registration.json').read_text())
        for group in reg['protocols']:
            folder = OUT/group/worker
            if (folder/'run.json').exists():
                status['completed'].append(group+' (byte-identical retained)')
                dump(status_path, status)
                continue
            status['status'] = 'running_recenter_'+group
            dump(status_path, status)
            if group == 'aligned_encoding_added':
                code = f'import sys,json;sys.path.insert(0,"src");from pathlib import Path;import recenter_encoding_engine_v2 as e;e.OUT=Path({str(OUT/group)!r});e.ARMS=json.loads((e.OUT/"protocol.json").read_text())["arms"];e.foundation({worker!r})'
            else:
                code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import calendar_recenter_study as m;m.OUT=Path({str(OUT)!r});m.run({group!r},{worker!r})'
            execute(['-c', code], OUT/group/(worker+'.execution.log'))
            dump(folder/'execution_recovery.json', dict(recovery_registration_sha256=sha(OUT/'recovery_registration.json'),
                actual_adapter='src/recenter_encoding_adapter_v1.py' if group == 'aligned_encoding_added' else None,
                completed_utc=datetime.now(timezone.utc).isoformat()))
            status['completed'].append(group)
            dump(status_path, status)
        mta = ROOT/'results/mta_holiday_v1'
        for cohort in ['event_window', 'ordinary']:
            status['status'] = 'running_MTA_'+cohort
            dump(status_path, status)
            assert not (mta/cohort/worker/'started.json').exists(), 'Preserve unexpected partial MTA worker'
            execute(['src/mta_holiday_study.py', worker, '--cohort', cohort], mta/cohort/(worker+'.execution.log'))
            status['completed'].append('MTA/'+cohort)
            dump(status_path, status)
        if worker == 'chronos':
            future = ROOT/'results/prospective_chronos_20261031_v1'
            dump(future/'execution_recovery_registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
                recovery_registration_sha256=sha(OUT/'recovery_registration.json'),
                policy='Scheduling-only recovery afterancestorqueuefailure; exactoriginalfuturefreeze/audit/sourcehashes/actualIndia-timeeligibility/publicdeadline unchanged. MTAChronoscompletedfirst, no extraproviderlane. Oldqueuefailure retained.'))
            for command in [['src/freeze_chronos_competitor.py', 'freeze'], ['src/audit_chronos_competitor.py']]:
                status['status'] = 'running_future_'+command[0]
                dump(status_path, status)
                execute(command, future/(command[0].split('/')[-1]+'.execution.log'))
                status['completed'].append(command)
        status.update(status='completed_recovered_lane', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(status_path, status)
    except BaseException:
        status.update(status='failed', traceback=traceback.format_exc())
        dump(status_path, status)
        raise


def analysis():
    validate()
    path = OUT/'analysis_recovery_status.json'
    if path.exists():
        raise FileExistsError('Preserve previous recovery analysis')
    status = dict(started_utc=datetime.now(timezone.utc).isoformat(), status='waiting_for_recenter_workers_and_semantic_audit', completed=[])
    dump(path, status)
    try:
        reg = json.loads((OUT/'registration.json').read_text())
        workers = [OUT/group/model for group in reg['protocols']
                   for model in json.loads((OUT/group/'protocol.json').read_text())['models']]
        assert len(workers) == 28
        while True:
            assert not any((p/'failure.txt').exists() for p in workers)
            for p in OUT.glob('*_queue_recovery_v1.json'):
                assert json.loads(p.read_text())['status'] != 'failed', p
            audit = ROOT/'results/calendar_semantics_v2/analysis/independent_audit.json'
            if all((p/'run.json').exists() for p in workers) and audit.exists() and json.loads(audit.read_text())['status'] == 'pass':
                break
            time.sleep(45)
        for module in ['finalize_calendar_recenter', 'audit_calendar_recenter', 'recenter_contrasts']:
            status['status'] = 'running_'+module
            dump(path, status)
            code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import {module} as m;m.OUT=Path({str(OUT)!r});m.main("all")'
            execute(['-c', code], OUT/(module+'.execution.log'))
            status['completed'].append(module)
            dump(path, status)
        support = ROOT/'results/event_support_v1'
        code = f'import sys;sys.path.insert(0,"src");from pathlib import Path;import event_support_analysis as m;m.RECENTER=Path({str(OUT)!r});m.analyze()'
        execute(['-c', code], support/'analysis_recovery.execution.log')
        execute(['src/audit_event_support_recovery_v1.py'], support/'audit_recovery.execution.log')
        status['completed'].append('event_support_analysis_and_separate_audit')
        status['status'] = 'waiting_for_all_MTA_workers'
        dump(path, status)
        mta = ROOT/'results/mta_holiday_v1'
        workers = [mta/cohort/model for cohort in ['event_window', 'ordinary']
                   for model in ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm']]
        while not all((p/'run.json').exists() for p in workers):
            assert not any((p/'failure.txt').exists() for p in workers)
            for p in OUT.glob('*_queue_recovery_v1.json'):
                assert json.loads(p.read_text())['status'] != 'failed', p
            time.sleep(45)
        for command in [['src/finalize_mta_holiday.py', 'analyze'], ['src/audit_mta_holiday.py']]:
            status['status'] = 'running_'+command[0]
            dump(path, status)
            execute(command, mta/(command[0].split('/')[-1]+'.execution.log'))
            status['completed'].append(command)
            dump(path, status)
        from build_integrated_review import GATES, OUT as PAPER
        while not all((ROOT/name).exists() and json.loads((ROOT/name).read_text())['status'] == 'pass' for name in GATES):
            time.sleep(45)
        for command in [['src/build_integrated_review.py'], ['src/audit_integrated_review.py']]:
            status['status'] = 'running_'+command[0]
            dump(path, status)
            execute(command, OUT/(command[0].split('/')[-1]+'.execution.log'))
            status['completed'].append(command)
            dump(path, status)
        status['status'] = 'rendering_integrated_PDF'
        dump(path, status)
        with (OUT/'libreoffice.execution.log').open('w') as stream:
            subprocess.run(['libreoffice', '-env:UserInstallation=file:///tmp/tsfm-integrated-recovery-lo',
                '--headless', '--convert-to', 'pdf', '--outdir', str(PAPER),
                str(PAPER/'Integrated_Review_Binay_Verma.docx')], cwd=ROOT,
                stdout=stream, stderr=subprocess.STDOUT, check=True)
        assert (PAPER/'Integrated_Review_Binay_Verma.pdf').is_file()
        status.update(status='completed_full_scientific_and_reporting_audits_PDF_visual_review_pending', completed_utc=datetime.now(timezone.utc).isoformat())
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
