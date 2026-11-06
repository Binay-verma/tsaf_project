# Ziel (2018) hSun comparator — India, local models (exploratory)

- **Read first:** `LABEL_CORRECTION.md`. The protocol, code docstring and this folder's name say "replacing", but the arm `sunday_day` is Ziel's **hSun** design (festival day treated as Sunday, no festival indicator). The replacing designs are in `../ziel_replacing_v2`.
- Timeline (UTC, from commit and file stamps): registration commit `a8975c9` 2026-11-06 20:35:55; first worker start 20:36:02; label-correction commit `86406ec` 20:39:38; registered analysis run 20:40:50. The repository cannot itself prove that no metric was looked at before the correction; the analysis outputs are time-stamped after it.
- Reference arms (`calendar`, `day5`, `pooled_day5`) reproduce the stored document-aligned forecasts (max 1.14e-13 GWh) and balanced MASE (2.2e-16): `analysis/checks.json`.
- Ordinary cohort: it has a single family, so the leave-one-family-out part of the "consistent" label is empty and the label rests on the two years only.
- Scope: only the five festival anchors are treated (not all public holidays as in Ziel). Lag features and SARIMAX's weekly seasonal term are not holiday-adjusted; only the calendar channels change.
