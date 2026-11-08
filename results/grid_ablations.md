# Ablations (CELOE, hasValue on, noise 0, 60 s, 3 workers, repeats 0 to 2); G1 is the reference row

Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats. Pooled F1: out-of-fold predictions of all folds of a repeat, mean over repeats; the interval is the 95% bootstrap (1000 resamples per repeat, bounds averaged over repeats). Concept length = number of names, constructors and numbers.

## Learned concepts

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 15/15 | 0.940 ± 0.003 | 0.757 ± 0.033 | 0.922 ± 0.004 | 0.815 ± 0.011 | 0.811 [0.692, 0.910] | 8.7 | 14911 | 60.0 |
| A1_celoe_extended_disc_hv1_n0 | 15/15 | 0.979 ± 0.000 | 0.888 ± 0.004 | 1.000 ± 0.000 | 0.936 ± 0.002 | 0.931 [0.853, 0.985] | 7.0 | 17874 | 60.0 |
| A2_celoe_masked_disc_hv1_n0 | 15/15 | 0.979 ± 0.000 | 0.888 ± 0.004 | 1.000 ± 0.000 | 0.936 ± 0.002 | 0.931 [0.853, 0.985] | 7.4 | 16111 | 60.0 |
| A3_celoe_none_disc_hv1_n0 | 15/15 | 0.945 ± 0.008 | 0.770 ± 0.031 | 0.933 ± 0.023 | 0.827 ± 0.027 | 0.826 [0.712, 0.920] | 8.8 | 14876 | 60.0 |
| A4_celoe_strict_dt_hv1_n0 | 15/15 | 0.952 ± 0.003 | 0.773 ± 0.021 | 0.987 ± 0.023 | 0.860 ± 0.017 | 0.851 [0.748, 0.937] | 8.5 | 19695 | 60.0 |

## Baselines (same folds)

The rule rows use the full unmasked `isMember` data; they are rules, not learned models.

| model | accuracy | precision | recall | F1 | pooled F1 [95% CI] |
|---|---|---|---|---|---|
| reference: majority_class | 0.861 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 [0.000, 0.000] |
| reference: rule_europe | 0.928 ± 0.000 | 0.680 ± 0.014 | 1.000 ± 0.000 | 0.803 ± 0.006 | 0.794 [0.674, 0.890] |
| reference: rule_AG | 0.938 ± 0.000 | 0.712 ± 0.017 | 1.000 ± 0.000 | 0.825 ± 0.006 | 0.818 [0.702, 0.906] |
| reference: rule_NSG | 0.907 ± 0.000 | 0.620 ± 0.016 | 1.000 ± 0.000 | 0.759 ± 0.008 | 0.750 [0.625, 0.848] |
| masked: tree_depth3 | 0.959 ± 0.014 | 0.867 ± 0.088 | 0.840 ± 0.055 | 0.839 ± 0.053 | 0.851 [0.733, 0.939] |
| masked: tree_full | 0.959 ± 0.010 | 0.875 ± 0.080 | 0.829 ± 0.054 | 0.838 ± 0.046 | 0.848 [0.730, 0.940] |
| masked: random_forest | 0.971 ± 0.003 | 0.886 ± 0.000 | 0.940 ± 0.018 | 0.903 ± 0.010 | 0.899 [0.802, 0.970] |
| extended: tree_depth3 | 0.959 ± 0.005 | 0.835 ± 0.029 | 0.884 ± 0.073 | 0.849 ± 0.037 | 0.856 [0.749, 0.941] |
| extended: tree_full | 0.954 ± 0.005 | 0.830 ± 0.034 | 0.862 ± 0.054 | 0.834 ± 0.027 | 0.838 [0.724, 0.928] |
| extended: random_forest | 0.976 ± 0.003 | 0.888 ± 0.004 | 0.976 ± 0.021 | 0.922 ± 0.013 | 0.919 [0.831, 0.982] |
| none: tree_depth3 | 0.942 ± 0.006 | 0.802 ± 0.021 | 0.836 ± 0.093 | 0.791 ± 0.046 | 0.799 [0.670, 0.899] |
| none: tree_full | 0.938 ± 0.009 | 0.798 ± 0.022 | 0.822 ± 0.091 | 0.781 ± 0.051 | 0.787 [0.655, 0.894] |
| none: random_forest | 0.954 ± 0.009 | 0.898 ± 0.017 | 0.791 ± 0.051 | 0.823 ± 0.037 | 0.825 [0.695, 0.924] |
| strict: tree_depth3 | 0.942 ± 0.008 | 0.797 ± 0.033 | 0.847 ± 0.110 | 0.792 ± 0.054 | 0.800 [0.670, 0.902] |
| strict: tree_full | 0.943 ± 0.005 | 0.802 ± 0.032 | 0.844 ± 0.073 | 0.799 ± 0.036 | 0.806 [0.679, 0.905] |
| strict: random_forest | 0.964 ± 0.005 | 0.898 ± 0.012 | 0.869 ± 0.015 | 0.872 ± 0.016 | 0.870 [0.753, 0.952] |

## Atom census

Share of the concepts (one per fold) that mention `cont_Europe`, that mention any organization (`isMember` or an `org_*` individual), and that use only numeric-bin classes (`...Q<n>`), `neighbor` and `hasAirport`; distinct atoms = distinct names excluding constructors.

| config | concepts | mention cont_Europe | mention an organization | only numeric-bin, neighbor, hasAirport | mean distinct atoms |
|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 15 | 1.00 | 0.07 | 0.00 | 4.1 |
| A1_celoe_extended_disc_hv1_n0 | 15 | 1.00 | 1.00 | 0.00 | 4.0 |
| A2_celoe_masked_disc_hv1_n0 | 15 | 1.00 | 1.00 | 0.00 | 4.1 |
| A3_celoe_none_disc_hv1_n0 | 15 | 1.00 | 0.00 | 0.00 | 4.1 |
| A4_celoe_strict_dt_hv1_n0 | 15 | 1.00 | 0.07 | 0.00 | 4.3 |

## Per-config details

### G1_celoe_strict_disc_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 68.0 to 72.7 s
- three most frequent concepts:
  - 8x `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 2x `(not (GdpPerCapitaQ2)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 1x `(GdpPerCapitaQ3 or (not (GdpQ2))) and (encompassed some ({cont_Europe}))`
- nearest reference (count): Europe and org_EBRD (8), Europe and org_NSG (2), Europe and org_ICC (2), Europe and org_IOM (1), Europe and org_ISO (1), Europe and org_CD (1)
- concept length min/median/max: 7/9/9; mean train accuracy 96.65; jaccard to nearest reference min/mean: 0.84/0.93

### A1_celoe_extended_disc_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 67.8 to 74.1 s
- three most frequent concepts:
  - 15x `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))`
- nearest reference (count): Europe and org_AG (15)
- concept length min/median/max: 7/7/7; mean train accuracy 97.94; jaccard to nearest reference min/mean: 1.00/1.00

### A2_celoe_masked_disc_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 70.8 to 72.8 s
- three most frequent concepts:
  - 13x `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))`
  - 1x `(not (InfantMortalityQ4)) and (encompassed some ({cont_Europe})) and (isMember some ({org_AG}))`
  - 1x `(not (InflationQ4)) and (encompassed some ({cont_Europe})) and (isMember some ({org_AG}))`
- nearest reference (count): Europe and org_AG (15)
- concept length min/median/max: 7/7/10; mean train accuracy 97.94; jaccard to nearest reference min/mean: 1.00/1.00

### A3_celoe_none_disc_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 68.1 to 72.7 s
- three most frequent concepts:
  - 9x `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 2x `(not (GdpPerCapitaQ2)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 1x `(GdpPerCapitaQ3 or (not (GdpQ2))) and (encompassed some ({cont_Europe}))`
- nearest reference (count): Europe and org_EBRD (9), Europe and org_NSG (2), Europe and org_ICC (2), Europe and org_IOM (1), Europe and org_ISO (1)
- concept length min/median/max: 7/9/9; mean train accuracy 96.65; jaccard to nearest reference min/mean: 0.84/0.92

### A4_celoe_strict_dt_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.1 s; wall range: 71.1 to 74.1 s
- three most frequent concepts:
  - 10x `(encompassed some ({cont_Europe})) and (population some double[>= "389830.5"^^double])`
  - 2x `(encompassed some ({cont_Europe})) and (gdp some double[>= "7502.0"^^double])`
  - 1x `(encompassed some ({cont_Europe})) and (follows some ({rel_Protestant})) and (population some double[>= "389830.5"^^double])`
- nearest reference (count): Europe and org_EBRD (11), Europe and org_ISO (4)
- concept length min/median/max: 8/8/12; mean train accuracy 96.05; jaccard to nearest reference min/mean: 0.94/0.96

