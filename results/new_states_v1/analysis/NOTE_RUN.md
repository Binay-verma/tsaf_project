# Registered analysis run (once)

- **Run:** 2026-11-14 21:28 UTC (2026-11-15 02:58 IST), `python src/new_states_analysis_v1.py`, unchanged since registration commit c987d7e (sha256 7fbe9730…7b7d7b, as recorded in all three protocol.json files). The 7 unit tests passed beforehand.
- **Inputs:** all eight run.json files present: four local models; Chronos-2 and TimesFM-3 for both cohorts. The two fm_2021_2025 runs were recovered from Kaggle output; see their NOTE_RECOVERY.md.

## Registered decisions (main analysis, 45 family-year clusters, 2017–2025)
| Hypothesis | Mean typed − pooled lead-1 MASE | Years in direction | Holm p | Decision |
|---|---|---|---|---|
| H1, SARIMAX typed better | −0.0097 | 6/9 | 0.038 | **CONFIRMED** |
| H2, TimesFM-3 pooled better | −0.0004 | 3/9 | 0.531 | **NOT CONFIRMED** |
| H3, leaf-2 LightGBM pooled better | +0.0068 | 8/9 | 0.038 | **CONFIRMED** |

## Registered sensitivities
| Sensitivity | H1 | H2 | H3 |
|---|---|---|---|
| Without 2020–2021 (35 clusters) | NOT CONFIRMED (Holm p 0.115, 4/7 years) | NOT CONFIRMED | CONFIRMED (Holm p 0.006, 7/7 years) |
| Official sources only (44 clusters) | NOT CONFIRMED | CONTRADICTED (typed better, p_opposite 0.028) | NOT CONFIRMED (sign reversed) |

**What the official-sources filter does:** 241 of the 331 calendar rows came from non-government reposts. All 331 rows were checked by the author, but the registered filter uses source type, not the check. In 2017–2025 it removes every row for Andhra Pradesh, Gujarat, Madhya Pradesh, Rajasthan and Uttar Pradesh, and 7 for Telangana. The remaining clusters therefore rest almost entirely on Tamil Nadu and Telangana. This sensitivity is reported as registered. It is a small, two-state subset, not a robustness check of comparable size.

## Effect sizes
All differences are small, about 0.01 MASE against lead-1 MASE levels of 0.50–0.71 (`balanced.csv`). No result was changed, rerun or reinterpreted after this run.
