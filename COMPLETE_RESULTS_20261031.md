# Completed research loop — 31 October 2026

All registered historical provider lanes and separate audits are complete. This does not close every journal gate. Outcomes are exploratory; more related forecast rows do not create independent events. The document-aligned, recentered Indian panel is the current main analysis. Original results and failures remain preserved.

## Corrected Indian festival windows

528 common target/lead cases across three related states, two years and five named families. Lower MASE is better. Lead 1 below; all eight arms and three leads remain in the source tables. Five substantive representations are displayed; zero and weekday-placebo controls are retained.

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | --- | --- | --- | --- | --- |
| Rich Ridge | 0.57699 | 0.45317 | 0.46093 | 0.57914 | 0.60838 |
| SARIMAX | 0.57301 | 0.42533 | 0.45345 | 0.57787 | 0.57511 |
| Stable LightGBM | 0.69865 | 0.69483 | 0.6611 | 0.70168 | 0.71233 |
| Tree leaf minimum 2 | 0.68582 | 0.64952 | 0.60469 | 0.69028 | 0.70001 |
| Chronos-2 | 0.53767 | 0.52009 | 0.51752 | 0.5372 | 0.53268 |
| TimesFM-3 | 0.55148 | 0.48005 | 0.42459 | 0.5554 | 0.55131 |

SARIMAX typed-day and TimesFM pooled-day are close here. No significance or universal winner follows. Typed/pooled contrasts match the five-channel event budget. Local and foundation adaptation/history policies differ, so model rankings are not architecture-only effects.

## Closest calendar-encoding adaptations

Every registered encoding on the same corrected Indian festival cases, all three leads. Target means use only preceding recorded context, never forecast labels. This daily adaptation differs from the closest paper's hourly experiment. Channel counts differ: one/two/three/eight versus 13 for calendar. The smallest displayed value is not a selected recommendation or proof of equal-information superiority.

| arm | chronos lead 1 | chronos lead 7 | chronos lead 14 | timesfm lead 1 | timesfm lead 7 | timesfm lead 14 |
| --- | --- | --- | --- | --- | --- | --- |
| history | 0.54769 | 0.89998 | 0.98812 | 0.55366 | 0.94413 | 1.032 |
| zero1 | 0.55892 | 0.94868 | 1.01507 | 0.55616 | 0.93951 | 1.04637 |
| ordinal | 0.51574 | 0.92318 | 1.00782 | 0.42608 | 0.82169 | 0.91444 |
| onehot | 0.51171 | 0.91878 | 1.00093 | 0.43188 | 0.83503 | 0.89914 |
| cyclic | 0.51636 | 0.91933 | 1.00031 | 0.45004 | 0.82605 | 0.90781 |
| te_weekday | 0.56433 | 0.94589 | 1.01264 | 0.55172 | 0.92713 | 1.02822 |
| te_sunday | 0.51563 | 0.8827 | 0.98085 | 0.42528 | 0.82821 | 0.90999 |
| te_holiday | 0.524 | 0.89404 | 0.98684 | 0.3984 | 0.80448 | 0.90374 |
| te_joint | 0.53781 | 0.9173 | 1.00568 | 0.4447 | 0.87412 | 0.9749 |
| te_separate | 0.52832 | 0.91284 | 1.00149 | 0.41227 | 0.81544 | 0.9247 |
| calendar | 0.53767 | 0.89117 | 0.95427 | 0.55148 | 0.88972 | 0.96819 |

## Independent-source NYC holidays

Two occurrences and two related transit modes in one city, 84 event cases. Decision lead 1 uses actual model step 8 under the seven-day observation buffer. Units are million estimated rides. Cross-dataset MASE levels do not imply equal task difficulty.

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | --- | --- | --- | --- | --- |
| Rich Ridge | 0.99718 | 1.00451 | 1.16887 | 1.19074 | 1.31328 |
| SARIMAX | 0.99947 | 0.79417 | 1.04067 | 1.1525 | 1.40939 |
| Stable LightGBM | 0.9194 | 0.9194 | 0.9194 | 0.9194 | 1.08484 |
| Tree leaf minimum 2 | 0.84819 | 0.8461 | 0.87819 | 0.88083 | 1.02851 |
| Chronos-2 | 0.93276 | 0.86384 | 0.76003 | 0.93928 | 0.92961 |
| TimesFM-3 | 0.88394 | 0.75636 | 0.79143 | 0.86121 | 0.91833 |

Chronos benefits from pooled-day flags here, while TimesFM favours typed-day flags and SARIMAX pooling worsens its calendar baseline. All leads, ordinary cases and controls are retained. This is revised-vintage retrospective evidence, not independent-city or prospective confirmation.

## Different electricity source and availability sensitivity

NESO ordinary September targets at decision lead 1: ideal actual model step 1 versus lag-21 actual model step 22. No holiday targets occur. Delay need not monotonically worsen realised error in this small sample; regressions also change lead-dependent features/fits.

| Model | Ideal | Lag 21 |
| --- | --- | --- |
| Rich Ridge | 0.48703 | 0.50152 |
| SARIMAX | 0.4808 | 0.46981 |
| Stable LightGBM | 0.53385 | 0.46448 |
| Tree leaf minimum 2 | 0.55685 | 0.47201 |
| Chronos-2 | 0.53605 | 0.5917 |
| TimesFM-3 | 0.45629 | 0.38886 |

## Prespecified past-support diagnostics

The analysis reuses 6,336 typed-minus-pooled case contrasts, 864 family/state/year/lead cells and 1,728 descriptive association records. The table is the declared day/lead-1/all-scope slice; all other scopes are retained. Positive forecast contrasts favour pooling. The 24 available cells are not independent replications. Mixed residual-response associations do not establish a general mechanism or causal effect.

| Model | Support rho | Support n | Response rho | Response n |
| --- | --- | --- | --- | --- |
| Rich Ridge | 0.05912 | 24 | 0.15478 | 24 |
| SARIMAX | 0.46684 | 24 | 0.12087 | 24 |
| Stable LightGBM | 0.3097 | 24 | 0.01451 | 24 |
| Tree leaf minimum 2 | 0.37794 | 24 | 0.08 | 24 |
| Chronos-2 | -0.04204 | 24 | 0.17391 | 24 |
| TimesFM-3 | 0.10992 | 24 | -0.02174 | 24 |

## Completed checks and preserved limitations

- Original breadth: 35,712 forecasts. Pure encodings: 14,880 fresh forecasts plus 1,488 reused calendar references. Composed/corrected views are not independent new data.
- Source correction changes one Karnataka named date. Recentring replaces three lead cases for one target date, not three target dates. All 1,092 fresh recenter forecasts and full contrasts pass audit.
- NESO: 4,608 model plus 192 naive rows. NYC: 6,300 model plus 252 naive rows; source/input/calendar/native/scalar audits pass.
- Clean internal runs reproduce all 4,032 NYC local forecasts and 72 validation MAEs exactly, plus comparator/simulation outputs. Same machine; no independent human or complete foundation reimplementation.
- Earlier float64-tree reproduction failure, near-zero float32 feature discrepancy, calendar preflight/interrupted-report/dispatch/schema failures remain preserved. Repairs did not select new cases, parameters, metrics or tolerances using errors.
- New Chronos future competitor: 84 stored/66 eligible full 1–11 November forecasts, actual completion 31 October 05:14:07 IST. First public commit `0e4ab330d6a798545f31476f79c59f55975eb8e3` and observed remote receipt precede eligible dates. No future accuracy exists. Same source/episode/stale context as the older freeze; no festival-feature confirmation.
- Old future and interval blobs are immutable. Manual date/vintage guards and paused automation remain in force. No future actuals were retrieved.

## Next loop and open gates

1. Publish completed artifacts and the integrated review draft after numerical/all-page visual checks. Historical computations above are finished; do not restart them to seek better scores.
2. Complete manual rolling-confirmation source/runner/scorer software and fixtures using its fixed availability bridge and first-commit/time guards. The 52-week study is unactivated; do not issue fake or early forecasts.
3. Verify primary 2026–2027 calendar coverage/amendments before future festival-feature issuance. Secondary pages/failed retrievals do not close this gate. MH2022 retained-excerpt evidence remains incomplete.
4. Obtain real independent scientific review and source-use/report-day clarification. The author is not the independent reviewer; no permission or sign-off is inferred.
5. Wait for actual outcomes, then score every issued configuration on the original first complete actual vintage. Repeated untouched events, rather than one episode or more models, are needed for stronger confirmation.

The proposed contribution is a conditional empirical forecasting lesson, not a new architecture, causal effect, contamination-free claim or IJF acceptance assurance. Exact impact-driven learned-event replication remains unresolved because full settings/code/account-profile data were not identified in examined sources. Author affiliation/email remain blank as requested.

Sources: [integrated draft](manuscript/integrated_review_v4/MANUSCRIPT.md), [corrected breadth](results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv), [corrected pure encodings](results/calendar_recenter_recovery_v1/analysis/encoding/event_window/metrics_balanced.csv), [NYC](results/mta_holiday_recovery_v1/analysis/event_window/metrics_balanced.csv), [NESO](results/neso_replication_v1/analysis/metrics.csv), [all diagnostics](results/event_support_v1/associations.csv).
