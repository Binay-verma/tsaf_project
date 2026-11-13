# New-states confirmatory study: design draft (not registered)

Status: DRAFT for discussion with the supervisor. Nothing here is registered. No forecast for any state below has been
made or inspected in this project. Registration happens only after every calendar row is checked by a person, and is
committed, pushed to GitHub and timestamped on OSF before any parameter selection or forecast.

## Why

The v9 results that a referee would question are: the confirmed SARIMAX result rests on one state and 15 clusters;
the TimesFM-3 pooling result was never registered; the LightGBM hypothesis could not be tested because the selected
trees could not split on rare flags; the registration had no external timestamp. This study addresses all four.

## Hypotheses (to be fixed at registration)

At lead 1, day flags, typed minus pooled event MASE (balanced over states within each family-year cluster):

- H1: SARIMAX(1,0,0)(1,0,0,7): negative (typed better).
- H2: TimesFM-3 (pinned weights as in v9): positive (pooled better).
- H3: LightGBM with minimum leaf size fixed at 2 (so rare flags can be split): positive (pooled better).
- Reported, not tested: Ridge, Chronos-2, stable LightGBM.

Test: exact one-sided sign-flip test over family-year clusters (Monte Carlo with 10^6 sign draws if more than 24
clusters), Holm across H1-H3, alpha 0.05; a hypothesis is confirmed only if, in addition, its sign holds in at least
two thirds of event years. Pre-declared sensitivity: 2020-2021 removed (COVID).

## Data

States not used anywhere in the study so far: Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat, Telangana,
Andhra Pradesh, Tamil Nadu. Same source (GRID-INDIA/POSOCO compilation), energy met (GWh). Completeness 2015-2025:
at most 8 bad days per state-year (2015), 0-1 from 2017; Telangana starts June 2014.

Event years 2017-2025 (nine years). Calendar years 2015-2025 (training history needs two prior years).
Festival families: the same five as the main study (Holi, Ugadi/Gudi Padwa, Ganesh Chaturthi, Dussehra, Diwali with
a state-listed second day), each used only in the states whose notification lists it.

Up to 5 x 9 = 45 family-year clusters, with 3-7 states per cluster.

## Power (from Stage A variance components)

Stage A, SARIMAX, lead 1: cluster-level SD 0.0565 with 2.4 states per cluster; within-cluster state SD 0.0571;
implied between-cluster SD about 0.043. Assuming the Stage A effect (-0.027 per state), one-sided alpha 0.0125
(Holm, three hypotheses), approximate power:

| Clusters | 2.4 states per cluster | 4 states | 6 states |
| --- | --- | --- | --- |
| 20 | 0.45 | 0.53 | 0.59 |
| 30 | 0.64 | 0.73 | 0.78 |
| 40 | 0.78 | 0.85 | 0.89 |
| 50 | 0.87 | 0.93 | 0.95 |

Stage B (15 clusters, one state) had roughly 0.3-0.45 power. With about 40 clusters and four or more states the
study has roughly 0.85 power for SARIMAX; TimesFM-3 (Stage A effect +0.051) needs fewer clusters.

## Calendar work

About 7 states x 11 years x 4-6 rows = 300-400 rows, sourced with document links by Claude and checked by the
author, as for the Maharashtra rows. Rows are refused by the code until checked.

## Open decisions for the supervisor

1. Data reuse terms of the compilation (or rebuild from the official GRID-INDIA daily reports).
2. Whether to register on OSF in the author's name.
3. Whether seven states and nine event years is the right scope for the time available.
