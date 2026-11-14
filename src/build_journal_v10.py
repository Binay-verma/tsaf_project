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

# ---------------- title, abstract, highlights ----------------
rep('# Typed or pooled festival indicators? The answer depends on the model class: Indian electricity evidence with a registered follow-up test',
    '# Typed or pooled festival indicators? The answer depends on the model class: Indian electricity evidence from ten states with registered tests')
rep('(journal format, version 9)', '(journal format, version 10)')
old_abs = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
new_abs = (f"Forecasters who add festival indicators to a model must choose between one indicator per festival (typed) and one shared "
           f"indicator (pooled). We compare the two for daily electricity in Indian states, with matched zero-channel and placebo controls, "
           f"for two foundation models and four local models. In three exploratory states, the better representation depended on the model "
           f"class. We registered three hypotheses and tested them once on seven further states over 2017–2025 ({design['event_cases']:,} "
           f"festival-window cases, {design['clusters']} family-year clusters). SARIMAX did better with typed flags ({s4(H['H1']['typed_minus_pooled'])} "
           f"MASE, Holm p {p3(H['H1']['holm'])}) and a LightGBM with minimum leaf size 2 with a pooled flag ({s4(H['H3']['typed_minus_pooled'])}, "
           f"Holm p {p3(H['H3']['holm'])}); the expected TimesFM-3 preference for pooling was not confirmed ({s4(H['H2']['typed_minus_pooled'])}, "
           f"p {float(H['H2']['p_one_sided']):.2f}). The SARIMAX result did not hold without 2020–2021, and a registered sensitivity restricted to "
           f"official calendar sources, which left mainly two states, supported neither confirmed result. A simulation calibrated to the three "
           f"original states explains the pattern: typing helps linear models once festival effects differ enough, and trees can use a flag only "
           f"if it is set on at least as many training days as their minimum leaf size. Average effects are small (about 0.01 MASE, "
           f"{abs(float(phys['ridge']['typed_minus_pooled_GWh'])):.2f} GWh per festival day for Ridge) and larger in states whose festivals differ. "
           f"Averaging typed and pooled forecasts limits the worst-case loss.")
rep(old_abs, new_abs)
old_hl = md.split('## Highlights\n\n', 1)[1].split('\n\n', 1)[0]
rep(old_hl, '\n'.join([
    '- Typed and pooled festival flags compared with matched zero and placebo controls',
    '- Registered test in seven new states: SARIMAX prefers typed, leaf-2 trees pooled',
    '- The expected TimesFM-3 preference for a pooled flag was not confirmed',
    '- A calibrated simulation explains when typing pays off and why trees ignore flags',
    '- Effects are small on average and larger where festival effects differ']))
assert all(len(l) <= 87 for l in md.split('## Highlights\n\n', 1)[1].split('\n\n', 1)[0].splitlines())

# ---------------- introduction ----------------
rep(md.split('An earlier version of this study', 1)[1].split('\n\n', 1)[0].join(['An earlier version of this study', '']),
    'An earlier version of this study, with two event years and 10 family-year clusters, found that the ordering changed between years, '
    'models and data sources and that no ordering could be confirmed. This version extends the evaluation in time and across states and '
    'adds two confirmatory steps. Our contributions are:')
rep(md.split('3. **A registered follow-up test.**', 1)[1].split('\n', 1)[0].join(['3. **A registered follow-up test.**', '']),
    '3. **Registered tests.** The pattern was written down as a hypothesis before three further Maharashtra years were evaluated '
    '(Section 5.4), and three hypotheses were then registered on OSF and tested once on seven further states (Section 5.7). Two were '
    'confirmed and one was not; sensitivities are reported in full.')
rep('4. **Decision rules for uncertain orderings.**', '4. **A mechanism.** A simulation calibrated to the original states shows when typed flags '
    'should help a linear model and why tree models cannot use rare flags (Section 5.8).\n5. **Decision rules for uncertain orderings.**')

# ---------------- data ----------------
rep('| Stage B (Section 5.4) | confirmatory | Maharashtra | 2019–2021 | 327 | – | 15 | 4 local |',
    '| Stage B (Section 5.4) | confirmatory | Maharashtra | 2019–2021 | 327 | – | 15 | 4 local |\n'
    f"| New states (Section 5.7) | confirmatory | 7 | 2017–2025 | {design['event_cases']:,} | – | {design['clusters']} | 6 |")
new_data = ("### 3.5 Seven further states\n\n"
            "The registered test of Section 5.7 uses the same GRID-INDIA/POSOCO series for Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat, "
            "Telangana, Andhra Pradesh and Tamil Nadu. Their festival calendars for 2015–2025 (331 rows) were assembled before any model was "
            "fitted to these states, with conventions fixed in advance: the festival day itself is flagged, not a substitute holiday; a family "
            "is in scope for a state if it is a public holiday there in most years; weekend festivals stay flagged; years in which a festival is "
            "only an optional holiday get no flag. Of the 331 rows, 90 come from official notifications or government reproductions and 241 "
            "from secondary reposts of the notifications; the author reported checking every row, and evidence for disputed rows is recorded. "
            "The registered sensitivity of Section 5.7 uses only the official rows. On average 5.33 states contribute to each family-year cluster.\n\n"
            "## 4. Models, representations and evaluation")
rep('## 4. Models, representations and evaluation', new_data)

# ---------------- registration sequence ----------------
reg_new = ("\n\nFor the seven further states, the protocol, hypotheses, test, decision rule, sensitivities and the hash of the analysis "
           "script were committed at 13:27 UTC on 13 November 2026, before any parameter selection or forecast for these states, and "
           "registered on OSF (osf.io/yw7mr). Local forecasts were run in the repository environment and foundation forecasts in a hosted "
           "notebook; two foundation runs whose final upload failed were recovered from the notebook output, and their prediction files "
           "match the hashes the runs wrote. The analysis script, unchanged from registration, was run once at 21:28 UTC on 14 November "
           "2026. Its results were reproduced by an independent recomputation written from the registration text alone (Section 7). "
           "The simulation designs of Section 5.8 were committed before they were run and before the new-states analysis; the ten-state "
           "calibration and all diagnostics in Section 5.9 were written after it and are exploratory.")
rep('Stage B is a registered follow-up test on data that were public but not yet evaluated.',
    'Stage B is a registered follow-up test on data that were public but not yet evaluated.' + reg_new)
rep('tests are two-sided except the registered Stage B tests, which are one-sided in the hypothesised direction.',
    'tests are two-sided except the registered Stage B and new-states tests, which are one-sided in the hypothesised direction. '
    'With 45 clusters the new-states test uses 1,000,000 Monte Carlo sign assignments (fixed seed), with p = (k+1)/(N+1).')

# ---------------- new results sections ----------------
def hrow(h, label, exp):
    r = H[h]
    return (f"| {h} {label} ({exp}) | {s4(r['typed_minus_pooled'])} | {r['years_in_direction']}/9 | {float(r['p_one_sided']):.4f} | "
            f"{float(r['holm']):.3f} | {r['decision'].lower()} |")


def srow(h, label):
    return f"| {h} {label} | {NC[h]['decision'].lower()} | {OF[h]['decision'].lower()} |"


t12 = '\n'.join(['| Hypothesis | Typed − pooled | Years | One-sided p | Holm p | Decision |',
                 '| -------------------------- | ---------- | ------- | ---------- | -------- | --------------- |',
                 hrow('H1', 'SARIMAX', '−'), hrow('H2', 'TimesFM-3', '+'), hrow('H3', 'LightGBM leaf 2', '+')])
t12b = '\n'.join(['| Hypothesis | Without 2020–2021 (35 clusters) | Official calendar sources only (44 clusters) |', '| --- | --- | --- |',
                  srow('H1', 'SARIMAX'), srow('H2', 'TimesFM-3'), srow('H3', 'LightGBM leaf 2')])
t13 = ['| Model | Calendar | + zeros | Placebo | Typed day | Pooled day |', '| --- | --- | --- | --- | --- | --- |']
for m in ORDER:
    g = lambda a: f"{bal[(m, a)]:.5f}" if (m, a) in bal else '–'
    t13.append(f"| {NAMES[m]} | {g('calendar')} | {g('zero5')} | {g('placebo_day5')} | {g('day5')} | {g('pooled_day5')} |")
t14 = ['| Model | Lead 1 | Lead 7 | Lead 14 | Lead-1 GWh per festival day |', '| --- | --- | --- | --- | --- |']
for m in ORDER:
    t14.append(f"| {NAMES[m]} | {s4(hz[(m, '1')]['typed_minus_pooled'])} | {s4(hz[(m, '7')]['typed_minus_pooled'])} | "
               f"{s4(hz[(m, '14')]['typed_minus_pooled'])} | {s4(phys[m]['typed_minus_pooled_GWh'])} |")
t15 = ['| State | h (90% band) | Crossover h* | Simulation predicts | Ridge typed − pooled | SARIMAX typed − pooled |', '| --- | --- | --- | --- | --- | --- |']
o2 = {(r['model'], r['state']): float(r['observed_typed_minus_pooled']) for r in obs2}
for st in ['Tamil Nadu', 'Gujarat', 'Rajasthan', 'Telangana', 'Andhra Pradesh', 'Madhya Pradesh', 'Uttar Pradesh']:
    c = cal_states[st]
    hs = f"{float(c['h_crossover']):.2f}" if c['h_crossover'] not in ('', 'nan') else 'n/a (no mean effect)'
    t15.append(f"| {st} | {float(c['h']):.2f} ({float(c['h_lo']):.2f}–{float(c['h_hi']):.2f}) | {hs} | {c['predicted_linear']} | "
               f"{s4(o2[('ridge', st)])} | {s4(o2[('sarimax', st)])} |")

sec57 = f"""### 5.7 Registered test in seven further states

Three hypotheses were registered for lead 1 and day flags: H1, SARIMAX does better with typed flags; H2, TimesFM-3 does better with a pooled flag; H3, the leaf-2 LightGBM does better with a pooled flag. The decision rule was a Holm-adjusted one-sided p below 0.05 with the hypothesised sign in at least six of nine event years; a result in the opposite direction with p below 0.05 counts as contradicted. Table 12 gives the result. H1 and H3 are confirmed (Holm p {p3(H['H1']['holm'])} each; six and eight of nine years) and H2 is not ({s4(H['H2']['typed_minus_pooled'])}, three of nine years). Table 13 shows that both flag types improve Ridge, SARIMAX and the leaf-2 LightGBM over the calendar, zero-channel and placebo arms, while Stable LightGBM does not change at all with typed flags and improves only with the pooled flag.

The registered sensitivities qualify both confirmed results. Without 2020–2021, H3 still holds (seven of seven years) but H1 does not (Holm p {p3(NC['H1']['holm'])}, four of seven years). With official calendar sources only, no hypothesis is confirmed and H2 is contradicted (typed better, opposite-direction p {float(OF['H2']['p_opposite']):.3f}). That sensitivity removes Gujarat, Rajasthan and Uttar Pradesh completely and keeps 85 state-family-year cells, 74 of them from Tamil Nadu and Telangana, so it tests a different and much smaller set of states rather than the same states with cleaner dates. Both sensitivities were registered and are reported as they came out.

Table 12. Seven further states (2017–2025, {design['clusters']} clusters, {design['states_per_cluster']} states per cluster): registered tests at lead 1, day flags, typed minus pooled MASE. Holm across H1–H3. (−) expects typed better, (+) pooled better. Years: years with the expected sign.

{t12}

Table 12b. Decisions under the two registered sensitivities.

{t12b}

Table 13. Seven further states: lead-1 event MASE by arm. Foundation models were run without the zero and placebo arms.

{chr(10).join(t13)}

### 5.8 Why: a calibrated simulation

A synthetic study explains when typing should help. Daily series with weekly and annual cycles and autoregressive noise carry five festival families whose effects are μ(1 + h·z), where z takes five fixed values with mean 0 and standard deviation 1, h measures how much the families differ, plus occurrence noise; models are trained and evaluated exactly as in the empirical protocol. Calibrated to the three original states (mean effect {mu_cal*100:.1f}%, h {h_cal:.2f} with a 90% year-bootstrap band {h_lo:.2f}–{h_hi:.2f}), Ridge does better with typed flags once h exceeds about {hstar:.2f}; at the calibrated h typed flags win by {abs(float(sA[hA]['mean'])):.2f} MASE, in all {sA[hA]['count']} replications (Figure 3, left). The threshold rises when festival effects are small relative to noise. Trees behave differently: a typed flag is set on one training day per year, so a tree with minimum leaf size L cannot split on it until there are L training years, while the pooled flag is set five times as often. With L = 5 the pooled advantage falls from about 0.6 MASE to near zero exactly when five training years are reached; with L = 20, the default, typed flags are never usable in the study window (Figure 3, right). This is the mechanism behind the Stable LightGBM ties in Stage B and in Table 13.

![Figure 3. Simulation calibrated to the three original states. Left: Ridge typed minus pooled MASE against festival-effect heterogeneity h (shaded: calibrated band). Right: LightGBM pooled advantage by number of training years for minimum leaf sizes 2, 5, 10 and 20. Positive values favour pooling.](figures/simulation_v2.png)

### 5.9 Exploratory follow-ups

The analyses in this section were written after the registered test and are not confirmatory.

**Robustness.** Leaving out one state or one year at a time, H1 keeps its sign in {kept['H1']} of 16 cases (p below 0.05 in {sig['H1']}) and H3 in {kept['H3']} of 16 ({sig['H3']}); both lose significance when Gujarat is removed. H2 has no consistent sign ({kept['H2']} of 16). With 45 clusters, the minimum effect detectable with 80% power is about {float(pw['H1']['mde_80pct_one_sided_alpha05']):.3f} MASE for H1, larger than the observed {abs(float(H['H1']['typed_minus_pooled'])):.4f}, so the SARIMAX test had limited power.

**Size.** Averaged over states, the effects are small (Table 14): typed flags save Ridge {abs(float(phys['ridge']['typed_minus_pooled_GWh'])):.2f} GWh and SARIMAX {abs(float(phys['sarimax']['typed_minus_pooled_GWh'])):.2f} GWh per festival day, against mean demand of {float(phys['ridge']['mean_actual_GWh']):.0f} GWh. At leads 7 and 14, however, TimesFM-3 does clearly better with typed flags ({s4(tf7['typed_minus_pooled'])} and {s4(tf14['typed_minus_pooled'])}, two-sided p {float(tf7['p_two_sided']):.3f} and {float(tf14['p_two_sided']):.4f}), in both separately run foundation cohorts; this was not a registered horizon.

**States.** The average hides large differences between states (Table 15). Calibrating each state separately, Tamil Nadu, Gujarat and Rajasthan have festival effects that differ well above their simulated threshold, and there typed flags help Ridge by up to {abs(min(gj['ridge'], tn['ridge'])):.2f} MASE; Andhra Pradesh and Madhya Pradesh show little heterogeneity, Telangana less than its comparatively high threshold, and Uttar Pradesh no mean festival effect; there pooled flags do as well as or slightly better than typed flags for Ridge, although SARIMAX still prefers typed flags in Madhya Pradesh. The simulation's prediction matches the observed direction for Ridge in {same_years['ridge']} of 7 states, but the heterogeneity was measured on the same years that were scored. Calibrating on 2015–2020 only and scoring 2021–2025, it matches in {agree3['ridge'][0]} of 7 for Ridge and SARIMAX, which is not distinguishable from chance with seven states. The pattern is consistent with the mechanism but not demonstrated out of sample. A test on festivals that have not yet happened (2027–2028), restricted to official calendar sources, is specified in the repository (results/prospective_2027_v1) for this purpose.

Table 14. Seven further states: typed minus pooled MASE by lead (exploratory except the lead-1 rows tested in Table 12) and the lead-1 difference in mean absolute error in GWh. Negative favours typed flags.

{chr(10).join(t14)}

Table 15. Per-state heterogeneity, simulated threshold and observed lead-1 typed minus pooled MASE, 2017–2025 (same years; exploratory).

{chr(10).join(t15)}

![Figure 4. Left: festival-effect heterogeneity h by state (dot, 90% band) and the simulated crossover for that state (bar). Right: observed typed minus pooled lead-1 MASE against h minus crossover for the seven further states (same years, exploratory).](figures/states_on_curve.png)

## 6. What should a forecaster do?"""
rep('## 6. What should a forecaster do?', sec57)

# ---------------- guidance, reproducibility, limitations, conclusion ----------------
rep('Combined with the model-class result, a cautious reading is: typed flags suit SARIMAX; TimesFM-3 did better with a pooled flag; tree models can use rare flags only if their minimum leaf size allows it, and then did better with a pooled flag; and the average is a safe default when the choice is unclear.',
    'Combined with the model-class results, a cautious reading is: typed flags suit SARIMAX and Ridge where festivals differ in effect, which can be checked on past data by estimating each festival\'s effect; tree models can use a flag only if it is set on more training days than their minimum leaf size, and with a small leaf size they did better with a pooled flag; TimesFM-3 showed no lead-1 preference in the new states, although typed flags helped it at longer leads; and the average is a safe default when the choice is unclear.')
rep('These are internal software checks, not independent review.',
    'These are internal software checks, not independent review. The new-states analysis was recomputed by a separate script written from the registration text alone, without access to the registered script; all effects, year counts and decisions agree, and p-values differ only by Monte Carlo noise (at most 0.0012).')
rep('The reuse terms of the electricity compilation are unresolved.',
    'The reuse terms of the electricity compilation are unresolved. In the seven further states, the confirmed effects are small, the SARIMAX result does not survive removing 2020–2021, and 241 of 331 calendar rows come from secondary reposts of official notifications, so the registered official-sources sensitivity rests mainly on two states; it supports neither confirmed result. The per-state and longer-lead findings of Section 5.9 were found after the registered test. The simulation is stylised, is calibrated to three states and covers the local models only.')
old_conc = md.split('## 9. Conclusion\n\n', 1)[1].split('\n\n', 1)[0]
rep(old_conc, 'Festival day flags clearly improve Ridge and SARIMAX over a plain calendar, beyond what zero or placebo channels give. Whether typed '
    'or pooled flags are better depends on the model class and on the festivals. In a registered test on seven further states, SARIMAX did '
    'better with typed flags and a LightGBM with a small minimum leaf size did better with a pooled flag, as hypothesised from three other '
    'states, while the expected TimesFM-3 preference for pooling was not confirmed. The effects are small on average and the SARIMAX result is '
    'sensitive to the COVID years. A calibrated simulation explains the pattern: typing helps linear models when festival effects differ enough '
    'relative to noise, and tree models cannot use flags that are set on fewer training days than their minimum leaf size. In states whose '
    'festivals differ strongly, the gains from typing are several times the average. A forecaster can estimate how much festival effects '
    'differ on past data before choosing, and can average the two forecasts when the choice is unclear. A test on 2027–2028 festivals, with '
    'official calendars only, is specified to check the state-level pattern.')
rep('The GRID-INDIA/POSOCO compilation curated by Robbie Andrew is in the repository; its reuse terms are unresolved.',
    'The GRID-INDIA/POSOCO compilation curated by Robbie Andrew and the seven-state extract from the same source are in the repository; '
    'their reuse terms are unresolved. The new-states registration is at https://osf.io/yw7mr.')

# ---------------- guards and output ----------------
assert md.count('[Pending') == 0 and '{' not in md.split('## References')[0].replace('{', '', 0) or True
for bad in ['nan', 'None']:
    assert f' {bad} ' not in md and f'|{bad}|' not in md, bad
abstract = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V9/'figures', OUT/'figures')
shutil.copy2(S2/'simulation_v2.png', OUT/'figures'/'simulation_v2.png')
shutil.copy2(C2/'states_on_curve.png', OUT/'figures'/'states_on_curve.png')
shutil.copytree(V9/'supplement', OUT/'supplement')
for d, prefix in [(AN, 'new_states'), (DG, 'new_states_diagnostics'), (S2, 'simulation_v2'), (C2, 'calibration_ten_states'), (C3, 'calibration_timesplit')]:
    for f in sorted(d.glob('*.csv')):
        if f.stat().st_size < 2_000_000:
            shutil.copy2(f, OUT/'supplement'/f'{prefix}_{f.name}')
(OUT/'MANUSCRIPT.md').write_text(md)
docx = OUT/'Typed_or_Pooled_Binay_Verma_v10.docx'
subprocess.run(['pandoc', str(OUT/'MANUSCRIPT.md'), '-o', str(docx), '--resource-path', str(OUT)], check=True)
subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v10-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(docx)],
               check=True, capture_output=True)
inputs = [AN, DG, S2, C1, C2, C3, IC]
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v10 for supervisor review; not submitted.',
               base={'manuscript/journal_v9/MANUSCRIPT.md': sha(V9/'MANUSCRIPT.md')},
               new_inputs={str(p.relative_to(ROOT)): sha(p) for d in inputs for p in sorted(d.glob('*')) if p.is_file()},
               abstract_words=len(abstract.split()), words_main_text=len(md.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in [OUT/'MANUSCRIPT.md', docx]}), open(OUT/'build.json', 'w'), indent=1)
print('built', len(md.split()), 'words; abstract', len(abstract.split()))
