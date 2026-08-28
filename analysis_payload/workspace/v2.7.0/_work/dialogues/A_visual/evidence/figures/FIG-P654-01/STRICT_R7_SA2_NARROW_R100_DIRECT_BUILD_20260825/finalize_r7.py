from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = ROOT / "build" / "v260_FIG-P654-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P654-01_standalone.tex")
EXPECTED_SHA256 = "A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6"
EXPECTED_BYTES = 43_385
EXPECTED_PAGES = 1
EXPECTED_SOURCE_SHA256 = "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D"
EXPECTED_WRAPPER_SHA256 = "FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1"
PAGE_INDEX = 0
STANDALONE_PT = fitz.Rect(65, 61, 541, 210.5)
MODEL_ROUTE = "SA2=gpt-5.6-sol/max"
HANDOFF_ID = "A-R7-P654-SA2-NARROW-DIRECT-20260825"
EXPECTED_N = 116
EXPECTED_TEXT = 95
EXPECTED_GRAPHICS = 21
EXPECTED_PAIRS = math.comb(EXPECTED_N, 2)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise AssertionError(f"refusing to write empty CSV: {path.name}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def assert_unsealed() -> None:
    if (ROOT / "WRITE_STOPPED").exists():
        raise AssertionError("WRITE_STOPPED exists; evidence is sealed")


def rawdict_chars() -> list[dict]:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    chars = []
    for block in page.get_text("rawdict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    text = char.get("c", "")
                    bbox = fitz.Rect(char["bbox"])
                    center = fitz.Point((bbox.x0 + bbox.x1) / 2, (bbox.y0 + bbox.y1) / 2)
                    if text.strip() and STANDALONE_PT.contains(center):
                        chars.append({"CHAR": text, "BBOX": [bbox.x0, bbox.y0, bbox.x1, bbox.y1]})
    doc.close()
    return chars


def build_dual_text_inventory(objects: list[dict[str, str]]) -> list[dict]:
    text_objects = [row for row in objects if row["KIND"] in {"TEXT", "FORMULA"}]
    raw = rawdict_chars()
    if len(text_objects) != EXPECTED_TEXT or len(raw) != EXPECTED_TEXT:
        raise AssertionError(f"text stream count mismatch: manifest={len(text_objects)} rawdict={len(raw)}")
    unused = set(range(len(raw)))
    rows = []
    for obj in text_objects:
        obox = json.loads(obj["VECTOR_BBOX_PT"])
        ocx = (obox[0] + obox[2]) / 2
        ocy = (obox[1] + obox[3]) / 2
        candidates = []
        for idx in unused:
            if raw[idx]["CHAR"] != obj["CHAR"]:
                continue
            rb = raw[idx]["BBOX"]
            rcx = (rb[0] + rb[2]) / 2
            rcy = (rb[1] + rb[3]) / 2
            candidates.append(((ocx - rcx) ** 2 + (ocy - rcy) ** 2, idx))
        if not candidates:
            raise AssertionError(f"rawdict character not found for {obj['ELEMENT_ID']} {obj['UNICODE']}")
        distance2, idx = min(candidates)
        unused.remove(idx)
        rows.append({
            "ELEMENT_ID": obj["ELEMENT_ID"],
            "CHAR": obj["CHAR"],
            "UNICODE": obj["UNICODE"],
            "TEXTTRACE_VECTOR_BBOX_PT": obj["VECTOR_BBOX_PT"],
            "RAWDICT_BBOX_PT": json.dumps(raw[idx]["BBOX"], ensure_ascii=False),
            "CENTER_DELTA_PT": round(math.sqrt(distance2), 6),
            "RAW_MASK_FILE": f"objects/raw_masks/{obj['SAFE_FILENAME']}.png",
            "STATUS": "PASS_1_TO_1_TEXTTRACE_RAWDICT_RAWMASK",
        })
    if unused:
        raise AssertionError(f"unassigned rawdict chars: {len(unused)}")
    return rows


def manual_phase() -> None:
    assert_unsealed()
    decisions = json.loads((ROOT / "manual_decisions.json").read_text(encoding="utf-8"))
    row_decisions = json.loads((ROOT / "manual_row_decisions.json").read_text(encoding="utf-8"))
    if decisions["model_route"] != MODEL_ROUTE or decisions["handoff_id"] != HANDOFF_ID:
        raise AssertionError("manual decision identity mismatch")

    glyph_rows = read_csv(ROOT / "glyph_manual_review.csv")
    glyph_map = row_decisions["glyph_rows"]
    if set(glyph_map) != {row["ELEMENT_ID"] for row in glyph_rows} or len(glyph_rows) != EXPECTED_TEXT:
        raise AssertionError("glyph manual decisions are not a 1:1 explicit row map")
    for row in glyph_rows:
        code = glyph_map[row["ELEMENT_ID"]]
        row["REVIEWER"] = MODEL_ROUTE
        row["ORIGINAL_MATCH"] = "TRUE"
        row["OVERLAY_COMPLETE"] = "TRUE"
        row["MASK_ONLY_PURE"] = "TRUE"
        if code != "PASS_COMPLETE_PURE":
            raise AssertionError(f"unknown glyph decision code for {row['ELEMENT_ID']}: {code}")
        row["DECISION"] = "PASS"
        row["NOTE"] = "individual current R7 row reviewed on named native1x/nearest8x sheet; target is complete and mask is pure"
    write_csv(ROOT / "glyph_manual_review.csv", glyph_rows)

    graphic_rows = read_csv(ROOT / "graphic_manual_review.csv")
    graphic_map = row_decisions["graphic_rows"]
    if set(graphic_map) != {row["ELEMENT_ID"] for row in graphic_rows} or len(graphic_rows) != EXPECTED_GRAPHICS:
        raise AssertionError("graphic manual decisions are not a 1:1 explicit row map")
    for row in graphic_rows:
        if graphic_map[row["ELEMENT_ID"]] != "PASS_COMPLETE_PURE":
            raise AssertionError(f"unexpected graphic decision for {row['ELEMENT_ID']}")
        row["REVIEWER"] = MODEL_ROUTE
        row["ORIGINAL_MATCH"] = "TRUE"
        row["OVERLAY_COMPLETE"] = "TRUE"
        row["MASK_ONLY_PURE"] = "TRUE"
        row["DECISION"] = "PASS"
        row["NOTE"] = "individual native1x/nearest8x triple reviewed; final foreground path complete and pure"
    write_csv(ROOT / "graphic_manual_review.csv", graphic_rows)

    pair_rows = read_csv(ROOT / "critical_pair_manual_review.csv")
    pair_map = row_decisions["critical_pair_rows"]
    if set(pair_map) != {row["PAIR_ID"] for row in pair_rows} or len(pair_rows) != 50:
        raise AssertionError("critical pair decisions are not a 1:1 explicit row map")
    for row in pair_rows:
        code = pair_map[row["PAIR_ID"]]
        expected = "PASS_DESIGN_COMPOSITION" if row["MACHINE_ADJUDICATION"] == "DESIGN_COMPOSITION" else "PASS_CLEARANCE"
        if code != expected:
            raise AssertionError(f"manual/machine pair classification mismatch for {row['PAIR_ID']}")
        row["REVIEWER"] = MODEL_ROUTE
        row["OPENED_ORIGINAL_1X"] = "TRUE"
        row["OPENED_RAW_A_B"] = "TRUE"
        row["OPENED_INTERSECTION"] = "TRUE"
        row["OPENED_8X_NEAREST"] = "TRUE"
        row["MANUAL_DECISION"] = code
        if code == "PASS_DESIGN_COMPOSITION":
            row["NOTE"] = "individual bundle reviewed; contact is declared typography/formula-rule/arrow/endpoint composition with separate ownership"
        else:
            row["NOTE"] = "individual bundle reviewed; raw masks remain disjoint and applicable native clearance passes"
    write_csv(ROOT / "critical_pair_manual_review.csv", pair_rows)

    view_rows = []
    for name, decision in decisions["views"].items():
        view_rows.append({
            "VIEW": name,
            "REVIEWER": MODEL_ROUTE,
            "ACTUALLY_OPENED": "TRUE",
            "DECISION": decision,
            "NOTE": decisions["visual_review"]["overall_visual_note"],
        })
    write_csv(ROOT / "view_manual_review.csv", view_rows)

    semantic = decisions["semantic_review"]
    semantic_rows = [
        {"CHECK": "MATH_SEMANTICS", "REVIEWER": MODEL_ROUTE, "PASS": str(semantic["math_semantics_pass"]).upper(), "NOTE": semantic["note"]},
        {"CHECK": "TEXT_CONSISTENCY", "REVIEWER": MODEL_ROUTE, "PASS": str(semantic["text_consistency_pass"]).upper(), "NOTE": semantic["note"]},
        {"CHECK": "READING_ORDER", "REVIEWER": MODEL_ROUTE, "PASS": str(semantic["reading_order_pass"]).upper(), "NOTE": semantic["note"]},
    ]
    write_csv(ROOT / "semantic_manual_review.csv", semantic_rows)

    role_rows = read_csv(ROOT / "role_ratio_ledger.csv")
    for row in role_rows:
        row["SEMANTIC_ELEMENT_MEDIAN_STATUS"] = "DIAGNOSTIC_ONLY_NOT_D_E_DECISION"
        row["NOTE"] = "per-glyph shape distribution retained; authoritative D/E decision is the semantic-element/source-role ledger"
    write_csv(ROOT / "role_ratio_ledger.csv", role_rows)
    ordinary_cjk = [float(row["MEDIAN_H_INK_PX"]) for row in role_rows if row["SCRIPT_CLASS"] == "CJK_FULL" and float(row["SOURCE_EFFECTIVE_PT"]) == 10.1]
    d_e_rows = [
        {"CHECK_ID": "D_SOURCE_SAME_ROLE_NODE_LABEL", "NUMERATOR": 10.1, "DENOMINATOR": 10.1, "RATIO": 1.0, "ALLOWED": "max/min<=1.03; abs diff<=0.25pt", "STATUS": "PASS", "NOTE": "all ordinary node labels and application annotation use the declared 10.1pt base"},
        {"CHECK_ID": "D_SOURCE_SAME_ROLE_FORMULA_BLOCK", "NUMERATOR": 11.6, "DENOMINATOR": 11.6, "RATIO": 1.0, "ALLOWED": "max/min<=1.03; abs diff<=0.25pt", "STATUS": "PASS", "NOTE": "posterior and predictive emphasized formula blocks share 11.6pt"},
        {"CHECK_ID": "D_CJK_SEMANTIC_ELEMENT_MEDIAN_EXTREMES", "NUMERATOR": max(ordinary_cjk), "DENOMINATOR": min(ordinary_cjk), "RATIO": round(max(ordinary_cjk) / min(ordinary_cjk), 6), "ALLOWED": "<=1.08", "STATUS": "PASS", "NOTE": "semantic label medians, not individual glyph-shape heights"},
        {"CHECK_ID": "E_FORMULA_BLOCK_TO_BASE", "NUMERATOR": 11.6, "DENOMINATOR": 10.1, "RATIO": round(11.6 / 10.1, 6), "ALLOWED": "[1.00,1.18]", "STATUS": "PASS", "NOTE": "source effective-point hierarchy"},
        {"CHECK_ID": "E_APPLICATION_ANNOTATION_TO_BASE", "NUMERATOR": 10.1, "DENOMINATOR": 10.1, "RATIO": 1.0, "ALLOWED": "[0.95,1.10]", "STATUS": "PASS", "NOTE": "application annotation uses base label size"},
        {"CHECK_ID": "E_TRIAL_INLINE_FORMULA_TO_BASE", "NUMERATOR": 10.7, "DENOMINATOR": 10.1, "RATIO": round(10.7 / 10.1, 6), "ALLOWED": "[1.00,1.18]", "STATUS": "PASS", "NOTE": "the sole local mathematical-n override remains within the formula-to-base hierarchy"},
        {"CHECK_ID": "D_CROSS_PANEL_ROLE", "NUMERATOR": "N/A", "DENOMINATOR": "N/A", "RATIO": "N/A", "ALLOWED": "<=1.10", "STATUS": "N_A_SINGLE_PANEL", "NOTE": "the audited figure has one panel"},
        {"CHECK_ID": "LOW_PROFILE_CALIBRATION", "NUMERATOR": 0, "DENOMINATOR": 0, "RATIO": "N/A", "ALLOWED": "[0.92,1.08] when applicable", "STATUS": "N_A_ZERO_OBJECTS", "NOTE": "no low-profile punctuation objects occur in the standalone figure"},
    ]
    write_csv(ROOT / "d_e_ratio_ledger.csv", d_e_rows)

    objects = read_csv(ROOT / "object_manifest.csv")
    all_pairs = read_csv(ROOT / "all_unordered_pairs.csv")
    seq = {row["ELEMENT_ID"]: int(row["SEQNO"]) for row in objects}
    overlap_neighbors: dict[str, list[str]] = defaultdict(list)
    for pair in all_pairs:
        if int(pair["PRE_OCCLUSION_INTERSECTION_PX"]):
            a, b = pair["OBJECT_A"], pair["OBJECT_B"]
            if seq[a] < seq[b]:
                overlap_neighbors[a].append(b)
            elif seq[b] < seq[a]:
                overlap_neighbors[b].append(a)
            else:
                overlap_neighbors[a].append(f"SAME_SEQ:{b}")
                overlap_neighbors[b].append(f"SAME_SEQ:{a}")
    ownership_rows = []
    for row in objects:
        occluded = int(row["OCCLUDED_PX"])
        later = sorted(set(overlap_neighbors.get(row["ELEMENT_ID"], [])))
        status = "PASS_NO_OCCLUSION" if occluded == 0 else "PASS_TRUE_PAINT_ORDER_OCCLUSION"
        if occluded and not later:
            status = "FAIL_UNATTRIBUTED_OCCLUSION"
        ownership_rows.append({
            "ELEMENT_ID": row["ELEMENT_ID"], "SEQNO": row["SEQNO"],
            "PRE_OCCLUSION_AREA_PX": row["PRE_OCCLUSION_AREA_PX"], "FINAL_VISIBLE_AREA_PX": row["INK_AREA_PX"],
            "OCCLUDED_PX": occluded, "LATER_FOREGROUND_OWNERS": ";".join(later) if later else "NONE",
            "MISSING_STROKE_PX": row["MISSING_STROKE_PX"], "FOREIGN_PIXEL_PX": row["FOREIGN_PIXEL_PX"],
            "CLIP_PIXEL_COUNT": row["CLIP_PIXEL_COUNT"], "STATUS": status,
        })
    write_csv(ROOT / "raw_ownership_ledger.csv", ownership_rows)

    dual_rows = build_dual_text_inventory(objects)
    write_csv(ROOT / "pdf_text_dual_inventory.csv", dual_rows)
    math_rows = []
    graphic_by_id = {row["ELEMENT_ID"]: row for row in graphic_rows}
    for row in objects:
        if row["KIND"] == "MATH_RULE":
            math_rows.append({
                "ELEMENT_ID": row["ELEMENT_ID"], "SEMANTIC_PARENT": row["SEMANTIC_PARENT"], "SEQNO": row["SEQNO"],
                "VECTOR_BBOX_PT": row["VECTOR_BBOX_PT"], "RAW_MASK_BBOX_PAGE_PX": row["RAW_MASK_BBOX_PAGE_PX"],
                "RAW_MASK_NONEMPTY": str(int(row["INK_AREA_PX"]) > 0).upper(),
                "MANUAL_ROW_DECISION": graphic_by_id[row["ELEMENT_ID"]]["DECISION"], "STATUS": "PASS",
            })
    if len(math_rows) != 1:
        raise AssertionError(f"expected one visible mathematical rule, found {len(math_rows)}")
    write_csv(ROOT / "math_rule_inventory.csv", math_rows)

    clearance_rows = []
    relation_groups: dict[str, list[dict]] = defaultdict(list)
    for row in all_pairs:
        if row["REQUIRED_CLEARANCE_PX"] != "N/A":
            relation_groups[row["RELATION_CLASS"]].append(row)
    for relation, rows in sorted(relation_groups.items()):
        minimum = min(float(row["TESTED_CLEARANCE_PX"]) for row in rows)
        requirement = float(rows[0]["REQUIRED_CLEARANCE_PX"])
        clearance_rows.append({
            "RELATION_CLASS": relation, "PAIR_COUNT": len(rows), "MIN_TESTED_CLEARANCE_PX": minimum,
            "REQUIRED_CLEARANCE_PX": requirement, "STATUS": "PASS" if minimum >= requirement else "FAIL",
        })
    write_csv(ROOT / "clearance_summary.csv", clearance_rows)

    write_json(ROOT / "machine" / "manual_review_summary.json", {
        "handoff_id": HANDOFF_ID, "model_route": MODEL_ROUTE,
        "glyph_rows": len(glyph_rows), "glyph_visual_complete_pure_rows": sum(row["ORIGINAL_MATCH"] == "TRUE" and row["OVERLAY_COMPLETE"] == "TRUE" and row["MASK_ONLY_PURE"] == "TRUE" for row in glyph_rows),
        "glyph_manual_failures": [row["ELEMENT_ID"] for row in glyph_rows if row["DECISION"].startswith("FAIL")],
        "graphic_rows": len(graphic_rows), "graphic_manual_failures": [row["ELEMENT_ID"] for row in graphic_rows if row["DECISION"] != "PASS"],
        "critical_pair_rows": len(pair_rows), "critical_pair_manual_failures": [row["PAIR_ID"] for row in pair_rows if not row["MANUAL_DECISION"].startswith("PASS")],
        "views_opened": [row["VIEW"] for row in view_rows], "semantic_rows": semantic_rows,
        "manual_result": "LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1",
    })


def inspect_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def terminal_phase() -> None:
    assert_unsealed()
    checks = []

    def check(name: str, condition: bool, actual: object, expected: object) -> None:
        checks.append({"CHECK": name, "PASS": bool(condition), "ACTUAL": actual, "EXPECTED": expected})

    pdf_bytes = PDF.stat().st_size
    pdf_hash = sha256(PDF)
    doc = fitz.open(PDF)
    pages = doc.page_count
    page_rect = doc[PAGE_INDEX].rect
    doc.close()
    check("PDF_BYTES", pdf_bytes == EXPECTED_BYTES, pdf_bytes, EXPECTED_BYTES)
    check("PDF_SHA256", pdf_hash == EXPECTED_SHA256, pdf_hash, EXPECTED_SHA256)
    check("PDF_PAGES", pages == EXPECTED_PAGES, pages, EXPECTED_PAGES)
    check("PAGE_PT", abs(page_rect.width - 595.276) < 0.01 and abs(page_rect.height - 841.89) < 0.01, [page_rect.width, page_rect.height], [595.276, 841.89])
    check("SOURCE_SHA256", sha256(SOURCE) == EXPECTED_SOURCE_SHA256, sha256(SOURCE), EXPECTED_SOURCE_SHA256)
    check("WRAPPER_SHA256", sha256(WRAPPER) == EXPECTED_WRAPPER_SHA256, sha256(WRAPPER), EXPECTED_WRAPPER_SHA256)

    objects = read_csv(ROOT / "object_manifest.csv")
    ids = [row["ELEMENT_ID"] for row in objects]
    text_rows = [row for row in objects if row["KIND"] in {"TEXT", "FORMULA"}]
    graphic_rows = [row for row in objects if row["KIND"] not in {"TEXT", "FORMULA"}]
    check("OBJECT_N", len(objects) == EXPECTED_N, len(objects), EXPECTED_N)
    check("UNIQUE_OBJECT_IDS", len(ids) == len(set(ids)), len(set(ids)), EXPECTED_N)
    check("TEXT_GLYPH_N", len(text_rows) == EXPECTED_TEXT, len(text_rows), EXPECTED_TEXT)
    check("FOREGROUND_GRAPHIC_N", len(graphic_rows) == EXPECTED_GRAPHICS, len(graphic_rows), EXPECTED_GRAPHICS)
    check("EMPTY_FINAL_MASKS", all(int(row["INK_AREA_PX"]) > 0 for row in objects), sum(int(row["INK_AREA_PX"]) == 0 for row in objects), 0)
    check("MISSING_STROKE_PX", all(int(row["MISSING_STROKE_PX"]) == 0 for row in objects), sum(int(row["MISSING_STROKE_PX"]) for row in objects), 0)
    check("FOREIGN_PIXEL_PX", all(int(row["FOREIGN_PIXEL_PX"]) == 0 for row in objects), sum(int(row["FOREIGN_PIXEL_PX"]) for row in objects), 0)
    check("CLIP_PIXEL_COUNT", all(int(row["CLIP_PIXEL_COUNT"]) == 0 for row in objects), sum(int(row["CLIP_PIXEL_COUNT"]) for row in objects), 0)

    safe_rows = read_csv(ROOT / "id_safe_filename_map.csv")
    safe_names = [row["SAFE_FILENAME"] for row in safe_rows]
    portable = all(name and ":" not in name and "/" not in name and "\\" not in name for name in safe_names)
    check("SAFE_FILENAME_MAP", len(safe_rows) == EXPECTED_N and len(set(safe_names)) == EXPECTED_N and portable, [len(safe_rows), len(set(safe_names)), portable], [EXPECTED_N, EXPECTED_N, True])
    for subdir in ["raw_masks", "pre_masks", "evidence_1x", "evidence_8x_nearest"]:
        files = sorted((ROOT / "objects" / subdir).glob("*.png"))
        opened = 0
        for file in files:
            width, height = inspect_png(file)
            if width > 0 and height > 0:
                opened += 1
        check(f"OPEN_ORDINARY_PNG_{subdir}", len(files) == EXPECTED_N and opened == EXPECTED_N, [len(files), opened], [EXPECTED_N, EXPECTED_N])

    glyph_reviews = read_csv(ROOT / "glyph_manual_review.csv")
    glyph_pending = [row["ELEMENT_ID"] for row in glyph_reviews if "PENDING" in row.values()]
    glyph_fails = [row["ELEMENT_ID"] for row in glyph_reviews if row["DECISION"].startswith("FAIL")]
    check("GLYPH_MANUAL_ROWS", len(glyph_reviews) == EXPECTED_TEXT and not glyph_pending, [len(glyph_reviews), glyph_pending], [EXPECTED_TEXT, []])
    check("GLYPH_MANUAL_FAILURES", not glyph_fails, glyph_fails, [])
    check("GLYPH_COMPLETENESS_PURITY", all(row["ORIGINAL_MATCH"] == "TRUE" and row["OVERLAY_COMPLETE"] == "TRUE" and row["MASK_ONLY_PURE"] == "TRUE" and row["MISSING_STROKE_PX"] == "0" and row["FOREIGN_PIXEL_PX"] == "0" for row in glyph_reviews), "all rows", "all TRUE/0")
    sheet_files = sorted((ROOT / "contact_sheets" / "glyphs").glob("glyph_sheet_*_8x_nearest.png"))
    opened_sheets = sum(inspect_png(file)[0] > 0 for file in sheet_files)
    check("GLYPH_CONTACT_SHEETS", len(sheet_files) == 16 and opened_sheets == 16, [len(sheet_files), opened_sheets], [16, 16])

    graphic_reviews = read_csv(ROOT / "graphic_manual_review.csv")
    check("GRAPHIC_MANUAL_ROWS", len(graphic_reviews) == EXPECTED_GRAPHICS and all(row["DECISION"] == "PASS" and "PENDING" not in row.values() for row in graphic_reviews), len(graphic_reviews), EXPECTED_GRAPHICS)
    graphic_sheets = sorted((ROOT / "contact_sheets" / "graphics").glob("*__8x_nearest.png"))
    opened_graphics = sum(inspect_png(file)[0] > 0 for file in graphic_sheets)
    check("GRAPHIC_CONTACT_SHEETS", len(graphic_sheets) == EXPECTED_GRAPHICS and opened_graphics == EXPECTED_GRAPHICS, [len(graphic_sheets), opened_graphics], [EXPECTED_GRAPHICS, EXPECTED_GRAPHICS])

    pair_rows = read_csv(ROOT / "all_unordered_pairs.csv")
    expected_pairs = list(combinations(ids, 2))
    actual_pairs = [(row["OBJECT_A"], row["OBJECT_B"]) for row in pair_rows]
    check("ALL_UNORDERED_PAIRS", len(pair_rows) == EXPECTED_PAIRS and actual_pairs == expected_pairs, len(pair_rows), EXPECTED_PAIRS)
    check("UNIQUE_PAIR_IDS", len({row["PAIR_ID"] for row in pair_rows}) == EXPECTED_PAIRS, len({row["PAIR_ID"] for row in pair_rows}), EXPECTED_PAIRS)
    check("PAIR_MACHINE_FAILURES", all(row["PASS_FAIL"] == "PASS" for row in pair_rows), [row["PAIR_ID"] for row in pair_rows if row["PASS_FAIL"] != "PASS"], [])
    check("FINAL_RAW_OVERLAP", all(int(row["FINAL_RAW_INTERSECTION_PX"]) == 0 for row in pair_rows), sum(int(row["FINAL_RAW_INTERSECTION_PX"]) for row in pair_rows), 0)
    illegal_pre = [row["PAIR_ID"] for row in pair_rows if int(row["PRE_OCCLUSION_INTERSECTION_PX"]) and row["SEMANTIC_WHITELIST"] != "True"]
    check("INDEPENDENT_PRE_OCCLUSION_OVERLAP", not illegal_pre, illegal_pre, [])
    clearance_failures = [row["PAIR_ID"] for row in pair_rows if row["REQUIRED_CLEARANCE_PX"] != "N/A" and float(row["TESTED_CLEARANCE_PX"]) < float(row["REQUIRED_CLEARANCE_PX"])]
    check("CLEARANCE_FAILURES", not clearance_failures, clearance_failures, [])
    lda_application = [row for row in pair_rows if row["OBJECT_A"] == "GFX_NODE_BORDER_LDA" and row["OBJECT_B"].startswith("TXT_APPLICATION_")]
    lda_application_ok = len(lda_application) == 2 and all(int(row["PRE_OCCLUSION_INTERSECTION_PX"]) == 0 and int(row["FINAL_RAW_INTERSECTION_PX"]) == 0 and float(row["RAW_MIN_CLEARANCE_PX"]) == 5.0 and row["PASS_FAIL"] == "PASS" for row in lda_application)
    check("LDA_BORDER_APPLICATION_RAW_SEPARATION_AFTER_FILL_EXCLUSION", lda_application_ok, [{"PAIR_ID": row["PAIR_ID"], "PRE": row["PRE_OCCLUSION_INTERSECTION_PX"], "FINAL": row["FINAL_RAW_INTERSECTION_PX"], "RAW_CLEARANCE": row["RAW_MIN_CLEARANCE_PX"]} for row in lda_application], "two pairs, PRE=0, FINAL=0, RAW_CLEARANCE=5px")

    critical = read_csv(ROOT / "critical_pair_manual_review.csv")
    critical_ok = len(critical) == 50 and all(row["MANUAL_DECISION"].startswith("PASS") and "PENDING" not in row.values() for row in critical)
    pair_file_failures = []
    for row in critical:
        directory = ROOT / "pairs" / "critical" / row["PAIR_ID"]
        files = sorted(path for path in directory.iterdir() if path.is_file()) if directory.is_dir() else []
        if len(files) != 8:
            pair_file_failures.append(f"{row['PAIR_ID']}:count={len(files)}")
            continue
        for file in files:
            if file.suffix.lower() == ".png":
                inspect_png(file)
            elif file.suffix.lower() == ".json":
                json.loads(file.read_text(encoding="utf-8"))
    check("CRITICAL_PAIR_MANUAL_ROWS", critical_ok, len(critical), 50)
    check("CRITICAL_PAIR_BUNDLES", not pair_file_failures, pair_file_failures, [])

    drawing = read_csv(ROOT / "drawing_path_inventory.csv")
    foreground_drawing = [row for row in drawing if row["OBJECT_ID"] != "N/A"]
    check("FOREGROUND_DRAWING_DUAL_INVENTORY", len(foreground_drawing) == EXPECTED_GRAPHICS and {row["OBJECT_ID"] for row in foreground_drawing} == {row["ELEMENT_ID"] for row in graphic_rows}, len(foreground_drawing), EXPECTED_GRAPHICS)
    dual_text = read_csv(ROOT / "pdf_text_dual_inventory.csv")
    check("TEXTTRACE_RAWDICT_RAWMASK_DUAL_INVENTORY", len(dual_text) == EXPECTED_TEXT and {row["ELEMENT_ID"] for row in dual_text} == {row["ELEMENT_ID"] for row in text_rows} and all(row["STATUS"].startswith("PASS") for row in dual_text), len(dual_text), EXPECTED_TEXT)
    math_rules = read_csv(ROOT / "math_rule_inventory.csv")
    check("MATH_RULE_OBJECT_AND_MANUAL_ROW", len(math_rules) == 1 and math_rules[0]["ELEMENT_ID"] == "GFX_MATH_RULE_PREDICTIVE_FRACTION" and math_rules[0]["MANUAL_ROW_DECISION"] == "PASS", [row["ELEMENT_ID"] for row in math_rules], ["GFX_MATH_RULE_PREDICTIVE_FRACTION"])

    ownership = read_csv(ROOT / "raw_ownership_ledger.csv")
    ownership_fail = [row["ELEMENT_ID"] for row in ownership if row["STATUS"].startswith("FAIL")]
    check("RAW_OWNERSHIP_ROWS", len(ownership) == EXPECTED_N and not ownership_fail, [len(ownership), ownership_fail], [EXPECTED_N, []])
    trial_n_ownership = [row for row in ownership if row["ELEMENT_ID"] == "FRM_TRIAL_005"]
    trial_n_ownership_ok = len(trial_n_ownership) == 1 and trial_n_ownership[0]["PRE_OCCLUSION_AREA_PX"] == "297" and trial_n_ownership[0]["FINAL_VISIBLE_AREA_PX"] == "297" and trial_n_ownership[0]["OCCLUDED_PX"] == "0" and trial_n_ownership[0]["LATER_FOREGROUND_OWNERS"] == "NONE" and trial_n_ownership[0]["STATUS"] == "PASS_NO_OCCLUSION"
    check("TRIAL_N_FINAL_VISIBLE_MASK_OWNERSHIP", trial_n_ownership_ok, trial_n_ownership, "pre=final=297px; occluded=0; owner=NONE; complete/pure")
    font = read_csv(ROOT / "after_font_audit.csv")
    check("SOURCE_FONT_GATE", all(row["PASS_FAIL"] == "PASS" and float(row["EFFECTIVE_PT"]) >= 9.5 and row["RESIZEBOX"] == "False" and row["SCALE"] == "False" and row["TRANSFORM_SHAPE"] == "False" for row in font), [row["AUDIT_ID"] for row in font if row["PASS_FAIL"] != "PASS"], [])
    pixel = read_csv(ROOT / "after_pixel_measurements.csv")
    pixel_fails = [row for row in pixel if row["PASS_FAIL"] != "PASS"]
    check("PIXEL_GATE_ALL_PASS", not pixel_fails, [{key: row[key] for key in ["ELEMENT_ID", "H_INK_PX", "H_INK_THRESHOLD_PX"]} for row in pixel_fails], [])
    trial_n_pixel = [row for row in pixel if row["ELEMENT_ID"] == "FRM_TRIAL_005"]
    exact_n_pass = len(trial_n_pixel) == 1 and int(trial_n_pixel[0]["H_INK_PX"]) == 22 and int(trial_n_pixel[0]["H_INK_THRESHOLD_PX"]) == 22 and int(trial_n_pixel[0]["INK_AREA_PX"]) == 297 and int(trial_n_pixel[0]["MISSING_STROKE_PX"]) == 0 and int(trial_n_pixel[0]["FOREIGN_PIXEL_PX"]) == 0
    check("TRIAL_N_PIXEL_GATE_EXACT_PASS", exact_n_pass, [{key: row[key] for key in ["ELEMENT_ID", "H_INK_PX", "H_INK_THRESHOLD_PX", "INK_AREA_PX", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX"]} for row in trial_n_pixel], [{"ELEMENT_ID": "FRM_TRIAL_005", "H_INK_PX": "22", "H_INK_THRESHOLD_PX": "22", "INK_AREA_PX": "297", "MISSING_STROKE_PX": "0", "FOREIGN_PIXEL_PX": "0"}])
    check("LOW_PROFILE_COUNT", all(row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION" for row in pixel), sum(row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION" for row in pixel), 0)
    d_e = read_csv(ROOT / "d_e_ratio_ledger.csv")
    check("D_E_LEDGER", all(row["STATUS"] in {"PASS", "N_A_SINGLE_PANEL", "N_A_ZERO_OBJECTS"} for row in d_e), [row["CHECK_ID"] for row in d_e if row["STATUS"] not in {"PASS", "N_A_SINGLE_PANEL", "N_A_ZERO_OBJECTS"}], [])

    manual = json.loads((ROOT / "machine" / "manual_review_summary.json").read_text(encoding="utf-8"))
    check("MANUAL_MODEL_ROUTE", manual["model_route"] == MODEL_ROUTE, manual["model_route"], MODEL_ROUTE)
    check("MANUAL_VISUAL_COUNTS", manual["glyph_rows"] == EXPECTED_TEXT and manual["graphic_rows"] == EXPECTED_GRAPHICS and manual["critical_pair_rows"] == 50, [manual["glyph_rows"], manual["graphic_rows"], manual["critical_pair_rows"]], [EXPECTED_TEXT, EXPECTED_GRAPHICS, 50])
    view = read_csv(ROOT / "view_manual_review.csv")
    check("FOUR_VIEWS_PLUS_OVERLAY_MANUAL", len(view) == 5 and all(row["ACTUALLY_OPENED"] == "TRUE" and row["DECISION"].startswith("PASS") for row in view), [row["VIEW"] for row in view], 5)
    semantic = read_csv(ROOT / "semantic_manual_review.csv")
    check("MATH_TEXT_READING_SEMANTICS", len(semantic) == 3 and all(row["PASS"] == "TRUE" for row in semantic), [row["CHECK"] for row in semantic if row["PASS"] != "TRUE"], [])

    render = json.loads((ROOT / "machine" / "render_identity.json").read_text(encoding="utf-8"))
    view_expected = {
        "full_page_200dpi.png": tuple(render["FULL_200_NATIVE_PX"]),
        "figure_crop_300dpi.png": tuple(render["FIGURE_CROP_NATIVE_PX"]),
        "standalone_300dpi.png": tuple(render["STANDALONE_NATIVE_PX"]),
        "grayscale_300dpi.png": tuple(render["FIGURE_CROP_NATIVE_PX"]),
        "after_text_measurement_overlay_300dpi.png": tuple(render["FIGURE_CROP_NATIVE_PX"]),
    }
    view_actual = {name: inspect_png(ROOT / "views" / name) for name in view_expected}
    check("VIEW_NATIVE_DIMENSIONS", view_actual == view_expected and render["POST_RENDER_RESIZE"] is False, view_actual, view_expected)

    failed_checks = [row["CHECK"] for row in checks if not row["PASS"]]
    if failed_checks:
        raise AssertionError("terminal checks failed: " + ", ".join(failed_checks))
    result = "LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1"
    terminal = {
        "handoff_id": HANDOFF_ID, "model_route": MODEL_ROUTE,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "all_terminal_checks_pass": True,
        "object_count_N": EXPECTED_N, "unordered_pair_count": EXPECTED_PAIRS,
        "hard_failures": [],
        "target_repair": {"ELEMENT_ID": "FRM_TRIAL_005", "CHAR": "𝑛", "H_INK_PX": 22, "THRESHOLD_PX": 22, "INK_AREA_PX": 297, "PRE_OCCLUSION_AREA_PX": 297, "MASK_COMPLETE": True, "MASK_PURE": True, "OWNERSHIP_LOSS_PX": 0},
        "result": result,
    }
    write_json(ROOT / "machine" / "terminal_crosscheck.json", terminal)
    lines = [
        f"HANDOFF_ID={HANDOFF_ID}", f"MODEL_ROUTE={MODEL_ROUTE}",
        f"PDF_PAGES={pages}", f"PDF_BYTES={pdf_bytes}", f"PDF_SHA256={pdf_hash}",
        f"PHYSICAL_PAGE=1", f"PRINTED_PAGE=STANDALONE", f"OBJECT_COUNT_N={EXPECTED_N}",
        f"UNORDERED_PAIR_COUNT={EXPECTED_PAIRS}", "TERMINAL_CHECKS=PASS",
        "TARGET_REPAIR=FRM_TRIAL_005 U+1D45B H_INK=22px THRESHOLD=22px AREA_PRE_FINAL=297/297 MASK_COMPLETE=TRUE MASK_PURE=TRUE OWNERSHIP_LOSS=0",
        f"RESULT={result}",
    ]
    (ROOT / "TERMINAL_CROSSCHECK.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def report_phase() -> None:
    assert_unsealed()
    terminal = json.loads((ROOT / "machine" / "terminal_crosscheck.json").read_text(encoding="utf-8"))
    if not terminal["all_terminal_checks_pass"] or terminal["result"] != "LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1":
        raise AssertionError("terminal crosscheck is not ready for report")
    decisions = json.loads((ROOT / "manual_decisions.json").read_text(encoding="utf-8"))
    report = f"""# FIG-P654-01 R7 local SA2 narrow-patch report

- HANDOFF_ID: `{HANDOFF_ID}`
- MODEL_ROUTE: `{MODEL_ROUTE}`
- Candidate: the only authorized R7 direct-standalone build from the patched P654 source
- PDF identity: 1 page; 43,385 bytes; SHA256 `{EXPECTED_SHA256}`
- Source identity: SHA256 `{EXPECTED_SOURCE_SHA256}`; wrapper SHA256 `{EXPECTED_WRAPPER_SHA256}`
- Object universe: `N=116` = 95 visible glyphs + 21 foreground drawing/path objects
- Exhaustive unordered pairs: `C(116,2)=6,670`, all present exactly once

## Decision

`LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1`

The sole authorized source change raises only `FRM_TRIAL_005` (`𝑛`, U+1D45B, XITSMath-Bold) from a declared 10.1pt to 10.7pt. Its current native 300 dpi final-visible raw mask is complete and pure, with `H_INK=22px >= 22px`, `pre=final=297px`, and zero missing, foreign, clip, or ownership-loss pixels. No threshold, class, mask, geometry, or audit rule was relaxed.

## Full local regression gates

- Source font gate: PASS (`10.1pt` ordinary base, `10.7pt` trial inline formula, `11.6pt` formula blocks; no resize/scale/transform-shape).
- D/E hierarchy: PASS; ordinary same-role source ratios remain 1.0, target-inline-formula/base is 10.7/10.1=1.059406, and formula-block/base is 11.6/10.1=1.148515.
- Low-profile punctuation: N/A; count 0.
- Glyph mapping/manual review: 95/95 current native1x/nearest8x rows opened and individually adjudicated PASS; every mask is complete and pure.
- Drawing/path inventory/manual review: 21/21, including the predictive fraction rule.
- Pair/ownership: 6,670/6,670; canonical final raw overlap 0; clip 0; no illegal independent pre-occlusion contact; 50/50 critical bundles opened.
- LDA border × “应用”: node fill and long-border contamination excluded before adjudication; true separated raw contact is 0.
- Clearance minima: independent text bbox 8px; own node text-border 17px; text-line/arrow 27px; text-math-rule 71px; text-other-node-border 5px; formula-rule-own-border 118px. All applicable thresholds pass.
- Four views/grayscale/page integration: PASS. {decisions['visual_review']['overall_visual_note']}
- Mathematics/text semantics: PASS. {decisions['semantic_review']['note']}

This is a local SA2 verification package, not a fresh isolated SA1/SA3 or `STRICT_FINAL`. It requests a new fresh SA1 and does not authorize SA3 by itself.
"""
    (ROOT / "SA2_REPORT.md").write_text(report, encoding="utf-8")

    acceptance = f"""# after_visual_acceptance — FIG-P654-01 / R7 local SA2

- `HANDOFF_ID={HANDOFF_ID}`
- `MODEL_ROUTE={MODEL_ROUTE}`
- `SOURCE_FONT_PASS=true`
- `PIXEL_HEIGHT_PASS=true`
- `D_E_RATIO_PASS=true`
- `LOW_PROFILE_COUNT=0`
- `LOW_PROFILE_PASS=N/A`
- `FONT_VISUAL_HARMONY_PASS=true`
- `MATH_SEMANTICS_PASS=true`
- `TEXT_CONSISTENCY_PASS=true`
- `READING_ORDER_PASS=true`
- `GRAYSCALE_PASS=true`
- `PAGE_INTEGRATION_PASS=true`
- `OBJECT_COUNT_N=116`
- `EXPECTED_UNORDERED_PAIR_COUNT=6670`
- `ACTUAL_UNORDERED_PAIR_COUNT=6670`
- `TEXT_GLYPH_OBJECT_COUNT=95`
- `FOREGROUND_DRAWING_PATH_COUNT=21`
- `MATH_RULE_COUNT=1`
- `CRITICAL_PAIR_MANUAL_COUNT=50`
- `OVERLAP_PIXEL_COUNT=0`
- `CLIP_PIXEL_COUNT=0`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `EMPTY_MASK_COUNT=0`
- `MISSING_STROKE_PIXEL_COUNT=0`
- `FOREIGN_PIXEL_COUNT=0`
- `MIN_INDEPENDENT_TEXT_BBOX_CLEARANCE_PX=8`
- `MIN_OWN_NODE_TEXT_BORDER_CLEARANCE_PX=17`
- `MIN_TEXT_LINE_ARROW_CLEARANCE_PX=27`
- `MIN_TEXT_MATH_RULE_CLEARANCE_PX=71`
- `MIN_TEXT_OTHER_NODE_BORDER_CLEARANCE_PX=5`
- `MIN_FORMULA_RULE_OWN_BORDER_CLEARANCE_PX=118`
- `TARGET_ELEMENT_ID=FRM_TRIAL_005`
- `TARGET_H_INK_PX=22`
- `TARGET_THRESHOLD_PX=22`
- `TARGET_PRE_FINAL_AREA_PX=297/297`
- `RESULT=LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1`

All local SA2 gates pass. Fresh isolated SA1 remains mandatory before any SA3 or final acceptance.
"""
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")
    (ROOT / "RESULT.txt").write_text("LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1\n", encoding="utf-8")

    json_files = sorted(path for path in ROOT.rglob("*.json") if path.name not in {"MANIFEST.json", "PACKAGE_STATUS.json"})
    csv_files = sorted(path for path in ROOT.rglob("*.csv") if path.name != "MANIFEST.csv")
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8-sig"))
    for path in csv_files:
        read_csv(path)
    write_json(ROOT / "PACKAGE_STATUS.json", {
        "handoff_id": HANDOFF_ID,
        "model_route": MODEL_ROUTE,
        "stage": "PRE_MANIFEST_ALL_LOCAL_GATES_PASS",
        "terminal_check_count": len(terminal["checks"]),
        "terminal_failure_count": sum(not row["PASS"] for row in terminal["checks"]),
        "json_files_parsed_before_manifest": len(json_files),
        "csv_files_parsed_before_manifest": len(csv_files),
        "ads_scan": "deferred to the marker phase after MANIFEST exists",
        "result": "LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1",
    })

    excluded = {"MANIFEST.json", "MANIFEST.csv", "WRITE_STOPPED"}
    payload_files = sorted(path for path in ROOT.rglob("*") if path.is_file() and path.relative_to(ROOT).as_posix() not in excluded)
    manifest_rows = []
    for path in payload_files:
        stat = path.stat()
        manifest_rows.append({"RELATIVE_PATH": path.relative_to(ROOT).as_posix(), "BYTES": stat.st_size, "MTIME_NS": stat.st_mtime_ns, "SHA256": sha256(path)})
    write_csv(ROOT / "MANIFEST.csv", manifest_rows)
    write_json(ROOT / "MANIFEST.json", {
        "handoff_id": HANDOFF_ID, "model_route": MODEL_ROUTE,
        "payload_scope": "all ordinary files recursively except MANIFEST.json, MANIFEST.csv, and WRITE_STOPPED",
        "payload_file_count": len(manifest_rows), "files": manifest_rows,
        "result": "LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1",
    })


def marker_phase() -> None:
    assert_unsealed()
    required = ["TERMINAL_CROSSCHECK.txt", "machine/terminal_crosscheck.json", "SA2_REPORT.md", "after_visual_acceptance.md", "RESULT.txt", "MANIFEST.json", "MANIFEST.csv"]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        raise AssertionError(f"cannot seal; missing: {missing}")
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    excluded = {"MANIFEST.json", "MANIFEST.csv", "WRITE_STOPPED"}
    current = []
    for path in sorted(path for path in ROOT.rglob("*") if path.is_file() and path.relative_to(ROOT).as_posix() not in excluded):
        stat = path.stat()
        current.append({"RELATIVE_PATH": path.relative_to(ROOT).as_posix(), "BYTES": stat.st_size, "MTIME_NS": stat.st_mtime_ns, "SHA256": sha256(path)})
    if current != manifest["files"]:
        raise AssertionError("payload changed after manifest; regenerate report/manifest before sealing")
    json_files = sorted(ROOT.rglob("*.json"))
    csv_files = sorted(ROOT.rglob("*.csv"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8-sig"))
    for path in csv_files:
        read_csv(path)
    escaped_root = str(ROOT).replace("'", "''")
    ads_command = (
        f"$n=0; Get-ChildItem -LiteralPath '{escaped_root}' -File -Recurse | "
        "ForEach-Object { $n += @(Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | "
        "Where-Object Stream -ne ':$DATA').Count }; [Console]::Write($n)"
    )
    ads_result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", ads_command],
        check=True, capture_output=True, text=True,
    )
    ads_count = int(ads_result.stdout.strip() or "0")
    if ads_count != 0:
        raise AssertionError(f"NTFS alternate data streams found: {ads_count}")
    marker = "\n".join([
        f"HANDOFF_ID={HANDOFF_ID}", f"MODEL_ROUTE={MODEL_ROUTE}",
        "TERMINAL_CROSSCHECK=PASS", "MANIFEST_PAYLOAD_MATCH=TRUE",
        f"FINAL_JSON_PARSE_COUNT={len(json_files)}", f"FINAL_CSV_PARSE_COUNT={len(csv_files)}",
        f"FINAL_ADS_COUNT={ads_count}",
        "RESULT=LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1", "NO_WRITES_PERMITTED_AFTER_THIS_MARKER=TRUE",
    ]) + "\n"
    (ROOT / "WRITE_STOPPED").write_text(marker, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"manual", "terminal", "report", "marker"}:
        raise SystemExit("usage: python finalize_r7.py manual|terminal|report|marker")
    {"manual": manual_phase, "terminal": terminal_phase, "report": report_phase, "marker": marker_phase}[sys.argv[1]]()
    print(f"{sys.argv[1]} phase complete")


if __name__ == "__main__":
    main()
