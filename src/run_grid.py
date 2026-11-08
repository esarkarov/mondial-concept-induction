import argparse
import subprocess
import sys
import time
from collections import Counter

import pandas as pd

from src.aggregate import read_runs, statistics
from src.config import FOLD_REPEATS, N_FOLDS, PROCESSED_DIR, RESULTS_DIR
from src.run_experiment import ROOT, RUNS_DIR

TIME_LIMIT = 60
WORKERS = 3
OVERRUN_SECONDS = 5
NUMERIC_SHORT = {"discretised": "disc", "datatype": "dt"}


def config(label, algorithm, has_value, noise, membership="strict", numeric="discretised", reasoner="cwr", closure=False):
    return {"label": label, "algorithm": algorithm, "has_value": has_value, "noise": noise,
            "membership": membership, "numeric": numeric, "reasoner": reasoner, "closure": closure}


SUITES = {
    "main": {
        "configs": [
            config("G1", "celoe", True, 0), config("G2", "celoe", True, 10),
            config("G3", "celoe", False, 0), config("G4", "celoe", False, 10),
            config("G5", "ocel", True, 0), config("G6", "ocel", True, 10),
            config("G7", "ocel", False, 0), config("G8", "ocel", False, 10),
        ],
        "report": RESULTS_DIR / "grid_main.md",
        "title": "Main grid (strict KB, discretised, 60 s, 3 workers, repeats 0 to 2)",
        "baseline_variants": ["strict", "reference"],
    },
    "ablations": {
        "configs": [
            config("A1", "celoe", True, 0, membership="extended"),
            config("A2", "celoe", True, 0, membership="masked"),
            config("A3", "celoe", True, 0, membership="none"),
            config("A4", "celoe", True, 0, membership="strict", numeric="datatype"),
        ],
        "report": RESULTS_DIR / "grid_ablations.md",
        "title": "Ablations (CELOE, hasValue on, noise 0, 60 s, 3 workers, repeats 0 to 2); G1 is the reference row",
        "baseline_variants": ["masked", "extended", "none", "strict", "reference"],
    },
    "owa": {
        "configs": [
            config("O1", "celoe", True, 0, reasoner="pellet"),
            config("O2", "celoe", True, 0, reasoner="pellet", closure=True),
        ],
        "report": RESULTS_DIR / "grid_owa.md",
        "title": "OWA vs CWA (CELOE, strict KB, discretised, hasValue on, noise 0, 60 s, Pellet via the OWL API reasoner); G1 is the reference row",
        "baseline_variants": ["strict", "reference"],
    },
}


def config_name(c):
    return (f"{c['label']}_{c['algorithm']}_{c['membership']}_{NUMERIC_SHORT[c['numeric']]}"
            f"_hv{int(c['has_value'])}_n{c['noise']}"
            + ("" if c["reasoner"] == "cwr" else f"_{c['reasoner']}") + ("_closure" if c["closure"] else ""))


def run_config(c, repeats=None):
    command = [
        sys.executable, "-m", "src.run_experiment", "--name", config_name(c), "--algorithm", c["algorithm"],
        "--membership", c["membership"], "--numeric", c["numeric"],
        "--has-value" if c["has_value"] else "--no-has-value", "--noise", str(c["noise"]),
        "--time", str(TIME_LIMIT), "--workers", str(WORKERS), "--reasoner", c["reasoner"],
    ]
    if c["closure"]:
        command.append("--closure")
    if repeats:
        command += ["--repeats", repeats]
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] {config_name(c)} ...", flush=True)
    subprocess.run(command, cwd=ROOT, check=False)
    print(f"[{time.strftime('%H:%M:%S')}] {config_name(c)} finished in {time.time() - start:.0f}s", flush=True)


def fmt(mean_std):
    mean, std = mean_std
    return f"{mean:.3f} ± {std:.3f}" if pd.notna(std) else f"{mean:.3f}"


def main_table(rows):
    lines = [
        "| config | folds | accuracy | precision | recall | F1 | pooled F1 [95% CI] | mean length | mean tested | mean algorithm s |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, runs, stats in rows:
        low, high = stats["ci"]
        lines.append(
            f"| {name} | {len(runs)}/{FOLD_REPEATS * N_FOLDS} | " + " | ".join(fmt(stats["per_fold"][m]) for m in ("accuracy", "precision", "recall", "f1"))
            + f" | {stats['pooled']['f1'][0]:.3f} [{low:.3f}, {high:.3f}] | {runs['length'].mean():.1f} | "
            f"{runs['tested'].mean():.0f} | {runs['algorithm_seconds'].mean():.1f} |"
        )
    return lines


def baseline_table(baselines_path, variants):
    baselines = pd.read_csv(baselines_path)
    wanted = baselines[baselines["variant"].isin(variants)]
    lines = [
        "| model | accuracy | precision | recall | F1 | pooled F1 [95% CI] |",
        "|---|---|---|---|---|---|",
    ]
    for r in wanted.itertuples():
        cells = " | ".join(f"{getattr(r, m + '_mean'):.3f} ± {getattr(r, m + '_std'):.3f}" for m in ("accuracy", "precision", "recall", "f1"))
        lines.append(
            f"| {r.variant}: {r.model} | {cells} | {r.f1_pooled_mean:.3f} [{r.f1_pooled_ci_low:.3f}, {r.f1_pooled_ci_high:.3f}] |"
        )
    return lines


def details(name, runs, time_limit):
    lines = [f"### {name}", ""]
    expected = {(r, f) for r in range(FOLD_REPEATS) for f in range(N_FOLDS)}
    missing = sorted(expected - set(zip(runs["repeat"], runs["fold"])))
    lines.append(f"- missing folds (no concept or scoring failure): {missing if missing else 'none'}")
    overrun = runs[(runs["algorithm_seconds"] > time_limit + OVERRUN_SECONDS)]
    lines.append(f"- algorithm time above {time_limit + OVERRUN_SECONDS} s: "
                 f"{[(r.repeat, r.fold, r.algorithm_seconds) for r in overrun.itertuples()] or 'none'}")
    lines.append(f"- algorithm time range: {runs['algorithm_seconds'].min():.1f} to {runs['algorithm_seconds'].max():.1f} s; "
                 f"wall range: {runs['wall_seconds'].min():.1f} to {runs['wall_seconds'].max():.1f} s")
    lines += ["- three most frequent concepts:"]
    for concept, count in Counter(runs["concept"]).most_common(3):
        lines.append(f"  - {count}x `{concept}`")
    lines.append("- nearest reference (count): " + ", ".join(f"{k} ({v})" for k, v in Counter(runs["nearest_reference"]).most_common()))
    lines.append(f"- concept length min/median/max: {runs['length'].min()}/{runs['length'].median():.0f}/{runs['length'].max()}; "
                 f"mean train accuracy {runs['train_accuracy'].mean():.2f}; jaccard to nearest reference min/mean: "
                 f"{runs['jaccard'].min():.2f}/{runs['jaccard'].mean():.2f}")
    lines.append("")
    return lines


def load_rows(configs, folds):
    rows = []
    for c in configs:
        path = RUNS_DIR / f"{config_name(c)}.csv"
        if path.exists():
            runs = read_runs(path)
            if len(runs):
                rows.append((config_name(c), runs, statistics(runs, folds)))
    return rows


def write_report(suite_name):
    from src.grid_extras import census_lines, ocel_sensitivity_lines
    suite = SUITES[suite_name]
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    rows = load_rows(suite["configs"], folds)
    if suite_name in ("ablations", "owa"):
        rows = load_rows(SUITES["main"]["configs"][:1], folds) + rows
    lines = [
        f"# {suite['title']}", "",
        "Per-fold columns: mean over the folds of a repeat, then mean ± std over repeats. "
        "Pooled F1: out-of-fold predictions of all folds of a repeat, mean over repeats; the interval is the 95% bootstrap "
        "(1000 resamples per repeat, bounds averaged over repeats). Concept length = number of names, constructors and numbers.", "",
        "## Learned concepts", "",
    ]
    lines += main_table(rows)
    lines += ["", "## Baselines (same folds)", "",
              "The rule rows use the full unmasked `isMember` data; they are rules, not learned models.", ""]
    lines += baseline_table(RESULTS_DIR / "baselines.csv", suite["baseline_variants"])
    lines += ["", "## Atom census", ""]
    lines += census_lines(rows)
    if suite_name == "main":
        lines += ["", "## OCEL rule sensitivity", ""]
        lines += ocel_sensitivity_lines()
    lines += ["", "## Per-config details", ""]
    for name, runs, _ in rows:
        lines += details(name, runs, TIME_LIMIT)
    suite["report"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {suite['report']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=list(SUITES), default="main")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--only")
    parser.add_argument("--repeats")
    args = parser.parse_args()
    if not args.report_only:
        start = time.time()
        for c in SUITES[args.suite]["configs"]:
            if args.only is None or c["label"] in args.only.split(","):
                run_config(c, args.repeats)
        print(f"grid finished in {(time.time() - start) / 60:.1f} min", flush=True)
    write_report(args.suite)


if __name__ == "__main__":
    main()
