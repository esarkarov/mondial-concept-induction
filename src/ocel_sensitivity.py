import pandas as pd

from src.aggregate import read_runs, statistics
from src.config import FOLD_REPEATS, KB_DIR, N_FOLDS, PROCESSED_DIR, RESULTS_DIR
from src.grid_extras import OCEL_ALT_PATH
from src.run_experiment import OCEL_SOLUTION_RE, RUNS_DIR
from src.run_grid import SUITES, config_name
from score_concept import batch_score


def first_listed(log_path):
    for line in log_path.read_text(encoding="utf-8").splitlines():
        match = OCEL_SOLUTION_RE.match(line)
        if match:
            return match.group(2), float(match.group(3).replace(",", "."))
    return None, None


def main():
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    details, summary = [], []
    for c in SUITES["main"]["configs"]:
        if c["algorithm"] != "ocel":
            continue
        name = config_name(c)
        main_runs = read_runs(RUNS_DIR / f"{name}.csv")
        kb = KB_DIR / f"mondial_{c['membership']}_{c['numeric']}.owl"
        items, meta = [], []
        for repeat in range(FOLD_REPEATS):
            for fold in range(N_FOLDS):
                main_concept = main_runs[(main_runs["repeat"] == repeat) & (main_runs["fold"] == fold)]["concept"].iloc[0]
                alt, accuracy = first_listed(RUNS_DIR / name / "logs" / f"r{repeat}_f{fold}.log")
                items.append({"kb": str(kb), "repeat": repeat, "fold": fold, "concept": alt or main_concept})
                meta.append((repeat, fold, main_concept, alt, accuracy))
        results = batch_score(items)
        rows = []
        for (repeat, fold, main_concept, alt, accuracy), result in zip(meta, results):
            if "error" in result:
                raise RuntimeError(f"{name} repeat {repeat} fold {fold}: {result['error']}")
            rows.append({
                "config": name, "repeat": repeat, "fold": fold, "has_list": alt is not None,
                "main_concept": main_concept, "alt_concept": alt or main_concept, "differs": alt is not None and alt != main_concept,
                "alt_train_accuracy": accuracy, "test_accuracy": result["accuracy"], "test_precision": result["precision"],
                "test_recall": result["recall"], "test_f1": result["f1"], "tp": result["tp"], "fp": result["fp"], "fn": result["fn"],
                "tn": result["tn"], "false_positives": " ".join(result["false_positives"]),
                "false_negatives": " ".join(result["false_negatives"]),
            })
        alt_runs = pd.DataFrame(rows)
        details.append(alt_runs)
        main_stats = statistics(main_runs, folds)
        alt_stats = statistics(alt_runs, folds)
        summary.append({
            "config": name, "with_list": int(alt_runs["has_list"].sum()), "without_list": int((~alt_runs["has_list"]).sum()),
            "differs": int(alt_runs["differs"].sum()), "pooled_f1_main": main_stats["pooled"]["f1"][0],
            "pooled_f1_alt": alt_stats["pooled"]["f1"][0], "ci_low": alt_stats["ci"][0], "ci_high": alt_stats["ci"][1],
        })
    pd.concat(details).to_csv(OCEL_ALT_PATH, index=False)
    table = pd.DataFrame(summary)
    table.to_csv(RESULTS_DIR / "ocel_alt_summary.csv", index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
