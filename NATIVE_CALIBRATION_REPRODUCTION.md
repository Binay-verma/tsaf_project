# Interval calibration and separate prospective annex

Continue the existing checkout/pinned environment. All earlier data, scientific outputs, source code, decks and integrated manuscript remain unchanged under a1,039-file protection manifest. The new phase uses the same frozen source through28October2026and previously audited local TimesFM weights. No future actual retrieval or model fine-tuning is required.

## Registered methods and case coverage

`results/native_calibration_v1/protocol.json` was written before its new calibration outcomes. Its source-hash and design-hash guards prevent silently changing inputs. A separate annex registration fixed all future postprocessing methods before historical calibration comparisons. The data were already inspected, so this is not external preregistration or a clean historical test.

Perconfiguration/state/individual lead, nonconformity is max(native lower−actual, actual−native upper). Use the finite-sample ceil((n+1)×0.8) order statistic, clamped at zero to prevent shrinking. FrozenSeptember uses16labels15–30September; expanding uses all available label dates strictly before query **origin**, not merely before target. Both methods remain in every table/annex; no best-looking arm or window is selected.

Historical target dates14–28October follow the month boundary and maximum14-day lead, ensuring at least16available calibration labels. The common four-configuration, three-lead cohort yields1,620intervalrows. The all14lead TimesFM extension yields3,780rows including810overlap; totalunique4,590. Newly retaining all lead days requires342TimesFMcontext/mode tasks on the exact parent contexts, producing3,696native rows and reproducing792parent rows. Chronos reuse is restricted to its three archived leads. Temporal dependence, short calibration blocks and changing contexts prevent a time-series coverage guarantee.

## Audit existing outputs

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -q
.venv/bin/python src/audit_calibration_inputs.py
.venv/bin/python src/audit_native_calibration.py
.venv/bin/python src/score_interval_annex.py
```

53tests pass in working and separate no-system-package environments. New tests address label-date/origin purging, current/future-label perturbations, frozen-block invariance, finite-sample ranks/no shrinking, inadequate sample rejection, early scoring and missing/duplicate/nonpositive labels. Separate audits reconstruct every task input, earlier point/quantile rows, source labels/scales, calibration dates/ranks, interval arithmetic/macro weights and the prospective annex. These are internal software checks, not independent human review or proof of distributional calibration.

Before12NovemberUTC, the prospective scorer printsPENDING without opening actuals or making a request. No future score or actual snapshot is generated now. After the complete period and once the ORIGINAL collector has preserved its first complete audited actual snapshot, use the commands in the annex README. The new scorer uses that exact same vintage/receipt, units/completeness/clock/hash/source-code checks, first-annex-Git-commit equality and no-overwrite guards. It does not download a new favourable vintage after viewing errors. Automation remains paused.

## Execution entry points — do not rerun completed workers

Preparation, workers, analysis and freeze deliberately refuse overwriting. A fresh reproduction requires explicitly versioned paths/source identities, not deletion of evidence.

```bash
.venv/bin/python src/native_interval_calibration.py prepare
.venv/bin/python src/native_interval_calibration.py hindcast
.venv/bin/python src/native_interval_calibration.py analyze
.venv/bin/python src/native_interval_calibration.py freeze_annex
.venv/bin/python src/report_native_calibration.py
```

The prospective scorer and its scoring registration were prepared before annex issuance. Actual annex issuance is2026-10-30T15:12:14.014369UTC /20:42:14IST; it was frozen BEFORE reviewing new coverage results. Original parent issuance remains05:35UTC and is not backdated. The actual published first-annex commit is29bdd984770904a032cebe9efcd2a12a8d5ffc17. `publication.json` records remote verification.252intervalrecords include216eligible=72originalTimesFMfuturecases×3arms. All14leads are represented; no lead borrows another lead's calibration. Samefutureepisode/source, not independent replication or216independent cases.

One tool transport connection failed after hindcasts completed; existing run/checkpoint files remained intact. The user requested resume, and analysis continued without restarting models. The primary protected outputs and old prospective Git blobs remained unchanged throughout. No failed result was hidden, new future label retrieved, journal/person contacted, workflow re-enabled or environment published.

## Review artifacts

`manuscript/calibration_update_v1` contains a separate four-page MD/DOCX/PDF supplement, vector/raster plot and all-lead tables; it preserves the original integrated paper. Internal QA checks144numeric table cells, figure/caption, ZIP integrity and rendered pages. `results/prospective_interval_20261030_v1/forecast_preview.*` plots only recorded past values through28October and pending future predictions/bands, explicitly excluding29/30October from prospective evaluation. No future observations are embedded.

Coverage gains incur width costs, lead7proper scores often worsen, and lead14can remain below nominal. This is established conformalized quantile regression, not a new method; see the verified primary citation metadata. Source processing/reuse, complete calendar amendments, independent human review and adequate untouched/source-independent confirmation remain publication gates. Q1 remains an aspiration requiring a verified database/year/category.
