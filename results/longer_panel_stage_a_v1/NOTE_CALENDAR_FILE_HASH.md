# Note: calendar file changed after Stage A registration (11 November 2026)

`review/longer_panel_v1/calendar_entries_2014_2021.csv` is one of Stage A's hashed inputs. Commit a635090 added
`checked_by`/`check_date` to the 18 Maharashtra rows for 2017-2019 (for Stage B). No date, and no 2020-2021 row
that Stage A reads, changed. Stage A's results are unaffected, but re-running a Stage A worker from the current tree
stops at the input-hash check; check out commit b2bebc3 to re-run Stage A exactly.
