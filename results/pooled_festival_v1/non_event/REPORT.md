# Pooled versus separate festival features — non_event

Exploratory historical follow-up after inspecting typed-feature results; frozen before new pooled outcomes. No clean test or external preregistration.

3456forecasts:2160new pooled/zero forecasts and1296reused calendar/typed forecasts. Six variants, eight arms and72identical cases per arm. The non-event family denotes its matched event pair. Individual leads1/7/14; MASE is scaled error, lower is better.

Separate identities versus pooled5 has equal channel count, but changes allocation and statistical sharing. Pooled1 versus pooled5 measures padding sensitivity. Neither comparison establishes causality or a universal need for identities. All model/lead/family/year outcomes are retained; no new deployment selection.

## Individual lead 1

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.2954 | 0.2819 | 0.27925 | 0.28154 | 0.28154 | 0.28726 | 0.28726 | 0.2954 |
| lightgbm | 0.33488 | 0.32823 | 0.33485 | 0.32519 | 0.32519 | 0.31644 | 0.31644 | 0.33488 |
| lightgbm_capacity2 | 0.32582 | 0.31406 | 0.32628 | 0.30095 | 0.30095 | 0.31953 | 0.31953 | 0.32582 |
| sarimax | 0.25238 | 0.24862 | 0.25313 | 0.2496 | 0.24972 | 0.25222 | 0.25229 | 0.25237 |
| chronos | 0.26101 | 0.24453 | 0.24759 | 0.25274 | 0.24959 | 0.26084 | 0.25367 | 0.26078 |
| timesfm | 0.24067 | 0.2321 | 0.22994 | 0.23234 | 0.2341 | 0.23757 | 0.23506 | 0.23643 |

## Individual lead 7

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.78005 | 0.777 | 0.77492 | 0.77307 | 0.77307 | 0.75963 | 0.75963 | 0.78005 |
| lightgbm | 1.10561 | 1.10172 | 1.09614 | 1.06517 | 1.06517 | 1.06894 | 1.06894 | 1.10561 |
| lightgbm_capacity2 | 0.96194 | 0.96439 | 0.95914 | 0.96547 | 0.96547 | 0.96798 | 0.96798 | 0.96194 |
| sarimax | 0.80052 | 0.74529 | 0.78022 | 0.73861 | 0.73957 | 0.79265 | 0.79298 | 0.80046 |
| chronos | 0.6224 | 0.61778 | 0.63584 | 0.63328 | 0.62041 | 0.64036 | 0.62664 | 0.61889 |
| timesfm | 0.59157 | 0.57628 | 0.56398 | 0.56568 | 0.55501 | 0.57359 | 0.55041 | 0.57661 |

## Individual lead 14

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.8742 | 0.87112 | 0.85256 | 0.87013 | 0.87013 | 0.85587 | 0.85587 | 0.8742 |
| lightgbm | 0.99641 | 0.99641 | 0.99988 | 1.00015 | 1.00015 | 1.00515 | 1.00515 | 0.99641 |
| lightgbm_capacity2 | 1.02477 | 1.03194 | 1.03125 | 1.04053 | 1.04053 | 1.01001 | 1.01001 | 1.02477 |
| sarimax | 1.10447 | 1.07901 | 1.10636 | 1.09047 | 1.09201 | 1.10145 | 1.10196 | 1.10441 |
| chronos | 0.7915 | 0.8171 | 0.8141 | 0.81043 | 0.83839 | 0.80372 | 0.82829 | 0.79911 |
| timesfm | 0.6661 | 0.64049 | 0.65545 | 0.66014 | 0.64249 | 0.65998 | 0.6452 | 0.65656 |

## Interpretation and limits

See contrasts_balanced.csv and contrasts_festival.csv: negative MASE_change favours the first arm. Percentage reductions are averaged within state/year, not computed from the macro-MASE ratio. A zero reference remains undefined; no epsilon or dropped cases.

All historical data were inspected previously. Two event years and three related states are limited, correlated evidence. No all-day operational, untouched, causal or architecture-superiority claim. Source rights, amendment completeness, model/source exposure and publication lag remain unresolved. No new future actuals were acquired. Frozen forecasts and paused automation are unchanged.

Native quantiles are retained without sorting/clipping. Their crossing inventory and actual-input byte checks are in the input audit. Point metrics do not establish calibration or independent human approval.
