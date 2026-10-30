# Rich histories and annual/monthly refits v1

Completed exploratory comparison: 891 validation fits, 162 chosen configurations,
1998 deployment fits and 107,244 forecasts. No failed fits.
All new configurations exactly match the historical Chronos history-only 8,937 state/origin/lead cases.
Data and original expanded results remain unchanged.

The protocol was recorded before these new results. All 2024–2026 outcomes were already development evidence.
Each state/year/mode/lead/model selects parameters using a chronological 180-day pre-year block,
with fitting targets strictly before validation origins. Parameters stay frozen for the entire evaluation year,
for both annual and monthly schedules. Deployment labels end before each refit date. Thus monthly versus annual
changes the refit schedule, not the annual hyperparameter budget. Rich history has 27 causal lag/rolling/trend
and target-aligned annual-lag features; calendar and regional modes add 13 and 20 known calendar channels.
LightGBM uses eight grid points; Ridge uses three alphas. This is a stronger explicit baseline budget,
not proof of the strongest attainable local forecast.

## Partial 2026 macro MASE

Lower is better. Every configuration has the same 288 origins per state/lead. Scores use identical fixed
pre-year scales; monthly retraining does not change the denominator. Leads are individual target days.

| model | mode | schedule | 1 | 7 | 14 |
| --- | --- | --- | --- | --- | --- |
| lightgbm | rich_calendar | annual | 0.6971 | 1.6917 | 2.1215 |
| lightgbm | rich_calendar | monthly | 0.6205 | 1.4861 | 1.8494 |
| lightgbm | rich_history | annual | 0.7087 | 1.5952 | 1.9236 |
| lightgbm | rich_history | monthly | 0.6904 | 1.5583 | 1.8610 |
| lightgbm | rich_regional | annual | 0.7021 | 1.7118 | 2.1215 |
| lightgbm | rich_regional | monthly | 0.6221 | 1.4940 | 1.8494 |
| ridge | rich_calendar | annual | 0.5954 | 1.4910 | 1.8358 |
| ridge | rich_calendar | monthly | 0.5416 | 1.3115 | 1.5098 |
| ridge | rich_history | annual | 0.5705 | 1.3955 | 1.5900 |
| ridge | rich_history | monthly | 0.5569 | 1.2978 | 1.4818 |
| ridge | rich_regional | annual | 0.5882 | 1.4920 | 1.8366 |
| ridge | rich_regional | monthly | 0.5395 | 1.3121 | 1.5105 |

For reference, matched history-only Chronos macro MASE is 0.4679 / 1.1629 / 1.3617 at leads 1/7/14.
These are descriptive deployment-policy comparisons, not architecture-isolated or significance claims.
Monthly rich-calendar Ridge improves over annual at all three 2026 leads (0.5416/1.3115/1.5098
versus 0.5954/1.4910/1.8358), but does not beat the recorded Chronos macro scores.
LightGBM still does not establish superiority, despite richer histories and monthly updates.

## Festival and refit failures of generalisation

Monthly refitting is not universally helpful. In 2024, regional Ridge lead-14 event MASE worsens from
1.347 to 1.731; in 2025, calendar LightGBM lead-14 event MASE worsens from 1.423 to 2.241.
Do not select a refit schedule on those event outcomes and present it as a clean test. The two event years
and three related states provide weak independent evidence; no row-level significance test is performed.
Full state/year and event/non-event metrics, selected parameters, all validation losses, deployment cutoffs,
runtime and source/code/protocol hashes are retained. No weather or real-time vintage reconstruction is claimed.

## Reproduce/audit

`.venv/bin/python src/test_robust_baselines.py` and `.venv/bin/python src/audit_phase2.py`.
The runner refuses to overwrite completed/interrupted fit artifacts; create a new versioned output/protocol
and use `--out` for a new run. Existing forecasts are not rewritten by this report generator.
