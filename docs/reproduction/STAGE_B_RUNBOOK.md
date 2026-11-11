# Stage B runbook (Maharashtra, event years 2019-2021)

Confirmatory test of `results/model_class_hypothesis_v1/registration.json`. Run in this order, from the repository root.
Nothing below may start until all 18 Maharashtra rows for 2017-2019 in
`review/longer_panel_v1/calendar_entries_2014_2021.csv` carry `checked_by` and `check_date`.

1. Tests: `cd src && python -m pytest -q test_longer_panel_stage_b_v1.py && cd ..`
2. Register: `python src/longer_panel_stage_b_v1.py prepare` — writes the ledgers, 327 event-window cases
   (expected; 0 dropped), the protocol carrying the hypothesis hash, and the two selection folders with
   `protected_before.json`. Commit and push before step 3.
3. Parameter selection (ordinary calendar only, unchanged procedures):
   `python src/robust_baselines.py --out results/longer_panel_stage_b_v1_selection_ridge`
   `python src/stable_tree_refit.py --out results/longer_panel_stage_b_v1_selection_tree`
   Commit.
4. Forecasts: `python src/longer_panel_stage_b_v1.py ridge` (then `lightgbm`, `lightgbm_capacity2`, `sarimax`). Commit.
5. Analysis: `python src/longer_panel_analysis_stage_b_v1.py` — writes `analysis/hypothesis_tests.csv`,
   `sensitivity_without_2020.csv`, `balanced.csv`, `summary.json`. Commit whatever the decision is.

Conventions fixed before any outcome: the first Diwali anchor is Maharashtra's listed Laxmi Pujan date; the
regression is executed from the registered Stage A source with only its two ledger file names changed (checked by a
test); the decision rule, test and sensitivity are copied from the hypothesis registration.
