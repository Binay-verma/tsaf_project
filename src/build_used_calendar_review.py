"""Coverage crosswalk for all used anchors, without claiming amendment review."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'review/used_calendar_v2'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve review packet')
    used = pd.read_csv(ROOT/'results/festival_features_v1/anchors_2022_2025.csv')
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv')
    assert len(used) == 58 and not used.duplicated(['family', 'state', 'date']).any()
    known = pd.read_csv(ROOT/'results/provenance_review_v1/event_issue_evidence.csv')
    pdfs = {('Delhi', y): f'evidence/calendars/DL{y}.pdf' for y in range(2022, 2026)}
    pdfs.update({('Karnataka', y): f'evidence/calendars/KA{y}_NOTIFICATION.pdf' for y in range(2022, 2025)})
    pdfs.update({('Maharashtra', 2022): 'evidence/calendars/MH2022_NOTIFICATION.pdf',
        ('Maharashtra', 2023): 'results/festival_features_v1/evidence/MH2023_official.pdf',
        ('Maharashtra', 2025): 'results/provenance_review_v1/mh2025_bank.pdf'})
    notices = {}
    for r in known.itertuples(index=False):
        notices[r.state, r.year] = (r.issued_date, r.review)
    notices['Karnataka', 2023] = ('2022-11-21', 'Previously visually inspected English notice page6; separate first-publication time unresolved')
    notices['Maharashtra', 2023] = ('2022-12-02', 'Previously extracted English official Gazette page3; separate first-publication time unresolved')
    rows = []
    for i, r in enumerate(used.itertuples(index=False), 1):
        match = annual[annual.state.eq(r.state) & annual.date.eq(r.date)]
        assert len(match) <= 1
        annual_match = len(match) == 1 and bool(match.in_annual_schedule.iloc[0])
        assert annual_match or r.role == 'national_main', (r.state, r.date, r.family)
        doc = pdfs.get((r.state, r.year), '')
        path = ROOT/doc if doc else None
        notice, notice_basis = notices.get((r.state, r.year), ('', 'Not strengthened in the retained notice-date evidence; reviewer to verify'))
        primary = match.primary_document.iloc[0] if len(match) else annual[annual.state.eq(r.state) & annual.year.eq(r.year)].primary_document.iloc[0]
        rows.append(dict(anchor_id=f'USED-{i:03d}', family=r.family, state=r.state, year=r.year, date=r.date,
            feature_role=r.role, definition='Declared shared main anchor; not automatically a state office closure' if r.role == 'national_main' else 'Annual-as-issued named family anchor/subsidiary; not statewide electricity shutdown evidence',
            matches_state_annual_schedule=annual_match, feature_source_url=r.source, state_annual_source_url=primary,
            retained_state_pdf=doc, retained_state_pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else '',
            retained_notice_date=notice, notice_evidence_basis=notice_basis,
            first_historical_publication_time_certified=False, amendment_chain_certified=False,
            reviewer_signoff='not_reviewed', required_review='Verify annual document/page, category, issue/publication timing, relevant amendments and state/event scope. Do not pick dates using electricity errors.',
            unchanged_model_date=True))
    OUT.mkdir(parents=True)
    result = pd.DataFrame(rows)
    result.to_csv(OUT/'all58_used_anchor_review.csv', index=False)
    exceptions = result[~result.matches_state_annual_schedule]
    exceptions.to_csv(OUT/'shared_main_not_state_schedule.csv', index=False)
    summary = dict(status='coverage_crosswalk_complete_not_calendar_certification', anchors=len(result),
        families=result.family.nunique(), state_years=len(result[['state', 'year']].drop_duplicates()),
        annual_schedule_date_matches=int(result.matches_state_annual_schedule.sum()),
        shared_main_without_state_schedule_match=len(exceptions),
        anchors_with_retained_state_pdf=int(result.retained_state_pdf.ne('').sum()),
        anchors_with_previously_strengthened_notice_date=int(result.retained_notice_date.ne('').sum()),
        amendment_chains_certified=0, human_signoffs=0,
        source_ledger_sha256=hashlib.sha256((ROOT/'results/festival_features_v1/anchors_2022_2025.csv').read_bytes()).hexdigest(),
        model_dates_changed=0)
    (OUT/'coverage.json').write_text(json.dumps(summary, indent=2)+'\n')
    (OUT/'README.md').write_text('''# All used festival-feature dates: review packet

This extends the older28-row Diwali-only worksheet to all58anchors used by the2022–2025five-family feature ledger. It is an internal coverage/source crosswalk, not new primary-document certification, a complete amendment search, first-publication reconstruction or independent human review. No model dates, results or source files were changed.

The CSV explicitly distinguishes feature-source URLs from state annual documents. A declared shared main Diwali anchor can differ from the state's office holiday; such rows are exported separately. In particular, Maharashtra's shared main anchors must not be relabelled as its state Lakshmi Pujan dates. Annual schedule agreement does not establish identical event meaning or a statewide electricity shutdown.

Retained notice dates are inherited only from previously strengthened evidence. Empty fields are unresolved, not evidence that no notice/amendment exists. Known notice dates are not automatically first public availability times. Retained PDFs can be government-authored copies on mirrors; the source ledger preserves host identity.

An independent regional reviewer should fill document page/category/amendment and sign-off information after checking evidence. All58amendment certifications and human sign-offs remain unfilled. Binay Verma is author/requester, not an invented independent reviewer. Older source-calendar artifacts and worksheets remain unchanged.
''')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
