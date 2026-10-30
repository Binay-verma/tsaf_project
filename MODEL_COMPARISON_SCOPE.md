# Reading the model comparisons correctly

The project has several separate comparisons. Their rankings answer different questions.

| Comparison | Period and cases | What the score means |
| --- | --- | --- |
| Original broad daily benchmark |2022–2026 daily origins; displayed2026scores are partial-year | Chronos history-only leads the displayed2026aggregate configurations. This is not proof that it beats every classical model or every festival configuration. |
| Original matched Diwali study |2022–2025, then a two-year matched TimesFM extension | Regional Diwali features can change rankings; SARIMAX and TimesFM beat Chronos in particular two-year comparisons. Different year scopes must not be pooled without explanation. |
| Multi-festival diagnostic |2024–2025; five festival groups; identical528cases per configuration | Compare performance around those windows. Ordinary-calendar arms contain weekdays/Fourier harmonics, not new Holi/Ganesh/Ugadi identities. These scores do not establish an effect of adding new festival indicators. |
| Diwali mechanism controls | Same150two-year Diwali cases; equal dimensions, zeros and active placebos | Calendar effects depend on representation/model. Zero channels can change predictions. Small gains alone do not prove a regional-information mechanism. |
| Prospective freeze | Eligible31October–11November2026targets | Predictions already exist; complete actual outcomes and scores do not. Historical extensions cannot retune this episode. |

## Multi-festival configurations and budgets

| Family | Inputs and adaptation | Selection and source |
| --- | --- | --- |
| Last value / weekly repeat | Fixed repetition rules using past observations | No fitting or hyperparameter search; original saved forecasts |
| Basic Ridge | Six history features, with/without13ordinary calendar channels; annual fit | Fixed alpha10; original saved forecasts |
| Rich Ridge |27history features, with/without13ordinary calendar channels; monthly fit | Three candidate alphas selected in the original pre-year validation; saved forecasts |
| Stable LightGBM | Same rich history/calendar variants; monthly fit; explicit float32 interface | Eight candidates selected by original pre-year validation; stable_tree_refit_v2saved forecasts |
| SARIMAX | Fixed(1,0,0)x(1,0,0,7), with/without13calendar channels; annual parameter fit and past-only state updates | New fits on exact multi-festival cases; retries use training convergence only |
| Weekly ETS | Additive error/weekly seasonality, no trend; monthly fit and fixed-parameter state updates | Fixed ETS(A,N,A), no grid; new fits; initial states stay tied to the same training start |
| Chronos-2 |730-day context; history and ordinary-calendar variants | Pinned pretrained weights, no task fine-tuning; history forecasts reused, calendar forecasts newly inferred |
| TimesFM-3 |730-day context; history and ordinary-calendar variants | Pinned pretrained weights, no task fine-tuning; new matched inference |

These yield fifteen configurations, not fifteen independently developed architectures. Refitting, feature sets and pretraining budgets differ; this is a documented deployment-policy comparison. None is claimed to be the strongest attainable configuration of its family.

## Metrics and scope

MAE is retained per state in GWh. MASE divides absolute error by a state-specific mean absolute weekly difference from the730-day pre-year reference period. The denominator is fixed within year. The main festival summaries weight states equally within each year, then years equally. Any overall summary additionally weights the five families equally. The state coverage differs between families, so comparing one festival's score with another does not isolate festival difficulty.

MASE is not an accuracy percentage. A value below1does not automatically mean beating the separately evaluated contemporaneous naive baseline. The observed lowest error is descriptive; these dependent windows and two years do not establish a universal statistically superior model.

The windows are fixed anchor-centred cohorts, not all days of every celebration. Government-office schedules, religious observance and actual statewide activity are different concepts. Dussehra2025coincides with Gandhi Jayanti; the2025spring-new-year window borders Eid. Source revisions/publication timing and historical pretraining/proxy overlap remain unresolved.

See the full configuration/state/year tables and audits before making a claim. Native uncertainty quality is checked separately from point error: the expanded Chronos-calendar run has three native quantile crossings, retained unmodified rather than hidden by sorting. A passed point-metric audit does not certify calibrated uncertainty.
