# Ten-state calibration and per-state prediction (EXPLORATORY)

Written and run after the registered new-states analysis (`results/new_states_v1/analysis`). Nothing here is confirmatory, and nothing registered was changed.

## Calibration (`calibration_by_state.csv`)
Each state is calibrated separately: original Delhi, Karnataka, Maharashtra; new UP, Rajasthan, MP, Gujarat, Telangana, AP, Tamil Nadu. The method is that of `simulation_calibration_v1`, on 2017–2025, with a 300-draw year bootstrap for h.
- **Uttar Pradesh:** shows no average festival effect (mu ≈ 0), so its h is undefined in practice.
- **Per-state bands:** wide where a state has only three families.
- **Crossover:** each state's crossover h* is simulated at its own effect size, noise and persistence (ridge, 30 replications per grid point).

## Prediction vs observed, same years (`predicted_vs_observed_new_states.csv`, figure right panel)
"Typed" is predicted when h > h*. Observed is typed-minus-pooled lead-1 MASE per state on the registered forecasts.
- **Ridge:** the direction agrees in 7 of 7 new states.
- **SARIMAX:** 6 of 7.

**Caveat:** h is measured on the same 2017–2025 years that are scored, so this agreement is partly circular. The out-of-time check is in `results/simulation_calibration_v3_timesplit/`.

## Notes
The figure was redrawn once after the run to cap the x-axis at 2.5 and label Uttar Pradesh. The data were unchanged.
