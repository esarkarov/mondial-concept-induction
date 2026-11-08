import argparse
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import owlready2
from rdflib import Graph

from src.config import EU_ORGANIZATION, MASK_EXTENDED, MASKED_ORGANIZATIONS, STRICT_EXTRA

DEFAULT_KB = ROOT / "kb" / "mondial_extended_discretised.owl"
DEFAULT_JAVA_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
FORBIDDEN_EXACT = {"eu", "org_eu", "eumember", "eumembers", "eucandidate", "eucandidates", "candidate", "candidates"}
REMOVED_BY_VARIANT = {
    "masked": MASKED_ORGANIZATIONS,
    "extended": MASK_EXTENDED,
    "strict": MASK_EXTENDED + STRICT_EXTRA,
    "none": [],
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def variant_of(path):
    match = re.match(r"mondial_(masked|extended|strict|none)_(discretised|datatype)\.owl$", path.name)
    check(match is not None, f"unexpected KB file name: {path.name}")
    return match.group(1)


def report_counts(onto):
    classes = Counter()
    roles = Counter()
    for individual in onto.individuals():
        for cls in individual.is_a:
            classes[cls.name] += 1
        for prop in individual.get_properties():
            roles[prop.name] += len(prop[individual])
    print("individuals per class:")
    for name, count in sorted(classes.items()):
        print(f"  {name}: {count}")
    print("assertions per role:")
    for name, count in sorted(roles.items()):
        print(f"  {name}: {count}")
    return classes


def check_assertions(onto, variant, classes):
    check(classes["Country"] == 246, f"countries: {classes['Country']}")
    check("org_" + EU_ORGANIZATION not in {i.name for i in onto.individuals()}, "EU organization individual present")

    removed = {"org_" + a for a in REMOVED_BY_VARIANT[variant]} | {"org_" + EU_ORGANIZATION}
    members = Counter()
    for country in onto.Country.instances():
        for org in country.isMember:
            members[org.name] += 1
    check(not set(members) & removed, f"isMember to removed organizations: {sorted(set(members) & removed)}")
    if variant == "none":
        check(not members, "isMember assertions present in the none variant")

    names = {e.name.lower() for e in list(onto.individuals()) + list(onto.classes()) + list(onto.properties())}
    check(not names & FORBIDDEN_EXACT, f"label-like names: {sorted(names & FORBIDDEN_EXACT)}")
    check(not any("eumember" in n or "eucandidate" in n for n in names), "label-like name containing EUMember/EUCandidate")

    pairs = {(c.name, n.name) for c in onto.Country.instances() for n in c.neighbor}
    asymmetric = [(a, b) for a, b in pairs if (b, a) not in pairs]
    check(not asymmetric, f"asymmetric neighbor pairs: {asymmetric[:5]}")
    print(f"assertions OK (neighbor pairs: {len(pairs)}, isMember organizations: {len(members)})")


def run_hermit(onto):
    owlready2.JAVA_EXE = str(Path(os.environ.get("DLLEARNER_JAVA_HOME", DEFAULT_JAVA_HOME)) / "bin" / "java.exe")
    start = time.time()
    try:
        with onto:
            owlready2.sync_reasoner_hermit([onto], infer_property_values=False)
    except Exception as error:
        print(f"HermiT FAILED after {time.time() - start:.1f}s: {type(error).__name__}: {error}")
        return
    print(f"HermiT OK in {time.time() - start:.1f}s (java: {owlready2.JAVA_EXE})")


def run_dllearner():
    start = time.time()
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "run_dllearner.ps1"),
         str(ROOT / "conf" / "smoke_load.conf")],
        capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    loaded = re.search(r"initialized component 'reasoner' in ([^\n]*?)\. Status: (\w+)", output)
    materialised = re.search(r"TBox materialised in ([^\n]*?)\.", output)
    if loaded:
        print(f"DL-Learner reasoner init: {loaded.group(1)} (status {loaded.group(2)}); TBox materialisation: "
              f"{materialised.group(1) if materialised else 'n/a'}; wall clock {time.time() - start:.1f}s")
    else:
        print(f"DL-Learner load FAILED (exit {result.returncode}):\n{output[-1500:]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--skip-hermit", action="store_true")
    parser.add_argument("--skip-dllearner", action="store_true")
    args = parser.parse_args()

    variant = variant_of(args.kb)
    print(f"KB: {args.kb} ({args.kb.stat().st_size / 1024:.0f} KB), membership variant: {variant}")
    print(f"total triples (rdflib): {len(Graph().parse(args.kb, format='xml'))}")

    with open(args.kb, "rb") as f:
        onto = owlready2.get_ontology("http://example.org/mondial").load(fileobj=f)
    classes = report_counts(onto)
    try:
        check_assertions(onto, variant, classes)
    except AssertionError as error:
        print(f"FAILED: {error}")
        sys.exit(1)

    if not args.skip_hermit:
        run_hermit(onto)
    if not args.skip_dllearner:
        if args.kb == DEFAULT_KB:
            run_dllearner()
        else:
            print("DL-Learner load skipped: conf/smoke_load.conf points to the default KB")


if __name__ == "__main__":
    main()
