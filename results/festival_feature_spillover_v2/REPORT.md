# Explicit festival-feature intervention

Secondary spillover protocol frozen before non-event model outputs; primary event experiment already started. Historical benchmarks inspected; still exploratory.

**This is an added-feature experiment. Earlier multi-festival scores were diagnostics without these event identities.**

## Matched primary comparison

72weekday-matched non-event cases; select first eligible shift from+28,-28,+35,-35,+42,-42days, excluding+/-3days of every annual schedule/registered family anchor in the same state/year. Same cases/arms for all6model variants. No errors or target magnitudes select dates.

1296 scored forecasts: 6model variants x 3common arms x 72identical cases. MASE is error, not accuracy percent; lower is better. Equal states within year, years within festival and families for overall summaries.

All variants, including zeros and active placebos, are reported. No best-looking date, encoding, capacity setting or model is selected for future deployment from these results.

### Individual lead 1

| model | calendar | day5 | window5 |
| --- | --- | --- | --- |
| ridge | 0.2954 | 0.2819 | 0.27925 |
| lightgbm | 0.33488 | 0.32823 | 0.33485 |
| lightgbm_capacity2 | 0.32582 | 0.31406 | 0.32628 |
| sarimax | 0.25238 | 0.24862 | 0.25313 |
| chronos | 0.26101 | 0.24453 | 0.24759 |
| timesfm | 0.24067 | 0.2321 | 0.22994 |

### Individual lead 7

| model | calendar | day5 | window5 |
| --- | --- | --- | --- |
| ridge | 0.78005 | 0.777 | 0.77492 |
| lightgbm | 1.10561 | 1.10172 | 1.09614 |
| lightgbm_capacity2 | 0.96194 | 0.96439 | 0.95914 |
| sarimax | 0.80052 | 0.74529 | 0.78022 |
| chronos | 0.6224 | 0.61778 | 0.63584 |
| timesfm | 0.59157 | 0.57628 | 0.56398 |

### Individual lead 14

| model | calendar | day5 | window5 |
| --- | --- | --- | --- |
| ridge | 0.8742 | 0.87112 | 0.85256 |
| lightgbm | 0.99641 | 0.99641 | 0.99988 |
| lightgbm_capacity2 | 1.02477 | 1.03194 | 1.03125 |
| sarimax | 1.10447 | 1.07901 | 1.10636 |
| chronos | 0.7915 | 0.8171 | 0.8141 |
| timesfm | 0.6661 | 0.64049 | 0.65545 |

## Per-festival and individual-year results

See primary_metrics_festival.csv, primary_metrics_state_year.csv and primary_paired_festival.csv. Paired percent reductions are means of within-state/year effects, not ratios of macro MASE. Zero denominators remain explicitly undefined; no epsilon or silent deletion. MASE changes remain available. Negative effects and all control outcomes are retained.

## Wider classical cohort

Bounded seasonal/weekday-matched spillover diagnostic, not an all-day or operational evaluation. Event-family label denotes the matched pair, not a festival observed on control date.

secondary_classical_* files retain every classical arm, including35offset/zero/placebo sensitivities where prespecified. Foundation-model anchor metrics must not be compared with these wider-window metrics.

## Bounds

Two historical years and related states/dates provide limited independent evidence. Calendar definitions are annual-as-issued, not full amendment certification or proof of statewide closure. Diwali is the legacy main/subsidiary subset. Dussehra2025/Gandhi and spring2025/Eid co-occur. New target values never enter inputs, but retrospective publication availability and pretraining/proxy overlap remain unresolved.

One fixed placebo seed and these representations do not establish causality or a universal event-information mechanism. Rare day indicators may be below a tree leaf constraint; capacity2 is a separate fixed sensitivity, not an outcome-selected best regime. Native quantile failures are reported separately and retained without sorting/clipping. Point-metric audits are not calibration or independent human approval.

Source permission, amendments, human review and prospective outcomes remain pending. Original source/forecast results and future Git blobs remain unchanged. No journal readiness, acceptance or new architectural method is claimed.
