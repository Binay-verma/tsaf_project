"""Date-only matching must retain exclusions, counts and temporal bounds."""
import unittest
import pandas as pd
from festival_label_transfer import removed_dates


class LabelTransferTests(unittest.TestCase):
    def test_exact_disjoint_weekday_matches(self):
        dates = pd.date_range('2022-01-01', '2023-12-31')
        anchors = pd.to_datetime(['2022-03-18', '2023-03-08'])
        blocked = {d for a in anchors for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))}
        held, control, pairs = removed_dates(dates, anchors, blocked)
        self.assertEqual(len(held), 14); self.assertEqual(len(control), 14)
        self.assertFalse(held & control); self.assertFalse(control & blocked)
        for row in pairs:
            a, b = pd.Timestamp(row['family_label_date']), pd.Timestamp(row['matched_control_date'])
            self.assertEqual(a.weekday(), b.weekday()); self.assertEqual(a.year, b.year)
            self.assertIn(b, dates)

    def test_missing_labels_and_window_bounds_do_not_silently_change_counts(self):
        dates = pd.date_range('2023-01-01', '2023-12-31').difference(pd.to_datetime(['2023-03-08', '2023-04-05']))
        anchors = pd.to_datetime(['2023-03-08'])
        blocked = set(pd.date_range('2023-03-05', '2023-03-11'))
        held, control, _ = removed_dates(dates, anchors, blocked)
        self.assertEqual(len(held), 6); self.assertEqual(len(control), 6)
        self.assertNotIn(pd.Timestamp('2023-04-05'), control)
        with self.assertRaises(ValueError):
            removed_dates(pd.date_range('2023-03-05', '2023-03-11'), anchors, blocked)


if __name__ == '__main__':
    unittest.main()
