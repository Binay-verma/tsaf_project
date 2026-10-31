"""Synthetic fixtures only: timing rule v2 relaxes ONLY the global 2024-2027 completeness check."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rolling_evidence_v1 as evidence
import rolling_execution_v1 as v1
import rolling_execution_v2_timing as v2
from test_rolling_runtime_v1 import ledgers


def package(root, years):
    a, f = ledgers()
    a = a[a.year.isin(years)]
    f = f[f.year.isin(years)]
    a.to_csv(root/'anchors.csv', index=False)
    f.to_csv(root/'placebos.csv', index=False)
    documents, coverage = {}, []
    for state in evidence.STATES:
        for year in years:
            key = state+str(year)
            (root/(key+'.pdf')).write_bytes(b'%PDF-1.4 synthetic fixture only')
            documents[key] = dict(file=key+'.pdf', sha256=evidence.sha(root/(key+'.pdf')), primary_document_url='https://example.invalid/synthetic',
                                  date_definition='synthetic fixture, not a holiday', notice_utc='2023-01-01T00:00:00+00:00', state=state, year=year)
            coverage += [dict(state=state, year=year, family=fam, document=key, status='named_dates') for fam in evidence.FAMILIES]
    manifest = dict(documents=documents, coverage=coverage, anchors='anchors.csv', placebos='placebos.csv',
                    anchors_sha256=evidence.sha(root/'anchors.csv'), placebos_sha256=evidence.sha(root/'placebos.csv'))
    evidence.dump(root/'manifest.json', manifest)
    for name in ('rights.txt', 'dates.txt'):
        (root/name).write_text('synthetic evidence fixture')
    activation = dict(status='reviewed_prerequisites', source_units='GWh', source_observation_day_confirmed=True,
                      reviewed_utc='2026-01-01T00:00:00+00:00',
                      source_rights_evidence=dict(file='rights.txt', sha256=evidence.sha(root/'rights.txt')),
                      source_date_evidence=dict(file='dates.txt', sha256=evidence.sha(root/'dates.txt')),
                      calendar_manifest='manifest.json', calendar_manifest_sha256=evidence.sha(root/'manifest.json'))
    evidence.dump(root/'activation.json', activation)
    return activation


class TimingV2(unittest.TestCase):
    def run_case(self, years, number):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            activation = package(root, years)
            now = evidence.planned(number)
            with patch.object(v1, 'ROOT', root), patch.object(v1, 'BASE', root):
                try:
                    v1.prerequisites(number, now)
                    v1_ok = True
                except ValueError:
                    v1_ok = False
                try:
                    v2.prerequisites_v2(number, now)
                    v2_ok = True
                except ValueError:
                    v2_ok = False
                # tampered evidence is still rejected by v2
                (root/'rights.txt').write_text('changed')
                with self.assertRaises(ValueError):
                    v2.prerequisites_v2(number, now)
                # missing activation still rejected
                (root/'activation.json').unlink()
                with self.assertRaises(ValueError):
                    v2.prerequisites_v2(number, now)
            return v1_ok, v2_ok

    def test_first_issuance_needs_only_its_own_years(self):
        self.assertEqual(self.run_case([2024, 2025, 2026], 0), (False, True))

    def test_issuance_with_2027_targets_still_requires_2027(self):
        number = next(n for n in range(52) if evidence.target_contract(evidence.planned(n))['targets']['14'] >= '2027-01-01')
        self.assertEqual(self.run_case([2024, 2025, 2026], number), (False, False))

    def test_full_package_accepted_by_both(self):
        self.assertEqual(self.run_case([2024, 2025, 2026, 2027], 0), (True, True))

    def test_unregistered_or_changed_code_refuses_to_run(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder)/'registration.json'
            fake.write_text(json.dumps(dict(code_sha256={'src/rolling_execution_v2_timing.py': '0'*64})))
            with patch.object(v2, 'REGISTRATION', fake):
                with self.assertRaises(ValueError):
                    v2.run('miss', 0)


if __name__ == '__main__':
    unittest.main()
