# Do explicit festival features improve forecasts?

**Yes, in this historical experiment, explicit festival-day flags improve the aggregate next-day results—most strongly for SARIMAX and Ridge. The benefit is not universal across festivals, representations or horizons.**

These are exploratory 2024–2025 results for Delhi, Karnataka and Maharashtra, with state coverage defined separately for each festival. The primary study has 24 festival/state/year targets at each of three lead times: 72 identical cases per model/arm. It is an anchor-day comparison, not the earlier whole-window benchmark. MASE is an error score, not an accuracy percentage; lower is better.

| Model variant | Ordinary calendar | Plus festival-day flags | Plus festival windows |
| --- | ---: | ---: | ---: |
| SARIMAX | 1.310 | **0.532** | 1.310 |
| Rich monthly Ridge | 1.244 | **0.561** | 1.188 |
| TimesFM-3 | 1.348 | **1.103** | 1.350 |
| Chronos-2 | 1.371 | **1.329** | 1.353 |
| Stable LightGBM | 1.286 | **1.268** | 1.277 |
| LightGBM, fixed leaf-minimum-2 sensitivity | 1.273 | **1.097** | 1.246 |

The smaller tree leaf minimum is a separately declared sensitivity with its own calendar baseline. It was not chosen using these evaluated errors. Some day indicators have only one or two prior examples, which larger minimum leaf sizes cannot isolate. This helps explain weak default-tree effects; it does not establish that the smaller regime will generalise better.

Same-size zero and active placebo features are included in the full tables. They do not explain the large aggregate Ridge/SARIMAX day-flag gains. They also expose numerical/interface changes: adding zeros changes some Chronos/TimesFM forecasts despite adding no event information. The placebo construction is bounded and can coincide with other holidays; it is not causal identification.

The per-festival view matters. Several models worsen around the spring-new-year group even while their overall day-flag scores improve. Broad windows are generally less effective and sometimes worsen errors. All individual-year/state/family/control results remain available rather than selecting favourable cases.

The wider classical window check also shows next-day day-flag gains: Ridge MASE changes from 0.578 to 0.456 and SARIMAX from 0.575 to 0.419. These gains are smaller than their anchor-day gains. The foundation models were not rerun on every window case with the new features, so this wider-window conclusion is restricted to the classical models.

## Ordinary-day costs

A separate, date-selected sample of 72 weekday/season-matched non-event cases tests calendar/day/window arms on every model. Aggregate next-day errors do not increase with day flags in that sample. At longer leads, some costs appear: Chronos day flags increase non-event lead-14 MASE by about 0.026, and the smaller-leaf tree by about 0.007. This is a bounded spillover check, not an exhaustive all-day evaluation or a causal comparison between event and control dates.

## What was checked and what remains open

- Corrected training-date assumptions using annual notices: Karnataka Ganesh 2023 is 18 September; Maharashtra lists 19 September and Holi on 7 March.
- Frozen dates, encodings, controls and budgets before new intervention outputs; no new hyperparameter search or tuning of future forecasts.
- Matched scoring cases, recorded labels, past-only fitting cutoffs, pre-year scales and all fitting-label hashes checked.
- All 1,296 foundation task inputs reconstructed byte-for-byte by a separate implementation; 37 software tests pass.
- Eight native Chronos quantile-crossing pairs remain unmodified across the new arms/cohorts; TimesFM has none in these scored outputs. Correct point scores do not establish calibrated uncertainty.
- All 466 protected prior source/result/presentation/protocol hashes remain unchanged. Original prospective predictions, protocol and freeze match their initial Git blobs.

Only two historical years, related states/days, coincident holidays, retrospective source revisions and possible model pretraining/proxy overlap limit the findings. A pooled-event comparator was not run, so this does not prove that separate family identities outperform a generic event flag. Data-reuse response, amendment certification, independent human review and later prospective outcomes remain pending. No new-method novelty, universal winner or journal readiness is claimed.

Full evidence: [event results](results/festival_features_v1/REPORT.md), [non-event results](results/festival_feature_spillover_v2/REPORT.md), [gap audit](MISSED_STEPS_AUDIT.md), [reproduction](FEATURE_INTERVENTION_REPRODUCTION.md), and [college supplement](presentation/festival_feature_update_v1/README.md).
