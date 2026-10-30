# Continuity work log

## 2026-10-30 — Expanded evaluation checkpoint and Codex handoff

Completed before handoff: dense 2022–2026 evaluation; four-year matched festival evaluation; 12 annual state-year calendar audit; actual Chronos weight identity audit; exploratory pre-2026-selected LightGBM; scoring, reports and focused primary-literature research. Current verified forecast-row count: 103,254. Eleven original-environment unit tests passed. Expanded results and all caveats are recorded in VALIDATION_REPORT.md.

Handoff changes: added AGENTS.md, CODEX_HANDOFF.md, CONTINUE_IN_CODEX.md, CODEX_START_PROMPT.txt, this log and a dependency-free package verifier. Included the user's original literature-survey PDF as USER_LITERATURE_SURVEY.pdf. Existing model code, predictions, data and published checkpoint findings were preserved. No new training, research experiment or Windows environment test was performed in the handoff step.

Transfer check before editing: all 172 files listed in the previous checkpoint manifest matched their hashes. The outgoing archive is rebuilt from the verified working tree and its own entries checked. Current verification command: `python src/verify_package.py`. Scientific unit tests were not rerun for these documentation-only changes.

Pending next action: load the handoff, verify the transfer/environment, define a new controlled encoding/calendar experiment with matched information and feature-count/placebo controls, then implement and run it without tuning against an untouched confirmation set. See CODEX_HANDOFF.md for the remaining data-rights, calendar, model, uncertainty and transfer work.

## Template for the next session

- Date and objective:
- Files changed:
- Protocol and result directory:
- Data/model/version identities:
- Exact commands and outcomes:
- Main findings, including failed hypotheses:
- Actual blockers or unfinished/running jobs:
- Next concrete action:
- Handoff updated:

## 2026-10-30 — Controlled representation experiment, first continuation checkpoint

- Transfer reverified with `python src/verify_package.py`: 179 entries pass before changes. Split transfer previously passed all 180 entries.
- Created Python 3.12.14 `.venv` with system numerical packages; `.venv/bin/python -m pip install holidays==0.107 statsmodels==0.15.0` succeeded. No application dependency declarations changed.
- `.venv/bin/python src/test_forecasting.py`: 6 pass. `src/test_extended.py`: 5 pass. `src/test_calendar_controls.py`: 5 pass (future perturbation, label purge/missing labels, placebo construction, dimensions, zero controls, shifted dates). Logs retained in `results/calendar_controls_v1/`.
- Protocol saved to `results/calendar_controls_v1/protocol.json` before experiment execution. `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python src/calendar_controls.py`: completed 612 fixed fits / 215,577 forecasts across 17 arms in about 21 seconds. No tuning; all outcomes exploratory. 2024–2025 primary; 2022–2023 secondary due incomplete early regional training dates. Zero and historical B/D reproduction checks pass; 61 data/historical-result hashes unchanged.
- `.venv/bin/python src/audit_checkpoint.py`: independently reconstructed key integrity/scoring/selection checks on 103,254 historical forecasts. No historical outputs rewritten.
- Main finding: no consistent provenance benefit; scalar regional day-1 MASE 0.61113 versus generic 0.60257, and 7-channel long-lead results worsen. Year/representation dependence retained. Date shifts are sensitivity controls, not chosen replacement dates.
- Retrieved official Chronos/TimesFM GitHub README snapshots with source URLs, retrieval dates, SHA-256. TimesFM 3.0 downloadable weights have noncommercial terms; neither weights nor inference audited yet. arXiv and newer source website blocked by proxy 403; no rights/novelty clearance claimed.
- Handoff current state updated. Next: independent new-result/source audit, report and evidence/gap matrix, then a separately registered transfer/baseline experiment. No publication/configuration changes and no long-running training processes.

## 2026-10-30 — Uncertainty baseline and independently audited continuation checkpoint

- Before interval outcomes, saved `results/residual_intervals_v1/protocol.json`: fixed 730-calendar-day signed out-of-sample residual calibration, strict target-date < origin, quantiles .05/.5/.95, four historical point configurations, 2024–2025 exploratory evaluation. No native model quantiles reconstructed or new pretrained inference performed.
- `.venv/bin/python src/test_residual_intervals.py`: 3 pass. `.venv/bin/python src/residual_intervals.py`: completed 25,380 interval forecasts / 6,345 matched cases per configuration; minimum 704 calibration errors. Original predictions unchanged. All metrics, per-state/year counts, protocols and run hashes saved.
- Finding: history-only Chronos day-1 nominal 90% residual-interval coverage is 89.74% across all days and 77.25% on fixed event windows. This is event undercoverage in a simple retrospective baseline, not proof about native quantiles. No calibration window/quantile/method retuned on these outcomes. All configurations, leads, widths, interval scores and pinball metrics retained.
- `.venv/bin/python src/audit_new_experiments.py`: passed labels, Delhi generic/regional identity, event metrics, protected hashes, quantile ordering, pre-origin residual boundaries, interval scores; independently reconstructed 144 first/event-origin residual quantiles. Reports in both result directories.
- Independently checked selected-state table against raw `State: EnergyMet` fields and GWh metadata, unique/ordered 5,048 source dates, missingness and coverage by year. Each full state series has 112 missing entries; no nonpositive recorded entries. Repeated values are only diagnostic counts, not proof of filling. Files: `source_audit.json`, `source_year_coverage.csv` in the controls directory.
- Saved completed `REPORT.md`, all-arm tables and scientific PNG figures in both experiment directories. Plotting succeeded with a temporary writable cache after read-only home warnings; future plotting can use `MPLCONFIGDIR=/tmp/tsfm-mpl XDG_CACHE_HOME=/tmp/tsfm-cache`.
- Official model README snapshots confirm TimesFM 3.0 future-covariate support and separate noncommercial downloaded-weight terms. New read requests to arxiv.org, huggingface.co model metadata, and robbieandrew.github.io were denied by proxy HTTP 403; saved evidence in `results/research_review_20261030/network_checks.json`. No network settings changed; no contacts, paid services or publishing used.
- Original PDF survey inspected as background, not verified experimental evidence. Created `CURRENT_RESEARCH_STATUS.md` with evidence/gap matrix, ordered next experiments, reproduction commands and external requirements. Handoff updated again at this substantial checkpoint.
- Final combined test command: `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLCONFIGDIR=/tmp/tsfm-mpl XDG_CACHE_HOME=/tmp/tsfm-cache .venv/bin/python -m unittest discover -s src -p 'test_*.py' -v` (19 tests; see final log). Independent audits and hashes verified after run completion. New continuation manifest preserves original manifests and includes intentional handoff/work-log edits.
- Next offline action: separately register stronger local baseline histories and annual/monthly refit comparison; then region/event transfer. External work needs allowed primary-paper/source/model hosts, actual weights, rights/vintage evidence and regional/human review. Fresh confirmation and manuscript submission remain open. No training process remains running.

## 2026-10-30 — Full GitHub checkpoint preparation

User authorized pushing completed tasks to GitHub and explicitly requested everything. Read-only `git ls-remote origin` confirmed no remote refs before initialization. Copied all 228 project checkpoint files (127,449,489 bytes before sync metadata) into `/workspace/tsaf_project`, preserving source/results/evidence bytes; excluded `.venv` and Python caches. Largest file is 21,558,084 bytes. No sensitive credential-name files found. `python src/verify_continuation.py` passed all 227 recorded files in the Git checkout before documentation changes. Added `.gitignore` for runtimes/caches/credentials and recorded the ongoing completed-task push preference in AGENTS.md. Source attribution/reuse notices are retained; no new data licence claimed. Next operation: normal initial commit to `main`, push, and verify remote SHA. No remote operation completed at this preparation checkpoint.

## 2026-10-30 — Full GitHub push verified

Initial full-project commit `eb6e9b0b9cc8c4dcc0778cc82d3af65b1dd8d223` was pushed normally to `https://github.com/Binay-verma/tsaf_project`, branch `main`. `git ls-remote origin refs/heads/main` exactly matched local HEAD. The push includes code, complete data snapshots, prediction rows, result reports, evidence PDFs, original survey and protocols; only local runtimes/caches/credentials were excluded. No data ownership/reuse licence was invented. Repository currently tracks 230 files. Follow-up metadata commit records this completed push, refreshes the GitHub checksum manifest and lets `src/verify_continuation.py` default to that current manifest; the earlier continuation/transfer manifests remain historical evidence. Future completed tasks should be committed/pushed normally, with remote SHA verification. Use `/workspace/tsaf_project` as the active Git work directory.

## 2026-10-30 — Phase two: richer baselines, refits, transfer, model audit, prospective freeze

- Restored Git checkout at 0b62ed1; `python src/verify_continuation.py` passed 229 recorded files before modifications. New environment network policy unrestricted/enforced. Created `.venv` (Python3.12, system numerical packages) and installed pinned holidays0.107/statsmodels0.15.0/LightGBM4.7.0. No published environment configuration changed.
- Saved `strong_refit_v1` and `regional_transfer_v1` protocols before new outcomes. `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python src/robust_baselines.py`: 891 selection fits / 162 chosen configs / 1,998 deployment fits / 107,244 forecasts, about288 seconds, no failures. Exact matched historical Chronos cases8,937/configuration. Pre-year hyperparameters frozen across annual/monthly schedules. Rich histories improve baseline coverage; monthly updates do not uniformly improve event errors. Full logs/protocol/forecasts/metrics/REPORT.md saved separately.
- `.venv/bin/python src/regional_transfer.py`: 162 fits / 53,622 predictions, fixed alpha10, three arms. Leave-region-out excludes target regression/scaler rows, but permits target historical context/normalization. Generally negative transfer; pooled-all differs from unseen-region transfer. No future-year pooling.
- TimesFM3 audit: code e51928e27119cb17bebc005be2696b75e0a9e688, weights43046b85ec22d584a13f8098c2ed39c889e129c2; actual SHA a7592b0a8432baee54483254e5647856911ce69e09d09a9bb65904b2d98f17da matches first upload2026-08-24. Installed40 Python files match pinned source. CPUtorch2.15.0+cpu, timesfm3.0.2, HFhub2.4.0, safetensors0.8.0. Weights/code installation under /workspace/model-cache and /workspace/model-code, excluded from project Git. Terms allow noncommercial academic research, restrict model redistribution.
- `.venv/bin/python src/timesfm_fixture.py`:18 predeclared API tasks (3states x2origins x3modes),252 forecast days,2268 native quantiles, no crossing. Future-covariate API and future-target perturbation check pass. This is a fixture, not full second-model/festival replication or final confirmation.
- `.venv/bin/python src/audit_phase2.py`: persisted source labels, scales, exact cases, metrics, selection minima/purge, refit cutoffs, transfer source identities and TimesFM first/current weight identity pass. Combined `python -m unittest discover -s src -p 'test_*.py' -v`:25 tests pass. Reports generated with `MPLCONFIGDIR=/tmp/tsfm-mpl XDG_CACHE_HOME=/tmp/tsfm-cache .venv/bin/python src/write_phase2_reports.py`.
- Recorded prospective protocol before new predictions, then `.venv/bin/python src/freeze_prospective.py`:252 frozen predictions,216 eligible future-target predictions (Oct31-Nov11), six configs,3states, source data throughOct28 only.462 pre-2026 selection fits and84 Oct1 deployment fits; familiar leads reproduce prior baseline parameter selections. No future outcomes fetched. Saved issue timestamp/hashes, native TimesFM quantiles and independent eligibility/selection/cutoff audit. Oct29/30 excluded from prospective scoring. This is one lagged-context forecast episode, not independent-source or broad confirmatory evidence.
- Live primary calendar paper/model/source pages now accessible; retrieved source metadata and close-work evidence. Source repository identification corrected from /india (404) to robbieandrew/robbieandrew.github.io; API licence null and no root licence found, so reuse remains unresolved. New detailed literature/rights report and manuscript still to be completed.
- Handoff updated at substantial checkpoint. All original data/extended results preserved. Next: push completed checkpoint, finish manuscript evidence/gates, then full multi-model matched controls and later prospective scoring with audited new actuals. No future score or journal-readiness claim.
