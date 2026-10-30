# Regional Calendar Representation, Adaptation and Transfer in Foundation-Model Forecasting of Indian Supplied Electricity

**Working research manuscript; not submission-ready.** Author: Binay Verma. This draft distinguishes completed exploratory evidence from pending confirmation. Numerical tables are linked to versioned artifacts rather than treated as independent replications. Journal selection, author verification and reuse clearance remain open.

## Abstract

Daily electricity forecasting around moving holidays can depend on regional calendar definitions, feature representation and adaptation policy. We examine these factors for supplied electricity in Karnataka, Delhi and Maharashtra. An existing expanded evaluation is followed by controlled Ridge representations, stronger causal-history baselines with pre-year parameter selection, annual/monthly refit comparisons, and forward-year regression-region transfer. Calendar effects are inconsistent across representation, year and lead; a reliable regional-provenance advantage is not established. Monthly refitting improves several aggregate errors but worsens some event-year outcomes. Withholding the target region from regression fitting generally degrades forecasts, whereas pooling including the target can help. Past-only residual intervals show that near-nominal aggregate coverage can conceal event undercoverage. We separately audit a second covariate-capable foundation model using pinned code and actual weight bytes, and freeze future forecasts before eligible outcomes. The current evidence is exploratory: model overlap, source vintages, calendar amendments, data reuse rights and limited independent events prevent confirmatory or causal conclusions.

## 1. Research question and relationship to prior work

The proposed question is whether regional calendar information improves forecasting when representation, feature count, adaptation schedule and evaluation cases are controlled. A broader practical question is when apparent calendar benefits survive changes in region, year and prediction lead.

Kreusel et al. [1] already compare seven calendar encodings across four covariate-capable foundation models and explicitly recompute target encodings from each observed context. Alipour et al. [2] study learned event covariates. Kaljevic et al. [3] examine load forecasting with uncertain future covariates, and Meyer et al. [4] distinguish sample overlap from correlated temporal overlap in foundation-model evaluation. Consequently, neither calendar encodings, learned event representations, foundation models for load, nor generic robustness are novel contributions here. This work can potentially contribute a carefully documented regional-calendar/adaptation/transfer evaluation and negative findings. That contribution remains conditional on completing the evidence and rights gates.

No causal interpretation of festival effects is intended. Weather, economic activity, supply constraints, revisions and other concurrent changes are not controlled causal interventions. More forecast rows do not substitute for more independent events or sources.

## 2. Data, target and calendar evidence

The target is daily energy met/supplied, in GWh (equivalently MU), not latent unconstrained demand or hourly peak power. The expanded study uses a frozen Robbie Andrew GRID-INDIA/POSOCO compilation ending 28 October 2026. It is separate from the older corrected Hunt/Bloomfield CC BY 4.0 source; sources are not silently spliced. The three extracted state columns match the frozen raw values and metadata units. Each full state history has 112 missing entries. Causal filling is restricted to model inputs, while only recorded positive labels are fitted/scored. Positive recorded entries do not establish absence of upstream imputation or revision.

The expanded calendar ledger contains twelve annual-as-issued state-year government-office schedules for 2022–2025. It does not certify all subsequent amendments, district/election/emergency closures or historical training-year dates. Government-office closure, bank holiday and religious observance are distinct concepts. Main Diwali and documented regional anchors define the existing broad event windows; nearby dates are not independent festivals. Earlier training histories lack fully specified regional extras before 2022, motivating primary exploratory representation analyses in 2024–2025 rather than claiming complete provenance for the whole period.

Real-time publication lag and data vintages have not been reconstructed. The live curator landing page describes missing/unreadable reports, but its summary coverage/missingness does not directly reconcile with the frozen state table. The live repository reports no explicit GitHub licence; this is not a legal determination, and no new redistribution licence is inferred. Calendar documentation and source copies preserve evidence, not permission grants.

## 3. Experimental design

### 3.1 Temporal availability and matched cases

An origin denotes the first unseen target date; lead h targets origin+h−1. Leads 7 and 14 are individual days, not aggregate weekly forecasts. Target history always ends before origin. Future weekday/harmonic/event covariates are permitted only as calendar information, never future target observations. Direct local-model fitting purges labels to remain strictly before validation origins or deployment refits.

All already-inspected 2022–2026 data are development/exploratory for new methods. New protocols are written before their new outcomes, but are not described as external preregistrations. Historical validation remains a useful leakage control without making the overall research design confirmatory. No new method or date perturbation is selected on final test outcomes.

Historical all-day comparisons use identical state/origin/lead cases. Scores use state-specific weekly-difference scales from the preceding 730-day annual fitting window. Scales remain fixed within evaluation year even when parameters refit monthly. Event metrics average within state/year/lead, then equally across states and years. We avoid day-level independence assumptions and high-precision significance claims with only two primary event years.

### 3.2 Controlled representation study

`calendar_controls_v1` crosses generic/regional dates with scalar event windows and seven relative-day channels, and adds zero-channel, target-independent weekday/approximately-season-matched placebo and ±1/2-day date-shift controls. Ridge alpha=10 is fixed. Seventeen arms produce 215,577 forecasts from 612 fits. Delhi generic/regional identities and zero-control predictions are verified. All arms use the same original unshifted event-target cases.

The scalar and seven-channel forms contain different relative-day information. Equal dimension within a representation controls channel count but does not turn predictive regional-date differences into causal provenance effects. A single seeded placebo constellation is not a randomisation distribution. Shifted dates remain sensitivity controls; the best-looking shift is never substituted for a documented date.

### 3.3 Richer baselines and adaptation schedules

`strong_refit_v1` adds 27 causal lag/rolling/trend/target-aligned annual-history features. Calendar mode adds thirteen weekday/annual harmonic channels; regional mode adds seven existing event channels. Ridge uses three fixed candidate alphas. LightGBM uses eight fixed configurations spanning leaves, estimators and minimum leaf size, with fixed learning rate, regularisation and seed. This is an explicit stronger baseline budget, not the strongest imaginable local model.

Each state/year/lead/mode/model uses a single 180-day pre-year temporal validation block. Fit labels end before the first validation origin, and validation labels end before the evaluation year. Selected parameters are frozen for both annual and monthly deployment schedules throughout that year. Both schedules use 730 preceding calendar days of label history; only refit timing changes. The experiment contains 891 validation fits, 162 selected configurations, 1,998 deployment fits and 107,244 forecasts, with no failed fits. Each configuration matches 8,937 cached Chronos history-only cases across 2024, 2025 and partial 2026.

### 3.4 Regression-region transfer

`regional_transfer_v1` compares local, pooled-all and leave-region-out Ridge with fixed alpha=10. In the held-out-region arm, coefficient estimation and fitted feature standardisation use only the other two states. Each region is normalised using its preceding-year training mean/std. Target-region history and historical normalisation are allowed, so this is not history-free geographic cold start. Future evaluation years are never pooled into training. The design produces 53,622 forecasts from 162 fits and records all source-state identities, cutoffs and normalisers.

### 3.5 Foundation-model identity and uncertainty

The saved Chronos-2 evaluation pins code/model settings and records actual weight identity. Its first audited weight upload is October 2025; unchanged weights predate 2026 targets, conditional on source-date integrity. This does not resolve historical/proxy overlap. The new TimesFM3 audit pins Google code `e51928e…` and model revision `43046b85…`. Actual downloaded weights match both current and first-upload SHA-256 `a7592b0a…`; first weight upload is 24 August 2026. Forty installed Python files match the pinned source. Noncommercial academic-research terms apply; downloaded weights are not redistributed with the code/results.

An eighteen-task TimesFM API fixture validates CPU inference, 730-day contexts, known-future covariates and nine native quantiles. It is not a broad performance benchmark. A separate exact historical event replication under `timesfm_matched_events_v1` is complete and independently audited: 384 inference tasks, with 450 scored rows on 150 identical event cases per mode across the two years. Single/batched output checks match for the first four tasks per mode. Historical event targets predate both weight-upload dates and remain overlap-uncertain.

`residual_intervals_v1` supplies a distinct uncertainty baseline around saved point forecasts. At each origin, signed out-of-sample errors have target dates in the preceding 730 days and strictly before origin. Fixed 0.05/0.5/0.95 residual quantiles are added to each point forecast. These are not reconstructed native model distributions and have no exchangeability-based coverage guarantee. Four configurations produce 25,380 matched interval forecasts. Native TimesFM 80% intervals must not be directly ranked against 90% residual intervals by coverage alone.

## 4. Completed results

### 4.1 Calendar representation is not a stable provenance mechanism

Across the two primary exploratory event years, scalar generic event MASE is 0.60257/1.34947/1.40894 at leads 1/7/14, compared with regional 0.61113/1.28008/1.40395. Regional day-1 error is slightly worse. Seven-channel generic MASE is 0.42600/1.11742/1.23166, compared with regional 0.42466/1.25384/1.47234. Thus representation and year matter, and regional channels do not consistently dominate. The original four-year Chronos calendar-to-regional contrast worsens mean day-1 festival MAE by 4.623%; it is retained as a negative finding, not relabelled as successful festival enhancement.

### 4.2 Adaptation improves some aggregates and harms some event cases

Partial-2026 matched macro MASE:

| Configuration | Lead 1 | Lead 7 | Lead 14 |
| --- | ---: | ---: | ---: |
| Cached Chronos history | 0.4679 | 1.1629 | 1.3617 |
| Rich-calendar Ridge, annual | 0.5954 | 1.4910 | 1.8358 |
| Rich-calendar Ridge, monthly | 0.5416 | 1.3115 | 1.5098 |
| Rich-calendar LightGBM, annual | 0.6971 | 1.6917 | 2.1215 |
| Rich-calendar LightGBM, monthly | 0.6205 | 1.4861 | 1.8494 |

All modes, states and years remain reported; this table is not an outcome-selected final model. More frequent local fitting narrows some gaps but does not reverse these aggregate Chronos comparisons. Monthly updates are not universally beneficial: regional Ridge lead-14 event MASE in 2024 worsens from 1.347 to 1.731, and calendar LightGBM in 2025 worsens from 1.423 to 2.241. These workflows differ in pretrained information and adaptation policy, so the comparison cannot isolate architecture alone.

### 4.3 Pooled fitting and unseen-region fitting are different

For rich-calendar 2026 forecasts, local MASE is 0.6002/1.7010/2.0879, pooled-all is 0.5048/1.2732/1.5266, and leave-region-out is 0.6109/1.8263/2.3468. Pooling including the target helps in this case, while withholding the target degrades forecasts. This is negative transfer evidence within one source, not proof of failure or success across arbitrary Indian regions. Uncertainty from three correlated states remains substantial.

### 4.4 All-day interval coverage conceals event failures

For history-only Chronos, nominal 90% residual intervals achieve 89.74% mean all-day coverage at lead 1 but 77.25% within the fixed event windows. Regional Ridge lead-1 event coverage is 87.04%, also below nominal. Coverage, width, scaled interval scores and pinball loss are all retained; coverage alone cannot identify a superior distribution. These findings motivate further event-conditional uncertainty work but do not justify calibrating a replacement on these evaluated outcomes.

### 4.5 Matched second-model historical event replication

On the same 2024–2025 event cases, TimesFM history/calendar/regional MASE at leads1/7/14 is respectively 0.53440/1.22783/1.06153, 0.52136/1.22139/1.16340 and 0.49828/0.98611/0.90890. Corresponding Chronos values are 0.54564/1.24114/1.19892, 0.53022/1.22380/1.19796 and 0.53466/1.18789/1.19962. Mean per-state/year relative regional MAE reductions are +3.49%/+14.72%/+18.33% for TimesFM versus −2.30%/+1.04%/−0.93% for Chronos. These relative-effect means differ from ratios of macro MASE. TimesFM day1 is negative in2024 and positive in2025. Native regional80%coverage ranges68.25%–95.24% across years/leads; calibration is not established.

The two-year result demonstrates model/lead/year dependence, not a clean provenance mechanism or novel encoding. Information and channel count still change together, and both historical event years predate the audited model uploads. The original four-year Chronos negative result is preserved. The new historical result cannot retune the independently frozen prospective episode.

## 5. Prospective freeze and pending outcomes

`prospective_20261030_v1` freezes 252 forecasts from six configurations: TimesFM history/calendar, monthly rich-calendar Ridge/LightGBM, last value and weekly repeat, for three states and fourteen target days. Issue time is 30 October 2026 05:35:15 UTC, with unchanged observed context ending 28 October. Origin (first unseen date) is 29 October, distinct from issue time. Only 216 predictions for 31 October–11 November are prospectively eligible; 29/30 October are excluded. Local selection uses pre-2026 data and deployment labels end September 30. No 2026 regional holiday indicators are supplied. The initial freeze is in GitHub commit `cabd5982e1948652b9841d6c31a2380f6f314198`.

**No prospective outcomes or scores are available in this draft.** Actuals must be acquired after their dates, preserved with retrieval/vintage/source hashes and scored into a new directory without changing predictions. This is one forecast episode with lagged context and a shared source, not independent-source confirmation or adequate independent festival replication. Festival-specific secondary analysis requires independently verified 2026 event definitions; primary scoring uses all eligible dates.

## 6. Limitations, contribution decision and reproducibility

Remaining limitations include unresolved source reuse/processing terms, annual-versus-amended calendar definitions, historical and proxy model overlap, retrospective availability, dependence across dates/states, only two primary exploratory event years and no independent human/clean-room review. Generic calendar/learned event features already have close prior work. A new-method or novelty claim is not supported by the present design. A defensible empirical/negative-results contribution may be possible if the provenance, independence and submission gates are completed.

Protocols precede new experiment outcomes but follow historical result inspection. Full selection/fitting logs, failed/negative findings, prediction files, model/source/code hashes, test logs and reports are versioned on GitHub. Original expanded results are preserved. Twenty-eight software tests and persisted-output audits pass; these checks address specific leakage and integrity risks rather than certifying zero errors. Full pretrained reruns, model-specific audits, tests and prospective scoring have different statuses and must not be conflated.

## References

1. Kreusel et al. (2026). *On the Encoding of Calendar Features in Covariate-Informed Time Series Foundation Models*. arXiv:2610.13676v1. https://arxiv.org/abs/2610.13676
2. Alipour et al. *Impact-driven event covariates for time-series foundation models*. Amazon Science primary page. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models (final bibliographic/venue metadata remains to be checked).
3. Kaljevic, Arzola and Zhang (2026). *Benchmarking Time Series Foundation Models for Load Forecasting Under Covariate Uncertainty*. arXiv:2610.07232v1. The primary page reports acceptance for a 2027 conference; do not describe it as a journal article. https://arxiv.org/abs/2610.07232
4. Meyer et al. *Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges*. arXiv:2510.13654v3. https://arxiv.org/abs/2510.13654
5. Chronos-2 report/model and TimesFM official code/model sources: see `PRETRAINING_AUDIT.md`, `RESEARCH_REFERENCES.md` and `results/second_model_audit_v1/REPORT.md` for exact identities, links and limits.
6. Data and government calendars: full source URLs and attribution in `DATA_SOURCES.md` and `REGIONAL_CALENDAR_AUDIT.md`. Reuse and amendment gaps are explicitly unresolved.
