import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import PROCESSED_DIR

DEFAULT_JAVA_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
DL_HOME = ROOT / "tools" / "dl-learner" / "dllearner-1.5.0"
SOURCE = ROOT / "scripts" / "java" / "ScoreConcept.java"
CLASS_DIR = ROOT / "tools" / "score_concept"
GENERATED_DIR = ROOT / "conf" / "generated"
OPEN_FLAGS = [
    "--add-opens", "java.base/java.lang.invoke=ALL-UNNAMED",
    "--add-opens", "java.base/java.lang=ALL-UNNAMED",
]
DEFAULT_KB = ROOT / "kb" / "mondial_extended_discretised.owl"


def java_home():
    return Path(os.environ.get("DLLEARNER_JAVA_HOME") or DEFAULT_JAVA_HOME)


def compile_if_needed():
    target = CLASS_DIR / "ScoreConcept.class"
    if target.exists() and target.stat().st_mtime >= SOURCE.stat().st_mtime:
        return
    CLASS_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(java_home() / "bin" / "javac.exe"), "-cp", str(DL_HOME / "lib" / "*"), "-d", str(CLASS_DIR), str(SOURCE)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"javac failed:\n{result.stdout}\n{result.stderr}")


def write_conf(kb, positives, negatives):
    key = hashlib.sha1(("|".join(positives) + "#" + "|".join(negatives) + str(kb)).encode()).hexdigest()[:10]
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_DIR / f"score_{key}.conf"
    block = lambda codes: "{ " + ", ".join(f'"m:{c}"' for c in codes) + " }"
    path.write_text(
        "\n".join([
            'prefixes = [ ("m","http://example.org/mondial#") ]',
            'ks.type = "OWL File"',
            f'ks.fileName = "{Path(kb).resolve().as_posix()}"',
            'reasoner.type = "closed world reasoner"',
            "reasoner.sources = { ks }",
            'lp.type = "posNegStandard"',
            f"lp.positiveExamples = {block(positives)}",
            f"lp.negativeExamples = {block(negatives)}",
        ]) + "\n",
        encoding="utf-8", newline="\n",
    )
    return path


def run_java(conf, kb, target):
    compile_if_needed()
    classpath = os.pathsep.join([str(CLASS_DIR), str(DL_HOME / "etc"), str(DL_HOME / "lib" / "*")])
    command = [
        str(java_home() / "bin" / "java.exe"), "-Xmx2g", *OPEN_FLAGS,
        f"-Dlog4j.configuration=file:{(DL_HOME / 'etc' / 'log4j.properties').as_posix()}",
        "-cp", classpath, "ScoreConcept", str(conf), str(Path(kb).resolve()), *target,
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DL_HOME)
    results, current = {}, None
    for line in result.stdout.splitlines():
        if line.startswith("SCORE_ITEM "):
            current = {}
            results[line[len("SCORE_ITEM "):]] = current
        elif line.startswith("SCORE_") and current is not None and line != "SCORE_END":
            key, _, value = line.partition(" ")
            current[key] = value.strip()
    if result.returncode != 0 or not results:
        raise RuntimeError(f"scoring failed (exit {result.returncode}):\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}")
    return results


def metrics(tp, fp, fn, tn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"accuracy": (tp + tn) / (tp + tn + fp + fn), "precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def score(kb, concept, positives, negatives):
    entry = run_java(write_conf(kb, positives, negatives), kb, [concept])["single"]
    if "SCORE_ERROR" in entry:
        raise RuntimeError(entry["SCORE_ERROR"])
    sets = {key: set(entry[f"SCORE_{key}"].split()) for key in ("TP", "FP", "FN", "TN")}
    if not (sets["TP"] | sets["FN"] == set(positives) and sets["FP"] | sets["TN"] == set(negatives)):
        raise RuntimeError(f"scored sets do not partition the test examples: {sets}")
    return {
        "expression": entry["SCORE_EXPRESSION"],
        **metrics(*(len(sets[k]) for k in ("TP", "FP", "FN", "TN"))),
        "true_positives": sorted(sets["TP"]),
        "false_positives": sorted(sets["FP"]),
        "false_negatives": sorted(sets["FN"]),
    }


def labelled_examples():
    positives = sorted(pd.read_csv(PROCESSED_DIR / "eu_positives.csv", dtype=str, keep_default_na=False)["code"])
    negatives = sorted(pd.read_csv(PROCESSED_DIR / "eu_negatives.csv", dtype=str, keep_default_na=False)["code"])
    return positives, negatives


def test_examples(repeat, fold):
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    test = folds[(folds["repeat"] == repeat) & (folds["fold"] == fold)]
    return sorted(test.loc[test["label"] == 1, "code"]), sorted(test.loc[test["label"] == 0, "code"])


def batch_score(items):
    positives, negatives = labelled_examples()
    results = [None] * len(items)
    by_kb = {}
    for index, item in enumerate(items):
        by_kb.setdefault(str(Path(item["kb"]).resolve()), []).append(index)
    for kb, indices in by_kb.items():
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1((kb + "".join(items[i]["concept"] for i in indices)).encode()).hexdigest()[:10]
        batch_file = GENERATED_DIR / f"batch_{key}.tsv"
        batch_file.write_text(
            "".join(f"{i}\t{items[i]['concept']}\n" for i in indices), encoding="utf-8", newline="\n"
        )
        entries = run_java(write_conf(kb, positives, negatives), kb, ["--batch", str(batch_file)])
        for i in indices:
            entry = entries[str(i)]
            if "SCORE_ERROR" in entry:
                results[i] = {"error": entry["SCORE_ERROR"]}
                continue
            covered = set(entry["SCORE_TP"].split()) | set(entry["SCORE_FP"].split())
            test_pos, test_neg = test_examples(int(items[i]["repeat"]), int(items[i]["fold"]))
            tp, fp = sorted(set(test_pos) & covered), sorted(set(test_neg) & covered)
            fn, tn = sorted(set(test_pos) - covered), sorted(set(test_neg) - covered)
            results[i] = {
                "expression": entry["SCORE_EXPRESSION"],
                **metrics(len(tp), len(fp), len(fn), len(tn)),
                "true_positives": tp, "false_positives": fp, "false_negatives": fn,
                "covered": sorted(covered),
            }
    return results


def load_items(path):
    path = Path(path)
    frame = pd.read_json(path, dtype=False) if path.suffix == ".json" else pd.read_csv(path, dtype=str, keep_default_na=False)
    return frame.to_dict("records")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--concept")
    parser.add_argument("--repeat", type=int)
    parser.add_argument("--fold", type=int)
    parser.add_argument("--items", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.items:
        items = load_items(args.items)
        for item in items:
            item.setdefault("kb", str(args.kb))
        results = batch_score(items)
        rows = []
        for item, result in zip(items, results):
            row = {**item}
            row.update({k: v for k, v in result.items() if k not in ("true_positives", "covered")})
            row["false_positives"] = " ".join(result.get("false_positives", []))
            row["false_negatives"] = " ".join(result.get("false_negatives", []))
            rows.append(row)
        table = pd.DataFrame(rows)
        if args.out:
            table.to_csv(args.out, index=False)
        print(table.to_string(index=False))
        return

    positives, negatives = test_examples(args.repeat, args.fold)
    print(json.dumps(score(args.kb, args.concept, positives, negatives), indent=2))


if __name__ == "__main__":
    main()
