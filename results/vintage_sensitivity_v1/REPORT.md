# Recorded-source availability sensitivity v1

Completed retrospective two-date panel:48 fresh inference tasks and672 forecast-day predictions,
three states, issue dates1September/1October2026, history/calendar modes, both pinned TSFMs.
The protocol was recorded before these new outcomes. No future prospective observations were retrieved.

At midnight India time, the last recorded Git snapshot before the issue cutoff ends30August or28September:
two/three calendar days behind the issue date. The ideal retrospective scenario instead supplies observations
through issue−1. The available-context scenario never fabricates those missing trailing labels; it starts
forecasting after the last recorded label and extends the horizon so BOTH scenarios score the same14
issue-relative target dates. Forecast-origin and issue-relative leads are saved separately. All inputs and
fitting choices remain past-only; no calibration or feature selection is performed on these cases.

## Mean scaled error over all14 target days

Equal state/issue weighting. This table is not the earlier all-year lead1/7/14 benchmark.

| model | mode | git_snapshot_at_India_midnight | ideal_retrospective | increase_pct |
| --- | --- | --- | --- | --- |
| chronos2 | calendar | 1.8413 | 1.7263 | 6.6657 |
| chronos2 | history | 1.7667 | 1.5873 | 11.3014 |
| timesfm3 | calendar | 1.4545 | 1.3996 | 3.9224 |
| timesfm3 | history | 1.4282 | 1.3353 | 6.9523 |

The recorded-lag scenario has larger mean error in each tested model/mode, with increases about3.9%–11.3%.
Only two issue dates were tested; this is not a causal/general operational-performance claim.

Recorded Git timestamps are not certified first-publication times. Sparse archive evidence establishes
some older snapshots but not every origin-time release. This study models the observed Git snapshots,
not all possible reporting channels. Historical revisions and source-day conventions require separate review.
The first post-period prospective episode remains frozen and unscored; this sensitivity cannot retune it.
