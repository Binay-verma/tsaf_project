"""Summarize downloaded primary-provider probes without redistributing source data."""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
from festival_feature_design import ROOT,dump

OUT=ROOT/'review/independent_sources_v1'


def main(cache):
    if OUT.exists():raise FileExistsError('Preserve source audit')
    needed=['mta_metadata.json','mta_historical_retry.json','mta_historical_retry_retrieval.json',
        'mta_open_data_retrieval.json','mta_terms_retrieval.json','elexon_week.json',
        'elexon_week_retrieval.json','probe_1.txt']
    for name in needed:assert (cache/name).is_file(),name
    m=json.loads((cache/'mta_metadata.json').read_text())
    data=json.loads((cache/'mta_historical_retry.json').read_text())
    dates=[r['date'][:10] for r in data]
    assert len(dates)==len(set(dates)) and min(dates)=='2022-01-01' and max(dates)=='2025-01-09'
    assert all('2022-01-01'<=d<'2026-01-01' for d in dates)
    metrics={}
    for field in ['subways_total_estimated_ridership','buses_total_estimated_ridersip']:
        valid=[r['date'][:10] for r in data if field in r and float(r[field])>0]
        metrics[field]=dict(positive_records=len(valid),by_year=dict(Counter(d[:4] for d in valid)))
    e=json.loads((cache/'elexon_week.json').read_text())['data']
    starts=[datetime.fromisoformat(r['startTime'].replace('Z','+00:00')) for r in e]
    ordered=sorted(starts)
    assert len(starts)==len(set(starts))==336
    assert all(b-a==timedelta(minutes=30) for a,b in zip(ordered,ordered[1:]))
    assert all(r['quantity']>0 and r['publishTime'] for r in e)
    settlement=dict(sorted(Counter(r['settlementDate'] for r in e).items()))
    OUT.mkdir()
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='Audit complete; independent model replication not performed and rights/coverage gates remain.',
        source_files={n:dict(bytes=(cache/n).stat().st_size,sha256=hashlib.sha256((cache/n).read_bytes()).hexdigest()) for n in needed},
        mta=dict(provider='Metropolitan Transportation Authority via NYS Open Data',
            url='https://data.ny.gov/resource/vxuj-8kew.json',metadata_url='https://data.ny.gov/api/views/vxuj-8kew.json',
            lineage='Independent of Indian GRID/POSOCO series; cross-domain ridership, not electricity supply.',
            title=m['name'],deprecated=True,source_license_id=m.get('licenseId'),requested_years=[2022,2023,2024,2025],
            returned_rows=len(data),first_date=min(dates),last_date=max(dates),fields=metrics,
            rights='NYS view metadata has no licenseId. MTA open-data page welcomes third-party analytical use, but general website terms are restrictive. Dataset-specific portal/research redistribution terms not established; do not infer a grant or redistribute raw probe.',
            next='Use a separately audited successor dataset for2025; do not silently splice this deprecated view.2024has366records but is historical/model-exposure unresolved. The closest calendar-encoding paper already uses MTA, so it is not a new benchmark.',
            retrieval=json.loads((cache/'mta_historical_retry_retrieval.json').read_text())),
        elexon=dict(provider='Elexon Insights API',url='https://data.elexon.co.uk/bmrs/api/v1/demand/actual/total',
            specification_url='https://data.elexon.co.uk/swagger/v1/swagger.json',
            lineage='GB actual total load ATL/B0610, independent of Indian GRID/POSOCO; different geography/measurement definition.',
            records=336,unique_half_hour_intervals=336,utc_grid_complete=True,settlement_counts=settlement,
            warning='UTC range and local settlement date differ:30March2025has46periods; query also includes2periods labelled3April. Daily local aggregation must validate full46/48/50period coverage and exact requested dates.',
            units='API schema calls the field quantity without an explicit unit. ATL convention alone is insufficient for this audit: verify authoritativeMWdefinition and period-average interpretation before GWhconversion.',
            vintages='publishTime retained in raw probe; API reflects current published values, not reconstructed historical first-release vintages. Dataset revision fields require further audit.',
            rights='Official Elexon licence/operational pages returned403; no bypass or redistribution-rights inference. Raw probe remains outsideGit.',
            invalid_probe='Generic /datasets/ITSDO ignored an unsupported settlementDate/from query and returned current30October2026row. Rejected as historical data; documented endpoint and explicit returned-date guards are necessary.',
            retrieval=json.loads((cache/'elexon_week_retrieval.json').read_text())),
        transport_failures=['requests module unavailable; used standard-library urllib',
            'Initial projected MTA request503; one bounded retry without projection succeeded',
            'MTA guessed license and NY guessed terms URLs404; actual linked MTA terms200',
            'Elexon licence pages403; no access bypass'],
        conclusion='Two genuinely separate primary-provider candidates acquired for audit, zero new independent model-result claims. Source terms, appropriate calendars, exposure and compatible evaluation protocol are prerequisites. No new future Indian actuals, old forecast changes or workflow activation.')
    dump(OUT/'audit.json',result)
    text='''# Independent-source readiness audit

Two primary-provider candidates were checked from downloaded bytes. Neither is a completed independent replication, an untouched test or a newly licensed research dataset. Raw probes remain outside Git; this folder contains our audit, source identifiers and hashes only.

| Candidate | Acquired evidence | Useful result | Remaining gate |
| --- | --- | --- | --- |
| MTA via NYS Open Data | 1,105 unique daily records, 1 January2022–9 January2025; subway/bus fields | All366days of2024present; the deprecated view does **not** cover full2025 | Successor-view provenance and compatible values, dataset-specific usage terms, US calendar and exposure audit; different target from electricity |
| Elexon ATL/B0610 | 336 unique, contiguous half-hour records across a seven-day UTC probe inMarch/April2025 | Local30March has46settlement periods; UTC query includes two3April-labelled periods | Authoritative quantity units/aggregation, revision/first-release policy, usage terms, broader bytes/calendar/model-exposure audit |

The MTA metadata's absent licenseId is not a proof that reuse is forbidden; neither is public download proof of permission. The open-data page welcomes analytical use but general site terms are restrictive. Dataset-specific terms remain unverified. Elexon legal pages returned403; no bypass was attempted. Generic dataset endpoints can ignore unsupported date filters: a rejected ITSDO probe returned a current row rather than the requested historical date. The documented dated ATL endpoint and returned-date guards avoid silently using that response.

These sources do not share Indian GRID/POSOCO lineage. That establishes source separation, not no pretraining exposure, regional-festival transfer or direct comparability of ridership, actual load and supplied energy. MTA is already used by the nearest calendar-encoding study. No primary raw probe is redistributed or used to claim forecast replication here.

See audit.json for exact URLs, retrieved hashes, row/date counts, transport failures and remaining acquisition rules. No future Indian observations, contact, environment publication or prospective workflow changes occurred.
'''
    (OUT/'README.md').write_text(text)
    print('Audited1105MTA daily records and336Elexon half-hours; independent replication remains pending')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path('/workspace/independent-source-cache'))
    main(p.parse_args().cache)
