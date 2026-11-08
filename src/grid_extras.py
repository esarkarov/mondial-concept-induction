import re

import pandas as pd

from src.config import RESULTS_DIR

KEYWORDS = {"and", "or", "not", "some", "only", "value", "min", "max", "exactly", "Thing", "Nothing"}
NAME_RE = re.compile(r"[A-Za-z_][\w.\-]*")
NUMERIC_ONLY_RE = re.compile(r"^(\w+Q\d+|neighbor|hasAirport)$")
OCEL_ALT_PATH = RESULTS_DIR / "ocel_alt.csv"


def atoms(concept):
    return {t for t in NAME_RE.findall(concept) if t not in KEYWORDS}


def census(concepts):
    sets = [atoms(c) for c in concepts]
    n = len(concepts)
    return {
        "europe": sum("cont_Europe" in a for a in sets) / n,
        "organization": sum(any(t.startswith("org_") for t in a) or "isMember" in a for a in sets) / n,
        "numeric_only": sum(all(NUMERIC_ONLY_RE.match(t) for t in a) for a in sets) / n,
        "mean_atoms": sum(len(a) for a in sets) / n,
    }


def census_lines(rows):
    lines = [
        "Share of the concepts (one per fold) that mention `cont_Europe`, that mention any organization (`isMember` or an `org_*` individual), "
        "and that use only numeric-bin classes (`...Q<n>`), `neighbor` and `hasAirport`; distinct atoms = distinct names excluding constructors.",
        "",
        "| config | concepts | mention cont_Europe | mention an organization | only numeric-bin, neighbor, hasAirport | mean distinct atoms |",
        "|---|---|---|---|---|---|",
    ]
    for name, runs, _ in rows:
        c = census(list(runs["concept"]))
        lines.append(f"| {name} | {len(runs)} | {c['europe']:.2f} | {c['organization']:.2f} | {c['numeric_only']:.2f} | {c['mean_atoms']:.1f} |")
    return lines


DIAGNOSTIC_NAME = "D1_celoe_strict_disc_hv1_n0_pellet_closure_disjoint_t600"
EUROPE_ALONE = {"encompassed some ({cont_Europe})", "encompassed value cont_Europe"}
IMPROVEMENT_RE = re.compile(r"^more accurate \(([\d,.]+)%\) class expression found(?: after (\S+))?: (.*)$")
DURATION_RE = re.compile(r"(?:(\d+)m(?!s))?(?:(\d+)s)?(?:(\d+)ms)?")


def seconds(text):
    minutes, secs, millis = DURATION_RE.fullmatch(text).groups()
    return int(minutes or 0) * 60 + int(secs or 0) + int(millis or 0) / 1000


def diagnostic_lines():
    from src.run_experiment import RUNS_DIR
    path = RUNS_DIR / f"{DIAGNOSTIC_NAME}.csv"
    log = RUNS_DIR / DIAGNOSTIC_NAME / "logs" / "r0_f0.log"
    if not path.exists():
        return ["Not run yet."]
    row = pd.read_csv(path, keep_default_na=False).iloc[0]
    timeline = []
    for line in log.read_text(encoding="utf-8").splitlines():
        match = IMPROVEMENT_RE.match(line)
        if match:
            timeline.append((seconds(match.group(2)) if match.group(2) else None, float(match.group(1).replace(",", ".")), match.group(3)))
    europe = next(((t, a) for t, a, e in timeline if e in EUROPE_ALONE), None)
    better = next(((t, a, e) for t, a, e in timeline if europe and a > europe[1]), None)
    lines = [
        f"Diagnostic, not part of the grid: the O3 configuration on repeat 0 fold 0 with a 600 s limit (`{DIAGNOSTIC_NAME}`).",
        "",
        f"- descriptions tested: {row.tested}; algorithm time {row.algorithm_seconds:.1f} s; wall {row.wall_seconds} s",
        f"- best concept: `{row.concept}` (train accuracy {row.train_accuracy}%)",
        f"- test: accuracy {row.test_accuracy:.3f}, precision {row.test_precision:.3f}, recall {row.test_recall:.3f}, F1 {row.test_f1:.3f}, "
        f"TP/FP/FN/TN {row.tp}/{row.fp}/{row.fn}/{row.tn}, FP [{row.false_positives}], FN [{row.false_negatives}]",
    ]
    if europe:
        lines.append(f"- Europe alone first printed at {europe[0]:.1f} s ({europe[1]}% training accuracy)")
        lines.append("- first concept better than Europe alone: " + (f"{better[0]:.1f} s, {better[1]}%, `{better[2]}`" if better else "none within the limit"))
    else:
        lines.append("- Europe alone was not printed within the limit")
    lines += ["- timeline of improvements (seconds, training accuracy %, concept):"]
    lines += [f"  - {t:.1f} s, {a}%, `{e}`" if t is not None else f"  - n/a, {a}%, `{e}`" for t, a, e in timeline]
    return lines


def ocel_sensitivity_lines():
    if not OCEL_ALT_PATH.exists():
        return ["Not computed yet (run `python -m src.ocel_sensitivity`)."]
    table = pd.read_csv(OCEL_ALT_PATH, keep_default_na=False)
    summary = pd.read_csv(RESULTS_DIR / "ocel_alt_summary.csv")
    lines = [
        "Alternative rule: OCEL's first listed entry (fallback to the main concept in folds whose log has no list). "
        "Main numbers above are unchanged.",
        "",
        "| config | folds with a list / without | folds where the first entry differs from the main concept | pooled F1, main rule | pooled F1, first listed entry | pooled F1 CI, first listed entry |",
        "|---|---|---|---|---|---|",
    ]
    for r in summary.itertuples():
        lines.append(f"| {r.config} | {r.with_list} / {r.without_list} | {r.differs} | {r.pooled_f1_main:.3f} | {r.pooled_f1_alt:.3f} | [{r.ci_low:.3f}, {r.ci_high:.3f}] |")
    return lines
