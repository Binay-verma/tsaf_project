# Reproduction and review packet v6 — for an external researcher

Author/requester: Binay Verma. Prepared 31 October 2026 with an AI assistant. **No independent human review has occurred.** The author, the professor-as-supervisor and AI sessions cannot fill the reviewer fields below on someone else's behalf.

This packet supersedes `review/INDEPENDENT_REVIEW_UPDATE_20261031.md` for the current checkpoint, which refers to an older v3 draft. Earlier packets are kept unchanged.

## What to review

- Paper: `manuscript/integrated_review_v5/MANUSCRIPT.md` and its PDF, plus the supplement CSVs in `manuscript/integrated_review_v5/supplement/`.
- Claim ledger and proposed revisions: `review/journal_seven_tasks_20261031_v1/SEVEN_TASK_LEDGER.md`, section 4.
- Cluster-level dependence tables: `review/journal_seven_tasks_20261031_v1/B_*.csv`, `C_*.csv`, `D_*.csv`.

## Reproduction tiers (expected results stated so that a mismatch is visible)

| Tier | Commands (repository root, Python 3.12) | Expected | Previously observed |
| --- | --- | --- | --- |
| 0 Integrity | `python src/verify_continuation.py` | `PASS: 3177 continuation files verified` at `cb03c72`. Later commits add files outside the manifest | PASS (Colab; this session) |
| 1 Tests | `python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest && .venv/bin/python -m pytest src -q` | 104 passed | 104 passed: earlier managed machine (working and isolated environments) and a new 3.12.13 environment on 31 Oct (SciPy 1.18.1) |
| 2 Tables from stored forecasts | `python review/journal_seven_tasks_20261031_v1/descriptive_reanalysis.py` | Reconstruction max abs diff ≤ 1e-12 against `metrics_balanced.csv`; outputs identical to committed CSVs | 2.2e-16 |
| 3 Local model rerun (NYC) | See `MTA_HOLIDAY_REPLICATION_BRIEF.md` / `review/clean_mta_v1` | 4,032 local forecasts byte-identical; 72 validation MAEs identical | Reproduced earlier on the same managed machine |
| 4 Foundation inference | `requirements-foundation.txt`; CPU torch per `PHASE2_REPRODUCTION.md`; weights by the hashes in `results/second_model_audit_v1/` and `results/mechanism_controls_v1/` | Point forecasts within a stated tolerance of stored files; native quantile crossings unchanged | Only internal API smoke checks (48 input blocks). No independent rerun |

Known discrepancies that must not be reported as passes: the earlier float64-tree reproduction failure; 15 of 45 Delhi lead-1 near-zero feature entries differ after float32 conversion (forecasts agree within 7.6e-12 GWh); SciPy 1.18.1 vs 1.17.0 drift.

## Questions for the reviewer

1. **Contribution.** Ziel (2018) compared single pooled, grouped and individual holiday dummies for load forecasting. Is extending that question to TSFM covariate channels, with matched zero/placebo controls, a sufficient contribution? Or is it a re-application?
2. **Instability as the finding.** The typed-versus-pooled ordering changes sign between 2024 and 2025 in 20 of 36 India cells and reverses for TimesFM-3 between India and NYC. Is "the preferred representation is unstable" a defensible primary message given 10 family-year clusters? Is the framing appropriate?
3. **Statistical unit.** Is reporting signs and ranges per family-year cluster, without p-values, adequate? Is there a dependence-respecting analysis you would require?
4. **Data and calendar.** Check observation-day versus report-day alignment of the GRID-INDIA-derived series against primary daily PSP reports. Check the Karnataka 2025 correction and the Maharashtra 2022 evidence gap.
5. **Data sharing.** `data/external/POSOCO_data.csv` (curator compilation; no licence found) is in the public repository. Advise on an appropriate data-availability statement.
6. **Leakage and availability.** Inspect the purge and context rules (`EXPERIMENT_INTEGRITY.md`) and the 7-day NYC observation buffer.
7. **Comparators.** Are the daily adaptations of Kreusel et al. and the fixed response profiles fairly described as *not* reproductions?
8. **Confirmation.** Do the frozen episode, the Chronos competitor and the unactivated 52-week rolling design (`results/rolling_confirmation_runtime_v1/`) constitute a credible confirmation plan?

## Reviewer response (to be completed only by the reviewer)

- Name, role, affiliation, expertise:
- Relationship to the author and any conflicts:
- Date, commit SHA reviewed, tiers attempted, environment:
- Results per tier (pass / fail / not attempted, with outputs):
- Answers to questions 1–8:
- Overall assessment and required changes:
- Signature/consent to be named:
