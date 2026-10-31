"""Independent score audit on temporary synthetic first-vintage fixtures."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

import rolling_execution_v1 as execution
import audit_rolling_scores_v1 as auditor
from rolling_evidence_v1 import dump
from test_rolling_runtime_v1 import fixture_matrix, source_bytes


class RollingScoreAuditChecks(unittest.TestCase):
    def make_scores(self, root):
        base = root/'runtime'
        folder = base/'issuances/00'
        folder.mkdir(parents=True)
        predictions, native, _ = fixture_matrix()
        predictions.to_csv(folder/'predictions.csv', index=False)
        native.to_csv(folder/'native_paths.csv', index=False)
        dump(folder/'freeze.json', {'number': 0})
        now = lambda: datetime(2026, 12, 1, tzinfo=timezone.utc)
        with patch.object(execution, 'BASE', base), patch.object(execution, 'validate_registration'), patch.object(execution, 'first_commit_guard', return_value='synthetic-only'), patch.object(execution, 'clock', now):
            execution.collect(0, now_fn=now, fetch_fn=source_bytes)
            execution.score(0)
        return folder

    def test_all_scores_and_aggregates_pass_then_detect_case_and_group_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = self.make_scores(Path(temp))
            later = datetime(2026, 12, 1, tzinfo=timezone.utc)
            with patch.object(auditor, 'first_commit_guard', return_value='synthetic-only'):
                result = auditor.audit(folder, now=later)
                self.assertEqual(result['scored_cases'], 432)
                path = folder/'scores/cases.csv'
                original = path.read_bytes()
                rows = pd.read_csv(path)
                rows.loc[0, 'MASE'] += .01
                rows.to_csv(path, index=False)
                with self.assertRaises(ValueError):
                    auditor.audit(folder, now=later)
                path.write_bytes(original)
                path = folder/'scores/metrics.csv'
                rows = pd.read_csv(path)
                rows.loc[0, 'MAE_GWh'] += .01
                rows.to_csv(path, index=False)
                with self.assertRaises(ValueError):
                    auditor.audit(folder, now=later)

    def test_clock_prevents_reading_actual_files(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            dump(folder/'freeze.json', {'number': 0})
            with self.assertRaises(ValueError):
                auditor.audit(folder, now=datetime(2026, 10, 31, tzinfo=timezone.utc))


if __name__ == '__main__':
    unittest.main(verbosity=2)
