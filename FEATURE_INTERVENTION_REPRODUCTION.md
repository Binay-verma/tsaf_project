# Explicit festival-feature intervention

This continues the existing project. Original source data, historical result directories, college decks and prospective forecasts remain unchanged. New public uploads are held under the current college-only sharing instruction. Use Python3.12and the existing pinned environment; no new scientific dependencies or online model downloads are required here.

## What is different from the previous benchmark?

The previous five-festival study measured errors during holiday windows, mostly using history and ordinary weekday/Fourier inputs. This intervention supplies explicit family-specific festival-day or window features. Its question is whether those fixed features improve matched predictions relative to ordinary calendar and same-size zero/placebo controls. It does not establish that family identities outperform a pooled event flag, invent a new encoding/architecture, or provide causal identification.

All historical outcomes have been inspected. Protocols were recorded before their new intervention outputs, not externally preregistered or presented as clean final tests.

## Frozen date ledger and cases

`results/festival_features_v1/anchors_2022_2025.csv` contains58anchors/48family-state-year groups. Karnataka2023English notification page6was visually checked; the newly downloaded government-hosted Maharashtra2023PDF and extracted English table are retained with hashes. In particular, Karnataka's Ganesh date is18September2023, Maharashtra's is19September, and Maharashtra's Holi holiday is7March2023. No library date silently substitutes for those annual-as-issued dates.

This ledger is bounded to2022–2025, not a full amended or statewide-activity calendar. Every used training/inference event-feature date is checked against that span. Original pre-year hyperparameters were selected without the added festival identities; they are reused for every new arm. This avoids needing unsupported event-feature dates in an earlier hyperparameter-fitting block. Raw historical target lags may extend earlier; that is distinct from using unverified event dates.

- Primary:72anchor targets,24state/festival/year groups, leads1/7/14, identical for all six model variants.
- Secondary:528unchanged window cases for the four classical/ML variants. Foundation intervention claims are restricted to the primary anchor cohort.
- Diwali preserves its legacy national/main plus subsidiary subset; Maharashtra's generic main target is not relabelled as its state Lakshmi Pujan date. Other named Diwali-office holidays are not silently added.

## Arms and budgets

Six common arms: calendar, zero5, day5, window5, placebo_day5, placebo_window5. Family channels are structurally zero outside their documented state scope. Day flags mark any declared anchor; windows use the union of+/-3days. Placebos preserve weekday with one seeded28–42day shift per family/state/year and exclude overlaps with all five registered true-family windows. One seed is not a randomisation distribution.

Ridge/stable LightGBM additionally evaluate35relative-day,35zero and35placebo channels. Models reuse the original state/year/lead ordinary-calendar parameters across arms, monthly fits and original arithmetic contracts. The second tree regime overrides only min_child_samples=2for all common arms. It is an explicit sparse-event capacity sensitivity with its own calendar baseline, not a winning setting selected by evaluated errors. Training support counts are retained; one or two past events can overfit.

SARIMAX keeps its fixed order, annual pre-year fit, past-only state updates and predefined training-convergence retries. Chronos and TimesFM use fresh pinned local-weight inference,730-day contexts,14-day horizons, batch4,2threads and seed42. All actual input matrices are hashed; future-target perturbations and solo/batch checks are retained.

## Secondary non-event check

`results/festival_feature_spillover_v2` fixes72weekday/season-matched control targets before their model outputs. Dates use the first eligible+28,-28,+35,-35,+42,-42day shift, excluding+/-3days of every annual/registered holiday anchor. The model specifications and true-feature ledger are unchanged; only calendar/day5/window5arms are run. Every model uses the same cases. A family label denotes the event paired with a control date, not a festival occurring on that date.

The wrapper explicitly records output/arm overrides. Its regression baseline reproduction uses the original **full-daily** saved files, because the parent window-only table does not cover ordinary-day targets. This is a bounded spillover check, not exhaustive all-day foundation evaluation, exchangeable sampling or a causal event/control effect.

An initial secondary preparation prototype failed before protocol write because Pathwas not imported. It also exposed the need for a full-daily baseline reference. Its date files/original runner and reason are retained in festival_feature_spillover_v1; no models ran there. The corrected version2was frozen before secondary model outputs. The primary preparation's60-versus58literal count was likewise corrected before protocol creation; no dates or evaluated settings were changed in response to results.

## Reproduction and audits

Completed/interrupted workers refuse overwrite. Preparation also refuses an existing protocol. Do not rerun these commands over the finished directories. A fresh reproduction requires explicitly versioned directories/source hashes and the same pinned models/data. Existing predictions can be audited without refitting:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -q
.venv/bin/python src/audit_festival_feature_fits.py
.venv/bin/python src/audit_festival_features.py
.venv/bin/python src/audit_festival_feature_inputs.py
.venv/bin/python src/audit_festival_feature_fits.py --out results/festival_feature_spillover_v2
.venv/bin/python src/audit_festival_features.py --out results/festival_feature_spillover_v2
.venv/bin/python src/audit_festival_feature_inputs.py --out results/festival_feature_spillover_v2
```

The37-test suite includes date scope, relative-day orientation, equal dimensions, disjoint placebos, future-target invariance and direct-label purging. A separate stdlib audit reconstructs labels, scales and state/year/family aggregation. A separate date/NumPy implementation reconstructs persisted foundation target/covariate bytes without importing experimental feature/model helpers. Fitting audits verify identical label hashes across arms, fixed budgets, cutoffs and support counts. These are internal software checks, not independent human scientific review, source permission or exhaustive no-leakage guarantees.

The original MASE denominator is the preceding730-calendar-day recorded weekly-difference reference, fixed within year. Primary summaries weight states within year, years within festival and then festivals equally. MAE remains per state in GWh. Paired percentages are computed within state/year; undefined zero denominators stay undefined. Never convert MASE into an accuracy percentage or select the best arm from evaluated errors for an untouched test. Native quantile crossings remain unmodified.

Current completion is established by worker run.json, combined run.json and audit outputs, not this command list. No computation is claimed to persist after the session. Source rights/amendment/human-review gates, historical overlap and later prospective outcomes remain open. See MISSED_STEPS_AUDIT.md, PROTOCOL_INDEX.md and the updated handoff.
