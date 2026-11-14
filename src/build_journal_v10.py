"""Build journal-format draft v10: v9 text plus the registered new-states test, the calibrated simulation and the
exploratory follow-ups. Every new number is read from committed result files here and asserted where restated.
v9 text is changed only by the explicit, asserted replacements below.
Run from the repository root: python src/build_journal_v10.py
"""
import csv, datetime, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V9 = ROOT/'manuscript/journal_v9'
OUT = ROOT/'manuscript/journal_v10'
NS = ROOT/'results/new_states_v1'
AN = NS/'analysis'
DG = ROOT/'results/new_states_v1_diagnostics'
S1 = ROOT/'results/simulation_typed_pooled_v1'
S2 = ROOT/'results/simulation_typed_pooled_v2'
C1 = ROOT/'results/simulation_calibration_v1'
C2 = ROOT/'results/simulation_calibration_v2'
C3 = ROOT/'results/simulation_calibration_v3_timesplit'
IC = ROOT/'results/new_states_v1_independent_check'
NAMES = {'ridge': 'Rich Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'Stable LightGBM', 'lightgbm_capacity2': 'Tree leaf minimum 2',
         'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
ORDER = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return list(csv.DictReader(open(p)))


def s4(x):
    x = float(x)
    return ('+' if x > 0 else '−' if x < 0 else '') + f'{abs(x):.4f}'


def p3(x):
    return f'{float(x):.3f}'


md = (V9/'MANUSCRIPT.md').read_text()


def rep(old, new):
    global md
    assert md.count(old) == 1, old[:80]
    md = md.replace(old, new)


# ---------------- numbers ----------------
design = json.load(open(NS/'design_summary.json'))
summ = json.load(open(AN/'summary.json'))
H = {r['hypothesis']: r for r in read(AN/'hypothesis_tests.csv')}
NC = {r['hypothesis']: r for r in read(AN/'sensitivity_without_2020_2021.csv')}
OF = {r['hypothesis']: r for r in read(AN/'sensitivity_official_sources_only.csv')}
assert summ['decisions'] == {'H1': 'CONFIRMED', 'H2': 'NOT CONFIRMED', 'H3': 'CONFIRMED'}
assert design['event_cases'] == 5157 and design['clusters'] == 45
for h in H:
    assert H[h]['decision'] == summ['decisions'][h]
bal = {(r['model'], r['arm']): float(r['MASE']) for r in read(AN/'balanced.csv') if r['horizon'] == '1'}
loo = read(DG/'leave_one_out.csv')
hz = {(r['model'], r['horizon']): r for r in read(DG/'by_horizon.csv')}
phys = {r['model']: r for r in read(DG/'physical_units.csv')}
pw = {r['hypothesis']: r for r in read(DG/'power.csv')}
ctl = {(r['model'], r['arm']): r for r in read(DG/'against_controls.csv')}
cal1 = json.load(open(C1/'calibration.json'))
cross = {r['part']: r for r in read(S2/'crossover.csv') if r['part'] == 'A'}
sA = {float(r['h']): r for r in read(S2/'summary.csv') if r['part'] == 'A'}
leafs = {(int(r['leaf']), float(r['h'])): float(r['mean']) for r in read(S2/'summary.csv') if r['part'] == 'C'}
lby = read(S2/'leaf_by_year.csv')
cal_states = {r['state']: r for r in read(C2/'calibration_by_state.csv')}
obs2 = read(C2/'predicted_vs_observed_new_states.csv')
agree3 = {r['model']: (int(r['sum']), int(r['count'])) for r in read(C3/'agreement_by_model.csv')}
same_years = {}
for m in ['ridge', 'sarimax']:
    rows = [r for r in obs2 if r['model'] == m and r['h_crossover'] not in ('', 'nan')]
    rows += [r for r in obs2 if r['model'] == m and r['h_crossover'] in ('', 'nan')]
    ok = sum((float(r['observed_typed_minus_pooled']) < 0) == (r['predicted_linear'] == 'typed') for r in obs2 if r['model'] == m)
    same_years[m] = ok
assert same_years['ridge'] == 7 and agree3['ridge'] == (5, 7) and agree3['sarimax'] == (5, 7)
h_cal, h_lo, h_hi = cal1['h']['point'], cal1['h']['lo'], cal1['h']['hi']
mu_cal = cal1['mu']['point']
hstar = float(cross['A']['h_crossover'])
hA = min(sA, key=lambda k: abs(k - h_cal))
loo_h = {h: [r for r in loo if r['hypothesis'] == h and r['left_out'] != 'none'] for h in ['H1', 'H2', 'H3']}
kept = {h: sum(r['direction_kept'] == 'True' for r in v) for h, v in loo_h.items()}
sig = {h: sum(float(r['p_one_sided']) < .05 for r in v) for h, v in loo_h.items()}
assert kept == {'H1': 16, 'H2': 8, 'H3': 16} and sig['H1'] == 15 and sig['H3'] == 14
tf7, tf14 = hz[('timesfm', '7')], hz[('timesfm', '14')]
assert float(tf7['typed_minus_pooled']) < 0 and float(tf14['typed_minus_pooled']) < 0
lg_ctl = ctl[('lightgbm', 'day5')]
assert float(lg_ctl['minus_zero5']) == 0.0
gj = {r['model']: float(r['observed_typed_minus_pooled']) for r in obs2 if r['state'] == 'Gujarat'}
tn = {r['model']: float(r['observed_typed_minus_pooled']) for r in obs2 if r['state'] == 'Tamil Nadu'}


# ---------------- further numbers (added after the internal referee check) ----------------
SAa = {r['model']: float(r['typed_minus_pooled']) for r in read(ROOT/'results/longer_panel_stage_a_v1/analysis/typed_vs_pooled.csv')
       if r['representation'] == 'day' and r['lead'] == '1'}
SBb = {r['model']: float(r['typed_minus_pooled']) for r in read(ROOT/'results/longer_panel_stage_b_v1/analysis/hypothesis_tests.csv')}
gjo = {r['hypothesis']: float(r['effect']) for r in loo if r['left_out'] == 'state: Gujarat'}
grp = {(r['subset'], r['hypothesis']): r for r in read(ROOT/'results/new_states_v1_official_plus_confirmed/by_state_group_all_rows.csv')}
south, north = 'AP+TS+TN, all rows', 'UP+RJ+MP+GJ, all rows'
assert grp[(north, 'H1')]['decision'] == 'CONFIRMED' and grp[(south, 'H2')]['decision'] == 'CONTRADICTED'
ncells = len(hz)
bonf7, bonf14 = min(1, ncells*float(tf7['p_two_sided'])), min(1, ncells*float(tf14['p_two_sided']))
srch = []
for f in ['found_UP_MP.csv', 'found_RJ_GJ.csv', 'found_AP_TS_TN.csv']:
    srch += read(ROOT/'review/new_states_v1/official_source_search_2026-11-15'/f)
n_match = sum(r['status'] == 'match' for r in srch)
n_match_gov = sum(r['status'] == 'match' and r['state'] == 'Rajasthan' for r in srch)
assert len(srch) == 241 and n_match == 35 and n_match_gov == 4
tf_south = float(grp[(south, 'H2')]['typed_minus_pooled'])
cal3 = [s for s in ['Delhi', 'Karnataka', 'Maharashtra']]
above = [s for s in ['Tamil Nadu', 'Gujarat', 'Rajasthan'] if float(cal_states[s]['h_lo']) > float(cal_states[s]['h_crossover'])]
assert above == ['Tamil Nadu', 'Gujarat']
agree_other = {m: agree3[m] for m in ['chronos', 'timesfm', 'lightgbm']}
assert all(v == (4, 7) for v in agree_other.values())

S3 = ROOT/'results/simulation_typed_pooled_v3'
v3 = {(r['model'], float(r['h'])): float(r['mean']) for r in read(S3/'summary.csv')}
hv3 = min({h for _, h in v3}, key=lambda v: abs(v - h_cal))
assert abs(v3[('ridge', hv3)] - (-0.0133)) < 0.001 and v3[('lgbm_leaf20', hv3)] == 0.0
FM = {(r['design'][:4], r['model']): r for r in read(ROOT/'results/new_states_v1_family_mechanism/spearman.csv')}
rho_r_same, rho_r_oot = FM[('same', 'ridge')], FM[('out ', 'ridge')]
rho_s_same, rho_s_oot = FM[('same', 'sarimax')], FM[('out ', 'sarimax')]
rho_t_oot = FM[('out ', 'timesfm')]
fe = {(r['state'], r['family']): float(r['effect']) for r in read(ROOT/'results/new_states_v1_family_mechanism/family_effects_2017_2025.csv')}
share5 = 0.524
SS = ROOT/'results/simulation_states_v3_seedcheck'   # reproducible (stable-seed) run
SV = {r['state']: r for r in read(SS/'predicted_vs_observed_2021_2025.csv')}
SCall = read(SS/'state_level_correlations.csv')
SC = {(r['predicted'], r['observed']): r for r in SCall if r['states'] == 'all 7'}
SC2 = {(r['predicted'], r['observed']): r for r in SCall if r['states'] == 'without Gujarat and Tamil Nadu'}
SVm = json.load(open(SS/'summary.json'))
agree6 = sum(((SV[k]['predicted_ridge_direction'] == 'typed') == (float(SV[k]['observed_ridge']) < 0)) for k in SV if SV[k]['h_crossover'] not in ('', 'nan'))
assert agree6 == 4
c_r, c_s, c_2, c_st = (SC[('predicted_ridge', 'observed_ridge')], SC[('predicted_ridge', 'observed_sarimax')],
                       SC[('predicted_lgbm_leaf2', 'observed_lightgbm_capacity2')], SC[('predicted_stable_mix', 'observed_lightgbm')])
assert abs(float(c_r['pearson']) - 0.885) < 0.002 and abs(float(c_2['pearson']) - 0.891) < 0.002
FW = {(r['design'][:4], r['model']): r for r in read(ROOT/'results/new_states_v1_family_mechanism/within_state_and_without_GJ_TN.csv')}
share5A = 7/12   # Stage A 2022-2025 lead-1 fits with min leaf 5 (2022-23: 5/6, 2024-25: 2/6)

# ---------------- title, abstract, highlights ----------------
rep('# Typed or pooled festival indicators? The answer depends on the model class: Indian electricity evidence with a registered follow-up test',
    '# Typed or pooled festival indicators? Evidence from ten Indian states with registered tests')
rep('(journal format, version 9)', '(journal format, version 10)')
old_abs = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
new_abs = ("Forecasters adding festival indicators must choose between one indicator per festival (typed) and one shared indicator (pooled). "
           "We compare both for daily electricity in Indian states, with matched zero and placebo controls, two foundation models and four local "
           "models. In three exploratory states the better choice depended on the model. We registered three hypotheses and tested them once on "
           "seven further states over 2017–2025. As hypothesised, SARIMAX did better with typed indicators and a small-leaf LightGBM with a pooled "
           "indicator, but both effects were small and rested mainly on one state; neither held when calendars were restricted to official sources. "
           "The expected pooling preference of TimesFM-3 was not confirmed. Trees cannot use an indicator active on fewer training days than "
           "their minimum leaf size, which is why LightGBM with a larger leaf size ignored typed indicators. An exploratory simulation "
           "reproduces the main differences between states, mainly through two states.")
rep(old_abs, new_abs)
hl = ['- Typed and pooled festival flags compared with matched zero and placebo controls',
      '- Registered test in seven new states: SARIMAX prefers typed, leaf-2 trees pooled',
      '- Both confirmed effects are small and rest mainly on one state, Gujarat',
      '- The expected TimesFM-3 preference for a pooled flag was not confirmed',
      '- Trees ignore flags set on fewer training days than their minimum leaf size']
rep(md.split('## Highlights\n\n', 1)[1].split('\n\n', 1)[0], '\n'.join(hl))
assert all(len(l) - 2 <= 85 for l in hl), [len(l) - 2 for l in hl]

# ---------------- introduction ----------------
rep(md.split('An earlier version of this study', 1)[1].split('\n\n', 1)[0].join(['An earlier version of this study', '']),
    'An earlier version of this study, with two event years and 10 family-year clusters, found that the ordering changed between years, '
    'models and data sources and that no ordering could be confirmed. This version extends the evaluation in time and across states and '
    'adds two confirmatory steps. Our contributions are:')
rep('LightGBM and TimesFM-3 do better with one pooled flag (Sections 5.2 and 5.3).',
    'LightGBM and TimesFM-3 do better with one pooled flag (Sections 5.2 and 5.3); the TimesFM-3 part did not replicate in seven further states.')
rep(md.split('3. **A registered follow-up test.**', 1)[1].split('\n', 1)[0].join(['3. **A registered follow-up test.**', '']),
    '3. **Registered tests.** The pattern was written down as a hypothesis before three further Maharashtra years were evaluated '
    '(Section 5.4), and three hypotheses were then registered and tested once on seven further states (Section 5.7). Two were '
    'confirmed, with small effects that rest mainly on one state, and one was not.')
rep('4. **Decision rules for uncertain orderings.**', '4. **A mechanism for tree models.** Trees cannot use a flag that is set on fewer '
    'training days than their minimum leaf size. A simulation matched to the forecasting pipeline reproduces this; run with each '
    'state’s own earlier parameters, it reproduces the main differences between states for Ridge and trees, mainly through the two '
    'states with the most heterogeneous festivals (Sections 5.8 and 5.9; exploratory).\n5. **Decision rules for uncertain orderings.**')
rep('although that expectation was not registered as a hypothesis.', 'although that expectation was not registered as a hypothesis; '
    'registered later as H2, it did not replicate in seven further states (Section 5.7).')
rep('### 5.4 Stage B: registered test on further years',
    'The TimesFM-3 preference for pooling did not replicate in the registered test on seven further states (Section 5.7).\n\n'
    '### 5.4 Stage B: registered test on further years')

# ---------------- data ----------------
rep('| Stage B (Section 5.4) | confirmatory | Maharashtra | 2019–2021 | 327 | – | 15 | 4 local |',
    '| Stage B (Section 5.4) | confirmatory | Maharashtra | 2019–2021 | 327 | – | 15 | 4 local |\n'
    f"| New states (Section 5.7) | confirmatory | 7 | 2017–2025 | {design['event_cases']:,} | – | {design['clusters']} | 6 |")
new_data = ("### 3.5 Seven further states\n\n"
            "The registered test of Section 5.7 uses the same GRID-INDIA/POSOCO series for Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat, "
            "Telangana, Andhra Pradesh and Tamil Nadu. Their festival calendars for 2015–2025 (331 rows) were assembled before any model was "
            "fitted to these states. The conventions, refined while the rows were sourced and fixed before any forecast, are: the festival day "
            "itself is flagged, not a substitute holiday; a family is in scope for a state if it is a public holiday there in most years; weekend "
            "festivals stay flagged; years in which a festival is only an optional holiday get no flag. Of the 331 rows, 90 come from official "
            "notifications or government reproductions and 241 from secondary sources (reposts of the notifications on teacher, employee and "
            "HR-compliance sites, holiday-listing aggregators and, for a few rows, news reports). The author reported checking every row; the method of each check was not "
            "recorded per row, and evidence is recorded for disputed rows. After the registered analysis, a search for the original "
            f"notifications behind the 241 secondary rows found matching dates for {n_match} of them ({n_match_gov} in official gazette copies, "
            f"the rest in third-party copies of the government orders) and no new discrepancy; the rest could not be read, because official "
            "portals block automated access and the copies found are image-only scans. On average 5.33 states contribute to each "
            "family-year cluster.\n\n"
            "## 4. Models, representations and evaluation")
rep('## 4. Models, representations and evaluation', new_data)

# ---------------- registration sequence ----------------
reg_new = ("\n\nFor the seven further states, the protocol, hypotheses, test, decision rule, sensitivities and the hash of the analysis "
           "script were committed at 13:27 UTC on 13 November 2026, before any parameter selection or forecast for these states. The OSF "
           "registration (osf.io/yw7mr) was submitted no later than 14:02 UTC (the commit recording it), after the parameter selection for the local models (ordinary "
           "calendar only) had started but before any forecast with festival indicators. Times are author timestamps; later rebases changed "
           "the committer timestamps of some commits but not their content. Foundation forecasts were run in a hosted notebook; two runs whose "
           "final upload failed were recovered from the notebook output, and their prediction files match the hashes the runs wrote. The "
           "analysis script, unchanged from registration, was run once at 21:28 UTC on 14 November 2026. The first simulation design of Section 5.8, "
           "with its three-state calibration, was committed (by author timestamp) before the new-states analysis; the pipeline-matched "
           "version and its per-state predictions were designed after that analysis, and after the first version's effect sizes were seen to "
           "be too large, with each design committed before its single run. Everything in Section 5.9 was written after the analysis and is "
           "exploratory.")
rep('Stage B is a registered follow-up test on data that were public but not yet evaluated.',
    'Stage B is a registered follow-up test on data that were public but not yet evaluated.' + reg_new)
rep('tests are two-sided except the registered Stage B tests, which are one-sided in the hypothesised direction.',
    'tests are two-sided except the registered Stage B and new-states tests, which are one-sided in the hypothesised direction. '
    'With 45 clusters the new-states test uses 1,000,000 Monte Carlo sign assignments (fixed seed), with p = (k+1)/(N+1).')

# ---------------- tables ----------------
def hrow(h, label, exp):
    r = H[h]
    return (f"| {h} {label} ({exp}) | {s4(r['typed_minus_pooled'])} | {r['years_in_direction']}/9 | {float(r['p_one_sided']):.4f} | "
            f"{float(r['holm']):.3f} | {r['decision'].lower()} |")


def srow(h, label):
    return f"| {h} {label} | {NC[h]['decision'].lower()} ({s4(NC[h]['typed_minus_pooled'])}) | {OF[h]['decision'].lower()} ({s4(OF[h]['typed_minus_pooled'])}) |"


t12 = '\n'.join(['| Hypothesis | Typed − pooled | Years | One-sided p | Holm p | Decision |',
                 '| -------------------------- | ---------- | ------- | ---------- | -------- | --------------- |',
                 hrow('H1', 'SARIMAX', '−'), hrow('H2', 'TimesFM-3', '+'), hrow('H3', 'LightGBM leaf 2', '+')])
t12b = '\n'.join(['| Hypothesis | Without 2020–2021 (35 clusters) | Official calendar sources only (44 clusters) |', '| --- | --- | --- |',
                  srow('H1', 'SARIMAX'), srow('H2', 'TimesFM-3'), srow('H3', 'LightGBM leaf 2')])
t13 = ['| Model | Calendar | + zeros | Placebo | Typed day | Pooled day |', '| --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    g = lambda a: f"{bal[(m, a)]:.5f}" if (m, a) in bal else '–'
    t13.append(f"| {NAMES[m]} | {g('calendar')} | {g('zero5')} | {g('placebo_day5')} | {g('day5')} | {g('pooled_day5')} |")
t14 = ['| Model | Lead 1 | Lead 7 | Lead 14 | Lead-1 GWh |', '| --- | --- | --- | --- | --- |']
for m in ORDER:
    t14.append(f"| {NAMES[m]} | {s4(hz[(m, '1')]['typed_minus_pooled'])} | {s4(hz[(m, '7')]['typed_minus_pooled'])} | "
               f"{s4(hz[(m, '14')]['typed_minus_pooled'])} | {s4(phys[m]['typed_minus_pooled_GWh'])} |")
t15 = ['| State | Effect μ, 2015–20 | h, 2015–20 | Threshold h* | Ridge predicted | Ridge observed | Leaf-2 predicted | Leaf-2 observed |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
o2 = {(r['model'], r['state']): float(r['observed_typed_minus_pooled']) for r in obs2}
for st in ['Tamil Nadu', 'Gujarat', 'Rajasthan', 'Telangana', 'Andhra Pradesh', 'Madhya Pradesh', 'Uttar Pradesh']:
    c = SV[st]
    hs = f"{float(c['h_crossover']):.2f}" if c['h_crossover'] not in ('', 'nan') else 'n/a'
    t15.append(f"| {st} | {float(c['mu'])*100:+.1f}% | {float(c['h']):.2f} | {hs} | {s4(c['predicted_ridge'])} | {s4(c['observed_ridge'])} | "
               f"{s4(c['predicted_lgbm_leaf2'])} | {s4(c['observed_lightgbm_capacity2'])} |")
t16 = ['| State group | H1 SARIMAX | H2 TimesFM-3 | H3 LightGBM leaf 2 |', '| --- | --- | --- | --- |']
for name, lab in [(north, 'Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat'), (south, 'Andhra Pradesh, Telangana, Tamil Nadu')]:
    dec = {'CONFIRMED': 'meets rule', 'NOT CONFIRMED': 'does not meet rule', 'CONTRADICTED': 'opposite direction'}
    t16.append(f"| {lab} | " + ' | '.join(f"{s4(grp[(name, h)]['typed_minus_pooled'])} ({dec[grp[(name, h)]['decision']]})" for h in ['H1', 'H2', 'H3']) + ' |')

sec57 = f"""### 5.7 Registered test in seven further states

Three hypotheses were registered for lead 1 and day flags: H1, SARIMAX does better with typed flags; H2, TimesFM-3 does better with a pooled flag; H3, the leaf-2 LightGBM does better with a pooled flag. The decision rule was a Holm-adjusted one-sided p below 0.05 with the hypothesised sign in at least six of nine event years; a result in the opposite direction with unadjusted p below 0.05 counts as contradicted. Table 12 gives the result. H1 and H3 are confirmed (Holm p {p3(H['H1']['holm'])} each; six and eight of nine years) and H2 is not ({s4(H['H2']['typed_minus_pooled'])}, three of nine years). Table 13 shows that both flag types improve Ridge, SARIMAX and the leaf-2 LightGBM over the calendar, zero-channel and placebo arms, while Stable LightGBM does not change at all with typed flags and improves only with the pooled flag. The confirmed effects are much smaller than the exploratory ones: SARIMAX went from {s4(SAa['sarimax'])} in Stage A and {s4(SBb['sarimax'])} in Stage B to {s4(H['H1']['typed_minus_pooled'])}, and the leaf-2 LightGBM from {s4(SAa['lightgbm_capacity2'])} and {s4(SBb['lightgbm_capacity2'])} to {s4(H['H3']['typed_minus_pooled'])}. The registration expected about 0.9 power at the Stage A size; at the observed size the SARIMAX test was underpowered (Section 5.9).

Table 12b gives the registered sensitivities. Without 2020–2021, the H1 effect is almost unchanged ({s4(NC['H1']['typed_minus_pooled'])}) but no longer significant with 35 clusters (Holm p {p3(NC['H1']['holm'])}, four of seven years); H3 holds. With official calendar sources only, no hypothesis is confirmed, the H3 sign reverses, and H2 is contradicted (typed better, unadjusted opposite-direction p {float(OF['H2']['p_opposite']):.3f}). That sensitivity removes Gujarat, Rajasthan and Uttar Pradesh completely and keeps 85 state-family-year cells, 74 of them from Tamil Nadu and Telangana. Running those southern states with all their calendar rows gives the same decisions (Section 5.9), so the sensitivity mainly reflects which states remain; whether calendar quality matters in the other states, which have almost no official rows, remains untested.

Table 12. Seven further states (2017–2025, {design['clusters']} clusters, {design['states_per_cluster']} states per cluster): registered tests at lead 1, day flags, typed minus pooled MASE. Holm across H1–H3. (−) expects typed better, (+) pooled better. Years: years with the expected sign.

{t12}

Table 12b. Decisions (and typed minus pooled MASE) under the two registered sensitivities.

{t12b}

Table 13. Seven further states: lead-1 event MASE by arm. Foundation models were run without the zero and placebo arms.

{chr(10).join(t13)}

### 5.8 A mechanism, and a simulation

Tree models need a minimum number of training days on each side of a split. A typed flag is set on one training day per year, so a tree with minimum leaf size L cannot split on it until there are L training years, while the pooled flag is set about five times as often. In the empirical models the trees are trained on a 730-day window, in which a typed flag is set on at most about four days; Stable LightGBM's selected minimum leaf sizes (5 or 20 in the new states, 20 in Stage B) are never reached, which is why its typed arm equals its calendar arm in Stage B and in Table 13, while the pooled flag, set on up to about a dozen days, can be used.

A synthetic study illustrates this and the trade-off for a linear model. It covers Ridge and LightGBM only, not SARIMAX or the foundation models. Daily series with weekly and annual cycles and autoregressive noise carry five festival families whose effects are μ(1 + h·z), where z takes five fixed values with mean 0 and standard deviation 1 and h measures how much the families differ, plus occurrence noise; it is calibrated to the three original states (festival-day effect {mu_cal*100:.1f}%, or −9.9% when the neighbouring days are modelled as well, so the window profile below adds neighbouring-day effects without changing the festival-day effect; h {h_cal:.2f} with a 90% year-bootstrap band {h_lo:.2f}–{h_hi:.2f}). A first version, committed before the new-states analysis, used one-day effects, trained on all earlier years and scored the festival day only; it reproduced the directions but gave effects about ten times the observed ones ({abs(float(sA[hA]['mean'])):.2f} MASE for Ridge at the calibrated h). After that analysis, and after this mismatch had been seen, a second version was built to match the forecasting pipeline in three respects only: each festival's effect is spread over its window with the profile measured on the three original states (the day after a festival keeps about two thirds of the festival-day effect), models are refitted monthly on the previous 730 days, and every day of the ±3-day window is scored. At the calibrated h it gives {s4(v3[('ridge', hv3)])} for Ridge, against {s4(SAa['ridge'])} observed in Stage A; exactly zero in every replication for a LightGBM with minimum leaf size 20, as for Stable LightGBM's typed arm; {s4(v3[('lgbm_leaf5', hv3)])} with leaf size 5, which at Stage A's lead-1 mix of selected leaf sizes (5 in {round(share5A*12)} of 12 fits, otherwise 20) implies about {s4(share5A*v3[('lgbm_leaf5', hv3)])} against {s4(SAa['lightgbm'])} observed; and {s4(v3[('lgbm_leaf2', hv3)])} with leaf size 2, against {s4(SAa['lightgbm_capacity2'])} in Stage A (Figure 3). These comparisons are in-sample, because the calibration, the window profile and Stage A use the same three states. Applied unchanged to the seven further states, the three-state parameters overstate the tree effects there by a factor of about 2.6 to 4.5; the per-state, out-of-time check in Section 5.9 uses each state's own earlier parameters instead. In this version Ridge typed flags start to win between h = 0.25 and h = {hv3:.2f}.

![Figure 3. Pipeline-matched simulation calibrated to the three original states (exploratory; designed after the registered analysis). Left: Ridge typed minus pooled MASE against festival-effect heterogeneity h (shaded: calibrated 90% band; cross: observed Stage A value). Right: LightGBM at the calibrated h for minimum leaf sizes 2, 5 and 20 (bars), the implied value for Stable LightGBM at Stage A's lead-1 mix of leaf sizes (circle), and observed Stage A values (crosses). Positive values favour pooling.](figures/figure3_simulation.png)

### 5.9 Exploratory follow-ups

The analyses in this section were written after the registered test and are not confirmatory.

**Robustness and power.** Leaving out one state or one year at a time (unadjusted one-sided p), H1 keeps its sign in {kept['H1']} of 16 cases (p below 0.05 in {sig['H1']}) and H3 in {kept['H3']} of 16 ({sig['H3']}). Both depend most on Gujarat: without it, H1 shrinks from {s4(H['H1']['typed_minus_pooled'])} to {s4(gjo['H1'])} and H3 from {s4(H['H3']['typed_minus_pooled'])} to {s4(gjo['H3'])}, and all 44 Gujarat calendar rows come from secondary sources. H2 has no consistent sign ({kept['H2']} of 16). With 45 clusters, the minimum effect detectable with 80% power is about {float(pw['H1']['mde_80pct_one_sided_alpha05']):.3f} MASE for H1, larger than the observed {abs(float(H['H1']['typed_minus_pooled'])):.4f}.

**Regions.** Table 16 splits the seven states into two groups, a split chosen after seeing the results and applied with all calendar rows. In Uttar Pradesh, Rajasthan, Madhya Pradesh and Gujarat, typed flags help SARIMAX ({s4(grp[(north, 'H1')]['typed_minus_pooled'])}), carried mainly by Gujarat ({s4(o2[('sarimax', 'Gujarat')])}), while Uttar Pradesh goes the other way ({s4(o2[('sarimax', 'Uttar Pradesh')])}); in Andhra Pradesh, Telangana and Tamil Nadu typed flags do not help SARIMAX ({s4(grp[(south, 'H1')]['typed_minus_pooled'])}), and there TimesFM-3 does better with typed flags ({s4(tf_south)}), the opposite of H2. The two groups also differ in festival mix: the southern states include Ganesh Chaturthi and Ugadi, the others mainly Holi, Dussehra and Diwali. Possible reasons are discussed below.

**Festivals.** If typing helps because festivals differ, the gain should be largest for festivals whose effect differs most from the state's average festival effect. Across the 27 state-festival pairs, that deviation is correlated with the typed advantage for Ridge (Spearman ρ {float(rho_r_same['spearman']):.2f}) and SARIMAX ({float(rho_s_same['spearman']):.2f}) when both are measured on 2017–2025, which is partly circular; measuring the effects on 2015–2020 and the gains on 2021–2025 leaves Ridge at {float(rho_r_oot['spearman']):.2f} (unadjusted p {float(rho_r_oot['p']):.3f}; twelve correlations were computed) and SARIMAX at {float(rho_s_oot['spearman']):.2f}. Within states, after removing each state's mean, the Ridge relation is weak ({float(FW[('same', 'ridge')]['within_state_spearman']):.2f} and {float(FW[('out ', 'ridge')]['within_state_spearman']):.2f}), so the pattern is mainly between states and is carried by Gujarat and Tamil Nadu. Both have strongly heterogeneous festival effects (Gujarat: Diwali {fe[('Gujarat', 'Diwali')]*100:.0f}%, Holi {fe[('Gujarat', 'Holi')]*100:.0f}%, Dussehra {fe[('Gujarat', 'Dussehra')]*100:.0f}%; Tamil Nadu: Diwali {fe[('Tamil Nadu', 'Diwali')]*100:.0f}%, its other festivals between {max(fe[('Tamil Nadu', f)] for f in ['Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa'])*100:.0f}% and {min(fe[('Tamil Nadu', f)] for f in ['Dussehra', 'Ganesh_Chaturthi', 'Ugadi_Gudi_Padwa'])*100:.0f}%) and large Ridge gains from typing, which is consistent with the mechanism; Uttar Pradesh has almost no festival effect.

**Size and horizons.** Averaged over states, the effects are small (Table 14): relative to pooled flags, typed flags reduce Ridge's mean absolute error by {abs(float(phys['ridge']['typed_minus_pooled_GWh'])):.2f} GWh and SARIMAX's by {abs(float(phys['sarimax']['typed_minus_pooled_GWh'])):.2f} GWh per festival-window day, against mean demand of {float(phys['ridge']['mean_actual_GWh']):.0f} GWh. At leads 7 and 14, TimesFM-3 does better with typed flags ({s4(tf7['typed_minus_pooled'])} and {s4(tf14['typed_minus_pooled'])}; unadjusted two-sided p {float(tf7['p_two_sided']):.3f} and {float(tf14['p_two_sided']):.4f}, {bonf7:.3f} and {bonf14:.3f} after Bonferroni over the {ncells} model-lead cells), with the same sign in both separately run cohorts. This was not a registered horizon, and the foundation runs had no zero or placebo arm while the pooled arm carries four all-zero channels, so an encoding effect cannot be excluded.

**States.** The average hides large differences between states (Table 15). To check the mechanism out of time, the pipeline-matched simulation was run for each further state with that state's own parameters estimated on 2015–2020, and its predictions were compared with the registered forecasts for 2021–2025. Averaged over the seven states it predicts {s4(SVm['state_means']['predicted_ridge'])} for Ridge (observed {s4(SVm['state_means']['observed_ridge'])}), {s4(SVm['state_means']['predicted_leaf2'])} for the leaf-2 LightGBM (observed {s4(SVm['state_means']['observed_leaf2'])}) and {s4(SVm['state_means']['predicted_stable_mix_0556'])} for Stable LightGBM at its lead-1 mix of leaf sizes (observed {s4(SVm['state_means']['observed_stable_lgbm'])}). Across states, predicted and observed sizes agree for Ridge (Pearson r {float(c_r['pearson']):.2f}, Spearman {float(c_r['spearman']):.2f}) and the leaf-2 LightGBM ({float(c_2['pearson']):.2f}, {float(c_2['spearman']):.2f}), less for Stable LightGBM ({float(c_st['pearson']):.2f}, {float(c_st['spearman']):.2f}) and SARIMAX, which is not simulated ({float(c_s['pearson']):.2f}). Without Gujarat and Tamil Nadu the Ridge agreement disappears ({float(SC2[('predicted_ridge', 'observed_ridge')]['pearson']):.2f}) while the leaf-2 agreement remains ({float(SC2[('predicted_lgbm_leaf2', 'observed_lightgbm_capacity2')]['pearson']):.2f}). There are clear misses: in Tamil Nadu both tree models do better with typed flags although the simulation predicts a pooled advantage, and in Rajasthan Ridge does better with typed flags although its 2015–2020 heterogeneity is about half its threshold. The predicted Ridge direction matches in {agree6} of the 6 states with a defined threshold (Uttar Pradesh, with no mean festival effect, has none). With seven states, a simulator designed after the registered analysis, and agreement driven by Gujarat and Tamil Nadu, this is supporting evidence, not a test. A test on 2027–2028 festivals with official calendars only has been drafted (results/prospective_2027_v1) but is not yet registered.

Table 14. Seven further states: typed minus pooled MASE by lead and, for lead 1, the difference in mean absolute error in GWh per festival-window day. Only the lead-1 values for SARIMAX, TimesFM-3 and the leaf-2 LightGBM are registered tests (Table 12); all other cells are exploratory. Negative favours typed flags.

{chr(10).join(t14)}

Table 15. Seven further states, out of time (exploratory): festival-day effect μ and heterogeneity h estimated on 2015–2020, the pipeline-matched simulation's Ridge threshold and predicted typed minus pooled MASE at that h, and the observed lead-1 values for 2021–2025. Uttar Pradesh had a positive mean effect in 2015–2020, so no threshold is defined.

{chr(10).join(t15)}

Table 16. Lead-1 typed minus pooled MASE by state group, all calendar rows, and whether the registered decision rule would be met in each group. The split was chosen after seeing the results and is not corrected for that choice (exploratory).

{chr(10).join(t16)}

![Figure 4. Out-of-time check of the pipeline-matched simulation for the seven further states (exploratory): predicted typed minus pooled MASE from 2015–2020 parameters against observed lead-1 values for 2021–2025. Left: Ridge. Right: LightGBM with minimum leaf size 2. Dashed line: equality.](figures/figure4_states.png)

## 6. What should a forecaster do?"""
rep('## 6. What should a forecaster do?', sec57)

# ---------------- guidance, reproducibility, limitations, conclusion ----------------
rep('Combined with the model-class result, a cautious reading is: typed flags suit SARIMAX; TimesFM-3 did better with a pooled flag; tree models can use rare flags only if their minimum leaf size allows it, and then did better with a pooled flag; and the average is a safe default when the choice is unclear.',
    'Combined with the model-class results, a cautious reading is: typed flags suited SARIMAX, an effect that rests mainly on one state; tree models can use a flag only if it is set on at least as many training days as their minimum leaf size, and with a small leaf size they did better with a pooled flag; TimesFM-3 showed no lead-1 preference in the new states; whether heterogeneity estimated from past data can guide the choice is not yet shown (Section 5.9); and the average is a safe default when the choice is unclear.')
rep('These are internal software checks, not independent review.',
    'These are internal software checks, not independent review. The new-states analysis was also recomputed by a second implementation, written by a separate automated agent from the registration text alone without access to the registered script; all effects, year counts and decisions agree, and p-values differ only by Monte Carlo noise (at most 0.0012 unadjusted, 0.0026 after Holm).')
old_lim = md.split('## 8. Limitations\n\n', 1)[1].split('\n\n', 1)[0]
rep(old_lim, 'The evidence covers ten states, five festival families and the years 2017–2025. Stage B uses one state that was also part of Stage A, '
    'its 2020–2021 values were Stage A training history, and its 15 clusters give limited power. In the seven further states, the two '
    'confirmed effects are small, much smaller than in Stages A and B, below the minimum detectable effect for H1, and driven mainly by '
    'one state, Gujarat, whose calendar rows all come from secondary sources; the southern states show a '
    'different pattern that is not explained here. Of the 331 calendar rows for these states, 241 come from secondary sources, and most could '
    'not be traced to the original documents. The TimesFM-3 preference for pooling seen in Stage A did not replicate. The per-state, regional '
    'and longer-lead findings were found after the registered test, and the foundation runs had no zero or placebo control. The simulation '
    'covers Ridge and LightGBM only; its pipeline-matched version was designed after the registered analysis and after the first '
    'version’s sizes were seen, its agreement with Stage A is in-sample, and its out-of-time state check rests on seven states. The order of the Stage A and B '
    'registrations rests on author commit timestamps; the new-states study is registered on OSF, recorded after local parameter selection had '
    'started but before any forecast with festival indicators. The foundation-model results for 2022–2023 come from a hosted notebook with '
    'Python 3.13; they reproduced the stored 2024 forecasts within tolerance but not bit for bit. Weather, supply constraints, coincident '
    'observances, source revisions and calendar amendments are alternative explanations; local models are refitted monthly and foundation '
    'models are frozen; weight dates do not rule out correlated pretraining exposure [5]. The decision-rule analysis is retrospective and covers '
    'only simple rules. The reuse terms of the electricity compilation are unresolved.')
old_conc = md.split('## 9. Conclusion\n\n', 1)[1].split('\n\n', 1)[0]
rep(old_conc, 'Festival day flags clearly improve Ridge and SARIMAX over a plain calendar, beyond what zero or placebo channels give. Whether typed '
    'or pooled flags are better depends on the model and on the festivals. In a registered test on seven further states, SARIMAX did better '
    'with typed flags and a LightGBM with a small minimum leaf size did better with a pooled flag, as hypothesised from three other states; the '
    'expected TimesFM-3 preference for pooling was not confirmed. The confirmed effects are small and rest mainly on '
    'one state. A tree model cannot use a flag that is set on fewer training days than its minimum leaf size, which is why Stable LightGBM '
    'ignored typed flags altogether. Exploratory analyses suggest that typing helps more where festival effects differ strongly; a test on '
    '2027–2028 festivals has been drafted to check this. A forecaster who cannot tell in advance which representation will win can average '
    'the two forecasts to limit the worst case.')
rep('The GRID-INDIA/POSOCO compilation curated by Robbie Andrew is in the repository; its reuse terms are unresolved.',
    'The GRID-INDIA/POSOCO compilation curated by Robbie Andrew and the seven-state extract from the same source are in the repository; '
    'their reuse terms are unresolved. The new-states registration is at https://osf.io/yw7mr.')


# ---------------- figures for the paper (drawn from committed CSVs) ----------------
def figures(dest):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    R3 = sorted([(h, v) for (m, h), v in v3.items() if m == 'ridge'])
    se3 = {(r['model'], float(r['h'])): float(r['mc_se']) for r in read(S3/'summary.csv')}
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    ax = axes[0]
    ax.axvspan(h_lo, h_hi, color='0.88', label='calibrated h (90% band)')
    ax.errorbar([h for h, _ in R3], [v for _, v in R3], yerr=[1.96*se3[('ridge', h)] for h, _ in R3], marker='o', capsize=3, label='Ridge, simulated')
    ax.plot([h_cal], [SAa['ridge']], 'kx', ms=9, mew=2, label='Ridge, observed (Stage A)')
    ax.axhline(0, color='grey', lw=.8)
    ax.set_xlabel('heterogeneity of festival effects, h'); ax.set_ylabel('typed minus pooled MASE\n(> 0: pooled better)')
    ax.set_title('Ridge'); ax.legend(fontsize=7)
    ax = axes[1]
    labels = ['leaf 2', 'leaf 5', 'leaf 20']
    vals = [v3[('lgbm_leaf2', hv3)], v3[('lgbm_leaf5', hv3)], v3[('lgbm_leaf20', hv3)]]
    ax.bar(labels, vals, color='C0', alpha=.7, label='simulated')
    ax.plot([0], [SAa['lightgbm_capacity2']], 'kx', ms=9, mew=2, label='observed, Stage A')
    ax.plot([1.5], [SAa['lightgbm']], 'kx', ms=9, mew=2)
    ax.plot([1.5], [share5A*v3[('lgbm_leaf5', hv3)]], 'o', color='C1', ms=7, label='implied Stable LightGBM (Stage A leaf mix)')
    ax.annotate('Stable LightGBM\n(leaf 5 or 20)', (1.5, SAa['lightgbm']), textcoords='offset points', xytext=(6, 6), fontsize=7)
    ax.text(2, 0.002, '0 in every replication\n(typed flags never used)', ha='center', fontsize=7)
    ax.axhline(0, color='grey', lw=.8)
    ax.set_ylim(0, 0.125)
    ax.set_ylabel('typed minus pooled MASE\n(> 0: pooled better)'); ax.set_title(f'LightGBM, h = {hv3:.2f}'); ax.legend(fontsize=7, loc='upper left')
    fig.tight_layout(); fig.savefig(dest/'figure3_simulation.png', dpi=200); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4))
    for ax, (pc, oc, title) in zip(axes, [('predicted_ridge', 'observed_ridge', 'Ridge'), ('predicted_lgbm_leaf2', 'observed_lightgbm_capacity2', 'LightGBM, min leaf 2')]):
        xs = [float(SV[k][pc]) for k in SV]; ys = [float(SV[k][oc]) for k in SV]
        ax.scatter(xs, ys, color='C0')
        offs = {'Uttar Pradesh': (4, 6), 'Andhra Pradesh': (4, -2), 'Telangana': (4, -11), 'Madhya Pradesh': (4, -11)} if pc == 'predicted_ridge' else \
               {'Uttar Pradesh': (-62, 6), 'Telangana': (-10, 10), 'Andhra Pradesh': (8, 2), 'Madhya Pradesh': (4, -11)}
        for k in SV:
            ax.annotate(k, (float(SV[k][pc]), float(SV[k][oc])), textcoords='offset points', xytext=offs.get(k, (4, 3)), fontsize=7)
        lo, hi = min(xs + ys) - 0.01, max(xs + ys) + 0.01
        ax.plot([lo, hi], [lo, hi], 'k--', lw=.8); ax.axhline(0, color='grey', lw=.6); ax.axvline(0, color='grey', lw=.6)
        ax.set_xlabel('predicted typed minus pooled (2015–2020 parameters)'); ax.set_ylabel('observed typed minus pooled, 2021–2025')
        ax.set_title(title)
    fig.tight_layout(); fig.savefig(dest/'figure4_states.png', dpi=200); plt.close(fig)


# ---------------- guards and output ----------------
for bad in ['nan', 'None', '{', '}']:
    assert bad not in md.split('## References')[0].replace('{table', ''), bad
abstract = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
assert 100 <= len(abstract.split()) <= 150, len(abstract.split())
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V9/'figures', OUT/'figures')
figures(OUT/'figures')
shutil.copytree(V9/'supplement', OUT/'supplement')
for d, prefix in [(AN, 'new_states'), (DG, 'new_states_diagnostics'), (S2, 'simulation_v2'), (C2, 'calibration_ten_states'), (C3, 'calibration_timesplit'),
                  (ROOT/'results/new_states_v1_official_plus_confirmed', 'new_states_state_groups')]:
    for f in sorted(d.glob('*.csv')):
        if f.stat().st_size < 2_000_000:
            shutil.copy2(f, OUT/'supplement'/f'{prefix}_{f.name}')
(OUT/'MANUSCRIPT.md').write_text(md)


def render(text, name):
    src = OUT/f'{name}.md'
    src.write_text(text)
    docx = OUT/f'{name}.docx'
    subprocess.run(['pandoc', str(src), '-o', str(docx), '--resource-path', str(OUT)], check=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v10-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(docx)],
                   check=True, capture_output=True)
    return docx


docx = render(md, 'Typed_or_Pooled_Binay_Verma_v10')
(OUT/'Typed_or_Pooled_Binay_Verma_v10.md').unlink()
# anonymised copy for double-blind review: no author name, affiliation line, or identifying links
blind = md.replace('Binay Verma\n\nAffiliation: __________ . Corresponding author email: __________ .\n\n', '')
blind = blind.replace('**Draft for supervisor review (journal format, version 10). Not submitted.**', '**Anonymised manuscript for review.**')
blind = blind.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]').replace('https://osf.io/yw7mr', '[registration link withheld for review]')
blind = blind.replace('osf.io/yw7mr', '[registration withheld for review]').replace('An earlier version of this study,', 'A preliminary analysis,').replace('the earlier version', 'a preliminary analysis')
blind = blind.split('**Funding.**')[0] + '**Funding, competing interests, author contributions, use of generative AI:** on the separate title page.\n\n## References' + blind.split('## References', 1)[1]
for ident in ['Binay', 'Verma', 'github.com/Binay', 'yw7mr']:
    assert ident not in blind, ident
render(blind, 'Typed_or_Pooled_v10_anonymised')
(OUT/'Typed_or_Pooled_v10_anonymised.md').rename(OUT/'MANUSCRIPT_anonymised.md')
inputs = [AN, DG, S2, C1, C2, C3, IC, ROOT/'results/new_states_v1_official_plus_confirmed']
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v10 for supervisor review; not submitted. Revised after an internal referee-style check.',
               base={'manuscript/journal_v9/MANUSCRIPT.md': sha(V9/'MANUSCRIPT.md')},
               new_inputs={str(p.relative_to(ROOT)): sha(p) for d in inputs for p in sorted(d.glob('*')) if p.is_file()},
               abstract_words=len(abstract.split()), words_main_text=len(md.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in sorted(OUT.glob('*')) if p.is_file()}), open(OUT/'build.json', 'w'), indent=1)
print('built', len(md.split()), 'words; abstract', len(abstract.split()))
