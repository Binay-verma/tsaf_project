# Note: the v1 NYC analysis is incomplete

Recorded 7 November 2026, after `analysis/` was written. The registered NYC filter `scenario == 'lag7'` keeps only Chronos-2 and TimesFM-3, because the local models' rows in `results/mta_holiday_recovery_v1/analysis/event_window/predictions_compared.csv` have no scenario label. The NYC summary therefore covers 12 cells, not 36. The India results use a different filter and are unaffected.

The v1 outputs are kept unchanged. `results/representation_combination_v2` repeats the analysis with the only change being that the NYC filter also keeps rows with an empty scenario label. It was registered before its outputs were computed; the NYC local-model combination results had not been computed before.
