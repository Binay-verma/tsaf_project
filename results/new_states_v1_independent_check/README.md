# Independent recomputation of the registered analysis

A separate agent wrote `indep.py` from the registration text only (REGISTRATION.md, OSF_REGISTRATION.md, protocol.json). It did not open src/new_states_analysis_v1.py or the analysis outputs until its own numbers were written. It verified all 8 predictions.csv hashes against run.json.

## Results
- **Effects, year means, years-in-direction, cluster counts and decisions:** identical (effects to about 1e-16) for the main analysis and both registered sensitivities.
- **p-values:** differ by at most 0.0012, from Monte Carlo noise: same draw count and seed, but a different way of drawing signs. One Holm value differs by 0.0026 (official-only H1, three times the raw-p noise). No decision is near a threshold.

## Choices the registered script made where the text was not explicit
- **7-year sensitivity:** years-in-direction uses ceil(2/3 × years), so 5 of 7, following DESIGN_DRAFT.md. This changes no outcome.
- **Official-only filter:** works on state-family-year cells.

## Documentation error found
NOTE_RUN.md said the official-only filter removes every row for Andhra Pradesh and Madhya Pradesh. It does not. In 2017–2025 the retained cells are Telangana 38, Tamil Nadu 36, Andhra Pradesh 9 and Madhya Pradesh 2. Gujarat, Rajasthan and Uttar Pradesh are fully removed. See analysis/NOTE_RUN_ERRATUM.md. The numbers were always correct.
