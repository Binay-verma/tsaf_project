# Current research status — 30 October 2026

The requested next research stage is completed and the prospective forecasts are frozen on GitHub. A working journal manuscript exists. **Submission readiness is not established:** remaining gates require source/calendar evidence, independent review, stronger mechanism controls and genuinely later observations. Previous data/results are preserved.

## Completed new evidence

| Work | Actual evidence | Main result / limit |
| --- | --- | --- |
| Richer baselines and refits |891 temporal validation fits;162 selected configs;1998 deployment fits;107244 predictions;8937 matched cases/configuration | Monthly updates improve several aggregates but harm some event-year cases. No universal refit advantage |
| Regression-region transfer |162 fits;53622 predictions; local/pooled-all/leave-region-out; source-only fitting tested | Held-out-region transfer generally degrades. Pooled-all includes target training rows and is not unseen-region fitting |
| Second foundation-model audit | TimesFM3 pinned code, actual1.32GB weights verified against first upload,40 installed files matched, native covariate/quantile API exercised | Upload24August2026; historical/proxy overlap unresolved. Noncommercial research terms; weights excluded from GitHub |
| Matched two-model festival comparison |384 TimesFM inference tasks;450 scored rows,150 exact cases/mode,2024–2025; cached Chronos/Ridge/SARIMAX on same cases | TimesFM regional mean state/year MAE improves3.49%/14.72%/18.33% at leads1/7/14; Chronos −2.30%/+1.04%/−0.93%. Model/year dependence; only2 historical clusters, not a causal mechanism or universal success |
| Prospective freeze |252 forecasts,216 eligible future predictions,6configs,3states; source through28October; issue30October | Eligible31October–11November. No future actuals fetched or scores available. Original freeze in commit cabd5982e1948652b9841d6c31a2380f6f314198 |
| Tests and independent audits |28 tests pass; saved labels/scales/cases/selection/refits/model hashes/metrics checked | Evidence against specific errors; not proof of zero leakage/bugs or clean-room reproduction |
| Research and manuscript | Live nearest-paper methods/abstract checks, source rights follow-up, evidence-linked manuscript and submission gates | No new-method/first-ever or journal acceptance claim; data rights remain unresolved |

Earlier representation study (612 Ridge fits/215577 forecasts), residual-interval study (25380 interval forecasts) and original expanded evaluation (103254 forecasts) remain unchanged. Aggregate90% residual coverage89.74% versus77.25% during day1 events remains a key uncertainty failure case. No retuning of those historical outcomes or frozen prospective forecasts followed the new TimesFM event findings.

## Read these artifacts

- [Rich baselines/refits](results/strong_refit_v1/REPORT.md) and [figure](results/strong_refit_v1/refit_comparison.png).
- [Region transfer](results/regional_transfer_v1/REPORT.md).
- [TimesFM identity/API audit](results/second_model_audit_v1/REPORT.md).
- [Exact historical event replication](results/timesfm_matched_events_v1/REPORT.md) and [model/year figure](results/timesfm_matched_events_v1/model_event_effects.png).
- [Prospective protocol](results/prospective_20261030_v1/protocol.json), [freeze](results/prospective_20261030_v1/freeze.json), [immutable forecasts](results/prospective_20261030_v1/predictions.csv).
- [Working manuscript](manuscript/DRAFT.md), [submission gates](manuscript/SUBMISSION_GATES.md), [live research/source review](results/research_review_v2/REPORT.md).
- [Reproduction and future scoring](PHASE2_REPRODUCTION.md).

## Remaining work, in order

1. Complete equal-information/feature-count/placebo controls across both TSFMs before a regional-provenance mechanism claim; existing B-to-D comparisons change information and dimension. Learned context-only encodings already have close prior work and require nested past-only development rules.
2. Resolve issue/effective/amendment-aware dates for every used event history and independent regional review. Annual schedules are not final amended observances.
3. Obtain explicit source reuse/redistribution and processing/vintage evidence; the live webpage/repository do not establish a licence. Landing-page coverage/missingness summaries differ from the frozen state table and need reconciliation. No frozen data were refreshed.
4. After11November, acquire actual outcomes with retrieval/vintage evidence and score the frozen episode without retuning. A test-gated scoring command is supplied; one episode will not replace independent-source/event evidence. No job is scheduled to fetch or score automatically.
5. Independent clean-environment/scientific rerun and human author/calendar review; adequate independent regions/events/source; bibliography/venue/reporting review before submission.

These are open gates, not completed work. Model-specific historical exposure, retrospective availability, correlated states/days and small event count prevent a contamination-free or confirmatory description. The defensible current framing is an empirical evaluation with model-dependent calendar effects and retained failures.

## Workflow and GitHub

Use `/workspace/tsaf_project` for active Git-tracked development. Do not switch back to the older `/workspace/tsfm_india` copy or recreate the project. Python3.12 `.venv` is prepared; model weights/code are outside the checkout. Network access now permits the formerly blocked source/paper/model checks. No paid API, outgoing message, environment publication or configuration update was used.

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -v
.venv/bin/python src/audit_phase2.py
.venv/bin/python src/audit_matched_events.py
python src/verify_continuation.py
```

The current GitHub checksum manifest verifies current files; earlier transfer/continuation manifests remain historical before intentional documentation edits. Completed experiment guards prevent overwriting predictions. New methods/versions need new named protocols/result directories. Commit and push completed checkpoints, then verify remote/local SHA equality.
