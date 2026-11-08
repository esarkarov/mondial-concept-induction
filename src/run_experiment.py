import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from score_concept import batch_score
from src.config import FOLD_REPEATS, KB_DIR, KB_MEMBERSHIP_VARIANTS, N_FOLDS, PROCESSED_DIR
from src.make_conf import GENERATED_DIR, render

RUNS_DIR = ROOT / "results" / "runs"
WRAPPER = ROOT / "scripts" / "run_dllearner.ps1"
MIN_REFERENCE_POSITIVES = 25

SOLUTION_RE = re.compile(r"^(\d+): (.*) \(pred\. acc\.: ([\d,.]+)%, F-measure: ([\d,.]+)%\)\s*$")
OCEL_SOLUTION_RE = re.compile(r"^(\d+): (.*) \(accuracy ([\d,.]+)%, length (\d+), depth \d+\)\s*$")
TERMINATED_RE =re.compile(r"Algorithm terminated[^(]*\(time: (.*?), (\d+) descriptions tested")
STOPPED_RE = re.compile(r"Algorithm stopped \((\d+) descriptions tested")
IMPROVEMENT_RE = re.compile(r"^more accurate \(([\d,.]+)%\) class expression found(?: after [^:]*)?: (.*)$")
PROGRESS_RE = re.compile(r"^\[[=. ]+\] *\d+%")
DURATION_RE = re.compile(r"(?:(\d+)m )?(?:(\d+)s )?(?:(\d+)ms)?")
TOKEN_RE = re.compile(r"[A-Za-z_][\w.\-]*|\d+(?:\.\d+)?|\[[^\]]*\]")

COLUMNS = [
    "config", "repeat", "fold", "concept", "length", "train_accuracy", "tested", "algorithm_seconds", "wall_seconds",
    "test_accuracy", "test_precision", "test_recall", "test_f1", "tp", "fp", "fn", "tn",
    "nearest_reference", "jaccard", "false_positives", "false_negatives", "top3",
]


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def kb_path(args):
    return KB_DIR / f"mondial_{args.membership}_{args.numeric}.owl"


def ensure_kb(args):
    path = kb_path(args)
    if not path.exists():
        subprocess.run(
            [sys.executable, "-m", "src.kb", "--membership", args.membership, "--numeric", args.numeric],
            check=True, cwd=ROOT, capture_output=True, text=True,
        )
    return path


def duration_seconds(text):
    minutes, seconds, millis = DURATION_RE.fullmatch(text.strip()).groups()
    return int(minutes or 0) * 60 + int(seconds or 0) + int(millis or 0) / 1000


def concept_length(expression):
    return len(TOKEN_RE.findall(expression))


def decimal(text):
    return float(text.replace(",", "."))


def parse_output(lines, time_limit):
    solutions = [m.groups() for m in map(SOLUTION_RE.match, lines) if m]
    terminated = next((m for m in map(TERMINATED_RE.search, lines) if m), None)
    if terminated:
        algorithm_seconds, tested = duration_seconds(terminated.group(1)), int(terminated.group(2))
    else:
        stopped = next((m for m in map(STOPPED_RE.search, lines) if m), None)
        algorithm_seconds, tested = (float(time_limit), int(stopped.group(1))) if stopped else (None, None)
    if solutions:
        top = [{"concept": s[1], "train_accuracy": decimal(s[2])} for s in solutions[:3]]
    else:
        reported = [(m.group(2), decimal(m.group(3)), int(m.group(4))) for m in map(OCEL_SOLUTION_RE.match, lines) if m]
        reported += [(m.group(2), decimal(m.group(1)), concept_length(m.group(2))) for m in map(IMPROVEMENT_RE.match, lines) if m]
        ranked, seen = [], set()
        for concept, accuracy, length in sorted(reported, key=lambda item: (-item[1], item[2])):
            if concept not in seen:
                seen.add(concept)
                ranked.append({"concept": concept, "train_accuracy": accuracy})
        top = ranked[:3]
    return top, algorithm_seconds, tested


def learn(args, repeat, fold, run_dir):
    state_file = run_dir / f"r{repeat}_f{fold}.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    conf_args = SimpleNamespace(
        repeat=repeat, fold=fold, algorithm=args.algorithm, time=args.time, noise=args.noise,
        use_negation=True, use_all=True, use_cardinality=True, use_has_value=args.has_value, max_depth=args.max_depth,
    )
    text, _, _ = render(conf_args, Path("..", "..", "kb", kb_path(args).name).as_posix())
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    conf = GENERATED_DIR / f"exp_{args.name}_r{repeat}_f{fold}.conf"
    conf.write_text(text, encoding="utf-8", newline="\n")
    start = time.time()
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(WRAPPER), str(conf)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    wall = time.time() - start
    lines = [l for l in (result.stdout + result.stderr).splitlines() if not PROGRESS_RE.match(l) and l.strip()]
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs" / f"r{repeat}_f{fold}.log").write_text("\n".join(lines), encoding="utf-8")
    top, algorithm_seconds, tested = parse_output(lines, args.time)
    state = {"repeat": repeat, "fold": fold, "top": top, "algorithm_seconds": algorithm_seconds, "tested": tested,
             "wall_seconds": wall, "exit": result.returncode}
    if top:
        state_file.write_text(json.dumps(state), encoding="utf-8")
    return state


def reference_sets():
    positives = set(read_csv(PROCESSED_DIR / "eu_positives.csv")["code"])
    labelled = positives | set(read_csv(PROCESSED_DIR / "eu_negatives.csv")["code"])
    encompasses = read_csv(PROCESSED_DIR / "csv" / "encompasses.csv")
    europe = set(encompasses.loc[encompasses["Continent"] == "Europe", "Country"]) & labelled
    sets = {"Europe": europe}
    members = read_csv(PROCESSED_DIR / "csv" / "ismember.csv")
    for org, group in members.groupby("Organization"):
        countries = set(group["Country"]) & labelled
        if org != "EU" and len(countries & positives) >= MIN_REFERENCE_POSITIVES:
            sets[f"org_{org}"] = countries
            sets[f"Europe and org_{org}"] = europe & countries
    return sets


def nearest_reference(covered, references):
    best, best_score = None, -1.0
    for name in sorted(references):
        union = covered | references[name]
        score = len(covered & references[name]) / len(union) if union else 1.0
        if score > best_score:
            best, best_score = name, score
    return best, best_score


def existing_rows(csv_path):
    if not csv_path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(csv_path, dtype={"repeat": int, "fold": int})


def append_rows(csv_path, rows):
    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)


def score_finished(args, states, csv_path, references):
    items = [{"kb": str(kb_path(args)), "repeat": s["repeat"], "fold": s["fold"], "concept": s["top"][0]["concept"]}
             for s in states]
    results = batch_score(items)
    rows = []
    for state, result in zip(states, results):
        if "error" in result:
            print(f"  scoring failed for repeat {state['repeat']} fold {state['fold']}: {result['error']}")
            continue
        reference, jaccard = nearest_reference(set(result["covered"]), references)
        concept = state["top"][0]["concept"]
        rows.append({
            "config": args.name, "repeat": state["repeat"], "fold": state["fold"], "concept": concept,
            "length": concept_length(concept), "train_accuracy": state["top"][0]["train_accuracy"],
            "tested": state["tested"], "algorithm_seconds": state["algorithm_seconds"],
            "wall_seconds": round(state["wall_seconds"], 1),
            "test_accuracy": result["accuracy"], "test_precision": result["precision"],
            "test_recall": result["recall"], "test_f1": result["f1"],
            "tp": result["tp"], "fp": result["fp"], "fn": result["fn"], "tn": result["tn"],
            "nearest_reference": reference, "jaccard": round(jaccard, 4),
            "false_positives": " ".join(result["false_positives"]),
            "false_negatives": " ".join(result["false_negatives"]),
            "top3": json.dumps(state["top"]),
        })
    append_rows(csv_path, rows)
    return rows


def parse_list(text, default):
    return default if text is None else [int(x) for x in text.split(",")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--algorithm", choices=["celoe", "ocel"], default="celoe")
    parser.add_argument("--membership", choices=KB_MEMBERSHIP_VARIANTS, default="extended")
    parser.add_argument("--numeric", choices=["discretised", "datatype"], default="discretised")
    parser.add_argument("--has-value", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--time", type=int, default=60)
    parser.add_argument("--max-depth", type=float, default=None)
    parser.add_argument("--repeats")
    parser.add_argument("--folds")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    ensure_kb(args)
    repeats = parse_list(args.repeats, list(range(FOLD_REPEATS)))
    folds = parse_list(args.folds, list(range(N_FOLDS)))
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = RUNS_DIR / args.name
    run_dir.mkdir(exist_ok=True)
    csv_path = RUNS_DIR / f"{args.name}.csv"

    done = existing_rows(csv_path)
    finished = set(zip(done["repeat"], done["fold"]))
    todo = [(r, f) for r in repeats for f in folds if (r, f) not in finished]
    print(f"{args.name}: {len(todo)} to run, {len(finished)} already finished; workers={args.workers}", flush=True)
    if not todo:
        return

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        states = list(pool.map(lambda rf: learn(args, rf[0], rf[1], run_dir), todo))
    learned = [s for s in states if s["top"]]
    for s in states:
        if not s["top"]:
            print(f"  no concept for repeat {s['repeat']} fold {s['fold']} (exit {s['exit']}); see {run_dir / 'logs'}")
    print(f"learning finished in {time.time() - start:.1f}s", flush=True)
    rows = score_finished(args, learned, csv_path, reference_sets())
    print(f"wrote {len(rows)} rows to {csv_path} (total time {time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
