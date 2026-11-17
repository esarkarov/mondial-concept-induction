# Phase 4: analysis of frozen results

Built from `results/predictions.csv`, `results/runs/*.csv`, `kb/bins.json` and the Phase 1 to 3 data; nothing from Phases 1 to 3 was changed. CSVs are in `results/analysis/`.

## 1. Error profile (3 repeats, 194 labelled countries)

Misclassified-repeat counts per country (0 to 3) are in `results/analysis/error_profile.csv`. The 14 European negatives are the labelled negatives with a `Europe` row in `encompasses` (14 found): Andorra, Bosnia and Herzegovina, Belarus, Switzerland, Liechtenstein, United Kingdom, Iceland, Kosovo, Kazakhstan, Monaco, Norway, Russia, San Marino, Vatican City.

| model | wrong in 3/3 repeats | false positives (3/3) | false negatives (3/3) | European negatives right per repeat (of 14) | European negatives right in 3/3 repeats |
|---|---|---|---|---|---|
| G1_celoe_strict_disc_hv1_n0 | 7 | Bosnia and Herzegovina; Switzerland; United Kingdom; Iceland; Kazakhstan; Norway; Russia | none | 4 / 5 / 4 | 1 |
| A1_celoe_extended_disc_hv1_n0 | 4 | Switzerland; United Kingdom; Iceland; Norway | none | 10 / 10 / 10 | 10 |
| strict_random_forest | 5 | Switzerland; United Kingdom; Norway | Cyprus; Malta | 11 / 10 / 11 | 10 |
| strict_tree_full | 3 | United Kingdom; Iceland; San Marino | none | 8 / 7 / 6 | 3 |
| rule_europe | 14 | Andorra; Bosnia and Herzegovina; Belarus; Switzerland; Liechtenstein; United Kingdom; Iceland; Kosovo; Kazakhstan; Monaco; Norway; Russia; San Marino; Vatican City | none | 0 / 0 / 0 | 0 |

## 2. Excluded countries (7 EU candidates, 45 dependent territories)

Most frequent concept of G1 (strict KB) and A1 (extended KB), evaluated with the closed world reasoner; no labels used.

### G1 (strict KB): `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))`

- EU candidates predicted positive: 6 of 7: Albania, Moldova, North Macedonia, Montenegro, Serbia, Ukraine
- candidates not predicted positive: Turkey
- dependent territories predicted positive: 0 of 45

No dependent territory is predicted positive, so there is no dependency table for this concept.

### A1 (extended KB): `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))`

- EU candidates predicted positive: 2 of 7: Turkey, Ukraine
- candidates not predicted positive: Albania, Moldova, North Macedonia, Montenegro, Serbia
- dependent territories predicted positive: 0 of 45

No dependent territory is predicted positive, so there is no dependency table for this concept.


## 3. Concepts fitted on all labelled countries (presentation only)

Fitted on all 194 labelled countries (27 positives, 167 negatives), CELOE, noise 0, 60 s, one run each. **For presentation only: training accuracy on the data the concept was fitted to, not an estimate of performance.**

| run | settings | concept | training accuracy % | length | tested | algorithm s |
|---|---|---|---|---|---|---|
| F1 | G1 settings: strict KB, hasValue on | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | 96.39 | 9 | 30490 | 60.0 |
| F2 | A1 settings: extended KB, hasValue on | `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 97.94 | 7 | 23186 | 60.009 |
| F3 | G3 settings: strict KB, hasValue off | `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1))) and (not (PopulationQ1))` | 87.63 | 10 | 30789 | 60.002 |

## 4. Concept inventory (most frequent concept per config, counts out of 15 folds)

The reading is generated from the atoms of the concept only. Bin atoms `XQn` depend on the quartile edges listed below.

| config | count | concept | length | mean train acc % | reading (atoms only) | discretisation-dependent atoms |
|---|---|---|---|---|---|---|
| G1 | 8/15 | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | 9 | 96.62 | not (InflationQ4 [inflation > 5.8]) and not (PopulationQ1 [population <= 276394]) and encompassed includes cont_Europe | InflationQ4, PopulationQ1 |
| G2 | 3/15 (tied with 1 other) | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | 9 | 96.77 | not (InflationQ4 [inflation > 5.8]) and not (PopulationQ1 [population <= 276394]) and encompassed includes cont_Europe | InflationQ4, PopulationQ1 |
| G3 | 4/15 | `(GdpPerCapitaQ4 or (GdpPerCapitaQ3 and (InfantMortalityQ1 or PopulationGrowthQ1))) and (not (PopulationQ1))` | 10 | 87.6 | (GdpPerCapitaQ4 [gdp_per_capita > 20465.1] or (GdpPerCapitaQ3 [6613.98 < gdp_per_capita <= 20465.1] and (InfantMortalityQ1 [infant_mortality <= 6.27] or PopulationGrowthQ1 [population_growth <= 0.3075]))) and not (PopulationQ1 [population <= 276394]) | GdpPerCapitaQ3, GdpPerCapitaQ4, InfantMortalityQ1, PopulationGrowthQ1, PopulationQ1 |
| G4 | 4/15 | `(GdpPerCapitaQ4 or PopulationGrowthQ1) and (neighbor some (PopulationGrowthQ1 or PopulationQ1))` | 9 | 93.4 | (GdpPerCapitaQ4 [gdp_per_capita > 20465.1] or PopulationGrowthQ1 [population_growth <= 0.3075]) and has a neighbor that is (PopulationGrowthQ1 [population_growth <= 0.3075] or PopulationQ1 [population <= 276394]) | GdpPerCapitaQ4, PopulationGrowthQ1, PopulationQ1 |
| G5 | 2/15 (tied with 1 other) | `(GdpPerCapitaQ3 or (isMember some ({org_ZC}))) and (not (InflationQ4)) and (encompassed some ({cont_Europe}))` | 12 | 98.38 | (GdpPerCapitaQ3 [6613.98 < gdp_per_capita <= 20465.1] or isMember includes org_ZC) and not (InflationQ4 [inflation > 5.8]) and encompassed includes cont_Europe | GdpPerCapitaQ3, InflationQ4 |
| G6 | 5/15 | `PopulationGrowthQ1 and (isMember some ({org_BIS})) and (neighbor some InflationQ1)` | 9 | 96.01 | PopulationGrowthQ1 [population_growth <= 0.3075] and isMember includes org_BIS and has a neighbor that is InflationQ1 [inflation <= 1.8] | InflationQ1, PopulationGrowthQ1 |
| G7 | 2/15 | `(not (GdpPerCapitaQ2)) and (not (InflationQ4)) and (hasAirport some Thing) and (neighbor some ((not (GdpPerCapitaQ1)) and (neighbor some (GdpPerCapitaQ4 and (PopulationGrowthQ1 or (NAirportsQ2 and PopulationGrowthQ3))))))` | 24 | 97.1 | not (GdpPerCapitaQ2 [2228.14 < gdp_per_capita <= 6613.98]) and not (InflationQ4 [inflation > 5.8]) and has some hasAirport and has a neighbor that is (not (GdpPerCapitaQ1 [gdp_per_capita <= 2228.14]) and has a neighbor that is (GdpPerCapitaQ4 [gdp_per_capita > 20465.1] and (PopulationGrowthQ1 [population_growth <= 0.3075] or (NAirportsQ2 [1 < n_airports <= 4] and PopulationGrowthQ3 [1.08 < population_growth <= 1.9275])))) | GdpPerCapitaQ1, GdpPerCapitaQ2, GdpPerCapitaQ4, InflationQ4, NAirportsQ2, PopulationGrowthQ1, PopulationGrowthQ3 |
| G8 | 4/15 | `PopulationGrowthQ1 and (not (InflationQ4)) and (hasAirport some Thing) and (neighbor some InflationQ1)` | 12 | 95.81 | PopulationGrowthQ1 [population_growth <= 0.3075] and not (InflationQ4 [inflation > 5.8]) and has some hasAirport and has a neighbor that is InflationQ1 [inflation <= 1.8] | InflationQ1, InflationQ4, PopulationGrowthQ1 |
| A1 | 15/15 | `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 7 | 97.94 | encompassed includes cont_Europe and isMember includes org_AG | none |
| A2 | 13/15 | `(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))` | 7 | 97.92 | encompassed includes cont_Europe and isMember includes org_AG | none |
| A3 | 9/15 | `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` | 9 | 96.63 | not (InflationQ4 [inflation > 5.8]) and not (PopulationQ1 [population <= 276394]) and encompassed includes cont_Europe | InflationQ4, PopulationQ1 |
| A4 | 10/15 | `(encompassed some ({cont_Europe})) and (population some double[>= "389830.5"^^double])` | 8 | 95.68 | encompassed includes cont_Europe and population [>= 389830.5] | population >= "389830.5"^^double |

### Edges of the bin atoms used above (`kb/bins.json`; bins are lower-exclusive, upper-inclusive, quartiles over all 246 countries)

**GdpPerCapitaQ1**: lower_exclusive None, upper_inclusive 2228.136342984535, 59 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 2228.136342984535 | inside | Papua New Guinea | 2212.96 | negative |
| 2228.136342984535 | inside | Yemen | 1789.46 | negative |
| 2228.136342984535 | inside | Nicaragua | 1779.41 | negative |
| 2228.136342984535 | outside | Honduras | 2273.67 | negative |
| 2228.136342984535 | outside | Moldova | 2283.31 | candidate |
| 2228.136342984535 | outside | Philippines | 2496.44 | negative |

**GdpPerCapitaQ2**: lower_exclusive 2228.136342984535, upper_inclusive 6613.978837036402, 58 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 2228.136342984535 | outside | Papua New Guinea | 2212.96 | negative |
| 2228.136342984535 | outside | Yemen | 1789.46 | negative |
| 2228.136342984535 | outside | Nicaragua | 1779.41 | negative |
| 2228.136342984535 | inside | Honduras | 2273.67 | negative |
| 2228.136342984535 | inside | Moldova | 2283.31 | candidate |
| 2228.136342984535 | inside | Philippines | 2496.44 | negative |
| 6613.978837036402 | inside | China | 6608.68 | negative |
| 6613.978837036402 | inside | Serbia | 6528.28 | candidate |
| 6613.978837036402 | inside | Cuba | 6474.25 | negative |
| 6613.978837036402 | outside | Botswana | 6619.27 | negative |
| 6613.978837036402 | outside | Turkmenistan | 6725.04 | negative |
| 6613.978837036402 | outside | Peru | 6732.32 | negative |

**GdpPerCapitaQ3**: lower_exclusive 6613.978837036402, upper_inclusive 20465.0548477869, 58 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 6613.978837036402 | outside | China | 6608.68 | negative |
| 6613.978837036402 | outside | Serbia | 6528.28 | candidate |
| 6613.978837036402 | outside | Cuba | 6474.25 | negative |
| 6613.978837036402 | inside | Botswana | 6619.27 | negative |
| 6613.978837036402 | inside | Turkmenistan | 6725.04 | negative |
| 6613.978837036402 | inside | Peru | 6732.32 | negative |
| 20465.0548477869 | inside | Trinidad and Tobago | 20428.9 | negative |
| 20465.0548477869 | inside | Bahrain | 18886.1 | negative |
| 20465.0548477869 | inside | Czech Republic | 18509.8 | positive |
| 20465.0548477869 | outside | French Polynesia | 20477.1 | dependent |
| 20465.0548477869 | outside | Taiwan | 20563.2 | negative |
| 20465.0548477869 | outside | Sint Maarten | 20778.1 | dependent |

**GdpPerCapitaQ4**: lower_exclusive 20465.0548477869, upper_inclusive None, 59 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 20465.0548477869 | outside | Trinidad and Tobago | 20428.9 | negative |
| 20465.0548477869 | outside | Bahrain | 18886.1 | negative |
| 20465.0548477869 | outside | Czech Republic | 18509.8 | positive |
| 20465.0548477869 | inside | French Polynesia | 20477.1 | dependent |
| 20465.0548477869 | inside | Taiwan | 20563.2 | negative |
| 20465.0548477869 | inside | Sint Maarten | 20778.1 | dependent |

**InfantMortalityQ1**: lower_exclusive None, upper_inclusive 6.27, 57 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 6.27 | inside | Cayman Islands | 6.21 | dependent |
| 6.27 | inside | Poland | 6.19 | positive |
| 6.27 | inside | United States | 6.17 | negative |
| 6.27 | outside | Gibraltar | 6.29 | dependent |
| 6.27 | outside | Qatar | 6.42 | negative |
| 6.27 | outside | Estonia | 6.7 | positive |

**InflationQ1**: lower_exclusive None, upper_inclusive 1.8, 60 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 1.8 | inside | Kosovo | 1.8 | negative |
| 1.8 | inside | Spain | 1.8 | positive |
| 1.8 | inside | Slovenia | 1.8 | positive |
| 1.8 | outside | Hungary | 1.9 | positive |
| 1.8 | outside | Norway | 1.9 | negative |
| 1.8 | outside | Guinea-Bissau | 1.9 | negative |

**InflationQ4**: lower_exclusive 5.8, upper_inclusive None, 56 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 5.8 | outside | Kenya | 5.8 | negative |
| 5.8 | outside | Kazakhstan | 5.8 | negative |
| 5.8 | outside | South Africa | 5.8 | negative |
| 5.8 | inside | Jordan | 5.9 | negative |
| 5.8 | inside | Rwanda | 5.9 | negative |
| 5.8 | inside | Equatorial Guinea | 6 | negative |

**NAirportsQ2**: lower_exclusive 1.0, upper_inclusive 4.0, 42 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 1.0 | outside | Albania | 1 | candidate |
| 1.0 | outside | North Macedonia | 1 | candidate |
| 1.0 | outside | Montenegro | 1 | candidate |
| 1.0 | inside | Cyprus | 2 | positive |
| 1.0 | inside | Serbia | 2 | candidate |
| 1.0 | inside | Slovakia | 2 | positive |
| 4.0 | inside | Netherlands | 4 | positive |
| 4.0 | inside | Belgium | 4 | positive |
| 4.0 | inside | Croatia | 4 | positive |
| 4.0 | outside | Czech Republic | 5 | positive |
| 4.0 | outside | Denmark | 5 | positive |
| 4.0 | outside | Iraq | 5 | negative |

**PopulationGrowthQ1**: lower_exclusive None, upper_inclusive 0.3075, 59 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 0.3075 | inside | Albania | 0.3 | candidate |
| 0.3075 | inside | Italy | 0.3 | positive |
| 0.3075 | inside | El Salvador | 0.27 | negative |
| 0.3075 | outside | Malta | 0.33 | positive |
| 0.3075 | outside | Wallis and Futuna | 0.33 | dependent |
| 0.3075 | outside | Barbados | 0.33 | negative |

**PopulationGrowthQ3**: lower_exclusive 1.08, upper_inclusive 1.9275, 58 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 1.08 | outside | Colombia | 1.07 | negative |
| 1.08 | outside | Kyrgyzstan | 1.04 | negative |
| 1.08 | outside | Myanmar | 1.03 | negative |
| 1.08 | inside | Australia | 1.09 | negative |
| 1.08 | inside | Martinique | 1.1 | dependent |
| 1.08 | inside | Turkey | 1.12 | candidate |
| 1.9275 | inside | Belize | 1.92 | negative |
| 1.9275 | inside | Chad | 1.92 | negative |
| 1.9275 | inside | Singapore | 1.92 | negative |
| 1.9275 | outside | Guinea-Bissau | 1.93 | negative |
| 1.9275 | outside | Reunion | 1.93 | dependent |
| 1.9275 | outside | Gabon | 1.94 | negative |

**PopulationQ1**: lower_exclusive None, upper_inclusive 276393.75, 62 countries

| edge | relation to bin | country | value | group |
|---|---|---|---|---|
| 276393.75 | inside | French Polynesia | 275918 | dependent |
| 276393.75 | inside | New Caledonia | 271407 | dependent |
| 276393.75 | inside | French Guiana | 268700 | dependent |
| 276393.75 | outside | Barbados | 277821 | negative |
| 276393.75 | outside | Vanuatu | 300019 | negative |
| 276393.75 | outside | Bahamas | 353658 | negative |

## 5. A4 threshold (population >= 389830.5)

Five labelled countries on each side of the threshold (population from `country.Population`, the value the A4 KB stores).

| side | country | code | population | label |
|---|---|---|---|---|
| below 389830.5 | Iceland | IS | 364134 | negative |
| below 389830.5 | Bahamas | BS | 353658 | negative |
| below 389830.5 | Vanuatu | VU | 300019 | negative |
| below 389830.5 | Barbados | BDS | 277821 | negative |
| below 389830.5 | Samoa | WS | 200010 | negative |
| >= 389830.5 | Maldives | MV | 402071 | negative |
| >= 389830.5 | Belize | BZ | 430191 | negative |
| >= 389830.5 | Brunei | BRU | 440715 | negative |
| >= 389830.5 | Cape Verde | CV | 483628 | negative |
| >= 389830.5 | Malta | M | 519562 | positive |

Smallest positive: Malta (519562). Labelled countries below the threshold: 27 (0 positives); missing population: 0.

## 6. Runtime

Wall seconds are per run as seen by the harness (JVM start included, 3 workers in parallel, so totals are compute minutes, not elapsed time); the O configs ran on repeat 0 only; the D1 row is an extra single diagnostic run with a 600 s limit.

| config | runs | mean wall s | mean tested | total wall minutes | total algorithm minutes |
|---|---|---|---|---|---|
| G1 | 15 | 70.9 | 14911 | 17.7 | 15.0 |
| G2 | 15 | 70.7 | 16489 | 17.7 | 15.0 |
| G3 | 15 | 70.8 | 35834 | 17.7 | 15.0 |
| G4 | 15 | 71.3 | 31141 | 17.8 | 15.0 |
| G5 | 15 | 72.6 | 111145 | 18.1 | 15.0 |
| G6 | 15 | 70.6 | 118435 | 17.7 | 15.0 |
| G7 | 15 | 71.3 | 107354 | 17.8 | 15.0 |
| G8 | 15 | 69.1 | 169757 | 17.3 | 15.0 |
| A1 | 15 | 71.6 | 17874 | 17.9 | 15.0 |
| A2 | 15 | 71.4 | 16111 | 17.9 | 15.0 |
| A3 | 15 | 70.4 | 14876 | 17.6 | 15.0 |
| A4 | 15 | 73.0 | 19695 | 18.3 | 15.0 |
| O1 | 5 | 75.9 | 1099 | 6.3 | 5.0 |
| O2 | 5 | 74.5 | 1272 | 6.2 | 5.1 |
| O3 | 5 | 83.9 | 80 | 7.0 | 6.2 |
| D1 (extra: 600 s diagnostic, not a grid config) | 1 | 639.8 | 104 | 10.7 | 10.5 |

## 7. How the most frequent concepts carve the countries

For each country of the three groups, the atom(s) of the concept that exclude it, from the stored edges (`kb/bins.json`, `kb/bins_b5.json`; bins are lower-exclusive, upper-inclusive). A bin atom excludes a country whose value lies in that bin; a country with no value is not in any bin and is not excluded by that atom; `Europe` excludes a country with no `Europe` row in `encompasses`. Each table was checked against the closed world reasoner: the countries with no excluding atom are exactly the countries the concept covers.

### G1 (strict KB, 4 bins): `(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` (8 of 15 folds)

InflationQ4: lower_exclusive 5.8, upper_inclusive None; PopulationQ1: lower_exclusive None, upper_inclusive 276393.75.

| group | countries | covered | excluded by InflationQ4 | excluded by PopulationQ1 | excluded by Europe |
|---|---|---|---|---|---|
| positive | 27 | 27 | 0 | 0 | 0 |
| European negative | 14 | 7 | 2 | 5 | 0 |
| candidate | 7 | 6 | 1 | 0 | 0 |

| group | country | inflation | population | excluded by |
|---|---|---|---|---|
| positive | Austria | 2.1 | 8401940 | none (covered) |
| positive | Belgium | 1.3 | 11492641 | none (covered) |
| positive | Bulgaria | 1.5 | 6520314 | none (covered) |
| positive | Cyprus | 0.2 | 918100 | none (covered) |
| positive | Czech Republic | 1.4 | 10524167 | none (covered) |
| positive | Germany | 1.6 | 82521653 | none (covered) |
| positive | Denmark | 0.8 | 5678348 | none (covered) |
| positive | Spain | 1.8 | 47400798 | none (covered) |
| positive | Estonia | 3.4 | 1331824 | none (covered) |
| positive | France | 0.9 | 64300821 | none (covered) |
| positive | Greece | -0.8 | 10432481 | none (covered) |
| positive | Hungary | 1.9 | 9937628 | none (covered) |
| positive | Croatia | 2.2 | 3871833 | none (covered) |
| positive | Italy | 1.2 | 59433744 | none (covered) |
| positive | Ireland | 0.6 | 5123536 | none (covered) |
| positive | Luxembourg | 1.8 | 645397 | none (covered) |
| positive | Lithuania | 1.2 | 2810761 | none (covered) |
| positive | Latvia | 0.2 | 2201196 | none (covered) |
| positive | Malta | 1 | 519562 | none (covered) |
| positive | Netherlands | 2.5 | 17590672 | none (covered) |
| positive | Portugal | 0.4 | 10343066 | none (covered) |
| positive | Poland | 1 | 38036118 | none (covered) |
| positive | Romania | 3.2 | 20121641 | none (covered) |
| positive | Sweden | 0 | 9555893 | none (covered) |
| positive | Finland | 2.2 | 5513130 | none (covered) |
| positive | Slovakia | 1.7 | 5449270 | none (covered) |
| positive | Slovenia | 1.8 | 2108977 | none (covered) |
| European negative | Andorra | 1.1 | 79535 | PopulationQ1 |
| European negative | Bosnia and Herzegovina | 0.2 | 3791622 | none (covered) |
| European negative | Belarus | 19 | 9503807 | InflationQ4 |
| European negative | Switzerland | -0.4 | 8670300 | none (covered) |
| European negative | Liechtenstein | -0.7 | 39055 | PopulationQ1 |
| European negative | United Kingdom | 2 | 66980000 | none (covered) |
| European negative | Iceland | 3.9 | 364134 | none (covered) |
| European negative | Kosovo | 1.8 | 1733872 | none (covered) |
| European negative | Kazakhstan | 5.8 | 17165239 | none (covered) |
| European negative | Monaco | 1.5 | 37308 | PopulationQ1 |
| European negative | Norway | 1.9 | 5051275 | none (covered) |
| European negative | Russia | 6.8 | 144699673 | InflationQ4 |
| European negative | San Marino | 2.8 | 33627 | PopulationQ1 |
| European negative | Vatican City | no value | 826 | PopulationQ1 |
| candidate | Albania | 1.7 | 2821977 | none (covered) |
| candidate | Moldova | 4.6 | 3473900 | none (covered) |
| candidate | North Macedonia | 2.8 | 1836713 | none (covered) |
| candidate | Montenegro | 4 | 619211 | none (covered) |
| candidate | Serbia | 2.2 | 6690887 | none (covered) |
| candidate | Turkey | 7.6 | 84680273 | InflationQ4 |
| candidate | Ukraine | 0.7 | 43999924 | none (covered) |

### E2b (strict KB, 5 bins): `(not (InflationQ5)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))` (10 of 15 folds)

InflationQ5: lower_exclusive 6.2, upper_inclusive None; PopulationQ1: lower_exclusive None, upper_inclusive 103328.0.

| group | countries | covered | excluded by InflationQ5 | excluded by PopulationQ1 | excluded by Europe |
|---|---|---|---|---|---|
| positive | 27 | 27 | 0 | 0 | 0 |
| European negative | 14 | 7 | 2 | 5 | 0 |
| candidate | 7 | 6 | 1 | 0 | 0 |

| group | country | inflation | population | excluded by |
|---|---|---|---|---|
| positive | Austria | 2.1 | 8401940 | none (covered) |
| positive | Belgium | 1.3 | 11492641 | none (covered) |
| positive | Bulgaria | 1.5 | 6520314 | none (covered) |
| positive | Cyprus | 0.2 | 918100 | none (covered) |
| positive | Czech Republic | 1.4 | 10524167 | none (covered) |
| positive | Germany | 1.6 | 82521653 | none (covered) |
| positive | Denmark | 0.8 | 5678348 | none (covered) |
| positive | Spain | 1.8 | 47400798 | none (covered) |
| positive | Estonia | 3.4 | 1331824 | none (covered) |
| positive | France | 0.9 | 64300821 | none (covered) |
| positive | Greece | -0.8 | 10432481 | none (covered) |
| positive | Hungary | 1.9 | 9937628 | none (covered) |
| positive | Croatia | 2.2 | 3871833 | none (covered) |
| positive | Italy | 1.2 | 59433744 | none (covered) |
| positive | Ireland | 0.6 | 5123536 | none (covered) |
| positive | Luxembourg | 1.8 | 645397 | none (covered) |
| positive | Lithuania | 1.2 | 2810761 | none (covered) |
| positive | Latvia | 0.2 | 2201196 | none (covered) |
| positive | Malta | 1 | 519562 | none (covered) |
| positive | Netherlands | 2.5 | 17590672 | none (covered) |
| positive | Portugal | 0.4 | 10343066 | none (covered) |
| positive | Poland | 1 | 38036118 | none (covered) |
| positive | Romania | 3.2 | 20121641 | none (covered) |
| positive | Sweden | 0 | 9555893 | none (covered) |
| positive | Finland | 2.2 | 5513130 | none (covered) |
| positive | Slovakia | 1.7 | 5449270 | none (covered) |
| positive | Slovenia | 1.8 | 2108977 | none (covered) |
| European negative | Andorra | 1.1 | 79535 | PopulationQ1 |
| European negative | Bosnia and Herzegovina | 0.2 | 3791622 | none (covered) |
| European negative | Belarus | 19 | 9503807 | InflationQ5 |
| European negative | Switzerland | -0.4 | 8670300 | none (covered) |
| European negative | Liechtenstein | -0.7 | 39055 | PopulationQ1 |
| European negative | United Kingdom | 2 | 66980000 | none (covered) |
| European negative | Iceland | 3.9 | 364134 | none (covered) |
| European negative | Kosovo | 1.8 | 1733872 | none (covered) |
| European negative | Kazakhstan | 5.8 | 17165239 | none (covered) |
| European negative | Monaco | 1.5 | 37308 | PopulationQ1 |
| European negative | Norway | 1.9 | 5051275 | none (covered) |
| European negative | Russia | 6.8 | 144699673 | InflationQ5 |
| European negative | San Marino | 2.8 | 33627 | PopulationQ1 |
| European negative | Vatican City | no value | 826 | PopulationQ1 |
| candidate | Albania | 1.7 | 2821977 | none (covered) |
| candidate | Moldova | 4.6 | 3473900 | none (covered) |
| candidate | North Macedonia | 2.8 | 1836713 | none (covered) |
| candidate | Montenegro | 4 | 619211 | none (covered) |
| candidate | Serbia | 2.2 | 6690887 | none (covered) |
| candidate | Turkey | 7.6 | 84680273 | InflationQ5 |
| candidate | Ukraine | 0.7 | 43999924 | none (covered) |

