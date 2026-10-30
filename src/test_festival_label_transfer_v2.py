"""Versioned matching preflight and deterministic fallback constraints."""
import unittest
import pandas as pd
from festival_label_transfer_v2 import removed_dates, SHIFTS


class TransferV2Tests(unittest.TestCase):
    def test_fixed_larger_shift_without_response_values(self):
        dates = pd.date_range('2022-08-13', '2024-07-31')
        anchors = pd.to_datetime(['2022-08-31'])
        held = set(pd.date_range('2022-08-28', '2022-09-03'))
        blocked = held | set(pd.date_range('2022-09-22', '2022-10-12'))
        removed, controls, pairs = removed_dates(dates, anchors, blocked)
        self.assertEqual(len(removed), 7); self.assertEqual(len(controls), 7)
        self.assertGreaterEqual(abs(pairs[0]['shift_days']), 49)
        self.assertFalse(controls & blocked)
        for r in pairs:
            self.assertIn(r['shift_days'], SHIFTS)
            a, b = pd.Timestamp(r['family_label_date']), pd.Timestamp(r['matched_control_date'])
            self.assertEqual(a.weekday(), b.weekday()); self.assertEqual(a.year, b.year)

    def test_still_aborts_instead_of_dropping_unmatchable_rows(self):
        dates = pd.date_range('2023-03-05', '2023-03-11')
        with self.assertRaises(ValueError):
            removed_dates(dates, pd.to_datetime(['2023-03-08']), set(dates))


if __name__ == '__main__':
    unittest.main()
