"""Synthetic fixtures only: dates below are invented test values, NOT holidays."""
import csv
import datetime as dt
from pathlib import Path
import tempfile
import unittest

import calendar_package_builder_v1 as b

WD = b.WEEKDAYS


def fixture(root, mutate=None):
    pdf = root/'doc.pdf'
    pdf.write_bytes(b'%PDF-1.4 synthetic fixture only, no calendar authority')
    scope = b.state_scope()
    entries = []
    for s in b.STATES:
        for i, f in enumerate(b.FAMILIES):
            if f in scope[s]:
                day = dt.date(2026, 2+2*i, 13)  # invented test dates, spaced >6 days apart
                entries.append(dict(state=s, year=2026, family=f, date=str(day), role='annual_as_issued_anchor',
                                    name_as_printed='synthetic', weekday_as_printed=WD[day.weekday()], document=f'{s}2026',
                                    secondary_lead_unverified=''))
    docs = [dict(key=f'{s}2026', state=s, year=2026, local_pdf=str(pdf), primary_document_url='https://example.invalid/synthetic',
                 issuer='synthetic', order_or_notification_no='0', notice_date='2025-12-01', read_by='test fixture',
                 read_utc='2025-12-02T00:00:00Z', host_type='government', notes='') for s in b.STATES]
    if mutate:
        mutate(entries, docs)
    b.write(root/'e.csv', entries, b.ENTRY_COLS)
    b.write(root/'d.csv', docs, b.DOC_COLS)
    return root/'e.csv', root/'d.csv'


class Builder(unittest.TestCase):
    def run_build(self, mutate=None, issuance=0):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            e, d = fixture(root, mutate)
            return b.build(e, d, root/'pkg', issuance)

    def test_valid_package_passes_rolling_validator_for_first_issuance(self):
        r = self.run_build()
        self.assertEqual(r['status'], 'built')
        self.assertEqual(r['validated_for_issuance'], 0)
        self.assertEqual(r['years'], [2024, 2025, 2026])

    def test_wrong_printed_weekday_is_rejected(self):
        def m(e, d):
            e[0]['weekday_as_printed'] = 'Sunday' if e[0]['weekday_as_printed'] != 'Sunday' else 'Monday'
        self.assertEqual(self.run_build(m)['status'], 'rejected')

    def test_blank_date_missing_reader_scope_and_coverage_are_rejected(self):
        for m in [lambda e, d: e[0].update(date=''),
                  lambda e, d: d[0].update(read_by=''),
                  lambda e, d: e.append(dict(e[0], family='Ganesh_Chaturthi', state='Delhi', document='Delhi2026')),
                  lambda e, d: e.pop()]:
            self.assertEqual(self.run_build(m)['status'], 'rejected')

    def test_historical_rows_cannot_be_reentered(self):
        def m(e, d):
            e[0]['year'] = 2025
        self.assertEqual(self.run_build(m)['status'], 'rejected')

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            e, d = fixture(root)
            (root/'pkg').mkdir()
            with self.assertRaises(FileExistsError):
                b.build(e, d, root/'pkg')

    def test_template_leaves_dates_blank(self):
        with tempfile.TemporaryDirectory() as t:
            b.template(Path(t)/'tpl')
            with open(Path(t)/'tpl'/'entries_2026.csv') as f:
                rows = list(csv.DictReader(f))
            self.assertTrue(rows and all(r['date'] == '' for r in rows))


if __name__ == '__main__':
    unittest.main()
