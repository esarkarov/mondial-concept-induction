import json
import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

from baselines.run_baselines import METRICS, models, score, summarize
from src.aggregate import read_runs, statistics
from baselines.run_kbonly import MIN_INDICATOR
from src.compare import f1_resampled, matrices, mean_f1, stack
from src.config import KB_DIR, N_FOLDS, PROCESSED_DIR, RESULTS_DIR, SEED
from src.grid_extras import IMPROVEMENT_RE, seconds
from src.problems import restrict, subset_codes
from src.run_extensions import EXTENSIONS_DIR, GROUPS, RUNS_DIR
from src.run_grid import details, main_table

REPORT = EXTENSIONS_DIR / "extensions.md"
E1_PREDICTIONS = EXTENSIONS_DIR / "predictions_e1.csv"
E2_PREDICTIONS = EXTENSIONS_DIR / "predictions_e2.csv"
TUNED_PREDICTIONS = EXTENSIONS_DIR / "predictions_tuned.csv"
N_RESAMPLES = 1000
G1 = "G1_celoe_strict_disc_hv1_n0"
G3 = "G3_celoe_strict_disc_hv0_n0"
A1 = "A1_celoe_extended_disc_hv1_n0"
STRICT_FOREST = "strict_random_forest"
BIN_RE = re.compile(r"[A-Za-z]+Q\d")
ATTRIBUTE_PREFIX = {"Population": "population", "Area": "area", "Gdp": "gdp", "GdpPerCapita": "gdp_per_capita", "Inflation": "inflation",
                    "InfantMortality": "infant_mortality", "PopulationGrowth": "population_growth", "NAirports": "n_airports"}
ODD_THINGS = [
    "E1: `majority_class` and `predict_all_positive` give identical predictions in every fold because the positives are the majority of the 41 countries (27 of 41); "
    "the test folds hold about 8 countries, so per-fold precision and recall are coarse. The `nearest_reference` columns in the E1 run CSVs use references restricted to the 41 countries, where `Europe` covers all of them.",
    "E1: specificity is the share of the 14 European negatives classified correctly, pooled per repeat and averaged over repeats; it is 0.000 for the two constant baselines by construction.",
    "E2: with 3 and 5 bins `n_airports` has fewer distinct bins than requested (3 classes for 3 bins and for the 4-bin reference, 4 classes for 5 bins); in the 5-bin KB `NAirportsQ2` has 0 countries because its interval (1, x] contains no integer. "
    "Atom names such as `InflationQ3` or `PopulationQ1` denote different intervals in each KB, so atoms are only comparable through the edges listed.",
    "E3: the tuned strict random forest has a lower pooled F1 than the untuned strict forest (paired difference in the table above). "
    "Ties between hyperparameter settings are broken by `GridSearchCV` in grid order.",
    "E4: the 'missing folds' lines in the per-config details of E4 list repeats 1 and 2 because only repeat 0 was run, as specified. All ten 300 s runs ended at exactly 300.0 algorithm seconds (wall 310 to 316 s).",
    "E4: for the stored G1 repeat 0 fold 2 run the final best concept does not appear as an improvement line in its 60 s log ('not printed as an improvement'); the cause was not investigated.",
    "E5: the kb-only sets have 165 to 230 features depending on the set, the baselines 188 (strict) and 206 (extended); `kb_raw` leaves missing numeric values missing and median-imputes them on the training fold, `kb_binned` gives a missing value all-zero bin columns. "
    "Choices fixed before running: neighbors as a count, role indicators kept for values present in at least 10 labelled countries (by analogy with the share-column threshold), main-language/religion/ethnic-group roles not used, organizations as in the baselines of the same variant.",
    "E5: the E1 reference rows (baseline strict forest and tree, E1a) show only the pooled F1 point value and specificity; their full rows are in the E1 section above.",
    "Part A ran sequentially, one DL-Learner configuration at a time with 3 workers; the light report generation for E1 overlapped with the first minutes of E2, and E3 ran alone after the DL-Learner runs.",
]
NOT_DONE = [
    "E1, E2 and E4: one run per configuration; no repeated runs to measure run-to-run variation (runs are time limited and not bit-reproducible).",
    "E1: only the three specified configurations (no OCEL, no noise, no other KB variants); baselines only with strict features.",
    "E2: bins 3 and 5 only for the strict KB with CELOE and hasValue on; no per-attribute bin choice; G1 was not rerun.",
    "E3: no paired bootstrap for the extended-feature tuned models and no other grids; tuned tree vs untuned tree was not compared.",
    "E5: no tuned kb-only models, no CELOE or kb-only runs on the extended Europe-only problem, no feature-group ablation of the baselines, one run per model (forest seeds fixed).",
    "E4: repeat 0 only (5 folds); no 300 s runs for other configurations; the log-time column is missing where a concept was not printed as an improvement.",
    "Not investigated: the log mismatch in the stored G1 fold 2 run, and why `NAirportsQ2` is empty in the 5-bin KB beyond the edge arithmetic.",
]


def md_table(frame):
    lines = ["| " + " | ".join(frame.columns) + " |", "|" + "---|" * len(frame.columns)]
    return lines + ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]


def folds_all():
    return pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})


def config_by_name(name):
    for group in GROUPS.values():
        for c in group:
            if c["name"] == name:
                return c


def runs_of(name):
    path = RUNS_DIR / f"{name}.csv"
    if not path.exists():
        return None
    runs = read_runs(path)
    return runs if len(runs) else None


def learned_predictions(name, runs, folds):
    rows = []
    for run in runs.itertuples():
        fp, fn = set(str(run.false_positives).split()), set(str(run.false_negatives).split())
        test = folds[(folds["repeat"] == run.repeat) & (folds["fold"] == run.fold)]
        for code, label in zip(test["code"], test["label"]):
            rows.append((name, run.repeat, code, label, int((label == 1 and code not in fn) or (label == 0 and code in fp))))
    return rows


def e1_baselines(folds):
    features = pd.read_csv(PROCESSED_DIR / "features_strict.csv").set_index("code")
    X, y = features.drop(columns="label"), features["label"]
    makers = {"majority_class": lambda: DummyClassifier(strategy="most_frequent"),
              "predict_all_positive": lambda: DummyClassifier(strategy="constant", constant=1), **models()}
    rows, predictions = [], []
    for model_name, make in makers.items():
        records = []
        for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
            train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
            model = make()
            dummy = model_name in ("majority_class", "predict_all_positive")
            model.fit(np.zeros((len(train), 1)) if dummy else X.loc[train["code"]], y.loc[train["code"]])
            predicted = model.predict(np.zeros((len(test), 1)) if dummy else X.loc[test["code"]])
            y_true = test["label"].to_numpy()
            records.append({"repeat": repeat, "fold": fold, **score(y_true, predicted), "y_true": y_true, "y_pred": predicted})
            predictions += [(f"e1_{model_name}", repeat, code, label, int(p)) for code, label, p in zip(test["code"], y_true, predicted)]
        rows.append(summarize(records, variant="e1_strict", model=model_name))
    return rows, predictions


def specificity(predictions, config):
    part = predictions[predictions["config"] == config]
    return np.mean([(g.loc[g["label"] == 0, "predicted"] == 0).mean() for _, g in part.groupby("repeat")])


def pooled_row(predictions, config):
    values = {m: [] for m in METRICS}
    for _, g in predictions[predictions["config"] == config].groupby("repeat"):
        for m, v in score(g["label"].to_numpy(), g["predicted"].to_numpy()).items():
            values[m].append(v)
    return {m: np.mean(v) for m, v in values.items()}


def paired_table(predictions, pairs, n_codes, note):
    rng = np.random.default_rng(SEED)
    indices = rng.integers(0, n_codes, size=(N_RESAMPLES, n_codes))
    lines = [note, "", "| first | second | repeats | point difference | mean difference | 95% interval | contains 0 |", "|---|---|---|---|---|---|---|"]
    for first, second in pairs:
        ra, rb = matrices(predictions, first), matrices(predictions, second)
        if ra is None or rb is None:
            lines.append(f"| {first} | {second} | | missing predictions | | | |")
            continue
        shared = sorted(set(ra) & set(rb))
        ma, mb = stack(ra, shared), stack(rb, shared)
        assert (ma[0] == mb[0]).all() and ma[0].shape[1] == n_codes, (first, second, ma[0].shape)
        diff = f1_resampled(*ma, indices).mean(axis=0) - f1_resampled(*mb, indices).mean(axis=0)
        low, high = np.percentile(diff, [2.5, 97.5])
        lines.append(f"| {first} | {second} | {','.join(map(str, shared))} | {mean_f1(*ma) - mean_f1(*mb):+.3f} | {diff.mean():+.3f} | "
                     f"[{low:+.3f}, {high:+.3f}] | {'yes' if low <= 0 <= high else 'no'} |")
    return lines


def baseline_lines(rows, predictions, with_specificity):
    lines = ["| model | accuracy | precision | recall | F1 | pooled F1 [95% CI] |" + (" specificity (pooled) |" if with_specificity else ""),
             "|---|---|---|---|---|---|" + ("---|" if with_specificity else "")]
    for r in rows:
        cells = " | ".join(f"{r[f'{m}_mean']:.3f} ± {r[f'{m}_std']:.3f}" for m in METRICS)
        spec = f" {specificity(predictions, 'e1_' + r['model']):.3f} |" if with_specificity else ""
        lines.append(f"| {r['variant']}: {r['model']} | {cells} | {r['f1_pooled_mean']:.3f} [{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}] |{spec}")
    return lines


def learned_rows(names, folds):
    rows = []
    for name in names:
        runs = runs_of(name)
        if runs is not None:
            rows.append((name, runs, statistics(runs, folds)))
    return rows


def concept_lines(rows, time_limit=60):
    lines = []
    for name, runs, _ in rows:
        lines += details(name, runs, time_limit)
    return lines


def e1_section(base_folds):
    names = [c["name"] for c in GROUPS["E1"]]
    folds = restrict(base_folds, "europe")
    rows = learned_rows(names, folds)
    if not rows:
        return None
    codes = sorted(subset_codes("europe"))
    n_pos = int(folds.drop_duplicates("code")["label"].sum())
    lines = ["## E1. Europe-only learning problem (run after the freeze)", "",
             f"**Sample: {len(codes)} countries** ({n_pos} positives, {len(codes) - n_pos} European negatives), the existing folds restricted to these countries "
             "(about 8 per test fold; 5 folds x 3 repeats). Training examples = the training part of the same folds restricted to the subset. "
             "CELOE, 60 s, noise 0, discretised, 3 workers. All numbers below are on 41 countries.", "",
             "### Learned concepts", ""]
    lines += main_table(rows)
    baseline_rows, baseline_predictions = e1_baselines(folds)
    predictions = [p for name, runs, _ in rows for p in learned_predictions(name, runs, folds)] + baseline_predictions
    predictions = pd.DataFrame(predictions, columns=["config", "repeat", "code", "label", "predicted"])
    lines += ["", "### Baselines on the same 41 countries and folds (strict features, trained on the subset's training rows only)", ""]
    lines += baseline_lines(baseline_rows, predictions, True)
    lines += ["", "### Pooled out-of-fold metrics and specificity (share of the 14 European negatives classified correctly; mean over repeats)", "",
              "| config | accuracy | precision | recall | F1 | specificity |", "|---|---|---|---|---|---|"]
    for config in [n for n, _, _ in rows] + [f"e1_{r['model']}" for r in baseline_rows]:
        p = pooled_row(predictions, config)
        lines.append(f"| {config} | {p['accuracy']:.3f} | {p['precision']:.3f} | {p['recall']:.3f} | {p['f1']:.3f} | {specificity(predictions, config):.3f} |")
    short = {c["label"]: c["name"] for c in GROUPS["E1"]}
    pairs = [(short["E1a"], "e1_random_forest"), (short["E1a"], "e1_predict_all_positive"), (short["E1c"], short["E1a"])]
    lines += [""] + paired_table(predictions, pairs, len(codes),
                                 f"### Paired bootstrap on the {len(codes)} countries\n\n{N_RESAMPLES} resamples (seed {SEED}), shared indices, F1 averaged over the 3 repeats, difference first minus second.")
    lines += ["", "### Most frequent concepts and details", ""] + concept_lines(rows)
    predictions.to_csv(E1_PREDICTIONS, index=False)
    return lines


def bin_size_lines():
    lines = ["| attribute | 3 bins | 4 bins (reference) | 5 bins |", "|---|---|---|---|"]
    files = {3: "bins_b3.json", 4: "bins.json", 5: "bins_b5.json"}
    data = {k: json.loads((KB_DIR / f).read_text(encoding="utf-8")) for k, f in files.items()}
    for attribute in data[4]:
        cells = [" / ".join(str(b["count"]) for b in data[k][attribute]["bins"]) + f" ({len(data[k][attribute]['bins'])} bins)" for k in (3, 4, 5)]
        lines.append(f"| {attribute} | " + " | ".join(cells) + " |")
    return lines


def atom_lines(runs, bins_file):
    bins = json.loads((KB_DIR / bins_file).read_text(encoding="utf-8"))
    lines = []
    for concept, count in Counter(runs["concept"]).most_common(3):
        atoms = sorted(set(BIN_RE.findall(concept)))
        parts = []
        for atom in atoms:
            prefix = re.match(r"[A-Za-z]+(?=Q\d)", atom).group(0)
            entry = next(b for b in bins[ATTRIBUTE_PREFIX[prefix]]["bins"] if b["class"] == atom)
            parts.append(f"{atom} (lower_exclusive {entry['lower_exclusive']}, upper_inclusive {entry['upper_inclusive']}, {entry['count']} countries)")
        lines.append(f"  - {count}x `{concept}`: " + ("; ".join(parts) if parts else "no bin atoms"))
    return lines


def e2_section(base_folds):
    names = [G1] + [c["name"] for c in GROUPS["E2"]]
    rows = learned_rows(names, base_folds)
    if len(rows) < 2:
        return None
    lines = ["## E2. Discretisation sensitivity (run after the freeze)", "",
             "CELOE, strict KB, hasValue on, noise 0, 60 s, 15 folds, 194 countries; G1 is the 4-bin reference (stored result, not rerun). "
             "Quantile bins as before; ties can give fewer bins.", "", "### Learned concepts", ""]
    lines += main_table(rows)
    lines += ["", "### Bin sizes (countries per bin, over the 246 countries with a value)", ""] + bin_size_lines()
    lines += ["", "### Bin atoms of the three most frequent concepts, with edges", ""]
    for name, runs, _ in rows:
        bins_file = "bins_b3.json" if "_b3_" in name else "bins_b5.json" if "_b5_" in name else "bins.json"
        lines += [f"- {name}"] + atom_lines(runs, bins_file)
    existing = pd.read_csv(RESULTS_DIR / "predictions.csv", dtype={"code": str})
    new = pd.DataFrame([p for name, runs, _ in rows if name != G1 for p in learned_predictions(name, runs, base_folds)],
                       columns=existing.columns)
    all_predictions = pd.concat([existing[existing["config"] == G1], new])
    pairs = [(c["name"], G1) for c in GROUPS["E2"]]
    lines += [""] + paired_table(all_predictions, pairs, 194, f"### Paired bootstrap vs G1\n\n{N_RESAMPLES} resamples of the 194 countries (seed {SEED}), same method as `results/compare.md`.")
    lines += ["", "### Most frequent concepts and details", ""] + concept_lines(rows)
    new.to_csv(E2_PREDICTIONS, index=False)
    return lines


def e3_section():
    path = EXTENSIONS_DIR / "tuned.csv"
    if not path.exists():
        return None
    tuned = pd.read_csv(path)
    untuned = pd.read_csv(RESULTS_DIR / "baselines.csv")
    untuned = untuned[untuned["variant"].isin(["strict", "extended"]) & untuned["model"].isin(["tree_full", "random_forest"])]
    lines = ["## E3 v1: grid did not contain the untuned default (run after the freeze)", "",
             "Same 15 folds. Inside each training fold, 3-fold stratified inner CV (seed 42) picks hyperparameters by F1: tree `max_depth` in {2,3,4,5,None} x `min_samples_leaf` in {1,2,5}; "
             "forest `n_estimators` in {100,300} x `max_depth` in {None,3,5} x `max_features` in {sqrt,0.3}. Median imputation fitted on the training fold. "
             "Untuned rows are from `results/baselines.csv` (unchanged).", "",
             "| model | accuracy | precision | recall | F1 | pooled accuracy | pooled precision | pooled recall | pooled F1 [95% CI] |", "|---|---|---|---|---|---|---|---|---|"]
    for r in pd.concat([tuned, untuned]).itertuples():
        cells = " | ".join(f"{getattr(r, m + '_mean'):.3f} ± {getattr(r, m + '_std'):.3f}" for m in METRICS)
        pooled = " | ".join(f"{getattr(r, m + '_pooled_mean'):.3f}" for m in ("accuracy", "precision", "recall"))
        lines.append(f"| {r.variant}: {r.model} | {cells} | {pooled} | {r.f1_pooled_mean:.3f} [{r.f1_pooled_ci_low:.3f}, {r.f1_pooled_ci_high:.3f}] |")
    chosen = pd.read_csv(EXTENSIONS_DIR / "tuned_hyperparameters.csv")
    lines += ["", "### Chosen hyperparameters (15 outer folds per row; full table in `tuned_hyperparameters.csv`)", ""]
    for (variant, model), group in chosen.groupby(["variant", "model"], sort=False):
        lines.append(f"**{variant} {model}** (mean inner F1 {group['inner_f1'].mean():.3f}): " +
                     "; ".join(f"{n}x `{p}`" for p, n in Counter(group["params"]).most_common()))
        parsed = group["params"].map(json.loads)
        for key in parsed.iloc[0]:
            lines.append(f"  - {key}: " + ", ".join(f"{v} ({n})" for v, n in Counter(str(p[key]) for p in parsed).most_common()))
        lines.append("")
    existing = pd.read_csv(RESULTS_DIR / "predictions.csv", dtype={"code": str})
    tuned_predictions = pd.read_csv(TUNED_PREDICTIONS, dtype={"code": str})
    all_predictions = pd.concat([existing[existing["config"].isin([G1, STRICT_FOREST])], tuned_predictions])
    pairs = [("tuned_strict_random_forest", G1), ("tuned_strict_tree", G1), ("tuned_strict_random_forest", STRICT_FOREST)]
    lines += paired_table(all_predictions, pairs, 194, f"### Paired bootstrap\n\n{N_RESAMPLES} resamples of the 194 countries (seed {SEED}), same method as `results/compare.md`.")
    return lines


FOREST_DEFAULT = {"n_estimators": 500, "max_depth": None, "max_features": "sqrt"}
TREE_DEFAULT = {"max_depth": None, "min_samples_leaf": 1}


def untuned_predictions(variant, folds):
    features = pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv").set_index("code")
    X = features.drop(columns="label")
    rows = []
    for model_name, make in models().items():
        for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
            train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
            model = make()
            model.fit(X.loc[train["code"]], features.loc[train["code"], "label"])
            rows += [(f"{variant}_{model_name}", repeat, code, label, int(p))
                     for code, label, p in zip(test["code"], test["label"], model.predict(X.loc[test["code"]]))]
    frame = pd.DataFrame(rows, columns=["config", "repeat", "code", "label", "predicted"])
    baselines = pd.read_csv(RESULTS_DIR / "baselines.csv")
    for model_name in ("tree_full", "random_forest"):
        expected = baselines[(baselines["variant"] == variant) & (baselines["model"] == model_name)]["f1_pooled_mean"].iloc[0]
        assert abs(pooled_f1_mean(frame, f"{variant}_{model_name}") - expected) < 1e-9, (variant, model_name)
    return frame


def pooled_f1_mean(predictions, config):
    return float(np.mean([score(g["label"].to_numpy(), g["predicted"].to_numpy())["f1"]
                          for _, g in predictions[predictions["config"] == config].groupby("repeat")]))


def e3_v2_section(base_folds):
    path = EXTENSIONS_DIR / "tuned_v2.csv"
    if not path.exists():
        return None
    tuned = pd.read_csv(path)
    baselines = pd.read_csv(RESULTS_DIR / "baselines.csv")
    untuned = baselines[baselines["variant"].isin(["strict", "extended"]) & baselines["model"].isin(["tree_full", "random_forest"])]
    lines = ["## E3 v2: grid contains the untuned default (run after the freeze)", "",
             "Same protocol as E3 v1 (15 folds, inner 3-fold stratified CV, seed 42, F1 selection, median imputation fitted on the training fold); the forest grid is now "
             "`n_estimators` in {100,300,500} x `max_depth` in {None,3,5} x `max_features` in {sqrt,0.3}, so it contains the untuned default (500, None, sqrt); the tree grid is unchanged and already contains the default (None, leaf 1). "
             "v1 results above are kept unchanged.", "",
             "| model | accuracy | precision | recall | F1 | pooled accuracy | pooled precision | pooled recall | pooled F1 [95% CI] |", "|---|---|---|---|---|---|---|---|---|"]
    for r in pd.concat([tuned, untuned]).itertuples():
        cells = " | ".join(f"{getattr(r, m + '_mean'):.3f} ± {getattr(r, m + '_std'):.3f}" for m in METRICS)
        pooled = " | ".join(f"{getattr(r, m + '_pooled_mean'):.3f}" for m in ("accuracy", "precision", "recall"))
        lines.append(f"| {r.variant}: {r.model} | {cells} | {pooled} | {r.f1_pooled_mean:.3f} [{r.f1_pooled_ci_low:.3f}, {r.f1_pooled_ci_high:.3f}] |")
    chosen = pd.read_csv(EXTENSIONS_DIR / "tuned_v2_hyperparameters.csv")
    lines += ["", "### Chosen hyperparameters (15 outer folds per row; full table in `tuned_v2_hyperparameters.csv`)", ""]
    for (variant, model), group in chosen.groupby(["variant", "model"], sort=False):
        parsed = group["params"].map(json.loads)
        default = FOREST_DEFAULT if model == "random_forest" else TREE_DEFAULT
        n_default = int(sum(p == default for p in parsed))
        lines.append(f"**{variant} {model}** (mean inner F1 {group['inner_f1'].mean():.3f}); untuned default `{json.dumps(default)}` chosen in {n_default} of {len(group)} folds: " +
                     "; ".join(f"{n}x `{p}`" for p, n in Counter(group["params"]).most_common()))
        for key in parsed.iloc[0]:
            lines.append(f"  - {key}: " + ", ".join(f"{v} ({n})" for v, n in Counter(str(p[key]) for p in parsed).most_common()))
        lines.append("")
    existing = pd.read_csv(RESULTS_DIR / "predictions.csv", dtype={"code": str})
    v2 = pd.read_csv(EXTENSIONS_DIR / "predictions_tuned_v2.csv", dtype={"code": str})
    extended = untuned_predictions("extended", base_folds)
    keep = ["G1_celoe_strict_disc_hv1_n0", "A1_celoe_extended_disc_hv1_n0", "strict_random_forest", "strict_tree_full"]
    all_predictions = pd.concat([existing[existing["config"].isin(keep)], extended, v2])
    pairs = [("tuned_v2_strict_random_forest", "strict_random_forest"), ("tuned_v2_strict_tree", "strict_tree_full"),
             ("tuned_v2_strict_random_forest", "G1_celoe_strict_disc_hv1_n0"), ("tuned_v2_strict_tree", "G1_celoe_strict_disc_hv1_n0"),
             ("tuned_v2_extended_random_forest", "extended_random_forest"), ("tuned_v2_extended_tree", "extended_tree_full"),
             ("tuned_v2_extended_random_forest", "A1_celoe_extended_disc_hv1_n0"), ("tuned_v2_extended_tree", "A1_celoe_extended_disc_hv1_n0")]
    lines += paired_table(all_predictions, pairs, 194, f"### Paired bootstrap (v2)\n\n{N_RESAMPLES} resamples of the 194 countries (seed {SEED}), same method as `results/compare.md`; "
                          "untuned extended predictions were refitted with the same seeds and match `results/baselines.csv` pooled F1 exactly.")
    return lines


def e1_importances(base_folds):
    folds = restrict(base_folds, "europe")
    lines = ["## E1 random forest feature importances (run after the freeze)", "",
             "Random forest of the Europe-only problem (500 trees, seed 42, median imputation), fitted on the training part of each of the 15 folds of the 41 countries; "
             "importance = `feature_importances_`, mean over the 15 fits (std over the 15 fits in the last column). Top 15 of each feature set; full lists in `results/extensions/e1_importances_<variant>.csv`.", ""]
    for variant in ("strict", "extended"):
        features = pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv").set_index("code")
        X, y = features.drop(columns="label"), features["label"]
        values = []
        for (repeat, fold), _ in folds.groupby(["repeat", "fold"]):
            train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
            model = models()["random_forest"]()
            model.fit(X.loc[train["code"]], y.loc[train["code"]])
            values.append(model[-1].feature_importances_)
        table = pd.DataFrame({"feature": X.columns, "mean importance": np.mean(values, axis=0), "std": np.std(values, axis=0, ddof=1)})
        table = table.sort_values("mean importance", ascending=False)
        table.to_csv(EXTENSIONS_DIR / f"e1_importances_{variant}.csv", index=False)
        top = table.head(15).copy()
        top.insert(0, "rank", range(1, 16))
        top["mean importance"] = top["mean importance"].map(lambda v: f"{v:.4f}")
        top["std"] = top["std"].map(lambda v: f"{v:.4f}")
        lines += [f"### {variant} features ({len(X.columns)} features)", ""] + md_table(top) + [""]
    return lines


def e5_section():
    path = EXTENSIONS_DIR / "kbonly.csv"
    if not path.exists():
        return None
    audit = pd.read_csv(EXTENSIONS_DIR / "feature_audit.csv", keep_default_na=False)
    kb = pd.read_csv(path)
    lines = ["## E5. Equal-information baselines (run after the freeze and after E1 to E4)", "",
             "### Feature audit (full table: `results/extensions/feature_audit.csv`)", "",
             "| group | features | source table | KB counterpart | form in the KB |", "|---|---|---|---|---|"]
    for (group, counterpart), part in audit.groupby(["group", "kb_counterpart"], sort=False):
        forms = "; ".join(sorted(set(part["kb_form"])))
        lines.append(f"| {group} | {len(part)} | {', '.join(sorted(set(part['source_table'])))} | {counterpart} | {forms} |")
    without = audit[audit["kb_counterpart"] == "no"]
    lines += ["", f"Baseline features **without a KB counterpart** ({len(without)} of {int((audit['in_extended']).sum())} extended-variant features): " +
              ", ".join(without["feature"]) + ".", "",
              f"KB information with no baseline column: {', '.join(audit.loc[audit['kb_counterpart'] == 'KB only', 'feature'])} (`gdpPerCapita`), "
              "the identities of neighbors, individual seas, all spoken languages (the baselines keep only the top language), and organizations with fewer than 3 labelled members are dropped from the baselines and from the kb-only sets alike.", "",
              "### KB-only feature sets", "",
              "`kb_raw`: raw values of the 8 KB numeric attributes (population, area, gdp, gdp per capita, inflation, infant mortality, population growth, airports; missing stays missing and is median-imputed on the training fold) "
              f"+ indicators for continent, the number of neighbors, seas, spoken languages, followed religions and ethnic groups (present in at least {MIN_INDICATOR} labelled countries) + organization membership indicators (same organizations as the baselines of that variant). "
              "`kb_binned`: the same, with the numeric attributes replaced by one-hot quartile bin classes from `kb/bins.json` (a missing value gives all zeros, as in the KB). "
              "Role indicators are 0 where the KB has no assertion. The main-language, main-religion and main-ethnic-group roles are not used. Untuned tree depth 3, full tree and 500-tree random forest, 15 folds.", "",
              "### Pooled results on the 194 countries (untuned baselines of `results/baselines.csv` repeated for reference)", "",
              "| features | model | n features | accuracy | precision | recall | F1 | pooled F1 [95% CI] |", "|---|---|---|---|---|---|---|---|"]
    baselines = pd.read_csv(RESULTS_DIR / "baselines.csv")

    def row(label, model, n, r):
        cells = " | ".join(f"{r[f'{m}_mean']:.3f} ± {r[f'{m}_std']:.3f}" for m in METRICS)
        return f"| {label} | {model} | {n} | {cells} | {r['f1_pooled_mean']:.3f} [{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}] |"

    for variant in ("strict", "extended"):
        for model in ("tree_depth3", "tree_full", "random_forest"):
            r = baselines[(baselines["variant"] == variant) & (baselines["model"] == model)].iloc[0]
            n = len(pd.read_csv(PROCESSED_DIR / f"features_{variant}.csv", nrows=0).columns) - 2
            lines.append(row(f"baseline {variant} (reference)", model, n, r))
        for kind in ("kb_raw", "kb_binned"):
            for model in ("tree_depth3", "tree_full", "random_forest"):
                r = kb[(kb["problem"] == "all") & (kb["variant"] == f"{kind}_{variant}") & (kb["model"] == model)].iloc[0]
                lines.append(row(f"{kind} {variant}", model, int(r["n_features"]), r))
    existing = pd.read_csv(RESULTS_DIR / "predictions.csv", dtype={"code": str})
    kb_predictions = pd.read_csv(EXTENSIONS_DIR / "predictions_kbonly.csv", dtype={"code": str})
    all_predictions = pd.concat([existing[existing["config"].isin([G1, A1, STRICT_FOREST])], kb_predictions])
    pairs = [("kbonly_kb_raw_strict_random_forest", STRICT_FOREST), ("kbonly_kb_binned_strict_random_forest", G1),
             ("kbonly_kb_raw_strict_random_forest", G1), ("kbonly_kb_binned_strict_tree_full", G1), ("kbonly_kb_binned_strict_tree_depth3", G1),
             ("kbonly_kb_raw_extended_random_forest", A1)]
    lines += [""] + paired_table(all_predictions, pairs, 194, f"### Paired bootstrap (194 countries)\n\n{N_RESAMPLES} resamples (seed {SEED}), same method as `results/compare.md`; difference first minus second. "
                                  "G1 and A1 are the stored CELOE results; the strict forest is the untuned baseline.")
    europe = kb[kb["problem"] == "europe"]
    e1 = pd.read_csv(E1_PREDICTIONS, dtype={"code": str})
    e1_all = pd.concat([e1, kb_predictions])
    e1a = GROUPS["E1"][0]["name"]
    lines += ["", "### Europe-only problem (E1: 41 countries, 14 European negatives), strict features", "",
              "Same subset and folds as E1; trained on the subset's training rows only. Specificity = share of the 14 European negatives classified correctly (pooled per repeat, mean over repeats).", "",
              "| features | model | n features | accuracy | precision | recall | F1 | pooled F1 [95% CI] | specificity |", "|---|---|---|---|---|---|---|---|---|"]
    for r in europe.to_dict("records"):
        config = f"kbonly_e1_{r['variant']}_{r['model']}"
        cells = " | ".join(f"{r[f'{m}_mean']:.3f} ± {r[f'{m}_std']:.3f}" for m in METRICS)
        lines.append(f"| {r['variant']} | {r['model']} | {int(r['n_features'])} | {cells} | {r['f1_pooled_mean']:.3f} [{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}] | {specificity(e1_all, config):.3f} |")
    for reference in ("e1_random_forest", "e1_tree_full", e1a):
        config = reference
        r = e1_all[e1_all["config"] == config]
        if config != e1a:
            lines.append(f"| baseline strict (E1 reference) | {config.removeprefix('e1_')} | | | | | | {pooled_f1_mean(e1_all, config):.3f} (pooled F1, point) | {specificity(e1_all, config):.3f} |")
        else:
            lines.append(f"| E1a CELOE (reference) | | | | | | | {pooled_f1_mean(e1_all, config):.3f} (pooled F1, point) | {specificity(e1_all, config):.3f} |")
    e1_pairs = [(f"kbonly_e1_{k}_strict_{m}", e1a) for k in ("kb_raw", "kb_binned") for m in ("random_forest", "tree_full")]
    lines += [""] + paired_table(e1_all, e1_pairs, 41, f"### Paired bootstrap on the 41 countries (vs E1a)\n\n{N_RESAMPLES} resamples (seed {SEED}), difference first minus second.")
    importances = pd.read_csv(EXTENSIONS_DIR / "e5_importances_e1_kb_raw_strict.csv").head(10)
    importances.insert(0, "rank", range(1, 11))
    importances["importance"] = importances["importance"].map(lambda v: f"{v:.4f}")
    lines += ["", "### Top 10 random forest feature importances, kb_raw strict features, Europe-only problem (mean over the 15 fits)", ""] + md_table(importances)
    return lines


def timeline(log):
    result = []
    for line in log.read_text(encoding="utf-8").splitlines():
        match = IMPROVEMENT_RE.match(line)
        if match:
            result.append((seconds(match.group(2)) if match.group(2) else None, match.group(3)))
    return result


def first_printed(runs_dir, name, repeat, fold, concept):
    log = runs_dir / name / "logs" / f"r{repeat}_f{fold}.log"
    if not log.exists():
        return "no log"
    for t, expression in timeline(log):
        if expression == concept:
            return f"{t:.1f}" if t is not None else "n/a"
    return "not printed as an improvement"


def e4_section(base_folds):
    stored_dir = RESULTS_DIR / "runs"
    pairs = [("E4a_celoe_strict_disc_hv1_n0_t300", G1, "G1 settings (hasValue on)"), ("E4b_celoe_strict_disc_hv0_n0_t300", G3, "G3 settings (hasValue off)")]
    lines = ["## E4. Longer time limit (run after the freeze)", "",
             "CELOE, strict KB, noise 0, 300 s, repeat 0 folds 0 to 4, 3 workers, compared with the stored 60 s results of the same folds (G1 and G3). "
             "With 3 workers sharing the machine, descriptions tested per second are lower than for a single run.", ""]
    rows, found = [], False
    for new_name, old_name, text in pairs:
        new = runs_of(new_name)
        if new is None:
            continue
        found = True
        old = read_runs(stored_dir / f"{old_name}.csv")
        old = old[(old["repeat"] == 0) & old["fold"].isin(new["fold"])]
        table = []
        for fold in sorted(new["fold"]):
            n, o = new[new["fold"] == fold].iloc[0], old[old["fold"] == fold].iloc[0]
            table.append({"fold": fold, "60 s concept": f"`{o['concept']}`", "300 s concept": f"`{n['concept']}`",
                          "changed": "no" if n["concept"] == o["concept"] else "yes",
                          "train acc 60 / 300": f"{o['train_accuracy']} / {n['train_accuracy']}",
                          "test F1 60 / 300": f"{float(o['test_f1']):.3f} / {float(n['test_f1']):.3f}",
                          "tested 60 / 300": f"{o['tested']} / {n['tested']}",
                          "final best first printed (s) 60 / 300": f"{first_printed(stored_dir, old_name, 0, fold, o['concept'])} / {first_printed(RUNS_DIR, new_name, 0, fold, n['concept'])}",
                          "algorithm s 300 run": f"{float(n['algorithm_seconds']):.1f}"})
        lines += [f"### {text}", ""] + md_table(pd.DataFrame(table))
        folds5 = base_folds[(base_folds["repeat"] == 0)]
        from src.aggregate import pooled_predictions
        f1 = {}
        for label, runs in (("60 s", old), ("300 s", new)):
            y, p = pooled_predictions(runs, folds5)[0]
            f1[label] = score(y, p)["f1"]
        changed = int((new["concept"].values != old.sort_values("fold")["concept"].values).sum()) if len(new) == len(old) else "n/a"
        lines += ["", f"Pooled test F1 over the 5 folds of repeat 0: 60 s {f1['60 s']:.3f}, 300 s {f1['300 s']:.3f}; best concept changed in {changed} of {len(new)} folds.", ""]
        rows.append((new_name, new, statistics(new, base_folds)))
    if not found:
        return None
    lines += ["### Grid table for the 300 s runs (5 folds of repeat 0 only)", ""] + main_table(rows)
    lines += [""] + concept_lines(rows, 300)
    return lines


def main():
    EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)
    base_folds = folds_all()
    lines = ["# Extensions E1 to E4 (run after the freeze at tag phase-3)", "",
             "Configurations were fixed before running and not changed after seeing results. Stored Phase 1 to 4 results are read, not modified. "
             "Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats (no std where there is one repeat); pooled F1 = out-of-fold predictions of all folds of a repeat, "
             "95% bootstrap (1000 resamples per repeat); concept length = number of names, constructors and numbers.", ""]
    for section in (e1_section(base_folds),):
        if section:
            lines += section + [""]
    for section in (e1_importances(base_folds) if runs_of(GROUPS["E1"][0]["name"]) is not None else None,):
        if section:
            lines += section + [""]
    for section in (e2_section(base_folds), ):
        if section:
            lines += section + [""]
    for section in (e3_section(), e3_v2_section(base_folds), e4_section(base_folds), e5_section()):
        if section:
            lines += section + [""]
    lines += ["## Odd things", ""] + [f"- {t}" for t in ODD_THINGS] + ["", "## Not done", ""] + [f"- {t}" for t in NOT_DONE]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
