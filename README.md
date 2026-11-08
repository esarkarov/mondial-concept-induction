# Concept induction on Mondial with DL-Learner

University project, Symbolic Learning course.

## Goal

Learn a description logic concept that characterises European Union member countries in the Mondial knowledge base, using DL-Learner, and compare it with decision tree and random forest baselines.

- Positives: the 27 countries with an `isMember` row of type `member` in the EU.
- Negatives: all other countries except the 7 EU candidates.
- Leakage control: `isMember` rows for the European organizations EMU, ECB, EIB, NATO, ESA, CEI, SELEC, V4, Benelux, CE and OSCE are dropped before building the knowledge base (see `MASKED_ORGANIZATIONS` in `src/config.py`).

Deliverables: `.owl` knowledge base, code, DL-Learner `.conf` files, baselines, report and slides.

## Folder layout

| Folder | Content |
|---|---|
| `data/raw/` | Source files: `mondial-schema.psql`, `mondial-inputs.psql` (committed), `mondial.rdf`, `mondial-meta.rdf` |
| `data/processed/` | Generated CSVs, P/N lists, fold splits |
| `src/` | Python package: `export_csv`, `labels`, `folds`, `features`; `config.py` holds seed, paths, masking lists, label set |
| `scripts/` | `run_dllearner.ps1` (DL-Learner wrapper), `check_phase1.py` (consistency checks) |
| `tools/` | DL-Learner distribution, downloaded manually (git-ignored) |
| `kb/` | Generated `.owl` files and `bins.json`; only the default variant is tracked |
| `conf/` | DL-Learner `.conf` files (`smoke_load.conf` loads the KB without learning) |
| `baselines/` | Decision tree and random forest |
| `results/` | Experiment outputs and logs (git-ignored) |
| `report/` | Report |
| `slides/` | Slides |

`data/raw/mondial.rdf` (24 MB) is git-ignored: each member copies it locally.

## Setup

Python 3.15.2 was used to create the pinned environment; other recent Python 3 versions are untested.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Linux/macOS, activate with `source .venv/bin/activate`.

## Running DL-Learner

- Release: DL-Learner 1.5.0, asset `dllearner-1.5.0.zip` from <https://github.com/SmartDataAnalytics/DL-Learner/releases>. `tools/` is git-ignored and is not filled by cloning: download the zip manually into `tools/`, then run `Expand-Archive tools\dllearner-1.5.0.zip -DestinationPath tools\dl-learner` so the launcher is `tools/dl-learner/dllearner-1.5.0/bin/cli.bat`.
- Java: 17 (Temurin 17.0.20.1 was used). Its `INSTALL` file says Java 7 is required, but the release fails at startup on Java 17 without the flags below. Java 25 was not tested.
- Flags: `--add-opens java.base/java.lang.invoke=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED`, passed through `JAVA_OPTS`. Removing either one made `examples/father.conf` fail.
- Script: `scripts/run_dllearner.ps1` sets `JAVA_HOME`, `PATH` and `JAVA_OPTS` for its own process only, then calls `cli.bat`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_dllearner.ps1 conf\my_problem.conf
```

Extra arguments after the conf path are passed to `cli.bat`. The default Java is `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot`; set the environment variable `DLLEARNER_JAVA_HOME` to use another JDK 17 folder. DL-Learner writes `log/error.log` inside the extracted folder.

## How to run

Run everything from the project root with the virtual environment active. Phase 1 (data, labels, folds, features, baselines):

```powershell
python -m src.export_csv
python -m src.labels
python -m src.folds
python -m src.features
python -m baselines.run_baselines
python scripts\check_phase1.py
```

| Step | Writes |
|---|---|
| `src.export_csv` | `data/processed/csv/<table>.csv` (47 tables) |
| `src.labels` | `eu_positives.csv`, `eu_negatives.csv`, `eu_excluded_candidates.csv`, `ismember_masked.csv`, `ismember_masked_extended.csv` |
| `src.folds` | `data/processed/folds.csv` (5 folds x 3 repeats, seeds 42 to 44) |
| `src.features` | `data/processed/features_{masked,extended,none}.csv` |
| `baselines.run_baselines` | `results/baselines.csv` |
| `scripts\check_phase1.py` | prints `OK` or the first failed check |

Phase 2A (OWL knowledge base), after `src.labels`:

```powershell
python -m src.kb --membership extended --numeric discretised
python scripts\check_kb.py
```

`src.kb` options: `--membership {masked,extended,none}` (default `extended`), `--numeric {discretised,datatype}` (default `discretised`), `--closure` (not implemented yet, it exits with a message). It writes `kb/mondial_<membership>_<numeric>.owl` and `kb/bins.json` (quantile bin edges over all 246 countries). Only `kb/mondial_extended_discretised.owl` and `kb/bins.json` are tracked; the other variants are regenerated with the same command.

`scripts\check_kb.py` prints the counts, asserts the leakage and consistency checks, runs HermiT (owlready2, Java 17 from `DLLEARNER_JAVA_HOME` or the default Temurin folder) and loads the KB in DL-Learner with `conf/smoke_load.conf`. Options: `--kb <file>`, `--skip-hermit`, `--skip-dllearner`.

Not yet implemented: the learning `.conf` files and the DL-Learner evaluation. DL-Learner itself runs through `scripts\run_dllearner.ps1` (see "Running DL-Learner"); it needs Java 17 and the manually downloaded `tools/dl-learner/` folder.
