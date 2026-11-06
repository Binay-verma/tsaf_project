# Runbook: dated steps in November 2026

These steps can only be run by the author, at or after the stated times, in Google Colab (the data source is reachable from Colab). Never edit a frozen forecast file. Commit and push only the new output folders named below.

## Setup (at the start of every new Colab session)

```bash
!git clone https://github.com/Binay-verma/tsaf_project.git /content/tsaf_project
%cd /content/tsaf_project
!pip -q install -r requirements.txt
!git config user.name "Binay Verma"
!git config user.email "binayvermabtech24@rvu.edu.in"
```

If the folder already exists in the same session, use `%cd /content/tsaf_project` and `!git pull --ff-only` instead of cloning.

## Step 1 — on or after 12 November 2026, 05:30 IST (00:00 UTC): score the frozen episodes

```bash
!python src/collect_prospective_actuals.py
```

- If it prints **PENDING**, the first complete actual vintage is not yet available. Stop, and rerun the same cell later (for example the next day). Do not edit anything.
- When it completes, run:

```bash
!python src/score_interval_annex.py
!python src/score_chronos_competitor.py
!git status --short
```

`git status` should list only these new folders: `results/prospective_20261030_scoring_v1/`, `results/prospective_interval_20261030_scoring_v1/` and `results/prospective_chronos_20261031_scoring_v1/`. If anything else appears, stop and check before committing.

```bash
!git add results/prospective_20261030_scoring_v1 results/prospective_interval_20261030_scoring_v1 results/prospective_chronos_20261031_scoring_v1
!git commit -m "Score frozen prospective episodes with the first complete actual vintage"
```

Push with a GitHub personal access token entered at the prompt (never write the token into a file, a cell you save, or a commit):

```python
from getpass import getpass
token = getpass("GitHub token: ")
!git push https://Binay-verma:{token}@github.com/Binay-verma/tsaf_project.git main
```

## Step 2 — after 16 November 2026, 09:59 UTC (15:29 IST): record rolling window 0 as a miss

The rolling study's prerequisites (source rights and observation-day evidence, human-verified 2024–2026 calendars) are not met, so window 0 cannot be issued. The registered rule records the miss; it never produces hindsight forecasts. Run the setup cell first, then:

```bash
!python src/rolling_execution_v2_timing.py miss --number 0
!git status --short
!git add results/rolling_confirmation_runtime_v1/issuances/00
!git commit -m "Record rolling window 0 as a registered miss"
```

Push as in Step 1. The command refuses to run before the window has closed. Repeat for later windows only after each has closed and only while the prerequisites remain unmet.

## What not to do

- Do not run any scorer before 12 November 05:30 IST.
- Do not replace PENDING with a guess, and do not score imputed labels.
- Do not issue a rolling forecast unless every prerequisite is factually met and documented.
