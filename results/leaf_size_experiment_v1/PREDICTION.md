# Leaf-size experiment: predictions written BEFORE any run (EXPLORATORY)

Written on 16 November 2026, after both registered new-states tests were analysed, before src/leaf_size_experiment_v1.py was run for the first time. Committed before the run so that the predictions cannot be adjusted to the results.

Design: both new-states tests (14 states, 2017-2025), lead 1, the registered LightGBM pipeline with all selected parameters kept except the minimum leaf size L (min_child_samples) in {1, 2, 3, 4, 5, 6, 8, 10, 20}; arms calendar, typed day flags, pooled day flag.

Mechanism being tested: a tree can split on a 0/1 flag only if the flag is set on at least L training rows (each side of a split needs L rows). LightGBM also merges value bins holding fewer than min_data_in_bin = 3 rows (its default), which may make a flag set on fewer than 3 rows unusable at any L.

## Predictions
- **P1 (exact, per fit):** in every fit where no typed flag is set on at least L training rows, the typed arm's predictions equal the calendar arm's exactly.
- **P1b (exact, per fit):** in every fit where no typed flag is set on at least 3 training rows, the typed arm equals the calendar arm at every L.
- **P2:** the share of fits in which the typed arm equals the calendar arm does not decrease as L grows.
- **P3:** balanced lead-1 typed minus pooled MASE is positive (pooled better) for every L from 2 to 20 in both tests.
- **P4:** the pooled arm differs from the calendar arm in most fits up to L = 6 (the pooled flag is set on more rows than any typed flag).

## Reproduction checks (must hold, otherwise the experiment is not comparable)
- At L = 2, the typed and pooled lead-1 predictions equal the registered leaf-2 LightGBM predictions of both tests.
- With each fit's selected L, they equal the registered Stable LightGBM lead-1 predictions.
