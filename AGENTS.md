# TSFM India project guidance

## Read before continuing

Read `CODEX_HANDOFF.md`, `VALIDATION_REPORT.md`, `DEEP_RESEARCH.md`, `JOURNAL_PROTOCOL.json`, `REGIONAL_CALENDAR_AUDIT.md` and `PRETRAINING_AUDIT.md`. The initial survey is `USER_LITERATURE_SURVEY.pdf`; treat its literature claims as background to verify. Earlier pilot documentation is historical. The expanded evaluation is completed; journal research is unfinished.

## User goal and working preferences

Build a defensible journal-level study of foundation-model forecasting for Indian electricity with regional festival/calendar features. The user wants substantial research, autonomous execution and honest results. Continue useful authorised work; avoid repeatedly asking whether to proceed. Explain material findings in plain language. Never optimise for attractive reported numbers, promise zero mistakes, promise acceptance or claim that planned work has been performed.

## Research integrity

- Preserve `results/extended_validation/` and the original pilot as historical evidence. Create a new named experiment directory for new methods, sources or model versions; do not overwrite results or bypass cache checks.
- Treat the already inspected 2022–2026 data as development/exploratory for new methods. Select features, event windows, hyperparameters and learned encodings only using the appropriate training/development folds. Never tune against the final test.
- Use chronological splits and purge overlapping future labels. Inputs at an origin may use only preceding target observations and genuinely available covariates. Score recorded labels only; do not score imputed labels.
- Match evaluation cases and availability rules across compared configurations. Retain failed fits, unsuccessful hypotheses and negative results. Record seeds, source hashes, actual model weights, packages and selection logs.
- The target is daily energy met/supplied in GWh, not unconstrained demand or hourly peak load. Historical revisions/publication lag are unresolved. Shared-source derivatives are not independent replication.
- Audit state holiday definitions and amendments. Twelve annual schedules are audited, not all amendments or historical dates. Do not infer holidays from observed electricity errors.
- The original four-year Chronos Diwali seven-channel contrast worsens mean day-1 festival MAE; preserve that negative result. Later day/window encodings on different festival/anchor cohorts have different effects and must not erase or be conflated with it. Do not claim universal festival enhancement. The original evaluation has only four event-year clusters; the matched second-model and new multi-festival studies have two historical years; nearby days/states/leads are not independent replications.
- Actual Chronos weights predate 2026 targets, but historical/proxy overlap remains uncertain. No post-upload 2026 Diwali outcome exists in the snapshot. Future-target predictions issued30October are frozen in `results/prospective_20261030_v1/`; they must not be overwritten or scored before later actuals are acquired. Audit every additional model separately.
- Generic calendar encodings and learned event covariates have close prior work. Verify primary literature before asserting novelty. Resolve reuse rights before publicly releasing the newer source snapshot.
- For added-festival features, use the named2022–2025ledger and explicit context/training-date bounds. Do not silently substitute generic library dates for Karnataka2023Ganesh18September or Maharashtra2023Holi7March. Distinguish72primary anchor cases from528secondary classical windows and the separate72matched non-event cases. Report original and capacity2tree budgets separately; do not select the better regime on evaluated errors. Zero/placebo controls do not establish causal or pooled-versus-typed identity superiority. Native quantile crossings remain visible and unmodified.

## Commands and continuity

Use Python 3.12. Start with `python src/verify_continuation.py` for the current GitHub checkpoint (standard library only). The original `src/verify_package.py` manifest is historical and will flag intentional later edits. See `CONTINUE_IN_CODEX.md` for environment setup and staged checks. `run_extended.py` reproduces expanded results; `run_all.py` is the older scheduled-origin experiment. Model weights are not bundled.

Before ending a substantial session, update `WORK_LOG.md` and the current-state/next-action sections of `CODEX_HANDOFF.md`. Record exact commands, outcomes, experiment directories, failures and actual blockers. Distinguish completed, running and planned work. Keep run checkpoints so work can resume without this conversation. Do not claim a process will continue after the session ends without verifying an actual persistent mechanism.

## GitHub checkpoints

The user requests that completed tasks be committed and pushed to `Binay-verma/tsaf_project`. They explicitly requested the full project, including data, predictions and evidence. Preserve attribution/reuse notices; do not invent a new data licence. Exclude local virtual environments, caches and credentials. Use normal commits and pushes, preserve remote changes, and verify the remote commit after pushing. Do not force-push without separate authorization.

## Latest sharing and outreach instructions

The user reports sending the permission email manually; do not send a duplicate through Gmail. Binay Verma is author/requester, not an independent reviewer. College presentation deadline is1November2026. After the earlier college-only sharing hold and repeated disclosure that GitHub is public, the user explicitly instructed "push it to github" on30October2026. This authorizes synchronizing the completed project to the existing public repository; do not change visibility or treat the earlier upload hold as still blocking that push. Research commit26cc645was pushed and remote SHA verified. Source permission is still pending; no reuse grant is implied. The prospective auto-scoring workflow remains paused; this push does not re-enable it or retrieve future outcomes. All frozen forecasts remain unchanged.

## Journal continuation scope (30 October 2026)

The user requests continued executable phases toward a Q1 journal. No specific venue or acceptance is implied. Use the current handoff and new pooled/label-transfer/daily reports rather than older checkpoint claims. Direct family-label exclusion still permits target-history exposure; do not call it wholly unseen-event transfer. Post-weight dates remain previously inspected retrospective outcomes. Retain native undercoverage/crossings and the strict scalar-review matrix discrepancy. Complete source rights, calendar amendments, independent human review and untouched confirmation remain separate gates. Verify a target journal's quartile database/year/category before calling it Q1. Continue authorized normal GitHub pushes; keep prospective automation paused and future forecast blobs immutable.

## New interval annex continuity

Preserve `results/prospective_interval_20261030_v1` guarded files from first public commit29bdd984770904a032cebe9efcd2a12a8d5ffc17. Its actual new issuance is30October15:12:14UTC/20:42:14IST, later than the unchanged original05:35UTCforecast. It retains native/frozen/expanding intervals for original TimesFM points;216eligible rows are72cases×3arms, not independent cases. No future labels before the full period ends; `score_interval_annex.py` reuses the original collector's exact completed actual vintage and first-commit/hash guards. Keep automation paused. Do not retune intervals on future scores, backdate issuance, overwrite native quantiles or call daily CQR a solution to the separate festival-feature cohort. New methods/issuances require new named protocols. Current calibrations remain historical/exploratory without a time-series exchangeability guarantee.
