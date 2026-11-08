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
| `src/` | Python package: export, kb, splits, masking; `config.py` holds seed, paths, masked organizations |
| `kb/` | Generated `.owl` files |
| `conf/` | DL-Learner `.conf` files |
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

- Release: DL-Learner 1.5.0, asset `dllearner-1.5.0.zip` from <https://github.com/SmartDataAnalytics/DL-Learner/releases>. Extract it into `tools/dl-learner/` so the launcher is `tools/dl-learner/dllearner-1.5.0/bin/cli.bat`. `tools/` is git-ignored.
- Java: 17 (Temurin 17.0.20.1 was used). Its `INSTALL` file says Java 7 is required, but the release fails at startup on Java 17 without the flags below. Java 25 was not tested.
- Flags: `--add-opens java.base/java.lang.invoke=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED`, passed through `JAVA_OPTS`. Removing either one made `examples/father.conf` fail.
- Script: `scripts/run_dllearner.ps1` sets `JAVA_HOME`, `PATH` and `JAVA_OPTS` for its own process only, then calls `cli.bat`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_dllearner.ps1 conf\my_problem.conf
```

Extra arguments after the conf path are passed to `cli.bat`. The default Java is `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot`; set the environment variable `DLLEARNER_JAVA_HOME` to use another JDK 17 folder. DL-Learner writes `log/error.log` inside the extracted folder.

## How to run

The pipeline order is below. The scripts are not written yet; each step will be added under `src/`, `baselines/` or `conf/`.

1. Export tables from the SQL files to CSV (`data/processed/`)
2. Build P/N lists and apply masking
3. Build the OWL knowledge base (`kb/`)
4. Make 5-fold splits (seed 42)
5. Run DL-Learner with the `.conf` files in `conf/`
6. Run baselines (`baselines/`)
7. Evaluate and collect results (`results/`)
