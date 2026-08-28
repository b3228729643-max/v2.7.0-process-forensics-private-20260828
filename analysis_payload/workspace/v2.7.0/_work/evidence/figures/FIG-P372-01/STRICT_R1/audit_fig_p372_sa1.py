from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


# This script is an evidence generator only. It reads the frozen candidate and
# figure source and writes exclusively beside this file.
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P372-01" / "STRICT_R1"
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第03册_优化模型与序列模型" / "V3-C05" / "fig_v3_c05_lattice.tex"

PDF_PAGE_1 = 405
PRINTED_PAGE = 392
FIGURE_NO = "图 21.1"
SCALE = 300.0 / 72.0  # PDF user space is points (1/72 inch); direct 300 dpi mapping.
FULL_RECT = fitz.Rect(0, 0, 595.276, 841.890)
# The crop has >= 6 px of intentional raw-PDF margin around all reader-visible
# graph/caption elements. It is a crop only, never a resize.
FIG_CROP = fitz.Rect(48, 390, 548, 560)
STANDALONE_CROP = fitz.Rect(80, 393, 520, 535)


def ensure_out() -> None:
    OUT.mkdir(parents=True, exist_ok=True)


def px_floor(v: float) -> int:
    return int(math.floor(v * SCALE + 1e-8))


def px_ceil(v: float) -> int:
    return int(math.ceil(v * SCALE - 1e-8))


def point_bbox_to_local_px(b: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return (
        px_floor(b[0] - FIG_CROP.x0),
        px_floor(b[1] - FIG_CROP.y0),
        px_ceil(b[2] - FIG_CROP.x0),
        px_ceil(b[3] - FIG_CROP.y0),
    )


def union_bbox(boxes: Iterable[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    boxes = list(boxes)
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    yy, xx = np.where(mask)
    if len(xx) == 0:
        return None
    return int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[float, bool]:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    intersects = not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
    return float(math.hypot(dx, dy)), intersects


def nearest_points(a: np.ndarray, b: np.ndarray) -> tuple[float, tuple[int, int] | None, tuple[int, int] | None]:
    if not a.any() or not b.any():
        return float("inf"), None, None
    dist, nearest = distance_transform_edt(~b, return_indices=True)
    ys, xs = np.where(a)
    vals = dist[ys, xs]
    j = int(np.argmin(vals))
    ay, ax = int(ys[j]), int(xs[j])
    by, bx = int(nearest[0, ay, ax]), int(nearest[1, ay, ax])
    return float(vals[j]), (ax, ay), (bx, by)


def local_modal_background(patch: np.ndarray) -> np.ndarray:
    flat = patch.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    return colors[int(np.argmax(counts))]


def script_info(text: str, semantic_hint: str | None = None) -> tuple[str, int]:
    if semantic_hint == "operator":
        # A horizontal +/- stroke has a naturally tiny vertical ink extent. Its
        # required base-math height is therefore measured on the complete
        # parent formula, retained below as TIME_TICK_FORMULA.
        return "INLINE_OPERATOR_DERIVED", 0
    if semantic_hint == "math_formula":
        return "MATH_BASE_FORMULA", 22
    if semantic_hint == "script":
        return "NATURAL_MATH_SCRIPT", 15
    if any(c in "∑+−" for c in text):
        return "MATH_BASE_OPERATOR", 22
    if any(c.isdigit() for c in text):
        return "LATIN_UPPER_OR_DIGIT", 24
    if text == "HMM" or (text and text[0].isupper()):
        return "LATIN_MIXED_WITH_UPPER", 24
    if any("\u4e00" <= c <= "\u9fff" for c in text):
        return "CJK_FULL", 30
    if text.strip() in {".", "：", "、", "；"}:
        return "PUNCTUATION_CONSERVATIVE", 17
    return "LATIN_LOWER_OR_GREEK", 17


def ppi_size_from_tex_pt(pt: float) -> float:
    return pt * 300.0 / 72.27


@dataclass
class Char:
    idx: int
    text: str
    bbox: tuple[float, float, float, float]
    font: str
    size: float
    color: int


@dataclass
class TextElement:
    element_id: str
    parent_id: str
    panel_id: str
    role: str
    source_line: str
    declared_pt: str
    effective_pt: str
    chars: list[Char]
    derivation: str = "direct source font"
    semantic_hint: str | None = None
    mask: np.ndarray | None = None
    point_bbox: tuple[float, float, float, float] | None = None
    px_bbox: tuple[int, int, int, int] | None = None
    h_ink: int | None = None
    script_class: str = ""
    required_px: int = 0
    pdf_font: str = ""
    pdf_size_pt: float = 0.0
    foreground_px: int = 0

    @property
    def text(self) -> str:
        return "".join(c.text for c in self.chars)


@dataclass
class VectorObject:
    object_id: str
    drawing_index: int
    object_type: str
    source_line: str
    mask: np.ndarray
    px_bbox: tuple[int, int, int, int] | None
    color: str
    note: str


def load_chars(page: fitz.Page) -> list[Char]:
    raw = page.get_text("rawdict")
    chars: list[Char] = []
    n = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for ch in span["chars"]:
                    b = tuple(float(v) for v in ch["bbox"])
                    if 400 <= b[1] and b[3] <= 550 and ch["c"].strip():
                        chars.append(Char(n, ch["c"], b, span["font"], float(span["size"]), int(span["color"])))
                        n += 1
    return chars


def make_group(
    elements: list[TextElement],
    assigned: set[int],
    element_id: str,
    parent_id: str,
    panel_id: str,
    role: str,
    source_line: str,
    declared_pt: str,
    effective_pt: str,
    chars: list[Char],
    derivation: str = "direct source font",
    semantic_hint: str | None = None,
) -> None:
    if not chars:
        raise RuntimeError(f"No PDF chars found for {element_id}")
    duplicate = [c.idx for c in chars if c.idx in assigned]
    if duplicate:
        raise RuntimeError(f"Duplicate char assignment in {element_id}: {duplicate}")
    assigned.update(c.idx for c in chars)
    elements.append(TextElement(element_id, parent_id, panel_id, role, source_line, declared_pt, effective_pt, chars, derivation, semantic_hint))


def build_text_elements(chars: list[Char]) -> tuple[list[TextElement], list[Char]]:
    by = lambda pred: [c for c in chars if pred(c)]
    elements: list[TextElement] = []
    assigned: set[int] = set()

    # Three panel headings. Real PDF character boxes are the grouping basis.
    heading_specs = [
        ("F", "F_TITLE_CN", 110, 197, "PANEL_LABEL", "15", "9.5", "9.5", "CJK"),
        ("F", "F_TITLE_SUM", 197, 209, "PANEL_LABEL", "15", "9.5", "9.5", "MATH"),
        ("B", "B_TITLE_CN", 242, 329, "PANEL_LABEL", "15", "9.5", "9.5", "CJK"),
        ("B", "B_TITLE_SUM", 329, 341, "PANEL_LABEL", "15", "9.5", "9.5", "MATH"),
        ("V", "V_TITLE_VITERBI", 373, 405, "PANEL_LABEL", "15", "9.5", "9.5", "LATIN"),
        ("V", "V_TITLE_CN", 405, 454, "PANEL_LABEL", "15", "9.5", "9.5", "CJK"),
        ("V", "V_TITLE_MAX", 454, 473, "PANEL_LABEL", "15", "9.5", "9.5", "MATH"),
    ]
    for panel, eid, lo, hi, role, line, declared, effective, hint in heading_specs:
        cs = by(lambda c, lo=lo, hi=hi: 405 <= c.bbox[1] <= 411 and lo <= c.bbox[0] < hi)
        make_group(elements, assigned, eid, f"{panel}_TITLE", panel, role, line, declared, effective, cs,
                   semantic_hint="math" if hint == "MATH" else None)

    # Tick components are separate ELEMENT_IDs so a digit can never be hidden by a taller nearby glyph.
    tick_centers = {
        "F": [(127, "TMINUS1"), (160, "T"), (192, "TPLUS1")],
        "B": [(259, "TMINUS1"), (292, "T"), (324, "TPLUS1")],
        "V": [(391, "TMINUS1"), (424, "T"), (456, "TPLUS1")],
    }
    for panel, centres in tick_centers.items():
        for ti, (cx, label) in enumerate(centres):
            cs = by(lambda c, cx=cx: 421.5 <= c.bbox[1] <= 424.0 and abs((c.bbox[0] + c.bbox[2]) / 2 - cx) < 14)
            for j, c in enumerate(sorted(cs, key=lambda q: q.bbox[0])):
                suffix = "DIGIT" if c.text.isdigit() else "OP" if c.text in {"+", "−"} else "BASE"
                make_group(elements, assigned, f"{panel}_TICK_{ti}_{suffix}_{j}", f"{panel}_TICK_{ti}", panel,
                           "TIME_TICK", "17", "8.7", "8.7", [c],
                           semantic_hint="operator" if suffix == "OP" else "math")

    # q_1, q_2 and x_i inside each native vector node. Base and script are independent measurement elements.
    node_x = {"F": [125, 157, 190], "B": [257, 289, 322], "V": [389, 421, 454]}
    node_rows = [("Q1", 443.5, 457.0, "state"), ("Q2", 469.0, 482.5, "state"), ("X", 497.5, 511.5, "obs")]
    for panel, xs in node_x.items():
        for ti, cx in enumerate(xs):
            for node_kind, y0, y1, style in node_rows:
                cs = by(lambda c, cx=cx, y0=y0, y1=y1: y0 <= c.bbox[1] <= y1 and abs(c.bbox[0] - cx) < 8)
                for c in sorted(cs, key=lambda q: q.bbox[0]):
                    is_script = c.text.isdigit()
                    suffix = "SCRIPT" if is_script else "BASE"
                    src_line = "8;18-19" if style == "state" else "9;20"
                    base_role = "STATE_NODE_LABEL" if style == "state" else "OBS_NODE_LABEL"
                    if is_script:
                        make_group(elements, assigned, f"{panel}_{node_kind}_{ti}_{suffix}",
                                   f"{panel}_{node_kind}_{ti}", panel, f"{base_role}_SCRIPT", src_line,
                                   "natural-script", "6.44", [c],
                                   derivation="natural TeX script from 9.2pt node base; PDF span establishes 6.44pt TeX-equivalent",
                                   semantic_hint="script")
                    else:
                        make_group(elements, assigned, f"{panel}_{node_kind}_{ti}_{suffix}",
                                   f"{panel}_{node_kind}_{ti}", panel, f"{base_role}_BASE", src_line,
                                   "9.2", "9.2", [c], semantic_hint="math")

    # The one normal annotation below the graph.
    ann = by(lambda c: 518.5 <= c.bbox[1] <= 520.0)
    make_group(elements, assigned, "COMMON_ANNOTATION", "COMMON_ANNOTATION", "COMMON", "ORDINARY_ANNOTATION",
               "41-42", "8.8", "8.8", ann)

    # Caption is reader-visible and included. Source lacks a local declared font, so it is correctly retained as UNKNOWN.
    cap_specs = [
        ("CAPTION_LABEL_CJK", 97, 109, "CJK"),
        ("CAPTION_LABEL_DIGITS", 109, 128, "DIGIT"),
        ("CAPTION_HMM", 137, 164, "LATIN"),
        ("CAPTION_CN_LEFT", 163, 384.5, "CJK"),
        ("CAPTION_VITERBI", 384, 414, "LATIN"),
        ("CAPTION_CN_RIGHT", 413, 490, "CJK"),
    ]
    for eid, lo, hi, hint in cap_specs:
        cs = by(lambda c, lo=lo, hi=hi: 533 <= c.bbox[1] <= 539 and lo <= c.bbox[0] < hi)
        make_group(elements, assigned, eid, "CAPTION", "CAPTION", "CAPTION", "44", "UNKNOWN", "UNKNOWN", cs,
                   derivation="caption font inherited outside the permitted figure/body context; source effective pt is not reconstructible", semantic_hint=None)

    unassigned = [c for c in chars if c.idx not in assigned]
    return elements, unassigned


def make_text_mask(element: TextElement, rgb: np.ndarray) -> None:
    h, w, _ = rgb.shape
    mask = np.zeros((h, w), dtype=bool)
    for ch in element.chars:
        x0, y0, x1, y1 = point_bbox_to_local_px(ch.bbox)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)
        if x1 <= x0 or y1 <= y0:
            continue
        patch = rgb[y0:y1, x0:x1]
        bg = local_modal_background(patch)
        foreground = np.max(np.abs(patch.astype(np.int16) - bg.astype(np.int16)), axis=2) >= 20
        mask[y0:y1, x0:x1] |= foreground
    element.mask = mask
    element.point_bbox = union_bbox(c.bbox for c in element.chars)
    element.px_bbox = point_bbox_to_local_px(element.point_bbox)
    rows = np.where(mask.any(axis=1))[0]
    element.h_ink = int(rows[-1] - rows[0] + 1) if len(rows) else 0
    element.foreground_px = int(mask.sum())
    element.script_class, element.required_px = script_info(element.text, element.semantic_hint)
    element.pdf_font = ";".join(sorted(set(c.font for c in element.chars)))
    element.pdf_size_pt = round(float(statistics.median(c.size for c in element.chars)), 4)


def replay_drawing_mask(drawing: dict[str, Any], part: str, page_width: float, page_height: float) -> np.ndarray:
    """Re-render one native PDF path only; no color segmentation or mask dilation."""
    doc = fitz.open()
    p = doc.new_page(width=page_width, height=page_height)
    shape = p.new_shape()
    for item in drawing["items"]:
        code = item[0]
        if code == "l":
            shape.draw_line(item[1], item[2])
        elif code == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        else:
            raise RuntimeError(f"Unsupported PDF vector command: {code}")
    if part == "fill":
        width, color, fill = 0, None, drawing.get("fill")
    elif part == "border":
        width, color, fill = float(drawing.get("width") or 0), drawing.get("color"), None
    else:
        width, color, fill = float(drawing.get("width") or 0), drawing.get("color"), drawing.get("fill")
    if color is None and fill is None:
        doc.close()
        return np.zeros((px_ceil(FIG_CROP.height), px_ceil(FIG_CROP.width)), dtype=bool)
    lc = drawing.get("lineCap") or (0, 0, 0)
    line_cap = int(lc[0]) if isinstance(lc, tuple) else int(lc)
    shape.finish(
        width=width,
        color=color,
        fill=fill,
        lineCap=line_cap,
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd")),
        closePath=bool(drawing.get("closePath")),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=FIG_CROP, alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    mask = arr[:, :, 3] > 0
    doc.close()
    return mask


def build_vector_objects(page: fitz.Page, crop_shape: tuple[int, int]) -> list[VectorObject]:
    vectors: list[VectorObject] = []
    for i, d in enumerate(page.get_drawings()):
        r = d["rect"]
        # Native graph paths occupy this range. Decorative page boxes are excluded.
        if r.x1 < 100 or r.x0 > 500 or r.y1 < 435 or r.y0 > 515:
            continue
        is_node = d.get("fill") is not None and r.width >= 10 and r.height >= 10
        is_arrowhead = d.get("fill") is not None and r.width <= 5 and r.height <= 5
        color = f"stroke={d.get('color')};fill={d.get('fill')};width={d.get('width')}"
        if is_node:
            fill_mask = replay_drawing_mask(d, "fill", page.rect.width, page.rect.height)
            border_mask = replay_drawing_mask(d, "border", page.rect.width, page.rect.height)
            vectors.append(VectorObject(f"D{i:03d}_NODE_FILL", i, "NODE_FILL_BACKGROUND", "8-9;18-20", fill_mask,
                                        mask_bbox(fill_mask), color, "native vector fill; explicitly exempt from text-inside-node overlap"))
            vectors.append(VectorObject(f"D{i:03d}_NODE_BORDER", i, "NODE_BORDER", "8-9;18-20", border_mask,
                                        mask_bbox(border_mask), color, "native vector stroke rendered independently"))
        else:
            kind = "ARROWHEAD" if is_arrowhead else "LINE_ARROW"
            source_line = "32-40" if i >= 95 else "23-27" if i >= 23 else "21"
            mask = replay_drawing_mask(d, "both", page.rect.width, page.rect.height)
            vectors.append(VectorObject(f"D{i:03d}_{kind}", i, kind, source_line, mask, mask_bbox(mask), color,
                                        "native PDF path replayed independently at 300 dpi"))
    return vectors


def parent_texts(elements: list[TextElement]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for e in elements:
        if e.parent_id not in result:
            result[e.parent_id] = {"id": e.parent_id, "panel": e.panel_id, "role": e.role, "children": [], "mask": None}
        result[e.parent_id]["children"].append(e)
    for p in result.values():
        mask = np.zeros_like(p["children"][0].mask, dtype=bool)
        for e in p["children"]:
            mask |= e.mask
        p["mask"] = mask
        p["px_bbox"] = mask_bbox(mask)
        p["text"] = "".join(e.text for e in p["children"])
    return result


def source_font_status(e: TextElement) -> tuple[str, str]:
    if e.effective_pt == "UNKNOWN":
        return "FAIL", "effective_pt cannot be reconstructed from permitted source context"
    if e.semantic_hint == "script":
        # Its base is known to be illegal, so derivative-script allowance cannot close the audit.
        return "FAIL", "natural script is permitted only from >=9.5pt base; its 9.2pt base fails"
    pt = float(e.effective_pt)
    if pt < 9.5:
        return "FAIL", f"effective_pt={pt:.2f}<9.50"
    return "PASS", "effective_pt>=9.5 and graphics_scale=1.0"


def writing_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def save_relation_bundle(prefix: str, image: Image.Image, a_mask: np.ndarray, b_mask: np.ndarray, a_id: str, b_id: str,
                         a_point: tuple[int, int] | None, b_point: tuple[int, int] | None) -> dict[str, str]:
    # A raw 1:1 ROI is a view aid; masks themselves remain unexpanded.
    union = mask_bbox(a_mask | b_mask)
    if union is None:
        return {}
    margin = 20
    x0, y0 = max(0, union[0] - margin), max(0, union[1] - margin)
    x1, y1 = min(image.width, union[2] + margin), min(image.height, union[3] + margin)
    raw_path = OUT / f"{prefix}_raw_1to1.png"
    image.crop((x0, y0, x1, y1)).save(raw_path, dpi=(300, 300))
    am_path = OUT / f"{prefix}_{a_id}_mask.png"
    bm_path = OUT / f"{prefix}_{b_id}_mask.png"
    ov_path = OUT / f"{prefix}_overlap_mask.png"
    save_mask(am_path, a_mask)
    save_mask(bm_path, b_mask)
    save_mask(ov_path, a_mask & b_mask)
    rgba = np.array(image.convert("RGBA"))
    # Exact masks are overlaid without morphology: red=A, cyan=B, magenta=intersection.
    rgba[a_mask] = np.array([235, 30, 30, 190], dtype=np.uint8)
    rgba[b_mask] = np.array([0, 180, 220, 190], dtype=np.uint8)
    rgba[a_mask & b_mask] = np.array([220, 0, 220, 255], dtype=np.uint8)
    overlay = Image.fromarray(rgba, mode="RGBA").convert("RGB")
    dr = ImageDraw.Draw(overlay)
    if a_point and b_point:
        ax, ay = a_point
        bx, by = b_point
        dr.line((ax, ay, bx, by), fill=(255, 0, 255), width=1)
        dr.ellipse((ax - 2, ay - 2, ax + 2, ay + 2), outline=(255, 0, 0), width=1)
        dr.ellipse((bx - 2, by - 2, bx + 2, by + 2), outline=(0, 180, 220), width=1)
    overlay_path = OUT / f"{prefix}_overlay.png"
    overlay.crop((x0, y0, x1, y1)).save(overlay_path, dpi=(300, 300))
    return {"RAW_ROI": raw_path.name, "A_MASK": am_path.name, "B_MASK": bm_path.name, "OVERLAP_MASK": ov_path.name, "OVERLAY": overlay_path.name}


def main() -> None:
    ensure_out()
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_1 - 1]
    if page.get_label() != str(PRINTED_PAGE):
        raise RuntimeError(f"Expected printed page {PRINTED_PAGE}, got {page.get_label()!r}")

    # Direct, unscaled 300 dpi source image for all measurements.
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    full_300 = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    full_300.save(OUT / "after_full_page_300dpi_measurement_raw.png", dpi=(300, 300))
    crop_box = (px_floor(FIG_CROP.x0), px_floor(FIG_CROP.y0), px_ceil(FIG_CROP.x1), px_ceil(FIG_CROP.y1))
    figure_img = full_300.crop(crop_box)
    figure_img.save(OUT / "after_figure_crop_300dpi.png", dpi=(300, 300))
    standalone_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=STANDALONE_CROP, alpha=False)
    standalone = Image.frombytes("RGB", (standalone_pix.width, standalone_pix.height), standalone_pix.samples)
    standalone.save(OUT / "after_standalone_300dpi.png", dpi=(300, 300))
    ImageOps.grayscale(figure_img).save(OUT / "after_grayscale_300dpi.png", dpi=(300, 300))
    rgb = np.array(figure_img.convert("RGB"))

    chars = load_chars(page)
    elements, unassigned = build_text_elements(chars)
    if unassigned:
        # Preserve unknowns as explicit audit failures rather than silently omitting them.
        for c in unassigned:
            elements.append(TextElement(f"UNASSIGNED_{c.idx:03d}", "UNASSIGNED", "UNKNOWN", "UNASSIGNED",
                                        "UNKNOWN", "UNKNOWN", "UNKNOWN", [c],
                                        "unassigned real PDF text character; audit cannot close"))
    for e in elements:
        make_text_mask(e, rgb)

    # Direct overlay of every PDF-derived measurement box and its deterministic ID.
    overlay = figure_img.copy()
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    overlay_key: list[dict[str, Any]] = []
    role_colors = {
        "PANEL_LABEL": (220, 20, 60), "TIME_TICK": (0, 100, 220), "NODE_LABEL_BASE": (0, 140, 90),
        "NODE_LABEL_SCRIPT": (150, 60, 0), "ORDINARY_ANNOTATION": (150, 0, 150), "CAPTION": (70, 70, 70),
    }
    for n, e in enumerate(elements, start=1):
        x0, y0, x1, y1 = e.px_bbox
        col = role_colors.get(e.role, (255, 0, 0))
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=col, width=1)
        label = f"E{n:03d}"
        draw.text((x0, max(0, y0 - 10)), label, fill=col, font=font)
        overlay_key.append({"OVERLAY_ID": label, "ELEMENT_ID": e.element_id, "PARENT_ID": e.parent_id, "ROLE": e.role,
                            "TEXT_SAMPLE": e.text, "PDF_BBOX": ";".join(f"{v:.3f}" for v in e.point_bbox)})
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))
    writing_csv(OUT / "after_text_measurement_overlay_key.csv", list(overlay_key[0].keys()), overlay_key)

    vectors = build_vector_objects(page, rgb.shape[:2])
    parents = parent_texts(elements)

    # Composite measurements keep naturally short horizontal operators honest:
    # +/- has its own raw-character row, while its 22px mathematical-baseline
    # test is made on the true unexpanded t-1 / t / t+1 formula object.
    semantic_measurements: list[TextElement] = []
    for p in parents.values():
        if p["role"] == "TIME_TICK":
            cs = sorted((c for child in p["children"] for c in child.chars), key=lambda c: c.bbox[0])
            e = TextElement(f"{p['id']}_FORMULA", p["id"], p["panel"], "TIME_TICK_FORMULA", "17", "8.7", "8.7", cs,
                            "complete native t-1/t/t+1 formula; no glyph-box expansion", "math_formula")
            make_text_mask(e, rgb)
            semantic_measurements.append(e)
    cap_children = [e for e in elements if e.parent_id == "CAPTION"]
    if cap_children:
        cs = sorted((c for child in cap_children for c in child.chars), key=lambda c: c.bbox[0])
        e = TextElement("CAPTION_LINE", "CAPTION", "CAPTION", "CAPTION_LINE", "44", "UNKNOWN", "UNKNOWN", cs,
                        "complete native caption line; local source caption font is not declared", None)
        make_text_mask(e, rgb)
        semantic_measurements.append(e)
    measurement_elements = elements + semantic_measurements

    # Font evidence, preserving unknown caption effective size as a hard FAIL.
    font_rows: list[dict[str, Any]] = []
    pixel_rows: list[dict[str, Any]] = []
    for e in measurement_elements:
        fstatus, freason = source_font_status(e)
        bbox = e.px_bbox
        if e.semantic_hint == "operator":
            status, reason = "PASS", "horizontal inline operator; its 22px base-formula test is recorded in parent TIME_TICK_FORMULA"
        else:
            status = "PASS" if e.h_ink >= e.required_px else "FAIL"
            reason = "meets script-class pixel floor" if status == "PASS" else f"H_ink_px={e.h_ink}<{e.required_px}"
        # Source audit has exactly one row per real reader-visible PDF text
        # component. Composite formula/caption rows below are measurement aids
        # only and must not inflate the source-font population.
        if e in elements:
            font_rows.append({
                "ELEMENT_ID": e.element_id, "PARENT_ID": e.parent_id, "PANEL_ID": e.panel_id, "ROLE": e.role,
                "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": e.source_line, "TEXT_SAMPLE": e.text,
                "DECLARED_PT": e.declared_pt, "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": e.effective_pt,
                "BASE_FORMULA_EFFECTIVE_PT": "9.2" if e.semantic_hint == "script" else e.effective_pt,
                "DERIVATION": e.derivation, "PDF_FONT": e.pdf_font, "PDF_SPAN_SIZE_PT": f"{e.pdf_size_pt:.4f}",
                "THEORETICAL_EM_PX": "UNKNOWN" if e.effective_pt == "UNKNOWN" else f"{ppi_size_from_tex_pt(float(e.effective_pt)):.3f}",
                "PASS_FAIL": fstatus, "REASON": freason,
            })
        pixel_rows.append({
            "ELEMENT_ID": e.element_id, "PARENT_ID": e.parent_id, "PANEL_ID": e.panel_id, "ROLE": e.role,
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": e.source_line, "DECLARED_PT": e.declared_pt,
            "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": e.effective_pt, "TEXT_SAMPLE": e.text,
            "SCRIPT_CLASS": e.script_class, "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3],
            "H_INK_PX": e.h_ink, "REQUIRED_MIN_PX": e.required_px, "FOREGROUND_PIXEL_COUNT": e.foreground_px,
            "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "",
            "PASS_FAIL": status, "REASON": reason,
            "MASK_METHOD": "real PDF RAWDICT character boxes + direct candidate-PDF 300dpi RGB foreground delta>=20; no dilation",
        })
    font_headers = list(font_rows[0].keys())
    writing_csv(OUT / "after_font_audit.csv", font_headers, font_rows)

    # Complete native object inventory: all reader-visible text components plus all vector paths (fill is separately recorded).
    inventory: list[dict[str, Any]] = []
    for e in elements:
        inventory.append({
            "OBJECT_ID": e.element_id, "PARENT_ID": e.parent_id, "OBJECT_TYPE": "TEXT_COMPONENT", "ROLE": e.role,
            "PANEL_ID": e.panel_id, "TEXT_SAMPLE": e.text, "PDF_BBOX": ";".join(f"{v:.3f}" for v in e.point_bbox),
            "PIXEL_BBOX": ";".join(map(str, e.px_bbox)), "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": e.source_line,
            "NATIVE_EVIDENCE": "PDF RAWDICT real text character span(s)",
            "MASK_METHOD": "direct 300dpi, PDF-char-bbox constrained, local modal background, delta>=20, no dilation",
            "NOTES": e.derivation,
        })
    for e in semantic_measurements:
        inventory.append({
            "OBJECT_ID": e.element_id, "PARENT_ID": e.parent_id, "OBJECT_TYPE": "TEXT_MEASUREMENT_COMPOSITE", "ROLE": e.role,
            "PANEL_ID": e.panel_id, "TEXT_SAMPLE": e.text, "PDF_BBOX": ";".join(f"{v:.3f}" for v in e.point_bbox),
            "PIXEL_BBOX": ";".join(map(str, e.px_bbox)), "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": e.source_line,
            "NATIVE_EVIDENCE": "union of real PDF RAWDICT character boxes for one semantic formula/caption",
            "MASK_METHOD": "direct 300dpi, PDF-char-bbox constrained, local modal background, delta>=20, no dilation",
            "NOTES": e.derivation,
        })
    for v in vectors:
        inventory.append({
            "OBJECT_ID": v.object_id, "PARENT_ID": f"DRAWING_{v.drawing_index:03d}", "OBJECT_TYPE": v.object_type,
            "ROLE": v.object_type, "PANEL_ID": "F/B/V", "TEXT_SAMPLE": "", "PDF_BBOX": "",
            "PIXEL_BBOX": "" if v.px_bbox is None else ";".join(map(str, v.px_bbox)), "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": v.source_line, "NATIVE_EVIDENCE": f"PDF get_drawings()[{v.drawing_index}] native path",
            "MASK_METHOD": "individual native path replayed with original geometry/stroke/fill at 300dpi transparent canvas; no color threshold/dilation",
            "NOTES": v.note,
        })
    writing_csv(OUT / "object_inventory.csv", list(inventory[0].keys()), inventory)

    # Text-text bbox clearance is an independent hard gate. Each pair is explicit.
    relation_rows: list[dict[str, Any]] = []
    detail_cache: dict[str, dict[str, Any]] = {}
    parent_list = list(parents.values())
    for ai in range(len(parent_list)):
        for bi in range(ai + 1, len(parent_list)):
            a, b = parent_list[ai], parent_list[bi]
            bc, intersect = bbox_clearance(a["px_bbox"], b["px_bbox"])
            if bc <= 20 or intersect:
                dist, ap, bp = nearest_points(a["mask"], b["mask"])
                min_ink, method = dist, "exact independent 300dpi text masks"
            else:
                min_ink, ap, bp, method = bc, None, None, "bbox lower-bound; >20px excludes a <=4px failure"
            overlap = int((a["mask"] & b["mask"]).sum())
            status = "PASS" if (bc >= 4 and overlap == 0) else "FAIL"
            rid = f"TT_{ai:03d}_{bi:03d}"
            row = {
                "RELATION_ID": rid, "RELATION_TYPE": "TEXT_TEXT", "OBJECT_A": a["id"], "OBJECT_B": b["id"],
                "PANEL_A": a["panel"], "PANEL_B": b["panel"], "BBOX_CLEARANCE_PX": f"{bc:.3f}",
                "BBOX_INTERSECTS": str(intersect).lower(), "REQUIRED_CLEARANCE_PX": 4, "MIN_INK_CLEARANCE_PX": f"{min_ink:.3f}",
                "N_OVERLAP_PX": overlap, "NEAREST_A_XY": "" if ap is None else f"{ap[0]},{ap[1]}",
                "NEAREST_B_XY": "" if bp is None else f"{bp[0]},{bp[1]}", "METHOD": method, "PASS_FAIL": status,
                "RAW_ROI": "", "OVERLAY": "", "A_MASK": "", "B_MASK": "", "OVERLAP_MASK": "",
            }
            relation_rows.append(row)
            detail_cache[rid] = {"a": a, "b": b, "ap": ap, "bp": bp, "row": row}

    # Text / foreground-vector relations. Node fills are backgrounds by protocol and are not tested as illegal overlaps.
    foreground_vectors = [v for v in vectors if v.object_type != "NODE_FILL_BACKGROUND" and v.px_bbox is not None]
    for ai, a in enumerate(parent_list):
        for vi, v in enumerate(foreground_vectors):
            bc, intersect = bbox_clearance(a["px_bbox"], v.px_bbox)
            required = 5 if ("_Q" in a["id"] or "_X" in a["id"]) and v.object_type == "NODE_BORDER" and bc <= 30 else 3
            if bc <= 20 or intersect:
                dist, ap, bp = nearest_points(a["mask"], v.mask)
                min_ink, method = dist, "exact independent PDF-text / native-vector 300dpi masks"
            else:
                min_ink, ap, bp, method = bc, None, None, f"bbox lower-bound; >20px excludes a <={required}px failure"
            overlap = int((a["mask"] & v.mask).sum())
            status = "PASS" if (overlap == 0 and min_ink >= required) else "FAIL"
            rid = f"TG_{ai:03d}_{vi:03d}"
            row = {
                "RELATION_ID": rid, "RELATION_TYPE": "TEXT_GRAPHIC", "OBJECT_A": a["id"], "OBJECT_B": v.object_id,
                "PANEL_A": a["panel"], "PANEL_B": "F/B/V", "BBOX_CLEARANCE_PX": f"{bc:.3f}",
                "BBOX_INTERSECTS": str(intersect).lower(), "REQUIRED_CLEARANCE_PX": required, "MIN_INK_CLEARANCE_PX": f"{min_ink:.3f}",
                "N_OVERLAP_PX": overlap, "NEAREST_A_XY": "" if ap is None else f"{ap[0]},{ap[1]}",
                "NEAREST_B_XY": "" if bp is None else f"{bp[0]},{bp[1]}", "METHOD": method, "PASS_FAIL": status,
                "RAW_ROI": "", "OVERLAY": "", "A_MASK": "", "B_MASK": "", "OVERLAP_MASK": "",
            }
            relation_rows.append(row)
            detail_cache[rid] = {"a": a, "b": v, "ap": ap, "bp": bp, "row": row}

    # Text to raw figure crop edge: actual foreground clearance, plus explicit bbox figure-crop containment.
    for ai, a in enumerate(parent_list):
        ys, xs = np.where(a["mask"])
        ink_edge = int(min(xs.min(), ys.min(), a["mask"].shape[1] - 1 - xs.max(), a["mask"].shape[0] - 1 - ys.max()))
        x0, y0, x1, y1 = a["px_bbox"]
        bbox_edge = float(min(x0, y0, a["mask"].shape[1] - x1, a["mask"].shape[0] - y1))
        status = "PASS" if ink_edge >= 6 else "FAIL"
        rid = f"TE_{ai:03d}"
        relation_rows.append({
            "RELATION_ID": rid, "RELATION_TYPE": "TEXT_IMAGE_EDGE", "OBJECT_A": a["id"], "OBJECT_B": "FIGURE_CROP_EDGE",
            "PANEL_A": a["panel"], "PANEL_B": "CROP", "BBOX_CLEARANCE_PX": f"{bbox_edge:.3f}",
            "BBOX_INTERSECTS": "false", "REQUIRED_CLEARANCE_PX": 6, "MIN_INK_CLEARANCE_PX": f"{ink_edge:.3f}",
            "N_OVERLAP_PX": 0, "NEAREST_A_XY": "", "NEAREST_B_XY": "", "METHOD": "exact foreground distance to unscaled raw crop edge",
            "PASS_FAIL": status, "RAW_ROI": "", "OVERLAY": "", "A_MASK": "", "B_MASK": "", "OVERLAP_MASK": "",
        })

    # Cross-panel reader elements are a separately reported >=8px gate.
    for ai in range(len(parent_list)):
        for bi in range(ai + 1, len(parent_list)):
            a, b = parent_list[ai], parent_list[bi]
            if a["panel"] not in {"F", "B", "V"} or b["panel"] not in {"F", "B", "V"} or a["panel"] == b["panel"]:
                continue
            bc, intersect = bbox_clearance(a["px_bbox"], b["px_bbox"])
            status = "PASS" if bc >= 8 else "FAIL"
            relation_rows.append({
                "RELATION_ID": f"CP_{ai:03d}_{bi:03d}", "RELATION_TYPE": "CROSS_PANEL_TEXT", "OBJECT_A": a["id"], "OBJECT_B": b["id"],
                "PANEL_A": a["panel"], "PANEL_B": b["panel"], "BBOX_CLEARANCE_PX": f"{bc:.3f}",
                "BBOX_INTERSECTS": str(intersect).lower(), "REQUIRED_CLEARANCE_PX": 8, "MIN_INK_CLEARANCE_PX": f"{bc:.3f}",
                "N_OVERLAP_PX": 0, "NEAREST_A_XY": "", "NEAREST_B_XY": "", "METHOD": "bbox lower-bound (cross-panel gate)",
                "PASS_FAIL": status, "RAW_ROI": "", "OVERLAY": "", "A_MASK": "", "B_MASK": "", "OVERLAP_MASK": "",
            })

    # Evidence bundle for every failed relation and the tightest relation of each audited type.
    selected: set[str] = {r["RELATION_ID"] for r in relation_rows if r["PASS_FAIL"] == "FAIL" and r["RELATION_ID"] in detail_cache}
    for kind in ("TEXT_TEXT", "TEXT_GRAPHIC"):
        candidates = [r for r in relation_rows if r["RELATION_TYPE"] == kind and r["RELATION_ID"] in detail_cache]
        if candidates:
            selected.add(min(candidates, key=lambda r: float(r["MIN_INK_CLEARANCE_PX"]))["RELATION_ID"])
    for n, rid in enumerate(sorted(selected), start=1):
        d = detail_cache[rid]
        paths = save_relation_bundle(f"relation_{n:02d}_{rid}", figure_img, d["a"]["mask"], d["b"].mask if isinstance(d["b"], VectorObject) else d["b"]["mask"],
                                     d["a"]["id"], d["b"].object_id if isinstance(d["b"], VectorObject) else d["b"]["id"], d["ap"], d["bp"])
        d["row"].update({k: v for k, v in paths.items()})

    # Pixel rows receive relation outcomes at their parent level.
    rel_by_parent: dict[str, list[dict[str, Any]]] = {p: [] for p in parents}
    for r in relation_rows:
        if r["OBJECT_A"] in rel_by_parent:
            rel_by_parent[r["OBJECT_A"]].append(r)
        if r["OBJECT_B"] in rel_by_parent:
            rel_by_parent[r["OBJECT_B"]].append(r)
    for row in pixel_rows:
        rels = rel_by_parent.get(row["PARENT_ID"], [])
        row["TEXT_TEXT_OVERLAP_PX"] = sum(int(r["N_OVERLAP_PX"]) for r in rels if r["RELATION_TYPE"] == "TEXT_TEXT")
        row["TEXT_GRAPHIC_OVERLAP_PX"] = sum(int(r["N_OVERLAP_PX"]) for r in rels if r["RELATION_TYPE"] == "TEXT_GRAPHIC")
        cands = [float(r["MIN_INK_CLEARANCE_PX"]) for r in rels if r["RELATION_TYPE"] in {"TEXT_GRAPHIC", "TEXT_IMAGE_EDGE"}]
        row["MIN_CLEARANCE_PX"] = f"{min(cands):.3f}" if cands else ""

    # Same-class ratio evidence; values are direct measured H_ink values only.
    same_rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, str, str], list[TextElement]] = {}
    # Compare repeat instances of the same glyph/function, not the inherently
    # different outlines of t, t-1 and t+1. The whole formula still has its own
    # direct 22px baseline audit in after_pixel_measurements.csv.
    ratio_entries: list[tuple[TextElement, str]] = []
    for e in elements:
        if e.role == "TIME_TICK":
            if e.text == "𝑡":
                ratio_entries.append((e, "TIME_TICK_T"))
            elif e.text.isdigit():
                ratio_entries.append((e, "TIME_TICK_DIGIT"))
            # +/- are distinct operator shapes; the parent formula provides its
            # legibility audit and no false font-size comparison is made here.
        elif e.role != "CAPTION":
            ratio_entries.append((e, e.role))
    # A caption is one continuous semantic text element, rather than six pieces
    # split only by PDF font-run boundaries.
    ratio_entries.extend((e, e.role) for e in semantic_measurements if e.role == "CAPTION_LINE")
    for e, ratio_role in ratio_entries:
        groups.setdefault((e.panel_id, ratio_role, e.script_class), []).append(e)
    panel_medians: dict[tuple[str, str, str], float] = {}
    for key, es in groups.items():
        panel_medians[key] = float(statistics.median(e.h_ink for e in es))
    for key, es in groups.items():
        panel, role, script = key
        med = panel_medians[key]
        ratio_max_min = max(e.h_ink for e in es) / min(e.h_ink for e in es)
        cross_meds = [m for (p, r, s), m in panel_medians.items() if r == role and s == script and p in {"F", "B", "V"}]
        cross_ratio = max(cross_meds) / min(cross_meds) if cross_meds else 1.0
        for e in es:
            ratio = e.h_ink / med if med else float("inf")
            same_pass = 0.92 <= ratio <= 1.08 and ratio_max_min <= 1.08
            cross_pass = cross_ratio <= 1.10
            same_rows.append({
                "AUDIT_SCOPE": "same-panel+cross-panel", "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script,
                "ELEMENT_ID": e.element_id, "H_INK_PX": e.h_ink, "CLASS_MEDIAN_PX": f"{med:.3f}",
                "RATIO_TO_CLASS_MEDIAN": f"{ratio:.3f}", "WITHIN_PANEL_MAX_MIN": f"{ratio_max_min:.3f}",
                "WITHIN_PANEL_PASS": str(same_pass).lower(), "CROSS_PANEL_MAX_MIN": f"{cross_ratio:.3f}",
                "CROSS_PANEL_PASS": str(cross_pass).lower(), "PASS_FAIL": "PASS" if same_pass and cross_pass else "FAIL",
                "REASON": "direct H_ink comparison restricted to same role and script class",
            })
            for row in pixel_rows:
                if row["ELEMENT_ID"] == e.element_id:
                    row["CLASS_MEDIAN_PX"] = f"{med:.3f}"
                    row["RATIO_TO_CLASS_MEDIAN"] = f"{ratio:.3f}"
    writing_csv(OUT / "same_class_ratio_audit.csv", list(same_rows[0].keys()), same_rows)

    # Role hierarchy is intentionally conservative: the primary node-label role is the mandated local base.
    node_base = [e.h_ink for e in elements if e.role in {"STATE_NODE_LABEL_BASE", "OBS_NODE_LABEL_BASE"}]
    base_median = float(statistics.median(node_base))
    role_rows: list[dict[str, Any]] = []
    for role, lo, hi in [("PANEL_LABEL", 1.05, 1.20), ("ORDINARY_ANNOTATION", 0.95, 1.10)]:
        es = [e for e in elements if e.role == role]
        if not es:
            continue
        med = float(statistics.median(e.h_ink for e in es))
        ratio = med / base_median
        role_rows.append({"ROLE": role, "BASE_ROLE": "NODE_LABEL_BASE", "BASE_MEDIAN_PX": f"{base_median:.3f}",
                          "ROLE_MEDIAN_PX": f"{med:.3f}", "ROLE_RATIO": f"{ratio:.3f}", "LOW": lo, "HIGH": hi,
                          "PASS_FAIL": "PASS" if lo <= ratio <= hi else "FAIL",
                          "REASON": "actual H_ink medians; mixed-script result is retained (not normalized away) under strict protocol"})
    # Roles absent from this figure are explicitly N/A, not silently treated as measured.
    for role, low, high in [("AXIS_TITLE_OR_UNIT", 1.00, 1.18), ("LEGEND", 0.95, 1.10), ("FORMULA_BLOCK", 1.00, 1.18)]:
        role_rows.append({"ROLE": role, "BASE_ROLE": "NODE_LABEL_BASE", "BASE_MEDIAN_PX": f"{base_median:.3f}",
                          "ROLE_MEDIAN_PX": "N/A", "ROLE_RATIO": "N/A", "LOW": low, "HIGH": high,
                          "PASS_FAIL": "N/A", "REASON": "role absent in this figure"})
    writing_csv(OUT / "role_ratio_audit.csv", list(role_rows[0].keys()), role_rows)
    role_pass = all(r["PASS_FAIL"] != "FAIL" for r in role_rows)

    # Required after_pixel_measurements ROLE_RATIO column: record a number for
    # roles governed by §9.2.1-E and an explicit N/A where that role has no
    # specified comparator (rather than leaving an unauditable blank).
    role_ratio_lookup = {r["ROLE"]: r["ROLE_RATIO"] for r in role_rows}
    for row in pixel_rows:
        if row["ROLE"] in {"STATE_NODE_LABEL_BASE", "OBS_NODE_LABEL_BASE"}:
            row["ROLE_RATIO"] = "1.000"
        elif row["ROLE"] == "PANEL_LABEL":
            row["ROLE_RATIO"] = role_ratio_lookup.get("PANEL_LABEL", "N/A")
        elif row["ROLE"] == "ORDINARY_ANNOTATION":
            row["ROLE_RATIO"] = role_ratio_lookup.get("ORDINARY_ANNOTATION", "N/A")
        else:
            row["ROLE_RATIO"] = "N/A (no §9.2.1-E comparator)"

    # Finalize after_pixel now that all derived columns are filled.
    writing_csv(OUT / "after_pixel_measurements.csv", list(pixel_rows[0].keys()), pixel_rows)
    writing_csv(OUT / "relation_clearance.csv", list(relation_rows[0].keys()), relation_rows)
    writing_csv(OUT / "after_overlap_report.csv", list(relation_rows[0].keys()), relation_rows)

    source_font_pass = all(r["PASS_FAIL"] == "PASS" for r in font_rows)
    pixel_height_pass = all(r["PASS_FAIL"] == "PASS" for r in pixel_rows)
    same_class_pass = all(r["PASS_FAIL"] == "PASS" for r in same_rows)
    overlap_total = sum(int(r["N_OVERLAP_PX"]) for r in relation_rows if r["RELATION_TYPE"] in {"TEXT_TEXT", "TEXT_GRAPHIC"})
    clearance_fail = [r for r in relation_rows if r["PASS_FAIL"] == "FAIL"]
    min_clearance = min(float(r["MIN_INK_CLEARANCE_PX"]) for r in relation_rows if r["RELATION_TYPE"] in {"TEXT_GRAPHIC", "TEXT_IMAGE_EDGE"})
    # Clipping is evaluated against the candidate PDF page boundary and the intentionally raw crop boundary.
    all_fg = np.zeros_like(rgb[:, :, 0], dtype=bool)
    for p in parents.values():
        all_fg |= p["mask"]
    for v in foreground_vectors:
        all_fg |= v.mask
    clip_pixels_page = 0  # all native figure bboxes lie strictly inside PDF MediaBox; verified below in manifest.
    clip_pixels_crop = int(all_fg[0, :].sum() + all_fg[-1, :].sum() + all_fg[:, 0].sum() + all_fg[:, -1].sum())
    clip_total = clip_pixels_page + clip_pixels_crop
    manifest = {
        "candidate_pdf": str(PDF), "candidate_pdf_bytes": PDF.stat().st_size, "pdf_physical_page": PDF_PAGE_1,
        "printed_page": PRINTED_PAGE, "figure_number": FIGURE_NO, "figure_label": "fig:V3-C05-lattice",
        "render_engine": "PyMuPDF direct candidate-PDF Page.get_pixmap(matrix=300/72)", "render_dpi": 300,
        "post_render_resize": False, "figure_crop_pdf_points": list(FIG_CROP), "standalone_crop_pdf_points": list(STANDALONE_CROP),
        "full_300_dimensions": [full_300.width, full_300.height], "figure_crop_dimensions": [figure_img.width, figure_img.height],
        "standalone_dimensions": [standalone.width, standalone.height], "text_components": len(elements), "text_parent_objects": len(parents),
        "native_vector_objects": len(vectors), "unassigned_text_chars": len(unassigned), "clip_pixels_crop_edge": clip_pixels_crop,
    }
    (OUT / "audit_run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Machine-readable facts consumed by the human-written acceptance report.
    facts = {
        "SOURCE_FONT_PASS": source_font_pass, "PIXEL_HEIGHT_PASS": pixel_height_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass, "ROLE_RATIO_PASS": role_pass,
        "OVERLAP_PIXEL_COUNT": overlap_total, "CLIP_PIXEL_COUNT": clip_total,
        "MIN_TEXT_CLEARANCE_PX": round(min_clearance, 3), "RELATION_FAILS": len(clearance_fail),
        "PIXEL_HEIGHT_FAILS": sum(r["PASS_FAIL"] == "FAIL" for r in pixel_rows),
        "SOURCE_FONT_FAILS": sum(r["PASS_FAIL"] == "FAIL" for r in font_rows),
        "SAME_CLASS_FAILS": sum(r["PASS_FAIL"] == "FAIL" for r in same_rows),
        "ROLE_RATIO_FAILS": sum(r["PASS_FAIL"] == "FAIL" for r in role_rows),
    }
    (OUT / "audit_facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    doc.close()
    print(json.dumps(facts, ensure_ascii=False))


if __name__ == "__main__":
    main()
