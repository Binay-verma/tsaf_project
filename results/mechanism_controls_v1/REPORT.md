# Both-foundation-model mechanism controls v1

Completed:2304 fresh inference tasks,2700 scored predictions (150 identical event cases x9arms x2models),
2024–2025, three states, leads1/7/14. No old forecast cache was adopted as new evidence.
Models/code/weights are pinned; all cases and source/model/protocol hashes recorded. Each batch checks
that perturbing unseen targets cannot change constructed inputs. Zero native quantile crossings.
Original61 protected source/result files and frozen prospective predictions remain unchanged.

The protocol predates the new controls but follows historical result inspection. All outcomes exploratory,
with only two annual event clusters and one seeded placebo. No p-values, independent-day inference,
external preregistration, source-independence or causal provenance claim is made.

## Prespecified contrasts

Positive percentage = lower MAE for arm versus reference. Compute each state/year effect, average states
within year then years. These means are not ratios of the macro MASE table.

| model | arm | reference | horizon | mean_state_improvement_pct |
| --- | --- | --- | --- | --- |
| chronos2 | regional_7 | generic_7 | 1.0000 | 1.4336 |
| chronos2 | regional_7 | generic_7 | 7.0000 | 1.5929 |
| chronos2 | regional_7 | generic_7 | 14.0000 | 1.5479 |
| chronos2 | regional_7 | placebo_7 | 1.0000 | -1.6952 |
| chronos2 | regional_7 | placebo_7 | 7.0000 | 6.8274 |
| chronos2 | regional_7 | placebo_7 | 14.0000 | 2.5355 |
| chronos2 | regional_window | generic_window | 1.0000 | 0.2185 |
| chronos2 | regional_window | generic_window | 7.0000 | -0.6753 |
| chronos2 | regional_window | generic_window | 14.0000 | -0.8099 |
| chronos2 | zero_1 | calendar | 1.0000 | 0.5624 |
| chronos2 | zero_1 | calendar | 7.0000 | -0.2485 |
| chronos2 | zero_1 | calendar | 14.0000 | -0.0422 |
| chronos2 | zero_7 | calendar | 1.0000 | 1.1666 |
| chronos2 | zero_7 | calendar | 7.0000 | -1.9548 |
| chronos2 | zero_7 | calendar | 14.0000 | -1.9705 |
| timesfm3 | regional_7 | generic_7 | 1.0000 | 4.7166 |
| timesfm3 | regional_7 | generic_7 | 7.0000 | 3.2523 |
| timesfm3 | regional_7 | generic_7 | 14.0000 | 6.4275 |
| timesfm3 | regional_7 | placebo_7 | 1.0000 | 2.3444 |
| timesfm3 | regional_7 | placebo_7 | 7.0000 | 15.0094 |
| timesfm3 | regional_7 | placebo_7 | 14.0000 | 18.1926 |
| timesfm3 | regional_window | generic_window | 1.0000 | 1.1717 |
| timesfm3 | regional_window | generic_window | 7.0000 | -0.0888 |
| timesfm3 | regional_window | generic_window | 14.0000 | 2.1207 |
| timesfm3 | zero_1 | calendar | 1.0000 | 0.6178 |
| timesfm3 | zero_1 | calendar | 7.0000 | -1.7639 |
| timesfm3 | zero_1 | calendar | 14.0000 | -2.6226 |
| timesfm3 | zero_7 | calendar | 1.0000 | 1.9910 |
| timesfm3 | zero_7 | calendar | 7.0000 | -5.1862 |
| timesfm3 | zero_7 | calendar | 14.0000 | -4.2726 |

## What changes the interpretation

1. Equal scalar dimensions give small/mixed regional increments: Chronos +0.22%/−0.68%/−0.81%,
TimesFM +1.17%/−0.09%/+2.12% at leads1/7/14. This does not demonstrate an encoding-independent regional benefit.
2. With seven channels held equal, regional increments are Chronos +1.43%/+1.59%/+1.55% and TimesFM
+4.72%/+3.25%/+6.43%. These differ markedly from the earlier ordinary-calendar-to-regional contrast,
which changes information and dimension together. Representation remains central to interpretation.
3. Zero channels change forecasts despite adding no event information. Seven zeros alter predictions by
up to6.05GWh (Chronos) and6.93GWh (TimesFM). Day1 mean error improvements from seven zeros are1.17% and1.99%.
Thus a small calendar gain alone cannot be assigned to extra date information without interface controls.
This is observed sensitivity, not proof of an implementation bug or a complete explanation of every gain.
4. Active placebo effects are model/lead dependent. Regional versus seven-channel placebo is negative
for Chronos day1 (−1.70%) but positive at its longer leads; TimesFM is positive across these tested leads.
One selected date-only seed is not an exchangeable randomisation distribution.
5. Delhi generic and regional inputs contain identical dates and produce identical predictions in both
dimensionalities, as expected. This check validates a specific implementation identity, not all calendar dates.

## Bounds

The scalar window discards relative-day detail. Scalar versus seven-channel results change both representation
and dimension; they do not isolate a pure dimension mechanism. Within each dimension, generic/regional
comparisons hold feature count fixed but change event information/duration. Annual dates are as-issued
evidence, not full amendment certification. Both historical years predate audited model uploads, so proxy/sample
overlap remains unresolved. No best arm, date shift or new forecast was selected from these outcomes.

Per-state/year metrics, individual-year contrasts and native predictions are retained under each model.
Audit using `src/audit_foundation_controls.py --model chronos2` and `--model timesfm3`.
