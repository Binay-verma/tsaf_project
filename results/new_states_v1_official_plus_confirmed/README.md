# Is the official-sources sensitivity about calendar quality or about which states remain? (EXPLORATORY)

Run after the registered analysis, with the registered `evaluate` function. The registered decisions are unchanged.

## Results
**Official plus provisionally confirmed rows** (`tests.csv`, `cells_kept.csv`): calendar rows whose date the 2026-11-15 search read from a copy of the government order (status `match`) are added to the officially sourced rows.
- This keeps 119 cells: AP 35, Telangana 43, Tamil Nadu 36, Rajasthan 3, MP 2.
- H1: NOT CONFIRMED (−0.0023, p 0.31).
- H2: CONTRADICTED (−0.0175, opposite p 0.019).
- H3: NOT CONFIRMED (−0.0036).

So adding back provisionally confirmed rows does not change the official-only picture.

**Same states, all rows regardless of source** (`by_state_group_all_rows.csv`):

| State group | H1 SARIMAX typed | H2 TimesFM-3 pooled | H3 leaf-2 LightGBM pooled |
|---|---|---|---|
| AP + Telangana + Tamil Nadu (123 cells) | +0.0040, not confirmed | −0.0137, **contradicted** (p_opp 0.027) | −0.0013, not confirmed |
| UP + Rajasthan + MP + Gujarat (117 cells, 36 clusters) | −0.0235, **confirmed** (Holm 0.004, 8/9 years) | +0.0065, not confirmed | +0.0107, p 0.040, Holm 0.080 |

## Reading
The three southern states give the same pattern with all their rows as with official rows only. The official-only sensitivity therefore mainly reflects which states it keeps, not calendar quality. The registered H1 and H3 results come from the northern and western states. In the southern states typed flags help TimesFM-3 at lead 1 and do not help SARIMAX. The family mix also differs: the southern states have four to five in-scope families including Ganesh Chaturthi and Ugadi; the northern and western states have three (Holi, Dussehra, Diwali), or four for MP.

This regional difference was found after the registered test and is not explained here. It is a limitation of the confirmed results.
