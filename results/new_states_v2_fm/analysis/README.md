# TimesFM-3 on the second-test states: result against the pre-committed prediction (EXPLORATORY)

Both hosted runs completed (3,528 + 4,410 rows = 3,969 cases x 2 arms); `python src/new_states_v2_fm_v1.py analyse` run once on 16 Nov 2026 (00:30 UTC).

| Contrast (typed - pooled1, 36 clusters) | Mean | Years negative | One-sided p (typed better) |
|---|---|---|---|
| lead 1 | +0.0056 | 2/9 | 0.945 |
| lead 7 | -0.0229 | 7/9 | 0.030 |
| lead 14 | -0.0150 | 5/9 | 0.140 |
| leads 7 and 14 | -0.0189 | 6/9 | 0.066 |

- **F1 failed:** the leads 7 and 14 contrast is negative, with 6 of 9 years negative, but its one-sided p is 0.066, above the 0.05 we required. It is about a third of the first test's -0.060/-0.064.
- **F2 held:** |lead 1| = 0.0056 < 0.01.
