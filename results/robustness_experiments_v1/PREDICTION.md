# Robustness experiments: predictions written BEFORE any run (EXPLORATORY)

Written on 16 November 2026, after both registered new-states tests were analysed and after an internal referee-style review, before src/robustness_experiments_v1.py was run. Committed before the first run. All quantities are lead-1, balanced as registered (state-family-year, then family-year clusters), typed minus pooled MASE; positive favours pooling. "Both tests" means the result is computed separately for results/new_states_v1 and _v2.

## Training window (event years 2021-2025; W = 730, 1460, 2190 days)
- **W1.** For LightGBM with leaf size 2, typed minus pooled decreases as W grows (typed flags gain training rows), in both tests.
- **W2.** For LightGBM with the selected leaf size (5 or 20), the typed arm stops being identical to the calendar arm in at least some fits once W = 2190, and typed minus pooled decreases with W.
- **W3.** For Ridge, typed minus pooled decreases (more favourable to typed) as W grows, in both tests.
- Not predicted: whether any difference changes sign.

## Hybrid arm (typed flags plus the pooled flag)
- **H1.** For Ridge at W = 730, the hybrid arm's MASE is within 0.005 of the better of typed and pooled, in both tests.
- **H2.** For LightGBM leaf 2 at W = 730, the hybrid arm is closer to the pooled arm than to the typed arm.

## Date noise (20% of anchor rows moved by one day; two seeds; W = 730)
- **N1.** For both Ridge and LightGBM leaf 2, moving dates makes typed minus pooled larger (more favourable to pooling) than with the registered calendar, in both tests and both seeds.

## Ridge penalty (alpha 0.1 to 1000, all arms; W = 730)
- **A1.** The sign of Ridge typed minus pooled is the same for alpha 0.1, 1, 10 and 100 in each test.
- Not predicted: alpha 1000.

Every prediction is reported as held or failed, with the numbers.
