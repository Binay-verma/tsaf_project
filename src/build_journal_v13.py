"""Journal draft v13: restructured around the registered-test scorecard and the support mechanism.

Main text: manuscript/journal_v13_src/MAIN.md, with «TOKENS» filled from result files (numbers are read, not typed).
Supplement: v12 supplement (companion tables, reproduction map) plus v12 sections moved out of the main text
(exploratory stages, simulations, first-test follow-ups, uncertainty and frozen episodes, NYC, Ziel comparators),
with their table, figure and section numbers mapped to v13, and the robustness experiment tables.
References are renumbered by first appearance (main, then supplement). Output: manuscript/journal_v13/.
Run: python src/build_journal_v13.py
"""
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'manuscript/journal_v13_src'
V12 = ROOT/'manuscript/journal_v12'
OUT = ROOT/'manuscript/journal_v13'
R = ROOT/'results'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def f4(x, plus=True):
    s = f'{x:+.4f}' if plus else f'{x:.4f}'
    return s.replace('-', '−')


def p3(p):
    return '< 0.0001' if p < 1e-4 else (f'{p:.4f}' if p < 0.01 else f'{p:.3f}')


def one(text, old, new):
    assert text.count(old) == 1, (text.count(old), old[:70])
    return text.replace(old, new)


# ---------------- numbers ----------------
sc = pd.read_csv(R/'scorecard_v1/scorecard.csv')
regb = pd.read_csv(R/'longer_panel_stage_b_v1/analysis/hypothesis_tests.csv').set_index('hypothesis')
leaf = pd.read_csv(R/'leaf_size_experiment_v1/analysis/by_leaf.csv')
win = pd.read_csv(R/'robustness_experiments_v1/analysis/window.csv')
noi = pd.read_csv(R/'robustness_experiments_v1/analysis/noise.csv')
alp = pd.read_csv(R/'robustness_experiments_v1/analysis/ridge_alpha.csv')
dr = pd.read_csv(R/'decision_rules_14_v1/summary.csv', index_col=0)
lp = json.loads((R/'leaf_size_experiment_v1/analysis/predictions_vs_results.json').read_text())['results']
wx = json.loads((R/'robustness_experiments_v1/analysis/predictions_vs_results.json').read_text())['extra']

rows = ['| Test | Hypothesis | Units | Estimate | 95% interval | Holm p | Decision |', '| --- | --- | --- | --- | --- | --- | --- |']
for r in sc.itertuples():
    est = f'{r.estimate:+.2f}'.replace('-', '−') if r.hypothesis == 'M2' else f4(r.estimate)
    ci = '–' if pd.isna(r.ci_low) else ('exactly 0' if r.ci_low == r.ci_high == 0 else f'{f4(r.ci_low)} to {f4(r.ci_high)}')
    units = r.units.replace(' family-year clusters', ' clusters').replace(' state-family-years', ' units')
    rows.append(f'| {r.test.replace(" test", "")} | {r.hypothesis}: {r.label.replace("Stable LightGBM", "Tuned LightGBM")} | {units} | {est} | {ci} | {p3(r.holm)} | {r.decision.lower()} |')
    if r.test == 'Stage B' and r.hypothesis == 'H2':
        b = regb.loc['H1b (secondary)']
        rows.append(f"| Stage B | H1b (secondary, no Holm): Leaf-2 LightGBM, pooled better | 15 clusters | {f4(b.typed_minus_pooled)} | – | – | meets rule unadjusted |")
SCORECARD = '\n'.join(rows)
assert len(sc) == 9

lt = ['| Leaf size L | First test: typed − pooled | First test: typed = calendar | Second test: typed − pooled | Second test: typed = calendar |', '| --- | --- | --- | --- | --- |']
for L in sorted(leaf.leaf.unique()):
    a = leaf[(leaf.test == 'v1') & (leaf.leaf == L)].iloc[0]; b = leaf[(leaf.test == 'v2') & (leaf.leaf == L)].iloc[0]
    lt.append(f'| {L} | {f4(a.typed_minus_pooled)} | {a.typed_equals_calendar_share:.2f} | {f4(b.typed_minus_pooled)} | {b.typed_equals_calendar_share:.2f} |')
LEAF = '\n'.join(lt)


def w(t, m, W, col='typed_minus_pooled'):
    return float(win[(win.test == t) & (win.model == m) & (win.W == W)][col].iloc[0])


wt = ['| Model | Test | 2 years | 4 years | 6 years |', '| --- | --- | --- | --- | --- |']
for m, name in [('lgbm_leaf2', 'Leaf-2 LightGBM'), ('lgbm_selected', 'Tuned LightGBM'), ('ridge', 'Rich Ridge')]:
    for t, tn in [('v1', 'first'), ('v2', 'second')]:
        wt.append(f'| {name} | {tn} | {f4(w(t, m, 730))} | {f4(w(t, m, 1460))} | {f4(w(t, m, 2190))} |')
WTABLE = '\n'.join(wt)
hyb_max = float(win.hybrid_minus_best.max())
assert hyb_max <= 0.0002
sh1, sh2 = wx['v1']['window_selected_typed_equals_calendar_share_by_W'], wx['v2']['window_selected_typed_equals_calendar_share_by_W']

WINDOW_SECTION = f"""**Training window.** If the pooled advantage of the trees comes from typed flags having too few training days, it should shrink when the training window is longer. A second experiment, also with predictions committed before it was run, refitted the models with windows of two, four and six years for event years 2021–2025 (the calendars start in 2015, so six years is the longest fully covered window). Table 5 and Figure 3 show the result. The leaf-2 LightGBM's pooled advantage shrinks as the window grows in both tests, as predicted: in the first test's states it reverses, from {f4(w('v1', 'lgbm_leaf2', 730))} to {f4(w('v1', 'lgbm_leaf2', 1460))} and {f4(w('v1', 'lgbm_leaf2', 2190))}, so that typed flags do better with four or six years of history; in the second test's states it falls from {f4(w('v2', 'lgbm_leaf2', 730))} to {f4(w('v2', 'lgbm_leaf2', 1460))} and then hardly moves ({f4(w('v2', 'lgbm_leaf2', 2190))}), staying positive. The tuned LightGBM begins to use typed flags: the share of state-years in which its typed and calendar forecasts are identical falls from {sh1['730']:.2f} to {sh1['2190']:.2f} (first test) and from {sh2['730']:.2f} to {sh2['2190']:.2f} (second). Its difference falls in the first test but not monotonically in the second, so that prediction failed there. For Ridge, which can use any flag, the window makes little difference (first test {f4(w('v1', 'ridge', 730))} to {f4(w('v1', 'ridge', 2190))}; second {f4(w('v2', 'ridge', 730))} to {f4(w('v2', 'ridge', 2190))}); we had predicted that typed flags would gain, and that prediction failed. With more history per flag, the pooled advantage shrank in all four LightGBM settings and reversed in one; these window contrasts have no intervals and rest on five event years. The registered tree result is therefore partly a property of the two-year window.

Table 5. Training-window experiment (exploratory, predictions committed before the run; event years 2021–2025, lead 1): typed minus pooled MASE. Positive favours pooling.

{WTABLE}

![Figure 3. Typed minus pooled lead-1 MASE for LightGBM. Left: by minimum leaf size, 730-day window, all event years (blue circles: first test; orange squares: second test). Right: by training window, event years 2021–2025, for the leaf-2 (solid) and tuned (dashed) LightGBM, same colours. Both experiments are exploratory, with predictions committed before they were run.](figures/leaf_window.png)"""

r730 = win[win.W == 730]
def hy(t, m, col): return float(r730[(r730.test == t) & (r730.model == m)][col].iloc[0])
def nz(t, led, m): return noi[(noi.test == t) & (noi.ledger == led) & (noi.model == m)].iloc[0]
OTHER = f"""**Both kinds of indicator.** A hybrid arm that passes the typed flags and the pooled flag together, the middle ground that shrinkage-based tools such as Prophet approximate, was as accurate as the better of the two arms in every setting in which it was run: for Ridge and both LightGBMs at lead 1, in both tests and at every training window, its MASE was at most {hyb_max:.4f} above the better arm, and often below it (for example, leaf-2 LightGBM in the first test, two-year window: typed {hy('v1', 'lgbm_leaf2', 'typed'):.4f}, pooled {hy('v1', 'lgbm_leaf2', 'pooled'):.4f}, hybrid {hy('v1', 'lgbm_leaf2', 'hybrid'):.4f}). Both predictions for this arm held.

**Dating errors.** Because most calendar rows come from secondary sources (Section 3.2), we moved a random 20% of festival dates by one day, with two seeds, and reran Ridge and the leaf-2 LightGBM. For Ridge, the errors moved the difference towards pooling in both tests and both seeds (by {f4(nz('v1', 'moved_seed1', 'ridge').change)} and {f4(nz('v1', 'moved_seed2', 'ridge').change)} in the first test, {f4(nz('v2', 'moved_seed1', 'ridge').change)} and {f4(nz('v2', 'moved_seed2', 'ridge').change)} in the second), as predicted; a plausible reason, not tested here, is that a misdated typed flag loses one of its few training days, while the pooled flag keeps the others. For the leaf-2 LightGBM the prediction failed in three of four cases (changes {f4(nz('v1', 'moved_seed1', 'lgbm_leaf2').change)}, {f4(nz('v1', 'moved_seed2', 'lgbm_leaf2').change)}, {f4(nz('v2', 'moved_seed1', 'lgbm_leaf2').change)}, {f4(nz('v2', 'moved_seed2', 'lgbm_leaf2').change)}), so dating errors do not explain its pooled advantage, although they may bias linear models towards pooling.

**Ridge penalty.** The arms share the penalty selected on ordinary days. Refitting Ridge with penalties from 0.1 to 1,000 for every arm left the first test's typed advantage in place (between {f4(alp[(alp.test == 'v1') & alp.alpha.isin([0.1, 1, 10, 100])].typed_minus_pooled.max())} and {f4(alp[(alp.test == 'v1') & alp.alpha.isin([0.1, 1, 10, 100])].typed_minus_pooled.min())} for penalties 0.1 to 100); in the second test every value was within 0.004 of zero, and the predicted constant sign failed only because of a value of {f4(alp[(alp.test == 'v2') & (alp.alpha == 10)].typed_minus_pooled.iloc[0])} at penalty 10. Details of all three checks are in Supplementary Section S10."""

DR_TABLE = '\n'.join(['| Rule | Mean regret | Largest regret |', '| --- | --- | --- |'] +
                     [f"| {n} | {dr.loc[k, 'mean_regret']:.4f} | {dr.loc[k, 'largest_regret']:.4f} |" for k, n in
                      [('typed', 'Always typed'), ('pooled', 'Always pooled'), ('follow', "Follow last year's winner"), ('average', 'Average of typed and pooled')]])
DR_MEAN = (f"{dr.loc['typed', 'mean_regret']:.4f} for always-typed, {dr.loc['pooled', 'mean_regret']:.4f} for always-pooled, "
           f"{dr.loc['follow', 'mean_regret']:.4f} for the follow rule and {dr.loc['average', 'mean_regret']:.4f} for the average")
DR_MAX = (f"{dr.loc['typed', 'largest_regret']:.3f}, {dr.loc['pooled', 'largest_regret']:.3f}, {dr.loc['follow', 'largest_regret']:.3f} and "
          f"{dr.loc['average', 'largest_regret']:.3f} respectively")
assert int(dr.loc['follow', 'follow_picked_worse_cells']) == 59 and int(dr.loc['follow', 'cells']) == 192

TOK = {
    '«HIGHLIGHT_WINDOW»': 'Longer windows shrank the trees’ pooled advantage; passing both flags did as well',
    '«CONTRIB_WINDOW»': 'and on the length of the training window',
    '«SCORECARD_TABLE»': SCORECARD, '«LEAF_TABLE»': LEAF, '«WINDOW_SECTION»': WINDOW_SECTION, '«HYBRID_NOISE_ALPHA_SECTION»': OTHER,
    '«DR_MEAN»': DR_MEAN, '«DR_MAX»': DR_MAX, '«DR_TABLE»': DR_TABLE,
    '«CONCLUSION_WINDOW»': 'With longer training windows that advantage shrank, and in one group of states reversed, and for Ridge and LightGBM passing typed and pooled indicators together was as accurate as the better of the two in every setting we ran.',
}
main = (SRC/'MAIN.md').read_text()
for k, v in TOK.items():
    main = one(main, k, v)
assert '«' not in main, re.findall('«[A-Z_]+»', main)
main = one(main, "Table 5 shows the result", "Table 5 shows the result") if "Table 5 shows the result" in main else main

# ---------------- supplement ----------------
v12 = (V12/'MANUSCRIPT.md').read_text()
def sec(a, b): return v12.split(a, 1)[1].split(b, 1)[0]
moved = [('S3. Exploratory stages in detail', sec('## 5. Where the hypotheses came from', '## 6. Registered tests')),
         ('S4. Simulations of the typed-pooled trade-off', sec('## 7. Mechanism and simulations', '## 8. Exploratory follow-ups')),
         ('S5. Exploratory follow-ups to the first registered test', sec('## 8. Exploratory follow-ups', '## 9. What should')),
         ('S6. Uncertainty, reproducibility and frozen prospective episodes', sec('## 10. Uncertainty and reproducibility', '## 11. Limitations')),
         ('S7. NYC transit replication', sec('## Appendix B. NYC transit replication', '## Appendix C.')),
         ('S8. Closest-method comparators', v12.split('## Appendix C. Closest-method comparators', 1)[1]),
         ('S9. First registered test: arms and sensitivities', 'Table 8b. ' + v12.split('Table 8b. ', 1)[1].split('### 6.2', 1)[0])]
TMAP = {'2': 'S16', '3': 'S17', '4': 'S18', '5': 'S19', '6': 'S20', '7': 'S21', '10': 'S22', '11': 'S23', '12': 'S24', '14': 'S25',
        'B1': 'S26', 'C1': 'S27', '8b': 'S28', '9': 'S29', '8': '3', '8c': '3', '1': '1', '13': None}
FMAP = {'1': 'S1', '2': 'S2', '3': 'S3', '4': 'S4'}


def map_refs(t):
    t = re.sub(r'(?m)^Table (\d+[bc]?|B1|C1)\.', lambda m: f'Table {TMAP[m.group(1)]}.', t)

    def lst(m):
        items = re.split(r'(,\s*|\s+and\s+|–)', m.group(2))
        out = []
        for it in items:
            if re.fullmatch(r'\d+[bc]?|B1|C1', it):
                new = TMAP[it]; assert new is not None, m.group(0)
                out.append(new if new.startswith('S') else f'{new} of the main paper')
            else:
                out.append(it)
        return m.group(1) + ' ' + ''.join(out)
    t = re.sub(r'\b(Tables?) ((?:\d+[bc]?|B1|C1)(?:(?:,\s*|\s+and\s+|–)(?:\d+[bc]?|B1|C1))*)\b', lst, t)
    t = re.sub(r'!\[Figure (\d)\.', lambda m: f'![Figure {FMAP[m.group(1)]}.', t)
    t = re.sub(r'\bFigures? (\d)\b', lambda m: f'Figure {FMAP[m.group(1)]}', t)
    t = re.sub(r'\bSection 6(?:\.\d)?\b', 'Section 5 of the main paper', t)
    t = re.sub(r'\bSection 8\b', 'Section S5', t)
    t = re.sub(r'\bSections? 5\.(\d)\b', r'Section S3.\1', t)
    t = re.sub(r'(?m)^### 5\.(\d) ', r'### S3.\1 ', t)
    t = re.sub(r'(?m)^### B\.(\d) ', r'### S7.\1 ', t)
    t = re.sub(r'\bAppendix C\b', 'Section S8', t)
    return t


sup12 = (V12/'Online_supplement_v12.md').read_text() if (V12/'Online_supplement_v12.md').exists() else None
if sup12 is None:
    # rebuild the v12 supplement text exactly as build_journal_v12 does
    v11 = (ROOT/'manuscript/journal_v11/MANUSCRIPT.md').read_text()
    app_a = v11.split('## Appendix A. Companion tables', 1)[1].split('## Appendix B. NYC transit replication', 1)[0]
    app_d = v11.split('## Appendix D. Reproduction map', 1)[1]
    app_a = re.sub(r'\bTable(s?) A(\d+)', r'Table\1 S\2', app_a); app_d = re.sub(r'\bTable(s?) A(\d+)', r'Table\1 S\2', app_d)
    sup12 = '## S1. Companion tables' + app_a.rstrip() + '\n\n## S2. Reproduction map (previous draft numbering; see note)' + app_d
s1, s2 = sup12.split('## S2.', 1)
s2 = ('## S2. Reproduction map\n\nRows refer to the previous draft (v12) numbering, mapped as follows: v12 Tables 2–7 are Tables S16–S21; 8, 8c are Table 3 of the main paper; 8b and 9 are Tables S28–S29; 10–12 are S22–S24; 13 is replaced by Table 6 of the main paper; 14 is S25; B1 and C1 are S26 and S27; v12 Figures 1–4 are Figures S1–S4; v12 Sections 5, 7, 8 and 10 are Supplementary Sections S3, S4, S5 and S6, and v12 Section 6 is Section 5 of the main paper. New in v13: Table 2 (results/longer_panel_stage_a_v1, longer_panel_foundation_v1); Table 3 and Figures 1–2 (src/scorecard_v1.py, figures_v13.py; results/scorecard_v1); Table 4 (src/leaf_size_experiment_v1.py, leaf_size_analysis_v1.py); Table 5, Figure 3 and Section S10 (src/robustness_experiments_v1.py, robustness_analysis_v1.py); Table 6 (src/decision_rules_14_v1.py); manuscript built by src/build_journal_v13.py.\n'
      + s2.split('\n', 1)[1].replace('| This manuscript | manuscript/journal_v11 | src/build_journal_v11.py (from journal_v10) |', '| This manuscript | manuscript/journal_v13 | src/build_journal_v13.py (from journal_v12) |'))
s1 = '## S1. Companion tables' + s1.split('## S1. Companion tables', 1)[1]
supp = '# Online supplement\n\nWhat replicates when festival indicators are tested on new states? Typed versus pooled indicators in Indian electricity forecasting\n\n**Names.** Sections S1 to S9 come from the previous draft and use its model names: "Stable LightGBM" and "LGBM" are the tuned LightGBM of the main paper; "Tree leaf minimum 2" and "LGBM-2" are the leaf-2 LightGBM; "Rich Ridge" is Ridge. Hypothesis labels H1-H3 in Section S3 refer to Stage B and in Sections S5 and S9 to the first state-level test, as in Table 3 of the main paper.\n\n' + s1.rstrip() + '\n\n' + s2.rstrip() + '\n'
for title, body in moved:
    body = map_refs(body.strip('\n'))
    body = re.sub(r'(?m)^## .*\n', '', body)
    supp += f'\n## {title}\n\n{body.strip()}\n'
# S10 robustness tables
nt = ['| Test | Model | Seed | Typed − pooled (moved dates) | Registered calendar | Change |', '| --- | --- | --- | --- | --- | --- |']
for r in noi.itertuples():
    nt.append(f"| {'first' if r.test == 'v1' else 'second'} | {'Rich Ridge' if r.model == 'ridge' else 'Leaf-2 LightGBM'} | {r.ledger[-1]} | {f4(r.typed_minus_pooled)} | {f4(r.registered_typed_minus_pooled)} | {f4(r.change)} |")
at = ['| Test | Penalty | Calendar | Typed | Pooled | Hybrid | Typed − pooled |', '| --- | --- | --- | --- | --- | --- | --- |']
for r in alp.itertuples():
    at.append(f"| {'first' if r.test == 'v1' else 'second'} | {r.alpha:g} | {r.calendar:.4f} | {r.typed:.4f} | {r.pooled:.4f} | {r.hybrid:.4f} | {f4(r.typed_minus_pooled)} |")
ht = ['| Test | Window (days) | Model | Calendar | Typed | Pooled | Hybrid |', '| --- | --- | --- | --- | --- | --- | --- |']
for r in win.sort_values(['test', 'W', 'model']).itertuples():
    ht.append(f"| {'first' if r.test == 'v1' else 'second'} | {r.W} | {r.model.replace('lgbm_leaf2', 'Leaf-2 LightGBM').replace('lgbm_selected', 'Tuned LightGBM').replace('ridge', 'Rich Ridge')} | {r.calendar:.4f} | {r.typed:.4f} | {r.pooled:.4f} | {r.hybrid:.4f} |")
supp += ('\n## S10. Robustness experiments\n\nAll exploratory, lead 1, with predictions committed before the runs (results/leaf_size_experiment_v1/PREDICTION.md and results/robustness_experiments_v1/PREDICTION.md); each prediction is listed as held or failed in the README files of those folders.\n\n'
         'Table S30. Balanced lead-1 MASE by arm and training window, event years 2021–2025.\n\n' + '\n'.join(ht) +
         '\n\nTable S31. Date-noise experiment: 20% of festival dates moved by one day (two seeds), event years 2017–2025.\n\n' + '\n'.join(nt) +
         '\n\nTable S32. Ridge with fixed penalties for every arm, 730-day window, event years 2017–2025: balanced lead-1 MASE.\n\n' + '\n'.join(at) + '\n')
NAME = {'ridge': 'Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'Tuned LightGBM', 'lightgbm_capacity2': 'Leaf-2 LightGBM'}
mm = pd.read_csv(R/'scorecard_v1/mixed_model.csv')
sens = pd.read_csv(R/'new_states_v2/analysis/sensitivity_author_checked_rows_only.csv').set_index('hypothesis')
nc2 = pd.read_csv(R/'new_states_v2/analysis/sensitivity_without_2020_2021.csv').set_index('hypothesis')
am2 = pd.read_csv(R/'new_states_v2/analysis/all_models_lead1.csv')
s11 = ['| Analysis | R1 SARIMAX | R2 leaf-2 LightGBM | M1 | M2 |', '| --- | --- | --- | --- | --- |']
for name, t in [('Without 2020–2021', nc2), ('Rows checked one by one only', sens)]:
    s11.append(f"| {name} | " + ' | '.join(f"{(f'{t.loc[k, "statistic"]:+.2f}'.replace('-', '−') if k == 'M2' else f4(t.loc[k, 'statistic']))} ({t.loc[k, 'decision'].lower()})" for k in ['R1', 'R2', 'M1', 'M2']) + ' |')
s12 = ['| Model | Typed − pooled | Clusters | Two-sided p |', '| --- | --- | --- | --- |'] + [f"| {NAME[r.model]} | {f4(r.typed_minus_pooled)} | {r.clusters} | {p3(r.p_two_sided)} |" for r in am2.itertuples()]
s13 = ['| Model | Estimate | 95% interval | p (two-sided) | SD state | SD family-year | Converged |', '| --- | --- | --- | --- | --- | --- | --- |'] + [
    f"| {NAME[r.model]} | {f4(r.intercept)} | {f4(r.ci_low)} to {f4(r.ci_high)} | {p3(r.p_two_sided)} | {r.sd_state:.4f} | {r.sd_family_year:.4f} | {'yes' if r.converged else 'no'} |" for r in mm.itertuples()]
supp += ('\n## S11. Second registered test: sensitivities, all models, mixed model\n\nTable S33. Registered sensitivities of the second test (statistic and decision).\n\n' + '\n'.join(s11)
         + '\n\nTable S34. Second test, all local models at lead 1 (reported, not tested): typed minus pooled MASE over 36 clusters, two-sided sign-flip p.\n\n' + '\n'.join(s12)
         + '\n\nTable S35. Linear mixed model over the fourteen states of both tests (typed minus pooled lead-1 MASE per state-family-year; crossed random effects for state and family-year; REML; descriptive). The Ridge fit did not converge and is shown for completeness only.\n\n' + '\n'.join(s13) + '\n')

# ---------------- references ----------------
refs12 = dict(re.findall(r'(?m)^\[(\d+)\] (.+)$', v12.split('## References', 1)[1].split('## Appendix B', 1)[0]))
order = []
for txt in [main, supp]:
    for grp in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', txt):
        for x in grp.split(','):
            x = x.strip()
            if x in refs12 and x not in order:
                order.append(x)
new = {old: str(i+1) for i, old in enumerate(order)}


def renum(t):
    return re.sub(r'\[(\d+(?:,\s*\d+)*)\]', lambda m: '[' + ', '.join(sorted({new[x.strip()] for x in m.group(1).split(',')}, key=int)) + ']', t)


main = renum(main); supp = renum(supp)
cited_main = sorted({int(x) for g in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', main) for x in g.split(',')})
cited_supp = sorted({int(x) for g in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', supp) for x in g.split(',')})
inv = {v: k for k, v in new.items()}
main = main.rstrip() + '\n\n## References\n\n' + '\n\n'.join(f'[{n}] {refs12[inv[str(n)]]}' for n in cited_main) + '\n'
supp = supp.rstrip() + '\n\n## References cited in the supplement\n\n' + '\n\n'.join(f'[{n}] {refs12[inv[str(n)]]}' for n in cited_supp) + '\n'

# ---------------- checks ----------------
abstract = main.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
assert 100 <= len(abstract.split()) <= 150, len(abstract.split())
for h in re.findall(r'(?m)^- (.+)$', main.split('## Highlights', 1)[1].split('## 1.', 1)[0]):
    assert len(h) <= 85, (len(h), h)
capt = set(re.findall(r'(?m)^Table (\d+)\.', main)); fig = set(re.findall(r'!\[Figure (\d)\.', main))
for m in re.finditer(r'\bTables? (\d+)\b(?! of the main)', main.split('## References')[0]):
    assert m.group(1) in capt, ('main table', m.group(0))
for m in re.finditer(r'\bFigures? (\d)\b', main.split('## References')[0]):
    assert m.group(1) in fig, ('main figure', m.group(0))
heads = set(re.findall(r'(?m)^##+ (\d+(?:\.\d+)?)\.? ', main))
for m in re.finditer(r'\bSections? (\d+(?:\.\d+)?)\b', main.split('## References')[0]):
    assert m.group(1) in heads, ('main section', m.group(0))
scapt = set(re.findall(r'(?m)^Table (S\d+)\.', supp))
for m in re.finditer(r'\bTables? (S\d+)', supp + main):
    assert m.group(1) in scapt, ('supp table', m.group(0))
for m in re.finditer(r'Supplementary Section (S\d+)', main):
    assert f'## {m.group(1)}.' in supp, m.group(0)
assert not re.search(r'\bAppendix [A-D]\b', main), 'appendix reference left'

# ---------------- output ----------------
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(SRC/'figures', OUT/'figures')
for f in ['india_contrasts.png', 'per_year.png', 'figure3_simulation.png', 'figure4_states.png']:
    shutil.copy2(V12/'figures'/f, OUT/'figures'/f)
(OUT/'MANUSCRIPT.md').write_text(main); (OUT/'SUPPLEMENT.md').write_text(supp)


def render(md, name):
    p = OUT/f'{name}.md'; p.write_text(md)
    subprocess.run(['pandoc', str(p), '-o', str(OUT/f'{name}.docx'), '--resource-path', str(OUT)], check=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v13-lo', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT), str(OUT/f'{name}.docx')],
                   check=True, capture_output=True)
    p.unlink()


def blind(t):
    t = t.replace('Binay Verma\n\nAffiliation: __________ . Corresponding author email: __________ .\n\n', '')
    t = t.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]')
    t = re.sub(r'https://osf\.io/\w+', '[registration link withheld for review]', t)
    t = re.sub(r'osf\.io/\w+', 'registration withheld for review', t)
    if '**Funding.**' in t:
        t = t.split('**Funding.**')[0] + '**Funding, competing interests, author contributions, use of generative AI:** on the separate title page.\n\n## References' + t.split('## References', 1)[1]
    for ident in ['Binay', 'Verma', 'github.com/Binay', 'osf.io']:
        assert ident not in t, ident
    return t


render(main, 'Typed_or_Pooled_Binay_Verma_v13'); render(blind(main), 'Typed_or_Pooled_v13_anonymised')
render(supp, 'Online_supplement_v13'); render(blind(supp), 'Online_supplement_v13_anonymised')
words = len(main.split('## Declarations')[0].split())
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='Journal-format draft v13; not submitted.',
               main_words=words, abstract_words=len(abstract.split()), reference_map_v12_to_v13=new,
               inputs={str(p.relative_to(ROOT)): sha(p) for p in [SRC/'MAIN.md', R/'scorecard_v1/scorecard.csv', R/'leaf_size_experiment_v1/analysis/by_leaf.csv',
                       R/'robustness_experiments_v1/analysis/window.csv', R/'robustness_experiments_v1/analysis/noise.csv',
                       R/'robustness_experiments_v1/analysis/ridge_alpha.csv', R/'decision_rules_14_v1/summary.csv', V12/'MANUSCRIPT.md']},
               outputs={p.name: sha(p) for p in sorted(OUT.glob('*')) if p.is_file()}), open(OUT/'build.json', 'w'), indent=1)
print('built v13: main words', words, 'abstract', len(abstract.split()))
