# Third pass on v10 (HEAD 27cd327), read-only

Numbers verified against files: Ridge -0.0133 vs -0.0109; leaf-5 +0.0837; leaf-2 +0.0306; leaf-20 = 0; 0.524 = 99/189 fits with min_child_samples 5 (selected.csv); 0.524 x 0.0837 = 0.0438; Spearman values and p in spearman.csv; Gujarat Diwali -27%, Holi -23%, Dussehra -3.6%; profile 0.637; one run of 950 rows (v3 raw.csv). Stage A +0.0429/+0.0458, Stage B +0.0648, new states +0.0181/+0.0068 match the tables.

## Errors and overclaims, most serious first

1. **Section 4.4 is now false for the version actually described in 5.8.** It says "The simulation designs of Section 5.8 were committed, by author timestamp, before they were run and before the new-states analysis". The second-version simulation in 5.8 is v3: design commit 82bfaa7 at 22:16 UTC on 14 Nov, after the registered analysis (21:28) and after v2's size mismatch was seen. Only v2's design (6d7714b, 13 Nov) pre-dates the analysis. Fix: "the first version's design pre-dates the analysis; the second was specified after the analysis and after the first version's sizes were seen to be too large; it was run once."

2. **"Reproduces the sizes" (Abstract last sentence; Contribution 4 wording is narrower; 5.8 "reproduces the observed sizes as well") is overstated.**
   - Ridge: matches Stage A (-0.0133 vs -0.0109) and the new-states value (-0.0154) is also close. This is the only clean match.
   - Stable LightGBM: the +0.0438 vs +0.0429 agreement is partly coincidental. The 52% leaf-5 mix is the new-states mix over all leads, but it is compared with the Stage A value. The Stage A selection (longer_panel_stage_a_v1_selection_tree/selected.csv) has 67% leaf 5 overall and 83% at lead 1, which implies about +0.07 (1.6x observed). With the new-states lead-1 mix (55.6%) the implied value is +0.0465 against +0.0181 observed (2.6x too large). The text itself reports +0.0181 and so shows the mismatch, but still says "reproduces".
   - Leaf 2: simulated +0.031 against +0.0458, +0.0648 and +0.0068; the new-states value is 4.5x smaller. Simulated values lie inside the range of the observed ones, which is not a size test.
   - SARIMAX, TimesFM-3 and Chronos-2 are not simulated, yet the Abstract says "local-model differences" (SARIMAX is a local model). Fix: "reproduces the size of the Ridge result in the calibration states and the order of magnitude (within a factor of about 2-4) of the tree results".

3. **v3 forking-paths / in-sample issue must be disclosed.**
   - v3 was designed after v2's mismatch with observed sizes, with matching sizes as the goal, and was run once. 5.8 mentions the ten-fold mismatch but not that the changes were chosen with that knowledge.
   - The comparator (Stage A, 2022-2025, Delhi/Karnataka/Maharashtra) uses the same states and overlapping years (2017-2025) used for calibration (simulation_calibration_v1: log-demand regression on 2017-2025), and the window profile is also measured on those three states. The Ridge and Stable-LightGBM Stage A matches are therefore in-sample. The only out-of-sample comparison is the new states (trees off by 2.6-4.5x).
   - mu was estimated with a one-day flag per family; v3 spreads the same mu over a window with weights summing to 2.07 (1 + 0.637 + 0.299 + 0.133, design.json). Calibration was not redone for the changed generator ("calibration unchanged", v3 README). Mention as a limit.
   - README minor: "days before about 0" but the measured profile has -0.14 at day -2.
   A legitimate fidelity fix, but disclose it as exploratory tuning, not validation.

4. **Table 15 / Figure 4 thresholds come from the superseded simulator.** The per-state crossovers h* (0.14-0.82) and the 0.23 in v2 summary.csv come from the version whose sizes the text now says were wrong by 10x. In v3 the Ridge crossover is between h = 0.25 (+0.006) and 0.46 (-0.013) for the calibrated mu/noise, i.e. at the lower edge of the calibrated band (0.30), not 0.23 below it. Section 5.9 "States" still says Tamil Nadu and Gujarat are "above their simulated threshold" and the 5/7 and 7/7 agreements depend on those thresholds. Either recompute thresholds with v3 or state that Table 15 uses the first-version simulator.

5. **Festival-level analysis: caveats missing or misleading.**
   - The 27 pairs sit in 7 states and are not independent. My recomputation within states (state-demeaned deviation and outcome, same script data): Ridge same-years rho -0.35 (p 0.075), out-of-time -0.25 (p 0.21); SARIMAX -0.10 and -0.01. Excluding Gujarat and Tamil Nadu: Ridge same-years -0.61, out-of-time -0.17; SARIMAX same-years -0.36, out-of-time -0.07. So the relation is mainly between states (the same Gujarat/Tamil Nadu/Rajasthan signal as Table 15), not "within-state festivals that differ more gain more". Say so, and add the clustering caveat.
   - Same-years circularity: the effects are estimated on the scored years; named only implicitly ("Measuring ... on 2015-2020 keeps the Ridge relation"). Say it for the first pair of numbers.
   - Multiplicity: 12 tests (6 models x 2 designs). Only the out-of-time Bonferroni (over 6) is mentioned: 0.16 for Ridge, and the SARIMAX same-years Bonferroni is 0.051, not shown. "SARIMAX (-0.50, p 0.008)" is unadjusted.
   - "keeps the Ridge relation (-0.43, p 0.027; 0.16 after Bonferroni)": acceptable, but it is a unadjusted-level finding only; the Intro (Contribution 4) says "festival-level data show the linear-model gain growing with how much a festival effect differs", which is too strong (SARIMAX out-of-time n.s.; within-state n.s.).
   - TimesFM-3 "relation reverses (+0.42, p 0.028), so it does not use the flags like a regression": Bonferroni 0.17, same-years +0.12 (n.s.), and the claim concerns lead 1 where TimesFM has no typed/pooled difference. Downgrade to "points the other way (unadjusted p 0.028; not significant after Bonferroni)"; delete the inference.
   - "This accounts for Gujarat ... one shared flag fits it worst": by the file's own deviation measure Tamil Nadu is as bad or worse (mean deviation 0.091 vs 0.095; max 0.182 vs 0.143; sum 0.364 vs 0.286). Tamil Nadu's Diwali effect (-27.2%) equals Gujarat's (-27.4%). Replace "accounts for" with "is consistent with", and drop "fits it worst" (or say "among the worst").
   - The text calls the pair statistic "correlated" for SARIMAX at p 0.008 without noting the two-sided test and that the mechanism predicts a direction only.

6. **Abstract wording "did not survive restricting calendars to official sources"** is a registered fact, but 5.7 now says the sensitivity mainly reflects which states remain (two southern states), not calendar quality. The Abstract reads as a calendar-quality failure. Use "did not hold in the official-sources-only subset, which keeps mainly two southern states". The Abstract also omits the without-2020-2021 result (H1 not significant, effect unchanged).

7. **N1-N5 fix check.**
   - N1: partly (official-only added; COVID not mentioned in Abstract; see 6).
   - N2: fixed (no "northern and western"; Table 16 now "meets rule").
   - N3: fixed ("no later than 14:02 UTC").
   - N4: fixed in 5.7 ("same decisions", untested in other states).
   - N5: NOT fixed. Section 9 still says "the default LightGBM"; Abstract uses "LightGBM with a larger leaf size" (fine) but Sections 5.2-5.8 say "Stable LightGBM". The "0.5-0.7" phrase is gone.
   - Pass-2 point 3 (5.3 cross-reference to 5.7): fixed.

8. **Minor inconsistencies.**
   - Figure 3 right: the single "Stable LightGBM" cross at +0.043 sits between the leaf-5 bar (+0.084) and the leaf-20 position (0), and the simulated mixture (+0.044, or +0.07/+0.047 with the matching mix) is not drawn; add a mixture bar or label the cross's comparator. The Ridge cross at h = 0.46 is placed at the calibrated h by construction.
   - 5.8 calls the new simulation "a second version" while repo and summary name are v2/v3 (v1 existed); say "version 3 (second calibrated version)" or cite the result folders.
   - Section 8 simulation sentence says only "written after the registered analysis"; add "specified after the first version's sizes were seen, run once, and matches the calibration states in-sample; tree sizes in the new states are 2.6-4.5x too large".
   - Section 5.8 closing sentence "(its designs committed before each run)" is true by author timestamp for v2 and v3 designs but contradicts the 4.4 sentence in item 1; harmonise.

## No problem found
- Gujarat Diwali/Holi/Dussehra values; 27 pairs; spearman and Bonferroni numbers (SARIMAX p 0.0085 shown as 0.008); 0.524; 0.0438; v3 single run with 950 rows; Table 16; 5.3 cross-reference.
