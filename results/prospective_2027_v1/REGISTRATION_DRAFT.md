# Prospective test, festivals of 2027 and 2028: registration DRAFT

**Status: draft for the author's approval.** Revised on 15 November 2026 after the TimesFM-3 encoding control (results/new_states_v1_fm_control): P2 now compares typed flags with the pooled flag without zero padding, and TimesFM-3 gets an unpadded pooled arm and a zero arm. Still before any 2027 data or notification existed. The draft was first written on 15 November 2026, after the registered new-states analysis and its exploratory follow-ups, and before any 2027 data or 2027 holiday notification existed. It becomes binding when the author approves it and records it on OSF as an addendum to osf.io/yw7mr. Until then, the commit history timestamps it.

## Why this test exists
The registered study (results/new_states_v1/analysis) found small average effects: H1 SARIMAX typed better, CONFIRMED; H2 TimesFM-3 pooled better at lead 1, NOT CONFIRMED; H3 leaf-2 LightGBM pooled better, CONFIRMED. Exploratory work after it suggested two things (results/simulation_calibration_v2, results/new_states_v1_diagnostics):
1. Typing helps linear models in states whose festivals differ strongly in effect (high heterogeneity h): Rajasthan, Gujarat and Tamil Nadu among the new states.
2. TimesFM-3 does better with typed flags at 7 and 14 days ahead, mainly in those same states.

Both were found after looking at the data, so neither is a confirmed result. This test checks them on festivals that have not happened yet.

## Fixed now
**States and labels.** The labels come from the ten-state calibration (results/simulation_calibration_v2/calibration_by_state.csv, data 2017–2025) and are frozen:
- **"typed" states:** Rajasthan, Gujarat, Tamil Nadu.
- **"pooled" states:** Uttar Pradesh, Madhya Pradesh, Telangana, Andhra Pradesh.

**Events.** The in-scope festival families for each state, as defined in review/new_states_v1/DESIGN_DRAFT.md (conventions 1–6), in calendar years 2027 and 2028.

**Calendar (lesson from the registered study).** Each date must come from the state government's own annual holiday notification (government domain, gazette, or a legible scan of the notification). It is entered with the document number, URL and quoted line before the festival date. A family-state-year without an official notification found before the festival is excluded, not filled from secondary sources. Exclusions are listed.

**Models and arms.** Exactly the registered pipeline (src/new_states_v1.py and the registered parameter selections), with the event years extended to 2027–2028 and no other change:
- ridge, SARIMAX, leaf-2 LightGBM (lightgbm_capacity2), TimesFM-3;
- day flags typed (day5) vs pooled (pooled_day5);
- TimesFM-3 additionally: pooled flag without zero padding (pooled1) and five zero channels (zero5), as in src/new_states_fm_control_v1.py;
- leads 1, 7, 14.

**Data.** The same Grid-India daily state energy series. A festival's data is downloaded only after its forecasts are frozen.

**Unit.** The state-family-year typed − pooled MASE (MASE as registered). A sensitivity uses family-year clusters.

## Hypotheses (Holm across P1 and P2; one-sided sign-flip over units, 1,000,000 draws, seed 20271101)
- **P1:** in the "typed" states, ridge typed − pooled lead-1 MASE < 0.
- **P2:** in the "typed" states, TimesFM-3 typed − unpadded pooled (pooled1) MASE, averaged over leads 7 and 14, < 0. (The registered pooled arm carries four zero channels, which alone cost about 0.015–0.018 at these leads, so comparing against it would make P2 too easy.)

**Decision.** CONFIRMED if Holm p < 0.05 and the mean is in the stated direction. CONTRADICTED if the mean is in the opposite direction with one-sided p < 0.05. Otherwise NOT CONFIRMED.

## Secondary (reported, not used for decisions)
- SARIMAX in the "typed" states (lead 1).
- In the "pooled" states: ridge and TimesFM-3 (leads 7/14, against pooled1), where the expectation is no typed advantage.
- TimesFM-3 in the "typed" states, typed against zero5 (does festival information help at all) and against the padded pooled arm (continuity with the registered contrast).
- Default LightGBM against the zero-flag arm, where the expectation is no effect of typed flags.
- All results with 2027 alone, as an interim description, not a decision.

## Power and honesty about it
**Units.** About 10 state-family units per year in the "typed" states (Rajasthan and Gujarat have 3 families each, Tamil Nadu 4).

**Minimum detectable effects (80% power, one-sided 0.05), from 2017–2025 unit spread:**

| Hypothesis | MDE, 2 years | MDE, 3 years | Observed (post hoc, likely inflated) |
|---|---|---|---|
| P1 | 0.057 | 0.046 | −0.075 |
| P2 | ≈ 0.27 | — | −0.30 against the padded arm; about −0.26 against the unpadded arm (state means for Rajasthan, Gujarat and Tamil Nadu, leads 7 and 14, results/new_states_v1_fm_control), carried by Gujarat and Tamil Nadu |

Because the observed effects were selected after looking, the true effects are probably smaller, so power is probably below 80%. A NOT CONFIRMED result is a likely outcome and will be reported as such. The analysis is run once, after the last 2028 festival's data is available. If notifications are missing for more than a third of planned units, the test is extended to 2029 under the same rules. That decision is taken before looking at any outcome.

## Still to do before 2027 data exists
- Extend src/new_states_v1.py to event years 2027–2028 (configuration only) and commit it.
- Obtain the 2027 official notifications (usually published in December 2026) and enter them.
- The author records this draft on OSF.

The analysis code is src/prospective_2027_analysis_v1.py (written now; tested on synthetic data only).
