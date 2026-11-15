# Search log: Punjab and Haryana holiday candidates (2015-2025)

Output files: candidates_punjab.csv, candidates_haryana.csv (66 rows each = 55 anchor rows + 11 Vishwakarma Day regional_subsidiary rows). No electricity or demand data was touched.

## Method and limits
- Tools: WebSearch and WebFetch only. WebFetch returns a model-summarised view of a page, not raw text, so every quoted_line is "as extracted by the tool". Numbers and dates were weekday-checked in code (a date whose weekday disagreed with the source's stated weekday would have failed the build).
- No row has candidate_source = official. No state-government PDF (punjab.gov.in, haryana.gov.in, csharyana.gov.in, e-gazette) could be opened with its text. The best evidence is a repost that reproduces the notification text (simpliance.in PDFs, archive.org scan, gconnect.in, staffnews.in, Tribune, Statesman) and, for several years, only aggregators (officeholidays.com, greythr).
- The Punjab and Haryana High Court calendars (highcourtchd.gov.in, cdnbbsr.s3waas.gov.in) were used only as a cross-check and are named in notes. They are court lists, not the state notification, and they differ from the state lists in some years (e.g. Holi 2023-03-07 vs 2023-03-08; Punjab Dussehra 2018). I did not label any row "government reproduction" for that reason.

## Searches run (summary)
- "Punjab/Haryana gazetted holidays <year> list notification", Hindi queries ("राजपत्रित छुट्टियां", "सार्वजनिक अवकाश" + year), "Public holidays in the public offices under the Haryana Government ... Calendar Year <year>", Punjab Department of Personnel / Good Governance and IT notification, amendment searches (Diwali holiday change 2024 and 2025), Tribune/Statesman/Sakshi news reposts. Hindi queries returned only election-holiday and generic aggregator pages.
- Fetched: officeholidays (Punjab 2016, 2017, 2020, 2024, 2025; Haryana 2016, 2018, 2019, 2023, 2024, 2025), greythr wiki (Punjab 2021, 2022, 2024; Haryana 2022 to 2025), thecurrentindia (Punjab 2023), simpliance PDFs (Punjab 2018, 2019), archive.org scan (Punjab 2015), gconnect (Haryana 2017, 2020; Punjab NI Act 2018, 2019), staffnews (Haryana 2021), Tribune (Haryana 2015, 2024 Diwali amendment, Dec 2024 list), Statesman (Haryana 2018, 2024 Diwali), Sakshi Post (Punjab and Haryana 2025), ascent-hr (Haryana Diwali amendment), cag.gov.in Punjab list page (shows 2026 only, out of scope), High Court calendars 2018, 2019, 2020, 2023, 2024.

## Blocked or unusable sources
- Direct curl through the agent proxy was refused (403 CONNECT policy denial) for cag.gov.in, officeholidays.com, punjab.gov.in, haryana.gov.in, cmo.punjab.gov.in, haryanahrms.gov.in and highcourtchd.gov.in. I did not retry or route around this; WebFetch was used instead.
- WebFetch worked for punjab.gov.in/impnotifications/page/9/ but returned metadata only: it confirms an official "List of Holidays - 2023" (Good Governance and Information Technology dept., published 14-12-2022, 3.06 MB PDF) and gives no download link. The PDF itself was not read.
- Blocked or empty: taxheal.com (bot check; this is the likely repost of the Punjab 2017 list), scribd.com (no document text, so the Haryana "public_holidays.pdf" and MDU Rohtak "rev holidays 2019" could not be read), web.archive.org (site blocked), complinity.com (Haryana 2019 text paywalled), teamleaseregtech.com (Haryana 2024 notification attached, text not shown), highcourtchd.gov.in 2017, 2021 and 2022 PDFs (robots_disallowed), csharyana.gov.in listing pages (no holiday entries), gmch.gov.in (Chandigarh UT, not relevant).
- Claude in Chrome had no connected browser, so no real-browser fallback was possible.
- Several compfie.aparajitha.com PDFs surfaced by search turned out to be Haryana election-holiday notifications or Himachal Pradesh lists; they were not used.
- cleartax.in's Punjab 2025 page contradicts itself (Diwali 31 Oct, Holi 8 March) and was ignored.

## Scope by state
Punjab (state lists even weekend-coinciding festivals as holidays):
- In scope as gazetted nearly every year: Holi, Dussehra, Diwali, and Vishwakarma Day (day after Diwali; gazetted every year seen except 2018, where it is restricted, and 2017, where nothing was found).
- Out of scope: Ganesh_Chaturthi and Ugadi_Gudi_Padwa are never gazetted in any list I could read (2015, 2018, 2019, 2023 full or partial lists; the 2026 central list shows them only as restricted). For other years the evidence is absence from aggregator pages only.
- No separate Holika Dahan holiday; Hola Mohalla appears as a restricted holiday (2015, 2018, 2023) and is not recorded.

Haryana (Schedule I excludes festivals that fall on Saturday or Sunday, but names them in a note in some years):
- In scope: Holi, Dussehra, Diwali, Vishwakarma Day (as subsidiary), gazetted in every year where the day was a working day.
- Out of scope: Ganesh_Chaturthi and Ugadi_Gudi_Padwa, absent from the full Schedule I and II texts read for 2017, 2020 and 2021, and from all aggregator lists. Govardhan Puja is a restricted holiday (2017, 2020, 2021, 2025 per Sakshi) and is not recorded as a subsidiary row.

## Rows I am unsure of (all in the CSV notes)
Punjab:
- 2017 Holi: no date. No usable source (officeholidays shows only Doljatra 12 March; taxheal blocked).
- 2017 Diwali subsidiary (Vishwakarma Day): no date, no source.
- 2017 Dussehra: aggregator says 2017-09-29, but Haryana's 2017 notification and the national date point to Saturday 2017-09-30.
- 2016 (all families) and 2020, 2021, 2022, 2024, 2025 Holi/Dussehra: aggregator-only; gazetted status not verified.
- 2023 Diwali: the repost's text reads "121th November"; 12 Nov used, supported by other sources.
- 2018 Dussehra: Punjab list says 2018-10-19; the court calendar says 2018-10-18.
- 2018 Vishwakarma Day: restricted, so date empty.

Haryana:
- 2024 Dussehra (Sat 2024-10-12) and 2024 Vishwakarma Day: marked not listed because greythr's list omits them and Haryana excludes closed-day festivals; notification not read, so this may be wrong.
- 2024 Diwali: amended. Original 2024-11-01 (Diwali/Haryana Day); Chief Secretary order of 22 Oct 2024 moved it to 2024-10-31; final date used.
- 2016: aggregator only; Vishwakarma Day 2016-11-01 looks suspect (Punjab 2016-10-31); Diwali 2016-10-30 is a Sunday.
- 2018: Statesman repost with no printed date; Dussehra 2018-10-18 vs officeholidays 2018-10-19; Vishwakarma Day 2018-11-09 vs court calendar 2018-11-08.
- 2019: aggregator only; Diwali 2019-10-27 is a Sunday.
- Weekend-coincident rows (2017 Dussehra, 2020 Dussehra, Diwali, Vishwakarma Day): the date comes from a note in the notification, not Schedule I, so these are flagged "WEEKEND_COINCIDENT_NOTE_ONLY" in notes. 2023 Diwali (Sunday) is listed by the aggregator.
- 2022, 2023, 2025: aggregator or news repost only; 2025 Dussehra is listed jointly with Mahatma Gandhi Jayanti.

## Convention used
- date filled if a source names the date; not_listed_this_year = "yes" only where the state list (or best available list) omits the family or classes it as restricted.
- candidate_source records the weakest tier actually used for that row; where a news repost corroborated an aggregator date the row is labelled repost and the aggregator is named in notes.
