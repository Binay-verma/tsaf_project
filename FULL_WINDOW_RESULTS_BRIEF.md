# Complete original-calendar festival-window results

Audited 31 October 2026, India time. All 25,344 existing forecasts are complete: 528 matched cases × six variants × eight arms, covering model leads 1/7/14, five families, three scoped states and two event years. Lower MASE is better; this is not percentage accuracy. Ordinary-day and corrected-calendar foundation panels remain pending.

**Calendar limitation:** the original Karnataka 2025 Dussehra flag uses 2 October; the retained notification names 1 October. Flag, window and weekday-control corrections have separate registrations. Maharashtra 2022 Gudi Padwa has an evidence gap, not proof of a wrong date. These tables are not the corrected final comparison.

## Model lead 1

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | --- | --- | --- | --- | --- |
| Ridge | 0.57813 | 0.45554 | 0.46207 | 0.58003 | 0.60952 |
| SARIMAX | 0.57478 | 0.41872 | 0.45079 | 0.57953 | 0.57689 |
| Stable LightGBM | 0.70086 | 0.69704 | 0.66331 | 0.70389 | 0.71454 |
| Leaf-2 tree | 0.68830 | 0.65121 | 0.60662 | 0.69270 | 0.70249 |
| Chronos-2 | 0.53897 | 0.52074 | 0.51821 | 0.53678 | 0.53291 |
| TimesFM-3 | 0.55002 | 0.47891 | 0.42256 | 0.55369 | 0.54953 |

## Model lead 7

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | --- | --- | --- | --- | --- |
| Ridge | 0.98672 | 0.92343 | 0.92903 | 1.05177 | 1.08817 |
| SARIMAX | 0.96411 | 0.90788 | 0.90769 | 0.96615 | 0.97697 |
| Stable LightGBM | 1.03775 | 1.03775 | 0.99718 | 1.02515 | 1.05709 |
| Leaf-2 tree | 1.06277 | 1.03159 | 0.99133 | 1.06984 | 1.07481 |
| Chronos-2 | 0.89199 | 0.91135 | 0.88820 | 0.91049 | 0.89251 |
| TimesFM-3 | 0.88898 | 0.79464 | 0.77696 | 0.90889 | 0.90445 |

## Model lead 14

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | --- | --- | --- | --- | --- |
| Ridge | 1.10076 | 1.03816 | 1.04280 | 1.18585 | 1.19292 |
| SARIMAX | 1.14190 | 1.07725 | 1.08324 | 1.14715 | 1.15146 |
| Stable LightGBM | 1.37246 | 1.37246 | 1.33859 | 1.37456 | 1.36843 |
| Leaf-2 tree | 1.45189 | 1.45127 | 1.40222 | 1.45480 | 1.46870 |
| Chronos-2 | 0.94949 | 0.95524 | 0.94828 | 0.96537 | 0.96108 |
| TimesFM-3 | 0.96230 | 0.92357 | 0.86802 | 0.95476 | 0.97561 |

At lead 1, SARIMAX with typed-day features (0.41872) and TimesFM with pooled-day features (0.42256) have lower MASE on this cohort than Chronos with pooled-day features (0.51821). Chronos with calendar features (0.53897) is another configuration. These are descriptive differences: the small event-year sample, correlated rows, different adaptation policies and total history budgets prevent a significance or universal-superiority claim. Do not select future arms from these errors.

Every zero-channel and weekday-placebo control, state/year/family comparison, leave-family-out contrast and native coverage/width/pinball/WIS table remains in the checkpoint. The separate audit reconstructs 7,520 foundation input tasks, local parameter/label/support/cutoff contracts, point and probability aggregates, and 1,023 protected prior files. Chronos's 42 native quantile crossing pairs remain visible; TimesFM has zero. This is internal software review, not independent human validation.

The first audit failed because a protected review brief had been updated. Its original bytes are restored; new guidance is in `review/INDEPENDENT_REVIEW_UPDATE_20261031.md`. The original failure is retained. A new directory-only recovery preserves all 32 scientific CSV files byte-for-byte, with unchanged scoring/audit source and tolerances. No inference or result was overwritten.

Read `results/feature_breadth_event_checkpoint_recovery_v1/README.md` and its `independent_audit.json`. The original full 35,712-forecast study continues separately; this checkpoint neither replaces it nor includes missing ordinary-day or corrected-calendar outputs.
