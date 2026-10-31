# 2026 calendar entry — to be filled by a person

1. Download the 2026 holiday notification PDF for each state, from a government site if one works, otherwise a copy. Save it locally.
2. In `documents_2026.csv`, fill in one row per state: the local PDF path, the URL, the issuer, the order number, the notice date, `read_by` (your name), `read_utc` (when you read it), and `host_type` (`government` or `secondary_copy`).
3. In `entries_2026.csv`, fill in `date` (YYYY-MM-DD), `role`, `name_as_printed` and `weekday_as_printed` **from the PDF**. Add a row for each subsidiary day, for example the second Diwali day, with role `regional_subsidiary`. The `secondary_lead_unverified` column is only a hint taken from secondary copies; never copy it without reading the document.
4. Run: `python src/calendar_package_builder_v1.py build --entries review/calendar_entry_2026_v1/entries_2026.csv --documents review/calendar_entry_2026_v1/documents_2026.csv --out review/calendar_package_2026_v1 --check-issuance 0`
5. Fix anything listed under `problems`. A printed weekday that doesn't match its date is reported, not silently corrected.

Roles: `annual_as_issued_anchor` (the named festival day), `national_main` (shared main Diwali day), `regional_subsidiary` (extra days). Allowed families per state follow the 2024–2025 ledger: Delhi has Holi, Dussehra and Diwali; Karnataka has Dussehra, Ganesh_Chaturthi, Ugadi_Gudi_Padwa and Diwali; Maharashtra has all five.
