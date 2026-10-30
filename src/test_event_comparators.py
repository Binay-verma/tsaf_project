import unittest
import numpy as np
import pandas as pd
from event_comparators import encoding_prediction,fit_responses


class ComparatorTests(unittest.TestCase):
    def test_unseen_holiday_falls_back_without_future_labels(self):
        y=pd.Series([10.,20.,30.],index=pd.to_datetime(['2024-01-01','2024-01-08','2024-01-15']))
        value,n,rule=encoding_prediction(y,np.zeros(3,dtype=bool),0,True,'holiday_separate_mean')
        self.assertEqual((value,n,rule),(20.,3,'weekday_fallback'))
        value,n,_=encoding_prediction(y,np.array([False,False,True]),0,True,'holiday_separate_mean')
        self.assertEqual((value,n),(30.,1))

    def test_partial_pooling_unseen_family_uses_pooled_prior(self):
        x=np.array([[1.,0.],[1.,0.],[0.,0.]])
        typed,pooled,partial,_=fit_responses(x,np.array([-2.,-2.,0.]))
        np.testing.assert_allclose(typed,[-2.,0.])
        self.assertEqual(pooled,-2.)
        np.testing.assert_allclose(partial,[-2.,-2.])

    def test_missing_labels_are_not_filled_or_fitted(self):
        x=np.eye(2)
        typed,pooled,partial,good=fit_responses(x,np.array([np.nan,4.]))
        self.assertEqual(good.tolist(),[False,True])
        np.testing.assert_allclose(typed,[0.,4.])


if __name__=='__main__':unittest.main()
