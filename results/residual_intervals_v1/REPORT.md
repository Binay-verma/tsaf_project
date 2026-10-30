# Past-only residual interval baseline v1

Completed exploratory study, 30 October 2026. This is a separately recorded protocol written before interval outcomes, after historical point scores were known. No final untouched outcomes were used and no calibration settings were selected on these results.

25,380 interval forecasts cover four point-model configurations, three states, leads 1/7/14 and 2024–2025. Each configuration has 6,345 identical cases. At every origin, calibration uses signed errors from out-of-sample forecasts with TARGET dates in the preceding 730 calendar days and strictly before that origin. Minimum actual calibration size is 704. Future-target residuals are excluded even if their forecast origin is in the past. Quantiles 0.05/0.5/0.95 are point forecasts plus the corresponding residual quantiles. Original point predictions are never overwritten. Three calibration tests pass; persisted-output audit reconstructs first/event-origin quantiles and interval scores independently.

These are **retrospective residual-calibrated intervals**, not recovered native model quantiles. Chronos inference was not rerun. There is no exchangeability or finite-sample coverage guarantee for these dependent time series. Model refits and source revisions may change error distributions.

## Equal state/year weighted results

Nominal central coverage is 90%. Interval scores penalize both width and misses and are divided by the pre-year weekly-difference scale; lower is better. Event counts and per-state/year results are in `metrics_state_year.csv`. Event days/states are not independent trials.

| Model / inputs | Lead | Scope | Coverage % | Scaled width | Scaled interval score |
| --- | ---: | --- | ---: | ---: | ---: |
| chronos2 / A_history | 1 | all | 89.74 | 1.6868 | 2.5539 |
| chronos2 / A_history | 1 | event | 77.25 | 1.7046 | 3.5773 |
| chronos2 / A_history | 7 | all | 90.40 | 4.3223 | 5.4438 |
| chronos2 / A_history | 7 | event | 88.89 | 4.3529 | 5.2761 |
| chronos2 / A_history | 14 | all | 90.68 | 5.0952 | 6.5347 |
| chronos2 / A_history | 14 | event | 94.44 | 5.1467 | 5.8248 |
| last_value / A_history | 1 | all | 89.27 | 2.2578 | 3.1001 |
| last_value / A_history | 1 | event | 82.80 | 2.2707 | 3.8115 |
| last_value / A_history | 7 | all | 90.54 | 4.7740 | 5.9877 |
| last_value / A_history | 7 | event | 88.89 | 4.7816 | 5.6732 |
| last_value / A_history | 14 | all | 89.93 | 5.8738 | 7.5315 |
| last_value / A_history | 14 | event | 80.69 | 5.8368 | 7.4749 |
| ridge / B_calendar | 1 | all | 90.02 | 1.7490 | 2.5608 |
| ridge / B_calendar | 1 | event | 78.57 | 1.7601 | 3.8912 |
| ridge / B_calendar | 7 | all | 91.35 | 4.5616 | 5.6563 |
| ridge / B_calendar | 7 | event | 83.33 | 4.4696 | 6.0403 |
| ridge / B_calendar | 14 | all | 90.64 | 5.2784 | 6.8344 |
| ridge / B_calendar | 14 | event | 81.75 | 5.1965 | 6.7357 |
| ridge / D_regional_festival | 1 | all | 90.17 | 1.7314 | 2.5324 |
| ridge / D_regional_festival | 1 | event | 87.04 | 1.7390 | 2.7450 |
| ridge / D_regional_festival | 7 | all | 91.21 | 4.4772 | 5.6621 |
| ridge / D_regional_festival | 7 | event | 87.04 | 4.3775 | 7.4967 |
| ridge / D_regional_festival | 14 | all | 90.50 | 5.2864 | 6.9010 |
| ridge / D_regional_festival | 14 | event | 81.22 | 5.1700 | 7.5824 |

## Interpretation

Chronos history-only day-1 intervals reach 89.74% average all-day coverage but only 77.25% during the fixed festival windows, below the nominal 90%. Therefore all-day calibration can conceal event-specific undercoverage. Regional Ridge day-1 event coverage is 87.04%, also below nominal; this is not evidence of a universally calibrated superior model. Coverage alone cannot rank forecasts without width and interval score. Other leads and per-year/state failures remain reported.

No interval method, calibration window or festival correction was retuned after this inspection. Native TSFM quantiles, event-conditional calibration with adequate prior event evidence, more independent events, and fresh confirmation remain open. Do not train an event-specific calibrator on these evaluated outcomes and call its score a clean test.

## Reproduction

`.venv/bin/python src/test_residual_intervals.py` checks the calibration boundaries. `.venv/bin/python src/audit_new_experiments.py` audits persisted outputs. `src/residual_intervals.py` refuses to overwrite the completed predictions. A new run requires a separately versioned output/protocol and explicit code path update; preserve this experiment.
