# Out-of-time check (EXPLORATORY)

- **Calibration:** 2015–2020 only, for the seven new states.
- **Crossover:** simulated at those early parameters.
- **Comparison:** observed typed-minus-pooled lead-1 MASE on 2021–2025 forecasts only.

## Agreement in direction (`agreement_by_model.csv`)
| Model | Agreement |
|---|---|
| Ridge | 5/7 |
| SARIMAX | 5/7 |
| Chronos-2, TimesFM-3, LightGBM | 4/7 |

The same-years figure (7/7 for ridge) therefore overstated the predictive value.

The two ridge/SARIMAX misses:
- **Rajasthan:** early h = 0.17, just below its crossover of 0.21, so a borderline call. Observed: typed better.
- **Madhya Pradesh:** early h = 0, so pooled was predicted. Observed ridge difference −0.007 ± 0.007, which is essentially zero.

5 of 7 is not statistically distinguishable from chance (one-sided sign test p ≈ 0.23). The fair summary is: "directionally consistent, not demonstrated out of sample".
