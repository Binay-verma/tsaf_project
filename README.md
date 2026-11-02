# TSFM India: festival covariates in foundation and local forecasting models

Binay Verma — B.Tech CSE (Data Science), RV University. Research in progress.

This repository studies how festival information should be given to forecasting models for **daily electricity supplied (GWh)** in Delhi, Karnataka and Maharashtra. Two pretrained time-series foundation models (Chronos-2, TimesFM-3) and four local models (Ridge, SARIMAX, LightGBM and a leaf-2 tree variant) are compared on the same cases with matched input designs: calendar only, typed festival flags (one per festival), pooled flags (one shared flag), ±3-day windows, zero channels and fake-date placebos.

**Main findings so far (historical data, exploratory):**

- Festival day flags usually lower next-day error versus calendar-only inputs.
- The better encoding (typed vs pooled) is **not stable**: it flips between 2024 and 2025 in 19 of 36 model/representation/lead comparisons and differs between India and a separate NYC holiday check in 11 of 36.
- A document-level calendar check corrected one festival date (Karnataka 2025 Vijayadashami: 1 Oct, not 2 Oct).
- Native 80% prediction intervals under-cover festival periods.

Forecasts for 31 Oct–11 Nov 2026 were frozen before outcomes and are scored from 12 Nov 2026. A 52-week rolling confirmation study is registered but not yet activated.

## Start here

| Read | Where |
| --- | --- |
| Current paper draft (v6) | [manuscript/integrated_review_v6/](manuscript/integrated_review_v6/) |
| Full project report (Word/PDF) | [manuscript/project_report_v1/](manuscript/project_report_v1/) |
| Current status and next steps | [docs/status/CURRENT_RESEARCH_STATUS.md](docs/status/CURRENT_RESEARCH_STATUS.md), [docs/status/HANDOFF.md](docs/status/HANDOFF.md) |
| Seven-task journal ledger | [review/journal_seven_tasks_20261031_v1/SEVEN_TASK_LEDGER.md](review/journal_seven_tasks_20261031_v1/SEVEN_TASK_LEDGER.md) |
| Viva slides | [presentation/viva_update_v2/](presentation/viva_update_v2/) |
| Setup and reproduction | [docs/reproduction/ENVIRONMENT_SETUP.md](docs/reproduction/ENVIRONMENT_SETUP.md) |
| Project rules (integrity, frozen forecasts, data rights) | [docs/PROJECT_GUIDELINES.md](docs/PROJECT_GUIDELINES.md) |

## Repository structure

```
README.md                 this overview
requirements*.txt         pinned environments (core, foundation, phase 2, controls, multifestival)
environment.json          recorded foundation-model package versions
run_all.py, run_extended.py, setup_project.py   historical entry points
GITHUB_CHECKSUMS_20261030.json   integrity manifest used by src/verify_continuation.py

src/            all code: data, features, models, experiment engines, scorers, audits, tests (test_*.py)
data/           raw and external source snapshots (see data/external/RIGHTS_NOTICE.md)
evidence/       retained calendar documents and model/corpus evidence
results/        one folder per registered experiment: protocol, forecasts, metrics, audits (frozen records)
review/         claim audits, re-analyses, calendar reviews, reviewer packets
manuscript/     paper drafts (v1–v6), supplements, project report
presentation/   college and viva decks with their builders
docs/
  PROJECT_GUIDELINES.md     research-integrity and working rules
  status/                   current status, handoff, work log, roadmap, results summary, plan/progress
  results_briefs/           short summaries of each completed study
  methods/                  architecture, integrity rules, protocol index, model-comparison scope
  data_and_calendars/       data sources, calendar verification and audits, pretraining audit
  reproduction/             environment setup and per-study reproduction notes
  literature/               literature notes, references, original literature survey
archive/        superseded integrity manifests (historical records)
.github/        prospective-evaluation workflow (kept disabled)
```

Files inside `results/` are registered research records: their contents and paths are protected by hashes and first-commit checks, so they are never edited or moved.

## Quick start

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pytest   # Windows: .venv\Scripts\python.exe
.venv/bin/python -m pytest src -q                            # 121 tests, synthetic fixtures
python src/verify_continuation.py                            # file-integrity check (Linux/macOS/Colab)
```

Foundation-model reruns need `requirements-foundation.txt` and separately downloaded weights; see [docs/reproduction/ENVIRONMENT_SETUP.md](docs/reproduction/ENVIRONMENT_SETUP.md).

## Data and attribution

- Robbie Andrew, *Indian Energy and Emissions Data* (compiled from GRID-INDIA/POSOCO daily reports), snapshot of 29 Oct 2026. No licence found; reuse request pending — see [data/external/RIGHTS_NOTICE.md](data/external/RIGHTS_NOTICE.md).
- Hunt and Bloomfield (2025), Zenodo [10.5281/zenodo.14983362](https://doi.org/10.5281/zenodo.14983362), CC BY 4.0.
- SASEA (Coombes, Hunt and Bloomfield), Zenodo 10.5281/zenodo.17175212, CC BY 4.0.
- MTA NYC daily ridership (dataset sayj-mze2); NESO transmission demand (raw archives kept outside Git).

Model weights are not included. TimesFM-3 weights carry their own noncommercial terms.

## Status and limits

Historical outcomes were inspected, so all historical results are exploratory. Two event years and three related states limit generalisation. Independent human review, data-reuse permission and calendar amendment certification are outstanding. Earlier README content is kept in [docs/status/README_HISTORY.md](docs/status/README_HISTORY.md).
