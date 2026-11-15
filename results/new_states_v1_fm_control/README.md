# TimesFM-3 encoding control (exploratory; run after the registered analysis)

**Question.** TimesFM-3 did better with typed flags at leads 7 and 14 (results/new_states_v1_diagnostics). Is that because the registered pooled arm carries four all-zero padding channels?

**Runs.** Kaggle, both cohorts (fm_2017_2020 in commit 5867b88; fm_2021_2025 recovered from the notebook output, see its NOTE_RECOVERY.md). Same weights, code and cases as the registered runs. Arms:
- pooled_day5: the registered pooled arm, rerun.
- pooled1: the pooled flag without padding.
- zero5: five zero channels, no festival information.

**Reproduction check.** The rerun pooled_day5 equals the registered forecasts exactly (5157 rows, maximum difference 0.0).

## Results (`analysis/contrasts.csv`)
Family-year clusters (45), two-sided sign-flip p with 100k draws. MASE differences; negative means the first arm is better.

| Contrast | Lead 1 | Lead 7 | Lead 14 |
|---|---|---|---|
| Padding effect (pooled_day5 − pooled1) | +0.0026 (p 0.075) | +0.0175 (p 0.004) | +0.0150 (p 0.063) |
| Typed − pooled1 | +0.0022 (p 0.66) | −0.0604 (p 0.019) | −0.0636 (p 0.0015) |
| Typed − pooled_day5 (registered contrast) | −0.0004 | −0.0779 | −0.0785 |
| Typed − zero5 | −0.0360 | −0.1375 | −0.1331 |
| pooled1 − zero5 | −0.0382 | −0.0771 | −0.0696 |

## Leave one state out (`analysis/typed_vs_pooled1_leave_one_state_out.csv`, src/new_states_fm_control_loso_v1.py)
Typed − pooled1, one-sided p for typed better:

| Left out | Lead 7 | Lead 14 |
|---|---|---|
| None | −0.0604 (p 0.009) | −0.0636 (p 0.0007) |
| Gujarat | −0.0351 (p 0.056) | −0.0254 (p 0.060) |
| Tamil Nadu | −0.0147 (p 0.27) | −0.0374 (p 0.028) |
| Any other state | −0.065 to −0.087 (all p < 0.015) | −0.070 to −0.084 (all p < 0.002) |

The per-state means are about −0.37 (lead 7) and −0.49 (lead 14) in Gujarat, and −0.36 and −0.22 in Tamil Nadu. Every other state is within ±0.07.

## Reading
- The padding hurts a little at longer leads. It explains about a quarter of the registered lead-7/14 contrast.
- Typed flags still beat the unpadded pooled flag, so the longer-lead advantage is mainly not an encoding artefact.
- Like the confirmed local-model results, it is concentrated in Gujarat and Tamil Nadu, the two states with the most heterogeneous festival effects.
- At lead 1 the representation does not matter for TimesFM-3. Festival information of either kind helps by about 0.04 against no festival information.

All of this is exploratory, found after the registered test. The registered H2 decision (NOT CONFIRMED) is unchanged.
