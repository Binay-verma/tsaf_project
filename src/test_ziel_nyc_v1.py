"""Invariants for the NYC Ziel comparator arms. Feature checks only; no forecast outcomes."""
import unittest
import pandas as pd
import ziel_nyc_v1 as z
from ziel_replacing_v1 import DOW


class ZielNYCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = pd.date_range('2024-01-01', '2026-12-31')
        cls.fc = z.frames(cls.index)

    def test_arms_and_shapes(self):
        self.assertEqual(list(self.fc), z.ARMS)
        for arm in ['sunday_day', 'replace_pooled', 'replace_typed', 'pooled_day5', 'day5']:
            self.assertEqual(self.fc[arm].shape[1], 18)
        self.assertEqual(list(self.fc['sunday_day'].columns[:13]), list(self.fc['calendar'].columns))

    def test_definitions(self):
        flag = self.fc['pooled_day5']['event_day'].astype(bool)
        anchors = pd.read_csv(z.PARENT/'anchors.csv', parse_dates=['date'])
        self.assertEqual(set(flag[flag].index), set(anchors.date) & set(self.index))
        s = self.fc['sunday_day']
        self.assertTrue((s.loc[flag, 'dow_6'] == 1).all() and (s[DOW].sum(axis=1) == 1).all())
        self.assertTrue(s.loc[~flag].iloc[:, :13].equals(self.fc['calendar'].loc[~flag]))
        for new, ref in [('replace_pooled', 'pooled_day5'), ('replace_typed', 'day5')]:
            self.assertTrue((self.fc[new].loc[flag, DOW] == 0).all().all())
            self.assertTrue(self.fc[new].loc[~flag].equals(self.fc[ref].loc[~flag]))
            other = [c for c in self.fc[ref].columns if c not in DOW]
            self.assertTrue(self.fc[new][other].equals(self.fc[ref][other]))

    def test_reference_design_matches_parent(self):
        import mta_holiday_study as mta
        data = mta.load_source()
        for arm in z.REFERENCE_ARMS:
            for h in [8, 21]:
                a = z.design(data['MTA_Bus'], h, arm); b = mta.design(data['MTA_Bus'], h, arm)
                self.assertTrue(a.equals(b))


if __name__ == '__main__':
    unittest.main()
