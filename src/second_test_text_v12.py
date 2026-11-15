"""Text for the second registered test in journal v12, built from results/new_states_v2/analysis (numbers read, not typed).

build(analysis_dir) returns {'replacements': [(old, new), ...]} applied once each by src/build_journal_v12.py.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def f4(x):
    return f'{x:+.4f}'.replace('-', '−')


def pv(p):
    return '< 0.0001' if p < 1e-4 else (f'{p:.4f}' if p < 0.01 else f'{p:.3f}')


def rho(x):
    return f'{x:+.2f}'.replace('-', '−')


def build(A):
    A = Path(A)
    t = pd.read_csv(A/'hypothesis_tests.csv').set_index('hypothesis')
    nc = pd.read_csv(A/'sensitivity_without_2020_2021.csv').set_index('hypothesis')
    au = pd.read_csv(A/'sensitivity_author_checked_rows_only.csv').set_index('hypothesis')
    fh = pd.read_csv(A/'sensitivity_first_test_h.csv').set_index('hypothesis')
    cb = pd.read_csv(A/'secondary_combined_both_tests.csv')
    b = pd.read_csv(A/'balanced.csv'); b = b[b.horizon == 1].pivot(index='model', columns='arm', values='MASE')
    allm = pd.read_csv(A/'all_models_lead1.csv').set_index('model')
    design = json.loads((ROOT/'results/new_states_v2/design_summary.json').read_text())
    h = pd.read_csv(ROOT/'review/new_states_v2/power/early_heterogeneity_2015_2020.csv').set_index('state')
    pw = pd.read_csv(ROOT/'review/new_states_v2/power/power_R1_R2.csv')
    p1 = pw[(pw.hypothesis == 'R1') & (pw.scenario == 'first-test effect')].iloc[0]
    p2 = pw[(pw.hypothesis == 'R2') & (pw.scenario == 'first-test effect')].iloc[0]
    dec = {k: t.loc[k, 'decision'] for k in t.index}
    assert dec == {'R1': 'NOT CONFIRMED', 'R2': 'CONFIRMED', 'M1': 'NOT CONFIRMED', 'M2': 'NOT CONFIRMED'}, dec
    R1, R2, M1, M2 = (t.loc[k] for k in ['R1', 'R2', 'M1', 'M2'])
    c1 = cb[cb.model == 'sarimax'].iloc[0]; c2 = cb[cb.model == 'lightgbm_capacity2'].iloc[0]
    yrs = lambda r: f"{int(r.years_in_direction)}/{int(r.years)}"
    pw_txt = f"R1 passes in only about {p1.power_holm_worst_0_0125*100:.0f}–{p1.power_holm_best_0_05:.0%} of simulated replications and R2 in about {p2.power_holm_worst_0_0125*100:.0f}–{p2.power_holm_best_0_05:.0%}"
    top3 = ', '.join(h.sort_values('h_abs', ascending=False).index[:3])

    sec62 = f"""### 6.2 Second test: seven more states

To check whether these results travel, and whether typing helps where festival effects differ, a second test was registered on OSF on 15 November 2026 on the seven remaining states whose mean daily energy is at least 70 GWh: Punjab, Haryana, West Bengal, Kerala, Bihar, Odisha and Chhattisgarh. Registration came before any parameter selection or forecast for these states; the pipeline, arms, case rule and decision rule are those of Section 6.1, with local models only. The calendar has one main festival day per family, state and year (231 rows for 2015–2025). Because festival days rarely differ between states, each row was compared with the dates checked for the first test: 183 agree, 43 were checked by the author one by one (the 22 that did not agree and a random sample of 21 that did; the sample found two Holi rows dated on the eve, so the Holi day was used), and 5 follow that Holi rule. Agreement with other states establishes the festival day, not each state's own notification. The design has {design['event_cases']:,} event cases in {design['clusters']} family-year clusters.

Four hypotheses were tested at lead 1 with Holm correction across them: R1 and R2 repeat H1 and H3; M1 states that Ridge does better with typed flags over 2021–2025 in the three states with the most dispersed festival effects, estimated from 2015–2020 demand only ({top3}); M2 states that this dispersion is negatively rank-correlated with the Ridge difference across the seven states. The dispersion is the between-family standard deviation of log festival effects, net of sampling noise, without the division by the mean effect used in Section 7, because one state's mean effect is close to zero; this choice was made after seeing the 2015–2020 values and before any forecast. The registration stated the power in advance: if the true effects equal those of Section 6.1, {pw_txt}.

Table 8c gives the result. R2 is confirmed and larger than in the first test ({f4(R2.statistic)}, all nine years). R1 is not: SARIMAX's typed advantage is close to zero ({f4(R1.statistic)}, {yrs(R1)} years). M1 and M2 point in the predicted direction but are not confirmed ({f4(M1.statistic)}, {yrs(M1)} years; Spearman {rho(M2.statistic)}). The decisions are the same without 2020–2021 and with the first test's dispersion measure. On the 43 rows checked one by one ({int(au.loc['R2','units'])} clusters), nothing is confirmed (R2 {f4(au.loc['R2','statistic'])}). As in the first test, Stable LightGBM's typed arm equals its calendar arm ({b.loc['lightgbm','day5']:.5f}), while its pooled arm improves ({b.loc['lightgbm','pooled_day5']:.5f}). Pooling both tests (secondary, 14 states, {int(c1.clusters)} family-year clusters), SARIMAX has {f4(c1.statistic)} (one-sided p {c1.p_one_sided:.3f}) and the leaf-2 LightGBM {f4(c2.statistic)} (p {pv(c2.p_one_sided)}).

Table 8c. Second registered test, seven more states (2017–2025, {design['clusters']} clusters): lead 1, day flags, typed minus pooled MASE (M2: Spearman correlation). Holm across R1, R2, M1 and M2. (−) expects typed better, (+) pooled better.

| Hypothesis | Statistic | Years | One-sided p | Holm p | Decision |
| --- | --- | --- | --- | --- | --- |
| R1 SARIMAX (−) | {f4(R1.statistic)} | {yrs(R1)} | {pv(R1.p_one_sided)} | {pv(R1.holm)} | not confirmed |
| R2 LightGBM leaf 2 (+) | {f4(R2.statistic)} | {yrs(R2)} | {pv(R2.p_one_sided)} | {pv(R2.holm)} | confirmed |
| M1 Ridge, three most dispersed states (−) | {f4(M1.statistic)} | {yrs(M1)} | {pv(M1.p_one_sided)} | {pv(M1.holm)} | not confirmed |
| M2 dispersion vs Ridge gain, ρ (−) | {rho(M2.statistic)} | – | {pv(M2.p_one_sided)} | {pv(M2.holm)} | not confirmed |

"""
    for k in ['R1', 'R2', 'M1', 'M2']:
        assert nc.loc[k, 'decision'] == t.loc[k, 'decision'] and fh.loc[k, 'decision'] == t.loc[k, 'decision'], k
    assert (au.decision == 'NOT CONFIRMED').all()
    assert abs(b.loc['lightgbm', 'day5']-b.loc['lightgbm', 'calendar']) < 1e-12

    abstract_new = ("Forecasters adding festival indicators must choose between one indicator per festival (typed) and one shared indicator (pooled). "
                    "We compare both for daily electricity in Indian states, with matched zero and placebo controls, four local models and two foundation models. "
                    "Hypotheses formed in three exploratory states were registered and tested on seven further states, then again on seven more. "
                    "A LightGBM with a small minimum leaf size did better with a pooled indicator in both tests, the second time in all nine years. "
                    "SARIMAX did better with typed indicators in the first test only, by a small margin resting mainly on one state. "
                    "The expected pooling preference of TimesFM-3 was not confirmed, nor was the idea that typing helps where festival effects differ. "
                    "Trees cannot use an indicator active on fewer training days than their minimum leaf size, which is why a larger-leaf LightGBM ignored typed indicators.")
    n = len(abstract_new.split()); assert 100 <= n <= 150, n

    R = []
    R.append(('# Typed or pooled festival indicators? Evidence from ten Indian states with registered tests',
              '# Typed or pooled festival indicators? Evidence from seventeen Indian states with two registered tests'))
    old_abs = ("Forecasters adding festival indicators must choose between one indicator per festival (typed) and one shared indicator (pooled). We compare both for daily electricity in Indian states, with matched zero and placebo controls, two foundation models and four local models. In three exploratory states the better choice depended on the model. We registered three hypotheses and tested them once on seven further states over 2017–2025. As hypothesised, SARIMAX did better with typed indicators and a small-leaf LightGBM with a pooled indicator, but both effects were small and rested mainly on one state; neither held when calendars were restricted to official sources. The expected pooling preference of TimesFM-3 was not confirmed. Trees cannot use an indicator active on fewer training days than their minimum leaf size, which is why LightGBM with a larger leaf size ignored typed indicators. An exploratory simulation reproduces the main differences between states, mainly through two states.")
    R.append((old_abs, abstract_new))
    R.append(('- Registered test in seven new states: SARIMAX prefers typed, leaf-2 trees pooled\n- Both confirmed effects are small and rest mainly on one state, Gujarat\n',
              '- Two registered tests in 14 new states: small-leaf trees prefer a pooled flag\n- SARIMAX preferred typed flags in the first test but not in the second\n'))
    R.append(('3. **Registered tests.** The pattern was written down as a hypothesis before three further Maharashtra years were evaluated (Section 5.4), and three hypotheses were then registered and tested once on seven further states (Section 6). Two were confirmed, with small effects that rest mainly on one state, and one was not.',
              '3. **Registered tests.** The pattern was written down as a hypothesis before three further Maharashtra years were evaluated (Section 5.4), and three hypotheses were then registered and tested once on seven further states (Section 6.1). Two were confirmed, with small effects that rest mainly on one state, and one was not. A second registered test on seven more states (Section 6.2) replicated the tree result, more strongly, but not the SARIMAX result, and did not confirm that typing helps where festival effects differ.'))
    R.append(('| New states (Section 6) | confirmatory | 7 | 2017–2025 | 5,157 | – | 45 | 6 |',
              f"| New states (Section 6.1) | confirmatory | 7 | 2017–2025 | 5,157 | – | 45 | 6 |\n| Second test (Section 6.2) | confirmatory | 7 | 2017–2025 | {design['event_cases']:,} | – | {design['clusters']} | 4 local |"))
    R.append(('Everything in Section 8 was written after the analysis and is exploratory.',
              'Everything in Section 8 was written after the analysis and is exploratory. The second test (Section 6.2) was registered on OSF on 15 November 2026, after its calendar, power calculation and analysis script had been committed and before any parameter selection or forecast for its states; its analysis script was run once, unchanged, at 19:26 UTC that day.'))
    R.append(('## 6. Registered test in seven further states\n\nThree hypotheses were registered',
              '## 6. Registered tests in further states\n\n### 6.1 First test: seven further states\n\nThree hypotheses were registered'))
    R.append(('\n## 7. Mechanism and simulations', '\n' + sec62 + '## 7. Mechanism and simulations'))
    R.append(('A test on 2027–2028 festivals with official calendars only has been drafted (results/prospective_2027_v1) but is not yet registered.',
              'The second registered test (Section 6.2) checked the mechanism on seven more states and did not confirm it. A test on 2027–2028 festivals with official calendars only is registered and will be analysed after those festivals.'))
    R.append(('typed flags suited SARIMAX, an effect that rests mainly on one state;',
              'typed flags suited SARIMAX in the first further-state test, mainly through one state, but not in the second;'))
    R.append(('with a small leaf size they did better with a pooled flag;', 'with a small leaf size they did better with a pooled flag, in both registered tests;'))
    R.append(('whether heterogeneity estimated from past data can guide the choice is not yet shown (Section 8);',
              'that heterogeneity estimated from past data can guide the choice was tested and not confirmed (Section 6.2);'))
    R.append(('The main evidence is the registered test on seven further states in Section 6.', 'The main evidence is the two registered tests on fourteen further states in Section 6.'))
    R.append(('A comparison with the closest published designs, a replication on New York transit data and a reproduction map are in the appendices.',
              'A comparison with the closest published designs and a replication on New York transit data are in the appendices; companion tables and a reproduction map are in the online supplement.'))
    R.append(('The evidence covers ten states, five festival families and the years 2017–2025.',
              'The evidence covers seventeen states, five festival families and the years 2017–2025.'))
    R.append(('The TimesFM-3 preference for pooling seen in Stage A did not replicate.',
              f"The TimesFM-3 preference for pooling seen in Stage A did not replicate. In the second test the SARIMAX effect did not replicate either; the power for that test was stated in advance as {p1.power_holm_worst_0_0125:.0%}–{p1.power_holm_best_0_05:.0%}, so the failure is weak evidence against the first result, but it does not support it. The second test's calendar rests mainly on agreement with dates checked for other states (183 of 231 rows) rather than on each state's own notification, and on the 43 rows checked one by one nothing is confirmed. Its dispersion measure was chosen after seeing 2015–2020 values, before any forecast."))
    R.append(("In a registered test on seven further states, SARIMAX did better with typed flags and a LightGBM with a small minimum leaf size did better with a pooled flag, as hypothesised from three other states; the expected TimesFM-3 preference for pooling was not confirmed. The confirmed effects are small and rest mainly on one state. A tree model cannot use a flag that is set on fewer training days than its minimum leaf size, which is why Stable LightGBM ignored typed flags altogether. Exploratory analyses suggest that typing helps more where festival effects differ strongly; a test on 2027–2028 festivals has been drafted to check this.",
              "In two registered tests on fourteen further states, a LightGBM with a small minimum leaf size did better with a pooled flag both times, as hypothesised from three other states. SARIMAX did better with typed flags in the first test, by a small margin resting mainly on one state, and not in the second; the expected TimesFM-3 preference for pooling was not confirmed. A tree model cannot use a flag that is set on fewer training days than its minimum leaf size, which is why Stable LightGBM ignored typed flags altogether. Exploratory analyses suggested that typing helps more where festival effects differ strongly, but a registered test on seven more states did not confirm this; a test on 2027–2028 festivals is registered."))
    R.append(('The new-states registration is at https://osf.io/yw7mr.',
              'The new-states registration is at https://osf.io/yw7mr; the second-test and 2027–2028 registrations are on OSF [links to be added].'))
    return dict(replacements=R)
