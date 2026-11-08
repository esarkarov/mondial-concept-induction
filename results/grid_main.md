# Main grid (strict KB, discretised, 60 s, 3 workers, repeats 0 to 2)

Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats. Pooled F1: out-of-fold predictions of all folds of a repeat, mean over repeats; the interval is the 95% bootstrap (1000 resamples per repeat, bounds averaged over repeats). Concept length = number of names, constructors and numbers.

## Learned concepts

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 15/15 | 0.940 ± 0.003 | 0.757 ± 0.033 | 0.922 ± 0.004 | 0.815 ± 0.011 | 0.811 [0.692, 0.910] | 8.7 | 14911 | 60.0 |
| G2_celoe_strict_disc_hv1_n10 | 15/15 | 0.928 ± 0.009 | 0.731 ± 0.021 | 0.847 ± 0.033 | 0.759 ± 0.038 | 0.767 [0.635, 0.872] | 7.8 | 16489 | 60.0 |
| G3_celoe_strict_disc_hv0_n0 | 15/15 | 0.851 ± 0.018 | 0.487 ± 0.025 | 0.827 ± 0.079 | 0.607 ± 0.048 | 0.606 [0.471, 0.727] | 9.5 | 35834 | 60.0 |
| G4_celoe_strict_disc_hv0_n10 | 15/15 | 0.904 ± 0.011 | 0.667 ± 0.052 | 0.800 ± 0.018 | 0.705 ± 0.030 | 0.699 [0.550, 0.814] | 9.7 | 31141 | 60.0 |
| G5_ocel_strict_disc_hv1_n0 | 15/15 | 0.921 ± 0.008 | 0.714 ± 0.004 | 0.809 ± 0.067 | 0.735 ± 0.047 | 0.741 [0.596, 0.859] | 11.0 | 111145 | 60.0 |
| G6_ocel_strict_disc_hv1_n10 | 15/15 | 0.924 ± 0.011 | 0.827 ± 0.049 | 0.627 ± 0.033 | 0.685 ± 0.052 | 0.699 [0.533, 0.832] | 8.4 | 118435 | 60.0 |
| G7_ocel_strict_disc_hv0_n0 | 15/15 | 0.904 ± 0.025 | 0.663 ± 0.084 | 0.731 ± 0.106 | 0.679 ± 0.081 | 0.678 [0.526, 0.804] | 23.7 | 107354 | 60.0 |
| G8_ocel_strict_disc_hv0_n10 | 15/15 | 0.919 ± 0.026 | 0.796 ± 0.163 | 0.604 ± 0.074 | 0.670 ± 0.103 | 0.678 [0.504, 0.814] | 10.3 | 169757 | 60.0 |

## Baselines on the strict variant (same folds)

The rule rows use the full unmasked `isMember` data; they are rules, not learned models.

| model | accuracy | precision | recall | F1 | pooled F1 [95% CI] |
|---|---|---|---|---|---|
| reference: majority_class | 0.861 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 [0.000, 0.000] |
| reference: rule_europe | 0.928 ± 0.000 | 0.680 ± 0.014 | 1.000 ± 0.000 | 0.803 ± 0.006 | 0.794 [0.674, 0.890] |
| reference: rule_AG | 0.938 ± 0.000 | 0.712 ± 0.017 | 1.000 ± 0.000 | 0.825 ± 0.006 | 0.818 [0.702, 0.906] |
| reference: rule_NSG | 0.907 ± 0.000 | 0.620 ± 0.016 | 1.000 ± 0.000 | 0.759 ± 0.008 | 0.750 [0.625, 0.848] |
| strict: tree_depth3 | 0.942 ± 0.008 | 0.797 ± 0.033 | 0.847 ± 0.110 | 0.792 ± 0.054 | 0.800 [0.670, 0.902] |
| strict: tree_full | 0.943 ± 0.005 | 0.802 ± 0.032 | 0.844 ± 0.073 | 0.799 ± 0.036 | 0.806 [0.679, 0.905] |
| strict: random_forest | 0.964 ± 0.005 | 0.898 ± 0.012 | 0.869 ± 0.015 | 0.872 ± 0.016 | 0.870 [0.753, 0.952] |

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

### G2_celoe_strict_disc_hv1_n10

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 67.3 to 73.2 s
- three most frequent concepts:
  - 3x `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 3x `(InflationQ1 or PopulationGrowthQ1) and (encompassed some ({cont_Europe}))`
  - 2x `(encompassed some ({cont_Europe})) and (isMember some ({org_BIS}))`
- nearest reference (count): Europe and org_ICC (4), Europe and org_EBRD (3), Europe and org_ISO (2), Europe and org_BIS (2), Europe and org_MIGA (2), Europe and org_WMO (1), Europe and org_NSG (1)
- concept length min/median/max: 7/7/10; mean train accuracy 96.48; jaccard to nearest reference min/mean: 0.71/0.90

### G3_celoe_strict_disc_hv0_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 68.9 to 73.4 s
- three most frequent concepts:
  - 4x `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1))) and (not (PopulationQ1))`
  - 1x `(InfantMortalityQ1 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (not (PopulationQ1))`
  - 1x `(AreaQ2 and GdpQ3 and PopulationQ2) or (InfantMortalityQ1 and (not (PopulationQ1)))`
- nearest reference (count): org_NSG (9), org_AG (3), Europe and org_IOC (2), org_CE (1)
- concept length min/median/max: 8/10/10; mean train accuracy 89.48; jaccard to nearest reference min/mean: 0.56/0.70

### G4_celoe_strict_disc_hv0_n10

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 69.4 to 73.4 s
- three most frequent concepts:
  - 4x `(GdpPerCapitaQ4 or PopulationGrowthQ1) and (neighbor some (PopulationGrowthQ1 or PopulationQ1))`
  - 3x `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (neighbor some PopulationGrowthQ1)`
  - 1x `(not (GdpPerCapitaQ2)) and (neighbor some (neighbor some (AreaQ3 and InfantMortalityQ1)))`
- nearest reference (count): Europe and org_ILO (4), Europe and org_PCA (3), Europe and org_IOC (2), Europe and org_IFRCS (1), Europe and org_EBRD (1), Europe and org_ICC (1), org_CE (1), Europe and org_BIS (1), Europe and org_ITUC (1)
- concept length min/median/max: 9/9/11; mean train accuracy 93.56; jaccard to nearest reference min/mean: 0.71/0.77

### G5_ocel_strict_disc_hv1_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 70.0 to 74.3 s
- three most frequent concepts:
  - 2x `(GdpPerCapitaQ3 or (isMember some ({org_ZC}))) and (not (InflationQ4)) and (encompassed some ({cont_Europe}))`
  - 2x `(InflationQ1 or PopulationGrowthQ1) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 1x `(GdpPerCapitaQ3 or (isMember some ({org_UNHCR}))) and (not (InflationQ4)) and (encompassed some ({cont_Europe}))`
- nearest reference (count): Europe and org_AG (6), Europe and org_EBRD (4), Europe and org_ICC (2), Europe and org_ISO (1), Europe and org_EIB (1), Europe and org_MIGA (1)
- concept length min/median/max: 9/11/13; mean train accuracy 97.89; jaccard to nearest reference min/mean: 0.84/0.89

### G6_ocel_strict_disc_hv1_n10

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 66.2 to 74.6 s
- three most frequent concepts:
  - 5x `PopulationGrowthQ1 and (isMember some ({org_BIS})) and (neighbor some InflationQ1)`
  - 4x `InflationQ1 and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`
  - 2x `PopulationGrowthQ1 and (not (AreaQ4)) and (isMember some ({org_BIS}))`
- nearest reference (count): Europe and org_EIB (14), Europe and org_ICCt (1)
- concept length min/median/max: 8/8/9; mean train accuracy 95.53; jaccard to nearest reference min/mean: 0.60/0.64

### G7_ocel_strict_disc_hv0_n0

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 68.0 to 74.6 s
- three most frequent concepts:
  - 2x `(not (GdpPerCapitaQ2)) and (not (InflationQ4)) and (hasAirport some Thing) and (neighbor some ((not (GdpPerCapitaQ1)) and (neighbor some (GdpPerCapitaQ4 and (PopulationGrowthQ1 or (NAirportsQ2 and PopulationGrowthQ3))))))`
  - 1x `((AreaQ1 and PopulationQ2 and (not (InfantMortalityQ2))) or (neighbor some (neighbor min 2 InfantMortalityQ1))) and (not (GdpPerCapitaQ1)) and (not (GdpPerCapitaQ2)) and (hasAirport some Thing)`
  - 1x `((AreaQ1 and InflationQ1) or (neighbor some (neighbor some (GdpPerCapitaQ4 and (PopulationGrowthQ1 or (NAirportsQ2 and PopulationGrowthQ3)))))) and (not (GdpPerCapitaQ1)) and (not (GdpPerCapitaQ2)) and (not (PopulationQ1))`
- nearest reference (count): Europe and org_AG (6), Europe and org_NSG (4), Europe and org_EAPC (2), org_AG (2), Europe and org_CE (1)
- concept length min/median/max: 21/24/27; mean train accuracy 96.82; jaccard to nearest reference min/mean: 0.72/0.79

### G8_ocel_strict_disc_hv0_n10

- missing folds (no concept or scoring failure): none
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 60.0 s; wall range: 68.5 to 69.9 s
- three most frequent concepts:
  - 4x `PopulationGrowthQ1 and (not (InflationQ4)) and (hasAirport some Thing) and (neighbor some InflationQ1)`
  - 3x `PopulationGrowthQ1 and (not (InflationQ4)) and (neighbor some InflationQ1)`
  - 1x `InfantMortalityQ1 and (GdpPerCapitaQ3 or (neighbor min 2 (InflationQ2 or PopulationGrowthQ1)))`
- nearest reference (count): Europe and org_EIB (11), Europe and org_AG (2), Europe and org_EAPC (1), Europe and org_PCA (1)
- concept length min/median/max: 8/11/13; mean train accuracy 95.70; jaccard to nearest reference min/mean: 0.60/0.65

