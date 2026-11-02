# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# Build completed: see FINAL_REPORT.md

The runnable pipeline, matched model/feature comparisons, three horizons, diagnostics and results report are implemented. Broader scientific validation remains a limitation rather than a claimed completed finding.

# TSFM India: execution plan

Owner: Binay Verma. Started 29 October 2026.

## Research question
Does India-specific festival information improve forecasting of state-level daily electricity supplied, beyond ordinary calendar inputs, for classical models and pretrained time-series models?

## Scope and staged checkpoints
1. **Find data:** compare open sources; download immutable raw files; preserve DOI, authors, licence and checksum. Prefer multiple states and several annual cycles.
2. **Understand data:** audit date coverage, duplicate conflicts, missing dates, units and anomalies; plot trends and weekly seasonality. Stop silent cleaning; record every policy.
3. **Build baseline pipeline:** weekly seasonal naive and lag regression; add SARIMAX. Keep all preprocessing causal. Evaluate 1-day forecasts first, then fixed-origin 7- and 14-day forecasts.
4. **Verify baseline pipeline:** check time ordering, lag availability, no test-target use and metric calculations; save per-date predictions, runtime and software versions.
5. **Add calendar and festival inputs:** compare A history only, B history + weekday/annual calendar, C B + state holiday flags, D C + named festival windows. Freeze window choices using validation only. Audit library dates against official state notifications; unverified dates remain exploratory.
6. **Run foundation model:** Chronos-2 A/B/C/D on identical origins, horizons and context; record checkpoint revision and inference cost. Run small CPU smoke test before scaling; use GPU only if available, without purchasing compute.
7. **Strengthen evaluation:** overall/festival/nonfestival MAE and training-scaled weekly MASE; per-state and per-horizon results; block bootstrap paired differences and event/year robustness. Overlapping festival windows use an explicit priority/overlap policy. Do not treat days as independent festival replications.
8. **Extend evidence:** add states first, optionally another Indian domain later. Seek recent observations after disclosed checkpoint training periods; otherwise label contamination unknown. Include COVID sensitivity and weather-aware comparisons only with forecast-available weather.
9. **Deliver:** reproducible project archive, data dictionary, figures, experiment tables, limitations and paper draft. Claim improvements only if measured; recheck novelty before manuscript.

## Frozen initial protocol
- Pilot states: Karnataka, Delhi, Maharashtra; no selection using forecast performance.
- Target: energy met in MU = GWh per day, NOT unconstrained demand or instantaneous MW.
- Raw source: Hunt & Bloomfield, Zenodo DOI 10.5281/zenodo.14983362 (CC BY 4.0).
- Initial training: 2015–2021; validation: full 2022; final holdout: full 2023. 2024 is incomplete and reserved for sensitivity. Final holdout is not scored during pipeline development.
- One-day rolling forecasts: previous observed targets become available at each next origin. No using targets inside a fixed-origin multi-day forecast.
- Weekly MASE denominator fixed from observed training pairs exactly 7 calendar days apart.
- Duplicate conflicts: mark conflicting state/date values missing, never choose last record arbitrarily. Identical duplicates collapse. Reindex daily; preserve observed flags. Seasonal causal imputation is for inputs only; never score imputed labels.
- Data quality thresholds: report completeness by year and selected state; inspect long gaps; exclude invalid forecast labels and report coverage. Any changes before holdout evaluation go into this file.

## Completion status
- Data located and raw download completed; actual coverage differs from catalogue title.
- Audit, seven baseline/feature configurations per state, development scoring and independent checks completed.
- History-only SARIMAX and Chronos-2 CPU smoke test completed. Verified regional festival calendars, matched covariate SARIMAX/Chronos-2 evaluation and final holdout remain pending until prerequisites pass.

## Source shortlist
- Selected: https://zenodo.org/records/14983362 — state daily energy met, multi-year, explicit reuse licence and source QC.
- Alternative: https://data.mendeley.com/datasets/y58jknpgs8/2 — hourly national aggregate; title/description coverage differs, inspect bytes before use.
- Karnataka short SLDC dataset in survey: insufficient annual cycles for the main festival question.

## Main risks
Unknown foundation-model pretraining overlap; retrospective source corrections; historical holiday-date inaccuracies; state-level heterogeneity; only a few held-out festival occurrences. This pilot is not a proven leakage-free benchmark and does not establish causal festival effects.
