import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from baselines.run_baselines import bootstrap_interval, score
from src.config import PROCESSED_DIR, SEED
from src.run_experiment import RUNS_DIR

METRICS = ["accuracy", "precision", "recall", "f1"]


def pooled_predictions(runs, folds):
    results = {}
    for repeat, part in runs.groupby("repeat"):
        rows = folds[(folds["repeat"] == repeat) & (folds["fold"].isin(part["fold"]))]
        fp = {(r.fold, c) for r in part.itertuples() for c in str(r.false_positives).split()}
        fn = {(r.fold, c) for r in part.itertuples() for c in str(r.false_negatives).split()}
        y_true = rows["label"].to_numpy()
        y_pred = np.array([
            int((label == 1 and (fold, code) not in fn) or (label == 0 and (fold, code) in fp))
            for code, label, fold in zip(rows["code"], rows["label"], rows["fold"])
        ])
        results[repeat] = (y_true, y_pred)
    return results


def summarize(name, runs, folds):
    per_repeat = runs.groupby("repeat")[[f"test_{m}" for m in METRICS]].mean()
    pooled = pooled_predictions(runs, folds)
    pooled_scores = pd.DataFrame([score(y, p) for y, p in pooled.values()], index=list(pooled))
    intervals = np.array([bootstrap_interval(y, p, np.random.default_rng(SEED + repeat)) for repeat, (y, p) in pooled.items()])

    print(f"\n=== {name}: {len(runs)} folds over {runs['repeat'].nunique()} repeat(s)")
    print("per-fold metrics (mean over folds per repeat, then mean +/- std over repeats):")
    for m in METRICS:
        values = per_repeat[f"test_{m}"]
        print(f"  {m:9s} {values.mean():.3f} +/- {values.std(ddof=1):.3f}")
    print("pooled out-of-fold (per repeat; mean +/- std over repeats):")
    for repeat, row in pooled_scores.iterrows():
        print(f"  repeat {repeat}: P {row['precision']:.3f}  R {row['recall']:.3f}  F1 {row['f1']:.3f}  acc {row['accuracy']:.3f}")
    for m in ["precision", "recall", "f1"]:
        values = pooled_scores[m]
        print(f"  pooled {m:9s} {values.mean():.3f} +/- {values.std(ddof=1):.3f}")
    low, high = intervals.mean(axis=0)
    print(f"  pooled F1 95% bootstrap CI (1000 resamples, bounds averaged over repeats): [{low:.3f}, {high:.3f}]")
    print(f"  mean concept length {runs['length'].mean():.1f}; mean train accuracy {runs['train_accuracy'].mean():.2f}; "
          f"mean wall {runs['wall_seconds'].mean():.1f}s")
    print("  nearest reference per fold: " + ", ".join(f"{r.nearest_reference} ({r.jaccard:.2f})" for r in runs.itertuples()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("configs", nargs="*")
    args = parser.parse_args()
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    paths = [RUNS_DIR / f"{c}.csv" for c in args.configs] or sorted(RUNS_DIR.glob("*.csv"))
    for path in paths:
        runs = pd.read_csv(path, dtype={"false_positives": str, "false_negatives": str}, keep_default_na=False)
        if len(runs):
            summarize(path.stem, runs, folds)


if __name__ == "__main__":
    main()
