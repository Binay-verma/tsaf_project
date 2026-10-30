# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# Latest status: completed scheduled-origin software benchmark

See FINAL_REPORT.md and START_HERE.md. Earlier entries below document the pilot and data-discovery stages and may describe tasks that have since been completed.

# Progress — 29 October 2026

## Completed

1. Located and downloaded an attributed CC BY 4.0 state-level source; verified its raw checksum.
2. Audited 3,955 rows: 3,900 unique dates between 2013-01-01 and 2024-04-28; 55 extra duplicate rows and 236 missing dates. Seven duplicate dates conflict in at least one pilot state.
3. Built reproducible daily observations for Karnataka, Delhi and Maharashtra; no imputed labels are scored.
4. Ran 7 baseline/feature-ablation configurations per state on 361 observed development dates in 2022.
5. All three SARIMAX fits converged. Independent checks passed for labels, forecast dates, naive predictions, score calculations and no final-holdout predictions.
6. Added an exploratory regional holiday calendar and fixed Diwali windows. These dates are not officially verified.

## First development results

MAE in GWh/day; smaller is better. These are regression feature comparisons, not foundation-model results.

| State | History only | Ordinary calendar | + Public holidays | + Diwali windows |
|---|---:|---:|---:|---:|
| Karnataka | 8.977 | 6.585 | 6.450 | 6.461 |
| Delhi | 4.311 | 3.642 | 3.511 | 3.485 |
| Maharashtra | 11.011 | 8.938 | 8.672 | 8.457 |

Calendar features improved the pilot regression overall in all three states. Diwali windows added to holiday flags improved overall MAE in Delhi and Maharashtra but slightly worsened Karnataka. Do not generalise from one development year.

## Foundation-model checkpoint

Chronos-2 successfully loaded and generated a history-only one-day Delhi forecast on CPU at origin 2022-10-24. Checkpoint revision: 29ec3766d36d6f73f0696f85560a422f50e8498c. Total smoke-test time: 38.1 seconds including load/download. This proves runtime feasibility, not comparative accuracy. Full evaluation and calendar ablations remain pending.

## Next execution order

1. DONE: Chronos-2 CPU/model-download access and one-origin smoke test.
2. Verify historical festival dates against official state calendars; resolve observed-vs-actual holidays and multi-day event definitions.
3. Implement matched SARIMAX covariate ablations and Chronos-2 A/B/C/D on the same origins and input context; choose context length using development data only.
4. Add 7/14-day fixed-origin forecasts with recursive or direct regression inputs; never use observed intermediate targets.
5. Freeze protocol, then evaluate untouched 2023 holdout; add further held-out years if obtainable.
6. Compute event/year-level robustness, paired block intervals and multi-state summaries; assess contamination and COVID sensitivity.
7. Expand benchmark scope and write the report after those checks.

## Deliberate method limits

Ridge alpha is fixed at 10, not tuned; calendar terms are weekday indicators and three annual Fourier harmonics. Regression fits on 2015–2021; SARIMAX uses 2020–2021 to keep this CPU pilot small, so their raw comparison is provisional. SARIMAX receives causally filled past targets during state updates. Add missing-input indicators and a gap-exclusion sensitivity test before final evaluation.

## Additional data discovery

See DATA_SOURCES.md. Downloaded and audited a newer state-level snapshot through 2026-10-28 and the SASEA archive. The latter does not extend the existing Indian dates and national totals match the original source. New snapshot is separate; no source switch or new holdout scoring was performed.
