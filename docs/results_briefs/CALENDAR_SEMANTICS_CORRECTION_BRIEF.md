# Document-aligned calendar sensitivity: audited local checkpoint

A new annual-document check identified Karnataka2025Vijayadasami1October, while the original ledger used2October(Gandhi Jayanthi). The v2protocol was pushed before corrected inference. Original ledgers/results remain unchanged. Same past-selected parameters and original target/window cases are used; no errors selected the replacement date.

All1,200fresh local forecasts are complete:60fixed late-2025Karnataka cases ×5arms ×4variants. Existing unaffected forecasts complete both23,808-row local views. The separate audit passes240local train/query byte checks,684unchanged-case block proofs and all label/scale/hierarchical scores. The repeatedcalendar check is retained. These are internal checks, not external human review.

event_window: next-day change in full-panel MASE (corrected minus original; negative improves)

| model | day5 | pooled_day5 | pooled_window5 | window5 |
| --- | --- | --- | --- | --- |
| lightgbm | 0.0 | 0.0 | 0.0 | 0.0 |
| lightgbm_capacity2 | 0.0 | 0.0001324 | 0.0 | 0.0 |
| ridge | -0.0011916 | -3.2e-06 | -0.0001332 | -0.000359 |
| sarimax | 0.0083597 | 0.0044264 | -0.0009189 | 8.12e-05 |

ordinary: next-day change in full-panel MASE (corrected minus original; negative improves)

| model | day5 | pooled_day5 | pooled_window5 | window5 |
| --- | --- | --- | --- | --- |
| lightgbm | 0.0 | 0.0 | 0.0004249 | 0.0 |
| lightgbm_capacity2 | 0.0 | -6.43e-05 | -3.59e-05 | -5.77e-05 |
| ridge | -5.2e-06 | 2.92e-05 | -9.4e-06 | -4.92e-05 |
| sarimax | 0.0 | 0.0 | -0.0 | 0.0 |

A document-aligned date can improve or worsen forecasts. Most tree changes are small; this is not proof of intrinsic feature irrelevance under sparse support. Allleads/controls/negativecases are retained. Foundation and pure-encoding correction lanes are queued after the existing NESO lanes.

The original window cohort remains centered on2October: this isolates feature changes on identical cases, and does not certify a complete newly centered1Octoberwindow. Placebos remain fixed to isolate the true-flag change, so the correctedflag versus originalplacebo is not newly weekday-matched. A separately registered recentered cohort/control amendment is the next executable gap. No second date is changed for the Maharashtra2022GudiPadwa evidence gap (review/used_calendar_v4).

Analysis execution note: the first local finalizer reached the lastworker before its run.json appeared and stopped; partial files and failure are preserved. Output-directory-only recovery reruns the unchanged registered scoring rules in local_checkpoint_recovery_v1. Allnine completed initial event CSVs are byte-identical, and the separate audit passes. No forecast or threshold was replaced to improve scores.
