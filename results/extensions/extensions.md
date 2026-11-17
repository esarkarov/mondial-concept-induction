# Extensions E1 to E4 (run after the freeze at tag phase-3)

Configurations were fixed before running and not changed after seeing results. Stored Phase 1 to 4 results are read, not modified. Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats (no std where there is one repeat); pooled F1 = out-of-fold predictions of all folds of a repeat, 95% bootstrap (1000 resamples per repeat); concept length = number of names, constructors and numbers.

## E1. Europe-only learning problem (run after the freeze)

**Sample: 41 countries** (27 positives, 14 European negatives), the existing folds restricted to these countries (about 8 per test fold; 5 folds x 3 repeats). Training examples = the training part of the same folds restricted to the subset. CELOE, 60 s, noise 0, discretised, 3 workers. All numbers below are on 41 countries.

### Learned concepts

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| E1a_celoe_strict_disc_hv1_n0_europe | 15/15 | 0.666 ± 0.047 | 0.737 ± 0.038 | 0.840 ± 0.041 | 0.765 ± 0.027 | 0.760 [0.624, 0.866] | 5.5 | 39111 | 60.0 |
| E1b_celoe_strict_disc_hv0_n0_europe | 15/15 | 0.695 ± 0.067 | 0.746 ± 0.030 | 0.871 ± 0.042 | 0.788 ± 0.042 | 0.785 [0.659, 0.888] | 5.5 | 26725 | 60.0 |
| E1c_celoe_extended_disc_hv1_n0_europe | 15/15 | 0.856 ± 0.014 | 0.874 ± 0.049 | 0.936 ± 0.021 | 0.892 ± 0.010 | 0.889 [0.786, 0.963] | 6.3 | 23930 | 60.0 |

### Baselines on the same 41 countries and folds (strict features, trained on the subset's training rows only)

| model | accuracy | precision | recall | F1 | pooled F1 [95% CI] | specificity (pooled) |
|---|---|---|---|---|---|---|
| e1_strict: majority_class | 0.680 ± 0.014 | 0.680 ± 0.014 | 1.000 ± 0.000 | 0.803 ± 0.006 | 0.794 [0.670, 0.887] | 0.000 |
| e1_strict: predict_all_positive | 0.680 ± 0.014 | 0.680 ± 0.014 | 1.000 ± 0.000 | 0.803 ± 0.006 | 0.794 [0.670, 0.887] | 0.000 |
| e1_strict: tree_depth3 | 0.711 ± 0.054 | 0.769 ± 0.030 | 0.838 ± 0.127 | 0.782 ± 0.059 | 0.783 [0.652, 0.890] | 0.429 |
| e1_strict: tree_full | 0.707 ± 0.069 | 0.786 ± 0.038 | 0.791 ± 0.102 | 0.769 ± 0.064 | 0.773 [0.636, 0.880] | 0.524 |
| e1_strict: random_forest | 0.844 ± 0.025 | 0.845 ± 0.011 | 0.973 ± 0.023 | 0.892 ± 0.018 | 0.883 [0.780, 0.955] | 0.548 |

### Pooled out-of-fold metrics and specificity (share of the 14 European negatives classified correctly; mean over repeats)

| config | accuracy | precision | recall | F1 | specificity |
|---|---|---|---|---|---|
| E1a_celoe_strict_disc_hv1_n0_europe | 0.650 | 0.695 | 0.840 | 0.760 | 0.286 |
| E1b_celoe_strict_disc_hv0_n0_europe | 0.683 | 0.710 | 0.877 | 0.785 | 0.310 |
| E1c_celoe_extended_disc_hv1_n0_europe | 0.846 | 0.846 | 0.938 | 0.889 | 0.667 |
| e1_majority_class | 0.659 | 0.659 | 1.000 | 0.794 | 0.000 |
| e1_predict_all_positive | 0.659 | 0.659 | 1.000 | 0.794 | 0.000 |
| e1_tree_depth3 | 0.699 | 0.741 | 0.840 | 0.783 | 0.429 |
| e1_tree_full | 0.699 | 0.761 | 0.790 | 0.773 | 0.524 |
| e1_random_forest | 0.829 | 0.806 | 0.975 | 0.883 | 0.548 |

### Paired bootstrap on the 41 countries

1000 resamples (seed 42), shared indices, F1 averaged over the 3 repeats, difference first minus second.

| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|---|
| E1a_celoe_strict_disc_hv1_n0_europe | e1_random_forest | 0,1,2 | -0.123 | -0.125 | [-0.197, -0.065] | no |
| E1a_celoe_strict_disc_hv1_n0_europe | e1_predict_all_positive | 0,1,2 | -0.034 | -0.036 | [-0.100, +0.028] | yes |
| E1c_celoe_extended_disc_hv1_n0_europe | E1a_celoe_strict_disc_hv1_n0_europe | 0,1,2 | +0.129 | +0.131 | [+0.064, +0.207] | no |

### Most frequent concepts and details

### E1a_celoe_strict_disc_hv1_n0_europe

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 70.8 to 75.4 s
- three most frequent concepts:
  - 4x `PopulationQ2 or (isMember some ({org_BIS}))`
  - 2x `(InflationQ1 or PopulationGrowthQ1) and (not (PopulationQ1))`
  - 2x `(not (InflationQ4)) and (isMember some ({org_MIGA}))`
- nearest reference (count): Europe and org_EBRD (7), Europe and org_MIGA (2), Europe and org_ICC (2), Europe and org_EAPC (1), Europe and org_AG (1), Europe and org_BIS (1), Europe and org_ISO (1)
- concept length min/median/max: 5/5/7; mean train accuracy 86.89; jaccard to nearest reference min/mean: 0.84/0.90

### E1b_celoe_strict_disc_hv0_n0_europe

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 70.6 to 74.8 s
- three most frequent concepts:
  - 3x `(not (InflationQ4)) and (not (PopulationQ1))`
  - 2x `GdpPerCapitaQ3 or GdpQ3 or GdpQ4`
  - 2x `GdpPerCapitaQ3 or GdpQ4 or PopulationGrowthQ3`
- nearest reference (count): Europe and org_ISO (5), Europe and org_EBRD (5), Europe and org_ICC (3), Europe and org_NSG (2)
- concept length min/median/max: 5/5/7; mean train accuracy 86.90; jaccard to nearest reference min/mean: 0.84/0.90

### E1c_celoe_extended_disc_hv1_n0_europe

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 72.4 to 87.2 s
- three most frequent concepts:
  - 7x `(isMember some ({org_AG})) and (isMember some ({org_IOM}))`
  - 2x `(InflationQ1 or PopulationGrowthQ1) and (isMember some ({org_AG}))`
  - 2x `(not (GdpQ2)) and (isMember some ({org_AG}))`
- nearest reference (count): Europe and org_AG (11), Europe and org_EIB (2), Europe and org_ICCt (1), Europe and org_EBRD (1)
- concept length min/median/max: 3/7/7; mean train accuracy 93.34; jaccard to nearest reference min/mean: 0.84/0.95


## Odd things


## Not done

