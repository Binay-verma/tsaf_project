# Version2 tree numerical-contract study

A separate scalar implementation and pandas rolling features agree to about2.4e-11 but produce different
float64 LightGBM split decisions. Eight of twelve checked tree forecasts fail the original tight tolerance;
the largest discrepancy is4.2798GWh. Identical production arrays give exactly equal1/2-thread forecasts,
so thread count is not the demonstrated cause. Ridge examples and parameter-choice IDs reproduce, but
one validation loss and several tree forecasts do not. These failed checks are preserved in provenance_review_v1.

The mitigation was recorded before new version2 outcomes: cast the complete prescribed feature matrix,
including queries, to float32 before any tree fitting/prediction. No features/grid/score-selected changes
are made. This is a NEW numerical contract, not a silent rewrite of version1 or frozen future forecasts.
648 past-only validation fits,81 selected configurations,999 deployment fits and53622 predictions completed.
Seventeen parameter choices differ from version1 through the same pre-year validation rule; no evaluation
error chooses between the contracts.

The separate implementation in a clean environment reproduces all12 checked version2 tree forecasts and
three selected configurations exactly (max difference0). This is bounded software evidence by the same
assistant, not an independent expert or proof that all future implementations/hardware will match.

## Partial2026 macro MASE

| mode | schedule | 1 | 7 | 14 |
| --- | --- | --- | --- | --- |
| rich_calendar | annual | 0.6944 | 1.6890 | 2.1338 |
| rich_calendar | monthly | 0.6220 | 1.4916 | 1.8456 |
| rich_history | annual | 0.7537 | 1.5883 | 1.9271 |
| rich_history | monthly | 0.7197 | 1.5543 | 1.8650 |
| rich_regional | annual | 0.6991 | 1.7613 | 2.1338 |
| rich_regional | monthly | 0.6200 | 1.4823 | 1.8456 |

Original version1 forecasts remain historical evidence. Version2 does not establish a superior model;
the point is an explicit reproducible arithmetic interface. See clean review hashes/package versions,
including SciPy1.18.1 in the separate environment versus1.17.0 in the original numerical stack.

## Retained runner failure

All forecasts and metrics completed, but final run-metadata writing failed because a relative output path
was passed to an absolute-root hash formatter. The original traceback and execution-time runner source
are retained. The wrapper now resolves paths before delegation. `audit_stable_tree.py` independently
checked completed outputs and reconstructed run metadata without rerunning fits or modifying predictions.
Total wall time was not fabricated; deployment-fit duration sum is recorded instead. This packaging failure
is distinct from model-fit failures. No failed scientific comparison is hidden or waived.
