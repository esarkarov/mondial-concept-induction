import pandas as pd
from sklearn.model_selection import StratifiedKFold

from src.config import N_FOLDS, PROCESSED_DIR, REPEAT_SEEDS

MIN_TEST_POSITIVES = 5


def load_labels():
    positives = pd.read_csv(PROCESSED_DIR / "eu_positives.csv", dtype=str, keep_default_na=False)
    negatives = pd.read_csv(PROCESSED_DIR / "eu_negatives.csv", dtype=str, keep_default_na=False)
    labels = pd.concat(
        [positives.assign(label=1), negatives.assign(label=0)], ignore_index=True
    )
    return labels.rename(columns={"name": "country_name"})[["code", "label"]]


def make_folds(labels):
    parts = []
    for repeat, seed in enumerate(REPEAT_SEEDS):
        splitter = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
        fold_of = pd.Series(-1, index=labels.index)
        for fold, (_, test_idx) in enumerate(splitter.split(labels["code"], labels["label"])):
            fold_of.iloc[test_idx] = fold
        parts.append(labels.assign(repeat=repeat, fold=fold_of))
    return pd.concat(parts, ignore_index=True)


def check(folds, labels):
    for repeat, part in folds.groupby("repeat"):
        assert part["code"].is_unique and set(part["code"]) == set(labels["code"])
        assert (part["fold"] >= 0).all()
        per_fold = part.groupby("fold")["label"].sum()
        assert len(per_fold) == N_FOLDS and (per_fold >= MIN_TEST_POSITIVES).all(), per_fold


def main():
    labels = load_labels()
    folds = make_folds(labels)
    check(folds, labels)
    folds.to_csv(PROCESSED_DIR / "folds.csv", index=False)
    print(f"countries: {len(labels)} (positives {labels['label'].sum()}, negatives {(labels['label'] == 0).sum()})")
    summary = folds.groupby(["repeat", "fold"])["label"].agg(test_size="size", test_positives="sum")
    print(summary.to_string())


if __name__ == "__main__":
    main()
