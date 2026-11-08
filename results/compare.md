# Paired bootstrap comparisons

1000 resamples of the 194 labelled countries (seed 42); the same indices are used for both models and all repeats. For each resample the F1 is computed per repeat (3 repeats) from the pooled out-of-fold predictions, averaged over repeats, and the difference first minus second is taken. Interval = 2.5th and 97.5th percentile of the differences.

Where one model has fewer repeats, both are compared on the repeats they share (column `repeats`).

| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | strict_random_forest | 0,1,2 | -0.059 | -0.060 | [-0.155, +0.014] | yes |
| G1_celoe_strict_disc_hv1_n0 | strict_tree_full | 0,1,2 | +0.005 | +0.006 | [-0.057, +0.068] | yes |
| G1_celoe_strict_disc_hv1_n0 | rule_europe | 0,1,2 | +0.017 | +0.017 | [-0.035, +0.072] | yes |
| G1_celoe_strict_disc_hv1_n0 | G3_celoe_strict_disc_hv0_n0 | 0,1,2 | +0.205 | +0.208 | [+0.109, +0.303] | no |
| G1_celoe_strict_disc_hv1_n0 | G2_celoe_strict_disc_hv1_n10 | 0,1,2 | +0.044 | +0.042 | [-0.003, +0.098] | yes |
| G3_celoe_strict_disc_hv0_n0 | G4_celoe_strict_disc_hv0_n10 | 0,1,2 | -0.093 | -0.098 | [-0.199, +0.009] | yes |
| G1_celoe_strict_disc_hv1_n0 | G5_ocel_strict_disc_hv1_n0 | 0,1,2 | +0.070 | +0.070 | [+0.025, +0.124] | no |
| G3_celoe_strict_disc_hv0_n0 | G7_ocel_strict_disc_hv0_n0 | 0,1,2 | -0.072 | -0.072 | [-0.163, +0.025] | yes |
| strict_random_forest | strict_tree_full | 0,1,2 | +0.064 | +0.066 | [-0.020, +0.168] | yes |
| A1_celoe_extended_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.120 | +0.121 | [+0.060, +0.198] | no |
| A2_celoe_masked_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.120 | +0.121 | [+0.060, +0.198] | no |
| A3_celoe_none_disc_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.015 | +0.015 | [+0.000, +0.035] | yes |
| O1_celoe_strict_disc_hv1_n0_pellet | G1_celoe_strict_disc_hv1_n0 | 0 only | -0.025 | -0.025 | [-0.112, +0.064] | yes |
| O2_celoe_strict_disc_hv1_n0_pellet_closure | G1_celoe_strict_disc_hv1_n0 | 0 only | +0.019 | +0.019 | [-0.061, +0.099] | yes |
| O2_celoe_strict_disc_hv1_n0_pellet_closure | O1_celoe_strict_disc_hv1_n0_pellet | 0 only | +0.044 | +0.044 | [+0.000, +0.102] | yes |
| A4_celoe_strict_dt_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.040 | +0.039 | [+0.000, +0.080] | no |
| A4_celoe_strict_dt_hv1_n0 | A3_celoe_none_disc_hv1_n0 | 0,1,2 | +0.025 | +0.024 | [-0.012, +0.062] | yes |
| O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint | G1_celoe_strict_disc_hv1_n0 | 0 only | -0.485 | -0.486 | [-0.597, -0.381] | no |
| O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint | O2_celoe_strict_disc_hv1_n0_pellet_closure | 0 only | -0.504 | -0.505 | [-0.605, -0.409] | no |
| O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint | O1_celoe_strict_disc_hv1_n0_pellet | 0 only | -0.460 | -0.461 | [-0.571, -0.363] | no |
