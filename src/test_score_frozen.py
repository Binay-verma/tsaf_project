import datetime as dt
import unittest
import numpy as np
import pandas as pd
from score_frozen import score_frame


class ProspectiveScoringChecks(unittest.TestCase):
    def setUp(self):
        # Synthetic in-memory fixtures; never saved as real future outcomes.
        self.predictions = pd.DataFrame({'date': ['2026-10-30', '2026-11-11'],
            'prospective_eligible': [False, True], 'model': ['timesfm3_history']*2,
            'state': ['Delhi']*2, 'prediction': [100., 100.], 'mase_scale': [10., 10.],
            **{f'q{i:02d}': [90.+2*i]*2 for i in range(1, 10)}})
        self.actuals = pd.DataFrame({'Delhi': [999999., 101.]},
                                    index=pd.to_datetime(['2026-10-30', '2026-11-11']))

    def test_future_scores_are_blocked(self):
        with self.assertRaises(ValueError):
            score_frame(self.predictions, self.actuals, dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc))

    def test_issue_day_excluded_and_exact_future_cases_scored(self):
        d, states, macro, _ = score_frame(self.predictions, self.actuals,
                                         dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc))
        self.assertEqual(len(d), 1)
        self.assertAlmostEqual(macro.MASE.iloc[0], .1)

    def test_missing_outcomes_cannot_be_imputed_or_dropped(self):
        a = self.actuals.copy()
        a.loc['2026-11-11', 'Delhi'] = np.nan
        with self.assertRaises(ValueError):
            score_frame(self.predictions, a, dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc))


if __name__ == '__main__':
    unittest.main(verbosity=2)
