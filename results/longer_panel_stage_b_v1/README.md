# Stage B: confirmatory test of the model-class hypothesis (Maharashtra, 2019-2021)

The hypothesis (`results/model_class_hypothesis_v1`, commit dec1274) was fixed before any Stage B data existed. The
Stage B protocol (commit 65d1880) was fixed before any parameter selection or forecast. The data are 327 event-window cases,
15 family-year clusters, five arms and four local models. The analysis is `src/longer_panel_analysis_stage_b_v1.py`, run once.

## Registered decisions (lead 1, typed-day minus pooled-day MASE; exact one-sided sign-flip test over 15 clusters)

| Hypothesis | Model | Expected | Typed − pooled | 2019 / 2020 / 2021 | One-sided p | Holm | Decision |
|---|---|---|---|---|---|---|---|
| H1 | Stable LightGBM | + | 0.0000 | 0 / 0 / 0 | 1.00 | 1.00 | NOT CONFIRMED |
| H2 | SARIMAX | − | −0.0539 | −0.089 / −0.017 / −0.056 | 0.015 | 0.031 | **CONFIRMED** |
| H1b (secondary, no adjustment) | Leaf-2 LightGBM | + | +0.0648 | −0.008 / +0.074 / +0.128 | 0.020 | — | CONFIRMED |

Pre-declared sensitivity without 2020: H2 is still CONFIRMED. H1 is NOT CONFIRMED. H1b is NOT CONFIRMED (2019 is against it).

H3 (ridge, reported, not tested) gives typed − pooled = −0.034, with 2 of 3 years negative. In Maharashtra the linear
model also prefers typed flags. In Stage A, ridge showed no ordering.

## Why H1 is an exact zero (an uninformative test, not evidence against H1)

At lead 1, the pre-year selection chose `min_child_samples = 20` for the stable LightGBM in all three Stage B years.
Over a 730-day training window, a typed day flag has at most 4 ones, and the pooled flag about 12. Neither reaches 20
samples in a leaf, so no tree splits on any festival flag. The day5, pooled_day5, zero5, placebo_day5 and calendar
forecasts are therefore identical at lead 1 (balanced MASE 0.9814 for all five). Stage A's 2024 exact tie has the same
cause. This mechanism could have been anticipated from that tie. It was not written into the registration, so the
registered decision stands as NOT CONFIRMED.

When leaves may hold 2 samples (leaf-2 LightGBM), the flags are used and pooling is better in 2 of 3 years (H1b).

## Controls (lead 1, balanced MASE)

The zero5 and placebo_day5 arms equal the calendar arm to within 0.0006 for every model, so the effects come from
the real festival dates.

| Model | calendar | zero5 | placebo_day5 | day5 | pooled_day5 |
|---|---|---|---|---|---|
| Ridge | 0.7242 | 0.7242 | 0.7236 | 0.5541 | 0.5876 |
| SARIMAX | 0.7316 | 0.7316 | 0.7311 | 0.5339 | 0.5879 |
| LightGBM (stable) | 0.9814 | 0.9814 | 0.9814 | 0.9814 | 0.9814 |
| LightGBM (leaf 2) | 0.9871 | 0.9871 | 0.9869 | 0.9820 | 0.9172 |

## Process notes

- `../longer_panel_stage_b_v1_selection_ridge/NOTE_RUN_JSON.md`: an import failure at the first attempt; `run.json` was
  not written because of a relative path. Integrity was re-checked.
- `event_window/NOTE_LAUNCH.md`: two workers did not start on the first launch.
- Packages: numpy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0, lightgbm 4.7.0, statsmodels 0.15.0.
