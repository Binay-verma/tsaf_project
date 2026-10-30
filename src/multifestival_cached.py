"""Prespecified, matched multi-festival diagnostics of existing daily forecasts.

This changes scoring cohorts only. It does not train new festival covariates.
Run prepare before score; completed outputs are immutable.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data

OUT = ROOT / 'results/multifestival_cached_v1'
KEY = ['state', 'origin', 'date', 'year', 'horizon']
CONFIGS = {
    'chronos_history': ('results/extended_validation/predictions.csv', {'model': 'chronos2', 'mode': 'A_history', 'cohort': 'daily'}),
    'last_value': ('results/extended_validation/predictions.csv', {'model': 'last_value', 'mode': 'A_history', 'cohort': 'daily'}),
    'weekly_repeat': ('results/extended_validation/predictions.csv', {'model': 'seasonal_naive', 'mode': 'A_history', 'cohort': 'daily'}),
    'ridge_basic_history': ('results/extended_validation/predictions.csv', {'model': 'ridge', 'mode': 'A_history', 'cohort': 'daily'}),
    'ridge_basic_calendar': ('results/extended_validation/predictions.csv', {'model': 'ridge', 'mode': 'B_calendar', 'cohort': 'daily'}),
    'ridge_rich_history_monthly': ('results/strong_refit_v1/predictions.csv', {'model': 'ridge', 'mode': 'rich_history', 'schedule': 'monthly'}),
    'ridge_rich_calendar_monthly': ('results/strong_refit_v1/predictions.csv', {'model': 'ridge', 'mode': 'rich_calendar', 'schedule': 'monthly'}),
    'lightgbm_stable_history_monthly': ('results/stable_tree_refit_v2/predictions.csv', {'model': 'lightgbm', 'mode': 'rich_history', 'schedule': 'monthly'}),
    'lightgbm_stable_calendar_monthly': ('results/stable_tree_refit_v2/predictions.csv', {'model': 'lightgbm', 'mode': 'rich_calendar', 'schedule': 'monthly'}),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def prepare():
    if OUT.exists():
        raise FileExistsError('Version a new experiment; never overwrite an existing protocol/run')
    ledger_path = ROOT / 'results/extended_validation/regional_calendar_date_audit.csv'
    ledger = pd.read_csv(ledger_path, keep_default_na=False)
    annual = ledger[ledger.in_annual_schedule & ledger.year.isin([2024, 2025])]
    definitions = {
        'Holi': ('Holi', ['Delhi', 'Maharashtra']),
        'Dussehra': ('Dussehra', ['Delhi', 'Karnataka', 'Maharashtra']),
        'Ganesh_Chaturthi': ('Ganesh Chaturthi', ['Karnataka', 'Maharashtra']),
        'Ugadi_Gudi_Padwa': ('Ugadi|Gudi Padwa', ['Karnataka', 'Maharashtra']),
    }
    anchors = []
    for family, (pattern, states) in definitions.items():
        selected = annual[annual.state.isin(states) & annual.library_name.str.contains(pattern, regex=True)]
        assert len(selected) == len(states)*2, (family, selected)
        for r in selected.itertuples(index=False):
            anchors.append(dict(family=family, state=r.state, year=r.year, date=r.date,
                label=r.library_name, role='annual_as_issued_anchor', source=r.primary_document))
    # Preserve the existing broad Diwali cohort exactly, including the national
    # main date plus explicit regional subsidiary dates. Do not invent one date
    # of observance for all states or call all window days independent festivals.
    main = {2024: '2024-10-31', 2025: '2025-10-20'}
    extra = {'Delhi': {2024: [], 2025: []},
        'Karnataka': {2024: ['2024-11-02'], 2025: ['2025-10-22']},
        'Maharashtra': {2024: ['2024-11-01', '2024-11-02'], 2025: ['2025-10-21', '2025-10-22']}}
    for state, years in extra.items():
        for year, dates in years.items():
            url = annual[(annual.state == state) & (annual.year == year)].primary_document.iloc[0]
            for date in [main[year]] + dates:
                anchors.append(dict(family='Diwali', state=state, year=year, date=date,
                    label='Existing broad Diwali cohort anchor', role='national_main' if date == main[year] else 'regional_subsidiary',
                    source=url if date != main[year] or state != 'Maharashtra' else 'src/extended_validation.py MAIN; national date, not Maharashtra annual Lakshmi Pujan date'))
    a = pd.DataFrame(anchors).sort_values(['family', 'state', 'year', 'date'])
    rows, overlaps = [], []
    for (family, state, year), g in a.groupby(['family', 'state', 'year']):
        targets = sorted(set(d for date in pd.to_datetime(g.date) for d in pd.date_range(date-pd.Timedelta(days=3), date+pd.Timedelta(days=3))))
        other = annual[(annual.state == state) & (annual.year == year) & annual.date.isin([str(d.date()) for d in targets])]
        overlaps.append(dict(family=family, state=state, year=year,
            scheduled_dates_in_window='; '.join(other.date + ': ' + other.library_name.replace('', '[unlabelled annual date]')),
            warning='No isolated causal festival effect; concurrent observances and neighbouring windows may overlap'))
        for date in targets:
            for horizon in [1, 7, 14]:
                origin = date-pd.Timedelta(days=horizon-1)
                rows.append(dict(family=family, state=state, year=year,
                    date=str(date.date()), horizon=horizon, origin=str(origin.date())))
    cases = pd.DataFrame(rows).sort_values(['family']+KEY)
    assert not cases.duplicated(['family']+KEY).any()
    OUT.mkdir(parents=True)
    a.to_csv(OUT/'anchors.csv', index=False)
    cases.to_csv(OUT/'expected_cases.csv', index=False)
    pd.DataFrame(overlaps).to_csv(OUT/'holiday_overlaps.csv', index=False)
    paths = sorted({x[0] for x in CONFIGS.values()} | {
        'data/external/latest_state_energy_GWh.csv', str(ledger_path.relative_to(ROOT)),
        'src/extended_validation.py', 'src/multifestival_cached.py'})
    protocol = dict(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory extension after historical results were inspected. Recorded before new festival-specific errors; not an external preregistration or new final test.',
        years=[2024, 2025], families=list(definitions)+['Diwali'], configurations=CONFIGS,
        event_definition='Union of fixed +/-3-calendar-day anchor windows per family/state/year. Holi Delhi/Maharashtra; Ganesh and Ugadi/Gudi Karnataka/Maharashtra; Dussehra and Diwali all three. States absent from a schedule are not treated as zero-impact controls.',
        calendar_limit='Dates are annual-as-issued and named by the existing library crosswalk; no new amendment certification. Dussehra2025 overlaps Gandhi Jayanti; Spring2025 is adjacent to Eid. Annual schedule scope is government offices, not measured statewide shutdown.',
        scoring='Only positive recorded source labels; remove a missing label for every configuration equally and retain explicit exclusion. Missing forecasts fail; never silently shrink to successful models. Unique state/origin/lead cases, horizons target origin+h-1.',
        scale='Identical mean absolute weekly differences of recorded labels in preceding730 calendar days ending previous December31; never refit denominator on evaluation outcomes.',
        aggregation='MAE and MASE per festival/state/year/lead; equal states within year, then equal years within festival. Any overall MASE equally weights festival families. No ranking across unlike cohorts or row-level significance tests.',
        intervention='None: reuse unchanged historical forecasts. Calendar arms contain ordinary weekday/Fourier features, not these additional festival identities. Monthly baselines retain original pre-year selection logs. No settings selected using these new scores.',
        exclusions='Christmas excluded in this first extension because the saved origin schedule stops December18, preventing complete next-day cases. Eid-specific contrasts deferred pending moon-sighting/amendment evidence. No retrospective choice of shifted dates.',
        limitations=['Two historical years; related states/days/overlapping windows are dependent', 'Historical pretraining/proxy overlap and source revisions/lag unresolved', 'Models use different fitting/adaptation budgets; no architecture-only or causal superiority claim', 'Prospective frozen forecasts unchanged; no future outcomes acquired'],
        input_hashes={p: sha(ROOT/p) for p in paths},
        design_hashes={p: sha(OUT/p) for p in ['anchors.csv', 'expected_cases.csv', 'holiday_overlaps.csv']})
    dump(OUT/'protocol.json', protocol)
    print('PREPARED', len(a), 'anchors;', len(cases), 'festival-case memberships;', len(cases[KEY].drop_duplicates()), 'unique cases')


def metrics(d, out):
    d = d.copy()
    d['ae'] = abs(d.prediction-d.actual)
    d['scaled'] = d.ae/d.mase_scale
    m = d.groupby(['family', 'configuration', 'state', 'year', 'horizon']).agg(
        MAE_GWh=('ae', 'mean'), MASE=('scaled', 'mean'), n=('ae', 'size')).reset_index()
    m.to_csv(out/'metrics_state_year.csv', index=False)
    y = m.groupby(['family', 'configuration', 'year', 'horizon']).agg(MASE=('MASE', 'mean'), states=('state', 'nunique')).reset_index()
    y.to_csv(out/'metrics_year.csv', index=False)
    macro = y.groupby(['family', 'configuration', 'horizon']).agg(MASE=('MASE', 'mean'), years=('year', 'nunique')).reset_index()
    macro.to_csv(out/'metrics_festival.csv', index=False)
    macro.groupby(['configuration', 'horizon']).MASE.mean().reset_index().to_csv(out/'metrics_balanced.csv', index=False)
    return macro


def score():
    if (OUT/'predictions.csv').exists():
        raise FileExistsError('Preserve completed scores')
    protocol = json.loads((OUT/'protocol.json').read_text())
    for p, h in protocol['input_hashes'].items():
        assert sha(ROOT/p) == h, p
    for p, h in protocol['design_hashes'].items():
        assert sha(OUT/p) == h, p
    cases = pd.read_csv(OUT/'expected_cases.csv')
    data = load_data('latest')
    cases['source_actual'] = [data.loc[pd.Timestamp(r.date), r.state] for r in cases.itertuples(index=False)]
    excluded = cases[cases.source_actual.isna()].copy()
    excluded['reason'] = 'No positive recorded source label; removed for all configurations'
    excluded.to_csv(OUT/'excluded_labels.csv', index=False)
    cases = cases[cases.source_actual.notna()].copy()
    rows = []
    cache = {}
    for configuration, (filename, filters) in protocol['configurations'].items():
        if filename not in cache:
            cache[filename] = pd.read_csv(ROOT/filename)
        source = cache[filename]
        for col, value in filters.items():
            source = source[source[col].eq(value)]
        assert not source.duplicated(KEY).any(), configuration
        matched = cases.merge(source[KEY+['prediction', 'actual', 'mase_scale']], on=KEY, how='left', validate='many_to_one', indicator=True)
        missing = matched[matched['_merge'] != 'both']
        if len(missing):
            missing.to_csv(OUT/f'missing_{configuration}.csv', index=False)
            raise ValueError(f'{configuration}: {len(missing)} missing forecasts; no cohort shrinking allowed')
        np.testing.assert_allclose(matched.actual, matched.source_actual, rtol=0, atol=1e-10)
        assert np.isfinite(matched[['prediction', 'actual', 'mase_scale']]).all().all()
        assert (matched.mase_scale > 0).all()
        matched['configuration'] = configuration
        rows.append(matched.drop(columns=['_merge', 'source_actual']))
    result = pd.concat(rows, ignore_index=True)
    result.to_csv(OUT/'predictions.csv', index=False)
    macro = metrics(result, OUT)
    report = ['# Multi-festival historical forecast diagnostics v1', '',
        'Completed rescore of unchanged daily forecasts, 2024–2025. No new fitting or festival feature was added.',
        f'{len(cases)} scored festival-case memberships per configuration; {len(result)} prediction memberships; {len(excluded)} missing-label memberships excluded equally.', '',
        '## Festival-balanced comparisons', '', 'MASE; lower is better. Equal states within year, then equal years. Only the listed state/festival combinations are included.', '']
    for family, g in macro.groupby('family'):
        report += [f'### {family}', '', g.pivot(index='configuration', columns='horizon', values='MASE').round(5).to_markdown(), '']
    report += ['## Interpretation and bounds', '',
        'These are forecast-performance diagnostics during documented festival windows, not estimated effects of adding new festival covariates. There is no universal winner or causal festival claim. All variants and individual-year/state metrics are retained; no best configuration is selected for a clean test.', '',
        'Only two years, shared-source states and overlapping observances. Dussehra2025 includes Gandhi Jayanti; Spring2025 borders Eid. Dates remain annual-as-issued, not fully amendment-certified. TimesFM/SARIMAX do not have full coverage in these saved files and are intentionally absent from this first table. A separately recorded extension must fill those cases.', '',
        'The broad Diwali union is unchanged from earlier studies; it is not identical to a single main-day window in every state. Other festival groups use one anchor per state/year. Christmas and moon-sensitive Eid contrasts are deferred for the reasons recorded in protocol.json. Source vintages/pretraining overlap remain uncertain. Prospective forecasts were not changed or scored.']
    (OUT/'REPORT.md').write_text('\n'.join(report)+'\n')
    dump(OUT/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), configurations=len(rows),
        scored_memberships_per_configuration=len(cases), unique_cases_per_configuration=len(cases[KEY].drop_duplicates()),
        prediction_memberships=len(result), excluded_missing_label_memberships=len(excluded),
        protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(OUT/'predictions.csv'),
        old_forecasts_reused=True, new_fits=0, no_prospective_scores=True))
    print('COMPLETED', len(rows), 'configurations;', len(result), 'prediction memberships')
    print(pd.read_csv(OUT/'metrics_balanced.csv').pivot(index='configuration', columns='horizon', values='MASE').round(5).to_string())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'score'])
    args = parser.parse_args()
    {'prepare': prepare, 'score': score}[args.action]()
