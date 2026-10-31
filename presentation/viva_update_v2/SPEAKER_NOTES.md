# Speaker notes — viva deck v2 (Binay Verma)

About 10 minutes, 12 slides (~50 s each). Numbers come from manuscript v6 and the audited re-analysis.


## Slide 1: Do festival features help electricity forecasting, and is the answer stable?

This is an empirical study, not a new model. I compare ways of giving festival information to two pretrained forecasting models (Chronos-2 and TimesFM-3) and four local models, on daily electricity supplied in three Indian states. The main finding is that festival information helps at short leads, but which way of encoding it works best is not stable.


## Slide 2: Why study this?

Typed means five separate flags, one per festival. Pooled means one flag that is on for any of them, padded with four zeros so both use five input channels. The question is which works better, and whether the answer holds across years and data sources.


## Slide 3: Data and evaluation rules

Each case is a target day within ±3 days of a festival. Lead 1 means forecasting the next day; lead 7 and 14 are single target days further ahead. Nearby days, states and leads share the same festival, weather and source, so I count festival-year clusters as the real units. NYC (subway and bus ridership around Yom Kippur and Columbus Day 2026) is a separate source registered before its data were downloaded.


## Slide 4: Six models, eight matched input designs

All models see the same cases. Zero channels check whether merely adding inputs changes forecasts. Placebos put the festival flags on wrong dates, shifted by whole weeks, to check that gains come from the real dates. Local and foundation models adapt differently, so rankings are not a pure architecture comparison.


## Slide 5: Finding 1: festival flags help at lead 1

Compared with calendar-only inputs, both typed and pooled day flags lower the error for most models at lead 1. But the two best results use different encodings: TimesFM prefers pooled, SARIMAX prefers typed. That already hints that there is no single best encoding.


## Slide 6: Finding 2: the best encoding is not stable

A cell is one model, one representation (day or window) and one lead: 6 × 2 × 3 = 36. These counts are descriptive. I registered this analysis before computing it, but it uses results I had already seen. I first reported 20 and 14 here; that counted exact ties as disagreements, so I corrected it to 19 and 11.


## Slide 7: Year by year: few orderings persist

Above zero means pooled was better that year; below zero means typed was better. Several models switch sides between 2024 and 2025. SARIMAX consistently prefers typed flags, and TimesFM prefers pooled in India, but in NYC TimesFM prefers typed. These persistent patterns are expectations for future testing, not proven effects.


## Slide 8: Checks that changed the evidence

Checking which festival the notice actually names is stronger than checking that a date is a holiday. Native uncertainty intervals are too narrow around festivals. All failures and corrections are kept in the repository so they can be checked.


## Slide 9: Closest prior work and what is new

The typed-versus-pooled question itself is old in load forecasting. What I add is testing it in foundation-model covariate channels with matched controls, and showing that the answer is unstable. Whether this is enough for a journal is for my supervisor and reviewers to judge.


## Slide 10: Confirmation on genuinely future data

Historical results were already seen, so real confirmation must come from forecasts made before outcomes exist. The first frozen episode is one period; it cannot confirm the typed-versus-pooled pattern on its own. The weekly study needs verified 2026 calendars and a data-rights reply before it can start; missed weeks are recorded, not filled in later.


## Slide 11: What I can claim, and the limits

I avoid claiming a universal winner, a causal effect or journal readiness. All code, protocols, forecasts and failures are public on GitHub, except model weights.


## Slide 12: Sources and questions

Thank the data curators and model developers. End with questions.
