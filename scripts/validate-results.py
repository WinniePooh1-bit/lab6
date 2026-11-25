#!/usr/bin/env python3
"""Validate PICT output, coverage, category isolation, and selected real rows."""
from __future__ import annotations

from itertools import combinations, product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def read_rows(filename: str) -> tuple[list[str], list[dict[str, str]]]:
    path = RESULTS / filename
    if not path.is_file():
        raise SystemExit(f"Missing PICT result: {filename}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise SystemExit(f"PICT result has no data rows: {filename}")
    header = lines[0].split()
    rows = []
    for number, line in enumerate(lines[1:], start=2):
        values = line.split()
        if len(values) != len(header):
            raise SystemExit(f"{filename}:{number}: expected {len(header)} columns, got {len(values)}")
        rows.append(dict(zip(header, values)))
    return header, rows

def require_header(filename: str, expected: list[str]) -> list[dict[str, str]]:
    header, rows = read_rows(filename)
    if header != expected:
        raise SystemExit(f"{filename}: header mismatch: {header!r} != {expected!r}")
    if len(rows) != len({tuple(row[name] for name in expected) for row in rows}):
        raise SystemExit(f"{filename}: duplicate test rows found")
    return rows

def assert_tway(rows: list[dict[str, str]], factors: list[str],
                domains: dict[str, list[str]], strength: int, label: str) -> None:
    for selected in combinations(factors, strength):
        expected = set(product(*(domains[name] for name in selected)))
        covered = {tuple(row[name] for name in selected) for row in rows}
        missing = expected - covered
        if missing:
            sample = sorted(missing)[:5]
            raise SystemExit(f"{label}: missing {strength}-way tuples for {selected}: {sample}")

browser_domains = {
    "Content": ["Allow", "Restrict", "Block"],
    "Cookies": ["Allow", "Restrict", "Block"],
    "Popups": ["Yes", "No"],
    "Addons": ["Yes", "No"],
    "Attacks": ["Yes", "No"],
    "Forgeries": ["Yes", "No"],
}
browser_factors = list(browser_domains)
browser2 = require_header("browser-2way.txt", browser_factors)
browser3 = require_header("browser-3way.txt", browser_factors)
assert_tway(browser2, browser_factors, browser_domains, 2, "browser 2-way")
assert_tway(browser3, browser_factors, browser_domains, 3, "browser 3-way")

transfer_domains = {
    "From": ["Valid", "Frozen", "Missing"],
    "To": ["Valid", "Missing", "SameAsFrom"],
    "Amount": ["Zero", "Normal", "OverBalance", "OverLimit"],
    "Currency": ["Same", "Different"],
}
transfer_factors = list(transfer_domains)
transfer_nc = require_header("transfer-nc.txt", transfer_factors)
assert_tway(transfer_nc, transfer_factors, transfer_domains, 2, "transfer-nc")

transfer = require_header("transfer.txt", transfer_factors)
expected_constrained = {
    ("Frozen", "Valid", "Normal", "Same"),
    ("Missing", "Valid", "Normal", "Same"),
    ("Valid", "Missing", "Normal", "Same"),
    ("Valid", "SameAsFrom", "Normal", "Same"),
    ("Valid", "Valid", "Zero", "Same"),
    ("Valid", "Valid", "OverBalance", "Same"),
    ("Valid", "Valid", "OverLimit", "Same"),
    ("Valid", "Valid", "Normal", "Same"),
    ("Valid", "Valid", "Normal", "Different"),
}
actual_constrained = {
    tuple(row[name] for name in transfer_factors) for row in transfer
}
if not actual_constrained.issubset(expected_constrained):
    raise SystemExit(
        "transfer.model emitted a row outside the allowed Category-Partition combinations: "
        f"{sorted(actual_constrained - expected_constrained)}"
    )
# PICT is a pairwise generator: it need not output every feasible tuple if its pairs
# are already covered by other rows. Validate every feasible pair from the nine
# category-partition combinations rather than incorrectly requiring all nine rows.
for pair in combinations(range(len(transfer_factors)), 2):
    left, right = pair
    feasible_pairs = {
        (row[left], row[right]) for row in
        [tuple(values) for values in expected_constrained]
    }
    observed_pairs = {
        (tuple(row[name] for name in transfer_factors)[left],
         tuple(row[name] for name in transfer_factors)[right])
        for row in transfer
    }
    missing_pairs = feasible_pairs - observed_pairs
    if missing_pairs:
        raise SystemExit(
            f"transfer.model missed feasible pair for {transfer_factors[left]}/{transfer_factors[right]}: "
            f"{sorted(missing_pairs)}"
        )
if len(transfer) != 8:
    raise SystemExit(f"Expected deterministic 8-row constrained pairwise array, got {len(transfer)}")
if not any(
    row["From"] == "Valid" and row["To"] == "Valid" and row["Amount"] == "Normal"
    for row in transfer
):
    raise SystemExit("transfer.model must contain a positive happy-path row.")

transfer_neg = require_header("transfer-neg.txt", transfer_factors)
negative_values = {
    "From": {"~Frozen", "~Missing"},
    "To": {"~Missing", "~SameAsFrom"},
    "Amount": {"~Zero", "~OverBalance", "~OverLimit"},
    "Currency": set(),
}
seen_negative = set()
for index, row in enumerate(transfer_neg, start=1):
    selected = [name for name in transfer_factors if row[name].startswith("~")]
    if len(selected) > 1:
        raise SystemExit(f"transfer-neg row {index} masks more than one error: {row}")
    for name in selected:
        if row[name] not in negative_values[name]:
            raise SystemExit(f"Unexpected negative value in {name}: {row[name]}")
        seen_negative.add((name, row[name]))

expected_negative = {(name, value) for name, values in negative_values.items() for value in values}
if seen_negative != expected_negative:
    raise SystemExit(
        f"transfer-neg did not emit every negative choice: missing={sorted(expected_negative - seen_negative)}"
    )

# PICT negative testing must pair every invalid value only with positive values,
# and cover each positive value in all remaining dimensions.
positive_domains = {
    "From": ["Valid"],
    "To": ["Valid"],
    "Amount": ["Normal"],
    "Currency": ["Same", "Different"],
}
for name, values in negative_values.items():
    for value in values:
        matching = [row for row in transfer_neg if row[name] == value]
        for row in matching:
            for other in transfer_factors:
                if other != name and row[other].startswith("~"):
                    raise SystemExit(f"Negative value paired with another negative value: {row}")
        for other in transfer_factors:
            if other == name:
                continue
            observed = {row[other] for row in matching}
            missing = set(positive_domains[other]) - observed
            if missing:
                raise SystemExit(
                    f"Negative {name}={value} was not paired with positive {other} values: {sorted(missing)}"
                )

def find_row(predicate, description):
    for row in transfer_neg:
        if predicate(row):
            return row
    raise SystemExit(f"Could not select required generated row: {description}")

selected = {
    "happy": find_row(
        lambda r: r["From"] == "Valid" and r["To"] == "Valid"
        and r["Amount"] == "Normal" and r["Currency"] == "Same",
        "valid happy path"
    ),
    "frozen": find_row(
        lambda r: r["From"] == "~Frozen" and r["To"] == "Valid"
        and r["Amount"] == "Normal",
        "single frozen-source error"
    ),
    "zero": find_row(
        lambda r: r["From"] == "Valid" and r["To"] == "Valid"
        and r["Amount"] == "~Zero",
        "single zero-amount error"
    ),
}
(RESULTS / "pict-selected-rows.json").write_text(
    json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

counts = {
    "browser_2way": len(browser2),
    "browser_3way": len(browser3),
    "transfer_unconstrained": len(transfer_nc),
    "transfer_constrained": len(transfer),
    "transfer_category_partition_allowed": len(expected_constrained),
    "transfer_negative": len(transfer_neg),
    "transfer_negative_rows_with_one_error": sum(
        1 for row in transfer_neg if any(row[name].startswith("~") for name in transfer_factors)
    ),
    "transfer_negative_error_choices": len(seen_negative),
}
(RESULTS / "pict-model-counts.json").write_text(
    json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("PICT output validation: PASS")
for name, count in counts.items():
    print(f"{name}={count}")
print("transfer.model: 8-row pairwise array covers every feasible pair from 9 allowed Category-Partition combinations.")
print("transfer-neg.model: each row has at most one negative value; all 7 negative choices present.")
print("browser models: pairwise and 3-way tuple coverage checked against the full Cartesian domains.")
