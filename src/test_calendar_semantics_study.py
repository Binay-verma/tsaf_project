"""Date provenance and leakage regression tests; no target-error optimisation."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from calendar_semantics_study import ROOT,OUT,frames,encoded_input,ENCODINGS
from breadth_study import frames as legacy
from calendar_encoding_study import encoded_input as legacy_encoded


class SemanticCalendarTests(unittest.TestCase):
    def test_corrected_named_flag_does_not_change_other_state_or_calendar(self):
        if not OUT.exists():self.skipTest('Protocol not prepared')
        index=pd.date_range('2025-09-01','2025-11-01');old=legacy(index,'Karnataka');new=frames(index,'Karnataka')
        self.assertEqual(old['day5'].loc['2025-10-02','Dussehra_day'],1)
        self.assertEqual(new['day5'].loc['2025-10-01','Dussehra_day'],1)
        self.assertEqual(new['day5'].loc['2025-10-02','Dussehra_day'],0)
        np.testing.assert_array_equal(old['calendar'],new['calendar'])
        for state in ['Delhi','Maharashtra']:
            a,b=legacy(index,state),frames(index,state)
            for arm in b:np.testing.assert_array_equal(a[arm].to_numpy(),b[arm].to_numpy())

    def test_context_means_never_see_future_target_values(self):
        if not OUT.exists():self.skipTest('Protocol not prepared')
        index=pd.date_range('2022-01-01','2025-12-31');y=pd.Series(np.arange(len(index))+100.,index=index);origin=pd.Timestamp('2025-10-01')
        changed=y.copy();changed.loc[origin:]=1e12
        for arm in ENCODINGS:
            a=encoded_input(y,'Karnataka',arm,origin);b=encoded_input(changed,'Karnataka',arm,origin)
            for i in [0,1]:np.testing.assert_array_equal(a[i],b[i])
            self.assertEqual(a[2],b[2])
            # Other states have exactly unchanged original input bytes.
            for state in ['Delhi','Maharashtra']:
                a=encoded_input(y,state,arm,origin);b=legacy_encoded(y,state,arm,origin)
                for i in [0,1]:np.testing.assert_array_equal(a[i],b[i])
                self.assertEqual(a[2],b[2])


if __name__=='__main__':unittest.main()
