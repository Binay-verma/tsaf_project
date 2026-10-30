# Pooled features, supervised event transfer and daily post-weight audit

Continue the existing checkout and pinned Python3.12environment. Do not restart the original project, overwrite completed workers or rerun the full benchmark merely to recreate context. All original scientific/source/deck files and future Git blobs remain protected. The current checksum manifest verifies transfer integrity, not scientific validity.

## Completed studies

| Study | Protocol and completed evidence | Important distinction |
| --- | --- | --- |
| `pooled_festival_v1` | Two unchanged72-case cohorts; six variants, five new arms plus three reused arms;4,320new/6,912compared forecasts; score/input/fitting/probability audits | Equal dimensions change signal allocation/sharing; outcomes remain historical/exploratory |
| `festival_label_transfer_v2` | Three fixed regression budgets, three feature forms, three row policies,144cases;3,888forecasts/3,807fits, all141training blocks preflighted | Direct own-family fitting labels excluded, but past target history remains available; not fully unseen-event transfer |
| `postweight_daily_v1` | Eight configurations,396identical cases each;44targetdates/state/lead;3,168forecasts and684foundation input tasks | Targets/origins after actual weight uploads, but already inspected and ideally available rather than real-time/untouched |

All labels, dates, scales and case sets are matched within the declared comparison. No new errors select features, matching distance, model budgets or deployment winners. Differences between studies are not pooled into a single ranking.

## Audit saved outputs without refitting

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -q
.venv/bin/python src/audit_pooled_festival.py
.venv/bin/python src/audit_pooled_inputs_fits.py
.venv/bin/python src/audit_pooled_uncertainty.py
.venv/bin/python src/audit_label_transfer.py
.venv/bin/python src/audit_postweight_panel.py
```

All45tests pass in the working environment and the separate no-system-package environment `/workspace/tsfm-clean-review`. The standalone numerical reproduction is more stringent than those tests: its135forecast checks agree within tolerance and all labels match, but byte discrepancies in Delhi matrices remain explicitly failed. See `POOLED_FEATURE_REPRODUCTION.md`, `clean_scalar_review.json` and `numerical_localization.json`; do not claim a complete clean-room pass.

Model caches stay outside the checkout. Both foundation models use previously pinned actual weights/code, seed42,730past targets,14output days, batch4and twoCPUthreads. Chronos independent-task attention and TimesFM symmetry settings remain fixed. No new packages/model downloads were required. Both the new pooled1440and daily684foundation task inputs reconstruct independently, and original source/future files remain unchanged.

## Executed preparation and worker entry points

These commands describe the execution. Completed/interrupted directories intentionally reject rerunning. A new reproduction must explicitly version output directories and record new source/protocol identities; do not delete old artifacts to bypass guards.

```bash
.venv/bin/python src/pooled_festival_experiment.py prepare
.venv/bin/python src/score_pooled_uncertainty.py prepare
# Each worker once for each --cohort event/non_event:
.venv/bin/python src/pooled_festival_experiment.py ridge --cohort event
# Also lightgbm, lightgbm_capacity2, sarimax, chronos, timesfm.
.venv/bin/python src/finalize_pooled_festival.py
.venv/bin/python src/score_pooled_uncertainty.py score

# Version1failed; preserved. Use the separately frozen version2:
.venv/bin/python src/festival_label_transfer_v2.py prepare
# Each worker once: ridge_fixed10, tree_fixed20, tree_fixed2.
.venv/bin/python src/festival_label_transfer_v2.py ridge_fixed10
.venv/bin/python src/finalize_label_transfer.py

.venv/bin/python src/postweight_daily_panel.py prepare
# Each worker once: classical, chronos, timesfm.
.venv/bin/python src/postweight_daily_panel.py classical
.venv/bin/python src/finalize_postweight_panel.py
```

The initial daily finalizer completed scientific CSVs then failed a Markdown integer-header formatter. Its exact execution source and failure note are retained. The separate numerical audit passed; `report_postweight_panel.py` recovered REPORT/run metadata from saved tables and verified all seven scientific file hashes unchanged. The finalizer now formats headers correctly for a separately versioned future reproduction. No daily model/metric rerun was used to repair documentation.

The first label-transfer design aborted when a28–42day exact control was unavailable for2022-08-28. Version2extends the fixed matcher to±28,±35,…,±84days and preflights every block before model outputs; actual maximum70days. No outcome scores selected that revision. Greater distance weakens seasonal matching and is inventoried. A slow first independent auditor was interrupted with its source/traceback retained, then repeated date plans were memoized; matching/model/prediction rules did not change.

## Paper and review artifacts

`src/build_journal_draft.py` creates a separate review manuscript from completed audited tables. It refuses an existing draft. Pandoc/Word styles and explicit cell widths were corrected during unpublished document QA; scientific tables stayed unchanged. The final MD/DOCX/PDF has four figures/four tables,91numeric cells checked against source tables and readable rendered result pages. `qa.json` records exact final output hashes. No journal template/submission approval is implied.

Source URLs and all58used calendar anchors are crosswalked in `review/used_calendar_v2`; zero amendment chains or human sign-offs are certified. Six primary arXiv records and BibTeX are under `review/reference_audit_v1`. IJF scope/reproducibility policy and inaccessible quartile/author-guide requests are under `review/journal_target_v1`; no proxy bypass or unverified Q1 label. See the author/professor review packet for the concrete remaining decisions.

The user authorized public GitHub synchronization, not a source licence grant or prospective workflow reactivation. The curator email was sent manually by the author; no duplicate/outside contact was sent here. Frozen prospective protocol/predictions/freeze are byte-equal to commit `cabd5982e1948652b9841d6c31a2380f6f314198`; the workflow remains `disabled_manually`. No new future actuals, environment publication, journal submission or acceptance.
