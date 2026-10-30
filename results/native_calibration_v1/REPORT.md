# Past-only calibration of native intervals

Exploratory historical study on previously inspected data. Fixed nominal80%intervals; native predictions and raw quantiles are unchanged. Both calibration rules were registered before their new comparison outcomes, with no model/method selection.

Expansion-only conformalized quantile regression is established prior work. Perstate/model/lead, use score=max(lower−actual,actual−upper) and the ceil((n+1)*0.8) order statistic; clamp expansion at zero, never shrink. FrozenSeptember uses16labels15–30September; expanding uses all labels strictly before query ORIGIN. Temporal dependence/drift mean no exchangeability-based time-series coverage guarantee.

The same15targetdates14–28October2026are scored within each state/lead. Coverage is shown with width and proper scores: wider intervals can raise coverage while worsening usefulness. No same-target calibration or forecast-origin-only purge.

## Common primary cohort: four configurations, three individual leads

1,620intervalrows:540matchedcases across configurations × three intervalarms. Negative interval-score/WIS changes favour calibration; positive width changes are costs. Coverage is a proportion, not point accuracy.

### Individual lead 1

| configuration | arm | coverage80 | scaled_width80 | scaled_interval_score80 | scaled_WIS80_median |
| --- | --- | --- | --- | --- | --- |
| chronos_calendar | expanding_past | 0.77778 | 2.01125 | 2.98443 | 0.40612 |
| chronos_calendar | frozen_september | 0.84444 | 2.06276 | 2.95368 | 0.40407 |
| chronos_calendar | native | 0.71111 | 1.78599 | 3.03015 | 0.40917 |
| chronos_history | expanding_past | 0.82222 | 1.87779 | 2.92477 | 0.39559 |
| chronos_history | frozen_september | 0.82222 | 1.8415 | 2.89429 | 0.39355 |
| chronos_history | native | 0.73333 | 1.64255 | 2.95651 | 0.3977 |
| timesfm_calendar | expanding_past | 0.84444 | 1.88484 | 2.78571 | 0.38021 |
| timesfm_calendar | frozen_september | 0.84444 | 1.74589 | 2.73693 | 0.37696 |
| timesfm_calendar | native | 0.77778 | 1.39925 | 2.73662 | 0.37694 |
| timesfm_history | expanding_past | 0.82222 | 1.69068 | 2.57485 | 0.35994 |
| timesfm_history | frozen_september | 0.84444 | 1.73419 | 2.56745 | 0.35944 |
| timesfm_history | native | 0.71111 | 1.44016 | 2.64999 | 0.36495 |

### Individual lead 7

| configuration | arm | coverage80 | scaled_width80 | scaled_interval_score80 | scaled_WIS80_median |
| --- | --- | --- | --- | --- | --- |
| chronos_calendar | expanding_past | 0.86667 | 4.76677 | 5.71189 | 0.76439 |
| chronos_calendar | frozen_september | 0.88889 | 4.3491 | 5.19266 | 0.72977 |
| chronos_calendar | native | 0.8 | 3.63834 | 4.87809 | 0.7088 |
| chronos_history | expanding_past | 0.91111 | 4.81863 | 5.63 | 0.7427 |
| chronos_history | frozen_september | 0.91111 | 4.33227 | 5.00951 | 0.70134 |
| chronos_history | native | 0.8 | 3.61034 | 4.87812 | 0.69258 |
| timesfm_calendar | expanding_past | 0.88889 | 4.20315 | 5.12288 | 0.67841 |
| timesfm_calendar | frozen_september | 0.91111 | 3.89991 | 4.60029 | 0.64357 |
| timesfm_calendar | native | 0.82222 | 3.18253 | 4.39985 | 0.63021 |
| timesfm_history | expanding_past | 0.86667 | 3.93423 | 4.94953 | 0.67498 |
| timesfm_history | frozen_september | 0.88889 | 3.50941 | 4.33485 | 0.634 |
| timesfm_history | native | 0.75556 | 3.01623 | 4.2814 | 0.63044 |

### Individual lead 14

| configuration | arm | coverage80 | scaled_width80 | scaled_interval_score80 | scaled_WIS80_median |
| --- | --- | --- | --- | --- | --- |
| chronos_calendar | expanding_past | 0.73333 | 4.90803 | 6.75155 | 0.91932 |
| chronos_calendar | frozen_september | 0.73333 | 4.51384 | 6.40935 | 0.89651 |
| chronos_calendar | native | 0.71111 | 4.09269 | 6.70152 | 0.91598 |
| chronos_history | expanding_past | 0.75556 | 4.63505 | 6.39446 | 0.87162 |
| chronos_history | frozen_september | 0.71111 | 4.19008 | 6.27454 | 0.86363 |
| chronos_history | native | 0.71111 | 3.98575 | 6.41076 | 0.87271 |
| timesfm_calendar | expanding_past | 0.75556 | 4.17163 | 5.34924 | 0.74992 |
| timesfm_calendar | frozen_september | 0.75556 | 3.88751 | 5.09311 | 0.73285 |
| timesfm_calendar | native | 0.75556 | 3.88225 | 5.09662 | 0.73308 |
| timesfm_history | expanding_past | 0.75556 | 3.91792 | 5.22432 | 0.74114 |
| timesfm_history | frozen_september | 0.71111 | 3.45765 | 4.81417 | 0.71379 |
| timesfm_history | native | 0.68889 | 3.42348 | 4.82657 | 0.71462 |

## Additional TimesFM lead coverage

extended_timesfm_metrics_macro.csv reports all14leads on the same targetdates,3,780intervalrows including810overlapping primaryTimesFMrows. All unique historical rows total4,590. Do not double count these exports or imply Chronos was recalibrated at unarchived leads. Fresh TimesFM hindcasts reproduce all792previous point/quantile rows.

## Prospective interval annex

Rules for a separate annex were registered before new calibration outcomes. It derives native/fixed/expanding intervals from ORIGINAL TimesFM future quantiles without new future inference, copying original points/median. Its own issuedUTC/eligibility/freeze hashes are recorded separately. Original252forecasts are untouched. Samefutureepisode/source, not independentconfirmation; no future actuals, scores or automatic workflow reactivation.

## Limitations

This short daily panel does not establish calibration across all festivals, seasons or sources. Native event-feature undercoverage in2024–2025is not repaired by this different-cohort daily experiment. No hyperparameter/window/nominal-level search or attractive-coverage winner selection. Source publication lag/revisions, rights, full amendments, independent human review and adequate fresh confirmation remain open. Native fine-grid crossings elsewhere remain visible.
