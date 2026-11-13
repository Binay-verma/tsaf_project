# Simulation v2: calibrated typed-vs-pooled simulation

Synthetic data only. The design (`src/simulation_typed_pooled_v2.py`) was committed before the run and before the registered new-states analysis. The calibration comes from `results/simulation_calibration_v1/`, which uses the original three-state panel only: mean festival effect −9.6%, heterogeneity h = 0.46 (90% year-bootstrap band 0.30–0.69), AR coefficient 0.92, innovation sd 3.6, occurrence noise 0.21.

Parts A–C ran locally. Part D (Chronos-2, TimesFM-3) runs on Kaggle (`docs/reproduction/SIMULATION_FM_KAGGLE.md`). After it, rerun `summarise` so the foundation-model points are added to the figure.

## A. Ridge at the calibrated parameters (`summary.csv`, part A; 200 replications)
- **Crossover:** typed starts to beat pooled at h ≈ 0.23 (`crossover.csv`). That is below the lower end of the calibrated band.
- **At the calibrated h = 0.46:** typed is better by 0.16 MASE, in all 200 replications.
- **At h = 0 (identical effects):** pooled is better by 0.03.

## B. Crossover map, ridge (`crossover.csv`; 50 replications per cell)
The crossover h rises when festival effects are small relative to noise:

| Effect size | Noise | Crossover h |
|---|---|---|
| −15% | low | 0.05 |
| −3% | high | 0.87 |

For the calibrated effect size (−9.6%), the crossover is 0.05, 0.24 and 0.32 at noise sd 2, 3.6 and 6.

## C. Tree leaf minimum (`leaf_by_year.csv`; 30 replications per cell)
Each typed flag is on for one training day per training year; the pooled flag is on five times as often. The pooled advantage follows the leaf minimum, as expected:

| Leaf minimum | Pattern |
|---|---|
| 5 | Pooled better by ~0.6 MASE while there are 2–4 training years. The advantage falls to ~0.03 from 5 years, when typed flags first reach 5 days. |
| 10 | Pooled better by 0.5–0.8 until year 10; at 10 years typed is slightly better (−0.11). |
| 20 | No difference at 2–3 years (neither flag is usable: pooled is on 10–15 days). Pooled better from 4 years (pooled reaches 20 days); typed never reaches 20 days in this window. |
| 2 | Pooled slightly better (≈ +0.1) at the calibrated h. Typed better only at h ≥ 1. |

## Limits
- The generator's weekly and annual shapes are stylised, with five families at one day each.
- The calibration uses three states. Its h band reflects year-to-year uncertainty only.
- Results are about mechanisms. They are not evidence for or against the registered hypotheses H1–H3.
