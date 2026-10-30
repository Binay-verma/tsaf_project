# Provenance, calendar and internal reproduction review v1

Completed on30October2026. This strengthens specific evidence; it is not a data licence, full amendment certification or independent human peer review.

## Clean environment and separate numerical implementation

A separate Python3.12 virtual environment was created without inherited system packages, installed from the repository requirements, and passed32 tests plus phase-two/event persisted-output audits. Numerical package versions and installation logs are retained. SciPy resolved to1.18.1 rather than the working environment1.17.0; this is a separate clean installation, not a byte-identical full environment. Foundation weights were not reinstalled into this clean environment.

A separate scalar baseline implementation imports no application feature/model helpers. Its Karnataka2026 rich-calendar review reproduced six chosen parameter IDs and Ridge forecasts, but eight of twelve tree forecasts failed the original tolerance. A checked difference reached4.2798GWh. Diagnosis shows feature arrays differ by at mostabout2.4e-11 from pandas rolling arithmetic; labels match, and identical production arrays give identical1/2-thread tree predictions. Float32 feature matrices match exactly in all checked matrix sets.

Rather than suppressing failures or loosening tolerances, `stable_tree_refit_v2` records a new numerical contract and reruns the tree study separately. In that contract, the independent scalar implementation in this clean environment reproduces three chosen configurations and twelve forecast examples exactly. Version1 results/failures and frozen future forecasts are preserved. This is bounded internal software review, not an external reviewer or full clean-room inference reproduction.

## Snapshot identity, historical revisions and reporting lag

The frozen raw compilation exactly matches Git revision7e0f29022d74… recorded29October2026. Two fixed snapshots recorded before India-midnight issue cutoffs1September/1October2026 end30August/28September: two/three calendar days behind issue. Comparable labels within those snapshots do not differ from the current frozen values.

The recorded Git root begins14May2026, but this does NOT mean the data were unavailable earlier. We searched Internet Archive CDX, found older captures, recovered three CSV payloads and verified their provider SHA1 digests plus SHA256. The initial parsing attempt encountered still-gzipped transport; raw bytes were retained, gzip decoded with CRC checks, and CDX digests matched the encoded payloads. No verification was disabled.

The18September2024,16October2025 and8November2025 captures reveal retrospective differences from the2026 snapshot. Differences include Maharashtra1January2025 620.30→558.80GWh and Karnataka313.35→259.79GWh, plus other dates. Across the selected snapshots,56 revision rows include repeats; they are NOT56 independent revision events. Exact dates/values are in `historical_revision_inventory.csv`. No attempt was made to infer which version is true without primary-report/curator evidence.

All150 selected2024–2025 festival case labels are identical between the8November2025 archive and the frozen2026 snapshot. This is a bounded label-vintage check, NOT proof of unchanged origin-time histories, first-release labels or all-year results. Input histories and non-event labels do include revised dates.

The completed `vintage_sensitivity_v1` experiment evaluates the observed publication-lag scenarios on matched targets and finds larger mean errors in the fixed two-date panel. Recorded Git/Wayback times are not certified first-publication times, and sparse captures cannot reconstruct every historical release. No future31October–11November2026 outcomes were retrieved.

## Calendar evidence and remaining amendment scope

New issue/date evidence includes: Delhi2024 notice dated19October2023 (visually inspected); Delhi2025 dated13November2024 (visually inspected); Karnataka2024 No.DPAR16HHL2023 dated28November2023 (English OCR table/header); Maharashtra2025 No.PHD-1124/C.R.91/Japuk(29), dated4December2024, Gazette published5December, retained as a government-authored copy on a bank host. Its PartA lists Lakshmi Pujan21October and Bali Pratipada22October; PartB April1 is expressly bank-only and excluded. A bank host is not falsely represented as an official government host.

The six strengthened rows and document hashes are in `event_issue_evidence.csv`. A28-row worksheet enumerates every actually used shared-main/regional-extra anchor, its definition/source, known notice date and UNFILLED amendment/reviewer sign-off. Shared generic anchors do not assert statewide office closure. Religious, office, NI/public, restricted and bank definitions are not interchangeable. No model date was changed based on forecast errors.

Official Karnataka/Delhi index requests returned503; the selected Maharashtra index404; some mirrored documents403/406; one older CAG link404. Search-engine challenges and irrelevant/no results are retained as retrieval limitations, not proof that no amendment exists. The current evidence still cannot certify every final amendment or every historical source's first-publication date.

## Reuse rights and human review

The curator root/India pages, metadata, repository and licence endpoint were inspected. No explicit applicable compilation licence was established; the licence API returns404 and repository metadata is null. Upstream GRID-INDIA retrieval/archived-rights attempts did not yield a verified applicable permission statement. Public availability and user-authorized GitHub synchronization are not a new rights grant.

`review/SOURCE_PERMISSION_REQUEST.md` is a concrete, unsent permission/processing request. `review/INDEPENDENT_REVIEW.md` is a concrete external scientific/calendar review brief with blank reviewer/sign-off fields. The user specified Binay Verma as requester and authorized Gmail, but Gmail connection did not become available. The latest user instruction is to send manually; the assistant supplied the verified public professional address and sent no email. The independent human reviewer is still unnamed; no sign-off is fabricated.

## Future-outcome persistence is now implemented

GitHub accepted `.github/workflows/prospective-evaluation.yml` in commitde42989 and reports it active. Manual dispatch run41018642681 completed successfully: checkout/setup/install/gating passed, score commit/artifact/self-disable steps were skipped as expected before the target period ends. Administrative Actions-permissions lookup403 did not prevent the authorized dry run.

The pinned-action workflow schedules07:15UTC (12:45India time) on12–20November. It verifies the original forecast Git blob, rejects incomplete/wrong-unit labels, archives the first eligible actual-label snapshot and provenance, scores without retuning, preserves an artifact if a branch rule blocks committing, and attempts one-shot disabling once results are retained. No claim is made that after-period source retrieval/scoring or external GitHub punctuality has already been verified. The clock gate prevents source requests/scores now and source requests in other years.

## Actual remaining external decisions

Applicable permission/processing clarification from the curator; an independent human reviewer and amendment-chain sign-off; prospective target dates actually occurring. Code-side controls, recorded-vintage sensitivity, bounded numerical repair and future scoring infrastructure have been executed/tested within their stated scopes. No universal calendar mechanism, contamination-free status, complete real-time reconstruction, journal readiness or acceptance is claimed.

## Latest user update

The user reports sending the email manually; no assistant email was sent and no owner reply/reuse grant is assumed. A college presentation is prepared for1November2026 using own aggregate figures and source credits. The earlier GitHub repository is public. New uploads are held pending a sharing choice, and the verified prospective workflow was paused (`disabled_manually`) to prevent new automatic public score uploads while that choice is unresolved. Its prior successful dry run remains evidence of infrastructure, not a currently active job.
