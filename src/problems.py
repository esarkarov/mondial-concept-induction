import pandas as pd

from src.config import PROCESSED_DIR

PROBLEMS = ("all", "europe")


def read(name):
    return pd.read_csv(PROCESSED_DIR / name, dtype=str, keep_default_na=False)


def subset_codes(problem):
    if problem == "all":
        return None
    positives = set(read("eu_positives.csv")["code"])
    negatives = set(read("eu_negatives.csv")["code"])
    encompasses = read("csv/encompasses.csv")
    europe = set(encompasses.loc[encompasses["Continent"] == "Europe", "Country"])
    return positives | (negatives & europe)


def restrict(folds, problem):
    codes = subset_codes(problem)
    return folds if codes is None else folds[folds["code"].isin(codes)]
