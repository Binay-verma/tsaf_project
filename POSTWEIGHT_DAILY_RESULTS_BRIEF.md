# Daily comparison after both audited weight uploads

Completed and independently audited internal study: `results/postweight_daily_v1`. Same frozen source, three states and44identical target dates (15September–28October2026) at each lead. Earliest origin2September;396cases/configuration,3,168forecasts across eight configurations. No added festival identities, new actual retrieval or future-score update.

Equal-state MASE is scaled error, lower is better. Leads are individual days.

| Configuration | Lead1 | Lead7 | Lead14 |
| --- | ---: | ---: | ---: |
| Chronos history |0.58548|1.31670|1.59292|
| Chronos calendar |0.60418|1.37518|1.68293|
| TimesFM history |0.54620|1.16303|1.30856|
| TimesFM calendar |0.54622|1.17994|1.34277|
| Rich monthly Ridge calendar |0.59838|1.34065|1.55885|
| Stable monthly LightGBM calendar |0.66784|1.38801|1.92280|
| Last value |0.67397|1.42503|1.85165|
| Weekly repeat |1.42503|1.42503|1.85165|

TimesFM history has the lowest macro error at each lead **among these eight configurations on this bounded panel**. Ordinary weekday/Fourier inputs slightly worsen both models here. This is a different cohort from the earlier partial-2026 benchmark, so it does not erase that earlier Chronos result or establish a universal/full-year ranking. Local pre-2026-selected parameters remain fixed, with monthly refits; memory/adaptation budgets are not architecture-identical.

All684foundation task inputs reconstruct byte-for-byte; future-target perturbations and solo/batch checks pass (Chronos maximum1.526e-5GWh,TimesFM0). Thirty-six local fits and18overlap groups reproduce earlier saved baseline points. Complete cases, source labels, annual scales, naive predictions, macro metrics and native probability arithmetic are audited. All686protectedpriorfiles remain unchanged.

Native0.1–0.9pinball and unmodified80%interval scores are reported with widths. Next-day coverage is approximately74–76%, below nominal80%; some longer leads are lower. No adjacent native quantile crossing occurs in scored panel outputs, but this is not proof of calibration. Event-anchor undercoverage in the separate pooled study is much more severe. No sorting, clipping or fitted calibration is applied.

Every scored target postdates both actual weight uploads, conditional on correct observation dates. These historical targets were already inspected, so the experiment is **not untouched confirmation**, proxy clearance, an independently sourced replication or a reconstructed real-time trial. Ideal origin-1data availability remains distinct from historical publication lag/revisions.

The first finalizer completed scientific tables, then failed on integer Markdown headers. Its execution source/failure note remain. A report-only recovery verified that all seven scientific output hashes were unchanged; no model rerun or invented timing. Source rights, amendments, independent human review and later/source-independent confirmation remain open. The original prospective freeze and paused workflow remain unchanged.

Full state/lead/native tables and audit: [REPORT.md](results/postweight_daily_v1/REPORT.md). The editable paper and figures are under `manuscript/journal_draft_v1/`.
