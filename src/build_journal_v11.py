"""Build journal draft v11: the v10 text reorganised around the registered test, with an expanded related-work section,
the SARIMAX simulation and a reproduction map. No result number of v10 is changed; sections, tables and figures are moved and
renumbered automatically, and every cross-reference is checked against the headings and captions that exist.
Run from the repository root: python src/build_journal_v11.py
"""
import datetime, hashlib, json, re, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V10 = ROOT/'manuscript/journal_v10'
OUT = ROOT/'manuscript/journal_v11'
LIT = ROOT/'review/literature_2026-11-15/references.json'
SAR = ROOT/'results/simulation_sarimax_v3'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


b10 = json.load(open(V10/'build.json'))
assert b10['outputs']['MANUSCRIPT.md'] == sha(V10/'MANUSCRIPT.md'), 'v10 manuscript changed since its build'
md = (V10/'MANUSCRIPT.md').read_text()

# ---------------- split into blocks ----------------
pre, rest = md.split('\n## 1. Introduction\n', 1)
rest = '## 1. Introduction\n' + rest
parts = re.split(r'(?m)^(?=##+ )', rest)
blocks = {}
order = []
for p in parts:
    if not p.strip():
        continue
    head = p.splitlines()[0]
    key = re.match(r'##+ ([0-9.]+|[A-Za-z].*?)(?: |$)', head).group(1)
    if key in ('Appendix',):
        key = head
    blocks[key] = p
    order.append(key)
for k in ['1.', '2.', '3.1', '3.2', '3.3', '3.4', '3.5', '4.1', '4.2', '4.3', '4.4', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7',
          '5.8', '5.9', '6.', '7.', '8.', '9.']:
    assert k in blocks, k


def body(k):
    return blocks[k].split('\n', 1)[1]


def rename(k, new_head):
    return f'{new_head}\n' + body(k)


# ---------------- new related work ----------------
refs_old = md.split('## References\n', 1)[1].split('\n## Appendix', 1)[0]
n_old = len(re.findall(r'(?m)^\[(\d+)\]', refs_old))
assert n_old == 16
lit = {r['key']: r for r in json.load(open(LIT))}
NEW = ['HongFan2016', 'ArsoraTaylor2013', 'CharltonSingleton2014', 'ZielLiu2016', 'BanerjeeSarkar2010', 'Fernandes2011', 'Liu1980',
       'BellHillmer1983', 'Findley1998', 'LinLiu2003', 'RobertsWhite2015', 'TaylorLetham2018', 'HyndmanAthanasopoulos2021', 'Das2024',
       'Ansari2024', 'Woo2024', 'Ekambaram2024', 'PinedaArango2025', 'Aksu2024', 'Shchur2025', 'EfronMorris1975', 'MicciBarreca2001',
       'Pargent2022', 'Probst2019', 'LightGBMDocs', 'DieboldMariano1995', 'HansenLundeNason2011', 'CameronGelbachMiller2008',
       'CanayRomanoShaikh2017', 'HemerikGoemanFinos2020', 'Franses2016', 'Petropoulos2022', 'Hewamalage2023', 'Boylan2015',
       'Makridakis2020M4', 'KapoorNarayanan2023', 'Morris2019', 'SmithWallis2009']
num = {k: n_old + 1 + i for i, k in enumerate(NEW)}
for k in NEW:
    assert k in lit, k


def c(*keys):
    return '[' + ', '.join(str(num[k]) for k in keys) + ']'


related = f"""## 2. Related work

**Holidays in load forecasting.** Load forecasting is reviewed in {c('HongFan2016')}, and competition models include special treatment of public holidays {c('CharltonSingleton2014', 'ZielLiu2016')}. Ziel [9] compared one shared holiday dummy, grouped dummies and a separate dummy for each holiday for German load. He reported that many additional per-holiday dummies did not seem to improve on one additional dummy, with univariate results mixed by holiday type; in his multivariate comparison three models were not significantly worse than the best model forecast, M-RpH (a replacing design with one dummy per holiday), and the holiday-as-Saturday and holiday-as-Sunday designs were in most cases significantly worse than the best approach. Arora and Taylor treat special days with rule-based seasonal models [10, {num['ArsoraTaylor2013']}]. For India, evidence is sparse: a regional study found no significant effect of a single pooled national-holiday dummy on hourly northern-grid load {c('BanerjeeSarkar2010')}, and day-ahead holiday load forecasting in the Indian context has been addressed at a conference {c('Fernandes2011')}; moving Indian holidays have been modelled in manufacturing statistics [3].

**Moving holidays in official statistics.** Festivals that follow lunar or lunisolar calendars move between months, and calendar adjustment has long used holiday-specific regressors for them {c('Liu1980', 'BellHillmer1983', 'Findley1998')}. For Taiwan's three main lunar holidays each festival gets its own before, during and after regressors, chosen by information criteria {c('LinLiu2003')}; for Chinese New Year the windows are chosen in the same way and insignificant holiday regressors are dropped {c('RobertsWhite2015')}, so "typed" in practice need not mean "keep every dummy". Forecasting software follows the same pattern: the Prophet procedure {c('TaylorLetham2018')}, as implemented, gives each named holiday its own effect with a prior scale that shrinks it, and textbook regression models use one dummy per holiday {c('HyndmanAthanasopoulos2021')}.

**Foundation models and covariates.** Pretrained time-series models such as TimesFM and Chronos were introduced without covariate inputs, and Moirai for a varying number of variates {c('Das2024', 'Ansari2024', 'Woo2024')}; support for known future covariates came later and differs between models, from exogenous inputs added during fine-tuning {c('Ekambaram2024')} to adapters that inject covariates such as holidays into a pretrained model {c('PinedaArango2025')} and the native covariate interfaces of Chronos-2 and TimesFM-3 [6, 7]. General benchmarks have followed {c('Aksu2024')}, and some now include tasks with covariates {c('Shchur2025')}. Closest to our question, Kreusel et al. [1] examine calendar encodings in Chronos-2 and TimesFM-3, Alipour et al. [2] learn event representations from residual responses, and Kaljevic et al. [4] benchmark foundation models for load forecasting under covariate uncertainty; Meyer et al. [5] show how information leakage can affect their evaluation.

**Typed, pooled, or in between.** Typed and pooled indicators are the two ends of a familiar trade-off. Pooling categories reduces variance at the cost of bias when the categories differ, and shrinkage estimators sit between the two, improving accuracy on average although they can worsen it for individual categories {c('EfronMorris1975')}; for categorical features with many levels, target encoding {c('MicciBarreca2001')} in regularised form outperforms integer and indicator (dummy) encodings {c('Pargent2022')}. Our setting has few categories but very few occurrences of each, which is where this trade-off bites. For random forests the minimum node size is an important tuning parameter {c('Probst2019')}, and in LightGBM the minimum number of rows in a leaf limits which splits are possible {c('LightGBMDocs')}; Section 7 shows how it decides whether typed flags can be used at all.

**Evaluation and inference.** We compare forecasts with the mean absolute scaled error [13], which can be used in tests of equal accuracy {c('Franses2016')}, rather than the usual pairwise tests {c('DieboldMariano1995')} or model confidence sets {c('HansenLundeNason2011')}, because our unit of evidence is a festival-year cluster and there are few of them. With few clusters, conventional cluster-robust tests over-reject {c('CameronGelbachMiller2008')}, and randomisation tests based on sign changes are an established alternative when cluster-level differences can be taken as symmetric about zero under the null {c('CanayRomanoShaikh2017', 'HemerikGoemanFinos2020')}; we adjust for multiple hypotheses with Holm's procedure [16]. Forecasting-practice reviews stress such evaluation choices {c('Petropoulos2022', 'Hewamalage2023')}.

**Combination, replication and simulation.** Averaging forecasts goes back to Bates and Granger [11], and simple equal weights often perform as well as estimated weights [12], a result that a simulation can explain {c('SmithWallis2009')}; we use equal weights only as a hedge between two representations. Published forecasting results do not always replicate {c('Boylan2015')}, large open comparisons such as the M4 competition {c('Makridakis2020M4')} set common benchmarks, and leakage undermines many machine-learning results {c('KapoorNarayanan2023')}; registering hypotheses before testing them separates hypotheses formed from data from those tested on new data [15]. We report our simulations following the usual structure of aims, data-generating mechanisms, methods and performance measures {c('Morris2019')}.

Our study does not introduce typed or pooled indicators, which are established. It examines how that choice behaves under a fixed channel budget with zero and placebo controls, across model classes, with a registered test on new states, and why the answer differs between models and festivals.

"""

# ---------------- SARIMAX simulation paragraph ----------------
sar_sum = json.load(open(SAR/'summary.json'))
sar = {(r.split(',')[0], float(r.split(',')[1])): r for r in (SAR/'summary.csv').read_text().splitlines()[1:]}
sar_cal = {float(line.split(',')[1]): float(line.split(',')[2]) for line in (SAR/'summary.csv').read_text().splitlines()[1:]
           if line.startswith('three-state calibration')}


def s4(x):
    x = float(x)
    return ('+' if x > 0 else '−' if x < 0 else '') + f'{abs(x):.4f}'


SAa_sar = next(float(r.split(',')[5]) for r in (ROOT/'results/longer_panel_stage_a_v1/analysis/typed_vs_pooled.csv').read_text().splitlines() if r.startswith('sarimax,day,1,'))
sar_st = {line.split(',')[0]: line.split(',') for line in (SAR/'per_state_predicted_vs_observed_2021_2025.csv').read_text().splitlines()[1:]}
assert sar_cal[0.25] > 0 and sar_cal[0.462] < 0 and sar_cal[0.0] > 0
sar_par = (f"SARIMAX, the model of the confirmed H1, was added to the pipeline-matched simulation afterwards, with the registered "
           f"specification (one fit per year on the previous 730 days, a first-order autoregression with a weekly seasonal term, parameters "
           f"then held fixed). At the three-state calibration it does better with a pooled flag when festival effects are alike "
           f"({s4(sar_cal[0.0])} at h = 0, {s4(sar_cal[0.25])} at h = 0.25) and with typed flags from the calibrated heterogeneity upwards "
           f"({s4(sar_cal[0.462])} at h = {0.462:.2f}, {s4(sar_cal[1.0])} at h = 1, {s4(sar_cal[2.0])} at h = 2), the direction of H1 at the measured "
           f"heterogeneity. Its per-state predictions are weaker than for Ridge and the trees: with each further state's 2015–2020 "
           f"parameters it predicts an average of {s4(sar_sum['mean_predicted'])} against {s4(sar_sum['mean_observed'])} observed for "
           f"2021–2025, with a state-level correlation of {sar_sum['pearson']:.2f} (Spearman {sar_sum['spearman']:.2f}, not significant), and the "
           f"observed SARIMAX favours typed flags in Rajasthan and Madhya Pradesh where the simulation predicts a pooled advantage. The "
           f"simulated gain at the calibrated h is also about {abs(SAa_sar/sar_cal[0.462]):.1f} times smaller than the observed Stage A value "
           f"({s4(SAa_sar)}), and Tamil Nadu is over-predicted ({s4(sar_st['Tamil Nadu'][2])} against {s4(sar_st['Tamil Nadu'][4])} observed). "
           f"With seven states this is supporting evidence, not a test: the simulation accounts for the direction of H1 at the calibrated "
           f"heterogeneity but not for its size or its distribution across states.")

# ---------------- reassemble ----------------
intro = body('1.')
_old_road = re.search(r' Section 2 reviews related work, Section 3[^\n]*', intro)
assert _old_road, 'old roadmap not found'
intro = intro.replace(_old_road.group(0), '')
roadmap = ("\nSection 2 reviews related work, Sections 3 and 4 describe the data, models and tests, and Section 5 summarises the exploratory "
           "stages in which the hypotheses were formed. The main evidence is the registered test on seven further states in Section 6. "
           "Section 7 explains the pattern with a mechanism and simulations, Section 8 reports exploratory follow-ups, Section 9 turns the "
           "results into advice, and Sections 10 to 12 cover uncertainty, limitations and conclusions. A comparison with the closest "
           "published designs, a replication on New York transit data and a reproduction map are in the appendices.\n")
intro = intro.rstrip('\n') + '\n' + roadmap + '\n'

sec5_intro = ("## 5. Where the hypotheses came from\n\nThis section summarises the exploratory work on the three original states and the "
              "registered follow-up on further Maharashtra years. It is the basis of the hypotheses tested in Section 6, not the main evidence.\n\n")
s6 = re.sub(r'^### 5\.7 Registered test in seven further states', '## 6. Registered test in seven further states', blocks['5.7'])
s7 = re.sub(r'^### 5\.8 A mechanism, and a simulation', '## 7. Mechanism and simulations', blocks['5.8'])
_t = 'Tree models need a minimum number of training days on each side of a split.'
assert s7.count(_t) == 1
s7 = s7.replace(_t, 'Tree models need a minimum number of training rows on each side of a split; because each tree model is fitted to one state, a row is a day.')
_o = ', or −9.9% when the neighbouring days are modelled as well, so the window profile below adds neighbouring-day effects without changing the festival-day effect;'
assert s7.count(_o) == 1
_wp = json.load(open(ROOT/'results/window_profile_v1/summary.json'))['festival_day_effect_three_state_mean']
s7 = s7.replace(_o, f'; {100*_wp:.1f}% in a regression that also models the neighbouring days, whose relative profile the generator uses;'.replace('-', '−'))
s7 = s7.replace('festival-day effect -9.6%', 'festival-day effect −9.6%')
anchor = 'In this version Ridge typed flags start to win between'
i = s7.index(anchor)
j = s7.index('\n', i)
s7 = s7[:j] + '\n\n' + sar_par + s7[j:]
s8 = re.sub(r'^### 5\.9 Exploratory follow-ups', '## 8. Exploratory follow-ups', blocks['5.9'])
main = (pre.rstrip('\n') + '\n\n' + '## 1. Introduction\n' + intro + related
        + blocks['3.'] + blocks['3.1'] + blocks['3.2']
        + re.sub(r'^### 3\.5', '### 3.3', blocks['3.5']) + re.sub(r'^### 3\.3', '### 3.4', blocks['3.3'])
        + blocks['4.'] + blocks['4.1'] + blocks['4.2'] + blocks['4.3'] + blocks['4.4']
        + sec5_intro + blocks['5.1'] + blocks['5.2'] + blocks['5.3'] + blocks['5.4']
        + s6 + s7 + s8
        + re.sub(r'^## 6\.', '## 9.', blocks['6.']) + re.sub(r'^## 7\.', '## 10.', blocks['7.'])
        + re.sub(r'^## 8\.', '## 11.', blocks['8.']) + re.sub(r'^## 9\.', '## 12.', blocks['9.']))
assert blocks['3.'].strip() == '## 3. Data and calendars' and blocks['4.'].strip().startswith('## 4.')
tail_keys = [k for k in order if k not in ['1.', '2.', '3.', '3.1', '3.2', '3.3', '3.4', '3.5', '4.', '4.1', '4.2', '4.3', '4.4', '5.', '5.1', '5.2',
                                           '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9', '6.', '7.', '8.', '9.']]
decl = ''.join(blocks[k] for k in tail_keys if not k.startswith('## Appendix') and k != 'References')
refs_block = blocks['References']
appA = ''.join(blocks[k] for k in tail_keys if k.startswith('## Appendix'))
appB = ('## Appendix B. NYC transit replication\n\n' + re.sub(r'^### 3\.4 NYC transit replication\n', '### B.1 Data\n', blocks['3.4'])
        + re.sub(r'^### 5\.6 NYC replication\n', '### B.2 Results\n', blocks['5.6']))
appC = re.sub(r'^### 5\.5 Closest-method comparators\n', '## Appendix C. Closest-method comparators\n', blocks['5.5'])

# references: append new ones
new_refs = '\n\n'.join(f"[{num[k]}] {lit[k]['citation']}" + (f" https://doi.org/{lit[k]['doi']}" if lit[k]['doi'] else f" {lit[k]['url']}")
                       for k in NEW)
refs_block = refs_block.rstrip('\n') + '\n\n' + new_refs + '\n\n'

# ---------------- section cross-references ----------------
SEC = {'3.4': 'B.1', '3.5': '3.3', '3.3': '3.4', '5.5': 'Appendix C', '5.6': 'Appendix B.2', '5.7': '6', '5.8': '7', '5.9': '8',
       '6': '9', '7': '10', '8': '11', '9': '12'}


def fix_sections(text):
    def one(m):
        word, nums = m.group(1), m.group(2)
        toks = re.split(r'(,\s*|\s+and\s+|\s+to\s+)', nums)
        out = []
        for t in toks:
            if re.fullmatch(r'\d+(\.\d+)?', t):
                out.append('§§' + t + '§§')
            else:
                out.append(t)
        return word + ' ' + ''.join(out)
    text = re.sub(r'\b(Sections?) ((?:\d+(?:\.\d+)?)(?:(?:,\s*|\s+and\s+|\s+to\s+)\d+(?:\.\d+)?)*)', one, text)

    def repl(m):
        t = m.group(1)
        return SEC.get(t, t)
    text = re.sub(r'§§([0-9.]+)§§', repl, text)
    return text.replace('Section Appendix ', 'Appendix ').replace('Sections Appendix ', 'Appendices ')


body_main = fix_sections(main)
appB, appC = fix_sections(appB), fix_sections(appC)
# the inserted roadmap and section-5 intro already use new numbers: restore them
body_main = body_main.replace(fix_sections(roadmap), roadmap).replace(fix_sections(sec5_intro), sec5_intro)
body_main = body_main.replace(fix_sections(related), related)
assert related in body_main and roadmap in body_main
appA = fix_sections(appA)
decl = fix_sections(decl)

# ---------------- tables and figures ----------------
doc = body_main + decl + refs_block + appA + appB + appC
main_part = body_main
caps_main = re.findall(r'(?m)^Table (\d+b?)\.', main_part)
caps_B = re.findall(r'(?m)^Table (\d+b?)\.', appB)
caps_C = re.findall(r'(?m)^Table (\d+b?)\.', appC)
tmap, n = {}, 0
for t in caps_main:
    if t.endswith('b'):
        tmap[t] = tmap[t[:-1]] + 'b'
    else:
        n += 1
        tmap[t] = str(n)
for i, t in enumerate(caps_B, 1):
    tmap[t] = f'B{i}'
for i, t in enumerate(caps_C, 1):
    tmap[t] = f'C{i}'
figs = re.findall(r'!\[Figure (\d+)\.', main_part) + re.findall(r'!\[Figure (\d+)\.', appB + appC)
fmap = {f: str(i) for i, f in enumerate(figs, 1)}


def renum(text):
    def tab(m):
        word, nums = m.group(1), m.group(2)
        return word + ' ' + re.sub(r'\d+b?', lambda x: '¤T' + tmap.get(x.group(0), x.group(0)) + '¤', nums)
    text = re.sub(r'\b(Tables?) ((?:\d+b?)(?:(?:,\s*|\s+and\s+|–)\d+b?)*)', tab, text)
    text = re.sub(r'\b(Figures?) ((?:\d+)(?:(?:,\s*|\s+and\s+|–)\d+)*)',
                  lambda m: m.group(1) + ' ' + re.sub(r'\d+', lambda x: '¤F' + fmap.get(x.group(0), x.group(0)) + '¤', m.group(2)), text)
    return re.sub(r'¤[TF]([A-Z]?\d+b?)¤', r'\1', text)


body_main, decl, appA, appB, appC = (renum(x) for x in (body_main, decl, appA, appB, appC))

# ---------------- reproduction map (Appendix D) ----------------
SRC = {  # v10 table/figure label -> (result folders, script that wrote them)
    'T1': ('results/longer_panel_stage_a_v1, longer_panel_stage_b_v1, new_states_v1/design_summary.json', 'src/longer_panel_stage_a_v1.py, longer_panel_stage_b_v1.py, new_states_v1.py'),
    'T2': ('results/calendar_recenter_recovery_v1/analysis/breadth', 'src/continue_pipeline_recovery_v2.py'),
    'F1': ('results/calendar_recenter_recovery_v1/analysis/breadth', 'src/build_integrated_review.py'),
    'T3': ('results/longer_panel_stage_a_v1/analysis', 'src/longer_panel_stage_a_v1.py (forecasts), longer_panel_analysis_stage_a_v1.py (tests)'),
    'T4': ('results/longer_panel_stage_a_v1/analysis', 'src/longer_panel_stage_a_v1.py (forecasts), longer_panel_analysis_stage_a_v1.py (tests)'),
    'T5': ('results/longer_panel_foundation_v1/analysis', 'src/longer_panel_foundation_v1.py (hosted notebook), longer_panel_foundation_analysis_v1.py'),
    'T6': ('results/longer_panel_stage_b_v1/analysis', 'src/longer_panel_stage_b_v1.py (forecasts), longer_panel_analysis_stage_b_v1.py (tests)'),
    'T7': ('results/longer_panel_stage_b_v1/analysis', 'src/longer_panel_stage_b_v1.py (forecasts), longer_panel_analysis_stage_b_v1.py (tests)'),
    'F2': ('results/longer_panel_stage_a_v1, longer_panel_stage_b_v1', 'drawn by src/build_journal_v9.py'),
    'T12': ('results/new_states_v1/analysis', 'src/new_states_v1.py (forecasts); src/new_states_analysis_v1.py (registered tests)'),
    'T12b': ('results/new_states_v1/analysis', 'src/new_states_analysis_v1.py (registered)'),
    'T13': ('results/new_states_v1/analysis/balanced.csv', 'src/new_states_analysis_v1.py (registered)'),
    'F3': ('results/simulation_typed_pooled_v3, window_profile_v1, longer_panel_stage_a_v1', 'src/simulation_typed_pooled_v3.py, window_profile_v1.py; drawn by src/build_journal_v10.py'),
    'T14': ('results/new_states_v1_diagnostics', 'src/new_states_diagnostics_v1.py'),
    'T15': ('results/simulation_states_v3_seedcheck', 'src/simulation_states_v3.py --stable-seed'),
    'T16': ('results/new_states_v1_official_plus_confirmed', 'src/new_states_official_plus_confirmed_v1.py (rerun reproduces it exactly)'),
    'F4': ('results/simulation_states_v3_seedcheck', 'src/simulation_states_v3.py --stable-seed; drawn by src/build_journal_v10.py'),
    'T10': ('results/longer_panel_stage_a_v1/analysis/decision_rules.csv', 'src/longer_panel_analysis_stage_a_v1.py'),
    'T11': ('results/prospective_20261030_scoring_v1, prospective_chronos_20261031_scoring_v1, prospective_interval_20261030_scoring_v1', 'src/collect_prospective_actuals.py, score_chronos_competitor.py, score_interval_annex.py'),
    'T8': ('results/ziel_replacing_v2', 'src/ziel_replacing_v2.py, ziel_replacing_analysis_v2.py'),
    'T9': ('results/mta_holiday_recovery_v1/analysis', 'src/continue_pipeline_recovery_v2.py'),
}
rows = ['| Paper item | Result files | How to reproduce |', '| --- | --- | --- |']
for lab, (files, how) in SRC.items():
    kind, old = lab[0], lab[1:]
    new = ('Table ' + tmap[old]) if kind == 'T' else ('Figure ' + fmap[old])
    rows.append(f'| {new} | {files} | {how} |')
rows.append('| Section 7 SARIMAX simulation | results/simulation_sarimax_v3 | src/simulation_sarimax_v3.py |')
rows.append('| Section 7 window profile (−9.9%) | results/window_profile_v1 | src/window_profile_v1.py |')
rows.append('| Section 8 festival-level analysis | results/new_states_v1_family_mechanism | src/new_states_family_mechanism_v1.py |')
rows.append('| Independent recomputation | results/new_states_v1_independent_check | indep.py in that folder |')
rows.append('| This manuscript | manuscript/journal_v11 | src/build_journal_v11.py (from journal_v10) |')
appD = ('## Appendix D. Reproduction map\n\nEach row names the result folder and the script that wrote it; '
        'foundation-model runs were made in a hosted notebook following docs/reproduction/.\n\n' + '\n'.join(rows) + '\n')

final = body_main + decl + refs_block + appA + appB + appC + appD
final = final.replace('(journal format, version 10)', '(journal format, version 11)')
_c = 'across its two arms and three interval calibrations.'
assert final.count(_c) == 1
final = final.replace(_c, 'across its two arms and three interval calibrations (native, and conformalised quantile recalibrations [8] on frozen and on expanding calibration windows).')

# ---------------- checks ----------------
heads = set(re.findall(r'(?m)^##+ ((?:Appendix )?[A-Z]?[0-9.]+[0-9A-Z]?)', final))
for m in re.finditer(r'\bSections? ((?:\d+(?:\.\d+)?)(?:(?:,\s*|\s+and\s+|\s+to\s+)\d+(?:\.\d+)?)*)', final.split('## References')[0]):
    for t in re.findall(r'\d+(?:\.\d+)?', m.group(1)):
        assert t in {h.rstrip('.') for h in heads} or t + '.' in heads, ('missing section', t, m.group(0))
capt = set(re.findall(r'(?m)^Table ([A-Z]?\d+b?)\.', final))
for m in re.finditer(r'\bTables? ((?:[A-Z]?\d+b?)(?:(?:,\s*|\s+and\s+|–)[A-Z]?\d+b?)*)', final):
    for t in re.findall(r'[A-Z]?\d+b?', m.group(1)):
        assert t in capt, ('missing table', t, m.group(0)[:60])
fcap = set(re.findall(r'!\[Figure (\d+)\.', final))
for m in re.finditer(r'\bFigures? ((?:\d+)(?:(?:,\s*|\s+and\s+|–)\d+)*)', final):
    for t in re.findall(r'\d+', m.group(1)):
        assert t in fcap, ('missing figure', t)
cited = {int(x) for grp in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', final.split('## References')[0]) for x in grp.split(',')}
listed = {int(x) for x in re.findall(r'(?m)^\[(\d+)\]', final.split('## References')[1])}
assert cited <= listed, cited - listed
uncited = sorted(listed - cited)
abstract = final.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
assert 100 <= len(abstract.split()) <= 150

# ---------------- output ----------------
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V10/'figures', OUT/'figures')
shutil.copytree(V10/'supplement', OUT/'supplement')
for f in ['summary.csv', 'per_state_predicted_vs_observed_2021_2025.csv']:
    shutil.copy2(SAR/f, OUT/'supplement'/f'simulation_sarimax_{f}')
shutil.copy2(LIT, OUT/'supplement'/'references_verified.json')
(OUT/'MANUSCRIPT.md').write_text(final)


def render(text, name):
    src = OUT/f'{name}.md'
    src.write_text(text)
    docx = OUT/f'{name}.docx'
    subprocess.run(['pandoc', str(src), '-o', str(docx), '--resource-path', str(OUT)], check=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v11-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(docx)],
                   check=True, capture_output=True)


render(final, 'Typed_or_Pooled_Binay_Verma_v11')
(OUT/'Typed_or_Pooled_Binay_Verma_v11.md').unlink()
blind = final.replace('Binay Verma\n\nAffiliation: __________ . Corresponding author email: __________ .\n\n', '')
blind = blind.replace('**Draft for supervisor review (journal format, version 11). Not submitted.**', '**Anonymised manuscript for review.**')
blind = blind.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]').replace('https://osf.io/yw7mr', '[registration link withheld for review]')
blind = blind.replace('osf.io/yw7mr', '[registration withheld for review]').replace('An earlier version of this study,', 'A preliminary analysis,').replace('the earlier version', 'a preliminary analysis')
blind = blind.split('**Funding.**')[0] + '**Funding, competing interests, author contributions, use of generative AI:** on the separate title page.\n\n## References' + blind.split('## References', 1)[1]
for ident in ['Binay', 'Verma', 'github.com/Binay', 'yw7mr']:
    assert ident not in blind, ident
render(blind, 'Typed_or_Pooled_v11_anonymised')
(OUT/'Typed_or_Pooled_v11_anonymised.md').rename(OUT/'MANUSCRIPT_anonymised.md')
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v11 (v10 reorganised; no result number changed); not submitted.',
               base={'manuscript/journal_v10/MANUSCRIPT.md': sha(V10/'MANUSCRIPT.md')},
               inputs={str(p.relative_to(ROOT)): sha(p) for p in [LIT, *sorted(SAR.glob('*'))] if p.is_file()},
               table_map_v10_to_v11=tmap, figure_map=fmap, section_map=SEC, uncited_references=uncited,
               abstract_words=len(abstract.split()), words_main_text=len(final.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in sorted(OUT.glob('*')) if p.is_file()}), open(OUT/'build.json', 'w'), indent=1)
print('built', len(final.split()), 'words; tables', tmap, 'figures', fmap, 'uncited', uncited)
