"""Refresh only the integrated draft's publication status in a new directory.

The frozen v4 builder/auditor and all scientific inputs remain unchanged.
Register before rendering; all nine numeric tables must be byte-identical.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT/'review/integrated_public_update_v1/registration.json'
OLD = ROOT/'manuscript/integrated_review_v4'
OUT = ROOT/'manuscript/integrated_review_v5'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(action):
    if action == 'register':
        if REG.exists() or OUT.exists():
            raise FileExistsError('Preserve prior publication update')
        from score_chronos_competitor import first_commit_guard
        first = first_commit_guard()
        inputs = ['src/update_integrated_public_status.py',
                  'src/build_integrated_review_v4.py', 'src/audit_integrated_review_v4.py',
                  'manuscript/integrated_review_v4/build.json',
                  'manuscript/integrated_review_v4/independent_reporting_audit.json',
                  'manuscript/integrated_review_v4/render_qa.json',
                  'results/prospective_chronos_20261031_v1/public_receipt.json']
        REG.parent.mkdir()
        REG.write_text(json.dumps(dict(registered_utc=datetime.now(timezone.utc).isoformat(),
            scope='Output-directory-only refresh using unchanged frozen v4 builder/auditor after observed Chronos public receipt. No new forecasts/data/method/case/metric/tolerance. All nine exported table CSVs must remain byte-identical; future-status paragraph and build provenance update. Preserve v4.',
            first_forecast_commit=first,
            inputs={name: sha(ROOT/name) for name in inputs}), indent=2)+'\n')
        return
    reg = json.loads(REG.read_text())
    for name, expected in reg['inputs'].items():
        assert sha(ROOT/name) == expected, name
    from score_chronos_competitor import first_commit_guard
    assert first_commit_guard() == reg['first_forecast_commit']
    import build_integrated_review_v4 as builder
    import audit_integrated_review_v4 as auditor
    builder.OUT = OUT
    builder.main()
    auditor.OUT = OUT
    auditor.main()
    tables = json.loads((OUT/'tables.json').read_text())
    for table in tables:
        assert (OUT/table['csv']).read_bytes() == (OLD/table['csv']).read_bytes(), table['name']
    assert len(tables) == 9
    with (OUT/'render.execution.log').open('w') as stream:
        subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-integrated-v5-lo',
            '--headless', '--convert-to', 'pdf', '--outdir', str(OUT),
            str(OUT/'Integrated_Review_Binay_Verma.docx')],
            cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    assert (OUT/'Integrated_Review_Binay_Verma.pdf').is_file()
    (OUT/'publication_update.json').write_text(json.dumps(dict(
        completed_utc=datetime.now(timezone.utc).isoformat(),
        registration_sha256=sha(REG), tables_byte_identical_to_v4=9,
        future_first_commit=reg['first_forecast_commit'],
        status='Numeric audit passes; new PDF all-page visual review pending'), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'run'])
    main(parser.parse_args().action)
