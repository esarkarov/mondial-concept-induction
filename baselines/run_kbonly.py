import json

import numpy as np
import pandas as pd

from baselines.run_baselines import METRICS, models, score, summarize
from src.config import KB_DIR, PROCESSED_DIR, RESULTS_DIR, STRICT_EXTRA
from src.features import ISMEMBER_FILES, organization_columns
from src.kb import bin_of, numeric_table
from src.labels import read
from src.problems import restrict

OUT_DIR = RESULTS_DIR / "extensions"
VARIANTS = ["strict", "extended"]
KINDS = ["kb_raw", "kb_binned"]
MIN_INDICATOR = 10
NUMERIC_COLUMNS = ["population", "area", "gdp", "gdp_per_capita", "inflation", "infant_mortality", "population_growth", "n_airports"]
SHARE_PREFIXES = ("religion_", "ethnic_")
NO_COUNTERPART = {
    "agriculture": "economy.Agriculture", "service": "economy.Service", "industry": "economy.Industry", "unemployment": "economy.Unemployment",
    "independence_year": "politics.Independence",
}
EXACT = {
    "area": ("country.Area", "numeric attribute `area` (quartile bin class AreaQ1..Q4, or datatype property)"),
    "population": ("country.Population", "numeric attribute `population` (PopulationQ1..Q4, or datatype property)"),
    "gdp": ("economy.GDP", "numeric attribute `gdp` (GdpQ1..Q4, or datatype property)"),
    "inflation": ("economy.Inflation", "numeric attribute `inflation` (InflationQ1..Q4, or datatype property)"),
    "pop_growth": ("population.Population_Growth", "numeric attribute `populationGrowth` (PopulationGrowthQ1..Q4, or datatype property)"),
    "infant_mortality": ("population.Infant_Mortality", "numeric attribute `infantMortality` (InfantMortalityQ1..Q4, or datatype property)"),
    "n_neighbors": ("borders", "count of `neighbor` fillers (role between country individuals)"),
    "coastal": ("geo_sea", "`borderedBySea` role to sea individuals (the feature collapses it to any/none)"),
    "n_airports": ("airport", "numeric attribute `nAirports` (NAirportsQ bins) and the `hasAirport` role to airport individuals"),
}


def audit_row(feature, in_strict):
    if feature in NO_COUNTERPART:
        return ("economy/politics column", NO_COUNTERPART[feature], "no", "not in the KB")
    if feature.startswith("gov_"):
        return ("politics.Government one-hot", "politics.Government", "no", "not in the KB")
    if feature.startswith(SHARE_PREFIXES):
        table = "religion.Percentage" if feature.startswith("religion_") else "ethnicgroup.Percentage"
        role = "follows" if feature.startswith("religion_") else "hasEthnicGroup"
        return ("share column", table, "no", f"share value not in the KB; only presence through the `{role}` role (used as an indicator in kb_raw and kb_binned)")
    if feature.startswith("continent_"):
        return ("continent indicator", "encompasses", "yes", "`encompassed` role to a continent individual (percentage not kept)")
    if feature.startswith("toplang_"):
        return ("top language indicator", "spoken", "yes", "`mainLanguage` role (sub-property of `speaks`), same top-by-percentage rule")
    if feature.startswith("org_"):
        return ("organization indicator", "ismember", "yes", "`isMember` role to an organization individual (membership Type not kept)")
    table, form = EXACT[feature]
    return ("base column", table, "yes", form)


def feature_audit():
    extended = pd.read_csv(PROCESSED_DIR / "features_extended.csv", nrows=0).columns.drop(["code", "label"])
    strict = set(pd.read_csv(PROCESSED_DIR / "features_strict.csv", nrows=0).columns)
    rows = []
    for feature in extended:
        group, table, counterpart, form = audit_row(feature, feature in strict)
        rows.append({"feature": feature, "group": group, "source_table": table, "in_strict": feature in strict, "in_extended": True,
                     "kb_counterpart": counterpart, "kb_form": form})
    rows.append({"feature": "(gdp_per_capita)", "group": "KB attribute without a baseline column", "source_table": "economy.GDP / country.Population",
                 "in_strict": False, "in_extended": False, "kb_counterpart": "KB only", "kb_form": "numeric attribute `gdpPerCapita` (GdpPerCapitaQ1..Q4); used in kb_raw and kb_binned"})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "feature_audit.csv", index=False)
    return table


def indicators(table, key, column, prefix, codes, min_countries):
    data = read(table)[[key, column]].drop_duplicates()
    data = data[data[key].isin(codes)]
    counts = data.groupby(column)[key].nunique()
    keep = sorted(counts[counts >= min_countries].index)
    members = data.groupby(column)[key].agg(set)
    return pd.DataFrame({f"{prefix}_{v}": pd.Index(codes).isin(members[v]).astype(float) for v in keep}, index=codes)


def role_columns(codes):
    frame = pd.DataFrame(index=codes)
    encompasses = read("encompasses")[["Country", "Continent"]].drop_duplicates()
    for continent in sorted(encompasses["Continent"].unique()):
        frame[f"continent_{continent}"] = pd.Index(codes).isin(set(encompasses.loc[encompasses["Continent"] == continent, "Country"])).astype(float)
    borders = read("borders")
    pairs = pd.concat([borders[["Country1", "Country2"]].set_axis(["a", "b"], axis=1),
                       borders[["Country2", "Country1"]].set_axis(["a", "b"], axis=1)]).drop_duplicates()
    frame["n_neighbors"] = pairs.groupby("a").size().reindex(codes).fillna(0).astype(float)
    for part in (indicators("geo_sea", "Country", "Sea", "sea", codes, MIN_INDICATOR),
                 indicators("spoken", "Country", "Language", "speaks", codes, MIN_INDICATOR),
                 indicators("religion", "Country", "Name", "follows", codes, MIN_INDICATOR),
                 indicators("ethnicgroup", "Country", "Name", "ethnic", codes, MIN_INDICATOR)):
        frame = frame.join(part)
    return frame


def membership_columns(codes, variant):
    ismember = pd.read_csv(ISMEMBER_FILES[variant], dtype=str, keep_default_na=False)
    if variant == "strict":
        ismember = ismember[~ismember["Organization"].isin(STRICT_EXTRA)]
    return organization_columns(codes, ismember)


def binned(values, bins):
    columns = {}
    for column in NUMERIC_COLUMNS:
        classes = [b["class"] for b in bins[column]["bins"]]
        assigned = values[column].map(lambda v: None if pd.isna(v) else bin_of(v, bins[column]))
        for cls in classes:
            columns[cls] = (assigned == cls).astype(float)
    return pd.DataFrame(columns, index=values.index)


def build_features(codes, kind, variant, values, bins):
    numeric = values.loc[codes, NUMERIC_COLUMNS]
    numeric = numeric if kind == "kb_raw" else binned(numeric, bins)
    return numeric.join(role_columns(codes)).join(membership_columns(codes, variant))


def fit_predict(make, X, y, train, test):
    model = make()
    model.fit(X.loc[train], y.loc[train])
    return model, model.predict(X.loc[test])


def run_problem(problem, folds, labels, kinds_variants, values, bins):
    summary, predictions, importances = [], [], {}
    for kind, variant in kinds_variants:
        features = build_features(list(labels.index), kind, variant, values, bins)
        features.reset_index(names="code").assign(label=labels.values).to_csv(PROCESSED_DIR / f"features_{kind}_{variant}.csv", index=False)
        for model_name, make in models().items():
            records, fitted = [], []
            for (repeat, fold), test in folds.groupby(["repeat", "fold"]):
                train = folds[(folds["repeat"] == repeat) & (folds["fold"] != fold)]
                model, predicted = fit_predict(make, features, labels, train["code"], test["code"])
                fitted.append(model)
                y_true = test["label"].to_numpy()
                records.append({"repeat": repeat, "fold": fold, **score(y_true, predicted), "y_true": y_true, "y_pred": predicted})
                config = f"kbonly_{'e1_' if problem == 'europe' else ''}{kind}_{variant}_{model_name}"
                predictions += [(config, repeat, code, label, int(p)) for code, label, p in zip(test["code"], y_true, predicted)]
            summary.append(summarize(records, variant=f"{kind}_{variant}", model=model_name, problem=problem, n_features=features.shape[1]))
            if model_name == "random_forest":
                importances[(kind, variant)] = pd.Series(np.mean([m[-1].feature_importances_ for m in fitted], axis=0), index=features.columns)
    return summary, predictions, importances


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = feature_audit()
    print(audit["kb_counterpart"].value_counts().to_string())
    folds = pd.read_csv(PROCESSED_DIR / "folds.csv", dtype={"code": str})
    labels = folds[folds["repeat"] == 0].set_index("code")["label"].sort_index()
    values = numeric_table(read("country"))
    bins = json.loads((KB_DIR / "bins.json").read_text(encoding="utf-8"))
    combos = [(k, v) for v in VARIANTS for k in KINDS]
    summary, predictions, _ = run_problem("all", folds, labels, combos, values, bins)
    europe_folds = restrict(folds, "europe")
    europe_labels = labels.loc[sorted(set(europe_folds["code"]))]
    e1_summary, e1_predictions, importances = run_problem("europe", europe_folds, europe_labels, [(k, "strict") for k in KINDS], values, bins)
    pd.DataFrame(summary + e1_summary).to_csv(OUT_DIR / "kbonly.csv", index=False)
    pd.DataFrame(predictions + e1_predictions, columns=["config", "repeat", "code", "label", "predicted"]).to_csv(OUT_DIR / "predictions_kbonly.csv", index=False)
    for (kind, variant), series in importances.items():
        series.sort_values(ascending=False).rename("importance").to_csv(OUT_DIR / f"e5_importances_e1_{kind}_{variant}.csv", index_label="feature")
    table = pd.DataFrame(summary + e1_summary)[["problem", "variant", "model", "n_features"]].copy()
    table["pooled F1 [CI]"] = [f"{r['f1_pooled_mean']:.3f} [{r['f1_pooled_ci_low']:.3f}, {r['f1_pooled_ci_high']:.3f}]" for r in summary + e1_summary]
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
