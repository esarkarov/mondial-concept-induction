import numpy as np
import pandas as pd

from src.config import MEMBERSHIP_VARIANTS, PROCESSED_DIR
from src.labels import read

ISMEMBER_FILES = {
    "masked": PROCESSED_DIR / "ismember_masked.csv",
    "extended": PROCESSED_DIR / "ismember_masked_extended.csv",
    "none": None,
}

MIN_CATEGORY = 5
MIN_SHARE_COUNTRIES = 10
MIN_ORG_MEMBERS = 3


def numeric_table(table, columns, rename, key):
    frame = read(table).set_index(key)[columns].apply(pd.to_numeric, errors="coerce")
    return frame.rename(columns=rename)


def one_hot(series, prefix, min_count):
    known = series.dropna()
    keep = known.value_counts()
    keep = keep[keep >= min_count].index
    frame = pd.DataFrame(
        {f"{prefix}_{value}": (series == value).astype(float) for value in keep},
        index=series.index,
    )
    frame[series.isna()] = np.nan
    return frame


def share_columns(table, key, prefix, codes, min_countries):
    data = read(table)
    data["Percentage"] = pd.to_numeric(data["Percentage"], errors="coerce")
    data = data[data[key].isin(codes)]
    counts = data.groupby("Name")[key].nunique()
    keep = counts[counts >= min_countries].index
    wide = data[data["Name"].isin(keep)].pivot_table(
        index=key, columns="Name", values="Percentage", aggfunc="sum"
    )
    wide = wide.reindex(codes).add_prefix(f"{prefix}_")
    has_rows = pd.Index(codes).isin(data[key])
    wide.loc[has_rows] = wide.loc[has_rows].fillna(0.0)
    return wide


def build_base(codes):
    country = numeric_table("country", ["Area", "Population"],{"Area": "area", "Population": "population"}, "Code")
    economy = numeric_table(
        "economy",
        ["GDP", "Agriculture", "Service", "Industry", "Inflation", "Unemployment"],
        {c: c.lower() for c in ["GDP", "Agriculture", "Service", "Industry", "Inflation", "Unemployment"]},
        "Country",
    )
    population = numeric_table(
        "population",
        ["Population_Growth", "Infant_Mortality"],
        {"Population_Growth": "pop_growth", "Infant_Mortality": "infant_mortality"},
        "Country",
    )
    frame = pd.DataFrame(index=codes)
    for part in (country, economy, population):
        frame = frame.join(part)

    politics = read("politics").set_index("Country").reindex(codes)
    government = politics["Government"].str.lower().replace("", np.nan)
    frequent = government.value_counts()
    frequent = frequent[frequent >= MIN_CATEGORY].index
    government = government.where(government.isin(frequent), "other").where(government.notna())
    frame = frame.join(one_hot(government, "gov", 1))
    frame["independence_year"] = pd.to_numeric(politics["Independence"].str[:4], errors="coerce")

    borders = read("borders")
    pairs = pd.concat(
        [
            borders[["Country1", "Country2"]].set_axis(["a", "b"], axis=1),
            borders[["Country2", "Country1"]].set_axis(["a", "b"], axis=1),
        ]
    ).drop_duplicates()
    frame["n_neighbors"] = pairs.groupby("a").size().reindex(codes).fillna(0).astype(float)

    frame["coastal"] = pd.Index(codes).isin(set(read("geo_sea")["Country"])).astype(float)

    encompasses = read("encompasses")
    for continent in sorted(encompasses["Continent"].unique()):
        members = set(encompasses.loc[encompasses["Continent"] == continent, "Country"])
        frame[f"continent_{continent}"] = pd.Index(codes).isin(members).astype(float)

    spoken = read("spoken")
    spoken["Percentage"] = pd.to_numeric(spoken["Percentage"], errors="coerce")
    top = spoken.sort_values("Percentage", ascending=False).drop_duplicates("Country").set_index("Country")["Language"]
    frame = frame.join(one_hot(top.reindex(codes), "toplang", MIN_CATEGORY))

    frame = frame.join(share_columns("religion", "Country", "religion", codes, MIN_SHARE_COUNTRIES))
    frame = frame.join(share_columns("ethnicgroup", "Country", "ethnic", codes, MIN_SHARE_COUNTRIES))
    return frame


def organization_columns(codes, ismember):
    sizes = ismember.groupby("Organization")["Country"].nunique()
    kept = sizes[sizes >= MIN_ORG_MEMBERS].index
    member_sets = ismember.groupby("Organization")["Country"].agg(set)
    return pd.DataFrame(
        {f"org_{org}": pd.Index(codes).isin(member_sets[org]).astype(float) for org in kept},
        index=codes,
    )


def main():
    labels = pd.concat(
        [
            pd.read_csv(PROCESSED_DIR / "eu_positives.csv", dtype=str, keep_default_na=False).assign(label=1),
            pd.read_csv(PROCESSED_DIR / "eu_negatives.csv", dtype=str, keep_default_na=False).assign(label=0),
        ],
        ignore_index=True,
    )
    codes = list(labels["code"])
    base = build_base(codes)
    print(f"countries: {len(codes)}; base feature columns: {base.shape[1]}")
    missing = base.isna().sum()
    print("columns with missing values:")
    print(missing[missing > 0].to_string())

    for variant in MEMBERSHIP_VARIANTS:
        features = base
        path = ISMEMBER_FILES[variant]
        if path is not None:
            features = base.join(organization_columns(codes, read_path(path)))
        out = features.reset_index(names="code").merge(labels[["code", "label"]], on="code")
        out = out[["code", "label"] + [c for c in features.columns]]
        out.to_csv(PROCESSED_DIR / f"features_{variant}.csv", index=False)
        org_cols = sum(c.startswith("org_") for c in features.columns)
        print(f"features_{variant}.csv: {out.shape[0]} rows, {features.shape[1]} features ({org_cols} organization columns)")


def read_path(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


if __name__ == "__main__":
    main()
