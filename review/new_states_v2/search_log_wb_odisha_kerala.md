# Search log: West Bengal, Odisha, Kerala (public-holiday calendars, 2015-2025)

Written 15 November 2026. Only holiday calendars were searched. No electricity or demand data was downloaded or opened.

## Outputs
- `candidates_west_bengal.csv`: 75 rows (55 anchors + 9 Holi subsidiaries + 11 Bhratridwitiya subsidiaries)
- `candidates_odisha.csv`: 61 rows (55 anchors + 6 Holi subsidiaries)
- `candidates_kerala.csv`: 55 rows (55 anchors, no subsidiaries)

## How the evidence was read (important)
- No official State PDF was read directly. Every `quoted_line` comes from the WebFetch tool, which returns a small-model extraction of the page or PDF text, not the raw text. Lines may be paraphrased or rebuilt; each row's notes say so, and rows where the line was rebuilt from a summary sentence say that too. The author should check against the PDFs.
- `candidate_source` classes: `official` was never reached (see blocks below). `government reproduction` is used once (Odisha 2019, a district .gov.in copy of the State notification). Copies of Kerala Gazette notifications on private sites (compfie.aparajitha.com, greytHR community upload, alp.consulting) are classed `repost` conservatively, because the host is not a government domain; a reviewer who accepts a legible Gazette scan as "official" could reclassify Kerala 2021, 2023, 2024, 2025.
- Not-listed rows were decided from the extracted list, so absence is only as good as the extraction.

## Conventions used
- Anchors: West Bengal Holi = Doljatra (N.I. Act list); subsidiary = "Holi (Day after Doljatra)" (State-order list). Odisha Holi = Dola Purnima where it was declared, else Holi; subsidiary = Holi (day after) where both were declared. Dussehra = Dasami / Vijaya Dashami / Vijayadasami. Diwali: West Bengal anchor = Kali Puja, subsidiary = Bhratridwitiya (Bhatridwitya); Odisha and Kerala = Diwali/Deepavali.
- Weekend festivals, because Sundays and some Saturdays are off anyway:
  - `SUNDAY_NI_ACT` (West Bengal): the notification itself says a Sunday festival is an N.I. Act public holiday not shown in the list. The date is filled in and the tag is in notes.
  - `WEEKEND_EXCLUDED` (Odisha Annexure-III, Kerala exception list): the document says weekend festivals are not declared holidays. The date column is empty, `not_listed_this_year` = yes, and the festival date is in notes and quoted_line. If the author wants these treated as holidays, filter on this tag.
  - Where the document was not read and status is unclear, the row keeps the listed date and is tagged `UNCERTAIN`.
  - `UNRESOLVED_DATE`: two conflicting aggregator dates, date left empty without a not-listed flag (Odisha Diwali 2015 and 2016).
- "Offices closed" days in West Bengal's second notification each year (State-order closures, not N.I. Act) are used for Holi subsidiary and Bhratridwitiya; other Durga Puja and Kali Puja days are listed in notes.

## Searches run (WebSearch, standard mode)
West Bengal: "West Bengal government holiday list <year> ..." for each of 2015-2019 and a general 2024 query; wbxpress-restricted query for 2020-2022; finance.wb.gov.in-restricted query.
Odisha: general 2024 query; "holiday list 2025 / 2023 / 2022 / 2020-2021 / 2015-2019" queries; domain-restricted queries on revenue.odisha.gov.in, odisha.gov.in, finance.odisha.gov.in; follow-up queries for 2024, 2016, 2015 and 2022.
Kerala: general 2024 query; "2025", "2022", "2019 2018 2017", "2015 2016", "2024", "2023" queries; follow-up for 2017 and 2016.

## Pages fetched that gave usable list content
- West Bengal (wbxpress.com reposts): holiday-list-calender-year-2015, holiday-list-calender-year-2016, holiday-list-2017, holiday-list-2018, holiday-list-2019, holiday-list-2020, holiday-list-2021, holiday-list-west-bengal-government-employees-2022, ...-2023, holiday-list-for-west-bengal-government-employees-2024, ...-2025. Cross-check for 2023: compfie.aparajitha.com/.../211112022_LEI_02.pdf (multi-state compilation quoting West Bengal No. 4331-F(P)).
- Odisha: gconnect 2017, 2018 and 2020 pages; kendujhar.odisha.gov.in/.../2018112870.pdf (2019 State list) and .../2018112861.pdf (2019 bank list); odiaportal (2020); odishatv (2023 and 2025); ommcomnews (2025); greytHR 2021, 2022, 2024; officeholidays 2015, 2016, 2024; finance.odisha.gov.in office order 1823.pdf (2020 festival advance dates, not a holiday list); krupajal.ac.in scan of the 2025 notification (OCR partly unreliable).
- Kerala: onmanorama (2018 and 2022 lists; 2024 Mahanavami note); gconnect 2019, 2020, 2021; staffnews 2021; compfie PDFs (2021 Gazette, 2023 Gazette); greytHR-hosted Gazette PDF (2024, via S3 redirect target); alp.consulting PDF (2025); latestly (2025); simpliance 2018 PDF; officeholidays 2015, 2016, 2017.

## Blocked, gated or unusable
- Direct curl to wbxpress.com, finance.wb.gov.in and revenue.odisha.gov.in was refused by the egress proxy (403 on CONNECT, policy denial). Not retried or bypassed.
- WebFetch `robots_disallowed` (site's robots rules): finance.wb.gov.in `Holidays 2015.pdf`, `2018.pdf`, `4712-F(P2).pdf` (2025 list), `3100-F(P2).pdf` (2021 list); wb.gov.in `pdf/State Holiday 2017_eng.pdf`; revenue.odisha.gov.in individual notice pages for the 2024 and 2025 State lists. Not worked around. (Oddly, finance.wb.gov.in `4188-F(P2).pdf` (the 2026 list) and `4421-F(P2).pdf` (a 2024 poll-day order) did load on the first try; both are outside scope and were not used as evidence.)
- revenue.odisha.gov.in listing pages (`/en/communication/declaration-holidays`, `/taxonomy/term/271?page=2`, `?page=3`) load as text but show no PDF link targets, so the State lists for 2017-2021, 2023-2025 are confirmed to exist (title, date, letter number) but their PDFs were not reachable. The 2023 notice page (`/en/node/118315`) loaded but had no table.
- wbxpress.com PDF `files/2023/11/6112-F.pdf` (2024 list): premium-members paywall.
- simpliance.in Kerala 2017 and 2023 pages: PDF login-gated. Scribd pages (Odisha 2015 calendar, Kerala 2016 and 2023): wrapper text only.
- sambadenglish 2024 PDF (`cdn.thepublive.com/.../here.pdf`) returned binary and was unreadable. odishabytes 2022 article and sambadenglish 2022 article: the list is an image.
- odishatreasury.gov.in holiday page: year selector, only 2026 shown, no static data.
- dhe.odisha.gov.in node 23210 ("Implementation of Common Holiday List - 2016"): title only, PDF not available.

## Scope summary (families that are State public holidays in most years)
- West Bengal: Holi (Doljatra, every year, plus a "Day after Doljatra/Holi" State-order day in 9 of 11 years), Dussehra (Dasami, every year), Diwali (Kali Puja, every year, plus Bhratridwitiya). In scope: Holi, Dussehra, Diwali. Ganesh Chaturthi and Ugadi/Gudi Padwa: not listed in any of the 11 years (as extracted).
- Odisha: Holi (Dola Purnima and/or Holi, every year), Dussehra (Vijaya Dashami, every year; 2024 uncertain, a Sunday), Ganesh Puja (public in 10 of 11 years; 2020 fell on a 4th Saturday and was Annexure-III), Diwali (public in 6 of 11 years; 3 years weekend-excluded, 2 unresolved, 2015 and 2016). In scope: Holi, Dussehra, Ganesh_Chaturthi; Diwali is in scope in most years but weaker. Ugadi: none of 11 years.
- Kerala: Dussehra (Vijayadasami, listed in 10 of 11 years; 2024 on a Sunday, excluded) and Diwali (Deepavali, listed in 9 of 11 years; 2020 on a second Saturday and 2023 on a Sunday, excluded). In scope: Dussehra, Diwali. Holi, Ganesh Chaturthi, Ugadi/Gudi Padwa: not State public holidays in any year (2015-2017 on aggregator evidence only).

## Least certain rows
1. Odisha 2015 and 2016, all five families: officeholidays.com only, typed "Regional Holiday"; State list never located. Odisha Diwali 2015 and 2016 have no date (two conflicting dates each).
2. Odisha 2024: only a 24-row greytHR table plus officeholidays (the official 2024 list reportedly has 30 public days). Dola Purnima 25 Mar 2024 (anchor) rests on officeholidays alone. Vijaya Dashami 13 Oct 2024 is a Sunday and may be Annexure-III (undeclared).
3. Odisha 2022 Holi: only "Holi 19 Mar" in the aggregator table; whether Dola Purnima (probably 18 Mar) was also declared is unknown. Odisha 2021 and 2022 rest on greytHR only.
4. Odisha 2023 Diwali: not-listed inferred from absence (Diwali was Sunday 12 Nov 2023); Annexure-III not reproduced.
5. Kerala 2015: Vijayadasami 23 Oct 2015 (aggregator) conflicts with West Bengal's official 22 Oct 2015. The same date appears on the Odisha aggregator page. Kerala 2015-2017 are aggregator-only.
6. Kerala 2019 Deepavali (Sunday 27 Oct): gconnect's extraction places it in a table headed "Public Holidays", but similar tables in 2020, 2023, 2024 are exception lists. Flagged UNCERTAIN, date kept.
7. Kerala 2025 Holi: latestly says it is a restricted holiday; the Gazette copy lists three other restricted days. Recorded as not listed; the 14 Mar 2025 holiday applies only to Kerala offices in New Delhi.
8. Kerala 2024 Vijayadasami (Sunday, exception list): greytHR's table shows it as a public holiday; the Gazette copy puts it in the exception list. The State additionally declared Fri 11 Oct 2024 for Mahanavami. Recorded as not listed.
9. West Bengal 2015: Holi day after Doljatra (6 Mar 2015) not seen in the extraction, so no subsidiary row; 2025 and 2024 Holi coincided with Doljatra per the page's own footnote (2024 has a "Day after Doljatra" row, 2025 none).
10. West Bengal 2023 Kali Puja (Sunday 12 Nov, named only in a note) and 2019 Kali Puja (Sunday 27 Oct) and 2017 and 2021 Doljatra (Sundays): dates are filled in under `SUNDAY_NI_ACT`; the author may prefer to treat these as plain Sundays.
11. Odisha 2025 notification date: the scan OCR says 24.11.2024, the government listing says 12/11/2024 (letter 39077). The listing date was used.
12. Odisha date differences from West Bengal and Kerala for the same festival: Diwali 2018 (Odisha 7 Nov vs 6 Nov) and 2025 (21 Oct vs 20 Oct). Recorded as each state's own list says.
