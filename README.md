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

## DL-Learner and Java

Not installed by this skeleton.

- Java: TODO confirm the required version. OpenJDK 25.0.5 is present on the setup machine, but compatibility with DL-Learner is not verified.
- DL-Learner: TODO pin the exact release, download URL and install location.

## How to run

The pipeline order is below. The scripts are not written yet; each step will be added under `src/`, `baselines/` or `conf/`.

1. Export tables from the SQL files to CSV (`data/processed/`)
2. Build P/N lists and apply masking
3. Build the OWL knowledge base (`kb/`)
4. Make 5-fold splits (seed 42)
5. Run DL-Learner with the `.conf` files in `conf/`
6. Run baselines (`baselines/`)
7. Evaluate and collect results (`results/`)
