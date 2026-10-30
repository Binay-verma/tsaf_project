# Current gate experiments and reproducibility

Use the existing `/workspace/tsaf_project` checkout. Do not restart from the stale sibling or create a worktree merely for a cloud task. Current scripts expect Python3.12. No application server is required.

## Installed model environment

The working `.venv` installs the CPU torch version and pinned Google code described in `PHASE2_REPRODUCTION.md`, plus chronos-forecasting2.3.2 and transformers5.22.0. `requirements-controls.txt` records this combined environment. Install CPU torch with its CPU index first; preserve TLS and package verification. Actual package versions/weights are recorded per run. An aggregate requirements-file install on another host is not already tested by writing that file.

TimesFM weights remain outside Git under the noncommercial research terms. Chronos actual downloaded bytes also remain outside Git and match SHA-256 `ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42` at the recorded revision. Locations and hashes are in the model identity/download evidence. Do not assume caches survive onto another host; download exact revisions and verify expected hashes before inference.

## Fixed protocols and guards

`foundation_controls.py --model chronos2` / `--model timesfm3` implements the nine predeclared controls in `results/mechanism_controls_v1`. Each family covers150 identical cases per arm; completed/interrupted runs are protected from overwrite. Changed source/model/code/runtime or a new run requires a separately named protocol/output directory and explicit OUT update. Do not bypass guards or replace old predictions.

`stable_tree_refit.py --out results/stable_tree_refit_v2` is the separate float32 tree contract. The completed run's final metadata-path failure and repair are documented; rerunning this exact completed folder is intentionally blocked. The current wrapper resolves output paths for future runs. Version1 and frozen prospective forecasts remain unchanged.

The clean review environment is `/workspace/tsfm-clean-review`, created WITHOUT `--system-site-packages` and installed using `requirements.txt`. It passes32 tests and saved-result audits. The scalar review imports no application feature/model helpers. Version1 numerical discrepancies remain recorded; the float32 check is bounded to twelve forecasts/three chosen configurations. This is not independent human scientific approval or a full pretrained clean-room rerun.

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python src/audit_foundation_controls.py --model chronos2
OPENBLAS_NUM_THREADS=1 .venv/bin/python src/audit_foundation_controls.py --model timesfm3
OPENBLAS_NUM_THREADS=1 .venv/bin/python src/audit_stable_tree.py
.venv/bin/python src/restore_vintage_cache.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python src/audit_vintage_sensitivity.py
OPENBLAS_NUM_THREADS=1 /workspace/tsfm-clean-review/bin/python src/review_reproduction.py --experiment stable_tree_refit_v2 --contract float32
python src/verify_continuation.py
```

The snapshot restorer only fetches the recorded immutable Git/archive historical revisions and verifies their expected payload hashes. It never downloads the live/latest series or future prospective labels. Archived compressed transport and decoded CSV hashes are distinguished. Raw copies stay outside Git; URLs, provider digests, input hashes and revision inventories remain in the project. `vintage_sensitivity.py` uses those restored snapshots and the separate pinned models to reproduce the two-date retrospective availability experiment in a NEW versioned directory; do not overwrite the completed one.

## Human and future gates

Review documents and rights request are in `review/`; both remain unsent/unapproved pending a reviewer and authorized contact channel. Do not fabricate sign-off. Annual calendar evidence and the28-anchor worksheet do not certify final amendments.

Future collection/scoring is registered in GitHub, not a process left running in this cloud machine. The successful pre-period manual dry run is recorded in `results/provenance_review_v1/workflow_dry_run_status.json`. Actual future outcomes/scoring remain unrun; the workflow is date/completeness/immutability gated and first-snapshot results still need human interpretation. See `results/prospective_20261030_v1/AUTOMATION.md`.

## Current sharing/outreach update

The user reports sending the permission request manually; no assistant email should be sent. Professional address was verified from the official CICERO profile. Public/private repository choice is pending after the user clarified college-only use. New artifacts are held locally; the registered/tested future workflow is paused, not currently active. Resume pushes and re-enable it only after the sharing choice is confirmed.
