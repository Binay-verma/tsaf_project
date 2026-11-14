# Festival-level test of the heterogeneity mechanism (EXPLORATORY)

Written and run after the registered analysis. Unit: 27 state-family pairs in the seven further states.

**Predictor:** the absolute deviation of a festival's estimated demand effect from its state's mean festival effect.
**Outcome:** observed typed − pooled lead-1 MASE.

The mechanism predicts a negative correlation for models that fit one coefficient per flag: festivals that differ more from the average should gain more from their own flag.

| Design | Ridge | SARIMAX | Trees | Chronos-2 | TimesFM-3 |
|---|---|---|---|---|---|
| Same years (2017–2025) | ρ −0.68 (p 0.0001; Bonferroni 0.0006) | −0.50 (0.009; 0.051) | ≈ 0 | ≈ 0 | +0.12 |
| Out of time (effects 2015–20, outcomes 2021–25) | −0.43 (0.027; 0.16) | −0.27 (0.18) | ≈ 0 to +0.28 | +0.27 | **+0.42 (0.028; 0.17)** |

## Reading
**Ridge.** The mechanism holds for Ridge out of time at the unadjusted level, but not after Bonferroni.

**SARIMAX.** Same direction, weaker.

**Trees.** No relation, as expected: their use of flags is limited by leaf size, not by effect differences.

**TimesFM-3.** Goes the other way. Festivals that differ more from the average do relatively better with a pooled flag, so TimesFM-3 does not appear to use covariates like a regression. This is consistent with H2's direction for heterogeneous festivals, though H2 was not confirmed overall.

**Gujarat.** It has the largest festival effects in the panel (Diwali −27%, Holi −23%) but a small Dussehra effect (−4%), so a single pooled flag fits it worst. That is why the confirmed linear-model results rest on Gujarat.

**Uttar Pradesh.** It has almost no festival effect (mean ≈ 0), so it has nothing to gain from typing.
