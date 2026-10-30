import unittest
import numpy as np
import pandas as pd
from mta_holiday_study import OUT,SERIES,FOUNDATION_ARMS,cases_for,parse_source,frames,build_input


class MtaHolidayTests(unittest.TestCase):
    def test_travel_counts_are_not_percentages_or_unique_people(self):
        rows=[dict(date='2023-01-01T00:00:00',mode='Subway',count='1000000'),dict(date='2023-01-01T00:00:00',mode='Bus',count='500000')]
        d=parse_source(rows);self.assertEqual(d.loc['2023-01-01','MTA_Subway'],1.);self.assertEqual(d.loc['2023-01-01','MTA_Bus'],.5)
        with self.assertRaises(ValueError):parse_source(rows+[rows[0]])

    def test_seven_day_buffer_keeps_all_scored_dates_and_release_order(self):
        for cohort,n in [('event_window',84),('ordinary',42)]:
            c=cases_for(cohort);self.assertEqual(len(c),n)
            for r in c.itertuples():
                self.assertEqual(r.horizon,r.decision_lead+7)
                self.assertEqual((pd.Timestamp(r.date)-pd.Timestamp(r.origin)).days,r.horizon-1)
                self.assertEqual((pd.Timestamp(r.decision_origin)-pd.Timestamp(r.origin)).days,7)
                self.assertGreater(pd.Timestamp(r.decision_origin),pd.Timestamp('2026-08-31'))

    def test_every_representation_preserves_future_target_invariance(self):
        if not OUT.exists():self.skipTest('Protocol not prepared')
        index=pd.date_range('2023-01-01','2026-10-21');y=pd.Series(np.arange(len(index))/1000+1,index=index);origin=pd.Timestamp('2026-09-01');changed=y.copy();changed.loc[origin:]=1e12
        fc=frames(index,'MTA_Subway')
        for arm in FOUNDATION_ARMS:
            a=build_input(y,fc[arm],origin,21);b=build_input(changed,fc[arm],origin,21)
            for j in [0,1]:np.testing.assert_array_equal(a[j],b[j])


if __name__=='__main__':unittest.main()
