# Referee-style check of manuscript/journal_v10/MANUSCRIPT.md (new and changed text)

Method: recomputed Tables 12, 12b, 13, 14, 15 and the Section 5.9 numbers from results/new_states_v1/analysis, results/new_states_v1_diagnostics, results/simulation_*; checked git log (author and committer dates), the calendar CSV, the independent-check CSVs and the figures.

## A. Numbers verified (no error found)
- Tables 12, 12b, 13, 14: all values match analysis/*.csv, balanced.csv, diagnostics/by_horizon.csv and physical_units.csv.
- Table 15: h, band, h*, Ridge and SARIMAX values match simulation_calibration_v2 (calibration_by_state.csv, predicted_vs_observed_new_states.csv).
- 5,157 cases, 45 clusters, 5.33 states per cluster; 331 rows = 90 official/government + 241 repost; 85 cells = 38+36+9+2, and 74 = TN+Telangana.
- Registration 13:27:32 UTC (c987d7e); analysis 21:28 UTC; the script hash is unchanged since registration.
- Leave-one-out counts (16/16, 15; 16/16, 14; 8/16); MDE 0.0109 vs 0.0097; 257 GWh.
- Sim crossover 0.23, 200/200 replications, L=5 drop at five years, L=20 never usable; 5/7 (sign test p about 0.23).
- Independent recomputation: effects and decisions identical.

## B. Clear errors and internal inconsistencies

1. **Section 5.8, Abstract, Highlights, Section 9 ("a calibrated simulation explains the pattern", "explains when typing pays off").** The simulation does not cover SARIMAX (simulation_typed_pooled_v1/README "Limits": "no SARIMAX"; v2 summary.csv has only models ridge and lightgbm). SARIMAX is the confirmed H1. It does not cover TimesFM-3 or Chronos-2 either (Part D never run; commit 8cd0e8f "not yet run"). The Section 8 limitation "covers the local models only" is therefore wrong: it covers Ridge and LightGBM. "Calibrated" is also directional only. At the calibrated parameters Ridge typed-minus-pooled is -0.16 MASE (summary.csv, part A, h=0.462). Observed Ridge on the three calibration states is -0.0054 (Delhi), -0.0073 (Karnataka) and -0.0154 (Maharashtra), I recomputed these from longer_panel_stage_a_v1/event_window/ridge, 2022-2025, lead 1. Pooled over the three states it is -0.0109, p 0.196, 2 of 4 years, Table 3. That is about 15 times smaller, and Section 5.2 says "Ridge shows no ordering". Trees: the simulated pooled advantage is +0.6 to +0.8 MASE (leaf_by_year.csv), against +0.018 (new states) and +0.043 (Stage A) observed. Fix: replace "explains" with "is consistent in direction with"; state that SARIMAX and the foundation models are not simulated; say that simulated magnitudes exceed observed ones by an order of magnitude; correct Section 8 to "Ridge and LightGBM only, one-day flags, one-step-ahead". Table 15 and Figure 4 also omit the three calibration states, where the simulation predicts typed for all three (h > h* in calibration_by_state.csv) while Stage A Ridge found no ordering; add them or say why they are omitted.

2. **Section 8 is stale after v10.**
   - "The evidence covers three states, five festival families and a few hundred festival days": it is now ten states and 5,157 cases.
   - "the SARIMAX result is not yet shown for Delhi or Karnataka or for event years evaluated only after registration": the registered seven-state test now covers this, so the sentence is misleading.
   - "the TimesFM-3 pooling preference was not registered as a hypothesis": it was (H2) and failed (-0.0004).
   - "The registration order rests on local commit history": the new states also have an OSF registration.
   Fix these sentences.

3. **TimesFM-3 failure is not propagated to v9 text.** Contribution 2 (Intro) still says "LightGBM and TimesFM-3 do better with one pooled flag (Sections 5.2 and 5.3)". Section 5.3 reports +0.0506, Holm p 0.017, and says its preference for pooling "is not explained by a minimum leaf size", with no pointer to the failed registered replication (-0.0004, 3 of 9 years, Section 5.7). Add "not replicated in the seven further states (Section 5.7)" to Contribution 2 and to the end of Section 5.3. The title ("answer depends on the model class") is now only partly supported: Table 15 shows a stronger state dependence for Ridge, and TimesFM at lead 1 shows no ordering.

4. **Section 6 contradicts the abstract and Section 5.8 on the tree criterion.** Section 6: "set on more training days than their minimum leaf size". Abstract: "at least as many training days as their minimum leaf size". Section 5.8: "cannot split until there are L training years", so L days suffice (README C: L=5 pooled advantage vanishes at exactly five years). Section 9 uses "fewer than", which is consistent with "at least". Fix Section 6 to "at least as many".

5. **Figure 4 caption.** It says "the seven further states", but the right panel shows six x-positions: Uttar Pradesh is missing because it has no crossover. The caption also does not say that the crossover is for linear models, while the panel plots leaf-2 LightGBM and TimesFM-3 as well. Gujarat leaf-2 (+0.065) and TimesFM (+0.041) are on the opposite side of the linear prediction. Left panel: the ticks are called "bar" in the caption; the arrows for Telangana and UP are truncated at 2.5 (bands to 3.49 and 12.47) without comment. Fig. 3 right has no y-axis label and the caption omits that it is at calibrated h = 0.462.

6. **"per festival day" (Abstract, Section 5.9, Table 14 header).** The GWh figures are mean absolute-error differences over all target days in the ±3-day windows at lead 1 (event_window/primary_cases.csv has 7 to 9 target dates per state-family-year per lead; src/new_states_diagnostics_v1.py averages abs_err over those cases). They are not per festival day. Also "typed flags save Ridge 0.33 GWh" is relative to pooled flags, not to no flags. Fix: "per festival-window day, typed relative to pooled".

## C. Overclaim and wording a referee will attack (most serious first)

7. **Both confirmed results hinge on Gujarat, and the text understates it.** Section 5.9: "both lose significance when Gujarat is removed". diagnostics/leave_one_out.csv: H1 -0.0097 -> -0.0029 (p 0.225); H3 +0.0068 -> +0.0011 (p 0.334), i.e. about 70% and 84% of the effect disappears. Gujarat has 44 of 44 rows from reposts, some from aggregators (officeholidays.com "NOT a transcription", portalseven), and is removed completely in the official-source sensitivity. Gujarat's own Ridge/SARIMAX gaps are -0.093/-0.076 (Table 15). Also the leave-one-out p-values are unadjusted one-sided with 100k draws; the text says "p below 0.05 in 15" without saying they are not Holm-adjusted (for example H1 without Madhya Pradesh: p 0.0427 would not pass Holm). Fix: state the effect without Gujarat, say that the p-values are unadjusted, and say in Abstract and Section 9 that the confirmed effects depend on one state whose calendar has no official source row.

8. **"sensitive to the COVID years" (Section 9) and "did not hold without 2020-2021" (Abstract), "does not survive removing 2020-2021" (Section 8).** sensitivity_without_2020_2021.csv: effect -0.0086 vs -0.0097 in the main analysis, same sign, raw one-sided p 0.0575, Holm 0.115 with 35 clusters instead of 45. The years 2020 (-0.011) and 2021 (-0.016) are not outliers, and leave-one-year-out for each of 2020 and 2021 keeps p < 0.05 (0.028, 0.034). The loss of significance reflects fewer clusters (power), not COVID driving the effect. Fix: "was no longer significant without 2020-2021 (effect -0.0086, Holm p 0.115); the effect size is unchanged". Delete "sensitive to COVID" or justify it.

9. **Per-state heterogeneity claims (Section 5.9, Section 6, Section 9, Abstract).**
   - Only Tamil Nadu (1.26-1.63 vs h* 0.20) and Gujarat (0.61-0.80 vs 0.14) have h bands entirely above h*. "Well above their simulated threshold" is wrong for Rajasthan (band 0.15-0.86 includes values below 0.23). AP, MP, Telangana and UP bands all straddle their thresholds (or h* is undefined), so the "pooled" calls are not distinguishable from "typed". The bands reflect only year-bootstrap uncertainty (README) and come from three to five family effects.
   - The 7/7 agreement is circular, as the text says. For the four "pooled" states the Ridge differences are +0.0060 (se 0.019), +0.0120 (se 0.0066), +0.0125 (se 0.011), +0.0162 (se 0.0065), so they are weak support. The out-of-time agreement is 5/7 (sign-test p about 0.23), and 4/7 for TimesFM, Chronos-2 and default LightGBM (agreement_by_model.csv). For SARIMAX the heterogeneity rule fails in MP (typed better at h=0).
   - Despite that, Section 6 ("which can be checked on past data by estimating each festival's effect") and Section 9 ("A forecaster can estimate how much festival effects differ on past data before choosing") give this as advice, and the Abstract ("larger in states whose festivals differ") and Section 9 ("several times the average") state it without the word "exploratory". Fix: label as exploratory and not validated out of sample; drop or hedge the advice; note that the Ridge gain in Tamil Nadu and Gujarat comes from two states.

10. **TimesFM-3 at leads 7 and 14 ("does clearly better with typed flags").**
    - It is one of 18 model-by-lead cells (diagnostics/by_horizon.csv). Bonferroni over 18 turns p=0.0053 (lead 7) into 0.096; only lead 14 (p 0.0005, 0.009 adjusted) survives. "Clearly" is too strong.
    - The new-states foundation runs have no zero-channel or placebo arm (Table 13 caption), and the pooled arm is one flag plus four all-zero channels. Commit 8cd0e8f drops all-zero padding columns for the foundation models in the simulation, suggesting the zero-padded encoding can matter. So the long-lead typed advantage may reflect the encoding or channel count rather than festival information. Say so.
    - The per-cohort figures in diagnostics/README.md (2017-20: -0.135/-0.106; 2021-25: -0.091/-0.111) do not reproduce. Cluster-mean recomputation from predictions.csv gives -0.090/-0.067 (2017-20) and -0.069/-0.088 (2021-25). The sign agrees in both cohorts, so the manuscript sentence ("in both cohorts") is right, but the README numbers need fixing or explaining.

11. **Registration chronology (Section 4.4, Intro item 3).**
    - "committed at 13:27 UTC ... before any parameter selection or forecast ..., and registered on OSF": OSF_REGISTRATION.md says OSF submission came "after the registered parameter selection had started". The commit history agrees: ridge selection d7c66b3 author 13:43 and tree selection 3a525a3 14:00, OSF record 60eb856 14:02. REGISTRATION.md said the order would be push, OSF, then selection. The deviation is minor (selection used the ordinary calendar only, no flags) but must be disclosed, since the OSF stamp is the only external timestamp.
    - Eight commits (d7c66b3 ... 487fd4a: parameter selection, local forecasts, both simulation designs and results) have committer dates of 14 Nov 23:00 +0530 but author dates of 13 Nov 13:43-18:55 UTC, i.e. history was rewritten or rebased. The sim v1 README cites commit 02e14cd, which exists as an object but is not reachable from HEAD (the current equivalent is c96d30e). "Simulation designs were committed before they were run" rests on author dates only; the existing "local commit history" caveat should be extended to cover this.
    - The v2 design commit already contains the three-state calibration results (calibration.json), so "fixed before running" applies to the simulation, not the calibration.

12. **Calendar provenance (Section 3.5).**
    - "conventions fixed in advance": DESIGN_DRAFT.md says the conventions were "decided while sourcing (before any forecast)", and commits f43c2fd (amendment convention refined) and b310e26 (rows 72, 78 corrected, row 60 aligned) changed them during checking. Write "fixed before any forecast".
    - "secondary reposts of the notifications" is too generous. Document titles include calendar aggregators (officeholidays.com, portalseven, greytHR) and news items. check_method for all 331 rows reads "per-row method not recorded", and the author's verification of 331 rows spans commits 707a93b (12:48) to 8680c59 (13:23), about 35 minutes. Say "secondary sources (reposts, news items, calendar aggregators); per-row verification method not recorded".
    - review/new_states_v1/official_source_search_2026-11-15/README.md (post-analysis) found 4 matches (Rajasthan 2025), 1 difference and 0 confirmations for 236+ rows, because portals are blocked. This is worth one sentence, since the sensitivity could not be improved.

13. **Shrinkage across stages not discussed (Section 5.7/5.9, Section 8).** SARIMAX typed-minus-pooled: -0.030 (Stage A), -0.054 (Stage B), -0.0097 (new states). Leaf-2 LightGBM: +0.046, +0.065 (secondary), +0.0068. The registration (DESIGN_DRAFT, REGISTRATION.md) expected power about 0.9 at the Stage A effect. The observed H1 (0.0097) is below the MDE (0.0109; 0.0130 with Holm worst case). Section 5.9 notes only "limited power". Add that the confirmed effects are about a third (H1) and a seventh (H3) of the earlier estimates (selection or winner's-curse effect in Stage A).

## D. Judgement calls and minor points

14. **Prospective test (Section 5.9, Section 9, Data availability).** "is specified in the repository" and "A test ... is specified": REGISTRATION_DRAFT.md says "draft for the author's approval", not yet on OSF, and "no 2027 notification existed" is unverified (some state 2027 lists may already be published). Say "a draft protocol (not yet registered)". Its own MDE table says P1 power is probably below 80%.

15. **Section 7 vs 4.4 wording.** 4.4 says "independent recomputation"; Section 7 says "internal software checks, not independent review". The recomputation was by a second AI agent reading the same predictions.csv files and using the same seed, so it checks only the analysis step, not forecasts. Harmonise. "p-values differ at most 0.0012" holds for raw p; one Holm value differs by 0.0026 (independent_check/README) and should be stated.

16. **Table 14 caption** "(exploratory except the lead-1 rows tested in Table 12)": only SARIMAX, TimesFM-3 and leaf-2 lead-1 were tested; Ridge, Stable LightGBM and Chronos-2 lead-1 were "reported, not tested" (protocol.json). Reword.

17. **Table 12b and Section 5.7 on the official-only sensitivity.** The text omits that H3 reversed sign (-0.0074) and that "contradicted" uses an unadjusted one-sided p (decision rule in protocol.json) with no year criterion. Add "unadjusted".

18. **Simulation scope in Section 5.8.** "in all 200 replications" describes Monte Carlo replications at fixed point estimates, not parameter uncertainty (at h=0.30, the lower band edge, the gap is only -0.037, summary.csv). The mapping from "training years" in the simulation to the empirical 730-day training window (typed flag on at most 4 days) should be explicit, because Section 8 and Section 5.2 use the 730-day window.

## E. Areas with nothing wrong
- Abstract, Highlights, Table 12/12b/13/14/15 numerical values.
- Decision-rule description in Section 5.7 (6 of 9 years, Holm, contradicted rule).
- Section 4.3 additions (1,000,000 draws, seed, (k+1)/(N+1)).
- 85 cells, 74 from TN and Telangana, and the NOTE_RUN erratum handling.
- Recovered Kaggle files and hash claim (NOTE_RECOVERY.md).
- Frozen script hash.
