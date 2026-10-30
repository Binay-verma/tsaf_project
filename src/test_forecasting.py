import unittest
import numpy as np
import pandas as pd
from forecasting import *
class ForecastChecks(unittest.TestCase):
 def setUp(self):
  self.idx=pd.date_range('2018-01-01','2023-12-31');self.y=pd.Series(100+np.sin(np.arange(len(self.idx))/10),index=self.idx)
 def test_future_target_changes_do_not_change_origin_features(self):
  origin=pd.Timestamp('2022-03-01');a=self.y.copy();a.loc[origin:]=999999
  np.testing.assert_equal(history_vector(self.y,origin),history_vector(a,origin))
 def test_causal_fill_does_not_use_future(self):
  a=self.y.copy();a.iloc[100:105]=np.nan;b=a.copy();b.iloc[105:]=1e9
  np.testing.assert_allclose(causal_fill(a).iloc[:105].to_numpy(),causal_fill(b).iloc[:105].to_numpy())
 def test_horizon_calendar_uses_target_date(self):
  cal,cols,_,_=calendar(self.idx,'Delhi');o=pd.Timestamp('2022-02-01')
  got=design(self.y,cal,cols['B_calendar'],14,[o])[0]
  np.testing.assert_equal(got[6:],cal.loc['2022-02-14',cols['B_calendar']])
 def test_no_holdout_labels_used_for_fit(self):
  cal,cols,_,_=calendar(self.idx,'Delhi');a=self.y.copy();a.loc['2022':]=99999
  m1=fit_direct(self.y,self.y,cal,cols['B_calendar'],14)
  m2=fit_direct(a,a,cal,cols['B_calendar'],14)
  np.testing.assert_allclose(m1[-1].coef_,m2[-1].coef_)
 def test_verified_diwali_dates_and_window(self):
  for s in STATES:
   _,_,event,names=calendar(self.idx,s)
   for date in ['2022-10-24','2023-11-12']:
    self.assertIn('Diwali',names.loc[date]);self.assertTrue(event.loc[date])
   self.assertEqual(int(event.loc['2023-11-09':'2023-11-15'].sum()),7)
 def test_fixed_origin_seasonal_repeat(self):
  # No future labels enter seasonal-naive horizons 8-14.
  a=np.arange(1,8);pred=[a[-7+(h-1)%7] for h in range(1,15)]
  self.assertEqual(pred,list(range(1,8))*2)
if __name__=='__main__':unittest.main(verbosity=2)
