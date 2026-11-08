import numpy as np
import pandas as pd

from baselines.run_baselines import models
from src.config import PROCESSED_DIR, RESULTS_DIR, SEED
from src.run_experiment import RUNS_DIR, read_csv
from src.run_grid import SUITES, config_name

OUTPUT = RESULTS_DIR / "predictions.csv"
BASELINE_VARIANT = "strict"
RULE_ORGANIZATIONS = {"rule_AG": "AG"}


def learned_predictions(folds):
    rows = []
    for suite in SUITES.values():
        for c in suite["configs"]:
            path = RUNS_DIR / f"{config_name(c)}.csv"
            if not path.exists():
                continue
            runs = pd.read_csv(path, dtype={"false_positives": str, "false_negatives": str}, keep_default_na=False)
            for run in runs.itertuples():
                fp, fn = set(run.false_positives.split()), set(run.false_negatives.split())
                test = folds[(folds["repeat"] == run.repeat) & (folds["fold"] == run.fold)]
                for code, label in zip(test["code"], test["label"]):
                    predicted = int((label == 1 and code not in fn) or (label == 0 and code in fp))
                    rows.append((config_name(c), run.repeat, code, label, predicted))
    return rows


def model_predictions(folds):
    features = pd.read_csv(PROCESSED_DIR / f"features_{BASELINE_VARIANT}.csv").set_index("code")
    X = features.drop(columns="label")
    rows = []
    for model_name, make_model in models().items():
        for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
            train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
            model = make_model()
            model.fit(X.loc[train["code"]], features.loc[train["code"], "label"])
            predicted = model.predict(X.loc[test["code"]])
            rows += [(f"{BASELINE_VARIANT}_{model_name}", repeat, code, label, int(p))
                     for code, label, p in zip(test["code"], test["label"], predicted)]
    return rows


def rule_predictions(folds):
    encompasses = read_csv(PROCESSED_DIR / "csv" / "encompasses.csv")
    ismember = read_csv(PROCESSED_DIR / "csv" / "ismember.csv")
    sets = {"rule_europe": set(encompasses.loc[encompasses["Continent"] == "Europe", "Country"])}
    for name, org in RULE_ORGANIZATIONS.items():
        sets[name] = set(ismember.loc[ismember["Organization"] == org, "Country"])
    return [(name, r.repeat, r.code, r.label, int(r.code in members))
            for name, members in sets.items() for r in folds.itertuples()]


def check_against_baselines(predictions):
    baselines = pd.read_csv(RESULTS_DIR / "baselines.csv")
    worst = 0.0
    for model in ("tree_depth3", "tree_full", "random_forest"):
        part = predictions[predictions["config"] == f"{BASELINE_VARIANT}_{model}"]
        f1s = []
        for _, group in part.groupby("repeat"):
            tp = int(((group["label"] == 1) & (group["predicted"] == 1)).sum())
            fp = int(((group["label"] == 0) & (group["predicted"] == 1)).sum())
            fn = int(((group["label"] == 1) & (group["predicted"] == 0)).sum())
            f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
        expected = baselines[(baselines["variant"] == BASELINE_VARIANT) & (baselines["model"] == model)]["f1_pooled_mean"].iloc[0]
        worst = max(worst, abs(np.mean(f1s) - expected))
    return worst


def main():
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    rows = learned_predictions(folds) + model_predictions(folds) + rule_predictions(folds)
    predictions = pd.DataFrame(rows, columns=["config", "repeat", "code", "label", "predicted"])
    predictions.to_csv(OUTPUT, index=False)
    print(f"wrote {OUTPUT}: {len(predictions)} rows, {predictions['config'].nunique()} configs")
    print(f"max |pooled F1 from predictions - f1_pooled_mean in baselines.csv| over the 3 strict models: {check_against_baselines(predictions):.2e}")


if __name__ == "__main__":
    main()
