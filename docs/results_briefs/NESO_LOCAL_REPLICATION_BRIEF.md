# Independent-source local checkpoint

The protocol was pushed in commit b279121 before downloading the target series. A new NESO England/Wales snapshot yields 1,369 complete daily observations from January 2023 through September 2026. Official documentation defines half-hour average MW; daily GWh sums actual periods and divides by 2,000, respecting 46/48/50-period daylight-saving days. Complete raw/derived source files remain outside GitHub while the custom licence body is unverified.

All 3,072 local forecasts (four variants × eight arms × 48 cases × two availability scenarios) and 192 fixed naive forecasts are complete. A separate internal audit reconstructs raw integration, recorded labels, scales, all 72 past-only selection fits’ input bytes, 192 regression refits’ train/query bytes, parameters, SARIMAX deployment dates and scalar metrics. It passes. It is not external human review or full independent model reimplementation.

Calendar/history-only MASE, lower is better:

| model | ideal, lead 1 | ideal, lead 7 | ideal, lead 14 | lag21, lead 1 | lag21, lead 7 | lag21, lead 14 |
| --- | --- | --- | --- | --- | --- | --- |
| last | 0.87217 | 0.62361 | 0.33376 | 1.36618 | 1.0862 | 1.12758 |
| lightgbm | 0.53385 | 0.42412 | 0.39583 | 0.46448 | 0.56322 | 0.47832 |
| lightgbm_capacity2 | 0.55685 | 0.43344 | 0.39421 | 0.47201 | 0.54119 | 0.48525 |
| ridge | 0.48703 | 0.45774 | 0.51523 | 0.50152 | 0.66165 | 0.5977 |
| sarimax | 0.4808 | 0.44528 | 0.43025 | 0.46981 | 0.48435 | 0.50267 |
| seasonal | 0.62361 | 0.62361 | 0.33376 | 1.0862 | 1.0862 | 1.12758 |

Each cell uses the same 16 target dates, 15–30 September 2026. “lag21” removes 21 additional calendar days of observations: decision leads 1/7/14 require actual model steps 22/28/35. These are revised historical snapshots, not reconstructed first releases or actual historical issuances. A delay need not worsen every score in this short dependent sample. The full foundation comparison remains queued.

All typed/pooled/day/window/zero/placebo results, including deteriorations, are retained in the checkpoint CSVs. Added holiday features have mixed ordinary-day effects. There are no holiday target dates, so this does not establish independent festival gains. No parameters are selected on these September outcomes.

Execution notes: an unmatched parenthesis was corrected before scoring registration could be created. The separate audit initially did not parse the provider’s old “01-Jan-23” format; explicit standard-library date formats were added, preserving forecasts and analysis outputs. The completed audit passes without loosening tolerances. A report-only pandas Markdown call lacked the optional tabulate package; the existing dependency-free table helper was used instead. No old Indian data, future forecasts, annex or disabled workflow was changed.
