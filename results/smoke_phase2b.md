# Phase 2B smoke runs

Repeat 0, fold 0, time limit 60 s, KB `mondial_extended_discretised.owl`, closed world reasoner. Test fold: 6 positives, 33 negatives. Test scores come from `scripts/score_concept.py` (same ClosedWorldReasoner as training). Concept length = number of names, constructors and numbers (parentheses not counted).

## celoe_hv0_noise0

- DL-Learner algorithm time: 60s 4ms; descriptions tested: 24387; wall clock including JVM start-up: 67.8 s


| # | concept | length | train acc % | test acc | test P | test R | test F1 | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `(InfantMortalityQ1 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (not (PopulationQ1))` | 8 | 90,97 | 0.821 | 0.455 | 0.833 | 0.588 | AUS, BY, C, RC, TT, USA | CY |
| 2 | `InfantMortalityQ1 or (PopulationGrowthQ1 and (neighbor min 2 PopulationGrowthQ1))` | 8 | 90,32 | 0.795 | 0.417 | 0.833 | 0.556 | AUS, BY, C, GE, MC, RC, USA | CY |
| 3 | `InfantMortalityQ1 or (PopulationGrowthQ1 and (neighbor min 2 InfantMortalityQ2))` | 8 | 90,32 | 0.795 | 0.417 | 0.833 | 0.556 | AUS, BY, C, GE, MC, RC, USA | CY |

- Best concept atoms: GdpPerCapitaQ3, InfantMortalityQ1, PopulationGrowthQ1, PopulationQ1
- Extension of the best concept over the 194 labelled countries: 46 predicted positives; closest reference `org_NSG` (Jaccard 0.709); identical to: none

## celoe_hv1_noise0

- DL-Learner algorithm time: 60s 0ms; descriptions tested: 25642; wall clock including JVM start-up: 65.7 s


| # | concept | length | train acc % | test acc | test P | test R | test F1 | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 7 | 97,42 | 1.000 | 1.000 | 1.000 | 1.000 | - | - |
| 2 | `(not (InfantMortalityQ4)) and (encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 10 | 97,42 | 1.000 | 1.000 | 1.000 | 1.000 | - | - |
| 3 | `(not (GdpPerCapitaQ1)) and (encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 10 | 97,42 | 1.000 | 1.000 | 1.000 | 1.000 | - | - |

- Best concept atoms: cont_Europe, encompassed, isMember, org_AG
- Extension of the best concept over the 194 labelled countries: 31 predicted positives; closest reference `Europe and org_AG` (Jaccard 0.939); identical to: Europe and org_AG

## celoe_hv0_noise10

- DL-Learner algorithm time: 60s 1ms; descriptions tested: 16876; wall clock including JVM start-up: 67.4 s


| # | concept | length | train acc % | test acc | test P | test R | test F1 | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (neighbor some PopulationGrowthQ1)` | 9 | 94,84 | 0.923 | 0.800 | 0.667 | 0.727 | BY | CY, IRL |
| 2 | `(InfantMortalityQ1 or (GdpPerCapitaQ3 and PopulationGrowthQ1)) and (neighbor some PopulationGrowthQ1)` | 9 | 94,19 | 0.923 | 0.800 | 0.667 | 0.727 | BY | CY, IRL |
| 3 | `(InfantMortalityQ1 or PopulationGrowthQ1) and (neighbor some PopulationGrowthQ1)` | 7 | 93,55 | 0.897 | 0.667 | 0.667 | 0.667 | BY, GE | CY, IRL |

- Best concept atoms: GdpPerCapitaQ3, GdpPerCapitaQ4, PopulationGrowthQ1, neighbor
- Extension of the best concept over the 194 labelled countries: 30 predicted positives; closest reference `Europe and org_BIS` (Jaccard 0.684); identical to: none

## ocel_hv0_noise0

- DL-Learner algorithm time: >= 60s (limit reached); descriptions tested: 95293; wall clock including JVM start-up: 67.7 s

- no solutions list printed (terminateOnNoiseReached with noise 0); best expression found so far is scored

| # | concept | length | train acc % | test acc | test P | test R | test F1 | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| best | `((AreaQ1 and PopulationQ2 and (not (InfantMortalityQ2))) or (neighbor some (neighbor min 2 InfantMortalityQ1))) and (not (GdpPerCapitaQ1)) and (not (GdpPerCapitaQ2)) and (hasAirport some Thing)` | 23 | 96,77 | 0.923 | 0.800 | 0.667 | 0.727 | BY | CY, IRL |

- Best concept atoms: AreaQ1, GdpPerCapitaQ1, GdpPerCapitaQ2, InfantMortalityQ1, InfantMortalityQ2, PopulationQ2, hasAirport, neighbor
- Extension of the best concept over the 194 labelled countries: 31 predicted positives; closest reference `Europe and org_NSG` (Jaccard 0.789); identical to: none
