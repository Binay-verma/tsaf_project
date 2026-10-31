# Seven-task journal ledger — 31 October 2026

Author: Binay Verma. Prepared in an AI-assistant session (Claude) from checkpoint `cb03c72`. This is an internal working document, not independent review, professor approval or a submission check.

Branch `journal-seven-tasks-20261031-claude`, local commits only. **Nothing was pushed from this session**: GitHub push access was not granted here. The bundle and the Colab cell in section 6 push it.


> **Correction (31 Oct 2026, later the same day).** The first version of this ledger counted exact ties as sign disagreements. The corrected counts are 19/36 opposite year signs plus 1 tie (not 20), and 11/36 opposite India–NYC signs plus 3 ties (not 14 implied). See `tie_correction_v2.json`; the original outputs are preserved.

## 000. Third pass — 31 October 2026, 23:30 IST

- **Calendar package builder** (`src/calendar_package_builder_v1.py`, 6 tests). It copies the reviewed, corrected 2024–2025 ledger and placebos unchanged, and accepts 2026+ dates **only** as typed by a person from a primary PDF. It checks printed weekdays, state scope, coverage, the reader's name and that each document is a real PDF; derives fixed-rule placebos; and validates with the unchanged rolling validator. A synthetic 2026 fixture plus the real 2024–2025 rows pass validation for issuance 0. A blank form is at `review/calendar_entry_2026_v1/`.
- **Singapore layer** (`src/singapore_replication_v1.py`, 7 tests): the calendar, case, feature and daily-energy code, ready for when C3 passes. The model runners and real file formats are still to do. No data was touched.
- **Your next actions:** (1) push `2c7b267` and later; (2) download the three 2026 state PDFs, fill in `review/calendar_entry_2026_v1/` and run the build command in its README; (3) C3; (4) source-rights/report-day evidence for activation; (5) C5 on/after 12 Nov.

## 00. Decisions taken — 31 October 2026, 21:47 IST (the author delegated all three)

| Decision | Choice | What was done | What it does not do |
| --- | --- | --- | --- |
| Rolling study timing | **Option B** | New registration `results/rolling_confirmation_timing_v2/` plus `src/rolling_execution_v2_timing.py`. Only v1's up-front 2024–2027 calendar requirement is removed; each issuance must still document its own context and target years. 4 synthetic tests; all v1 files unchanged | It does not activate anything. Source rights, observation-day review and human-verified 2024–2026 calendars are still missing, so 16 Nov remains a likely miss. It is effective only if pushed before 16 Nov 09:00 UTC |
| `POSOCO_data.csv` | **Keep for now, with notice** | `data/external/RIGHTS_NOTICE.md`: attribution, no licence found, request sent 30 Oct, prompt removal on request | Not a permission claim. Removing it from the current version would not remove it from public history and would break exact reproduction |
| v6 title | **Keep** | No change | Your professor can still change it |

## 0. Second pass — 31 October 2026 evening (current status; sections 1–6 below are the first pass)

**Repository and code check.**
- **History.** All 46 commits were scanned. No commit deletes a file. The only renames are four live-progress logs, moved byte-identically into `review/progress_snapshot_5a7467f/`. Changes inside `results/` are confined to `prospective_20261030_v1/AUTOMATION.md` (status wording). The two post-freeze code changes were an import path in `score_frozen.py` and a *stricter* completeness check in `collect_prospective_actuals.py`, both before any outcome. No credential patterns were found in any revision.
- **Static analysis.** pyflakes over 189 source files found no undefined names outside legacy star-import modules.
- **Dry runs.** All three frozen-episode scorers stop at PENDING with no network request before 12 Nov UTC. Registered self-hashes match: the interval scorer, and 8/8 source files of the Chronos competitor.
- **Rolling runner.** It checks the issuance window before any network or model access.

**Correction to the first pass.** Exact ties were counted as sign disagreements. Corrected: India 2024 vs 2025 opposite in **19**/36 (+1 tie); India vs NYC opposite in **11**/36 (+3 ties, all Stable LightGBM day flags with identical NYC forecasts); agreement is still 22/36. The original outputs are preserved; see `tie_correction_v2.json`.

| # | Task | Deliverable now | Status | Remaining blocker | Next action |
| --- | --- | --- | --- | --- | --- |
| 1 | Distinct contribution | **Manuscript v6** (`manuscript/integrated_review_v6/`, MD/DOCX/PDF, 15 pages). R1–R8 applied as asserted edits to v5; all 9 v5 tables byte-identical. Separate audit `independent_v6_audit.json` recomputes every new number from case-level files: **pass** | Done internally | Distinctiveness is a human judgement | Professor reads v6; decide whether to keep the reframed title |
| 2 | Generalisation | Assessment plus Singapore draft protocol | Blocked | EMA history start and terms scope; protocol must be pushed before any acquisition | Run C3, then push the protocol |
| 3 | Untouched confirmation | Guards and dry runs verified. Calendar/activation assessment `review/india2026_calendar_feasibility_v2/` | Guards intact. Rolling activation **not satisfiable** as registered (2027 state lists not issued) | Option B registered locally; must be pushed before 16 Nov | Push the bundle before 16 Nov 09:00 UTC. Score the frozen episodes with C5 on/after 12 Nov 05:30 IST |
| 4 | Closest-method comparison | `CLOSEST_METHOD_MAP.md` | Mapped. Ziel's additive single and per-holiday dummies correspond to the existing pooled/typed local arms; only Ziel's replacing (holiday-as-Sunday) variant is missing; Alipour is not reproducible | — | Optional: register and run the replacing variant (exploratory, multi-hour) |
| 5 | Source and calendar credibility | Data-statement correction in v6. 2026 notifications located on secondary hosts (Maharashtra gazette of 8 Dec 2025 from two hosts; Karnataka; GNCTD order of 4 Dec 2025) | Located, not verified | Bytes could not be downloaded here. The Delhi extraction looks truncated. Curator reply pending. `POSOCO_data.csv` decision pending | A human downloads and reads the three PDFs, records hashes and checks amendments. You decide on the public file |
| 6 | Independent review | Reviewer packet v6 (corrected counts) | Ready | No reviewer | Send v6 PDF and packet to a real external researcher |
| 7 | Dependence and uncertainty | Cluster tables, now in v6 Appendix A4–A5 | Done (descriptive) | Two event years | — |

**Possibly important if confirmed by a human reading:** 2026 Dussehra appears on 20 Oct (Delhi, Maharashtra) but Vijayadashami on 21 Oct (Karnataka). National Diwali, 8 Nov 2026, is a Sunday. The frozen 31 Oct–11 Nov episode therefore spans Diwali, so its 12 Nov scoring tests history-only models across a festival. It is still one episode.

**C5 — on or after 12 Nov 2026 05:30 IST only** (frozen episodes; read-only on forecasts):

```bash
cd /content/tsaf_project && git pull --ff-only
python src/collect_prospective_actuals.py      # prints PENDING if labels are incomplete; rerun later, never edit
python src/score_interval_annex.py
python src/score_chronos_competitor.py
git status --short                              # new scoring dirs only; commit and push them
```

## 1. What was actually done in this session

| Category | Item | Evidence |
| --- | --- | --- |
| Completed earlier (not repeated) | All registered historical lanes, v5 manuscript, frozen forecasts, rolling software | Repository at `cb03c72`; `src/verify_continuation.py` PASS, 3,177 files |
| Newly executed | Independent check of the Colab claim audit | All 36 lead-1 table cells, both contrast ranges and the case inventories reproduce exactly from repository files. The Colab report did not state which India version it used: its values match `document_aligned` only. The original-calendar max is 0.05614, not 0.05564 |
| Newly executed | Registered descriptive re-analysis (A–D) of already-inspected forecasts | Registration `registration_descriptive_reanalysis.json` committed (`f09baed`) before computing; outputs `A_*.csv`–`D_*.csv`, `descriptive_reanalysis_result.json`. Hierarchy reconstruction matches audited balanced MASE to 2.2e-16 |
| Newly executed | Full test suite in a newly built Python 3.12.13 environment, pinned `requirements.txt` | 104 passed, 30 subtests (`pytest_py312_core.txt`, `pytest_py312_freeze.txt`). SciPy 1.18.1 unpinned. Torch, Chronos and TimesFM were **not** installed, so no foundation inference ran. This is a different machine, but it is still an AI-run software check, not human reproduction |
| Newly executed | Frozen-forecast immutability check | Every file present at the first commit of each frozen directory is byte-identical at HEAD: 7/7 (`cabd598`), 6/6 (`29bdd98`), 12/12 (`0e4ab33`). No outcomes fetched |
| Newly executed | Literature check of nearest classical work | Ziel (2018) and Arora & Taylor (2018) verified at primary pages. Neither is cited in v5 |
| Newly executed | Source-rights check of tracked data | Robbie Andrew's full compilation `data/external/POSOCO_data.csv` has been tracked since the first public commit `eb6e9b0`. No licence was found for it earlier. The other two tracked sources are CC BY 4.0 |
| Draft only | Singapore replication protocol | `results/singapore_festival_replication_v1/DRAFT_PROTOCOL.json`. **Not registered**: it has not been pushed, and its calendar files are not yet acquired. No demand records were viewed |
| Draft only | Reviewer packet, contribution statement, claim revisions | This file and `REVIEWER_PACKET_v6.md`. The manuscript was not edited |
| Unavailable external facts | Curator reply, professor feedback, independent reviewer, primary 2027 state calendars, EMA history start and terms scope, public push time of `e7d9423`, live workflow state | See section 3 |
| Time-gated | Frozen episode scoring and the rolling study | Earliest frozen scoring is 12 Nov 2026 00:00 UTC (05:30 IST). The first rolling window is 16 Nov 2026 09:00–09:59 UTC |

## 2. Seven-task ledger

| # | Task | Concrete deliverable | Evidence | Status | Blocker | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Distinct contribution | Claim/evidence/limitation ledger (section 4); contribution statement (section 5) | Colab audit verified; re-analysis A/B; Ziel 2018 located | **Draft complete; manuscript not revised** | Whether the contribution is sufficiently distinct is a human judgement | Author applies revisions R1–R8 to make v6, then the professor reviews |
| 2 | Generalisation | Assessment of independent evidence (re-analysis A); source screen; Singapore draft protocol | India–NYC typed/pooled sign agrees in 22/36 cells, is opposite in 11 and ties in 3 (16/23 agree outside ±0.005); TimesFM reverses in 6/6 | **Assessment done; replication drafted, not registered or run** | EMA history coverage and terms scope unverified; no push access; adapter not implemented | Run Colab cell C3 (metadata only); if criteria pass, push the protocol, acquire MOM calendars, then implement the adapter |
| 3 | Untouched confirmation | Immutability and clock-gate check | 25/25 frozen files unchanged; workflow file still has cron `15 7 12-20 11 *` | **Guards intact; nothing scored** | Live GitHub workflow state not checkable here; rolling activation needs a primary 2024–2027 calendar package. Only secondary 2027 state lists were found | Run Colab cell C2 to confirm `disabled_manually`. Score frozen episodes only after 12 Nov 05:30 IST with the original first complete vintage. Issue rolling forecasts only if the prerequisites are factually met; otherwise record misses |
| 4 | Closest-method comparison | Fidelity table (section 4, rows C11–C13) | Kreusel 2026: the abstract page describes no typed-vs-pooled test (the earlier full-text notes in DEEP_RESEARCH.md cover encodings and separate holiday evaluation); Alipour has no runnable code identified; Ziel 2018 compared single, grouped and individual holiday dummies | **Gaps documented; no new comparator run** | Alipour settings, code and account data are unavailable | Optionally register a Ziel-style "holiday-as-Sunday replacement" local comparator. It would be exploratory on inspected data |
| 5 | Source and calendar credibility | Rights findings (section 4, C15–C16) | `POSOCO_data.csv` is public and unlicensed as far as found; MTA and NESO notes unchanged | **Finding recorded; no action on history or visibility** | Curator reply pending; author decision on public-file scope needed | Author decides: keep it pending the reply, or remove it from HEAD in a normal commit. History rewriting requires your explicit instruction |
| 6 | Independent reproduction and review | `REVIEWER_PACKET_v6.md` | 104 tests in a third environment | **Packet prepared; no reviewer** | A real external researcher is needed | Professor or author identifies a reviewer; the reviewer completes the blank form themselves |
| 7 | Dependence and uncertainty | Cluster tables B, C, D | 2024 vs 2025 sign is opposite in 19/36 India cells (+1 exact tie); leave-one-family-out flips 17/36; native 80% coverage <0.8 in 85/100 lead-1 family-year clusters | **Descriptive audit done** | Two event years cannot support annual-generalisation intervals | Add the cluster tables to the v6 appendix; keep row-level and bootstrap inference out |

## 3. Unverified or external items, stated plainly

- **NYC "publicly committed before acquisition."** The local commit `e7d9423` is at 20:23:38 UTC and the acquisition log starts at 20:24:51 UTC. I found no recorded remote-SHA check for that push. The GitHub API was blocked here. Colab cell C2 checks the public push-event time. Until then, describe it as "committed before acquisition".
- **Workflow state.** `disabled_manually` cannot be observed from a clone. Cell C2 reads it.
- **2027 calendars.** For Karnataka, Maharashtra and Delhi (GNCTD) I located only secondary aggregators. A central-government 2027 list exists, but it is not the state calendar. None of these is treated as a feature date.
- **Singapore.** The EMA page shows year/month filters, but its history start was not visible. The dataset terms permit redistribution with attribution, but it is unconfirmed whether that clause covers this statistics page.

## 4. Claim / evidence / limitation ledger (v5 manuscript)

Status key: **S** supported as worded; **Q** supported but needs a qualifier; **R** revise; **U** unverified in this session.

| ID | v5 claim (location) | Evidence checked | Status | Limitation / required revision |
| --- | --- | --- | --- | --- |
| C1 | Typed−pooled range −0.03971 to 0.05564 (India), −0.34441 to 0.15136 (NYC) (Abstract, §4, §5) | Recomputed from metrics files; matches `numeric_claims.json` | S | Name the document-aligned version explicitly. `mta_max` differs from the recomputation in the 16th digit only |
| C2 | Tables 1 and 4 lead-1 cells | 36/36 cells match | S | — |
| C3 | 528 cases, 176 state-date combinations, 24 groups, 2 years (§2.1) | 528 cases; 176 state-dates; 24 family-state-year cells; 75 unique dates; **10 family-year clusters** | Q | **R1**: add "10 family-year clusters; 75 unique target dates" as the effective event count |
| C4 | "Pre-acquisition registered NYC replication" / "publicly committed" (Abstract, §2.2) | Local commit 73 s before acquisition; public push time unverified | U | **R2**: verify with C2, or reword to "committed before acquisition" |
| C5 | Evidence "qualifies when representations help" (Abstract, title) | Re-analysis A/B: the ordering often changes with year, family set and source | R | **R3**: retitle and reframe. The evidence mainly shows **instability** of the preferred representation; it does not identify its conditions |
| C6 | Pooled helps some foundation/tree models; typed helps Ridge/SARIMAX | India day/lead 1: SARIMAX typed in both years and every leave-one-family-out; tree models pooled in India but mixed in NYC; TimesFM pooled in India (9/10 clusters) but typed in NYC | Q | **R4**: report it per model with the year split and the NYC reversal. Do not present it as a model-class rule |
| C7 | Closest work: Kreusel, Alipour, Sanyal, Kaljevic, Meyer (§1) | Kreusel verified (arXiv 2610.13676v1, 9 Oct 2026; its abstract describes no typed-vs-pooled test) | R | **R5**: add Ziel (2018), who directly compared single pooled, grouped and individual holiday dummies in load forecasting, plus Arora & Taylor (2018). The typed-vs-pooled question itself is not new; the new part is the TSFM channel interface and its controls |
| C8 | "Do not use daily-row significance tests" (§2.4) | Consistent with the re-analysis | S | **R6**: add the cluster tables B/D to Appendix A |
| C9 | Native coverage table (Table 6) | Cluster dispersion: TimesFM calendar lead-1 coverage is below 0.8 in 10/10 family-year clusters (range 0.36–0.79); 0 crossings and 0 invalid endpoints in this cohort | Q | **R7**: add cluster coverage ranges next to the means |
| C10 | Simulation "illustrates the familiar trade-off" (§5) | Not re-run | S | — |
| C11 | Pure encodings are daily adaptations of Kreusel (§3) | Wording already says "not an exact reproduction" | S | — |
| C12 | Response profiles are not Alipour's method (§3) | METHOD_REVIEW.md | S | Keep as worded |
| C13 | Generic encodings and pooling have close prior work (§7) | As C7 | Q | Include Ziel 2018 in this sentence |
| C14 | 104 tests and internal checks (§6, status files) | 104 passed in a new 3.12 environment | Q | Still the same software, run by an AI. Not independent human reproduction |
| C15 | "Restricted or unresolved external raw archives are excluded" (Data statement) | `data/external/POSOCO_data.csv` (no licence found) is tracked publicly, and the prediction files contain its actual values | **R** | **R8**: correct the statement. This is a factual inaccuracy in v5 |
| C16 | Indian reuse permission pending (§7) | Unchanged; no reply recorded | S | — |
| C17 | Karnataka 2025 correction and MH2022 evidence gap (§2.1) | Not re-audited; wording matches your constraints | S | Not a new discovery |
| C18 | Float64-tree failure and float32 discrepancy retained (§6) | Present in §6 | S | Keep |

## 5. Contribution statement (draft for your and your professor's judgement)

> We study how sparse named-festival information should be supplied to covariate-informed time-series foundation models and to local regressions. The setting is daily electricity supplied in three Indian states, with a separately sourced NYC holiday check. Cases, five-channel budgets and information availability are held fixed. We compare separate (typed) and shared (pooled) event indicators against calendar-only, zero-padding and weekday-placebo controls, and we correct one named festival date from the primary notification before scoring. The main empirical finding is that **the preferred representation is not a stable property of a model class.** In India the typed-versus-pooled ordering has opposite signs in the two event years in 19 of 36 model/representation/lead cells (one more is an exact tie). Across sources it agrees in 22 of 36 cells, is opposite in 11 and ties in 3, and reverses in all six TimesFM-3 cells. A few orderings persist across both years, leave-one-family-out and NYC; for example, SARIMAX day flags at lead 1 favour separate identities. These are stated as expectations for registered confirmation, not as established effects. This extends classical comparisons of pooled versus individual holiday dummies (Ziel, 2018) to foundation-model covariate interfaces. It does not propose a new architecture or a causal event effect.

The statement only uses numbers from this session's registered re-analysis and the audited tables. Whether this conditional and largely negative lesson is enough for IJF is not established here.

## 6. Colab cells (run in order; paste the outputs back)

**C1 — apply this session's commits** (upload `tsfm_journal_seven_tasks_20261031.bundle` to `/content` first):

```bash
cd /content/tsaf_project
git fetch /content/tsfm_journal_seven_tasks_20261031.bundle journal-seven-tasks-20261031-claude:journal-seven-tasks-20261031-claude
git log --oneline -5 journal-seven-tasks-20261031-claude
git checkout journal-seven-tasks-20261031-claude && python src/verify_continuation.py
python review/journal_seven_tasks_20261031_v1/descriptive_reanalysis.py | tail -5
```

**C2 — verify public push time of `e7d9423` and the live workflow state** (read-only):

```python
import json, urllib.request
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/vnd.github+json"})))
R = "https://api.github.com/repos/Binay-verma/tsaf_project"
for e in get(R + "/events?per_page=100"):
    if e["type"] == "PushEvent":
        print(e["created_at"], e["payload"].get("before", "")[:7], "->", e["payload"].get("head", "")[:7])
for w in get(R + "/actions/workflows")["workflows"]:
    print(w["path"], w["state"])
```

The events API keeps only about 90 days and 300 events. If `e7d9423` (or a later head containing it) does not appear before 20:24:51 UTC, R2 rewording applies.

**C3 — Singapore metadata probe only.** Do not download demand values. Open https://ema.gov.sg/resources/statistics/half-hourly-system-demand-data in a browser and record the earliest year offered in the Year filter. Do the same for the latest year and month. Record whether the download carries a terms or licence notice. Paste only those facts.

**C4 — push, after reviewing the diff** (normal push, no force):

```bash
git push origin journal-seven-tasks-20261031-claude
git ls-remote origin journal-seven-tasks-20261031-claude
```

## Sources

- [Ziel 2018, J. Mod. Power Syst. Clean Energy 6(2):191–207](https://link.springer.com/article/10.1007/s40565-018-0385-5)
- [Arora & Taylor 2018, EJOR 266(1):259–268](https://ideas.repec.org/a/eee/ejores/v266y2018i1p259-268.html), [arXiv 1803.09590](https://arxiv.org/abs/1803.09590)
- [Kreusel et al. 2026, arXiv 2610.13676](https://arxiv.org/abs/2610.13676)
- [EMA half-hourly system demand](https://ema.gov.sg/resources/statistics/half-hourly-system-demand-data), [EMA terms of use](https://ema.gov.sg/terms-of-use), [Singapore Open Data Licence](https://data.gov.sg/open-data-licence), [MOM 2026 public holidays (data.gov.sg)](https://data.gov.sg/datasets/d_149b61ad0a22f61c09dc80f2df5bbec8/view)
- [Taipower dataset mirror](https://ark.nchc.org.tw/en/dataset/best_wish19995)
- [Central Government 2027 holiday list (secondary mirror)](https://www.staffnews.in/2026/07/list-of-holidays-for-the-year-2027-gazetted.html)
