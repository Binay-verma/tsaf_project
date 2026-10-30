"""Date-only, versioned intervention design; no outcomes select its features."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.metadata
import json
import numpy as np
import pandas as pd
from forecasting import ROOT

OUT = ROOT/'results/festival_features_v1'
BASE = ROOT/'results/multifestival_cached_v1'
FAMILIES = ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa', 'Diwali']
ARMS = ['calendar', 'zero5', 'day5', 'window5', 'placebo_day5', 'placebo_window5']
EXTRA = ['offset35', 'zero35', 'placebo_offset35']
KEY = ['family', 'state', 'year', 'origin', 'date', 'horizon']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def prepare():
    if (OUT/'protocol.json').exists():
        raise FileExistsError('Preserve the frozen design; version a new experiment')
    OUT.mkdir(parents=True, exist_ok=True)
    annual = pd.read_csv(ROOT/'results/extended_validation/regional_calendar_date_audit.csv', keep_default_na=False)
    anchors = pd.read_csv(BASE/'anchors.csv').to_dict('records')
    dates = {
        'Holi': {'Delhi': {2022: ['03-18'], 2023: ['03-08']}, 'Maharashtra': {2022: ['03-18'], 2023: ['03-07']}},
        'Dussehra': {s: {2022: ['10-05'], 2023: ['10-24']} for s in ['Delhi', 'Karnataka', 'Maharashtra']},
        'Ganesh_Chaturthi': {'Karnataka': {2022: ['08-31'], 2023: ['09-18']}, 'Maharashtra': {2022: ['08-31'], 2023: ['09-19']}},
        'Ugadi_Gudi_Padwa': {s: {2022: ['04-02'], 2023: ['03-22']} for s in ['Karnataka', 'Maharashtra']},
        'Diwali': {'Delhi': {2022: ['10-24'], 2023: ['11-12']},
            'Karnataka': {2022: ['10-24', '10-26'], 2023: ['11-12', '11-14']},
            'Maharashtra': {2022: ['10-24', '10-26'], 2023: ['11-12', '11-14']}}
    }
    for family, states in dates.items():
        for state, years in states.items():
            for year, days in years.items():
                source = annual[(annual.state.eq(state)) & annual.year.eq(year)].primary_document.iloc[0]
                for day in days:
                    date = f'{year}-{day}'
                    assert len(annual[annual.state.eq(state) & annual.date.eq(date) & annual.in_annual_schedule]) == 1, (family, state, date)
                    evidence = 'Existing annual-as-issued audit crosswalk'
                    if state == 'Karnataka' and year == 2023:
                        evidence = 'KA2023_NOTIFICATION.pdf page6: visually checked English table/notes; notice21Nov2022'
                    if state == 'Maharashtra' and year == 2023:
                        evidence = 'MH2023_official.pdf English page3; government-hosted notice2Dec2022, newly retrieved'
                    anchors.append(dict(family=family, state=state, year=year, date=date,
                        label=family, role='national_main' if family == 'Diwali' and day == days[0] else 'regional_subsidiary' if family == 'Diwali' else 'annual_as_issued_anchor',
                        source=source, evidence=evidence))
    a = pd.DataFrame(anchors).fillna({'evidence': 'Existing2024–2025evaluation-anchor ledger; annual-as-issued, not amended'})
    assert len(a) == 58 and len(a[['family', 'state', 'year']].drop_duplicates()) == 48
    a = a.sort_values(['state', 'year', 'family', 'date'])
    a.to_csv(OUT/'anchors_2022_2025.csv', index=False)
    cases = pd.read_csv(BASE/'expected_cases.csv')
    cases.to_csv(OUT/'window_cases.csv', index=False)
    centre = a[a.year.isin([2024, 2025]) & ((a.family != 'Diwali') | a.role.eq('national_main'))][['family', 'state', 'year', 'date']]
    primary = cases.merge(centre, on=['family', 'state', 'year', 'date'], validate='many_to_one')
    assert len(primary) == 72 and not primary.duplicated(KEY).any()
    primary.sort_values(KEY).to_csv(OUT/'primary_cases.csv', index=False)
    rng = np.random.default_rng(42)
    placebos = []
    for (state, year, family), g in a.groupby(['state', 'year', 'family'], sort=True):
        true = a[a.state.eq(state) & a.year.eq(year)]
        prohibited = {d for date in pd.to_datetime(true.date) for d in pd.date_range(date-pd.Timedelta(days=3), date+pd.Timedelta(days=3))}
        valid = []
        for shift in [-42, -35, -28, 28, 35, 42]:
            shifted = pd.to_datetime(g.date)+pd.Timedelta(days=shift)
            window = {d for date in shifted for d in pd.date_range(date-pd.Timedelta(days=3), date+pd.Timedelta(days=3))}
            if all(d.year == year for d in window) and not window.intersection(prohibited):
                valid.append(shift)
        assert valid, (state, year, family)
        shift = int(rng.choice(valid))
        for r in g.itertuples(index=False):
            placebos.append(dict(state=state, year=int(year), family=family,
                date=str((pd.Timestamp(r.date)+pd.Timedelta(days=shift)).date()), original_date=r.date, shift_days=shift))
    pd.DataFrame(placebos).to_csv(OUT/'placebo_anchors.csv', index=False)
    evidence = [p for p in (OUT/'evidence').glob('*') if p.is_file()]
    paths = ['src/festival_feature_design.py', 'src/festival_feature_experiment.py',
        'src/forecasting.py', 'src/extended_validation.py', 'src/robust_baselines.py',
        'data/external/latest_state_energy_GWh.csv',
        'results/strong_refit_v1/selected.csv', 'results/strong_refit_v1/protocol.json',
        'results/stable_tree_refit_v2/selected.csv', 'results/stable_tree_refit_v2/protocol.json',
        'results/multifestival_models_v1/predictions.csv',
        'results/mechanism_controls_v1/chronos_download.json', 'results/second_model_audit_v1/weight_download.json',
        'results/extended_validation/regional_calendar_date_audit.csv',
        'evidence/calendars/KA2023_NOTIFICATION.pdf'] + [str(p.relative_to(ROOT)) for p in evidence]
    p = dict(experiment=OUT.name, created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory intervention after inspecting historical benchmark/plots; frozen before new intervention outcomes. Not external preregistration, clean final test, causal identification or new-method novelty.',
        primary='72date-selected anchor targets,24festival/state/year groups, leads1/7/14. Same cases for every model/arm. Diwali uses legacy national/main target; Maharashtra regional dates remain in features. No outcome-selected case reduction.',
        secondary='All528unchanged window cases for rich Ridge, stable LightGBM, fixed-capacity2 tree and SARIMAX. Foundation-model claims restricted to72anchor targets; never compare their anchor scores with others window scores.',
        years=[2024, 2025], ledger_years=[2022, 2023, 2024, 2025], families=FAMILIES,
        arms=ARMS, regression_extra_arms=EXTRA,
        features='day5: one binary per family on any declared anchor. window5: one binary per family over union+/-3days. offset35: five families x seven relative-day channels. Structural zero families remain zero in states outside the documented scope. No target encoding.',
        controls='Same5/35zero channels; same-size active placebo day/window/offset channels. One seeded family/state/year shift by a multiple of7within28–42days; no overlap of placebo windows with any registered true window in that state/year. Not a randomization distribution.',
        local_models='Rich27history+13ordinary-calendar monthly Ridge/LightGBM; retain each state/year/lead original rich_calendar pre-year-selected parameters for ALL new arms. No new feature/parameter search. Tree interface float32, deterministic1thread. Capacity sensitivity changes only min_child_samples to2 for all6arms; report separately, never select it by evaluated errors.',
        sparse_events='Day indicators may have only1–2prior examples, below tree leaf constraints. Log training/context support; weak/ignored indicators are not evidence of intrinsic irrelevance. Additive features can also affect non-event days.',
        sarimax='Fixed(1,0,0)x(1,0,0,7), no trend with13calendar plus0/5event channels. Annual pre-year730day fit; causal past fill and state updates only. Training-only L-BFGS150,500thenPowell500 convergence retries; retain failures.',
        foundation_models='Pinned Chronos2 and TimesFM3, all6arms fresh inference,730day target context,14day horizon, batch4,2CPUthreads,42seed. No fine-tuning; native quantiles retained. Future calendar information only. Verify actual weights/config hashes; input perturbation/solo batching checks.',
        batch=4, threads=2, seed=42, context=730, horizon=14,
        availability='All used event covariate dates in training or inference must lie within2022–2025ledger coverage. Reused pre-year hyperparameters were selected WITHOUT these new event identities. This avoids needing an unaudited2021event-feature fitting block. No claim of fully reconstructed historical publication availability.',
        metrics='Only positive recorded labels; same pre-year730calendar-day weekly-difference MASE scale, MAE per state/year/lead. Equal states within year, years within festival, festivals for overall summaries. Paired percent reductions calculated within state/year, not ratio of macro MASE. Record all years, arms, failures and native quantile crossings; no significance claims.',
        limits=['Two historical years; source/proxy overlap and publication revisions unresolved',
            'Annual-as-issued dates, not complete amendment certification or statewide closure evidence',
            'Dussehra2025/Gandhi and spring2025/Eid overlap',
            'Legacy Diwali subset is not every named Diwali-office holiday',
            'One placebo seed and fixed representation are bounded controls',
            'No future outcomes, prospective changes, public push or external message'],
        input_hashes={f: sha(ROOT/f) for f in paths},
        design_hashes={f: sha(OUT/f) for f in ['anchors_2022_2025.csv', 'placebo_anchors.csv', 'primary_cases.csv', 'window_cases.csv']},
        packages={n: importlib.metadata.version(n) for n in ['numpy', 'pandas', 'scikit-learn', 'lightgbm', 'statsmodels', 'torch', 'chronos-forecasting', 'timesfm']})
    dump(OUT/'protocol.json', p)
    print('FROZEN58anchors;72primary/528secondarycases;6commonarms;3extraoffsetarms for main regressions')


def frames(index, state):
    from extended_validation import features
    base, cols, _ = features(index, state)
    base = base[cols['B_calendar']].copy()
    true = pd.read_csv(OUT/'anchors_2022_2025.csv')
    fake = pd.read_csv(OUT/'placebo_anchors.csv')
    def event_columns(ledger, kind):
        values = {}
        for family in FAMILIES:
            dates = pd.to_datetime(ledger[ledger.state.eq(state) & ledger.family.eq(family)].date)
            if kind == 'offset':
                for offset in range(-3, 4):
                    values[f'{family}_offset_{offset}'] = index.isin(dates+pd.Timedelta(days=offset)).astype(float)
            else:
                targets = dates if kind == 'day' else [d for a in dates for d in pd.date_range(a-pd.Timedelta(days=3), a+pd.Timedelta(days=3))]
                values[f'{family}_{kind}'] = index.isin(targets).astype(float)
        return pd.DataFrame(values, index=index)
    extra = {'zero5': pd.DataFrame(0., index=index, columns=[f'zero_{i}' for i in range(5)]),
        'zero35': pd.DataFrame(0., index=index, columns=[f'zero_{i}' for i in range(35)]),
        'day5': event_columns(true, 'day'), 'window5': event_columns(true, 'window'),
        'offset35': event_columns(true, 'offset'), 'placebo_day5': event_columns(fake, 'day'),
        'placebo_window5': event_columns(fake, 'window'), 'placebo_offset35': event_columns(fake, 'offset')}
    return {'calendar': base, **{name: pd.concat([base, value], axis=1) for name, value in extra.items()}}


if __name__ == '__main__':
    prepare()
