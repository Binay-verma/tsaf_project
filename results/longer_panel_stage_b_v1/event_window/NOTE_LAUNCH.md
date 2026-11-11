# Note: first launch of sarimax and lightgbm_capacity2 did not start (11 November 2026)

A shell grouping error started these two workers from the wrong directory. Python could not find the script and
exited with code 2 before creating anything; no `started.json` was written. Both workers were then started once, from
`src/`. Ridge and lightgbm ran from the first launch.
