"""Second registered test, seven more states (registered before any selection or forecast).

Seven states never used in the project: Punjab, Haryana, West Bengal, Kerala, Bihar, Odisha, Chhattisgarh.
Event years 2017-2025; calendars 2015-2025 from review/new_states_v2/calendar_entries_2015_2025.csv (built by
src/new_states_v2_calendar_build_v1.py; check_method per row). Same arms, case rule, frames, placebos, regression
and SARIMAX code as Stage A/B and the first registered test (src/new_states_v1.py); local models only.

The shared modules read their state list and data loader from forecasting.py; this module points them at the
new states BEFORE importing anything else, so this file must be run as its own process.

Actions:
  data                     build data/external/new_states_v2_energy_GWh.csv from data/external/POSOCO_data.csv
  prepare                  write the registered design (refuses unchecked calendar rows)
  select-ridge | select-tree   parameter selection by the unchanged strong_refit / stable_tree procedures
  ridge | lightgbm | lightgbm_capacity2 | sarimax   local forecasts
"""
import sys
from pathlib import Path
import forecasting

NEW_STATES = {'Punjab': 'PB', 'Haryana': 'HR', 'West Bengal': 'WB', 'Kerala': 'KL', 'Bihar': 'BR',
              'Odisha': 'OD', 'Chhattisgarh': 'CG'}
POSOCO_COLUMN = {k: k for k in NEW_STATES}
DATA = forecasting.ROOT/'data/external/new_states_v2_energy_GWh.csv'


def load_new(source='latest'):
    import pandas as pd
    assert source == 'latest'
    d = pd.read_csv(DATA, index_col=0, parse_dates=True).sort_index()
    if d.index.has_duplicates:
        raise ValueError('Duplicate dates are not permitted')
    d = d[list(NEW_STATES)].asfreq('D')
    return d.where(d > 0)


forecasting.STATES = NEW_STATES
forecasting.load_data = load_new

import argparse  # noqa: E402
import json  # noqa: E402
import inspect  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from forecasting import ROOT  # noqa: E402
from festival_feature_design import sha, dump  # noqa: E402
import longer_panel_stage_a_v1 as A  # noqa: E402

OUT = ROOT/'results/new_states_v2'
ENTRIES = ROOT/'review/new_states_v2/calendar_entries_2015_2025.csv'
CAL_YEARS = list(range(2015, 2026))
EVENT_YEARS = list(range(2017, 2026))
ARMS = ['calendar', 'zero5', 'day5', 'pooled_day5', 'placebo_day5']
LOCAL = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
SCOPE = {'Bihar': ['Holi', 'Dussehra', 'Diwali'], 'Chhattisgarh': ['Holi', 'Dussehra', 'Diwali'],
         'Haryana': ['Holi', 'Dussehra', 'Diwali'], 'Punjab': ['Holi', 'Dussehra', 'Diwali'],
         'West Bengal': ['Holi', 'Dussehra', 'Diwali'], 'Kerala': ['Dussehra', 'Diwali'],
         'Odisha': ['Holi', 'Dussehra', 'Ganesh_Chaturthi', 'Diwali']}
LEDGER = 'anchors_2015_2025.csv'
PLACEBO = 'placebo_anchors_2015_2025.csv'
HYPOTHESES = {
    'R1': 'SARIMAX(1,0,0)(1,0,0,7): typed-day minus pooled-day event MASE at lead 1 is NEGATIVE (typed better). Replicates H1 of osf.io/yw7mr.',
    'R2': 'LightGBM with minimum leaf size fixed at 2: typed-day minus pooled-day event MASE at lead 1 is POSITIVE (pooled better). Replicates H3 of osf.io/yw7mr.',
    'M1': 'Ridge: in the three states with the highest early-period absolute festival-effect dispersion (h_abs, 2015-2020 demand only: Chhattisgarh, West Bengal, Haryana), typed-day minus pooled-day lead-1 MASE over 2021-2025 is NEGATIVE.',
    'M2': 'Across the seven states, h_abs is NEGATIVELY rank-correlated (Spearman) with the state mean Ridge typed-day minus pooled-day lead-1 MASE over 2021-2025.'}


def build_data():
    if DATA.exists():
        raise FileExistsError(DATA)
    d = pd.read_csv(ROOT/'data/external/POSOCO_data.csv')
    d.index = pd.to_datetime(d.yyyymmdd.astype(str)); d.index.name = 'date'
    out = pd.DataFrame({s: d[f'{c}: EnergyMet'] for s, c in POSOCO_COLUMN.items()})
    out.to_csv(DATA)
    print(DATA, out.shape, out.index.min().date(), out.index.max().date())


def anchors():
    t = pd.read_csv(ENTRIES, dtype=str).fillna('')
    if (t.checked_by.eq('') | t.check_date.eq('')).any():
        raise ValueError('unchecked calendar rows')
    t = t[t.date.ne('')]
    rows = [dict(family=r.family, state=r.state, year=int(r.year), date=r.date, label=r.family,
                 role='regional_subsidiary' if r.role == 'regional_subsidiary' else 'annual_as_issued_anchor',
                 source=r.document_url, evidence=f'{r.candidate_source}; row {r.row}; checked {r.checked_by} {r.check_date}')
            for r in t.itertuples(index=False)]
    a = pd.DataFrame(rows)
    assert set(a.state) == set(NEW_STATES) and all(set(a[a.state == s].family) <= set(f) for s, f in SCOPE.items())
    assert (pd.to_datetime(a.date).dt.year == a.year).all()
    return a.sort_values(['state', 'year', 'family', 'date']).reset_index(drop=True)


def event_cases(a):
    ev = A.event_cases(a, EVENT_YEARS)
    lab = load_new()
    ok = [pd.notna(lab.at[pd.Timestamp(r.date), r.state]) for r in ev.itertuples(index=False)]
    return ev[ok].reset_index(drop=True), ev[[not x for x in ok]]


INPUTS = ['src/new_states_v2.py', 'src/new_states_v2_analysis.py', 'src/test_new_states_v2.py', 'src/new_states_v1.py',
          'src/longer_panel_stage_a_v1.py', 'src/breadth_model_engine_v1.py', 'src/robust_baselines.py', 'src/stable_tree_refit.py',
          'src/extended_validation.py', 'src/forecasting.py', 'src/ziel_foundation_v1.py', 'src/festival_feature_design.py',
          'src/cluster_inference_v1.py', 'data/external/new_states_v2_energy_GWh.csv', 'data/external/POSOCO_data.csv',
          'review/new_states_v2/calendar_entries_2015_2025.csv', 'review/new_states_v2/DESIGN_DRAFT.md',
          'review/new_states_v2/power/early_heterogeneity_2015_2020.csv', 'src/new_states_v2_early_h_v1.py',
          'src/new_states_v2_calendar_build_v1.py', 'src/new_states_v2_power_v1.py',
          'results/strong_refit_v1/protocol.json', 'results/stable_tree_refit_v2/protocol.json',
          'results/feature_breadth_v1/event_window/protocol.json']

TEST = ('R1, R2: per state, family and year, mean lead-1 MASE over the event cases, typed-day minus pooled-day. Cluster = family-year; '
        'cluster value = equal-weight mean over the states in that cluster. Statistic = mean over clusters. One-sided sign-flip '
        'p in the hypothesised direction, Monte Carlo with 1,000,000 sign draws (numpy default_rng seed 20261116), p = (k+1)/(N+1). '
        'M1: units = state-family-year values of Ridge typed minus pooled lead-1 MASE, 2021-2025, in the three named states; '
        'statistic = mean over units; same one-sided sign-flip (seed 20261116). '
        'M2: Spearman correlation (average ranks for ties) between h_abs and the state mean of the M1 unit values over 2021-2025, '
        'one-sided exact permutation p over all 5040 orderings of the outcome, p = share of orderings with correlation <= observed. '
        'Holm across R1, R2, M1, M2, alpha 0.05.')
DECISION = ('R1, R2: CONFIRMED if the Holm-adjusted p < 0.05 AND the year means (each year = mean of its family-year clusters) have the '
            'hypothesised sign in at least 6 of the 9 event years. M1: CONFIRMED if the Holm-adjusted p < 0.05 AND the year means '
            '(2021-2025) are negative in at least 4 of 5 years. M2: CONFIRMED if the Holm-adjusted p < 0.05. CONTRADICTED (any) if the '
            'statistic has the opposite sign and its opposite-direction one-sided p < 0.05 (not Holm-adjusted). Otherwise NOT CONFIRMED.')


def prepare(out=OUT):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    a = anchors(); fake = A.placebos(a)
    ev, dropped = event_cases(a)
    out.mkdir(parents=True)
    a.to_csv(out/LEDGER, index=False); fake.to_csv(out/PLACEBO, index=False)
    sel = {}
    for name, parent in [('ridge', 'strong_refit_v1'), ('tree', 'stable_tree_refit_v2')]:
        d = Path(str(out)+f'_selection_{name}'); d.mkdir()
        q = json.loads((ROOT/f'results/{parent}/protocol.json').read_text())
        q.update(experiment=d.name, created_utc=datetime.now(timezone.utc).isoformat(), years=EVENT_YEARS, modes=['rich_calendar'], refits=['monthly'],
                 states=list(NEW_STATES), status=f'Parameter selection for the new-states study by the unchanged procedure of results/{parent}; ordinary calendar only.')
        dump(d/'protocol.json', q)
        dump(d/'protected_before.json', {f: sha(ROOT/f) for f in INPUTS})
        sel[name] = str(d.relative_to(ROOT))
    parent = json.loads((ROOT/'results/feature_breadth_v1/event_window/protocol.json').read_text())
    cohorts = {'event_window': (ev, LOCAL, ARMS)}
    for name, (cases, models, arms) in cohorts.items():
        (out/name).mkdir()
        for f in ['window_cases.csv', 'primary_cases.csv']:
            cases.to_csv(out/name/f, index=False)
        p = dict(experiment=f'{out.name}/{name}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
                 status='Registered before any parameter selection or forecast for these states; no outcome of these states has been evaluated in this project.',
                 states=list(NEW_STATES), scope=SCOPE, event_years=sorted(cases.year.unique().tolist()), calendar_years=CAL_YEARS,
                 arms=arms, models=models, parameter_selection=sel,
                 hypotheses=HYPOTHESES,
                 reported_not_tested=['ridge and lightgbm (stable) at lead 1 against the R1/R2 rule', 'all arms, leads 7 and 14', 'zero and placebo controls',
                                      'combined first + second test: R1/R2 statistic over the 45 family-year clusters with all 14 states'],
                 power='review/new_states_v2/power/README.md: about 18-34% (R1) and 19-36% (R2) if the effect equals the first test; stated before any forecast.',
                 test=TEST, decision=DECISION,
                 sensitivity='Pre-declared, reported alongside without changing the decision: (a) 2020-2021 removed (COVID); (b) only rows checked by the author one by one (check_method not triage); (c) M1/M2 with the first-test h instead of h_abs.',
                 conventions=['anchors = main festival day per family and year (review/new_states_v2/DESIGN_DRAFT.md); conventions 1-6 of review/new_states_v1/DESIGN_DRAFT.md',
                              'weekend festivals stay flagged; optional-only years get no flag',
                              'case rule, frames, placebos (seed 42), regression and SARIMAX code as Stage A',
                              'cases whose label is missing or non-positive are dropped before registration'],
                 threads=parent['threads'], seed=parent['seed'], batch=parent['batch'],
                 expected_tasks=int(len(cases[['state', 'year', 'origin']].drop_duplicates())),
                 input_hashes={f: sha(ROOT/f) for f in INPUTS},
                 design_hashes={f: sha(out/name/f) for f in ['window_cases.csv', 'primary_cases.csv']}
                 | {f'../{LEDGER}': sha(out/LEDGER), f'../{PLACEBO}': sha(out/PLACEBO)})
        dump(out/name/'protocol.json', p)
    s = dict(event_cases=len(ev), dropped_missing_label=len(dropped), by_year=ev.groupby('year').size().to_dict(),
             by_state=ev.groupby('state').size().to_dict(), clusters=int(ev[['family', 'year']].drop_duplicates().shape[0]),
             states_per_cluster=round(float(ev.groupby(['family', 'year']).state.nunique().mean()), 2))
    dump(out/'design_summary.json', s)
    print(json.dumps(s, indent=1, default=str))
    return s


def bound(dates):
    assert pd.Timestamp(min(dates)) >= pd.Timestamp('2015-01-01') and pd.Timestamp(max(dates)) <= pd.Timestamp('2025-12-31')


def selected(model_name, year):
    assert year in EVENT_YEARS
    return pd.read_csv(Path(str(OUT)+('_selection_ridge' if model_name == 'ridge' else '_selection_tree'))/'selected.csv')


def regression(engine, worker):
    """The registered Stage A regression, executed from its own source with only the two ledger file names changed."""
    src = inspect.getsource(A.regression)
    new = src.replace("'anchors_2020_2025.csv'", repr(LEDGER)).replace("'placebo_anchors_2020_2025.csv'", repr(PLACEBO))
    assert sum(x != y for x, y in zip(src.splitlines(), new.splitlines())) == 1
    ns = dict(vars(A)); ns.update(ARMS=ARMS, bound=bound, selected=selected)
    exec(compile(new, A.__file__, 'exec'), ns)
    return ns['regression'](engine, worker)


def _engine(cohort, arms=ARMS):
    """Point the shared engine at this study; A.frames builds all eight Stage A arms and the five used here are kept."""
    import breadth_model_engine_v1 as engine
    a = pd.read_csv(OUT/LEDGER); fake = pd.read_csv(OUT/PLACEBO)
    assert set(ARMS) <= set(A.ARMS)
    engine.OUT = OUT/cohort; engine.ARMS = arms; engine.EXTRA = []; engine.ledger_bound = bound
    engine.frames = lambda index, state: {k: v for k, v in A.frames(index, state, a, fake).items() if k in arms}
    return engine, a, fake


def run_local(worker):
    for name in ['ridge', 'tree']:
        assert (Path(str(OUT)+f'_selection_{name}')/'selected.csv').exists(), 'run the parameter selection first'
    engine, _, _ = _engine('event_window')
    engine.sarimax() if worker == 'sarimax' else regression(engine, worker)


def select(kind):
    import robust_baselines
    out = Path(str(OUT)+f'_selection_{kind}').resolve()
    if kind == 'tree':
        original = robust_baselines.design_frame

        def stable_design(*args, **kwargs):
            frame, event = original(*args, **kwargs)
            return frame.astype(np.float32), event
        robust_baselines.design_frame = stable_design
    sys.argv = [sys.argv[0], '--out', str(out)]
    robust_baselines.main()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['data', 'prepare', 'select-ridge', 'select-tree', *LOCAL])
    args = p.parse_args()
    if args.action == 'data':
        build_data()
    elif args.action == 'prepare':
        prepare()
    elif args.action.startswith('select-'):
        select(args.action.split('-')[1])
    else:
        run_local(args.action)
