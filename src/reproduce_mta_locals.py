"""Complete same-machine isolated-environment MTA local reproduction.

Exact source/input copies and all 72 selection fits/all 4,032 local forecasts;
no network, foundation inference, target tuning or original result overwrite.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/clean_mta_v1'
SCRATCH = Path('/tmp/tsfm-clean-mta-v1')
PYTHON = Path('/workspace/tsfm-clean-review/bin/python')
STUDY = Path('results/mta_holiday_v1')
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def register():
    if OUT.exists() or SCRATCH.exists():
        raise FileExistsError('Preserve previous registration/reproduction')
    assert json.loads((ROOT/STUDY/'local_checkpoint/independent_audit.json').read_text())['status'] == 'pass'
    query = 'import importlib.metadata as m,json;print(json.dumps({n:m.version(n) for n in ["numpy","pandas","scipy","scikit-learn","lightgbm","statsmodels"]}))'
    packages = json.loads(subprocess.check_output([str(PYTHON), '-c', query], text=True))
    names = {str(p.relative_to(ROOT)) for p in (ROOT/'src').glob('*.py')}
    names |= {str(p.relative_to(ROOT)) for p in (ROOT/STUDY).iterdir()
              if p.is_file() and not p.name.startswith(('selection', 'acqui', 'local_', 'pipeline', 'chronos', 'timesfm'))
              and p.suffix in ['.json', '.csv']}
    for cohort in ['event_window', 'ordinary']:
        protocol_path = ROOT/STUDY/cohort/'protocol.json'
        protocol = json.loads(protocol_path.read_text())
        names |= set(protocol['input_hashes'])
        names |= {str(STUDY/cohort/name) for name in ['protocol.json', 'primary_cases.csv', 'window_cases.csv']}
    names |= {str(p.relative_to(ROOT)) for p in (ROOT/STUDY/'evidence').iterdir() if p.is_file()}
    OUT.mkdir(parents=True)
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        scope='All72past-onlyselectionfits and4032localforecasts in a no-system-packages Python environment on the SAME machine; not independent human/model implementation or foundation rerun.',
        source_root=str(SCRATCH), python=str(PYTHON), packages=packages,
        source_hashes={name: sha(ROOT/name) for name in sorted(names)},
        driver_sha256=sha(__file__), prediction_absolute_tolerance_million_rides=1e-9,
        prediction_relative_tolerance=1e-8, validation_MAE_absolute_tolerance_million_rides=1e-10,
        record_exact_bytes_and_all_failures=True,
        scipy_note='Clean SciPy1.18.1 versus original1.17.0 is explicitly a package-drift sensitivity, not an identical dependency claim. No tolerated difference may be hidden or threshold widened after outputs.'))
    print('Registered complete clean MTA rerun before its outputs')


def run():
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(__file__) == reg['driver_sha256']
    if SCRATCH.exists() or (OUT/'started.json').exists():
        raise FileExistsError('Inspect and preserve an existing run; never restart blindly')
    for name, expected in reg['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    SCRATCH.mkdir()
    for name in reg['source_hashes']:
        target = SCRATCH/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, target)
    dump(OUT/'started.json', dict(started_utc=datetime.now(timezone.utc).isoformat()))
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               MPLCONFIGDIR='/tmp/tsfm-mpl', XDG_CACHE_HOME='/tmp/tsfm-cache')
    commands = [('selection', ['src/mta_holiday_study.py', 'select'])]
    commands += [(cohort+'_'+model, ['src/mta_holiday_study.py', model, '--cohort', cohort])
                 for cohort in ['event_window', 'ordinary'] for model in MODELS]
    commands += [('finalize', ['src/finalize_mta_holiday.py', 'analyze', '--part', 'local']),
                 ('separate_audit', ['src/audit_mta_holiday.py', '--part', 'local'])]
    try:
        for name, command in commands:
            print('Clean MTA:', name, flush=True)
            with (OUT/(name+'.execution.log')).open('w') as stream:
                subprocess.run([str(PYTHON), *command], cwd=SCRATCH, env=env,
                               stdout=stream, stderr=subprocess.STDOUT, check=True)
        # Compare independently by explicit identity, never CSV row position.
        import csv
        def rows(path):
            with Path(path).open(newline='') as stream:
                return list(csv.DictReader(stream))
        keys = ['family', 'state', 'year', 'origin', 'date', 'horizon', 'model', 'arm']
        stats = {}
        failures = []
        for cohort in ['event_window', 'ordinary']:
            for model in MODELS:
                relative = STUDY/cohort/model/'predictions.csv'
                original = rows(ROOT/relative)
                clean = rows(SCRATCH/relative)
                lookup = {tuple(row[k] for k in keys): row for row in original}
                assert len(lookup) == len(original) == len(clean)
                assert set(lookup) == {tuple(row[k] for k in keys) for row in clean}
                diffs = []
                for row in clean:
                    reference = lookup[tuple(row[k] for k in keys)]
                    a, b = float(row['prediction']), float(reference['prediction'])
                    assert row['actual'] == reference['actual'] and row['mase_scale'] == reference['mase_scale']
                    error = abs(a-b)
                    diffs.append(error)
                    if error > reg['prediction_absolute_tolerance_million_rides']+reg['prediction_relative_tolerance']*abs(b):
                        failures.append(dict(cohort=cohort, model=model, case={k: row[k] for k in keys},
                                             original=b, reproduced=a, difference=error))
                stats[cohort+'/'+model] = dict(rows=len(clean), maximum_absolute_difference_million_rides=max(diffs),
                    prediction_csv_byte_identical=sha(ROOT/relative) == sha(SCRATCH/relative),
                    original_sha256=sha(ROOT/relative), reproduced_sha256=sha(SCRATCH/relative))
                target = OUT/cohort/model
                target.mkdir(parents=True)
                for name in ['predictions.csv', 'run.json', 'fit_log.json', 'fit_attempts.json', 'deployments.json']:
                    source = SCRATCH/relative.parent/name
                    if source.exists():
                        shutil.copy2(source, target/name)
        original = json.loads((ROOT/STUDY/'selection.json').read_text())
        clean = json.loads((SCRATCH/STUDY/'selection.json').read_text())
        assert original['parameters'] == clean['parameters']
        assert len(original['attempts']) == len(clean['attempts']) == 72
        original_trials = {(r['state'], r['model'], r['horizon'], r['configuration']): r for r in original['attempts']}
        validation_differences = []
        for trial in clean['attempts']:
            reference = original_trials[tuple(trial[k] for k in ['state', 'model', 'horizon', 'configuration'])]
            for key in ['training_X_sha256', 'training_y_sha256', 'parameters', 'validation_n', 'validation_target_max']:
                assert trial[key] == reference[key], key
            error = abs(trial['validation_MAE_million_rides']-reference['validation_MAE_million_rides'])
            validation_differences.append(error)
            if error > reg['validation_MAE_absolute_tolerance_million_rides']:
                failures.append(dict(scope='selection_MAE', trial=trial, difference=error))
        assert sum(v['rows'] for v in stats.values()) == 4032
        for name in ['selection.json', 'local_checkpoint/independent_audit.json', 'local_checkpoint/run.json']:
            shutil.copy2(SCRATCH/STUDY/name, OUT/name.replace('/', '_'))
        result = dict(status='pass' if not failures else 'fail', completed_utc=datetime.now(timezone.utc).isoformat(),
            scope=reg['scope'], workers=stats, rows=4032, selection_fits=72,
            maximum_validation_MAE_difference_million_rides=max(validation_differences),
            selected_parameters_identical=True, failures=failures, registration_sha256=sha(OUT/'registration.json'),
            source_copies_reverified=all(sha(SCRATCH/name) == expected for name, expected in reg['source_hashes'].items()))
        dump(OUT/'comparison.json', result)
        if failures:
            raise AssertionError('Retained clean reproduction differences; do not widen thresholds')
        print(json.dumps(result, indent=2), flush=True)
    except BaseException:
        (OUT/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'run'])
    args = parser.parse_args()
    register() if args.action == 'register' else run()
