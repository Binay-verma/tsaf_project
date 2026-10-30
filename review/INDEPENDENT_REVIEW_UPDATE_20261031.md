# Independent scientific/calendar review brief

Author/requester: **Binay Verma**. This does not fill the independent reviewer identity.

**Prepared for an external reviewer. No external human review has occurred.** Clean-environment checks and separate software implementations are internal evidence, not independent peer approval.

## Review scope and concrete questions

1. Verify the target and units: recorded daily supplied/met electricity in GWh. Check observation-day versus report-day conventions against primary GRID-INDIA reports; cross-source date agreement alone is insufficient.
2. Review all actually used calendar anchors and notification issue/effective/amendment dates. Distinguish Delhi government offices, Karnataka general/restricted schedules, Maharashtra public/NI/bank-only/additional-office categories, and religious observances. Review `event_issue_evidence.csv` and the existing ledger. Six strengthened rows are not full amendment certification.
3. Inspect temporal fit/selection purges and model inputs. Can any target at/after an origin enter its features or learned fitting state? Are local history warm-up and pretrained context/adaptation schedules accurately described?
4. Review dimension/information controls on both TSFMs, zero-channel sensitivity and active placebo construction. Generic versus regional dates do not automatically mean wrong versus correct dates. Scalar versus seven channels also changes representation/information. Do effect claims survive these distinctions?
5. Review the statistical unit: only two primary historical event-year clusters, correlated states/days and one seeded placebo. No row-count-based significance, causal inference or strong regional generalisation is claimed.
6. Inspect the internal numerical review: scalar/pandas float64 features differed by about2.4e-11 but altered tree forecasts. Original failed comparisons are preserved; a new float32 interface reproduces the checked forecasts in a clean environment. Check whether the bounded review is adequate for the intended claims; do not call it full independent replication.
7. Review model identities, actual weight hashes, licence and temporal exposure. Historical event targets predate both audited weight uploads. Neither named corpus searches nor changed weights imply absence of proxies.
8. Examine historical revisions and publication-time lag: sparse archived data and two fixed midnight Git snapshots support bounded findings, not an exhaustive real-time reconstruction.
9. Verify that prospective forecasts in commit `cabd5982e1948652b9841d6c31a2380f6f314198` remain unchanged. Only31October–11November targets are eligible. Later scoring uses first complete later snapshot, no retuning; one episode is not independent-source confirmation.
10. Review nearest primary work and the empirical/negative-results framing. No new-method or first-ever claim is established by this project. Evaluate whether contribution/coverage fit a credible journal after rights and evidence gaps are addressed.

## Evidence locations

- Protocols/forecasts/selection logs/audits under each named `results/` directory.
- Current results and open gates in `CURRENT_RESEARCH_STATUS.md`.
- Working manuscript and `manuscript/SUBMISSION_GATES.md`.
- `PHASE2_REPRODUCTION.md`, package pins and current checkpoint checksum manifest.
- Source permission draft in `review/SOURCE_PERMISSION_REQUEST.md`; the author reports sending the email manually. No assistant duplicate or permission reply is inferred.

## Latest evidence to examine (31 October 2026 India time)

- Start with CODEX_HANDOFF.md and the current named-protocol matrix. Some foundation extensions remain active; no review of unavailable results is implied.
- Review `review/used_calendar_v4`: the Karnataka2025 Vijayadasami1October/Gandhi2October mismatch was real, while Maharashtra2022 GudiPadwa remains an evidence gap. Compare flag-only and recentered/weekday-control amendments separately; do not attribute cohort changes solely to features.
- Review `MTA_HOLIDAY_REPLICATION_BRIEF.md` and exact pre-acquisition registration: two NYC occurrences/two related modes, million rides, decision1/7/14→model8/14/21, revised estimates, parking-observance scope, provider reuse statement and pre-year archive digests. Internal reruns of72selectionfits/624inputbytechecks are not independent human review.
- Review `review/future_freeze_scope_v1`: original future evidence has noChronos orfestival-feature comparison; the later interval annex repeats the sameTimesFMepisode. Oldforecasts/workflow unchanged. Future outcomes cannot directly validate the primary festival pooling hypothesis.
- Once complete, examine new `manuscript/integrated_review_v3` with its source manifest, all-case supplements and reporting audit. Before completion, use audited local briefs and historical drafts with their explicit cohort/version limits.

## Reviewer response fields (unfilled)

- Reviewer name, role, affiliation and relevant expertise:
- Independence/conflicts of interest:
- Date, reviewed commit, commands and source documents checked:
- Confirmed findings, defects and unresolved questions:
- Calendar rows independently verified and amendment scope:
- Reproduction results and scientific claims supported/not supported:
- Required corrections before submission:

Leaving these blank is intentional; no sign-off or reviewer identity is fabricated.
