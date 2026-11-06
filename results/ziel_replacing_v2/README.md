# Ziel (2018) replacing comparators Rph and RpH — India, local models (exploratory)

- Arms: `replace_pooled` (Rph) and `replace_typed` (RpH): festival day flags added and all seven weekday dummies set to zero on festival days (Ziel 2018, Eq. 11).
- Timeline (UTC): registration commit `5e1e4dc` 2026-11-06 20:40:32; first worker start 20:40:50; analysis 20:46:15.
- Reference arms reproduce the stored forecasts (max 1.14e-13 GWh) and balanced MASE (2.2e-16): `analysis/checks.json`.
- Ordinary cohort: single family, so the leave-one-family-out part of the "consistent" label is empty and the label rests on the two years only.
- Scope as in `../ziel_replacing_v1/README.md`.
