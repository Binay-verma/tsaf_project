# Singapore festival replication — DRAFT, not registered, no data acquired

- Protocol draft: `DRAFT_PROTOCOL.json`.
- Code ready (data/calendar/case/feature layer): `src/singapore_replication_v1.py`, with 7 synthetic tests in `src/test_singapore_replication_v1.py`. It mirrors the NYC rules: ±3-day windows, decision leads 1/7/14 mapped to model steps 8/14/21, the 13 calendar channels and the same arms. Daily GWh are formed only from days with all 48 positive half-hours. Sunday holidays add the following Monday by rule. Placebos use a fixed shift order.
- Not done: confirmation of the real EMA and MOM file formats (the parsers fail loudly on unexpected columns); adaptation of the model runners (the NYC runners are hard-wired to 2026); registration push; any data acquisition.
- Order before any outcome: C3 metadata check → finalise and push the protocol → acquire and hash the MOM calendars → acquire EMA data → adapt the runners and run the selection fits → forecast → score.
