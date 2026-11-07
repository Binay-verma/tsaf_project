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
