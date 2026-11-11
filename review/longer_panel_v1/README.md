# Longer-panel study (path A): event years 2016–2025 instead of 2024–2025

Step 1 (done): `data_quality_by_year.csv` shows at most 8 missing or non-positive days per state per year in 2014–2025 (2013 has 98 and is used only as context). Event years 2016–2025 give 10 years instead of 2, about 50 family-year clusters instead of 10 for the same three states.

Step 2 (in progress; needs a person): fill `calendar_entries_2014_2021.csv` (120 rows; 2022–2025 already exist in `results/calendar_semantics_v2/anchors_2022_2025.csv`). Rules:

- The date must come from the state government's general-holiday notification for that year, or from a copy that reproduces it (notification number or date visible). Record the URL, page and the exact line.
- `candidate_source` marks dates found by machine search. They are not used until `checked_by` and `check_date` are filled by a person who opened the document.
- Mark `not_listed_this_year` when the notice does not list the festival; never infer a date from the electricity data or news.

Step 3 (later): registered protocol before any new forecast; COVID years 2020–2021 declared as a sensitivity in advance; local models first, foundation models with a pretraining-exposure caveat.

## Source search result (7 November 2026)

`source_candidates.csv` lists one candidate document per state-year where an automated search found one: 16 of 24 state-years, mostly reposts of the government notification, some only news reports, and for Delhi 2014/2016 only central-government lists (a different authority). No date was taken from them: an automated reading of the 2019 Maharashtra repost gave doubtful Diwali dates, and the official government sites were not reachable from the automated environment.

Where to look first (in a browser): Maharashtra GR archive (gr.maharashtra.gov.in, search "सार्वजनिक सुट्ट्या" / "public holidays" for each year); Karnataka DPAR notifications and the Karnataka e-Gazette; Delhi Services Department / GNCTD holiday orders. Prefer the government copy; a repost is acceptable only if it reproduces the notification number and date.

## Research result (11 November 2026)

A research search filled 65 of 120 rows (`candidate_source` = "research report 11 Nov 2026", with source type). Official or government-reproduced: Delhi 2019–2020, Maharashtra 2019 (resolves the 2019 Diwali doubt: Laxmi Pujan 27 Oct 2019). Reposts with notification number and date: Delhi 2021, Karnataka 2015/2017/2020/2021, Maharashtra 2017/2018/2020/2021. Delhi 2016 and 2018 come only from the central DoPT list (different authority). Missing: Delhi 2014–2015 and 2017, Karnataka 2014/2016/2018/2019, Maharashtra 2014/2016 (2015 partial).

Feasible extensions once the rows are checked by a person:

| Stage | States | Event years | Calendar years needed | Status |
| --- | --- | --- | --- | --- |
| A (primary) | Delhi, Karnataka, Maharashtra | 2022–2025 (4 years, ~20 family-year clusters) | 2020–2025 | 2020–2021 found; 2022–2025 already in the ledger |
| B (unbalanced extension) | Maharashtra 2019–2025, Delhi 2021–2025 | per state | 2017–2021 (MH), 2019–2021 (Delhi) | found |

Conventions to keep identical to the 2022–2025 ledger (to be fixed in the protocol before any run):

1. First Diwali anchor = the national main Diwali date (as in `src/extended_validation.py` MAIN); second = the state's listed second Diwali holiday. Karnataka's own Naraka Chaturdashi date differs in 2015, 2017 and 2021 (e.g. 2021-11-03 vs 2021-11-04): pre-declared sensitivity.
2. A festival the state omits from the general list only because it falls on a Sunday or second/fourth Saturday is still flagged (the 2022–2025 ledger already flags the Sunday Diwali of 2023-11-12).
3. COVID: 2020–2021 are context years only in Stage A; Stage B event years 2020–2021 get a pre-declared sensitivity that drops them.
