# Simulation v3: matched to the empirical pipeline (EXPLORATORY)

Written after the registered analysis; the design (src/simulation_typed_pooled_v3.py) was committed before running. v2 reproduced directions, but its effect sizes were about ten times the observed ones. v3 changes only three things, to match the empirical protocol:
1. **Window profile:** each festival's effect is spread over its ±3-day window, using the profile measured on Delhi, Karnataka and Maharashtra. Relative to the festival day: day +1 is 0.64, day +2 is 0.30, day +3 is 0.13; the three days before are small, from −0.14 to +0.07 of the festival-day effect.
2. **Training window:** models are refitted monthly on the 730 days before the refit month, instead of on all earlier years.
3. **Scoring:** every day of the ±3-day window is scored, not only the festival day.

The calibration (three original states) is unchanged from v2.

## Result at the calibrated heterogeneity h = 0.46 (summary.csv)
| Model | Simulated typed − pooled | Observed |
|---|---|---|
| Ridge | −0.0133 (MC se 0.0011) | Stage A −0.0109; new states −0.0154 |
| LightGBM, min leaf 20 | 0.0000 in every replication (typed flags never usable) | Stage B and new states: Stable LightGBM's typed arm equals its calendar arm |
| LightGBM, min leaf 5 | +0.084 | — |
| Stable LightGBM (selected leaf 5 or 20) | at the lead-1 share of leaf 5: Stage A 2022–2025 7/12 → about +0.049; new states 35/63 → about +0.047 | Stage A +0.043; new states +0.018 (2.6× smaller than implied) |
| LightGBM, min leaf 2 | +0.031 | Stage A +0.046; Stage B +0.065; new states +0.0068 |

**Ridge crossover.** Ridge typed flags start to win between h = 0.25 (+0.006) and h = 0.46 (−0.013). At h = 0 pooling is better (+0.012).

**Reading.** Once the simulation matches the empirical training window, scoring set and festival profile, it reproduces the sizes observed in the calibration states as well as the directions. The ten-fold gap in v2 came from those three mismatches. The new-states effects are smaller than the simulated ones for the trees, consistent with their lower average festival heterogeneity and effect sizes.

**Limits.** Stylised seasonality. The calibration uses three states. LightGBM hyperparameters other than the leaf size are fixed.

## How v3 came about, and what that means (added after an internal review)
- **Post hoc.** v3 was specified after the registered analysis and after seeing that v2's sizes were about ten times too large. Its stated aim was to match the pipeline. The design was committed before the single run, but the choice to build it was not made blind.
- **In-sample comparison.** The calibration, the window profile and the Stage A comparator all use the same three states and overlapping years. The Ridge and Stable LightGBM matches are therefore in-sample. The out-of-sample comparison is the new states: there the simulated tree effects are 2.6× (Stable LightGBM) and about 4.5× (leaf 2) larger than observed.
- **Effect scale.** μ is the festival-day effect, estimated with a festival-day flag. The profile keeps the festival day at weight 1 and adds the measured neighbouring-day effects, which also exist in the data but were not part of μ.
- **Per-state predictions.** Out-of-time predictions for each further state, using each state's own 2015–2020 parameters: results/simulation_states_v3.
