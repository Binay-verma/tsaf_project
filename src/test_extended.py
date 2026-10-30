import unittest,json
import numpy as np,pandas as pd
from extended_validation import *
from forecasting import design
class ExtendedChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=load_data('latest')
 def test_fast_design_matches_reference(self):
  y=causal_fill(self.d.Delhi);c,cols,_=features(y.index,'Delhi');o=pd.date_range('2023-01-01',periods=10)
  for h in [1,7,14]:np.testing.assert_allclose(fast_design(y,c,cols['B_calendar'],h,o),design(y,c,cols['B_calendar'],h,o))
 def test_future_perturbation(self):
  y=causal_fill(self.d.Delhi);c,cols,_=features(y.index,'Delhi');o=pd.Timestamp('2025-10-17');changed=y.copy();changed.loc[o:]=1e12
  for h in [1,7,14]:np.testing.assert_equal(fast_design(y,c,cols['D_regional_festival'],h,pd.DatetimeIndex([o])),fast_design(changed,c,cols['D_regional_festival'],h,pd.DatetimeIndex([o])))
 def test_festival_present_in_each_training_year(self):
  for s in STATES:
   c,cols,_=features(self.d.index,s)
   for year in range(2022,2027):
    end=pd.Timestamp(f'{year-1}-12-31');a=c.loc[end-pd.Timedelta(days=729):end,cols['D_regional_festival'][-7:]]
    self.assertGreater(a.to_numpy().sum(),0)
 def test_known_regional_dates(self):
  for s,dates in {'Karnataka':['2024-11-02','2025-10-22'],'Maharashtra':['2024-11-01','2025-10-21'],'Delhi':['2024-10-31','2025-10-20']}.items():
   _,_,e=features(self.d.index,s)
   for d in dates:self.assertTrue(e.loc[d])
 def test_model_weight_identity(self):
  a=json.loads((OUT/'pretraining_audit.json').read_text());self.assertEqual(a['safetensors_sha256'],a['locally_verified_weight_sha256']);self.assertTrue(a['same_weights'])
if __name__=='__main__':unittest.main(verbosity=2)
