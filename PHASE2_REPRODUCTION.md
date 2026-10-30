# Phase-two reproduction and future scoring

Use Python3.12 and the existing checkout; cloud tasks are already isolated, so do not create a worktree merely for setup.

```bash
cd /workspace/tsaf_project
python3.12 -m venv --system-site-packages .venv
.venv/bin/python -m pip install "torch==2.15.0+cpu" --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements-phase2.txt
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s src -p 'test_*.py' -v
.venv/bin/python src/audit_phase2.py
python src/verify_continuation.py
```

The CPU torch installation, pinned Google source installation and packages were exercised in this cloud machine. The exact requirements-file aggregate installation has not been independently rerun in a second clean environment. `--system-site-packages` deliberately reuses the numerical stack; recorded package versions must still match. An isolated clean-room rerun remains a separate submission gate. TLS/package integrity checks stay enabled.

No services need starting. Existing numerical reports can be read without installing model weights. Local `.venv`, model installation and weight caches are excluded from GitHub. TimesFM3's noncommercial academic-research licence applies separately from source code licensing; do not redistribute weights or vendor model code under an invented project licence.

The audited TimesFM source is Google revision `e51928e27119cb17bebc005be2696b75e0a9e688` (3.0.2). Weights are HF revision `43046b85ec22d584a13f8098c2ed39c889e129c2`; verify SHA-256 `a7592b0a8432baee54483254e5647856911ce69e09d09a9bb65904b2d98f17da` before use. Use inherited proxy/CA trust. `results/second_model_audit_v1/weight_download.json` records the current local path outside the checkout. For another machine, download the exact revision outside the checkout and create a new audited run with the updated cache location. Do not assume host paths transfer.

Completed forecasting runners refuse to overwrite results. For changed protocols, code, models, source or runtime identity, create new versioned output directories and update their configuration/code paths explicitly. The baseline runner has `--out`; transfer/model/fixture runners currently use explicit `OUT` paths. Do not delete old outputs or bypass a guard to make a rerun succeed.

## Prospective episode: frozen, not scored

The original forecasts and protocol were pushed in commit `cabd5982e1948652b9841d6c31a2380f6f314198` on30October2026 before eligible targets31October–11November. Their source context ends28October. They must not be regenerated to replace the recorded forecast artifact. Their file hash and timestamp are in `results/prospective_20261030_v1/freeze.json`.

After the target period has ended (12November2026 UTC or later), acquire a genuinely later actuals snapshot, retain first-retrieval time/source URL/raw checksum and review units, revisions, missingness and reporting dates. Extract recorded GWh values into `date,Karnataka,Delhi,Maharashtra` without imputation or silent source mixing. Then use:

```bash
.venv/bin/python src/score_frozen.py \
  --actuals /path/to/audited-later-state-energy.csv \
  --source-url 'ACTUAL_PUBLIC_SOURCE_URL' \
  --retrieved-utc 'ACTUAL_TIME_WITH_TIMEZONE' \
  --out results/prospective_20261030_scoring_v1
```

The placeholders must be replaced with actual provenance, not invented timestamps/URLs. The command blocks scoring before the final eligible target date has ended, checks forecast immutability, excludes issue-day/past targets and rejects missing/nonpositive labels. Tests exercise the gate with synthetic in-memory data only; no real future labels or prospective scores exist now. It reports six fixed configurations and native TimesFM quantile scores; do not tune or select a replacement method on this episode and call it confirmatory. Source/vintage authentication and independent review still require evidence beyond this command.

No job will automatically fetch future outcomes or remain running after the session. Keep the handoff/current status/work log and GitHub checkpoint current when later evidence arrives.
