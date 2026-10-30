# Calendar information and representation controls v1

Completed exploratory study, 30 October 2026. Protocol was written before these new outcomes; historical outcomes were already known. This is not external preregistration or untouched confirmation.

612 fixed Ridge fits; 215,577 daily predictions; 17 arms; three states, leads 1/7/14. 2024–2025 is the primary descriptive scope, with only two annual event clusters. 2022–2023 remains secondary because prior training windows lack fully specified regional extras. All 61 protected source/historical-result files are unchanged. The historical B/D Ridge forecasts reproduce; zero padding is numerically identical. All arms share evaluation cases and unshifted event membership. Five new unit tests and an independent persisted-output audit passed.

## Primary event results

MASE averaged equally across states within year, then across the two years. Lower is better. These are individual lead-day errors, not weekly averages. The scale comes from the preceding annual training window. Full state/year metrics, all-day/non-event scores, predictions, fit logs, hashes and placebo shifts are saved alongside this report.

| Arm | Lead 1 | Lead 7 | Lead 14 |
| --- | ---: | ---: | ---: |
| calendar | 0.57450 | 1.12869 | 1.20611 |
| generic_7 | 0.42600 | 1.11742 | 1.23166 |
| generic_window | 0.60257 | 1.34947 | 1.40894 |
| placebo_7 | 0.57439 | 1.10077 | 1.17783 |
| placebo_window | 0.57499 | 1.09743 | 1.17517 |
| regional_7 | 0.42466 | 1.25384 | 1.47234 |
| regional_shift_+1_7 | 0.41955 | 1.21500 | 1.44021 |
| regional_shift_+1_window | 0.58099 | 1.14979 | 1.27512 |
| regional_shift_+2_7 | 0.40370 | 1.17663 | 1.34051 |
| regional_shift_+2_window | 0.55854 | 1.00539 | 1.12257 |
| regional_shift_-1_7 | 0.42431 | 1.26324 | 1.45918 |
| regional_shift_-1_window | 0.60064 | 1.25901 | 1.38794 |
| regional_shift_-2_7 | 0.45098 | 1.28099 | 1.44383 |
| regional_shift_-2_window | 0.58968 | 1.27248 | 1.37794 |
| regional_window | 0.61113 | 1.28008 | 1.40395 |
| zero_1 | 0.57450 | 1.12869 | 1.20611 |
| zero_7 | 0.57450 | 1.12869 | 1.20611 |

## Interpretation and limits

The primary regional-versus-generic scalar contrast is mixed: regional MASE is 0.00856 higher at lead 1, 0.06939 lower at lead 7, and 0.00499 lower at lead 14. In 2024 the scalar regional result is worse at every lead; in 2025 it is worse at lead 1 and better at leads 7/14. This does not demonstrate a stable calendar-provenance benefit.

Seven-channel regional encoding has much lower day-1 error than the scalar regional window, but worse long-lead error than generic seven-channel encoding in the two-year average. The information lost by collapsing relative-day channels matters; the original B-to-D result does not isolate regional calendar provenance. Delhi has no extra regional anchors and generic/regional predictions are identical, as expected.

Zero controls provide a software check for this fixed linear Ridge pipeline. They cannot establish how Chronos reacts to added channels. Placebo channels are broadly near the ordinary-calendar baseline; one seed/constellation is not a randomization distribution. Date shifts change results considerably, but choosing a shift from these outcomes would tune the calendar against the evaluation data. **Do not replace documented dates with the best-scoring perturbation.**

These comparisons concern predictive representations, not causal effects of festivals. Regional ledgers also change the duration of the event information. Full amendments and actual regional electricity-response dates remain unverified. Only two primary annual clusters and three correlated states are present. No p-values, generalisation claim, successful new TSFM claim, or winning encoding selected for a final test follows from this experiment.

## Reproduction

Use `.venv/bin/python src/test_calendar_controls.py` and `.venv/bin/python src/audit_new_experiments.py` for existing artifacts. `src/calendar_controls.py` refuses to overwrite this run. For a genuinely new run, create a new directory containing the protocol and protected-file manifest, then pass `--out NEW_DIRECTORY`. Preserve this run and label any protocol/code changes. No model weights were needed.
