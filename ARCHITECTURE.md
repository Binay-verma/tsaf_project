# Project architecture

The project is a forecasting experiment, with an offline HTML results report.

1. **Source data**: attributed raw daily state energy-met CSV; newer snapshot remains separate.
2. **Loader and quality flags**: chronological daily index, observed targets retained, nonpositive or conflicting values treated as missing.
3. **Causal inputs**: missing historical inputs use prior-week or prior-day values only. Missing targets never become scored labels.
4. **Known calendar inputs**: ordinary calendar, state holiday flag and main Diwali windows; date verification status recorded.
5. **Prediction engines**: last value, repeated previous week, direct ridge models, SARIMAX and pretrained Chronos-2.
6. **Evaluation**: common scheduled origins, days 1/7/14, observed-label MAE and training-scaled MASE; identical model coverage checked.
7. **Outputs**: per-origin predictions, state metrics, macro comparisons, descriptive paired intervals, plots, checks and HTML report.

Model fitting uses 730 pre-2022 days. For each later origin, ridge input lags and SARIMAX latent state can incorporate observations available before that origin. Chronos receives the most recent 730 days but no parameter fine-tuning. Its quantile median is used as the point forecast. Direct ridge models predict each horizon from origin history and target-date calendar, while SARIMAX and Chronos forecast the full 14-day path; no future observed targets are provided inside that path.

2022 is the development year. The schedule, features and model parameters were fixed before this build's 2023 scoring. The prior exploratory pilot did not score 2023. Because the benchmark includes few scheduled dates and one main Diwali per year, the held-out result is preliminary evidence rather than a broad generalisation claim.
