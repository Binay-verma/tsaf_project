import unittest
from datetime import datetime,timezone,timedelta
from rolling_confirmation_plan import target_contract,validate_manifest,schedule


class RollingPlanTests(unittest.TestCase):
    def test_lag_bridge_targets_are_after_decision(self):
        c=target_contract(datetime(2026,11,16,9,tzinfo=timezone.utc))
        self.assertEqual(c['context_last_date'],'2026-11-14')
        self.assertEqual(c['model_origin'],'2026-11-15')
        self.assertEqual(c['targets'],{'1':'2026-11-17','7':'2026-11-23','14':'2026-11-30'})
        self.assertEqual(c['model_steps'],{'1':3,'7':9,'14':16})

    def test_late_issuance_and_missing_calendar_are_rejected(self):
        planned=schedule()[0]
        with self.assertRaisesRegex(ValueError,'Late/early'):
            validate_manifest({'issued_utc':(planned+timedelta(hours=1)).isoformat()},planned)
        m=dict(issued_utc=planned.isoformat(),contract=target_contract(planned),units='GWh',workflow_enabled=False,calendar_complete=False)
        with self.assertRaisesRegex(ValueError,'Missing dated ledger'):validate_manifest(m,planned)

    def test_schedule_is_future_weekly_without_old_period_overlap(self):
        dates=schedule()
        self.assertEqual(len(dates),52)
        self.assertTrue(all((b-a).days==7 for a,b in zip(dates,dates[1:])))
        self.assertEqual(dates[-1].date().isoformat(),'2027-11-08')


if __name__=='__main__':unittest.main()
