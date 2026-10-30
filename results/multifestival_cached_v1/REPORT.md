# Multi-festival matched historical results

Exploratory 2024–2025 evaluation. MASE is error, not accuracy percent; lower is better.
Equal states within year, equal years within festival. Different festivals have different documented state coverage.

## Results by festival

### Diwali

States: Delhi, Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_history | 0.54564 | 1.24114 | 1.19892 |
| last_value | 0.62186 | 1.43692 | 1.62996 |
| lightgbm_stable_calendar_monthly | 0.59083 | 1.26678 | 1.39904 |
| lightgbm_stable_history_monthly | 0.68421 | 1.42091 | 1.90131 |
| ridge_basic_calendar | 0.57450 | 1.12869 | 1.20611 |
| ridge_basic_history | 0.64870 | 1.20534 | 1.57393 |
| ridge_rich_calendar_monthly | 0.54736 | 1.22158 | 1.32808 |
| ridge_rich_history_monthly | 0.63524 | 1.40509 | 1.43856 |
| weekly_repeat | 1.43692 | 1.43692 | 1.62996 |

### Dussehra

States: Delhi, Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_history | 0.71885 | 1.19297 | 1.31899 |
| last_value | 0.84725 | 1.50367 | 1.70176 |
| lightgbm_stable_calendar_monthly | 0.72042 | 1.32018 | 1.48697 |
| lightgbm_stable_history_monthly | 0.76570 | 1.25343 | 1.63660 |
| ridge_basic_calendar | 0.68688 | 1.19562 | 1.48880 |
| ridge_basic_history | 0.79116 | 1.49519 | 1.54479 |
| ridge_rich_calendar_monthly | 0.67399 | 1.17608 | 1.19611 |
| ridge_rich_history_monthly | 0.74108 | 1.37693 | 1.56940 |
| weekly_repeat | 1.50367 | 1.50367 | 1.70176 |

### Ganesh_Chaturthi

States: Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_history | 0.46701 | 0.60004 | 0.79805 |
| last_value | 0.66994 | 0.79276 | 1.17519 |
| lightgbm_stable_calendar_monthly | 0.53158 | 0.79081 | 1.49324 |
| lightgbm_stable_history_monthly | 0.62650 | 1.03195 | 1.54694 |
| ridge_basic_calendar | 0.43197 | 0.42923 | 0.54150 |
| ridge_basic_history | 0.61507 | 0.59288 | 0.88429 |
| ridge_rich_calendar_monthly | 0.46332 | 0.57828 | 0.75280 |
| ridge_rich_history_monthly | 0.44729 | 0.77169 | 1.26974 |
| weekly_repeat | 0.79276 | 0.79276 | 1.17519 |

### Holi

States: Delhi, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_history | 0.65920 | 0.73778 | 0.88348 |
| last_value | 0.79637 | 0.69435 | 0.84458 |
| lightgbm_stable_calendar_monthly | 0.93049 | 0.95756 | 1.21104 |
| lightgbm_stable_history_monthly | 0.90708 | 1.16811 | 1.22895 |
| ridge_basic_calendar | 0.79841 | 1.05681 | 1.34910 |
| ridge_basic_history | 0.77867 | 0.98345 | 1.25715 |
| ridge_rich_calendar_monthly | 0.80909 | 1.07697 | 1.24434 |
| ridge_rich_history_monthly | 0.74659 | 1.04277 | 1.11161 |
| weekly_repeat | 0.69435 | 0.69435 | 0.84458 |

### Ugadi_Gudi_Padwa

States: Karnataka, Maharashtra.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | --- | --- | --- |
| chronos_history | 0.35381 | 0.74208 | 0.72212 |
| last_value | 0.44210 | 0.84064 | 0.92981 |
| lightgbm_stable_calendar_monthly | 0.73099 | 0.85344 | 1.27199 |
| lightgbm_stable_history_monthly | 0.68255 | 1.32208 | 2.19615 |
| ridge_basic_calendar | 0.33398 | 0.93980 | 1.25602 |
| ridge_basic_history | 0.41163 | 0.82507 | 1.16235 |
| ridge_rich_calendar_monthly | 0.39687 | 0.88067 | 0.98247 |
| ridge_rich_history_monthly | 0.36615 | 0.80547 | 0.79606 |
| weekly_repeat | 0.84064 | 0.84064 | 0.92981 |

## Interpretation

The ranking varies by festival and horizon. These scores diagnose forecast performance during fixed holiday windows. The ordinary calendar inputs encode weekdays and annual harmonics, not new Holi/Ganesh/Ugadi indicators. Therefore these scores do not measure a benefit from adding those festival identities.

Diwali retains its earlier broad union of national/main and regional subsidiary windows. Other groups use one anchor per state/year. No setting, window or best model was chosen for a clean test using these results. Detailed state/year scores and all configurations are retained.

Only two historical years; related states/days and coincident observances are dependent. Dussehra2025 coincides with Gandhi Jayanti and Spring2025 is adjacent to Eid. Annual-as-issued schedules are not full amendment certification or evidence of statewide closure. Eid-specific and incomplete late-December cohorts are deferred, with reasons in the frozen protocol.

Historical source revisions/publication lag and foundation-model pretraining/proxy overlap remain unresolved. Different adaptation/feature budgets prevent an architecture-only conclusion. No causal festival effect, universal winner, journal readiness or independent human review is claimed. Original and prospective predictions remain unchanged.
