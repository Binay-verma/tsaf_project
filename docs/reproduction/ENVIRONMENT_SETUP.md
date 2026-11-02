# Environment setup and reproduction

## Verify the checkout

From the repository root:

```bash
python src/verify_continuation.py
```

This checks every tracked file against the SHA-256 manifest `GITHUB_CHECKSUMS_20261030.json`; it uses the standard library only. It verifies file integrity, not scientific validity. On Windows, Git's line-ending conversion makes text files differ from the manifest, so run it on Linux/macOS or in Colab, or with `core.autocrlf=false`. Older manifests are kept under `archive/integrity_manifests_20261030/` as historical records; `src/verify_package.py` expects the 30 October package manifest at the root and is historical.

## Python environment

Use Python 3.12 in an isolated environment.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
```

Linux/macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pytest
```

Saved reports and results can be read without installing anything.

## Checks

```bash
python -m pytest src -q
```

Expected: 121 passed (synthetic fixtures; no network or model weights needed).

## Regenerate scoring/reports from included predictions

```bash
python src/summarize_extended.py
python src/write_validation_report.py
```

Historical report builders in `src/` write their outputs to the paths used when they were first run (the repository root). Their committed copies now live under `docs/`.

## Foundation-model reproduction (only when needed)

Inspect `requirements-foundation.txt` and `results/extended_validation/environment.json`. The recorded CPU torch wheel needs the PyTorch CPU index:

```bash
python -m pip install "torch==2.15.0+cpu" --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-foundation.txt
python src/cache_identity.py
```

Model weights need a separate download; no paid forecasting API is used. If pinned wheels are unavailable for a platform, record the limitation and use a separately named reproducibility run. Do not remove the cache guard or change package versions while claiming an identical rerun.

`python setup_project.py` is an earlier installer whose torch installation is not pinned. `python run_extended.py` reruns the expanded pipeline; `python run_all.py` is the older scheduled-origin study. A full rerun is not needed to read or check results.

## Keeping the record

Keep `docs/status/HANDOFF.md` and `docs/status/WORK_LOG.md` up to date at each substantive checkpoint, including failed attempts. Commit and push at safe checkpoints. Do not assume a process continues after a session ends.
