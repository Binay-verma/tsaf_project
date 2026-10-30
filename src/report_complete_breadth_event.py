"""Report the COMPLETE event cohort while ordinary inference continues.

Calls the unchanged registered finalizer and separate auditor with only their
output root redirected. The explicitly derived registration retains every
event case/model/arm/contrast. Original study artifacts are never written.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'results/feature_breadth_v1'
OUT = ROOT/'results/feature_breadth_event_checkpoint_v1'
REG = ROOT/'review/breadth_event_reporting_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def register():
    if REG.exists() or OUT.exists():
        raise FileExistsError('Preserve existing event-report checkpoint')
    parent = json.loads((PARENT/'registration.json').read_text())
    paths = [PARENT/'registration.json', PARENT/'scoring_registration.json',
             PARENT/'protected_prior_files.json', ROOT/'src/finalize_breadth_study.py',
             ROOT/'src/audit_breadth_study.py', Path(__file__)]
    paths += [p for p in (PARENT/'event_window').rglob('*') if p.is_file()]
    for model in parent['models']:
        worker = PARENT/'event_window'/model
        assert not (worker/'failure.txt').exists()
        run = json.loads((worker/'run.json').read_text())
        assert run['predictions_sha256'] == sha(worker/'predictions.csv')
        assert run['rows'] == 528*8
        assert run['protocol_sha256'] == parent['cohorts']['event_window']
    REG.mkdir(parents=True)
    dump(REG/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        policy='Report complete528eventcases x6variants x8arms before firstaggregateeventerrors; allregisteredlead/control/native/paired rules unchanged. Ordinarycohort remains incomplete and outside this checkpoint. Source-driven correction is separately queued; originalcalendar mismatch disclosed.',
        rows=25344, cases_per_arm=528, source_hashes={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))},
        source_contract='Unchangedfinalizer/auditor with explicitderivedone-cohort registration/planned25344rows. Copyclosedworkers/cases/protocol byte-for-byte; redirectOUT only, preserveROOT/source/protectedprior paths. Original35712-row fullstudy/registration/managers unchanged.',
        known_calendar_limit='KA2025Dussehra old2October versus notification1October; MH2022GudiPadwa evidencegap. No silentcorrection, allresults exploratory; not finalrankings on correctedcalendar.'))
    print('Registered complete event-only report; original scoring/auditor bytes fixed')


def run():
    reg = json.loads((REG/'registration.json').read_text())
    for name, expected in reg['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    if OUT.exists():
        raise FileExistsError('Preserve completed/interrupted event report')
    OUT.mkdir()
    try:
        shutil.copytree(PARENT/'event_window', OUT/'event_window')
        parent = json.loads((PARENT/'registration.json').read_text())
        derived = {**parent, 'cohorts': {'event_window': parent['cohorts']['event_window']},
                   'planned_rows': 25344,
                   'derived_report_scope': 'Complete event cohort only; original fullstudy continues',
                   'parent_registration_sha256': sha(PARENT/'registration.json')}
        dump(OUT/'registration.json', derived)
        for name in ['scoring_registration.json', 'protected_prior_files.json']:
            shutil.copy2(PARENT/name, OUT/name)
        for module in ['finalize_breadth_study', 'audit_breadth_study']:
            code = f'import sys;sys.path.insert(0,"src");import {module} as m;from pathlib import Path;m.OUT=Path({str(OUT)!r});m.main()'
            with (OUT/(module+'.execution.log')).open('w') as stream:
                subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                               stdout=stream, stderr=subprocess.STDOUT, check=True)
        assert json.loads((OUT/'independent_audit.json').read_text())['status'] == 'pass'
        import pandas as pd
        from report_multifestival import markdown
        scores = pd.read_csv(OUT/'event_window/primary_metrics_balanced.csv')
        table = scores[scores.horizon.eq(1)].pivot(index='model', columns='arm', values='MASE')
        table = table.reindex(parent['models'])[parent['arms']]
        (OUT/'README.md').write_text('''# Complete original-ledger festival-window checkpoint

All 25,344 forecasts are complete: 528 identical cases × six model variants × eight arms. The original registered finalizer and separate auditor run unchanged on an explicitly derived event-only registration. Every source/case/protocol/worker is a byte-identical closed copy. Original full-study files/managers are unchanged; the ordinary cohort and combined 35,712-forecast analysis remain separate and unfinished.

**Known calendar limitation:** these are original-ledger results. Karnataka2025Dussehra uses2October although the notification names1October; Maharashtra2022GudiPadwa has a separate evidence gap. Document-aligned flag/window/placebo corrections are registered elsewhere and still await foundation results. Do not treat these tables as corrected-calendar rankings or select a method/version on their errors.

Lead-1 event-window MASE (lower is better; not percentage accuracy):

'''+markdown(table.round(5).reset_index())+'''

All leads, zero and weekday-placebo controls, paired contrasts, both years/families, leave-family-out sensitivities, unmodified native uncertainty/crossings, actual-input and fitting audits are retained. Different local adaptation/total-history budgets preclude architecture-only claims. Two event years and correlated state/day/lead rows do not establish universal superiority, causality, an untouched test or independent human review.
''')
        # Proof that redirecting the reporting root left every original byte intact.
        assert all(sha(ROOT/name) == expected for name, expected in reg['source_hashes'].items())
        dump(OUT/'checkpoint.json', dict(status='complete_event_cohort_audited',
            completed_utc=datetime.now(timezone.utc).isoformat(), new_forecasts=0,
            reused_forecasts=25344, source_registration_sha256=sha(REG/'registration.json'),
            original_files_unchanged=True, ordinary_or_corrected_results_included=False))
        print(table.round(5).to_string())
    except BaseException:
        (OUT/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'run'])
    register() if parser.parse_args().action == 'register' else run()
