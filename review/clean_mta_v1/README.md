# Complete isolated-environment MTA local reproduction

All 4,032 local forecasts from eight workers reproduce as byte-identical prediction CSVs. All 72 chronological validation fits reproduce exactly the original validation MAEs and chosen parameters; maximum prediction and validation-MAE differences are zero. The unchanged finalizer and separate local source/input/metric audit also pass in the clean environment. No original worker or forecast was overwritten.

The no-system-packages environment uses the same Python/model source/input copies and machine, with SciPy1.18.1 versus the original1.17.0 explicitly recorded. This is a complete local package-drift sensitivity, not independent human review, another geography or a clean foundation-model rerun. Fixed tolerances were registered before rerun outputs and were not widened. The earlier Indian near-zero feature discrepancy and float64 tree failures remain unchanged.

registration.json records source/package identities and tolerances; comparison.json contains all worker hashes/differences. Fresh selection, predictions, fit/update logs and separate-audit results are retained. The temporary execution root is /tmp/tsfm-clean-mta-v1. No model weights, future labels, source acquisition or task tuning were involved.
