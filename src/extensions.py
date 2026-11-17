import json
import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

from baselines.run_baselines import METRICS, models, score, summarize
from src.aggregate import read_runs, statistics
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
STRICT_FOREST = "strict_random_forest"
BIN_RE = re.compile(r"[A-Za-z]+Q\d")
ATTRIBUTE_PREFIX = {"Population": "population", "Area": "area", "Gdp": "gdp", "GdpPerCapita": "gdp_per_capita", "Inflation": "inflation",
                    "InfantMortality": "infant_mortality", "PopulationGrowth": "population_growth", "NAirports": "n_airports"}
ODD_THINGS = []
NOT_DONE = []


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
    lines = ["## E3. Tuned baselines (run after the freeze)", "",
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
    for section in (e2_section(base_folds), ):
        if section:
            lines += section + [""]
    for section in (e3_section(), e4_section(base_folds)):
        if section:
            lines += section + [""]
    lines += ["## Odd things", ""] + [f"- {t}" for t in ODD_THINGS] + ["", "## Not done", ""] + [f"- {t}" for t in NOT_DONE]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
