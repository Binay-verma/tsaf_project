> **Current31October2026:** all registered historical lanes and separate audits are complete. Read the [corrected/cross-source result tables](COMPLETE_RESULTS_20261031.md), [current12-page paper](manuscript/integrated_review_v5/Integrated_Review_Binay_Verma.pdf), [editable paper](manuscript/integrated_review_v5/MANUSCRIPT.md) and [status](CURRENT_RESEARCH_STATUS.md) and [next steps](NEXT_RESEARCH_STEPS.md).104tests pass in working/isolated environments. Manual rolling-confirmation software is implemented and fixture/API checked, **not activated**; [future manual operations](results/rolling_confirmation_runtime_v1/MANUAL_OPERATIONS.md). New Chronos future forecasts/publicreceipt are frozen; no future accuracy exists. Reuse/day/calendar/human/untouched-confirmation gates remain open. Earlier checkpoints below are historical.

> Earlier uncertainty checkpoint: [past-only interval calibration](NATIVE_CALIBRATION_RESULTS_BRIEF.md), a [four-page review supplement](manuscript/calibration_update_v1/CALIBRATION_UPDATE.md), and a [separate prospective interval annex](results/prospective_interval_20261030_v1/README.md) are complete/issued and audited. Coverage gains incur width/score costs; future results remain pending. Original forecasts, integrated paper and decks are unchanged.53tests pass in both environments. See [reproduction](NATIVE_CALIBRATION_REPRODUCTION.md).

> Earlier journal checkpoint: pooled-versus-typed features, controlled family-label exclusion and a broader daily comparison of both pinned foundation models are complete and audited. Read the [pooled brief](POOLED_FEATURE_RESULTS_BRIEF.md), [transfer brief](LABEL_TRANSFER_RESULTS_BRIEF.md), [daily results](results/postweight_daily_v1/REPORT.md), [editable manuscript](manuscript/journal_draft_v1/MANUSCRIPT.md), and [author/professor review packet](review/AUTHOR_PROFESSOR_REVIEW_PACKET.md). Q1 is the author’s goal; current venue rank, source permission, independent review and untouched confirmation remain open. Earlier results/decks and future forecast blobs are preserved. Prospective automation remains paused.

> Earlier checkpoint: explicit festival-day/window features and controls are tested, with matched ordinary-day checks. See [results brief](FESTIVAL_FEATURE_RESULTS_BRIEF.md), [feature results](results/festival_features_v1/REPORT.md), [ordinary-day results](results/festival_feature_spillover_v2/REPORT.md), [gap audit](MISSED_STEPS_AUDIT.md), [reproduction](FEATURE_INTERVENTION_REPRODUCTION.md), and the [new college supplement](presentation/festival_feature_update_v1/README.md). Completed work was pushed to this existing public repository under the user's explicit instruction. Prospective automation remains paused; no source reuse grant or future score is implied.

> Earlier completed checkpoint: a five-festival matched comparison—15configurations,528identical cases each, including new SARIMAX/ETS and both foundation models. See [results](results/multifestival_models_v1/REPORT.md), [comparison scope](MODEL_COMPARISON_SCOPE.md), [reproduction](MULTIFESTIVAL_REPRODUCTION.md), and the [college results supplement](presentation/multifestival_update_v1/README.md).

> Current continuation (30 October 2026): richer baselines/refits, regression-region transfer, an audited TimesFM historical event comparison, and frozen prospective forecasts are complete. See [current status](CURRENT_RESEARCH_STATUS.md), [working manuscript](manuscript/DRAFT.md), and [reproduction](PHASE2_REPRODUCTION.md). Prospective scores and journal submission gates remain open. Older results below are preserved as historical context.

# Continuing in Codex

Read `CONTINUE_IN_CODEX.md`, then start with `CODEX_START_PROMPT.txt`. `AGENTS.md` and `CODEX_HANDOFF.md` preserve the research instructions and state; `WORK_LOG.md` carries future checkpoints. The original survey is included as `USER_LITERATURE_SURVEY.pdf`.

# Current status: expanded evaluation complete; journal research unfinished

Read **CURRENT_RESEARCH_STATUS.md** for current results and **VALIDATION_REPORT.md** for the original expanded checkpoint, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# Complete runnable project

Start with **START_HERE.md**. Run `python setup_project.py` and `python run_all.py` to execute checks, matched model comparisons, scoring and the HTML report. The completed scheduled-origin benchmark is under `results/benchmark_original_s28/`. The earlier pilot and data audits remain available below.

# TSFM India — reproducible first pilot

Start with **PLAN.md** for the full research plan and **PROGRESS.md** for completed work and next steps.

## Run locally

Python 3.12 was used. From this directory:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run_pilot.py
python src/check_results.py
```

The source data is included, so the baseline pipeline needs no data download or account.
Optional foundation-model smoke test (downloads model weights): install CPU PyTorch and `chronos-forecasting`, then run `python src/chronos_smoke.py`. This is a separate dependency set from the tested baseline requirements.

## Files

- `data/raw/`: unchanged source CSV and complete repository metadata.
- `data/clean_daily_energy_GWh.csv`: daily selected-state observations with invalid/conflicting entries missing.
- `data/exploratory_calendar.csv`: library-generated state holidays and Diwali windows; verification status explicit.
- `src/run_pilot.py`: data audit, causal input filling, baseline and feature-ablation development experiment.
- `src/check_results.py`: independent result checks.
- `src/chronos_smoke.py`: separate single-origin CPU smoke test with explicit success/failure record.
- `results/`: row-level predictions, metrics, coverage, audit, software versions and plot.

## Data dictionary

| Field | Meaning |
|---|---|
| date | Source daily reporting date; no UTC conversion or hour inferred |
| Karnataka / Delhi / Maharashtra | Electricity supplied during the day, MU = million kWh = GWh |
| actual | Observed target only; missing/conflicting labels excluded |
| prediction | Forecast for that date using information through the preceding date |
| training_mase_scale | Mean absolute 7-calendar-day difference over observed 2015–2021 training pairs |
| public_holiday | State calendar flag from the recorded holidays version |
| diwali_window | Union of ±3 calendar-day windows around library holidays with Diwali/Deepavali in their names |
| MAE_GWh | Mean absolute error in daily supplied energy |
| MASE | Absolute error divided by fixed training weekly seasonal-error scale |

## Attribution

Hunt, Kieran & Bloomfield, Hannah (2025). *Daily electricity demand data for Indian states (2014–2024)*, v1.0, Zenodo, https://doi.org/10.5281/zenodo.14983362. Licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . The authors scraped national grid records and supplied quality-controlled versions. This project uses the corrected daily energy-met file. Changes: three-state extraction, identical duplicate collapse, conflicting state/date masking, daily reindexing, separate causal input fills and derived features. The original file is unchanged and its repository MD5 is checked at runtime.

## Interpretation limits

The model comparison is developmental, not a final benchmark. Zero-shot model contamination is unknown. Historical source corrections could use retrospective information. Holiday-library dates need official regional validation. The single development year provides one Diwali occurrence per state; nearby days and states are not independent replications. No causal festival effect or publication novelty is established. Existing results are for one-day rolling forecasts, not seven-day fixed-origin forecasts.

## Expanded data search

Read DATA_SOURCES.md for actual coverage, reuse status, source dependence and the newer state snapshot. Run `python src/audit_sources.py` to reproduce its audit.
