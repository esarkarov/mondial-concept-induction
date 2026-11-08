import csv
import re

from src.config import INPUTS_SQL, PROCESSED_DIR, SCHEMA_SQL

CSV_DIR = PROCESSED_DIR / "csv"

EXPECTED = {
    "country": 246,
    "borders": 326,
    "ismember": 10091,
    "airport": 1304,
    "encompasses": 251,
    "organization": 169,
    "spoken": 1416,
    "religion": 956,
    "ethnicgroup": 1472,
    "economy": 246,
    "geo_sea": 944,
}

CONSTRAINT_KEYWORDS = {"constraint", "primary", "unique", "foreign", "check"}
INSERT_RE = re.compile(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\(", re.IGNORECASE)
CREATE_RE = re.compile(r"CREATE\s+TABLE\s+(\w+)\s*\(", re.IGNORECASE)
NUMBER_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")
WORD_RE = re.compile(r"\w+")


def matching_paren(text, start):
    depth = 0
    in_string = False
    i = start
    while i < len(text):
        c = text[i]
        if in_string:
            if c == "'":
                if text[i + 1 : i + 2] == "'":
                    i += 1
                else:
                    in_string = False
        elif c == "'":
            in_string = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced parenthesis")


def split_top_level(body):
    parts, depth, current = [], 0, []
    for c in body:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(c)
    parts.append("".join(current))
    return parts


def parse_schema(path):
    text = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
    tables = {}
    for m in CREATE_RE.finditer(text):
        end = matching_paren(text, m.end() - 1)
        columns = []
        for item in split_top_level(text[m.end() : end]):
            tokens = item.split()
            if tokens and tokens[0].lower() not in CONSTRAINT_KEYWORDS:
                columns.append(tokens[0])
        tables[m.group(1).lower()] = columns
    return tables


def parse_value(text, i):
    while text[i].isspace():
        i += 1
    c = text[i]
    if c == "'":
        out = []
        i += 1
        while True:
            if text[i] == "'":
                if text[i + 1 : i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), i + 1
            out.append(text[i])
            i += 1
    if c == "(":
        items = []
        i += 1
        while True:
            value, i = parse_value(text, i)
            items.append(value)
            while text[i].isspace():
                i += 1
            if text[i] == ",":
                i += 1
            elif text[i] == ")":
                return tuple(items), i + 1
            else:
                raise ValueError(f"unexpected {text[i]!r} in composite value")
    m = NUMBER_RE.match(text, i)
    if m:
        return m.group(0), m.end()
    m = WORD_RE.match(text, i)
    if not m:
        raise ValueError(f"unexpected {c!r} at offset {i}")
    word = m.group(0)
    return (None if word.upper() == "NULL" else word), m.end()


def parse_row(text, i):
    values = []
    while True:
        value, i = parse_value(text, i)
        values.append(value)
        while text[i].isspace():
            i += 1
        if text[i] == ",":
            i += 1
        elif text[i] == ")":
            return values, i + 1
        else:
            raise ValueError(f"unexpected {text[i]!r} between values")


def format_cell(value):
    if value is None:
        return ""
    if isinstance(value, tuple):
        return "(" + ",".join(format_cell(v) for v in value) + ")"
    return value


def parse_inserts(path):
    text = path.read_text(encoding="utf-8")
    rows = {}
    pos = 0
    while True:
        m = INSERT_RE.search(text, pos)
        if not m:
            return rows
        values, pos = parse_row(text, m.end())
        rows.setdefault(m.group(1).lower(), []).append(values)


def main():
    schema = parse_schema(SCHEMA_SQL)
    rows = parse_inserts(INPUTS_SQL)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    unknown = sorted(set(rows) - set(schema))
    if unknown:
        print(f"INSERTs into tables missing from schema: {unknown}")

    for table, columns in schema.items():
        table_rows = rows.get(table, [])
        bad = [r for r in table_rows if len(r) != len(columns)]
        if bad:
            print(f"WARNING {table}: {len(bad)} rows with column count != {len(columns)}, first: {bad[0]}")
        with open(CSV_DIR / f"{table}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for r in table_rows:
                writer.writerow([format_cell(v) for v in r])
        print(f"{table}: {len(table_rows)}")

    print()
    for table, expected in EXPECTED.items():
        actual = len(rows.get(table, []))
        status = "ok" if actual == expected else "MISMATCH"
        print(f"{status} {table}: expected {expected}, got {actual}")


if __name__ == "__main__":
    main()
