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


def run_java(conf, kb, concept):
    compile_if_needed()
    classpath = os.pathsep.join([str(CLASS_DIR), str(DL_HOME / "etc"), str(DL_HOME / "lib" / "*")])
    command = [
        str(java_home() / "bin" / "java.exe"), "-Xmx2g", *OPEN_FLAGS,
        f"-Dlog4j.configuration=file:{(DL_HOME / 'etc' / 'log4j.properties').as_posix()}",
        "-cp", classpath, "ScoreConcept", str(conf), str(Path(kb).resolve()), concept,
    ]
    result = subprocess.run(command, capture_output=True, text=True, cwd=DL_HOME)
    lines = {line.split(" ", 1)[0]: (line.split(" ", 1) + [""])[1].strip()
             for line in result.stdout.splitlines() if line.startswith("SCORE_")}
    if result.returncode != 0 or "SCORE_TP" not in lines:
        raise RuntimeError(f"scoring failed (exit {result.returncode}):\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}")
    return lines


def score(kb, concept, positives, negatives):
    lines = run_java(write_conf(kb, positives, negatives), kb, concept)
    sets = {key: set(lines[f"SCORE_{key}"].split()) for key in ("TP", "FP", "FN", "TN")}
    check = (sets["TP"] | sets["FN"] == set(positives) and sets["FP"] | sets["TN"] == set(negatives))
    if not check:
        raise RuntimeError(f"scored sets do not partition the test examples: {sets}")
    tp, fp, fn, tn = (len(sets[k]) for k in ("TP", "FP", "FN", "TN"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "expression": lines["SCORE_EXPRESSION"],
        "accuracy": (tp + tn) / (tp + tn + fp + fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "true_positives": sorted(sets["TP"]),
        "false_positives": sorted(sets["FP"]),
        "false_negatives": sorted(sets["FN"]),
    }


def test_examples(repeat, fold):
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    test = folds[(folds["repeat"] == repeat) & (folds["fold"] == fold)]
    return sorted(test.loc[test["label"] == 1, "code"]), sorted(test.loc[test["label"] == 0, "code"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--concept", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("--fold", type=int, required=True)
    args = parser.parse_args()
    positives, negatives = test_examples(args.repeat, args.fold)
    print(json.dumps(score(args.kb, args.concept, positives, negatives), indent=2))


if __name__ == "__main__":
    main()
