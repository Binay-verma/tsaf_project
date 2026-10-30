# Matched TimesFM/Chronos historical event comparison v1

Completed predeclared exploratory replication, 2024–2025, three states, leads1/7/14. 128 state/origin contexts per input mode; 384 inference tasks,5376 forecast-day outputs. Only the fixed150 case rows per mode are scored (450 total TimesFM rows). Every model sees identical event-target cases; batch4 versus single-sample checks match exactly for the first4 tasks in each mode. Task independence here means inference samples, not statistically independent dates/states/events. No task-specific training or model/feature selection.

Pinned code/weights are identical to `second_model_audit_v1`. Actual weight hash, case/protocol/code hashes, prediction files, quantiles, task logs and source-label/scale/metric audits are retained. All61 protected historical files remain unchanged. Zero native adjacent-quantile crossings. Runtime about435seconds on4 CPU threads.

## Equal-state/year macro MASE

| Model | Inputs | Lead1 | Lead7 | Lead14 |
| --- | --- | ---: | ---: | ---: |
| chronos2 | A_history | 0.54564 | 1.24114 | 1.19892 |
| chronos2 | B_calendar | 0.53022 | 1.22380 | 1.19796 |
| chronos2 | D_regional_festival | 0.53466 | 1.18789 | 1.19962 |
| timesfm3 | A_history | 0.53440 | 1.22783 | 1.06153 |
| timesfm3 | B_calendar | 0.52136 | 1.22139 | 1.16340 |
| timesfm3 | D_regional_festival | 0.49828 | 0.98611 | 0.90890 |

TimesFM regional versus ordinary-calendar mean per-state/year percentage MAE reductions are +3.49%,+14.72%,+18.33% at leads1/7/14. The matched two-year Chronos effects are −2.30%,+1.04%,−0.93%. These are means of relative state/year effects, not ratios of the aggregate MASE table. The earlier four-year Chronos result remains unchanged; different year scopes must not be conflated.

Year dependence matters. TimesFM regional day1 effect is −1.61% in2024 and +8.59% in2025; longer-lead effects are positive in both years. Chronos is negative at every lead in2024, with mixed2025 results. This is evidence of model/lead/year dependence, not a universal festival method or causal effect. No best-scoring shift/encoding or new final model was selected on these results.

## Native uncertainty

Native .1–.9 quantiles are scored separately with pinball/80%coverage/width. Regional coverage ranges from68.25% (2024 day1) to95.24% (2024 day14), so the model is not declared calibrated. Wider intervals can improve coverage while reducing sharpness; inspect pinball and width together. Do not rank these80% intervals against90% residual intervals by coverage alone. Per-year/state metrics are retained.

## Limits and contribution

Only two event-year clusters; states and nearby days are correlated. Both years precede TimesFM's August2026 weights and Chronos's audited2025 upload, so historical/proxy overlap remains unresolved. B-to-D changes information and channel dimension; equal-information/feature-count controls across both TSFMs are still needed for a provenance mechanism claim. All previous outcomes were already exploratory; this protocol was recorded before new model outcomes, not externally preregistered. No prospective predictions, method choices or source snapshots were changed.

The useful finding is that a calendar contrast can help one pretrained model while hurting another on the same cases. Generic encoding dependence already has close prior work; an India/state/calendar-quality contribution requires further provenance, independence and rights evidence. No novelty, significance, architecture-only superiority or journal-readiness claim follows.

Audit: `.venv/bin/python src/audit_matched_events.py`. Completed/interrupted run guards preserve all prior artifacts. A rerun requires a separately versioned experiment directory and explicit OUT change.
