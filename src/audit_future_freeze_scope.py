"""Read-only scope/chronology audit of the two already public future freezes.

Reads predictions/their historical Git blobs and read-only GitHub workflow
metadata, never actual labels or a data provider. Keeps original artifacts intact.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/future_freeze_scope_v1'
EPISODES = [
    ('prospective_20261030_v1', 'cabd5982e1948652b9841d6c31a2380f6f314198',
     ['protocol.json', 'predictions.csv', 'freeze.json', 'fits.json', 'selection.json']),
    ('prospective_interval_20261030_v1', '29bdd984770904a032cebe9efcd2a12a8d5ffc17',
     ['registration.json', 'predictions.csv', 'freeze.json', 'calibration_log.json', 'scoring_registration.json']),
]


def main():
    if OUT.exists():
        raise FileExistsError('Preserve previous scope audit')
    india = ZoneInfo('Asia/Calcutta')
    summary = {}
    for name, expected_commit, guarded in EPISODES:
        path = ROOT/'results'/name
        relative = str((path/'predictions.csv').relative_to(ROOT))
        commits = subprocess.check_output(['git', 'rev-list', '--reverse', 'HEAD', '--', relative],
                                          cwd=ROOT, text=True).splitlines()
        assert commits[0] == expected_commit
        hashes = {}
        for filename in guarded:
            p = path/filename
            blob = subprocess.check_output(['git', 'show', expected_commit+':'+str(p.relative_to(ROOT))], cwd=ROOT)
            assert blob == p.read_bytes(), (name, filename)
            hashes[filename] = hashlib.sha256(blob).hexdigest()
        with (path/'predictions.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 252
        freeze = json.loads((path/'freeze.json').read_text())
        issued = datetime.fromisoformat(freeze['issued_utc'])
        assert issued.tzinfo is not None
        eligible = [row for row in rows if row['prospective_eligible'].lower() == 'true']
        assert len(eligible) == 216
        dates = sorted({row['date'][:10] for row in eligible})
        assert dates[0] == '2026-10-31' and dates[-1] == '2026-11-11'
        for row in eligible:
            target_start = datetime.fromisoformat(row['date'][:10]).replace(tzinfo=india)
            assert target_start > issued, (name, row['date'])
        models = sorted({row['model'] for row in rows})
        summary[name] = dict(first_prediction_git_commit=commits[0], guarded_files=hashes,
            issued_utc=issued.isoformat(), issued_india=issued.astimezone(india).isoformat(),
            rows=len(rows), eligible_rows=len(eligible), eligible_start=dates[0], eligible_end=dates[-1],
            models=models, eligible_full_india_days_after_issue=True)
    expected = {'timesfm3_history', 'timesfm3_calendar', 'ridge_rich_calendar_monthly',
                'lightgbm_rich_calendar_monthly', 'last_value', 'weekly_repeat'}
    assert set(summary['prospective_20261030_v1']['models']) == expected
    assert set(summary['prospective_interval_20261030_v1']['models']) == {'timesfm3_history', 'timesfm3_calendar'}
    protocol = json.loads((ROOT/'results/prospective_20261030_v1/protocol.json').read_text())
    source = ROOT/protocol['context_snapshot']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == protocol['context_sha256']
    assert 'No unverified 2026 regional holiday inputs' in protocol['calendar']
    workflow = ROOT/'.github/workflows/prospective-evaluation.yml'
    # Activation is server-side state, not a marker in the workflow YAML.
    workflow_metadata = json.loads(subprocess.check_output([
        'gh', 'api', 'repos/Binay-verma/tsaf_project/actions/workflows/prospective-evaluation.yml',
        '--jq', '{id,name,path,state,updated_at}'], cwd=ROOT, text=True))
    assert workflow_metadata['state'] == 'disabled_manually'
    audit = dict(status='pass', audited_utc=datetime.now(timezone.utc).isoformat(),
        scope='Exact first-Git-blob preservation, configuration scope, source hash, actual issuance/full India-day chronology and read-only live GitHub workflow state; no actual labels/data-provider request/model inference or independent human review.',
        episodes=summary, source_sha256=protocol['context_sha256'], workflow_sha256=hashlib.sha256(workflow.read_bytes()).hexdigest(),
        workflow_metadata=workflow_metadata,
        chronos_future_forecasts_present=False, festival_feature_future_comparison_present=False,
        interpretation='The original episode and later interval annex do not directly confirm typed/pooling festival-feature hypotheses. A new competitor or feature issuance requires its own registered protocol, verified future covariates, actual completion time, full local-day eligibility and pre-outcome public freeze. Old forecasts stay immutable.',
        public_time_limit='First committed blobs and prior recorded remote verifications are retained; local Git alone does not independently certify the time of first public server visibility.')
    OUT.mkdir(parents=True)
    (OUT/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    (OUT/'README.md').write_text('''# Actual scope of the frozen future evidence

The original six-configuration episode and later interval annex remain byte-identical to their first prediction commits. Both were actually issued before the beginning of their eligible full Indian daily targets. The context snapshot hash and live GitHub workflow state pass their checks. The workflow remains disabled_manually; activation is server-side state, not a YAML marker. The only network request reads GitHub workflow metadata; no actual labels, data-provider request or new inference is part of this audit.

The original episode includes **TimesFM history/calendar, Ridge, the original float64 LightGBM and two naive baselines**. It contains **no Chronos or festival-feature comparison**. The interval annex adds three interval arms to the same TimesFM cases with an actual later issue time; it does not add an independent episode. Thus later outcomes cannot directly confirm the main typed-versus-pooled festival hypothesis.

Any new issuance needs a new named protocol and genuinely available covariates, an actual completion time, full India-day eligibility and a public pre-outcome freeze. Do not backdate or modify old forecasts, guess unverified regional dates, activate the paused workflow or treat Git metadata alone as independent server-time certification. Detailed hashes/configurations/timestamps are in audit.json. This is an internal audit, not human approval or future accuracy.
''')
    print(json.dumps({key: value for key, value in audit.items() if key != 'episodes'}, indent=2))


if __name__ == '__main__':
    main()
