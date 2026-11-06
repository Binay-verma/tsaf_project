# Label correction — recorded before any metric of the new arm was computed

Recorded 6 November 2026 (UTC). The registered protocol files are unchanged.

**What was wrong.** The protocol calls the new arm `sunday_day` Ziel's (2018) "replacing" variant. Reading Section 4 of the paper (Ziel 2018, J. Mod. Power Syst. Clean Energy 6(2), 191–207, doi:10.1007/s40565-018-0385-5) shows two different designs:

- Section 4.3, "holiday as weekday dummy" (**hSun**, hSat): the holiday "is treated as a Sunday"; no holiday dummy is added.
- Section 4.5, "replacing" (**Rph** with one dummy for all holidays, **RpH** with one dummy per holiday): holiday dummies are added as in the additional approach, and "the corresponding week-day effect is set to zero if there is a holiday" (Eq. 11).

**What the arm actually is.** `sunday_day` is computed exactly as its registered `new_arm_definition` states (weekday one-hot replaced by the Sunday one-hot on anchor days, no festival indicator). That is Ziel's **hSun** design adapted to daily festival anchors, not the replacing design. The error came from the earlier closest-method map, which merged the two.

**Timing.** At the time of this note the Ridge, LightGBM and SARIMAX event-window forecasts and some ordinary forecasts had been produced. Only the reference arms of Ridge were compared with the stored forecasts (to check reproduction). No MASE or other metric of `sunday_day` had been computed or viewed.

**Consequence.** Results of this study are reported as Ziel's hSun variant. The replacing variants Rph and RpH are registered separately in `results/ziel_replacing_v2/` before any of their forecasts exist. No arm, case or rule of this study is changed.
