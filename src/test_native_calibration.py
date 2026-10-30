"""Calibration must obey label availability and finite-sample rank rules."""
import unittest
import numpy as np
import pandas as pd
from native_interval_calibration import calibration_rows,adjustment


class CalibrationTests(unittest.TestCase):
    def sample(self):
        dates=pd.date_range('2026-09-15','2026-10-28')
        return pd.DataFrame(dict(state='Delhi',configuration='timesfm_history',horizon=14,
            origin=dates-pd.Timedelta(days=13),date=dates,actual=np.arange(len(dates),dtype=float),q_100=-1.,q_900=2.))

    def test_label_date_not_forecast_origin_controls_availability(self):
        d=self.sample();past=calibration_rows(d,'Delhi','timesfm_history',14,'2026-10-01','expanding_past')
        self.assertEqual(len(past),16);self.assertEqual(past.date.max(),pd.Timestamp('2026-09-30'))
        self.assertTrue((past.date<pd.Timestamp('2026-10-01')).all())

    def test_current_and_future_actuals_cannot_change_calibration(self):
        d=self.sample();other=d.copy();other.loc[other.date.ge('2026-10-01'),'actual']=1e15
        for arm in ['frozen_september','expanding_past']:
            x=calibration_rows(d,'Delhi','timesfm_history',14,'2026-10-01',arm)
            y=calibration_rows(other,'Delhi','timesfm_history',14,'2026-10-01',arm)
            self.assertEqual(adjustment(x),adjustment(y))

    def test_frozen_block_never_adapts_to_october(self):
        d=self.sample();x=calibration_rows(d,'Delhi','timesfm_history',14,'2026-10-28','frozen_september')
        self.assertEqual(len(x),16)
        self.assertEqual(adjustment(x),adjustment(calibration_rows(d,'Delhi','timesfm_history',14,'2026-10-01','frozen_september')))

    def test_order_statistic_has_no_interpolation_and_no_shrinking(self):
        d=pd.DataFrame(dict(actual=np.arange(1.,17.),q_100=np.zeros(16),q_900=np.zeros(16)))
        delta,rank,raw=adjustment(d);self.assertEqual((delta,rank,raw),(14.,14,14.))
        inside=pd.DataFrame(dict(actual=np.zeros(16),q_100=np.full(16,-100.),q_900=np.full(16,100.)))
        self.assertEqual(adjustment(inside)[0],0.)
        with self.assertRaises(ValueError):adjustment(d.iloc[:3])

    def test_insufficient_past_labels_aborts(self):
        with self.assertRaises(ValueError):calibration_rows(self.sample(),'Delhi','timesfm_history',14,'2026-09-30','expanding_past')


if __name__=='__main__':unittest.main()
