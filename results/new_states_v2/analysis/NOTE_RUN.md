# Registered analysis run (once), second test

- **Run:** 2026-11-15 19:26 UTC (2026-11-16 00:56 IST), `python src/new_states_v2_analysis.py`. The analysis code, pipeline, tests, calendar and heterogeneity file are byte-identical to registered commit f1f3560 (git diff empty). The 8 unit tests passed beforehand.
- **Order:** OSF registration submitted by 23:51 IST on 15 Nov 2026; parameter selection started 18:21 UTC (23:51 IST); all forecasts 18:48–19:25 UTC; no outcome was looked at before this run.
- **Inputs:** four run.json files (Ridge, stable LightGBM, leaf-2 LightGBM, SARIMAX), 19,845 rows each (3,969 cases x 5 arms), hashes checked by the script.

## Registered decisions (36 family-year clusters, 2017-2025; Holm across R1, R2, M1, M2)
| Hypothesis | Statistic | Years in direction | One-sided p | Holm p | Decision |
|---|---|---|---|---|---|
| R1, SARIMAX typed better | -0.0008 | 5/9 | 0.410 | 0.489 | **NOT CONFIRMED** |
| R2, leaf-2 LightGBM pooled better | +0.0147 | 9/9 | 0.000001 | 0.000004 | **CONFIRMED** |
| M1, Ridge typed better in the 3 highest-h_abs states | -0.0081 | 4/5 | 0.168 | 0.489 | **NOT CONFIRMED** |
| M2, Spearman(h_abs, Ridge difference) < 0 | -0.43 | - | 0.163 | 0.489 | **NOT CONFIRMED** |

## Registered sensitivities and secondary analysis
- Without 2020-2021: same decisions (R2 confirmed, others not).
- Author-checked calendar rows only (24 clusters, built from the 43 rows the author checked one by one): nothing confirmed; R2 +0.0040, 6/9 years. This subset is small and depends on which rows were sampled.
- M1/M2 with the first-test h: same decisions.
- Combined with the first test (45 family-year clusters, 14 states): R1 SARIMAX -0.0056 (6/9 years, one-sided p 0.029); R2 leaf-2 LightGBM +0.0089 (8/9 years, p 0.0005). Secondary, not used for decisions.

## Reading
R2 replicates and is larger than in the first test (+0.0147 against +0.0068). R1 does not replicate: SARIMAX's typed advantage is about zero in these states (power for R1 was stated as 18-34%). The heterogeneity mechanism is not confirmed: the signs are in the predicted direction (M1 -0.0081, 4/5 years; M2 rho -0.43) but neither test is close to significance. No result was changed, rerun or reinterpreted after this run.
