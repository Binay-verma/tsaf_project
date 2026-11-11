# Note: final integrity step did not run

The selection completed (selected.csv, predictions.csv, metrics written) but robust_baselines.py stopped at its last step because this new folder had no `protected_before.json` (that file was created by hand for the original strong_refit_v1 run and is not produced by the script). As a result `run.json` was not written.

Equivalent check recorded 11 November 2026 after the run: all registered Stage A input hashes still match (True); `git status` lists no changed file outside the selection folders (0 other entries). For the tree selection a `protected_before.json` snapshot of the registered inputs was written before that run started.
