# OWA vs CWA (CELOE, strict KB, discretised, hasValue on, noise 0, 60 s, Pellet via the OWL API reasoner); G1 is the reference row

Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats. Pooled F1: out-of-fold predictions of all folds of a repeat, mean over repeats; the interval is the 95% bootstrap (1000 resamples per repeat, bounds averaged over repeats). Concept length = number of names, constructors and numbers.

## Learned concepts

| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |
|---|---|---|---|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 15/15 | 0.940 ± 0.003 | 0.757 ± 0.033 | 0.922 ± 0.004 | 0.815 ± 0.011 | 0.811 [0.692, 0.910] | 8.7 | 14911 | 60.0 |
| O1_celoe_strict_disc_hv1_n0_pellet | 5/15 | 0.928 | 0.695 | 0.920 | 0.784 | 0.781 [0.656, 0.880] | 7.0 | 1099 | 60.4 |
| O2_celoe_strict_disc_hv1_n0_pellet_closure | 5/15 | 0.943 | 0.735 | 0.960 | 0.826 | 0.825 [0.710, 0.915] | 6.2 | 1272 | 61.1 |
| O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint | 5/15 | 0.412 | 0.195 | 1.000 | 0.325 | 0.321 [0.228, 0.409] | 2.0 | 80 | 74.8 |

## Baselines (same folds)

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

## Atom census

Share of the concepts (one per fold) that mention `cont_Europe`, that mention any organization (`isMember` or an `org_*` individual), and that use only numeric-bin classes (`...Q<n>`), `neighbor` and `hasAirport`; distinct atoms = distinct names excluding constructors.

| config | concepts | mention cont_Europe | mention an organization | only numeric-bin, neighbor, hasAirport | mean distinct atoms |
|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 15 | 1.00 | 0.07 | 0.00 | 4.1 |
| O1_celoe_strict_disc_hv1_n0_pellet | 5 | 1.00 | 0.40 | 0.00 | 4.0 |
| O2_celoe_strict_disc_hv1_n0_pellet_closure | 5 | 1.00 | 0.20 | 0.00 | 3.6 |
| O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint | 5 | 0.00 | 0.00 | 1.00 | 1.0 |

## Diagnostic run (not part of the grid)

Diagnostic, not part of the grid: the O3 configuration on repeat 0 fold 0 with a 600 s limit (`D1_celoe_strict_disc_hv1_n0_pellet_closure_disjoint_t600`).

- descriptions tested: 104; algorithm time 630.8 s; wall 639.8 s
- best concept: `not (GdpPerCapitaQ1)` (train accuracy 46.45%)
- test: accuracy 0.385, precision 0.200, recall 1.000, F1 0.333, TP/FP/FN/TN 6/24/0/9, FP [AUS BY C CK CO DOM DZ GE GUY HN IRQ JOR LAR MAL MC MH NU PA PAL RC TN TT UAE USA], FN []
- Europe alone was not printed within the limit
- timeline of improvements (seconds, training accuracy %, concept):
  - 0.2 s, 13.55%, `Thing`
  - 1.5 s, 46.45%, `not (GdpPerCapitaQ1)`

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

### O1_celoe_strict_disc_hv1_n0_pellet

- missing folds (no concept or scoring failure): [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
- algorithm time above 65 s: none
- algorithm time range: 60.0 to 61.4 s; wall range: 68.9 to 85.5 s
- three most frequent concepts:
  - 3x `(encompassed some ({cont_Europe})) and (follows some ({rel_Protestant}))`
  - 1x `(encompassed some ({cont_Europe})) and (isMember some ({org_ITUC}))`
  - 1x `(encompassed some ({cont_Europe})) and (isMember some ({org_CD}))`
- nearest reference (count): Europe and org_IOC (3), Europe and org_ITUC (1), Europe and org_CD (1)
- concept length min/median/max: 7/7/7; mean train accuracy 94.33; jaccard to nearest reference min/mean: 1.00/1.00

### O2_celoe_strict_disc_hv1_n0_pellet_closure

- missing folds (no concept or scoring failure): [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
- algorithm time above 65 s: none
- algorithm time range: 60.6 to 61.7 s; wall range: 67.2 to 89.1 s
- three most frequent concepts:
  - 3x `(encompassed some ({cont_Europe})) and (hasAirport some Airport)`
  - 1x `encompassed some ({cont_Europe})`
  - 1x `(encompassed some ({cont_Europe})) and (isMember some ({org_CD}))`
- nearest reference (count): Europe and org_EBRD (3), Europe (1), Europe and org_CD (1)
- concept length min/median/max: 3/7/7; mean train accuracy 94.84; jaccard to nearest reference min/mean: 0.97/0.98

### O3_celoe_strict_disc_hv1_n0_pellet_closure_disjoint

- missing folds (no concept or scoring failure): [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]
- algorithm time above 65 s: [(0, 0, 82.908), (0, 1, 84.879), (0, 2, 84.937)]
- algorithm time range: 60.3 to 84.9 s; wall range: 67.6 to 95.4 s
- three most frequent concepts:
  - 3x `not (GdpPerCapitaQ1)`
  - 2x `not (InflationQ4)`
- nearest reference (count): org_IOC (3), org_IFRCS (2)
- concept length min/median/max: 2/2/2; mean train accuracy 45.49; jaccard to nearest reference min/mean: 0.69/0.70

