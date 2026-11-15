# Search log: Bihar and Chhattisgarh public-holiday candidates (2015-2025)

Written 15 Nov 2026. Only holiday calendars were looked at. No electricity or demand data was opened. No git commands were run.

## Result in one line
No official state document could be read for any year. Every row rests on a repost (news or employee-info site quoting a list) or an aggregator. Official PDFs exist but were blocked, scanned without a text layer, or behind a login.

## What was searched (WebSearch, English and Hindi)
- "Bihar government general administration department holiday list <year> Holi Dussehra Diwali Chhath gazetted", repeated for 2016, 2017, 2018, 2019, 2021, 2023 (with "gad.bih.nic.in", "Negotiable Instruments Act")
- Hindi: "बिहार सरकार ... अवकाश तालिका ... सामान्य प्रशासन विभाग", "छत्तीसगढ़ शासन सामान्य प्रशासन विभाग सार्वजनिक अवकाश <year>", "छत्तीसगढ़ ... दीपावली अवकाश 2025". One Bihar Hindi query was refused by the tool permission layer and was re-run with other wording.
- "Chhattisgarh government holiday list <year> ..." for 2015, 2016, 2017, 2018, 2019, 2022, 2025
- Domain-restricted searches (nic.in, gov.in, cg.gov.in) for Bihar and Chhattisgarh lists
- Targeted checks: Bihar Durga Puja 2024, Bihar Holi 2024, Chhattisgarh Diwali 2025, Chhattisgarh Govardhan Puja

## Pages that gave usable text (all non-official)
- officeholidays.com state pages: Bihar 2015-2018, Bihar 2019 (cross-check), Chhattisgarh 2015, 2016, 2018, 2019. Weakest: no data source named, only "Regional Holiday" labels, and the Bihar and Chhattisgarh pages for 2015 and 2016 returned identical festival rows (looks like a generic list).
- Atulya Bihar blog (Bihar 2019)
- Simpliance holiday-list pages: Bihar 2020, Bihar 2025, Chhattisgarh 2020, Chhattisgarh 2025 (82 rows, general and optional mixed, types Regional/National/Optional)
- greytHR wiki: Bihar 2021, 2022, 2023, 2024 (cross-check); Chhattisgarh 2021 (cross-check), 2022, 2023, 2024, 2025. Claims "sourced and verified from official notifications" but names no notification.
- Pratidin Time (Bihar 2024 list), Patna Press (quotes Bihar "official calendar" Holi Mar 26-27 2024), TheCurrentIndia (Bihar 2024; Bihar 2026 page also seen)
- indianemployees.com Bihar circulars: titles and numbers for the 2024, 2025, 2026 lists and for the Diwali 2025 amendment (19026, 19025, 19065). Used for the Bihar 2025 Diwali row.
- GConnect and TaxHeal (Chhattisgarh 2017 list; TaxHeal splits General and Optional)
- indiacustomercare.com (Chhattisgarh 2021 General and Optional tables)
- The Hitavada (Chhattisgarh Govardhan Puja bank holiday, 1 Nov 2024), Business Standard (Diwali 2025 bank holidays by state), Digiliance, IndiaObservers (Chhattisgarh 2025)
- Not used for dates because garbled: Sakshi Post "Bihar Government Holidays 2025" (wrong dates, e.g. Vijaya Dashami Oct 23) and greytHR Bihar 2025 (wrong weekdays, 16 rows). Noted in the Bihar 2025 rows.

## Official sites blocked or unreadable
- gad.bih.nic.in: robots_disallowed
- state.bihar.gov.in/gad/ home page: fetched but had no holiday links; the GAD PDF the TheCurrentIndia page cites (state.bihar.gov.in/gad/cache/4/29-Sep-21/SHOW_DOCS/11265 (3).pdf): robots_disallowed
- cg.gov.in, gad.cg.gov.in/ias/Reports/Calender.aspx, raigarh.gov.in (local holidays 2025): robots_disallowed
- Bihar 2023 official PDF (datocms-assets.com .../1666084110-bihar-state-list-of-holidays-2023_compressed.pdf): fetched, no text layer (scan)
- Chhattisgarh 2025 official PDF (datocms-assets.com .../1733654931-chhattisgarh-state-list-of-holidays-2025.pdf): no text layer
- Simpliance notification PDFs for Chhattisgarh 2023, 2024, 2025: "Login to Download"
- Bihar 2024 and 2025 list PDFs held on Google Drive (via indianemployees.com circulars 16953 and 15764): viewer page only, no text
- Direct curl to the datocms PDF: proxy returned 403 (not pursued further)
- greytHR 2019 and 2020 pages for both states: client error
- A government site that did load: ngdrs.cg.gov.in holidaylist.pdf (Chhattisgarh Registration dept). It is the central government 2021 gazetted/restricted list (17 + 34), not the state list, so it was used only as a cross-check for Chhattisgarh 2021 and mentioned in the notes.

## Scope summary (what looks like a public holiday in most years)
Bihar
- Holi: yes, every year, normally two days (anchor = first listed day, second day as subsidiary row; 2015-2017 only one day was visible, so no subsidiary row).
- Dussehra (Vijaya Dashami): yes, every year, inside a block of Durga Puja holidays (usually Maha Asthami/Navami/Vijaya Dashami; the other days are in the notes).
- Diwali: yes, every year (2025 moved from Oct 22 to Oct 20 by GAD notification). Chhath, 2 days, is also public most years (notes only). Bhai Dooj/Chitragupt appears in only 2019, 2024 (one source) and 2025 (subsidiary rows).
- Ganesh Chaturthi: not a public holiday in any list read (one 2025 article puts it in the Restricted list).
- Ugadi/Gudi Padwa: not in any Bihar list read.

Chhattisgarh
- Holi: yes, one day, every year.
- Dussehra (Vijaya Dashami): yes, one day, every year (Maha Ashtami and Maha Navami are Optional where split lists were seen: 2017, 2021).
- Diwali: yes, one day, every year. Chhath is also on the list most years (notes only). Govardhan Puja and Bhai Dooj are Optional (2017, 2021; 2026 notice says Govardhan changed from Optional to public in 2026, outside the range). One subsidiary row for 1 Nov 2024 (Govardhan Puja, NI Act bank holiday, low confidence).
- Ganesh Chaturthi: Optional in 2017 and 2021 (explicit), absent elsewhere; treated as not public.
- Ugadi/Gudi Padwa: Optional in 2017 and 2021 (as "Gudi Parva/Chaiti Chand" or "Gudi Padva/Chaitichand/Vaishakhi"); absent elsewhere; treated as not public.

## Rows I am unsure of (author should check first)
1. Bihar Holi 2017 (Mar 14 vs Mar 13; aggregator shows Doljatra Mar 13). Chhattisgarh reposted state list gives Mar 13.
2. Bihar Holi 2019 (Mar 22 labelled Holi with Doljatra Mar 21; main colour day may be Mar 21).
3. Bihar Holi 2024 (Mar 26 and 27 per three sources and a news quote of the official calendar, but colour day in much of India was Mar 25).
4. Bihar Dussehra 2020 (Oct 26 on Bihar page; Chhattisgarh 2020 gives Oct 25).
5. Bihar Dussehra 2024 (all sources label Oct 12 "Maha Navami"; Vijaya Dashami was most likely Oct 12 but the label does not say so).
6. Bihar Dussehra 2025 (Durga Puja rows Sep 29 to Oct 3, none labelled Vijaya Dashami; Oct 2 chosen).
7. Bihar 2015 and 2016, Chhattisgarh 2015, 2016, 2018, 2019: generic officeholidays rows, no state document seen, Bihar and Chhattisgarh pages identical.
8. Chhattisgarh Diwali 2025 (Oct 20 per three lists; Oct 21 per one page and banks closed on both days).
9. Chhattisgarh Ganesh Chaturthi and Gudi Padwa 2025 (on the Simpliance combined list, with no general/optional label).
10. Chhattisgarh Govardhan Puja 2024 subsidiary row (NI Act bank holiday only) and Bihar Chitragupt/Bhai Dooj rows for 2024 (one source) and 2025 (aggregator list that mixes restricted days).
11. All "not listed" rows for years where only an aggregator list was read; no optional/restricted table was available to confirm the status, except Chhattisgarh 2017 and 2021.

## Conventions used
- quoted_line is from WebFetch tool extraction (a summarising model), not from reading the page image or PDF. Some Hindi or longer quotes are shortened by the tool.
- candidate_source classes used: repost and aggregator only. There are no official or government-reproduction rows and no "none" rows.
- Dates are as the source printed them. Where a source's date conflicts with the usual festival date, this is flagged in notes and not corrected.
- Most Bihar aggregator pages do not separate gazetted from restricted days. Holi, Durga Puja and Diwali are treated as public because they sit in the main list of those pages (restricted days such as Holika Dahan were shown separately where an optional table was seen, e.g. Bihar 2024 on TheCurrentIndia). A typed public/restricted table was seen only for Bihar 2024 and 2025 reposts, so this is not confirmed for other years.
