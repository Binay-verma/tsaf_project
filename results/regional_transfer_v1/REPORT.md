# Regional regression transfer v1

162 fixed Ridge fits, 53,622 predictions, six configurations, 8,937 matched cases each.
Alpha=10 is fixed, with no held-out-region tuning. All fitting labels predate each evaluation year.
Three arms share features and dates: target-region local fitting, pooled fitting including the target,
and regression fitting on the other two states only. Source-fitted StandardScaler and coefficients in
the last arm never use target-region rows. Tests explicitly perturb the held-out region and verify
source coefficients and scaler do not change; future-year perturbations cannot change fits/normalizers.

**This is not geographic cold start.** Target-region observed history and a fixed pre-year mean/std are
allowed context/normalization. Scaling parameters use only recorded values before the held-out year.
The sources and target are all from the same compilation; this is not independent dataset replication.
The forward-held-out year is never pooled into training. No future-year leave-one-year-out leakage is used.

## Equal-state macro MASE

| year | mode | arm | 1 | 7 | 14 |
| --- | --- | --- | --- | --- | --- |
| 2024.0000 | rich_calendar | leave_region_out | 0.4273 | 1.0766 | 1.4285 |
| 2024.0000 | rich_calendar | local | 0.4063 | 0.9782 | 1.0972 |
| 2024.0000 | rich_calendar | pooled_all | 0.3846 | 0.8949 | 1.0884 |
| 2024.0000 | rich_regional | leave_region_out | 0.4247 | 1.1048 | 1.4436 |
| 2024.0000 | rich_regional | local | 0.3992 | 0.9726 | 1.0983 |
| 2024.0000 | rich_regional | pooled_all | 0.3805 | 0.9131 | 1.1148 |
| 2025.0000 | rich_calendar | leave_region_out | 0.4928 | 1.4747 | 1.9077 |
| 2025.0000 | rich_calendar | local | 0.4217 | 1.1136 | 1.3196 |
| 2025.0000 | rich_calendar | pooled_all | 0.4118 | 1.0132 | 1.2305 |
| 2025.0000 | rich_regional | leave_region_out | 0.4914 | 1.4596 | 1.8840 |
| 2025.0000 | rich_regional | local | 0.4172 | 1.0940 | 1.3007 |
| 2025.0000 | rich_regional | pooled_all | 0.4087 | 0.9925 | 1.2163 |
| 2026.0000 | rich_calendar | leave_region_out | 0.6109 | 1.8263 | 2.3468 |
| 2026.0000 | rich_calendar | local | 0.6002 | 1.7010 | 2.0879 |
| 2026.0000 | rich_calendar | pooled_all | 0.5048 | 1.2732 | 1.5266 |
| 2026.0000 | rich_regional | leave_region_out | 0.6093 | 1.8173 | 2.3443 |
| 2026.0000 | rich_regional | local | 0.5957 | 1.6899 | 2.0898 |
| 2026.0000 | rich_regional | pooled_all | 0.5033 | 1.2703 | 1.5266 |

Held-out-region transfer generally degrades versus local fitting, particularly at long leads. For 2026
rich-calendar lead 14, leave-region-out is 2.3468 versus local 2.0879; pooled-all is 1.5266.
Pooling all regions can help but includes target-region fitting data, so it cannot be advertised as
successful transfer to a wholly unseen region. These negative transfer results are retained.

Three states and two historical event years do not support broad regional generalisation, causal festival
claims or high-precision significance inference. All current outcomes are exploratory. Full event/non-event,
state/year metrics and training state/cutoff/normalizer logs remain alongside this report.

Audit with `.venv/bin/python src/test_regional_transfer.py` and `src/audit_phase2.py`.
