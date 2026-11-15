# Pass 5: review of the restructured v11 (15 November 2026), and what was done

A referee-style check of manuscript/journal_v11 after the restructure (new related-work section, sections and tables renumbered, Appendix D added).

**No errors found** in section, table, figure or citation cross-references. The builder asserts all of them.

## Findings and fixes
| # | Finding | Fix |
|---|---|---|
| 1 | Appendix D named wrong or vague scripts (F1, F3/F4, T2, T3/T4, T5, T9, T11, "as Table above") and said every folder has a README (many do not) | Map rewritten with the script that wrote each folder. The intro now says each row names the folder and its script. |
| 2 | T16 (official plus confirmed rows) had no committed script | src/new_states_official_plus_confirmed_v1.py added. A rerun reproduces all three files exactly (numeric difference 0, same decisions, same 119 cells). |
| 3 | The −9.9% festival-day effect (with neighbouring days) had no saved source | src/window_profile_v1.py and results/window_profile_v1. It gives −0.0991 and the generator's profile to three decimals. The text now reads the value from the file. |
| 4 | Related work went beyond its sources: Hong & Fan; GIFT-Eval; "univariate" for Moirai; Roberts & White; Prophet; Micci-Barreca / Pargent; Efron–Morris; Probst; sign-flip symmetry; Boylan; M4; citation "[18] [10]" | Each sentence reworded to what the source states. |
| 5 | Section 7 said "training days" where LightGBM counts rows | Now says rows, and that a row is a day because each tree model is fitted to one state. |
| 6 | The SARIMAX simulation paragraph was silent on size | It now says the simulated gain is about 3.6× smaller than in Stage A, that Tamil Nadu is over-predicted, and that this is supporting evidence, not a test. |
| 7 | README overstated two things: the Stage B leaf-2 result called "confirmed", and the simulation agreement. It also pointed to v10 | Corrected. The leaf-2 result is descriptive (p 0.020, 2 of 3 years). The simulation row is given with its limits. Links now point to v11. |
| 8 | Seedcheck README gave Ridge Pearson 0.89 (actual 0.8846) | Changed to 0.88, here and in the overnight audit. |

The review also listed a vague "discussed below" pointer. It no longer appears in the v11 text, so nothing was changed.
