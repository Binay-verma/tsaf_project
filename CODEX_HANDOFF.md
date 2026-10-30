# Codex handoff — TSFM India

Updated 30 October 2026. This is a portable project-state summary, not a verbatim chat export. Use repository files and recorded outputs as evidence. Codex should not need access to the original ChatGPT conversation to resume useful work.

## Latest checkpoint — multi-festival extension, step 1 completed

User authorized proceeding one task at a time within the college deadline. `results/multifestival_cached_v1` freezes30anchors,24festival/state/year groups and528 identical cases/configuration across Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali in2024–2025. Nine unchanged saved daily configurations yield4752 prediction rows. No labels missing, no new fits or festival features. The existing broad Diwali cohort is preserved. State coverage differs by festival; no absent-state zero-impact controls. Dussehra2025/Gandhi coincidence and Spring2025/Eid proximity are explicit.

Independent stdlib audit reconstructs all528cases, scales, labels,648metric cells and equal-state/year aggregation;71source/original/prospective hashes unchanged. Existing32tests pass. Markdown report initially failed because optional `tabulate` is absent after all scientific outputs completed; failure retained in report_failure.json. `report_multifestival.py` recovered report/run metadata without changing predictions/metrics or fabricating timing. Original scoring source/protocol preserved.

Step2 completed in `results/multifestival_models_v1`:15configurations,7920scored forecasts,528same cases each. Classical worker completed1584rows:12annual SARIMAX fits and31monthly additive weekly ETS fits,45optimiser attempts including2nonconverged Delhi2025calendar attempts before the predeclared training-only Powell retry converged. Fresh foundation inference completed470Chronos ordinary-calendar contexts and940TimesFM history/calendar contexts. All workers exited successfully; no model job remains running. Independent stdlib audit reconstructs1080metric cells; deployment/input/weight/source audits pass. ETS scalar recurrence reproduces six date-selected deployments (max1.42e-14GWh). New TimesFM reproduces old150Diwali history/calendar cases exactly; Chronos matches old ordinary-calendar control points within6.11e-5GWh batching differences. Three Chronos native0.35/0.40quantile crossings on Karnataka spring2024lead1cases are retained; TimesFM none. Do not sort away the issue or equate point-audit pass with calibrated uncertainty.

Rankings vary across festival and lead. Full15configuration tables in REPORT.md;90descriptive ordinary-calendar/history contrasts and432state/year relative-effect cells retained, not festival-identity interventions. Earlier regional-Diwali arms remain distinct and unchanged. New eight-slide PPTX/PDF supplement, all-lead tables/charts, fixed-date forecast illustrations and notes are under `presentation/multifestival_update_v1/`; PPTX ZIP/notes and8PDFpages checked, slides3/6visually inspected. Original12-slide deck preserved. Viva preparation and MODEL_COMPARISON_SCOPE.md explain comparison boundaries. Manuscript/status/gates updated. Commands and limitations in MULTIFESTIVAL_REPRODUCTION.md.

Next authorized scientific experiment: incremental additional-festival covariates with a separately audited training-year date ledger and fixed encodings; not yet run. The new diagnostic uses ordinary calendar/history, not new event identities. Source/calendar review, rights response, external human review and later frozen outcomes remain open. Sharing hold, paused prospective workflow and no-duplicate-email instruction below remain in force; new work is local and no future actuals acquired. No environment publication or public push.

## Earlier checkpoint — gate studies completed; college deadline and sharing hold

The user now needs a college presentation on1November2026 (day after tomorrow from30October). They report sending the source-permission email manually. Verified address supplied from the official CICERO employee profile; no assistant email was sent. A previous Gmail send authorization was superseded by manual sending. **Do not send duplicate email.** Binay Verma is author/requester, not an independent reviewer.

Presentation: `presentation/College_Presentation_Binay_Verma_2026-11-01.pptx`, matching PDF and SPEAKER_NOTES.md;12slides/12pages, embedded notes, source credit, own aggregate charts only. Renders checked. Label as ongoing academic research; no completed prospective accuracy result by1November.

**Sharing hold:** earlier GitHub pushes are public. After user said college-only/not publishing, this was disclosed and a private/public preference question is pending. Do not push the new research/deck until choice is confirmed. The existing prospective workflow was deliberately paused via API (204; state disabled_manually) to avoid automatic public score uploads. It had already registered active and completed a successful pre-period manual dry run. After explicit sharing choice, make/verify repository private if requested (or keep public if confirmed), push saved work and re-enable workflow as appropriate. Do not silently publish or claim paused workflow is still active.

New `mechanism_controls_v1`:9arms x2pinned TSFMs x128state/origin tasks =2304fresh inference tasks,2700scored rows on150same cases/arm. Scalar and7-channel generic/regional, zero and active placebo controls. Audits pass; zero channels change point forecasts byup to6.05/6.93GWh. Regional effects representation-dependent; not a universal/causal provenance mechanism. Reports include all years/cases.

`provenance_review_v1`:32tests pass in working/clean no-system-package envs. Separate scalar implementation reveals float64 tree sensitivity (8/12examples fail; max4.2798GWh) despitefeature differences~2.4e-11. Failed checks retained. `stable_tree_refit_v2` explicitly casts feature matricesfloat32,648selection fits/81chosen/999deployment/53622predictions, and all12checked forecasts/3choices reproduce exactly in separate implementation. No original/frozen predictions replaced. Metadata-path error after completed fits was repaired with retained traceback/execution source and audited artifacts; no fake wall time.

Source frozen raw bytes match a29Oct2026 Git revision. Git history beginsMay2026, but olderWayback captures prove earlier public snapshots; never claim Git start is first data publication. Three compressed archive payloads were decoded and checked against provider digests; observed historical revisions include61.5GWh, while150selected festival labels agree with checked later2025archive. Raw snapshots remain outside checkout, with restorer/hashes/URLs provided. `vintage_sensitivity_v1`48tasks/672predictions quantifies two fixed midnight source-availability scenarios (last labels2/3days behindissue; matched mean errors increase3.9–11.3%). Not full real-time reconstruction or future scoring.

Six notice/date rows and28used-anchor worksheet strengthen calendar evidence; no final amendment chain is certified. Public source rights searches did not establish applicable permission. Reference request and review brief under `review/`; curator response and independent human sign-off pending. User reports email sent; do not fabricate response/licence.

Current docs: CURRENT_RESEARCH_STATUS.md, manuscript/DRAFT.md, manuscript/SUBMISSION_GATES.md, RESEARCH_GATE_REPRODUCTION.md. Immutable prospective original inputs/protocol/predictions unchanged. Added CLARIFICATIONS.md distinguishes simulated October1 label cutoff from actual October30 fit computation; it does not change forecasts. Source vintages retrospective; index-time purges do not certify historical publication availability. No local model process continues after this session.

## Earlier completed checkpoint — matched models and manuscript

The phase-two checkpoint below is now extended with `results/timesfm_matched_events_v1/`: 384 inference tasks,5376 forecast-day outputs,450 scored rows on150 exact event cases/mode in2024–2025. History/calendar/regional TimesFM3 were compared with cached Chronos/Ridge/SARIMAX on identical cases, with finite outputs/source labels/scales/metrics/case hashes independently audited. Batch4 versus solo predictions match exactly on the first4 tasks/mode. These tasks are not independent event replications.

TimesFM regional mean per-state/year MAE reductions at leads1/7/14 are +3.49%/+14.72%/+18.33%, while matched two-year Chronos effects are −2.30%/+1.04%/−0.93%. TimesFM day1 is negative in2024 and positive in2025. Retain both scopes and the original four-year Chronos negative result. B-to-D still changes information and channels; no provenance mechanism, clean exposure, universal benefit or new-method claim is established. Native TimesFM80% interval coverage varies substantially, not declared calibrated.

`manuscript/DRAFT.md` integrates these completed findings and pending prospective evidence; `manuscript/SUBMISSION_GATES.md` states remaining requirements. `CURRENT_RESEARCH_STATUS.md` is current. `PHASE2_REPRODUCTION.md` and `requirements-phase2.txt` document actual installations/pins and remaining clean-room limitations. `results/research_review_v2/REPORT.md` records live nearest-paper/source rights checks, including repository identification/coverage mismatch and unresolved terms.

Twenty-eight tests pass, including a prospective scoring gate with synthetic in-memory fixtures only. `src/score_frozen.py` blocks scoring until the full target period ends, requires later actuals provenance, rejects missing/nonpositive labels, verifies the forecast hash and excludes issue-day/past targets. It has not scored real future data. No outcomes through11November exist here. The immutable original prospective freeze was pushed at cabd5982e1948652b9841d6c31a2380f6f314198; later historical findings did not change it.

Immediate remaining offline work: full equal-information/dimension/placebo controls across both model families and nested past-only learned-encoding comparisons before mechanism claims. External/scientific gates: amendment-aware calendars, explicit reuse/processing/vintage evidence, independent source/region/event coverage and human/clean-room review. After11November, acquire and audit actuals then score the frozen episode in a new directory. One episode is limited evidence, not a complete confirmatory study. Do not call the manuscript journal-ready or submitted. No background model/inference job remains running at this checkpoint.

## Phase-two completed checkpoint — 30 October 2026

New results in `results/strong_refit_v1/`: 891 pre-year validation fits, 162 selected configurations, 1,998 annual/monthly deployment fits and 107,244 forecasts; no failed fits. Rich causal history, ordinary calendar and regional modes for Ridge/LightGBM, 2024/25/partial26; parameters frozen within year. Exact 8,937 matched historical Chronos cases per configuration. Monthly updates improve several aggregate scores but harm some festival-year cases. Full reports and independent audits retained.

`results/regional_transfer_v1/`: 162 fixed-Ridge fits, 53,622 predictions; local, pooled-all and leave-region-out arms. Target historical context/normalization is allowed; held-region regression/scaler fitting is excluded and tested. Transfer generally degrades; pooled-all often helps but is not unseen-region fitting.

`results/second_model_audit_v1/`: TimesFM3 pinned code/weights, first weight upload 2026-08-24, actual 1.32 GB SHA-256 verified and matched first upload, forty installed code files match pinned source. Noncommercial academic research terms retained; weights/vendor package outside checkout. Eighteen fixed CPU API tasks produced 252 forecast days and 2,268 native quantiles. This is a successful small API fixture, not broad second-model/festival replication. Network access now works for formerly blocked domains. Twenty-five total unit tests pass; phase-two persisted-output audits pass; historical sources/results remain unchanged.

**Prospective forecasts now exist:** `results/prospective_20261030_v1/` freezes 252 predictions from six fixed configurations across three states, using the unchanged data through 28 October. Issued 30 October; first-unseen origin 29 October. Only 216 predictions targeting 31 October–11 November qualify as future at issuance. Oct29/30 are explicitly ineligible. No outcome retrieval/scoring occurred. Ordinary calendar only; no unverified 2026 regional anchors used. Model/selection/fit/forecast hashes and audit saved. Push this checkpoint to GitHub before those outcomes; never overwrite the frozen predictions. Their later scores, source revisions and single-episode limitations remain open. This supersedes older statements that no prospective forecasts have been made.

Next: complete evidence-linked manuscript draft/updated gap matrix and research-source follow-up; run full matched multi-model calendar controls before new-method claims. Acquire prospective actuals only after target dates, preserve first-retrieval/vintage evidence and score into a new directory. Calendar amendments, explicit data reuse terms, independent source/human review and adequate independent event evidence remain journal gates.

## Earlier continuation checkpoint — 30 October 2026

The split archives were verified (180 transfer entries, 179 checkpoint file hashes) before edits. Python 3.12.14 `.venv` reuses installed numerical packages and installs holidays 0.107/statsmodels 0.15.0. The 11 original unit tests and 5 new controlled-experiment tests pass. `src/audit_checkpoint.py` independently reconstructs labels, scales, matched cases, saved MAE/MASE and LightGBM selection boundaries for all 103,254 historical rows without rewriting original results.

New **exploratory** experiment `results/calendar_controls_v1/` has a protocol saved before outcomes, 612 fixed Ridge fits, 215,577 predictions and 17 arms. It compares identical scalar/7-channel generic and regional encodings, zero controls, seeded weekday-matched placebos and +/-1/2-day date shifts. Main analysis uses 2024–2025 because regional training anchors before 2022 are incomplete; 2022–2023 is secondary. Only two primary annual clusters: no significance claims. All original data and expanded result files (61 hashed files) remain unchanged. Calendar and seven-channel regional Ridge forecasts reproduce the historical B/D forecasts; zero-padding forecasts are identical.

Preliminary primary event MASE (leads 1/7/14): generic scalar 0.60257/1.34947/1.40894 versus regional scalar 0.61113/1.28008/1.40395; generic 7-channel 0.42600/1.11742/1.23166 versus regional 7-channel 0.42466/1.25384/1.47234. Representation and year dependence are substantial; this does not establish a reliable regional-date mechanism or any new TSFM benefit. Shift controls must not become outcome-selected calendar dates. See `results/calendar_controls_v1/REPORT.md` for completed analysis, all controls, and the per-year figure.

Official Chronos/TimesFM repository documentation snapshots are stored with hashes under the experiment's `external_evidence/`. TimesFM 3.0 has native future covariates but downloaded weights are under a separate noncommercial licence. This is not a weight identity audit or an inference run. arXiv, robbieandrew.github.io and Hugging Face model-metadata requests returned proxy HTTP 403; their literature/reuse claims were not newly verified. No network settings, published configuration, paid APIs or source snapshots were changed.

Second completed checkpoint: `results/residual_intervals_v1/` adds a protocol-frozen, strictly past-target residual-calibration baseline: 25,380 quantile/interval forecasts, four configurations, 2024–2025, 6,345 matched cases each, and at least 704 prior errors at each origin. Three calibration tests pass. Independent checks reconstruct 144 first/event-origin calibration examples, labels, coverage, width and interval scores. Chronos history-only nominal 90% intervals cover 89.74% of all day-1 outcomes but 77.25% within festival windows (equal state/year averages). These are retrospective calibrated residual intervals, not native model quantiles or guaranteed coverage. No retuning followed these outcomes.

All 19 tests pass together. Raw state extraction and metadata units are independently checked; each full series has 112 missing entries and no nonpositive recorded values. Zero padding and Delhi generic/regional identities pass. All 61 protected historical files remain unchanged. Completed reports/figures are in both new result directories. `CURRENT_RESEARCH_STATUS.md` maps evidence, pending work and actual external blockers. `CONTINUATION_CHECKSUMS_20261030.json` and `src/verify_continuation.py` verify intentional current-state edits while retaining the original historical transfer manifests.

Next: freeze and run stronger causal local histories/refit comparisons in a new experiment directory, then predeclared regional transfer and model-specific audit before foundation-model controls. Data reuse rights, amendment-aware dates, uncertainty, untouched confirmation and human review remain open. No new model weights are installed and no background training job is promised.

## GitHub synchronization preference

The user requests pushes after completed tasks and explicitly authorized the full project, including data/results/evidence, to `Binay-verma/tsaf_project`. The Git checkout is `/workspace/tsaf_project`; `/workspace/tsfm_india` remains the original working copy. The initial full-project push to `main` was verified at commit `eb6e9b0b9cc8c4dcc0778cc82d3af65b1dd8d223`. A follow-up metadata commit records this result. `src/verify_continuation.py` now defaults to `GITHUB_CHECKSUMS_20261030.json` when present; older manifests remain historical. Complete normal commits/pushes from the Git checkout, verify remote SHA, preserve attribution and do not force-push. Prefer the Git checkout for subsequent development so it does not diverge from the original working copy.

## Goal and user intent

The user, Binay, began with a literature survey and no code/data. They asked for automatic data discovery, understanding, implementation, training, testing, festival features and deeper research. They explicitly rejected overfitting or changing experiments to obtain impressive numbers. They want a project strong enough to submit to a credible journal, not merely a quickly completed demo. They prefer sustained autonomous execution and dislike repeated requests to proceed. They asked for careful work and continuity into Codex.

The earlier assistant over-described a runnable benchmark as a finished project. This was corrected: **software and expanded evaluation work; journal-level research remains unfinished.** Acceptance, novelty and zero errors are not guaranteed. Estimated 3–6 active research weeks is a plan, not time already spent or an acceptance promise.

## Read in this order

1. `AGENTS.md`: compact working rules.
2. `VALIDATION_REPORT.md`: current coverage, numbers, methods and limitations.
3. `DEEP_RESEARCH.md` and `RESEARCH_REFERENCES.md`: nearest prior work, contribution assessment and research sequence.
4. `JOURNAL_PROTOCOL.json`: draft next-study design and open gates; not externally preregistered.
5. `REGIONAL_CALENDAR_AUDIT.md` and `PRETRAINING_AUDIT.md`: exact evidence and residual uncertainty.
6. `CONTINUE_IN_CODEX.md`: setup, commands and how to preserve future context.
7. `USER_LITERATURE_SURVEY.pdf`: original user-provided starting document. Its claims are background, not automatically verified facts.

`README.md`, `START_HERE.md`, `PLAN.md`, `PROGRESS.md` and `FINAL_REPORT.md` have current-status notices above older material. Avoid confusing their historical pilot numbers with the expanded evaluation.

## Data and target

- Target: daily **energy met/supplied**, MU = GWh. Not latent unconstrained demand, household consumption or hourly peak power.
- States evaluated: Karnataka, Delhi and Maharashtra. More columns in the raw compilation do not automatically imply comparable clean state series.
- Original source: Hunt/Bloomfield Zenodo DOI 10.5281/zenodo.14983362, CC BY 4.0, corrected daily energy file. Actual coverage 2013-01-01–2024-04-28; 3,955 rows, 3,900 unique dates, 55 extra duplicate rows, 236 missing days; seven conflicting dates across selected states. Conflicting labels are missing, inputs can be filled causally, missing labels are not scored.
- Expanded source: Robbie Andrew POSOCO compilation, separate frozen snapshot in `data/external/POSOCO_data.csv` and selected-state table `latest_state_energy_GWh.csv`, through **2026-10-28**. Do not splice it into the original corrected source. Explicit reuse licence and upstream imputation/revision details remain unresolved. Preserve attribution; do not publish it as newly licensed open data.
- The SASEA Indian national series shares source lineage with the earlier data and is not an independent replication source. Raw snapshots, metadata and audits are included.
- Source date/reporting-lag checks are recorded, but a genuine real-time data-vintage reconstruction has not been done.

## Completed experiments

Original `results/benchmark_original_s28/`: scheduled-origin 2022/2023 benchmark, three states and horizons 1/7/14, multiple model/feature ablations. Preserved as an earlier experiment.

Expanded `results/extended_validation/`:

- Daily origins per state: 352 (2022), 352 (2023), 353 (2024), 352 (2025), 288 (partial 2026). **1,697 per state**, 5,091 state-origin tasks.
- Origin denotes first unseen date; lead h target = origin+h-1. Lead-7/14 scores are individual days, not aggregate weekly/fortnightly predictions.
- **103,254 verified prediction rows** across configurations; this is not a count of independent replications.
- All daily origins: Chronos history only, Ridge A/B/D and last-value/weekly-repeat baselines. LightGBM A/B/D covers 2026 only.
- Chronos calendar/festival and SARIMAX: matched event cohorts only, **not all-year evaluation**. Four Diwali years 2022–2025; union of +/-3-day windows around declared main and state-specific dates.
- Ridge alpha 10; SARIMAX (1,0,0)x(1,0,0,7); annual fitting on preceding 730 days. Chronos uses rolling context 730, independent tasks, no task fine-tuning. Different adaptation schedules limit architecture-level claims.
- LightGBM: eight configurations per state/mode/lead, 216 selection fits, 27 selected configurations. Validation starts 2025-07-05, labels end before 2026, training-label purge enforced, refit on pre-2026 data. Added after looking at 2026: **exploratory**, even though hyperparameter selection itself uses past validation only. Six history features and limited grid are not the strongest conceivable local baseline.
- All 36 SARIMAX fits ultimately converged. One failed L-BFGS fit used a documented Powell retry selected on training likelihood/convergence, never test score. Failed forecasts retained.
- Eleven unit tests passed in the original environment. Independent checks validated dates, labels, finite/unique predictions, matching daily/event cases, validation minima and purge dates. This is evidence against specific bugs, not a zero-error guarantee.

## Main saved results

Partial 2026 macro MASE across three states, lower better, 288 origins per state/lead:

| Model / mode | Lead 1 | Lead 7 | Lead 14 |
|---|---:|---:|---:|
| Chronos / history | 0.467902 | 1.162937 | 1.361749 |
| Last value | 0.617451 | 1.257600 | 1.514284 |
| Ridge / history | 0.609002 | 1.271352 | 1.463683 |
| Ridge / ordinary calendar | 0.578452 | 1.617819 | 1.978059 |
| Ridge / regional festival | 0.574877 | 1.620542 | 1.946305 |
| LightGBM / history | 0.670228 | 1.293954 | 1.592660 |
| LightGBM / ordinary calendar | 0.634528 | 1.465224 | 1.932487 |
| LightGBM / regional festival | 0.634528 | 1.465224 | 1.932487 |
| Weekly repeat | 1.228532 | 1.257600 | 1.514284 |

Mean per-state/year percentage MAE reduction from D regional festival versus B ordinary calendar, four historical event years:

| Model | Lead 1 | Lead 7 | Lead 14 |
|---|---:|---:|---:|
| Chronos | -4.623% | -0.561% | -2.317% |
| Ridge | +22.006% | +1.102% | -16.851% |
| SARIMAX | +24.241% | +13.057% | -4.015% |

Positive = improvement, negative = worse. Bootstrap intervals resample only four annual clusters and are descriptive. Do not interpret many neighbouring days or three correlated states as large independent event evidence. Current Chronos festival encoding fails to improve average error; longer-horizon effects are unstable. All configurations and per-state/year results remain visible.

## Calendar audit status

Twelve annual government-office schedules, three states x 2022–2025, are audited against the previously used library PUBLIC category. Government-office closures, bank holidays and religious observances are distinct definitions. Printed annual dates can differ from later amendments; these differences are not automatically library errors. The installed GOVERNMENT-category switch returned no dates for audited historical cases, so a category switch is not a verified fix.

Examples: main Delhi Diwali dates 2024-10-31/2025-10-20; Maharashtra Lakshmi Pujan 2024-11-01/2025-10-21 plus subsequent Bali dates; Karnataka Naraka/Balipadyami include 2024-10-31/11-02 and 2025-10-20/10-22. Expanded primary features use explicit Diwali anchors plus ordinary calendar features, not an uncertified generic holiday flag.

All amendments, local/election/emergency closures, moon-sighting changes and all earlier training-year holidays are **not** certified. Main 2020/2021 Diwali anchors were included in feature histories before inspecting calendar-model results. Calendar PDFs and date-level/source ledgers are included.

## Foundation model identity and overlap

- Model `amazon/chronos-2`, revision `29ec3766d36d6f73f0696f85560a422f50e8498c`.
- First weight commit `95a9710e2596287d08352589f42634fa5abdf0a7`, upload **2025-10-30T14:58:57Z**.
- First-upload and evaluated safetensors SHA-256, also verified against actual locally cached bytes: `ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42`.
- Genuinely later 2026 target observations postdate unchanged weights, conditional on source date integrity. This is not the exact pretraining cutoff and does not clear 2022–2025 or unknown historical proxies.
- Disclosed corpus names did not identify these Indian state series; no exhaustive numeric deduplication was done.
- Snapshot ends before main Diwali 2026-11-08: **no clean post-upload Diwali evaluation exists**. No prospective festival forecasts were made in this checkpoint. Do not claim otherwise.
- Weights are not bundled. New models need separate pins, licence and temporal-exposure audits.

## Prior work and research direction

The focused primary-source novelty audit already found close work: Kreusel et al. arXiv:2610.13676 (seven calendar encodings/four TSFMs), Alipour et al. impact-driven event covariates (Amazon Science 2026), Kaljevic et al. arXiv:2610.07232 (load/covariate uncertainty), Meyer et al. arXiv:2510.13654 (overlap), and classical Indian Diwali window regressors. All links and caveats are in RESEARCH_REFERENCES.md. This is not an exhaustive systematic review. Generic festival flags, event embeddings and India-only applications are not established novelty.

Candidate question: **Does verified regional calendar provenance improve unseen-region/event forecasting when encoding and feature count are controlled?** The present B-to-D contrast changes information, representation and dimension together; it does not isolate a mechanism. A potential paper could be a rigorous empirical/calendar-quality contribution rather than a new architecture, if the evidence supports it.

## Original next-action plan (current progress and immediate next step above)

1. Check package integrity and read the files above. Reproduce cheap tests/scoring before expensive model inference. Do not rerun the whole historical search merely to recover context.
2. Create a new experiment directory and versioned protocol before any new method results. Start with equal-information encodings, zero-channel/weekday-season-matched placebo controls and +/-1/2-day calendar perturbations. Use past-only target encoding with development-selected shrinkage/fallback. All current outcomes are exploratory for this new study.
3. In parallel research work within the same project, complete amendment-aware event provenance and source reuse rights; strengthen local features/refit schedules and select a second independently developed covariate-capable TSFM after its own API/weight audit. No need to request a new plan from the user.
4. Add unseen-region/event-year tests and quantile/coverage scoring; reserve new data/source for final confirmation. Freeze any genuinely prospective predictions before their outcomes arrive.
5. Run independent reproduction and human scientific/calendar review before writing submission claims. Preserve all failure cases and negative findings. The novelty may require a benchmark/negative-results framing or a pivot.

These are pending tasks, not experiments already performed. Full details and decision gates are in DEEP_RESEARCH.md.

## File map and implementation cautions

- `src/forecasting.py`: data loading, causal fills, original features, shared helpers. Expanded code calls its ordinary calendar subset.
- `src/extended_validation.py`: explicit regional anchors, feature construction, dense Ridge/naive and Chronos evaluation.
- `src/extended_sarimax.py` / `repair_sarimax_optimizer.py`: event-matched annual SARIMAX and training-only convergence repair.
- `src/strong_baseline.py`: exploratory train-only LightGBM selection and 2026 scoring.
- `src/audit_regional_calendars.py`: manually curated annual date ledger and comparison.
- `src/summarize_extended.py`: independent prediction checks, metrics, year-cluster intervals and figure.
- `src/write_validation_report.py`: generated report from saved metrics. Its narrative refers to this checkpoint; new studies need their own report.
- `src/cache_identity.py`: source/feature/model/package/cache hash checks. Existing manifest was adopted after review and is labelled accordingly, not preregistered. Package/version or line-ending differences on another machine can correctly trip the guard; investigate rather than bypass it.
- `src/verify_package.py`: new dependency-free transfer-integrity checker.
- `results/extended_validation/`: all verified forecasts, metrics, model selection, audits, environment and protocol evidence.

Original run: Python 3.12.14, CPU, torch 2.15.0+cpu, chronos-forecasting 2.3.2, holidays 0.107. Full package versions are recorded in `results/extended_validation/environment.json` and requirements files. The host-specific runtime environment and downloaded weight cache do not transfer automatically. Use relative project paths; do not rely on the old `/workspace/scratch/...` location. Do not assume GPU availability or that any job remains running.

## Continuity after every session

Update WORK_LOG.md with completed work, exact commands/checks, result locations and actual blockers. Update this file's current state and next actions. Save protocols before runs and checkpoints during long experiments. Keep a local Git history and backup; a private remote can be added when the user chooses. Avoid publishing unlicensed data. If exact conversational wording is needed, the user can separately copy/export the chat into a local reference file; the project handoff does not claim to be a full transcript.
