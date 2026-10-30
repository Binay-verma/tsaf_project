# Expanded validation: results and research status

**A functioning research prototype with a completed expanded evaluation; not a completed journal study.** This report supersedes the earlier pilot/scheduled-origin report for current status. No accuracy target was used to tune the reported fixed models. Negative results are retained. The LightGBM comparison is an explicitly exploratory addition after viewing 2026 outcomes, with its hyperparameters selected only on pre-2026 validation.

## Coverage and target

- Three states: Karnataka, Delhi and Maharashtra. Target: daily **electricity energy met/supplied in GWh**, not unconstrained demand or hourly peak power.
- Separate latest compilation snapshot through **2026-10-28**. It is not spliced into the earlier corrected source.
- Daily origins per state: 352 in 2022, 352 in 2023, 353 in 2024, 352 in 2025 and 288 in partial 2026: **1,697 total per state**, 5,091 state-origin tasks.
- Horizons 1, 7 and 14 are individual lead-day errors, not means of the whole next week/fortnight. Origin means first unseen date; lead h target is origin+h-1.
- **103,254 verified forecast rows** across models/configurations. These rows are not independent experiments or event replications.
- All-year evaluation: history-only Chronos, Ridge A/B/D and two naive methods. LightGBM A/B/D covers only 2026. Chronos calendar/festival modes and SARIMAX cover matched festival-origin cohorts only; they are not all-year scores.

## Partial 2026 daily comparison

Mean MASE across the three states; lower is better. Every configuration below has exactly 288 origins per state and horizon. Scale is the state's mean absolute weekly difference in the previous 730-day training window, calculated before 2026. A MASE above one is possible; compare methods on the same cases rather than treating one as an automatic pass/fail threshold.

| Model | Inputs | Day 1 | Day 7 | Day 14 |
| --- | --- | --- | --- | --- |
| chronos2 | A_history | 0.4679 | 1.1629 | 1.3617 |
| last_value | A_history | 0.6175 | 1.2576 | 1.5143 |
| lightgbm | A_history | 0.6702 | 1.2940 | 1.5927 |
| lightgbm | B_calendar | 0.6345 | 1.4652 | 1.9325 |
| lightgbm | D_regional_festival | 0.6345 | 1.4652 | 1.9325 |
| ridge | A_history | 0.6090 | 1.2714 | 1.4637 |
| ridge | B_calendar | 0.5785 | 1.6178 | 1.9781 |
| ridge | D_regional_festival | 0.5749 | 1.6205 | 1.9463 |
| seasonal_naive | A_history | 1.2285 | 1.2576 | 1.5143 |

Chronos history-only has the lowest macro MASE among these tested configurations at each lead. Relative to last-value persistence its error is approximately 24.2%, 7.5% and 10.1% lower at leads 1, 7 and 14. Its day-1 advantage over Ridge with regional festival training features is approximately 18.6%. These are descriptive aggregate comparisons, not significance claims or proof of universal superiority. Per-state/year scores are supplied, including weaker outcomes. The eight-configuration LightGBM search is limited and does not establish the strongest possible local model. B/D LightGBM predictions are identical here; rare binary indicators can be ignored under the selected tree constraints, and this partial 2026 cohort precedes Diwali.

## Festival comparison: four historical event years

The comparison below adds the declared regional festival channels D to ordinary calendar inputs B on **identical event-target cases**, for 2022–2025. The event set is a union of +/-3 days around main and separately documented regional Diwali dates. It is a broad Diwali period, not seven independent festivals. Positive percentages mean lower MAE; negative percentages mean worse MAE. Compute per-state/year relative MAE reductions, average states within year, then average the four years.

| Model | Horizon | Mean MAE reduction % | Year bootstrap low | Year bootstrap high |
| --- | --- | --- | --- | --- |
| chronos2 | 1 | -4.6230 | -6.9503 | -2.2957 |
| chronos2 | 7 | -0.5612 | -3.0160 | 2.9504 |
| chronos2 | 14 | -2.3167 | -5.9741 | 0.7559 |
| ridge | 1 | 22.0064 | 9.2244 | 31.8371 |
| ridge | 7 | 1.1017 | -63.4658 | 41.4639 |
| ridge | 14 | -16.8509 | -91.9483 | 30.6317 |
| sarimax | 1 | 24.2409 | 16.4699 | 29.6879 |
| sarimax | 7 | 13.0568 | -33.1446 | 47.5930 |
| sarimax | 14 | -4.0153 | -50.9930 | 31.0822 |

**Current festival encoding does not improve Chronos-2 on average.** It improves short-horizon Ridge and SARIMAX, with unstable longer-horizon effects. The percentile intervals resample only four annual clusters (2,000 replicates, seed 42); their precision is weak and they are descriptive, not strong generalisation or causal evidence. States and neighbouring days are correlated. LightGBM has no historical festival comparison in this checkpoint.

## Regional holiday audit

Twelve state-year annual government-office schedules were compared with the original default PUBLIC-category library dates. A mismatch can reflect category or amendment differences rather than a library defect. The complete date-level ledger and sources are included.

| state | year | schedule_unique_dates | library_dates | matched_dates | schedule_only | library_only |
| --- | --- | --- | --- | --- | --- | --- |
| Delhi | 2024 | 18 | 18 | 17 | 1 | 1 |
| Delhi | 2025 | 17 | 17 | 16 | 1 | 1 |
| Karnataka | 2024 | 24 | 22 | 16 | 8 | 6 |
| Karnataka | 2025 | 24 | 21 | 17 | 7 | 4 |
| Maharashtra | 2024 | 24 | 23 | 21 | 3 | 2 |
| Maharashtra | 2025 | 23 | 22 | 20 | 3 | 2 |
| Delhi | 2022 | 17 | 17 | 17 | 0 | 0 |
| Delhi | 2023 | 18 | 18 | 17 | 1 | 1 |
| Karnataka | 2022 | 22 | 21 | 16 | 6 | 5 |
| Karnataka | 2023 | 25 | 22 | 14 | 11 | 8 |
| Maharashtra | 2022 | 23 | 23 | 21 | 2 | 2 |
| Maharashtra | 2023 | 25 | 24 | 20 | 5 | 4 |

Annual-as-issued verification is completed for this scope. **Full amendment-aware verification remains incomplete**, including local/emergency/election and some moon-sighting changes and earlier training-year holidays. The expanded primary models therefore use ordinary calendar inputs plus explicit dated Diwali anchors; they do not use an uncertified general-holiday flag. See REGIONAL_CALENDAR_AUDIT.md.

## Pretraining-overlap evidence

The actual evaluated weight bytes match the first October 2025 uploaded weight object. The 2026 targets postdate those unchanged weights, conditional on correct source dates. Historical 2022–2025 sample/proxy overlap remains unresolved, and a corpus name search is not exhaustive numeric deduplication. **No post-upload Diwali result exists** in the current data. See PRETRAINING_AUDIT.md and its JSON evidence.

## Training, selection and verification

Ridge alpha 10 and SARIMAX orders were fixed, with annual fits on 730 preceding calendar days. History predictors use only preceding observations; lag warm-up can extend before the fitting-label window. Chronos is pretrained inference without task fine-tuning and uses a rolling 730-day context per origin, independent task attention. This differs from annual classical parameter refitting; more frequent local refits must be evaluated before architecture-level conclusions.

LightGBM used eight fixed configurations per state/mode/lead: leaves 7/15, estimators 100/300, lambda 1/10, learning rate .05 and minimum child samples 20. Its validation starts 2025-07-05 and ends in 2025, with training labels purged strictly before validation start. The best validation configuration is refitted on the pre-2026 730-day window. All 216 selection fits and 27 selected configurations are logged. No selection uses 2026 errors; the decision to add this baseline occurred after 2026 inspection, so the comparison is exploratory.

All 36 SARIMAX fits ultimately converged. One fit required a recorded Powell retry after L-BFGS failed; acceptance used training likelihood and convergence only. Original failed forecasts are retained. Eleven unit tests passed, including future-target perturbation and fitting checks. Independent result checks passed for unique cases, finite predictions, source labels, lead/date alignment, identical daily cases within each year, identical festival cases and pre-test LightGBM selection. These checks reduce specific errors; they do not guarantee zero mistakes.

Chronos cache reuse now checks source bytes, feature code, model settings, package versions and stored prediction hashes. This manifest was added after reviewing the completed run and is labelled as such; it is not falsely represented as a contemporaneous external preregistration.

## Practical limits and publication decision

The newer compilation's explicit redistribution licence and curator imputation/revision details remain unresolved; do not publish the bundled snapshot as a newly licensed open dataset. Source copies are study evidence, not a grant of reuse rights. No genuine real-time vintage reconstruction, weather-forecast availability experiment, calibrated interval evaluation, multiple-foundation-model replication or final untouched confirmation has been completed. Original and national SASEA derivatives are not independent sources.

**Worth continuing: yes. Journal-ready: no.** The most promising direction is controlled regional calendar provenance and event representation, with independent region/event transfer. Closely related literature already covers generic calendar encoding and learned event covariates, so adding flags alone is insufficient novelty. Read DEEP_RESEARCH.md and RESEARCH_REFERENCES.md for the reviewed prior work, experiment design, decision gates and realistic multiweek programme.

## Reproduce

Install with `python setup_project.py`, then run `python run_extended.py`. This checks the existing pinned snapshot and cached foundation forecasts, reruns classical fitting/selection, scoring and this report. Changing source/model/features requires a separate experiment directory rather than silently reusing caches. Downloaded foundation weights are not bundled. `python src/summarize_extended.py` and `python src/write_validation_report.py` regenerate reports from included predictions without rerunning training.
