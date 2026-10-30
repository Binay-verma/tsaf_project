# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# TSFM India — completed research software and first evaluation

## What is finished

The package downloads/retains source data, audits it, creates causal historical inputs and calendar features, fits classical models, runs a pinned pretrained foundation model, scores forecasts and generates a self-contained HTML report. It includes setup and one-command execution, leakage tests, independent output verification, training diagnostics, per-case predictions, figures and source documentation.

Completed run: three states (Karnataka, Delhi, Maharashtra), two evaluation years (2022 development and 2023 held-out scoring), 28 forecast origins per state across both years, horizons 1/7/14 days, and 14 model/feature configurations. All 3,528 prediction rows had observed labels in this schedule. This is a **scheduled-origin experiment**, not a full daily benchmark.

Classical models were trained on 730 pre-2022 days. Chronos-2 used zero-shot inference with a pinned checkpoint; no foundation-model fine-tuning was performed or needed for this comparison. At later forecast origins, only past observations became available. Parameters and feature definitions were not adjusted after the 2023 results.

## Findings, including negative results

Macro MASE across the three states, 2023 scheduled origins (lower is better):

| Horizon | Chronos history only | Chronos + ordinary calendar | Chronos + holiday flag | Chronos + Diwali window |
|---|---:|---:|---:|---:|
| Day 1 | 0.4215 | 0.4290 | 0.4271 | 0.4198 |
| Day 7 | 1.0886 | 1.1800 | 1.1545 | 1.1610 |
| Day 14 | 1.1547 | 1.1717 | 1.1541 | 1.2109 |

Festival inputs do not consistently improve Chronos-2. Their tiny one-day aggregate difference does not establish a robust festival benefit; at longer horizons these inputs can worsen forecasts. Classical calendar regression improved at the one-day horizon but often performed poorly at longer horizons. All configurations, including worse ones, remain in the result tables.

MASE uses a fixed mean weekly seasonal error from the training period. MASE below one compares against that training scale, not necessarily against the seasonal-naive errors in the evaluation year. Read the actual baseline rows before claiming a model beats the baseline.

Training diagnostics show larger regression train/evaluation gaps at longer horizons. These gaps are retained rather than used to tune against the held-out results. They may reflect model overfitting, distribution shift, omitted variables or a combination; this experiment does not establish a unique cause. Do not describe the project as proven free of overfitting.

## Verification

- Six tests passed: future-target perturbation, causal fills, correct target-date calendar inputs, training-label isolation, verified main Diwali dates/windows and fixed-origin seasonal repetition.
- All twelve SARIMAX configurations converged.
- Independent output checks passed: unique predictions, finite forecasts, correct horizon dates, positive training scale, observed labels matching source and identical case coverage across configurations.
- Complete workflow rerun uses the pinned/cached Chronos forecasts with provenance checks; classical models are refit from the same data and configuration.

## How to run and inspect

Read START_HERE.md, then run `python setup_project.py` and `python run_all.py`. The result is `results/benchmark_original_s28/report.html`; it embeds the comparison figure for standalone viewing. Raw predictions and detailed metrics are next to it. `training_diagnostics.csv` compares training and evaluation regression errors. `paired_intervals.csv` contains descriptive moving-block intervals; these are not proof of general festival benefit.

The first full CPU run took approximately 486 seconds including model loading. Runtime varies by machine and whether weights are cached. A denser schedule is available with `--stride 7` but was not executed in this delivered evaluation. Data for newer years is included separately; no 2024–2026 performance is claimed.

## Boundaries of completion

The runnable research project and its declared first evaluation are complete. Publication-quality validation remains open: fully verified historical regional calendars, disclosed pretraining-cutoff/contamination checks, more independent festival years, denser origins, recent holdouts and possibly another Indian domain. The package does not claim a new forecasting architecture or a successful India-specific model improvement.

The current 2023 results have been examined. Any subsequent method tuning must use a different genuinely reserved evaluation period. No future work is silently scheduled, and no background training needs to remain running to inspect the delivered results.
