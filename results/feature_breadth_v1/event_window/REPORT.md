# Matched feature breadth — event_window

Exploratory extension registered before new breadth outputs, after historical anchor/pooled results were examined. No untouched or external preregistration claim.

25,344 forecasts; 528 identical cases per model/arm; all six variants/eight arms. Individual lead errors, not week-average forecasts. Lower MASE is better.

Event summaries weight states within year, years within family, then families equally. Ordinary summaries weight states and years equally; monthly dates form a bounded calendar-selected sample. No row-independent significance or generalisation from two years.

## Lead 1

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.57813 | 0.57813 | 0.45554 | 0.46207 | 0.58003 | 0.60952 | 0.57927 | 0.5782 |
| lightgbm | 0.70086 | 0.70086 | 0.69704 | 0.66331 | 0.70389 | 0.71454 | 0.70086 | 0.7003 |
| lightgbm_capacity2 | 0.6883 | 0.6883 | 0.65121 | 0.60662 | 0.6927 | 0.70249 | 0.68922 | 0.69309 |
| sarimax | 0.57478 | 0.57483 | 0.41872 | 0.45079 | 0.57953 | 0.57689 | 0.57492 | 0.5748 |
| chronos | 0.53897 | 0.53432 | 0.52074 | 0.51821 | 0.53678 | 0.53291 | 0.5378 | 0.54026 |
| timesfm | 0.55002 | 0.54722 | 0.47891 | 0.42256 | 0.55369 | 0.54953 | 0.55063 | 0.55042 |

## Lead 7

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0.98672 | 0.98672 | 0.92343 | 0.92903 | 1.05177 | 1.08817 | 0.99178 | 0.9981 |
| lightgbm | 1.03775 | 1.03775 | 1.03775 | 0.99718 | 1.02515 | 1.05709 | 1.03749 | 1.03354 |
| lightgbm_capacity2 | 1.06277 | 1.06277 | 1.03159 | 0.99133 | 1.06984 | 1.07481 | 1.06447 | 1.05966 |
| sarimax | 0.96411 | 0.96431 | 0.90788 | 0.90769 | 0.96615 | 0.97697 | 0.96574 | 0.96673 |
| chronos | 0.89199 | 0.91231 | 0.91135 | 0.8882 | 0.91049 | 0.89251 | 0.91832 | 0.91832 |
| timesfm | 0.88898 | 0.91455 | 0.79464 | 0.77696 | 0.90889 | 0.90445 | 0.91278 | 0.91219 |

## Lead 14

| model | calendar | zero5 | day5 | pooled_day5 | window5 | pooled_window5 | placebo_day5 | placebo_window5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 1.10076 | 1.10076 | 1.03816 | 1.0428 | 1.18585 | 1.19292 | 1.10916 | 1.1221 |
| lightgbm | 1.37246 | 1.37246 | 1.37246 | 1.33859 | 1.37456 | 1.36843 | 1.37246 | 1.37638 |
| lightgbm_capacity2 | 1.45189 | 1.45189 | 1.45127 | 1.40222 | 1.4548 | 1.4687 | 1.45021 | 1.46512 |
| sarimax | 1.1419 | 1.14217 | 1.07725 | 1.08324 | 1.14715 | 1.15146 | 1.14336 | 1.13983 |
| chronos | 0.94949 | 0.96057 | 0.95524 | 0.94828 | 0.96537 | 0.96108 | 0.9611 | 0.95899 |
| timesfm | 0.9623 | 0.98333 | 0.92357 | 0.86802 | 0.95476 | 0.97561 | 0.9727 | 0.96632 |

## Native uncertainty

| model | arm | horizon | scaled_mean_pinball | coverage80 | scaled_width80 | scaled_WIS80_median |
| --- | --- | --- | --- | --- | --- | --- |
| chronos | calendar | 1 | 0.21982 | 0.70714 | 1.44827 | 0.36767 |
| chronos | calendar | 7 | 0.34737 | 0.75582 | 2.66684 | 0.55831 |
| chronos | calendar | 14 | 0.36601 | 0.80688 | 3.1963 | 0.59173 |
| chronos | day5 | 1 | 0.21117 | 0.73942 | 1.44383 | 0.35179 |
| chronos | day5 | 7 | 0.35111 | 0.7336 | 2.79905 | 0.56406 |
| chronos | day5 | 14 | 0.36858 | 0.82275 | 3.45089 | 0.59486 |
| chronos | placebo_day5 | 1 | 0.22064 | 0.72143 | 1.4243 | 0.37028 |
| chronos | placebo_day5 | 7 | 0.35688 | 0.71905 | 2.74643 | 0.57619 |
| chronos | placebo_day5 | 14 | 0.37191 | 0.80714 | 3.40337 | 0.60018 |
| chronos | placebo_window5 | 1 | 0.22195 | 0.70238 | 1.40882 | 0.37214 |
| chronos | placebo_window5 | 7 | 0.35722 | 0.72619 | 2.72072 | 0.57547 |
| chronos | placebo_window5 | 14 | 0.37144 | 0.8045 | 3.3889 | 0.59994 |
| chronos | pooled_day5 | 1 | 0.21013 | 0.73095 | 1.45796 | 0.3501 |
| chronos | pooled_day5 | 7 | 0.34187 | 0.74974 | 2.84353 | 0.54633 |
| chronos | pooled_day5 | 14 | 0.36744 | 0.82646 | 3.46209 | 0.59484 |
| chronos | pooled_window5 | 1 | 0.21872 | 0.73228 | 1.48665 | 0.36528 |
| chronos | pooled_window5 | 7 | 0.34521 | 0.78016 | 2.93189 | 0.55214 |
| chronos | pooled_window5 | 14 | 0.37219 | 0.83466 | 3.60208 | 0.60536 |
| chronos | window5 | 1 | 0.21949 | 0.72857 | 1.45596 | 0.36515 |
| chronos | window5 | 7 | 0.35113 | 0.78492 | 2.85705 | 0.56057 |
| chronos | window5 | 14 | 0.37278 | 0.81931 | 3.54355 | 0.60388 |
| chronos | zero5 | 1 | 0.21861 | 0.74153 | 1.45582 | 0.36641 |
| chronos | zero5 | 7 | 0.35408 | 0.7381 | 2.762 | 0.57024 |
| chronos | zero5 | 14 | 0.37151 | 0.80106 | 3.37297 | 0.59985 |
| timesfm | calendar | 1 | 0.22743 | 0.65926 | 1.21409 | 0.3844 |
| timesfm | calendar | 7 | 0.35101 | 0.70608 | 2.55804 | 0.5686 |
| timesfm | calendar | 14 | 0.37054 | 0.84074 | 3.33174 | 0.60042 |
| timesfm | day5 | 1 | 0.19414 | 0.69762 | 1.23286 | 0.3214 |
| timesfm | day5 | 7 | 0.31326 | 0.79841 | 2.7235 | 0.50413 |
| timesfm | day5 | 14 | 0.35793 | 0.85899 | 3.46161 | 0.58332 |
| timesfm | placebo_day5 | 1 | 0.22808 | 0.65079 | 1.19803 | 0.38676 |
| timesfm | placebo_day5 | 7 | 0.36026 | 0.67381 | 2.53414 | 0.58475 |
| timesfm | placebo_day5 | 14 | 0.37534 | 0.80714 | 3.31206 | 0.60595 |
| timesfm | placebo_window5 | 1 | 0.22793 | 0.6545 | 1.19658 | 0.38701 |
| timesfm | placebo_window5 | 7 | 0.35919 | 0.69048 | 2.53871 | 0.58156 |
| timesfm | placebo_window5 | 14 | 0.37292 | 0.82143 | 3.31949 | 0.60341 |
| timesfm | pooled_day5 | 1 | 0.16887 | 0.70265 | 1.16786 | 0.27846 |
| timesfm | pooled_day5 | 7 | 0.30592 | 0.7918 | 2.622 | 0.49063 |
| timesfm | pooled_day5 | 14 | 0.33707 | 0.86243 | 3.33911 | 0.54786 |
| timesfm | pooled_window5 | 1 | 0.22774 | 0.63651 | 1.1921 | 0.38556 |
| timesfm | pooled_window5 | 7 | 0.3561 | 0.68095 | 2.52904 | 0.57765 |
| timesfm | pooled_window5 | 14 | 0.37489 | 0.82143 | 3.28266 | 0.60516 |
| timesfm | window5 | 1 | 0.22938 | 0.64735 | 1.2181 | 0.38886 |
| timesfm | window5 | 7 | 0.35464 | 0.71429 | 2.60291 | 0.57241 |
| timesfm | window5 | 14 | 0.3689 | 0.8418 | 3.36015 | 0.59935 |
| timesfm | zero5 | 1 | 0.22702 | 0.63889 | 1.18766 | 0.38495 |
| timesfm | zero5 | 7 | 0.36068 | 0.67857 | 2.50804 | 0.58656 |
| timesfm | zero5 | 14 | 0.37973 | 0.80952 | 3.28254 | 0.6111 |

Native intervals are uncalibrated and unchanged. Coverage accompanies width/pinball and one-interval WIS; WIS=(0.5*median absolute error+0.1*80%interval score)/1.5. No marginal sorting or clipping. Invalid intervals propagate undefined scores.

Paired contrasts, both years, each family and leave-family-out sensitivity are retained. Historical/proxy overlap, publication lag/revisions, complete amendments, source rights and human review remain unresolved. Ordinary-day and event scores describe different cohorts. No causal mechanism, universal winner, untouched test or new independent events are inferred.
