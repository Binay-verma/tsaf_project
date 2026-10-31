"""Synthetic temporary fixtures, never research forecasts or future actuals."""
from datetime import datetime, timedelta, timezone
import gzip
import json
from functools import lru_cache
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

import rolling_evidence_v1 as evidence
import rolling_execution_v1 as execution
from rolling_models_v1 import forecast, foundation_input, direct_arrays, fixed_direct


def synthetic_source():
    index = pd.date_range('2023-01-01', '2027-01-31')
    t = np.arange(len(index))
    return pd.DataFrame({state: 100+j*20+.02*t+8*np.sin(2*np.pi*t/7) for j, state in enumerate(evidence.STATES)}, index=index)


def ledgers():
    anchors, fake = [], []
    for state in evidence.STATES:
        for year in range(2024, 2028):
            for family, month in zip(evidence.FAMILIES, [1, 3, 5, 7, 9]):
                day = pd.Timestamp(year, month, 15)
                anchors.append(dict(state=state, year=year, family=family, date=str(day.date()), document=state+str(year)))
                fake.append(dict(state=state, year=year, family=family, date=str((day+pd.Timedelta(days=28)).date()), original_date=str(day.date()), shift_days=28))
    return pd.DataFrame(anchors), pd.DataFrame(fake)


class DummyDirect:
    def fit(self, x, y):
        self.value = y.mean()
        return self

    def predict(self, x):
        return np.repeat(self.value, len(x))


def dummy_provider(name):
    levels = [.01, .05]+[k/20 for k in range(2, 19)]+[.95, .99] if name == 'chronos' else [k/10 for k in range(1, 10)]

    def predict(inputs):
        result = []
        for target, cov in inputs:
            q = np.repeat((target[-1]+(np.array(levels)-.5)*8)[None, :], 16, axis=0)
            point = q[:, levels.index(.5)]+(.3 if name == 'timesfm' else 0)
            result.append((point, q))
        return result
    return predict, levels, 'synthetic-fixture-not-real-weights'


@lru_cache(maxsize=1)
def fixture_matrix():
    a, f = ledgers()
    return forecast(synthetic_source(), a, f, 0,
        direct_factory=lambda name: DummyDirect(), provider_factory=dummy_provider,
        sarimax_factory=lambda y, past, future: np.repeat(y[-1], 16))


def source_bytes(missing=False):
    source = synthetic_source().copy()
    if missing:
        source.loc['2026-11-17', 'Delhi'] = np.nan
    frame = source.rename(columns={state: state+': EnergyMet' for state in evidence.STATES})
    frame.insert(0, 'yyyymmdd', frame.index.strftime('%Y%m%d'))
    raw = frame.to_csv(index=False).encode()
    meta = json.dumps({'fields': [{'name': state+': EnergyMet', 'units': 'GWh'} for state in evidence.STATES]}).encode()
    return raw, meta


class RollingRuntimeChecks(unittest.TestCase):
    def test_early_issue_and_collection_make_no_network_request(self):
        network = Mock(side_effect=AssertionError('Must not fetch'))
        before = lambda: datetime(2026, 10, 31, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            execution.issue(0, now_fn=before, fetch_fn=network)
        with self.assertRaises(ValueError):
            execution.collect(0, now_fn=before, fetch_fn=network)
        network.assert_not_called()

    def test_clock_boundaries_and_year_rollover(self):
        start = evidence.planned(0)
        evidence.issuance_gate(0, start)
        evidence.issuance_gate(0, start+timedelta(minutes=59))
        for value in [start-timedelta(microseconds=1), start+timedelta(minutes=59, microseconds=1), start.replace(tzinfo=None)]:
            with self.assertRaises(ValueError):
                evidence.issuance_gate(0, value)
        with self.assertRaises(ValueError):
            evidence.collection_gate(0, datetime(2026, 11, 30, 23, 59, tzinfo=timezone.utc))
        evidence.collection_gate(0, datetime(2026, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(evidence.target_contract(evidence.planned(6))['targets']['14'], '2027-01-11')
        a = evidence.frozen_scales(synthetic_source(), 6)
        source = synthetic_source()
        source.loc['2026-01-01':] *= 10
        self.assertEqual(a, evidence.frozen_scales(source, 6))

    def test_source_units_duplicates_compression_and_unavailable_labels(self):
        meta = json.dumps({'fields': [{'name': state+': EnergyMet', 'units': 'GWh'} for state in evidence.STATES]}).encode()
        data = pd.DataFrame({'yyyymmdd': [20260101, 20260102], **{state+': EnergyMet': [100, -1] for state in evidence.STATES}}).to_csv(index=False).encode()
        source = evidence.parse_source(gzip.compress(data), gzip.compress(meta))
        self.assertTrue(source.iloc[1].isna().all())
        with self.assertRaises(ValueError):
            evidence.parse_source(data, meta.replace(b'GWh', b'MW'))
        with self.assertRaises(ValueError):
            evidence.parse_source(data.replace(b'20260102', b'20260101'), meta)

    def test_all_arms_inputs_ignore_unavailable_and_future_targets(self):
        source = synthetic_source()
        altered = source.copy()
        altered.loc['2026-11-15':] = 1e12
        a, f = ledgers()
        for arm in evidence.ARMS:
            with self.subTest(arm=arm):
                left = foundation_input(evidence.available_history(source, 0), 'Delhi', arm, a, f, 0)
                right = foundation_input(evidence.available_history(altered, 0), 'Delhi', arm, a, f, 0)
                for x, y in zip(left, right):
                    np.testing.assert_array_equal(x, y)
                self.assertEqual(left[1].shape, (13 if arm == 'calendar' else 18, 746))
        x, y, q, log = direct_arrays(evidence.available_history(source, 0), 'Delhi', 16, 'day5', a, f, 0)
        xx, yy, qq, _ = direct_arrays(evidence.available_history(altered, 0), 'Delhi', 16, 'day5', a, f, 0)
        for left, right in [(x, xx), (y, yy), (q, qq)]:
            np.testing.assert_array_equal(left, right)
        self.assertLessEqual(log['training_target_max'], '2026-11-14')
        self.assertEqual(x.shape[1], 45)  # Rich history27 + calendar13 + event5.

    def test_calendar_contract_and_tampered_documents(self):
        a, f = ledgers()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a.to_csv(root/'anchors.csv', index=False)
            f.to_csv(root/'placebos.csv', index=False)
            documents, coverage = {}, []
            for state in evidence.STATES:
                for year in range(2024, 2028):
                    key = state+str(year)
                    file = root/(key+'.pdf')
                    file.write_bytes(b'%PDF-1.4 synthetic fixture only, no calendar authority')
                    documents[key] = dict(file=file.name, sha256=evidence.sha(file), primary_document_url='https://example.invalid/synthetic',
                        date_definition='synthetic fixture, not an actual holiday', notice_utc='2023-01-01T00:00:00+00:00', state=state, year=year)
                    coverage += [dict(state=state, year=year, family=family, document=key, status='named_dates') for family in evidence.FAMILIES]
            manifest = dict(documents=documents, coverage=coverage, anchors='anchors.csv', placebos='placebos.csv', anchors_sha256=evidence.sha(root/'anchors.csv'), placebos_sha256=evidence.sha(root/'placebos.csv'))
            path = root/'manifest.json'
            evidence.dump(path, manifest)
            evidence.calendar_package(path, 0, evidence.planned(0))
            manifest['coverage'] = [r for r in coverage if not (r['state'] == 'Delhi' and r['year'] == 2026 and r['family'] == 'Holi')]
            evidence.dump(path, manifest)
            with self.assertRaises(ValueError):
                evidence.calendar_package(path, 0, evidence.planned(0))
            manifest['coverage'] = coverage
            evidence.dump(path, manifest)
            (root/'Delhi2026.pdf').write_bytes(b'%PDF-1.4 changed')
            with self.assertRaises(ValueError):
                evidence.calendar_package(path, 0, evidence.planned(0))
        with self.assertRaises(ValueError):
            evidence.within('/tmp/calendar-package', '../private-file')

    def test_complete_six_model_fixture_and_native_scoring(self):
        predictions, native, logs = fixture_matrix()
        evidence.case_matrix(predictions.to_dict('records'), 0)
        self.assertEqual(len(predictions), 432)
        self.assertEqual(len(native), 768)
        self.assertEqual(len(logs['inputs']), 48)
        self.assertEqual(len(logs['solo_batch_audit']), 48)
        times = predictions[predictions.model.eq('timesfm')]
        np.testing.assert_allclose(times.prediction-times.q_500, .3)
        actuals = synthetic_source()
        result = evidence.score_cases(predictions, actuals, 0)
        self.assertEqual(len(result), 432)
        self.assertEqual(len(evidence.metrics(result).query('scope == "all"')), 144)
        with self.assertRaises(ValueError):
            evidence.case_matrix(predictions.iloc[:-1].to_dict('records'), 0)
        missing = actuals.copy()
        missing.loc['2026-11-17', 'Delhi'] = np.nan
        with self.assertRaises(ValueError):
            evidence.score_cases(predictions, missing, 0)
        crossing = predictions.copy()
        mask = crossing.model.eq('chronos')&crossing.arm.eq('calendar')&crossing.state.eq('Delhi')&crossing.decision_lead.eq(1)
        crossing.loc[mask, 'q_100'] = crossing.loc[mask, 'q_900']+1
        invalid = evidence.score_cases(crossing, actuals, 0)
        summary = evidence.metrics(invalid)
        cell = summary.query('scope == "all" and model == "chronos" and arm == "calendar" and decision_lead == 1')
        self.assertTrue(cell.coverage80.isna().all())
        self.assertTrue(np.isfinite(cell.scaled_pinball).all())

    def test_first_complete_vintage_is_sealed_scored_once_and_never_refetched(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)/'runtime'
            folder = base/'issuances/00'
            folder.mkdir(parents=True)
            fixture_matrix()[0].to_csv(folder/'predictions.csv', index=False)
            evidence.dump(folder/'freeze.json', {'number': 0})
            network = Mock(side_effect=[source_bytes(missing=True), source_bytes()])
            later = lambda: datetime(2026, 12, 1, tzinfo=timezone.utc)
            with patch.object(execution, 'BASE', base), patch.object(execution, 'validate_registration'), patch.object(execution, 'first_commit_guard', return_value='synthetic-fixture-only'), patch.object(execution, 'clock', later):
                self.assertTrue(execution.collect(0, now_fn=later, fetch_fn=network).startswith('PENDING'))
                self.assertFalse((folder/'actuals').exists())
                self.assertTrue(execution.collect(0, now_fn=later, fetch_fn=network).startswith('FIRST_COMPLETE'))
                self.assertTrue(execution.collect(0, now_fn=later, fetch_fn=network).startswith('ALREADY_COMPLETE'))
                self.assertEqual(network.call_count, 2)
                execution.score(0)
                self.assertEqual(len(pd.read_csv(folder/'scores/cases.csv')), 432)
                with self.assertRaises(FileExistsError):
                    execution.score(0)
                with (folder/'actuals/actuals.csv').open('ab') as stream:
                    stream.write(b'changed')
                with self.assertRaises(ValueError):
                    execution.collect(0, now_fn=later, fetch_fn=network)
                self.assertEqual(network.call_count, 2)

    def test_complete_attempt_without_seal_blocks_another_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            attempt = base/'issuances/00/actual_attempts/0000'
            attempt.mkdir(parents=True)
            evidence.dump(attempt/'collection.json', {'complete': True})
            network = Mock(side_effect=AssertionError('Must not refetch'))
            with patch.object(execution, 'BASE', base), patch.object(execution, 'validate_registration'), patch.object(execution, 'first_commit_guard'):
                with self.assertRaises(ValueError):
                    execution.collect(0, now_fn=lambda: datetime(2026, 12, 1, tzinfo=timezone.utc), fetch_fn=network)
            network.assert_not_called()

    def test_late_completion_preserves_failure_without_issuing_predictions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root/'runtime'
            base.mkdir()
            evidence.dump(base/'registration.json', {'inputs': {}})
            a, f = ledgers()
            a.to_csv(root/'anchors.csv', index=False)
            f.to_csv(root/'fake.csv', index=False)
            evidence.dump(root/'calendar.json', {})
            (root/'source-review.txt').write_text('Synthetic fixture only, no real source approval')
            activation = {key: {'file': 'source-review.txt'} for key in ['source_rights_evidence', 'source_date_evidence']}
            package = dict(anchors='anchors.csv', placebos='fake.csv', documents={})
            start = evidence.planned(0)+timedelta(minutes=10)
            times = iter([start]*4+[evidence.planned(0)+timedelta(minutes=60)])
            with patch.object(execution, 'ROOT', root), patch.object(execution, 'BASE', base), patch.object(execution, 'validate_registration'), patch.object(execution, 'prerequisites', return_value=(activation, root/'calendar.json', package, a, f)):
                with self.assertRaises(ValueError):
                    execution.issue(0, now_fn=lambda: next(times), fetch_fn=source_bytes,
                        forecast_fn=lambda *args, **kw: fixture_matrix())
            self.assertTrue((base/'issuances/00/failure.txt').exists())
            self.assertFalse((base/'issuances/00/predictions.csv').exists())
            self.assertFalse((base/'issuances/00/freeze.json').exists())

    def test_first_commit_blob_runtime_and_receipt_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/'issue'
            folder.mkdir()
            (root/'runtime.py').write_text('synthetic fixture source')
            (folder/'predictions.csv').write_text('synthetic fixture predictions')
            evidence.dump(folder/'runtime_registration.json', {'inputs': {'runtime.py': evidence.sha(root/'runtime.py')}})
            start = evidence.planned(0)
            evidence.dump(folder/'freeze.json', dict(number=0, issued_utc=(start+timedelta(minutes=10)).isoformat(),
                files={name: evidence.sha(folder/name) for name in ['predictions.csv', 'runtime_registration.json']}))
            evidence.dump(folder/'public_receipt.json', dict(first_forecast_commit='fixture-commit', observed_utc=(start+timedelta(minutes=30)).isoformat(), predictions_sha256=evidence.sha(folder/'predictions.csv')))
            blobs = {str(path.relative_to(root)): path.read_bytes() for path in folder.iterdir() if path.is_file()}

            def git(command, **kwargs):
                if command[1] == 'rev-list':
                    return 'fixture-commit\n'
                if '-s' in command:
                    return (start+timedelta(minutes=20)).isoformat()
                return blobs[command[-1].split(':', 1)[1]]
            with patch.object(evidence, 'ROOT', root), patch.object(evidence.subprocess, 'check_output', side_effect=git):
                self.assertEqual(evidence.first_commit_guard(folder), 'fixture-commit')
                (root/'runtime.py').write_text('changed')
                with self.assertRaises(ValueError):
                    evidence.first_commit_guard(folder)
                (root/'runtime.py').write_text('synthetic fixture source')
                original = blobs['issue/predictions.csv']
                blobs['issue/predictions.csv'] = b'changed first commit blob'
                with self.assertRaises(ValueError):
                    evidence.first_commit_guard(folder)
                blobs['issue/predictions.csv'] = original
                receipt = json.loads((folder/'public_receipt.json').read_text())
                receipt['observed_utc'] = (start+timedelta(minutes=60)).isoformat()
                evidence.dump(folder/'public_receipt.json', receipt)
                with self.assertRaises(ValueError):
                    evidence.first_commit_guard(folder)

    def test_failed_direct_fit_is_recorded_before_error(self):
        class Failed(DummyDirect):
            def fit(self, x, y):
                raise RuntimeError('synthetic deliberate failure')
        records = []
        a, f = ledgers()
        with self.assertRaises(RuntimeError):
            forecast(synthetic_source(), a, f, 0, progress=lambda value: records.append(json.loads(json.dumps(value))),
                direct_factory=lambda name: Failed(), provider_factory=dummy_provider)
        self.assertEqual(records[-1]['fit_log'][-1]['status'], 'failed')

    def test_real_local_fixed_parameters_and_past_only_design(self):
        source = evidence.available_history(synthetic_source(), 0)
        a, f = ledgers()
        x, y, query, _ = direct_arrays(source, 'Delhi', 3, 'pooled_day5', a, f, 0)
        for name in evidence.MODELS[:3]:
            model = fixed_direct(name)
            xx = x.astype(np.float32) if name.startswith('tree_') else x
            qq = query.astype(np.float32) if name.startswith('tree_') else query
            self.assertTrue(np.isfinite(model.fit(xx, y).predict(qq)).all())
            if name.startswith('tree_'):
                self.assertEqual(model.get_params()['min_child_samples'], 20 if name == 'tree_leaf20_fixed' else 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
