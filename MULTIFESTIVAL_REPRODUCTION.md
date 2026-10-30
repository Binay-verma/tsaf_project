# Multi-festival continuation — 30 October 2026

Use the existing checkout and Python3.12 environment. These historical extensions are exploratory, not new test sets. All original/frozen predictions remain unchanged. Do not overwrite result directories or run preparation over completed experiments. Public uploads remain held under the current college-only sharing instruction.

## Frozen scope

2024–2025; five families and24state/year groups:

- Holi: Delhi and Maharashtra.
- Dussehra: Delhi, Karnataka and Maharashtra.
- Ganesh Chaturthi: Karnataka and Maharashtra.
- Ugadi/Gudi Padwa: Karnataka and Maharashtra, with local names retained.
- Diwali: three states, preserving the previous broad national/main-plus-regional union.

Thirty anchors yield528identical state/origin/lead cases, at individual leads1,7,14. Windows are fixed at+/-3days, not the full duration of every observance. The dates and state coverage were frozen before newly stratified errors. Annual-as-issued dates are not complete amendment certification or evidence of statewide closure. Coincident/nearby holidays are logged. Christmas is deferred because the saved origin schedule prevents complete next-day coverage; moon-sensitive Eid-specific inference is deferred pending dated amendment/observance evidence. Missing labels must be excluded for all configurations equally; missing forecasts fail rather than silently shrinking cohorts.

## Completed saved-forecast diagnostic

`src/multifestival_cached.py prepare` froze the protocol before `score`; nine existing daily configurations were rescored without fitting or introducing festival identities. Original predictions, source labels, pre-year weekly scales and original selection logs are reused explicitly, not claimed as new inference. Run/audit artifacts are under `results/multifestival_cached_v1/`.

The original score runner completed all scientific CSVs, then its `.to_markdown()` call failed because the optional `tabulate` package was absent. The failure is recorded; the executed code/protocol and forecast hashes are retained. `src/report_multifestival.py` renders without that optional dependency and reconstructs run metadata without changing predictions/metrics. Do not rerun scoring over the existing files. In a fresh versioned reproduction, install `tabulate==0.9.0` before using the original renderer, or use the recorded report-recovery path. The requirements file is an installation specification, not a claim that its full aggregate installation was clean-room tested here.

```bash
.venv/bin/python src/audit_multifestival.py
.venv/bin/python src/report_multifestival.py
```

## Missing-model extension

`src/multifestival_models.py prepare` freezes the exact same cases and six new configurations before their outcomes: SARIMAX history/calendar with annual fits and past-only state updates, additive weekly ETS with monthly fits, Chronos ordinary-calendar inputs, and TimesFM history/ordinary-calendar inputs. SARIMAX and ETS use fixed specifications, not outcome-selected grids. ETS uses `statsmodels.tsa.exponential_smoothing.ets.ETSModel`, not the separate seasonal state-space exponential-smoothing implementation. Recorded fitted initial states are kept at the same training start when smoothing through an origin; no parameters are optimised between monthly fits.

Workers have separate immutable checkpoints. Actual pinned local model/config bytes are checked before inference; no online latest model is downloaded. Every foundation input is checked against unseen-target perturbations and hashed. First-batch solo comparisons check batching behavior. Optimiser retries use training convergence only and remain in fit_attempts.json. Failed/interrupted workers are retained rather than overwritten. `audit_ets_recursion.py` also reconstructs the first origin per state/year with scalar ETS(A,N,A) innovation equations; these six deployments match to numerical precision. This is an internal implementation check, not an external review.

In a fresh versioned experiment only:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python src/multifestival_models.py classical
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 HF_HUB_OFFLINE=1 .venv/bin/python src/multifestival_models.py chronos
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 HF_HUB_OFFLINE=1 .venv/bin/python src/multifestival_models.py timesfm
```

After all workers finish, combine only complete identical cases; audit raw labels, scales and hierarchy of aggregation separately from deployment/provenance checks:

```bash
.venv/bin/python src/multifestival_models.py combine
.venv/bin/python src/audit_multifestival.py --out results/multifestival_models_v1
.venv/bin/python src/audit_multifestival_models.py
.venv/bin/python src/report_multifestival.py --out results/multifestival_models_v1
```

These ordinary-calendar configurations still do not encode additional Holi/Ganesh/Ugadi identities. A later festival-feature intervention needs its own training-year date ledger, protocol and past-only feature/parameter selection. Historical pretraining/proxy overlap, retrospective source availability, related states and only two event years remain limitations. Do not claim a universal or causal winner, external human review or completed future accuracy.
