#!/usr/bin/env python3
"""Populate the Lab06 report from actual PICT outputs and selected generated rows."""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
README_PATH = ROOT / "README.md"
TICK = chr(96)

def required(name: str) -> str:
    path = RESULTS / name
    if not path.is_file():
        raise SystemExit(f"Missing required evidence: {name}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise SystemExit(f"Empty required evidence: {name}")
    return text

counts = json.loads(required("pict-model-counts.json"))
selected = json.loads(required("pict-selected-rows.json"))
build_log = required("pict-build.txt")
if "pict commit " not in build_log or "Usage:" not in build_log:
    raise SystemExit("pict-build.txt must include the actual PICT source commit and CLI usage.")
if counts["transfer_category_partition_allowed"] != 9:
    raise SystemExit(f"Expected 9 allowed Category-Partition combinations, got {counts['transfer_category_partition_allowed']}")
if counts["transfer_constrained"] != 8:
    raise SystemExit(f"Expected an 8-row constrained pairwise array, got {counts['transfer_constrained']}")
if counts["transfer_negative_error_choices"] != 7:
    raise SystemExit("Expected all seven negative/error choices in transfer-neg output.")

def result_for(row):
    for field in ("From", "To", "Amount"):
        value = row[field]
        if value.startswith("~"):
            mapping = {
                ("From", "~Frozen"): "ERROR_FROZEN",
                ("From", "~Missing"): "ERROR_NO_FROM",
                ("To", "~Missing"): "ERROR_NO_TO",
                ("To", "~SameAsFrom"): "ERROR_SAME_ACCOUNT",
                ("Amount", "~Zero"): "ERROR_BAD_AMOUNT",
                ("Amount", "~OverBalance"): "ERROR_INSUFFICIENT",
                ("Amount", "~OverLimit"): "ERROR_LIMIT",
            }
            return mapping[(field, value)]
    return "OK"

def concrete_body(row):
    source = {"Valid": "ACC001", "~Frozen": "ACC_FROZEN", "~Missing": "ACC404"}[row["From"]]
    destination = {"Valid": "ACC002", "~Missing": "ACC404", "~SameAsFrom": "ACC001"}[row["To"]]
    currency = "MNT" if row["Currency"] == "Same" else "USD"
    amount_map = {
        ("Normal", "Same"): 50000,
        ("Normal", "Different"): 10,
        ("~Zero", "Same"): 0,
        ("~Zero", "Different"): 0,
        ("~OverBalance", "Same"): 150000,
        ("~OverBalance", "Different"): 50,
        ("~OverLimit", "Same"): 250000,
        ("~OverLimit", "Different"): 75,
    }
    return {"from": source, "to": destination, "amount": amount_map[(row["Amount"], row["Currency"])], "currency": currency}

def setup_for(row):
    if row["From"] == "~Frozen":
        source = "ACC_FROZEN: frozen=true, currency=MNT"
    elif row["From"] == "~Missing":
        source = "ACC404: absent"
    else:
        if row["Amount"] == "~OverBalance":
            balance, daily = "100,000 MNT", "250,000 MNT"
        elif row["Amount"] == "~OverLimit":
            balance, daily = "500,000 MNT", "200,000 MNT"
        else:
            balance, daily = "500,000 MNT", "500,000 MNT"
        source = f"ACC001: active, balance={balance}, daily remaining={daily}, currency=MNT"
    if row["To"] == "~Missing":
        destination = "ACC404: absent"
    elif row["To"] == "~SameAsFrom":
        destination = "ACC001 (same as source)"
    else:
        destination = "ACC002: active, currency=MNT"
    fx = "; FX rate 1 USD = 3,500 MNT" if row["Currency"] == "Different" else ""
    return source + "; " + destination + fx

def render_case(title, row):
    generated = ", ".join(f"{key}={value}" for key, value in row.items())
    body = json.dumps(concrete_body(row), ensure_ascii=False, separators=(",", ":"))
    result = result_for(row)
    oracle = "HTTP 201, result=OK" if result == "OK" else f"HTTP 200, result={result}"
    return f"| {title} | {TICK}{generated}{TICK} | {setup_for(row)} | {TICK}{body}{TICK} | {oracle} |"

happy, frozen, zero = selected["happy"], selected["frozen"], selected["zero"]
if result_for(happy) != "OK" or result_for(frozen) != "ERROR_FROZEN" or result_for(zero) != "ERROR_BAD_AMOUNT":
    raise SystemExit("Selected PICT rows do not represent the expected happy/frozen/zero cases.")

readme = README_PATH.read_text(encoding="utf-8")
def replace_section(text, start_marker, end_marker, content):
    if start_marker not in text or end_marker not in text:
        raise SystemExit(f"Missing README markers: {start_marker} / {end_marker}")
    before, rest = text.split(start_marker, 1)
    _, after = rest.split(end_marker, 1)
    return before + start_marker + "\n\n" + content.rstrip() + "\n\n" + end_marker + after

summary_table = (
    "| PICT модель / гаралт | Мөрийн тоо | Тайлбар |\n"
    "|---|---:|---|\n"
    f"| browser 2-way | {counts['browser_2way']} | Pairwise бүх хосын утгыг хамруулсан |\n"
    f"| browser 3-way | {counts['browser_3way']} | 144 боломжит гурвалын хамралт |\n"
    f"| transfer-nc (хязгаарлалтгүй) | {counts['transfer_unconstrained']} | 2-way; олон алдаатай хослол үүсч болно |\n"
    f"| transfer (A2 хязгаарлалттай) | {counts['transfer_constrained']} | 9 зөвшөөрөгдсөн CP хувилбарын pairwise бүрхүүл |\n"
    f"| transfer-neg (~ сөрөг утгатай) | {counts['transfer_negative']} | Нэг мөрөнд хамгийн ихдээ нэг сөрөг утга |"
)
readme = replace_section(readme, "<!-- PICT-COUNTS-START -->", "<!-- PICT-COUNTS-END -->", summary_table)

case_table = (
    "| PICT-ээс сонгосон тест | Үүсгэсэн мөр | Setup (данс, үлдэгдэл, лимит) | POST /transfer body | Oracle |\n"
    "|---|---|---|---|---|\n"
    + render_case("Happy path", happy) + "\n"
    + render_case("Нэг алдаа — царцаасан from", frozen) + "\n"
    + render_case("Нэг алдаа — amount=0", zero)
)
readme = replace_section(readme, "<!-- PICT-CASES-START -->", "<!-- PICT-CASES-END -->", case_table)

explanation = (
    f"- Browser-ийн бүрэн оролтын олонлог: **144**; 3-way PICT мөр: **{counts['browser_3way']}**.\n"
    f"- 2-way browser мөр: **{counts['browser_2way']}**. Лекцийн гараар хийсэн 9 мөртэй харьцуулахад "
    + ("олон" if counts["browser_2way"] > 9 else "их биш")
    + " мөр гарсан. PICT greedy алгоритм нь тухайн алхамд хамгийн олон шинэ хосыг хамруулах сонголт хийдэг ч глобал хамгийн цөөн мөрийн оптимумыг баталгаажуулдаггүй.\n"
    f"- Category-Partition-ийн зөвшөөрөгдсөн олонлог 72-оос 9 болсон (**72 → 9**). PICT constrained model {counts['transfer_constrained']} мөрөөр эдгээр хувилбарын бүх боломжит pairwise хосыг бүрхсэн; бүх tuple-ийг тус тусад нь хэвлэх шаардлагагүй.\n"
    f"- transfer-neg output дотор {counts['transfer_negative_rows_with_one_error']} мөр дор хаяж нэг сөрөг утгатай бөгөөд долоон сөрөг сонголт бүгд орсон."
)
readme = replace_section(readme, "<!-- PICT-ANALYSIS-START -->", "<!-- PICT-ANALYSIS-END -->", explanation)
README_PATH.write_text(readme, encoding="utf-8")
print("README.md бодит PICT мөрийн тоо болон PICT-ээс сонгосон тестүүдээр шинэчлэгдлээ.")
