import json
import re
import subprocess
import sys
from collections import Counter
from types import SimpleNamespace

import pandas as pd

from src.config import KB_DIR, PROCESSED_DIR, RESULTS_DIR, ROOT
from src.kb import numeric_table
from src.make_conf import GENERATED_DIR, examples_block, flag, reasoner_lines
from src.run_experiment import RUNS_DIR, WRAPPER, concept_length, parse_output
from src.grid_extras import DIAGNOSTIC_NAME
from src.run_grid import SUITES, config_name

sys.path.insert(0, str(ROOT / "scripts"))
from score_concept import covered_by

OUT_DIR = RESULTS_DIR / "analysis"
REPORT = RESULTS_DIR / "analysis.md"
CSV_DIR = PROCESSED_DIR / "csv"
ERROR_MODELS = ["G1_celoe_strict_disc_hv1_n0", "A1_celoe_extended_disc_hv1_n0", "strict_random_forest", "strict_tree_full", "rule_europe"]
ALL_CONFIGS = [c for suite in ("main", "ablations", "owa") for c in SUITES[suite]["configs"]]
NUMERIC_ATTRIBUTES = {"Population": "population", "Area": "area", "Gdp": "gdp", "GdpPerCapita": "gdp_per_capita", "Inflation": "inflation",
                      "InfantMortality": "infant_mortality", "PopulationGrowth": "population_growth", "NAirports": "n_airports"}
BIN_RE = re.compile(r"^([A-Za-z]+)Q(\d)$")
TOKEN_RE = re.compile(r'\{[^}]*\}|double\[[^\]]*\]|[()]|[^\s()]+')
ROLE_WORDS = {"some", "only", "value", "min", "max", "exactly"}


def read(name):
    return pd.read_csv(CSV_DIR / f"{name}.csv", dtype=str, keep_default_na=False)


def md_table(frame):
    lines = ["| " + " | ".join(frame.columns) + " |", "|" + "---|" * len(frame.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return lines


def context():
    country = read("country")
    names = dict(zip(country["Code"], country["Name"]))
    positives = set(pd.read_csv(PROCESSED_DIR / "eu_positives.csv", dtype=str, keep_default_na=False)["code"])
    negatives = set(pd.read_csv(PROCESSED_DIR / "eu_negatives.csv", dtype=str, keep_default_na=False)["code"])
    candidates = set(pd.read_csv(PROCESSED_DIR / "eu_excluded_candidates.csv", dtype=str, keep_default_na=False)["code"])
    politics = read("politics").set_index("Country")
    dependents = set(names) - positives - negatives - candidates
    assert all(politics.loc[c, "Dependent"] != "" for c in dependents)
    europe = set(read("encompasses").query("Continent == 'Europe'")["Country"])
    return SimpleNamespace(names=names, positives=positives, negatives=negatives, candidates=candidates, dependents=dependents,
                           politics=politics, europe=europe, country=country)


def label_text(ctx, code):
    return "positive" if code in ctx.positives else "negative" if code in ctx.negatives else "candidate" if code in ctx.candidates else "dependent"


def error_profile(ctx):
    predictions = pd.read_csv(RESULTS_DIR / "predictions.csv", dtype={"code": str}, keep_default_na=False)
    labelled = sorted(ctx.positives | ctx.negatives)
    european_negatives = sorted(ctx.negatives & ctx.europe)
    frame = pd.DataFrame({"code": labelled})
    frame["country"] = frame["code"].map(ctx.names)
    frame["label"] = frame["code"].map(lambda c: int(c in ctx.positives))
    wrong_per_repeat = {}
    for model in ERROR_MODELS:
        part = predictions[predictions["config"] == model]
        wrong = part.assign(wrong=(part["label"] != part["predicted"]).astype(int)).pivot(index="code", columns="repeat", values="wrong")
        assert wrong.shape == (194, 3), model
        wrong_per_repeat[model] = wrong
        frame[model] = frame["code"].map(wrong.sum(axis=1))
    frame.to_csv(OUT_DIR / "error_profile.csv", index=False)
    lines = [f"Misclassified-repeat counts per country (0 to 3) are in `results/analysis/error_profile.csv`. The 14 European negatives are the labelled negatives with a `Europe` row in `encompasses` ({len(european_negatives)} found): "
             + ", ".join(ctx.names[c] for c in european_negatives) + ".", ""]
    summary = []
    for model in ERROR_MODELS:
        wrong = wrong_per_repeat[model]
        always = frame[frame[model] == 3]
        fp = [r.country for r in always.itertuples() if r.label == 0]
        fn = [r.country for r in always.itertuples() if r.label == 1]
        right = [int((wrong.loc[european_negatives, r] == 0).sum()) for r in range(3)]
        summary.append({"model": model, "wrong in 3/3 repeats": len(always), "false positives (3/3)": "; ".join(fp) or "none",
                        "false negatives (3/3)": "; ".join(fn) or "none",
                        "European negatives right per repeat (of 14)": " / ".join(map(str, right)),
                        "European negatives right in 3/3 repeats": int((wrong.loc[european_negatives].sum(axis=1) == 0).sum())})
    return lines + md_table(pd.DataFrame(summary))


def most_frequent(config):
    runs = pd.read_csv(RUNS_DIR / f"{config_name(config)}.csv", keep_default_na=False)
    counts = Counter(runs["concept"]).most_common()
    top, count = counts[0]
    rows = runs[runs["concept"] == top]
    ties = sum(1 for _, n in counts[1:] if n == count)
    return {"concept": top, "count": count, "folds": len(runs), "length": int(rows["length"].iloc[0]),
            "train_accuracy": rows["train_accuracy"].mean(), "ties": ties}


def kb_file(membership, numeric="discretised"):
    return KB_DIR / f"mondial_{membership}_{numeric}.owl"


def excluded_countries(ctx):
    by_label = {c["label"]: c for c in ALL_CONFIGS}
    targets = [("G1", "strict"), ("A1", "extended")]
    codes = sorted(ctx.candidates | ctx.dependents)
    assert len(ctx.candidates) == 7 and len(ctx.dependents) == 45, (len(ctx.candidates), len(ctx.dependents))
    expected = {"G1": "(not (InflationQ4)) and (not (PopulationQ1)) and (encompassed some ({cont_Europe}))",
                "A1": "(encompassed some ({cont_Europe})) and (isMember some ({org_AG}))"}
    lines, rows = [], []
    for label, membership in targets:
        top = most_frequent(by_label[label])
        assert top["concept"] == expected[label], top["concept"]
        covered = covered_by(kb_file(membership), [top["concept"]], codes)[top["concept"]]
        predicted = sorted(covered)
        for code in predicted:
            depends = ctx.politics.loc[code, "Dependent"] if code in ctx.dependents else ""
            rows.append({"config": label, "kb": membership, "code": code, "country": ctx.names[code], "group": label_text(ctx, code),
                         "depends_on": ctx.names.get(depends, depends), "depends_on_positive": (depends in ctx.positives) if depends else ""})
        candidates_hit = [c for c in predicted if c in ctx.candidates]
        dependents_hit = [c for c in predicted if c in ctx.dependents]
        lines += [f"### {label} ({membership} KB): `{top['concept']}`", "",
                  f"- EU candidates predicted positive: {len(candidates_hit)} of 7: " + (", ".join(ctx.names[c] for c in candidates_hit) or "none"),
                  f"- candidates not predicted positive: " + (", ".join(ctx.names[c] for c in sorted(ctx.candidates) if c not in covered) or "none"),
                  f"- dependent territories predicted positive: {len(dependents_hit)} of 45", ""]
        dependent_rows = [r for r in rows if r["config"] == label and r["group"] == "dependent"]
        if dependent_rows:
            lines += md_table(pd.DataFrame(dependent_rows)[["country", "code", "depends_on", "depends_on_positive"]]) + [""]
        else:
            lines += ["No dependent territory is predicted positive, so there is no dependency table for this concept.", ""]
    pd.DataFrame(rows).to_csv(OUT_DIR / "excluded_predicted_positive.csv", index=False)
    return lines


FULL_CONFIGS = [("F1", "G1 settings: strict KB, hasValue on", "strict", True), ("F2", "A1 settings: extended KB, hasValue on", "extended", True),
                ("F3", "G3 settings: strict KB, hasValue off", "strict", False)]


def learn_full(ctx, label, membership, has_value):
    directory = OUT_DIR / "full_data"
    directory.mkdir(parents=True, exist_ok=True)
    state_file = directory / f"{label}.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    positives, negatives = sorted(ctx.positives), sorted(ctx.negatives)
    text = "\n".join([
        'prefixes = [ ("m","http://example.org/mondial#") ]', "", 'ks.type = "OWL File"',
        f'ks.fileName = "../../kb/mondial_{membership}_discretised.owl"', "", *reasoner_lines("cwr"), "",
        'lp.type = "posNegStandard"', f"lp.positiveExamples = {examples_block(positives)}",
        f"lp.negativeExamples = {examples_block(negatives)}", "", 'op.type = "rho"', "op.useNegation = true", "op.useAllConstructor = true",
        "op.useCardinalityRestrictions = true", f"op.useHasValueConstructor = {flag(has_value)}", "",
        'alg.type = "celoe"', "alg.maxExecutionTimeInSeconds = 60", "alg.noisePercentage = 0", ""])
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    conf = GENERATED_DIR / f"full_data_{label}.conf"
    conf.write_text(text, encoding="utf-8", newline="\n")
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(WRAPPER), str(conf)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in (result.stdout + result.stderr).splitlines() if l.strip() and not re.match(r"^\[[=. ]+\] *\d+%", l)]
    (directory / f"{label}.log").write_text("\n".join(lines), encoding="utf-8")
    top, seconds, tested = parse_output(lines, 60)
    if not top:
        raise RuntimeError(f"no concept learned for {label}")
    state = {"concept": top[0]["concept"], "train_accuracy": top[0]["train_accuracy"], "length": concept_length(top[0]["concept"]),
             "tested": tested, "algorithm_seconds": seconds}
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state


def full_data(ctx):
    rows = []
    for label, text, membership, has_value in FULL_CONFIGS:
        state = learn_full(ctx, label, membership, has_value)
        rows.append({"run": label, "settings": text, "concept": f"`{state['concept']}`", "training accuracy %": state["train_accuracy"],
                     "length": state["length"], "tested": state["tested"], "algorithm s": state["algorithm_seconds"]})
    pd.DataFrame(rows).to_csv(OUT_DIR / "full_data_concepts.csv", index=False)
    lines = ["Fitted on all 194 labelled countries (27 positives, 167 negatives), CELOE, noise 0, 60 s, one run each. "
             "**For presentation only: training accuracy on the data the concept was fitted to, not an estimate of performance.**", ""]
    return lines + md_table(pd.DataFrame(rows))


class Translator:
    def __init__(self, bins):
        self.phrases = {}
        for key, entry in bins.items():
            attribute = {v: k for k, v in NUMERIC_ATTRIBUTES.items()}[key]
            for b in entry["bins"]:
                lo, hi = b["lower_exclusive"], b["upper_inclusive"]
                self.phrases[b["class"]] = (f"{key} <= {hi:g}" if lo is None else f"{key} > {lo:g}" if hi is None else f"{lo:g} < {key} <= {hi:g}")

    def parse(self, text):
        self.tokens, self.i = TOKEN_RE.findall(text), 0
        tree = self.expression()
        assert self.i == len(self.tokens), text
        return tree

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self):
        self.i += 1
        return self.tokens[self.i - 1]

    def expression(self):
        terms, operator = [self.term()], None
        while self.peek() in ("and", "or"):
            operator = self.take()
            terms.append(self.term())
        return (operator, terms) if operator else terms[0]

    def term(self):
        token = self.take()
        if token == "not":
            return ("not", self.term())
        if token == "(":
            inner = self.expression()
            assert self.take() == ")"
            return inner
        if token.startswith("{"):
            return ("nominal", token.strip("{} "))
        if self.peek() in ROLE_WORDS:
            kind = self.take()
            if kind in ("min", "max", "exactly"):
                number = self.take()
                return (kind, token, number, self.term())
            if kind == "value":
                return ("value", token, self.take())
            return (kind, token, self.term())
        return ("atom", token)

    def say(self, node):
        kind = node[0]
        if kind == "atom":
            name = node[1]
            return f"{name} [{self.phrases[name]}]" if name in self.phrases else "anything" if name == "Thing" else name
        if kind == "nominal":
            return node[1]
        if kind == "not":
            return f"not ({self.say(node[1])})"
        if kind in ("and", "or"):
            return f" {kind} ".join(self.wrap(t) for t in node[1])
        if kind == "value":
            return f"{node[1]} is {node[2]}"
        if kind in ("some", "only"):
            role, filler = node[1], node[2]
            if filler[0] == "atom" and filler[1].startswith("double["):
                return f"{role} {filler[1].replace('double', '').replace('^^', '').replace(chr(34), '')}"
            if filler[0] == "nominal":
                return f"{role} includes {filler[1]}" if kind == "some" else f"every {role} is {filler[1]}"
            if filler == ("atom", "Thing"):
                return f"has some {role}" if kind == "some" else f"{role} unrestricted"
            return f"has a {role} that is {self.wrap(filler)}" if kind == "some" else f"every {role} is {self.wrap(filler)}"
        label = {"min": "at least", "max": "at most", "exactly": "exactly"}[kind]
        return f"has {label} {node[2]} {node[1]} that are {self.wrap(node[3])}"

    def wrap(self, node):
        return f"({self.say(node)})" if node[0] in ("and", "or") else self.say(node)


def double_facets(concept):
    return re.findall(r'(\w+) some double\[([^\]]*)\]', concept)


def inventory(ctx):
    bins = json.loads((KB_DIR / "bins.json").read_text(encoding="utf-8"))
    translator = Translator(bins)
    rows, flagged = [], []
    for c in SUITES["main"]["configs"] + SUITES["ablations"]["configs"]:
        top = most_frequent(c)
        atoms = {a for a in re.findall(r"[A-Za-z_][\w]*", top["concept"]) if BIN_RE.match(a)}
        flags = sorted(atoms) + [f"{p} {f}" for p, f in double_facets(top["concept"])]
        flagged += [a for a in atoms]
        rows.append({"config": c["label"], "count": f"{top['count']}/{top['folds']}" + (f" (tied with {top['ties']} other)" if top["ties"] else ""),
                     "concept": f"`{top['concept']}`", "length": top["length"], "mean train acc %": round(top["train_accuracy"], 2),
                     "reading (atoms only)": translator.say(translator.parse(top["concept"])),
                     "discretisation-dependent atoms": ", ".join(flags) or "none"})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "concept_inventory.csv", index=False)
    values = numeric_table(ctx.country)
    edge_rows = []
    for atom in sorted(set(flagged)):
        prefix, index = BIN_RE.match(atom).groups()
        key = NUMERIC_ATTRIBUTES[prefix]
        entry = [b for b in bins[key]["bins"] if b["class"] == atom][0]
        series = values[key].dropna()
        for edge, inside_below in ((entry["lower_exclusive"], False), (entry["upper_inclusive"], True)):
            if edge is None:
                continue
            below = series[series <= edge].sort_values(ascending=False).head(3)
            above = series[series > edge].sort_values().head(3)
            for side, part in (("<= edge", below), ("> edge", above)):
                inside = (side == "<= edge") == inside_below
                for code, value in part.items():
                    edge_rows.append({"atom": atom, "edge": edge, "side": side, "relation to bin": "inside" if inside else "outside",
                                      "code": code, "country": ctx.names[code], "value": value, "group": label_text(ctx, code)})
    edges = pd.DataFrame(edge_rows)
    edges.to_csv(OUT_DIR / "bin_edges.csv", index=False)
    return table, edges, bins


def threshold(ctx):
    values = numeric_table(ctx.country)["population"]
    labelled = sorted(ctx.positives | ctx.negatives)
    frame = pd.DataFrame({"code": labelled, "population": values.reindex(labelled).values})
    frame["country"] = frame["code"].map(ctx.names)
    frame["label"] = frame["code"].map(lambda c: "positive" if c in ctx.positives else "negative")
    below = frame[frame["population"] < 389830.5].sort_values("population", ascending=False).head(5)
    above = frame[frame["population"] >= 389830.5].sort_values("population").head(5)
    result = pd.concat([below.assign(side="below 389830.5"), above.assign(side=">= 389830.5")])[["side", "country", "code", "population", "label"]]
    result.to_csv(OUT_DIR / "a4_threshold.csv", index=False)
    smallest_positive = frame[frame["label"] == "positive"].sort_values("population").head(1)
    return result, frame, smallest_positive


def runtime():
    rows = []
    for c in ALL_CONFIGS:
        runs = pd.read_csv(RUNS_DIR / f"{config_name(c)}.csv", keep_default_na=False)
        rows.append({"config": c["label"], "runs": len(runs), "mean wall s": round(runs["wall_seconds"].mean(), 1),
                     "mean tested": round(runs["tested"].mean()), "total wall minutes": round(runs["wall_seconds"].sum() / 60, 1),
                     "total algorithm minutes": round(runs["algorithm_seconds"].sum() / 60, 1)})
    diagnostic = pd.read_csv(RUNS_DIR / f"{DIAGNOSTIC_NAME}.csv", keep_default_na=False)
    rows.append({"config": "D1 (extra: 600 s diagnostic, not a grid config)", "runs": len(diagnostic),
                 "mean wall s": round(diagnostic["wall_seconds"].mean(), 1), "mean tested": round(diagnostic["tested"].mean()),
                 "total wall minutes": round(diagnostic["wall_seconds"].sum() / 60, 1),
                 "total algorithm minutes": round(diagnostic["algorithm_seconds"].sum() / 60, 1)})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "runtime.csv", index=False)
    return table


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = context()
    lines = ["# Phase 4: analysis of frozen results", "",
             "Built from `results/predictions.csv`, `results/runs/*.csv`, `kb/bins.json` and the Phase 1 to 3 data; nothing from Phases 1 to 3 was changed. "
             "CSVs are in `results/analysis/`.", "", "## 1. Error profile (3 repeats, 194 labelled countries)", ""]
    lines += error_profile(ctx)
    lines += ["", "## 2. Excluded countries (7 EU candidates, 45 dependent territories)", "",
              "Most frequent concept of G1 (strict KB) and A1 (extended KB), evaluated with the closed world reasoner; no labels used.", ""]
    lines += excluded_countries(ctx)
    lines += ["", "## 3. Concepts fitted on all labelled countries (presentation only)", ""]
    lines += full_data(ctx)
    table, edges, bins = inventory(ctx)
    lines += ["", "## 4. Concept inventory (most frequent concept per config, counts out of 15 folds)", "",
              "The reading is generated from the atoms of the concept only. Bin atoms `XQn` depend on the quartile edges listed below.", ""]
    lines += md_table(table)
    lines += ["", "### Edges of the bin atoms used above (`kb/bins.json`; bins are lower-exclusive, upper-inclusive, quartiles over all 246 countries)", ""]
    for atom, group in edges.groupby("atom", sort=True):
        prefix = BIN_RE.match(atom).group(1)
        entry = [b for b in bins[NUMERIC_ATTRIBUTES[prefix]]["bins"] if b["class"] == atom][0]
        lines += [f"**{atom}**: lower_exclusive {entry['lower_exclusive']}, upper_inclusive {entry['upper_inclusive']}, {entry['count']} countries", ""]
        shown = group.copy()
        shown["value"] = shown["value"].map(lambda v: f"{v:g}")
        lines += md_table(shown[["edge", "relation to bin", "country", "value", "group"]]) + [""]
    result, frame, smallest = threshold(ctx)
    lines += ["## 5. A4 threshold (population >= 389830.5)", "",
              "Five labelled countries on each side of the threshold (population from `country.Population`, the value the A4 KB stores).", ""]
    lines += md_table(result)
    lines += ["", f"Smallest positive: {smallest['country'].iloc[0]} ({smallest['population'].iloc[0]:g}). "
              f"Labelled countries below the threshold: {int((frame['population'] < 389830.5).sum())} "
              f"({int(((frame['population'] < 389830.5) & (frame['label'] == 'positive')).sum())} positives); "
              f"missing population: {int(frame['population'].isna().sum())}.", ""]
    lines += ["## 6. Runtime", "",
              "Wall seconds are per run as seen by the harness (JVM start included, 3 workers in parallel, so totals are compute minutes, not elapsed time); "
              "the O configs ran on repeat 0 only; the D1 row is an extra single diagnostic run with a 600 s limit.", ""]
    lines += md_table(runtime())
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
