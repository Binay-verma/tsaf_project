# What replicates when festival indicators are tested on new states? Typed versus pooled indicators in Indian electricity forecasting

Binay Verma

Affiliation: __________ . Corresponding author email: __________ .

## Abstract

Forecasters who add festival indicators to a demand model must choose between one indicator per festival (typed) and one shared indicator (pooled). We compare both for daily electricity in seventeen Indian states, with zero-channel and placebo controls, four local models and two foundation models. Patterns from three exploratory states were registered and tested on further data, including fourteen new states. Most effects shrank: SARIMAX's typed advantage held in two of three tests but not the last, and TimesFM-3's pooling preference and a heterogeneity explanation were not confirmed. A LightGBM with minimum leaf size 2 did better with the pooled indicator in both state-level tests. Pre-committed experiments partly explain this: in a two-year window a typed indicator covers two to four training days, too few for most trees to split on. Longer windows shrank the pooled advantage, and for Ridge and LightGBM passing both indicators matched the better one.

**Keywords:** holiday effects; event covariates; load forecasting; gradient boosting; time-series foundation models; replication; pre-registration.

## Highlights

- Typed and pooled festival flags compared in 17 Indian states with controls
- Most exploratory effects shrank or vanished in two registered tests
- Small-leaf LightGBM preferred one pooled flag in both registered tests
- A tree cannot use a flag set on fewer training days than its leaf size
- Longer windows shrank the trees’ pooled advantage; passing both flags did as well

## 1. Introduction

Holidays and festivals are rare, recurring and heterogeneous. A forecaster who adds them to a model faces an old choice: give each named event its own indicator, so that each can have its own effect, or pool them into one indicator, so that sparse events borrow strength from one another [1, 2]. Covariate-informed time-series foundation models (TSFMs) such as Chronos-2 [3] and TimesFM-3 [4] reopen the choice in a new form, because the forecaster no longer estimates the effect but only decides which channels to pass [5, 6].

We study this choice for daily electricity in Indian states, where festivals such as Holi, Dussehra and Diwali move with the lunisolar calendar and differ in size and sign from state to state. Our first, exploratory analyses on three states suggested a tidy model-class pattern: SARIMAX gained from typed flags, LightGBM and TimesFM-3 from a pooled flag. Exploratory patterns of this kind often fail to replicate [7], so we registered them and tested them on data no model had been evaluated on: further years for one state, then seven new states, then seven more.

The main finding is how little survived. Of the exploratory effects, the SARIMAX typed advantage was confirmed on further Maharashtra years and in the first test of new states, at about a third of its exploratory size, and was near zero in the second; the TimesFM-3 pooling preference vanished; and a mechanism proposed to explain which states gain from typing was not confirmed. One result replicated in both state-level tests: a LightGBM with a minimum leaf size of 2 forecast better with one pooled flag. Part of its explanation is mechanical. In the two-year training window used here, each typed flag is set on two to four days, and a tree cannot split on a flag that is set on fewer days than its minimum leaf size. Experiments whose predictions were committed before they were run are consistent with this: they show exactly when trees ignore typed flags, and that the pooled advantage shrinks when the training window is longer (Section 6). The leaf-2 result itself depends on an unusual setting and is only partly explained by support.

Our contributions are:

1. **A replication record.** All registered typed-versus-pooled hypotheses, with their decisions, sensitivities and 95% intervals, in one scorecard, showing how effects shrink from exploration to confirmation (Section 5).
2. **A support mechanism for tree models.** The number of training days on which an indicator is set, relative to the minimum leaf size, decides whether a tree can use typed indicators at all; we document this and trace how the typed-versus-pooled difference depends on leaf size and on the length of the training window (Section 6).
3. **Negative results reported as such.** The SARIMAX typed advantage did not replicate in the second test, no preference was found for Chronos-2, the TimesFM-3 hypothesis was not confirmed, and festival-effect heterogeneity estimated from past data did not predict which states gain from typing (Sections 5 and 7).
4. **A practical rule.** When the better representation is uncertain, passing both kinds of indicator, or averaging the two forecasts, limits the cost of choosing wrongly (Sections 7 and 8).

The study does not introduce typed or pooled indicators, which are established, and makes no claim of a new method. Its value is in testing how the choice behaves when the same pipeline meets new data.

## 2. Related work

**Holidays in load forecasting.** Load forecasting is reviewed in [8], and competition models give public holidays special treatment [9, 10]. Ziel [1] compared one shared holiday dummy, grouped dummies and one dummy per holiday for German load and found that many per-holiday dummies did not clearly improve on one additional dummy. Arora and Taylor treat special days with rule-based seasonal models [2, 11]. For India, evidence is sparse: a regional study found no significant effect of a pooled national-holiday dummy on northern-grid load [12], day-ahead holiday load forecasting has been addressed at a conference [13], and moving Indian holidays have been modelled in manufacturing statistics [14].

**Moving holidays and shrinkage.** Calendar adjustment has long used holiday-specific regressors for lunar and lunisolar festivals [15, 16, 17], and practical procedures select or drop them by information criteria [18, 19]. Prophet gives each named holiday its own effect with a prior that shrinks it [20], which sits between typed and pooled indicators; we test such a hybrid arm only as an exploratory check (Section 7). For tree models, the minimum leaf size limits which splits are possible [21, 22].

**Foundation models and covariates.** Pretrained time-series models were introduced without covariates [23, 24, 25]; support for known future covariates came later [26, 27] and is native in Chronos-2 and TimesFM-3 [3, 4]. Kreusel et al. [5] examine calendar encodings in these two models, Alipour et al. [6] learn event representations from residual responses, Kaljevic et al. [28] benchmark foundation models for load forecasting under covariate uncertainty, and Meyer et al. [29] show how information leakage can affect their evaluation.

**Evaluation, replication and combination.** We use the mean absolute scaled error [30, 31]. Because our unit of evidence is a festival-year cluster and there are few of them, we use sign-flip randomisation tests [32, 33] rather than pairwise tests [34], with Holm's adjustment [35]. Forecasting results do not always replicate [7], and registering hypotheses before testing them separates hypotheses formed from data from those tested on new data [36]. Equal-weight averaging of forecasts [37, 38] is used here only as a hedge between two representations.

## 3. Data and design

### 3.1 Electricity series and states

The target is daily energy met in GWh from a GRID-INDIA/POSOCO compilation, for seventeen states in three groups: three exploratory states (Delhi, Karnataka, Maharashtra); seven states of the first registered test (Uttar Pradesh, Rajasthan, Madhya Pradesh, Gujarat, Telangana, Andhra Pradesh, Tamil Nadu); and seven of the second (Punjab, Haryana, West Bengal, Kerala, Bihar, Odisha, Chhattisgarh), which are all remaining states with mean daily energy of at least 70 GWh. The series are energy met, not unconstrained demand. All values are public and historical, so every result is retrospective: the registrations fix the analysis before it is run, not before the data exist.

### 3.2 Festival calendars

Five festival families are used where they are public holidays in most years: Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali. The festival day itself is flagged, also when it falls on a weekend. Calendar quality is the weakest part of the data, and we state it plainly. In the exploratory states, rows for 2022–2025 were checked against retained state documents. In the first registered test, 90 of 331 rows (2015–2025) come from official notifications or government reproductions and 241 from secondary sources (reposts and holiday aggregators); the author checked every row, but the method of each check was not recorded. In the second test, the 231 rows were found by machine search, again mostly on secondary sources, and compared with the dates verified for the same festival and year in the first test: 183 agree, 43 were checked by the author one by one (the 22 that disagreed and a random sample of 21 that agreed, in which two Holi dates were on the eve), and 5 Holi rows were moved to the Holi day by rule. Agreement with other states corroborates the festival day; it does not show each state's own notification. Section 7 tests how sensitive the results are to dating errors.

### 3.3 Models, arms and controls

Four local models are refitted monthly on the previous 730 days: a rich Ridge regression, LightGBM [39] with parameters selected each year on the 180 days before the event year using the ordinary calendar only ("tuned LightGBM", whose selected minimum leaf size is 5 or 20), the same LightGBM with the minimum leaf size fixed at 2 ("leaf-2 LightGBM"), and SARIMAX(1,0,0)(1,0,0,7). Ridge and LightGBM use 27 past-only history features. Two pinned TSFMs, Chronos-2 and TimesFM-3, are used zero-shot with 730 days of context. Selected parameters are shared by all arms of a model, so arms differ only in their festival channels.

Every arm keeps 13 ordinary calendar channels. The compared arms add five channels: **typed** (one indicator per festival family, on the festival day), **pooled** (one indicator on any festival day, padded with four zero channels to equal dimension), **zero** (five zero channels) and **placebo** (the typed indicators shifted by seeded, weekday-preserving offsets of four to six weeks). For each festival a ±3-day window is forecast at leads 1, 7 and 14; the registered tests concern lead 1.

### 3.4 Error measure and tests

The error measure is MASE [30] with a fixed scale from the 730 days before each event year. Errors are averaged within state, festival family and year, then over states within each family-year, and each family-year is one cluster. The registered tests use the mean typed-minus-pooled MASE over clusters (positive favours pooling) with a one-sided sign-flip test in the hypothesised direction and Holm's adjustment within each registration. A sign-flip test assumes symmetric cluster differences; clusters in the same year share weather and data vintage, so the tests are approximate. We add descriptive 95% t intervals over clusters and a linear mixed model with crossed random effects for state and family-year.

### 3.5 Registration sequence

Table 1 gives the sequence. The Stage A and Stage B protocols are commits in the author's public repository, whose timestamps are author-set; the two state-level tests are also registered on OSF. For the first state-level test, the OSF registration was recorded after local parameter selection (ordinary calendar only) had started but before any forecast with festival indicators. For the second, the protocol and analysis script were committed at 17:52 UTC on 15 November 2026 and, by the author's record, the OSF submission was complete by 18:21 UTC, the minute parameter selection started; all its forecasts ran afterwards and its analysis script was run once. The 2027–2028 registration links a protocol file containing one wrong sentence (that no 2027 state notification existed; Tamil Nadu's had been published), corrected in a later commit without changing any hypothesis or rule. The exploratory experiments of Sections 6 and 7 had their predictions committed before they ran (commits 4108af1 and 1f0a1b0, author timestamps, 5 seconds and 12 minutes before the runs). These registrations are weaker evidence of pre-specification than an independently timestamped registry would be, and we rely on them only for the order of analysis and forecasts.

Table 1. Cohorts and registration sequence.

| Stage | Role | States | Event years | Event cases | Clusters | Models | Fixed before forecasts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage A | exploratory | 3 | 2022–2025 | 1,056 | 20 | 6 | – |
| Stage B | registered (repository) | Maharashtra | 2019–2021 | 327 | 15 | 4 local | hypotheses H1–H2, rule |
| First test | registered (osf.io/yw7mr) | 7 | 2017–2025 | 5,157 | 45 | 6 | H1–H3, rule, script |
| Second test | registered (osf.io/f9tv4) | 7 | 2017–2025 | 3,969 | 36 | 4 local | R1, R2, M1, M2, rule, script, power |
| 2027–2028 | registered (osf.io/xr25s) | 3 + 4 | 2027–2028 | – | – | 4 | P1, P2; not yet observed |

## 4. Where the hypotheses came from

On the three exploratory states over 2022–2025 (Stage A), festival flags clearly helped Ridge and SARIMAX: at lead 1, typed and pooled day flags lowered their MASE by more than 0.1 against the calendar arm, while the zero and placebo arms stayed within 0.003 of it, so the gains come from festival dates, not from extra channels. The typed-versus-pooled contrasts depended on the model (Table 2). The tuned LightGBM was better with the pooled flag (+0.0429, Holm p 0.029 over eight lead-1 cells), the leaf-2 LightGBM pointed the same way in all four years (+0.0458, Holm p 0.063), SARIMAX pointed to typed flags in all four years (−0.0300, Holm p 0.160), and TimesFM-3 favoured the pooled flag (+0.0506, Holm p 0.017 over four foundation-model cells); Ridge and Chronos-2 showed no ordering. Over all 24 local model/representation/lead cells, six had a raw p below 0.05 and none survived Holm over 24. Details, all leads and the window representations are in Supplementary Section S3.

Table 2. Stage A (three states, 2022–2025, 20 clusters): lead-1 typed minus pooled MASE, exploratory. Positive favours pooling.

| Model | Typed − pooled | Holm p (family of cells) |
| --- | --- | --- |
| Rich Ridge | −0.0109 | 0.588 (8 local) |
| SARIMAX | −0.0300 | 0.160 (8 local) |
| Tuned LightGBM | +0.0429 | 0.029 (8 local) |
| Leaf-2 LightGBM | +0.0458 | 0.063 (8 local) |
| Chronos-2 | +0.0038 | 1.000 (4 foundation) |
| TimesFM-3 | +0.0506 | 0.017 (4 foundation) |

## 5. Registered tests

### 5.1 Hypotheses

Stage B tested on further Maharashtra years (2019–2021; their 2020–2021 values had been Stage A training history) that the tuned LightGBM favours the pooled flag and SARIMAX typed flags, with the leaf-2 LightGBM as a secondary hypothesis. The first state-level test registered three hypotheses on seven new states: SARIMAX favours typed flags (H1), TimesFM-3 the pooled flag (H2) and the leaf-2 LightGBM the pooled flag (H3), each requiring a Holm-adjusted p below 0.05 and the hypothesised sign in at least six of nine event years. After that test, exploratory analyses suggested that typing helps where a state's festival effects differ strongly. The second state-level test therefore repeated H1 and H3 (as R1 and R2) on seven more states and added two mechanism hypotheses: Ridge gains from typing in the three states with the most dispersed festival effects, estimated from 2015–2020 demand only (M1), and dispersion is negatively rank-correlated with the Ridge gain across the seven states (M2). Its registration stated in advance that, if the true effects equalled those of the first test, R1 and R2 would pass in only about 18–34% and 19–36% of simulated replications.

### 5.2 Results

Table 3 lists every registered hypothesis. Four were confirmed and five were not. The tuned LightGBM hypothesis of Stage B gave an exact zero, because its selected minimum leaf size of 20 exceeded the number of days on which any festival flag was set, so all its arms gave identical forecasts (Section 6). The SARIMAX typed advantage was confirmed in Stage B and in the first state-level test but not in the second (whose power for it was 18–34%), where it was close to zero (−0.0008, 95% interval −0.0076 to 0.0060). The TimesFM-3 pooling preference was not confirmed (−0.0004). The mechanism hypotheses M1 and M2 pointed in the predicted direction but were not confirmed. The leaf-2 LightGBM favoured the pooled flag in both state-level tests (+0.0068 and +0.0147), the second time in all nine event years.

Table 3. Registered typed-versus-pooled hypotheses (lead 1, day flags). Estimate: typed minus pooled MASE (M2: Spearman correlation); positive favours pooling. Interval: descriptive 95% t interval over the units, not adjusted. Holm p within each registration.

| Test | Hypothesis | Units | Estimate | 95% interval | Holm p | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Stage B | H1: Tuned LightGBM, pooled better | 15 clusters | +0.0000 | exactly 0 | 1.000 | not confirmed |
| Stage B | H2: SARIMAX, typed better | 15 clusters | −0.0539 | −0.1059 to −0.0020 | 0.031 | confirmed |
| Stage B | H1b (secondary, no Holm): Leaf-2 LightGBM, pooled better | 15 clusters | +0.0648 | – | – | meets rule unadjusted |
| First | H1: SARIMAX, typed better | 45 clusters | −0.0097 | −0.0185 to −0.0009 | 0.038 | confirmed |
| First | H2: TimesFM-3, pooled better | 45 clusters | −0.0004 | −0.0105 to +0.0097 | 0.531 | not confirmed |
| First | H3: LightGBM leaf 2, pooled better | 45 clusters | +0.0068 | +0.0009 to +0.0127 | 0.038 | confirmed |
| Second | R1: SARIMAX, typed better | 36 clusters | −0.0008 | −0.0076 to +0.0060 | 0.489 | not confirmed |
| Second | R2: LightGBM leaf 2, pooled better | 36 clusters | +0.0147 | +0.0094 to +0.0201 | < 0.0001 | confirmed |
| Second | M1: Ridge, typed better in the three most dispersed states | 45 units | −0.0081 | −0.0247 to +0.0085 | 0.489 | not confirmed |
| Second | M2: Dispersion vs Ridge gain (Spearman) | 7 states | −0.43 | – | 0.489 | not confirmed |

The effects shrank from exploration to confirmation (Figure 1). SARIMAX went from −0.0300 (Stage A) and −0.0539 (Stage B) to −0.0097 and −0.0008; TimesFM-3 from +0.0506 to −0.0004; the leaf-2 LightGBM from +0.0458 and +0.0648 to +0.0068 and +0.0147. The surviving effect is small in absolute terms: in the first test, the leaf-2 LightGBM's pooling advantage corresponds to 0.16 GWh per festival-window day against mean demand of 257 GWh (about 0.06%), or about 1% of its lead-1 MASE (2% in the second test). Without Gujarat, the first test's leaf-2 estimate falls from +0.0068 to +0.0011 (Supplementary Section S5).

![Figure 1. Typed minus pooled lead-1 MASE for the three exploratory patterns that were registered, by stage (TimesFM-3 was tested once; its open circle is the Stage A point estimate without interval), from the exploratory stage to the two registered state-level tests (95% intervals over clusters). Positive values favour pooling.](figures/shrinkage.png)

**Sensitivities.** Without 2020–2021, the decisions of both state-level tests are unchanged except that the first test's SARIMAX result is no longer significant (−0.0086, Holm p 0.115). The leaf-2 LightGBM result does not hold on the best-checked calendar rows alone: with official-source rows only, the first test's estimate reverses (−0.0074, 44 clusters, almost all from Tamil Nadu and Telangana; in this subset TimesFM-3 is significantly better with typed flags, contradicting H2), and with the 43 rows checked one by one the second test's is +0.0040 (24 clusters, six of nine years, not confirmed; Supplementary Section S11). Both subsets are small and leave out the states that carry the main effects, so they have little power, but the result is not shown on the best-documented rows.

**States.** Figure 2 shows the state-level estimates. In the first test the leaf-2 LightGBM result rests mainly on Gujarat (+0.065), and Madhya Pradesh and Tamil Nadu go the other way; in the second it is positive in four states (Haryana +0.066, Punjab +0.030, Chhattisgarh +0.025, West Bengal +0.013) and about zero in the three states with the smallest festival effects (Bihar, Kerala, Odisha). The SARIMAX typed advantage of the first test comes mostly from Gujarat (−0.076); no second-test state shows a clear typed advantage. A mixed model over all fourteen states with crossed random effects for state and family-year gives +0.0146 (95% interval 0.0012 to 0.0279) for the leaf-2 LightGBM and −0.0064 (−0.0189 to 0.0061) for SARIMAX (Supplementary Table S35).

![Figure 2. Per-state lead-1 typed minus pooled MASE in the fourteen states of the two registered tests, with 95% intervals over family-years (exploratory summary of registered forecasts). Left: SARIMAX. Right: leaf-2 LightGBM. Positive values favour pooling.](figures/forest.png)

## 6. Why trees ignore typed flags

A regression tree needs at least L training rows on each side of a split, where L is the minimum leaf size, and each of our trees is fitted to one state, so a row is a day. A typed flag is set on one day per festival per year, so in a 730-day training window it is set on two days, or three to four where a state lists a second festival day; the pooled flag is set on every festival day, a median of six to eight days. Once L exceeds the number of days on which a typed flag is set, the tree cannot split on it, and the typed arm must give the same forecasts as the calendar arm.

We tested this with an experiment whose predictions were committed to the repository before it was run. For all fourteen states of both registered tests, lead 1 was re-forecast with every selected parameter kept except the minimum leaf size L, set to 1, 2, 3, 4, 5, 6, 8, 10 or 20. At L = 2 and at each fit's selected L, all 3,042 forecasts per arm equal the registered ones exactly, so the experiment uses the registered pipeline. The prediction that the typed arm equals the calendar arm whenever no typed flag reaches L training days held in every such fit (1,501 of 1,501 in the first test, 1,314 of 1,314 in the second), and the share of fits with identical typed and calendar forecasts rose with L, reaching 1.00 at L = 5 and L = 4. This prediction is close to a property of the algorithm, so it confirms the pipeline rather than discovering anything. Three predictions failed: we expected LightGBM's default bin construction (at least three rows per bin) to make flags set on only two days unusable at any L, but 137 and 147 such fits did use them; we expected the pooled advantage to stay positive up to L = 20, but it vanished once neither flag could be used; and in the second test the pooled flag was unused in about half the fits even at small L. At the registered L = 2, typed flags were unusable in 47% (first test) and 61% (second test) of fits; in the other fits the trees could use them and still did better with the pooled flag, so support explains the tuned LightGBM fully but the leaf-2 result only partly.

Table 4 shows the consequence. Typed minus pooled MASE is positive at every leaf size from 1 to 6, is largest at L = 3 to 6 (+0.018 to +0.027), where typed flags are mostly unusable but the pooled flag is not, and falls to about zero once neither flag can be used (+0.0002 at L = 10 and exactly zero at L = 20 in the first test; exactly zero from L = 8 in the second). The leaf-2 result of the registered tests therefore sits on a curve whose shape is set by how many training days each flag covers. The tuned LightGBM, whose selected L of 5 or 20 makes typed flags invisible, is the extreme case: its "preference" for pooling is a support effect, not a judgement on typed information.

Table 4. Leaf-size experiment (exploratory, predictions committed before the run): lead-1 typed minus pooled MASE and the share of fits in which the typed arm equals the calendar arm.

| Leaf size L | First test: typed − pooled | First test: typed = calendar | Second test: typed − pooled | Second test: typed = calendar |
| --- | --- | --- | --- | --- |
| 1 | +0.0086 | 0.42 | +0.0146 | 0.59 |
| 2 | +0.0068 | 0.47 | +0.0147 | 0.61 |
| 3 | +0.0214 | 0.78 | +0.0215 | 0.99 |
| 4 | +0.0218 | 0.81 | +0.0223 | 1.00 |
| 5 | +0.0269 | 1.00 | +0.0221 | 1.00 |
| 6 | +0.0252 | 1.00 | +0.0178 | 1.00 |
| 8 | +0.0219 | 1.00 | +0.0000 | 1.00 |
| 10 | +0.0002 | 1.00 | +0.0000 | 1.00 |
| 20 | +0.0000 | 1.00 | +0.0000 | 1.00 |

**Training window.** If the pooled advantage of the trees comes from typed flags having too few training days, it should shrink when the training window is longer. A second experiment, also with predictions committed before it was run, refitted the models with windows of two, four and six years for event years 2021–2025 (the calendars start in 2015, so six years is the longest fully covered window). Table 5 and Figure 3 show the result. The leaf-2 LightGBM's pooled advantage shrinks as the window grows in both tests, as predicted: in the first test's states it reverses, from +0.0068 to −0.0027 and −0.0061, so that typed flags do better with four or six years of history; in the second test's states it falls from +0.0162 to +0.0115 and then hardly moves (+0.0108), staying positive. The tuned LightGBM begins to use typed flags: the share of state-years in which its typed and calendar forecasts are identical falls from 1.00 to 0.46 (first test) and from 1.00 to 0.74 (second). Its difference falls in the first test but not monotonically in the second, so that prediction failed there. For Ridge, which can use any flag, the window makes little difference (first test −0.0212 to −0.0215; second −0.0047 to −0.0052); we had predicted that typed flags would gain, and that prediction failed. With more history per flag, the pooled advantage shrank in all four LightGBM settings and reversed in one; these window contrasts have no intervals and rest on five event years. The registered tree result is therefore partly a property of the two-year window.

Table 5. Training-window experiment (exploratory, predictions committed before the run; event years 2021–2025, lead 1): typed minus pooled MASE. Positive favours pooling.

| Model | Test | 2 years | 4 years | 6 years |
| --- | --- | --- | --- | --- |
| Leaf-2 LightGBM | first | +0.0068 | −0.0027 | −0.0061 |
| Leaf-2 LightGBM | second | +0.0162 | +0.0115 | +0.0108 |
| Tuned LightGBM | first | +0.0150 | +0.0136 | +0.0098 |
| Tuned LightGBM | second | +0.0133 | +0.0145 | +0.0030 |
| Rich Ridge | first | −0.0212 | −0.0198 | −0.0215 |
| Rich Ridge | second | −0.0047 | −0.0055 | −0.0052 |

![Figure 3. Typed minus pooled lead-1 MASE for LightGBM. Left: by minimum leaf size, 730-day window, all event years (blue circles: first test; orange squares: second test). Right: by training window, event years 2021–2025, for the leaf-2 (solid) and tuned (dashed) LightGBM, same colours. Both experiments are exploratory, with predictions committed before they were run.](figures/leaf_window.png)

## 7. Other checks

**Both kinds of indicator.** A hybrid arm that passes the typed flags and the pooled flag together, the middle ground that shrinkage-based tools such as Prophet approximate, was as accurate as the better of the two arms in every setting in which it was run: for Ridge and both LightGBMs at lead 1, in both tests and at every training window, its MASE was at most 0.0002 above the better arm, and often below it (for example, leaf-2 LightGBM in the first test, two-year window: typed 0.6064, pooled 0.5996, hybrid 0.5965). Both predictions for this arm held.

**Dating errors.** Because most calendar rows come from secondary sources (Section 3.2), we moved a random 20% of festival dates by one day, with two seeds, and reran Ridge and the leaf-2 LightGBM. For Ridge, the errors moved the difference towards pooling in both tests and both seeds (by +0.0152 and +0.0067 in the first test, +0.0021 and +0.0135 in the second), as predicted; a plausible reason, not tested here, is that a misdated typed flag loses one of its few training days, while the pooled flag keeps the others. For the leaf-2 LightGBM the prediction failed in three of four cases (changes +0.0011, −0.0042, −0.0081, −0.0055), so dating errors do not explain its pooled advantage, although they may bias linear models towards pooling.

**Ridge penalty.** The arms share the penalty selected on ordinary days. Refitting Ridge with penalties from 0.1 to 1,000 for every arm left the first test's typed advantage in place (between −0.0132 and −0.0158 for penalties 0.1 to 100); in the second test every value was within 0.004 of zero, and the predicted constant sign failed only because of a value of +0.0000 at penalty 10. Details of all three checks are in Supplementary Section S10.

**Heterogeneity.** Exploratory analyses after the first test suggested that typing helps Ridge where a state's festival effects differ strongly; a simulation matched to the pipeline, built after that test, reproduced the differences between states mainly through Gujarat and Tamil Nadu (Supplementary Sections S4 and S5). The second registered test did not confirm this out of sample (M1 −0.0081, interval −0.0247 to 0.0085; M2 ρ −0.43). We treat it as an unconfirmed explanation.

**Foundation models at longer leads.** In the first test, TimesFM-3 did better with typed flags at leads 7 and 14 (−0.078 and −0.079), also against a pooled flag without zero padding (−0.060 and −0.064). This was not a registered horizon, rests mainly on Gujarat and Tamil Nadu, and is the subject of the 2027–2028 registration (Table 1).

## 8. What should a forecaster do?

If the better representation cannot be known in advance, choosing it from past performance is unreliable. Using the stored forecasts of both registered tests (four local models, three leads, eight event years with a previous year; 192 decisions), we compare always-typed, always-pooled, following last year's winner, and an equal-weight average of the typed and pooled point forecasts. Regret is MASE minus that of the better representation in hindsight. Mean regret was 0.0069 for always-typed, 0.0050 for always-pooled, 0.0040 for the follow rule and 0.0031 for the average; the largest regret was 0.057, 0.050, 0.057 and 0.023 respectively (Table 6). Following last year's winner has lower mean regret than either fixed choice, but it picked the worse representation in 59 of 192 decisions and has the same worst case as always-typed. The differences are small (0.001 to 0.004 MASE) and the decisions are correlated, so this is a weakly supported suggestion. Where the model can take both, the hybrid arm of Section 7 is a simpler hedge. Because the absolute error of an average is at most the mean of the two absolute errors, the average cannot be worse than the worse representation; its value is in limiting the worst case, not in a new method. The rules were chosen after the instability had been seen, so this analysis is exploratory.

Table 6. Decision rules over 192 decisions in the fourteen states (regret in MASE against the hindsight-better representation; exploratory).

| Rule | Mean regret | Largest regret |
| --- | --- | --- |
| Always typed | 0.0069 | 0.0571 |
| Always pooled | 0.0050 | 0.0498 |
| Follow last year's winner | 0.0040 | 0.0571 |
| Average of typed and pooled | 0.0031 | 0.0229 |

For tree models the practical advice is concrete: count how many training days each flag covers and compare it with the minimum leaf size; a typed flag below that count is a wasted channel, and a pooled flag, or a longer training window, is needed for the tree to use festival information at all.

## 9. Limitations

- All data are historical and public, so the registrations fix the analysis order, not the data; registration times rest on repository commits and, for the second test, on the author's record of the OSF submission (Section 3.5).
- Calendar quality is limited: most rows come from secondary sources, the second test's calendar is corroborated mainly by agreement with other states, and the confirmed LightGBM result is not shown on the best-checked rows alone.
- The effects are small (about 1–2% of MASE, under 0.1% of demand) and spread unevenly over states; the first test's results rest mainly on Gujarat, and the surviving result uses an unusual minimum leaf size.
- Power was low for some tests: R1 had 18–34% power at the first test's effect, so its failure is weak evidence against that effect.
- The parameters are selected on ordinary days and shared by all arms; weather, supply constraints and coincident observances are not modelled; foundation models are used zero-shot and their pretraining data are not known to exclude these series [29].
- The experiments in Sections 6 and 7 were designed after the registered results were known; their predictions were committed before they were run, but they remain exploratory.
- The reuse terms of the electricity compilation are unresolved.

## 10. Conclusion

Typed and pooled festival indicators are a small choice with a small effect in our data, and most of what an exploratory analysis suggested about it did not survive two registered tests on new states. The one result that replicated, that a LightGBM with a small minimum leaf size forecasts better with a pooled flag, has a partly mechanical explanation: a tree cannot use an indicator that is set on fewer training days than its minimum leaf size, and typed festival indicators are set on very few days. With longer training windows that advantage shrank, and in one group of states reversed, and for Ridge and LightGBM passing typed and pooled indicators together was as accurate as the better of the two in every setting we ran. Where the better representation is uncertain, averaging the two forecasts limits the worst case. A registered test on 2027–2028 festivals with official calendars will check two remaining exploratory leads: a Ridge typed advantage in three states labelled from the unconfirmed heterogeneity explanation, and the TimesFM-3 typed advantage at leads 7 and 14.

## Declarations

**Data availability.** Code, protocols, forecasts, failures and audits are at https://github.com/Binay-verma/tsaf_project. The GRID-INDIA/POSOCO compilation curated by Robbie Andrew and the two seven-state extracts from the same source are in the repository; their reuse terms are unresolved. Registrations: https://osf.io/yw7mr (first state-level test), https://osf.io/f9tv4 (second) and https://osf.io/xr25s (2027–2028). Model weights are not redistributed.

**Funding.** __________ [author to confirm].

**Competing interests.** __________ [author to confirm].

**Author contribution.** Binay Verma: __________ [author to complete, CRediT roles].

**Use of generative AI.** __________ [author to complete according to the journal's policy before submission].

## References

[1] Ziel, F. (2018). Modeling public holidays in load forecasting: A German case study. Journal of Modern Power Systems and Clean Energy, 6(2), 191–207. https://doi.org/10.1007/s40565-018-0385-5

[2] Arora, S., & Taylor, J. W. (2018). Rule-based autoregressive moving average models for forecasting load on special days: A case study for France. European Journal of Operational Research, 266(1), 259–268. https://doi.org/10.1016/j.ejor.2017.08.056

[3] Ansari, A. F., Shchur, O., Küken, J., Auer, A., Han, B., et al. (2025). Chronos-2: From univariate to universal forecasting. arXiv:2510.15821 (v1, 17 Oct 2025; 23 authors). https://arxiv.org/abs/2510.15821

[4] Jain, A., & Sen, R. (2026, August 31). TimesFM-3: A zero-shot foundation model for multivariate forecasting. Google Research blog. https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/

[5] Kreusel, A., Beichter, M., Nikoltchovska, A., Schäfer, B., Mikut, R., Zahn, F., & Hagenmeyer, V. (2026). On the encoding of calendar features in covariate-informed time series foundation models. arXiv:2610.13676 (v1, 9 Oct 2026). https://arxiv.org/abs/2610.13676

[6] Alipour, E., Zhang, S., Jin, T., & Moschos, A. (2025). Impact-driven event covariates for time-series foundation models. ICML 2025 Workshop on Foundation Models for Structured Data. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models

[7] Boylan, J. E., Goodwin, P., Mohammadipour, M., & Syntetos, A. A. (2015). Reproducibility in forecasting research. International Journal of Forecasting, 31(1), 79–90. https://doi.org/10.1016/j.ijforecast.2014.05.008

[8] Hong, T., & Fan, S. (2016). Probabilistic electric load forecasting: A tutorial review. International Journal of Forecasting, 32(3), 914–938. https://doi.org/10.1016/j.ijforecast.2015.11.011

[9] Charlton, N., & Singleton, C. (2014). A refined parametric model for short term load forecasting. International Journal of Forecasting, 30(2), 364–368. https://doi.org/10.1016/j.ijforecast.2013.07.003

[10] Ziel, F., & Liu, B. (2016). Lasso estimation for GEFCom2014 probabilistic electric load forecasting. International Journal of Forecasting, 32(3), 1029–1037. https://doi.org/10.1016/j.ijforecast.2016.01.001

[11] Arora, S., & Taylor, J. W. (2013). Short-term forecasting of anomalous load using rule-based triple seasonal methods. IEEE Transactions on Power Systems, 28(3), 3235–3242. https://doi.org/10.1109/TPWRS.2013.2252929

[12] Banerjee, A., & Sarkar, S. (2010). Modeling regional electricity load in India (Working Paper Series No. 656). Indian Institute of Management Calcutta, May 2010. https://ir.iimcal.ac.in:8443/jspui/handle/123456789/384

[13] Fernandes, R. S. S., Bichpuriya, Y. K., Rao, M. S. S., & Soman, S. A. (2011). Day ahead load forecasting models for holidays in Indian context. In 2011 International Conference on Power and Energy Systems (ICPES), pp. 1–5. IEEE. https://doi.org/10.1109/ICPES.2011.6156652

[14] Sanyal, A., Mitra, P., McElroy, T. S., & Roy, A. (2017). Holiday effects in Indian manufacturing series (Research Report Series RRS2017-04). U.S. Census Bureau. https://www.census.gov/library/working-papers/2017/adrm/rrs2017-04.html

[15] Liu, L.-M. (1980). Note - Analysis of time series with calendar effects. Management Science, 26(1), 106–112. https://doi.org/10.1287/mnsc.26.1.106

[16] Bell, W. R., & Hillmer, S. C. (1983). Modeling time series with calendar variation. Journal of the American Statistical Association, 78(383), 526–534. https://doi.org/10.1080/01621459.1983.10478005

[17] Findley, D. F., Monsell, B. C., Bell, W. R., Otto, M. C., & Chen, B.-C. (1998). New capabilities and methods of the X-12-ARIMA seasonal-adjustment program. Journal of Business & Economic Statistics, 16(2), 127–152. https://doi.org/10.1080/07350015.1998.10524743

[18] Lin, J.-L., & Liu, T.-S. (2003). Modeling lunar calendar effects in Taiwan. Econometrics 0306005, EconWPA, University Library of Munich. (Earlier version: Modeling lunar calendar holiday effects in Taiwan, U.S. Census Bureau working paper, July 2002.) https://ideas.repec.org/p/wpa/wuwpem/0306005.html

[19] Roberts, I., & White, G. (2015). Seasonal adjustment of Chinese economic statistics (Research Discussion Paper RDP 2015-13), Section 2: Seasonal adjustment with Chinese moving holiday effects. Reserve Bank of Australia. https://www.rba.gov.au/publications/rdp/2015/2015-13/seasonal-adjustment-with-chinese-moving-holiday-effects.html

[20] Taylor, S. J., & Letham, B. (2018). Forecasting at scale. The American Statistician, 72(1), 37–45. https://doi.org/10.1080/00031305.2017.1380080

[21] Probst, P., Wright, M. N., & Boulesteix, A.-L. (2019). Hyperparameters and tuning strategies for random forest. WIREs Data Mining and Knowledge Discovery, 9(3), e1301. https://doi.org/10.1002/widm.1301

[22] LightGBM developers. LightGBM documentation: Parameters; Parameters Tuning (min_data_in_leaf, alias min_child_samples; categorical parameters). https://lightgbm.readthedocs.io/en/latest/ (accessed 15 Nov 2026). https://lightgbm.readthedocs.io/en/latest/Parameters.html

[23] Das, A., Kong, W., Sen, R., & Zhou, Y. (2024). A decoder-only foundation model for time-series forecasting. In Proceedings of the 41st International Conference on Machine Learning (ICML 2024), PMLR 235, 10148–10167. https://proceedings.mlr.press/v235/das24c.html

[24] Ansari, A. F., Stella, L., Turkmen, A. C., Zhang, X., Mercado, P., Shen, H., Shchur, O., Rangapuram, S. S., Pineda Arango, S., Kapoor, S., Zschiegner, J., Maddix, D. C., Wang, H., Mahoney, M. W., Torkkola, K., Wilson, A. G., Bohlke-Schneider, M., & Wang, B. (2024). Chronos: Learning the language of time series. Transactions on Machine Learning Research. arXiv:2403.07815. https://openreview.net/forum?id=gerNCVqqtR

[25] Woo, G., Liu, C., Kumar, A., Xiong, C., Savarese, S., & Sahoo, D. (2024). Unified training of universal time series forecasting transformers. In Proceedings of the 41st International Conference on Machine Learning (ICML 2024), PMLR 235, 53140–53164. https://proceedings.mlr.press/v235/woo24a.html

[26] Ekambaram, V., Jati, A., Dayama, P., Mukherjee, S., Nguyen, N. H., Gifford, W. M., Reddy, C., & Kalagnanam, J. (2024). Tiny Time Mixers (TTMs): Fast pre-trained models for enhanced zero/few-shot forecasting of multivariate time series. arXiv:2401.03955 (v8); accepted at NeurIPS 2024. https://arxiv.org/abs/2401.03955

[27] Pineda Arango, S., Mercado, P., Kapoor, S., Ansari, A. F., Stella, L., Shen, H., Senetaire, H., Turkmen, C., Shchur, O., Maddix, D. C., Bohlke-Schneider, M., Wang, Y., & Rangapuram, S. S. (2025). ChronosX: Adapting pretrained time series models with exogenous variables. arXiv:2503.12107 (v1). https://arxiv.org/abs/2503.12107

[28] Kaljevic, T., Arzola, I., & Zhang, Y. (2026). Benchmarking time series foundation models for load forecasting under covariate uncertainty. arXiv:2610.07232 (v1, 5 Oct 2026). https://arxiv.org/abs/2610.07232

[29] Meyer, M., Kaltenpoth, S., Zalipski, K., & Müller, O. (2025). Rethinking evaluation in the era of time series foundation models: (Un)known information leakage challenges. arXiv:2510.13654 (v3, 25 Feb 2026). https://arxiv.org/abs/2510.13654

[30] Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. International Journal of Forecasting, 22(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001

[31] Franses, P. H. (2016). A note on the Mean Absolute Scaled Error. International Journal of Forecasting, 32(1), 20–22. https://doi.org/10.1016/j.ijforecast.2015.03.008

[32] Canay, I. A., Romano, J. P., & Shaikh, A. M. (2017). Randomization tests under an approximate symmetry assumption. Econometrica, 85(3), 1013–1030. https://doi.org/10.3982/ECTA13081

[33] Hemerik, J., Goeman, J. J., & Finos, L. (2020). Robust testing in generalized linear models by sign flipping score contributions. Journal of the Royal Statistical Society: Series B, 82(3), 841–864. https://doi.org/10.1111/rssb.12369

[34] Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business & Economic Statistics, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599

[35] Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65–70.

[36] Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. Proceedings of the National Academy of Sciences, 115(11), 2600–2606. https://doi.org/10.1073/pnas.1708274114

[37] Bates, J. M., & Granger, C. W. J. (1969). The combination of forecasts. Operational Research Quarterly, 20(4), 451–468. https://doi.org/10.1057/jors.1969.103

[38] Claeskens, G., Magnus, J. R., Vasnev, A. L., & Wang, W. (2016). The forecast combination puzzle: A simple theoretical explanation. International Journal of Forecasting, 32(3), 754–762. https://doi.org/10.1016/j.ijforecast.2015.12.005

[39] Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems, 30, 3146–3154.
