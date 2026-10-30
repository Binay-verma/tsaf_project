"""Calendar selection and temporal invariants for the wider feature panel."""
import unittest
import pandas as pd
import numpy as np
from breadth_study import ordinary_cases, frames, ARMS, ROOT
from festival_feature_experiment import input_pair
from forecasting import load_data


class BreadthTests(unittest.TestCase):
    def test_monthly_dates_and_complete_leads_without_outcome_selection(self):
        c = ordinary_cases()
        self.assertEqual(len(c), 216)
        for _, g in c.groupby(['state', 'year', 'month']):
            self.assertEqual(set(g.horizon), {1, 7, 14})
            self.assertEqual(g.date.nunique(), 1)
            for r in g.itertuples():
                date, origin = pd.Timestamp(r.date), pd.Timestamp(r.origin)
                self.assertEqual(date.weekday(), r.requested_weekday)
                self.assertEqual((date-origin).days, r.horizon-1)
                self.assertGreaterEqual(origin-pd.Timedelta(days=730), pd.Timestamp('2022-01-01'))
                self.assertLessEqual(origin+pd.Timedelta(days=13), pd.Timestamp('2025-12-31'))
        annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv')
        for r in c.drop_duplicates(['state', 'date']).itertuples():
            holidays = pd.to_datetime(annual[annual.state.eq(r.state) & annual.year.eq(r.year) & annual.in_annual_schedule].date)
            self.assertTrue(all(abs((pd.Timestamp(r.date)-d).days)>3 for d in holidays))

    def test_all_arm_inputs_ignore_future_targets(self):
        data = load_data('latest')['Karnataka']
        origin = pd.Timestamp('2024-03-12')
        changed = data.copy(); changed.loc[origin:] = 9e12
        for arm, frame in frames(data.index, 'Karnataka').items():
            self.assertIn(arm, ARMS)
            self.assertEqual(frame.shape[1], 13 if arm == 'calendar' else 18)
            a, b = input_pair(data, frame, origin)
            c, d = input_pair(changed, frame, origin)
            np.testing.assert_array_equal(a, c)
            np.testing.assert_array_equal(b, d)


if __name__ == '__main__':
    unittest.main()
