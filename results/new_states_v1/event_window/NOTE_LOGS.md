# Note: two worker logs written outside the folder (13 November 2026)

A shell grouping error sent the execution logs of the lightgbm and lightgbm_capacity2 workers to the filesystem root
instead of this folder. Both workers ran once, from src/, and completed; the logs were moved here unchanged after
completion. No forecast is affected.
