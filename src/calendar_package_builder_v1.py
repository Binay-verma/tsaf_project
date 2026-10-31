"""Build and check a rolling-study calendar package from HUMAN-READ primary documents.

This tool never supplies a holiday date. 2024-2025 rows are copied unchanged from the project's
document-aligned ledger and its existing placebos. Rows for 2026 onward must be typed by a person
from a downloaded primary document (entries CSV + documents CSV); the tool only checks them,
derives fixed-rule weekday placebos, hashes everything and validates the result with the
unchanged rolling_evidence_v1.calendar_package().

Usage:
  python src/calendar_package_builder_v1.py template --out DIR
  python src/calendar_package_builder_v1.py build --entries E.csv --documents D.csv --out NEW_DIR [--check-issuance N]
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIGNED = ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv'
PLACEBOS = ROOT/'results/calendar_recenter_recovery_v1/placebo_anchors.csv'
REVIEW = ROOT/'review/used_calendar_v4/all58_named_family_review.csv'
STATES = ['Delhi', 'Karnataka', 'Maharashtra']
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']
HIST_YEARS = (2024, 2025)
ROLES = {'annual_as_issued_anchor', 'national_main', 'regional_subsidiary'}
SHIFT_ORDER = [35, -35, 28, -28, 42, -42]  # fixed before any rolling outcome; first valid shift is used
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
ENTRY_COLS = ['state', 'year', 'family', 'date', 'role', 'name_as_printed', 'weekday_as_printed', 'document', 'secondary_lead_unverified']
DOC_COLS = ['key', 'state', 'year', 'local_pdf', 'primary_document_url', 'issuer', 'order_or_notification_no',
            'notice_date', 'read_by', 'read_utc', 'host_type', 'notes']

# Leads located on secondary hosts (review/india2026_calendar_feasibility_v2). Shown ONLY as hints in the
# template; the 'date' column is left blank and must be filled from the primary document.
LEADS_2026 = {('Delhi', 'Holi'): '2026-03-04', ('Delhi', 'Dussehra'): '2026-10-20', ('Delhi', 'Diwali'): '2026-11-08 (restricted list?)',
              ('Karnataka', 'Ugadi_Gudi_Padwa'): '2026-03-19', ('Karnataka', 'Ganesh_Chaturthi'): '2026-09-14',
              ('Karnataka', 'Dussehra'): '2026-10-21 Vijayadashami (Mahanavami 2026-10-20)', ('Karnataka', 'Diwali'): '2026-11-10 Balipadyami; national 2026-11-08',
              ('Maharashtra', 'Holi'): '2026-03-03', ('Maharashtra', 'Ugadi_Gudi_Padwa'): '2026-03-19', ('Maharashtra', 'Ganesh_Chaturthi'): '2026-09-14',
              ('Maharashtra', 'Dussehra'): '2026-10-20', ('Maharashtra', 'Diwali'): '2026-11-08 Laxmi Pujan; 2026-11-10 Bali Pratipada; 2026-11-11 Bhaubeej (separate notification)'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write(path, data, cols):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)


def state_scope():
    """Families each state carries in the reviewed document-aligned ledger (2024-2025)."""
    scope = {s: set() for s in STATES}
    for r in rows(ALIGNED):
        if int(r['year']) in HIST_YEARS:
            scope[r['state']].add(r['family'])
    return scope


def historical():
    anchors, docs = [], {}
    review = {(r['state'], int(r['year'])): r for r in rows(REVIEW) if int(r['year']) in HIST_YEARS}
    for (state, year), r in review.items():
        key = f'{state}{year}'
        docs[key] = dict(src=ROOT/r['retained_state_pdf'], state=state, year=year,
                         primary_document_url=r['state_annual_source_url'],
                         date_definition='Annual-as-issued named family anchor from the project document-aligned ledger (calendar_semantics_v2); not amendment-certified',
                         notice_utc=f"{r['retained_notice_date']}T00:00:00+05:30")
        if sha(docs[key]['src'])[:12] != r['retained_state_pdf_sha256'][:12]:
            raise ValueError('Retained historical PDF changed: '+key)
    for r in rows(ALIGNED):
        if int(r['year']) in HIST_YEARS:
            anchors.append(dict(state=r['state'], year=int(r['year']), family=r['family'], date=r['date'], role=r['role'],
                                name_as_printed=r.get('label', ''), document=f"{r['state']}{r['year']}"))
    fake = [dict(state=r['state'], year=int(r['year']), family=r['family'], date=r['date'],
                 original_date=r['original_date'], shift_days=int(r['shift_days']))
            for r in rows(PLACEBOS) if int(r['year']) in HIST_YEARS]
    return anchors, fake, docs


def check_new(entries, documents, scope):
    problems, notes = [], []
    dkeys = {}
    for d in documents:
        k = d['key']
        if k in dkeys:
            problems.append(f'duplicate document key {k}')
        dkeys[k] = d
        if not d['read_by'].strip() or not d['read_utc'].strip():
            problems.append(f'{k}: read_by/read_utc must name the person who read the document')
        if not d['primary_document_url'].strip():
            problems.append(f'{k}: primary_document_url required')
        p = Path(d['local_pdf'])
        if not p.is_file() or not p.read_bytes().startswith(b'%PDF-'):
            problems.append(f'{k}: local_pdf missing or not a PDF')
        try:
            dt.date.fromisoformat(d['notice_date'])
        except ValueError:
            problems.append(f'{k}: notice_date must be YYYY-MM-DD')
        if d['host_type'] not in ('government', 'secondary_copy'):
            problems.append(f'{k}: host_type must be government or secondary_copy')
        elif d['host_type'] == 'secondary_copy':
            notes.append(f'{k}: secondary-host copy; record this limitation in the paper')
    years = sorted({int(e['year']) for e in entries})
    for e in entries:
        tag = f"{e['state']} {e['year']} {e['family']} {e['date']}"
        if e['state'] not in STATES or e['family'] not in FAMILIES:
            problems.append(f'{tag}: unknown state/family')
            continue
        if not e['date'].strip():
            problems.append(f'{tag}: date is blank (fill it from the primary document)')
            continue
        try:
            day = dt.date.fromisoformat(e['date'])
        except ValueError:
            problems.append(f'{tag}: date must be YYYY-MM-DD')
            continue
        if day.year != int(e['year']):
            problems.append(f'{tag}: date outside its year')
        if e['weekday_as_printed'].strip().capitalize() != WEEKDAYS[day.weekday()]:
            problems.append(f"{tag}: printed weekday '{e['weekday_as_printed']}' but the date is a {WEEKDAYS[day.weekday()]}")
        if e['role'] not in ROLES:
            problems.append(f'{tag}: role must be one of {sorted(ROLES)}')
        if e['family'] not in scope[e['state']]:
            problems.append(f'{tag}: family outside this state\'s registered scope')
        if e['document'] not in dkeys:
            problems.append(f'{tag}: unknown document key')
        else:
            d = dkeys[e['document']]
            if d['state'] != e['state'] or int(d['year']) != int(e['year']):
                problems.append(f'{tag}: document is for another state/year')
        if not e['name_as_printed'].strip():
            problems.append(f'{tag}: name_as_printed required')
    for y in years:
        for s in STATES:
            for fam in FAMILIES:
                got = [e for e in entries if e['state'] == s and int(e['year']) == y and e['family'] == fam]
                if fam in scope[s] and not got:
                    problems.append(f'{s} {y} {fam}: in scope but no entry')
                main = [e for e in got if e['role'] != 'regional_subsidiary']
                if got and len(main) != 1:
                    problems.append(f'{s} {y} {fam}: needs exactly one non-subsidiary anchor')
        for fam in FAMILIES:
            mains = {e['state']: e['date'] for e in entries if int(e['year']) == y and e['family'] == fam and e['role'] != 'regional_subsidiary' and e['date']}
            if len(set(mains.values())) > 1:
                notes.append(f'{y} {fam}: states name different main dates {mains} (keep as documented; do not harmonise)')
    return problems, notes, years


def placebos(new_anchors, all_anchors):
    out = []
    for a in new_anchors:
        day = dt.date.fromisoformat(a['date'])
        same = [dt.date.fromisoformat(x['date']) for x in all_anchors if x['state'] == a['state']]
        for shift in SHIFT_ORDER:
            p = day+dt.timedelta(days=shift)
            if p.year == a['year'] and all(abs((p-x).days) > 6 for x in same):
                out.append(dict(state=a['state'], year=a['year'], family=a['family'], date=str(p),
                                original_date=a['date'], shift_days=shift))
                break
        else:
            raise ValueError(f"No valid fixed-rule placebo for {a['state']} {a['family']} {a['date']}")
    return out


def build(entries_path, documents_path, out, check_issuance=None):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Use a new package directory; never overwrite a reviewed package')
    scope = state_scope()
    entries = rows(entries_path)
    documents = rows(documents_path)
    problems, notes, years = check_new(entries, documents, scope)
    if any(y in HIST_YEARS for y in years):
        problems.append('2024-2025 rows come from the reviewed ledger; enter only 2026 onward')
    if problems:
        return dict(status='rejected', problems=problems, notes=notes)
    hist_anchors, hist_fake, hist_docs = historical()
    new_anchors = [dict(state=e['state'], year=int(e['year']), family=e['family'], date=e['date'], role=e['role'],
                        name_as_printed=e['name_as_printed'], document=e['document']) for e in entries]
    anchors = hist_anchors+new_anchors
    fake = hist_fake+placebos(new_anchors, anchors)
    out.mkdir(parents=True)
    docs = {}
    for key, d in hist_docs.items():
        shutil.copy2(d['src'], out/(key+'.pdf'))
        docs[key] = dict(file=key+'.pdf', sha256=sha(out/(key+'.pdf')), primary_document_url=d['primary_document_url'],
                         date_definition=d['date_definition'], notice_utc=d['notice_utc'], state=d['state'], year=d['year'])
    for d in documents:
        name = d['key']+'.pdf'
        shutil.copy2(d['local_pdf'], out/name)
        docs[d['key']] = dict(file=name, sha256=sha(out/name), primary_document_url=d['primary_document_url'],
                              date_definition=f"Named family date as printed; read by {d['read_by']} at {d['read_utc']}; host {d['host_type']}; not amendment-certified",
                              notice_utc=f"{d['notice_date']}T00:00:00+05:30", state=d['state'], year=int(d['year']),
                              issuer=d['issuer'], order_or_notification_no=d['order_or_notification_no'])
    coverage = []
    for y in sorted(set(HIST_YEARS) | set(years)):
        for s in STATES:
            key = f'{s}{y}' if y in HIST_YEARS else next(d['key'] for d in documents if d['state'] == s and int(d['year']) == y)
            for fam in FAMILIES:
                coverage.append(dict(state=s, year=y, family=fam, document=key,
                                     status='named_dates' if fam in scope[s] else 'not_in_state_scope'))
    write(out/'anchors.csv', anchors, ['state', 'year', 'family', 'date', 'role', 'name_as_printed', 'document'])
    write(out/'placebos.csv', fake, ['state', 'year', 'family', 'date', 'original_date', 'shift_days'])
    manifest = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), documents=docs, coverage=coverage,
                    anchors='anchors.csv', placebos='placebos.csv', anchors_sha256=sha(out/'anchors.csv'),
                    placebos_sha256=sha(out/'placebos.csv'), builder='src/calendar_package_builder_v1.py',
                    builder_sha256=sha(__file__), notes=notes)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=1)+'\n')
    result = dict(status='built', years=sorted(set(HIST_YEARS) | set(years)), anchors=len(anchors), placebos=len(fake),
                  manifest_sha256=sha(out/'manifest.json'), notes=notes)
    if check_issuance is not None:
        import rolling_evidence_v1 as evidence
        evidence.calendar_package(out/'manifest.json', check_issuance, evidence.planned(check_issuance))
        result['validated_for_issuance'] = check_issuance
    (out/'build_result.json').write_text(json.dumps(result, indent=1)+'\n')
    return result


def template(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    scope = state_scope()
    entries = [dict(state=s, year=2026, family=f, date='', role='', name_as_printed='', weekday_as_printed='',
                    document=f'{s}2026', secondary_lead_unverified=LEADS_2026.get((s, f), ''))
               for s in STATES for f in FAMILIES if f in scope[s]]
    write(out/'entries_2026.csv', entries, ENTRY_COLS)
    docs = [dict(key=f'{s}2026', state=s, year=2026, local_pdf='', primary_document_url='', issuer='', order_or_notification_no='',
                 notice_date='', read_by='', read_utc='', host_type='', notes='') for s in STATES]
    write(out/'documents_2026.csv', docs, DOC_COLS)
    return dict(status='template', files=['entries_2026.csv', 'documents_2026.csv'],
                instruction='Fill every blank from the downloaded primary PDF. The secondary_lead_unverified column is a hint only. Add extra rows for subsidiary anchors (e.g. Diwali second day). Never copy a lead without reading the document.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['template', 'build'])
    ap.add_argument('--entries'); ap.add_argument('--documents'); ap.add_argument('--out', required=True)
    ap.add_argument('--check-issuance', type=int)
    a = ap.parse_args()
    res = template(a.out) if a.action == 'template' else build(a.entries, a.documents, a.out, a.check_issuance)
    print(json.dumps(res, indent=1))
