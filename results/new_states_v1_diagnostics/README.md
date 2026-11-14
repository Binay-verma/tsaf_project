# Diagnostics for the registered new-states analysis (EXPLORATORY)

Written and run after the registered analysis. The registered decisions (H1 CONFIRMED, H2 NOT CONFIRMED, H3 CONFIRMED) are unchanged. The script reuses the registered `load`, `clusters` and `signflip`, with 100k sign-flip draws.

| Check | File | Result |
|---|---|---|
| Leave one state out (7) and one year out (9) | leave_one_out.csv | **H1:** direction kept 16/16, p < 0.05 in 15/16 (fails only without Gujarat, p 0.23). **H3:** direction kept 16/16, p < 0.05 in 14/16 (not without Gujarat 0.33, AP 0.07). **H2:** direction kept 8/16, no consistent effect. |
| Horizons 1, 7, 14 | by_horizon.csv | **SARIMAX:** typed better at all three (−0.010, −0.014, −0.013). **TimesFM-3:** no difference at lead 1 (the registered horizon) but typed clearly better at 7 and 14 days (−0.078, −0.079; p 0.005, 0.0005). This holds in both separate Kaggle cohorts (2017–20: −0.135/−0.106; 2021–25: −0.091/−0.111) and is concentrated in the high-heterogeneity states (Gujarat −0.56, Tamil Nadu −0.26 at 14 days; about 0 in AP, MP, UP, Telangana). Not a registered test. |
| Physical units, lead 1 | physical_units.csv | **Typed vs pooled:** ridge saves 0.33 GWh per festival day (0.12 percentage points of a 3.4% error); SARIMAX saves 0.20 GWh. **Scale:** mean demand 257 GWh/day per state. |
| Power | power.csv | **Minimum detectable effect, 80% power, 45 clusters:** 0.011 (H1), 0.0125 (H2), 0.0073 (H3) MASE. **H1:** observed 0.0097, below its MDE, so the study had limited power for an effect this size. **H2:** effects of 0.0125 or more in the registered direction would very likely have been detected. |
| Against zero-flag and placebo controls | against_controls.csv | **Placebo flags:** no effect for any model (p ≥ 0.1). **Default LightGBM:** typed flags change nothing at all (day5 − zero5 = 0.0000, p = 1), the mechanism the simulation predicts (min leaf 20, flags on ≤ 10 training days); pooled flags help it (−0.018). **Ridge, SARIMAX, leaf-2 LightGBM:** both typed and pooled beat no flags. |
