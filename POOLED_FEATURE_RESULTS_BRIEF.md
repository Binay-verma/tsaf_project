# Do separate festival identities help beyond a pooled flag?

Completed exploratory follow-up, 30 October 2026. Daily supplied electricity in Delhi, Karnataka and Maharashtra. Historical 2024–2025 labels were previously inspected; this is not a clean final test.

The original study asked whether predictions differ during festivals. The preceding intervention added explicit festival features. This follow-up asks whether five separate family features add value beyond marking their pooled dates, and whether padding alone changes the forecast.

## Next-day festival-anchor results

MASE is scaled error; lower is better. Same 72 event/lead cases per arm, including 24 next-day cases, with equal states within year, years within family and families overall. Each tree capacity regime keeps its own fixed parameters and baseline.

| model | calendar | pooled_day1 | pooled_day5 | day5 | pooled_window1 | pooled_window5 | window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.24369 | 0.59692 | 0.59692 | 0.56112 | 1.15559 | 1.15559 | 1.18795 | 1.24369 |
| lightgbm | 1.28595 | 1.12357 | 1.12357 | 1.2681 | 1.22733 | 1.22733 | 1.2775 | 1.28595 |
| lightgbm_capacity2 | 1.27323 | 0.84252 | 0.84252 | 1.09736 | 1.2203 | 1.2203 | 1.24629 | 1.27323 |
| sarimax | 1.31035 | 0.656 | 0.656 | 0.53159 | 1.31001 | 1.30999 | 1.31002 | 1.31032 |
| chronos | 1.3711 | 1.25978 | 1.2933 | 1.32921 | 1.28535 | 1.32979 | 1.35326 | 1.37181 |
| timesfm | 1.34818 | 0.69871 | 0.68281 | 1.1033 | 1.33541 | 1.36195 | 1.35036 | 1.3599 |

## Typed minus pooled at the same five-channel budget

Negative changes favour separate family channels; positive changes favour the pooled representation. These are macro-MASE differences, not accuracy percentages. All leads and both representations are shown; no best arm is selected for future use.

### Festival anchors

| model | day5: lead 1 | day5: lead 7 | day5: lead 14 | window5: lead 1 | window5: lead 7 | window5: lead 14 |
| --- | --- | --- | --- | --- | --- | --- |
| ridge | -0.0358 | -0.05488 | -0.0369 | 0.03236 | 0.20178 | 0.19295 |
| lightgbm | 0.14453 | 0.17901 | 0.14932 | 0.05017 | 0.03025 | 0.05923 |
| lightgbm_capacity2 | 0.25483 | 0.13485 | 0.17805 | 0.02599 | 0.01553 | 0.00978 |
| sarimax | -0.12441 | -0.0455 | -0.01393 | 3e-05 | 0.01303 | 0.01394 |
| chronos | 0.03591 | -0.02244 | -0.01627 | 0.02347 | 0.02214 | 0.03519 |
| timesfm | 0.42049 | -0.01527 | 0.16754 | -0.01158 | -0.01307 | 0.047 |

### Matched non-event targets

| model | day5: lead 1 | day5: lead 7 | day5: lead 14 | window5: lead 1 | window5: lead 7 | window5: lead 14 |
| --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.00035 | 0.00393 | 0.001 | -0.00801 | 0.01529 | -0.0033 |
| lightgbm | 0.00304 | 0.03654 | -0.00374 | 0.01841 | 0.0272 | -0.00527 |
| lightgbm_capacity2 | 0.01311 | -0.00108 | -0.00859 | 0.00675 | -0.00884 | 0.02124 |
| sarimax | -0.0011 | 0.00572 | -0.013 | 0.00084 | -0.01275 | 0.0044 |
| chronos | -0.00506 | -0.00263 | -0.02129 | -0.00608 | 0.0092 | -0.01419 |
| timesfm | -0.00201 | 0.02127 | -0.002 | -0.00512 | 0.01357 | 0.01025 |

## Native uncertainty

Common native0.1–0.9quantiles and unmodified80%intervals are scored separately for both foundation models. Coverage accompanies width, scaled pinball and a one-interval WIS; these intervals have not been calibrated. See both NATIVE_UNCERTAINTY.md reports and the independent arithmetic audit. The limited historical cases cannot certify calibration. Nominal 80% next-day event-balanced coverage is only 0.100 for calendar Chronos and 0.16667 for calendar TimesFM; pooled-day5 TimesFM reaches 0.500. All compared native Chronos outputs retain 14 adjacent crossing pairs (9 new, 5 reused), while TimesFM has none; the common nine-level grid does not cross.

## Verification and limits

4,320 new forecasts plus 2,592 hash-checked reused forecasts give 6,912 compared rows across two distinct72-case cohorts. Complete-case, label/scale/hierarchy/paired-score, actual-input-byte, budget/cutoff/support and probabilistic arithmetic audits are recorded. All original source/result/deck/future-freeze hashes in the protection manifest remain unchanged.

The bounded separate clean scalar review reproduces all135checked forecasts within tolerance, maximum7.617e-12GWh, and every label vector exactly. Its strict overall status is discrepancies_retained: the Delhi tree matrices differ at one near-zero trend entry per checked block (maximum float32 difference1.421e-14GWh). The original failure and localization are retained; do not call this a full clean-room pass or assume float32 guarantees byte identity.

Separate versus pooled channels changes statistical sharing and signal allocation. Same dimensions do not identify a causal festival-identity mechanism. State scopes differ; annual dates are not complete amendment histories; two years and related dates provide limited independent evidence. Source reuse/processing clarification, independent human review, historical/proxy exposure and untouched/source-independent confirmation remain open. Frozen future forecasts and the paused workflow are unchanged.

Reproduction: [POOLED_FEATURE_REPRODUCTION.md](POOLED_FEATURE_REPRODUCTION.md). Full results: [event](results/pooled_festival_v1/event/REPORT.md), [non-event](results/pooled_festival_v1/non_event/REPORT.md).

Later checkpoint: the separately registered supervised family-label exclusion study is now completed and audited; see [label-transfer brief](LABEL_TRANSFER_RESULTS_BRIEF.md). Target-history exposure remains allowed and longer-lead failures are retained. External rights/human and later prospective gates remain open.
