import argparse
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import numpy as np
import pandas as pd
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from src.config import KB_DIR, KB_MEMBERSHIP_VARIANTS, PROCESSED_DIR, STRICT_EXTRA

CSV_DIR = PROCESSED_DIR / "csv"
BASE = "http://example.org/mondial#"
M = Namespace(BASE)

CLASSES = ["Country", "Organization", "Continent", "Language", "Religion", "EthnicGroup", "Airport", "Sea"]

OBJECT_ROLES = {
    "neighbor": "Country",
    "encompassed": "Continent",
    "borderedBySea": "Sea",
    "speaks": "Language",
    "follows": "Religion",
    "hasEthnicGroup": "EthnicGroup",
    "isMember": "Organization",
    "hasAirport": "Airport",
}

MAIN_ROLES = {"mainLanguage": "speaks", "mainReligion": "follows", "mainEthnicGroup": "hasEthnicGroup"}

ISMEMBER_FILES = {
    "masked": PROCESSED_DIR / "ismember_masked.csv",
    "extended": PROCESSED_DIR / "ismember_masked_extended.csv",
    "strict": PROCESSED_DIR / "ismember_masked_extended.csv",
    "none": None,
}

NUMERIC = {
    "population": ("Population", "population", "double"),
    "area": ("Area", "area", "double"),
    "gdp": ("Gdp", "gdp", "double"),
    "gdp_per_capita": ("GdpPerCapita", "gdpPerCapita", "double"),
    "inflation": ("Inflation", "inflation", "double"),
    "infant_mortality": ("InfantMortality", "infantMortality", "double"),
    "population_growth": ("PopulationGrowth", "populationGrowth", "double"),
    "n_airports": ("NAirports", "nAirports", "integer"),
}

QUANTILES = [0, 0.25, 0.5, 0.75, 1]


def read(table):
    return pd.read_csv(CSV_DIR / f"{table}.csv", dtype=str, keep_default_na=False)


def local_name(prefix, name):
    return prefix + re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")


class Names:
    def __init__(self):
        self.used = {}

    def iri(self, local, source):
        if local in self.used and self.used[local] != source:
            raise ValueError(f"IRI collision for {local}: {self.used[local]} and {source}")
        self.used[local] = source
        return M[local]


def numeric_table(country):
    economy = read("economy").set_index("Country")
    population = read("population").set_index("Country")
    airports = read("airport")["Country"].value_counts()
    codes = country["Code"]
    to_num = lambda series: pd.to_numeric(series, errors="coerce")
    frame = pd.DataFrame(index=codes)
    frame["population"] = to_num(country.set_index("Code")["Population"])
    frame["area"] = to_num(country.set_index("Code")["Area"])
    frame["gdp"] = to_num(economy["GDP"]).reindex(codes)
    frame["gdp_per_capita"] = frame["gdp"] * 1e6 / frame["population"].where(frame["population"] > 0)
    frame["inflation"] = to_num(economy["Inflation"]).reindex(codes)
    frame["infant_mortality"] = to_num(population["Infant_Mortality"]).reindex(codes)
    frame["population_growth"] = to_num(population["Population_Growth"]).reindex(codes)
    frame["n_airports"] = airports.reindex(codes).fillna(0).astype(float)
    return frame


def make_bins(frame):
    bins = {}
    for column, (class_prefix, _, _) in NUMERIC.items():
        values = frame[column].dropna()
        edges = np.unique(np.quantile(values, QUANTILES))
        inner = edges[1:-1]
        index = np.searchsorted(inner, values.to_numpy(), side="left")
        counts = np.bincount(index, minlength=len(inner) + 1)
        entries = []
        for j in range(len(inner) + 1):
            entries.append(
                {
                    "class": f"{class_prefix}Q{j + 1}",
                    "lower_exclusive": None if j == 0 else float(inner[j - 1]),
                    "upper_inclusive": None if j == len(inner) else float(inner[j]),
                    "count": int(counts[j]),
                }
            )
        bins[column] = {"n_values": int(len(values)), "edges": [float(e) for e in edges], "bins": entries}
    return bins


def bin_of(value, bins_entry):
    inner = bins_entry["edges"][1:-1]
    return f"{bins_entry['bins'][int(np.searchsorted(inner, value, side='left'))]['class']}"


def top_one(table, key_column):
    data = read(table).rename(columns={key_column: "value"})
    data["Percentage"] = pd.to_numeric(data["Percentage"], errors="coerce").fillna(-1.0)
    data = data.sort_values(["Country", "Percentage", "value"], ascending=[True, False, True])
    return data.drop_duplicates("Country").set_index("Country")["value"]


def add_tbox(g, numeric_mode, bins):
    ontology = URIRef(BASE.rstrip("#"))
    g.add((ontology, RDF.type, OWL.Ontology))
    for name in CLASSES:
        g.add((M[name], RDF.type, OWL.Class))
    disjoint = BNode("disjointClasses")
    g.add((disjoint, RDF.type, OWL.AllDisjointClasses))
    cells = [BNode(f"disjointCell{i}") for i in range(len(CLASSES))]
    for i, (cell, name) in enumerate(zip(cells, CLASSES)):
        g.add((cell, RDF.first, M[name]))
        g.add((cell, RDF.rest, cells[i + 1] if i + 1 < len(cells) else RDF.nil))
    g.add((disjoint, OWL.members, cells[0]))

    for role, range_class in OBJECT_ROLES.items():
        g.add((M[role], RDF.type, OWL.ObjectProperty))
        g.add((M[role], RDFS.domain, M.Country))
        g.add((M[role], RDFS.range, M[range_class]))
    g.add((M.neighbor, RDF.type, OWL.SymmetricProperty))
    for role, parent in MAIN_ROLES.items():
        g.add((M[role], RDF.type, OWL.ObjectProperty))
        g.add((M[role], RDFS.subPropertyOf, M[parent]))

    if numeric_mode == "datatype":
        for _, (_, prop, kind) in NUMERIC.items():
            g.add((M[prop], RDF.type, OWL.DatatypeProperty))
            g.add((M[prop], RDFS.domain, M.Country))
            g.add((M[prop], RDFS.range, XSD[kind]))
    else:
        for column, (class_prefix, _, _) in NUMERIC.items():
            for entry in bins[column]["bins"]:
                g.add((M[entry["class"]], RDF.type, OWL.Class))
                g.add((M[entry["class"]], RDFS.subClassOf, M.Country))


CLOSURE_ROLES = ["neighbor", "speaks", "follows", "borderedBySea", "hasEthnicGroup", "hasAirport", "isMember"]


def add_closure(g):
    countries = sorted(g.subjects(RDF.type, M.Country), key=str)
    for country in countries:
        code = str(country)[len(BASE):]
        for role in CLOSURE_ROLES:
            fillers = sorted(g.objects(country, M[role]), key=str)
            restriction = BNode(f"closure_{code}_{role}")
            g.add((country, RDF.type, restriction))
            g.add((restriction, RDF.type, OWL.Restriction))
            g.add((restriction, OWL.onProperty, M[role]))
            if not fillers:
                g.add((restriction, OWL.allValuesFrom, OWL.Nothing))
                continue
            values = BNode(f"closure_{code}_{role}_set")
            cells = [BNode(f"closure_{code}_{role}_{i}") for i in range(len(fillers))]
            g.add((restriction, OWL.allValuesFrom, values))
            g.add((values, RDF.type, OWL.Class))
            g.add((values, OWL.oneOf, cells[0]))
            for i, (cell, filler) in enumerate(zip(cells, fillers)):
                g.add((cell, RDF.first, filler))
                g.add((cell, RDF.rest, cells[i + 1] if i + 1 < len(cells) else RDF.nil))


def build(membership, numeric, closure):
    g = Graph()
    g.bind("m", M)
    names = Names()
    sizes = {}

    country = read("country")
    frame = numeric_table(country)
    bins = make_bins(frame)
    add_tbox(g, numeric, bins)
    sizes["tbox"] = len(g)

    def declare(iri, cls):
        g.add((iri, RDF.type, OWL.NamedIndividual))
        g.add((iri, RDF.type, M[cls]))
        return iri

    country_iri = {}
    for code, name in zip(country["Code"], country["Name"]):
        iri = declare(names.iri(code, f"country:{code}"), "Country")
        country_iri[code] = iri
        g.add((iri, RDFS.label, Literal(name)))
    sizes["countries"] = len(g) - sizes["tbox"]

    def node(prefix, name, cls):
        return declare(names.iri(local_name(prefix, name), f"{cls}:{name}"), cls)

    mark = len(g)
    borders = read("borders")
    for a, b in zip(borders["Country1"], borders["Country2"]):
        g.add((country_iri[a], M.neighbor, country_iri[b]))
        g.add((country_iri[b], M.neighbor, country_iri[a]))
    sizes["neighbor"] = len(g) - mark

    mark = len(g)
    for code, continent in read("encompasses")[["Country", "Continent"]].drop_duplicates().itertuples(index=False):
        g.add((country_iri[code], M.encompassed, node("cont_", continent, "Continent")))
    sizes["encompassed"] = len(g) - mark

    mark = len(g)
    for sea, code in read("geo_sea")[["Sea", "Country"]].drop_duplicates().itertuples(index=False):
        g.add((country_iri[code], M.borderedBySea, node("sea_", sea, "Sea")))
    sizes["borderedBySea"] = len(g) - mark

    flat = [("spoken", "Language", "speaks", "lang_", "Language", "mainLanguage"),
            ("religion", "Name", "follows", "rel_", "Religion", "mainReligion"),
            ("ethnicgroup", "Name", "hasEthnicGroup", "eth_", "EthnicGroup", "mainEthnicGroup")]
    for table, column, role, prefix, cls, main_role in flat:
        mark = len(g)
        for code, value in read(table)[["Country", column]].drop_duplicates().itertuples(index=False):
            g.add((country_iri[code], M[role], node(prefix, value, cls)))
        for code, value in top_one(table, column).items():
            g.add((country_iri[code], M[main_role], node(prefix, value, cls)))
        sizes[role] = len(g) - mark

    mark = len(g)
    path = ISMEMBER_FILES[membership]
    if path is not None:
        ismember = pd.read_csv(path, dtype=str, keep_default_na=False)
        if membership == "strict":
            ismember = ismember[~ismember["Organization"].isin(STRICT_EXTRA)]
        for code, org in ismember[["Country", "Organization"]].drop_duplicates().itertuples(index=False):
            org_iri = declare(names.iri(local_name("org_", org), f"organization:{org}"), "Organization")
            g.add((country_iri[code], M.isMember, org_iri))
    sizes["isMember"] = len(g) - mark

    mark = len(g)
    for _, row in read("airport").iterrows():
        iri = declare(names.iri(local_name("ap_", row["IATACode"]), f"airport:{row['IATACode']}"), "Airport")
        g.add((country_iri[row["Country"]], M.hasAirport, iri))
    sizes["airports"] = len(g) - mark

    mark = len(g)
    for code, row in frame.iterrows():
        for column, (_, prop, kind) in NUMERIC.items():
            value = row[column]
            if pd.isna(value):
                continue
            if numeric == "datatype":
                literal = Literal(int(value), datatype=XSD.integer) if kind == "integer" else Literal(float(value), datatype=XSD.double)
                g.add((country_iri[code], M[prop], literal))
            else:
                g.add((country_iri[code], RDF.type, M[bin_of(value, bins[column])]))
    sizes["numeric"] = len(g) - mark

    if closure:
        add_closure(g)
    return g, bins, sizes


PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "m": BASE,
}


def qname(iri):
    for prefix, namespace in PREFIXES.items():
        if str(iri).startswith(namespace):
            return f"{prefix}:{str(iri)[len(namespace):]}"
    raise ValueError(f"no prefix for predicate {iri}")


def write_rdfxml(g, path):
    by_subject = {}
    for s, p, o in g:
        by_subject.setdefault(s, []).append((p, o))
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<rdf:RDF"]
    lines += [f"    xmlns:{prefix}={quoteattr(namespace)}" for prefix, namespace in PREFIXES.items()]
    lines.append(">")
    for s in sorted(by_subject, key=lambda term: term.n3()):
        subject = f"rdf:nodeID={quoteattr(str(s))}" if isinstance(s, BNode) else f"rdf:about={quoteattr(str(s))}"
        lines.append(f"  <rdf:Description {subject}>")
        for p, o in sorted(by_subject[s], key=lambda po: (po[0].n3(), po[1].n3())):
            tag = qname(p)
            if isinstance(o, BNode):
                lines.append(f"    <{tag} rdf:nodeID={quoteattr(str(o))}/>")
            elif isinstance(o, URIRef):
                lines.append(f"    <{tag} rdf:resource={quoteattr(str(o))}/>")
            else:
                attribute = ""
                if o.datatype:
                    attribute = f" rdf:datatype={quoteattr(str(o.datatype))}"
                elif o.language:
                    attribute = f" xml:lang={quoteattr(o.language)}"
                lines.append(f"    <{tag}{attribute}>{escape(str(o))}</{tag}>")
        lines.append("  </rdf:Description>")
    lines.append("</rdf:RDF>")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--membership", choices=KB_MEMBERSHIP_VARIANTS, default="extended")
    parser.add_argument("--numeric", choices=["discretised", "datatype"], default="discretised")
    parser.add_argument("--closure", action="store_true")
    args = parser.parse_args()

    g, bins, sizes = build(args.membership, args.numeric, args.closure)
    KB_DIR.mkdir(exist_ok=True)
    out = KB_DIR / f"mondial_{args.membership}_{args.numeric}{'_closure' if args.closure else ''}.owl"
    write_rdfxml(g, out)
    with open(KB_DIR / "bins.json", "w", encoding="utf-8") as f:
        json.dump(bins, f, indent=2)

    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    print(f"total triples: {len(g)}")
    for key, value in sizes.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
