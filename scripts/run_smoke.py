import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from score_concept import DEFAULT_KB, score, test_examples
from src.config import PROCESSED_DIR

LOG_DIR = ROOT / "results" / "smoke_logs"
REPORT = ROOT / "results" / "smoke_phase2b.md"
REPEAT, FOLD, TIME_LIMIT = 0, 0, 60

RUNS = [
    ("celoe_hv0_noise0", ["--algorithm", "celoe", "--noise", "0", "--no-use-has-value"]),
    ("celoe_hv1_noise0", ["--algorithm", "celoe", "--noise", "0", "--use-has-value"]),
    ("celoe_hv0_noise10", ["--algorithm", "celoe", "--noise", "10", "--no-use-has-value"]),
    ("ocel_hv0_noise0", ["--algorithm", "ocel", "--noise", "0", "--no-use-has-value"]),
]

SOLUTION_RE = re.compile(r"^(\d+): (.*) \(pred\. acc\.: ([\d,.]+)%, F-measure: ([\d,.]+)%\)\s*$")
TERMINATED_RE = re.compile(r"Algorithm terminated[^(]*\(time: (.*?), (\d+) descriptions tested")
STOPPED_RE = re.compile(r"Algorithm stopped \((\d+) descriptions tested")
IMPROVEMENT_RE = re.compile(r"^more accurate \(([\d,.]+)%\) class expression found(?: after [^:]*)?: (.*)$")
PROGRESS_RE =re.compile(r"^\[[=. ]+\] *\d+%")
KEYWORDS = {"and", "or", "not", "some", "only", "value", "min", "max", "exactly", "Thing", "Nothing"}


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def concept_length(expression):
    tokens = re.findall(r"[A-Za-z_][\w.\-]*|\d+(?:\.\d+)?|\[[^\]]*\]", expression)
    return len(tokens)


def atoms(expression):
    return sorted({t for t in re.findall(r"[A-Za-z_][\w.\-]*", expression) if t not in KEYWORDS})


def reference_sets():
    enc = read_csv(PROCESSED_DIR / "csv" / "encompasses.csv")
    sets = {"Europe": set(enc.loc[enc["Continent"] == "Europe", "Country"])}
    members = read_csv(PROCESSED_DIR / "ismember_masked_extended.csv")
    for org, group in members.groupby("Organization"):
        sets[f"org_{org}"] = set(group["Country"])
    for org, group in members.groupby("Organization"):
        sets[f"Europe and org_{org}"] = sets["Europe"] & set(group["Country"])
    return sets


def extension_comparison(kb, expression, labelled, references):
    codes = sorted(labelled)
    result = score(kb, expression, codes, [])
    predicted = set(result["true_positives"])
    best = max(references, key=lambda name: len(predicted & references[name]) / max(1, len(predicted | references[name])))
    jaccard = len(predicted & references[best]) / max(1, len(predicted | references[best]))
    exact = [name for name, ref in references.items() if (ref & set(codes)) == predicted]
    return len(predicted), best, jaccard, exact


def run_one(name, extra, labelled, references):
    conf_name = f"smoke_{name}"
    subprocess.run(
        [sys.executable, "-m", "src.make_conf", "--repeat", str(REPEAT), "--fold", str(FOLD), "--time", str(TIME_LIMIT),
         "--name", conf_name, *extra],
        check=True, cwd=ROOT, capture_output=True, text=True,
    )
    conf = ROOT / "conf" / "generated" / f"{conf_name}.conf"
    start = time.time()
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "run_dllearner.ps1"), str(conf)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    wall = time.time() - start
    raw = [line for line in (result.stdout + result.stderr).splitlines() if not PROGRESS_RE.match(line) and line.strip()]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{name}.log").write_text("\n".join(raw), encoding="utf-8")

    solutions = [m.groups() for m in map(SOLUTION_RE.match, raw) if m]
    terminated = next((m for m in map(TERMINATED_RE.search, raw) if m), None)
    record = {"name": name, "wall": wall, "exit": result.returncode, "raw": raw, "solutions": solutions}
    record["algorithm_time"], record["tested"] = (terminated.group(1), terminated.group(2)) if terminated else ("n/a", "n/a")
    if not solutions:
        stopped = next((m for m in map(STOPPED_RE.search, raw) if m), None)
        improvements = [m.groups() for m in map(IMPROVEMENT_RE.match, raw) if m]
        if stopped and improvements:
            record["algorithm_time"], record["tested"] = f">= {TIME_LIMIT}s (limit reached)", stopped.group(1)
            record["note"] = "no solutions list printed (terminateOnNoiseReached with noise 0); best expression found so far is scored"
            solutions = [("best", improvements[-1][1], improvements[-1][0], "n/a")]
            record["solutions"] = solutions
        else:
            record["error"] = "\n".join(raw[-15:])
            return record
    positives, negatives = test_examples(REPEAT, FOLD)
    record["scores"] = []
    for _, expression, accuracy, fmeasure in solutions[:3]:
        scored = score(DEFAULT_KB, expression, positives, negatives)
        record["scores"].append(scored)
    best = solutions[0][1]
    record["extension"] = extension_comparison(DEFAULT_KB, best, labelled, references)
    return record


def format_record(record, labelled_count):
    lines = [f"## {record['name']}", ""]
    if "error" in record:
        return lines + ["Did not produce solutions. Last output lines:", "", "```", record["error"], "```", ""]
    lines += [
        f"- DL-Learner algorithm time: {record['algorithm_time']}; descriptions tested: {record['tested']}; "
        f"wall clock including JVM start-up: {record['wall']:.1f} s",
        "",
        (f"- {record['note']}\n" if "note" in record else ""),
        "| # | concept | length | train acc % | test acc | test P | test R | test F1 | FP | FN |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for (rank, expression, accuracy, _), scored in zip(record["solutions"][:3], record["scores"]):
        lines.append(
            f"| {rank} | `{expression}` | {concept_length(expression)} | {accuracy} | {scored['accuracy']:.3f} | "
            f"{scored['precision']:.3f} | {scored['recall']:.3f} | {scored['f1']:.3f} | "
            f"{', '.join(scored['false_positives']) or '-'} | {', '.join(scored['false_negatives']) or '-'} |"
        )
    size, best, jaccard, exact = record["extension"]
    lines += [
        "",
        f"- Best concept atoms: {', '.join(atoms(record['solutions'][0][1]))}",
        f"- Extension of the best concept over the {labelled_count} labelled countries: {size} predicted positives; "
        f"closest reference `{best}` (Jaccard {jaccard:.3f}); identical to: {', '.join(exact) or 'none'}",
        "",
    ]
    return lines


def main():
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    labelled = sorted(set(folds["code"]))
    references = reference_sets()
    positives, negatives = test_examples(REPEAT, FOLD)
    report = [
        "# Phase 2B smoke runs",
        "",
        f"Repeat {REPEAT}, fold {FOLD}, time limit {TIME_LIMIT} s, KB `{DEFAULT_KB.name}`, closed world reasoner. "
        f"Test fold: {len(positives)} positives, {len(negatives)} negatives. Test scores come from `scripts/score_concept.py` "
        "(same ClosedWorldReasoner as training). Concept length = number of names, constructors and numbers (parentheses not counted).",
        "",
    ]
    records = []
    for name, extra in RUNS:
        print(f"running {name} ...", flush=True)
        record = run_one(name, extra, labelled, references)
        records.append(record)
        print(f"  done: wall {record['wall']:.1f}s", flush=True)
        report += format_record(record, len(labelled))
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
