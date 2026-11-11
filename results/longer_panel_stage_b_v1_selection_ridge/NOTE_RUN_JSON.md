# Note: run.json not written (11 November 2026)

Attempt 1 stopped at import (lightgbm missing after an environment reset; log kept as
`failed_attempt_1_import_error.log`; nothing else was written). Packages were then pinned to the Stage A versions
(numpy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0, lightgbm 4.7.0) and the selection was run once.

That run completed selection, deployment, predictions, metrics and `selected.csv`, and passed the script's
`protected_before.json` integrity assertion. It then stopped while writing `run.json`, because `--out` was given as a
relative path and the script computes `relative_to(ROOT)` on it. No result is affected. All 16 protected input hashes
were re-checked afterwards and match.
