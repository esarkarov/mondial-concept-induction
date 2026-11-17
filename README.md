# Concept induction on Mondial with DL-Learner

University project, Symbolic Learning course (M1 Data Science & AI).

## 1. Overview

- Task: learn a description logic concept that characterises European Union member countries in the Mondial knowledge base, and compare it with decision tree and random forest baselines.
- Data: the Mondial relational database (`data/raw/*.psql`), converted to CSV and then to an OWL knowledge base (individuals for countries, organizations, continents, languages, religions, ethnic groups, airports, seas).
- Labels: 27 positives (`isMember` of type `member` for `EU`) and 167 negatives (all other sovereign countries); the 7 EU candidates and 45 dependent territories are excluded.
- Leakage control: membership rows of the EU and of organizations that reveal EU membership are removed from the KB (variants `masked`, `extended`, `strict`, `none`; see `src/config.py`).
- Method: stratified 5-fold cross-validation repeated 3 times on the 194 labelled countries; DL-Learner 1.5.0 (CELOE, OCEL) learns on the training folds only, concepts are scored on the held-out fold with DL-Learner's own reasoner; baselines use the same folds.
- Deliverables: `.owl` KB, code, DL-Learner `.conf` files (generated), baselines, result tables; report and slides are not written yet.

## 2. Requirements and setup (Windows, PowerShell)

- Python 3.15.2 was used (other versions untested). Packages are pinned in `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Java 17 (Temurin 17.0.20.101 was used, default path `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot`; set `DLLEARNER_JAVA_HOME` to use another JDK 17 folder). DL-Learner 1.5.0 fails at startup on Java 17 without `--add-opens java.base/java.lang.invoke=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED`. They are set in one place per tool: `scripts/run_dllearner.ps1` (through `JAVA_OPTS`) for learning, and `OPEN_FLAGS` in `scripts/score_concept.py` for the scoring JVM. Java 25 was not tested.
- DL-Learner: download `dllearner-1.5.0.zip` manually from <https://github.com/SmartDataAnalytics/DL-Learner/releases> into `tools/`, then `Expand-Archive tools\dllearner-1.5.0.zip -DestinationPath tools\dl-learner` (launcher: `tools\dl-learner\dllearner-1.5.0\bin\cli.bat`). `tools/` is git-ignored. The scorer compiles `scripts/java/ScoreConcept.java` into `tools/score_concept/` on first use (needs the JDK's `javac`).
- Mondial: `data/raw/mondial-schema.psql` and `data/raw/mondial-inputs.psql` are in the repository and are the only raw files the code reads. `mondial.rdf` (24 MB, git-ignored) and `mondial-meta.rdf` are not used by the pipeline.

## 3. Repository layout

```
data/raw/        Mondial SQL files
data/processed/  CSVs, labels, folds, features (most generated and git-ignored; labels and folds tracked)
src/             pipeline: export, labels, folds, features, KB builder, conf writer, harness, grid, comparison, analysis, extensions
baselines/       decision tree / random forest baselines (run_baselines.py, run_tuned.py)
scripts/         DL-Learner wrapper, scorer (Python + Java), consistency checks, smoke run
kb/              generated .owl files (only mondial_strict_discretised.owl and mondial_extended_discretised.owl are tracked) and bins*.json
conf/            smoke_load*.conf (tracked); conf/generated/ holds generated confs (git-ignored)
results/         result tables (tracked .md/.csv; run caches and logs are git-ignored)
results/extensions/  outputs of the extensions E1 to E4
report/, slides/ Mondial schema PDFs; report and slides not written yet
tools/           DL-Learner distribution (manual download, git-ignored)
```

## 4. How to reproduce

Run from the project root with the virtual environment active. `[ ]` = output file.

1. Data export: `python -m src.export_csv` [`data/processed/csv/*.csv`, 47 tables]
2. Labels and folds: `python -m src.labels` [`eu_positives.csv`, `eu_negatives.csv`, `eu_excluded_candidates.csv`, `ismember_masked.csv`, `ismember_masked_extended.csv`]; `python -m src.folds` [`folds.csv`]
3. Features and baselines: `python -m src.features` [`features_{masked,extended,none,strict}.csv`]; `python -m baselines.run_baselines` [`results/baselines.csv`]; `python scripts\check_phase1.py` (prints `OK`)
4. Knowledge bases: `python -m src.kb --membership <masked|extended|strict|none> [--numeric discretised|datatype] [--closure] [--disjoint-bins] [--bins 3|4|5]` [`kb/mondial_<membership>_<numeric>[_closure][_disjoint][_b3|_b5].owl`, `kb/bins.json` (`bins_b3.json`, `bins_b5.json` for other bin counts)]. Defaults: `--numeric discretised`, 4 bins. `python scripts\check_kb.py [--kb FILE] [--skip-hermit] [--skip-dllearner]` prints counts and runs consistency checks (HermiT through owlready2, DL-Learner load).
5. One DL-Learner run on one fold, then score it on the held-out fold:
   ```powershell
   python -m src.make_conf --repeat 0 --fold 0 --algorithm celoe --use-has-value --name demo
   powershell -ExecutionPolicy Bypass -File scripts\run_dllearner.ps1 conf\generated\demo.conf
   python scripts\score_concept.py --repeat 0 --fold 0 --concept "<learned concept>"
   ```
   `make_conf` writes the conf from the training folds only [`conf/generated/demo.conf`]; `--kb`, `--noise`, `--time`, `--max-depth`, `--reasoner`, `--problem` are options. `python scripts\run_smoke.py` reruns four smoke configurations [`results/smoke_phase2b.md`].
6. Experiment grid (3 workers each; the harness is `python -m src.run_experiment`, resumable, one CSV per config):
   - `python -m src.run_grid` runs G1 to G8, about 50 min [`results/grid_main.md`, `results/runs/G*.csv`]
   - `python -m src.run_grid --suite ablations` runs A1 to A4 [`results/grid_ablations.md`]
   - `python -m src.run_grid --suite owa --repeats 0` runs O1 to O3 (Pellet, repeat 0 only) [`results/grid_owa.md`]
   - 600 s diagnostic: `python -m src.run_experiment --name D1_celoe_strict_disc_hv1_n0_pellet_closure_disjoint_t600 --membership strict --has-value --noise 0 --time 600 --reasoner pellet --closure --disjoint-bins --repeats 0 --folds 0`
7. Aggregation and paired bootstrap: `python -m src.aggregate [config]` (console summary); `python -m src.ocel_sensitivity` [`results/ocel_alt*.csv`]; `python -m src.export_predictions` [`results/predictions.csv`, git-ignored]; `python -m src.compare` [`results/compare.md`]; `python -m src.run_grid --report-only` (also `--suite ablations` or `--suite owa`) rebuilds the grid tables from the run CSVs.
8. Analysis from the frozen results: `python -m src.analysis` [`results/analysis.md`, `results/analysis/*.csv`]; it also fits the three full-data concepts F1 to F3 (cached in `results/analysis/full_data/`).
9. Extensions, run after the freeze (tag `phase-3`):
   - `python -m src.run_extensions E1` (Europe-only problem), `E2` (3 and 5 bins), `E4` (300 s) [`results/extensions/runs/*.csv`]
   - `python -m baselines.run_tuned` [`results/extensions/tuned*.csv`, `predictions_tuned.csv`]
   - `python -m baselines.run_kbonly` (KB-only baselines, feature audit) [`results/extensions/kbonly.csv`, `feature_audit.csv`, `predictions_kbonly.csv`]
   - `python -m src.extensions` [`results/extensions/extensions.md`]

## 5. Results

Result tables are in `results/`: `baselines.csv`, `grid_main.md`, `grid_ablations.md`, `grid_owa.md`, `compare.md`, `analysis.md`, `extensions/extensions.md`, `smoke_phase2b.md`. Per-fold learned concepts are in `results/runs/<config>.csv`. Decisions and their status are in `DECISIONS.md`.

| Config | What it varies |
|---|---|
| G1 to G4 | CELOE on the strict KB: hasValue on/off, noise 0/10 (G1 on/0, G2 on/10, G3 off/0, G4 off/10) |
| G5 to G8 | the same four settings with OCEL |
| A1, A2, A3 | G1 settings with the `extended`, `masked` and `none` membership variants |
| A4 | G1 settings with numeric datatype restrictions instead of bins |
| O1, O2, O3 | G1 settings with Pellet (open world): normal KB, plus closure axioms, plus disjoint bin classes (repeat 0 only) |
| D1 | O3 with a 600 s limit, repeat 0 fold 0 (diagnostic) |
| E1a, E1b, E1c | Europe-only problem (41 countries): strict hasValue on, strict hasValue off, extended hasValue on |
| E2a, E2b | G1 settings with 3 and 5 quantile bins |
| E3 | tuned decision tree and random forest (inner 3-fold CV), strict and extended features |
| E4a, E4b | G1 and G3 settings with a 300 s limit (repeat 0, folds 0 to 4) |
| E5 | untuned tree/forest on KB-only features (raw or binned numerics, role indicators), 194 countries and the E1 subset |
| F1, F2, F3 | concepts fitted on all 194 labelled countries (G1, A1, G3 settings), for presentation only |

## 6. Known limitations

- Runs are time limited (60 s per fold); the number of descriptions tested depends on machine load, so results are not bit-reproducible.
- In DL-Learner 1.5.0 the closed world reasoner treated `max n` as at most n+1 in probes; no learned best concept in G1 to G8 and A1 to A4 contains `max`.
- Pellet on the closure plus disjoint-bins KB (O3) stalls: 80 descriptions tested per fold in 60 s; the cause was not identified.
- The label set and the masking lists were chosen with knowledge of all labels, so reported performance is not a clean out-of-sample estimate of the whole procedure.
- Only 27 positives: pooled F1 intervals are wide (about ±0.1) and many differences between configurations include 0.
- O1 to O3 cover repeat 0 only; E4 covers repeat 0 only.

## 7. Data and tool licenses

- Mondial database: Creative Commons Attribution 3.0 (CC BY 3.0); attribute it to its authors (Wolfgang May, University of Göttingen; author name from memory, not verified). The license terms were taken from the task statement and were not re-checked at the source (not verified).
- DL-Learner 1.5.0: GNU General Public License v3 (the `LICENSE` file of the distribution); the distribution is not redistributed in this repository.
