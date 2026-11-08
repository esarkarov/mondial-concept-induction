# Paired bootstrap comparisons

1000 resamples of the 194 labelled countries (seed 42); the same indices are used for both models and all repeats. For each resample the F1 is computed per repeat (3 repeats) from the pooled out-of-fold predictions, averaged over repeats, and the difference first minus second is taken. Interval = 2.5th and 97.5th percentile of the differences.

| first | second | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | strict_random_forest | -0.059 | -0.060 | [-0.155, +0.014] | yes |
| G1_celoe_strict_disc_hv1_n0 | strict_tree_full | +0.005 | +0.006 | [-0.057, +0.068] | yes |
| G1_celoe_strict_disc_hv1_n0 | rule_europe | +0.017 | +0.017 | [-0.035, +0.072] | yes |
| G1_celoe_strict_disc_hv1_n0 | G3_celoe_strict_disc_hv0_n0 | +0.205 | +0.208 | [+0.109, +0.303] | no |
| G1_celoe_strict_disc_hv1_n0 | G2_celoe_strict_disc_hv1_n10 | +0.044 | +0.042 | [-0.003, +0.098] | yes |
| G3_celoe_strict_disc_hv0_n0 | G4_celoe_strict_disc_hv0_n10 | -0.093 | -0.098 | [-0.199, +0.009] | yes |
| G1_celoe_strict_disc_hv1_n0 | G5_ocel_strict_disc_hv1_n0 | +0.070 | +0.070 | [+0.025, +0.124] | no |
| G3_celoe_strict_disc_hv0_n0 | G7_ocel_strict_disc_hv0_n0 | -0.072 | -0.072 | [-0.163, +0.025] | yes |
| strict_random_forest | strict_tree_full | +0.064 | +0.066 | [-0.020, +0.168] | yes |
| A1_celoe_extended_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | +0.120 | +0.121 | [+0.060, +0.198] | no |
| A2_celoe_masked_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | +0.120 | +0.121 | [+0.060, +0.198] | no |
| A3_celoe_none_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | +0.015 | +0.015 | [+0.000, +0.035] | yes |
