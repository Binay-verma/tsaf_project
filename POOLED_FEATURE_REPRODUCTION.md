# Pooled versus separate festival features

This follows the completed added-feature study without changing its results, calendars or prospective freeze. The user authorized the next research phase and pushing completed checkpoints to the existing GitHub repository. No new source data, weights, dependencies or future actuals are needed.

## Fixed comparison

`results/pooled_festival_v1/registration.json` and `event/protocol.json` / `non_event/protocol.json` were written before any new pooled fits or inference. These are exploratory historical protocols, not external preregistrations or clean final tests. Previous typed-feature outcomes had already been inspected.

Each cohort preserves its parent's 72 cases: 24 target dates across family/state/year groups, evaluated at individual leads 1/7/14. The non-event family is a pairing label. All six model variants run every new arm; all parameters, fit schedules, 730-day histories, original annual scale denominators, actual weight hashes and missingness rules remain fixed. Calendar/typed-day/typed-window predictions are reused from the hash-checked parent combined files, rather than refit.

The five new arms are:

| Arm | Extra inputs |
| --- | --- |
| pooled_day1 | One logical-union flag for all documented state-scoped family anchors |
| pooled_day5 | The same flag in channel 1 plus four exact-zero channels |
| pooled_window1 | One logical-union flag for the existing ±3-day family windows |
| pooled_window5 | The same window flag plus four exact-zero channels |
| zero1 | One exact-zero channel |

No date is selected from electricity outcomes. Overlapping anchors/windows remain binary unions. The five-channel typed/pool comparison holds dimension fixed, while changing signal allocation and pooling of historical examples. It is not a causal intervention on identity. One versus five pooled channels checks padding sensitivity; the zero1/calendar contrast shows that a zero channel need not be inert.

New forecasts planned: 2 cohorts × 6 variants × 5 arms × 72 cases = 4,320. With the 2,592 reused calendar/typed forecasts, the final comparison contains 6,912 rows. These are related historical predictions, not independent replications. No wider-window or all-day foundation evaluation is added here.

## Commands and safeguards

Use the existing Python 3.12 `.venv`, pinned packages and local model caches. Preparation and completed workers refuse overwriting. Do not run the following over finished directories; explicitly version source/output paths for a fresh reproduction.

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -q
.venv/bin/python src/pooled_festival_experiment.py prepare
.venv/bin/python src/score_pooled_uncertainty.py prepare

# Each worker runs once in each cohort. The executed launch logs are retained.
.venv/bin/python src/pooled_festival_experiment.py ridge --cohort event
# Workers: ridge, lightgbm, lightgbm_capacity2, sarimax, chronos, timesfm
# Cohorts: event, non_event

.venv/bin/python src/finalize_pooled_festival.py
.venv/bin/python src/audit_pooled_festival.py
.venv/bin/python src/audit_pooled_inputs_fits.py
.venv/bin/python src/score_pooled_uncertainty.py score
.venv/bin/python src/audit_pooled_uncertainty.py
```

The wrapper assigns output/arm/frame overrides to the existing engine. Both classical case files deliberately contain the same 72 primary cases. This prevents accidentally advertising the parent 528-case secondary window coverage. The finalizer demands all six variants and every arm/case, checks protocol/prediction hashes and preserves all results. It does not take a successful-forecast intersection or select winners for deployment.

The independent stdlib audit reconstructs source labels, scale denominators, complete-case sets, reused/new predictions, state/year/family weighting and paired differences. Another independent date/NumPy implementation reconstructs foundation input bytes and checks fitting budgets, label hashes, cutoffs and actual active-feature support. These are internal software checks, not an independent human review or pretraining/source clearance.

## Native uncertainty analysis

`probabilistic_protocol.json` was fixed while inference was running, before pooled score tables, as an explicitly secondary exploratory analysis. Both models supply the common native 0.1–0.9 quantile grid; no interpolation, recalibration, sorting or clipping. Report mean scaled pinball, inclusive central-80% coverage/miss rates, width, interval score, and a one-interval WIS with the native median. This WIS is not a full-distribution score over all native levels. Invalid endpoints remain explicit and propagate undefined interval aggregates. All-native crossing counts remain separate from crossings on the nine-level common grid.

Coverage uses only 24 target dates per lead in each small historical cohort, with correlated states and two years. It does not certify calibration or allow comparison with a differently nominal 90% residual interval based on coverage alone. Proper scores and width accompany coverage. A separate stdlib audit checks arithmetic and macro weights.

## Separate clean scalar reproduction and retained discrepancy

`/workspace/tsfm-clean-review/bin/python src/review_pooled_baselines.py` uses a separate environment with no inherited system packages and independently constructs lag/rolling/calendar/event features. Dates are the first 2024 event target per state, at all three leads, all five new arms and three regression variants: 135 forecast checks. Every forecast matches within tolerance (maximum difference 7.617×10⁻¹² GWh); every fitting-label vector matches exactly.

The **overall strict review is `discrepancies_retained`, exit 1**. Only 30/45 training matrices per tree variant match byte-for-byte; the 15 Delhi examples differ. `diagnose_pooled_numerics.py` localizes this to one near-zero `trend_7_28` entry in each of the three checked Delhi blocks. The maximum float32 difference is 1.421×10⁻¹⁴ GWh. Other checked state tree blocks match exactly. Float64 history differences reach 4.099×10⁻¹¹ GWh. The original review, failure status and diagnostic remain saved; no matrices, parameters or scientific forecasts were changed to force a pass. Agreement on these examples does not guarantee agreement on every forecast, and float32 conversion alone does not ensure byte-identical features.

An initial in-progress handoff/log sentence overstated matrix agreement before the strict result was inspected. It was immediately corrected; the review artifact always retained the discrepancy. Do not describe this phase as a complete clean-room pass.

## Remaining boundaries

All historical labels are already development/exploratory for new methods. Annual-as-issued calendars remain incomplete as amendment histories. Source reuse and processing/report-day clarification await the curator; the author reports sending email manually. Historical/proxy overlap, sparse events and source revisions remain unresolved. Independent human review and untouched/source-independent confirmation remain open. The original frozen future forecasts and deliberately paused scoring workflow are preserved. Completion must be established by run/audit artifacts, not this command list.
