import argparse
from pathlib import Path

import pandas as pd

from src.config import CONF_DIR, PROCESSED_DIR, ROOT

DEFAULT_KB = ROOT / "kb" / "mondial_extended_discretised.owl"
GENERATED_DIR = CONF_DIR / "generated"
BASE_IRI = "http://example.org/mondial#"


def training_examples(repeat, fold):
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
    positives = sorted(train.loc[train["label"] == 1, "code"])
    negatives = sorted(train.loc[train["label"] == 0, "code"])
    return positives, negatives


def examples_block(codes):
    return "{ " + ", ".join(f'"m:{code}"' for code in codes) + " }"


def flag(value):
    return "true" if value else "false"


REASONERS = ("cwr", "pellet")


def reasoner_lines(reasoner):
    if reasoner == "cwr":
        return ['reasoner.type = "closed world reasoner"', "reasoner.sources = { ks }"]
    if reasoner == "pellet":
        return ['reasoner.type = "OWL API Reasoner"', "reasoner.sources = { ks }",
                'reasoner.reasonerImplementation = "pellet"']
    raise ValueError(f"unknown reasoner {reasoner}")


def render(args, kb_relative):
    positives, negatives = training_examples(args.repeat, args.fold)
    lines = [
        f'prefixes = [ ("m","{BASE_IRI}") ]',
        "",
        'ks.type = "OWL File"',
        f'ks.fileName = "{kb_relative}"',
        "",
        *reasoner_lines(getattr(args, "reasoner", "cwr")),
        "",
        'lp.type = "posNegStandard"',
        f"lp.positiveExamples = {examples_block(positives)}",
        f"lp.negativeExamples = {examples_block(negatives)}",
        "",
        'op.type = "rho"',
        f"op.useNegation = {flag(args.use_negation)}",
        f"op.useAllConstructor = {flag(args.use_all)}",
        f"op.useCardinalityRestrictions = {flag(args.use_cardinality)}",
        f"op.useHasValueConstructor = {flag(args.use_has_value)}",
        "",
        f'alg.type = "{args.algorithm}"',
        f"alg.maxExecutionTimeInSeconds = {args.time}",
        f"alg.noisePercentage = {args.noise}",
    ]
    if args.max_depth is not None:
        lines.append(f"alg.maxDepth = {args.max_depth}")
    return "\n".join(lines) + "\n", len(positives), len(negatives)


def default_name(args, kb):
    return (
        f"r{args.repeat}_f{args.fold}_{args.algorithm}_{kb.stem.replace('mondial_', '')}"
        f"_t{args.time}_n{args.noise:g}_hv{int(args.use_has_value)}"
        + ("" if args.max_depth is None else f"_d{args.max_depth:g}")
        + ("" if args.reasoner == "cwr" else f"_{args.reasoner}")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("--fold", type=int, required=True)
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--algorithm", choices=["celoe", "ocel"], required=True)
    parser.add_argument("--time", type=int, default=60)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--use-negation", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-all", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-cardinality", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-has-value", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--max-depth", type=float, default=None)
    parser.add_argument("--reasoner", choices=REASONERS, default="cwr")
    parser.add_argument("--name")
    args = parser.parse_args()

    kb = args.kb.resolve()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    kb_relative = Path("..", "..", kb.relative_to(ROOT)).as_posix()
    text, n_pos, n_neg = render(args, kb_relative)
    out = GENERATED_DIR / f"{args.name or default_name(args, kb)}.conf"
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({n_pos} positives, {n_neg} negatives)")


if __name__ == "__main__":
    main()
