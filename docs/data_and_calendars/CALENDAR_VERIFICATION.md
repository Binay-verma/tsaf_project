# Calendar verification and feature definitions

Verified on 29 October 2026 from primary government pages:

| Event | Date | Evidence | Scope |
|---|---|---|---|
| Main Diwali 2022 | 24 October 2022 | https://www.lpsc.gov.in/holidaysBangalore2022.html | LPSC Bengaluru institutional holiday list |
| Main Diwali 2023 | 12 November 2023 | https://www.lpsc.gov.in/holidaysBangalore2023.html | LPSC Bengaluru institutional holiday list |

Both match the generated main Diwali dates used in the experiment. These institutional lists corroborate main festival dates; they do not verify every historical holiday in all three states or establish a uniform regional electricity response.

Modes:

- A: target history only.
- B: A plus target-date weekday and three annual sine/cosine harmonics.
- C: B plus state public-holiday flag generated with the recorded `holidays` package version.
- D: C plus seven separate binary indicators for the target date lying -3 to +3 days relative to the main Diwali day. Subsidiary Diwali-labelled holidays do not create additional anchors in this benchmark.

The earlier `run_pilot.py` used all Diwali-labelled holidays for exploratory windows. That earlier output remains unchanged. The new benchmark uses the single main-day definition above, so do not merge those two result tables.

Future calendar inputs are allowed because event dates can be known before a forecast is issued. Historical library corrections and holidays announced at short notice may violate a strict as-of-date information assumption. This experiment does not reconstruct historical announcement snapshots, so that aspect remains a limitation.

No target-dependent festival window selection was performed. All three states use the same +/-3-day main-event window; broader festivals, regional effects and window tuning can be explored only in a separately declared development experiment.
