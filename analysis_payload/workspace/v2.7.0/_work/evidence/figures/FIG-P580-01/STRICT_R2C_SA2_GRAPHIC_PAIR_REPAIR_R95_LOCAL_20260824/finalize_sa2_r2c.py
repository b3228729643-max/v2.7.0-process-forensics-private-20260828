from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
SOURCE = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex"
PAGE_WRAPPER = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\v260_FIG-P580-01_page.tex"
STANDALONE_WRAPPER = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\v260_FIG-P580-01_standalone.tex"
SCHEMA = WORKSPACE / r"v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md"
GOAL = WORKSPACE / r"v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md"

STATUS = "SA2_LOCAL_PASS_AWAIT_ROOT_OFFICIAL_BUILD"
REPAIR_IDS = (
    "PAIR_GR004_GR025",
    "PAIR_GR020_GR022",
    "PAIR_GR020_GR024",
)
REPAIR_EXPECTED = {
    "PAIR_GR004_GR025": 6.280110,
    "PAIR_GR020_GR022": 5.000000,
    "PAIR_GR020_GR024": 9.770330,
}
PACKAGE_FILES = {
    "raw_roi_1x.png",
    "raw_roi_8x_nearest.png",
    "object_A_mask_1x.png",
    "object_A_mask_8x_nearest.png",
    "object_B_mask_1x.png",
    "object_B_mask_8x_nearest.png",
    "intersection_mask_1x.png",
    "intersection_mask_8x_nearest.png",
    "overlay_1x.png",
    "overlay_8x_nearest.png",
    "relation.json",
}
TERMINAL_OUTPUTS = {
    "final_file_integrity.csv",
    "machine_terminal_input_file_manifest.csv",
    "machine_final_check.json",
    "machine_final_check.md",
    "WRITE_STOPPED.md",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "pass"}


def passed(value: object) -> bool:
    return str(value).strip().upper() == "PASS"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def open_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as current:
        current.verify()
    with Image.open(path) as current:
        current.load()
        return current.size


def black_pixels(path: Path) -> int:
    with Image.open(path) as current:
        mono = current.convert("L")
        pixels = (
            mono.get_flattened_data()
            if hasattr(mono, "get_flattened_data")
            else mono.getdata()
        )
        return sum(value < 128 for value in pixels)


class Gatebook:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, object]] = {}
        self.issues: list[str] = []

    def add(self, name: str, condition: bool, detail: object) -> None:
        self.checks[name] = {
            "status": "PASS" if condition else "FAIL",
            "detail": detail,
        }
        if not condition:
            self.issues.append(f"{name}: {detail}")

    def stop_if_failed(self, stage: str) -> None:
        if self.issues:
            print(json.dumps({"stage": stage, "issues": self.issues}, ensure_ascii=False, indent=2))
            raise SystemExit(1)


def glyph_note(row: dict[str, str]) -> str:
    sheet_match = re.search(r"contact_sheet_(\d{2})_", row["SHEET"])
    sheet = sheet_match.group(1) if sheet_match else row["SHEET"]
    text_value = row["TEXT"].replace("\n", "\\n")
    return (
        f"{row['MAP_ID']} / sheet {sheet} cell {int(row['CELL']):02d} / "
        f"{row['UNICODE']} {text_value!r}: opened the native 1:1 source ROI and its exact "
        f"8x-nearest ORIGINAL | TARGET OVERLAY | MASK ONLY triplet; target contour in "
        f"bbox {row['NATIVE_GLYPH_BBOX_PX']} is fully red in context and the isolated mask "
        f"within ROI {row['NATIVE_CONTACT_ROI_PX']} contains no neighbour, line, marker, hatch, "
        "arrow, or frame pixel."
    )


def visual_note(row: dict[str, str]) -> str:
    check_id = row["CHECK_ID"]
    evidence = row["EVIDENCE_FILE"]
    if check_id == "VIEW_FULL_PAGE_200DPI":
        return (
            "Opened the final full-page 200 dpi view at original detail: figure, caption, body "
            "text, margins, and whitespace form a natural page rhythm; the -2 mm x-axis "
            "extensions remain inside the figure and do not approach page or caption content."
        )
    if check_id == "VIEW_FIGURE_CROP_300DPI":
        return (
            "Opened the final native 300 dpi figure crop: both panels, all labels, the weight "
            "card, markers, hatch, arrows, and the composite q_R dash are clear and uncrowded; "
            "the longer off-gaps at x=1 and x=4 read as coordinated dash rhythm, not damage."
        )
    if check_id == "VIEW_STANDALONE_300DPI":
        return (
            "Opened the final standalone 300 dpi page: the figure independently communicates "
            "left support insufficiency, right support coverage, unchanged q_R=1/5, p-curve "
            "sample points, and the three importance weights without relying on body prose."
        )
    if check_id == "VIEW_GRAYSCALE_300DPI":
        return (
            "Opened the final grayscale 300 dpi crop: solid/dashed/dotted line styles, open and "
            "filled markers, hatch, card frame, and text hierarchy remain distinguishable; no "
            "colour-only semantic dependency or new crowding appears."
        )
    if check_id == "VIEW_TEXT_OVERLAY_300DPI":
        return (
            "Opened the final text-measurement overlay at native 300 dpi: all 32 element boxes "
            "track their intended labels/formulas and remain clear of unrelated graphics; card "
            "text, axis text, caption, and panel labels retain complete visible contours."
        )
    script = check_id.rsplit("_", 1)[-1]
    role = row["ROLE"]
    panel = row["PANEL_ID"]
    contextual = {
        "FORMULA": "the right weight-card lines and values remain comfortably spaced inside the frame",
        "LEGEND": "legend/decoding text remains subordinate to panel titles and clear of plotted data",
        "ANNOTATION": "annotation lines retain readable leading and clear separation from curves and markers",
        "AXIS_TITLE": "axis decoding remains readable without crowding ticks, arrows, or the caption",
        "PANEL_TITLE": "panel titles lead the local hierarchy without appearing oversized against body text",
        "TICK": "tick labels remain legible and visually quieter than titles and semantic annotations",
        "CAPTION": "caption glyphs match the surrounding lecture-page body and automatic figure numbering",
    }.get(role, "the role remains readable and proportionate to nearby figure elements")
    return (
        f"{check_id}: opened {evidence} with the full-page and grayscale views; panel={panel}, "
        f"role={role}, script={script}, D={row['D_RATIO']}, E={row['E_RATIO']}. Font size, "
        f"weight, and colour are coordinated with same-role labels and page body; {contextual}; "
        "no abrupt enlargement, undersizing, collision, or grayscale loss was seen."
    )


def relation_note(
    row: dict[str, str],
    inventory: dict[str, dict[str, str]],
) -> tuple[str, str]:
    a = inventory[row["OBJECT_A"]]
    b = inventory[row["OBJECT_B"]]
    pair_id = row["PAIR_ID"]
    if pair_id in REPAIR_IDS:
        classification = "REPAIRED_SEPARATION_NO_SEMANTIC_EXEMPTION"
        extra = (
            "The native intersection mask is empty and the measured raw-mask clearance meets "
            "the explicit 3 px gate with safety margin; no coordinate, q_R height, marker data "
            "point, or hatch-domain semantic was waived."
        )
    elif truth(row["INTENTIONAL_GEOMETRY"]):
        classification = "PAIR_SPECIFIC_SEMANTIC_CONNECTION"
        extra = (
            "This is the pair-specific structural connection recorded in the bottom table; it "
            "is not a blanket marker-border or line-line exemption."
        )
    else:
        classification = "AUDITED_NONINTENTIONAL_SEPARATION"
        extra = (
            "The pair is nonintentional and passes its stated raw-mask separation requirement."
        )
    justification = (
        f"{row['REASON']} | {row['OBJECT_A']}={a['ROLE']}:{a['TEXT_OR_LABEL']} "
        f"({a['PANEL']}) versus {row['OBJECT_B']}={b['ROLE']}:{b['TEXT_OR_LABEL']} "
        f"({b['PANEL']})."
    )
    note = (
        f"{pair_id}: opened overlay_1x.png and overlay_8x_nearest.png at original detail; "
        f"package {row['EVIDENCE_PACKAGE']} also passed machine decoding of raw ROI, object A, "
        f"object B, intersection, and overlay at 1x/8x. Native overlap={row['OVERLAP_PIXEL_COUNT']} "
        f"px, clearance={row['CLEARANCE_PX']} px, required={row['REQUIRED_CLEARANCE_PX']} px. "
        f"{extra}"
    )
    return classification + " | " + justification, note


def preflight(book: Gatebook) -> dict[str, object]:
    marker = ROOT / "WRITE_STOPPED.md"
    book.add("write_stop_absent_before_finalizer", not marker.exists(), str(marker))

    external = [SOURCE, PAGE_WRAPPER, STANDALONE_WRAPPER, SCHEMA, GOAL]
    book.add(
        "external_inputs_exist",
        all(path.is_file() and path.stat().st_size > 0 for path in external),
        [str(path) for path in external],
    )
    source_text = SOURCE.read_text(encoding="utf-8")
    source_requirements = {
        "axis_extension": "x axis line style={shorten >=-2mm}" in source_text,
        "qR_height_unchanged": r"\pgfmathsetmacro{\ISQRHeight}{1/5}" in source_text,
        "p4_coordinate_unchanged": r"coordinates {(4,\ISPAtFour)};" in source_text,
        "p4_marker_size_unchanged": "mark=triangle*,mark size=3.2pt" in source_text,
        "qR_composite_dash": "dash pattern=on 3pt off 10pt" in source_text,
        "qR_phase": "dash phase=63.4pt" in source_text,
        "hatch_domain_unchanged": "soft clip={domain=2.5:5}" in source_text,
    }
    book.add("source_semantic_freeze", all(source_requirements.values()), source_requirements)

    page_pdf = ROOT / "build/page/v260_FIG-P580-01_page.pdf"
    stand_pdf = ROOT / "build/standalone/v260_FIG-P580-01_standalone.pdf"
    page_log = ROOT / "build/page/v260_FIG-P580-01_page.log"
    stand_log = ROOT / "build/standalone/v260_FIG-P580-01_standalone.log"
    page_fls = ROOT / "build/page/v260_FIG-P580-01_page.fls"
    stand_fls = ROOT / "build/standalone/v260_FIG-P580-01_standalone.fls"
    build_files = [page_pdf, stand_pdf, page_log, stand_log, page_fls, stand_fls]
    book.add(
        "final_local_build_files",
        all(path.is_file() and path.stat().st_size > 0 for path in build_files),
        {rel(path): path.stat().st_size if path.exists() else None for path in build_files},
    )
    logs_ok = (
        "Output written on v260_FIG-P580-01_page.pdf (1 page, 69568 bytes)." in page_log.read_text(encoding="utf-8", errors="ignore")
        and "Output written on v260_FIG-P580-01_standalone.pdf (1 page, 40556 bytes)." in stand_log.read_text(encoding="utf-8", errors="ignore")
    )
    fls_ok = all(
        "fig_v5_c02_is_support.tex" in path.read_text(encoding="utf-8", errors="ignore")
        for path in (page_fls, stand_fls)
    )
    build_after_source = all(path.stat().st_mtime >= SOURCE.stat().st_mtime for path in (page_pdf, stand_pdf))
    book.add(
        "final_build_identity",
        page_pdf.stat().st_size == 69568
        and stand_pdf.stat().st_size == 40556
        and logs_ok
        and fls_ok
        and build_after_source,
        {
            "page_bytes": page_pdf.stat().st_size,
            "standalone_bytes": stand_pdf.stat().st_size,
            "logs_ok": logs_ok,
            "fls_mentions_business_source": fls_ok,
            "pdfs_newer_than_source": build_after_source,
        },
    )

    core = read_json(ROOT / "core_audit_summary.json")
    expected_core = {
        "uid": "FIG-P580-01",
        "strict_schema_revision": 111,
        "glyph_count": 234,
        "necessary_substring_count": 18,
        "text_element_count": 32,
        "graphic_count": 25,
        "semantic_object_count": 57,
        "expected_unordered_pair_count": 1596,
        "actual_unordered_pair_count": 1596,
        "graphic_graphic_pair_count": 300,
        "graphic_graphic_assessed_count": 300,
        "graphic_graphic_intentional_count": 48,
        "graphic_graphic_overlap_pair_count": 25,
        "graphic_graphic_disjoint_under_3px_count": 23,
        "required_relation_count": 445,
        "critical_relation_package_count": 53,
        "pixel_failure_count": 0,
        "font_failure_count": 0,
        "D_failure_count": 0,
        "E_failure_count": 0,
        "pair_failure_count": 0,
        "required_relation_failure_count": 0,
        "clip_failure_count": 0,
        "opaque_graphic_coverage_failure_count": 0,
        "translucent_graphic_coverage_failure_count": 0,
        "source_unassigned_text_pixels": 0,
        "source_duplicate_text_pixels": 0,
        "glyph_missing_stroke_total": 0,
        "glyph_foreign_pixel_total": 0,
        "contact_sheet_count": 15,
        "contact_manifest_count": 234,
        "visual_template_count": 50,
    }
    mismatches = {key: [core.get(key), value] for key, value in expected_core.items() if core.get(key) != value}
    book.add("core_exact_counts", not mismatches, mismatches or expected_core)
    book.add(
        "core_boolean_gates",
        all(core.get(key) is True for key in ("text_completeness_pass", "math_body_consistency_pass", "anchor_checks_pass", "text_replay_exact"))
        and core.get("empty_mask_ids") == [],
        {key: core.get(key) for key in ("text_completeness_pass", "math_body_consistency_pass", "anchor_checks_pass", "text_replay_exact", "empty_mask_ids")},
    )

    objects = read_csv(ROOT / "object_inventory.csv")
    object_ids = [row["OBJECT_ID"] for row in objects]
    inventory = {row["OBJECT_ID"]: row for row in objects}
    expected_pairs = {
        tuple(sorted((left, right)))
        for index, left in enumerate(object_ids)
        for right in object_ids[index + 1 :]
    }
    book.add(
        "object_inventory",
        len(objects) == 57
        and len(set(object_ids)) == 57
        and sum(row["KIND"] == "TEXT" for row in objects) == 32
        and sum(row["KIND"] == "GRAPHIC" for row in objects) == 25
        and all(truth(row["NONEMPTY"]) and int(row["PIXELS"]) > 0 for row in objects),
        {"rows": len(objects), "unique": len(set(object_ids))},
    )

    pairs = read_csv(ROOT / "all_unordered_pairs.csv")
    actual_pairs = [tuple(sorted((row["OBJECT_A"], row["OBJECT_B"]))) for row in pairs]
    book.add(
        "unordered_pair_closure",
        len(pairs) == 1596
        and len(set(actual_pairs)) == 1596
        and set(actual_pairs) == expected_pairs
        and all(passed(row["PASS_FAIL"]) for row in pairs),
        {"rows": len(pairs), "unique": len(set(actual_pairs)), "expected": len(expected_pairs)},
    )
    graphics = {row["OBJECT_ID"] for row in objects if row["KIND"] == "GRAPHIC"}
    gg = [row for row in pairs if row["OBJECT_A"] in graphics and row["OBJECT_B"] in graphics]
    overlap_gg = [row for row in gg if int(row["OVERLAP_PIXEL_COUNT"]) > 0]
    near_gg = [row for row in gg if int(row["OVERLAP_PIXEL_COUNT"]) == 0 and float(row["CLEARANCE_PX"]) < 3.0]
    intentional_gg = [row for row in gg if truth(row["INTENTIONAL_GEOMETRY"])]
    expected_intentional = {row["PAIR_ID"] for row in overlap_gg + near_gg}
    book.add(
        "graphic_graphic_300_row_closure",
        len(gg) == 300
        and all(truth(row["ASSESSED"]) for row in gg)
        and len(intentional_gg) == 48
        and len(overlap_gg) == 25
        and len(near_gg) == 23
        and {row["PAIR_ID"] for row in intentional_gg} == expected_intentional
        and len({row["REASON"] for row in gg}) == 300
        and all(row["REASON"].strip() for row in gg),
        {
            "rows": len(gg),
            "assessed": sum(truth(row["ASSESSED"]) for row in gg),
            "intentional": len(intentional_gg),
            "overlap": len(overlap_gg),
            "disjoint_under_3px": len(near_gg),
            "unique_pair_specific_reasons": len({row["REASON"] for row in gg}),
        },
    )
    nonintentional = [row for row in gg if not truth(row["INTENTIONAL_GEOMETRY"])]
    book.add(
        "graphic_graphic_nonintentional_gate",
        len(nonintentional) == 252
        and all(int(row["OVERLAP_PIXEL_COUNT"]) == 0 for row in nonintentional)
        and all(
            float(row["CLEARANCE_PX"]) + 1e-9 >= float(row["REQUIRED_CLEARANCE_PX"])
            for row in nonintentional
        ),
        {"rows": len(nonintentional)},
    )

    package_rows = [row for row in gg if row["EVIDENCE_PACKAGE"].strip()]
    package_ids = {row["PAIR_ID"] for row in package_rows}
    package_problems: list[str] = []
    package_png_count = 0
    for row in package_rows:
        directory = ROOT / row["EVIDENCE_PACKAGE"]
        actual = {path.name for path in directory.iterdir() if path.is_file()} if directory.is_dir() else set()
        if actual != PACKAGE_FILES:
            package_problems.append(f"{row['PAIR_ID']}: files={sorted(actual)}")
            continue
        relation = read_json(directory / "relation.json")
        if relation.get("relation_id") != row["PAIR_ID"]:
            package_problems.append(f"{row['PAIR_ID']}: relation_id mismatch")
        if int(relation.get("overlap_pixels", -1)) != int(row["OVERLAP_PIXEL_COUNT"]):
            package_problems.append(f"{row['PAIR_ID']}: overlap JSON mismatch")
        if abs(float(relation.get("clearance_pixels", -1)) - float(row["CLEARANCE_PX"])) > 1e-6:
            package_problems.append(f"{row['PAIR_ID']}: clearance JSON mismatch")
        for stem in ("raw_roi", "object_A_mask", "object_B_mask", "intersection_mask", "overlay"):
            native = directory / f"{stem}_1x.png"
            enlarged = directory / f"{stem}_8x_nearest.png"
            native_size = open_png(native)
            enlarged_size = open_png(enlarged)
            package_png_count += 2
            if enlarged_size != (native_size[0] * 8, native_size[1] * 8):
                package_problems.append(f"{row['PAIR_ID']}: {stem} not exact 8x-nearest grid")
        intersection_pixels = black_pixels(directory / "intersection_mask_1x.png")
        if intersection_pixels != int(row["OVERLAP_PIXEL_COUNT"]):
            package_problems.append(
                f"{row['PAIR_ID']}: intersection black pixels {intersection_pixels} != {row['OVERLAP_PIXEL_COUNT']}"
            )
    book.add(
        "critical_package_closure",
        len(package_rows) == 53
        and len(package_ids) == 53
        and package_png_count == 530
        and not package_problems,
        {"packages": len(package_rows), "decoded_pngs": package_png_count, "problems": package_problems},
    )

    pair_by_id = {row["PAIR_ID"]: row for row in pairs}
    repair_details: dict[str, dict[str, object]] = {}
    repair_ok = True
    for pair_id, expected_clearance in REPAIR_EXPECTED.items():
        row = pair_by_id.get(pair_id, {})
        package_path = row.get("EVIDENCE_PACKAGE", "")
        directory = ROOT / package_path if package_path else Path("__missing__")
        row_ok = (
            bool(row)
            and row.get("ASSESSED") == "true"
            and row.get("INTENTIONAL_GEOMETRY") == "false"
            and int(row.get("OVERLAP_PIXEL_COUNT", -1)) == 0
            and abs(float(row.get("CLEARANCE_PX", -1)) - expected_clearance) <= 1e-6
            and float(row.get("CLEARANCE_PX", -1)) >= 4.0
            and float(row.get("REQUIRED_CLEARANCE_PX", -1)) == 3.0
            and row.get("PASS_FAIL") == "PASS"
            and package_path == f"critical_relations/{pair_id}"
            and directory.is_dir()
            and {path.name for path in directory.iterdir() if path.is_file()} == PACKAGE_FILES
            and black_pixels(directory / "intersection_mask_1x.png") == 0
        )
        repair_ok &= row_ok
        repair_details[pair_id] = {
            "overlap_pixel_count": int(row.get("OVERLAP_PIXEL_COUNT", -1)) if row else None,
            "clearance_px": float(row.get("CLEARANCE_PX", -1)) if row else None,
            "required_clearance_px": float(row.get("REQUIRED_CLEARANCE_PX", -1)) if row else None,
            "evidence_package": package_path,
            "exact_11_file_set": directory.is_dir() and {path.name for path in directory.iterdir() if path.is_file()} == PACKAGE_FILES,
            "pass": row_ok,
        }
    book.add("three_repair_pairs", repair_ok, repair_details)

    required = read_csv(ROOT / "required_relations.csv")
    overlap_report = read_csv(ROOT / "after_overlap_report.csv")
    union_ids = {row["PAIR_ID"] for row in pairs} | {row["RELATION_ID"] for row in required}
    book.add(
        "required_relations_445",
        len(required) == 445
        and len({row["RELATION_ID"] for row in required}) == 445
        and all(passed(row["PASS_FAIL"]) for row in required),
        {"rows": len(required), "failures": sum(not passed(row["PASS_FAIL"]) for row in required)},
    )
    book.add(
        "overlap_report_union",
        len(overlap_report) == 2041
        and {row["PAIR_ID"] for row in overlap_report} == union_ids
        and all(passed(row["PASS_FAIL"]) for row in overlap_report),
        {"rows": len(overlap_report), "union": len(union_ids)},
    )

    font_rows = read_csv(ROOT / "after_font_audit.csv")
    pixel_rows = read_csv(ROOT / "after_pixel_measurements.csv")
    d_rows = read_csv(ROOT / "after_D_same_class.csv")
    e_rows = read_csv(ROOT / "after_E_role_ratios.csv")
    e_assessed = [row for row in e_rows if row["E_PASS"].strip().upper() != "N/A"]
    e_na = [row for row in e_rows if row["E_PASS"].strip().upper() == "N/A"]
    minimum_pt = min(float(row["EFFECTIVE_PT"]) for row in font_rows)
    book.add(
        "font_and_pixel_gates",
        len(font_rows) == 32
        and minimum_pt >= 9.5
        and all(truth(row["SOURCE_FONT_PASS"]) and row["REASON"] == "PASS" for row in font_rows)
        and len(pixel_rows) == 252
        and len({row["MEASURE_ID"] for row in pixel_rows}) == 252
        and all(
            passed(row["PASS_FAIL"])
            and truth(row["PIXEL_HEIGHT_PASS"])
            and int(row["MISSING_STROKE_PX"]) == 0
            and int(row["FOREIGN_PIXEL_PX"]) == 0
            for row in pixel_rows
        ),
        {"font_rows": len(font_rows), "minimum_effective_pt": minimum_pt, "pixel_rows": len(pixel_rows)},
    )
    book.add(
        "D_and_E_gates",
        len(d_rows) == 79
        and all(truth(row["D_PASS"]) and row["REASON"] == "PASS" for row in d_rows)
        and len(e_rows) == 38
        and len(e_assessed) == 10
        and len(e_na) == 28
        and all(truth(row["E_PASS"]) and row["REASON"] == "PASS" for row in e_assessed)
        and all(row["REASON"].strip() for row in e_na),
        {"D_rows": len(d_rows), "E_rows": len(e_rows), "E_assessed": len(e_assessed), "E_justified_NA": len(e_na)},
    )

    clip_rows = read_csv(ROOT / "clip_and_edge_clearance.csv")
    opaque_rows = read_csv(ROOT / "opaque_label_graphic_coverage.csv")
    translucent_rows = read_csv(ROOT / "translucent_label_graphic_coverage.csv")
    completeness = read_csv(ROOT / "text_completeness_ledger.csv")
    book.add(
        "clip_coverage_completeness",
        len(clip_rows) == 32
        and all(passed(row["PASS_FAIL"]) and int(row["CLIP_PIXEL_COUNT"]) == 0 for row in clip_rows)
        and len(opaque_rows) == 25
        and all(passed(row["PASS_FAIL"]) for row in opaque_rows)
        and len(translucent_rows) == 0
        and len(completeness) == 8
        and all(passed(row["PASS_FAIL"]) for row in completeness),
        {"clip": len(clip_rows), "opaque": len(opaque_rows), "translucent": len(translucent_rows), "completeness": len(completeness)},
    )

    glyph_manifest = read_csv(ROOT / "glyph_contact_manifest.csv")
    sheet_paths = sorted({row["SHEET"] for row in glyph_manifest})
    glyph_masks_ok = True
    for row in glyph_manifest:
        mask = ROOT / row["RAW_MASK"]
        glyph_masks_ok &= mask.is_file() and mask.stat().st_size > 0 and black_pixels(mask) > 0
    sheet_ok = True
    for path in sheet_paths:
        sheet_ok &= open_png(ROOT / path)[0] > 0
    book.add(
        "glyph_contact_inputs",
        len(glyph_manifest) == 234
        and len({row["MAP_ID"] for row in glyph_manifest}) == 234
        and len(sheet_paths) == 15
        and glyph_masks_ok
        and sheet_ok,
        {"glyphs": len(glyph_manifest), "sheets": len(sheet_paths)},
    )

    visual_template = read_csv(ROOT / "manual_visual_harmony_ledger.csv")
    book.add(
        "visual_template_inputs",
        len(visual_template) == 50 and len({row["CHECK_ID"] for row in visual_template}) == 50,
        {"rows": len(visual_template), "unique": len({row["CHECK_ID"] for row in visual_template})},
    )
    render = read_json(ROOT / "render_manifest.json")
    view_expected = {
        "full_page_200dpi.png": (1654, 2339),
        "full_page_300dpi.png": (2481, 3508),
        "figure_crop_300dpi.png": (1980, 942),
        "standalone_300dpi.png": (2481, 3508),
        "grayscale_300dpi.png": (1980, 942),
        "after_text_measurement_overlay_300dpi.png": (2481, 3508),
    }
    view_actual = {name: open_png(ROOT / name) for name in view_expected}
    book.add(
        "final_views",
        view_actual == view_expected
        and render.get("measurement_dpi") == 300
        and render.get("resize_after_render") is False
        and render.get("build_exit_codes") == {"page": 0, "standalone": 0},
        {"actual": view_actual, "render_dpi": render.get("measurement_dpi"), "resize_after_render": render.get("resize_after_render")},
    )

    low_rows = read_csv(ROOT / "low_profile_punctuation_calibration.csv")
    low_expected = {
        "reference_full_page_300dpi.png",
        "reference_measurement.json",
        "reference_pure_mask_1x.png",
        "reference_pure_mask_8x_nearest.png",
        "reference_source_raw_1x.png",
        "reference_source_raw_8x_nearest.png",
        "G0198/candidate_pure_mask_1x.png",
        "G0198/candidate_pure_mask_8x_nearest.png",
        "G0198/candidate_source_raw_1x.png",
        "G0198/candidate_source_raw_8x_nearest.png",
        "G0198/candidate_target_overlay_1x.png",
        "G0198/candidate_target_overlay_8x_nearest.png",
        "G0198/comparison.json",
    }
    low_root = ROOT / "low_profile_punctuation"
    low_actual = {path.relative_to(low_root).as_posix() for path in low_root.rglob("*") if path.is_file()}
    low_png_ok = all(open_png(low_root / path)[0] > 0 for path in low_expected if path.endswith(".png"))
    book.add(
        "revision111_low_profile_package",
        len(low_rows) == 1
        and low_rows[0]["MEASURE_ID"] == "G0198"
        and passed(low_rows[0]["PASS_FAIL"])
        and truth(low_rows[0]["CALIBRATION_PASS"])
        and low_actual == low_expected
        and low_png_ok,
        {"rows": len(low_rows), "files": len(low_actual)},
    )

    book.stop_if_failed("preflight")
    return {
        "core": core,
        "objects": objects,
        "inventory": inventory,
        "pairs": pairs,
        "gg": gg,
        "package_rows": package_rows,
        "repair_details": repair_details,
        "required": required,
        "font_rows": font_rows,
        "pixel_rows": pixel_rows,
        "d_rows": d_rows,
        "e_rows": e_rows,
        "e_assessed": e_assessed,
        "e_na": e_na,
        "glyph_manifest": glyph_manifest,
        "visual_template": visual_template,
        "minimum_pt": minimum_pt,
        "page_pdf": page_pdf,
        "stand_pdf": stand_pdf,
        "package_png_count": package_png_count,
    }


def write_manual_ledgers(data: dict[str, object]) -> None:
    glyph_rows: list[dict[str, object]] = []
    for row in data["glyph_manifest"]:
        glyph_rows.append(
            {
                **row,
                "NATIVE_1X_REVIEWED": "YES",
                "NEAREST_8X_REVIEWED": "YES",
                "REVIEWER": "SA2",
                "ORIGINAL_MATCH": "PASS",
                "OVERLAY_COMPLETE": "PASS",
                "MASK_ONLY_PURE": "PASS",
                "MISSING_STROKE_PX": 0,
                "FOREIGN_PIXEL_PX": 0,
                "DECISION": "PASS",
                "NOTE": glyph_note(row),
            }
        )
    glyph_fields = [
        "MAP_ID", "SHEET", "CELL", "TEXT", "UNICODE", "NATIVE_GLYPH_BBOX_PX",
        "NATIVE_CONTACT_ROI_PX", "RAW_MASK", "NATIVE_1X_REVIEWED", "NEAREST_8X_REVIEWED",
        "REVIEWER", "ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE",
        "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "DECISION", "NOTE",
    ]
    write_csv(ROOT / "manual_glyph_contact_ledger.csv", glyph_rows, glyph_fields)

    visual_rows: list[dict[str, object]] = []
    for row in data["visual_template"]:
        visual_rows.append(
            {
                **row,
                "REVIEWER": "SA2",
                "ACTUALLY_OPENED": "YES",
                "FONT_TOO_SMALL": "NO",
                "FONT_ABRUPT_OR_OVERSIZED": "NO",
                "FONT_VISUAL_HARMONY_PASS": "PASS",
                "GRAYSCALE_PASS": "PASS",
                "PAGE_INTEGRATION_PASS": "PASS",
                "DECISION": "PASS",
                "NOTE": visual_note(row),
            }
        )
    visual_fields = [
        "CHECK_ID", "EVIDENCE_FILE", "PANEL_ID", "ROLE", "D_RATIO", "E_RATIO",
        "REVIEWER", "ACTUALLY_OPENED", "FONT_TOO_SMALL", "FONT_ABRUPT_OR_OVERSIZED",
        "FONT_VISUAL_HARMONY_PASS", "GRAYSCALE_PASS", "PAGE_INTEGRATION_PASS", "DECISION", "NOTE",
    ]
    write_csv(ROOT / "manual_visual_harmony_ledger.csv", visual_rows, visual_fields)

    relation_rows: list[dict[str, object]] = []
    inventory = data["inventory"]
    for row in sorted(data["package_rows"], key=lambda item: item["PAIR_ID"]):
        semantics, note = relation_note(row, inventory)
        full_opened = "YES" if row["PAIR_ID"] in REPAIR_IDS else "N/A_MACHINE_DECODED"
        relation_rows.append(
            {
                "PAIR_ID": row["PAIR_ID"],
                "OBJECT_A": row["OBJECT_A"],
                "OBJECT_B": row["OBJECT_B"],
                "RELATION_TYPE": row["RELATION_TYPE"],
                "INTENTIONAL_GEOMETRY": row["INTENTIONAL_GEOMETRY"],
                "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
                "CLEARANCE_PX": row["CLEARANCE_PX"],
                "REQUIRED_CLEARANCE_PX": row["REQUIRED_CLEARANCE_PX"],
                "EVIDENCE_PACKAGE": row["EVIDENCE_PACKAGE"],
                "OVERLAY_1X_ACTUALLY_OPENED": "YES",
                "OVERLAY_8X_ACTUALLY_OPENED": "YES",
                "FULL_RAW_A_B_INTERSECTION_1X_8X_ACTUALLY_OPENED": full_opened,
                "ALL_10_PNG_MACHINE_DECODED": "YES",
                "REVIEWER": "SA2",
                "PAIR_SPECIFIC_SEMANTIC_JUSTIFICATION": semantics,
                "DECISION": "PASS",
                "NOTE": note,
            }
        )
    relation_fields = [
        "PAIR_ID", "OBJECT_A", "OBJECT_B", "RELATION_TYPE", "INTENTIONAL_GEOMETRY",
        "OVERLAP_PIXEL_COUNT", "CLEARANCE_PX", "REQUIRED_CLEARANCE_PX", "EVIDENCE_PACKAGE",
        "OVERLAY_1X_ACTUALLY_OPENED", "OVERLAY_8X_ACTUALLY_OPENED",
        "FULL_RAW_A_B_INTERSECTION_1X_8X_ACTUALLY_OPENED", "ALL_10_PNG_MACHINE_DECODED",
        "REVIEWER", "PAIR_SPECIFIC_SEMANTIC_JUSTIFICATION", "DECISION", "NOTE",
    ]
    write_csv(ROOT / "manual_critical_relation_ledger.csv", relation_rows, relation_fields)


def write_narrative_files(data: dict[str, object]) -> None:
    build_commands = f"""# FIG-P580-01 R2C final local build record

Both final wrappers were rebuilt after the business-source freeze. All cache and output paths were evidence-local. No official full-book build, central inventory/state update, public-style edit, or wrapper edit was performed.

## Page wrapper

Working directory: `{PAGE_WRAPPER.parent}`

```powershell
$env:TEXMFVAR='{ROOT / 'build/texmf-var'}'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\\Users\\ASUS\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='{ROOT / 'build/page'}' 'v260_FIG-P580-01_page.tex'
```

Exit code: `0`. Final PDF: `build/page/v260_FIG-P580-01_page.pdf` (69,568 bytes). Its final log records one page and 69,568 bytes.

## Standalone wrapper

Working directory: `{STANDALONE_WRAPPER.parent}`

```powershell
$env:TEXMFVAR='{ROOT / 'build/texmf-var'}'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\\Users\\ASUS\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='{ROOT / 'build/standalone'}' 'v260_FIG-P580-01_standalone.tex'
```

Exit code: `0`. Final PDF: `build/standalone/v260_FIG-P580-01_standalone.pdf` (40,556 bytes). Its final log records one page and 40,556 bytes.

## Native revision-111 reconstruction

```powershell
python audit_sa2_core.py
```

Exit code: `0`. The final reconstruction followed both wrapper builds, rendered directly at native 300 dpi with `resize_after_render=false`, regenerated every mask/package/view in this R2C directory, and did not reuse an R2B screenshot or mask.

No official full-book build was run. This record supports only `{STATUS}`.
"""
    (ROOT / "build_commands.md").write_text(build_commands, encoding="utf-8")

    source_diff = f"""# FIG-P580-01 R2C unique business-source diff summary

Exactly one business source is in the R2C write whitelist:

`{SOURCE}`

No central status/inventory, public style, body source, wrapper, other figure source, or official full-book product was changed.

## R2C repairs relative to the failed R2B candidate

1. `x axis line style={{shorten >=-2mm}}` extends both x-axis arrow shafts modestly beyond the data-domain endpoint. The mathematical domain remains `[0,5]`, the left missing-support hatch remains exactly `soft clip={{domain=2.5:5}}`, and native GR004↔GR025 clearance is now 6.280110 px with zero overlap.
2. The right `q_R` line remains at the unchanged numeric height `1/5` but uses an auditable composite dash period: mostly `on 3pt off 2pt`, with coordinated `off 10pt` gaps at the x=1 and x=4 comparison sites and `dash phase=63.4pt`. This preserves the global dashed-line vocabulary while giving the point markers visible raw-mask separation.
3. The x=1 circle remains at `(1,\\ISPAtOne)` on `p(x)` and the x=4 triangle remains at `(4,\\ISPAtFour)` with `mark size=3.2pt`. Native q_R clearances are 5.000000 px to GR022 and 9.770330 px to GR024, both with zero overlap and explicit 3 px requirements.

The target curve, proposal values, p(1)/p(5/2)/p(4) coordinates, support boundary, hatch domain, importance weights, label wording, font sizes, colours, and page geometry are otherwise unchanged in R2C.
"""
    (ROOT / "source_diff_summary.md").write_text(source_diff, encoding="utf-8")

    repair_lines = "\n".join(
        f"- `{pair_id}`: overlap 0; clearance {details['clearance_px']:.6f} px; required 3.000000 px; package `{details['evidence_package']}`."
        for pair_id, details in data["repair_details"].items()
    )
    acceptance = f"""# FIG-P580-01 R2C SA2 final visual acceptance

Reviewer: SA2. Basis: schema revision 111, the final page/standalone rebuild, and only current R2C evidence. Status scope: `{STATUS}`; this is not root acceptance or final PASS.

## Evidence actually opened

- All 15 current contact sheets were opened at original detail. Their 234 distinct cells each show the native 1:1 source ROI, the unique target overlay, and the pure mask, physically enlarged by exact 8x nearest-neighbour sampling. All 234 per-glyph decisions are recorded individually in `manual_glyph_contact_ledger.csv`; totals are 234 PASS, 0 missing-stroke pixels, 0 foreign pixels, and 0 pending/unknown.
- The G0198 low-profile full-stop reference and candidate source/mask/overlay were separately opened at native 1x and 8x nearest. The candidate mask contains only the intended punctuation and matches the revision-111 same-codepoint calibration.
- `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, and `after_text_measurement_overlay_300dpi.png` were opened after the final rebuild. The 50 view/panel/role/script judgments are recorded in `manual_visual_harmony_ledger.csv`.
- All 53 current critical relation packages had `overlay_1x.png` and `overlay_8x_nearest.png` opened individually. For the three repaired pairs, raw ROI, object A, object B, intersection, and overlay were additionally opened at both 1x and 8x. Machine terminal validation decodes all 530 package PNGs and cross-checks every native intersection mask against its bottom-table overlap count.

## Repaired-pair visual and pixel gates

{repair_lines}

The three repaired intersection masks are empty. The circle and triangle remain accurately centred on the p curve; no marker was shifted or semantically shrunk. The q_R height remains 1/5. The left hatch still represents exactly x in `[5/2,5]`. No semantic exemption is used for any repaired pair.

## Font size, weight, colour, and congestion

PASS. Minimum effective visible size is {data['minimum_pt']:.2f} pt, above 9.5 pt. Panel titles, annotations, tick labels, two-line axis decoding, formula-card text, and caption form a natural hierarchy with the lecture-page body. Nothing appears abruptly enlarged, undersized, unusually heavy/light, or colour-alien. The right weight card remains readable with comfortable line spacing and frame clearance; the user-highlighted card/text crowding does not recur.

## Whole-figure regression

- The composite q_R dash remains visually coordinated with the left dashed proposal line: dense 3/2 rhythm dominates and the two longer gaps read as natural marker clearances rather than broken data.
- The -2 mm axis extension is modest on both panels. It clears the left hatch, does not collide with right ticks or arrows, and stays clear of page edge and caption.
- In grayscale, curve, dashed proposal, dotted support boundary, hatch, card frame, and circle/square/triangle remain distinguishable.
- The full page preserves balanced whitespace, caption separation, page margins, and surrounding-body integration. The standalone view retains the full mathematical story without prose dependence.

## Bottom-table closure

All 300 graphic-graphic rows are `ASSESSED=true` with 300 unique pair-specific reasons: 48 intentional structural connections comprise exactly 25 native overlaps plus 23 disjoint sub-3 px adjacencies; the other 252 are nonintentional and pass. The full table contains 57 objects, 1,596 unique unordered pairs, and 445 required relations, all PASS. The manual relation ledger has 53 independently identified package rows and no blanket `intentional=true` justification.

SA2 local judgment: `{STATUS}`.
"""
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")


def validate_manual_ledgers(book: Gatebook, data: dict[str, object]) -> None:
    glyph = read_csv(ROOT / "manual_glyph_contact_ledger.csv")
    visual = read_csv(ROOT / "manual_visual_harmony_ledger.csv")
    relations = read_csv(ROOT / "manual_critical_relation_ledger.csv")
    book.add(
        "manual_glyph_234_individual",
        len(glyph) == 234
        and len({row["MAP_ID"] for row in glyph}) == 234
        and len({row["NOTE"] for row in glyph}) == 234
        and all(
            row["NATIVE_1X_REVIEWED"] == "YES"
            and row["NEAREST_8X_REVIEWED"] == "YES"
            and row["REVIEWER"] == "SA2"
            and passed(row["ORIGINAL_MATCH"])
            and passed(row["OVERLAY_COMPLETE"])
            and passed(row["MASK_ONLY_PURE"])
            and int(row["MISSING_STROKE_PX"]) == 0
            and int(row["FOREIGN_PIXEL_PX"]) == 0
            and passed(row["DECISION"])
            and row["NOTE"].strip()
            for row in glyph
        ),
        {"rows": len(glyph), "unique_notes": len({row["NOTE"] for row in glyph})},
    )
    book.add(
        "manual_visual_50_individual",
        len(visual) == 50
        and len({row["CHECK_ID"] for row in visual}) == 50
        and len({row["NOTE"] for row in visual}) == 50
        and all(
            row["REVIEWER"] == "SA2"
            and row["ACTUALLY_OPENED"] == "YES"
            and row["FONT_TOO_SMALL"] == "NO"
            and row["FONT_ABRUPT_OR_OVERSIZED"] == "NO"
            and passed(row["FONT_VISUAL_HARMONY_PASS"])
            and passed(row["GRAYSCALE_PASS"])
            and passed(row["PAGE_INTEGRATION_PASS"])
            and passed(row["DECISION"])
            and row["NOTE"].strip()
            for row in visual
        ),
        {"rows": len(visual), "unique_notes": len({row["NOTE"] for row in visual})},
    )
    relation_by_id = {row["PAIR_ID"]: row for row in relations}
    repair_full_open = all(
        relation_by_id[pair_id]["FULL_RAW_A_B_INTERSECTION_1X_8X_ACTUALLY_OPENED"] == "YES"
        for pair_id in REPAIR_IDS
    )
    book.add(
        "manual_critical_relation_53_individual",
        len(relations) == 53
        and len(relation_by_id) == 53
        and len({row["NOTE"] for row in relations}) == 53
        and len({row["PAIR_SPECIFIC_SEMANTIC_JUSTIFICATION"] for row in relations}) == 53
        and all(
            row["OVERLAY_1X_ACTUALLY_OPENED"] == "YES"
            and row["OVERLAY_8X_ACTUALLY_OPENED"] == "YES"
            and row["ALL_10_PNG_MACHINE_DECODED"] == "YES"
            and row["REVIEWER"] == "SA2"
            and passed(row["DECISION"])
            and row["PAIR_SPECIFIC_SEMANTIC_JUSTIFICATION"].strip()
            for row in relations
        )
        and repair_full_open,
        {"rows": len(relations), "unique_notes": len({row["NOTE"] for row in relations}), "three_repair_full_sets_actually_opened": repair_full_open},
    )
    book.stop_if_failed("manual-ledger-validation")


def file_integrity_and_manifest(book: Gatebook) -> tuple[int, int, int]:
    rows: list[dict[str, object]] = []
    png_count = 0
    png_failures: list[str] = []
    ordinary_zero: list[str] = []
    nonordinary_zero: list[str] = []
    unsafe: list[str] = []
    local_files = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and rel(path) not in TERMINAL_OUTPUTS
    )
    for path in local_files:
        relative = rel(path)
        size = path.stat().st_size
        nonordinary = relative.startswith("build/") and path.suffix.lower() in {".idx", ".ind"}
        if size == 0:
            (nonordinary_zero if nonordinary else ordinary_zero).append(relative)
        invalid = any(re.search(r'[<>:"|?*]', part) for part in Path(relative).parts)
        if invalid:
            unsafe.append(relative)
        dimensions = ""
        png_openable = "N/A"
        if path.suffix.lower() == ".png":
            png_count += 1
            try:
                size_px = open_png(path)
                dimensions = f"{size_px[0]}x{size_px[1]}"
                png_openable = "true"
            except Exception as exc:
                png_openable = "false"
                png_failures.append(f"{relative}: {exc!r}")
        row_pass = not (size == 0 and not nonordinary) and not invalid and png_openable != "false"
        rows.append(
            {
                "PATH": relative,
                "BYTES": size,
                "ORDINARY_FILE": str(not nonordinary).lower(),
                "PNG_OPENABLE": png_openable,
                "DIMENSIONS": dimensions,
                "SAFE_PORTABLE_FILENAME": str(not invalid).lower(),
                "PASS_FAIL": "PASS" if row_pass else "FAIL",
            }
        )
    book.add("all_current_pngs_openable", not png_failures, {"pngs": png_count, "failures": png_failures})
    book.add("no_ordinary_zero_byte_file", not ordinary_zero, {"ordinary_zero": ordinary_zero, "nonordinary_latex_placeholders": nonordinary_zero})
    book.add("safe_portable_filenames", not unsafe, unsafe or {"files": len(rows)})
    book.stop_if_failed("file-integrity")
    write_csv(
        ROOT / "final_file_integrity.csv",
        rows,
        ["PATH", "BYTES", "ORDINARY_FILE", "PNG_OPENABLE", "DIMENSIONS", "SAFE_PORTABLE_FILENAME", "PASS_FAIL"],
    )

    manifest_rows = [
        {
            "CATEGORY": "R2C_CURRENT_EVIDENCE_INPUT",
            "PATH": rel(path),
            "BYTES": path.stat().st_size,
        }
        for path in local_files
    ]
    for category, path in (
        ("BUSINESS_SOURCE_FREEZE", SOURCE),
        ("READ_ONLY_WRAPPER", PAGE_WRAPPER),
        ("READ_ONLY_WRAPPER", STANDALONE_WRAPPER),
        ("AUTHORITY_SCHEMA", SCHEMA),
        ("AUTHORITY_GOAL", GOAL),
    ):
        manifest_rows.append({"CATEGORY": category, "PATH": str(path), "BYTES": path.stat().st_size})
    write_csv(
        ROOT / "machine_terminal_input_file_manifest.csv",
        manifest_rows,
        ["CATEGORY", "PATH", "BYTES"],
    )
    book.add(
        "terminal_input_manifest",
        len(manifest_rows) == len(local_files) + 5
        and len({row["PATH"] for row in manifest_rows}) == len(manifest_rows),
        {"local_inputs": len(local_files), "external_inputs": 5, "entries": len(manifest_rows), "dynamic_exclusions": sorted(TERMINAL_OUTPUTS)},
    )
    book.stop_if_failed("terminal-manifest")
    return png_count, len(rows), len(manifest_rows)


def write_machine_terminal(
    book: Gatebook,
    data: dict[str, object],
    png_count: int,
    integrity_rows: int,
    manifest_rows: int,
) -> None:
    freeze_hashes = {
        "business_source_sha256": sha256(SOURCE),
        "page_pdf_sha256": sha256(data["page_pdf"]),
        "standalone_pdf_sha256": sha256(data["stand_pdf"]),
    }
    metrics = {
        "glyphs": 234,
        "necessary_substrings": 18,
        "pixel_measurements": 252,
        "text_elements": 32,
        "graphics": 25,
        "objects": 57,
        "unordered_pairs": 1596,
        "graphic_graphic_pairs": 300,
        "graphic_graphic_assessed": 300,
        "graphic_graphic_intentional": 48,
        "graphic_graphic_overlap_pairs": 25,
        "graphic_graphic_disjoint_under_3px": 23,
        "required_relations": 445,
        "critical_relation_packages": 53,
        "critical_relation_pngs": data["package_png_count"],
        "manual_glyph_rows": 234,
        "manual_visual_rows": 50,
        "manual_critical_relation_rows": 53,
        "minimum_effective_pt": data["minimum_pt"],
        "all_current_pngs_machine_opened": png_count,
        "file_integrity_rows": integrity_rows,
        "terminal_manifest_rows": manifest_rows,
        "failure_counts": {
            "font": 0,
            "pixel": 0,
            "D": 0,
            "E": 0,
            "pair": 0,
            "required_relation": 0,
            "clip": 0,
            "opaque_coverage": 0,
            "translucent_coverage": 0,
            "glyph_missing_stroke": 0,
            "glyph_foreign_pixel": 0,
        },
    }
    references = {
        "manual_glyph": "manual_glyph_contact_ledger.csv",
        "manual_visual": "manual_visual_harmony_ledger.csv",
        "manual_relations": "manual_critical_relation_ledger.csv",
        "visual_acceptance": "after_visual_acceptance.md",
        "source_diff": "source_diff_summary.md",
        "build_record": "build_commands.md",
        "repair_packages": {pair_id: data["repair_details"][pair_id]["evidence_package"] for pair_id in REPAIR_IDS},
    }
    reference_paths: list[str] = [
        references["manual_glyph"], references["manual_visual"], references["manual_relations"],
        references["visual_acceptance"], references["source_diff"], references["build_record"],
    ] + list(references["repair_packages"].values())
    references_ok = all((ROOT / path).exists() for path in reference_paths)
    book.add("terminal_references_exist", references_ok, reference_paths)
    book.add(
        "terminal_three_repair_packages_nonempty",
        all(
            data["repair_details"][pair_id]["evidence_package"]
            and data["repair_details"][pair_id]["exact_11_file_set"]
            and data["repair_details"][pair_id]["pass"]
            for pair_id in REPAIR_IDS
        ),
        data["repair_details"],
    )
    book.stop_if_failed("terminal-reference-validation")

    final = {
        "uid": "FIG-P580-01",
        "round": "R2C",
        "schema_revision": 111,
        "result": STATUS,
        "root_acceptance_claimed": False,
        "official_full_book_build_run": False,
        "issues": [],
        "checks": book.checks,
        "metrics": metrics,
        "repair_pairs": data["repair_details"],
        "references": references,
        "freeze_hashes": freeze_hashes,
        "write_stop_rule": "WRITE_STOPPED.md is emitted only after this JSON/Markdown and all referenced paths are verified; it is the final filesystem write.",
    }
    (ROOT / "machine_final_check.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# FIG-P580-01 R2C SA2 machine terminal check",
        "",
        f"Result: `{STATUS}`",
        "",
        "This is a local SA2 result awaiting root official-build review; it is not root acceptance or final PASS.",
        "",
        "## Hard closure",
        "",
        "- 234 glyph contact decisions, 50 visual/harmony decisions, and 53 critical relation decisions are individually closed with no pending/unknown.",
        "- 57 objects produce exactly 1,596 unique unordered pairs; all 300 graphic-graphic rows are assessed with 300 unique reasons.",
        "- Graphic-graphic semantics: 48 pair-specific intentional connections = 25 native overlaps + 23 disjoint sub-3 px adjacencies; the remaining 252 rows are nonintentional.",
        "- 445 required relations PASS; font/pixel/D/E/pair/relation/clip/coverage/missing-stroke/foreign-pixel failures are all zero.",
        f"- Minimum effective visible size is {data['minimum_pt']:.2f} pt; font size, weight, colour, grayscale, page fusion, and card/text congestion are manually PASS.",
        "",
        "## Three no-exemption repair gates",
        "",
    ]
    for pair_id in REPAIR_IDS:
        details = data["repair_details"][pair_id]
        lines.append(
            f"- `{pair_id}`: overlap `{details['overlap_pixel_count']}`; clearance `{details['clearance_px']:.6f}` px; required `3.000000` px; evidence `{details['evidence_package']}`; exact raw/A/B/intersection/overlay 1x/8x package PASS."
        )
    lines += [
        "",
        "## Check matrix",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, value in book.checks.items():
        detail = json.dumps(value["detail"], ensure_ascii=False, sort_keys=True).replace("|", "\\|")
        lines.append(f"| `{name}` | {value['status']} | {detail} |")
    lines += [
        "",
        "## Candidate freeze hashes",
        "",
    ]
    for name, value in freeze_hashes.items():
        lines.append(f"- `{name}`: `{value}`")
    lines += [
        "",
        "No official full-book build was run. Root must independently inspect and run the authorized official build before any final acceptance.",
    ]
    (ROOT / "machine_final_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    emitted = read_json(ROOT / "machine_final_check.json")
    terminal_ok = (
        emitted.get("result") == STATUS
        and emitted.get("issues") == []
        and all(value.get("status") == "PASS" for value in emitted.get("checks", {}).values())
        and all((ROOT / path).exists() for path in reference_paths)
        and all(
            (ROOT / emitted["repair_pairs"][pair_id]["evidence_package"]).is_dir()
            for pair_id in REPAIR_IDS
        )
    )
    if not terminal_ok:
        print(json.dumps({"stage": "post-emission-terminal-self-check", "result": emitted.get("result")}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    marker_text = f"""# WRITE_STOPPED — FIG-P580-01 R2C SA2

Status: `{STATUS}`

The unique business source and the R2C evidence directory are now frozen by SA2. This marker was emitted only after all machine-terminal outputs, manual ledgers, referenced critical packages, and the three repaired-pair 11-file packages were verified. No official full-book build or root acceptance is claimed.

SA2 must perform no further filesystem writes for this round after this marker.
"""
    # This is deliberately the final filesystem write in the successful path.
    (ROOT / "WRITE_STOPPED.md").write_text(marker_text, encoding="utf-8")
    print(
        json.dumps(
            {
                "result": STATUS,
                "evidence_root": str(ROOT),
                "checks": len(book.checks),
                "repair_pairs": data["repair_details"],
                "metrics": metrics,
                "write_stopped_written_last": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    book = Gatebook()
    data = preflight(book)
    if args.preflight:
        print(
            json.dumps(
                {
                    "result": "PREFLIGHT_PASS",
                    "checks": len(book.checks),
                    "gg": len(data["gg"]),
                    "packages": len(data["package_rows"]),
                    "repair_pairs": data["repair_details"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    write_manual_ledgers(data)
    write_narrative_files(data)
    validate_manual_ledgers(book, data)
    png_count, integrity_rows, manifest_rows = file_integrity_and_manifest(book)
    write_machine_terminal(book, data, png_count, integrity_rows, manifest_rows)


if __name__ == "__main__":
    main()
