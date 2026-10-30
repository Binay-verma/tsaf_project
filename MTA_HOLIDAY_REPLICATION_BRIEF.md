# Independent NYC holiday replication: audited local checkpoint

Updated 31 October 2026 India time. This is a completed local-model checkpoint, not the full foundation-model comparison.

The protocol was published in commit `e7d9423a073569bec93a96730a09c321756d1042` before acquiring the new evaluation records. The fixed query returned 2,780 source records, yielding 1,390 complete daily observations per series from 1 January 2023 to 21 October 2026. Subway and Bus are two related NYC modes from one primary MTA source, not two independent cities. Counts are reported estimated rides, expressed in million rides; they are not electricity or unique travellers.

The 84 event cases cover the complete ±3-day windows of Yom Kippur (21 September 2026) and Columbus Day (12 October 2026), both modes, and three decision leads. The 42 ordinary cases balance weekdays and exclude the registered September–October parking-observance windows. NYC DOT parking calendars supply named observance dates, not evidence of transit closure. All three selected annual PDFs have pre-year archive captures with matching archive digests. The provider's attached Overview states “There are no limitations on the data at this time”; retain attribution and do not invent a standard licence or infer permission for Indian source data.

The fixed seven-day observation buffer means decision leads 1/7/14 correspond to actual model steps 8/14/21. No unobserved bridge labels enter model inputs. This is a conservative availability sensitivity using current revised estimates, not reconstructed first-vintage or prospective forecasting.

All eight local workers are complete: 4,032 forecasts from four local variants and eight arms, plus 252 common naive forecasts. The separate audit passes raw-count conversion, primary calendar dates/digests, seeded weekday-placebo construction, case/scale reconstruction, 624 fit/query byte checks, label purging, parameters, all point metrics and paired composition tables. It independently reruns all 72 past-only validation fits with separately constructed matrices and the same numerical model libraries; maximum validation-MAE difference is zero. This is an internal software audit, not independent human review. The source has no missing values, so actual missing-label imputation is not exercised.

At decision lead 1 (actual model step 8), event-window MASE is:

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ridge | 0.99718 | 1.00451 | 1.16887 | 1.19074 | 1.31328 |
| SARIMAX | 0.99947 | 0.79417 | 1.04067 | 1.15250 | 1.40939 |
| Stable LightGBM | 0.91940 | 0.91940 | 0.91940 | 0.91940 | 1.08484 |
| Leaf-minimum-2 LightGBM | 0.84819 | 0.84610 | 0.87819 | 0.88083 | 1.02851 |

For the same decision lead, ordinary-day MASE is:

| Model | Calendar | Typed day | Pooled day | Typed window | Pooled window |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ridge | 0.93022 | 0.82514 | 0.74570 | 0.82214 | 0.69602 |
| SARIMAX | 0.69848 | 0.57159 | 0.53110 | 0.61851 | 0.54580 |
| Stable LightGBM | 0.83653 | 0.83653 | 0.83653 | 0.83653 | 0.75887 |
| Leaf-minimum-2 LightGBM | 0.76625 | 0.75037 | 0.71580 | 0.72767 | 0.71070 |

Lower MASE is better; this is not percentage accuracy. SARIMAX's typed-day representation improves the event average while pooled-day worsens it, although pooling helps the ordinary sample. These mixed results oppose universal pooling claims. All eight arms, all leads, both families, series-level results and leave-family-out tables are retained in `results/mta_holiday_v1/local_checkpoint`; these displayed cells do not select a deployed winner.

Chronos and TimesFM remain queued behind the already registered correction/recentering runs. The full registered study comprises 6,300 model forecasts plus 252 naive forecasts. Its completion manager waits for all 12 workers, then runs the frozen finalizer and separate audit. Do not restart completed local workers, describe queued outputs as results, or treat two event occurrences as sufficient generalisation for journal acceptance.
