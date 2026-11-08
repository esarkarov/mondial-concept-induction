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
