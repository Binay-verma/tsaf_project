import unittest
from datetime import date
import pandas as pd
from neso_replication import periods_for_day,aggregate_daily,cases_for,STATE


class NesoTests(unittest.TestCase):
    def test_dst_and_power_energy_conversion(self):
        for day,n in [(date(2024,3,31),46),(date(2024,10,27),50),(date(2024,4,2),48)]:
            self.assertEqual(periods_for_day(day),n)
            raw=pd.DataFrame({'SETTLEMENT_DATE':[day.isoformat()]*n,'SETTLEMENT_PERIOD':range(1,n+1),'ENGLAND_WALES_DEMAND':[1000]*n,'FORECAST_ACTUAL_INDICATOR':['A']*n})
            d=aggregate_daily(raw);self.assertAlmostEqual(d[STATE].iloc[0],n/2)

    def test_incomplete_and_forecast_rows_are_never_actual_daily_labels(self):
        raw=pd.DataFrame({'SETTLEMENT_DATE':['2026-09-15']*48,'SETTLEMENT_PERIOD':range(1,49),'ENGLAND_WALES_DEMAND':[1000]*48,'FORECAST_ACTUAL_INDICATOR':['A']*47+['F']})
        d=aggregate_daily(raw);self.assertFalse(d.complete.iloc[0]);self.assertTrue(pd.isna(d[STATE].iloc[0]))

    def test_delay_maps_to_effective_model_lead_without_changing_target(self):
        for scenario,lag in [('ideal',0),('lag21',21)]:
            c=cases_for(scenario);self.assertEqual(len(c),48)
            for r in c.itertuples():
                self.assertEqual(r.horizon,r.decision_lead+lag)
                self.assertEqual((pd.Timestamp(r.date)-pd.Timestamp(r.origin)).days,r.horizon-1)
                self.assertEqual((pd.Timestamp(r.decision_origin)-pd.Timestamp(r.origin)).days,lag)


if __name__=='__main__':unittest.main()
