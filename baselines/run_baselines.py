import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

from src.config import MEMBERSHIP_VARIANTS, PROCESSED_DIR, RESULTS_DIR, SEED
from src.labels import read

METRICS = {
    "accuracy": accuracy_score,
    "precision": lambda y, p: precision_score(y, p, zero_division=0),
    "recall": lambda y, p: recall_score(y, p, zero_division=0),
    "f1": lambda y, p: f1_score(y, p, zero_division=0),
}
REFERENCE_ORGANIZATIONS = ["AG", "NSG"]
N_BOOTSTRAP = 1000


def models():
    return {
        "tree_depth3": lambda: make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            DecisionTreeClassifier(max_depth=3, random_state=SEED),
        ),
        "tree_full": lambda: make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            DecisionTreeClassifier(random_state=SEED),
        ),
        "random_forest": lambda: make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=1),
        ),
    }


def score(y_true, y_pred):
    return {name: fn(y_true, y_pred) for name, fn in METRICS.items()}


def bootstrap_interval(y_true, y_pred, rng):
    n = len(y_true)
    f1s = np.empty(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, n)
        f1s[i] = f1_score(y_true[idx], y_pred[idx], zero_division=0)
    return np.percentile(f1s, [2.5, 97.5])


def summarize(records, **keys):
    frame = pd.DataFrame(records)
    per_repeat = frame.groupby("repeat")[list(METRICS)].mean()
    row = dict(keys)
    for name in METRICS:
        row[f"{name}_mean"] = per_repeat[name].mean()
        row[f"{name}_std"] = per_repeat[name].std(ddof=1)

    pooled, intervals = [], []
    for repeat in sorted(frame["repeat"].unique()):
        part = frame[frame["repeat"] == repeat]
        y_true = np.concatenate(part["y_true"].to_list())
        y_pred = np.concatenate(part["y_pred"].to_list())
        pooled.append(score(y_true, y_pred))
        intervals.append(bootstrap_interval(y_true, y_pred, np.random.default_rng(SEED + repeat)))
    pooled = pd.DataFrame(pooled)
    for name in METRICS:
        row[f"{name}_pooled_mean"] = pooled[name].mean()
        row[f"{name}_pooled_std"] = pooled[name].std(ddof=1)
    row["f1_pooled_ci_low"], row["f1_pooled_ci_high"] = np.mean(intervals, axis=0)
    return row


def evaluate(folds, predict_fn):
    records = []
    for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
        train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
        pred = predict_fn(train["code"].to_numpy(), test["code"].to_numpy())
        y_true = test["label"].to_numpy()
        records.append(
            {"repeat": repeat, "fold": fold, **score(y_true, pred), "y_true": y_true, "y_pred": np.asarray(pred)}
        )
    return records


def run_variant(variant, folds):
    features = pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv").set_index("code")
    X = features.drop(columns="label")
    rows, importances = [], []
    for model_name, make_model in models().items():
        fitted = []

        def predict(train_codes, test_codes):
            model = make_model()
            model.fit(X.loc[train_codes], features.loc[train_codes, "label"])
            fitted.append(model)
            return model.predict(X.loc[test_codes])

        records = evaluate(folds, predict)
        rows.append(summarize(records, variant=variant, model=model_name))
        if model_name == "random_forest":
            importances = np.mean([m[-1].feature_importances_ for m in fitted], axis=0)
    top = pd.Series(importances, index=X.columns).sort_values(ascending=False).head(10)
    return rows, top


def reference_rows(folds):
    labels = folds[["code", "label"]].drop_duplicates().set_index("code")["label"]
    encompasses = read("encompasses")
    europe = set(encompasses.loc[encompasses["Continent"] == "Europe", "Country"])
    ismember = read("ismember")
    rules = {"rule_europe": europe}
    for org in REFERENCE_ORGANIZATIONS:
        rules[f"rule_{org}"] = set(ismember.loc[ismember["Organization"] == org, "Country"])

    rows = []
    majority = lambda train, test: DummyClassifier(strategy="most_frequent").fit(
        np.zeros((len(train), 1)), labels.loc[train]
    ).predict(np.zeros((len(test), 1)))
    rows.append(summarize(evaluate(folds, majority), variant="reference", model="majority_class"))
    for name, members in rules.items():
        predict = lambda train, test, members=members: np.isin(test, list(members)).astype(int)
        rows.append(summarize(evaluate(folds, predict), variant="reference", model=name))
    return rows


def main():
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    rows = reference_rows(folds)
    for variant in MEMBERSHIP_VARIANTS:
        variant_rows, top = run_variant(variant, folds)
        rows += variant_rows
        print(f"\nTop 10 random forest feature importances ({variant}):")
        print(top.round(4).to_string())

    results = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    results.to_csv(RESULTS_DIR / "baselines.csv", index=False)

    table = results[["variant", "model"]].copy()
    for name in METRICS:
        table[name] = results.apply(lambda r: f"{r[f'{name}_mean']:.3f} ± {r[f'{name}_std']:.3f}", axis=1)
    print("\nPer-fold metrics: mean ± std over repeats (per-repeat value = mean over the folds):")
    print(table.to_string(index=False))

    pooled = results[["variant", "model"]].copy()
    for name in METRICS:
        pooled[name] = results.apply(
            lambda r: f"{r[f'{name}_pooled_mean']:.3f} ± {r[f'{name}_pooled_std']:.3f}", axis=1
        )
    pooled["f1_95%_bootstrap_ci"] = results.apply(
        lambda r: f"[{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}]", axis=1
    )
    print("\nPooled out-of-fold metrics (194 predictions per repeat): mean ± std over repeats:")
    print(pooled.to_string(index=False))


if __name__ == "__main__":
    main()
