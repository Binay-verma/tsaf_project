"""Nontrivial clock, availability and matched-case failure guards, no actual data."""
from datetime import datetime, timezone
import unittest

import numpy as np
import pandas as pd

from freeze_chronos_competitor import deadline
from score_chronos_competitor import point_cases


class FutureCompetitorTests(unittest.TestCase):
    def fixture(self):
        rows = []
        for model in range(8):
            for state in ['Delhi', 'Karnataka', 'Maharashtra']:
                for step, day in enumerate(pd.date_range('2026-11-01', '2026-11-11'), start=4):
                    rows.append(dict(model='fixture_'+str(model), state=state, date=str(day.date()),
                                     horizon=step, prediction=100., mase_scale=10.))
        frame = pd.DataFrame(rows)
        actual = pd.DataFrame({state: np.full(11, 105.) for state in ['Delhi', 'Karnataka', 'Maharashtra']},
                              index=pd.date_range('2026-11-01', '2026-11-11'))
        return frame.iloc[:198].copy(), frame.iloc[198:].copy(), actual

    def test_india_day_boundary_not_utc_date(self):
        deadline(datetime(2026, 10, 30, 18, 30, tzinfo=timezone.utc))
        deadline(datetime(2026, 10, 31, 18, 29, 59, tzinfo=timezone.utc))
        for now in [datetime(2026, 10, 30, 18, 29, tzinfo=timezone.utc),
                    datetime(2026, 10, 31, 18, 30, tzinfo=timezone.utc), datetime(2026, 10, 31, 12)]:
            with self.assertRaises(ValueError):
                deadline(now)

    def test_early_score_rejected_even_with_synthetic_labels(self):
        parent, new, actual = self.fixture()
        with self.assertRaises(ValueError):
            point_cases(parent, new, actual, datetime(2026, 11, 11, 23, 59, tzinfo=timezone.utc))

    def test_missing_nonpositive_duplicate_labels_rejected(self):
        parent, new, actual = self.fixture()
        now = datetime(2026, 11, 12, tzinfo=timezone.utc)
        for bad in [actual.iloc[:-1], actual*0, pd.concat([actual, actual.iloc[:1]])]:
            with self.assertRaises(ValueError):
                point_cases(parent, new, bad, now)

    def test_duplicate_or_missing_case_not_dropped(self):
        parent, new, actual = self.fixture()
        now = datetime(2026, 11, 12, tzinfo=timezone.utc)
        for bad in [new.iloc[:-1], pd.concat([new, new.iloc[:1]])]:
            with self.assertRaises(ValueError):
                point_cases(parent, bad, actual, now)

    def test_all_eight_methods_same_case_set_and_scalar_losses(self):
        parent, new, actual = self.fixture()
        d = point_cases(parent, new, actual, datetime(2026, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(len(d), 264)
        self.assertTrue(d.MAE_GWh.eq(5).all())
        self.assertTrue(d.MASE.eq(.5).all())
        self.assertEqual(d.groupby('model').size().unique().tolist(), [33])


if __name__ == '__main__':
    unittest.main()
