# TimesFM-3 on the second-test states: prediction written BEFORE any run (EXPLORATORY)

Written on 16 November 2026, after both registered state-level tests were analysed and before any TimesFM-3 forecast for the second-test states existed. Not part of the registered second test (osf.io/f9tv4), which used local models only. Committed before the hosted run.

Source of the prediction: in the first test, TimesFM-3 did better with typed day flags than with the pooled flag without padding at leads 7 and 14 (-0.0604 and -0.0636; results/new_states_v1_fm_control), an exploratory finding that rests mainly on Gujarat and Tamil Nadu.

Arms: typed day flags (day5) and the pooled day flag without zero padding (pooled1). Same pinned weights, runner, cases (3,969, 36 family-year clusters) and ledgers as the registered second test.

## Predictions
- **F1 (main):** averaged over leads 7 and 14, typed minus pooled1 MASE is negative (typed better), one-sided sign-flip p < 0.05 over the 36 family-year clusters (1,000,000 draws, seed 20261116), with a negative year mean in at least 6 of 9 years.
- **F2:** at lead 1, |typed minus pooled1| < 0.01.
- Expectation stated in advance: because the first-test effect rested on two states with strongly different festival effects, and the second-test states mostly have smaller festival effects, F1 may well fail; a failure will be reported as such.

Analysis: `python src/new_states_v2_fm_v1.py analyse`, run once after both cohorts finish.
