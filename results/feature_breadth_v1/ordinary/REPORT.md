# Matched feature breadth — ordinary

Exploratory extension registered before new breadth outputs, after historical anchor/pooled results were examined. No untouched or external preregistration claim.

10,368 forecasts; 216 identical cases per model/arm; all six variants/eight arms. Individual lead errors, not week-average forecasts. Lower MASE is better.

Event summaries weight states within year, years within family, then families equally. Ordinary summaries weight states and years equally; monthly dates form a bounded calendar-selected sample. No row-independent significance or generalisation from two years.

## Lead 1

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.28458 | 0.28458 | 0.27908 | 0.2836 | 0.28892 | 0.2871 | 0.28596 | 0.29129 |
| lightgbm | 0.39366 | 0.39366 | 0.39545 | 0.38932 | 0.39507 | 0.39562 | 0.39366 | 0.39371 |
| lightgbm_capacity2 | 0.39178 | 0.39178 | 0.37852 | 0.36525 | 0.38882 | 0.37955 | 0.39113 | 0.3899 |
| sarimax | 0.23073 | 0.23076 | 0.22949 | 0.2291 | 0.22995 | 0.23155 | 0.22933 | 0.23395 |
| chronos | 0.24924 | 0.2587 | 0.26477 | 0.26567 | 0.26117 | 0.26297 | 0.25853 | 0.25926 |
| timesfm | 0.26547 | 0.25598 | 0.26928 | 0.26696 | 0.26214 | 0.25902 | 0.26205 | 0.26311 |

## Lead 7

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.88539 | 0.88539 | 0.87908 | 0.87935 | 0.88709 | 0.87975 | 0.88291 | 0.89212 |
| lightgbm | 1.05804 | 1.05804 | 1.05657 | 1.03976 | 1.056 | 1.03557 | 1.05797 | 1.05663 |
| lightgbm_capacity2 | 1.03915 | 1.03915 | 1.03922 | 1.05298 | 1.04884 | 1.03931 | 1.04478 | 1.03745 |
| sarimax | 0.96617 | 0.96617 | 0.94968 | 0.94136 | 0.96056 | 0.96662 | 0.967 | 0.95932 |
| chronos | 0.89539 | 0.90447 | 0.91123 | 0.90402 | 0.91262 | 0.8989 | 0.90268 | 0.91257 |
| timesfm | 0.88821 | 0.87606 | 0.8855 | 0.87905 | 0.87563 | 0.87343 | 0.88339 | 0.88382 |

## Lead 14

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.07574 | 1.07574 | 1.07403 | 1.07638 | 1.06283 | 1.07372 | 1.07416 | 1.09668 |
| lightgbm | 1.22473 | 1.22473 | 1.22473 | 1.22476 | 1.2233 | 1.22783 | 1.22473 | 1.23892 |
| lightgbm_capacity2 | 1.24331 | 1.24331 | 1.23858 | 1.25542 | 1.23264 | 1.22226 | 1.24659 | 1.23358 |
| sarimax | 1.12965 | 1.1305 | 1.10474 | 1.11681 | 1.13213 | 1.13066 | 1.1311 | 1.12599 |
| chronos | 0.98343 | 1.00775 | 1.01861 | 1.01507 | 1.02232 | 1.01445 | 1.0063 | 1.0121 |
| timesfm | 0.91187 | 0.91862 | 0.91434 | 0.92471 | 0.92019 | 0.92098 | 0.91701 | 0.91142 |

## Native uncertainty

| model | arm | horizon | scaled_mean_pinball | coverage80 | scaled_width80 | scaled_WIS80_median |
| --- | --- | --- | --- | --- | --- | --- |
| chronos | calendar | 1 | 0.10736 | 0.97222 | 1.3928 | 0.17972 |
| chronos | calendar | 7 | 0.34192 | 0.84722 | 2.7197 | 0.55541 |
| chronos | calendar | 14 | 0.3748 | 0.81944 | 3.1796 | 0.60724 |
| chronos | day5 | 1 | 0.10967 | 0.97222 | 1.36864 | 0.18171 |
| chronos | day5 | 7 | 0.35006 | 0.84722 | 2.85271 | 0.56966 |
| chronos | day5 | 14 | 0.39104 | 0.83333 | 3.46319 | 0.62531 |
| chronos | placebo_day5 | 1 | 0.10939 | 0.97222 | 1.3849 | 0.18082 |
| chronos | placebo_day5 | 7 | 0.34759 | 0.84722 | 2.842 | 0.56421 |
| chronos | placebo_day5 | 14 | 0.38505 | 0.84722 | 3.43492 | 0.6178 |
| chronos | placebo_window5 | 1 | 0.1094 | 0.93056 | 1.37134 | 0.18063 |
| chronos | placebo_window5 | 7 | 0.34832 | 0.84722 | 2.84212 | 0.56448 |
| chronos | placebo_window5 | 14 | 0.38794 | 0.84722 | 3.42461 | 0.61984 |
| chronos | pooled_day5 | 1 | 0.10997 | 0.97222 | 1.37712 | 0.18312 |
| chronos | pooled_day5 | 7 | 0.3479 | 0.84722 | 2.85452 | 0.56677 |
| chronos | pooled_day5 | 14 | 0.38805 | 0.83333 | 3.42341 | 0.62251 |
| chronos | pooled_window5 | 1 | 0.10975 | 0.94444 | 1.3738 | 0.18213 |
| chronos | pooled_window5 | 7 | 0.34722 | 0.84722 | 2.86242 | 0.56505 |
| chronos | pooled_window5 | 14 | 0.38673 | 0.84722 | 3.44696 | 0.62128 |
| chronos | window5 | 1 | 0.10937 | 0.95833 | 1.36433 | 0.18085 |
| chronos | window5 | 7 | 0.34944 | 0.84722 | 2.84146 | 0.56978 |
| chronos | window5 | 14 | 0.39012 | 0.84722 | 3.44661 | 0.62663 |
| chronos | zero5 | 1 | 0.10946 | 0.97222 | 1.40165 | 0.1824 |
| chronos | zero5 | 7 | 0.3473 | 0.86111 | 2.844 | 0.56562 |
| chronos | zero5 | 14 | 0.38519 | 0.83333 | 3.39192 | 0.61733 |
| timesfm | calendar | 1 | 0.10525 | 0.91667 | 1.06524 | 0.17078 |
| timesfm | calendar | 7 | 0.33763 | 0.80556 | 2.62214 | 0.54545 |
| timesfm | calendar | 14 | 0.35341 | 0.86111 | 3.29402 | 0.58063 |
| timesfm | day5 | 1 | 0.10552 | 0.875 | 1.01981 | 0.17169 |
| timesfm | day5 | 7 | 0.3386 | 0.80556 | 2.56839 | 0.54702 |
| timesfm | day5 | 14 | 0.35564 | 0.84722 | 3.27052 | 0.58213 |
| timesfm | placebo_day5 | 1 | 0.10327 | 0.88889 | 1.05001 | 0.1684 |
| timesfm | placebo_day5 | 7 | 0.33771 | 0.79167 | 2.58434 | 0.5461 |
| timesfm | placebo_day5 | 14 | 0.35624 | 0.86111 | 3.26324 | 0.58539 |
| timesfm | placebo_window5 | 1 | 0.10328 | 0.90278 | 1.04849 | 0.16789 |
| timesfm | placebo_window5 | 7 | 0.33681 | 0.79167 | 2.59693 | 0.54602 |
| timesfm | placebo_window5 | 14 | 0.3539 | 0.86111 | 3.26901 | 0.58399 |
| timesfm | pooled_day5 | 1 | 0.10365 | 0.875 | 1.00997 | 0.16808 |
| timesfm | pooled_day5 | 7 | 0.33773 | 0.77778 | 2.5268 | 0.5458 |
| timesfm | pooled_day5 | 14 | 0.36096 | 0.84722 | 3.23197 | 0.58971 |
| timesfm | pooled_window5 | 1 | 0.10215 | 0.88889 | 1.04033 | 0.16567 |
| timesfm | pooled_window5 | 7 | 0.33579 | 0.77778 | 2.56036 | 0.54125 |
| timesfm | pooled_window5 | 14 | 0.35925 | 0.84722 | 3.24631 | 0.58995 |
| timesfm | window5 | 1 | 0.10348 | 0.88889 | 1.04731 | 0.16844 |
| timesfm | window5 | 7 | 0.33534 | 0.80556 | 2.59312 | 0.54306 |
| timesfm | window5 | 14 | 0.35766 | 0.84722 | 3.26363 | 0.58978 |
| timesfm | zero5 | 1 | 0.10134 | 0.90278 | 1.04725 | 0.16426 |
| timesfm | zero5 | 7 | 0.33577 | 0.77778 | 2.5638 | 0.5411 |
| timesfm | zero5 | 14 | 0.35907 | 0.84722 | 3.25674 | 0.58724 |

Native intervals are uncalibrated and unchanged. Coverage accompanies width/pinball and one-interval WIS; WIS=(0.5*median absolute error+0.1*80%interval score)/1.5. No marginal sorting or clipping. Invalid intervals propagate undefined scores.

Paired contrasts, both years, each family and leave-family-out sensitivity are retained. Historical/proxy overlap, publication lag/revisions, complete amendments, source rights and human review remain unresolved. Ordinary-day and event scores describe different cohorts. No causal mechanism, universal winner, untouched test or new independent events are inferred.
