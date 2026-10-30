"""Prospective interval scoring must reject early/partial/duplicate labels."""
from datetime import datetime,timezone
import unittest
import pandas as pd
from score_interval_annex import metrics_frame


class IntervalAnnexTests(unittest.TestCase):
    def fixture(self):
        p=pd.DataFrame(dict(state=['Delhi','Delhi'],date=['2026-11-11','2026-11-11'],prospective_eligible=[True,True],
            lower=[90.,80.],upper=[110.,120.],native_median=[100.,100.],mase_scale=[10.,10.]))
        actuals=pd.DataFrame({'Delhi':[100.]},index=pd.to_datetime(['2026-11-11']))
        return p,actuals

    def test_early_score_rejected_even_with_synthetic_labels(self):
        p,a=self.fixture()
        with self.assertRaises(ValueError):metrics_frame(p,a,datetime(2026,11,11,tzinfo=timezone.utc))

    def test_missing_duplicate_or_nonpositive_labels_abort(self):
        p,a=self.fixture();now=datetime(2026,11,12,tzinfo=timezone.utc)
        for bad in [a.iloc[:0],pd.concat([a,a]),a*0]:
            with self.assertRaises(ValueError):metrics_frame(p,bad,now)

    def test_wider_interval_cost_is_visible_with_same_coverage(self):
        p,a=self.fixture();d=metrics_frame(p,a,datetime(2026,11,12,tzinfo=timezone.utc))
        self.assertTrue(d.coverage80.eq(1).all())
        self.assertGreater(d.scaled_WIS80_median.iloc[1],d.scaled_WIS80_median.iloc[0])


if __name__=='__main__':unittest.main()
