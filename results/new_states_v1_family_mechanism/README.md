# Festival-level test of the heterogeneity mechanism (EXPLORATORY)

Written and run after the registered analysis. Unit: 27 state-family pairs in the seven further states.

**Predictor:** the absolute deviation of a festival's estimated demand effect from its state's mean festival effect.
**Outcome:** observed typed − pooled lead-1 MASE.

The mechanism predicts a negative correlation for models that fit one coefficient per flag: festivals that differ more from the average should gain more from their own flag.

| Design | Ridge | SARIMAX | Trees | Chronos-2 | TimesFM-3 |
|---|---|---|---|---|---|
| Same years (2017–2025) | ρ −0.68 (p 0.0001; Bonferroni 0.0006) | −0.50 (0.009; 0.051) | ≈ 0 | ≈ 0 | +0.12 |
| Out of time (effects 2015–20, outcomes 2021–25) | −0.43 (0.027; 0.16) | −0.27 (0.18) | ≈ 0 to +0.28 | +0.27 | **+0.42 (0.028; 0.17)** |

## Reading (revised after an internal review)
- **Within states the relation is weak.** Removing each state's mean (`within_state_and_without_GJ_TN.csv`): Ridge ρ −0.35 on the same years (p 0.075) and −0.25 out of time (p 0.21); SARIMAX about 0. The relation above is therefore mainly between states, driven by Gujarat and Tamil Nadu. These are the two states with the most heterogeneous festival effects and the largest typed gains. Without them, Ridge is −0.61 on the same years but −0.17 out of time.
- **Multiplicity.** Twelve correlations were computed (6 models × 2 designs). The same-years design is partly circular, because effects and gains come from the same years.
- **TimesFM-3.** The out-of-time ρ +0.42 is not robust: the same-years value is +0.12, and Bonferroni gives 0.17. Lead 1 shows no TimesFM typed/pooled difference on average. No conclusion is drawn about how TimesFM-3 uses flags.
- **Gujarat and Tamil Nadu.** Both have strongly heterogeneous festival effects. Gujarat: Diwali −27%, Holi −23%, Dussehra −4%. Tamil Nadu: Diwali −27%, others −0.5% to −5%. Both show large Ridge gains from typing. This is consistent with the heterogeneity mechanism, but with seven states it does not establish it.
- **Uttar Pradesh.** It has almost no mean festival effect.
