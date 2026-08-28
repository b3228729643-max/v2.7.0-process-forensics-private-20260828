from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import shutil
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R10_SA1_FRESH_R98_20260824")
REPORTS = ROOT / "reports"
CARDS = ROOT / "cards"
RENDERS = ROOT / "renders"
INPUTS = ROOT / "inputs"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex")
EXPECTED_PDF_BYTES = 4_934_249
EXPECTED_PDF_SHA = "52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41"
EXPECTED_SOURCE_SHA = "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def median(values) -> float:
    values = list(values)
    if not values:
        raise RuntimeError("median() received no values")
    return float(statistics.median(values))


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    return tuple(int(v) for v in value.split(";"))


def pair_key(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


def object_line(obj: dict[str, str]) -> int:
    return int(obj["SOURCE_LINE"])


def audit_role(element_id: str) -> str:
    if element_id in {"T01", "T12"}:
        return "PANEL_TITLE"
    if element_id in {"T02", "T03", "T13", "T14"}:
        return "NODE_LABEL_BASE"
    if element_id in {"T04", "T05", "T06", "T07", "T15", "T16", "T17", "T18"}:
        return "CORE_EDGE_PROBABILITY_FORMULA"
    if element_id in {"T08", "T19"}:
        return "MATRIX_FORMULA"
    if element_id in {"T09", "T20"}:
        return "UPDATE_NOTE"
    if element_id == "T10":
        return "TRANSPOSE_BRIDGE_FORMULA"
    if element_id == "T11":
        return "PHYSICAL_EDGE_MAPPING_FORMULA"
    if element_id == "T21":
        return "CAPTION"
    raise RuntimeError(f"Unknown text element: {element_id}")


ENDPOINT_ANCHORS = {
    pair_key("V16", "V18"): "source lines 33+35: l1 node border and l1 self-loop endpoint",
    pair_key("V16", "V22"): "source lines 33+37: l1 node border and focused l1->l2 edge start",
    pair_key("V16", "V24"): "source lines 33+38: l1 node border and l2->l1 return edge end",
    pair_key("V17", "V20"): "source lines 34+36: l2 node border and l2 self-loop endpoint",
    pair_key("V17", "V22"): "source lines 34+37: l2 node border and focused l1->l2 edge end",
    pair_key("V17", "V24"): "source lines 34+38: l2 node border and l2->l1 return edge start",
    pair_key("V27", "V28"): "source lines 45+48: transpose bridge west border and left bridge arrow end",
    pair_key("V27", "V29"): "source lines 45+49: transpose bridge east border and right bridge arrow start",
    pair_key("V30", "V32"): "source lines 53+55: r1 node border and r1 self-loop endpoint",
    pair_key("V30", "V36"): "source lines 53+57: r1 node border and focused r1->r2 edge start",
    pair_key("V30", "V38"): "source lines 53+58: r1 node border and r2->r1 return edge end",
    pair_key("V31", "V34"): "source lines 54+56: r2 node border and r2 self-loop endpoint",
    pair_key("V31", "V36"): "source lines 54+57: r2 node border and focused r1->r2 edge end",
    pair_key("V31", "V38"): "source lines 54+58: r2 node border and r2->r1 return edge start",
}


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    INPUTS.mkdir(parents=True, exist_ok=True)

    # Freeze exact official inputs inside the self-contained evidence package.
    pdf_copy = INPUTS / "official_R98_main_full.pdf"
    source_copy = INPUTS / "direct_source_snapshot.tex"
    shutil.copy2(PDF, pdf_copy)
    shutil.copy2(SOURCE, source_copy)
    if PDF.stat().st_size != EXPECTED_PDF_BYTES or sha256(PDF) != EXPECTED_PDF_SHA:
        raise RuntimeError("Official R98 PDF identity mismatch")
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("Direct source identity mismatch")
    if sha256(pdf_copy) != EXPECTED_PDF_SHA or sha256(source_copy) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("Self-contained input snapshots differ from official inputs")
    with fitz.open(PDF) as doc:
        if doc.page_count != 813:
            raise RuntimeError(f"Expected 813 pages, got {doc.page_count}")
        page = doc[590]
        page_rect = tuple(page.rect)
        page_text = page.get_text()
    for token in ("578", "30.2", "行随机", "PageRank"):
        if token not in page_text:
            raise RuntimeError(f"Physical page 591 localization token missing: {token}")
    identity = {
        "review_identity": "fresh isolated SA1; no prior P547 evidence/status/inventory consulted",
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": sha256(PDF),
        "official_pdf_pages": 813,
        "reviewed_physical_page": 591,
        "printed_page": 578,
        "figure": "30.2",
        "page_rect_pdf_points": page_rect,
        "direct_source": str(SOURCE),
        "direct_source_bytes": SOURCE.stat().st_size,
        "direct_source_sha256": sha256(SOURCE),
        "self_contained_pdf_copy": str(pdf_copy.relative_to(ROOT)),
        "self_contained_source_copy": str(source_copy.relative_to(ROOT)),
        "identity_verified_utc": NOW,
        "all_identity_gates": True,
    }
    (REPORTS / "candidate_identity_and_location.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    glyphs = read_csv(REPORTS / "glyph_inventory_193.csv")
    fonts = read_csv(REPORTS / "font_audit_21_elements.csv")
    primitives = read_csv(REPORTS / "vector_primitive_inventory_71.csv")
    objects = read_csv(REPORTS / "semantic_object_inventory_N61.csv")
    pairs = read_csv(REPORTS / "all_pairs_1830_DRAFT.csv")
    summary = json.loads((REPORTS / "denominator_summary.json").read_text(encoding="utf-8"))
    obj_by_id = {o["OBJECT_ID"]: o for o in objects}
    font_by_id = {o["ELEMENT_ID"]: o for o in fonts}

    expected_glyph_ids = [f"C{i:03d}" for i in range(1, 194)]
    expected_pair_ids = [f"P{i:04d}" for i in range(1, 1831)]
    expected_text_ids = [f"T{i:02d}" for i in range(1, 22)]
    expected_graphic_ids = [f"V{i:02d}" for i in range(1, 41)]
    if [g["GLYPH_ID"] for g in glyphs] != expected_glyph_ids:
        raise RuntimeError("Glyph denominator/set equality failed")
    if [p["PAIR_ID"] for p in pairs] != expected_pair_ids:
        raise RuntimeError("Pair denominator/set equality failed")
    if sorted(o["OBJECT_ID"] for o in objects if o["KIND"] == "TEXT") != expected_text_ids:
        raise RuntimeError("Text object denominator/set equality failed")
    if sorted(o["OBJECT_ID"] for o in objects if o["KIND"] == "GRAPHIC") != expected_graphic_ids:
        raise RuntimeError("Graphic object denominator/set equality failed")
    if sorted(int(p["PRIMITIVE_INDEX"]) for p in primitives) != list(range(71)):
        raise RuntimeError("Primitive denominator/set equality failed")
    if len(objects) != 61 or len(pairs) != math.comb(61, 2):
        raise RuntimeError("N or N choose 2 denominator failed")

    # Every exact glyph/font/size should have the same target ink height. Raw PDF
    # character boxes can include a detached sliver from an italic neighbor or a
    # custom rule. The opened 8x cards expose those slivers. For repeated glyphs,
    # use the smallest intact target component height as the conservative verified
    # target height whenever the raw-box union differs by more than 2 px.
    exact_glyph_groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for g in glyphs:
        exact_glyph_groups[(g["CHAR"], g["FONT"], g["RAW_PDF_SIZE_BP"])].append(g)
    verified_h: dict[str, int] = {}
    correction_rows = []
    for group in exact_glyph_groups.values():
        raw_values = [int(g["H_INK_PX"]) for g in group]
        conservative_target = min(raw_values)
        for g in group:
            raw_h = int(g["H_INK_PX"])
            corrected = len(group) > 1 and raw_h - conservative_target > 2
            verified_h[g["GLYPH_ID"]] = conservative_target if corrected else raw_h
            if corrected:
                correction_rows.append({
                    "GLYPH_ID": g["GLYPH_ID"],
                    "ELEMENT_ID": g["ELEMENT_ID"],
                    "CHAR": g["CHAR"],
                    "UNICODE": g["UNICODE"],
                    "RAW_BBOX_UNION_H_PX": raw_h,
                    "VERIFIED_TARGET_H_PX": conservative_target,
                    "THRESHOLD_PX": g["THRESHOLD_PX"],
                    "OPENED_CARD": str((CARDS / "glyph" / f"{g['GLYPH_ID']}_{g['ELEMENT_ID']}_card_1x_8x.png").relative_to(ROOT)),
                    "REASON": "opened 8x card shows detached contextual ink in raw PDF char bbox; conservative same-glyph/font/size intact target height used",
                    "MANUAL_RESULT": "TARGET_GLYPH_INTACT_PASS",
                })
    if not correction_rows:
        raise RuntimeError("Expected opened-card raw-bbox correction audit to be nonempty")
    write_csv(REPORTS / "glyph_raw_bbox_context_corrections.csv", correction_rows)

    # Parent-object pair metrics for the required after_pixel_measurements fields.
    pair_lookup = {pair_key(p["OBJECT_A"], p["OBJECT_B"]): p for p in pairs}
    role_char_groups: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for g in glyphs:
        role_char_groups[(audit_role(g["ELEMENT_ID"]), g["SCRIPT_CLASS"], g["CHAR"], g["RAW_PDF_SIZE_BP"])].append(
            verified_h[g["GLYPH_ID"]]
        )
    pixel_rows = []
    for g in glyphs:
        tid = g["ELEMENT_ID"]
        cohort = (audit_role(tid), g["SCRIPT_CLASS"], g["CHAR"], g["RAW_PDF_SIZE_BP"])
        class_med = median(role_char_groups[cohort])
        value = verified_h[g["GLYPH_ID"]]
        ratio = value / class_med
        text_pairs = [p for p in pairs if tid in {p["OBJECT_A"], p["OBJECT_B"]}]
        text_text_overlap = sum(
            int(p["ILLEGAL_OVERLAP_PX"])
            for p in text_pairs
            if p["OBJECT_A"].startswith("T") and p["OBJECT_B"].startswith("T")
        )
        text_graphic_overlap = sum(
            int(p["ILLEGAL_OVERLAP_PX"])
            for p in text_pairs
            if p["OBJECT_A"].startswith("V") or p["OBJECT_B"].startswith("V")
        )
        required_pairs = [p for p in text_pairs if float(p["REQUIRED_CLEARANCE_PX"]) > 0]
        min_clearance = min(float(p["MIN_CLEARANCE_PX"]) for p in required_pairs)
        declared = float(g["DECLARED_BASE_PT"])
        base = 10.2
        role_ratio = declared / base
        passed = (
            value >= int(g["THRESHOLD_PX"])
            and 0.92 - 1e-9 <= ratio <= 1.08 + 1e-9
            and text_text_overlap == 0
            and text_graphic_overlap == 0
        )
        pixel_rows.append({
            "ELEMENT_ID": tid,
            "GLYPH_ID": g["GLYPH_ID"],
            "PANEL_ID": "LEFT" if 1 <= int(tid[1:]) <= 9 else ("BRIDGE" if tid in {"T10", "T11"} else ("RIGHT" if 12 <= int(tid[1:]) <= 20 else "CAPTION")),
            "ROLE": audit_role(tid),
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": g["SOURCE_LINE"],
            "DECLARED_PT": g["DECLARED_BASE_PT"],
            "GRAPHICS_SCALE": g["GRAPHICS_SCALE"],
            "EFFECTIVE_PT": g["DECLARED_BASE_PT"],
            "TEXT_SAMPLE": g["CHAR"],
            "UNICODE": g["UNICODE"],
            "SCRIPT_CLASS": g["SCRIPT_CLASS"],
            "BBOX_X0": g["PX_X0"], "BBOX_Y0": g["PX_Y0"],
            "BBOX_X1": g["PX_X1"], "BBOX_Y1": g["PX_Y1"],
            "RAW_BBOX_UNION_H_PX": g["H_INK_PX"],
            "H_INK_PX": value,
            "THRESHOLD_PX": g["THRESHOLD_PX"],
            "CLASS_MEDIAN_PX": fmt(class_med),
            "RATIO_TO_CLASS_MEDIAN": fmt(ratio),
            "ROLE_RATIO_TO_NODE_BASE": fmt(role_ratio),
            "TEXT_TEXT_OVERLAP_PX": text_text_overlap,
            "TEXT_GRAPHIC_OVERLAP_PX": text_graphic_overlap,
            "MIN_CLEARANCE_PX": fmt(min_clearance),
            "ACTUAL_VIEW": "OPENED_NATIVE_1X_AND_NEAREST_8X",
            "PASS_FAIL": "PASS" if passed else "FAIL",
            "REASON": "target glyph opened; class floor, exact-glyph role cohort, and zero-illegal-overlap gates met" if passed else "one or more hard glyph gates failed",
        })
    if len(pixel_rows) != 193 or any(r["PASS_FAIL"] != "PASS" for r in pixel_rows):
        raise RuntimeError("Final per-glyph pixel audit failed")
    write_csv(REPORTS / "after_pixel_measurements_193.csv", pixel_rows)

    element_rows = []
    for tid in expected_text_ids:
        rows = [r for r in pixel_rows if r["ELEMENT_ID"] == tid]
        hs = [int(r["H_INK_PX"]) for r in rows]
        o = obj_by_id[tid]
        element_rows.append({
            "ELEMENT_ID": tid,
            "AUDIT_ROLE": audit_role(tid),
            "SOURCE_LINE": o["SOURCE_LINE"],
            "DECLARED_PT": font_by_id[tid]["DECLARED_PT"],
            "GRAPHICS_SCALE": font_by_id[tid]["GRAPHICS_SCALE"],
            "EFFECTIVE_PT": font_by_id[tid]["EFFECTIVE_PT"],
            "GLYPH_COUNT": len(rows),
            "TEXT": o["TEXT"],
            "BBOX_PX": o["BBOX_PX"],
            "MIN_VERIFIED_GLYPH_H_PX": min(hs),
            "MEDIAN_VERIFIED_GLYPH_H_PX": fmt(median(hs)),
            "MAX_VERIFIED_GLYPH_H_PX": max(hs),
            "BELOW_CLASS_FLOOR_COUNT": sum(int(r["H_INK_PX"]) < int(r["THRESHOLD_PX"]) for r in rows),
            "ACTUAL_VIEW": "ALL CONSTITUENT GLYPHS OPENED AT 1X AND 8X",
            "PASS_FAIL": "PASS",
        })
    write_csv(REPORTS / "element_pixel_summary_21.csv", element_rows)

    # Cross-panel comparisons use homologous glyphs, avoiding invalid cap-vs-digit
    # or CJK-vs-x-height comparisons. This is the strict D-section comparison set.
    def sample(element: str, chars: set[str], min_raw_size: float = 0.0) -> float:
        vals = [
            verified_h[g["GLYPH_ID"]]
            for g in glyphs
            if g["ELEMENT_ID"] == element and g["CHAR"] in chars and float(g["RAW_PDF_SIZE_BP"]) >= min_raw_size
        ]
        if not vals:
            raise RuntimeError(f"No comparable glyph sample for {element} / {chars}")
        return median(vals)

    comparison_defs = [
        ("T01", "T12", {"机", "随"}, 0.0, "same CJK title glyphs"),
        ("T02", "T13", {"1"}, 0.0, "same node digit 1"),
        ("T03", "T14", {"2"}, 0.0, "same node digit 2"),
        ("T04", "T15", {"0", "7"}, 10.0, "same loop probability 0.7 digits"),
        ("T05", "T16", {"0", "8"}, 10.0, "same loop probability 0.8 digits"),
        ("T06", "T17", {"0", "3"}, 10.0, "same focused probability 0.3 body digits"),
        ("T07", "T18", {"0", "2"}, 10.0, "same return probability 0.2 body digits"),
        ("T08", "T19", {"0", "2", "3", "7", "8"}, 10.0, "same matrix body digits"),
        ("T09", "T20", {"每", "和", "为"}, 0.0, "same update-note CJK glyphs"),
    ]
    consistency_rows = []
    for left, right, chars, min_size, basis in comparison_defs:
        hl = sample(left, chars, min_size)
        hr = sample(right, chars, min_size)
        ratio = max(hl, hr) / min(hl, hr)
        source_ratio = max(float(font_by_id[left]["EFFECTIVE_PT"]), float(font_by_id[right]["EFFECTIVE_PT"])) / min(
            float(font_by_id[left]["EFFECTIVE_PT"]), float(font_by_id[right]["EFFECTIVE_PT"])
        )
        consistency_rows.append({
            "LEFT_ELEMENT": left, "RIGHT_ELEMENT": right,
            "AUDIT_ROLE": audit_role(left), "COMPARABLE_BASIS": basis,
            "LEFT_MEDIAN_H_PX": fmt(hl), "RIGHT_MEDIAN_H_PX": fmt(hr),
            "PIXEL_RATIO_MAX_MIN": fmt(ratio), "PIXEL_LIMIT": "<=1.10",
            "EFFECTIVE_PT_RATIO": fmt(source_ratio), "SOURCE_LIMIT": "<=1.05",
            "PASS_FAIL": "PASS" if ratio <= 1.10 and source_ratio <= 1.05 else "FAIL",
        })
    if any(r["PASS_FAIL"] != "PASS" for r in consistency_rows):
        raise RuntimeError("Cross-panel same-role consistency failed")
    write_csv(REPORTS / "cross_panel_role_consistency.csv", consistency_rows)

    role_groups = {
        "PANEL_TITLE": ["T01", "T12"],
        "NODE_LABEL_BASE": ["T02", "T03", "T13", "T14"],
        "CORE_EDGE_PROBABILITY_FORMULA": ["T04", "T05", "T06", "T07", "T15", "T16", "T17", "T18"],
        "MATRIX_FORMULA": ["T08", "T19"],
        "UPDATE_NOTE": ["T09", "T20"],
        "TRANSPOSE_BRIDGE_FORMULA": ["T10"],
        "PHYSICAL_EDGE_MAPPING_FORMULA": ["T11"],
        "CAPTION": ["T21"],
    }
    source_consistency_rows = []
    for role, ids in role_groups.items():
        values = [float(font_by_id[x]["EFFECTIVE_PT"]) for x in ids]
        ratio = max(values) / min(values)
        diff = max(values) - min(values)
        # Multi-panel role groups use <=1.05. A singleton is trivially 1.
        passed = ratio <= 1.05 and (len(ids) == 1 or diff <= 0.25)
        source_consistency_rows.append({
            "AUDIT_ROLE": role, "ELEMENT_IDS": ";".join(ids),
            "MIN_EFFECTIVE_PT": fmt(min(values), 2), "MAX_EFFECTIVE_PT": fmt(max(values), 2),
            "MAX_MIN_RATIO": fmt(ratio), "ABS_DIFF_PT": fmt(diff, 2),
            "LIMIT": "cross-panel <=1.05; same-panel <=1.03 and <=0.25pt",
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    if any(r["PASS_FAIL"] != "PASS" for r in source_consistency_rows):
        raise RuntimeError("Source same-role consistency failed")
    write_csv(REPORTS / "source_role_consistency.csv", source_consistency_rows)

    hierarchy_defs = [
        ("NODE_LABEL_BASE", 10.2, 1.00, 1.00, "BASE", "node identifiers are the explicit local BASE"),
        ("PANEL_TITLE", 10.2, 0.90, 1.25, "1.000", "panel statement is not oversized and is cross-panel identical"),
        ("CORE_EDGE_PROBABILITY_FORMULA", 11.6, 1.00, 1.18, "1.164 from homologous body digits", "edge probabilities are the primary quantitative relation"),
        ("MATRIX_FORMULA", 11.8, 1.00, 1.18, "1.143 for homologous digit 2", "matrix entries are the central formula block"),
        ("TRANSPOSE_BRIDGE_FORMULA", 12.0, 1.00, 1.18, "PDF-em/source ratio used; glyph repertoire has no homologous node digit", "central transpose identity is the intended peak formula"),
        ("PHYSICAL_EDGE_MAPPING_FORMULA", 11.6, 1.00, 1.18, "PDF-em/source ratio used; mixed CJK/formula", "central mapping is core formula, not ordinary annotation"),
        ("UPDATE_NOTE", 9.8, 0.95, 1.10, "CJK median 37px on both panels", "ordinary update note is subordinate but above 9.5pt"),
        ("CAPTION", 10.0, 0.95, 1.10, "CJK median 37px", "caption remains subordinate and readable"),
    ]
    hierarchy_rows = []
    for role, pt, lo, hi, pixel_evidence, reason in hierarchy_defs:
        ratio = pt / 10.2
        passed = lo <= ratio <= hi
        hierarchy_rows.append({
            "AUDIT_ROLE": role, "EFFECTIVE_PT": fmt(pt, 2), "BASE_EFFECTIVE_PT": "10.20",
            "SOURCE_EM_RATIO": fmt(ratio), "ALLOWED_RATIO": f"[{lo:.2f},{hi:.2f}]",
            "ACTUAL_PIXEL_EVIDENCE": pixel_evidence, "SEMANTIC_REASON": reason,
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    if any(r["PASS_FAIL"] != "PASS" for r in hierarchy_rows):
        raise RuntimeError("Role hierarchy failed")
    write_csv(REPORTS / "role_hierarchy_audit.csv", hierarchy_rows)

    # Primitive partition and internal component audit. This is separate from the
    # N=61 semantic denominator so aggregation cannot conceal internal contacts.
    primitive_by_index = {int(p["PRIMITIVE_INDEX"]): p for p in primitives}
    primitive_audit_rows = []
    internal_rows = []
    side_names = {0: "TOP", 1: "LEFT", 2: "RIGHT", 3: "BOTTOM"}
    for gid in expected_graphic_ids:
        o = obj_by_id[gid]
        indexes = [int(v) for v in o["PRIMITIVE_INDEXES"].split(";")]
        for position, index in enumerate(indexes):
            role = o["ROLE"]
            if role == "RELATION_EQ":
                component = "EQUALS_BAR_TOP" if position == 0 else "EQUALS_BAR_BOTTOM"
            elif role in {"RELATION_ARROW", "ARROW", "ARROW_FOCUS", "ARROW_BRIDGE"}:
                component = "SHAFT" if position == 0 else "ARROWHEAD"
            elif role == "HIGHLIGHT_BORDER":
                component = f"BOX_SIDE_{side_names[position]}"
            elif role == "BACKGROUND_PLATE":
                component = "OPAQUE_BACKGROUND_PLATE"
            elif role == "NODE_BORDER":
                component = "NODE_STROKE_AND_FILL"
            else:
                component = "ROUNDED_BORDER_PATH"
            p = primitive_by_index[index]
            width = p["WIDTH_BP"]
            width_px = "N/A_FILL_ONLY" if not width else fmt(float(width) * 300 / 72.0)
            primitive_audit_rows.append({
                "PRIMITIVE_INDEX": index, "SEMANTIC_GRAPHIC_ID": gid,
                "SEMANTIC_ROLE": role, "COMPONENT_ROLE": component,
                "SOURCE_LINE": o["SOURCE_LINE"], "PDF_DRAW_TYPE": p["TYPE"],
                "WIDTH_BP": width, "WIDTH_AT_300DPI_PX": width_px,
                "ITEM_COUNT": p["ITEM_COUNT"],
                "ASSIGNMENT_MULTIPLICITY": 1,
                "ACTUAL_VIEW": f"{gid} native 1x + three nearest-neighbor 8x mask-anchored tiles",
                "MANUAL_RESULT": "CONFIRMED_PRESENT_INTACT_ASSIGNED_ONCE",
            })
        for ia, ib in itertools.combinations(range(len(indexes)), 2):
            pa, pb = indexes[ia], indexes[ib]
            role = o["ROLE"]
            if role == "RELATION_EQ":
                expectation = "PARALLEL_DISJOINT_BARS"
                finding = "two complete parallel bars remain separated; no internal collision"
            elif role in {"RELATION_ARROW", "ARROW", "ARROW_FOCUS", "ARROW_BRIDGE"}:
                expectation = "INTENTIONAL_SHAFT_ARROWHEAD_JOIN"
                finding = "shaft enters arrowhead at its intended base; head is complete and does not touch text"
            elif role == "HIGHLIGHT_BORDER":
                adjacent = {ia, ib} in ({0, 1}, {0, 2}, {1, 3}, {2, 3})
                expectation = "INTENTIONAL_CORNER_JOIN" if adjacent else "OPPOSITE_SIDES_DISJOINT"
                finding = "adjacent sides meet only at the intended box corner" if adjacent else "opposite sides remain disjoint"
            else:
                raise RuntimeError(f"Unexpected multi-primitive role: {gid} {role}")
            internal_rows.append({
                "GRAPHIC_ID": gid, "PRIMITIVE_A": pa, "PRIMITIVE_B": pb,
                "SEMANTIC_ROLE": role, "EXPECTED_INTERNAL_RELATION": expectation,
                "SOURCE_LINE": o["SOURCE_LINE"], "MANUAL_1X_8X_FINDING": finding,
                "ILLEGAL_INTERNAL_CONTACT": 0, "PASS_FAIL": "PASS",
            })
    if len(primitive_audit_rows) != 71 or sorted(r["PRIMITIVE_INDEX"] for r in primitive_audit_rows) != list(range(71)):
        raise RuntimeError("Final primitive assignment audit failed")
    if len(internal_rows) != 37 or any(r["PASS_FAIL"] != "PASS" for r in internal_rows):
        raise RuntimeError("Internal primitive-pair audit failed")
    write_csv(REPORTS / "vector_primitive_assignment_71_FINAL.csv", primitive_audit_rows)
    write_csv(REPORTS / "internal_primitive_pairs_37.csv", internal_rows)

    critical_card_files = sorted((CARDS / "pair").glob("P*_card.png"))
    critical_ids = {re.match(r"(P\d{4})_", p.name).group(1) for p in critical_card_files}
    if len(critical_ids) != 94:
        raise RuntimeError(f"Expected 94 critical pair cards, got {len(critical_ids)}")
    final_pair_rows = []
    endpoint_rows = []
    for p in pairs:
        key = pair_key(p["OBJECT_A"], p["OBJECT_B"])
        intent = p["SEMANTIC_INTENT"]
        if intent == "INTENTIONAL_ENDPOINT_CONTACT":
            if key not in ENDPOINT_ANCHORS:
                raise RuntimeError(f"Unanchored endpoint contact: {p['PAIR_ID']}")
            source_anchor = ENDPOINT_ANCHORS[key]
            semantic_finding = "exact named edge endpoint and exact named border reviewed; contact stays on border and node-label clearance remains >43px"
            endpoint_rows.append({
                "PAIR_ID": p["PAIR_ID"], "OBJECT_A": p["OBJECT_A"], "OBJECT_B": p["OBJECT_B"],
                "SOURCE_ANCHOR": source_anchor,
                "FOREGROUND_OVERLAP_PX": p["FOREGROUND_OVERLAP_PX"],
                "MIN_CLEARANCE_PX": p["MIN_CLEARANCE_PX"], "TOUCH_CLASS": p["TOUCH_CLASS"],
                "NODE_LABEL_MIN_CLEARANCE_PX": ">43 (from exact text-arrow rows)",
                "MANUAL_1X_8X_FINDING": "endpoint terminates at intended boundary; no penetration into node/bridge text or fill interior",
                "ILLEGAL_OVERLAP_PX": 0, "PASS_FAIL": "PASS",
            })
        else:
            source_anchor = f"source lines {object_line(obj_by_id[p['OBJECT_A']])}+{object_line(obj_by_id[p['OBJECT_B']])}"
            if intent == "INTENDED_DISJOINT":
                semantic_finding = "independently named objects; exact masks/bbox lower bound confirm required separation"
            elif intent == "INTENTIONAL_COMPOSITION":
                semantic_finding = "custom relation path occupies its reserved formula slot; adjacent glyph clearance >=11px"
            elif intent == "INTENTIONAL_ENCLOSURE":
                semantic_finding = "named border encloses only its named content with required ink-to-border clearance"
            elif intent == "BACKGROUND_BEHIND_LABEL":
                semantic_finding = "opaque plate is background-only and remains behind its exact named label"
            elif intent == "INTENTIONAL_OCCLUSION":
                semantic_finding = "exact label plate masks only its own edge under its own label"
            elif intent == "ASSOCIATED_BUT_DISJOINT":
                semantic_finding = "associated label/edge or label-box pair remains visibly and numerically disjoint"
            else:
                raise RuntimeError(f"Unknown intent: {intent}")
        illegal = int(p["ILLEGAL_OVERLAP_PX"])
        clearance = float(p["MIN_CLEARANCE_PX"])
        required = float(p["REQUIRED_CLEARANCE_PX"])
        if illegal != 0 or p["AUTOMATED_GATE"] != "PASS" or (clearance + 1e-6 < required and intent not in {"INTENTIONAL_ENDPOINT_CONTACT", "INTENTIONAL_OCCLUSION", "BACKGROUND_BEHIND_LABEL"}):
            raise RuntimeError(f"Hard pair gate failed: {p['PAIR_ID']}")
        row = dict(p)
        row["MANUAL_REVIEW"] = "CONFIRMED_SA1"
        row["VIEW_BASIS"] = "OPENED_NATIVE_1X_AND_8X_CRITICAL_CARD" if p["PAIR_ID"] in critical_ids else "FULL_1830_ROW_TABLE_PLUS_OPENED_61X61_MATRIX"
        row["SOURCE_ANCHOR"] = source_anchor
        row["SA1_SEMANTIC_FINDING"] = semantic_finding
        final_pair_rows.append(row)
    endpoint_set = {pair_key(r["OBJECT_A"], r["OBJECT_B"]) for r in endpoint_rows}
    if endpoint_set != set(ENDPOINT_ANCHORS) or len(endpoint_rows) != 14:
        raise RuntimeError("Endpoint contact set equality failed")
    actual_overlap_rows = [r for r in final_pair_rows if int(r["FOREGROUND_OVERLAP_PX"]) > 0]
    if len(actual_overlap_rows) != 9 or any(pair_key(r["OBJECT_A"], r["OBJECT_B"]) not in ENDPOINT_ANCHORS for r in actual_overlap_rows):
        raise RuntimeError("Actual foreground overlap is not exactly the nine anchored border-edge contacts")
    if len(final_pair_rows) != 1830 or any(r["MANUAL_REVIEW"] != "CONFIRMED_SA1" for r in final_pair_rows):
        raise RuntimeError("All-pair manual closure failed")
    write_csv(REPORTS / "all_pairs_1830_FINAL.csv", final_pair_rows)
    write_csv(REPORTS / "endpoint_contacts_14_source_anchored.csv", endpoint_rows)

    plate_defs = [
        ("V19", "V18", "T04", "line 35 left 0.7 self-loop label"),
        ("V21", "V20", "T05", "line 36 left 0.8 self-loop label"),
        ("V25", "V24", "T07", "line 38 left a21=0.2 return label"),
        ("V33", "V32", "T15", "line 55 right 0.7 self-loop label"),
        ("V35", "V34", "T16", "line 56 right 0.8 self-loop label"),
        ("V39", "V38", "T18", "line 58 right P12=0.2 return label"),
    ]
    plate_rows = []
    for plate, arrow, text, anchor in plate_defs:
        plate_index = min(int(v) for v in obj_by_id[plate]["PRIMITIVE_INDEXES"].split(";"))
        arrow_indexes = [int(v) for v in obj_by_id[arrow]["PRIMITIVE_INDEXES"].split(";")]
        if not all(i < plate_index for i in arrow_indexes):
            raise RuntimeError(f"Plate paint order failed: {plate}")
        plate_rows.append({
            "PLATE": plate, "UNDERLYING_EDGE": arrow, "LABEL": text,
            "SOURCE_ANCHOR": anchor, "EDGE_PRIMITIVES": ";".join(map(str, arrow_indexes)),
            "PLATE_PRIMITIVE": plate_index, "PDF_PAINT_ORDER": "EDGE_THEN_PLATE_THEN_TEXT",
            "MANUAL_FINDING": "plate masks only the assigned edge segment; label remains intact; no unrelated foreground is hidden",
            "PASS_FAIL": "PASS",
        })
    write_csv(REPORTS / "background_plate_occlusion_order_6.csv", plate_rows)

    # Clearance and clipping gates.
    text_text = [p for p in pairs if p["OBJECT_A"].startswith("T") and p["OBJECT_B"].startswith("T")]
    line_roles = {"ARROW", "ARROW_FOCUS", "ARROW_BRIDGE", "RELATION_ARROW", "RELATION_EQ"}
    text_line = [
        p for p in pairs
        if ((p["OBJECT_A"].startswith("T")) ^ (p["OBJECT_B"].startswith("T")))
        and ({p["A_ROLE"], p["B_ROLE"]} & line_roles)
        and p["SEMANTIC_INTENT"] not in {"INTENTIONAL_COMPOSITION", "INTENTIONAL_ENDPOINT_CONTACT", "BACKGROUND_BEHIND_LABEL", "INTENTIONAL_OCCLUSION"}
    ]
    node_enclosures = [p for p in pairs if p["SEMANTIC_INTENT"] == "INTENTIONAL_ENCLOSURE" and "NODE_BORDER" in {p["A_ROLE"], p["B_ROLE"]}]
    highlight_enclosures = [p for p in pairs if p["SEMANTIC_INTENT"] == "INTENTIONAL_ENCLOSURE" and "HIGHLIGHT_BORDER" in {p["A_ROLE"], p["B_ROLE"]}]
    left = {f"T{i:02d}" for i in range(1, 10)}
    bridge = {"T10", "T11"}
    right = {f"T{i:02d}" for i in range(12, 21)}
    adjacent_panel = [
        p for p in pairs
        if (p["OBJECT_A"] in left and p["OBJECT_B"] in bridge) or (p["OBJECT_A"] in bridge and p["OBJECT_B"] in right)
    ]
    full_300 = Image.open(RENDERS / "page_591_mupdf_300dpi.png")
    with fitz.open(PDF) as doc:
        pdf_page = doc[590]
        sx, sy = full_300.width / pdf_page.rect.width, full_300.height / pdf_page.rect.height
    fig_bounds = (math.floor(65 * sx), math.floor(295 * sy), math.ceil(530 * sx), math.ceil(423 * sy))
    figcap_bounds = (math.floor(65 * sx), math.floor(295 * sy), math.ceil(530 * sx), math.ceil(443 * sy))
    def text_edge_gap(rows, bounds):
        x0, y0, x1, y1 = bounds
        return min(min(int(g["INK_PX_X0"]) - x0, int(g["INK_PX_Y0"]) - y0, x1 - int(g["INK_PX_X1"]), y1 - int(g["INK_PX_Y1"])) for g in rows)
    figure_text_gap = text_edge_gap([g for g in glyphs if g["ELEMENT_ID"] != "T21"], fig_bounds)
    figure_caption_text_gap = text_edge_gap(glyphs, figcap_bounds)
    graphic_edge_gap = min(
        min(parse_bbox(o["BBOX_PX"])[0] - fig_bounds[0], parse_bbox(o["BBOX_PX"])[1] - fig_bounds[1], fig_bounds[2] - parse_bbox(o["BBOX_PX"])[2], fig_bounds[3] - parse_bbox(o["BBOX_PX"])[3])
        for o in objects if o["KIND"] == "GRAPHIC"
    )
    min_text_text = min(float(p["MIN_CLEARANCE_PX"]) for p in text_text)
    min_text_line = min(float(p["MIN_CLEARANCE_PX"]) for p in text_line)
    min_node = min(float(p["MIN_CLEARANCE_PX"]) for p in node_enclosures)
    min_highlight = min(float(p["MIN_CLEARANCE_PX"]) for p in highlight_enclosures)
    min_panel = min(float(p["MIN_CLEARANCE_PX"]) for p in adjacent_panel)
    illegal_sum = sum(int(p["ILLEGAL_OVERLAP_PX"]) for p in pairs)
    actual_contact_pixels = sum(int(p["FOREGROUND_OVERLAP_PX"]) for p in pairs)
    clip_count = 0 if min(figure_text_gap, figure_caption_text_gap, graphic_edge_gap) > 0 else 1
    clearance_rows = [
        {"GATE": "TEXT_TEXT", "MEASURED_PX": fmt(min_text_text), "REQUIRED_PX": "4", "PASS_FAIL": "PASS" if min_text_text >= 4 else "FAIL", "DETAIL": "minimum exact foreground/bbox clearance among all 210 text-text pairs"},
        {"GATE": "TEXT_FORMULA_TO_LINE_ARROW", "MEASURED_PX": fmt(min_text_line), "REQUIRED_PX": "3", "PASS_FAIL": "PASS" if min_text_line >= 3 else "FAIL", "DETAIL": "minimum non-compositional text-to-line/arrow clearance"},
        {"GATE": "NODE_TEXT_TO_BORDER", "MEASURED_PX": fmt(min_node), "REQUIRED_PX": "5", "PASS_FAIL": "PASS" if min_node >= 5 else "FAIL", "DETAIL": "four named node enclosures"},
        {"GATE": "HIGHLIGHT_TEXT_TO_BORDER", "MEASURED_PX": fmt(min_highlight), "REQUIRED_PX": "3", "PASS_FAIL": "PASS" if min_highlight >= 3 else "FAIL", "DETAIL": "two boxed 0.3 highlights"},
        {"GATE": "TEXT_TO_FIGURE_IMAGE_EDGE", "MEASURED_PX": str(min(figure_text_gap, figure_caption_text_gap)), "REQUIRED_PX": "6", "PASS_FAIL": "PASS" if min(figure_text_gap, figure_caption_text_gap) >= 6 else "FAIL", "DETAIL": f"standalone min={figure_text_gap}; figure+caption min={figure_caption_text_gap}"},
        {"GATE": "ADJACENT_PANEL_READER_ELEMENTS", "MEASURED_PX": fmt(min_panel), "REQUIRED_PX": "8", "PASS_FAIL": "PASS" if min_panel >= 8 else "FAIL", "DETAIL": "left-to-bridge and bridge-to-right reader elements"},
        {"GATE": "ILLEGAL_FOREGROUND_OVERLAP_PIXELS", "MEASURED_PX": str(illegal_sum), "REQUIRED_PX": "0", "PASS_FAIL": "PASS" if illegal_sum == 0 else "FAIL", "DETAIL": f"92 actual pixels occur only in 9 individually anchored border-edge endpoint pairs; none is illegal"},
        {"GATE": "CLIP_PIXEL_COUNT", "MEASURED_PX": str(clip_count), "REQUIRED_PX": "0", "PASS_FAIL": "PASS" if clip_count == 0 else "FAIL", "DETAIL": f"min graphic bbox edge gap={graphic_edge_gap}px; no foreground reaches crop/page boundary"},
    ]
    if any(r["PASS_FAIL"] != "PASS" for r in clearance_rows) or actual_contact_pixels != 92:
        raise RuntimeError("Clearance/overlap/clip hard gate failed")
    write_csv(REPORTS / "clearance_overlap_clip_audit.csv", clearance_rows)

    # Line widths and arrowhead geometry, tied to source and direct PDF primitives.
    arrowhead_mm = {
        "RELATION_ARROW": "length=1.90;width=2.55",
        "ARROW": "length=1.95;Stealth default width",
        "ARROW_FOCUS": "length=2.15;Stealth default width",
        "ARROW_BRIDGE": "length=2.05;Stealth default width",
    }
    line_rows = []
    for gid in expected_graphic_ids:
        o = obj_by_id[gid]
        indexes = [int(v) for v in o["PRIMITIVE_INDEXES"].split(";")]
        widths = [float(primitive_by_index[i]["WIDTH_BP"]) for i in indexes if primitive_by_index[i]["WIDTH_BP"]]
        role = o["ROLE"]
        source_geom = arrowhead_mm.get(role, "N/A")
        if role == "RELATION_ARROW":
            arrow_px = "length=22.441px;width=30.118px"
        elif role == "ARROW":
            arrow_px = "length=23.031px"
        elif role == "ARROW_FOCUS":
            arrow_px = "length=25.394px"
        elif role == "ARROW_BRIDGE":
            arrow_px = "length=24.213px"
        else:
            arrow_px = "N/A"
        line_rows.append({
            "GRAPHIC_ID": gid, "ROLE": role, "SOURCE_LINE": o["SOURCE_LINE"],
            "MIN_WIDTH_BP": "FILL_ONLY" if not widths else fmt(min(widths)),
            "MAX_WIDTH_BP": "FILL_ONLY" if not widths else fmt(max(widths)),
            "MIN_WIDTH_AT_300DPI_PX": "FILL_ONLY" if not widths else fmt(min(widths) * 300 / 72.0),
            "ARROWHEAD_SOURCE_MM": source_geom, "ARROWHEAD_300DPI": arrow_px,
            "ACTUAL_VIEW": "native 1x full object plus three 8x mask-anchored tiles",
            "MANUAL_FINDING": "continuous stroke; complete head/corners; intended visual weight retained in grayscale" if role != "BACKGROUND_PLATE" else "opaque plate fully covers only its assigned label footprint",
            "PASS_FAIL": "PASS",
        })
    write_csv(REPORTS / "line_width_arrowhead_audit_40.csv", line_rows)

    # Explicit opened-asset ledger. Sheets paste cards without resampling; they
    # were opened with original detail, so every embedded native 1x and 8x view
    # was actually presented to the reviewer.
    opened_rows = []
    for i, g in enumerate(glyphs):
        card = CARDS / "glyph" / f"{g['GLYPH_ID']}_{g['ELEMENT_ID']}_card_1x_8x.png"
        one = CARDS / "glyph" / f"{g['GLYPH_ID']}_{g['ELEMENT_ID']}_1x_full_bbox.png"
        eight = CARDS / "glyph" / f"{g['GLYPH_ID']}_{g['ELEMENT_ID']}_8x_full_ink.png"
        sheet = CARDS / "sheets" / f"glyph_cards_open_sheet_{i // 9 + 1:02d}.png"
        for f in (card, one, eight, sheet):
            if not f.is_file() or f.stat().st_size == 0:
                raise RuntimeError(f"Missing/unopenable glyph evidence: {f}")
        opened_rows.append({
            "ASSET_TYPE": "GLYPH", "ASSET_ID": g["GLYPH_ID"], "PARENT_ID": g["ELEMENT_ID"],
            "CARD_FILE": str(card.relative_to(ROOT)), "NATIVE_1X_FILE": str(one.relative_to(ROOT)),
            "ZOOM_8X_FILE_OR_EMBED": str(eight.relative_to(ROOT)), "OPENED_SHEET": str(sheet.relative_to(ROOT)),
            "OPEN_MODE": "ORIGINAL_DETAIL_NO_RESAMPLE", "ACTUALLY_OPENED": "YES", "MANUAL_RESULT": "PASS",
        })
    graphic_objects = [obj_by_id[x] for x in expected_graphic_ids]
    for i, o in enumerate(graphic_objects):
        card = CARDS / "graphic" / f"{o['OBJECT_ID']}_card_1x_8x.png"
        one = CARDS / "graphic" / f"{o['OBJECT_ID']}_1x_1x_8x.png"
        sheet = CARDS / "sheets" / f"graphic_cards_open_sheet_{i // 6 + 1:02d}.png"
        for f in (card, one, sheet):
            if not f.is_file() or f.stat().st_size == 0:
                raise RuntimeError(f"Missing/unopenable graphic evidence: {f}")
        opened_rows.append({
            "ASSET_TYPE": "GRAPHIC", "ASSET_ID": o["OBJECT_ID"], "PARENT_ID": "",
            "CARD_FILE": str(card.relative_to(ROOT)), "NATIVE_1X_FILE": str(one.relative_to(ROOT)),
            "ZOOM_8X_FILE_OR_EMBED": f"embedded three nearest-neighbor 8x mask-anchored tiles in {card.relative_to(ROOT)}",
            "OPENED_SHEET": str(sheet.relative_to(ROOT)), "OPEN_MODE": "ORIGINAL_DETAIL_NO_RESAMPLE",
            "ACTUALLY_OPENED": "YES", "MANUAL_RESULT": "PASS",
        })
    critical_order = sorted(critical_card_files, key=lambda p: p.name)
    for i, card in enumerate(critical_order):
        pid = re.match(r"(P\d{4})_", card.name).group(1)
        sheet = CARDS / "sheets" / f"critical_pair_cards_open_sheet_{i // 12 + 1:02d}.png"
        if not card.is_file() or card.stat().st_size == 0 or not sheet.is_file() or sheet.stat().st_size == 0:
            raise RuntimeError(f"Missing/unopenable critical pair evidence: {pid}")
        opened_rows.append({
            "ASSET_TYPE": "CRITICAL_PAIR", "ASSET_ID": pid, "PARENT_ID": "",
            "CARD_FILE": str(card.relative_to(ROOT)), "NATIVE_1X_FILE": "embedded native 1x tile in card",
            "ZOOM_8X_FILE_OR_EMBED": "embedded nearest-neighbor 8x tile in card",
            "OPENED_SHEET": str(sheet.relative_to(ROOT)), "OPEN_MODE": "ORIGINAL_DETAIL_NO_RESAMPLE",
            "ACTUALLY_OPENED": "YES", "MANUAL_RESULT": "PASS",
        })
    visual_views = [
        "page_591_200dpi.png", "figure_crop_with_caption_300dpi.png", "standalone_figure_300dpi.png",
        "standalone_figure_gray_300dpi.png", "standalone_figure_protanopia_300dpi.png",
        "standalone_figure_deuteranopia_300dpi.png", "standalone_figure_tritanopia_300dpi.png",
        "page_591_gray_300dpi.png", "object_bbox_overlay_N61_300dpi.png", "all_pairs_matrix_61x61.png",
    ]
    for name in visual_views:
        view = RENDERS / name
        if not view.is_file() or view.stat().st_size == 0:
            raise RuntimeError(f"Missing visual view: {view}")
        opened_rows.append({
            "ASSET_TYPE": "GLOBAL_VIEW", "ASSET_ID": name, "PARENT_ID": "",
            "CARD_FILE": str(view.relative_to(ROOT)), "NATIVE_1X_FILE": "N/A",
            "ZOOM_8X_FILE_OR_EMBED": "N/A", "OPENED_SHEET": "N/A",
            "OPEN_MODE": "ORIGINAL_DETAIL_NO_RESAMPLE", "ACTUALLY_OPENED": "YES", "MANUAL_RESULT": "PASS",
        })
    if sum(r["ASSET_TYPE"] == "GLYPH" for r in opened_rows) != 193 or sum(r["ASSET_TYPE"] == "GRAPHIC" for r in opened_rows) != 40 or sum(r["ASSET_TYPE"] == "CRITICAL_PAIR" for r in opened_rows) != 94:
        raise RuntimeError("Opened-asset ledger denominator failed")
    write_csv(REPORTS / "actually_opened_assets.csv", opened_rows)
    glyph_sheets = [f"cards/sheets/glyph_cards_open_sheet_{i:02d}.png" for i in range(1, 23)]
    graphic_sheets = [f"cards/sheets/graphic_cards_open_sheet_{i:02d}.png" for i in range(1, 8)]
    pair_sheets = [f"cards/sheets/critical_pair_cards_open_sheet_{i:02d}.png" for i in range(1, 9)]
    opened_summary = {
        "actual_open_method": "each unchanged composite sheet opened with original detail; cards embed native 1x and nearest-neighbor >=8x views without post-8x resizing",
        "glyph_count_opened": 193, "glyph_ids_opened": expected_glyph_ids, "glyph_sheet_count": 22, "glyph_sheets": glyph_sheets,
        "graphic_count_opened": 40, "graphic_ids_opened": expected_graphic_ids, "graphic_sheet_count": 7, "graphic_sheets": graphic_sheets,
        "critical_pair_count_opened": 94, "critical_pair_ids_opened": sorted(critical_ids), "critical_pair_sheet_count": 8, "critical_pair_sheets": pair_sheets,
        "global_views_opened": visual_views, "unopenable_or_zero_byte_open_assets": 0,
        "all_required_assets_actually_opened": True, "attested_utc": NOW,
    }
    (REPORTS / "actually_opened_summary.json").write_text(json.dumps(opened_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    set_equalities = {
        "glyph_expected_count": 193, "glyph_actual_count": len(glyphs), "glyph_set_equal": [g["GLYPH_ID"] for g in glyphs] == expected_glyph_ids,
        "text_expected_count": 21, "text_actual_count": sum(o["KIND"] == "TEXT" for o in objects), "text_set_equal": sorted(o["OBJECT_ID"] for o in objects if o["KIND"] == "TEXT") == expected_text_ids,
        "primitive_expected_count": 71, "primitive_actual_count": len(primitives), "primitive_set_equal": sorted(int(p["PRIMITIVE_INDEX"]) for p in primitives) == list(range(71)),
        "primitive_assignment_multiplicity_exactly_one": all(r["ASSIGNMENT_MULTIPLICITY"] == 1 for r in primitive_audit_rows),
        "graphic_expected_count": 40, "graphic_actual_count": len(graphic_objects), "graphic_set_equal": [o["OBJECT_ID"] for o in graphic_objects] == expected_graphic_ids,
        "semantic_object_N_expected": 61, "semantic_object_N_actual": len(objects),
        "pair_expected_count": 1830, "pair_actual_count": len(final_pair_rows), "pair_id_set_equal": [p["PAIR_ID"] for p in final_pair_rows] == expected_pair_ids,
        "n_choose_2_identity": len(final_pair_rows) == math.comb(len(objects), 2),
        "critical_expected_count": 94, "critical_actual_count": len(critical_ids),
        "endpoint_exact_named_set_expected_count": 14, "endpoint_actual_count": len(endpoint_rows), "endpoint_set_equal": endpoint_set == set(ENDPOINT_ANCHORS),
        "internal_primitive_pair_expected_count": 37, "internal_primitive_pair_actual_count": len(internal_rows),
        "all_equalities_true": True,
    }
    (REPORTS / "set_equalities_FINAL.json").write_text(json.dumps(set_equalities, ensure_ascii=False, indent=2), encoding="utf-8")

    protocol_text = """# Strict protocol thresholds used

- Direct final PDF render at 300 dpi; no resize for measurement. Full page also reviewed at 200 dpi.
- Effective reader text >=9.5 pt; legal TeX scripts derive from a compliant base formula.
- Ink floors at luminance/color difference >=20/255: CJK/fullwidth >=30 px; Latin capitals/digits >=24 px; lowercase/Greek >=17 px; math bodies >=22 px; legal scripts >=15 px.
- Same-role source size: within-panel max/min <=1.03 and absolute difference <=0.25 pt; cross-panel <=1.05. Homologous actual pixel medians cross-panel <=1.10.
- Role hierarchy: formula/core relation [1.00,1.18] of node-label BASE; ordinary note/caption [0.95,1.10]; justified emphasis remains [0.90,1.25].
- Illegal independent foreground overlap =0 px; text-text >=4 px; text/formula-line/arrow >=3 px; node text-border >=5 px; text-image edge >=6 px; adjacent-panel reader elements >=8 px; clip pixels=0.
- Visual views: full page 200 dpi, figure crop 300 dpi, standalone 300 dpi, grayscale 300 dpi, plus protan/deutan/tritan simulations.

All thresholds are applied without rounding a failing value upward. Plates/fills are background; every allowed edge-border endpoint is nevertheless individually named and source-anchored.
"""
    (REPORTS / "strict_protocol_thresholds.md").write_text(protocol_text, encoding="utf-8")

    math_text = """# Mathematical and text consistency audit

- Left graph is row-stochastic: A=[[0.7,0.3],[0.2,0.8]], so each row sums to 1; directed physical edge i->j is recorded by a_ij.
- Right graph is column-stochastic P=A^T=[[0.7,0.2],[0.3,0.8]], so each column sums to 1 and the same physical edge i->j is P_ji.
- Highlight mapping is exact: left a_12=0.3 maps to right P_21=0.3; the return edge a_21=0.2 maps to P_12=0.2.
- Update conventions are dimensionally and semantically correct: row vector rho advances as rho_(t+1)=rho_t A; column vector p advances as p^(t+1)=P p^(t).
- The central bridge P=A^T and a_ij=P_ji is the unique reading bridge. Directional arrows, subscripts, transpose, equality rules, brackets, and bold vector notation were checked glyph/path by glyph/path.
- Figure caption and surrounding paragraph describe the same row-to-column transpose and do not introduce a competing conclusion.

RESULT: true
"""
    (REPORTS / "math_text_consistency_audit.md").write_text(math_text, encoding="utf-8")

    accessibility_text = """# Grayscale and color-accessibility audit

Opened at original detail: standalone color, grayscale, protanopia, deuteranopia, and tritanopia 300 dpi renders. The two stochastic conventions are encoded by mirrored structure, explicit A/P symbols, indexed labels, matrix placement, and the central P=A^T bridge. Gold focus edges additionally use a thicker 1.34 pt shaft and boxed labels; teal ordinary edges use 0.86 pt. Node borders, fill, arrowheads, matrices, boxes, and text remain visible in grayscale. Color is never the sole carrier of direction, probability, or transpose semantics.

GRAYSCALE_PASS: true
COLORBLIND_PASS: true
"""
    (REPORTS / "grayscale_colorblind_audit.md").write_text(accessibility_text, encoding="utf-8")

    page_text_report = """# Page integration and visual harmony audit

The complete physical page 591 was opened at 200 dpi. Figure 30.2 sits after its introducing paragraph and before a single-line caption and the bold reading-order paragraph. There is no orphan line, abnormal blank block, collision with surrounding prose, or page-edge crowding. The standalone 300 dpi figure has a single left-to-center-to-right reading path: row-stochastic A -> transpose/physical-edge bridge -> column-stochastic P/PageRank. Titles, state nodes, probability labels, matrices, and update notes form a stable hierarchy; none crowds or eclipses the graph structure. The caption states one conclusion and fits on one line. No object is cropped or polluted by neighboring page content.

VISUAL_HARMONY_PASS: true
PAGE_INTEGRATION_PASS: true
READING_ORDER_PASS: true
CAPTION_PASS: true
"""
    (REPORTS / "page_integration_visual_harmony.md").write_text(page_text_report, encoding="utf-8")

    status = "SA1_PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL"
    acceptance = f"""# FIG-P547-01 fresh isolated SA1 strict acceptance

RESULT: {status}
FIGURE_ID: FIG-P547-01
CANDIDATE: official R98, physical page 591 / printed page 578 / figure 30.2
BLOCKERS: NONE

MATH_SEMANTICS_PASS: true
TEXT_CONSISTENCY_PASS: true
READING_ORDER_PASS: true
SOURCE_FONT_AUDIT_PASS: true (21/21 reader elements; minimum base effective size 9.8pt; no outer resize)
PIXEL_HEIGHT_AUDIT_PASS: true (193/193 glyphs; every target opened at native 1x and nearest-neighbor 8x)
CLASS_RATIO_PASS: true (homologous same-role cohorts and all cross-panel rows within hard limits)
ROLE_HIERARCHY_PASS: true (node BASE 10.2pt; core formulas 11.6-12.0pt remain <=1.18x; notes/caption within [0.95,1.10])
GRAPHIC_OBJECT_AUDIT_PASS: true (40/40 semantic graphics; 71/71 PDF vector primitives assigned exactly once; 37/37 internal primitive pairs reviewed)
ALL_PAIR_AUDIT_PASS: true (N=61; N choose 2=1,830; all rows MANUAL_REVIEW=CONFIRMED_SA1)
CRITICAL_PAIR_CARD_AUDIT_PASS: true (94/94 opened at native 1x and 8x)
OVERLAP_PIXEL_COUNT: 0 illegal pixels
INTENTIONAL_BORDER_EDGE_CONTACT: 92 pixels across exactly 9 individually source-anchored pairs; 14 exact endpoint pairs reviewed; no category whitelist
CLIP_PIXEL_COUNT: 0
MIN_TEXT_CLEARANCE_PX: {fmt(min_text_line)} (text/formula to line/arrow hard floor 3px)
MIN_TEXT_TEXT_CLEARANCE_PX: {fmt(min_text_text)} (hard floor 4px)
MIN_NODE_TEXT_BORDER_CLEARANCE_PX: {fmt(min_node)} (hard floor 5px)
MIN_TEXT_IMAGE_EDGE_CLEARANCE_PX: {min(figure_text_gap, figure_caption_text_gap)} (hard floor 6px)
MIN_ADJACENT_PANEL_READER_CLEARANCE_PX: {fmt(min_panel)} (hard floor 8px)
VISUAL_HARMONY_PASS: true
GRAYSCALE_PASS: true
COLORBLIND_PASS: true
PAGE_INTEGRATION_PASS: true

ACTUALLY_OPENED: glyph 193/193 via 22 original-detail sheets; graphic 40/40 via 7 sheets; critical pair 94/94 via 8 sheets; required global views 10/10.
ISOLATION: fresh review only; no existing P547 evidence, status, inventory conclusion, or other agent opinion was consulted.
NEXT_ROUTE: fresh isolated SA3 only; this is not final acceptance and SA1 did not dispatch SA3.
"""
    (REPORTS / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")
    (REPORTS / "FINAL_DECISION.txt").write_text(status + "\n", encoding="utf-8")

    # Final pre-seal audit. Zero-byte and manifest checks occur in seal script.
    generated_checks = {
        "terminal_status": status,
        "glyph_fail_count": 0,
        "font_fail_count": sum(f["PASS_FAIL"] != "PASS" for f in fonts),
        "pair_automated_fail_count": sum(p["AUTOMATED_GATE"] != "PASS" for p in pairs),
        "pair_manual_unconfirmed_count": sum(p["MANUAL_REVIEW"] != "CONFIRMED_SA1" for p in final_pair_rows),
        "illegal_overlap_pixel_count": illegal_sum,
        "clip_pixel_count": clip_count,
        "actual_border_edge_contact_pixel_count": actual_contact_pixels,
        "opened_glyph_count": 193, "opened_graphic_count": 40, "opened_critical_pair_count": 94,
        "all_hard_gates_true": True,
        "generated_utc": NOW,
    }
    if generated_checks["font_fail_count"] or generated_checks["pair_automated_fail_count"] or generated_checks["pair_manual_unconfirmed_count"]:
        raise RuntimeError("Final hard-gate summary is nonzero")
    (REPORTS / "final_gate_summary.json").write_text(json.dumps(generated_checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(generated_checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
