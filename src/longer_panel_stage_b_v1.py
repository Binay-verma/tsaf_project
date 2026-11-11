"""Longer panel, Stage B: confirmatory test of results/model_class_hypothesis_v1 on Maharashtra 2019-2021.

Event years 2019, 2020, 2021 are unseen by every model and arm. Calendar years 2017-2021 from
review/longer_panel_v1/calendar_entries_2014_2021.csv, every row checked by a person. Everything else
reuses the registered Stage A code unchanged (cases rule, frames, placebos, regression, SARIMAX engine);
only the state, years, arms and parameter-selection folders differ.

Conventions: first Diwali anchor = Maharashtra's listed Laxmi Pujan date (equal to extended_validation.MAIN
in 2020-2021, the only Stage B years MAIN covers); second = Bali Pratipada; weekend-listed festivals stay flagged; cases on a
date without a recorded positive label are dropped before registration (none expected).

Actions:
  prepare [--allow-unchecked --out DIR]
  ridge | lightgbm | lightgbm_capacity2 | sarimax
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from forecasting import ROOT, load_data
from festival_feature_design import sha, dump
import longer_panel_stage_a_v1 as A

OUT = ROOT/'results/longer_panel_stage_b_v1'
STATE = 'Maharashtra'
CAL_YEARS = [2017, 2018, 2019, 2020, 2021]
EVENT_YEARS = [2019, 2020, 2021]
ARMS = ['calendar', 'zero5', 'day5', 'pooled_day5', 'placebo_day5']
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax']
HYPOTHESIS = ROOT/'results/model_class_hypothesis_v1/registration.json'


def anchors(allow_unchecked=False):
    t = pd.read_csv(A.ENTRIES, dtype=str).fillna('')
    t = t[t.state.eq(STATE) & t.year.astype(int).isin(CAL_YEARS) & t.date.ne('')]
    if not allow_unchecked and (t.checked_by.eq('') | t.check_date.eq('')).any():
        raise ValueError(f'{int((t.checked_by == "").sum())} Maharashtra calendar rows for 2017-2021 are not checked yet')
    rows = []
    for r in t.itertuples(index=False):
        role = 'national_main' if (r.family == 'Diwali' and r.role == 'annual_as_issued_anchor') else (
            'regional_subsidiary' if r.role == 'regional_subsidiary' else 'annual_as_issued_anchor')
        rows.append(dict(family=r.family, state=STATE, year=int(r.year), date=r.date, label=r.family, role=role,
                         source=r.document_url, evidence=f'{r.candidate_source}; checked {r.checked_by} {r.check_date}'))
    a = pd.DataFrame(rows)
    for y in CAL_YEARS:
        fam = a[a.year.eq(y)].family
        assert set(fam) == set(A.SCOPE[STATE]) and (fam == 'Diwali').sum() == 2, (y, sorted(fam))
    return a.sort_values(['year', 'family', 'date']).reset_index(drop=True)


INPUTS = ['src/longer_panel_stage_b_v1.py', 'src/longer_panel_analysis_stage_b_v1.py', 'src/test_longer_panel_stage_b_v1.py',
          'src/longer_panel_stage_a_v1.py', 'src/breadth_model_engine_v1.py', 'src/robust_baselines.py', 'src/stable_tree_refit.py',
          'src/extended_validation.py', 'src/forecasting.py', 'src/multifestival_models.py', 'src/cluster_inference_v1.py',
          'data/external/latest_state_energy_GWh.csv', 'review/longer_panel_v1/calendar_entries_2014_2021.csv',
          'results/model_class_hypothesis_v1/registration.json',
          'results/strong_refit_v1/protocol.json', 'results/stable_tree_refit_v2/protocol.json']


def prepare(out=OUT, allow_unchecked=False):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    a = anchors(allow_unchecked)
    fake = A.placebos(a)
    ev = A.event_cases(a, EVENT_YEARS)
    data = load_data('latest')[STATE]
    lab = data.reindex(pd.to_datetime(ev.date))
    keep = (lab.notna() & (lab > 0)).to_numpy()
    dropped = ev[~keep]
    ev = ev[keep].reset_index(drop=True)
    out.mkdir(parents=True)
    a.to_csv(out/'anchors_2017_2021.csv', index=False); fake.to_csv(out/'placebo_anchors_2017_2021.csv', index=False)
    (out/'event_window').mkdir()
    ev.to_csv(out/'event_window'/'window_cases.csv', index=False); ev.to_csv(out/'event_window'/'primary_cases.csv', index=False)
    sel = {}
    for name, parent in [('ridge', 'strong_refit_v1'), ('tree', 'stable_tree_refit_v2')]:
        d = Path(str(out)+f'_selection_{name}'); d.mkdir()
        q = json.loads((ROOT/f'results/{parent}/protocol.json').read_text())
        q.update(experiment=d.name, created_utc=datetime.now(timezone.utc).isoformat(), years=EVENT_YEARS, modes=['rich_calendar'],
                 refits=['monthly'], status=f'Parameter selection for Stage B event years 2019-2021 by the unchanged procedure of results/{parent}; ordinary calendar only.')
        dump(d/'protocol.json', q)
        dump(d/'protected_before.json', {f: sha(ROOT/f) for f in INPUTS})
        sel[name] = str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
    h = json.loads(HYPOTHESIS.read_text())
    dump(out/'event_window'/'protocol.json', dict(
        experiment=f'{out.name}/event_window', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
        status='Confirmatory test of results/model_class_hypothesis_v1, registered before any Stage B selection or forecast.',
        hypotheses=h['hypotheses'], test=h['test'], decision=h['decision'], sensitivity=h['sensitivity'],
        state=STATE, event_years=EVENT_YEARS, calendar_years=CAL_YEARS, arms=ARMS, models=MODELS, parameter_selection=sel,
        cases=f'{len(ev)} event-window cases (union of +/-3-day windows, leads 1/7/14); {len(dropped)} dropped for a missing label',
        conventions=['first Diwali anchor = Maharashtra Laxmi Pujan (equals extended_validation.MAIN in 2020-2021)',
                     'weekend-listed festivals stay flagged', 'same Stage A cases rule, frames, regression and SARIMAX code'],
        hypothesis_sha256=sha(HYPOTHESIS),
        input_hashes={f: sha(ROOT/f) for f in INPUTS},
        design_hashes={'window_cases.csv': sha(out/'event_window'/'window_cases.csv'), 'primary_cases.csv': sha(out/'event_window'/'primary_cases.csv'),
                       '../anchors_2017_2021.csv': sha(out/'anchors_2017_2021.csv'), '../placebo_anchors_2017_2021.csv': sha(out/'placebo_anchors_2017_2021.csv')}))
    s = dict(event_cases=len(ev), dropped=len(dropped), by_year=ev.groupby('year').size().to_dict(),
             clusters=int(ev[['family', 'year']].drop_duplicates().shape[0]), unchecked_dry_run=bool(allow_unchecked))
    dump(out/'design_summary.json', s)
    print(json.dumps(s, indent=1, default=str))
    return s


def bound(dates):
    assert pd.Timestamp(min(dates)) >= pd.Timestamp('2017-01-01') and pd.Timestamp(max(dates)) <= pd.Timestamp('2021-12-31')


def selected(model_name, year):
    assert year in EVENT_YEARS
    return pd.read_csv(Path(str(OUT)+('_selection_ridge' if model_name == 'ridge' else '_selection_tree'))/'selected.csv')


def regression(engine, worker):
    """The registered Stage A regression, executed from its own source with only the two ledger file names changed."""
    import inspect
    src = inspect.getsource(A.regression)
    new = src.replace("'anchors_2020_2025.csv'", "'anchors_2017_2021.csv'").replace("'placebo_anchors_2020_2025.csv'", "'placebo_anchors_2017_2021.csv'")
    assert sum(a != b for a, b in zip(src.splitlines(), new.splitlines())) == 1 and len(src.splitlines()) == len(new.splitlines())
    ns = dict(vars(A)); ns.update(ARMS=ARMS, bound=bound, selected=selected)
    exec(compile(new, A.__file__, 'exec'), ns)
    return ns['regression'](engine, worker)


def run(worker):
    import breadth_model_engine_v1 as engine
    co = OUT/'event_window'
    a = pd.read_csv(OUT/'anchors_2017_2021.csv'); fake = pd.read_csv(OUT/'placebo_anchors_2017_2021.csv')
    for name in ['ridge', 'tree']:
        assert (Path(str(OUT)+f'_selection_{name}')/'selected.csv').exists(), 'run the 2019-2021 parameter selection first'
    engine.OUT = co; engine.ARMS = ARMS; engine.EXTRA = []; engine.ledger_bound = bound
    engine.frames = lambda index, state: A.frames(index, state, a, fake)
    A.ARMS = ARMS  # A.frames returns exactly these arms
    engine.sarimax() if worker == 'sarimax' else regression(engine, worker)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', *MODELS])
    p.add_argument('--allow-unchecked', action='store_true')
    p.add_argument('--out', default=str(OUT))
    args = p.parse_args()
    if args.allow_unchecked and Path(args.out).resolve() == OUT.resolve():
        raise SystemExit('Unchecked calendars may only be used for a dry run outside the registered folder')
    prepare(args.out, args.allow_unchecked) if args.action == 'prepare' else run(args.action)
