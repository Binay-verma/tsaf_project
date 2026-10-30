# Explicit festival-feature intervention

Exploratory intervention after inspecting historical benchmark/plots; frozen before new intervention outcomes. Not external preregistration, clean final test, causal identification or new-method novelty.

**This is an added-feature experiment. Earlier multi-festival scores were diagnostics without these event identities.**

## Matched primary comparison

72date-selected anchor targets,24festival/state/year groups, leads1/7/14. Same cases for every model/arm. Diwali uses legacy national/main target; Maharashtra regional dates remain in features. No outcome-selected case reduction.

2592 scored forecasts: 6model variants x 6common arms x 72identical cases. MASE is error, not accuracy percent; lower is better. Equal states within year, years within festival and families for overall summaries.

All variants, including zeros and active placebos, are reported. No best-looking date, encoding, capacity setting or model is selected for future deployment from these results.

### Individual lead 1

| model | calendar | zero5 | day5 | window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.24369 | 1.24369 | 0.56112 | 1.18795 | 1.24458 | 1.24298 |
| lightgbm | 1.28595 | 1.28595 | 1.2681 | 1.2775 | 1.28595 | 1.28595 |
| lightgbm_capacity2 | 1.27323 | 1.27323 | 1.09736 | 1.24629 | 1.27393 | 1.28554 |
| sarimax | 1.31035 | 1.31023 | 0.53159 | 1.31002 | 1.30993 | 1.31127 |
| chronos | 1.3711 | 1.37509 | 1.32921 | 1.35326 | 1.40526 | 1.40152 |
| timesfm | 1.34818 | 1.37329 | 1.1033 | 1.35036 | 1.35827 | 1.36604 |

### Individual lead 7

| model | calendar | zero5 | day5 | window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.18944 | 1.18944 | 1.02322 | 1.21098 | 1.18626 | 1.19628 |
| lightgbm | 1.34908 | 1.34908 | 1.34908 | 1.32312 | 1.34937 | 1.35632 |
| lightgbm_capacity2 | 1.38805 | 1.38805 | 1.29031 | 1.34217 | 1.38863 | 1.37783 |
| sarimax | 1.15947 | 1.15871 | 0.95267 | 1.18135 | 1.15843 | 1.16285 |
| chronos | 1.24728 | 1.27639 | 1.23788 | 1.25983 | 1.29657 | 1.30275 |
| timesfm | 1.26603 | 1.30575 | 0.90905 | 1.23886 | 1.30225 | 1.29826 |

### Individual lead 14

| model | calendar | zero5 | day5 | window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.25324 | 1.25324 | 1.1381 | 1.33426 | 1.25305 | 1.27266 |
| lightgbm | 1.55964 | 1.55964 | 1.55964 | 1.56521 | 1.55964 | 1.56063 |
| lightgbm_capacity2 | 1.59331 | 1.59331 | 1.56003 | 1.60454 | 1.59108 | 1.60473 |
| sarimax | 1.19745 | 1.19623 | 1.08689 | 1.21966 | 1.19639 | 1.20284 |
| chronos | 1.18242 | 1.19803 | 1.12934 | 1.21053 | 1.23178 | 1.208 |
| timesfm | 1.24429 | 1.30528 | 1.03615 | 1.2666 | 1.2846 | 1.28798 |

## Per-festival and individual-year results

See primary_metrics_festival.csv, primary_metrics_state_year.csv and primary_paired_festival.csv. Paired percent reductions are means of within-state/year effects, not ratios of macro MASE. Zero denominators remain explicitly undefined; no epsilon or silent deletion. MASE changes remain available. Negative effects and all control outcomes are retained.

## Wider classical cohort

All528unchanged window cases for rich Ridge, stable LightGBM, fixed-capacity2 tree and SARIMAX. Foundation-model claims restricted to72anchor targets; never compare their anchor scores with others window scores.

secondary_classical_* files retain every classical arm, including35offset/zero/placebo sensitivities where prespecified. Foundation-model anchor metrics must not be compared with these wider-window metrics.

## Bounds

Two historical years and related states/dates provide limited independent evidence. Calendar definitions are annual-as-issued, not full amendment certification or proof of statewide closure. Diwali is the legacy main/subsidiary subset. Dussehra2025/Gandhi and spring2025/Eid co-occur. New target values never enter inputs, but retrospective publication availability and pretraining/proxy overlap remain unresolved.

One fixed placebo seed and these representations do not establish causality or a universal event-information mechanism. Rare day indicators may be below a tree leaf constraint; capacity2 is a separate fixed sensitivity, not an outcome-selected best regime. Native quantile failures are reported separately and retained without sorting/clipping. Point-metric audits are not calibration or independent human approval.

Source permission, amendments, human review and prospective outcomes remain pending. Original source/forecast results and future Git blobs remain unchanged. No journal readiness, acceptance or new architectural method is claimed.
