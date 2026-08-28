"""Local SA2 non-resampling pixel audit for FIG-P157-01 STRICT-R2.

Inputs are the independently compiled standalone candidate and its direct
300 dpi Poppler raster. All generated files stay beside this script.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


OUT = Path(__file__).resolve().parent
PDF = OUT / "build" / "standalone_wrapper.pdf"
PAGE_PNG = OUT / "standalone_page_300dpi.png"
SCALE = 300.0 / 72.0  # PDF user space point -> native 300 dpi raster pixel
SOURCE_FILE = (
    "v2.7.0/_work/source/v2.7.0/src/绘图源码/"
    "第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex"
)


def pbox(rect: fitz.Rect) -> tuple[float, float, float, float]:
    """Map a PDF vector bbox to native raster coordinates without resampling."""
    return tuple(float(v) * SCALE for v in (rect.x0, rect.y0, rect.x1, rect.y1))


def crop_bounds(rect: fitz.Rect, width: int, height: int, pad: int = 1) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pbox(rect)
    return (
        max(0, math.floor(x0) - pad),
        max(0, math.floor(y0) - pad),
        min(width, math.ceil(x1) + pad),
        min(height, math.ceil(y1) + pad),
    )


def bbox_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    """Euclidean edge-to-edge gap between two continuous pixel bboxes."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def nearest_drawing(drawings: list[dict], expected: tuple[float, float, float, float]) -> dict:
    """Find one official-PDF vector drawing by its PDF-space bounding box."""
    ex = fitz.Rect(expected)

    def score(d: dict) -> float:
        r = d["rect"]
        return abs(r.x0 - ex.x0) + abs(r.y0 - ex.y0) + abs(r.x1 - ex.x1) + abs(r.y1 - ex.y1)

    hit = min(drawings, key=score)
    if score(hit) > 0.25:
        raise RuntimeError(f"Drawing lookup was not reproducible: wanted {expected}, got {hit['rect']}")
    return hit


def point_px(point: fitz.Point) -> tuple[int, int]:
    return (round(float(point.x) * SCALE), round(float(point.y) * SCALE))


def cubic_points(p0: fitz.Point, p1: fitz.Point, p2: fitz.Point, p3: fitz.Point, n: int = 64) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for t in np.linspace(0.0, 1.0, n):
        u = 1.0 - t
        x = u**3 * p0.x + 3.0 * u * u * t * p1.x + 3.0 * u * t * t * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3.0 * u * u * t * p1.y + 3.0 * u * t * t * p2.y + t**3 * p3.y
        out.append((round(float(x) * SCALE), round(float(y) * SCALE)))
    return out


def candidate_mask_for_drawing(
    drawing: dict,
    width: int,
    height: int,
    *,
    force_ellipse: bool = False,
    force_fill_rect: bool = False,
) -> np.ndarray:
    """Build only a locating band; final object pixels come from native raster."""
    canvas = Image.new("1", (width, height), 0)
    pen = ImageDraw.Draw(canvas)
    r = drawing["rect"]
    if force_ellipse:
        x0, y0, x1, y1 = crop_bounds(r, width, height, pad=3)
        pen.ellipse((x0, y0, x1, y1), fill=1)
    elif force_fill_rect:
        x0, y0, x1, y1 = crop_bounds(r, width, height, pad=2)
        pen.rectangle((x0, y0, x1, y1), fill=1)
    else:
        # Native stroke width plus a one-pixel anti-alias allowance on each
        # side.  Do not use an oversized locator band: it would inflate a
        # semantic-object intersection merely because two objects are nearby.
        px_width = max(2, math.ceil(float(drawing.get("width") or 0.6) * SCALE) + 2)
        for item in drawing["items"]:
            op = item[0]
            if op == "l":
                pen.line((point_px(item[1]), point_px(item[2])), fill=1, width=px_width)
            elif op == "c":
                pen.line(cubic_points(item[1], item[2], item[3], item[4]), fill=1, width=px_width)
            elif op == "re":
                x0, y0, x1, y1 = crop_bounds(item[1], width, height, pad=2)
                pen.rectangle((x0, y0, x1, y1), outline=1, width=px_width)
            else:
                raise RuntimeError(f"Unhandled vector item {op!r} in official page drawing")
    return np.asarray(canvas, dtype=bool)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    page_img = Image.open(PAGE_PNG).convert("RGB")
    rgb = np.asarray(page_img)
    height, width = rgb.shape[:2]
    if (width, height) != (2481, 3508):
        raise RuntimeError(f"Native page raster must be 2481x3508, got {width}x{height}")

    document = fitz.open(PDF)
    if document.page_count != 1:
        raise RuntimeError("The official page extract is not exactly one page")
    page = document[0]
    drawings = page.get_drawings()

    # The three very pale panel fills plus white are the only local backgrounds
    # in the figure.  A pixel is foreground only if it differs by >=20 in at
    # least one channel from its closest local background, as §9.2.1-C requires.
    backgrounds: list[np.ndarray] = [np.array((255, 255, 255), dtype=np.int16)]
    for d in drawings:
        r = d["rect"]
        if d["type"] == "f" and d.get("fill") and 60.0 <= r.y0 and r.y1 <= 300.0 and 90.0 <= r.x0 and r.x1 <= 535.0:
            backgrounds.append(np.rint(np.array(d["fill"]) * 255).astype(np.int16))
    image16 = rgb.astype(np.int16)
    nearest_bg_delta = np.full((height, width), 255, dtype=np.int16)
    for bg in backgrounds:
        delta = np.max(np.abs(image16 - bg), axis=2)
        nearest_bg_delta = np.minimum(nearest_bg_delta, delta)
    foreground = nearest_bg_delta >= 20

    # All text elements visible in the figure itself, including figure number
    # and caption, are enumerated independently.  Target locations are PDF
    # vector locations only; actual ink heights come only from the raw PNG.
    specs = [
        {
            "id": "FIG-P157-01-T01", "sample": "训练误差：单调下降", "role": "CURVE_LABEL", "script": "CJK",
            "anchor": (466.85, 233.71), "declared": 9.2, "scale": 1.12,
            "source_line": "5-7; 44-46", "font_origin": "local direct style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T02", "sample": "验证误差：先降后升", "role": "CURVE_LABEL", "script": "CJK",
            "anchor": (313.86, 175.52), "declared": 9.2, "scale": 1.12,
            "source_line": "5-7; 47-48", "font_origin": "local direct style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T03", "sample": "最低验证误差", "role": "KEY_ANNOTATION", "script": "CJK",
            "anchor": (324.95, 219.57), "declared": 9.2, "scale": 1.12,
            "source_line": "8-9; 49-50", "font_origin": "local key style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T04", "sample": "选择复杂度", "role": "KEY_ANNOTATION", "script": "CJK",
            "anchor": (324.95, 291.24), "declared": 9.2, "scale": 1.12,
            "source_line": "8-9; 51-52", "font_origin": "local key style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T05", "sample": "欠拟合", "role": "REGION_ANNOTATION", "script": "CJK",
            "anchor": (176.29, 314.86), "declared": 8.8, "scale": 1.12,
            "source_line": "10; 53-54", "font_origin": "local region style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T06", "sample": "合适", "role": "REGION_ANNOTATION", "script": "CJK",
            "anchor": (321.91, 314.86), "declared": 8.8, "scale": 1.12,
            "source_line": "10; 55-56", "font_origin": "local region style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T07", "sample": "过拟合", "role": "REGION_ANNOTATION", "script": "CJK",
            "anchor": (459.30, 314.86), "declared": 8.8, "scale": 1.12,
            "source_line": "10; 57-58", "font_origin": "local region style; node", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T08", "sample": "模型复杂度", "role": "AXIS_TITLE", "script": "CJK",
            "anchor": (340.11, 337.23), "declared": 10.0, "scale": 1.12,
            "source_line": "20-25; styles/figure-style-v2.3.1.tex:67-78", "font_origin": "slfig axis later overrides local label style with \\small", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T09", "sample": "预测误差", "role": "AXIS_TITLE", "script": "CJK",
            "anchor": (86.16, 175.57), "declared": 10.0, "scale": 1.12,
            "source_line": "20-25; styles/figure-style-v2.3.1.tex:67-78", "font_origin": "slfig axis later overrides local label style with \\small", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T10", "sample": "图", "role": "CAPTION_LABEL", "script": "CJK",
            "anchor": (143.92, 355.60), "declared": 10.0, "scale": 1.00,
            "source_line": "61; common statlearnbook.sty:305", "font_origin": "caption \\small, bold label", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T11", "sample": "10.1", "role": "CAPTION_LABEL", "script": "DIGIT",
            "anchor": (160.02, 357.33), "declared": 10.0, "scale": 1.00,
            "source_line": "61; common statlearnbook.sty:305", "font_origin": "caption \\small, bold number", "panel": "P01",
        },
        {
            "id": "FIG-P157-01-T12", "sample": "模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。", "role": "CAPTION_BODY", "script": "CJK",
            "anchor": (323.21, 357.31), "declared": 10.0, "scale": 1.00,
            "source_line": "61; common statlearnbook.sty:305", "font_origin": "caption \\small", "panel": "P01",
        },
    ]

    raw_spans: list[dict] = []
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                chars = span.get("chars", [])
                if not chars:
                    continue
                raw_spans.append(
                    {
                        "bbox": fitz.Rect(span["bbox"]),
                        "size": float(span["size"]),
                        "font": span["font"],
                        "color": span["color"],
                        "chars": chars,
                    }
                )

    def lookup_span(spec: dict) -> dict:
        ax, ay = spec["anchor"]

        def score(span: dict) -> float:
            r = span["bbox"]
            cx = (r.x0 + r.x1) / 2.0
            cy = (r.y0 + r.y1) / 2.0
            return math.hypot(cx - ax, cy - ay) + 0.02 * abs(len(span["chars"]) - len(spec["sample"]))

        hit = min(raw_spans, key=score)
        if score(hit) > 2.0:
            raise RuntimeError(f"Text span lookup was not reproducible for {spec['id']}: {hit['bbox']}")
        if len(hit["chars"]) != len(spec["sample"]):
            raise RuntimeError(
                f"Text character count mismatch for {spec['id']}: vector has {len(hit['chars'])}, source has {len(spec['sample'])}"
            )
        return hit

    elements: list[dict] = []
    detail: dict[str, dict] = {}
    for spec in specs:
        span = lookup_span(spec)
        rect = span["bbox"]
        mask = np.zeros((height, width), dtype=bool)
        char_details: list[dict] = []
        sample = spec["sample"]
        if spec["script"] == "CJK":
            selected_indices = [i for i, ch in enumerate(sample) if "\u4e00" <= ch <= "\u9fff"]
        else:
            selected_indices = [i for i, ch in enumerate(sample) if ch.isdigit()]
        char_heights: list[int] = []
        for i, char in enumerate(span["chars"]):
            cr = fitz.Rect(char["bbox"])
            x0, y0, x1, y1 = crop_bounds(cr, width, height, pad=1)
            cmask = foreground[y0:y1, x0:x1]
            mask[y0:y1, x0:x1] |= cmask
            rows = np.flatnonzero(cmask.any(axis=1))
            ink_h = int(rows[-1] - rows[0] + 1) if rows.size else 0
            char_details.append(
                {
                    "index": i,
                    "source_character": sample[i],
                    "bbox_px": [x0, y0, x1, y1],
                    "ink_height_px": ink_h,
                    "used_for_threshold": i in selected_indices,
                }
            )
            if i in selected_indices:
                char_heights.append(ink_h)
        if not char_heights or min(char_heights) <= 0:
            raise RuntimeError(f"No measurable threshold character ink for {spec['id']}")
        px_bbox = pbox(rect)
        spec = dict(spec)
        spec.update(
            {
                "pdf_bbox": rect,
                "px_bbox": px_bbox,
                "rendered_pdf_pt": float(span["size"]),
                "rendered_font": span["font"],
                "ink_height": min(char_heights),  # strict: least full-size glyph, not a convenient maximum
                "ink_height_median": float(np.median(char_heights)),
                "char_heights": char_heights,
                "mask": mask,
            }
        )
        elements.append(spec)
        detail[spec["id"]] = {
            "sample": sample,
            "vector_bbox_pt": [rect.x0, rect.y0, rect.x1, rect.y1],
            "vector_font_pdf_pt": span["size"],
            "native_pixel_bbox": list(px_bbox),
            "threshold_character_measurements": char_details,
        }

    # Locate every non-text foreground object from the official page vector
    # display list, then retain only actual native-raster foreground pixels.
    d_training = nearest_drawing(drawings, (97.414, 99.876, 530.814, 259.557))
    d_validation = nearest_drawing(drawings, (97.414, 86.855, 530.814, 229.565))
    d_reference = nearest_drawing(drawings, (324.949, 229.565, 324.949, 282.822))
    d_leader = nearest_drawing(drawings, (407.295, 238.442, 415.963, 250.523))
    d_x_axis = nearest_drawing(drawings, (97.414, 282.822, 528.382, 282.822))
    d_x_arrow = nearest_drawing(drawings, (526.923, 280.876, 530.815, 284.768))
    d_y_axis = nearest_drawing(drawings, (97.414, 70.751, 97.414, 282.822))
    d_y_arrow = nearest_drawing(drawings, (95.468, 68.318, 99.360, 72.210))
    d_marker = nearest_drawing(drawings, (321.950, 226.566, 327.948, 232.565))
    graphic_specs = [
        ("FIG-P157-01-G01", "DATA_CURVE", "training error curve", [d_training], {}),
        ("FIG-P157-01-G02", "DATA_CURVE", "validation error curve", [d_validation], {}),
        ("FIG-P157-01-G03", "LINE_ARROW", "selection reference line", [d_reference], {}),
        ("FIG-P157-01-G04", "MARKER", "minimum-validation-error marker", [d_marker], {"force_ellipse": True}),
        ("FIG-P157-01-G05", "LINE_ARROW", "training-label leader", [d_leader], {}),
        ("FIG-P157-01-G06", "LINE_ARROW", "x-axis and arrowhead", [d_x_axis, d_x_arrow], {"force_fill_rect_for_last": True}),
        ("FIG-P157-01-G07", "LINE_ARROW", "y-axis and arrowhead", [d_y_axis, d_y_arrow], {"force_fill_rect_for_last": True}),
    ]
    graphics: list[dict] = []
    for gid, kind, name, ds, options in graphic_specs:
        candidate = np.zeros((height, width), dtype=bool)
        for n, drawing in enumerate(ds):
            candidate |= candidate_mask_for_drawing(
                drawing,
                width,
                height,
                force_ellipse=bool(options.get("force_ellipse")),
                force_fill_rect=bool(options.get("force_fill_rect_for_last")) and n == len(ds) - 1,
            )
        actual = candidate & foreground
        if not actual.any():
            raise RuntimeError(f"No native foreground pixels located for {gid}")
        graphics.append({"id": gid, "kind": kind, "name": name, "mask": actual, "drawing_count": len(ds)})

    graphic_union = np.zeros((height, width), dtype=bool)
    for g in graphics:
        graphic_union |= g["mask"]

    # Required source-level font audit.
    font_rows: list[dict] = []
    by_role: dict[str, list[dict]] = {}
    for e in elements:
        by_role.setdefault(e["role"], []).append(e)
    for e in elements:
        peers = by_role[e["role"]]
        sizes = [p["declared"] * p["scale"] for p in peers]
        effective = e["declared"] * e["scale"]
        ratio = max(sizes) / min(sizes)
        diff = max(sizes) - min(sizes)
        source_pass = effective >= 9.5 and ratio <= 1.03 and diff <= 0.25
        font_rows.append(
            {
                "ELEMENT_ID": e["id"], "PANEL_ID": e["panel"], "ROLE": e["role"], "SOURCE_FILE": SOURCE_FILE,
                "SOURCE_LINE": e["source_line"], "DECLARED_PT": f"{e['declared']:.3f}",
                "GRAPHICS_SCALE": f"{e['scale']:.3f}", "EFFECTIVE_PT": f"{effective:.3f}",
                "RENDERED_PDF_FONT_PT": f"{e['rendered_pdf_pt']:.3f}", "FONT_ORIGIN": e["font_origin"],
                "SAME_ROLE_MAX_MIN_RATIO": f"{ratio:.3f}", "SAME_ROLE_ABS_DIFF_PT": f"{diff:.3f}",
                "CROSS_PANEL_RATIO": "N/A (single panel)", "PASS_FAIL": "PASS" if source_pass else "FAIL",
                "REASON": "effective >=9.5pt; same-role source-size criteria met; single panel",
            }
        )
    write_csv(
        OUT / "after_font_audit.csv",
        [
            "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE",
            "EFFECTIVE_PT", "RENDERED_PDF_FONT_PT", "FONT_ORIGIN", "SAME_ROLE_MAX_MIN_RATIO",
            "SAME_ROLE_ABS_DIFF_PT", "CROSS_PANEL_RATIO", "PASS_FAIL", "REASON",
        ],
        font_rows,
    )

    # Pixel metrics: strict full-size-character minima, same-role medians, and
    # designated base-role hierarchy.  CURVE_LABEL is the figure's BASE role.
    # §9.2.1-D compares only the same semantic role *and* script class.
    # In particular the 10.1 digits must clear their own digit floor, rather
    # than being treated as undersized CJK merely because Arabic numerals have
    # a naturally shorter ink box at the same declared caption font.
    by_class: dict[tuple[str, str], list[dict]] = {}
    for e in elements:
        by_class.setdefault((e["role"], e["script"]), []).append(e)
    class_medians = {
        key: float(np.median([e["ink_height"] for e in peers])) for key, peers in by_class.items()
    }
    role_medians = {role: float(np.median([e["ink_height"] for e in peers])) for role, peers in by_role.items()}
    base_median = role_medians["CURVE_LABEL"]
    dist_to_graphic = ndimage.distance_transform_edt(~graphic_union)
    pixel_rows: list[dict] = []
    for e in elements:
        script_min = 30 if e["script"] == "CJK" else 24
        class_median = class_medians[(e["role"], e["script"])]
        class_ratio = e["ink_height"] / class_median if class_median else 0.0
        if e["role"] == "AXIS_TITLE":
            role_ratio = class_median / base_median
            role_bounds = (1.00, 1.18)
        elif e["role"] in {"CURVE_LABEL", "KEY_ANNOTATION", "REGION_ANNOTATION"}:
            role_ratio = class_median / base_median
            role_bounds = (0.95, 1.10)
        else:
            role_ratio = float("nan")
            role_bounds = None
        text_graphic_overlap = int(np.count_nonzero(e["mask"] & graphic_union))
        min_graphic_clearance = float(dist_to_graphic[e["mask"]].min()) if e["mask"].any() else 0.0
        role_ok = role_bounds is None or (role_bounds[0] <= role_ratio <= role_bounds[1])
        px_pass = (
            e["ink_height"] >= script_min
            and 0.92 <= class_ratio <= 1.08
            and role_ok
            and text_graphic_overlap == 0
            and min_graphic_clearance >= 3.0
        )
        e["text_graphic_overlap"] = text_graphic_overlap
        e["min_graphic_clearance"] = min_graphic_clearance
        pixel_rows.append(
            {
                "ELEMENT_ID": e["id"], "PANEL_ID": e["panel"], "ROLE": e["role"], "SOURCE_FILE": SOURCE_FILE,
                "SOURCE_LINE": e["source_line"], "DECLARED_PT": f"{e['declared']:.3f}",
                "GRAPHICS_SCALE": f"{e['scale']:.3f}", "EFFECTIVE_PT": f"{e['declared'] * e['scale']:.3f}",
                "TEXT_SAMPLE": e["sample"], "SCRIPT_CLASS": e["script"],
                "BBOX_X0": f"{e['px_bbox'][0]:.2f}", "BBOX_Y0": f"{e['px_bbox'][1]:.2f}",
                "BBOX_X1": f"{e['px_bbox'][2]:.2f}", "BBOX_Y1": f"{e['px_bbox'][3]:.2f}",
                "H_INK_PX": e["ink_height"], "CLASS_MEDIAN_PX": f"{class_median:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{class_ratio:.3f}",
                "ROLE_RATIO": "N/A" if role_bounds is None else f"{role_ratio:.3f}",
                "TEXT_TEXT_OVERLAP_PX": "pending pair audit", "TEXT_GRAPHIC_OVERLAP_PX": text_graphic_overlap,
                "MIN_CLEARANCE_PX": f"{min_graphic_clearance:.2f}", "PASS_FAIL": "PASS" if px_pass else "FAIL",
                "REASON": (
                    f"strict min full-size glyph={e['ink_height']}px (threshold {script_min}); "
                    f"same-class ratio={class_ratio:.3f}; "
                    + ("caption role has no axis-role ratio" if role_bounds is None else f"role ratio={role_ratio:.3f}")
                    + f"; text-graphic overlap={text_graphic_overlap}; min text-graphic clearance={min_graphic_clearance:.2f}px"
                ),
            }
        )

    # Pairwise text/graphic overlap and clearance evidence.
    overlap_rows: list[dict] = []
    text_overlap_total = 0
    text_text_min_gap = float("inf")
    for i, a in enumerate(elements):
        for b in elements[i + 1 :]:
            overlap = int(np.count_nonzero(a["mask"] & b["mask"]))
            gap = bbox_gap(a["px_bbox"], b["px_bbox"])
            text_overlap_total += overlap
            text_text_min_gap = min(text_text_min_gap, gap)
            passed = overlap == 0 and gap >= 4.0
            overlap_rows.append(
                {
                    "PAIR_ID": f"TT-{a['id'].split('-')[-1]}-{b['id'].split('-')[-1]}", "OBJECT_A": a["id"], "CLASS_A": "TEXT",
                    "OBJECT_B": b["id"], "CLASS_B": "TEXT", "CHECK": "TEXT_TEXT", "OVERLAP_PX": overlap,
                    "OVERLAP_PIXEL_COUNT": overlap, "CLIP_PIXEL_COUNT": "N/A",
                    "MIN_CLEARANCE_PX": f"{gap:.2f}", "REQUIRED": "overlap=0; bbox gap>=4px", "PASS_FAIL": "PASS" if passed else "FAIL",
                "METHOD": "local-candidate native 300dpi foreground masks + PDF-vector bboxes mapped at 300/72", "NOTES": "all reader-visible text pairs",
                }
            )
    for g in graphics:
        dist = ndimage.distance_transform_edt(~g["mask"])
        for e in elements:
            overlap = int(np.count_nonzero(e["mask"] & g["mask"]))
            gap = float(dist[e["mask"]].min()) if e["mask"].any() else 0.0
            passed = overlap == 0 and gap >= 3.0
            overlap_rows.append(
                {
                    "PAIR_ID": f"TG-{e['id'].split('-')[-1]}-{g['id'].split('-')[-1]}", "OBJECT_A": e["id"], "CLASS_A": "TEXT",
                    "OBJECT_B": g["id"], "CLASS_B": g["kind"], "CHECK": "TEXT_GRAPHIC", "OVERLAP_PX": overlap,
                    "OVERLAP_PIXEL_COUNT": overlap, "CLIP_PIXEL_COUNT": "N/A",
                    "MIN_CLEARANCE_PX": f"{gap:.2f}", "REQUIRED": "overlap=0; ink-to-line/arrow/marker>=3px", "PASS_FAIL": "PASS" if passed else "FAIL",
                    "METHOD": "local-candidate native 300dpi foreground masks; vector path is locator only", "NOTES": g["name"],
                }
            )
    outer = np.zeros((height, width), dtype=bool)
    outer[0, :] = outer[-1, :] = True
    outer[:, 0] = outer[:, -1] = True
    object_union = graphic_union.copy()
    for e in elements:
        object_union |= e["mask"]
    clip_count = int(np.count_nonzero(object_union & outer))
    overlap_rows.append(
        {
            "PAIR_ID": "CLIP-PAGE-EDGE", "OBJECT_A": "ALL_FIGURE_OBJECTS", "CLASS_A": "TEXT+GRAPHIC",
            "OBJECT_B": "LOCAL_CANDIDATE_PAGE_EDGE", "CLASS_B": "IMAGE_EDGE", "CHECK": "CLIP", "OVERLAP_PX": clip_count,
            "OVERLAP_PIXEL_COUNT": clip_count, "CLIP_PIXEL_COUNT": clip_count,
            "MIN_CLEARANCE_PX": f"{min(min(e['px_bbox'][0], e['px_bbox'][1], width-e['px_bbox'][2], height-e['px_bbox'][3]) for e in elements):.2f}",
            "REQUIRED": "clip pixel count=0; text-to-image edge>=6px", "PASS_FAIL": "PASS" if clip_count == 0 else "FAIL",
            "METHOD": "local-candidate native 300dpi outermost-pixel inspection", "NOTES": "axis uses clip=false; no node/panel border exists in this single-panel figure",
        }
    )
    write_csv(
        OUT / "after_overlap_report.csv",
        [
            "PAIR_ID", "OBJECT_A", "CLASS_A", "OBJECT_B", "CLASS_B", "CHECK", "OVERLAP_PX", "OVERLAP_PIXEL_COUNT", "CLIP_PIXEL_COUNT", "MIN_CLEARANCE_PX",
            "REQUIRED", "PASS_FAIL", "METHOD", "NOTES",
        ],
        overlap_rows,
    )

    # Fill the pairwise text-overlap column now that its total is determined.
    for row, e in zip(pixel_rows, elements):
        peers = [p for p in elements if p is not e]
        row["TEXT_TEXT_OVERLAP_PX"] = sum(int(np.count_nonzero(e["mask"] & p["mask"])) for p in peers)
    write_csv(
        OUT / "after_pixel_measurements.csv",
        [
            "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE",
            "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1",
            "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX",
            "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
        ],
        pixel_rows,
    )

    # Complete object inventory, including expressly absent classes so that
    # absence is not silently mistaken for an omitted inspection.
    inventory_rows = []
    for e in elements:
        inventory_rows.append(
            {
                "ELEMENT_ID": e["id"], "PANEL_ID": e["panel"], "OBJECT_CLASS": "TEXT", "ROLE_OR_NAME": e["role"],
                "TEXT_OR_DESCRIPTION": e["sample"], "SOURCE_LINE": e["source_line"], "STATUS": "PRESENT", "NOTES": e["font_origin"],
            }
        )
    for g in graphics:
        inventory_rows.append(
            {
                "ELEMENT_ID": g["id"], "PANEL_ID": "P01", "OBJECT_CLASS": g["kind"], "ROLE_OR_NAME": g["name"],
                "TEXT_OR_DESCRIPTION": "", "SOURCE_LINE": "30-43", "STATUS": "PRESENT", "NOTES": f"local candidate vector drawings={g['drawing_count']}",
            }
        )
    for gid, kind, note in [
        ("FIG-P157-01-G08", "NODE_BORDER", "No node border: annotation fills are explicitly draw=none."),
        ("FIG-P157-01-G09", "PANEL_BORDER", "No enclosing panel border: axis lines=left only."),
        ("FIG-P157-01-G10", "LEGEND", "No legend object is drawn."),
    ]:
        inventory_rows.append(
            {
                "ELEMENT_ID": gid, "PANEL_ID": "P01", "OBJECT_CLASS": kind, "ROLE_OR_NAME": kind,
                "TEXT_OR_DESCRIPTION": "", "SOURCE_LINE": "21-59", "STATUS": "ABSENT", "NOTES": note,
            }
        )
    write_csv(
        OUT / "element_inventory.csv",
        ["ELEMENT_ID", "PANEL_ID", "OBJECT_CLASS", "ROLE_OR_NAME", "TEXT_OR_DESCRIPTION", "SOURCE_LINE", "STATUS", "NOTES"],
        inventory_rows,
    )

    # Original-pixel crop and ROIs: all are lossless crops or grayscale
    # conversion, never resized.
    fig_pt = fitz.Rect(70.0, 55.0, 555.0, 375.0)
    fx0, fy0, fx1, fy1 = crop_bounds(fig_pt, width, height, pad=0)
    figure_crop = page_img.crop((fx0, fy0, fx1, fy1))
    figure_crop.save(OUT / "figure_crop_300dpi.png", dpi=(300, 300))
    # "standalone" here is the unaltered figure-level pixel crop from the
    # official-page 300 dpi raster, retained separately for the required view;
    # it is deliberately not a recompiled or rescaled substitute candidate.
    figure_crop.save(OUT / "standalone_300dpi.png", dpi=(300, 300))
    figure_crop.convert("L").save(OUT / "figure_grayscale_300dpi.png", dpi=(300, 300))
    roi_specs = [
        ("roi_01_validation_label_100pct.png", fitz.Rect(245.0, 150.0, 385.0, 200.0)),
        ("roi_02_minimum_marker_100pct.png", fitz.Rect(275.0, 200.0, 370.0, 245.0)),
        ("roi_03_axis_and_regions_100pct.png", fitz.Rect(140.0, 270.0, 490.0, 350.0)),
        ("roi_04_caption_100pct.png", fitz.Rect(125.0, 340.0, 485.0, 370.0)),
    ]
    roi_rows = []
    for name, rect in roi_specs:
        x0, y0, x1, y1 = crop_bounds(rect, width, height, pad=0)
        page_img.crop((x0, y0, x1, y1)).save(OUT / name, dpi=(300, 300))
        roi_rows.append({"FILE": name, "X0": x0, "Y0": y0, "X1": x1, "Y1": y1, "PIXELS": f"{x1-x0}x{y1-y0}", "RESAMPLING": "none; native crop"})
    # Overlay is the native raw page plus vector-mapped text boxes; no resize.
    overlay = page_img.copy()
    pen = ImageDraw.Draw(overlay)
    palette = {"CURVE_LABEL": "#0050A0", "KEY_ANNOTATION": "#9A6200", "REGION_ANNOTATION": "#7B4F00", "AXIS_TITLE": "#000000", "CAPTION_LABEL": "#7A007A", "CAPTION_BODY": "#7A007A"}
    for e in elements:
        x0, y0, x1, y1 = e["px_bbox"]
        color = palette[e["role"]]
        pen.rectangle((round(x0), round(y0), round(x1), round(y1)), outline=color, width=2)
        pen.rectangle((round(x0), max(0, round(y0) - 13), round(x0) + 88, max(0, round(y0) - 1)), fill="white")
        pen.text((round(x0) + 1, max(0, round(y0) - 13)), e["id"].split("-")[-1], fill=color)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    # A focused, native-pixel diagnostic for the one validation-label / curve
    # collision candidate.  Red pixels are only the independently located
    # semantic-object intersection; the underlying crop is untouched PNG data.
    t02 = next(e for e in elements if e["id"] == "FIG-P157-01-T02")
    g02 = next(g for g in graphics if g["id"] == "FIG-P157-01-G02")
    conflict = page_img.copy()
    conflict_array = np.asarray(conflict).copy()
    conflict_array[t02["mask"] & g02["mask"]] = np.array([235, 30, 30], dtype=np.uint8)
    conflict = Image.fromarray(conflict_array)
    cx0, cy0, cx1, cy1 = crop_bounds(fitz.Rect(245.0, 145.0, 385.0, 245.0), width, height, pad=0)
    conflict_name = "roi_05_validation_label_curve_clearance_100pct.png"
    conflict.crop((cx0, cy0, cx1, cy1)).save(OUT / conflict_name, dpi=(300, 300))
    roi_rows.append({"FILE": conflict_name, "X0": cx0, "Y0": cy0, "X1": cx1, "Y1": cy1, "PIXELS": f"{cx1-cx0}x{cy1-cy0}", "RESAMPLING": "none; native crop; red only if illegal intersection exists"})
    write_csv(OUT / "roi_manifest.csv", ["FILE", "X0", "Y0", "X1", "Y1", "PIXELS", "RESAMPLING"], roi_rows)

    # Detailed, reproducible method data and a compact non-conclusive summary.
    (OUT / "pixel_measurement_detail.json").write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    all_font_pass = all(r["PASS_FAIL"] == "PASS" for r in font_rows)
    all_pixel_pass = all(r["PASS_FAIL"] == "PASS" for r in pixel_rows)
    all_overlap_pass = all(r["PASS_FAIL"] == "PASS" for r in overlap_rows)
    summary = {
        "source_pdf": str(PDF.name),
        "native_raster": {"file": PAGE_PNG.name, "dpi": 300, "width_px": width, "height_px": height, "resampling": "none"},
        "figure_panel_count": 1,
        "text_element_count": len(elements),
        "graphic_foreground_object_count": len(graphics),
        "source_font_pass": all_font_pass,
        "pixel_measurement_pass": all_pixel_pass,
        "overlap_and_clearance_pass": all_overlap_pass,
        "illegal_text_text_overlap_px": text_overlap_total,
        "clip_pixel_count": clip_count,
        "minimum_text_text_bbox_clearance_px": text_text_min_gap,
        "notes": "Local SA2 mechanical candidate summary; root will rebuild the official continuous PDF and obtain fresh independent SA1/SA3 verdicts.",
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
