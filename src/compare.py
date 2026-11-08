import numpy as np
import pandas as pd

from src.config import FOLD_REPEATS, RESULTS_DIR, SEED
from src.export_predictions import OUTPUT as PREDICTIONS
from src.run_grid import SUITES, config_name

N_RESAMPLES = 1000
REPORT = RESULTS_DIR / "compare.md"


def name_of(label):
    for suite in SUITES.values():
        for c in suite["configs"]:
            if c["label"] == label:
                return config_name(c)
    return label


RANDOM_FOREST = "strict_random_forest"
TREE_FULL = "strict_tree_full"
EUROPE_RULE = "rule_europe"

PAIRS = [
    ("G1", RANDOM_FOREST), ("G1", TREE_FULL), ("G1", EUROPE_RULE),
    ("G1", "G3"), ("G1", "G2"), ("G3", "G4"),
    ("G1", "G5"), ("G3", "G7"),
    (RANDOM_FOREST, TREE_FULL),
    ("A1", "G1"), ("A2", "G1"), ("A3", "G1"),
]


def matrices(predictions, config):
    part = predictions[predictions["config"] == config].sort_values(["repeat", "code"])
    if part.empty:
        return None
    y = np.stack([g["label"].to_numpy() for _, g in part.groupby("repeat")])
    p = np.stack([g["predicted"].to_numpy() for _, g in part.groupby("repeat")])
    return y, p


def f1_resampled(y, p, indices):
    tp = (y * p)[:, indices].sum(axis=2)
    fp = ((1 - y) * p)[:, indices].sum(axis=2)
    fn = (y * (1 - p))[:, indices].sum(axis=2)
    denominator = 2 * tp + fp + fn
    return np.where(denominator > 0, 2 * tp / np.maximum(denominator, 1), 0.0)


def mean_f1(y, p):
    tp, fp, fn = (y * p).sum(axis=1), ((1 - y) * p).sum(axis=1), (y * (1 - p)).sum(axis=1)
    return np.where(tp > 0, 2 * tp / (2 * tp + fp + fn), 0.0).mean()


def main():
    predictions = pd.read_csv(PREDICTIONS, dtype={"code": str})
    rng = np.random.default_rng(SEED)
    n = predictions[predictions["config"] == EUROPE_RULE]["code"].nunique()
    indices = rng.integers(0, n, size=(N_RESAMPLES, n))
    lines = [
        "# Paired bootstrap comparisons", "",
        f"{N_RESAMPLES} resamples of the {n} labelled countries (seed {SEED}); the same indices are used for both models and all repeats. "
        f"For each resample the F1 is computed per repeat ({FOLD_REPEATS} repeats) from the pooled out-of-fold predictions, averaged over repeats, "
        "and the difference first minus second is taken. Interval = 2.5th and 97.5th percentile of the differences.", "",
        "| first | second | point difference | mean difference | 95% interval | contains 0 |",
        "|---|---|---|---|---|---|",
    ]
    for first, second in PAIRS:
        a, b = name_of(first), name_of(second)
        ma, mb = matrices(predictions, a), matrices(predictions, b)
        if ma is None or mb is None:
            lines.append(f"| {a} | {b} | missing predictions | | | |")
            continue
        assert (ma[0] == mb[0]).all()
        diff = f1_resampled(*ma, indices).mean(axis=0) - f1_resampled(*mb, indices).mean(axis=0)
        low, high = np.percentile(diff, [2.5, 97.5])
        point = mean_f1(*ma) - mean_f1(*mb)
        lines.append(f"| {a} | {b} | {point:+.3f} | {diff.mean():+.3f} | [{low:+.3f}, {high:+.3f}] | {'yes' if low <= 0 <= high else 'no'} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
