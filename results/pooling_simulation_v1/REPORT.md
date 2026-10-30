# Pooling under sparse support, response heterogeneity and date error

Controlled exploratory simulation registered before its outputs; informed by earlier real-data hypotheses. Established pooling/shrinkage, no novelty claim.

512synthetic datasets;2560method cells. The known baseline isolates event-effect estimation. This does not reproduce the behaviour of either foundation model or add independent real-world events. Lower error is better. Oracle is an unavailable reference.

| frequency | heterogeneity | date_error | noise | method | MAE_all | MAE_event | MAE_ordinary | coefficient_MSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | 1.0 | no_event | 0.90333 | 1.85095 | 0.80282 | 9.0 |
| 1 | 0.0 | 0 | 1.0 | oracle_true_effect | 0.80148 | 0.78885 | 0.80282 | 0.0 |
| 1 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | 0.80486 | 0.8241 | 0.80282 | 0.27837 |
| 1 | 0.0 | 0 | 1.0 | pooled_OLS | 0.80141 | 0.78814 | 0.80282 | 0.0681 |
| 1 | 0.0 | 0 | 1.0 | typed_OLS | 0.80724 | 0.84895 | 0.80282 | 0.45113 |
| 1 | 0.0 | 0 | 3.0 | no_event | 2.45421 | 2.88549 | 2.40847 | 9.0 |
| 1 | 0.0 | 0 | 3.0 | oracle_true_effect | 2.40445 | 2.36654 | 2.40847 | 0.0 |
| 1 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | 2.41459 | 2.47231 | 2.40847 | 2.50537 |
| 1 | 0.0 | 0 | 3.0 | pooled_OLS | 2.40424 | 2.36442 | 2.40847 | 0.61288 |
| 1 | 0.0 | 0 | 3.0 | typed_OLS | 2.42173 | 2.54685 | 2.40847 | 4.06015 |
| 1 | 0.0 | 2 | 1.0 | no_event | 0.89369 | 1.77361 | 0.80037 | 9.0 |
| 1 | 0.0 | 2 | 1.0 | oracle_true_effect | 0.80051 | 0.80181 | 0.80037 | 0.0 |
| 1 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | 0.84601 | 1.20479 | 0.80796 | 0.56858 |
| 1 | 0.0 | 2 | 1.0 | pooled_OLS | 0.84473 | 1.19248 | 0.80785 | 0.35812 |
| 1 | 0.0 | 2 | 1.0 | typed_OLS | 0.84749 | 1.21957 | 0.80803 | 0.74148 |
| 1 | 0.0 | 2 | 3.0 | no_event | 2.43515 | 2.75617 | 2.40111 | 9.0 |
| 1 | 0.0 | 2 | 3.0 | oracle_true_effect | 2.40152 | 2.40542 | 2.40111 | 0.0 |
| 1 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | 2.42867 | 2.63709 | 2.40656 | 2.42676 |
| 1 | 0.0 | 2 | 3.0 | pooled_OLS | 2.42398 | 2.5943 | 2.40592 | 0.79686 |
| 1 | 0.0 | 2 | 3.0 | typed_OLS | 2.43348 | 2.68238 | 2.40708 | 3.76582 |
| 1 | 3.0 | 0 | 1.0 | no_event | 0.96873 | 2.53302 | 0.80282 | 27.0 |
| 1 | 3.0 | 0 | 1.0 | oracle_true_effect | 0.80148 | 0.78885 | 0.80282 | 0.0 |
| 1 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | 0.81797 | 0.96076 | 0.80282 | 1.46551 |
| 1 | 3.0 | 0 | 1.0 | pooled_OLS | 0.93674 | 2.19935 | 0.80282 | 18.0681 |
| 1 | 3.0 | 0 | 1.0 | typed_OLS | 0.80724 | 0.84895 | 0.80282 | 0.45113 |
| 1 | 3.0 | 0 | 3.0 | no_event | 2.49725 | 3.33432 | 2.40847 | 27.0 |
| 1 | 3.0 | 0 | 3.0 | oracle_true_effect | 2.40445 | 2.36654 | 2.40847 | 0.0 |
| 1 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | 2.41655 | 2.4928 | 2.40847 | 3.65061 |
| 1 | 3.0 | 0 | 3.0 | pooled_OLS | 2.47167 | 3.06763 | 2.40847 | 18.61288 |
| 1 | 3.0 | 0 | 3.0 | typed_OLS | 2.42173 | 2.54685 | 2.40847 | 4.06015 |
| 1 | 3.0 | 2 | 1.0 | no_event | 0.96865 | 2.55533 | 0.80037 | 27.0 |
| 1 | 3.0 | 2 | 1.0 | oracle_true_effect | 0.80051 | 0.80181 | 0.80037 | 0.0 |
| 1 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | 0.90162 | 1.74626 | 0.81204 | 3.57156 |
| 1 | 3.0 | 2 | 1.0 | pooled_OLS | 0.96103 | 2.40563 | 0.80781 | 18.43219 |
| 1 | 3.0 | 2 | 1.0 | typed_OLS | 0.89725 | 1.67337 | 0.81493 | 1.55657 |
| 1 | 3.0 | 2 | 3.0 | no_event | 2.49592 | 3.38992 | 2.40111 | 27.0 |
| 1 | 3.0 | 2 | 3.0 | oracle_true_effect | 2.40152 | 2.40542 | 2.40111 | 0.0 |
| 1 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | 2.46613 | 2.99189 | 2.41037 | 5.57223 |
| 1 | 3.0 | 2 | 3.0 | pooled_OLS | 2.49719 | 3.358 | 2.40589 | 18.89925 |
| 1 | 3.0 | 2 | 3.0 | typed_OLS | 2.4672 | 2.9825 | 2.41255 | 4.65517 |
| 4 | 0.0 | 0 | 1.0 | no_event | 1.19335 | 1.82616 | 0.79959 | 9.0 |
| 4 | 0.0 | 0 | 1.0 | oracle_true_effect | 0.79719 | 0.79333 | 0.79959 | 0.0 |
| 4 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | 0.79909 | 0.79828 | 0.79959 | 0.08452 |
| 4 | 0.0 | 0 | 1.0 | pooled_OLS | 0.79836 | 0.79638 | 0.79959 | 0.02022 |
| 4 | 0.0 | 0 | 1.0 | typed_OLS | 0.79955 | 0.79947 | 0.79959 | 0.09625 |
| 4 | 0.0 | 0 | 3.0 | no_event | 2.5687 | 2.84177 | 2.39878 | 9.0 |
| 4 | 0.0 | 0 | 3.0 | oracle_true_effect | 2.39158 | 2.38 | 2.39878 | 0.0 |
| 4 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | 2.39727 | 2.39484 | 2.39878 | 0.76064 |
| 4 | 0.0 | 0 | 3.0 | pooled_OLS | 2.39508 | 2.38914 | 2.39878 | 0.18201 |
| 4 | 0.0 | 0 | 3.0 | typed_OLS | 2.39864 | 2.39841 | 2.39878 | 0.86622 |
| 4 | 0.0 | 2 | 1.0 | no_event | 1.19374 | 1.83455 | 0.79502 | 9.0 |
| 4 | 0.0 | 2 | 1.0 | oracle_true_effect | 0.7958 | 0.79705 | 0.79502 | 0.0 |
| 4 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | 0.9404 | 1.14128 | 0.81541 | 0.35289 |
| 4 | 0.0 | 2 | 1.0 | pooled_OLS | 0.93712 | 1.13253 | 0.81553 | 0.28819 |
| 4 | 0.0 | 2 | 1.0 | typed_OLS | 0.94103 | 1.1429 | 0.81542 | 0.3647 |
| 4 | 0.0 | 2 | 3.0 | no_event | 2.56058 | 2.84269 | 2.38505 | 9.0 |
| 4 | 0.0 | 2 | 3.0 | oracle_true_effect | 2.38739 | 2.39116 | 2.38505 | 0.0 |
| 4 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | 2.44656 | 2.54059 | 2.38805 | 0.93453 |
| 4 | 0.0 | 2 | 3.0 | pooled_OLS | 2.43745 | 2.516 | 2.38858 | 0.43391 |
| 4 | 0.0 | 2 | 3.0 | typed_OLS | 2.44836 | 2.54532 | 2.38803 | 1.02587 |
| 4 | 3.0 | 0 | 1.0 | no_event | 1.49784 | 2.62001 | 0.79959 | 27.0 |
| 4 | 3.0 | 0 | 1.0 | oracle_true_effect | 0.79719 | 0.79333 | 0.79959 | 0.0 |
| 4 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | 0.80625 | 0.81695 | 0.79959 | 0.20795 |
| 4 | 3.0 | 0 | 1.0 | pooled_OLS | 1.37086 | 2.28897 | 0.79959 | 18.02022 |
| 4 | 3.0 | 0 | 1.0 | typed_OLS | 0.79955 | 0.79947 | 0.79959 | 0.09625 |
| 4 | 3.0 | 0 | 3.0 | no_event | 2.82807 | 3.51799 | 2.39878 | 27.0 |
| 4 | 3.0 | 0 | 3.0 | oracle_true_effect | 2.39158 | 2.38 | 2.39878 | 0.0 |
| 4 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | 2.40012 | 2.40228 | 2.39878 | 0.89832 |
| 4 | 3.0 | 0 | 3.0 | pooled_OLS | 2.71685 | 3.22804 | 2.39878 | 18.18201 |
| 4 | 3.0 | 0 | 3.0 | typed_OLS | 2.39864 | 2.39841 | 2.39878 | 0.86622 |
| 4 | 3.0 | 2 | 1.0 | no_event | 1.49205 | 2.61228 | 0.79502 | 27.0 |
| 4 | 3.0 | 2 | 1.0 | oracle_true_effect | 0.7958 | 0.79705 | 0.79502 | 0.0 |
| 4 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | 1.11175 | 1.53538 | 0.84815 | 1.43336 |
| 4 | 3.0 | 2 | 1.0 | pooled_OLS | 1.42119 | 2.39482 | 0.81538 | 18.30533 |
| 4 | 3.0 | 2 | 1.0 | typed_OLS | 1.1101 | 1.52223 | 0.85366 | 0.95761 |
| 4 | 3.0 | 2 | 3.0 | no_event | 2.81658 | 3.51013 | 2.38505 | 27.0 |
| 4 | 3.0 | 2 | 3.0 | oracle_true_effect | 2.38739 | 2.39116 | 2.38505 | 0.0 |
| 4 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | 2.54173 | 2.76616 | 2.40208 | 2.00605 |
| 4 | 3.0 | 2 | 3.0 | pooled_OLS | 2.74219 | 3.31049 | 2.38857 | 18.45465 |
| 4 | 3.0 | 2 | 3.0 | typed_OLS | 2.54255 | 2.764 | 2.40475 | 1.61875 |

## Paired contrasts

| frequency | heterogeneity | date_error | noise | arm | reference | n_seeds | event_MAE_difference | MC_standard_error | MC95_low | MC95_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | 1.0 | typed_OLS | pooled_OLS | 32 | 0.06081 | 0.01623 | 0.02901 | 0.09261 |
| 1 | 0.0 | 0 | 3.0 | typed_OLS | pooled_OLS | 32 | 0.18243 | 0.04868 | 0.08702 | 0.27784 |
| 1 | 0.0 | 2 | 1.0 | typed_OLS | pooled_OLS | 32 | 0.02709 | 0.01171 | 0.00414 | 0.05004 |
| 1 | 0.0 | 2 | 3.0 | typed_OLS | pooled_OLS | 32 | 0.08809 | 0.04216 | 0.00546 | 0.17072 |
| 1 | 3.0 | 0 | 1.0 | typed_OLS | pooled_OLS | 32 | -1.3504 | 0.05082 | -1.45 | -1.2508 |
| 1 | 3.0 | 0 | 3.0 | typed_OLS | pooled_OLS | 32 | -0.52079 | 0.10302 | -0.7227 | -0.31888 |
| 1 | 3.0 | 2 | 1.0 | typed_OLS | pooled_OLS | 32 | -0.73225 | 0.04849 | -0.8273 | -0.63721 |
| 1 | 3.0 | 2 | 3.0 | typed_OLS | pooled_OLS | 32 | -0.3755 | 0.07415 | -0.52082 | -0.23017 |
| 4 | 0.0 | 0 | 1.0 | typed_OLS | pooled_OLS | 32 | 0.00309 | 0.00286 | -0.00252 | 0.0087 |
| 4 | 0.0 | 0 | 3.0 | typed_OLS | pooled_OLS | 32 | 0.00927 | 0.00859 | -0.00757 | 0.0261 |
| 4 | 0.0 | 2 | 1.0 | typed_OLS | pooled_OLS | 32 | 0.01037 | 0.00311 | 0.00428 | 0.01646 |
| 4 | 0.0 | 2 | 3.0 | typed_OLS | pooled_OLS | 32 | 0.02932 | 0.01081 | 0.00813 | 0.0505 |
| 4 | 3.0 | 0 | 1.0 | typed_OLS | pooled_OLS | 32 | -1.4895 | 0.01911 | -1.52696 | -1.45203 |
| 4 | 3.0 | 0 | 3.0 | typed_OLS | pooled_OLS | 32 | -0.82963 | 0.03862 | -0.90532 | -0.75394 |
| 4 | 3.0 | 2 | 1.0 | typed_OLS | pooled_OLS | 32 | -0.87259 | 0.02116 | -0.91407 | -0.83111 |
| 4 | 3.0 | 2 | 3.0 | typed_OLS | pooled_OLS | 32 | -0.5465 | 0.04133 | -0.6275 | -0.4655 |
| 1 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.03596 | 0.01124 | 0.01393 | 0.058 |
| 1 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.10789 | 0.03373 | 0.04179 | 0.17399 |
| 1 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.01231 | 0.00903 | -0.00539 | 0.03001 |
| 1 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.04279 | 0.03235 | -0.02062 | 0.1062 |
| 1 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -1.23859 | 0.02784 | -1.29316 | -1.18403 |
| 1 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.57483 | 0.07353 | -0.71896 | -0.43071 |
| 1 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.65937 | 0.03498 | -0.72793 | -0.59081 |
| 1 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.36611 | 0.05828 | -0.48034 | -0.25187 |
| 4 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.0019 | 0.00263 | -0.00326 | 0.00706 |
| 4 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.0057 | 0.0079 | -0.00979 | 0.02118 |
| 4 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.00876 | 0.00287 | 0.00314 | 0.01438 |
| 4 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | 0.02459 | 0.00987 | 0.00524 | 0.04393 |
| 4 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -1.47202 | 0.01666 | -1.50468 | -1.43936 |
| 4 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.82576 | 0.03548 | -0.89531 | -0.75621 |
| 4 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.85944 | 0.01894 | -0.89656 | -0.82231 |
| 4 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | pooled_OLS | 32 | -0.54433 | 0.03746 | -0.61775 | -0.47091 |
| 1 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.02485 | 0.00517 | -0.03497 | -0.01472 |
| 1 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.07454 | 0.0155 | -0.10492 | -0.04415 |
| 1 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.01478 | 0.00312 | -0.0209 | -0.00866 |
| 1 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.0453 | 0.01053 | -0.06593 | -0.02467 |
| 1 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.11181 | 0.02956 | 0.05386 | 0.16975 |
| 1 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.05404 | 0.03418 | -0.12103 | 0.01294 |
| 1 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.07288 | 0.01647 | 0.04059 | 0.10517 |
| 1 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.00939 | 0.02156 | -0.03287 | 0.05164 |
| 4 | 0.0 | 0 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.00119 | 0.00027 | -0.00171 | -0.00067 |
| 4 | 0.0 | 0 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.00357 | 0.0008 | -0.00514 | -0.002 |
| 4 | 0.0 | 2 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.00161 | 0.00026 | -0.00213 | -0.0011 |
| 4 | 0.0 | 2 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | -0.00473 | 0.00105 | -0.00679 | -0.00267 |
| 4 | 3.0 | 0 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.01748 | 0.00433 | 0.00899 | 0.02597 |
| 4 | 3.0 | 0 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.00387 | 0.00447 | -0.00488 | 0.01262 |
| 4 | 3.0 | 2 | 1.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.01316 | 0.00308 | 0.00713 | 0.01918 |
| 4 | 3.0 | 2 | 3.0 | partial_pooling_fixed2 | typed_OLS | 32 | 0.00216 | 0.00482 | -0.00728 | 0.01161 |

Test365daily absolute error, separately trueevent-window/non-event and all days; coefficient mean square error. Complete seed/scenario/method cells. Paired seed differences with mean+/-1.96MCstandarderror across32independent generators describe MonteCarlo precision only; do not use them for Indian event significance.

Pooling and shrinkage have established bias/variance explanations. Any pattern here is conditional on this declared generator, known shape/baseline and fixed penalty, not evidence of a new method or universal identity mechanism.
