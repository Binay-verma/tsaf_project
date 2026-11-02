# Regional calendar audit

The expanded ledger compares every distinct named general-holiday date in the selected annual government-office schedules for Karnataka, Delhi and Maharashtra, 2022–2025 (12 state-years), with the default PUBLIC-category calendar previously used. Named events omitted from printed rows because they fall on existing weekly closures are included; ordinary Sundays/second/fourth Saturdays are not individually labelled as festivals. Bank-only account-closing holidays and optional/restricted leave are excluded. Additional listed statewide government-office holidays are included.

Evidence consists of government notifications, official department-hosted copies and government-authored notifications preserved by mirrors. `evidence/calendars/` retains downloaded PDFs and extracted/OCR text where available. Some official sites failed direct downloads; their publicly indexed documents and exact URLs are recorded. Karnataka 2023 is preserved from the public government-notification PDF linked by the notification transcription, and its English annual table was visually checked. Mirrors are identified as such rather than represented as official hosts.

The table is in `results/extended_validation/regional_calendar_summary.csv`; the individual dates and source URLs are in `regional_calendar_date_audit.csv`. A discrepancy means a difference against the chosen government-office schedule, NOT necessarily an error in the library's own PUBLIC-category definition.

## Important distinctions

- Delhi's main Diwali dates are 31 October 2024 and 20 October 2025.
- Maharashtra lists Lakshmi Pujan on 1 November 2024 and 21 October 2025, with Bali Pratipada the following day.
- Karnataka lists Naraka Chaturdashi and Balipadyami/Deepavali separately; relevant 2024 dates are 31 October and 2 November, and 2025 dates are 20 and 22 October.
- The original PUBLIC-category flag therefore must not be described as a fully verified state-government closure calendar. Changing the category alone is also insufficient: the installed library returned no GOVERNMENT-category dates for these historical state-years. That observation is recorded separately.

## What is verified and what is not

The ledger audits the annual publications as issued. It does not reconstruct every later amendment, local/district holiday, emergency closure, election holiday or actual moon-sighting observance. Examples that need amendment-aware treatment include Karnataka's 2023 Mahavir date and Maharashtra's 2023 Bakrid date; the original publications and later observance dates can differ. These differences remain visible instead of being silently resolved by model error.

The expanded primary forecast comparison therefore isolates ordinary calendar features and explicit Diwali windows rather than feeding an uncertified generic state-holiday flag. The explicit main Diwali anchors for 2020–2025 and the separately listed 2022–2025 regional Diwali dates are retained, with sources. The window is a union of +/-3 days around the national/main anchor and declared regional Diwali dates, fixed without using electricity outcomes. This is a deliberate broad Diwali-period definition, not a claim that every date is the same religious observance.

Full amendment-aware certification of every historical calendar date, including all prior training years, remains incomplete. Do not describe the whole project as having solved that problem. All inputs actually added to the expanded festival feature are explicit dated anchors rather than an unverified catch-all holiday flag.

## Principal sources

- Delhi official annual schedules: https://delhi.gov.in/sites/default/files/documents/Gazzeted_holiday_2022.pdf ; https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holiday_list_2023_1.pdf ; https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holidays_2024_gnctd.pdf ; https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holiday_list_2025.pdf .
- Maharashtra annual state notifications: https://www.maharashtra.gov.in/site/Upload/pdf/PUBLIC_HOLIDAY_2023.pdf ; https://www.maharashtra.gov.in/site/Upload/pdf/Public_Holidays_2024.pdf ; https://www.maharashtra.gov.in/site/Upload/pdf/Maharashtra_Holiday_2025.pdf . The 2022 notification is preserved via the FIMMDA-hosted government gazette copy identified in the ledger.
- Karnataka government notification identifiers: DPAR 37 HHL 2021 (2022), DPAR 16 HHL 2022 (2023), DPAR 16 HHL 2023 (2024), DPAR 16 HHL 2024 (2025). Exact copies/transcriptions are linked in the ledger.
- Main anchors in earlier training years: https://www.lpsc.gov.in/holidaysBangalore2020.html and https://www.lpsc.gov.in/holidaysBangalore2021.html .
