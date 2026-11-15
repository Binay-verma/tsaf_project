# Reproducibility rerun of the per-state simulation (stable seeds)

The original run (results/simulation_states_v3) seeded each state with Python's `hash(state)`, which is randomised per process, so it cannot be reproduced exactly. This rerun uses `zlib.crc32(state)` and is reproducible (`python src/simulation_states_v3.py --stable-seed`). It is the version cited in the paper.

**Agreement with the original run.** Predicted sizes differ by at most 0.008, which is Monte Carlo noise. Thresholds differ by up to 0.12 in states with h = 0, where the simulated Ridge curve is flat.

## State-level agreement, predicted (2015–2020 parameters) vs observed 2021–2025 (`state_level_correlations.csv`)
| | Ridge → Ridge | Ridge → SARIMAX | Leaf 2 → leaf 2 | Stable mix → Stable LightGBM |
|---|---|---|---|---|
| All 7 states, Pearson (Spearman) | 0.88 (0.75) | 0.55 (0.64) | 0.89 (0.86) | 0.80 (0.36) |
| Without Gujarat | 0.86 (0.60) | 0.44 | 0.65 (0.77) | 0.45 (−0.03) |
| Without Gujarat and Tamil Nadu | 0.32 (0.30) | 0.03 | 0.92 (0.90) | 0.97 (0.70) |

**Reading:**
- The Ridge agreement rests on Gujarat and Tamil Nadu.
- The leaf-2 agreement survives removing them.
- Sign misses: Tamil Nadu for both tree models (predicted pooled advantage, observed typed advantage), and Rajasthan for Ridge (predicted +0.012, observed −0.049; its 2015–2020 h of 0.17 is about half its threshold).

**Ridge direction.** Agreement is 4 of the 6 states with a defined threshold; Uttar Pradesh, with no mean festival effect, is predicted pooled by default and observed pooled. The direction counts for leaf 2 and TimesFM-3 in `summary.json` use the Ridge direction as the target, which is not meaningful for those models, so they are not cited.

The original run's results are kept unchanged in results/simulation_states_v3.
