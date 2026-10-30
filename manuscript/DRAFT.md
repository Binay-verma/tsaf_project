# Regional Calendar Representation, Adaptation and Transfer in Foundation-Model Forecasting of Indian Supplied Electricity

**Working research manuscript; not submission-ready.** Author: Binay Verma. This draft distinguishes completed exploratory evidence from pending confirmation. Numerical tables are linked to versioned artifacts rather than treated as independent replications. Journal selection, author verification and reuse clearance remain open.

## Latest review manuscript

The restructured current MD/DOCX/PDF is under [journal_draft_v1](journal_draft_v1/MANUSCRIPT.md). It includes the completed pooled-feature, supervised-family-label exclusion and broader daily post-weight studies, native probability quality and four figures. This older working draft remains useful historical detail; current claims follow the versioned reports and new paper. Q1 is the target, not a verified venue or acceptance claim.

## Abstract

Daily electricity forecasting around moving holidays can depend on regional calendar definitions, feature representation and adaptation policy. We examine these factors for supplied electricity in Karnataka, Delhi and Maharashtra. An existing expanded evaluation is followed by controlled Ridge representations, stronger causal-history baselines with pre-year parameter selection, annual/monthly refit comparisons, and forward-year regression-region transfer. Calendar effects are inconsistent across representation, year and lead; a reliable regional-provenance advantage is not established. A later five-family intervention finds substantial historical anchor-day gains from explicit day flags for some classical models and smaller foundation-model gains, while broad-window effects and ordinary-day costs remain model/lead dependent. Monthly refitting improves several aggregate errors but worsens some event-year outcomes. Withholding the target region from regression fitting generally degrades forecasts, whereas pooling including the target can help. Past-only residual intervals show that near-nominal aggregate coverage can conceal event undercoverage. We separately audit a second covariate-capable foundation model, test equal-dimension/zero/placebo controls across both families, document historical source revisions and availability sensitivity, and freeze future forecasts before eligible outcomes. The current evidence is exploratory: model overlap, source vintages, calendar amendments, data reuse rights and limited independent events prevent confirmatory or causal conclusions.

## 1. Research question and relationship to prior work

The proposed question is whether regional calendar information improves forecasting when representation, feature count, adaptation schedule and evaluation cases are controlled. A broader practical question is when apparent calendar benefits survive changes in region, year and prediction lead.

Kreusel et al. [1] already compare seven calendar encodings across four covariate-capable foundation models and explicitly recompute target encodings from each observed context. Alipour et al. [2] study learned event covariates. Kaljevic et al. [3] examine load forecasting with uncertain future covariates, and Meyer et al. [4] distinguish sample overlap from correlated temporal overlap in foundation-model evaluation. Consequently, neither calendar encodings, learned event representations, foundation models for load, nor generic robustness are novel contributions here. This work can potentially contribute a carefully documented regional-calendar/adaptation/transfer evaluation and negative findings. That contribution remains conditional on completing the evidence and rights gates.

No causal interpretation of festival effects is intended. Weather, economic activity, supply constraints, revisions and other concurrent changes are not controlled causal interventions. More forecast rows do not substitute for more independent events or sources.

## 2. Data, target and calendar evidence

The target is daily energy met/supplied, in GWh (equivalently MU), not latent unconstrained demand or hourly peak power. The expanded study uses a frozen Robbie Andrew GRID-INDIA/POSOCO compilation ending 28 October 2026. It is separate from the older corrected Hunt/Bloomfield CC BY 4.0 source; sources are not silently spliced. The three extracted state columns match the frozen raw values and metadata units. Each full state history has 112 missing entries. Supervised-regression fitting labels and all scoring labels are recorded positive values. Historical model contexts are causally filled; the statistical-model specification can also use that past filled series for parameter fitting, with missing counts recorded. Positive recorded entries do not establish absence of upstream imputation or revision.

The expanded calendar ledger contains twelve annual-as-issued state-year schedules for 2022–2025, with distinct government-office/public-holiday statutory scopes documented separately. It does not certify all subsequent amendments, district/election/emergency closures or historical training-year dates. Government-office closure, bank holiday and religious observance are distinct concepts. Main Diwali and documented regional anchors define the existing broad event windows; nearby dates are not independent festivals. Earlier training histories lack fully specified regional extras before 2022, motivating primary exploratory representation analyses in 2024–2025 rather than claiming complete provenance for the whole period.

A bounded source-vintage review now identifies exact Git/archive snapshots and two fixed issue-time availability scenarios; exhaustive real-time publication/vintage reconstruction remains incomplete. The live curator landing page describes missing/unreadable reports, but its summary coverage/missingness does not directly reconcile with the frozen state table. The live repository reports no explicit GitHub licence; this is not a legal determination, and no new redistribution licence is inferred. Calendar documentation and source copies preserve evidence, not permission grants.

## 3. Experimental design

### 3.1 Temporal availability and matched cases

An origin denotes the first unseen target date; lead h targets origin+h−1. Leads 7 and 14 are individual days, not aggregate weekly forecasts. Target history always ends before the first-unseen origin by date. This index-temporal restriction does not certify that each retrospective value or corrected calendar was actually published at a historical issue time. Future weekday/harmonic/event covariates are permitted only as calendar information, never future target observations. Direct local-model fitting purges labels to remain strictly before validation origins or deployment refits.

All already-inspected 2022–2026 data are development/exploratory for new methods. New protocols are written before their new outcomes, but are not described as external preregistrations. Historical validation remains a useful leakage control without making the overall research design confirmatory. No new method or date perturbation is selected on final test outcomes.

Historical all-day comparisons use identical state/origin/lead cases. Scores use state-specific weekly-difference scales from the preceding 730-day annual fitting window. Scales remain fixed within evaluation year even when parameters refit monthly. Event metrics average within state/year/lead, then equally across states and years. We avoid day-level independence assumptions and high-precision significance claims with only two primary event years.

### 3.2 Controlled representation study

`calendar_controls_v1` crosses generic/regional dates with scalar event windows and seven relative-day channels, and adds zero-channel, target-independent weekday/approximately-season-matched placebo and ±1/2-day date-shift controls. Ridge alpha=10 is fixed. Seventeen arms produce 215,577 forecasts from 612 fits. Delhi generic/regional identities and zero-control predictions are verified. All arms use the same original unshifted event-target cases.

A new `mechanism_controls_v1` study freshly evaluates nine fixed arms on both pinned foundation models over the same150 event cases per arm in2024–2025:2304 inference tasks and2700 scored predictions. Arms comprise ordinary calendar,1/7zero channels, generic/regional scalar windows, generic/regional seven-offset encodings, and scalar/seven-channel seeded placebos. All original cases, predictions and prospective forecasts are preserved. This protocol predates those new control outcomes but follows prior exploratory findings.

The scalar and seven-channel forms contain different relative-day information. Equal dimension within a representation controls channel count but does not turn predictive regional-date differences into causal provenance effects. A single seeded placebo constellation is not a randomisation distribution. Shifted dates remain sensitivity controls; the best-looking shift is never substituted for a documented date.

### 3.3 Richer baselines and adaptation schedules

`strong_refit_v1` adds 27 causal lag/rolling/trend/target-aligned annual-history features. Calendar mode adds thirteen weekday/annual harmonic channels; regional mode adds seven existing event channels. Ridge uses three fixed candidate alphas. LightGBM uses eight fixed configurations spanning leaves, estimators and minimum leaf size, with fixed learning rate, regularisation and seed. This is an explicit stronger baseline budget, not the strongest imaginable local model.

Each state/year/lead/mode/model uses a single 180-day pre-year temporal validation block. Fit labels end before the first validation origin, and validation labels end before the evaluation year. Selected parameters are frozen for both annual and monthly deployment schedules throughout that year. Both schedules use 730 preceding calendar days of label history; only refit timing changes. Version1 contains891 validation fits,162 selected configurations,1998 deployment fits and107244 forecasts, with no failed model fits. A separate scalar implementation later exposed tree sensitivity to tiny differences in rolling arithmetic. A new float32 feature-interface contract was therefore specified before rerunning the tree study: version2 contains648 validation fits,81 selected configurations,999 deployment fits and53622 predictions. Version1 and its failed cross-implementation checks are retained. The contract was selected for numerical reproducibility, not evaluation accuracy;17/81 parameter choices differ under the same pre-year selection rule. Each configuration matches 8,937 cached Chronos history-only cases across 2024, 2025 and partial 2026.

### 3.4 Regression-region transfer

`regional_transfer_v1` compares local, pooled-all and leave-region-out Ridge with fixed alpha=10. In the held-out-region arm, coefficient estimation and fitted feature standardisation use only the other two states. Each region is normalised using its preceding-year training mean/std. Target-region history and historical normalisation are allowed, so this is not history-free geographic cold start. Future evaluation years are never pooled into training. The design produces 53,622 forecasts from 162 fits and records all source-state identities, cutoffs and normalisers.

### 3.5 Foundation-model identity and uncertainty

The saved Chronos-2 evaluation pins code/model settings and records actual weight identity. Its first audited weight upload is October 2025; unchanged weights predate 2026 targets, conditional on source-date integrity. This does not resolve historical/proxy overlap. The new TimesFM3 audit pins Google code `e51928e…` and model revision `43046b85…`. Actual downloaded weights match both current and first-upload SHA-256 `a7592b0a…`; first weight upload is 24 August 2026. Forty installed Python files match the pinned source. Noncommercial academic-research terms apply; downloaded weights are not redistributed with the code/results.

An eighteen-task TimesFM API fixture validates CPU inference, 730-day contexts, known-future covariates and nine native quantiles. It is not a broad performance benchmark. A separate exact historical event replication under `timesfm_matched_events_v1` is complete and independently audited: 384 inference tasks, with 450 scored rows on 150 identical event cases per mode across the two years. Single/batched output checks match for the first four tasks per mode. Historical event targets predate both weight-upload dates and remain overlap-uncertain.

`residual_intervals_v1` supplies a distinct uncertainty baseline around saved point forecasts. At each origin, signed out-of-sample errors have target dates in the preceding 730 days and strictly before origin. Fixed 0.05/0.5/0.95 residual quantiles are added to each point forecast. These are not reconstructed native model distributions and have no exchangeability-based coverage guarantee. Four configurations produce 25,380 matched interval forecasts. Native TimesFM 80% intervals must not be directly ranked against 90% residual intervals by coverage alone.

### 3.6 Matched multi-festival diagnostic extension

`multifestival_cached_v1` fixes thirty anchors and twenty-four festival/state/year groups before newly stratified errors: Holi in Delhi/Maharashtra, Ganesh Chaturthi and Ugadi/Gudi Padwa in Karnataka/Maharashtra, and Dussehra/Diwali in all three states, for2024–2025. Fixed +/-3-day windows yield528identical cases at leads1/7/14; no scoring labels are missing. Diwali preserves its earlier broad union, while other groups use one annual-as-issued anchor per state/year. Coincident holidays remain explicit: Dussehra2025 includes Gandhi Jayanti and the spring2025 window borders Eid. This is neither a complete multi-festival calendar nor a causal attribution design.

Nine unchanged daily configurations are rescored. A separate `multifestival_models_v1` protocol then adds annual fixed-order SARIMAX history/calendar, monthly additive weekly ETS(A,N,A), ordinary-calendar Chronos and history/calendar TimesFM, giving fifteen configurations and7920scored forecasts on the same528cases/configuration. Twelve SARIMAX and31ETS parameter fits converge after45total optimiser attempts, including two retained nonconverged attempts before the predefined training-only Powell retry. New foundation inference uses1410state/origin contexts. Causal past filling, scale definitions and model/code/weight hashes are explicit. No forecast-success intersection or held-out-error-driven hyperparameter change is permitted. Fixed-parameter scalar ETS recurrences reproduce six date-selected deployments to numerical precision.

Ordinary calendar means thirteen weekday/Fourier channels; additional Holi/Ganesh/Ugadi identities are not supplied. Thus the extension diagnoses performance around additional festivals, not their incremental covariate benefit. It also does not replace the separate regional-Diwali arms. All family/state/year/configuration scores are retained in `results/multifestival_models_v1/`; historical overlap and unequal adaptation budgets remain limitations.

### 3.7 Explicit additional-festival features and non-event costs

`festival_features_v1` adds explicit family-specific date features using a named2022–2025ledger:58anchors across48family/state/year groups. Karnataka's2023English notice and newly retrieved official Maharashtra2023PDF resolve important training-date differences: Ganesh18September versus19September respectively, and Maharashtra Holi7March. Annual-as-issued evidence is not full amendment certification. All used event-feature dates are bounded to the ledger span; original pre-year ordinary-calendar parameters are reused across arms rather than retuned with an unsupported earlier event-feature ledger.

Six common arms comprise ordinary calendar, five zeros, five family day indicators, five family window indicators, and same-size day/window active placebos. Windows use the fixed+/-3day union. Placebos shift each family/state/year constellation by a seeded multiple of seven within28–42days, excluding overlaps with registered true-family windows; they can coincide with other holidays and are not exchangeable causal controls. Ridge/stable-tree additionally test35relative-day/zero/placebo channels. A prespecified tree sensitivity changes only the leaf minimum to2for every common arm, with a fresh corresponding calendar baseline. It is not an outcome-selected winning regime.

The primary evaluation uses24festival/state/year anchor targets at three individual leads, giving72matched cases per model/arm. Six model variants and six common arms produce2592scored primary forecasts. Rich Ridge and stable/capacity2trees refit monthly; fixed-order SARIMAX refits annually and updates states only through origin-1. Both pinned foundation models perform fresh inference for every common arm. Secondary classical evaluation retains528window cases; its15840forecasts include overlapping primary cases and must not be counted as independent replications. Foundation intervention claims are restricted to the primary anchor cohort.

`festival_feature_spillover_v2` separately fixes72weekday/season-matched non-event cases before their outputs, excluding+/-3days around annual/registered holiday anchors. Calendar/day/window arms produce1296matched forecasts. The event-family label denotes the paired control, not a festival occurring on its date. This is bounded ordinary-day checking, not an exhaustive all-day or causal event/control study. A preparation prototype failed before protocol write and was retained; the corrected secondary regression code explicitly reproduces original full-daily calendar baselines because window-only baseline files do not cover non-event dates. All model/fitting/source/code/case hashes and failed attempts remain visible.

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

### 4.6 Equal-dimension controls qualify the calendar finding

With scalar windows held at one added channel, regional-versus-generic mean state/year MAE reductions are +0.22%/−0.68%/−0.81% for Chronos and +1.17%/−0.09%/+2.12% for TimesFM at leads1/7/14. With seven channels held equal, increments are +1.43%/+1.59%/+1.55% and +4.72%/+3.25%/+6.43%. These smaller, representation-dependent regional increments must not be conflated with the earlier B-to-D contrast.

Seven zero channels alter forecasts by up to6.05GWh and6.93GWh respectively, and improve mean day1 error by1.17% and1.99% despite adding no event information. Placebo effects are model/lead dependent, and regional versus placebo is negative for Chronos day1. Thus neither small calendar gains nor differing channel counts establish a pure regional-information mechanism. Both-year/state details and all controls remain visible.

### 4.7 Recorded-source availability and revisions

The frozen raw compilation exactly matches a recorded29October2026 Git revision. Three older Internet Archive CSV captures were recovered, decompressed and checked against provider digests. Differences include Maharashtra1January2025 620.30→558.80GWh and Karnataka313.35→259.79GWh; these are observed revisions, not a determination of which value is true. All150 selected festival case labels match the8November2025 archive, while some input-history and non-event values differ. Sparse archives do not reconstruct every release.

For fixed1September/1October2026 India-midnight cutoffs, the observed Git snapshots end30August/28September. A new48-task,672-prediction experiment extends first-unseen forecast horizons to score identical14 issue-relative dates with lagged versus ideal retrospective contexts. Mean scaled errors rise by about3.9%–11.3% across the tested families/modes. These two dates do not establish general operational degradation, and recorded timestamps are not certified first-publication times. The original benchmark is a retrospective available-date study, not a fully reconstructed operational trial.

### 4.8 Bounded numerical reproduction and version2 tree interface

A clean Python environment without inherited packages passes32 tests and saved-output audits. A separate scalar implementation reproduces Ridge examples and parameter IDs but fails tight tolerance for8/12 float64 tree examples (maximum4.2798GWh). Inputs differ by onlyabout2.4e-11; identical production matrices reproduce exactly across one/two threads. Under the separately specified float32 interface, all12checked tree forecasts and3chosen configurations reproduce exactly. This is bounded internal software review, not independent human approval or full clean-room model inference.

Version2 rich-calendar LightGBM2026 annual MASE is0.69444/1.68901/2.13381, monthly0.62203/1.49159/1.84560. These do not reverse the recorded Chronos aggregate comparison. The version1 table above is historical evidence; no forecast was silently replaced. A run-metadata path-formatting failure after version2 forecasts/metrics completed was repaired from independently audited artifacts; its traceback/execution source are retained.

### 4.9 Multi-festival performance does not support one universal winner

In the new matched history/ordinary-calendar comparison, next-day Holi MASE is0.65920 for Chronos history versus0.79841 for basic-calendar Ridge. Around Ganesh Chaturthi, basic-calendar Ridge instead scores0.43197 versus Chronos history0.46701, and calendar SARIMAX lead14 scores0.48067 versus0.79805. Around Ugadi/Gudi Padwa, next-day calendar SARIMAX scores0.32840 versus Chronos history0.35381. Around Dussehra, monthly rich-calendar Ridge scores0.67399 versus0.71885 for Chronos history. Around the unchanged broad Diwali cohort, ordinary-calendar TimesFM scores0.52136 next day versus Chronos history0.54564. These are descriptive examples, not statistically established winners or selected deployment models. Complete fifteen-configuration tables, individual years/states and all leads are reported in [the versioned report](../results/multifestival_models_v1/REPORT.md).

The scope differs from the earlier regional-Diwali table: regional event-feature arms are not silently relabelled as ordinary-calendar configurations. Previously reported positive/negative regional-Diwali results remain unchanged. Near ties, including ETS and naive longer-lead Holi errors, do not support fine ranking claims. Neither larger case counts nor more configurations create additional independent years or resolve historical pretraining exposure.

Three native adjacent-quantile crossings occur in the expanded Chronos-calendar run, at levels0.35/0.40 for Karnataka spring2024 lead1cases; none occur in the new TimesFM scored outputs. Crossings are retained without sorting or clipping. Point-metric audits pass but do not certify ordered or calibrated distributions. Chronos forecasts on the old150Diwali cases agree with earlier calendar controls within small batch floating-point differences (maximum0.0000611GWh); TimesFM history/calendar predictions on those same old cases match exactly. These checks are bounded internal software evidence, not external human review.

### 4.10 Explicit day flags can help without establishing a universal encoding

The added-feature primary next-day results are below. These scores use the same72anchor/lead cases per arm, with24distinct next-day festival/state/year targets; they are not the earlier full-window scores.

| Model variant | Ordinary calendar | Plus day flags | Plus windows |
| --- | ---: | ---: | ---: |
| Rich monthly Ridge |1.24369|0.56112|1.18795|
| Annual SARIMAX |1.31035|0.53159|1.31002|
| Stable monthly LightGBM |1.28595|1.26810|1.27750|
| LightGBM leaf-minimum2sensitivity |1.27323|1.09736|1.24629|
| Chronos-2 |1.37110|1.32921|1.35326|
| TimesFM-3 |1.34818|1.10330|1.35036|

Large aggregate Ridge/SARIMAX day-flag gains exceed their zero/placebo changes: next-day day-versus-placebo MASE differences are−0.68345and−0.77834respectively. TimesFM's corresponding difference is−0.25498; Chronos's is−0.07605. These are paired descriptive error differences, not significance or causal estimates. Zero-valued inputs themselves change some point forecasts by up to4.22GWh for Chronos and6.00GWh for TimesFM; SARIMAX optimiser sensitivity reaches0.286GWh, while Ridge/tree zero controls are effectively identical. The full controls, all leads and individual-year/state/family outcomes remain reported.

Feature support explains why weak tree gains cannot be interpreted as inherent irrelevance. An annual day indicator may have only one or two active past rows, below the original tree leaf minimum. The separately declared minimum2regime improves more on day flags but remains sparse-history exploratory evidence; it is not selected as a final configuration. Day flags harm some family-specific comparisons, including the spring group for several models. In the wider classical window cohort, next-day Ridge MASE changes0.57813→0.45554and SARIMAX0.57478→0.41872with day flags; these smaller gains do not establish full-window foundation improvement, which was not evaluated with the new features. Broad-window encodings are smaller or mixed, so neither a universal feature benefit nor representation-independent mechanism is established. At that checkpoint a pooled-event comparator had not run. The later pooled_festival_v1 study is now complete and audited: pooled versus typed gains depend on model/lead; no universal identity superiority is claimed.

### 4.11 Ordinary-day diagnostics and bounded implementation checks

In the matched non-event sample, day flags lower aggregate next-day MASE for all six variants: Ridge0.29540→0.28190, SARIMAX0.25238→0.24862, original tree0.33488→0.32823, capacity2tree0.32582→0.31406, Chronos0.26101→0.24453and TimesFM0.24067→0.23210. This is not a claim of exhaustive all-day improvement. Costs appear at other leads: Chronos day flags increase non-event lead14MASE by0.02561and the capacity2tree by0.00717. Event/control raw error levels are not causal contrasts; feature arms must be compared within each matched cohort.

Thirty-seven software tests pass. Independent stdlib audits reconstruct both primary and wider classical labels, cases, scales, paired contrasts and hierarchical metrics. A separate date/NumPy implementation reconstructs all1296foundation task inputs (target vectors and covariate matrices) byte-for-byte across event/non-event cohorts without importing experiment feature/model helpers. Fitting logs verify matching label hashes across arms, fixed declared parameter budgets and temporal cutoffs. Original calendar Ridge/tree/SARIMAX/TimesFM baseline points match the previous matched study on the primary cohort exactly; Chronos differs only by up to0.0000611GWh batching arithmetic. Eight native Chronos adjacent-quantile crossing pairs are retained across the new event/non-event arms; TimesFM has none in these scored outputs. These are internal implementation checks, not ordered/calibrated uncertainty certification or independent human scientific review. All466protectedprior source/result/presentation/protocol hashes remain unchanged.

## 5. Prospective freeze and pending outcomes

`prospective_20261030_v1` freezes 252 forecasts from six configurations: TimesFM history/calendar, monthly rich-calendar Ridge/LightGBM, last value and weekly repeat, for three states and fourteen target days. Issue time is 30 October 2026 05:35:15 UTC, with unchanged observed context ending 28 October. Origin (first unseen date) is 29 October, distinct from issue time. Only 216 predictions for 31 October–11 November are prospectively eligible; 29/30 October are excluded. Local selection uses pre-2026 data and deployment labels end September30. Parameters were actually computed at the30October issue time using a simulated monthly policy with an October1 data-window cutoff; no claim is made that those parameter files existed on October1. No 2026 regional holiday indicators are supplied. The initial freeze is in GitHub commit `cabd5982e1948652b9841d6c31a2380f6f314198`.

**No prospective outcomes or scores are available in this draft.** Actuals must be acquired after their dates, preserved with retrieval/vintage/source hashes and scored into a new directory without changing predictions. A registered GitHub workflow schedules12–20November checks, and its pre-period manual dry run succeeded without downloading outcomes or scoring. It verifies the original forecast Git blob, requires complete positive GWh labels and preserves first-snapshot results; actual after-period operation remains unrun. The tested workflow remains deliberately paused despite later explicit authorization for public GitHub synchronization; it has not been re-enabled. This is one forecast episode with lagged context and a shared source, not independent-source confirmation or adequate independent festival replication. Festival-specific secondary analysis requires independently verified 2026 event definitions; primary scoring uses all eligible dates.

## 6. Limitations, contribution decision and reproducibility

Remaining limitations include unresolved source reuse/processing terms, annual-versus-amended calendar definitions, historical and proxy model overlap, retrospective availability, dependence across dates/states, only two primary exploratory event years and no independent human/clean-room review. Generic calendar/learned event features already have close prior work. A new-method or novelty claim is not supported by the present design. A defensible empirical/negative-results contribution may be possible if the provenance, independence and submission gates are completed.

Protocols precede new experiment outcomes but follow historical result inspection. Full selection/fitting logs, failed/negative findings, prediction files, model/source/code hashes, test logs and reports are versioned locally; completed checkpoints are synchronized to the existing public GitHub repository under the user's later explicit authorization; no upstream reuse grant is implied. Original expanded results are preserved. Thirty-two software tests and persisted-output audits pass; these checks address specific leakage and integrity risks rather than certifying zero errors. Separate software implementations, bounded source vintages, model-specific audits, tests, human review and future prospective scoring have different statuses and must not be conflated.

## References

1. Kreusel et al. (2026). *On the Encoding of Calendar Features in Covariate-Informed Time Series Foundation Models*. arXiv:2610.13676v1. https://arxiv.org/abs/2610.13676
2. Alipour et al. *Impact-driven event covariates for time-series foundation models*. Amazon Science primary page. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models (final bibliographic/venue metadata remains to be checked).
3. Kaljevic, Arzola and Zhang (2026). *Benchmarking Time Series Foundation Models for Load Forecasting Under Covariate Uncertainty*. arXiv:2610.07232v1. The primary page reports acceptance for a 2027 conference; do not describe it as a journal article. https://arxiv.org/abs/2610.07232
4. Meyer et al. *Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges*. arXiv:2510.13654v3. https://arxiv.org/abs/2510.13654
5. Chronos-2 report/model and TimesFM official code/model sources: see `PRETRAINING_AUDIT.md`, `RESEARCH_REFERENCES.md` and `results/second_model_audit_v1/REPORT.md` for exact identities, links and limits.
6. Data and government calendars: full source URLs and attribution in `DATA_SOURCES.md` and `REGIONAL_CALENDAR_AUDIT.md`. Reuse and amendment gaps are explicitly unresolved.
