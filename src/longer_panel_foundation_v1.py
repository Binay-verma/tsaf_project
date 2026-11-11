"""Longer panel, Stage A extension: Chronos-2 and TimesFM-3 on the two new event years 2022-2023.

Exploratory (the registered model-class hypothesis concerns local models only). Same Stage A cases, ledgers
(results/longer_panel_stage_a_v1/anchors_2020_2025.csv and placebos), eight arms, 730-day context, 14-day
horizon, pinned weights, threads, seed and batch as the parent breadth study. For 2024-2025 the stored
document-aligned foundation forecasts are used; a reproduction cohort re-forecasts 2024 event-window cases
for three reference arms and must match them within the parent's tolerance (rtol 2e-4, atol 1e-3 GWh).

Colab steps (docs/reproduction/LONGER_PANEL_FOUNDATION_COLAB.md):
  python src/longer_panel_foundation_v1.py weights
  python src/longer_panel_foundation_v1.py chronos --cohort reproduce_2024   (then event_2022_2023, ordinary_2022_2023; then timesfm)
  python src/longer_panel_foundation_analysis_v1.py
"""
import argparse
import json
from datetime import datetime, timezone
import pandas as pd
from forecasting import ROOT
from festival_feature_design import sha, dump
import longer_panel_stage_a_v1 as A
import ziel_foundation_v1 as zf

OUT = ROOT/'results/longer_panel_foundation_v1'
STAGE_A = ROOT/'results/longer_panel_stage_a_v1'
MODELS = ['chronos', 'timesfm']
ALL_ARMS = list(A.ARMS)
REFERENCE_ARMS = ['calendar', 'day5', 'pooled_day5']
COHORTS = {'reproduce_2024': ('event_window', [2024], REFERENCE_ARMS),
           'event_2022_2023': ('event_window', [2022, 2023], ALL_ARMS),
           'ordinary_2022_2023': ('ordinary', [2022, 2023], ALL_ARMS)}
INPUTS = ['src/longer_panel_foundation_v1.py', 'src/longer_panel_foundation_analysis_v1.py', 'src/test_longer_panel_foundation_v1.py',
          'src/longer_panel_stage_a_v1.py', 'src/longer_panel_analysis_stage_a_v1.py', 'src/ziel_foundation_v1.py',
          'src/breadth_model_engine_v1.py', 'src/extended_validation.py', 'src/festival_feature_design.py', 'src/forecasting.py',
          'data/external/latest_state_energy_GWh.csv',
          'results/longer_panel_stage_a_v1/anchors_2020_2025.csv', 'results/longer_panel_stage_a_v1/placebo_anchors_2020_2025.csv',
          'results/longer_panel_stage_a_v1/event_window/primary_cases.csv', 'results/longer_panel_stage_a_v1/ordinary/primary_cases.csv',
          'results/mechanism_controls_v1/chronos_download.json', 'results/second_model_audit_v1/weight_download.json',
          'results/feature_breadth_v1/event_window/protocol.json',
          'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv',
          'results/calendar_recenter_recovery_v1/analysis/breadth/ordinary/predictions_compared.csv']


def cohort_cases(cohort):
    source, years, _ = COHORTS[cohort]
    c = pd.read_csv(STAGE_A/source/'primary_cases.csv')
    return c[c.year.isin(years)][['family', 'state', 'year', 'date', 'horizon', 'origin']].reset_index(drop=True)


def prepare():
    if OUT.exists():
        raise FileExistsError('Preserve the registered protocol; create a new version')
    OUT.mkdir()
    parent = json.loads((ROOT/'results/feature_breadth_v1/event_window/protocol.json').read_text())
    protocols = {}
    for cohort, (source, years, arms) in COHORTS.items():
        out = OUT/cohort; out.mkdir()
        cases = cohort_cases(cohort)
        for name in ['primary_cases.csv', 'window_cases.csv']:
            cases.to_csv(out/name, index=False)
        p = dict(experiment=f'{OUT.name}/{cohort}', created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma',
            status=('Exploratory extension of results/longer_panel_stage_a_v1 to the foundation models. Registered and committed before '
                    'any forecast of this study existed; local-model Stage A results and the stored 2024-2025 foundation forecasts were already inspected. '
                    'To be run by the author in Google Colab.'),
            source_cohort=source, years=years, arms=arms, models=MODELS,
            threads=parent['threads'], seed=parent['seed'], batch=parent['batch'], expected_tasks=int(len(cases[['state', 'year', 'origin']].drop_duplicates())),
            weights=dict(chronos_revision=zf.CHRONOS_REV, timesfm_revision=zf.TIMESFM_REV, timesfm_code_revision=zf.TIMESFM_CODE),
            reproduction_check=('reproduce_2024 predictions must match the stored document_aligned foundation predictions within rtol 2e-4, atol 1e-3 GWh. '
                                'If they do not, the failure is reported and the 2022-2023 forecasts are not combined with stored 2024-2025 ones.'),
            analysis=('As results/longer_panel_stage_a_v1 (row MASE, fixed pre-year scale, family-year-state balanced hierarchy, 20 family-year clusters, '
                      'exact two-sided sign-flip, Holm over the four lead-1 cells, supported = Holm < 0.05 and same sign in >= 3 of 4 years). '
                      'Exploratory: no confirmatory claim; the registered model-class hypothesis concerns local models.'),
            input_hashes={f: sha(ROOT/f) for f in INPUTS},
            design_hashes={name: sha(out/name) for name in ['primary_cases.csv', 'window_cases.csv']})
        dump(out/'protocol.json', p)
        protocols[cohort] = sha(out/'protocol.json')
    dump(OUT/'registration.json', dict(created_utc=datetime.now(timezone.utc).isoformat(), author='Binay Verma', protocols=protocols,
        statement='Protocol fixed before any forecast of this study was produced. Commit before running.'))


def run(cohort, worker):
    reg = json.loads((OUT/'registration.json').read_text())
    assert sha(OUT/cohort/'protocol.json') == reg['protocols'][cohort]
    import breadth_model_engine_v1 as engine
    arms = COHORTS[cohort][2]
    a = pd.read_csv(STAGE_A/'anchors_2020_2025.csv'); fake = pd.read_csv(STAGE_A/'placebo_anchors_2020_2025.csv')
    A.ARMS = ALL_ARMS
    zf.OUT = OUT; zf.ARMS = arms
    zf.frames = lambda index, state: {k: v for k, v in A.frames(index, state, a, fake).items() if k in arms}
    engine.OUT = OUT/cohort; engine.ARMS = arms; engine.EXTRA = []; engine.ledger_bound = A.bound
    zf.foundation(engine, worker)


def weights():
    zf.OUT = OUT
    zf.weights()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'weights', *MODELS])
    p.add_argument('--cohort', choices=list(COHORTS), default='reproduce_2024')
    args = p.parse_args()
    {'prepare': prepare, 'weights': weights}.get(args.action, lambda: run(args.cohort, args.action))()
