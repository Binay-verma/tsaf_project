# Draft protocol: extending the festival study to ten more Indian states (not registered)

Status: **draft only**. Nothing here has been run. Registration requires every calendar entry below to be entered and checked by a person against the official document, and the source-rights question for the GRID-INDIA compilation to stay as documented in `data/external/RIGHTS_NOTICE.md`.

## Why

The main analysis has three states and two event years (10 family-year clusters), and the registered cluster tests (`results/cluster_inference_v1`) detect no typed-versus-pooled difference after Holm adjustment. More states cannot add family-year clusters (those stay at 10 until new years arrive), but they add state-level replication (13 states instead of 3, and many more family-state-year cells than the current 24) and test whether the instability seen in Delhi, Karnataka and Maharashtra appears elsewhere.

## States (fixed by an outcome-free rule)

`data_feasibility.csv` was computed from the existing source file using only missing-day counts and mean daily energy. States with at most 7 missing days in 2020–2025, mean at least 150 GWh/day and not already in the study: **UP, Gujarat, Tamil Nadu, Rajasthan, MP, Telangana, Andhra Pradesh, Punjab, Haryana, West Bengal**. The values for these states come from the same `POSOCO_data.csv` columns as the existing three, with no filling (the existing three match the source exactly).

## Calendar rule

- `calendar_entries_template.csv`: 200 rows (10 states × 4 years × 5 families). For each row, enter the date the **state government's own general-holiday notification** gives for that festival, or mark `not_a_state_holiday`. Record the document title, issuing authority, URL, page and the exact line quoted.
- A family is used for a state-year only if that state's notification lists it as a public holiday, as with Holi in Karnataka.
- `entered_by` and `checked_by` must be different people, or the same person on two separate days, with both names recorded. Machine-extracted dates are never used without this check.
- Dates are never taken from the electricity data, news articles or private calendars.

## Design (unchanged from the main study)

Same arms (calendar, zero5, typed and pooled day and window, placebos at ±28/35/42 days), same models and pinned weights, same leads (1, 7, 14), same 2024–2025 event years with 730-day context, same MASE scale and balanced hierarchy, same descriptive labels, and the registered cluster sign-flip tests with Holm adjustment, run twice: over the 10 family-year clusters (as now) and with states as the clustering unit (sign-flip over 13 state-level means). No tuning; past-only parameter selection as before. Failures and nulls are reported.

## Primary question

Is the typed-minus-pooled sign stable across 13 states, and is it the same within each of the two event years?
