import argparse
import json
from collections import Counter

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from baselines.run_baselines import METRICS, score, summarize
from src.config import PROCESSED_DIR, RESULTS_DIR, SEED

OUT_DIR = RESULTS_DIR / "extensions"
VARIANTS = ["strict", "extended"]
INNER_SPLITS = 3
TREE_GRID = {"max_depth": [2, 3, 4, 5, None], "min_samples_leaf": [1, 2, 5]}
FOREST_GRIDS = {
    "v1": {"n_estimators": [100, 300], "max_depth": [None, 3, 5], "max_features": ["sqrt", 0.3]},
    "v2": {"n_estimators": [100, 300, 500], "max_depth": [None, 3, 5], "max_features": ["sqrt", 0.3]},
}
SUFFIX = {"v1": "", "v2": "_v2"}


def models_for(version):
    return {
        "tree": (lambda: DecisionTreeClassifier(random_state=SEED), TREE_GRID),
        "random_forest": (lambda: RandomForestClassifier(random_state=SEED, n_jobs=1), FOREST_GRIDS[version]),
    }


def search(make_estimator, grid):
    pipeline = Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)), ("model", make_estimator())])
    return GridSearchCV(
        pipeline, {f"model__{k}": v for k, v in grid.items()}, scoring=make_scorer(f1_score, zero_division=0),
        cv=StratifiedKFold(INNER_SPLITS, shuffle=True, random_state=SEED), n_jobs=4, refit=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=list(FOREST_GRIDS), default="v1")
    version = parser.parse_args().version
    suffix = SUFFIX[version]
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, predictions, chosen = [], [], []
    for variant in VARIANTS:
        features = pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv").set_index("code")
        X, y = features.drop(columns="label"), features["label"]
        for model_name, (make_estimator, grid) in models_for(version).items():
            records = []
            for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
                train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
                grid_search = search(make_estimator, grid).fit(X.loc[train["code"]], y.loc[train["code"]])
                predicted = grid_search.predict(X.loc[test["code"]])
                y_true = test["label"].to_numpy()
                records.append({"repeat": repeat, "fold": fold, **score(y_true, predicted), "y_true": y_true, "y_pred": predicted})
                params = {k.removeprefix("model__"): v for k, v in grid_search.best_params_.items()}
                chosen.append({"variant": variant, "model": model_name, "repeat": repeat, "fold": fold,
                               "params": json.dumps(params), "inner_f1": round(grid_search.best_score_, 4)})
                predictions += [(f"tuned{suffix}_{variant}_{model_name}", repeat, code, label, int(p))
                                for code, label, p in zip(test["code"], y_true, predicted)]
            summary.append(summarize(records, variant=variant, model=f"tuned{suffix}_{model_name}"))
            print(f"{variant} {model_name} done", flush=True)
    pd.DataFrame(summary).to_csv(OUT_DIR / f"tuned{suffix}.csv", index=False)
    pd.DataFrame(chosen).to_csv(OUT_DIR / f"tuned{suffix}_hyperparameters.csv", index=False)
    pd.DataFrame(predictions, columns=["config", "repeat", "code", "label", "predicted"]).to_csv(OUT_DIR / f"predictions_tuned{suffix}.csv", index=False)
    table = pd.DataFrame(summary)[["variant", "model"]].copy()
    for name in METRICS:
        table[name] = [f"{r[f'{name}_mean']:.3f} ± {r[f'{name}_std']:.3f}" for r in summary]
    table["pooled F1 [CI]"] = [f"{r['f1_pooled_mean']:.3f} [{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}]" for r in summary]
    print(table.to_string(index=False))
    counts = Counter((c["variant"], c["model"], c["params"]) for c in chosen)
    for key, n in counts.most_common(8):
        print(n, key)


if __name__ == "__main__":
    main()
