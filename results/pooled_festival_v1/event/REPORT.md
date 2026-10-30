# Pooled versus separate festival features — event

Exploratory historical follow-up after inspecting typed-feature results; frozen before new pooled outcomes. No clean test or external preregistration.

3456forecasts:2160new pooled/zero forecasts and1296reused calendar/typed forecasts. Six variants, eight arms and72identical cases per arm. The non-event family denotes its matched event pair. Individual leads1/7/14; MASE is scaled error, lower is better.

Separate identities versus pooled5 has equal channel count, but changes allocation and statistical sharing. Pooled1 versus pooled5 measures padding sensitivity. Neither comparison establishes causality or a universal need for identities. All model/lead/family/year outcomes are retained; no new deployment selection.

## Individual lead 1

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.24369 | 0.56112 | 1.18795 | 0.59692 | 0.59692 | 1.15559 | 1.15559 | 1.24369 |
| lightgbm | 1.28595 | 1.2681 | 1.2775 | 1.12357 | 1.12357 | 1.22733 | 1.22733 | 1.28595 |
| lightgbm_capacity2 | 1.27323 | 1.09736 | 1.24629 | 0.84252 | 0.84252 | 1.2203 | 1.2203 | 1.27323 |
| sarimax | 1.31035 | 0.53159 | 1.31002 | 0.656 | 0.656 | 1.31001 | 1.30999 | 1.31032 |
| chronos | 1.3711 | 1.32921 | 1.35326 | 1.25978 | 1.2933 | 1.28535 | 1.32979 | 1.37181 |
| timesfm | 1.34818 | 1.1033 | 1.35036 | 0.69871 | 0.68281 | 1.33541 | 1.36195 | 1.3599 |

## Individual lead 7

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.18944 | 1.02322 | 1.21098 | 1.0781 | 1.0781 | 1.0092 | 1.0092 | 1.18944 |
| lightgbm | 1.34908 | 1.34908 | 1.32312 | 1.17007 | 1.17007 | 1.29287 | 1.29287 | 1.34908 |
| lightgbm_capacity2 | 1.38805 | 1.29031 | 1.34217 | 1.15545 | 1.15545 | 1.32664 | 1.32664 | 1.38805 |
| sarimax | 1.15947 | 0.95267 | 1.18135 | 0.99828 | 0.99817 | 1.16825 | 1.16832 | 1.15896 |
| chronos | 1.24728 | 1.23788 | 1.25983 | 1.23792 | 1.26032 | 1.17343 | 1.2377 | 1.25702 |
| timesfm | 1.26603 | 0.90905 | 1.23886 | 0.94979 | 0.92432 | 1.19286 | 1.25193 | 1.28601 |

## Individual lead 14

| model | calendar | day5 | window5 | pooled_day1 | pooled_day5 | pooled_window1 | pooled_window5 | zero1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.25324 | 1.1381 | 1.33426 | 1.175 | 1.175 | 1.14131 | 1.14131 | 1.25324 |
| lightgbm | 1.55964 | 1.55964 | 1.56521 | 1.41032 | 1.41032 | 1.50598 | 1.50598 | 1.55964 |
| lightgbm_capacity2 | 1.59331 | 1.56003 | 1.60454 | 1.38198 | 1.38198 | 1.59475 | 1.59475 | 1.59331 |
| sarimax | 1.19745 | 1.08689 | 1.21966 | 1.10014 | 1.10082 | 1.20555 | 1.20572 | 1.19641 |
| chronos | 1.18242 | 1.12934 | 1.21053 | 1.13648 | 1.1456 | 1.15496 | 1.17534 | 1.18585 |
| timesfm | 1.24429 | 1.03615 | 1.2666 | 0.85683 | 0.8686 | 1.1876 | 1.2196 | 1.27505 |

## Interpretation and limits

See contrasts_balanced.csv and contrasts_festival.csv: negative MASE_change favours the first arm. Percentage reductions are averaged within state/year, not computed from the macro-MASE ratio. A zero reference remains undefined; no epsilon or dropped cases.

All historical data were inspected previously. Two event years and three related states are limited, correlated evidence. No all-day operational, untouched, causal or architecture-superiority claim. Source rights, amendment completeness, model/source exposure and publication lag remain unresolved. No new future actuals were acquired. Frozen forecasts and paused automation are unchanged.

Native quantiles are retained without sorting/clipping. Their crossing inventory and actual-input byte checks are in the input audit. Point metrics do not establish calibration or independent human approval.
