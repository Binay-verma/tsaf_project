# Supervised family-label exclusion and event transfer

Exploratory after historical benchmarks; fixed before these exclusion outcomes. No untouched test or external preregistration.

3,888 forecasts: three fixed regression budgets, nine feature/row-policy arms and the same144cases across separate event and non-event cohorts. Rows, dates and leads remain matched. No best-arm selection or parameter search.

**This is not fully unseen event exposure.** Past electricity history, annual lags and other rows containing earlier festival responses remain available. Direct own-family labels are removed from model/scaler fitting; foundation pretraining is not tested by this experiment.

Version1stopped on an exact matching guard and is preserved. Version2preflights all141training blocks, then uses fixed same-weekday/same-year28–84day matches; longer shifts weaken seasonal comparability and are fully recorded.

## event · individual lead 1

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 1.29619 | 1.30951 | 1.29997 | 0.55744 | 1.32139 | 0.55616 | 0.59977 | 0.7106 | 0.60301 |
| tree_fixed20 | 1.28723 | 1.30805 | 1.29638 | 1.28723 | 1.30805 | 1.29638 | 1.28723 | 1.30805 | 1.29638 |
| tree_fixed2 | 1.2831 | 1.28728 | 1.28201 | 1.12244 | 1.2754 | 1.13196 | 0.86181 | 1.01676 | 0.88787 |

## event · individual lead 7

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 1.16179 | 1.18662 | 1.16577 | 1.24636 | 1.20247 | 1.24496 | 1.36794 | 1.33987 | 1.36308 |
| tree_fixed20 | 1.25992 | 1.23955 | 1.26834 | 1.25992 | 1.23955 | 1.26834 | 1.25992 | 1.23955 | 1.26834 |
| tree_fixed2 | 1.26651 | 1.24388 | 1.26424 | 1.1894 | 1.2343 | 1.17333 | 1.02878 | 1.11386 | 1.06552 |

## event · individual lead 14

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 1.19318 | 1.21157 | 1.21654 | 1.34222 | 1.21904 | 1.32856 | 1.48068 | 1.52931 | 1.46352 |
| tree_fixed20 | 1.49594 | 1.62237 | 1.44588 | 1.49594 | 1.62237 | 1.44588 | 1.49594 | 1.62237 | 1.44588 |
| tree_fixed2 | 1.52767 | 1.57566 | 1.49627 | 1.50067 | 1.56497 | 1.42634 | 1.34079 | 1.43248 | 1.3365 |

## non_event · individual lead 1

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 0.28629 | 0.28035 | 0.28981 | 0.28462 | 0.28333 | 0.28783 | 0.28446 | 0.27824 | 0.28752 |
| tree_fixed20 | 0.34899 | 0.31104 | 0.34572 | 0.34899 | 0.31104 | 0.34572 | 0.34899 | 0.31104 | 0.34572 |
| tree_fixed2 | 0.31828 | 0.32399 | 0.33841 | 0.31051 | 0.31728 | 0.3265 | 0.29822 | 0.30827 | 0.30706 |

## non_event · individual lead 7

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 0.9177 | 0.91675 | 0.92314 | 0.9121 | 0.91631 | 0.92263 | 0.90832 | 0.91614 | 0.91803 |
| tree_fixed20 | 0.94808 | 0.99022 | 0.92086 | 0.94808 | 0.99022 | 0.92086 | 0.94808 | 0.99022 | 0.92086 |
| tree_fixed2 | 0.92104 | 0.94135 | 0.92116 | 0.91989 | 0.93612 | 0.92563 | 0.89999 | 0.88198 | 0.89076 |

## non_event · individual lead 14

| model | calendar__all_rows | calendar__exclude_family | calendar__exclude_control | typed_day5__all_rows | typed_day5__exclude_family | typed_day5__exclude_control | pooled_day5__all_rows | pooled_day5__exclude_family | pooled_day5__exclude_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_fixed10 | 1.02987 | 1.03152 | 1.0446 | 1.02331 | 1.02614 | 1.03761 | 1.02151 | 1.02806 | 1.03617 |
| tree_fixed20 | 1.04405 | 1.08671 | 0.96451 | 1.04405 | 1.08671 | 0.96451 | 1.04405 | 1.08671 | 0.96451 |
| tree_fixed2 | 1.07906 | 1.11205 | 1.04296 | 1.09589 | 1.09084 | 1.05868 | 1.09345 | 1.09874 | 1.05321 |

## Read the controls

Compare pooled_day5 with calendar under exclude_family to assess pooled-feature usefulness without direct own-family fitting labels. Compare exclude_family with exclude_control for the same feature to separate removal of own-family labels from the same number of ordinary labels. Compare with all_rows to show the full-data reference. All parameters are fixed; these budgets differ from earlier validation-selected models and are not interchangeable ranking entries.

Negative MASE_change favours the first arm. Individual state/year/lead cells and every family remain available. This is exploratory historical evidence, with two years and correlated states/dates. No causal mechanism, clean-test transfer, universal benefit, calibrated uncertainty or new-method novelty is established. Source rights, amendments, independent human review and later/source-independent confirmation remain open. Original results and prospective forecasts remain unchanged.
