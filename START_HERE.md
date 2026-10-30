# Continuing in Codex

Read `CONTINUE_IN_CODEX.md`, then start with `CODEX_START_PROMPT.txt`. `AGENTS.md` and `CODEX_HANDOFF.md` preserve the research instructions and state; `WORK_LOG.md` carries future checkpoints. The original survey is included as `USER_LITERATURE_SURVEY.pdf`.

# Current status: expanded evaluation complete; journal research unfinished

Read **VALIDATION_REPORT.md** for the current results, **DEEP_RESEARCH.md** for the literature and publication assessment, **PRETRAINING_AUDIT.md** for overlap evidence, and **REGIONAL_CALENDAR_AUDIT.md** for the exact calendar-verification scope.

The expanded study contains 103,254 checked forecasts, daily origins across 2022–2026, four historical Diwali years, a twelve state-year annual calendar audit and a pre-2026-selected exploratory LightGBM baseline. Eleven unit tests pass. The festival encoding does not improve Chronos consistently. These are preliminary research findings, not a publication-ready new method. Full holiday-amendment certification and final independent confirmation remain incomplete.

Run `python setup_project.py`, then `python run_extended.py`. Inspect `results/extended_validation/report.html` or the Markdown report without rerunning. `run_all.py` reproduces the earlier scheduled-origin study only.

---

## Earlier checkpoint documentation (historical)

# Run the complete forecasting project

Use Python 3.12. Unzip this folder, open a terminal in it, and run:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Then:

```bash
python setup_project.py
python run_all.py
```

Open `results/benchmark_original_s28/report.html`. Saved results are already included; no rerun is required to inspect them. The first foundation-model run downloads model weights. No paid API or cloud account is used.

The default experiment evaluates a declared schedule every 28 days plus a pre-festival origin, across 2022 and 2023. This is a complete scheduled-origin experiment, not a full daily benchmark. It compares three states, three forecast horizons, ridge regression, SARIMAX, Chronos-2, last-value and seasonal-naive baselines. Modes A/B/C/D progressively add ordinary calendar inputs, public holidays and a seven-day window around the main Diwali date.

For a denser schedule, run `python run_all.py --stride 7`. This uses a different output directory and takes longer. For the separately audited newer data snapshot, use `--source latest`; this does not automatically establish its reuse licence or remove pretraining overlap. It still evaluates the frozen 2022/2023 protocol.

For baseline-only installation and execution:

```bash
python setup_project.py --baseline-only
python run_all.py --skip-chronos
```

Important: cached Chronos CSVs belong to the exact protocol in their output folder. Remove only the corresponding experiment output folder manually if intentionally changing model, feature or context settings. Keep source data and baseline pilot results. The benchmark checks protocol identity before reusing cached outputs.

## Project map

- `src/forecasting.py`: data loading, causal fills, known-calendar features, direct regression models.
- `src/benchmark.py`: matched forecast origins, state-updated SARIMAX, batched independent Chronos tasks and cached output.
- `src/test_forecasting.py`: future-target perturbation and date/window tests.
- `src/summarize.py`: independent validation, observed-only scoring, plots, descriptive paired intervals and HTML report.
- `run_all.py`: checks → experiment → summary.
- `DATA_SOURCES.md`: provenance, actual coverage and source limitations.
- `results/benchmark_original_s28/protocol.json`: frozen experiment definition.

## Research status

Software completeness and research validity are separate. Historical state holiday flags are only partially officially verified; unknown pretraining overlap remains. Each evaluation year has only one main Diwali occurrence, so per-festival results cannot establish general improvement. No new architecture, causal effect, leakage-free benchmark or publication novelty is claimed. The results are suitable for inspecting the implementation and planning a larger study.
