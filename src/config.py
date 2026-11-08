from pathlib import Path

SEED = 42
N_FOLDS = 5
FOLD_REPEATS = 3
REPEAT_SEEDS = [SEED + r for r in range(FOLD_REPEATS)]

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

MASK_EXTENDED = MASKED_ORGANIZATIONS + [
    "G-9",
    "NIB",
    "EFTA",
    "BA",
    "CBSS",
    "NC",
    "CERN",
    "EAPC",
    "EBRD",
    "BSEC",
]

STRICT_EXTRA = [
    "AG",
    "IAEA",
    "ICC",
    "ICCt",
    "IFRCS",
    "IOC",
    "IOM",
    "IPU",
    "ISO",
    "Interpol",
    "NSG",
    "OAS",
    "OPCW",
    "PCA",
    "UN",
    "UNESCO",
    "WCO",
    "WTO",
]

KB_MEMBERSHIP_VARIANTS = ("masked", "extended", "strict", "none")

LABEL_SET = "sovereign"
LABEL_SETS = ("all", "sovereign")

MEMBERSHIP_VARIANT = "masked"
MEMBERSHIP_VARIANTS = ("masked", "extended", "none")

EU_ORGANIZATION = "EU"
EU_MEMBERSHIP_TYPE = "member"
EU_CANDIDATE_TYPE = "candidate"
