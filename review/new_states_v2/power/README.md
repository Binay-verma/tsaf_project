# Power and early heterogeneity, second test (computed 15-16 Nov 2026, before registration)

No forecast and no 2021-2025 outcome of the seven new states was used.

- `power_R1_R2.csv` (src/new_states_v2_power_v1.py): resamples the FIRST test's family-year clusters into the new structure (per year: Holi 6 states, Dussehra 7, Diwali 7, Ganesh Chaturthi 1; 36 clusters). If the true effect equals the first test's, R1 passes about 18% of the time at the worst Holm level (0.0125) and 34% at the best (0.05); R2 19% and 36%. At half the effect, 5-14%. Size check at no effect: 0.6-4%. Both tests are underpowered as replications.
- `mechanism_analogue.json`: in the first test, the out-of-time analogue of M2 gives Spearman -0.91 (exact p 0.005) and M1 (Ridge, top-3 h states) p < 0.001, power about 1.0. These are optimistic: they use the states that generated the hypothesis.
- `early_heterogeneity_2015_2020.csv` (src/new_states_v2_early_h_v1.py): 2015-2020 demand only. The registered-style h divides by the mean festival effect, which is near zero in Bihar (mean log effect +0.007), so Bihar's h (2.41) is an artefact; its absolute dispersion h_abs is only 0.016. Top three by h: Bihar, Chhattisgarh, West Bengal. By h_abs: Chhattisgarh, West Bengal, Haryana. Kerala and Odisha are 0 on both (tied).
