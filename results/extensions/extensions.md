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


## E1 random forest feature importances (run after the freeze)

Random forest of the Europe-only problem (500 trees, seed 42, median imputation), fitted on the training part of each of the 15 folds of the 41 countries; importance = `feature_importances_`, mean over the 15 fits (std over the 15 fits in the last column). Top 15 of each feature set; full lists in `results/extensions/e1_importances_<variant>.csv`.

### strict features (188 features)

| rank | feature | mean importance | std |
|---|---|---|---|
| 1 | unemployment | 0.0659 | 0.0151 |
| 2 | agriculture | 0.0477 | 0.0090 |
| 3 | service | 0.0419 | 0.0116 |
| 4 | industry | 0.0419 | 0.0106 |
| 5 | population | 0.0373 | 0.0064 |
| 6 | gdp | 0.0369 | 0.0080 |
| 7 | gov_other | 0.0297 | 0.0103 |
| 8 | inflation | 0.0256 | 0.0057 |
| 9 | n_airports | 0.0238 | 0.0051 |
| 10 | independence_year | 0.0233 | 0.0116 |
| 11 | religion_Protestant | 0.0228 | 0.0057 |
| 12 | area | 0.0211 | 0.0052 |
| 13 | org_BIS | 0.0189 | 0.0080 |
| 14 | pop_growth | 0.0187 | 0.0065 |
| 15 | religion_Christian Orthodox | 0.0182 | 0.0081 |

### extended features (206 features)

| rank | feature | mean importance | std |
|---|---|---|---|
| 1 | org_AG | 0.0666 | 0.0102 |
| 2 | unemployment | 0.0594 | 0.0139 |
| 3 | agriculture | 0.0372 | 0.0092 |
| 4 | service | 0.0344 | 0.0110 |
| 5 | industry | 0.0344 | 0.0123 |
| 6 | gdp | 0.0295 | 0.0080 |
| 7 | population | 0.0283 | 0.0056 |
| 8 | org_PCA | 0.0264 | 0.0070 |
| 9 | gov_other | 0.0260 | 0.0098 |
| 10 | n_airports | 0.0237 | 0.0036 |
| 11 | inflation | 0.0236 | 0.0057 |
| 12 | org_NSG | 0.0215 | 0.0060 |
| 13 | org_ICCt | 0.0199 | 0.0085 |
| 14 | religion_Protestant | 0.0192 | 0.0050 |
| 15 | independence_year | 0.0192 | 0.0095 |


## E2. Discretisation sensitivity (run after the freeze)

CELOE, strict KB, hasValue on, noise 0, 60 s, 15 folds, 194 countries; G1 is the 4-bin reference (stored result, not rerun). Quantile bins as before; ties can give fewer bins.

### Learned concepts

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| E2a_celoe_strict_b3_hv1_n0 | 15/15 | 0.945 ± 0.006 | 0.784 ± 0.003 | 0.902 ± 0.073 | 0.825 ± 0.039 | 0.819 [0.700, 0.914] | 9.7 | 20637 | 60.0 |
| E2b_celoe_strict_b5_hv1_n0 | 15/15 | 0.954 ± 0.009 | 0.802 ± 0.025 | 0.951 ± 0.021 | 0.859 ± 0.026 | 0.851 [0.739, 0.938] | 8.7 | 14100 | 60.0 |

### Bin sizes (countries per bin, over the 246 countries with a value)

| attribute | 3 bins | 4 bins (reference) | 5 bins |
|---|---|---|---|
| population | 82 / 82 / 82 (3 bins) | 62 / 61 / 61 / 62 (4 bins) | 50 / 49 / 49 / 49 / 49 (5 bins) |
| area | 82 / 82 / 82 (3 bins) | 62 / 61 / 61 / 62 (4 bins) | 50 / 49 / 49 / 49 / 49 (5 bins) |
| gdp | 79 / 77 / 78 (3 bins) | 59 / 58 / 58 / 59 (4 bins) | 47 / 47 / 46 / 47 / 47 (5 bins) |
| gdp_per_capita | 78 / 78 / 78 (3 bins) | 59 / 58 / 58 / 59 (4 bins) | 47 / 47 / 46 / 47 / 47 (5 bins) |
| inflation | 82 / 69 / 75 (3 bins) | 60 / 53 / 57 / 56 (4 bins) | 46 / 49 / 44 / 42 / 45 (5 bins) |
| infant_mortality | 76 / 76 / 76 (3 bins) | 57 / 57 / 57 / 57 (4 bins) | 46 / 45 / 46 / 45 / 46 (5 bins) |
| population_growth | 78 / 78 / 78 (3 bins) | 59 / 58 / 58 / 59 (4 bins) | 47 / 49 / 44 / 47 / 47 (5 bins) |
| n_airports | 148 / 24 / 74 (3 bins) | 148 / 42 / 56 (3 bins) | 148 / 0 / 53 / 45 (4 bins) |

### Bin atoms of the three most frequent concepts, with edges

- E2a_celoe_strict_b3_hv1_n0
  - 8x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (hasAirport some Airport)`: InflationQ3 (lower_exclusive 4.6, upper_inclusive None, 75 countries)
  - 2x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (isMember some ({org_MIGA}))`: InflationQ3 (lower_exclusive 4.6, upper_inclusive None, 75 countries)
  - 1x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (isMember some ({org_WMO}))`: InflationQ3 (lower_exclusive 4.6, upper_inclusive None, 75 countries)
- E2b_celoe_strict_b5_hv1_n0
  - 10x `(not (InflationQ5)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`: InflationQ5 (lower_exclusive 6.2, upper_inclusive None, 45 countries); PopulationQ1 (lower_exclusive None, upper_inclusive 103328.0, 50 countries)
  - 3x `(GdpPerCapitaQ4 or (not (NAirportsQ1))) and (encompassed some ({cont_Europe}))`: GdpPerCapitaQ4 (lower_exclusive 10126.707650136887, upper_inclusive 28519.580468882985, 47 countries); NAirportsQ1 (lower_exclusive None, upper_inclusive 1.0, 148 countries)
  - 1x `(encompassed some ({cont_Europe})) and (isMember some ({org_WMO}))`: no bin atoms

### Paired bootstrap vs G1

1000 resamples of the 194 countries (seed 42), same method as `results/compare.md`.

| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|---|
| E2a_celoe_strict_b3_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.008 | +0.009 | [-0.066, +0.075] | yes |
| E2b_celoe_strict_b5_hv1_n0 | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.040 | +0.040 | [-0.009, +0.095] | yes |

### Most frequent concepts and details

### E2a_celoe_strict_b3_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 70.8 to 74.6 s
- three most frequent concepts:
  - 8x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (hasAirport some Airport)`
  - 2x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (isMember some ({org_MIGA}))`
  - 1x `(not (InflationQ3)) and (encompassed some ({cont_Europe})) and (isMember some ({org_WMO}))`
- nearest reference (count): Europe and org_AG (11), Europe and org_ICC (2), Europe and org_IMO (1), Europe and org_CD (1)
- concept length min/median/max: 8/10/10; mean train accuracy 96.99; jaccard to nearest reference min/mean: 0.85/0.93

### E2b_celoe_strict_b5_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 69.8 to 76.4 s
- three most frequent concepts:
  - 10x `(not (InflationQ5)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 3x `(GdpPerCapitaQ4 or (not (NAirportsQ1))) and (encompassed some ({cont_Europe}))`
  - 1x `(encompassed some ({cont_Europe})) and (isMember some ({org_WMO}))`
- nearest reference (count): Europe and org_EBRD (11), Europe and org_NSG (3), Europe and org_WMO (1)
- concept length min/median/max: 7/9/9; mean train accuracy 96.60; jaccard to nearest reference min/mean: 0.91/0.92


## E3 v1: grid did not contain the untuned default (run after the freeze)

Same 15 folds. Inside each training fold, 3-fold stratified inner CV (seed 42) picks hyperparameters by F1: tree `max_depth` in {2,3,4,5,None} x `min_samples_leaf` in {1,2,5}; forest `n_estimators` in {100,300} x `max_depth` in {None,3,5} x `max_features` in {sqrt,0.3}. Median imputation fitted on the training fold. Untuned rows are from `results/baselines.csv` (unchanged).

| model | accuracy | precision | recall | F1 | pooled accuracy | pooled precision | pooled recall | pooled F1 [95% CI] |
|---|---|---|---|---|---|---|---|---|
| strict: tuned_tree | 0.931 ± 0.011 | 0.756 ± 0.021 | 0.838 ± 0.097 | 0.764 ± 0.054 | 0.931 | 0.718 | 0.840 | 0.772 [0.637, 0.882] |
| strict: tuned_random_forest | 0.955 ± 0.008 | 0.877 ± 0.013 | 0.842 ± 0.038 | 0.840 ± 0.030 | 0.955 | 0.839 | 0.840 | 0.839 [0.712, 0.929] |
| extended: tuned_tree | 0.957 ± 0.012 | 0.808 ± 0.037 | 0.933 ± 0.061 | 0.857 ± 0.033 | 0.957 | 0.796 | 0.938 | 0.859 [0.755, 0.941] |
| extended: tuned_random_forest | 0.974 ± 0.005 | 0.888 ± 0.004 | 0.964 ± 0.034 | 0.915 ± 0.019 | 0.974 | 0.867 | 0.963 | 0.912 [0.820, 0.976] |
| extended: tree_full | 0.954 ± 0.005 | 0.830 ± 0.034 | 0.862 ± 0.054 | 0.834 ± 0.027 | 0.954 | 0.816 | 0.864 | 0.838 [0.724, 0.928] |
| extended: random_forest | 0.976 ± 0.003 | 0.888 ± 0.004 | 0.976 ± 0.021 | 0.922 ± 0.013 | 0.976 | 0.868 | 0.975 | 0.919 [0.831, 0.982] |
| strict: tree_full | 0.943 ± 0.005 | 0.802 ± 0.032 | 0.844 ± 0.073 | 0.799 ± 0.036 | 0.943 | 0.767 | 0.852 | 0.806 [0.679, 0.905] |
| strict: random_forest | 0.964 ± 0.005 | 0.898 ± 0.012 | 0.869 ± 0.015 | 0.872 ± 0.016 | 0.964 | 0.875 | 0.864 | 0.870 [0.753, 0.952] |

### Chosen hyperparameters (15 outer folds per row; full table in `tuned_hyperparameters.csv`)

**strict tree** (mean inner F1 0.764): 6x `{"max_depth": 2, "min_samples_leaf": 1}`; 5x `{"max_depth": 3, "min_samples_leaf": 1}`; 3x `{"max_depth": 2, "min_samples_leaf": 5}`; 1x `{"max_depth": 3, "min_samples_leaf": 5}`
  - max_depth: 2 (9), 3 (6)
  - min_samples_leaf: 1 (11), 5 (4)

**strict random_forest** (mean inner F1 0.858): 4x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 100}`; 4x `{"max_depth": null, "max_features": 0.3, "n_estimators": 100}`; 3x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 300}`; 1x `{"max_depth": 3, "max_features": 0.3, "n_estimators": 300}`; 1x `{"max_depth": 3, "max_features": "sqrt", "n_estimators": 100}`; 1x `{"max_depth": 5, "max_features": "sqrt", "n_estimators": 100}`; 1x `{"max_depth": null, "max_features": 0.3, "n_estimators": 300}`
  - max_depth: None (12), 3 (2), 5 (1)
  - max_features: sqrt (9), 0.3 (6)
  - n_estimators: 100 (10), 300 (5)

**extended tree** (mean inner F1 0.815): 9x `{"max_depth": 2, "min_samples_leaf": 1}`; 5x `{"max_depth": 3, "min_samples_leaf": 1}`; 1x `{"max_depth": 4, "min_samples_leaf": 2}`
  - max_depth: 2 (9), 3 (5), 4 (1)
  - min_samples_leaf: 1 (14), 2 (1)

**extended random_forest** (mean inner F1 0.929): 5x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 100}`; 4x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 300}`; 2x `{"max_depth": null, "max_features": 0.3, "n_estimators": 100}`; 2x `{"max_depth": null, "max_features": 0.3, "n_estimators": 300}`; 1x `{"max_depth": 3, "max_features": 0.3, "n_estimators": 100}`; 1x `{"max_depth": 5, "max_features": "sqrt", "n_estimators": 100}`
  - max_depth: None (13), 3 (1), 5 (1)
  - max_features: sqrt (10), 0.3 (5)
  - n_estimators: 100 (9), 300 (6)

### Paired bootstrap

1000 resamples of the 194 countries (seed 42), same method as `results/compare.md`.

| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|---|
| tuned_strict_random_forest | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.028 | +0.029 | [-0.043, +0.107] | yes |
| tuned_strict_tree | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | -0.039 | -0.040 | [-0.114, +0.022] | yes |
| tuned_strict_random_forest | strict_random_forest | 0,1,2 | -0.030 | -0.031 | [-0.064, -0.007] | no |

## E3 v2: grid contains the untuned default (run after the freeze)

Same protocol as E3 v1 (15 folds, inner 3-fold stratified CV, seed 42, F1 selection, median imputation fitted on the training fold); the forest grid is now `n_estimators` in {100,300,500} x `max_depth` in {None,3,5} x `max_features` in {sqrt,0.3}, so it contains the untuned default (500, None, sqrt); the tree grid is unchanged and already contains the default (None, leaf 1). v1 results above are kept unchanged.

| model | accuracy | precision | recall | F1 | pooled accuracy | pooled precision | pooled recall | pooled F1 [95% CI] |
|---|---|---|---|---|---|---|---|---|
| strict: tuned_v2_tree | 0.931 ± 0.011 | 0.756 ± 0.021 | 0.838 ± 0.097 | 0.764 ± 0.054 | 0.931 | 0.718 | 0.840 | 0.772 [0.637, 0.882] |
| strict: tuned_v2_random_forest | 0.961 ± 0.013 | 0.892 ± 0.022 | 0.856 ± 0.062 | 0.856 ± 0.049 | 0.960 | 0.863 | 0.852 | 0.857 [0.740, 0.943] |
| extended: tuned_v2_tree | 0.957 ± 0.012 | 0.808 ± 0.037 | 0.933 ± 0.061 | 0.857 ± 0.033 | 0.957 | 0.796 | 0.938 | 0.859 [0.755, 0.941] |
| extended: tuned_v2_random_forest | 0.974 ± 0.005 | 0.888 ± 0.004 | 0.964 ± 0.034 | 0.915 ± 0.019 | 0.974 | 0.867 | 0.963 | 0.912 [0.820, 0.976] |
| extended: tree_full | 0.954 ± 0.005 | 0.830 ± 0.034 | 0.862 ± 0.054 | 0.834 ± 0.027 | 0.954 | 0.816 | 0.864 | 0.838 [0.724, 0.928] |
| extended: random_forest | 0.976 ± 0.003 | 0.888 ± 0.004 | 0.976 ± 0.021 | 0.922 ± 0.013 | 0.976 | 0.868 | 0.975 | 0.919 [0.831, 0.982] |
| strict: tree_full | 0.943 ± 0.005 | 0.802 ± 0.032 | 0.844 ± 0.073 | 0.799 ± 0.036 | 0.943 | 0.767 | 0.852 | 0.806 [0.679, 0.905] |
| strict: random_forest | 0.964 ± 0.005 | 0.898 ± 0.012 | 0.869 ± 0.015 | 0.872 ± 0.016 | 0.964 | 0.875 | 0.864 | 0.870 [0.753, 0.952] |

### Chosen hyperparameters (15 outer folds per row; full table in `tuned_v2_hyperparameters.csv`)

**strict tree** (mean inner F1 0.764); untuned default `{"max_depth": null, "min_samples_leaf": 1}` chosen in 0 of 15 folds: 6x `{"max_depth": 2, "min_samples_leaf": 1}`; 5x `{"max_depth": 3, "min_samples_leaf": 1}`; 3x `{"max_depth": 2, "min_samples_leaf": 5}`; 1x `{"max_depth": 3, "min_samples_leaf": 5}`
  - max_depth: 2 (9), 3 (6)
  - min_samples_leaf: 1 (11), 5 (4)

**strict random_forest** (mean inner F1 0.864); untuned default `{"n_estimators": 500, "max_depth": null, "max_features": "sqrt"}` chosen in 5 of 15 folds: 5x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 500}`; 2x `{"max_depth": 5, "max_features": "sqrt", "n_estimators": 500}`; 2x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 300}`; 1x `{"max_depth": 3, "max_features": 0.3, "n_estimators": 300}`; 1x `{"max_depth": 5, "max_features": "sqrt", "n_estimators": 100}`; 1x `{"max_depth": null, "max_features": 0.3, "n_estimators": 100}`; 1x `{"max_depth": null, "max_features": 0.3, "n_estimators": 300}`; 1x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 100}`; 1x `{"max_depth": null, "max_features": 0.3, "n_estimators": 500}`
  - max_depth: None (11), 5 (3), 3 (1)
  - max_features: sqrt (11), 0.3 (4)
  - n_estimators: 500 (8), 300 (4), 100 (3)

**extended tree** (mean inner F1 0.815); untuned default `{"max_depth": null, "min_samples_leaf": 1}` chosen in 0 of 15 folds: 9x `{"max_depth": 2, "min_samples_leaf": 1}`; 5x `{"max_depth": 3, "min_samples_leaf": 1}`; 1x `{"max_depth": 4, "min_samples_leaf": 2}`
  - max_depth: 2 (9), 3 (5), 4 (1)
  - min_samples_leaf: 1 (14), 2 (1)

**extended random_forest** (mean inner F1 0.929); untuned default `{"n_estimators": 500, "max_depth": null, "max_features": "sqrt"}` chosen in 0 of 15 folds: 5x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 100}`; 3x `{"max_depth": null, "max_features": "sqrt", "n_estimators": 300}`; 2x `{"max_depth": null, "max_features": 0.3, "n_estimators": 100}`; 2x `{"max_depth": null, "max_features": 0.3, "n_estimators": 300}`; 1x `{"max_depth": 3, "max_features": 0.3, "n_estimators": 100}`; 1x `{"max_depth": null, "max_features": 0.3, "n_estimators": 500}`; 1x `{"max_depth": 5, "max_features": "sqrt", "n_estimators": 100}`
  - max_depth: None (13), 3 (1), 5 (1)
  - max_features: sqrt (9), 0.3 (6)
  - n_estimators: 100 (9), 300 (5), 500 (1)

### Paired bootstrap (v2)

1000 resamples of the 194 countries (seed 42), same method as `results/compare.md`; untuned extended predictions were refitted with the same seeds and match `results/baselines.csv` pooled F1 exactly.

| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |
|---|---|---|---|---|---|---|
| tuned_v2_strict_random_forest | strict_random_forest | 0,1,2 | -0.013 | -0.013 | [-0.042, +0.012] | yes |
| tuned_v2_strict_tree | strict_tree_full | 0,1,2 | -0.035 | -0.035 | [-0.077, +0.003] | yes |
| tuned_v2_strict_random_forest | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | +0.046 | +0.047 | [-0.023, +0.133] | yes |
| tuned_v2_strict_tree | G1_celoe_strict_disc_hv1_n0 | 0,1,2 | -0.039 | -0.040 | [-0.114, +0.022] | yes |
| tuned_v2_extended_random_forest | extended_random_forest | 0,1,2 | -0.006 | -0.006 | [-0.022, +0.000] | yes |
| tuned_v2_extended_tree | extended_tree_full | 0,1,2 | +0.021 | +0.021 | [-0.020, +0.063] | yes |
| tuned_v2_extended_random_forest | A1_celoe_extended_disc_hv1_n0 | 0,1,2 | -0.019 | -0.019 | [-0.043, +0.000] | yes |
| tuned_v2_extended_tree | A1_celoe_extended_disc_hv1_n0 | 0,1,2 | -0.072 | -0.072 | [-0.118, -0.035] | no |

## E4. Longer time limit (run after the freeze)

CELOE, strict KB, noise 0, 300 s, repeat 0 folds 0 to 4, 3 workers, compared with the stored 60 s results of the same folds (G1 and G3). With 3 workers sharing the machine, descriptions tested per second are lower than for a single run.

### G1 settings (hasValue on)

| fold | 60 s concept | 300 s concept | changed | train acc 60 / 300 | test F1 60 / 300 | tested 60 / 300 | final best first printed (s) 60 / 300 | algorithm s 300 run |
|---|---|---|---|---|---|---|---|---|
| 0 | `(not (GdpPerCapitaQ2)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | `(GdpPerCapitaQ3 or (isMember some ({org_ZC}))) and (encompassed some ({cont_Europe}))` | yes | 96.13 / 96.77 | 0.923 / 0.833 | 15159 / 109164 | 49.4 / 105.2 | 300.0 |
| 1 | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | `(GdpPerCapitaQ3 or (isMember some ({org_UNHCR}))) and (encompassed some ({cont_Europe}))` | yes | 96.13 / 96.77 | 0.923 / 0.857 | 13552 / 109429 | 38.5 / 90.6 | 300.0 |
| 2 | `(GdpPerCapitaQ3 or (not (GdpQ2))) and (encompassed some ({cont_Europe}))` | `(PopulationQ2 or (isMember some ({org_BIS}))) and (encompassed some ({cont_Europe}))` | yes | 97.42 / 98.06 | 0.667 / 0.714 | 17712 / 105576 | not printed as an improvement / 126.0 | 300.0 |
| 3 | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | no | 96.77 / 96.77 | 0.833 / 0.833 | 18527 / 116452 | 40.3 / 32.4 | 300.0 |
| 4 | `(PopulationGrowthQ1 or (speaks some ({lang_Arabic}))) and (encompassed some ({cont_Europe}))` | `(PopulationGrowthQ1 or (speaks some ({lang_Arabic}))) and (encompassed some ({cont_Europe}))` | no | 96.79 / 96.79 | 0.667 / 0.667 | 20700 / 119414 | 57.5 / 50.0 | 300.0 |

Pooled test F1 over the 5 folds of repeat 0: 60 s 0.806, 300 s 0.787; best concept changed in 3 of 5 folds.

### G3 settings (hasValue off)

| fold | 60 s concept | 300 s concept | changed | train acc 60 / 300 | test F1 60 / 300 | tested 60 / 300 | final best first printed (s) 60 / 300 | algorithm s 300 run |
|---|---|---|---|---|---|---|---|---|
| 0 | `(InfantMortalityQ1 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (not (PopulationQ1))` | `(InfantMortalityQ1 or PopulationGrowthQ1) and (PopulationGrowthQ2 or (neighbor some InflationQ1))` | yes | 90.97 / 92.26 | 0.588 / 0.615 | 26899 / 231980 | 36.0 / 119.4 | 300.0 |
| 1 | `(AreaQ2 and GdpQ3 and PopulationQ2) or (InfantMortalityQ1 and (not (PopulationQ1)))` | `(AreaQ2 and GdpQ3 and PopulationQ2) or (InfantMortalityQ1 and (not (PopulationQ1)))` | no | 88.39 / 88.39 | 0.667 / 0.667 | 42927 / 248020 | 58.7 / 47.6 | 300.0 |
| 2 | `(GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1)) or (GdpPerCapitaQ4 and (not (GdpQ2)))` | `(GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1)) or (GdpPerCapitaQ4 and (neighbor some Country))` | yes | 88.39 / 89.03 | 0.556 / 0.588 | 24363 / 197614 | 25.4 / 191.0 | 300.0 |
| 3 | `(GdpPerCapitaQ3 or GdpPerCapitaQ4) and (InflationQ1 or (AreaQ3 and PopulationGrowthQ1))` | `(GdpPerCapitaQ3 or GdpPerCapitaQ4) and (InflationQ1 or (AreaQ3 and PopulationGrowthQ1))` | no | 90.97 / 90.97 | 0.286 / 0.286 | 59490 / 229188 | 10.4 / 19.3 | 300.0 |
| 4 | `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (neighbor some (not (InfantMortalityQ3)))` | `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (neighbor some (not (InfantMortalityQ3)))` | no | 91.03 / 91.03 | 0.667 / 0.667 | 51864 / 225532 | 44.5 / 81.3 | 300.0 |

Pooled test F1 over the 5 folds of repeat 0: 60 s 0.548, 300 s 0.559; best concept changed in 2 of 5 folds.

### Grid table for the 300 s runs (5 folds of repeat 0 only)

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| E4a_celoe_strict_disc_hv1_n0_t300 | 5/15 | 0.933 | 0.721 | 0.887 | 0.781 | 0.787 [0.667, 0.895] | 9.0 | 112007 | 300.0 |
| E4b_celoe_strict_disc_hv0_n0_t300 | 5/15 | 0.846 | 0.490 | 0.707 | 0.565 | 0.559 [0.408, 0.690] | 9.8 | 226467 | 300.0 |

### E4a_celoe_strict_disc_hv1_n0_t300

- missing folds (no concept or scoring failure): [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
- algorithm time above 305 s: none
- algorithm time range: 300.0 to 300.0 s; wall range: 311.9 to 316.1 s
- three most frequent concepts:
  - 1x `(GdpPerCapitaQ3 or (isMember some ({org_ZC}))) and (encompassed some ({cont_Europe}))`
  - 1x `(GdpPerCapitaQ3 or (isMember some ({org_UNHCR}))) and (encompassed some ({cont_Europe}))`
  - 1x `(PopulationQ2 or (isMember some ({org_BIS}))) and (encompassed some ({cont_Europe}))`
- nearest reference (count): Europe and org_EBRD (2), Europe and org_EAPC (1), Europe and org_IOM (1), Europe and org_ICC (1)
- concept length min/median/max: 9/9/9; mean train accuracy 97.03; jaccard to nearest reference min/mean: 0.86/0.92

### E4b_celoe_strict_disc_hv0_n0_t300

- missing folds (no concept or scoring failure): [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
- algorithm time above 305 s: none
- algorithm time range: 300.0 to 300.0 s; wall range: 310.2 to 313.4 s
- three most frequent concepts:
  - 1x `(InfantMortalityQ1 or PopulationGrowthQ1) and (PopulationGrowthQ2 or (neighbor some InflationQ1))`
  - 1x `(AreaQ2 and GdpQ3 and PopulationQ2) or (InfantMortalityQ1 and (not (PopulationQ1)))`
  - 1x `(GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1)) or (GdpPerCapitaQ4 and (neighbor some Country))`
- nearest reference (count): Europe and org_IOC (3), org_AG (2)
- concept length min/median/max: 9/10/11; mean train accuracy 90.34; jaccard to nearest reference min/mean: 0.56/0.70


## Odd things

- E1: `majority_class` and `predict_all_positive` give identical predictions in every fold because the positives are the majority of the 41 countries (27 of 41); the test folds hold about 8 countries, so per-fold precision and recall are coarse. The `nearest_reference` columns in the E1 run CSVs use references restricted to the 41 countries, where `Europe` covers all of them.
- E1: specificity is the share of the 14 European negatives classified correctly, pooled per repeat and averaged over repeats; it is 0.000 for the two constant baselines by construction.
- E2: with 3 and 5 bins `n_airports` has fewer distinct bins than requested (3 classes for 3 bins and for the 4-bin reference, 4 classes for 5 bins); in the 5-bin KB `NAirportsQ2` has 0 countries because its interval (1, x] contains no integer. Atom names such as `InflationQ3` or `PopulationQ1` denote different intervals in each KB, so atoms are only comparable through the edges listed.
- E3: the tuned strict random forest has a lower pooled F1 than the untuned strict forest (paired difference in the table above). Ties between hyperparameter settings are broken by `GridSearchCV` in grid order.
- E4: the 'missing folds' lines in the per-config details of E4 list repeats 1 and 2 because only repeat 0 was run, as specified. All ten 300 s runs ended at exactly 300.0 algorithm seconds (wall 310 to 316 s).
- E4: for the stored G1 repeat 0 fold 2 run the final best concept does not appear as an improvement line in its 60 s log ('not printed as an improvement'); the cause was not investigated.
- Part A ran sequentially, one DL-Learner configuration at a time with 3 workers; the light report generation for E1 overlapped with the first minutes of E2, and E3 ran alone after the DL-Learner runs.

## Not done

- E1, E2 and E4: one run per configuration; no repeated runs to measure run-to-run variation (runs are time limited and not bit-reproducible).
- E1: only the three specified configurations (no OCEL, no noise, no other KB variants); baselines only with strict features.
- E2: bins 3 and 5 only for the strict KB with CELOE and hasValue on; no per-attribute bin choice; G1 was not rerun.
- E3: no paired bootstrap for the extended-feature tuned models and no other grids; tuned tree vs untuned tree was not compared.
- E4: repeat 0 only (5 folds); no 300 s runs for other configurations; the log-time column is missing where a concept was not printed as an improvement.
- Not investigated: the log mismatch in the stored G1 fold 2 run, and why `NAirportsQ2` is empty in the 5-bin KB beyond the edge arithmetic.
