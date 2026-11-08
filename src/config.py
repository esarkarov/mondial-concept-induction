from pathlib import Path

SEED = 42

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
KB_DIR = ROOT / "kb"
CONF_DIR = ROOT / "conf"
RESULTS_DIR = ROOT / "results"

SCHEMA_SQL = RAW_DIR / "mondial-schema.psql"
INPUTS_SQL = RAW_DIR / "mondial-inputs.psql"

MASKED_ORGANIZATIONS = [
    "EMU",
    "ECB",
    "EIB",
    "NATO",
    "ESA",
    "CEI",
    "SELEC",
    "V4",
    "Benelux",
    "CE",
    "OSCE",
]

EU_ORGANIZATION = "EU"
EU_MEMBERSHIP_TYPE = "member"
EU_CANDIDATE_TYPE = "candidate"
