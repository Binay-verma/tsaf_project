# Simulation: when do typed event flags beat a pooled flag?

Synthetic data only. The design is in `src/simulation_typed_pooled_v1.py` (committed as 02e14cd before the run). It is independent of the registered new-states study: it uses no real data and no new-states results.

## Setup
- **Data:** daily synthetic demand, 2015–2025, with five event families occurring one day per year at shifting dates.
- **True effects:** each family's effect is mu·(1 + h·z_k), with mu = −6%. **h** is how different the families are (h = 0 means identical). **omega** adds occurrence-to-occurrence noise that no flag can explain.
- **Protocol:** each event year 2017–2025, train on all earlier days, then forecast that year's event days one day ahead. The arms are typed (5 flags) and pooled (1 flag + 4 zero columns).
- **Error:** MASE with a 730-day weekly scale (724 days in 2017).
- **Outcome:** typed minus pooled MASE, averaged over family-years. Negative means typed is better.
- **Replications:** ridge 200 per setting; each LightGBM variant 50 per setting. LightGBM hyperparameters are fixed, not tuned.

## Results (`summary.csv`, figure `typed_vs_pooled_simulation.png`)
| Model | Result |
|---|---|
| **Ridge** | Pooled is slightly better only when effects are nearly identical: h = 0, +0.03 (omega 0) and +0.07 (omega 0.5). Typed wins from about h = 0.25 (omega 0) or h ≈ 0.4 (omega 0.5), and the gain grows steadily with h (h = 2: −2.5 MASE). |
| **LightGBM, default min_child_samples = 20** | Pooled is better in every setting and every replication (+0.55 to +0.89). A typed flag is on for at most ~10 training days, fewer than the 20 needed for a leaf, so the trees can never use it. The pooled flag is on for up to ~50 days, so it can be used. The gap grows with training length, because the pooled flag crosses that threshold while the typed flags never do. |
| **LightGBM, min_child_samples = 2** | Pooled is slightly better (+0.08 to +0.13) until h ≈ 1. Typed wins only at h = 2 (−0.12 to −0.14). |

**Main finding:** whether typing helps depends on two things together: how different the true event effects are, and whether the model can actually use a rarely-on flag. For a linear model, typing pays off once effects differ even modestly. For tree models, the minimum leaf size can decide the comparison regardless of how different the effects are.

## Limits
- The parameters (mu, noise, h grid, LightGBM settings) were chosen by us, so the crossover points are illustrative, not estimates for Indian demand.
- One-day flags only; lagged values are observed (one-step-ahead); no window flags; no SARIMAX.
- Foundation models (Chronos-2, TimesFM-3) are not simulated. Their covariate handling cannot be reproduced with a simple generator, so the simulation says nothing about H2.
