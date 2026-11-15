# Second registered test, seven more states: design DRAFT (not registered)

Status: draft written on 15 November 2026; design (R1, R2, M1, M2 and the state rule) approved by the author on the evening of 15 November 2026. Not yet registered. Calendar procedure below added after approval, before any parameter selection or forecast. No parameter selection or forecast for these states has been made. No electricity outcome for them has been evaluated. The only use of their data so far is a count of missing or zero days.

## Why
The first registered test (osf.io/yw7mr) confirmed H1 (SARIMAX typed better) and H3 (leaf-2 LightGBM pooled better). Both rest mainly on Gujarat, and the follow-ups suggest why: typing helps where a state's festivals differ strongly in effect. That explanation was found after looking at the data. This test checks it, and replicates H1 and H3, on states the project has never used.

## States (fixed rule, no outcomes used)
Every state not yet used in the project whose mean daily energy met (Grid-India, 2015–2025) is at least 70 GWh: **Punjab, Haryana, West Bengal, Kerala, Bihar, Odisha, Chhattisgarh.** Smaller states (Jharkhand, Assam, Uttarakhand, Himachal Pradesh, J&K, Goa) are excluded because their series are noisier relative to festival effects.

Data quality (counted 15 Nov 2026): missing or zero days are 8 (2015), 3 (2016), 0–1 per year from 2017 for all seven. This is the same pattern as the first test.

## Families and calendars
These are the same five families and the same unchanged code: Holi, Dussehra, Ganesh_Chaturthi, Ugadi_Gudi_Padwa and Diwali. Durga Puja enters through its Dussehra (Vijaya Dashami) day. Festivals outside the five (Onam, Chhath, Bihu, Vishu, Pongal) are not added, because that would change the registered code.

Calendar conventions 1–6 of review/new_states_v1/DESIGN_DRAFT.md apply unchanged. Every row is checked by the author before registration. A family is in scope where the state notifies it as a public holiday in most years.

## Hypotheses (lead 1, day flags, typed minus pooled event MASE; registered pipeline unchanged)
- **R1 (replicates H1):** SARIMAX typed better. Event years 2017–2025, with the same test and decision rule as osf.io/yw7mr: family-year clusters, sign-flip, Holm, at least 6 of 9 years.
- **R2 (replicates H3):** leaf-2 LightGBM pooled better. Same rule.
- **M1 (mechanism):** each state's festival-effect heterogeneity h is estimated from 2015–2020 demand only, with the method of src/simulation_calibration_v3_timesplit.py. In the three states with the highest h, Ridge typed − pooled < 0 over 2021–2025 (state-family-year units, sign-flip).
- **M2 (mechanism, gradient):** across the seven states, the early-period h (2015–2020) is negatively rank-correlated with the mean Ridge typed − pooled lead-1 MASE over 2021–2025 (higher h, more typed-favouring). One-sided permutation test over all 7! = 5040 orderings (Spearman correlation). The three-versus-four split first drafted here was dropped: it allows only 35 assignments, so its smallest possible p (1/35 = 0.029) could not pass a Holm correction over four hypotheses.
- Holm across R1, R2, M1 and M2.

Secondary, reported but not used for decisions: Ridge and Stable LightGBM at lead 1; leads 7 and 14; zero and placebo controls; the 2020–2021 and official-source sensitivities, as before.

TimesFM-3 and Chronos-2 are left out of the confirmatory set because of time. They may be run afterwards as exploratory.

## Still open (author)
1. Approve the state rule and hypotheses. M1 and M2 can be changed now, before registration, but not after.
2. Check every calendar row.
3. Register on OSF before any selection or forecast.
4. Power: computed from the first test's spread once the calendar fixes the number of clusters, and added here before registration.

## Timeline
- Calendar candidates: 1–2 days (machine search).
- Author check: depends on the author.
- Registration: same day.
- Local runs: under a day.
- Analysis: run once.

## Calendar procedure (added 15 November 2026, before any forecast; the author checks it before registration)
- Only the main festival day of each family and year is used. The extra days some states add (second Holi day, Bhai Dooj, Vishwakarma Day) are not used. The first study did use extra Diwali days, so this differs slightly.
- Each counted festival day was compared with the dates the author verified for the same family and year in the first study (src/new_states_v2_calendar_triage_v1.py). Of 231 counted days, 209 match, 11 differ by one day and 11 have no date (weekend or conflicting sources). The author checks the 22 non-matching rows one by one and a random sample of 21 matching rows (3 per state, seed 20261115).
- Agreement with other states corroborates the festival day, not the state's own notification. The registration will say so.
- Weekend rule (convention 3 of the first study) applies unchanged.

## Calendar check result (15 November 2026, evening)
- The author filled the short workbook: 22 decision rows and 21 spot-check rows (triage/author_decisions.csv).
- Spot-check found 2 errors in 21 (Odisha 2020 Holi and West Bengal 2020 Holi: the triage date was the earlier of two reference days, the states hold Holi on the later day). Rule adopted: for Holi the state's Holi (Rangwali) day is used, not the eve. Five more matched Holi rows with the same pattern (Odisha 2018, 2023; West Bengal 2016, 2017, 2023) are proposed for the later day and wait for the author's confirmation.
- Open: Kerala 2015 Dussehra (no author status); Chhattisgarh 2022 Dussehra (spot-check, no status).
- Resolved on 15 November 2026: Kerala 2015 Dussehra = 23 Oct (author, from a screenshot of a regional-holiday list); Chhattisgarh 2022 Dussehra = 5 Oct (author). Only the five proposed Holi rows await confirmation.
