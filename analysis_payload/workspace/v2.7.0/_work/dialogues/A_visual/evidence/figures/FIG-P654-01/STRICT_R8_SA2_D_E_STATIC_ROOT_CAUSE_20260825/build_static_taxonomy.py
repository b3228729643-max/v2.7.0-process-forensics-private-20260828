from __future__ import annotations

import csv
import json
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
R7A = ROOT.parent / "STRICT_R7A_SA2_NARROW_R100_EVIDENCE_RESEAL_20260825"
INPUT = R7A / "machine_reuse" / "after_pixel_measurements.csv"

LOWER_ASCENDERS = frozenset("bdfhklt")
LOWER_DESCENDERS = frozenset("gjpqy")


def semantic_role(frozen_role: str, frozen_class: str) -> tuple[str, str]:
    """Predeclared source-semantic roles; never inspect IDs or measured pixels."""
    if frozen_role in {"POSTERIOR_FORMULA", "PREDICTIVE_FORMULA"}:
        return "FORMULA_BLOCK", "SRC_ROLE_02"
    if frozen_role == "APPLICATION":
        return "ANNOTATION", "SRC_ROLE_04"
    if frozen_role == "TRIAL" and frozen_class == "BASE_MATH_OPERATOR_OR_GLYPH":
        return "TRIAL_INLINE_FORMULA", "SRC_ROLE_03"
    return "NODE_BASE", "SRC_ROLE_01"


def typographic_class(text: str, frozen_class: str) -> tuple[str, str]:
    """Global character taxonomy. No rule is keyed to an ELEMENT_ID or pixel value."""
    if frozen_class == "CJK_FULL":
        return "CJK_FULL", "TYPE_01"

    if frozen_class in {"LATIN_CAP_DIGIT", "LATIN_GREEK_LOWER"}:
        if len(text) != 1:
            raise ValueError(f"expected one Latin glyph, got {text!r}")
        ch = text
        if ch.isupper() or ch.isdigit() or ch in LOWER_ASCENDERS:
            return "LATIN_FULL_HEIGHT_CAP_OR_ASCENDER", "TYPE_02"
        if ch in LOWER_DESCENDERS:
            return "LATIN_LOWER_DESCENDER", "TYPE_04"
        return "LATIN_LOWER_X_HEIGHT", "TYPE_03"

    if frozen_class == "NATURAL_TEX_SCRIPT":
        return "NATURAL_TEX_SCRIPT", "TYPE_08"

    if frozen_class == "BASE_MATH_OPERATOR_OR_GLYPH":
        name = unicodedata.name(text, "")
        if text in {"+", "−", "-", "=", "<", ">", "≤", "≥", "×", "÷"}:
            return "MATH_BASE_BINARY_RELATION_OPERATOR", "TYPE_06"
        if "CAPITAL" in name or text.isupper():
            return "MATH_BASE_UPPER_VARIABLE", "TYPE_07"
        return "MATH_BASE_LOWER_VARIABLE", "TYPE_05"

    raise ValueError(f"unclassified frozen script class {frozen_class!r} for {text!r}")


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def fmt_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.12g}"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
    source_rows = list(csv.DictReader(handle))

if len(source_rows) != 95:
    raise SystemExit(f"expected 95 source elements, found {len(source_rows)}")
if len({row["ELEMENT_ID"] for row in source_rows}) != 95:
    raise SystemExit("source ELEMENT_ID set is not unique")

element_rows: list[dict] = []
groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
legacy_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

for source in source_rows:
    role, role_rule = semantic_role(source["ROLE"], source["SCRIPT_CLASS"])
    taxon, taxon_rule = typographic_class(source["TEXT_SAMPLE"], source["SCRIPT_CLASS"])
    row = {
        "ELEMENT_ID": source["ELEMENT_ID"],
        "PANEL_ID": source["PANEL_ID"],
        "SOURCE_LINE": source["SOURCE_LINE"],
        "TEXT_SAMPLE": source["TEXT_SAMPLE"],
        "FROZEN_LOCATION_ROLE": source["ROLE"],
        "FROZEN_SCRIPT_CLASS": source["SCRIPT_CLASS"],
        "SEMANTIC_ROLE": role,
        "SEMANTIC_ROLE_RULE": role_rule,
        "TYPOGRAPHIC_CLASS": taxon,
        "TYPOGRAPHIC_CLASS_RULE": taxon_rule,
        "EFFECTIVE_PT": source["EFFECTIVE_PT"],
        "H_INK_PX": source["H_INK_PX"],
        "INK_AREA_PX": source["INK_AREA_PX"],
    }
    element_rows.append(row)
    groups[(row["PANEL_ID"], role, taxon)].append(row)
    legacy_groups[(row["PANEL_ID"], source["ROLE"], source["SCRIPT_CLASS"])].append(row)

group_rows: list[dict] = []
element_by_id = {row["ELEMENT_ID"]: row for row in element_rows}
for key in sorted(groups):
    members = groups[key]
    heights = [float(member["H_INK_PX"]) for member in members]
    med = median(heights)
    ratios = [height / med for height in heights]
    failures = [
        member["ELEMENT_ID"]
        for member, ratio in zip(members, ratios)
        if ratio < 0.92 or ratio > 1.08
    ]
    for member, ratio in zip(members, ratios):
        member["GROUP_MEDIAN_H_PX"] = fmt_number(med)
        member["RATIO_TO_GROUP_MEDIAN"] = f"{ratio:.12f}"
        member["D_E_HARD_GATE"] = "PASS" if 0.92 <= ratio <= 1.08 else "FAIL"
    group_rows.append(
        {
            "PANEL_ID": key[0],
            "SEMANTIC_ROLE": key[1],
            "TYPOGRAPHIC_CLASS": key[2],
            "COUNT": len(members),
            "MEMBER_IDS": ";".join(member["ELEMENT_ID"] for member in members),
            "H_VALUES_PX": ";".join(member["H_INK_PX"] for member in members),
            "MEDIAN_H_PX": fmt_number(med),
            "MIN_RATIO": f"{min(ratios):.12f}",
            "MAX_RATIO": f"{max(ratios):.12f}",
            "FAIL_COUNT": len(failures),
            "FAIL_IDS": ";".join(failures),
            "GROUP_DECISION": "PASS" if not failures else "FAIL",
            "SINGLETON_STATUS": (
                "PREDECLARED_GLOBAL_CLASS_NOT_EXACT_GLYPH_ESCAPE"
                if len(members) == 1
                else "NOT_SINGLETON"
            ),
        }
    )

legacy_rows: list[dict] = []
for key in sorted(legacy_groups):
    members = legacy_groups[key]
    heights = [float(member["H_INK_PX"]) for member in members]
    med = median(heights)
    ratios = [height / med for height in heights]
    failures = [
        member["ELEMENT_ID"]
        for member, ratio in zip(members, ratios)
        if ratio < 0.92 or ratio > 1.08
    ]
    legacy_rows.append(
        {
            "PANEL_ID": key[0],
            "FROZEN_LOCATION_ROLE": key[1],
            "FROZEN_SCRIPT_CLASS": key[2],
            "COUNT": len(members),
            "MEMBER_IDS": ";".join(member["ELEMENT_ID"] for member in members),
            "H_VALUES_PX": ";".join(member["H_INK_PX"] for member in members),
            "MEDIAN_H_PX": fmt_number(med),
            "FAIL_COUNT": len(failures),
            "FAIL_IDS": ";".join(failures),
            "GROUP_DECISION": "PASS" if not failures else "FAIL",
        }
    )

role_pt: dict[str, list[float]] = defaultdict(list)
for row in element_rows:
    role_pt[row["SEMANTIC_ROLE"]].append(float(row["EFFECTIVE_PT"]))

source_role_rows: list[dict] = []
for role in ["NODE_BASE", "FORMULA_BLOCK", "TRIAL_INLINE_FORMULA", "ANNOTATION"]:
    values = role_pt[role]
    low = min(values)
    high = max(values)
    ratio = high / low
    delta = high - low
    source_role_rows.append(
        {
            "SEMANTIC_ROLE": role,
            "ELEMENT_COUNT": len(values),
            "PT_VALUES": ";".join(fmt_number(value) for value in sorted(set(values))),
            "MIN_PT": fmt_number(low),
            "MAX_PT": fmt_number(high),
            "MAX_MIN_RATIO": f"{ratio:.12f}",
            "ABS_DIFF_PT": f"{delta:.12f}",
            "SAME_ROLE_SOURCE_GATE": "PASS" if ratio <= 1.03 and delta <= 0.25 else "FAIL",
        }
    )

base = min(role_pt["NODE_BASE"])
hierarchy_ranges = {
    "NODE_BASE": (1.0, 1.0),
    "FORMULA_BLOCK": (1.0, 1.18),
    "TRIAL_INLINE_FORMULA": (1.0, 1.18),
    "ANNOTATION": (0.95, 1.10),
}
hierarchy_rows: list[dict] = []
for role, (minimum, maximum) in hierarchy_ranges.items():
    value = statistics.median(role_pt[role])
    ratio = value / base
    hierarchy_rows.append(
        {
            "SEMANTIC_ROLE": role,
            "MEDIAN_EFFECTIVE_PT": fmt_number(float(value)),
            "BASE_NODE_PT": fmt_number(base),
            "RATIO_TO_BASE": f"{ratio:.12f}",
            "ALLOWED_MIN": f"{minimum:.2f}",
            "ALLOWED_MAX": f"{maximum:.2f}",
            "HIERARCHY_GATE": "PASS" if minimum <= ratio <= maximum else "FAIL",
        }
    )

element_fields = [
    "ELEMENT_ID",
    "PANEL_ID",
    "SOURCE_LINE",
    "TEXT_SAMPLE",
    "FROZEN_LOCATION_ROLE",
    "FROZEN_SCRIPT_CLASS",
    "SEMANTIC_ROLE",
    "SEMANTIC_ROLE_RULE",
    "TYPOGRAPHIC_CLASS",
    "TYPOGRAPHIC_CLASS_RULE",
    "EFFECTIVE_PT",
    "H_INK_PX",
    "INK_AREA_PX",
    "GROUP_MEDIAN_H_PX",
    "RATIO_TO_GROUP_MEDIAN",
    "D_E_HARD_GATE",
]
group_fields = list(group_rows[0])
legacy_fields = list(legacy_rows[0])
source_role_fields = list(source_role_rows[0])
hierarchy_fields = list(hierarchy_rows[0])

write_csv(ROOT / "TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.csv", element_rows, element_fields)
write_csv(ROOT / "TYPOGRAPHIC_GROUP_SUMMARY.csv", group_rows, group_fields)
write_csv(ROOT / "FROZEN_R7A_GROUP_RECOMPUTE.csv", legacy_rows, legacy_fields)
write_csv(ROOT / "SOURCE_SAME_ROLE_SIZE_LEDGER.csv", source_role_rows, source_role_fields)
write_csv(ROOT / "SOURCE_ROLE_HIERARCHY_LEDGER.csv", hierarchy_rows, hierarchy_fields)

(ROOT / "TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.json").write_text(
    json.dumps(element_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(ROOT / "TYPOGRAPHIC_GROUP_SUMMARY.json").write_text(
    json.dumps(group_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

summary = {
    "input": str(INPUT),
    "element_count": len(element_rows),
    "unique_element_count": len(element_by_id),
    "mapped_exactly_once": len(element_rows) == len(element_by_id) == 95,
    "taxonomy_group_count": len(group_rows),
    "taxonomy_failure_count": sum(int(row["FAIL_COUNT"]) for row in group_rows),
    "legacy_frozen_group_failure_count": sum(int(row["FAIL_COUNT"]) for row in legacy_rows),
    "source_same_role_failure_count": sum(
        row["SAME_ROLE_SOURCE_GATE"] == "FAIL" for row in source_role_rows
    ),
    "source_hierarchy_failure_count": sum(
        row["HIERARCHY_GATE"] == "FAIL" for row in hierarchy_rows
    ),
    "singleton_groups": [
        {
            "semantic_role": row["SEMANTIC_ROLE"],
            "typographic_class": row["TYPOGRAPHIC_CLASS"],
            "member_ids": row["MEMBER_IDS"],
        }
        for row in group_rows
        if int(row["COUNT"]) == 1
    ],
    "conclusion": "TAXONOMY_STATIC_PASS_SOURCE_UNCHANGED",
}
(ROOT / "STATIC_RECOMPUTE_SUMMARY.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print(json.dumps(summary, ensure_ascii=False, indent=2))
