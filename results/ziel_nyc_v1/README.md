# Ziel (2018) hSun and replacing comparators — NYC MTA replication, local models (exploratory)

- Same cases, source snapshot, selected parameters, refits and seven-day buffer as `../mta_holiday_v1`.
- Timeline (UTC): registration commit `add10e1` 2026-11-06 20:43:36; first worker start 20:46:08; analysis 20:47:10.
- Reference arms reproduce the parent forecasts exactly and the stored balanced MASE (2.2e-16): `analysis/checks.json`.
- Labels use the two modes (Bus, Subway) in place of years. The ordinary cohort has a single family, so its labels rest on the two modes only.
- Two observances and two related modes: a bounded robustness check only.
