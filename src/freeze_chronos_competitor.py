"""Separately timed Chronos future competitor; original episode is immutable.

No actual-source acquisition or scoring. New two-thread inference follows the
existing Chronos provider lane. Only full Indian days after actual completion
are eligible; a missed issuance deadline is a hard failure, never backdated.
"""
import argparse
from datetime import datetime, timezone, date
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import traceback
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from forecasting import ROOT
from timesfm_fixture import build_input

OUT = ROOT/'results/prospective_chronos_20261031_v1'
PARENT = ROOT/'results/prospective_20261030_v1'
PARENT_COMMIT = 'cabd5982e1948652b9841d6c31a2380f6f314198'
INDIA = ZoneInfo('Asia/Calcutta')
FIRST = date(2026, 11, 1)
LAST = date(2026, 11, 11)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def deadline(now):
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Require an explicit timezone for actual issuance')
    local = now.astimezone(INDIA)
    if local.date() != date(2026, 10, 31):
        raise ValueError('Actual India issuance day must be31October; preserve and version a missed window')
    if now >= datetime(2026, 11, 1, tzinfo=INDIA):
        raise ValueError('First eligible full target day has begun; no backdating')


def guard_parent():
    for name in ['protocol.json', 'predictions.csv', 'freeze.json', 'fits.json', 'selection.json']:
        relative = str((PARENT/name).relative_to(ROOT))
        original = subprocess.check_output(['git', 'show', PARENT_COMMIT+':'+relative], cwd=ROOT)
        assert original == (PARENT/name).read_bytes(), name


def inputs(data, state, origin, mode):
    return build_input(data[state], state, origin, mode, context=730)


def register():
    if OUT.exists():
        raise FileExistsError('Preserve an earlier future protocol')
    deadline(datetime.now(timezone.utc))
    guard_parent()
    parent = json.loads((PARENT/'protocol.json').read_text())
    names = ['src/freeze_chronos_competitor.py', 'src/score_chronos_competitor.py',
             'src/audit_chronos_competitor.py', 'src/test_chronos_competitor.py',
             'src/run_chronos_competitor_after_mta.py',
             'src/timesfm_fixture.py', 'src/extended_validation.py', 'src/forecasting.py',
             'results/mechanism_controls_v1/chronos_download.json',
             'results/prospective_20261030_v1/protocol.json',
             'results/prospective_20261030_v1/predictions.csv',
             'results/prospective_20261030_v1/freeze.json',
             parent['context_snapshot']]
    OUT.mkdir(parents=True)
    protocol = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Newcompetitor registered before its predictions or any futurelabels. Historicalcomparisons alreadyinspected; not a retrospectively untouched method claim.',
        configurations=['chronos2_history', 'chronos2_calendar'], states=parent['states'],
        context_snapshot=parent['context_snapshot'], context_sha256=parent['context_sha256'],
        context_last_observation='2026-10-28', first_unseen_origin='2026-10-29',
        model_steps=list(range(1, 15)), targets=['2026-10-29', '2026-11-11'],
        first_eligible='2026-11-01', last_eligible='2026-11-11',
        expected_rows=84, expected_eligible_rows=66, expected_common_parent_rows=198,
        eligibility='Actualcompletion and firstpubliccommit must precede1November00:00India. Issue31OctoberIndia only; fullNov1–11targets. Modelsteps4–14 under sameoldcontext asparent; no assumption ofequalissuance times orreal-timelead1.',
        input='Same730recorded/causallyfilled past target days and ordinary13weekday/annualharmonic channels asoriginalTimesFM. No named2026festivalflags or guessedcalendar. Allfuturetargets NaN; perturb at/afterorigin and verifyinputbytes. No datarefresh.',
        foundation='Exactly pinnedChronos2 revision29ec3766d36d6f73f0696f85560a422f50e8498c/actualweightddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42. CPU2threads/seed42/context730/h14/batch3states/cross_learningFalse/pipelinebatch128. No finetuning orerror-selectedsettings.',
        points='Use nativeChronosmedian; retainall21nativequantiles/crossings, common.1–.9forpairedprobabilityscores. Batchversussoloall6tasks checked withunchangedhistoricalrtol2e-4/atol1e-3GWh; norepair.',
        parent_comparison='Reuseunchangedall6parentconfigurations onexactcommonNov1–11states/dates/modelsteps4–14. Eighttotalconfigs/264pointrows,4foundationconfigs/132nativecommonquantilecases. Differentactualissuances butidenticalsource/context/forecaststeps; not twoindependentepisodes.',
        scoring='Onlyafter11NovemberendsUTC; use SAMEcompletedfirstoriginalactualcollection/vintage, no alternativecapture. Fixedpre2026weeklyscale fromoriginal. State/date/step pointMAE/MASE and equalstatemeans; unchangednativecommonquantiles meanpinball/80coverage/width/WISmedian, invalidendpoints propagateundefined. Allconfigs, no winnerdeployment/retuning/rowindependenttests.',
        guards='Freeze completedpredictions/timestamps/inputbytes/actualweights/protocol/sourcehashes, then normalpublicpush beforefirsteligibleIndia-day. No overwrite ofoldfuture/annex, no workflowactivation orautoactualfetch.',
        limitations='Oneadditionalcompetitor in SAMEsource/episode/stalecontext, not independentyear/source or a prospectivefestival-featuretest. Oldfloat64tree remainsasissued. Calendaramendments/Indianreuse/humanreview/proxyexposure/futureoutcomes remain separategates.',
        source_hashes={name: sha(ROOT/name) for name in names})
    dump(OUT/'protocol.json', protocol)
    (OUT/'README.md').write_text('''# New Chronos future competitor: protocol only

This separately timed issuance adds Chronos history/calendar forecasts using the original context through 28 October and no unverified 2026 festival flags. It must finish and be publicly frozen on 31 October, India time, before the eligible full 1–11 November days. The stored model steps remain 1–14; only steps 4–14 are eligible in the common comparison.

It is not a festival-feature confirmation or another independent episode. Original TimesFM/local/naive forecasts and the interval annex stay immutable. Actual later issuance, common eligibility and the original episode's exact first actual vintage are explicit. No future outcomes or accuracy exist yet. See protocol.json. Automation remains paused; the queue only issues predictions after the current Chronos lane, and later scoring is manual and date-gated.
''')
    print('Registered84newforecasts/66eligible; no inference/actual labels acquired')


def freeze():
    protocol = json.loads((OUT/'protocol.json').read_text())
    deadline(datetime.now(timezone.utc))
    guard_parent()
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    if any((OUT/name).exists() for name in ['started.json', 'predictions.csv', 'freeze.json']):
        raise FileExistsError('Preserve interrupted/completed issuance')
    started = datetime.now(timezone.utc)
    dump(OUT/'started.json', dict(started_utc=started.isoformat(), protocol_sha256=sha(OUT/'protocol.json')))
    try:
        import torch
        from chronos import Chronos2Pipeline
        torch.set_num_threads(2)
        torch.manual_seed(42)
        np.random.seed(42)
        identity = json.loads((ROOT/'results/mechanism_controls_v1/chronos_download.json').read_text())
        for record in identity['files']:
            assert sha(record['path']) == record['sha256']
        weight = next(record for record in identity['files'] if record['name'] == 'model.safetensors')
        model = Chronos2Pipeline.from_pretrained(str(Path(weight['path']).parent), device_map='cpu', local_files_only=True)
        levels = list(model.quantiles)
        source = pd.read_csv(ROOT/protocol['context_snapshot'], index_col=0, parse_dates=True).asfreq('D')
        assert source.index.max() == pd.Timestamp('2026-10-28')
        origin = pd.Timestamp(protocol['first_unseen_origin'])
        data = source.reindex(pd.date_range(source.index.min(), origin+pd.Timedelta(days=13)))
        assert data.loc[origin:].isna().all().all()
        rows, logs, solo = [], [], []
        for mode in ['history', 'calendar']:
            packed = []
            for state in protocol['states']:
                target, covariates = inputs(data, state, origin, mode)
                changed = data.copy()
                changed.loc[origin:, :] = 1e12
                altered_target, altered_covariates = inputs(changed, state, origin, mode)
                assert np.array_equal(target, altered_target)
                assert (covariates is None and altered_covariates is None) or np.array_equal(covariates, altered_covariates)
                record = dict(target=target)
                if covariates is not None:
                    names = [f'dow_{i}' for i in range(7)]+[f'{wave}_{k}' for k in [1, 2, 3] for wave in ['sin', 'cos']]
                    assert covariates.shape == (13, 744)
                    record.update(past_covariates={name: covariates[i, :730] for i, name in enumerate(names)},
                                  future_covariates={name: covariates[i, 730:] for i, name in enumerate(names)})
                packed.append(record)
                logs.append(dict(state=state, mode=mode, origin=str(origin.date()), context_start=str((origin-pd.Timedelta(days=730)).date()),
                    context_end='2026-10-28', target_sha256=hashlib.sha256(target.tobytes()).hexdigest(),
                    covariate_sha256=None if covariates is None else hashlib.sha256(covariates.tobytes()).hexdigest(),
                    feature_names=[] if covariates is None else names,
                    feature_count=0 if covariates is None else 13, future_target_perturbation_invariant=True))
            output = model.predict(packed, prediction_length=14, batch_size=128, context_length=730, cross_learning=False)
            quantiles = [item[0].detach().cpu().numpy().T for item in output]
            for record, result, state in zip(packed, quantiles, protocol['states']):
                individual = model.predict([record], prediction_length=14, batch_size=128, context_length=730, cross_learning=False)[0][0].detach().cpu().numpy().T
                assert result.shape == individual.shape == (14, len(levels))
                np.testing.assert_allclose(result, individual, rtol=2e-4, atol=1e-3)
                solo.append(dict(state=state, mode=mode, maximum_absolute_difference_GWh=float(abs(result-individual).max())))
                assert np.isfinite(result).all()
                tr = source[state].loc['2024-01-02':'2025-12-31']
                scale = float((tr-tr.shift(7)).abs().mean())
                for step in range(1, 15):
                    rows.append(dict(state=state, model='chronos2_'+mode, horizon=step,
                        origin=str(origin.date()), date=str((origin+pd.Timedelta(days=step-1)).date()),
                        prediction=float(result[step-1, levels.index(.5)]), mase_scale=scale,
                        **{f'q_{int(round(level*1000)):03d}': float(value) for level, value in zip(levels, result[step-1])}))
        # Capture issuance AFTER all predictions and checks, never at run start.
        issued = datetime.now(timezone.utc)
        deadline(issued)
        frame = pd.DataFrame(rows)
        frame['issued_utc'] = issued.isoformat()
        frame['prospective_eligible'] = [FIRST <= date.fromisoformat(value) <= LAST and date.fromisoformat(value) > issued.astimezone(INDIA).date() for value in frame.date]
        assert len(frame) == 84 and frame.prospective_eligible.sum() == 66
        assert not frame.duplicated(['state', 'model', 'horizon']).any()
        frame.to_csv(OUT/'predictions.csv', index=False)
        dump(OUT/'inputs.json', logs)
        dump(OUT/'solo_batch_audit.json', solo)
        qcols = sorted(c for c in frame if c.startswith('q_'))
        dump(OUT/'freeze.json', dict(started_utc=started.isoformat(), issued_utc=issued.isoformat(),
            issued_india=issued.astimezone(INDIA).isoformat(), rows=84, eligible_rows=66,
            eligible_start=FIRST.isoformat(), eligible_end=LAST.isoformat(), outcomes_fetched=False,
            predictions_sha256=sha(OUT/'predictions.csv'), inputs_sha256=sha(OUT/'inputs.json'),
            protocol_sha256=sha(OUT/'protocol.json'), weight_sha256=weight['sha256'],
            source_sha256=protocol['context_sha256'], all_quantiles=levels,
            native_crossing_pairs=int((np.diff(frame[qcols].to_numpy(), axis=1) < 0).sum()),
            packages={name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'torch', 'chronos-forecasting']},
            public_commit_status='Pending normal push before firsteligible India day; localfreeze alone is not public evidence',
            scores_status='Pending original first actual vintage after11November; no futureaccuracy available'))
        print('Frozen84newChronos predictions afteractualcompletion;66eligible; publicpush/audit required', flush=True)
    except BaseException:
        (OUT/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'freeze'])
    register() if parser.parse_args().action == 'register' else freeze()
