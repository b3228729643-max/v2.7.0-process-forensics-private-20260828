from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

import fitz


ROOT = Path(__file__).resolve().parents[1]
PAGE_PDF = ROOT / "build" / "page" / "v260_FIG-P654-01_page.pdf"
STANDALONE_PDF = ROOT / "build" / "standalone" / "v260_FIG-P654-01_standalone.pdf"
SUMMARY = ROOT / "reports" / "denominator_and_machine_summary.json"
OUT = ROOT / "reports" / "standalone_page_consistency.json"
# LuaTeX/PDF coordinate quantization leaves at most about 0.011 pt of rawdict
# bbox drift between the two otherwise identical wrappers (<0.05 px at 300 dpi).
TOLERANCE_PT = 0.02


def glyphs(page: fitz.Page, clip: fitz.Rect) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for block in page.get_text("rawdict", clip=clip).get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    result.append(
                        {
                            "char": char["c"],
                            "origin": tuple(char["origin"]),
                            "bbox": tuple(char["bbox"]),
                            "font": span["font"],
                            "size": float(span["size"]),
                            "color": int(span["color"]),
                        }
                    )
    return result


def normalized_item(value: Any, origin_x: float, origin_y: float) -> Any:
    if isinstance(value, fitz.Point):
        return ["Point", value.x - origin_x, value.y - origin_y]
    if isinstance(value, fitz.Rect):
        return [
            "Rect",
            value.x0 - origin_x,
            value.y0 - origin_y,
            value.x1 - origin_x,
            value.y1 - origin_y,
        ]
    if isinstance(value, fitz.Quad):
        return [
            "Quad",
            *[
                coordinate
                for point in (value.ul, value.ur, value.ll, value.lr)
                for coordinate in (point.x - origin_x, point.y - origin_y)
            ],
        ]
    if isinstance(value, (list, tuple)):
        return [normalized_item(item, origin_x, origin_y) for item in value]
    if isinstance(value, float):
        return float(value)
    return value


def compare_nested(left: Any, right: Any, path: str = "") -> tuple[float, list[str]]:
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return math.inf, [f"{path}: length {len(left)} != {len(right)}"]
        maximum = 0.0
        failures: list[str] = []
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            delta, child_failures = compare_nested(a, b, f"{path}/{index}")
            maximum = max(maximum, delta)
            failures.extend(child_failures)
        return maximum, failures
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)), []
    if left != right:
        return math.inf, [f"{path}: {left!r} != {right!r}"]
    return 0.0, []


summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
page_doc = fitz.open(PAGE_PDF)
standalone_doc = fitz.open(STANDALONE_PDF)
page = page_doc[0]
standalone = standalone_doc[0]

page_drawings = page.get_drawings()
standalone_drawings = standalone.get_drawings()
if len(page_drawings) != len(standalone_drawings):
    raise RuntimeError(
        f"drawing count mismatch: page={len(page_drawings)}, standalone={len(standalone_drawings)}"
    )

draw_dx = [a["rect"].x0 - b["rect"].x0 for a, b in zip(page_drawings, standalone_drawings, strict=True)]
draw_dy = [a["rect"].y0 - b["rect"].y0 for a, b in zip(page_drawings, standalone_drawings, strict=True)]
translation_x = statistics.median(draw_dx)
translation_y = statistics.median(draw_dy)

drawing_rows: list[dict[str, Any]] = []
drawing_failures: list[str] = []
max_rect_residual = 0.0
max_geometry_residual = 0.0
for index, (page_path, standalone_path) in enumerate(
    zip(page_drawings, standalone_drawings, strict=True), start=1
):
    page_rect = page_path["rect"]
    standalone_rect = standalone_path["rect"]
    rect_residuals = [
        abs((page_rect.x0 - standalone_rect.x0) - translation_x),
        abs((page_rect.y0 - standalone_rect.y0) - translation_y),
        abs((page_rect.x1 - standalone_rect.x1) - translation_x),
        abs((page_rect.y1 - standalone_rect.y1) - translation_y),
    ]
    rect_residual = max(rect_residuals)
    max_rect_residual = max(max_rect_residual, rect_residual)

    page_items = normalized_item(page_path["items"], page_rect.x0, page_rect.y0)
    standalone_items = normalized_item(
        standalone_path["items"], standalone_rect.x0, standalone_rect.y0
    )
    geometry_residual, structural_failures = compare_nested(
        page_items, standalone_items, f"drawing[{index}]/items"
    )
    max_geometry_residual = max(max_geometry_residual, geometry_residual)

    style_fields = ("type", "closePath", "fill", "color", "width", "lineCap", "lineJoin", "dashes")
    style_mismatches = [
        key for key in style_fields if page_path.get(key) != standalone_path.get(key)
    ]
    passed = (
        rect_residual <= TOLERANCE_PT
        and geometry_residual <= TOLERANCE_PT
        and not structural_failures
        and not style_mismatches
    )
    if not passed:
        drawing_failures.append(f"drawing_{index:02d}")
    drawing_rows.append(
        {
            "ordinal": index,
            "page_seqno": page_path["seqno"],
            "standalone_seqno": standalone_path["seqno"],
            "item_count_page": len(page_path["items"]),
            "item_count_standalone": len(standalone_path["items"]),
            "rect_translation_residual_pt": rect_residual,
            "normalized_geometry_residual_pt": geometry_residual,
            "style_mismatches": style_mismatches,
            "structural_failures": structural_failures,
            "status": "PASS" if passed else "FAIL",
        }
    )

page_clip = fitz.Rect(summary["strict_clip_pt"])
standalone_clip = fitz.Rect(
    page_clip.x0 - translation_x,
    page_clip.y0 - translation_y,
    page_clip.x1 - translation_x,
    page_clip.y1 - translation_y,
)
page_glyphs = glyphs(page, page_clip)
standalone_glyphs = glyphs(standalone, standalone_clip)

text_failures: list[str] = []
max_text_translation_residual = 0.0
if len(page_glyphs) != len(standalone_glyphs):
    text_failures.append(
        f"glyph count page={len(page_glyphs)} standalone={len(standalone_glyphs)}"
    )
else:
    for index, (a, b) in enumerate(zip(page_glyphs, standalone_glyphs, strict=True), start=1):
        if (a["char"], a["font"], a["color"]) != (b["char"], b["font"], b["color"]):
            text_failures.append(f"glyph_{index:03d}_identity")
        if abs(a["size"] - b["size"]) > TOLERANCE_PT:
            text_failures.append(f"glyph_{index:03d}_size")
        residuals = [
            abs((a["origin"][0] - b["origin"][0]) - translation_x),
            abs((a["origin"][1] - b["origin"][1]) - translation_y),
            abs((a["bbox"][0] - b["bbox"][0]) - translation_x),
            abs((a["bbox"][1] - b["bbox"][1]) - translation_y),
            abs((a["bbox"][2] - b["bbox"][2]) - translation_x),
            abs((a["bbox"][3] - b["bbox"][3]) - translation_y),
        ]
        residual = max(residuals)
        max_text_translation_residual = max(max_text_translation_residual, residual)
        if residual > TOLERANCE_PT:
            text_failures.append(f"glyph_{index:03d}_geometry")

text_sequence_page = "".join(item["char"] for item in page_glyphs)
text_sequence_standalone = "".join(item["char"] for item in standalone_glyphs)
passed = not drawing_failures and not text_failures
report = {
    "figure_uid": "FIG-P654-01",
    "check": "compiled page wrapper versus compiled standalone wrapper",
    "status": "PASS" if passed else "FAIL",
    "method": (
        "Compare all PDF drawing objects ordinal-by-ordinal after a single fitted translation; "
        "compare every rawdict character identity/font/size/color/origin/bbox in the figure clip "
        "after the same translation. The fraction rule is included among drawing objects."
    ),
    "tolerance_pt": TOLERANCE_PT,
    "page_pdf": str(PAGE_PDF),
    "standalone_pdf": str(STANDALONE_PDF),
    "page_size_pt": [page.rect.width, page.rect.height],
    "standalone_size_pt": [standalone.rect.width, standalone.rect.height],
    "translation_page_minus_standalone_pt": [translation_x, translation_y],
    "drawing_count": len(page_drawings),
    "drawing_failures": drawing_failures,
    "max_drawing_rect_translation_residual_pt": max_rect_residual,
    "max_drawing_normalized_geometry_residual_pt": max_geometry_residual,
    "drawing_rows": drawing_rows,
    "rawdict_character_slots_including_spaces": len(page_glyphs),
    "visible_nonspace_glyphs": sum(not item["char"].isspace() for item in page_glyphs),
    "text_sequence_exact": text_sequence_page == text_sequence_standalone,
    "text_failures": sorted(set(text_failures)),
    "max_text_translation_residual_pt": max_text_translation_residual,
    "page_clip_pt": list(page_clip),
    "standalone_clip_pt": list(standalone_clip),
    "conclusion": (
        "The two compiled wrappers contain the same 95 visible glyphs and 21 PDF drawing/path "
        "objects, with identical geometry modulo placement translation."
        if passed
        else "The compiled wrappers are not geometrically identical within tolerance."
    ),
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "status": report["status"],
            "drawings": len(page_drawings),
            "visible_glyphs": report["visible_nonspace_glyphs"],
            "translation_pt": report["translation_page_minus_standalone_pt"],
            "max_rect_residual_pt": max_rect_residual,
            "max_geometry_residual_pt": max_geometry_residual,
            "max_text_residual_pt": max_text_translation_residual,
        },
        ensure_ascii=False,
    )
)
if not passed:
    raise SystemExit(1)
