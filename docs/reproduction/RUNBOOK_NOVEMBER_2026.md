# Runbook: dated steps in November 2026

These steps can only be run by the author, at or after the stated times, in Google Colab (the data source is reachable from Colab). Never edit a frozen forecast file. Commit and push new outputs only.

## Step 1 — on or after 12 November 2026, 05:30 IST (00:00 UTC): score the frozen episodes

New Colab notebook, one cell at a time:

```bash
!git clone https://github.com/Binay-verma/tsaf_project.git /content/tsaf_project
%cd /content/tsaf_project
!pip -q install -r requirements.txt
!python src/collect_prospective_actuals.py
```

- If it prints **PENDING**, the first complete actual vintage is not yet available. Stop, and rerun the same cell later (for example the next day). Do not edit anything.
- When it completes, run:

```bash
!python src/score_interval_annex.py
!python src/score_chronos_competitor.py
!git status --short
```

`git status` should list only new scoring directories. Commit and push them under your RVU identity:

```bash
!git config user.name "Binay Verma"
!git config user.email "binayvermabtech24@rvu.edu.in"
!git add -A && git commit -m "Score frozen prospective episodes with the first complete actual vintage"
```

Push with a personal access token (never paste the token into a file or a commit).

## Step 2 — after 16 November 2026, 09:59 UTC (15:29 IST): record the first rolling window as a miss

The rolling study's prerequisites (source rights and observation-day evidence, human-verified 2024–2026 calendars) are not met, so window 0 cannot be issued. The registered rule records the miss; it never produces hindsight forecasts.

```bash
%cd /content/tsaf_project
!git pull --ff-only
!python src/rolling_execution_v2_timing.py miss --number 0
!git add -A && git commit -m "Record rolling window 0 as a registered miss"
```

The command refuses to run before the window has closed. Repeat for later windows only after each has closed and only while the prerequisites remain unmet.

## What not to do

- Do not run any scorer before 12 November 05:30 IST.
- Do not replace PENDING with a guess, and do not score imputed labels.
- Do not issue a rolling forecast unless every prerequisite is factually met and documented.
