# Recentered calendar panel: audited local result

The document-defined1October2025KarnatakaVijayadasami window is now complete (28September–4October). Three target/lead cases move5October→28September; the originalfeature baseline predicts exactly the same newcohort. The corresponding placebo retains its +35day shift, moving6November→5November to preserve weekday. No outcome chose either date.

All648new local forecasts are complete and separately audited. Composition reuses verified original/v2forecasts; the fullpanel still has528event/216ordinarycases perconfiguration and all8arms for all4localvariants. The audit passes240newfit/querybytechecks,684unchangedplaceboblock proofs, all labels/scales, point/hierarchical/composition calculations. Original results and the separate same-case trueflag-only sensitivity remain intact.

Next-day MASE for the aligned-feature view (lower is better):

event_window

| model | calendar | day5 | pooled_day5 | pooled_window5 | window5 |
| --- | --- | --- | --- | --- | --- |
| lightgbm | 0.69865 | 0.69483 | 0.6611 | 0.71233 | 0.70168 |
| lightgbm_capacity2 | 0.68582 | 0.64952 | 0.60469 | 0.70001 | 0.69028 |
| ridge | 0.57699 | 0.45317 | 0.46093 | 0.60838 | 0.57914 |
| sarimax | 0.57301 | 0.42533 | 0.45345 | 0.57511 | 0.57787 |

ordinary

| model | calendar | day5 | pooled_day5 | pooled_window5 | window5 |
| --- | --- | --- | --- | --- | --- |
| lightgbm | 0.39366 | 0.39545 | 0.38932 | 0.39604 | 0.39507 |
| lightgbm_capacity2 | 0.39178 | 0.37852 | 0.36518 | 0.37951 | 0.38876 |
| ridge | 0.28458 | 0.27908 | 0.28363 | 0.28709 | 0.28887 |
| sarimax | 0.23073 | 0.22949 | 0.2291 | 0.23155 | 0.22995 |

All28pairwise arm contrasts, bothyears, everyfamily and leave-family-out tables are retained and separately scalar-checked in the contrasts subdirectory. These are descriptive dependent-cell comparisons, not 528independent events or precise two-year significance.

The matchedfeature contrast is in changes_balanced.csv. The separate3-date cohort-composition change is in composition_changes.csv; do not compare old/newcohortmacro scores as an isolated feature effect. Foundations/pureencodings remain queued; fullallmodelresults and paperintegration are pending. OneMH2022nameddate evidencegap, two sharedmainexceptions, amendments, vintages, Indianreusepermission, independenthumanreview and futureconfirmation remain unresolved.
