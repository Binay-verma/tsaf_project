# Text to paste into OSF (osf.io/yw7mr): "Add update" or a new linked registration

Title: Prospective follow-up: typed vs pooled festival flags on 2027-2028 festivals

Summary: After the registered new-states analysis (H1 confirmed, H2 not confirmed, H3 confirmed), exploratory analyses suggested larger typed-flag gains in states with heterogeneous festival effects (Rajasthan, Gujarat, Tamil Nadu), for ridge at lead 1 and for TimesFM-3 at leads 7 and 14. These were found after seeing the data. This follow-up tests them on festivals that have not yet occurred (calendar years 2027 and 2028), using the frozen pipeline, official government holiday notifications only, and a fixed analysis script.

Primary hypotheses (Holm, one-sided sign-flip over state-family-year units):
- P1: in Rajasthan, Gujarat and Tamil Nadu, ridge typed minus pooled lead-1 MASE < 0.
- P2: in the same states, TimesFM-3 typed minus pooled MASE (mean of leads 7 and 14) < 0.

Full protocol: https://github.com/Binay-verma/tsaf_project/blob/main/results/prospective_2027_v1/REGISTRATION_DRAFT.md
Analysis code: https://github.com/Binay-verma/tsaf_project/blob/main/src/prospective_2027_analysis_v1.py
Power note: about 80-90% at the observed (likely inflated) effects with two years; a null result is plausible and will be reported.
