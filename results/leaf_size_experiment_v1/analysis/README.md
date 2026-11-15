# Leaf-size experiment: results against the pre-committed predictions (EXPLORATORY)

Reproduction: at leaf size 2, and at each fit's selected leaf size, all lead-1 predictions equal the registered leaf-2 and Stable LightGBM predictions exactly (maximum absolute difference 0.0; 1,719 cases in the first test, 1,323 in the second).

| Prediction | First test | Second test |
|---|---|---|
| P1: typed = calendar exactly whenever no typed flag is set on at least L training rows | held (1,501 of 1,501 fits) | held (1,314 of 1,314) |
| P1b: typed = calendar at every L when no typed flag reaches 3 rows (min_data_in_bin) | **failed** (1,195 of 1,332) | **failed** (1,473 of 1,620) |
| P2: share of fits with typed = calendar does not fall as L grows | held (0.42 at L=1 to 1.00 from L=5) | held (0.59 at L=1 to 1.00 from L=4) |
| P3: typed minus pooled > 0 for every L from 2 to 20 | **failed at L >= 10** (0.0002 at 10, exactly 0 at 20: neither flag usable); positive for L = 2 to 8 | **failed at L >= 8** (exactly 0); positive for L = 2 to 6 |
| P4: pooled differs from calendar in most fits up to L = 6 | held (pooled = calendar in 15-18% of fits) | **failed** (47-54% of fits) |

Typed flags are set on 2 to 4 training rows per 730-day window (most often 2); the pooled flag on a median of 8 (first test) and 6 (second test) rows. Typed minus pooled lead-1 MASE by leaf size: first test 0.0086 (L=1), 0.0068 (2), 0.0214 (3), 0.0218 (4), 0.0269 (5), 0.0252 (6), 0.0219 (8), 0.0002 (10), 0 (20); second test 0.0146, 0.0148, 0.0215, 0.0223, 0.0221, 0.0178, 0 (8, 10, 20). Source: by_leaf.csv, predictions_vs_results.json.
