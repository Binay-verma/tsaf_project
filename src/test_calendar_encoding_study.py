import unittest
import numpy as np
import pandas as pd
from forecasting import load_data
from calendar_encoding_study import encoded_input,ARMS,feature_names


class CalendarEncodingTests(unittest.TestCase):
    def test_all_encodings_ignore_future_targets_and_use_declared_dimensions(self):
        observed=load_data('latest')['Maharashtra'];origin=pd.Timestamp('2024-03-12')
        changed=observed.copy();changed.loc[origin:]=1e15
        for arm in ARMS:
            target,cov,meta=encoded_input(observed,'Maharashtra',arm,origin)
            b,d,meta2=encoded_input(changed,'Maharashtra',arm,origin)
            np.testing.assert_array_equal(target,b);np.testing.assert_array_equal(cov,d)
            self.assertEqual(meta,meta2)
            self.assertEqual(cov.shape,(len(feature_names(arm)),744))
            self.assertLess(pd.Timestamp(meta['max_encoding_label']),origin)

    def test_target_means_are_from_observed_context_not_filled_labels(self):
        data=load_data('latest')['Delhi'].copy();origin=pd.Timestamp('2024-03-26')
        data.loc['2023-03-08']=np.nan
        _,_,meta=encoded_input(data,'Delhi','te_holiday',origin)
        self.assertEqual(meta['recorded_context_labels'],729)
        self.assertEqual(sum(meta['category_tables'][0]['support'].values()),729)


if __name__=='__main__':unittest.main()
