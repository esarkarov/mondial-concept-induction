import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    EU_ORGANIZATION,
    FOLD_REPEATS,
    MASK_EXTENDED,
    MASKED_ORGANIZATIONS,
    N_FOLDS,
    PROCESSED_DIR,
)

CSV_DIR = PROCESSED_DIR / "csv"


def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def check_labels():
    country = read(CSV_DIR / "country.csv")
    check(len(country) == 246, f"country rows: {len(country)}")

    positives = set(read(PROCESSED_DIR / "eu_positives.csv")["code"])
    negatives = set(read(PROCESSED_DIR / "eu_negatives.csv")["code"])
    candidates = set(read(PROCESSED_DIR / "eu_excluded_candidates.csv")["code"])
    check(len(positives) == 27, f"positives: {len(positives)}")
    check(len(negatives) == 167, f"negatives: {len(negatives)}")
    check(len(candidates) == 7, f"candidates: {len(candidates)}")
    check(not positives & negatives, "positives and negatives overlap")
    check(not positives & candidates, "positives and candidates overlap")
    check(not negatives & candidates, "negatives and candidates overlap")
    check((positives | negatives | candidates) <= set(country["Code"]), "label code missing from country table")

    politics = read(CSV_DIR / "politics.csv")
    dependent = set(politics.loc[politics["Dependent"] != "", "Country"])
    check(not negatives & dependent, f"negatives with Dependent: {sorted(negatives & dependent)}")
    check(not (positives | candidates) & dependent, "positive or candidate with Dependent")


def check_ismember():
    for name, masked in [("ismember_masked.csv", MASKED_ORGANIZATIONS), ("ismember_masked_extended.csv", MASK_EXTENDED)]:
        organizations = set(read(PROCESSED_DIR / name)["Organization"])
        check(EU_ORGANIZATION not in organizations, f"{name} contains {EU_ORGANIZATION}")
        check(not organizations & set(masked), f"{name} contains masked organizations: {sorted(organizations & set(masked))}")


def check_features():
    expected = {"masked": 156, "extended": 146, "none": 0, "strict": 128}
    for variant, org_columns in expected.items():
        features = pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv")
        check(len(features) == 194, f"features_{variant} rows: {len(features)}")
        check("n_airports" in features.columns and features["n_airports"].notna().all(), f"features_{variant} n_airports")
        organizations = [c for c in features.columns if c.startswith("org_")]
        check(f"org_{EU_ORGANIZATION}" not in organizations, f"features_{variant} has an {EU_ORGANIZATION} column")
        check(len(organizations) == org_columns, f"features_{variant} organization columns: {len(organizations)}")


def check_folds():
    folds = read(PROCESSED_DIR / "folds.csv")
    check(len(folds) == FOLD_REPEATS * 194, f"folds rows: {len(folds)}")
    check(folds["repeat"].nunique() == FOLD_REPEATS, "repeat count")
    for repeat, part in folds.groupby("repeat"):
        check(len(part) == 194 and part["code"].is_unique, f"repeat {repeat}: country not exactly once")
        check(part["fold"].nunique() == N_FOLDS, f"repeat {repeat}: fold count")
        positives = part.assign(label=part["label"].astype(int)).groupby("fold")["label"].sum()
        check((positives >= 5).all(), f"repeat {repeat}: test fold positives {positives.to_dict()}")


def main():
    for step in (check_labels, check_ismember, check_features, check_folds):
        try:
            step()
        except AssertionError as error:
            print(f"FAILED {step.__name__}: {error}")
            sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
