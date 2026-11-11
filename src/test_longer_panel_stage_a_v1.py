"""Date-only checks for the Stage A design (no forecasts, no outcomes)."""
import unittest
import pandas as pd
import longer_panel_stage_a_v1 as s


class StageATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        new, _ = s.new_anchors(allow_unchecked=True)
        cls.anchors = pd.concat([new, pd.read_csv(s.ANCHORS_2225)], ignore_index=True)

    def test_existing_cases_reproduced(self):
        ev = s.event_cases(self.anchors, [2024, 2025]); od = s.ordinary_cases(self.anchors, [2024, 2025])
        self.assertTrue(s.same(ev, s.existing_cases('event_window')))
        self.assertTrue(s.same(od, s.existing_cases('ordinary')))
        self.assertTrue((od.weekday_fallback == 0).all())

    def test_scope_and_conventions(self):
        a = self.anchors
        for st, fams in s.SCOPE.items():
            for y in range(2020, 2026):
                self.assertEqual(set(a[(a.state == st) & (a.year == y)].family), set(fams), (st, y))
        from extended_validation import MAIN
        main = a[a.role.eq('national_main')]
        for r in main.itertuples():
            self.assertEqual(r.date, MAIN[r.year])

    def test_cases_and_placebos(self):
        ev = s.event_cases(self.anchors, s.EVENT_YEARS)
        self.assertTrue((pd.to_datetime(ev.date)-pd.to_datetime(ev.origin)).dt.days.eq(ev.horizon-1).all())
        self.assertFalse(ev.duplicated(s.KEY).any())
        new, _ = s.new_anchors(allow_unchecked=True)
        p = s.placebos(new)
        for r in p.itertuples():
            self.assertIn(abs(r.shift_days), (28, 35, 42)); self.assertEqual(pd.Timestamp(r.date).year, r.year)

    def test_frames_shapes(self):
        idx = pd.date_range('2020-01-01', '2025-12-31')
        fake = pd.concat([s.placebos(s.new_anchors(True)[0]), pd.read_csv(s.PLACEBO_2225)])
        fc = s.frames(idx, 'Maharashtra', self.anchors, fake)
        self.assertEqual(list(fc), s.ARMS)
        self.assertTrue(all(fc[a].shape[1] == 18 for a in s.ARMS if a != 'calendar'))
        self.assertEqual(fc['day5'].loc['2020-11-14', 'Diwali_day'], 1.)

    def test_registered_run_requires_checked_calendar(self):
        t = pd.read_csv(s.ENTRIES, dtype=str).fillna('')
        if (t[t.year.isin(['2020', '2021']) & t.date.ne('')].checked_by == '').any():
            with self.assertRaises(ValueError):
                s.new_anchors(allow_unchecked=False)


if __name__ == '__main__':
    unittest.main()
