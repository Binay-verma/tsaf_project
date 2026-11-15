# Robustness experiments: results against the pre-committed predictions (EXPLORATORY)

Lead 1, both registered state-level tests; balanced typed minus pooled MASE (positive favours pooling). At W = 730 with the registered parameters the experiment reproduces the registered forecasts exactly (checked on one state-year before the run). Files: window.csv, noise.csv, ridge_alpha.csv, predictions_vs_results.json.

| Prediction | First test | Second test |
|---|---|---|
| W1 leaf-2 LightGBM: typed - pooled falls as the window grows (2021-2025) | held: +0.0068, -0.0027, -0.0061 (730, 1460, 2190 days) | held: +0.0162, +0.0115, +0.0108 |
| W2 tuned LightGBM: typed used at 2190 days and difference falls | held: +0.0150, +0.0136, +0.0098; typed = calendar in 100%, 71%, 46% of state-years | **failed** (not monotone): +0.0133, +0.0145, +0.0030; typed = calendar in 100%, 91%, 74% |
| W3 Ridge: typed - pooled falls with the window | **failed**: -0.0212, -0.0198, -0.0215 | **failed**: -0.0047, -0.0055, -0.0052 |
| H1 Ridge hybrid within 0.005 of the better arm (730 days) | held (+0.0002) | held (0.0000) |
| H2 leaf-2 hybrid closer to pooled than to typed | held | held |
| N1 date noise (20% of anchors moved one day) moves typed - pooled towards pooling | Ridge held in both seeds (+0.0152, +0.0067); leaf-2 held in one seed (+0.0011) and **failed** in the other (-0.0042) | Ridge held (+0.0021, +0.0135); leaf-2 **failed** in both (-0.0081, -0.0055) |
| A1 Ridge sign unchanged for alpha 0.1 to 100 | held (-0.0148 to -0.0132) | **failed**: all within 0.003 of zero, +0.00002 at alpha 10 |

Across every window and both tests, the hybrid arm (typed flags plus the pooled flag) was within 0.0002 MASE of, or better than, the better of typed and pooled for Ridge and both LightGBMs.
