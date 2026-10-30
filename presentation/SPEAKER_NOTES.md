# Speaker notes — Binay Verma

Presentation date: **1 November 2026**. Suggested duration: 10–12 minutes.

Use as ongoing academic research. No prospective accuracy claim is available yet.


## Slide 1: Do regional calendars help electricity forecasting?

Introduce the project as an empirical study. We use existing pretrained models and train local baselines; we do not claim a new foundation-model architecture. The presentation covers completed historical experiments, controls and data-quality findings. Prospective outcomes are still pending.


## Slide 2: Why study this?

The question is whether regional date information adds predictive value after controlling the representation and feature count. Do not equate an office holiday with a proven statewide electricity response. Weather, economic activity and supply constraints can also affect the target; this is predictive analysis, not causal estimation.


## Slide 3: Data and evaluation rules

Explain origin as the first unseen date: lead h targets origin+h−1. Lead 7 is one target day, not a weekly average. We fill only historical inputs causally and do not score locally imputed labels. Retrospective revisions and unknown publication times mean date-order checks alone do not establish a fully operational real-time experiment. Cite Robbie Andrew and GRID-INDIA/POSOCO, with reuse clarification pending.


## Slide 4: Models and comparison design

Local hyperparameters use a pre-year temporal validation block and stay fixed for both deployment schedules during that year. The foundation models run pretrained inference; they are not trained from scratch here. Adaptation policies differ, so the benchmark is not an architecture-only experiment. Leave-region-out regression allows target-region historical context and normalization; it is not cold start.


## Slide 5: Finding 1: refitting matters

Use the chart to explain why a weak baseline is insufficient. With richer histories, monthly Ridge and LightGBM improve over their annual versions on several aggregate errors. Chronos remains lower on the displayed aggregate comparisons. Some event-year results become worse with monthly updates, so there is no universal winning refit schedule. Do not claim statistical superiority from these aggregate lines.


## Slide 6: Controls before making a calendar claim

The primary controlled event study covers 2024–2025. Two event-year clusters are not hundreds of independent experiments, even though we produce many forecasts. A single seeded placebo is not a randomization distribution. Scalar versus seven channels changes relative-day information as well as dimensionality; within-dimension generic/regional contrasts are more specific.


## Slide 7: Finding 2: representation changes the answer

For equal seven-channel inputs, regional mean state/year MAE improvements are about 1.4–1.6 percent for Chronos and 3.3–6.4 percent for TimesFM across leads. Scalar-window increments are smaller or mixed. These are exploratory effects, not universal or causal evidence. Adding seven zeros also changes forecasts by up to about 6–7 GWh, so interface/channel-count controls matter.


## Slide 8: Quality checks found issues worth reporting

These findings are part of the contribution, not defects to hide. Archive payload digests were verified. The selected festival labels agree across the checked later vintages, but some historical input values were revised. The availability experiment has only two dates. Original numerical failures and all old results remain preserved; the new stable tree run does not replace the frozen prospective forecasts.


## Slide 9: Prospective validation: frozen before outcomes

Forecasts were issued on 30 October using data through 28 October. Only 31 October–11 November targets qualify as future; 29/30 October are excluded. The GitHub workflow is registered and its pre-period dry run passed, but no actual future score exists yet. It checks time, source completeness and the original forecast Git blob before scoring. Do not report prospective accuracy on 1 November.


## Slide 10: What the study supports today

Present the completed work confidently but precisely. We found conditional calendar effects and failure modes, not a universally superior festival model. Three related states and two primary historical event years limit generalisation. Historic pretraining/proxy overlap remains unresolved. Data reuse clarification and independent human/calendar review are still pending.


## Slide 11: What happens next?

It is appropriate to discuss the project as work in progress in college. Use source acknowledgments and your own aggregate charts. Do not distribute raw datasets or model weights before clarifying terms. The author’s reply may take time. College feedback can inform improvements, but it is not automatically independent scientific sign-off or publication acceptance.


## Slide 12: Sources and questions

Acknowledge the data curator, upstream organisation, model developers and close prior work. This is not a first-ever calendar-encoding claim. For follow-up, refer to the working manuscript, protocols and controlled-result reports. Avoid claiming a data licence or external review has already been granted. End with questions.
