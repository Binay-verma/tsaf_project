# Multi-festival matched historical results

Exploratory 2024–2025 evaluation. MASE is error, not accuracy percent; lower is better.
Equal states within year, equal years within festival. Different festivals have different documented state coverage.

## Results by festival

### Diwali

States: Delhi, Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_calendar | 0.53022 | 1.22380 | 1.19796 |
| chronos_history | 0.54564 | 1.24114 | 1.19892 |
| ets_weekly_monthly | 0.58633 | 1.43692 | 1.62996 |
| last_value | 0.62186 | 1.43692 | 1.62996 |
| lightgbm_stable_calendar_monthly | 0.59083 | 1.26678 | 1.39904 |
| lightgbm_stable_history_monthly | 0.68421 | 1.42091 | 1.90131 |
| ridge_basic_calendar | 0.57450 | 1.12869 | 1.20611 |
| ridge_basic_history | 0.64870 | 1.20534 | 1.57393 |
| ridge_rich_calendar_monthly | 0.54736 | 1.22158 | 1.32808 |
| ridge_rich_history_monthly | 0.63524 | 1.40509 | 1.43856 |
| sarimax_calendar_annual | 0.58122 | 1.18218 | 1.20223 |
| sarimax_history_annual | 0.59046 | 1.45349 | 1.50606 |
| timesfm_calendar | 0.52136 | 1.22139 | 1.16340 |
| timesfm_history | 0.53440 | 1.22783 | 1.06153 |
| weekly_repeat | 1.43692 | 1.43692 | 1.62996 |

### Dussehra

States: Delhi, Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_calendar | 0.68705 | 1.17201 | 1.22108 |
| chronos_history | 0.71885 | 1.19297 | 1.31899 |
| ets_weekly_monthly | 0.77586 | 1.50366 | 1.70176 |
| last_value | 0.84725 | 1.50367 | 1.70176 |
| lightgbm_stable_calendar_monthly | 0.72042 | 1.32018 | 1.48697 |
| lightgbm_stable_history_monthly | 0.76570 | 1.25343 | 1.63660 |
| ridge_basic_calendar | 0.68688 | 1.19562 | 1.48880 |
| ridge_basic_history | 0.79116 | 1.49519 | 1.54479 |
| ridge_rich_calendar_monthly | 0.67399 | 1.17608 | 1.19611 |
| ridge_rich_history_monthly | 0.74108 | 1.37693 | 1.56940 |
| sarimax_calendar_annual | 0.70798 | 1.13350 | 1.40592 |
| sarimax_history_annual | 0.77093 | 1.42556 | 1.45152 |
| timesfm_calendar | 0.67741 | 1.13234 | 1.23239 |
| timesfm_history | 0.68838 | 1.28006 | 1.48910 |
| weekly_repeat | 1.50367 | 1.50367 | 1.70176 |

### Ganesh_Chaturthi

States: Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_calendar | 0.44606 | 0.52336 | 0.67852 |
| chronos_history | 0.46701 | 0.60004 | 0.79805 |
| ets_weekly_monthly | 0.47173 | 0.79276 | 1.17518 |
| last_value | 0.66994 | 0.79276 | 1.17519 |
| lightgbm_stable_calendar_monthly | 0.53158 | 0.79081 | 1.49324 |
| lightgbm_stable_history_monthly | 0.62650 | 1.03195 | 1.54694 |
| ridge_basic_calendar | 0.43197 | 0.42923 | 0.54150 |
| ridge_basic_history | 0.61507 | 0.59288 | 0.88429 |
| ridge_rich_calendar_monthly | 0.46332 | 0.57828 | 0.75280 |
| ridge_rich_history_monthly | 0.44729 | 0.77169 | 1.26974 |
| sarimax_calendar_annual | 0.44923 | 0.48489 | 0.48067 |
| sarimax_history_annual | 0.57891 | 0.70062 | 0.86831 |
| timesfm_calendar | 0.47728 | 0.61692 | 0.86845 |
| timesfm_history | 0.47470 | 0.74769 | 1.05098 |
| weekly_repeat | 0.79276 | 0.79276 | 1.17519 |

### Holi

States: Delhi, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_calendar | 0.68181 | 0.75677 | 0.91244 |
| chronos_history | 0.65920 | 0.73778 | 0.88348 |
| ets_weekly_monthly | 0.77963 | 0.69435 | 0.84458 |
| last_value | 0.79637 | 0.69435 | 0.84458 |
| lightgbm_stable_calendar_monthly | 0.93049 | 0.95756 | 1.21104 |
| lightgbm_stable_history_monthly | 0.90708 | 1.16811 | 1.22895 |
| ridge_basic_calendar | 0.79841 | 1.05681 | 1.34910 |
| ridge_basic_history | 0.77867 | 0.98345 | 1.25715 |
| ridge_rich_calendar_monthly | 0.80909 | 1.07697 | 1.24434 |
| ridge_rich_history_monthly | 0.74659 | 1.04277 | 1.11161 |
| sarimax_calendar_annual | 0.80706 | 1.05471 | 1.31044 |
| sarimax_history_annual | 0.83182 | 1.14835 | 1.76370 |
| timesfm_calendar | 0.71847 | 0.73959 | 0.83533 |
| timesfm_history | 0.70584 | 0.72905 | 0.86379 |
| weekly_repeat | 0.69435 | 0.69435 | 0.84458 |

### Ugadi_Gudi_Padwa

States: Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_calendar | 0.34968 | 0.78401 | 0.73746 |
| chronos_history | 0.35381 | 0.74208 | 0.72212 |
| ets_weekly_monthly | 0.33033 | 0.84063 | 0.92980 |
| last_value | 0.44210 | 0.84064 | 0.92981 |
| lightgbm_stable_calendar_monthly | 0.73099 | 0.85344 | 1.27199 |
| lightgbm_stable_history_monthly | 0.68255 | 1.32208 | 2.19615 |
| ridge_basic_calendar | 0.33398 | 0.93980 | 1.25602 |
| ridge_basic_history | 0.41163 | 0.82507 | 1.16235 |
| ridge_rich_calendar_monthly | 0.39687 | 0.88067 | 0.98247 |
| ridge_rich_history_monthly | 0.36615 | 0.80547 | 0.79606 |
| sarimax_calendar_annual | 0.32840 | 0.96524 | 1.31025 |
| sarimax_history_annual | 0.40093 | 1.08840 | 2.00424 |
| timesfm_calendar | 0.35558 | 0.73467 | 0.71196 |
| timesfm_history | 0.36812 | 0.73081 | 0.65873 |
| weekly_repeat | 0.84064 | 0.84064 | 0.92981 |

## Interpretation

The ranking varies by festival and horizon. These scores diagnose forecast performance during fixed holiday windows. The ordinary calendar inputs encode weekdays and annual harmonics, not new Holi/Ganesh/Ugadi indicators. Therefore these scores do not measure a benefit from adding those festival identities.

Diwali retains its earlier broad union of national/main and regional subsidiary windows. Other groups use one anchor per state/year. The history/ordinary-calendar tables do not replace previously reported regional-Diwali feature arms. No setting, window or best model was chosen for a clean test using these results. Detailed state/year scores and all configurations are retained.

Only two historical years; related states/days and coincident observances are dependent. Dussehra2025 coincides with Gandhi Jayanti and Spring2025 is adjacent to Eid. Annual-as-issued schedules are not full amendment certification or evidence of statewide closure. Eid-specific and incomplete late-December cohorts are deferred, with reasons in the frozen protocol.

Historical source revisions/publication lag and foundation-model pretraining/proxy overlap remain unresolved. Different adaptation/feature budgets prevent an architecture-only conclusion. No causal festival effect, universal winner, journal readiness or independent human review is claimed. Original and prospective predictions remain unchanged.

## Numerical and uncertainty diagnostics

Native quantile crossings retained: Chronos 3; TimesFM 0. No sorting or clipping. The point-metric audit does not establish ordered/calibrated uncertainty.

New TimesFM history/calendar predictions reproduce the old150Diwali cases exactly. New Chronos ordinary-calendar values agree with the prior controls within small batching differences (maximum0.0000611GWh). Six date-selected ETS deployments reproduce through scalar innovation recurrences. These are bounded internal software checks, not independent human review.

Near ties must not be overinterpreted; ETS and naive longer-lead Holi scores are almost identical. Refer to full precision and individual-year/state tables.
