# Closest-method map (Priority 4) — 31 October 2026

What each nearest method does, which existing arm comes closest, and what is genuinely missing. No new experiment was run for this map.

| Nearest method | What it does | Closest existing arm(s) | Fidelity | Missing / not reproducible |
| --- | --- | --- | --- | --- |
| Ziel (2018), additive single holiday dummy ("Adh") | One extra dummy for all public holidays, added to weekday effects, in hourly German load models | `pooled_day5` in Ridge/SARIMAX/trees: one binary on any family anchor (plus four zero channels), added to 13 calendar channels | Same additive pooled-dummy idea. It differs in daily vs hourly resolution, festivals vs all public holidays, Ridge/SARIMAX/trees vs Ziel's models, and the four padding zeros | — |
| Ziel (2018), separate dummy per holiday ("AdH") | One dummy per holiday | `day5`: one binary per family | Same idea at family level | — |
| Ziel (2018), replacing / holiday-as-Sunday | The weekday effect on a holiday is replaced by the Sunday effect (no additive double-counting) | None | — | **Not implemented.** Feasible for local models as a new registered arm; it would be exploratory on inspected data |
| Kreusel et al. (2026), calendar encodings in TSFMs | Ordinal, one-hot, cyclic and target encodings of calendar covariates, hourly datasets | Ten pure daily encodings (`calendar_encoding_v1`, recentered) | Daily adaptation; the hour feature is omitted; channel counts differ | Exact hourly replication not attempted. Its abstract describes no typed-vs-pooled test |
| Alipour et al., impact-driven event embeddings | Learned 16-d contrastive embeddings from account-level residual responses, supplied to Chronos-2 | Fixed triangular response-profile comparators (Table A2) | Simpler, different method | No runnable code was identified; settings are incomplete; no account-level panel exists. **Not reproducible here** |
| Sanyal et al. (2017), Indian moving-holiday regressors | Window regressors for Navaratri/Diwali in X-13 style models | `window5` / `pooled_window5` in SARIMAX | Close in spirit | Exact X-13 regARIMA not run |
| Arora & Taylor (2018), rule-based seasonal ARMA for special days | Hour-by-hour special-day indicators with judgemental rules | SARIMAX with day flags | Loose | Rule-based judgemental adjustments not reproduced |

Honest summary: Ziel's two additive dummy designs are already represented in the local-model arms, so the typed-vs-pooled question for classical regressions is not new. The study's addition is the same comparison through TSFM covariate channels with zero and placebo controls. The one practical classical gap is Ziel's replacing variant.
