# Transfer after removing direct own-family fitting labels

Completed exploratory study: `results/festival_label_transfer_v2`. Fixed Ridge alpha10 and two fixed tree budgets (7leaves,200estimators,lambda10; leaf minimum20or2). No event-exposed validation-selected parameters are reused. All three feature forms and all three row policies are reported on the same event and matched non-event cases.

**Earlier electricity history remains available. This is not fully unseen-event exposure.** The evaluated family's direct fitting labels within±3days are removed, while lag/rolling predictors can still contain older festival responses. A same-count control removes eligible ordinary labels matched by weekday, year, training availability and holiday exclusions.

MASE is error, lower is better. The table uses the event-anchor cohort and equal state/year/family weighting. Each row has the same cases across arms.

| Fixed model | Lead | Calendar, family labels excluded | Pooled flag, family labels excluded | Pooled flag, matched ordinary labels excluded |
| --- | ---: | ---: | ---: | ---: |
| Ridge alpha10 |1|1.30951|0.71060|0.60301|
| Ridge alpha10 |7|1.18662|1.33987|1.36308|
| Ridge alpha10 |14|1.21157|1.52931|1.46352|
| Tree leaf2 |1|1.28728|1.01676|0.88787|
| Tree leaf2 |7|1.24388|1.11386|1.06552|
| Tree leaf2 |14|1.57566|1.43248|1.33650|
| Tree leaf20 |1|1.30805|1.30805|1.29638|
| Tree leaf20 |7|1.23955|1.23955|1.26834|
| Tree leaf20 |14|1.62237|1.62237|1.44588|

Pooled information can help after direct own-family labels are removed, but the finding is conditional: Ridge helps next day and hurts at leads7/14; the leaf2tree helps these aggregate event scores, while the leaf20tree ignores the sparse indicators. Removing actual family examples generally has a different effect from removing equally many ordinary examples. Neither a universal transfer benefit nor a causal festival mechanism follows.

All3workers completed3,888forecasts from3,807fits. An independent date/NumPy/log/score audit passes: exact case sets, retained labels and their bytes, own-family typed support of zero, fixed parameters, chronological cutoffs, equal training-row counts, source labels/scales and macro contrasts. All686protectedpriorfiles remain unchanged.

Version1aborted at an exact-control matching guard for2022-08-28; its partial fits, predictions and traceback remain. Version2extends the fixed matching range from28–42to28–84days and preflights all141training blocks before protocol/model execution. The largest actual match is70days; greater distance weakens seasonal comparability. Complete distances are inventoried. The first slow auditor was interrupted, its execution source/traceback retained, and repeated date plans were memoized without changing the matching rules or scientific outputs.

The source is still retrospectively compiled; historical/proxy exposure, source processing/reuse, amendment certification, independent human review and untouched/source-independent confirmation remain open. No new foundation inference or foundation pretraining-exposure test is implied by this classical study. Frozen prospective predictions and the paused workflow remain unchanged.

Full tables, non-event costs and all families/years: [REPORT.md](results/festival_label_transfer_v2/REPORT.md). Exact protocol and failed version are retained beside the results.
