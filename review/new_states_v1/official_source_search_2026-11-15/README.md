# Search for official sources for the 241 "repost" calendar rows (2026-11-15, after the registered analysis)

Goal: find the state government's own holiday notification for each row whose current source is a secondary repost. Subagents searched year by year per state with web search and page fetching. A date counted only if it was read from a government domain, the official gazette, or a legible scan of the notification itself. The calendar used by the registered study is not changed by this search.

| State | Rows | match | differs | not_found |
|---|---|---|---|---|
| Uttar Pradesh | 44 | 0 | 0 | 44 |
| Madhya Pradesh | 44 | 0 | 0 | 44 |
| Rajasthan | 43 | 4 (2025) | 1 | 38 |
| Gujarat | 44 | 0 | 0 | 44 |
| AP, Telangana, Tamil Nadu | see found_AP_TS_TN.csv when added | | | |

## Why most rows were not found
- **Blocked portals:** the official portals refuse automated access (robots.txt). These include gad.mp.gov.in, egazette.mp.gov.in, shasanadesh.up.gov.in, gad.gujarat.gov.in, egazette.gujarat.gov.in, rajasthan.gov.in and dop.rajasthan.gov.in content pages. The web archive is also blocked.
- **Unreadable copies:** where copies of the notifications exist elsewhere, they are image-only scans (Google Drive, HR-vendor PDFs) with no readable text.
- **Text transcriptions not counted:** some text transcriptions quote notification numbers and give the same dates as ours (Gujarat 2018, 2020, 2021; Rajasthan 2022). They have no visible letterhead, so they were not counted.

## The one "differs" row
Rajasthan 2024 Diwali (row 181). A separate gazette dated 30 Oct 2024 declares 1 Nov 2024 a public holiday for Deepavali. Our row already recorded this before registration. Under convention 1 (DESIGN_DRAFT.md), the anchor is the festival day in the annual list (31 Oct), not the added day off. This is not a new discrepancy.

## What a person with a browser can do
Open the image-only notifications listed in the `attempts` and `url` columns (for example MP GAD notifications No. 450/2021, 625/2022, 389/2023, 357/2024; the Rajasthan and Gujarat 2023–2025 PDFs) and read the dates. Rows confirmed this way could support a post-hoc, clearly labelled official-source sensitivity. With only 4 rows confirmed so far, that sensitivity was not run.
