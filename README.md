# Continuing in Codex

Read `CONTINUE_IN_CODEX.md`, then start with `CODEX_START_PROMPT.txt`. `AGENTS.md` and `CODEX_HANDOFF.md` preserve the research instructions and state; `WORK_LOG.md` carries future checkpoints. The original survey is included as `USER_LITERATURE_SURVEY.pdf`.

# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

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
