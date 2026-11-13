# New-states study: registration

This folder is the registration. It was committed before any parameter selection or forecast for these seven
states, and before any of their outcomes was evaluated in this project. It becomes public when this commit is pushed
to https://github.com/Binay-verma/tsaf_project, and is additionally timestamped on OSF by the author.

- States: Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat, Telangana, Andhra Pradesh, Tamil Nadu.
- Event years 2017-2025; 5,157 event-window cases (leads 1, 7, 14); 45 family-year clusters; 5.33 states per cluster.
- Calendars: review/new_states_v1/calendar_entries_2015_2025.csv, 331 rows reported verified by the author on
  13 November 2026 (method recorded per row); conventions in review/new_states_v1/DESIGN_DRAFT.md.
- Hypotheses (lead 1, day flags, typed minus pooled event MASE):
  - H1 SARIMAX: negative (typed better).
  - H2 TimesFM-3: positive (pooled better).
  - H3 LightGBM with minimum leaf size 2: positive (pooled better).
- Test, decision rule and sensitivities: event_window/protocol.json (`test`, `decision`, `sensitivity`), implemented in
  src/new_states_analysis_v1.py, which is hashed in the protocol.
- Expected power (from Stage A variance components) at 45 clusters and about 5 states per cluster: about 0.9 for
  SARIMAX at the Stage A effect size.

Order of work after registration: push; OSF registration; parameter selection (select-ridge, select-tree); local
forecasts; foundation forecasts on a hosted notebook (docs/reproduction/NEW_STATES_KAGGLE.md); analysis, run once.
Every deviation is recorded in a note in this folder, and no file here is edited after registration.
