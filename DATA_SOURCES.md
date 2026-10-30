# Data selection update — 29 October 2026

## Decision
Keep the original CC BY 4.0 state-level dataset as the reproducible pilot. Add Robbie Andrew's GRID-INDIA/POSOCO compilation as a separately audited candidate for newer evaluation. Do not splice the two sources silently or call SASEA an independent dataset. No new model results were generated during this data-search stage.

| Source | Coverage verified from downloaded bytes | Resolution / geography | Decision |
|---|---|---|---|
| Hunt & Bloomfield, DOI 10.5281/zenodo.14983362 | 2013-01-01 to 2024-04-28 | Daily energy supplied, states | Existing pilot; CC BY 4.0 |
| Robbie Andrew, GRID-INDIA/POSOCO compilation | 2013-01-02 to 2026-10-28; 5,048 rows, 144 columns | Daily; state energy met plus regional power/energy fields | Strong candidate for 2024–2025 complete-year evaluation; licence and processing policy need verification |
| Coombes, Hunt & Bloomfield, DOI 10.5281/zenodo.17175212 | Indian aggregate: 2013-01-01 to 2024-04-28, despite multi-country catalogue title ending 2025 | Daily national series in MWh | Supplement only; 3,900 comparable totals match existing pilot source after unit conversion; 55 repeated date rows remain |
| Mukherjee et al., DOI 10.17632/y58jknpgs8.2 | Not verified: catalogue title says September 2021–June 2025, description says September 2021–December 2023 | Hourly national aggregate | Candidate only; programmatic metadata request returned HTTP 403 |
| AGMARKNET, Government of India | Historical bytes not acquired or audited | Daily market/commodity prices and arrivals | Second-domain candidate; not ready for model evaluation |

## Downloaded files

`data/external/POSOCO_data.csv` and `POSOCO_metadata.json` are an unchanged snapshot and field dictionary. `latest_state_energy_GWh.csv` extracts Karnataka, Delhi and Maharashtra energy-met columns with original values; no filling, smoothing or source merging. Metadata explicitly gives GWh for these fields.

`data/external/sasea_data.zip` is the original 15.2 MB source archive, verified against repository MD5 `22921011c0fdabea0df5f926f3372a9e`. Indian CSV/YAML files are extracted separately, with national aggregates and source gap/statistics tables retained. The raw Indian table must not be assumed to use the same variable or units as the national daily-energy aggregate; consult YAML metadata.

`results/data_search/` contains the audit, annual state coverage, source-overlap differences and SHA-256 inventory. Reproduce with `python src/audit_sources.py`.

## What the newer data enables

For Karnataka, Delhi and Maharashtra, all 366 days in 2024 and all 365 days in 2025 have positive recorded energy-met values. The partial 2026 file contains 301 days through 28 October. Complete calendar entries do not establish that every value is independently observed: source filling, corrections, reporting-day alignment and anomaly handling still need checking.

Use 2024 as an additional development/sensitivity period and reserve full-year 2025 for evaluation only after freezing the protocol. This proposed extension does not change the existing reserved 2023 test automatically. No 2025 scores have been calculated. A newer test year is not automatically beyond the model's pretraining cutoff; verify the selected checkpoint's training disclosures first.

The two state sources differ numerically on some overlap dates (see `source_overlap.csv`). Compare their report-date conventions, rounding and corrections before deciding to replace the pilot. Fit and evaluate within a single source for primary comparisons.

## Attribution and reuse

Original pilot: Hunt & Bloomfield (2025), *Daily electricity demand data for Indian states (2014–2024)*, https://doi.org/10.5281/zenodo.14983362, CC BY 4.0.

SASEA: Coombes, Oliver G.; Hunt, Kieran; Bloomfield, Hannah (2025), *SASEA Electricity Demand Data for 2013–2025*, v1, https://doi.org/10.5281/zenodo.17175212, CC BY 4.0 per repository API metadata. Indian aggregates are converted to MWh in the source archive; this project does not treat them as new independent observations.

Newer compilation: Andrew, R., *Indian Energy and Emissions Data*, https://robbieandrew.github.io/india/, snapshot retrieved for this project on 29 October 2026. Underlying reporting organisation: GRID-INDIA/POSOCO. URLs: https://robbieandrew.github.io/india/data/POSOCO_data.csv and https://robbieandrew.github.io/india/data/POSOCO_metadata.json . No explicit dataset reuse licence was located on the inspected landing page or metadata. Retain attribution and resolve reuse terms before public redistribution; current snapshot is for private project inspection.

Hourly candidate: https://data.mendeley.com/datasets/y58jknpgs8/2 . AGMARKNET candidate: https://data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi . These candidates were located, not downloaded successfully.

## Immediate next build tasks

1. Resolve newer source processing/licence and reporting-day alignment; inspect overlap discrepancies.
2. Audit official state festival dates against generated flags.
3. Build a source-selectable loader and matched model/feature comparisons; preserve original pilot reproducibility.
4. Run Chronos-2 comparisons and 7/14-day horizons on development data before any new holdout scoring.
