import unittest
import pandas as pd
from calendar_recenter_study import ROOT,OUT,aligned_frames,old_frames


class RecenterTests(unittest.TestCase):
    def test_complete_new_window_and_matched_leads(self):
        if not OUT.exists():self.skipTest('New protocol not prepared')
        c=pd.read_csv(OUT/'event_cases_recentered.csv');g=c[c.state.eq('Karnataka')&c.year.eq(2025)&c.family.eq('Dussehra')]
        self.assertEqual(len(c),528);self.assertEqual(len(g),21)
        self.assertEqual(set(g.date),set(str(d.date()) for d in pd.date_range('2025-09-28','2025-10-04')))
        self.assertTrue(((pd.to_datetime(g.date)-pd.to_datetime(g.origin)).dt.days==g.horizon-1).all())

    def test_placebo_realigns_weekday_without_changing_channel_keys(self):
        if not OUT.exists():self.skipTest('New protocol not prepared')
        p=pd.read_csv(OUT/'placebo_anchors.csv');r=p[p.state.eq('Karnataka')&p.year.eq(2025)&p.family.eq('Dussehra')].iloc[0]
        self.assertEqual(r.date,'2025-11-05');self.assertEqual(pd.Timestamp(r.date).weekday(),pd.Timestamp('2025-10-01').weekday())
        index=pd.date_range('2025-01-01','2025-12-31');old=old_frames(index,'Karnataka');new=aligned_frames(index,'Karnataka')
        for arm in old:self.assertEqual(list(old[arm]),list(new[arm]))


if __name__=='__main__':unittest.main()
