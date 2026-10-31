"""Manual-only, append-only rolling study execution. Not activated.

The CLI reads the actual clock; it offers no date override. Registration and
fixture tests neither retrieve outcomes nor enable a scheduler/workflow.
"""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import traceback
import urllib.request

import numpy as np
import pandas as pd

from rolling_evidence_v1 import (
    ROOT, BASE, SOURCE, METADATA, STATES, sha, dump, planned, issuance_gate,
    collection_gate, parse_source, calendar_package, case_matrix,
    first_commit_guard, score_cases, metrics, within)


def clock():
    return datetime.now(timezone.utc)


def fetch():
    with urllib.request.urlopen(SOURCE, timeout=30) as response:
        raw = response.read()
    with urllib.request.urlopen(METADATA, timeout=30) as response:
        meta = response.read()
    return raw, meta


def validate_registration():
    reg = json.loads((BASE/'registration.json').read_text())
    for name, expected in reg['inputs'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('Registered runtime dependency changed:'+name)
    for name, expected in reg['provider_code_files'].items():
        if sha(name) != expected:
            raise ValueError('Installed pinned provider code changed:'+name)
    return reg


def prerequisites(number, now):
    path = BASE/'activation.json'
    if not path.exists():
        raise ValueError('UNACTIVATED: reviewed source/date/calendar prerequisites missing')
    activation = json.loads(path.read_text())
    if activation['status'] != 'reviewed_prerequisites' or activation['source_units'] != 'GWh' or activation['source_observation_day_confirmed'] is not True:
        raise ValueError('Unresolved source unit/day convention')
    if datetime.fromisoformat(activation['reviewed_utc']) > now:
        raise ValueError('Review is not yet available')
    for key in ['source_rights_evidence', 'source_date_evidence']:
        item = activation[key]
        if sha(within(ROOT, item['file'])) != item['sha256']:
            raise ValueError('Missing/changed reviewed source evidence')
    manifest = within(ROOT, activation['calendar_manifest'])
    if sha(manifest) != activation['calendar_manifest_sha256']:
        raise ValueError('Calendar package changed since review')
    package, anchors, fake = calendar_package(manifest, number, now)
    from rolling_evidence_v1 import FAMILIES
    required = {(state, year, family) for state in STATES for year in range(2024, 2028) for family in FAMILIES}
    if not required.issubset({(row['state'], row['year'], row['family']) for row in package['coverage']}):
        raise ValueError('Original plan requires complete2024–2027calendar package before activation')
    return activation, manifest, package, anchors, fake


def register():
    if BASE.exists():
        raise FileExistsError('Preserve old runtime registration')
    from rolling_confirmation_plan import OUT as PLAN
    inputs = ['src/rolling_execution_v1.py', 'src/rolling_evidence_v1.py',
        'src/rolling_models_v1.py', 'src/test_rolling_runtime_v1.py',
        'src/rolling_confirmation_plan.py', 'src/forecasting.py',
        'src/robust_baselines.py', 'src/multifestival_models.py',
        'results/rolling_confirmation_plan_v1/protocol.json',
        'results/rolling_confirmation_plan_v1/schedule.json',
        'results/mechanism_controls_v1/chronos_download.json',
        'results/second_model_audit_v1/weight_download.json',
        'results/second_model_audit_v1/installed_code_identity.json']
    original = json.loads((PLAN/'protocol.json').read_text())
    for name, expected in original['input_hashes'].items():
        assert sha(ROOT/name) == expected, name
    import importlib.util
    provider_code = {}
    for name in ['chronos', 'timesfm3']:
        spec = importlib.util.find_spec(name)
        package = Path(spec.origin).parent
        for path in package.rglob('*.py'):
            provider_code[str(path)] = sha(path)
    BASE.mkdir()
    dump(BASE/'registration.json', dict(registered_utc=clock().isoformat(),
        status='SOFTWARE_ONLY_UNACTIVATED; no forecasts, source capture or future actuals',
        scope='Executable manual issue/public-receipt/first-complete-vintage/scoring adapters for unchanged52weekly schedule and6models/8arms/3states/3decisionleads. No scheduler/workflow activation, outcome-based selection or old-freeze writes.',
        clarifications_before_new_outcomes={
            'scale':'Fixed730calendar-day observed weekly scale ending31December BEFORE ISSUANCEyear, also for targets crossingNewYear. At least365validweeklypairs. This resolves an unspecified boundary without future labels.',
            'local_fit':'Preceding730label-calendar-days; directmodelsteps3/9/16 with strict label purge. Rich27historymay accessolderlags, ashistoricalmodels. Ridge10/tree7leaves200rounds/.05/L2=10/minleaf20or2; fixedSARIMAXorder(1,0,0)x(1,0,0,7), no trend, y/100 thenGWhbackconversion, original training-only convergence retries.',
            'matrix':'432eligiblepointrows perissue;768full16stepfoundationpaths, allnativequantiles/crossings. Chronosmedian versus TimesFMnativepoint. All48foundationinputblocks/all48solochecks; context730, horizon16, seed42/2threads, nofinetuning.',
            'calendar':'ExplicitprimaryPDF/noticehashes, allusedstate-year-familycoverage andabsent-familydeclarations. Everytrue/subsidiaryanchor hasoneweekdayplacebo shifted28/35/42days, sameyear, withnonoverlappingtruewindows. No implicit missingyearzero. Perissuepackage frozen; this does not certify finalamendments or humanreview.',
            'actuals':'After full14-dayperiod endsUTC only. Retain everyincomplete/failedretrieval attempt; firstcomplete common positive recordedlabels immutable. Onevintage for all432rows. No imputation/favourablecaseintersection; nativeinvalidendpoints propagateundefined aggregates.',
            'scoring':'AllpointMAE/MASE and nativecommon.1–.9pinball/80coverage/width/WISmedian. Reportall/outside-named-windows/eachdeclaredfamily; overlappingfamilycases notindependent. Equalstatewithin model/arm/lead, no tests/retuning/calibration.',
            'publication':'Actualcompletion ANDfirstforecastcommit ANDobservedremote receipt mustlie within scheduled09:00–09:59UTC. Firstcommit hashguards cover source/metadata, completehistory/calendarpackage, input/fit/solo logs, predictions/nativepaths andfreeze. No backdating; failed/lateissue retained, neverreplaced.',
            'activation':'Notcreated. Requires realreviewed source-rights/date evidence and datedprimarycalendarpackage; no fictional approvals or permissions. Source terms/report-day/calendar/human/futuregates remain open.'},
        inputs={name: sha(ROOT/name) for name in inputs}, provider_code_files=provider_code))
    (BASE/'README.md').write_text('''# Manual rolling runtime — software only, not activated

The original52Monday09:00UTC schedule begins16November2026. No forecast or data capture is issued now. No automatic job is created or enabled. Missing reviewed source-day/rights evidence and primary dated calendars block execution.

Commands: `python src/rolling_execution_v1.py status`, then at a genuinely eligible future time, with factual prerequisites supplied, `issue --number 0`. Normal commit/push ALL issue artifacts, then `receipt --number 0`, then push its receipt before09:59UTC. Never edit frozen files. After the full target period endsUTC, `collect --number 0` retains attempts and the first complete shared actual vintage; `score --number 0` is separate and reads no network. `miss --number 0` records a missed window, never hindsight predictions. There is no CLI clock override.

`activation.json` is deliberately absent. Its factual fields must identify reviewed source units/observation-day evidence, rights evidence and hashed primary calendar manifest; a filename or internal boolean is not a legal or human-review certification. Inspect the code and registration before future operation. Calendar manifests contain explicit coverage/documents/anchors/placebos, not guessed dates.

Fixture tests use temporary synthetic data/models/clocks; they do not constitute actual issuance, future accuracy, independent human review or complete real-foundation numerical reproduction. Current outcomes and external gates remain in the main handoff.
''')


def folder_for(number):
    planned(number)
    return BASE/'issuances'/f'{number:02d}'


def issue(number, now_fn=clock, fetch_fn=fetch, forecast_fn=None):
    contract = issuance_gate(number, now_fn())  # MUST precede source/network/weights.
    validate_registration()
    activation, manifest_path, package, anchors, fake = prerequisites(number, now_fn())
    folder = folder_for(number)
    if folder.exists():
        raise FileExistsError('Preserve completed/failed/missed issuance')
    folder.mkdir(parents=True)
    dump(folder/'started.json', dict(started_utc=now_fn().isoformat(), number=number))
    try:
        shutil.copy2(BASE/'registration.json', folder/'runtime_registration.json')
        dump(folder/'prerequisite_review.json', activation)
        calendar = folder/'calendar'
        calendar.mkdir()
        shutil.copy2(manifest_path, calendar/'manifest.json')
        for relative in [package['anchors'], package['placebos']]+[item['file'] for item in package['documents'].values()]:
            target = calendar/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest_path.parent/relative, target)
        # Freeze the actual reviewed source-evidence files, not only references.
        evidence = folder/'source_evidence'
        evidence.mkdir()
        for key in ['source_rights_evidence', 'source_date_evidence']:
            shutil.copy2(ROOT/activation[key]['file'], evidence/(key+Path(activation[key]['file']).suffix))
        raw, metadata = fetch_fn()
        captured = now_fn()
        issuance_gate(number, captured)
        (folder/'source.raw').write_bytes(raw)
        (folder/'metadata.raw').write_bytes(metadata)
        dump(folder/'capture.json', dict(captured_utc=captured.isoformat(), source_url=SOURCE, metadata_url=METADATA,
            raw_sha256=sha(folder/'source.raw'), metadata_sha256=sha(folder/'metadata.raw')))
        source = parse_source(raw, metadata)
        from rolling_evidence_v1 import available_history
        history = available_history(source, number)
        history.to_csv(folder/'available_history.csv')
        if forecast_fn is None:
            from rolling_models_v1 import forecast
            forecast_fn = forecast

        def progress(value):
            for name, rows in value.items():
                dump(folder/(name+'.json'), rows)

        predictions, native, logs = forecast_fn(history, anchors, fake, number, progress=progress)
        progress(logs)
        case_matrix(predictions.to_dict('records'), number)
        from rolling_evidence_v1 import ARMS
        expected = {(m, a, s, h) for m in ['chronos', 'timesfm'] for a in ARMS for s in STATES for h in range(1, 17)}
        given = set(map(tuple, native[['model', 'arm', 'state', 'model_step']].to_numpy()))
        if len(native) != 768 or given != expected or len(logs['inputs']) != 48 or len(logs['solo_batch_audit']) != 48:
            raise ValueError('Incomplete native full-path matrix')
        issued = now_fn()  # Actual completion AFTER all model/solo checks.
        issuance_gate(number, issued)
        predictions['issued_utc'] = issued.isoformat()
        predictions.to_csv(folder/'predictions.csv', index=False)
        native.to_csv(folder/'native_paths.csv', index=False)
        packages = {name: importlib.metadata.version(name) for name in
            ['numpy', 'pandas', 'scikit-learn', 'lightgbm', 'statsmodels', 'torch', 'chronos-forecasting', 'timesfm']}
        dump(folder/'freeze.json', dict(number=number, issued_utc=issued.isoformat(),
            contract=contract, rows=432, native_path_rows=768, outcomes_fetched=False,
            packages=packages, files={str(p.relative_to(folder)): sha(p) for p in folder.rglob('*') if p.is_file()},
            note='Unscored manual forecast; requires normal public commit/observed receipt before09:59UTC. No independent review/rights certification implied.'))
    except BaseException:
        (folder/'failure.txt').write_text(traceback.format_exc())
        raise


def receipt(number):
    issuance_gate(number, clock())
    folder = folder_for(number)
    first = first_commit_guard(folder, require_receipt=False)
    path = folder/'public_receipt.json'
    if path.exists():
        raise FileExistsError('Preserve first observed receipt')
    local = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    if local != remote:
        raise ValueError('Normal push/remote verification required')
    observed = clock()
    issuance_gate(number, observed)
    dump(path, dict(observed_utc=observed.isoformat(), first_forecast_commit=first,
        observed_remote_sha=remote, predictions_sha256=sha(folder/'predictions.csv'),
        limit='Observed Git remote, not independent server-signed first-publication certification'))


def collect(number, now_fn=clock, fetch_fn=fetch):
    collection_gate(number, now_fn())  # No early network/actual reads.
    validate_registration()
    folder = folder_for(number)
    first_commit_guard(folder)
    destination = folder/'actuals'
    if destination.exists():
        verify_actuals(folder)
        return 'ALREADY_COMPLETE: preserve first actual vintage; no network'
    attempts = folder/'actual_attempts'
    attempts.mkdir(exist_ok=True)
    prior = sorted(attempts.glob('*/collection.json'))
    if any(json.loads(path.read_text()).get('complete') for path in prior):
        raise ValueError('Earlier complete attempt exists without sealed actuals; manual review required')
    attempt = attempts/f'{len(list(attempts.iterdir())):04d}'
    attempt.mkdir()
    descriptor = dict(started_utc=now_fn().isoformat(), complete=False)
    dump(attempt/'collection.json', descriptor)
    try:
        raw, metadata = fetch_fn()
        (attempt/'source.raw').write_bytes(raw)
        (attempt/'metadata.raw').write_bytes(metadata)
        descriptor.update(captured_utc=now_fn().isoformat(), source_url=SOURCE, metadata_url=METADATA,
            raw_sha256=sha(attempt/'source.raw'), metadata_sha256=sha(attempt/'metadata.raw'))
        source = parse_source(raw, metadata)
        predictions = pd.read_csv(folder/'predictions.csv')
        dates = sorted(pd.to_datetime(predictions.date.unique()))
        actuals = source.reindex(dates)[STATES]
        if actuals.isna().any().any():
            dump(attempt/'collection.json', descriptor)
            return 'PENDING: incomplete recorded labels, attempt retained; no score'
        actuals.to_csv(attempt/'actuals.csv')
        descriptor.update(complete=True, actuals_sha256=sha(attempt/'actuals.csv'))
        dump(attempt/'collection.json', descriptor)
        # Parent was just checked absent. copytree refuses an existing destination.
        shutil.copytree(attempt, destination)
        return 'FIRST_COMPLETE_ACTUAL_VINTAGE_SEALED; scoring remains separate'
    except BaseException:
        (attempt/'failure.txt').write_text(traceback.format_exc())
        raise


def verify_actuals(folder):
    path = folder/'actuals'
    meta = json.loads((path/'collection.json').read_text())
    freeze = json.loads((folder/'freeze.json').read_text())
    collection_gate(freeze['number'], datetime.fromisoformat(meta['captured_utc']))
    if not meta['complete'] or sha(path/'source.raw') != meta['raw_sha256'] or sha(path/'metadata.raw') != meta['metadata_sha256'] or sha(path/'actuals.csv') != meta['actuals_sha256']:
        raise ValueError('Sealed actual snapshot changed/incomplete')
    complete = [p for p in sorted((folder/'actual_attempts').glob('*/collection.json')) if json.loads(p.read_text()).get('complete')]
    if not complete or complete[0].read_bytes() != (path/'collection.json').read_bytes():
        raise ValueError('Actuals are not the first complete retained attempt')
    for name in ['source.raw', 'metadata.raw', 'actuals.csv']:
        if sha(complete[0].parent/name) != sha(path/name):
            raise ValueError('First complete attempt differs from sealed actuals')
    return meta


def score(number):
    collection_gate(number, clock())
    validate_registration()
    folder = folder_for(number)
    first = first_commit_guard(folder)
    meta = verify_actuals(folder)
    destination = folder/'scores'
    if destination.exists():
        raise FileExistsError('Preserve first scored evaluation')
    predictions = pd.read_csv(folder/'predictions.csv')
    actuals = pd.read_csv(folder/'actuals/actuals.csv', index_col=0, parse_dates=True)
    cases = score_cases(predictions, actuals, number)
    summary = metrics(cases)
    destination.mkdir()
    cases.to_csv(destination/'cases.csv', index=False)
    summary.to_csv(destination/'metrics.csv', index=False)
    dump(destination/'run.json', dict(scored_utc=clock().isoformat(), rows=len(cases),
        first_forecast_commit=first, first_actuals_sha256=meta['actuals_sha256'],
        cases_sha256=sha(destination/'cases.csv'), metrics_sha256=sha(destination/'metrics.csv'),
        limit='One dependent issuance; internal scorer, no independent scientific audit or outcome-based selection'))


def miss(number):
    if clock() <= planned(number)+timedelta(minutes=59):
        raise ValueError('Cannot declare a future issuance missed')
    folder = folder_for(number)
    if folder.exists():
        raise FileExistsError('Preserve prior issuance/failure/miss')
    folder.mkdir(parents=True)
    dump(folder/'missed.json', dict(recorded_utc=clock().isoformat(), number=number,
        reason='No completed public issuance in registered window; no hindsight replacement'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'register', 'issue', 'receipt', 'collect', 'score', 'miss'])
    parser.add_argument('--number', type=int)
    args = parser.parse_args()
    if args.action == 'status':
        print('SOFTWARE_ONLY_UNACTIVATED: no scheduler or new forecast; prerequisites and genuine future window required')
    elif args.action == 'register':
        register()
    else:
        if args.number is None:
            parser.error('--number required')
        result = globals()[args.action](args.number)
        if result:
            print(result)
