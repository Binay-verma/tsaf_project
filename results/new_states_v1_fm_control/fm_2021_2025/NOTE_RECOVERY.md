# Recovery of the fm_2021_2025 control run (15 November 2026)

The run finished on Kaggle: 2598 of 2598 tasks in each of the three arms, 8676 prediction rows, completed 12:11:50 UTC. Its final `git pull --rebase` stopped on a conflict in `results/new_states_v1_fm_control/weights_identity.json`, because the fm_2017_2020 run (commit 5867b88) had already pushed that file. The two copies give the same weight hashes and package versions. They differ only in `verified_utc` (05:18:03 against 05:19:50), as shown in the run log. The session then closed, so the author downloaded the output files and they were committed by hand.

Checks before committing:
- `timesfm/predictions.csv`: sha256 bcfad7d3…ba937, equal to `predictions_sha256` in `timesfm/run.json`. `checkpoint.csv` is byte-identical to it.
- `protocol.json`: sha256 2b175812…b14c, equal to the registered results/new_states_v1/fm_2021_2025/protocol.json and to `protocol_sha256` in run.json.
- `window_cases.csv` and `primary_cases.csv`: sha256 0f9df18e…555c, equal to the registered `design_hashes`.
- Weights: `weight_sha256` in run.json (a7592b0a…f17da) equals the TimesFM-3 hash in the committed weights_identity.json.

File names were restored from the Kaggle output paths. Contents are unchanged.
