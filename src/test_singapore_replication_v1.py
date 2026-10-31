"""Synthetic fixtures only: illustrative test values, never a source of feature dates (MOM files are the only source)."""
import unittest

import numpy as np
import pandas as pd

import singapore_replication_v1 as sg


def holidays():
    rows = [('2024-02-10', 'Chinese New Year'), ('2024-02-11', 'Chinese New Year'), ('2024-04-10', 'Hari Raya Puasa'),
            ('2024-05-22', 'Vesak Day'), ('2024-06-17', 'Hari Raya Haji'), ('2024-10-27', 'Deepavali'),
            ('2024-08-09', 'National Day'), ('2024-12-25', 'Christmas Day'),
            ('2025-01-29', 'Chinese New Year'), ('2025-01-30', 'Chinese New Year'), ('2025-03-31', 'Hari Raya Puasa'),
            ('2025-05-12', 'Vesak Day'), ('2025-06-07', 'Hari Raya Haji'), ('2025-10-20', 'Deepavali')]
    return pd.DataFrame(rows, columns=['Date', 'Holiday'])


class Singapore(unittest.TestCase):
    def setUp(self):
        self.h = sg.parse_mom_holidays(holidays())
        self.a, self.o = sg.family_anchors(self.h)

    def test_anchor_roles_and_in_lieu_rule(self):
        cny = self.a[(self.a.family == 'Chinese_New_Year') & (self.a.year == 2024)]
        self.assertEqual(list(cny.role), ['annual_as_issued_anchor', 'regional_subsidiary', 'regional_subsidiary'])
        self.assertIn(pd.Timestamp('2024-02-12'), set(cny.date))  # 11 Feb 2024 synthetic Sunday -> Monday
        self.assertEqual(set(self.o.name), {'National Day', 'Christmas Day'})

    def test_case_mapping_matches_nyc_buffer(self):
        c = sg.cases_for('event_window', self.a, self.o)
        self.assertEqual(len(c), 10*7*3)
        r = c.iloc[0]
        self.assertEqual(r.horizon, r.decision_lead+7)
        target, origin = pd.Timestamp(r.date), pd.Timestamp(r.origin)
        self.assertEqual((target-origin).days, r.horizon-1)

    def test_ordinary_cases_avoid_every_holiday_window(self):
        c = sg.cases_for('ordinary', self.a, self.o)
        roots = list(self.a.date)+list(self.o.date)
        for d in pd.to_datetime(c.date):
            self.assertTrue(all(abs((d-r).days) > 3 for r in roots))

    def test_placebos_preserve_weekday_and_avoid_holidays(self):
        f = sg.placebos(self.a, list(self.o.date))
        self.assertEqual(len(f), len(self.a))
        self.assertTrue(((f.date-f.original_date).dt.days % 7 == 0).all())
        roots = pd.DatetimeIndex(list(self.a.date)+list(self.o.date))
        for p in f.date:
            self.assertTrue((abs((roots-p).days) > 6).all())

    def test_daily_energy_requires_48_positive_periods(self):
        rows = [(d, p, 5000.) for d in ['2024-01-01', '2024-01-02'] for p in range(1, 49)]
        rows = [r for r in rows if not (r[0] == '2024-01-02' and r[1] == 30)]
        e = sg.daily_energy(pd.DataFrame(rows, columns=['DATE', 'PERIOD', 'MW']))
        self.assertAlmostEqual(e.loc['2024-01-01', 'Singapore'], 48*5000*0.5/1000)
        self.assertTrue(np.isnan(e.loc['2024-01-02', 'Singapore']))
        with self.assertRaises(ValueError):
            sg.daily_energy(pd.DataFrame(rows+[rows[0]], columns=['date', 'period', 'mw']))

    def test_frames_typed_pooled_and_controls(self):
        idx = pd.date_range('2024-01-01', '2025-12-31')
        f = sg.frames(idx, self.a, sg.placebos(self.a, list(self.o.date)))
        self.assertEqual(set(f), set(sg.FOUNDATION_ARMS))
        for arm in sg.ARMS:
            self.assertEqual(f[arm].shape[1], 13 if arm == 'calendar' else 18)
        self.assertTrue((f['pooled_day5']['event_day'] == f['day5'].iloc[:, 13:].max(axis=1)).all())
        self.assertEqual(f['zero5'].iloc[:, 13:].abs().sum().sum(), 0)

    def test_unknown_format_fails_loudly(self):
        with self.assertRaises(ValueError):
            sg.parse_mom_holidays(pd.DataFrame({'when': [], 'what': []}))


if __name__ == '__main__':
    unittest.main()
