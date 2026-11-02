# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# Experiment integrity

The experiment reports all configurations, including those that perform worse. No model, forecast origin or reported state was removed based on test error.

- Fixed ridge regularisation alpha = 10; no hyperparameter search or test-driven tuning.
- Same declared train period and initial context length across classical configurations: last 730 pre-2022 days.
- Fixed SARIMAX orders (1,0,0) with seasonal (1,0,0,7); no test-driven order selection.
- Chronos-2 uses a pinned pretrained revision, inference only; no local fine-tuning or target-label training.
- 2022 is development; 2023 was first scored after fixing this build's models, feature definitions and forecast schedule. Now that its results are visible, future method changes must treat 2023 as previously examined evaluation data, not a fresh untouched test set.
- Forecast schedule is fixed independently of outcomes: every 28 days plus one main-Diwali-minus-three-days origin per year. This intentionally samples festival periods and is not a prevalence-weighted full-year daily assessment.
- Report all 14 configurations across each state and 1/7/14-day horizon.
- Future-target perturbation tests verify that origin features do not depend on future targets and regression fitting does not consume post-2021 labels.
- Observed historical values may enter later forecast origins; no observed intermediate values enter a fixed-origin 14-day forecast.
- Missing evaluation labels are excluded, never replaced with imputed labels. Prediction coverage is checked across models before scoring.
- Code/data fingerprints guard against reusing caches after input or code changes.
- Training diagnostics report in-sample regression error alongside evaluation error, without using those gaps to tune this test run. A small gap does not prove absence of overfitting; a large gap can also reflect distribution shift or missing explanatory variables.

Limitations retained: partially verified historical calendars, possible model pretraining overlap, retrospective data corrections, only one main Diwali per evaluation year and a sparse origin schedule. Descriptive intervals are not evidence of general festival benefit. There is no promise of positive results or publication readiness.
