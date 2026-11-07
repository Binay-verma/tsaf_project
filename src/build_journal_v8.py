"""Build journal-format draft v8 (IJF-style structure) from audited sources.

- Tables from v7 are copied verbatim (rows untouched); only captions and numbering change.
- New tables and every new number are computed here from committed analysis files.
- audit_journal_v8.py later checks that every number in the prose traces to v7 or to these sources.
Run from the repository root: python src/build_journal_v8.py
"""
import csv, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V7 = ROOT/'manuscript/integrated_review_v7'
OUT = ROOT/'manuscript/journal_v8'
CI = ROOT/'results/cluster_inference_v1/analysis'
RC = ROOT/'results/representation_combination_v2/analysis'
NAMES = {'ridge': 'Rich Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'Stable LightGBM', 'lightgbm_capacity2': 'Tree leaf minimum 2',
         'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
ORDER = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return list(csv.DictReader(open(p)))


def f5(x):
    return f'{float(x):.5f}'


v7 = (V7/'MANUSCRIPT.md').read_text()


def table(label):
    """Header, separator and rows of a v7 table, verbatim."""
    block = v7.split(f'\n{label}. ', 1)[1].split('\n\n', 2)[1]
    rows = [l for l in block.splitlines() if l.startswith('|')]
    assert len(rows) >= 3, label
    return '\n'.join(rows)


# ---------------- new numbers ----------------
ci = json.load(open(CI/'summary.json'))
rc = json.load(open(RC/'summary.json'))
ind = read(CI/'india_cluster_tests.csv')
tf = next(r for r in ind if r['model'] == 'timesfm' and r['representation'] == 'day' and r['lead'] == '1')
assert float(tf['p_T1']) == ci['T1']['min_raw_p']
comb_i = read(RC/'india_combination.csv'); comb_n = read(RC/'nyc_combination.csv')
dec = read(RC/'india_2025_decision_rules.csv')
half_gap_i = sum(abs(float(r['typed'])-float(r['pooled']))/2 for r in comb_i)/len(comb_i)
half_gap_n = sum(abs(float(r['typed'])-float(r['pooled']))/2 for r in comb_n)/len(comb_n)
ties_n = sum(float(r['typed']) == float(r['pooled']) for r in comb_n)
assert rc['India']['combine_below_worse'] == 36 and rc['NYC']['combine_below_worse'] + ties_n == 36
nyc_ci_excl = ci['t_interval_excludes_zero']['NYC']
N = dict(T1_raw=ci['T1']['raw_below_005'], T1_holm=ci['T1']['holm_detected'], T1_min=f"{ci['T1']['min_raw_p']:.4f}",
         tf_holm=f"{float(tf['holm_T1']):.3f}", T2_raw=ci['T2']['raw_below_005'], T3_raw=ci['T3']['raw_below_005'],
         ci_i=ci['t_interval_excludes_zero']['India'], ci_n=nyc_ci_excl,
         below_both_i=rc['India']['combine_below_both'], below_both_n=rc['NYC']['combine_below_both'],
         regret_i=f"{rc['India']['mean_combine_regret']:.4f}", bound_i=f'{half_gap_i:.4f}',
         regret_n=f"{rc['NYC']['mean_combine_regret']:.4f}", bound_n=f'{half_gap_n:.4f}', ties_n=ties_n,
         worse=rc['India']['india_2025']['follow_picked_worse'], follow_r=f"{rc['India']['india_2025']['mean_follow_regret']:.4f}",
         comb_r=f"{rc['India']['india_2025']['mean_combine_regret']:.4f}", beats=rc['India']['india_2025']['combine_beats_follow'],
         holm_c=rc['India']['holm_detected_vs_typed']+rc['India']['holm_detected_vs_pooled']+rc['NYC']['holm_detected_vs_typed']+rc['NYC']['holm_detected_vs_pooled'])
assert N['holm_c'] == 0 and N['T1_holm'] == 0

# post-hoc descriptive numbers requested by the internal referee check (not part of any registered protocol)
from statistics import mean, median
from math import comb
N['holm_floor36'] = f'{36*2/1024:.3f}'; N['holm_floor12'] = f'{12*min(float(r["p_T1"]) for r in ind if r["lead"] == "1"):.3f}'
N['expected_raw'] = f'{36*0.05:.1f}'
fr = [float(r['follow_regret']) for r in dec]; cr = [float(r['combine_regret']) for r in dec]
N['random_r'] = f"{mean(abs(float(r['typed'])-float(r['pooled']))/2 for r in dec):.4f}"
N['med_follow'] = f'{median(fr):.4f}'; N['med_comb'] = f'{median(cr):.4f}'; N['max_follow'] = f'{max(fr):.3f}'; N['max_comb'] = f'{max(cr):.3f}'
w = sum(float(r['combine']) < float(r['follow_2024']) for r in dec); assert w == N['beats']
N['sign_p'] = f'{min(1, 2*sum(comb(36, k) for k in range(max(w, 36-w), 37))/2**36):.2f}'
def fixed(rows, col):
    return [float(r[col])-float(r['oracle']) for r in rows]
for tag, rows in [('i', comb_i), ('n', comb_n)]:
    t, p, c = fixed(rows, 'typed'), fixed(rows, 'pooled'), [float(r['combine_regret']) for r in rows]
    N[f'mt_{tag}'], N[f'mp_{tag}'], N[f'mc_{tag}'] = f'{mean(t):.4f}', f'{mean(p):.4f}', f'{mean(c):.4f}'
    N[f'xt_{tag}'], N[f'xp_{tag}'], N[f'xc_{tag}'] = f'{max(t):.4f}', f'{max(p):.4f}', f'{max(c):.4f}'
    assert max(c) < min(max(t), max(p))
# controls table (stored registered metrics)
MI = [r for r in read(ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv') if r['version'] == 'document_aligned' and r['horizon'] == '1']
MN = [r for r in read(ROOT/'results/mta_holiday_recovery_v1/analysis/event_window/metrics_balanced.csv') if r['horizon'] == '8']
def mv(rows, m, a):
    x = [r for r in rows if r['model'] == m and r['arm'] == a]
    return f5(x[0]['MASE']) if x else '–'
t_ctl = ['| Source | Model | History | Cal. | + zeros | Placebo | Typed | Pooled |', '| ------- | --------------- | -------- | -------- | -------- | -------- | -------- | -------- |']
for src, rows in [('India', MI), ('NYC', MN)]:
    for m in ORDER:
        t_ctl.append(f"| {src} | {NAMES[m]} | {mv(rows, m, 'history')} | {mv(rows, m, 'calendar')} | {mv(rows, m, 'zero5')} | {mv(rows, m, 'placebo_day5')} | {mv(rows, m, 'day5')} | {mv(rows, m, 'pooled_day5')} |")
t_ctl.append(f"| NYC | Last value | {mv(MN, 'last', 'history')} | – | – | – | – | – |")
t_ctl.append(f"| NYC | Seasonal naive | {mv(MN, 'seasonal', 'history')} | – | – | – | – | – |")

# ---------------- new tables ----------------
t_ci = ['| Model | Rep. | Mean (10 clusters) | 95% t interval | Sign-flip p | Holm p | Year-change p |', '| --- | --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in ind if x['model'] == m and x['representation'] == rep and x['lead'] == '1')
        t_ci.append(f"| {NAMES[m]} | {rep} | {f5(r['mean'])} | {f5(r['t_low'])} to {f5(r['t_high'])} | {float(r['p_T1']):.4f} | {float(r['holm_T1']):.4f} | {float(r['p_T2']):.4f} |")
t_comb = ['| Model | Rep. | Typed | Pooled | Average | 2025: follow-2024 regret | 2025: average regret |', '| --- | --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in comb_i if x['model'] == m and x['representation'] == rep and x['horizon'] == '1')
        y = next(x for x in dec if x['model'] == m and x['representation'] == rep and x['horizon'] == '1')
        t_comb.append(f"| {NAMES[m]} | {rep} | {f5(r['typed'])} | {f5(r['pooled'])} | {f5(r['combine'])} | {f5(y['follow_regret'])} | {f5(y['combine_regret'])} |")
t_comb_n = ['| Model | Rep. | Typed | Pooled | Average |', '| --- | --- | --- | --- | --- |']
for m in ORDER:
    for rep in ['day', 'window']:
        r = next(x for x in comb_n if x['model'] == m and x['representation'] == rep and x['horizon'] == '8')
        t_comb_n.append(f"| {NAMES[m]} | {rep} | {f5(r['typed'])} | {f5(r['pooled'])} | {f5(r['combine'])} |")

# ---------------- manuscript ----------------
TITLE = 'Typed or pooled? Festival covariates in foundation and local forecasting models: unstable orderings, matched controls and a combination hedge'
md = f"""# {TITLE}

Binay Verma

Affiliation: __________ . Corresponding author email: __________ .

**Draft for supervisor review (journal format, version 8). Not submitted.**

## Abstract

Forecasters who add festival or holiday indicators to a model must decide whether to give each named event its own channel (typed) or to share one channel across events (pooled). We examine this choice for two pinned time-series foundation models (Chronos-2 and TimesFM-3) and four local specifications (Ridge, SARIMAX and two LightGBM configurations) on daily electricity supplied in three Indian states, with matched calendar, zero-channel and weekday-placebo controls, a source-driven correction of one festival date, and a separately registered replication on New York City transit ridership. On 528 Indian festival-window cases, typed-minus-pooled MASE ranges from -0.03971 to 0.05564 across 36 model/representation/lead cells, and its sign is opposite between the two event years in 19 cells. Cluster-level sign-flip tests have too little resolution to confirm any ordering (smallest raw p {N['T1_min']}, for TimesFM-3 day flags at lead 1). India and NYC agree in sign in 22 of 36 cells, disagree in 11 and tie in 3. For the local specifications, daily adaptations of Ziel's holiday-as-Sunday and replacing designs improve on the calendar baseline in all Indian cells, as the additive flags do; in NYC event windows the holiday-as-Sunday design is worse in all 12 cells. Because the better representation cannot be identified in advance, we compare exploratory decision rules on stored forecasts. Choosing the 2024 winner for 2025 picks the worse representation in {N['worse']} of 36 cells, with mean regret close to that of a random pick; no fixed representation is best in both sources; and an equal-weight average of the typed and pooled forecasts, whose error is bounded by the mean of the two by construction, has the smallest worst-case regret in both India and NYC. The evidence is retrospective, from two Indian event years and two NYC observances, and supports a conditional recommendation rather than a general ranking of representations or models.

**Keywords:** holiday effects; event covariates; time-series foundation models; forecast combination; electricity demand; forecast evaluation.

## Highlights

- Typed and pooled festival flags compared with matched zero and placebo controls
- The better representation changes between years, models and data sources
- With 10 event clusters, no typed-versus-pooled ordering can be confirmed
- Following last year's winner did no better than a random pick
- Averaging both forecasts gave the smallest worst-case loss in both sources

## 1. Introduction

Holidays and festivals are rare, recurring and heterogeneous. A forecaster who adds them to a model faces a choice that predates modern machine learning: give each named event its own indicator, so that each can have its own response, or pool them into one indicator, so that sparse events borrow strength from one another. In load forecasting the trade-off is familiar [9, 10]. Covariate-informed time-series foundation models (TSFMs) such as Chronos-2 [6] and TimesFM-3 [7] reopen it in a new form, because the model is not re-estimated: the forecaster controls only which channels are passed and how they are encoded [1, 2].

This paper asks a narrow question: on the same cases, with the same information budget, does the typed or the pooled representation give lower error, and is the answer stable enough to act on? We answer it for daily electricity supplied in Delhi, Karnataka and Maharashtra around five Indian festival families, and repeat the design on two later NYC observances. Our contributions are:

1. **A matched comparison.** Typed and pooled festival indicators are compared for two pinned TSFMs and four local models on identical cases, with a calendar baseline, an equal-dimension zero-channel control and weekday-shifted placebos, so that gains from adding channels and gains from festival information can be separated (Sections 3 and 4).
2. **Evidence of instability.** The preferred representation changes sign between event years, between models, and between India and NYC, and cluster-level permutation tests cannot confirm any ordering with 10 event clusters (Sections 4 and 5).
3. **A source-driven calendar correction.** One festival date in the original ledger did not match the state notification. We show how correcting it changes cases and features separately (Section 2).
4. **Decision rules for unstable orderings.** Using stored forecasts only, we find that following the previous year's winner does no better than a random pick, and that an equal-weight average of the two representations has the smallest worst-case regret in both sources (Section 6).

We do not propose a new architecture, claim causal holiday effects or claim contamination-free testing of pretrained models. Section 2 describes the data and calendars, Section 3 the models and controls, Sections 4 to 6 the results, and Section 7 the limitations.

## 2. Related work

**Holidays in load forecasting.** Ziel [9] compared one shared holiday dummy, grouped dummies and a separate dummy for each holiday for German load. He reported that many additional per-holiday dummies did not seem to improve on one additional dummy, with univariate results mixed by holiday type; in his multivariate comparison three models were not significantly worse than the best model forecast, M-RpH (a replacing design with one dummy per holiday), and the holiday-as-Saturday and holiday-as-Sunday designs were in most cases significantly worse than the best approach. Arora and Taylor [10] treat special days with rule-based seasonal ARMA models. Moving Indian holidays have been modelled in official manufacturing statistics [3].

**Covariates in foundation models.** Kreusel et al. [1] examine calendar encodings in Chronos-2 and TimesFM-3. Alipour et al. [2] learn impact-driven event representations from residual responses. Kaljevic et al. [4] benchmark TSFMs for load forecasting under covariate uncertainty.

**Forecast combination.** Averaging forecasts goes back to Bates and Granger [11]; simple equal weights often perform as well as estimated weights, the forecast combination puzzle [12]. We use equal weights only as a hedge between two representations, not as a new combination method.

**Evaluation of pretrained models.** Meyer et al. [5] show that sample and proxy leakage can affect TSFM evaluation, and that model release dates alone do not establish contamination-free tests.

Our study does not introduce typed or pooled indicators, which are established. It examines how that choice behaves through TSFM covariate channels under a fixed channel budget with zero and placebo controls, and what a forecaster should do when the ordering is unstable.

## 3. Data and calendars

### 3.1 Indian electricity and festival dates

The target is daily energy met/supplied in GWh for Delhi, Karnataka and Maharashtra, from a GRID-INDIA/POSOCO compilation. It is not latent unconstrained demand, household consumption or hourly peak load. Outcomes through 28 October 2026 have been inspected, so all historical method choices made after that are exploratory.

Five festival families are used: Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali, with declared state scopes and subsidiary anchors. Twelve retained annual state documents support an internal review of all 58 named dates: 54 match the declared family, two are explicit shared-national-main exceptions, one Karnataka 2025 date did not match, and one Maharashtra 2022 Gudi Padwa date could not be corroborated from the retained one-page schedule. Visible notification dates are not certified first-publication histories, and amendment chains and human sign-off remain incomplete, so it is not established that every flag was publicly known at each forecast origin. Office closure does not establish a statewide electricity response.

**Correction.** The Karnataka notification labels Vijayadasami on 1 October 2025 and Gandhi Jayanthi on 2 October; the original ledger used 2 October for Dussehra. A separately registered flag-only correction holds cases and placebos fixed. A further registered recentering replaces only three old 5 October target/lead cases with 28 September, yielding the complete 28 September–4 October window, and moves the corresponding +35-day placebo from 6 to 5 November. Same-case aligned-feature changes at lead 1 range from -0.00119 to 0.00836, while replacing the three cases under original features changes the aggregate by -0.00251 to 0.00171; the two are different estimands and are reported separately. No forecast error was used to choose these dates.

The resulting 528 event-window cases are 176 state/target-date combinations at leads 1, 7 and 14 across 24 family/state/year groups in 2024–2025. They cover 75 distinct target dates and 10 family/year clusters; the clusters, not rows, are the effective event units. The 216 ordinary cases are a seasonal sample (the first eligible rotating weekday per month, state and year, excluding festival windows).

### 3.2 NYC transit replication

The MTA daily ridership dataset (identifier sayj-mze2) provides Subway and Bus estimated counts, converted to million rides. The protocol was committed (e7d9423, 20:23:38 UTC on 30 October 2026) before the evaluation records were acquired (20:24:51 UTC); the public push time of that commit has not been independently verified. The observance dates come from the NYC DOT alternate-side-parking calendar, which documents parking observances rather than MTA service changes; five calendar families keep the Indian five-channel budget, of which two occur in the test windows. The 84 event cases cover complete ±3-day windows around Yom Kippur on 21 September and Columbus Day on 12 October 2026, two modes and three decision leads; the 42 ordinary cases balance weekdays and exclude all registered observance windows. The current MTA source is revised, so the study is retrospective despite registration before the targets were acquired. A fixed seven-day observation buffer maps decision leads 1/7/14 to model steps 8/14/21. Two observances in one city support a bounded robustness check only.

### 3.3 England/Wales delay check

NESO transmission demand supplies an independent electricity source with no holiday targets. Sixteen ordinary September 2026 targets are compared under ideal availability and 21 extra days of observation delay (Appendix Table A7). This is a lag sensitivity, not a holiday replication.

## 4. Models, representations and evaluation

### 4.1 Models

Chronos-2 and TimesFM-3 use pinned code and weights, 730 prior target days, fixed seeds, two CPU threads and no task fine-tuning; weight and input bytes are checked, and every registered run includes a future-target perturbation check. The four local specifications are a rich Ridge regression, a float32 LightGBM, a separately reported minimum-leaf-2 LightGBM sensitivity, and SARIMAX(1,0,0)(1,0,0,7). Ridge and LightGBM use 27 past-only history features plus the same calendar and event covariates; their parameters come from pre-evaluation chronological validation with purged future labels and are shared across arms. Local models are refitted monthly while foundation models are frozen, so model rankings do not isolate architecture.

### 4.2 Representations and controls

Every arm keeps 13 ordinary calendar channels (seven weekday indicators and three annual harmonic pairs). Apart from the calendar arm, each main arm adds five channels:

- **calendar** (no festival information) and **calendar + five zeros** (equal dimension, no information);
- **typed day / typed window**: one indicator per family, on the festival day or on its ±3-day window;
- **pooled day / pooled window**: one shared indicator plus four zero channels;
- **typed day / window placebos**: the same indicators shifted by fixed seeded weekday-preserving offsets that avoid true windows.

Three further local-model arms adapt Ziel's designs [9] to daily festival anchors (Section 5.3): **hSun** treats each anchor day as a Sunday; **Rph** adds the pooled day flag and sets all seven weekday dummies to zero on flagged days; **RpH** does the same with the five typed flags (Ziel's Eq. 11).

### 4.3 Evaluation

Each origin is the first unseen date, and the target date is origin plus model step minus one. The error measure is MASE with a fixed pre-year scale (the mean absolute weekly difference over the previous 730 days); imputed labels are never scored. Indian event summaries average errors within state/year/family, then states within year, years within family, and families equally. NYC uses the analogous mode hierarchy.

Because rows are correlated, we report every registered contrast with its sign by year and leave-one-family-out (LOFO) range, and use exact sign-flip permutation tests with clusters as units (10 Indian family-year clusters; 4 NYC family-mode cells), Holm-adjusted across the 36 cells of each test family. These tests were registered before any p-value was computed, but the cluster values had already been reported descriptively. A sign-flip test assumes the cluster differences are symmetric about zero under the null; clusters in the same year share weather and source vintage and the same families recur across years, so the tests are approximate. The protocol failed to note that, with 1,024 sign assignments and Holm over 36 cells, the smallest attainable adjusted p is {N['holm_floor36']}, so the India test could not reach 0.05 for any cell; we therefore report raw p-values and the consistency of signs rather than a detection count.

## 5. Results

### 5.1 Indian festival windows

Table 1 gives the pre-specified next-day comparison and Figure 1 all leads. Festival information helps the local models: typed and pooled day flags lower Rich Ridge event MASE from 0.57699 to 0.45317 and 0.46093, and SARIMAX from 0.57301 to 0.42533 and 0.45345. Chronos-2 gains little; TimesFM-3 gains with both day flags (typed 0.48005, pooled 0.42459, against 0.55148 for calendar). Window indicators help little. On ordinary days (Table 2) the differences between arms are smaller, but for both foundation models the day arms slightly raise ordinary-day MASE relative to calendar.

Appendix Table A12 shows that in India the gains come from festival information rather than from extra channels: the zero-channel and placebo arms stay within 0.005 of calendar for every local specification, whereas typed and pooled day flags lower Rich Ridge and SARIMAX MASE by more than 0.1. MASE above 1 in some cells, mostly at leads 7 and 14 and in NYC, means those forecasts are worse than the in-sample weekly naive scale.

Table 1. Indian festival windows (document-aligned, recentered): lead-1 MASE.

{table('Table 1')}

Table 2. Indian seasonal ordinary sample: lead-1 MASE.

{table('Table 2')}

![Figure 1. Typed minus pooled MASE on the same Indian festival-window cases, all models, representations and leads. Positive values favour pooling.](figures/india_contrasts.png)

### 5.2 Is there a winner?

The typed-minus-pooled contrast ranges from -0.03971 to 0.05564 across the 36 model/representation/lead cells. Its sign is opposite between 2024 and 2025 in 19 cells (one more is an exact tie), and leaving out one festival family flips the balanced sign in 17 (Appendix Table A4). The 36 cells are 12 model/representation pairs at three correlated leads, so these counts are not independent. A few orderings persist: SARIMAX day flags at lead 1 favour separate identities in both years and under every leave-one-family-out subset, and TimesFM-3 day flags at lead 1 favour pooling in 9 of 10 family/year clusters; these are expectations for future confirmation, not established effects.

Table 3 gives the cluster-level tests at lead 1. Across all 36 cells, {N['T1_raw']} reach a raw sign-flip p below 0.05, against {N['expected_raw']} expected if every null were true; the smallest raw p is {N['T1_min']} (TimesFM-3 day flags). Holm adjustment over 36 cells cannot produce an adjusted p below {N['holm_floor36']} with 10 clusters, and even a post hoc restriction to the 12 lead-1 cells would leave the smallest adjusted p at {N['holm_floor12']}. The year-interaction test (five family-level differences; smallest attainable p 0.0625) and the NYC test (four cells; 0.125) cannot reach 0.05 either. The tests therefore cannot confirm any ordering; they also cannot show that the representations are equivalent, and effects of a few hundredths of MASE would go undetected.

Table 3. Indian typed-minus-pooled MASE at lead 1 with family-year clusters as units. Positive favours pooling. The t interval is descriptive and unadjusted (df 9). Sign-flip p: exact two-sided test over 1,024 sign assignments; Holm across all 36 cells (smallest attainable {N['holm_floor36']}); year-change p: sign-flip over 5 family-level (2025 minus 2024) differences.

{chr(10).join(t_ci)}

### 5.3 Closest-method comparators

Ziel's designs (Table 4; Figure 2) improve on the calendar baseline in all 12 Indian local model/lead cells for each design, but the additive typed and pooled day flags also do so in 22 of their 24 cells, and the replacing designs differ consistently from the additive flags they carry in only 3 (Rph) and 4 (RpH) of 12 cells. In NYC event windows hSun raises MASE relative to calendar in all 12 local cells, and Rph and RpH in 9 and 6 of 12, while on NYC ordinary days all three designs mostly lower it. These designs were run for the local specifications only. Pure daily encodings of the calendar (ordinal, one-hot, cyclic and context-mean target encodings) for the foundation models are in Appendix Table A6, and fixed response-profile comparators in Table A2.

Table 4. Ziel adaptations on Indian festival windows: local-model lead-1 MASE. The first three columns equal Table 1.

{table('Table A6')}

![Figure 2. Change in lead-1 event MASE relative to the calendar baseline for Ziel's holiday-as-Sunday (hSun) and replacing (Rph, RpH) designs. Left: India; right: NYC (decision lead 1, model step 8).](figures/ziel_designs.png)

### 5.4 NYC replication

Table 5 and Figure 3 repeat the main comparison on NYC. The contrast range is wider, -0.34441 to 0.15136. Within NYC, 36 of 144 family/mode/step cells favour pooling, 96 favour separate identities and 12 tie. India and NYC agree in sign in 22 of 36 cells, are opposite in 11 and tie in 3. TimesFM-3's sign differs between India and NYC in all 6 of its cells: pooling is favoured in India and typed flags in NYC in five of them, and the reverse for the lead-14 window cell. SARIMAX typed-day flags improve on calendar while pooled-day flags worsen it, whereas pooling helps the ordinary sample (Appendix Table A1).

Table 5. NYC event windows: decision lead 1 (model step 8), MASE.

{table('Table 4')}

![Figure 3. NYC typed minus pooled MASE. Columns are decision leads 1/7/14 (model steps 8/14/21).](figures/mta_contrasts.png)

## 6. What should a forecaster do?

If the better representation reverses between years and sources, choosing it from past performance may not help. We compared always-typed, always-pooled, an equal-weight average of the typed and pooled point forecasts, and (for India, where an earlier event year exists) a rule that uses in 2025 whichever representation had the lower 2024 balanced MASE. Regret is MASE minus that of the better representation in hindsight for the same cell; it can be negative for the average. The rules were chosen after the instability had been observed, so this analysis is exploratory. Its first protocol was committed before any combined forecast was computed; it contained a filter that dropped the NYC local specifications, and a corrected second version was committed after the first version's India results existed. Both versions are retained. In the one cell where the 2024 MASEs were exactly equal (Stable LightGBM day flags, lead 1), the registered code picks pooled.

Following the 2024 winner picks the worse representation in 2025 in {N['worse']} of 36 cells, and its mean regret ({N['follow_r']}) is close to the {N['random_r']} expected from a random pick. The average has lower mean regret ({N['comb_r']}) and beats the follow rule in {N['beats']} of 36 cells, but this difference is not distinguishable from noise (sign test p {N['sign_p']}), median regret favours the follow rule ({N['med_follow']} versus {N['med_comb']}), and most of the mean difference comes from Rich Ridge window cells at leads 7 and 14. The clearer difference is in the worst case: the largest 2025 regret is {N['max_comb']} for the average and {N['max_follow']} for the follow rule (Table 6, Figure 4).

No fixed representation is best in both sources. Over both years, mean regret in India is {N['mt_i']} for always-typed, {N['mp_i']} for always-pooled and {N['mc_i']} for the average; in NYC it is {N['mt_n']}, {N['mp_n']} and {N['mc_n']}, so always-typed beats the average there on the mean. The largest regret of the average is below that of both fixed choices in both sources (India {N['xc_i']} against {N['xt_i']} and {N['xp_i']}; NYC {N['xc_n']} against {N['xt_n']} and {N['xp_n']}), although in NYC only narrowly. By construction, the absolute error of an equal-weight average is at most the mean of the two absolute errors, so the average cannot be worse than the worse representation; its mean regret is {N['regret_i']} in India against that bound of {N['bound_i']}, and {N['regret_n']} against {N['bound_n']} in NYC, and it beats both representations in {N['below_both_i']} of 36 Indian cells and {N['below_both_n']} of 36 NYC cells (Appendix Table A11 for NYC lead 1). None of the average-versus-single differences is distinguishable by the cluster tests. The practical reading is modest: when a representation cannot be chosen reliably, averaging the two forecasts limits the worst case; it is not shown to improve typical accuracy, and estimated combination weights were not tried.

Table 6. India, lead 1: balanced MASE over both years for typed, pooled and their average, and 2025 regret of the follow-2024 rule and of the average.

{chr(10).join(t_comb)}

![Figure 4. India 2025 regret relative to the hindsight-better representation, for the follow-2024 rule and the equal-weight average, by model, representation and lead.](figures/decision_rules.png)

## 7. Uncertainty and reproducibility

Both foundation models are compared on their native quantiles 0.1–0.9 (Table 7). Means hide dispersion across event clusters: at lead 1, family/year coverage of the nominal 80% interval falls below 0.80 in 85 of 100 cluster/arm cells (Appendix Table A5). This cohort has 0 crossing quantile pairs and 0 invalid interval endpoints.

Table 7. Native Indian festival-window 80% intervals at lead 1.

{table('Table 6')}

Separate audits reconstruct source transformations, dates, cohorts, scales, inputs, local fit/query arrays, label purging and metrics. Complete clean-environment reruns of all 5,952 direct-comparator forecasts and 2,560 simulation cells are byte-identical, and an isolated NYC rerun reproduces all 4,032 local forecasts. These are internal software checks on one machine, not independent review. Earlier numerical failures are retained: a float64 tree reproduction failed before a separately named float32 revision, and 15 of 45 Delhi lead-1 near-zero feature entries differ after float32 conversion. A controlled simulation (512 datasets, 2,560 method cells; Figure 5) reproduces the familiar pooling trade-off under homogeneous versus heterogeneous effects; it does not explain foundation-model internals.

![Figure 5. Synthetic pooling conditions. Intervals show Monte Carlo precision over generator seeds.](figures/simulation.png)

## 8. Limitations

The evidence is conditional on source, event definition, representation, horizon and adaptation policy. India has two event years and 10 family-year clusters; NYC contributes two observances in one city; the NESO check has no holiday targets. A drafted Singapore replication was not registered because the history start and licence scope of the source could not be verified. Weather, supply constraints, coincident observances, source revisions and calendar amendments are alternative explanations. Local models are refitted monthly and foundation models are frozen, so their histories and adaptation differ. Weight dates do not rule out correlated pretraining exposure [5]. The Ziel adaptations treat only the five festival families and were run for the local models only. The decision-rule analysis is retrospective, uses forecasts whose single-representation results had already been inspected, and covers only simple rules (no estimated weights or cross-family selection). No naive benchmark was run on the Indian festival cases. The registrations made on 6–7 November 2026 were local commits not yet pushed when this draft was built, so their order rests on the author's commit history and file time stamps rather than a public timestamp.

Two prospective components are pending: frozen forecasts for 31 October–11 November 2026, to be scored with the first complete actual vintage from 12 November, and a registered weekly rolling study that is not yet activated. Neither tests the typed-versus-pooled hypothesis directly.

## 9. Conclusion

On matched cases with complete controls, neither typed nor pooled festival indicators is reliably better: the ordering changes between years, models and data sources, and with 10 event clusters no ordering can be confirmed. Festival information itself helps the local specifications in Indian festival windows, beyond what zero and placebo channels give, and Ziel-style designs do not change that picture in a way that transfers to NYC. When the representation cannot be chosen in advance, following last year's winner did no better than a random pick, and averaging the typed and pooled forecasts limited the worst case in both sources. Confirming any of these orderings requires future event years with calendars verified before the outcomes exist.

## Declarations

**Data availability.** Code, protocols, forecasts, failures and audits are at https://github.com/Binay-verma/tsaf_project (the work of 6–7 November 2026 must be pushed there before submission). The GRID-INDIA/POSOCO compilation curated by Robbie Andrew is in the repository; its reuse terms are unresolved and a request to the curator is pending. The MTA snapshot is an attributed minimal filtered extract. NESO raw archives are kept outside the repository. Model weights are not redistributed.

**Funding.** __________ [author to confirm].

**Competing interests.** __________ [author to confirm].

**Author contribution.** Binay Verma: __________ [author to complete, CRediT roles].

**Use of generative AI.** __________ [author to complete according to the journal's policy before submission].

## References

[1] Kreusel et al. (2026). On the Encoding of Calendar Features in Covariate-Informed Time Series Foundation Models. arXiv:2610.13676v1. https://arxiv.org/abs/2610.13676

[2] Alipour et al. Impact-driven event covariates for time-series foundation models. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models

[3] Sanyal, Mitra, McElroy and Roy (2017). Holiday Effects in Indian Manufacturing Series. U.S. Census Bureau RRS2017-04. https://www.census.gov/library/working-papers/2017/adrm/rrs2017-04.html

[4] Kaljevic, Arzola and Zhang (2026). Benchmarking Time Series Foundation Models for Load Forecasting Under Covariate Uncertainty. arXiv:2610.07232v1. https://arxiv.org/abs/2610.07232

[5] Meyer et al. Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges. arXiv:2510.13654v3. https://arxiv.org/abs/2510.13654

[6] Ansari et al. (2025). Chronos-2: From Univariate to Universal Forecasting. arXiv:2510.15821v1. https://arxiv.org/abs/2510.15821

[7] Jain and Sen (2026). TimesFM-3: A zero-shot foundation model for multivariate forecasting. Google Research. https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/

[8] Romano, Patterson and Candès (2019). Conformalized Quantile Regression. arXiv:1905.03222v1. https://arxiv.org/abs/1905.03222

[9] Ziel (2018). Modeling public holidays in load forecasting: a German case study. Journal of Modern Power Systems and Clean Energy 6(2), 191–207. https://doi.org/10.1007/s40565-018-0385-5

[10] Arora and Taylor (2018). Rule-based autoregressive moving average models for forecasting load on special days: A case study for France. European Journal of Operational Research 266(1), 259–268. https://doi.org/10.1016/j.ejor.2017.08.056

[11] Bates and Granger (1969). The combination of forecasts. Operational Research Quarterly (now Journal of the Operational Research Society). https://doi.org/10.1057/jors.1969.103

[12] Claeskens, Magnus, Vasnev and Wang (2016). The forecast combination puzzle: A simple theoretical explanation. International Journal of Forecasting 32(3), 754–762. https://doi.org/10.1016/j.ijforecast.2015.12.005

## Appendix A. Companion tables

Table A1. NYC ordinary sample: decision lead 1 (model step 8), MASE.

{table('Table A1')}

Table A2. Fixed response-profile comparators on the original Indian case ledger (separate, unchanged sensitivity).

{table('Table A2')}

Table A3. Day-representation lead-1 Spearman diagnostics of past support and response heterogeneity. n counts family/state/year cells, not independent replications.

{table('Table A3')}

Table A4. Indian typed-minus-pooled MASE at lead 1 by event year and family. Positive favours pooling. LOFO: leave-one-family-out balanced contrast.

{table('Table A4')}

Table A5. Native 80% coverage across the ten Indian family/year clusters at lead 1.

{table('Table A5')}

Table A6. Pure daily calendar encodings for the foundation models on Indian festival windows, lead-1 MASE.

{table('Table 3')}

Table A7. NESO calendar models at decision lead 1: ideal (model step 1) versus 21-day delay (model step 22), MASE.

{table('Table 5')}

Table A8. Indian lead-1 contrasts for the Ziel adaptations. Negative favours the first arm. Label: consistent = same sign in both years and every leave-one-family-out subset; negligible = absolute value below 0.005; otherwise unstable.

{table('Table A7')}

Table A9. Ziel adaptations on NYC event windows: decision lead 1, local-model MASE.

{table('Table A8')}

Table A10. NYC lead-1 contrasts for the Ziel adaptations (modes in place of years).

{table('Table A9')}

Table A11. NYC, decision lead 1: balanced MASE for typed, pooled and their equal-weight average.

{chr(10).join(t_comb_n)}

Table A12. Controls at lead 1 (India) and decision lead 1 (NYC), MASE. History: no covariates; Cal.: calendar; + zeros: calendar plus five zero channels; Placebo: weekday-shifted typed day flags; Typed, Pooled: day flags. A dash marks an arm that was not run for that model.

{chr(10).join(t_ctl)}

All leads, cohorts and registered contrasts are in the supplement CSV files.
"""

# guards: every v7 table used exactly once, rows unchanged
used = re.findall(r"\{table\('([^']+)'\)\}", Path(__file__).read_text())
assert sorted(used) == sorted(set(used)) and len(used) == 15, used
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V7/'figures', OUT/'figures')
subprocess.run([sys.executable, str(ROOT/'src/figures_journal_v8.py'), str(OUT/'figures')], check=True)
shutil.copytree(V7/'supplement', OUT/'supplement')
for d, prefix in [(CI, 'cluster_inference'), (RC, 'combination')]:
    for f in sorted(d.glob('*.csv')):
        shutil.copy2(f, OUT/'supplement'/f'{prefix}_{f.name}')
(OUT/'MANUSCRIPT.md').write_text(md)
docx = OUT/'Typed_or_Pooled_Binay_Verma_v8.docx'
subprocess.run(['pandoc', str(OUT/'MANUSCRIPT.md'), '-o', str(docx), '--resource-path', str(OUT)], check=True)
subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v8-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(docx)],
               check=True, capture_output=True)
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v8 for supervisor review; not submitted; not independently reviewed.',
               base={'manuscript/integrated_review_v7/MANUSCRIPT.md': sha(V7/'MANUSCRIPT.md')},
               new_inputs={str(p.relative_to(ROOT)): sha(p) for d in (CI, RC) for p in sorted(d.glob('*'))},
               v7_tables_copied=used, words_main_text=len(md.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in [OUT/'MANUSCRIPT.md', docx]}), open(OUT/'build.json', 'w'), indent=1)
print('built', len(md.split()), 'words')
