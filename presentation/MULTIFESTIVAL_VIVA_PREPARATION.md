# Viva preparation — multi-festival extension

Use the final saved tables for exact values. Do not memorise a universal ranking.

**What do you predict?** Daily electricity energy met/supplied in GWh for Delhi, Karnataka and Maharashtra. It is not hourly peak power or unconstrained latent demand.

**Did you build a new foundation model?** No. We evaluate pinned pretrained Chronos and TimesFM models and fit local classical/machine-learning baselines. The contribution being investigated is the evaluation of regional calendars, representation and practical data/model limitations.

**Which other models did you compare?** Last-value and weekly-repeat baselines, Ridge, LightGBM, SARIMAX and additive weekly ETS. The expanded matched study includes fifteen configurations across these and the two foundation-model families. Different feature/refit budgets are reported explicitly.

**Which festivals?** Historical 2024–2025 windows around Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali, only for documented state/festival combinations. Ganesh and spring-new-year groups use Karnataka/Maharashtra; Holi uses Delhi/Maharashtra; Dussehra and Diwali use all three. These are fixed anchor-centred windows, not the full duration of every festival.

**Are all holiday dates fully verified?** We have annual-as-issued source evidence and a date crosswalk. Later amendments and actual observance changes are not fully certified. Government-office schedules do not prove statewide shutdown. We do not select dates from forecast errors.

**Did adding all those festival features improve forecasts?** That has not been established. The new extension primarily measures existing/ordinary-calendar configurations during additional festival windows. Those calendar inputs contain weekdays and annual harmonics, not each new festival identity. The earlier Diwali feature/control experiments are a separate result.

**Why use MASE?** It scales absolute errors by a pre-year weekly-difference reference, supporting equal-state summaries despite different energy magnitudes. Lower is better. A score 0.5 is not 50 percent accuracy, and MASE below 1 does not by itself prove superiority to a separately evaluated contemporary naive forecast. We also retain per-state MAE in GWh.

**How did you avoid looking into the future?** Inputs stop before each forecast origin. Fitting/validation labels follow chronological boundaries; monthly parameter fits stop before the month begins. We retain the source/model hashes and case ledger, and perturb unseen target values to check foundation inputs remain unchanged. These checks do not resolve historical publication lag or unknown pretraining overlap.

**Why is a seven-day-ahead forecast not a weekly average?** Lead 7 scores the individual target day at origin+6 under our first-unseen-origin definition. Lead 14 is another individual target day. Each model is compared on the same state/origin/lead cases.

**Is Chronos the best?** It performed strongly in the broader daily benchmark, but historical rankings change with festival, horizon, features and adaptation policy. Show the all-configuration table. Do not turn an observed minimum into a statistically established universal winner.

**Are 528 forecasts 528 independent experiments?** No. They share states, nearby days, years and data lineage. There are only two historical years in this extension. Dussehra 2025 coincides with Gandhi Jayanti; the spring 2025 window borders Eid. These observations do not identify an isolated causal festival effect.

**Were there failures?** Yes. The first report renderer lacked an optional Markdown dependency after scientific scores completed; we retained that failure and repaired only reporting. Two SARIMAX optimisation attempts failed to converge before the predefined training-only retry converged. Earlier numerical-reproduction and negative-calendar results are also preserved.

**Why not include weather immediately?** Weather may help electricity forecasting, but a fair operational comparison needs historical weather forecasts available at each issue time, matched geographic aggregation and a separate protocol. Actual future weather must not be passed as though it were available to the forecaster.

**Is future validation complete?** No. Forecasts were frozen on 30 October for eligible 31 October–11 November targets. On 1 November the full outcome period is incomplete. The source-permission reply and independent human review are also pending. Present this as ongoing research.

**What comes next?** A separately recorded test of the incremental value of additional festival covariates with training-year date evidence, further source/calendar review, and later scoring of the unchanged prospective forecasts. Do not tune those frozen forecasts after seeing these historical results.

**Are the native uncertainty forecasts always well ordered?** No. Three adjacent-quantile crossings occur in the new Chronos calendar forecasts for Karnataka spring 2024; they are retained unchanged. TimesFM has none in this scored run. Passing point-error checks does not establish calibrated uncertainty.
