# Current status — 30 October 2026

## Immediate goal: college presentation on1November2026

**Latest completed experiment:** explicit festival-day/window inputs have now been tested separately from the earlier diagnostic. `results/festival_features_v1` contains2592matched primary forecasts (six variants/six arms/72anchor-lead cases) and15840secondary classical window forecasts. Ridge/SARIMAX day flags show substantial next-day gains, TimesFM smaller gains and Chronos modest changes; broad windows are mixed. `festival_feature_spillover_v2` adds1296matched non-event forecasts; no aggregate next-day day-flag penalty in that sample, but some longer-lead costs. All controls, years and sparse-capacity regimes remain reported.37tests and source/metric/fitting/input-byte audits pass;8native Chronos quantile crossings retained, TimesFM0. No universal, causal, typed-versus-pooled or clean-test claim. The new eight-slide supplement is under presentation/festival_feature_update_v1. See FEATURE_INTERVENTION_REPRODUCTION.md, MISSED_STEPS_AUDIT.md and PROTOCOL_INDEX.md.

Multi-festival continuation now extends the earlier Diwali-only event study. `results/multifestival_cached_v1` completed a9-configuration diagnostic on528identical cases across Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali in2024–2025. `results/multifestival_models_v1` adds six matched configurations: SARIMAX history/calendar, weekly ETS, ordinary-calendar Chronos, and TimesFM history/calendar. All workers finished;15configurations yield7920scored forecasts. No missing forecast cases or scoring labels were dropped. Forty-three classical fits converged after45attempts; two unsuccessful attempts remain recorded. New foundation inference comprises1410contexts. Independent case/metric/deployment audits pass. Three native Chronos quantile crossings are retained; TimesFM has none in scored outputs. No new event identities were introduced. See MULTIFESTIVAL_REPRODUCTION.md, MODEL_COMPARISON_SCOPE.md and the separate college supplement under presentation/multifestival_update_v1. The original deck and prospective freeze remain unchanged.

The user reports sending the source-permission email manually and will present this as ongoing noncommercial college research. A12-slide editable PowerPoint, matching12-page PDF and speaker notes are ready under `presentation/`, signed Binay Verma. They use project-generated aggregate charts, not embedded raw datasets/model weights. Prospective accuracy remains pending after11November.

**Sharing status:** the user explicitly requested pushing the completed work after being informed the repository is public. Repository visibility was verified public and preserved. A normal push published the held project commits through26cc645; remote main exactly matched that research commit. The earlier upload hold is superseded for this synchronization. The prospective scoring workflow remains disabled_manually; no automatic scoring, future retrieval or workflow reactivation is part of this push. Original forecasts/dry-run evidence remain valid, and source reuse permission is still pending.

## Newly completed gate studies

| Work | Executed evidence | Interpretation |
| --- | --- | --- |
| Both-TSFM mechanism controls |2304 fresh inference tasks,2700 scored predictions,9arms,150 identical historical cases/arm | Regional increments depend on representation/model. Zeros change forecasts without event information. Two clusters/one placebo seed do not establish universal or causal benefit |
| Source vintage investigation | Exact frozen Git revision;3older Internet Archive CSVs with verified payload digests; dated revision inventory | Historical differences up61.5GWh; all150selected festival labels agree across the checked later archive, but some input histories/non-event labels differ |
| Availability sensitivity |48tasks,672predictions, two fixed issue dates, matched14-day targets in both models | Recorded midnight snapshots lag by2/3days; mean scaled errors increaseabout3.9–11.3%. Not complete real-time reconstruction |
| Separate numerical implementation | Clean environment without inherited packages; original float64 tree discrepancies retained | Tiny rolling differences can alter trees. Version2 float32 interface reproduces12checked forecasts/3choices exactly; internal software evidence, not independent human review |
| Stable tree version2 |648past-only validation fits,81choices,999deployment fits,53622predictions; audits pass | Precision contract chosen for reproducibility, not held-out accuracy. Original/frozen forecasts never replaced. Metadata-path failure transparently repaired |
| Calendar provenance |6stronger notice/date rows;28used-anchor worksheet; administrative/statutory scopes distinguished | Annual-as-issued evidence improved, final amendment/reviewer sign-off still unfilled. Official retrieval failures recorded, not treated as absence of amendments |
| Future infrastructure | Pinned-action GitHub workflow accepted, registered, actual pre-period dry run successful | No future outcome download/score occurred. Workflow remains paused and was not re-enabled by the explicit project push; after-period source/commit behavior is not already tested |
| Tests and artifacts |32tests pass in working and separate clean environments; source/case/scale/metric/hash audits pass; PPTX/PDF checked | Specific checks reduce risks; no zero-bug/leakage/acceptance guarantee |

Earlier expanded evaluation, richer baseline/refit and regression-region-transfer studies, matched TimesFM events, Ridge representation controls and residual intervals remain preserved. See their reports rather than treating forecast-row counts as independent replications.

## Key controlled result

Regional-versus-generic mean state/year MAE reduction at leads1/7/14:

- Scalar windows: Chronos +0.22%/−0.68%/−0.81%; TimesFM +1.17%/−0.09%/+2.12%.
- Seven channels: Chronos +1.43%/+1.59%/+1.55%; TimesFM +4.72%/+3.25%/+6.43%.
- Seven zero channels improve mean day1 error1.17%/1.99% without adding event information and change some point forecasts by6–7GWh.

These equal-dimension increments differ from the earlier calendar-to-regional contrast that also changes feature count. Scalar versus seven-channel comparisons themselves change representation/information. Historical exposure, limited event count and dependence remain.

## Evidence and presentation

- [Presentation files](presentation/README.md) and [speaker notes](presentation/SPEAKER_NOTES.md).
- [Mechanism controls](results/mechanism_controls_v1/REPORT.md).
- [Numerical-contract study](results/stable_tree_refit_v2/REPORT.md).
- [Source/internal review](results/provenance_review_v1/REPORT.md), [availability sensitivity](results/vintage_sensitivity_v1/REPORT.md).
- [Working manuscript](manuscript/DRAFT.md), [submission gates](manuscript/SUBMISSION_GATES.md).
- [Reproduction](RESEARCH_GATE_REPRODUCTION.md).

## Actual dependencies still open

The user reports emailing Robbie Andrew and is awaiting a reply. No assistant email was sent and no reuse grant is assumed. Verified professional contact is in the reference request; do not send a duplicate. An independent human reviewer is not yet named. The user's name is author/requester, not a fabricated independent sign-off. Calendar amendment certification and source processing/report-day/rights clarifications require evidence/review not yet obtained.

Future31October–11November outcomes have not completed; never fabricate their scores. The original cabd598 prospective forecasts/hashes remain immutable. Once sharing is confirmed, the tested workflow can be re-enabled for12–20November checks (07:15UTC/12:45India time) or scoring run manually after complete actuals. One episode remains limited confirmation evidence.

Use `/workspace/tsaf_project` as the active checkout. Existing checkouts are already isolated; do not restart or create a worktree just for setup. No model-fitting process remains running. No environment publication/configuration change occurred. New work is saved locally pending sharing choice; current local checkpoint manifest verifies file integrity separately from scientific validity.
