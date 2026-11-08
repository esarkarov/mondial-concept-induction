import pandas as pd

from src.config import (
    EU_CANDIDATE_TYPE,
    EU_MEMBERSHIP_TYPE,
    LABEL_SET,
    LABEL_SETS,
    MASK_EXTENDED,
    MASKED_ORGANIZATIONS,
    PROCESSED_DIR,
)

CSV_DIR = PROCESSED_DIR / "csv"
EU_NAME = "european union"


def read(table):
    return pd.read_csv(CSV_DIR / f"{table}.csv", dtype=str, keep_default_na=False)


def find_eu(organization):
    names = organization["Name"].str.lower()
    candidates = organization[names.str.contains(EU_NAME)]
    print("Organizations matching 'European Union':")
    print(candidates.to_string(index=False))
    exact = organization[names == EU_NAME]
    if len(exact) != 1:
        raise SystemExit(f"expected one exact match for {EU_NAME!r}, got {len(exact)}")
    return exact.iloc[0]["Abbreviation"]


def as_frame(country, codes):
    frame = country[country["Code"].isin(codes)][["Code", "Name"]]
    return frame.rename(columns={"Code": "code", "Name": "name"}).sort_values("name")


def show(title, frame):
    print(f"\n{title} ({len(frame)})")
    print(", ".join(frame["name"]))


def main():
    country = read("country")
    organization = read("organization")
    ismember = read("ismember")

    eu = find_eu(organization)
    print(f"\nEU abbreviation: {eu}")

    eu_rows = ismember[ismember["Organization"] == eu]
    print("\nDistinct Type values for the EU:")
    print(eu_rows["Type"].value_counts().to_string())

    member_codes = set(eu_rows.loc[eu_rows["Type"] == EU_MEMBERSHIP_TYPE, "Country"])
    excluded_rows = eu_rows[eu_rows["Type"] != EU_MEMBERSHIP_TYPE]
    excluded_codes = set(excluded_rows["Country"])
    print("\nNon-member EU rows:")
    print(excluded_rows.merge(country[["Code", "Name"]], left_on="Country", right_on="Code")[["Country", "Name", "Type"]].to_string(index=False))

    unexpected = set(excluded_rows["Type"]) - {EU_CANDIDATE_TYPE}
    if unexpected:
        print(f"WARNING: Type values other than {EU_CANDIDATE_TYPE!r}: {sorted(unexpected)}")
    unknown = (member_codes | excluded_codes) - set(country["Code"])
    if unknown:
        print(f"WARNING: EU codes missing from country table: {sorted(unknown)}")

    positives = as_frame(country, member_codes)
    excluded = as_frame(country, excluded_codes)
    negatives = as_frame(country, set(country["Code"]) - member_codes - excluded_codes)

    show("Positives", positives)
    show("Excluded candidates", excluded)
    show("Negatives", negatives)

    for label, expected, frame in [("positives", 27, positives), ("candidates", 7, excluded)]:
        if len(frame) != expected:
            print(f"WARNING: expected {expected} {label}, got {len(frame)}")

    uk = country[country["Name"].str.contains("United Kingdom", case=False)]
    print("\nUnited Kingdom in country table:")
    print(uk[["Name", "Code"]].to_string(index=False))
    for _, row in uk.iterrows():
        uk_eu = ismember[(ismember["Country"] == row["Code"]) & (ismember["Organization"] == eu)]
        print(f"EU rows for {row['Code']}: {len(uk_eu)}")
        if len(uk_eu):
            print(uk_eu.to_string(index=False))
        in_negatives = row["Code"] in set(negatives["code"])
        print(f"{row['Code']} is in negatives: {in_negatives}")

    known = set(organization["Abbreviation"])
    missing = [a for a in MASKED_ORGANIZATIONS if a not in known]
    print(f"\nMasked organizations missing from organization table: {missing if missing else 'none'}")
    for a in MASKED_ORGANIZATIONS:
        if a in known:
            name = organization.loc[organization["Abbreviation"] == a, "Name"].iloc[0]
            count = (ismember["Organization"] == a).sum()
            print(f"  {a}: {name} ({count} isMember rows)")

    print("\nisMember rows removed per masked organization:")
    removed = ismember["Organization"].value_counts()
    for a in MASKED_ORGANIZATIONS:
        print(f"  {a}: {removed.get(a, 0)}")
    print(f"  total masked: {sum(removed.get(a, 0) for a in MASKED_ORGANIZATIONS)}")
    print(f"  EU: {removed.get(eu, 0)}")

    masked = ismember[~ismember["Organization"].isin([*MASKED_ORGANIZATIONS, eu])]
    assert not (masked["Organization"] == eu).any()
    print(f"\nisMember rows: {len(ismember)} -> {len(masked)} after dropping masked organizations and {eu}")

    extended = ismember[~ismember["Organization"].isin([*MASK_EXTENDED, eu])]
    assert not (extended["Organization"] == eu).any()
    print("\nRows removed per added abbreviation (extended mask):")
    for a in MASK_EXTENDED[len(MASKED_ORGANIZATIONS):]:
        in_org = a in known
        print(f"  {a}: {removed.get(a, 0)}{'' if in_org else ' (NOT in organization table)'}")
    print(f"isMember rows extended: {len(ismember)} -> {len(extended)}")
    extended.to_csv(PROCESSED_DIR / "ismember_masked_extended.csv", index=False)

    dependent = set(read("politics").query("Dependent != ''")["Country"])
    sovereign = negatives[~negatives["code"].isin(dependent)]
    print(f"\nLabel sets: all = {len(positives)} positives / {len(negatives)} negatives; "
          f"sovereign = {len(positives)} positives / {len(sovereign)} negatives "
          f"(dropped {len(negatives) - len(sovereign)})")
    if LABEL_SET not in LABEL_SETS:
        raise SystemExit(f"LABEL_SET must be one of {LABEL_SETS}")
    print(f"Writing label set: {LABEL_SET}")
    if LABEL_SET == "sovereign":
        negatives = sovereign

    positives.to_csv(PROCESSED_DIR / "eu_positives.csv", index=False)
    negatives.to_csv(PROCESSED_DIR / "eu_negatives.csv", index=False)
    excluded.to_csv(PROCESSED_DIR / "eu_excluded_candidates.csv", index=False)
    masked.to_csv(PROCESSED_DIR / "ismember_masked.csv", index=False)


if __name__ == "__main__":
    main()
