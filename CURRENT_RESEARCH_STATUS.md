# Current research status — 30 October 2026

The original project has been continued, not restarted. The expanded historical evaluation is preserved. Two additional exploratory studies and independent audits are complete. **The project is not yet ready for journal submission.** Negative results are retained; no new outcomes were treated as an untouched final test.

## What now has evidence

| Area | Verified in this continuation | Limits |
| --- | --- | --- |
| Transfer integrity | 180 split-package entries and 179 original checkpoint hashes passed before edits | Documents were intentionally updated afterward; use the new continuation manifest for the current state |
| Software | Python 3.12.14; 11 original and 8 new unit tests pass | Foundation packages/weights and LightGBM are not installed in this environment |
| Existing scores | 103,254 forecasts audited; source labels, scales, matched cases, date alignment, saved MAE/MASE, and selection boundaries independently reconstructed | Does not rerun pretrained inference or certify absence of every possible bug |
| Data extraction | All three selected state series match their frozen raw columns; metadata confirms GWh | Each full series contains 112 missing entries; positive recorded values do not prove no upstream filling; revisions/availability remain unresolved |
| Calendar/representation controls | 612 fixed Ridge fits, 215,577 predictions, 17 arms; zero/placebo/date-shift controls and generic/regional encodings | No stable provenance benefit; two primary event-year clusters; no new TSFM inference |
| Uncertainty baseline | 25,380 residual-calibrated interval forecasts, four configurations, matched cases; strictly pre-origin residual targets | Not native TSFM quantiles; no coverage guarantee; event-specific undercoverage observed |
| Second-model feasibility | Official TimesFM repository confirms future covariates and separate noncommercial terms for 3.0 weights | No pinned weight/API/overlap audit or model run yet |
| Research background | Handoff, protocol, reports and original survey inspected; official model documentation snapshots retrieved and hashed | Prior paper claims not newly verified: arXiv blocked; focused review remains incomplete |

## What the new results mean

1. Equal scalar representations give mixed regional-versus-generic results. For 2024–2025 day 1, regional event MASE is 0.61113 versus generic 0.60257 (lower is better). Seven relative-day channels behave differently. Earlier improvements cannot be assigned to regional date provenance alone.
2. Shifting dates can change scores substantially. These are sensitivity controls, **not a licence to select the best-scoring festival date**. Annual/state results and all unsuccessful controls remain visible.
3. A 90% past-only residual interval around history-only Chronos has 89.74% average day-1 all-day coverage but 77.25% festival-window coverage. This supports investigating event-conditional uncertainty; it does not establish a calibrated method or a successful new model.
4. Historical 2022–2026 outcomes already examined remain exploratory for all newly proposed methods. No unseen final confirmation has been created by relabelling a historical split.

Detailed evidence:

- [Controlled experiment](results/calendar_controls_v1/REPORT.md), [protocol](results/calendar_controls_v1/protocol.json), [figure](results/calendar_controls_v1/event_controls.png).
- [Interval experiment](results/residual_intervals_v1/REPORT.md), [protocol](results/residual_intervals_v1/protocol.json), [coverage figure](results/residual_intervals_v1/coverage.png).
- Original-score audit: `results/calendar_controls_v1/checkpoint_audit.json`.
- Data extraction and coverage: `results/calendar_controls_v1/source_audit.json` and `source_year_coverage.csv`.
- Independent new-output audits: `independent_audit.json` in both experiment directories, including 144 reconstructed calibration examples.

## Ordered remaining work and completion evidence

| Priority | Work | Completion evidence needed | What prevents claiming completion now |
| --- | --- | --- | --- |
| 1 | Stronger local baselines and refit comparison | Freeze richer causal histories and past-only development budget; compare annual/monthly schedules on matched exploratory cases; retain every selection fit | Not implemented/run; poor old LightGBM scores do not settle baseline strength |
| 2 | Regional/event transfer | New protocol for held-out region and forward-held-out event-year development folds; no held-out-specific feature selection; clear rules for target-region historical scaling/context | Current models are state-specific; two primary years give weak event evidence |
| 3 | Second covariate-capable TSFM and controlled TSFM inference | Exact API/code revision, weight bytes/hash, licence, temporal exposure audit, resources, fixed inference cases, then encodings/controls | Hugging Face metadata request denied by proxy; weights not bundled. TimesFM 3.0 weights have noncommercial restrictions |
| 4 | Calendar provenance | Amendment-aware ledger for every used train/evaluation anchor, issue/effective dates, scoped definitions, independent regional review | Annual schedules alone are insufficient; training-year extras before 2022 incomplete |
| 5 | Data provenance and rights | Explicit reuse/redistribution terms, source processing policy, publication lags and revision/vintage evidence; independent licensed dataset if feasible | Compilation website denied by proxy; terms and upstream processing unresolved. No permission inferred from downloadable data |
| 6 | Distributional forecasting | Native quantiles and past-only calibration under a separately frozen protocol, event/all-day pinball, coverage, width and interval scores | New residual baseline is diagnostic only; limited independent event count |
| 7 | Literature/contribution | Recheck closest primary papers, versions, methods and licence; document exact differences; avoid first-ever claims | arXiv blocked; generic encodings/learned event features already have close prior work |
| 8 | Fresh confirmation and manuscript | Freeze protocol/models before new outcomes; independent clean rerun, human scientific/calendar review, evidence-linked manuscript | No untouched confirmation or independent human review. No post-weight 2026 Diwali outcome in frozen snapshot |

These are pending tasks, not completed experiments. Calendar quality, event representation and uncertainty failures may support a careful empirical/negative-result study; a new-method contribution has not been demonstrated.

## Environment and next external action

Use the existing project directory `/workspace/tsfm_india`; do not restart from the empty `tsaf_project` checkout. Activate the prepared interpreter through `.venv/bin/python`. The environment reuses installed numerical packages and adds holidays 0.107/statsmodels 0.15.0. It is usable for the current local experiments, not an identical full foundation-model environment. Do not bypass historical cache identity checks or rerun a whole search just to regain context.

Requests to `arxiv.org`, `huggingface.co` and `robbieandrew.github.io` returned proxy HTTP 403. For the blocked external research/model-metadata checks, these domains need to be allowed in environment network settings, followed by retrying the exact requests. Additional weight-download hosts may be required after inspecting actual metadata; none are assumed here. Existing allowed domains and published settings were left unchanged. No paid APIs were used, nobody was contacted, and nothing was published.

No new scientific decision is needed from the user to continue offline baseline/transfer work. Data reuse rights and independent human review require evidence beyond model computation. The immediate next offline task is priority 1 above, with a new protocol and output directory before evaluating its outcomes.

## Current checks

```bash
cd /workspace/tsfm_india
.venv/bin/python -m unittest discover -s src -p 'test_*.py' -v
.venv/bin/python src/audit_checkpoint.py
.venv/bin/python src/audit_new_experiments.py
python src/verify_continuation.py
```

The last verifier uses a new versioned continuation manifest. Original transfer manifests are preserved as historical evidence; they will flag intentional handoff/work-log edits. Completed experiment runners refuse to overwrite predictions. Use new versioned protocols/directories for changed methods, and treat subsequent artifact changes as a new checkpoint.
