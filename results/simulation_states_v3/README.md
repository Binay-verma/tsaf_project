# Per-state, out-of-time predictions from the pipeline-matched simulation (EXPLORATORY)

Written after the registered analysis; the design (src/simulation_states_v3.py) was committed before the single run.

**Method.** For each further state, the simulation of results/simulation_typed_pooled_v3 (window profile, 730-day monthly refits, all window days scored) is run with that state's parameters, estimated on 2015–2020 only. It predicts:
- the Ridge threshold h* and direction;
- typed − pooled for Ridge, LightGBM leaf 2 and leaf 5.

These are compared with the observed 2021–2025 typed − pooled lead-1 MASE from the registered forecasts.

## Results (`predicted_vs_observed_2021_2025.csv`, `state_level_correlations.csv`, `summary.json`)
| Quantity | Predicted (mean over 7 states) | Observed 2021–2025 |
|---|---|---|
| Ridge | −0.011 | −0.027 |
| LightGBM leaf 2 | +0.016 | +0.012 |
| Stable LightGBM (56% leaf 5 at lead 1 → 0.556 × leaf-5 prediction) | +0.028 | +0.024 |

**State-level agreement of sizes:**

| Predicted | Observed | Pearson r (p) | Spearman (p) |
|---|---|---|---|
| Ridge | Ridge | 0.88 (0.009) | 0.79 (0.036) |
| Ridge | SARIMAX | 0.54 (0.21) | 0.57 (0.18) |
| Leaf 2 | Leaf-2 LightGBM | 0.91 (0.004) | 0.89 (0.007) |
| Stable mix | Stable LightGBM | 0.82 (0.025) | 0.36 (0.43) |

**Direction for Ridge.** Typed is predicted in Gujarat and Tamil Nadu only, and the prediction matches the observed direction in 5 of 7 states. The misses are Rajasthan (h 0.17 against a threshold of 0.32; observed typed better) and Madhya Pradesh (observed −0.007, about 0).

## Reading
**What this shows.** With parameters measured before 2021, the pipeline-matched simulation predicts which states gain from typing and by roughly how much, for Ridge and for trees. The earlier 2.6–4.5× gap for trees came from applying the three original states' parameters to the new states.

**Limits:**
- seven states, and the correlations are driven by Gujarat and Tamil Nadu;
- the simulator was designed after the registered analysis;
- SARIMAX and the foundation models are not simulated;
- Uttar Pradesh had a positive mean effect in 2015–2020, so it has no threshold.

## Note added later
The seeds used Python's `hash(state)`, which is randomised per process, so this run cannot be reproduced exactly. A rerun with stable seeds is in results/simulation_states_v3_seedcheck (differences ≤ 0.008), and that rerun is the one cited in the paper. The `summary.json` direction counts for leaf 2 and TimesFM-3 use the Ridge target and are not meaningful.
