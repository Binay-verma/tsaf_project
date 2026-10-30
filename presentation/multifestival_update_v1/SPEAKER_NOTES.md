# Multi-festival results supplement — Binay Verma

1 November 2026 · Research in progress

## Slide 1: Do rankings hold beyond Diwali?

This supplement extends the earlier Diwali study. It evaluates forecast errors around five documented festival groups. It does not establish a new architecture, causal effect or benefit from adding new festival identities.

## Slide 2: Expanded comparison, fixed evaluation cases

There are24festival/state/year groups, not528independent replications. Diwali preserves the earlier broad union; other groups use fixed plus/minus3day anchor windows. Fifteen configurations have different adaptation and feature budgets, so this is a deployment-policy comparison. SARIMAX and ETS use fixed specifications; learned Ridge/tree settings retain their original pre-year selection. Date evidence is annual-as-issued.

## Slide 3: Lead 1: all configurations

Lower MASE is better; these are not percentages. Each festival uses equal states within year and equal years. Different families have different documented state coverage. Every configuration is shown, including poor results. Colors use the same scale across leads. A lead is an individual future day, not an average over that many days. Do not infer statistical superiority from the lowest cell.

## Slide 4: Lead 7: all configurations

Lower MASE is better; these are not percentages. Each festival uses equal states within year and equal years. Different families have different documented state coverage. Every configuration is shown, including poor results. Colors use the same scale across leads. A lead is an individual future day, not an average over that many days. Do not infer statistical superiority from the lowest cell.

## Slide 5: Lead 14: all configurations

Lower MASE is better; these are not percentages. Each festival uses equal states within year and equal years. Different families have different documented state coverage. Every configuration is shown, including poor results. Colors use the same scale across leads. A lead is an individual future day, not an average over that many days. Do not infer statistical superiority from the lowest cell.

## Slide 6: Inspect forecasts, not just rankings

These illustrations were selected by dates and states before plotting, not because they are the most favorable errors: Delhi Holi2024 and Maharashtra Ganesh2025. Each point is a separately issued next-day prediction using earlier observations; it is not a single seven-day forecast path. The five plotted configurations are fixed for readability; all fifteen are retained in the tables.

## Slide 7: What the extension supports

This is an exploratory diagnostic result. We have extended case coverage, not proved the incremental value of adding every festival feature. Calendar arms here contain weekdays and annual Fourier harmonics. Foundation-model historical/proxy overlap remains unresolved; matching cases controls a specific comparison, not every source of bias.

## Slide 8: Next experiment and remaining limits

Dussehra2025 coincides with Gandhi Jayanti and Spring2025 is adjacent to Eid. Annual office schedules do not establish actual statewide shutdown or all later amendments. Cite Robbie Andrew/GRID-INDIA/POSOCO, the earlier Hunt/Bloomfield source, model developers and close calendar-encoding prior work. Sources and full scores are in multifestival_models_v1 and MULTIFESTIVAL_REPRODUCTION.md. The original college deck and frozen predictions remain unchanged. This supplement is local pending sharing clarification.

