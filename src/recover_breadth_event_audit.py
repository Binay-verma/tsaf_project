"""Preserve failed event audit, copy its completed science and audit a new root.

The original frozen review brief has been restored; its update has a new name.
No score, prediction, protocol, source, method or audit tolerance is changed.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'results/feature_breadth_event_checkpoint_v1'
OUT = ROOT/'results/feature_breadth_event_checkpoint_recovery_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError('Preserve a previous recovery')
    assert (OLD/'failure.txt').exists() and (OLD/'run.json').exists()
    protected = json.loads((OLD/'protected_prior_files.json').read_text())
    assert all(sha(ROOT/name) == expected for name, expected in protected.items())
    before = {str(p.relative_to(OLD)): sha(p) for p in OLD.rglob('*.csv')}
    assert before
    shutil.copytree(OLD, OUT, ignore=shutil.ignore_patterns('failure.txt', 'audit_breadth_study.execution.log'))
    registration = dict(registered_utc=datetime.now(timezone.utc).isoformat(),
        policy='Directory-only audit recovery after restoring one protected review document byte-for-byte; updated review guidance in a NEWfile. Original failed audit retained. No new inference, changed metric/source/protocol/tolerance or claim of prior audit success.',
        protected_files_restored_and_verified=len(protected), scientific_csv_hashes=before,
        parent_failure_sha256=sha(OLD/'failure.txt'),
        unchanged_audit_source_sha256=sha(ROOT/'src/audit_breadth_study.py'))
    (OUT/'recovery_registration.json').write_text(json.dumps(registration, indent=2)+'\n')
    try:
        code = f'import sys;sys.path.insert(0,"src");import audit_breadth_study as m;from pathlib import Path;m.OUT=Path({str(OUT)!r});m.main()'
        with (OUT/'audit_recovery.execution.log').open('w') as stream:
            subprocess.run([sys.executable, '-c', code], cwd=ROOT, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        assert json.loads((OUT/'independent_audit.json').read_text())['status'] == 'pass'
        assert all(sha(OLD/name) == expected == sha(OUT/name) for name, expected in before.items())
        import pandas as pd
        from report_multifestival import markdown
        d = pd.read_csv(OUT/'event_window/primary_metrics_balanced.csv')
        models = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']
        arms = ['calendar', 'zero5', 'day5', 'pooled_day5', 'window5', 'pooled_window5', 'placebo_day5', 'placebo_window5']
        table = d[d.horizon.eq(1)].pivot(index='model', columns='arm', values='MASE').reindex(index=models, columns=arms)
        (OUT/'README.md').write_text('''# Complete original-ledger event checkpoint: audited recovery

All 25,344 existing forecasts are retained:528identical cases × sixvariants × eightarms. This is the COMPLETE event cohort; the ordinary cohort/full35,712-rowstudy and corrected-calendar foundation comparisons remain separate and unfinished. The unchanged registered finalizer generated the event scores. The separate frozen auditor now passes source/case/label/scale/actual-foundation-input/native/probability/local-budget/chronology/protected-file checks.

The first audit stopped because a frozen review brief had been updated. Its original bytes are restored and all1,023protectedfiles verify; updated guidance is now in review/INDEPENDENT_REVIEW_UPDATE_20261031.md. Original failure/evidence remain in feature_breadth_event_checkpoint_v1. This NEWdirectory-only recovery copies every scientificCSV byte-for-byte; no inference, score, protocol or tolerance changed. recovery_registration.json records the exact proof.

**Known calendar limitation:** originalKA2025Dussehra uses2October while the notification names1October; MH2022GudiPadwa has a separate evidence gap. Flag-only/recentered/weekday-placebo corrections are registered elsewhere. These are not corrected-calendar rankings or a reason to select a version on its errors.

Lead-1 original-ledger complete-window MASE; lower is better, not percentage accuracy:

'''+markdown(table.round(5).reset_index())+'''

All three leads/controls/paired contrasts/both years/families/leave-family-out composition/native intervals and crossings remain available. Local adaptation and raw-history access differ from foundation inference. No universal winner, causal effect, untouched test, independent human review or journal acceptance follows from this checkpoint.
''')
        result = dict(status='complete_event_cohort_audited', completed_utc=datetime.now(timezone.utc).isoformat(),
            new_forecasts=0, reused_forecasts=25344, byte_identical_scientific_csvs=len(before),
            original_failure_retained=True, all_protected_files_restored=True,
            ordinary_or_corrected_results_included=False)
        (OUT/'checkpoint.json').write_text(json.dumps(result, indent=2)+'\n')
        print(table.round(5).to_string())
        print(json.dumps(result, indent=2))
    except BaseException:
        (OUT/'recovery_failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
