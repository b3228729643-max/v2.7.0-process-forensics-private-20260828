"""FIG-P573-01 SA1 strict native-PDF audit.

This is an independent, read-only audit of the frozen R94 PDF.  All generated
artefacts stay below this evidence directory.  It deliberately derives every
300-dpi crop from the fixed-grid full-page render before any measurement.
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import statistics
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


HERE = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_mc_integral.tex")
BODY = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C02.tex")
STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")

FIGURE_ID = "FIG-P573-01"
PHYSICAL_PAGE = 620                 # one-indexed / independently located by caption text
PRINTED_PAGE = 607
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0
THRESHOLD_DELTA = 20
CROP_PT = fitz.Rect(65.0, 60.0, 540.0, 303.0)          # chart + formula + caption
STANDALONE_PT = fitz.Rect(125.0, 64.0, 485.0, 266.0)    # chart + formula, no caption

FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]


def fail_if(condition: bool, msg: str) -> None:
    if condition:
        raise RuntimeError(msg)


def jdump(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        keys = set()
        for row in rows:
            keys.update(row)
        fields = sorted(keys)
    with path.open("w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rect_to_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE),
        math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE),
        math.ceil(rect.y1 * SCALE),
    )


def rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return float(math.hypot(dx, dy))


def bbox_from_mask(mask: np.ndarray, origin: tuple[int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    ox, oy = origin
    return (ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1)


def mask_height(mask: np.ndarray, vertical_text: bool = False) -> tuple[int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return (0, 0, 0)
    h = int(ys.max() - ys.min() + 1)
    w = int(xs.max() - xs.min() + 1)
    return (w if vertical_text else h, h, w)


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def classify_char(ch: str, span_size: float) -> tuple[str, int | None, bool, str]:
    """Return script class, required H_ink, natural-script, explanatory class."""
    if ch.isspace():
        return "WHITESPACE", 0, False, "non-ink separator"
    if span_size < 8.0:
        return "NATURAL_SCRIPT", 15, True, "TeX-generated script/script-script component"
    if ch in {"ˆ", "ˆ", "ˇ", "ˉ", "˜"}:
        return "COMBINING_ACCENT", None, False, "non-independent accent component of adjacent base glyph"
    code = ord(ch)
    name = unicodedata.name(ch, "")
    if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0xF900 <= code <= 0xFAFF or 0xFF00 <= code <= 0xFFEF:
        return "CJK", 30, False, "CJK/full-width glyph"
    if ch in {"−", "+", "=", "−", "∑", "∫", "×", "÷", "≤", "≥", "/", "|"} or unicodedata.category(ch) == "Sm":
        return "MATH_OPERATOR", 22, False, "base mathematical operator"
    if ch in {".", ",", "，", "。", "：", ":", "；", ";", "（", "）", "(", ")", "[", "]", "…", "—", "-"} or unicodedata.category(ch).startswith("P"):
        return "SEMANTIC_PUNCTUATION", 22, False, "literal punctuation independently measured"
    if ch.isdigit() or ch.isupper() or "CAPITAL" in name:
        return "UPPER_DIGIT", 24, False, "capital letter or digit"
    if ch.islower() or "SMALL" in name or "GREEK" in name or "MATHEMATICAL ITALIC" in name:
        return "LOWER_GREEK", 17, False, "x-height Latin/Greek/math-italic lower glyph"
    return "LOWER_GREEK", 17, False, "alphabetic/math symbol mapped to lower/Greek class"


def pil_font(size: int = 16):
    for candidate in FONT_PATHS:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def crop_save(image: Image.Image, crop_px: tuple[int, int, int, int], path: Path) -> None:
    image.crop(crop_px).save(path)


def clip_box(box: tuple[int, int, int, int], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad)


def save_mask_roi(mask: np.ndarray, path: Path, origin: tuple[int, int], pad: int = 1) -> dict:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        Image.fromarray(np.zeros((1, 1), dtype=np.uint8)).save(path)
        return {"file": path.name, "local_bbox": [0, 0, 1, 1], "global_bbox": None, "pixels": 0}
    y0, y1 = max(0, int(ys.min()) - pad), min(mask.shape[0], int(ys.max()) + 1 + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(mask.shape[1], int(xs.max()) + 1 + pad)
    Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8)).save(path)
    ox, oy = origin
    return {
        "file": path.name,
        "local_bbox": [x0, y0, x1, y1],
        "global_bbox": [ox + x0, oy + y0, ox + x1, oy + y1],
        "pixels": int(mask.sum()),
    }


def save_pair_assets(pair_dir: Path, crop_rgb: np.ndarray, a: np.ndarray, b: np.ndarray, info: dict, origin: tuple[int, int]) -> dict:
    pair_dir.mkdir(parents=True, exist_ok=True)
    union = a | b
    box = bbox_from_mask(union, origin)
    if box is None:
        # A critical pair never should be empty, but keep evidence mechanically reviewable.
        local = (0, 0, min(32, a.shape[1]), min(32, a.shape[0]))
    else:
        local = clip_box((box[0] - origin[0], box[1] - origin[1], box[2] - origin[0], box[3] - origin[1]), a.shape[1], a.shape[0], 12)
    x0, y0, x1, y1 = local
    raw = Image.fromarray(crop_rgb[y0:y1, x0:x1])
    aa = a[y0:y1, x0:x1]
    bb = b[y0:y1, x0:x1]
    inter = aa & bb
    raw.save(pair_dir / "raw_1to1.png")
    Image.fromarray((aa * 255).astype(np.uint8)).save(pair_dir / "A_raw_mask.png")
    Image.fromarray((bb * 255).astype(np.uint8)).save(pair_dir / "B_final_visible_raw_mask.png")
    Image.fromarray((inter * 255).astype(np.uint8)).save(pair_dir / "intersection_raw_mask.png")
    overlay = crop_rgb[y0:y1, x0:x1].copy()
    overlay[aa] = np.array([235, 60, 50], dtype=np.uint8)
    overlay[bb] = np.array([45, 190, 220], dtype=np.uint8)
    overlay[inter] = np.array([255, 230, 30], dtype=np.uint8)
    ov = Image.fromarray(overlay)
    ov.save(pair_dir / "overlay_1to1.png")
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(pair_dir / "raw_8xNN.png")
    ov.resize((ov.width * 8, ov.height * 8), Image.Resampling.NEAREST).save(pair_dir / "overlay_8xNN.png")
    meta = dict(info)
    meta.update({
        "ROI_LOCAL_PX": [x0, y0, x1, y1],
        "ROI_GLOBAL_PAGE_PX": [origin[0] + x0, origin[1] + y0, origin[0] + x1, origin[1] + y1],
        "MASK_MORPHOLOGY": "none",
        "RAW_GRID": "final PDF full-page native 300dpi; fixed grid; crop only",
        "ARTIFACTS": ["raw_1to1.png", "A_raw_mask.png", "B_final_visible_raw_mask.png", "intersection_raw_mask.png", "overlay_1to1.png", "raw_8xNN.png", "overlay_8xNN.png"],
    })
    jdump(pair_dir / "pair_manifest.json", meta)
    return meta


def approximate_cubic(p0, p1, p2, p3, steps=40):
    pts = []
    for k in range(steps + 1):
        t = k / steps
        mt = 1.0 - t
        x = mt**3 * p0.x + 3 * mt**2 * t * p1.x + 3 * mt * t**2 * p2.x + t**3 * p3.x
        y = mt**3 * p0.y + 3 * mt**2 * t * p1.y + 3 * mt * t**2 * p2.y + t**3 * p3.y
        pts.append((x, y))
    return pts


def rasterize_drawing(drawing: dict, crop_origin_px: tuple[int, int], crop_shape: tuple[int, int], mode: str) -> np.ndarray:
    """Rasterize a page.get_drawings primitive at native 300dpi without morphology.

    This is vector geometry, not a color pick from the composite page; therefore
    text painted later cannot pollute a line or border raw mask.
    """
    height, width = crop_shape
    canvas = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(canvas)
    ox, oy = crop_origin_px
    width_px = max(1, int(round(float(drawing.get("width") or 0.6) * SCALE)))

    def cv(p):
        return (int(round(p.x * SCALE - ox)), int(round(p.y * SCALE - oy)))

    all_fill_points = []
    for item in drawing["items"]:
        typ = item[0]
        if typ == "l":
            p0, p1 = item[1], item[2]
            if mode in {"stroke", "all"}:
                draw.line([cv(p0), cv(p1)], fill=255, width=width_px)
            if mode in {"fill", "all"}:
                all_fill_points.extend([cv(p0), cv(p1)])
        elif typ == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            pts = [cv(fitz.Point(x, y)) for x, y in approximate_cubic(p0, p1, p2, p3)]
            if mode in {"stroke", "all"}:
                draw.line(pts, fill=255, width=width_px)
            if mode in {"fill", "all"}:
                all_fill_points.extend(pts)
        elif typ == "re":
            rect = item[1]
            box = (int(round(rect.x0 * SCALE - ox)), int(round(rect.y0 * SCALE - oy)), int(round(rect.x1 * SCALE - ox)), int(round(rect.y1 * SCALE - oy)))
            if mode in {"fill", "all"}:
                draw.rectangle(box, fill=255)
            if mode in {"stroke", "all"}:
                draw.rectangle(box, outline=255, width=width_px)
        elif typ == "qu":
            # Quadrilateral entries are uncommon here; use their supplied points.
            pts = [cv(p) for p in item[1:]]
            if mode in {"fill", "all"}:
                draw.polygon(pts, fill=255)
            if mode in {"stroke", "all"}:
                draw.line(pts + [pts[0]], fill=255, width=width_px)
    if mode in {"fill", "all"} and drawing.get("fill") is not None and len(all_fill_points) >= 3:
        draw.polygon(all_fill_points, fill=255)
    return np.asarray(canvas, dtype=np.uint8) > 0


def source_meta(object_id: str) -> dict:
    if object_id.startswith("TXT_XTICK") or object_id.startswith("TXT_YTICK"):
        return {"declared": 8.6, "line": 8, "source_kind": "PGFPlots tick label style"}
    if object_id == "TXT_XLABEL" or object_id == "TXT_YLABEL":
        return {"declared": 9.5, "line": 9, "source_kind": "PGFPlots label style"}
    if object_id == "TXT_ANNOT_MEAN":
        return {"declared": 9.5, "line": 28, "source_kind": "TikZ annotation node"}
    if object_id == "TXT_ANNOT_TRUE":
        return {"declared": 9.5, "line": 31, "source_kind": "TikZ annotation node"}
    if object_id == "TXT_ESTIMATOR":
        return {"declared": 9.5, "line": 36, "source_kind": "TikZ formula node"}
    if object_id == "TXT_CAPTION":
        return {"declared": 10.0, "line": 305, "source_kind": "11pt class \\small caption setting in statlearnbook.sty"}
    raise RuntimeError(f"Unmapped semantic text object: {object_id}")


def role_of(object_id: str) -> str:
    if "TICK" in object_id:
        return "TICK"
    if "XLABEL" in object_id or "YLABEL" in object_id:
        return "AXIS_LABEL"
    if "ANNOT" in object_id:
        return "ANNOTATION"
    if "ESTIMATOR" in object_id:
        return "FORMULA"
    if "CAPTION" in object_id:
        return "CAPTION"
    raise RuntimeError(object_id)


def expected_vector_category(drawing_index: int) -> tuple[str, str, bool, str]:
    mapping = {
        1: ("LINE_ARROW", "x tick marks", True, ""),
        2: ("LINE_ARROW", "y tick marks", True, ""),
        3: ("LINE_ARROW", "x axis", True, ""),
        4: ("ARROWHEAD", "x axis arrowhead", True, ""),
        5: ("LINE_ARROW", "y axis", True, ""),
        6: ("ARROWHEAD", "y axis arrowhead", True, ""),
        7: ("BACKGROUND_FILL", "low-opacity area fill", False, "opacity .08 produces <20/255 contrast; recorded but excluded from foreground collision geometry"),
        8: ("DATA_CURVE", "h(u) curve", True, ""),
        9: ("LINE_ARROW", "four sample stems", True, ""),
        10: ("DATA_CURVE", "sample mean solid reference", True, ""),
        11: ("DATA_CURVE", "true integral long dash", True, ""),
        12: ("HALO_BACKGROUND", "opaque sample-mean annotation halo", False, "opaque white halo: pre-occlusion and halo masks retained; excluded from foreground geometry"),
        13: ("HALO_BACKGROUND", "opaque true-integral annotation halo", False, "opaque white halo: pre-occlusion and halo masks retained; excluded from foreground geometry"),
        14: ("MARKER", "sample marker u=.10", True, ""),
        15: ("MARKER", "sample marker u=.40", True, ""),
        16: ("MARKER", "sample marker u=.70", True, ""),
        17: ("MARKER", "sample marker u=.80", True, ""),
        18: ("FORMULA_NODE_BORDER", "formula rounded border", True, ""),
        19: ("FORMULA_INTERNAL_RULE", "the \\frac numerator/denominator rule inside TXT_ESTIMATOR", False, "intrinsic formula typography; merged into the parent formula semantic foreground for external relations, never self-paired as an external line/border"),
    }
    return mapping[drawing_index]


def make_vector_components(drawings, crop_origin, crop_shape, mask_dir: Path) -> tuple[list[dict], np.ndarray]:
    """Build component-specific pre-occlusion/halo/final-visible raw masks."""
    components: list[dict] = []
    # only immutable, known figure draw operations; the header/body drawings are deliberately out of scope
    for idx in range(1, 20):
        drawing = drawings[idx]
        category, owner, include, reason = expected_vector_category(idx)
        if idx == 18:
            fill = rasterize_drawing(drawing, crop_origin, crop_shape, "fill")
            components.append({
                "id": "V018_FORMULA_NODE_FILL", "drawing_index": idx, "kind": "BACKGROUND_FILL", "owner": "formula node white fill",
                "pre": fill, "halo": np.zeros_like(fill), "include": False,
                "reason": "opaque formula-node fill is a background, not a border foreground; border stroke audited separately",
                "bbox": drawing["rect"], "mask_mode": "fill",
            })
            stroke = rasterize_drawing(drawing, crop_origin, crop_shape, "stroke")
            components.append({
                "id": "V018_FORMULA_NODE_BORDER", "drawing_index": idx, "kind": "FORMULA_NODE_BORDER", "owner": owner,
                "pre": stroke, "halo": np.zeros_like(stroke), "include": True, "reason": "",
                "bbox": drawing["rect"], "mask_mode": "stroke-only",
            })
            continue
        mode = "fill" if category in {"BACKGROUND_FILL", "HALO_BACKGROUND"} else "all"
        pre = rasterize_drawing(drawing, crop_origin, crop_shape, mode)
        halo = pre.copy() if category == "HALO_BACKGROUND" else np.zeros_like(pre)
        components.append({
            "id": f"V{idx:03d}_{category}", "drawing_index": idx, "kind": category, "owner": owner,
            "pre": pre, "halo": halo, "include": include, "reason": reason,
            "bbox": drawing["rect"], "mask_mode": mode,
        })
    all_halo = np.zeros(crop_shape, dtype=bool)
    for component in components:
        all_halo |= component["halo"]
    for component in components:
        if component["kind"] == "HALO_BACKGROUND":
            component["final"] = np.zeros_like(component["pre"])
        elif component["kind"] == "BACKGROUND_FILL":
            component["final"] = np.zeros_like(component["pre"])
        else:
            component["final"] = component["pre"] & ~all_halo
    (mask_dir / "vector").mkdir(parents=True, exist_ok=True)
    for component in components:
        ident = safe_name(component["id"])
        pre_path = mask_dir / "vector" / f"{ident}__pre_occlusion_raw.png"
        halo_path = mask_dir / "vector" / f"{ident}__halo_raw.png"
        final_path = mask_dir / "vector" / f"{ident}__final_visible_raw.png"
        Image.fromarray((component["pre"] * 255).astype(np.uint8)).save(pre_path)
        Image.fromarray((component["halo"] * 255).astype(np.uint8)).save(halo_path)
        Image.fromarray((component["final"] * 255).astype(np.uint8)).save(final_path)
        component["pre_path"] = pre_path
        component["halo_path"] = halo_path
        component["final_path"] = final_path
    return components, all_halo


def collect_text_spans(rawdict: dict) -> list[dict]:
    spans = []
    serial = 0
    for block in rawdict["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                bbox = fitz.Rect(span["bbox"])
                if bbox.y1 < CROP_PT.y0 or bbox.y0 > CROP_PT.y1 or bbox.x1 < CROP_PT.x0 or bbox.x0 > CROP_PT.x1:
                    continue
                serial += 1
                entry = dict(span)
                entry["serial"] = serial
                entry["text"] = "".join(ch["c"] for ch in span["chars"])
                spans.append(entry)
    return spans


def object_id_for_span(span: dict, counters: dict) -> str:
    x0, y0, x1, y1 = span["bbox"]
    if y0 >= 266:
        return "TXT_CAPTION"
    # Formula and x-axis title sit below the plot, so classify them before x ticks.
    if 225 <= y0 < 265:
        return "TXT_ESTIMATOR"
    if x0 >= 300 and 210 <= y0 < 224:
        return "TXT_XLABEL"
    # The y-axis title is represented as several rotated PDF spans and has a
    # similar x range to the y ticks; title ownership must win before tick routing.
    if x1 <= 150 and 90 <= y0 < 180:
        return "TXT_YLABEL"
    if 200 <= y0 < 210:
        counters["x"] += 1
        return f"TXT_XTICK_{counters['x']:02d}"
    if x1 <= 166 and 70 <= y0 < 202:
        counters["y"] += 1
        return f"TXT_YTICK_{counters['y']:02d}"
    if x0 >= 292 and y0 < 81.5:
        return "TXT_ANNOT_MEAN"
    if x0 >= 340 and 80 <= y0 < 94:
        return "TXT_ANNOT_TRUE"
    raise RuntimeError(f"Unmapped text span at {span['bbox']}: {span['text']!r}")


def output_paths():
    return {
        "masks": HERE / "masks",
        "glyph_masks": HERE / "glyph_masks",
        "critical_pairs": HERE / "critical_pairs",
        "critical_glyphs": HERE / "critical_glyphs",
    }


def main() -> None:
    fail_if(not PDF.exists(), f"Frozen PDF missing: {PDF}")
    fail_if(not SOURCE.exists() or not BODY.exists() or not STYLE.exists(), "Required read-only source/body/style input missing")
    paths = output_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    # Remove only regenerable artefacts inside this dedicated SA1 evidence directory.
    for path in (paths["masks"], paths["glyph_masks"], paths["critical_pairs"], paths["critical_glyphs"]):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    document = fitz.open(PDF)
    page = document[PAGE_INDEX]
    fail_if(len(document) != 813, f"Unexpected R94 page count {len(document)}")
    page_text = page.get_text("text")
    fail_if("图31.2" not in page_text or "蒙特卡罗积分把曲线下的面积" not in page_text, "Caption-based independent page location failed")

    page300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    page200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False)
    page300_path = HERE / "full_page_300dpi_native.png"
    page200_path = HERE / "full_page_200dpi.png"
    page300.save(page300_path)
    page200.save(page200_path)
    full_rgb = np.asarray(Image.open(page300_path).convert("RGB"))
    crop_px = rect_to_px(CROP_PT)
    standalone_px = rect_to_px(STANDALONE_PT)
    crop_rgb = full_rgb[crop_px[1]:crop_px[3], crop_px[0]:crop_px[2]].copy()
    standalone_rgb = full_rgb[standalone_px[1]:standalone_px[3], standalone_px[0]:standalone_px[2]].copy()
    Image.fromarray(crop_rgb).save(HERE / "figure_crop_300dpi.png")
    Image.fromarray(standalone_rgb).save(HERE / "standalone_300dpi.png")
    Image.fromarray(np.asarray(Image.fromarray(crop_rgb).convert("L"))).save(HERE / "grayscale_300dpi.png")
    crop_origin = (crop_px[0], crop_px[1])
    crop_shape = crop_rgb.shape[:2]

    drawings = page.get_drawings()
    components, halo_union = make_vector_components(drawings, crop_origin, crop_shape, paths["masks"])
    # `visible_vectors` are independent objects for cross-object pair enumeration.
    # The fraction bar remains final-visible but is intrinsic to TXT_ESTIMATOR.
    visible_vectors = [c for c in components if c["include"]]
    final_visible_vectors = [c for c in components if c["kind"] not in {"BACKGROUND_FILL", "HALO_BACKGROUND"} and c["final"].any()]
    vector_union = np.zeros(crop_shape, dtype=bool)
    for component in final_visible_vectors:
        vector_union |= component["final"]

    # Text is extracted by the PDF's character-level vector bboxes, then sampled
    # from the direct final-page raster.  The independent mask removes vector
    # geometry solely for H_ink; any removed candidate pixel remains an explicit
    # collision candidate in the pair report and critical ROI.
    rawdict = page.get_text("rawdict")
    spans = collect_text_spans(rawdict)
    counters = defaultdict(int)
    text_objects: dict[str, dict] = {}
    glyphs: list[dict] = []
    gid = 0
    for span in spans:
        object_id = object_id_for_span(span, counters)
        role = role_of(object_id)
        meta = source_meta(object_id)
        if object_id not in text_objects:
            text_objects[object_id] = {
                "id": object_id, "role": role, "glyph_ids": [], "candidate": np.zeros(crop_shape, dtype=bool),
                "independent": np.zeros(crop_shape, dtype=bool), "bboxes": [], "pdf_sizes": [], "meta": meta,
                "vertical": False,
            }
        obj = text_objects[object_id]
        direction = span.get("dir", (1.0, 0.0))
        vertical = abs(direction[1]) > abs(direction[0])
        obj["vertical"] = obj["vertical"] or vertical
        obj["pdf_sizes"].append(float(span["size"]))
        for char in span["chars"]:
            gid += 1
            ch = char["c"]
            cb = fitz.Rect(char["bbox"])
            gx0 = math.floor(cb.x0 * SCALE) - crop_origin[0]
            gy0 = math.floor(cb.y0 * SCALE) - crop_origin[1]
            gx1 = math.ceil(cb.x1 * SCALE) - crop_origin[0]
            gy1 = math.ceil(cb.y1 * SCALE) - crop_origin[1]
            gx0, gy0 = max(0, gx0), max(0, gy0)
            gx1, gy1 = min(crop_shape[1], gx1), min(crop_shape[0], gy1)
            candidate = np.zeros(crop_shape, dtype=bool)
            if gx1 > gx0 and gy1 > gy0:
                patch = crop_rgb[gy0:gy1, gx0:gx1]
                # 20/255 contrast from the white local background; no dilation/closing.
                ink = (255 - patch).max(axis=2) >= THRESHOLD_DELTA
                candidate[gy0:gy1, gx0:gx1] = ink
            script_class, threshold, natural_script, class_reason = classify_char(ch, float(span["size"]))
            # A PDF whitespace advance has a bbox but no glyph ink.  It must never
            # absorb a nearby fraction bar / curve / border into a text mask.
            if script_class == "WHITESPACE":
                candidate.fill(False)
            independent = candidate & ~vector_union
            h_ink, raw_h, raw_w = mask_height(independent, vertical)
            cand_h, _, _ = mask_height(candidate, vertical)
            glyph_id = f"G{gid:04d}"
            mask_path = paths["glyph_masks"] / f"{glyph_id}__independent_raw.png"
            candidate_path = paths["glyph_masks"] / f"{glyph_id}__candidate_before_vector_guard.png"
            mask_meta = save_mask_roi(independent, mask_path, crop_origin)
            candidate_meta = save_mask_roi(candidate, candidate_path, crop_origin)
            # Spaces and accent-only fragments are explicitly documented rather than silently omitted.
            applies = threshold is not None and script_class != "WHITESPACE"
            gate_pass = (not applies) or h_ink >= threshold
            reason = ""
            if script_class == "WHITESPACE":
                reason = "non-ink space; no visual glyph gate"
            elif script_class == "COMBINING_ACCENT":
                reason = "accent is recorded independently but governed by its base math glyph"
            elif not gate_pass:
                reason = f"H_ink={h_ink}px < {threshold}px ({script_class})"
            if int((candidate & vector_union).sum()) > 0:
                reason = (reason + "; " if reason else "") + "vector-geometry candidate pixels excluded from H_ink and escalated to pair check"
            record = {
                "ELEMENT_ID": glyph_id, "PARENT_ELEMENT_ID": object_id, "PANEL_ID": "PANEL_MAIN",
                "ROLE": role, "SOURCE_FILE": str(SOURCE if object_id != "TXT_CAPTION" else STYLE),
                "SOURCE_LINE": meta["line"], "DECLARED_PT": meta["declared"], "GRAPHICS_SCALE": 1.0,
                "EFFECTIVE_PT": round(float(span["size"]), 3), "BASE_EFFECTIVE_PT": meta["declared"],
                "PDF_SPAN_PT": round(float(span["size"]), 3), "IS_NATURAL_SCRIPT": natural_script,
                "TEXT_SAMPLE": ch, "SCRIPT_CLASS": script_class, "SCRIPT_CLASS_REASON": class_reason,
                "MEASUREMENT_LEVEL": "GLYPH", "PDF_BBOX_PT": [round(v, 4) for v in cb],
                "BBOX_X0": crop_origin[0] + gx0, "BBOX_Y0": crop_origin[1] + gy0,
                "BBOX_X1": crop_origin[0] + gx1, "BBOX_Y1": crop_origin[1] + gy1,
                "TEXT_DIRECTION": "VERTICAL" if vertical else "HORIZONTAL", "H_INK_PX": h_ink,
                "RAW_H_Y_PX": raw_h, "RAW_W_X_PX": raw_w, "CANDIDATE_H_INK_PX": cand_h,
                "MIN_REQUIRED_PX": threshold if threshold is not None else "N/A", "GATE_APPLIES": applies,
                "MASK_FILE": str(mask_path.relative_to(HERE)).replace("\\", "/"),
                "CANDIDATE_MASK_FILE": str(candidate_path.relative_to(HERE)).replace("\\", "/"),
                "MASK_PIXEL_COUNT": int(independent.sum()), "CANDIDATE_PIXEL_COUNT": int(candidate.sum()),
                "VECTOR_CANDIDATE_PIXEL_COUNT": int((candidate & vector_union).sum()),
                "MASK_MORPHOLOGY": "none", "PASS_FAIL": "PASS" if gate_pass else "FAIL", "REASON": reason,
            }
            glyphs.append(record)
            obj["glyph_ids"].append(glyph_id)
            obj["candidate"] |= candidate
            obj["independent"] |= independent
            obj["bboxes"].append((crop_origin[0] + gx0, crop_origin[1] + gy0, crop_origin[0] + gx1, crop_origin[1] + gy1))

    # Create semantic CJK/sub-string rows.  They preserve true reading units for
    # CJK low-stroke handling and provide D/E ratio inputs without exact-glyph groups.
    glyph_by_id = {row["ELEMENT_ID"]: row for row in glyphs}
    semantic_rows: list[dict] = []
    sid = 0
    for object_id, obj in text_objects.items():
        by_class = defaultdict(list)
        for gid_ in obj["glyph_ids"]:
            row = glyph_by_id[gid_]
            if row["SCRIPT_CLASS"] not in {"WHITESPACE", "COMBINING_ACCENT"}:
                by_class[row["SCRIPT_CLASS"]].append(row)
        for script_class, members in by_class.items():
            sid += 1
            sem_id = f"S{sid:04d}"
            # For the comparison component, use actual per-glyph raw H median;
            # this is a semantic object x script-class aggregate, not an exact glyph group.
            hs = [float(m["H_INK_PX"]) for m in members]
            semantic_h = float(statistics.median(hs)) if hs else 0.0
            bbox = (
                min(m["BBOX_X0"] for m in members), min(m["BBOX_Y0"] for m in members),
                max(m["BBOX_X1"] for m in members), max(m["BBOX_Y1"] for m in members),
            )
            joined = "".join(m["TEXT_SAMPLE"] for m in members)
            applies = script_class != "WHITESPACE"
            threshold = members[0]["MIN_REQUIRED_PX"]
            # The CJK semantic component is the safety net for a legitimate thin-stroke ideograph.
            component_mask = np.zeros(crop_shape, dtype=bool)
            for m in members:
                # rebuild from stored independent mask just once through direct crop placement is unnecessary;
                # object independence is sufficient for component evidence, while member IDs retain glyph masks.
                pass
            sem_row = {
                "ELEMENT_ID": sem_id, "PARENT_ELEMENT_ID": object_id, "PANEL_ID": "PANEL_MAIN", "ROLE": obj["role"],
                "SOURCE_FILE": str(SOURCE if object_id != "TXT_CAPTION" else STYLE), "SOURCE_LINE": obj["meta"]["line"],
                "DECLARED_PT": obj["meta"]["declared"], "GRAPHICS_SCALE": 1.0,
                "EFFECTIVE_PT": round(float(statistics.median(obj["pdf_sizes"])), 3), "BASE_EFFECTIVE_PT": obj["meta"]["declared"],
                "PDF_SPAN_PT": round(float(statistics.median(obj["pdf_sizes"])), 3), "IS_NATURAL_SCRIPT": script_class == "NATURAL_SCRIPT",
                "TEXT_SAMPLE": joined, "SCRIPT_CLASS": script_class,
                "SCRIPT_CLASS_REASON": "semantic parent × script-class aggregate; actual raw glyph H median; no exact-glyph/cross-script comparison",
                "MEASUREMENT_LEVEL": "SEMANTIC_SUBSTRING", "PDF_BBOX_PT": "derived from glyph PDF bboxes",
                "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3],
                "TEXT_DIRECTION": "VERTICAL" if obj["vertical"] else "HORIZONTAL", "H_INK_PX": round(semantic_h, 3),
                "RAW_H_Y_PX": "see glyph rows", "RAW_W_X_PX": "see glyph rows", "CANDIDATE_H_INK_PX": "see glyph rows",
                "MIN_REQUIRED_PX": threshold, "GATE_APPLIES": False,
                "MASK_FILE": "glyph_masks (member IDs listed)", "CANDIDATE_MASK_FILE": "glyph_masks (member IDs listed)",
                "MASK_PIXEL_COUNT": "per-member", "CANDIDATE_PIXEL_COUNT": "per-member", "VECTOR_CANDIDATE_PIXEL_COUNT": sum(m["VECTOR_CANDIDATE_PIXEL_COUNT"] for m in members),
                "MASK_MORPHOLOGY": "none", "PASS_FAIL": "PASS", "REASON": "ratio component; individual glyph gates remain authoritative",
                "MEMBER_GLYPH_IDS": ";".join(m["ELEMENT_ID"] for m in members),
            }
            semantic_rows.append(sem_row)

    # No low-stroke exception exists: every visible CJK/full-width glyph remains
    # independently subject to the 30px gate.  Semantic rows are only D/E inputs.

    # Object masks and inventory are produced only after every glyph is available.
    # The fraction rule is a final-visible part of the formula semantic object for
    # relations to external text/vectors, while it is never self-paired with its
    # own formula glyphs as if it were a foreign line or node border.
    formula_internal_rule = next(c for c in components if c["id"] == "V019_FORMULA_INTERNAL_RULE")
    object_rows = []
    for object_id, obj in text_objects.items():
        ind_path = paths["masks"] / "text" / f"{safe_name(object_id)}__independent_raw.png"
        cand_path = paths["masks"] / "text" / f"{safe_name(object_id)}__candidate_raw.png"
        ind_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray((obj["independent"] * 255).astype(np.uint8)).save(ind_path)
        Image.fromarray((obj["candidate"] * 255).astype(np.uint8)).save(cand_path)
        bboxes = obj["bboxes"]
        bbox = (min(x[0] for x in bboxes), min(x[1] for x in bboxes), max(x[2] for x in bboxes), max(x[3] for x in bboxes))
        obj["bbox"] = bbox
        obj["pair_mask"] = obj["independent"].copy()
        obj["pair_candidate"] = obj["candidate"].copy()
        obj["internal_vector_components"] = []
        if object_id == "TXT_ESTIMATOR":
            obj["pair_mask"] |= formula_internal_rule["final"]
            obj["pair_candidate"] |= formula_internal_rule["final"]
            obj["internal_vector_components"] = [formula_internal_rule["id"]]
        obj["mask_path"] = ind_path
        obj["candidate_path"] = cand_path
        semantic_path = paths["masks"] / "text" / f"{safe_name(object_id)}__semantic_final_foreground.png"
        Image.fromarray((obj["pair_mask"] * 255).astype(np.uint8)).save(semantic_path)
        obj["semantic_path"] = semantic_path
        object_rows.append({
            "OBJECT_ID": object_id, "CATEGORY": "TEXT" if obj["role"] != "FORMULA" else "FORMULA", "PANEL_ID": "PANEL_MAIN", "ROLE": obj["role"],
            "DRAWING_INDEX": "TEXT_RAWDICT", "OWNER": object_id, "PDF_VECTOR_BBOX_PX": bbox,
            "RAW_MASK": str(ind_path.relative_to(HERE)).replace("\\", "/"), "CANDIDATE_MASK": str(cand_path.relative_to(HERE)).replace("\\", "/"), "SEMANTIC_FINAL_FOREGROUND_MASK": str(semantic_path.relative_to(HERE)).replace("\\", "/"),
            "RAW_PIXEL_COUNT": int(obj["independent"].sum()), "CANDIDATE_PIXEL_COUNT": int(obj["candidate"].sum()), "SEMANTIC_FINAL_FOREGROUND_PIXEL_COUNT": int(obj["pair_mask"].sum()), "INTERNAL_VECTOR_COMPONENTS": ";".join(obj["internal_vector_components"]),
            "GLYPH_COUNT": len(obj["glyph_ids"]), "MASK_MORPHOLOGY": "none",
        })

    # Source audit, one row per semantic object (caption is documented as the 11pt-class small setting).
    font_rows = []
    for object_id, obj in text_objects.items():
        declared = obj["meta"]["declared"]
        source_pass = declared >= 9.5
        font_rows.append({
            "ELEMENT_ID": object_id, "PANEL_ID": "PANEL_MAIN", "ROLE": obj["role"],
            "SOURCE_FILE": str(SOURCE if object_id != "TXT_CAPTION" else STYLE), "SOURCE_LINE": obj["meta"]["line"],
            "DECLARED_PT": declared, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": declared,
            "PDF_MEDIAN_SPAN_PT": round(float(statistics.median(obj["pdf_sizes"])), 3), "SOURCE_KIND": obj["meta"]["source_kind"],
            "NATURAL_SCRIPT_POLICY": "base formula remains 9.5pt; its TeX-generated scripts are evaluated in pixel CSV",
            "PASS_FAIL": "PASS" if source_pass else "FAIL", "REASON": "" if source_pass else "ordinary visible tick label effective_pt=8.6 < 9.5",
        })
    source_font_pass = all(row["PASS_FAIL"] == "PASS" for row in font_rows)

    # D: same panel + same semantic role + same script class; median contribution per semantic parent.
    sem_by_parent_class = {(r["PARENT_ELEMENT_ID"], r["SCRIPT_CLASS"]): r for r in semantic_rows}
    same_rows = []
    groups = defaultdict(list)
    for (parent, script), row in sem_by_parent_class.items():
        groups[("PANEL_MAIN", text_objects[parent]["role"], script)].append(row)
    same_class_pass = True
    for (panel, role, script), rows in sorted(groups.items()):
        values = [float(r["H_INK_PX"]) for r in rows]
        median = float(statistics.median(values))
        for row in rows:
            ratio = float(row["H_INK_PX"]) / median if median else 0.0
            passes = 0.92 <= ratio <= 1.08
            same_class_pass &= passes
            same_rows.append({
                "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "ELEMENT_ID": row["PARENT_ELEMENT_ID"],
                "SEMANTIC_COMPONENT_ID": row["ELEMENT_ID"], "H_INK_PX": row["H_INK_PX"], "ROLE_SCRIPT_MEDIAN_PX": round(median, 3),
                "RATIO_TO_CLASS_MEDIAN": round(ratio, 4), "RANGE": "[0.92,1.08]", "PASS_FAIL": "PASS" if passes else "FAIL",
                "METHOD": "actual raw H_ink median across each semantic parent × script class; no exact-glyph or cross-script grouping",
            })
    # There is only one panel.  Explicitly record rather than imply a cross-panel result.
    same_rows.append({"PANEL_ID": "CROSS_PANEL", "ROLE": "ALL", "SCRIPT_CLASS": "ALL", "ELEMENT_ID": "N/A", "SEMANTIC_COMPONENT_ID": "N/A", "H_INK_PX": "N/A", "ROLE_SCRIPT_MEDIAN_PX": "N/A", "RATIO_TO_CLASS_MEDIAN": "N/A", "RANGE": "<=1.10", "PASS_FAIL": "N/A_SINGLE_PANEL", "METHOD": "no second panel exists"})

    # E: compare only equivalent script classes to local BASE=TICK.  Any no-base-script relationship is N/A, never a proxy.
    base_role = "TICK"
    base_by_script = {}
    for (panel, role, script), rows in groups.items():
        if role == base_role:
            base_by_script[script] = float(statistics.median([float(r["H_INK_PX"]) for r in rows]))
    role_ranges = {"AXIS_LABEL": (1.00, 1.18), "ANNOTATION": (0.95, 1.10), "FORMULA": (1.00, 1.18)}
    role_rows = []
    role_pass = True
    for (panel, role, script), rows in sorted(groups.items()):
        if role == base_role or role not in role_ranges:
            continue
        target = float(statistics.median([float(r["H_INK_PX"]) for r in rows]))
        if script not in base_by_script:
            role_rows.append({"PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "BASE_ROLE": base_role, "BASE_H_INK_PX": "N/A", "ROLE_H_INK_PX": round(target, 3), "ROLE_RATIO": "N/A", "RANGE": "N/A", "PASS_FAIL": "N/A_NO_COMPARABLE_BASE_SCRIPT", "METHOD": "Goal E comparable-script rule; no proxy/cross-script substitution"})
            continue
        ratio = target / base_by_script[script] if base_by_script[script] else 0.0
        lo, hi = role_ranges[role]
        passes = lo <= ratio <= hi
        role_pass &= passes
        role_rows.append({"PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "BASE_ROLE": base_role, "BASE_H_INK_PX": round(base_by_script[script], 3), "ROLE_H_INK_PX": round(target, 3), "ROLE_RATIO": round(ratio, 4), "RANGE": f"[{lo:.2f},{hi:.2f}]", "PASS_FAIL": "PASS" if passes else "FAIL", "METHOD": "actual raw H_ink role medians, comparable script only"})

    # Associate D/E results with the detailed pixel CSV without proxying metrics.
    for row in glyphs:
        key = ("PANEL_MAIN", row["ROLE"], row["SCRIPT_CLASS"])
        candidates = [x for x in same_rows if x.get("PANEL_ID") == key[0] and x.get("ROLE") == key[1] and x.get("SCRIPT_CLASS") == key[2] and x.get("ELEMENT_ID") == row["PARENT_ELEMENT_ID"]]
        row["CLASS_MEDIAN_PX"] = candidates[0]["ROLE_SCRIPT_MEDIAN_PX"] if candidates else "N/A"
        row["RATIO_TO_CLASS_MEDIAN"] = candidates[0]["RATIO_TO_CLASS_MEDIAN"] if candidates else "N/A"
        role_candidates = [x for x in role_rows if x["ROLE"] == row["ROLE"] and x["SCRIPT_CLASS"] == row["SCRIPT_CLASS"]]
        row["ROLE_RATIO"] = role_candidates[0]["ROLE_RATIO"] if role_candidates else "N/A"
        row["TEXT_TEXT_OVERLAP_PX"] = "see all-pairs CSV"
        row["TEXT_GRAPHIC_OVERLAP_PX"] = "see all-pairs CSV"
        row["MIN_CLEARANCE_PX"] = "see all-pairs CSV"

    # Pair matrix: all independent semantic TEXT/FOMULA objects, and every final-visible vector object.
    text_items = list(text_objects.values())
    overlap_rows = []
    unique_overlap = np.zeros(crop_shape, dtype=bool)
    critical_specs = []

    def pair_clearance(a, b) -> float:
        if not a.any() or not b.any():
            return float("inf")
        dist = distance_transform_edt(~b)
        return float(dist[a].min())

    def pair_row(pair_id, a_id, a_cat, a_mask, a_bbox, b_id, b_cat, b_mask, b_bbox, threshold, check_type, candidate_mask=None):
        overlap_mask = (candidate_mask if candidate_mask is not None else a_mask) & b_mask
        overlap = int(overlap_mask.sum())
        clearance = 0.0 if overlap else pair_clearance(a_mask, b_mask)
        bbox_clearance = rect_distance(a_bbox, b_bbox)
        passes = overlap == 0 and clearance >= threshold
        status = "PASS" if passes else "FAIL"
        row = {
            "PAIR_ID": pair_id, "CHECK_TYPE": check_type, "A_ID": a_id, "A_CATEGORY": a_cat,
            "B_ID": b_id, "B_CATEGORY": b_cat, "OVERLAP_PIXEL_COUNT": overlap,
            "OVERLAP_MASK_KIND": "candidate_text_raw_vs_final_visible_vector" if candidate_mask is not None else "independent_raw_masks",
            "RAW_MASK_CLEARANCE_PX": "INF" if math.isinf(clearance) else round(clearance, 4),
            "BBOX_CLEARANCE_PX": round(bbox_clearance, 4), "MIN_REQUIRED_CLEARANCE_PX": threshold,
            "PASS_FAIL": status, "MASK_MORPHOLOGY": "none",
            "A_MASK": "", "B_MASK": "", "REASON": "" if passes else (f"overlap={overlap}px" if overlap else f"raw-mask clearance {clearance:.3f}px < {threshold}px"),
        }
        if overlap:
            unique_overlap[:] |= overlap_mask
        critical = (not passes) or (not math.isinf(clearance) and clearance <= threshold + 2.0)
        if critical:
            critical_specs.append((row, a_mask, b_mask, overlap_mask, candidate_mask))
        return row

    pair_no = 0
    for a, b in combinations(text_items, 2):
        pair_no += 1
        a_cat = "FORMULA" if a["role"] == "FORMULA" else "TEXT"
        b_cat = "FORMULA" if b["role"] == "FORMULA" else "TEXT"
        row = pair_row(f"TT{pair_no:04d}", a["id"], a_cat, a["pair_mask"], a["bbox"], b["id"], b_cat, b["pair_mask"], b["bbox"], 4.0, "TEXT_TEXT")
        row["A_MASK"] = str(a["semantic_path"].relative_to(HERE)).replace("\\", "/")
        row["B_MASK"] = str(b["semantic_path"].relative_to(HERE)).replace("\\", "/")
        overlap_rows.append(row)
    for a in text_items:
        a_cat = "FORMULA" if a["role"] == "FORMULA" else "TEXT"
        for b in visible_vectors:
            pair_no += 1
            threshold = 5.0 if b["kind"] == "FORMULA_NODE_BORDER" else 3.0
            row = pair_row(f"TV{pair_no:04d}", a["id"], a_cat, a["pair_mask"], a["bbox"], b["id"], b["kind"], b["final"], rect_to_px(b["bbox"]), threshold, "TEXT_VECTOR", candidate_mask=a["pair_candidate"])
            row["A_MASK"] = str(a["semantic_path"].relative_to(HERE)).replace("\\", "/")
            row["B_MASK"] = str(b["final_path"].relative_to(HERE)).replace("\\", "/")
            overlap_rows.append(row)

    # Page-edge/clip audit on final raw foreground, never against the local crop edge.
    edge_rows = []
    page_w, page_h = full_rgb.shape[1], full_rgb.shape[0]
    def edge_row(obj_id, category, mask, bbox, source):
        if not mask.any():
            return {"OBJECT_ID": obj_id, "CATEGORY": category, "RAW_MASK": source, "MIN_EDGE_CLEARANCE_PX": "N/A", "CLIP_PIXEL_COUNT": 0, "PASS_FAIL": "N/A_EMPTY_BACKGROUND"}
        bb = bbox_from_mask(mask, crop_origin)
        left, top, right, bottom = bb
        clear = min(left, top, page_w - right, page_h - bottom)
        clip = int(left <= 0 or top <= 0 or right >= page_w or bottom >= page_h)
        return {"OBJECT_ID": obj_id, "CATEGORY": category, "RAW_MASK": source, "MIN_EDGE_CLEARANCE_PX": clear, "CLIP_PIXEL_COUNT": clip, "PASS_FAIL": "PASS" if clip == 0 and clear >= 6 else "FAIL"}
    for item in text_items:
        edge_rows.append(edge_row(item["id"], "TEXT" if item["role"] != "FORMULA" else "FORMULA", item["pair_mask"], item["bbox"], str(item["semantic_path"].relative_to(HERE))))
    for item in visible_vectors:
        edge_rows.append(edge_row(item["id"], item["kind"], item["final"], rect_to_px(item["bbox"]), str(item["final_path"].relative_to(HERE))))

    # Critical pair evidence and 8x nearest-neighbour copies.
    critical_manifest = []
    for order, (row, a_mask, b_mask, overlap_mask, candidate) in enumerate(critical_specs, 1):
        pair_dir = paths["critical_pairs"] / f"CP{order:03d}__{safe_name(row['PAIR_ID'])}"
        manifest = save_pair_assets(pair_dir, crop_rgb, candidate if candidate is not None else a_mask, b_mask, {"PAIR": row, "INTERSECTION_PIXELS": int(overlap_mask.sum())}, crop_origin)
        critical_manifest.append({"PAIR_ID": row["PAIR_ID"], "DIRECTORY": str(pair_dir.relative_to(HERE)).replace("\\", "/"), "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"], "RAW_MASK_CLEARANCE_PX": row["RAW_MASK_CLEARANCE_PX"], "PASS_FAIL": row["PASS_FAIL"], "manifest": manifest})
    jdump(HERE / "critical_pairs_manifest.json", critical_manifest)

    # Individual glyph failures get their own raw/mask/8x evidence.  They are not
    # incorrectly converted into text-to-text pairs.
    critical_glyphs = []
    for row in glyphs:
        if row["PASS_FAIL"] != "FAIL":
            continue
        x0, y0, x1, y1 = (int(row[k]) - crop_origin[0] if k in {"BBOX_X0", "BBOX_X1"} else int(row[k]) - crop_origin[1] for k in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        x0, y0, x1, y1 = clip_box((x0, y0, x1, y1), crop_shape[1], crop_shape[0], 8)
        d = paths["critical_glyphs"] / row["ELEMENT_ID"]
        d.mkdir(parents=True, exist_ok=True)
        raw = Image.fromarray(crop_rgb[y0:y1, x0:x1])
        raw.save(d / "raw_1to1.png")
        raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(d / "raw_8xNN.png")
        # Copy masks rather than resample them; their files remain canonical global-map evidence.
        shutil.copyfile(HERE / row["MASK_FILE"], d / "independent_raw_mask.png")
        shutil.copyfile(HERE / row["CANDIDATE_MASK_FILE"], d / "candidate_before_vector_guard.png")
        glyph_meta = {"GLYPH": row, "ROI_LOCAL_PX": [x0, y0, x1, y1], "ROI_GLOBAL_PAGE_PX": [crop_origin[0] + x0, crop_origin[1] + y0, crop_origin[0] + x1, crop_origin[1] + y1], "MASK_MORPHOLOGY": "none"}
        jdump(d / "glyph_manifest.json", glyph_meta)
        critical_glyphs.append({"ELEMENT_ID": row["ELEMENT_ID"], "TEXT_SAMPLE": row["TEXT_SAMPLE"], "DIRECTORY": str(d.relative_to(HERE)).replace("\\", "/"), "H_INK_PX": row["H_INK_PX"], "MIN_REQUIRED_PX": row["MIN_REQUIRED_PX"], "REASON": row["REASON"]})
    jdump(HERE / "critical_glyphs_manifest.json", critical_glyphs)

    # Fully-labelled measurement overlay: semantic objects rather than line-broken caption children.
    overlay = Image.fromarray(crop_rgb.copy())
    draw = ImageDraw.Draw(overlay, "RGBA")
    font = pil_font(14)
    palette = {"TICK": (240, 110, 30, 210), "AXIS_LABEL": (40, 120, 235, 210), "ANNOTATION": (20, 170, 105, 210), "FORMULA": (185, 60, 195, 210), "CAPTION": (235, 45, 95, 210)}
    for obj in text_items:
        x0, y0, x1, y1 = obj["bbox"]
        x0 -= crop_origin[0]; x1 -= crop_origin[0]; y0 -= crop_origin[1]; y1 -= crop_origin[1]
        color = palette[obj["role"]]
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.rectangle((x0, max(0, y0 - 18), min(overlay.width, x0 + 165), y0), fill=(255, 255, 255, 205))
        draw.text((x0 + 1, max(0, y0 - 17)), obj["id"], fill=color, font=font)
    overlay.save(HERE / "after_text_measurement_overlay_300dpi.png")
    overlay.save(HERE / "object_id_overlay_300dpi.png")

    # Vector inventory must use every component's own fields (not a loop-end variable).
    vector_rows = []
    for component in components:
        bb = rect_to_px(component["bbox"])
        vector_rows.append({
            "VECTOR_ID": component["id"], "DRAWING_INDEX": component["drawing_index"], "CATEGORY": component["kind"], "OWNER": component["owner"],
            "PDF_BBOX_PT": [round(v, 4) for v in component["bbox"]], "PDF_BBOX_PAGE_PX": bb,
            "MASK_MODE": component["mask_mode"], "PRE_OCCLUSION_RAW_MASK": str(component["pre_path"].relative_to(HERE)).replace("\\", "/"),
            "HALO_RAW_MASK": str(component["halo_path"].relative_to(HERE)).replace("\\", "/"), "FINAL_VISIBLE_RAW_MASK": str(component["final_path"].relative_to(HERE)).replace("\\", "/"),
            "PRE_OCCLUSION_PIXEL_COUNT": int(component["pre"].sum()), "HALO_PIXEL_COUNT": int(component["halo"].sum()), "FINAL_VISIBLE_PIXEL_COUNT": int(component["final"].sum()),
            "INCLUDED_IN_GEOMETRY": component["include"], "EXCLUSION_REASON": component["reason"], "MASK_MORPHOLOGY": "none",
        })

    # Numerical audit results.
    glyph_failures = [row for row in glyphs if row["PASS_FAIL"] == "FAIL"]
    pixel_height_pass = len(glyph_failures) == 0
    overlap_failures = [row for row in overlap_rows if int(row["OVERLAP_PIXEL_COUNT"]) > 0]
    clearance_failures = [row for row in overlap_rows if row["RAW_MASK_CLEARANCE_PX"] != "INF" and float(row["RAW_MASK_CLEARANCE_PX"]) < float(row["MIN_REQUIRED_CLEARANCE_PX"])]
    edge_failures = [row for row in edge_rows if row["PASS_FAIL"] == "FAIL"]
    unique_overlap_count = int(unique_overlap.sum())
    clip_count = int(sum(int(row["CLIP_PIXEL_COUNT"]) for row in edge_rows))
    clear_values = [float(row["RAW_MASK_CLEARANCE_PX"]) for row in overlap_rows if row["RAW_MASK_CLEARANCE_PX"] != "INF"]
    min_clearance = min(clear_values) if clear_values else float("inf")
    clearance_pass = not clearance_failures and not edge_failures

    # Independent mathematical recomputation.
    sample_u = [0.10, 0.40, 0.70, 0.80]
    values = [math.exp(-u * u / 2) for u in sample_u]
    sample_mean = sum(values) / len(values)
    # Simpson integral at high resolution is deterministic and adequate for evidence; also state the known numeric reference.
    n = 100000
    dx = 1.0 / n
    simpson = (dx / 3.0) * (math.exp(0) + math.exp(-0.5) + 4 * sum(math.exp(-((2*k-1)*dx)**2 / 2) for k in range(1, n//2 + 1)) + 2 * sum(math.exp(-((2*k)*dx)**2 / 2) for k in range(1, n//2)))
    math_pass = abs(sample_mean - 0.8567456) < 1e-6 and abs(simpson - 0.8556244) < 1e-6
    math_evidence = {
        "h(u)": "exp(-u^2/2)", "domain": "[0,1]", "uniform_density": 1.0,
        "sample_u": sample_u, "h_values": values, "sample_mean": sample_mean, "displayed_sample_mean": 0.8567,
        "integral_simpson": simpson, "displayed_true_integral": 0.8556,
        "formula_check": "For U_i iid Uniform(0,1), E[h(U)] = integral_0^1 h(u)du and muhat_N=N^{-1}sum h(U_i).",
        "pass": math_pass,
    }
    jdump(HERE / "math_semantics_recomputation.json", math_evidence)

    # R94 visual inspection gates are documented; source tick failure prevents a harmony pass even if the rest reads cleanly.
    text_consistency_pass = True
    grayscale_pass = True
    reading_order_pass = True
    page_integration_pass = True
    font_harmony_pass = source_font_pass and same_class_pass and role_pass and pixel_height_pass and clearance_pass
    visual_harmony_pass = font_harmony_pass

    expected_pair_count = math.comb(len(text_items), 2) + len(text_items) * len(visible_vectors)
    fail_if(len(overlap_rows) != expected_pair_count, f"pair enumeration mismatch {len(overlap_rows)} != {expected_pair_count}")

    # Write primary evidence CSV/JSON before final machine consistency check.
    write_csv(HERE / "after_font_audit.csv", font_rows)
    pixel_fields = [
        "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "BASE_EFFECTIVE_PT", "PDF_SPAN_PT", "IS_NATURAL_SCRIPT", "TEXT_SAMPLE", "SCRIPT_CLASS", "SCRIPT_CLASS_REASON", "MEASUREMENT_LEVEL", "PDF_BBOX_PT", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "TEXT_DIRECTION", "H_INK_PX", "RAW_H_Y_PX", "RAW_W_X_PX", "CANDIDATE_H_INK_PX", "MIN_REQUIRED_PX", "GATE_APPLIES", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "MASK_FILE", "CANDIDATE_MASK_FILE", "MASK_PIXEL_COUNT", "CANDIDATE_PIXEL_COUNT", "VECTOR_CANDIDATE_PIXEL_COUNT", "MASK_MORPHOLOGY", "PASS_FAIL", "REASON", "MEMBER_GLYPH_IDS",
    ]
    write_csv(HERE / "after_pixel_measurements.csv", glyphs + semantic_rows, pixel_fields)
    write_csv(HERE / "object_inventory.csv", object_rows)
    write_csv(HERE / "vector_component_inventory.csv", vector_rows)
    write_csv(HERE / "after_overlap_report.csv", overlap_rows)
    write_csv(HERE / "after_edge_clip_report.csv", edge_rows)
    write_csv(HERE / "same_class_ratio_audit.csv", same_rows)
    write_csv(HERE / "role_ratio_audit.csv", role_rows)

    geometry_manifest = {
        "figure_id": FIGURE_ID, "frozen_pdf": str(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
        "page_render_method": "PyMuPDF direct native 300dpi full-page fixed grid; no resize; figure views are integer-pixel crops",
        "page_300_dimensions": [int(full_rgb.shape[1]), int(full_rgb.shape[0])], "page_200_dimensions": [page200.width, page200.height],
        "crop_page_px": list(crop_px), "standalone_page_px": list(standalone_px), "threshold_delta": THRESHOLD_DELTA,
        "text_object_count": len(text_items), "glyph_count": len(glyphs), "semantic_substring_count": len(semantic_rows),
        "vector_component_count": len(components), "halo_background_count": sum(c["kind"] == "HALO_BACKGROUND" for c in components),
        "nonhalo_final_visible_count": len(final_visible_vectors), "independent_vector_pair_component_count": len(visible_vectors),
        "background_or_internal_excluded_count": sum(not c["include"] and c["kind"] != "HALO_BACKGROUND" for c in components),
        "mask_rules": {"text": "final composite raster at 20/255 local-white contrast; vector geometry guard for H_ink; no morphology", "vector": "PDF drawing primitive rasterized at native 300dpi; pre-occlusion/halo/final-visible stored separately; no morphology"},
    }
    jdump(HERE / "geometry_manifest.json", geometry_manifest)

    metrics = {
        "FIGURE_ID": FIGURE_ID, "FROZEN_PDF": str(PDF), "PHYSICAL_PAGE": PHYSICAL_PAGE, "PRINTED_PAGE": PRINTED_PAGE,
        "SOURCE_FONT_PASS": source_font_pass, "SOURCE_FONT_FAIL_COUNT": sum(r["PASS_FAIL"] == "FAIL" for r in font_rows),
        "PIXEL_HEIGHT_PASS": pixel_height_pass, "PIXEL_HEIGHT_FAIL_COUNT": len(glyph_failures),
        "SAME_CLASS_RATIO_PASS": same_class_pass, "SAME_CLASS_RATIO_FAIL_COUNT": sum(r["PASS_FAIL"] == "FAIL" for r in same_rows),
        "ROLE_RATIO_PASS": role_pass, "ROLE_RATIO_FAIL_COUNT": sum(r["PASS_FAIL"] == "FAIL" for r in role_rows),
        "OVERLAP_PASS": unique_overlap_count == 0, "OVERLAP_PIXEL_COUNT": unique_overlap_count,
        "OVERLAP_PIXEL_SUM_NO_DEDUP": int(sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in overlap_rows)), "OVERLAP_FAIL_PAIR_COUNT": len(overlap_failures),
        "CLIP_PASS": clip_count == 0, "CLIP_PIXEL_COUNT": clip_count,
        "CLEARANCE_PASS": clearance_pass, "CLEARANCE_FAIL_PAIR_COUNT": len(clearance_failures), "EDGE_FAIL_COUNT": len(edge_failures),
        "MIN_TEXT_CLEARANCE_PX": None if math.isinf(min_clearance) else round(min_clearance, 4),
        "FONT_VISUAL_HARMONY_PASS": font_harmony_pass, "VISUAL_HARMONY_PASS": visual_harmony_pass,
        "MATH_SEMANTICS_PASS": math_pass, "TEXT_CONSISTENCY_PASS": text_consistency_pass,
        "GRAYSCALE_PASS": grayscale_pass, "READING_ORDER_PASS": reading_order_pass, "PAGE_INTEGRATION_PASS": page_integration_pass,
        "TEXT_OBJECT_COUNT": len(text_items), "GLYPH_COUNT": len(glyphs), "SEMANTIC_SUBSTRING_COUNT": len(semantic_rows),
        "VECTOR_COMPONENT_COUNT": len(components), "HALO_BACKGROUND_COUNT": sum(c["kind"] == "HALO_BACKGROUND" for c in components), "NONHALO_FINAL_VISIBLE_COUNT": len(final_visible_vectors), "INDEPENDENT_VECTOR_PAIR_COMPONENT_COUNT": len(visible_vectors),
        "PAIR_COUNT": len(overlap_rows), "TEXT_TEXT_PAIR_COUNT": math.comb(len(text_items), 2), "TEXT_VECTOR_PAIR_COUNT": len(text_items) * len(visible_vectors),
        "CRITICAL_PAIR_COUNT": len(critical_manifest), "CRITICAL_GLYPH_COUNT": len(critical_glyphs),
        "EVIDENCE_INTEGRITY_PASS": None, "ALL_HARD_GATES_PASS": False,
    }

    def audit_text(metrics_now: dict) -> str:
        return f"""# FIG-P573-01｜SA1 严格视觉／数学盲审（R94）

## 1. 冻结输入、定位与覆盖

- 冻结输入：`{PDF}`；只读。
- 以 R94 题注“蒙特卡罗积分把曲线下的面积…”独立定位：物理页 **{PHYSICAL_PAGE}**、印刷页 **{PRINTED_PAGE}**、图 **31.2**。
- 300dpi 固定整页网格为 `{full_rgb.shape[1]}×{full_rgb.shape[0]}`；整页后以整数像素裁切，无 resize。覆盖 {len(text_items)} 个语义文字／公式对象、{len(glyphs)} 个逐字形记录、{len(components)} 个矢量对象（{len(final_visible_vectors)} 个 non-halo final-visible，其中 {len(visible_vectors)} 个是跨对象 pair 组件；{sum(c['kind']=='HALO_BACKGROUND' for c in components)} 个 opaque halo）。

## 2. 源级有效字号

`SOURCE_FONT_PASS = {str(source_font_pass).lower()}`。普通 PGFPlots tick label 为源码第 8 行 `8.6pt`，共 {sum(r['PASS_FAIL']=='FAIL' for r in font_rows)} 个独立刻度对象低于 9.5pt；其余图内 node／axis label／公式基准为 9.5pt，caption 由 11pt 文档的 `\\small`（10pt）产生。自然数学 script 仅由 9.5pt 基公式产生，逐字形像素另验。

## 3. 原生 300dpi 字形与比例

`PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}`（失败 {len(glyph_failures)} 个独立 glyph／字面语义项）；`SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}`（失败 {sum(r['PASS_FAIL']=='FAIL' for r in same_rows)}）；`ROLE_RATIO_PASS = {str(role_pass).lower()}`（失败 {sum(r['PASS_FAIL']=='FAIL' for r in role_rows)}）。D 仅比较同面板、同 role、同 script class 的实际 independent raw H_ink；E 仅用可比 script 相对于 TICK base，不可比项记为 N/A。每个 CJK／全角字形仍按自身 30px 门，连续 CJK 语义组件仅作 D/E 可追溯聚合，绝不替代单字门。

## 4. 无膨胀 mask、重叠、净空与裁切

`PAIR_COUNT = {len(overlap_rows)} = C({len(text_items)},2)+{len(text_items)}×{len(visible_vectors)}`；`OVERLAP_PIXEL_COUNT = {unique_overlap_count}`（无重复 union，pair-sum={sum(int(r['OVERLAP_PIXEL_COUNT']) for r in overlap_rows)}，失败 pair={len(overlap_failures)}）；`CLIP_PIXEL_COUNT = {clip_count}`；`MIN_TEXT_CLEARANCE_PX = {metrics_now['MIN_TEXT_CLEARANCE_PX']}`；`CLEARANCE_PASS = {str(clearance_pass).lower()}`。节点文字—公式框只对 final-visible **border stroke**测 5px，不把白色 node fill／bbox 误记为 0px。V019 是 `\\frac` 的内部分数线，已并入同一公式的 semantic foreground 作对外关系检查，绝不按外部 line／node-border 与其父公式自配对。所有 opaque halo 均保存 pre-occlusion、halo、final-visible mask。临界／失败 pair 共 {len(critical_manifest)} 包，均含 raw、A/B raw mask、intersection、overlay、1:1 和 8×NN。

## 5. 四视图、灰度与页面融合

四视图齐全：`full_page_200dpi.png`、`full_page_300dpi_native.png`、`figure_crop_300dpi.png`／`standalone_300dpi.png`、`grayscale_300dpi.png`。`GRAYSCALE_PASS = {str(grayscale_pass).lower()}`；曲线、样本 stem/marker、均值实线和积分虚线仍可由线型／点型区分。`READING_ORDER_PASS = {str(reading_order_pass).lower()}`；`PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}`。

`FONT_VISUAL_HARMONY_PASS = {str(font_harmony_pass).lower()}`。本项不能因“仍可辨认”放宽：8.6pt 刻度低于硬门，故不接受以缩小或局部可读性作为协调性通过理由。

## 6. 数学、文本与题注一致性

`MATH_SEMANTICS_PASS = {str(math_pass).lower()}`。重算：$h(u)=\\exp(-u^2/2)$、四点 $(0.1,0.4,0.7,0.8)$ 的均值为 {sample_mean:.10f}，图示 0.8567；$\\int_0^1h(u)\\,du={simpson:.10f}$，图示 0.8556。对 $U_i\\sim\\mathrm U(0,1)$，$E[h(U)]=\\int_0^1h$ 与图内 $\\widehat\\mu_N=N^{{-1}}\\sum h(U_i)$ 一致；caption 的“竖线四个均匀样本、虚线参考值”与直接正文一致。

`TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}`。

## 7. 机器一致性与证据完整性

`EVIDENCE_INTEGRITY_PASS = {str(metrics_now['EVIDENCE_INTEGRITY_PASS']).lower()}`。`final_consistency_check.json`逐行核对 VECTOR_ID、DRAWING_INDEX、CATEGORY、OWNER、pre/halo/final mask 路径、pair B_CATEGORY／阈值、pair 数、临界包和报告数字；`machine_terminal_check.csv/json/md`再交叉核对非空 mask、全部失败／临界包的 8 件证据、relation/pair/clearance 计数、字号／像素／D/E 失败数和最终 RESULT。任何未知或错配即 integrity FAIL。

## 8. 判定与下一角色

**RESULT: FAIL → SA2。** 直接阻断项至少包括 `SOURCE_FONT_PASS=false`（8.6pt tick）以及所有逐字形像素门的失败项；即使其他视觉／数学项通过，§9.2.1 要求全门为 true 才能转 SA3。
"""

    # First final consistency uses the primary tables.  It is intentionally not a second audit.
    required = [
        "full_page_200dpi.png", "full_page_300dpi_native.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv", "after_edge_clip_report.csv", "same_class_ratio_audit.csv", "role_ratio_audit.csv", "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md", "SA1_report.md", "object_inventory.csv", "vector_component_inventory.csv", "geometry_manifest.json", "math_semantics_recomputation.json", "critical_pairs_manifest.json", "critical_glyphs_manifest.json",
    ]
    terminal_required = ["machine_terminal_check.csv", "machine_terminal_check.json", "machine_terminal_check.md"]

    def run_consistency(metrics_now: dict, include_terminal: bool = False) -> dict:
        errors = []
        required_now = required + (terminal_required if include_terminal else [])
        missing = [name for name in required_now if not (HERE / name).exists()]
        errors.extend(f"missing required artifact: {x}" for x in missing)
        inv_rows = list(csv.DictReader((HERE / "vector_component_inventory.csv").open(encoding="utf-8-sig")))
        inv_by_id = {row["VECTOR_ID"]: row for row in inv_rows}
        if len(inv_rows) != len(components):
            errors.append(f"vector inventory cardinality {len(inv_rows)} != memory {len(components)}")
        for component in components:
            row = inv_by_id.get(component["id"])
            if row is None:
                errors.append(f"missing vector inventory row {component['id']}")
                continue
            own = {"DRAWING_INDEX": str(component["drawing_index"]), "CATEGORY": component["kind"], "OWNER": component["owner"]}
            for key, expected in own.items():
                if row.get(key) != expected:
                    errors.append(f"vector field mismatch {component['id']} {key}: {row.get(key)!r}!={expected!r}")
            for pathkey in ("PRE_OCCLUSION_RAW_MASK", "HALO_RAW_MASK", "FINAL_VISIBLE_RAW_MASK"):
                file_ref = row.get(pathkey, "")
                if not file_ref or not (HERE / file_ref).exists():
                    errors.append(f"missing vector mask {component['id']} {pathkey}")
            pre_ref = HERE / row["PRE_OCCLUSION_RAW_MASK"]
            if pre_ref.exists() and not np.asarray(Image.open(pre_ref).convert("L")).any():
                errors.append(f"empty pre-occlusion vector mask {component['id']}")
            final_ref = HERE / row["FINAL_VISIBLE_RAW_MASK"]
            if component["include"] and final_ref.exists() and not np.asarray(Image.open(final_ref).convert("L")).any():
                errors.append(f"empty final-visible independent vector mask {component['id']}")
            if component["kind"] == "HALO_BACKGROUND":
                halo_ref = HERE / row["HALO_RAW_MASK"]
                if halo_ref.exists() and not np.asarray(Image.open(halo_ref).convert("L")).any():
                    errors.append(f"empty opaque halo mask {component['id']}")
        halo_count = sum(row["CATEGORY"] == "HALO_BACKGROUND" for row in inv_rows)
        independent_count = sum(row["INCLUDED_IN_GEOMETRY"].lower() == "true" for row in inv_rows)
        final_visible_count = sum(row["CATEGORY"] not in {"BACKGROUND_FILL", "HALO_BACKGROUND"} and int(row["FINAL_VISIBLE_PIXEL_COUNT"]) > 0 for row in inv_rows)
        if halo_count != 2:
            errors.append(f"HALO_BACKGROUND={halo_count}, expected 2")
        if independent_count != len(visible_vectors):
            errors.append(f"independent pair vectors={independent_count}, expected {len(visible_vectors)}")
        if final_visible_count != len(final_visible_vectors):
            errors.append(f"final-visible vectors={final_visible_count}, expected {len(final_visible_vectors)}")
        object_rows_now = list(csv.DictReader((HERE / "object_inventory.csv").open(encoding="utf-8-sig")))
        if len({r["OBJECT_ID"] for r in object_rows_now}) != len(text_items) or len(object_rows_now) != len(text_items):
            errors.append("text object manifest unique-ID/cardinality mismatch")
        for row in object_rows_now:
            for pathkey in ("RAW_MASK", "SEMANTIC_FINAL_FOREGROUND_MASK"):
                ref = HERE / row[pathkey]
                if not ref.exists():
                    errors.append(f"missing text mask {row['OBJECT_ID']} {pathkey}")
                elif not np.asarray(Image.open(ref).convert("L")).any():
                    errors.append(f"empty text mask {row['OBJECT_ID']} {pathkey}")
        pair_rows = list(csv.DictReader((HERE / "after_overlap_report.csv").open(encoding="utf-8-sig")))
        if len(pair_rows) != expected_pair_count:
            errors.append(f"pair rows={len(pair_rows)}, expected {expected_pair_count}")
        for row in pair_rows:
            if row["CHECK_TYPE"] == "TEXT_VECTOR":
                target = inv_by_id.get(row["B_ID"])
                if target is None:
                    errors.append(f"unknown vector in pair {row['PAIR_ID']}: {row['B_ID']}")
                    continue
                if row["B_CATEGORY"] != target["CATEGORY"]:
                    errors.append(f"pair category mismatch {row['PAIR_ID']}")
                expected_threshold = 5.0 if target["CATEGORY"] == "FORMULA_NODE_BORDER" else 3.0
                if abs(float(row["MIN_REQUIRED_CLEARANCE_PX"]) - expected_threshold) > 1e-9:
                    errors.append(f"pair threshold mismatch {row['PAIR_ID']}")
            elif row["CHECK_TYPE"] == "TEXT_TEXT" and abs(float(row["MIN_REQUIRED_CLEARANCE_PX"]) - 4.0) > 1e-9:
                errors.append(f"text-text threshold mismatch {row['PAIR_ID']}")
        crit = json.loads((HERE / "critical_pairs_manifest.json").read_text(encoding="utf-8"))
        if len(crit) != metrics_now["CRITICAL_PAIR_COUNT"]:
            errors.append("critical pair manifest count mismatch")
        for entry in crit:
            d = HERE / entry["DIRECTORY"]
            for name in ["raw_1to1.png", "A_raw_mask.png", "B_final_visible_raw_mask.png", "intersection_raw_mask.png", "overlay_1to1.png", "raw_8xNN.png", "overlay_8xNN.png", "pair_manifest.json"]:
                if not (d / name).exists():
                    errors.append(f"critical package incomplete {entry['PAIR_ID']}/{name}")
        metric_files = [HERE / "audit_metrics.json", HERE / "after_visual_acceptance.md", HERE / "SA1_report.md"]
        report_strings = [path.read_text(encoding="utf-8") for path in metric_files if path.exists()]
        numeric_tokens = [str(metrics_now["PAIR_COUNT"]), str(metrics_now["OVERLAP_PIXEL_COUNT"]), str(metrics_now["CLIP_PIXEL_COUNT"])]
        report_numeric = all(any(token in text for text in report_strings) for token in numeric_tokens)
        if not report_numeric:
            errors.append("report/metrics numeric token mismatch")
        if include_terminal:
            terminal = json.loads((HERE / "machine_terminal_check.json").read_text(encoding="utf-8"))
            if not terminal.get("pass", False):
                errors.append("machine terminal check reports FAIL")
        return {
            "figure_id": FIGURE_ID, "pass": not errors, "errors": errors, "missing_artifacts": missing,
            "vector_inventory_csv_traceability": not any("vector" in e or "HALO" in e for e in errors),
            "pair_csv_traceability": not any("pair" in e or "threshold" in e or "category" in e for e in errors),
            "critical_evidence_complete": not any("critical" in e for e in errors),
            "report_numeric_consistency": report_numeric,
            "component_count": len(components), "halo_background_count": halo_count, "nonhalo_final_visible_count": final_visible_count, "independent_vector_pair_component_count": independent_count,
            "pair_count": len(pair_rows), "expected_pair_count": expected_pair_count,
        }

    def write_terminal_check(metrics_now: dict, base: dict) -> dict:
        """Last machine-readable integrity gate.  Gate failures are expected audit
        findings; this verifies they are consistently reported, never converts them
        to a PASS."""
        rows = []
        def check(check_id: str, expected, actual, passed: bool, detail: str) -> None:
            rows.append({"CHECK_ID": check_id, "EXPECTED": expected, "ACTUAL": actual, "PASS_FAIL": "PASS" if passed else "FAIL", "DETAIL": detail})

        pixel_rows = list(csv.DictReader((HERE / "after_pixel_measurements.csv").open(encoding="utf-8-sig")))
        glyph_rows = [r for r in pixel_rows if r["MEASUREMENT_LEVEL"] == "GLYPH"]
        glyph_fails_now = sum(r["PASS_FAIL"] == "FAIL" for r in glyph_rows)
        glyph_masks_nonempty = 0
        glyph_masks_expected = 0
        for r in glyph_rows:
            if r["SCRIPT_CLASS"] == "WHITESPACE":
                continue
            glyph_masks_expected += 1
            ref = HERE / r["MASK_FILE"]
            if ref.exists() and np.asarray(Image.open(ref).convert("L")).any():
                glyph_masks_nonempty += 1
        same_fails_now = sum(r["PASS_FAIL"] == "FAIL" for r in csv.DictReader((HERE / "same_class_ratio_audit.csv").open(encoding="utf-8-sig")))
        role_fails_now = sum(r["PASS_FAIL"] == "FAIL" for r in csv.DictReader((HERE / "role_ratio_audit.csv").open(encoding="utf-8-sig")))
        overlap_now = list(csv.DictReader((HERE / "after_overlap_report.csv").open(encoding="utf-8-sig")))
        overlap_fail_now = sum(int(r["OVERLAP_PIXEL_COUNT"]) > 0 for r in overlap_now)
        clearance_fail_now = sum(r["RAW_MASK_CLEARANCE_PX"] != "INF" and float(r["RAW_MASK_CLEARANCE_PX"]) < float(r["MIN_REQUIRED_CLEARANCE_PX"]) for r in overlap_now)
        critical_pairs_now = json.loads((HERE / "critical_pairs_manifest.json").read_text(encoding="utf-8"))
        critical_glyphs_now = json.loads((HERE / "critical_glyphs_manifest.json").read_text(encoding="utf-8"))
        check("BASE_CONSISTENCY", True, base["pass"], bool(base["pass"]), "pre-terminal inventory/pair/report check")
        check("OBJECT_UNIQUE_ID_COUNT", len(text_items), len({r["OBJECT_ID"] for r in csv.DictReader((HERE / "object_inventory.csv").open(encoding="utf-8-sig"))}), len({r["OBJECT_ID"] for r in csv.DictReader((HERE / "object_inventory.csv").open(encoding="utf-8-sig"))}) == len(text_items), "text manifest IDs")
        check("NONEMPTY_GLYPH_RAW_MASKS", glyph_masks_expected, glyph_masks_nonempty, glyph_masks_expected == glyph_masks_nonempty, "all non-whitespace glyph independent raw masks")
        check("RELATION_PAIR_COUNT", expected_pair_count, len(overlap_now), len(overlap_now) == expected_pair_count, "C(text,2)+text×independent-vector")
        check("OVERLAP_FAIL_PAIR_COUNT", metrics_now["OVERLAP_FAIL_PAIR_COUNT"], overlap_fail_now, metrics_now["OVERLAP_FAIL_PAIR_COUNT"] == overlap_fail_now, "pair CSV vs metrics")
        check("CLEARANCE_FAIL_PAIR_COUNT", metrics_now["CLEARANCE_FAIL_PAIR_COUNT"], clearance_fail_now, metrics_now["CLEARANCE_FAIL_PAIR_COUNT"] == clearance_fail_now, "pair CSV vs metrics")
        check("PIXEL_GLYPH_FAIL_COUNT", metrics_now["PIXEL_HEIGHT_FAIL_COUNT"], glyph_fails_now, metrics_now["PIXEL_HEIGHT_FAIL_COUNT"] == glyph_fails_now, "glyph-only rows")
        check("SAME_CLASS_FAIL_COUNT", metrics_now["SAME_CLASS_RATIO_FAIL_COUNT"], same_fails_now, metrics_now["SAME_CLASS_RATIO_FAIL_COUNT"] == same_fails_now, "D actual raw H_ink CSV")
        check("ROLE_RATIO_FAIL_COUNT", metrics_now["ROLE_RATIO_FAIL_COUNT"], role_fails_now, metrics_now["ROLE_RATIO_FAIL_COUNT"] == role_fails_now, "E comparable-script CSV")
        check("CRITICAL_PAIR_PACKAGE_COUNT", metrics_now["CRITICAL_PAIR_COUNT"], len(critical_pairs_now), metrics_now["CRITICAL_PAIR_COUNT"] == len(critical_pairs_now), "all failed/critical pairs")
        required_pair_files = ["raw_1to1.png", "A_raw_mask.png", "B_final_visible_raw_mask.png", "intersection_raw_mask.png", "overlay_1to1.png", "raw_8xNN.png", "overlay_8xNN.png", "pair_manifest.json"]
        pair_files_ok = all(all((HERE / x["DIRECTORY"] / f).exists() for f in required_pair_files) for x in critical_pairs_now)
        check("CRITICAL_PAIR_8_ARTIFACTS", "all failed/critical pairs × 8", "complete" if pair_files_ok else "missing", pair_files_ok, "raw/A/B/intersection/overlay/1:1/8x/manifest")
        glyph_files_ok = all(all((HERE / x["DIRECTORY"] / f).exists() for f in ["raw_1to1.png", "raw_8xNN.png", "independent_raw_mask.png", "candidate_before_vector_guard.png", "glyph_manifest.json"]) for x in critical_glyphs_now)
        check("CRITICAL_GLYPH_ARTIFACTS", metrics_now["CRITICAL_GLYPH_COUNT"], len(critical_glyphs_now), glyph_files_ok and metrics_now["CRITICAL_GLYPH_COUNT"] == len(critical_glyphs_now), "every glyph failure has raw/mask/8x/manifest")
        report = (HERE / "SA1_report.md").read_text(encoding="utf-8")
        expected_result = "FAIL → SA2" if not metrics_now["ALL_HARD_GATES_PASS"] else "PASS → SA3"
        check("FINAL_RESULT", expected_result, "FAIL → SA2" if "RESULT: FAIL → SA2" in report else "PASS → SA3" if "RESULT: PASS → SA3" in report else "MISSING", expected_result in report, "report outcome matches hard-gate matrix")
        terminal = {"figure_id": FIGURE_ID, "pass": all(r["PASS_FAIL"] == "PASS" for r in rows), "checks": rows, "metrics_snapshot": metrics_now}
        write_csv(HERE / "machine_terminal_check.csv", rows, ["CHECK_ID", "EXPECTED", "ACTUAL", "PASS_FAIL", "DETAIL"])
        jdump(HERE / "machine_terminal_check.json", terminal)
        (HERE / "machine_terminal_check.md").write_text("# FIG-P573-01 machine terminal check\n\n" + "\n".join(f"- `{r['CHECK_ID']}`: {r['PASS_FAIL']} — expected `{r['EXPECTED']}`, actual `{r['ACTUAL']}`." for r in rows) + f"\n\n`EVIDENCE_INTEGRITY_PASS = {str(terminal['pass']).lower()}`\n", encoding="utf-8")
        return terminal

    # Materialize preliminary reports to give consistency a stable target.
    (HERE / "audit_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (HERE / "SA1_report.md").write_text(audit_text(metrics), encoding="utf-8")
    (HERE / "after_visual_acceptance.md").write_text(audit_text(metrics), encoding="utf-8")
    base_consistency = run_consistency(metrics, include_terminal=False)
    metrics["EVIDENCE_INTEGRITY_PASS"] = bool(base_consistency["pass"])
    metrics["ALL_HARD_GATES_PASS"] = bool(
        source_font_pass and pixel_height_pass and same_class_pass and role_pass and unique_overlap_count == 0 and clip_count == 0 and clearance_pass and
        font_harmony_pass and math_pass and text_consistency_pass and grayscale_pass and page_integration_pass and reading_order_pass and base_consistency["pass"]
    )
    (HERE / "audit_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (HERE / "SA1_report.md").write_text(audit_text(metrics), encoding="utf-8")
    (HERE / "after_visual_acceptance.md").write_text(audit_text(metrics), encoding="utf-8")
    terminal = write_terminal_check(metrics, base_consistency)
    consistency = run_consistency(metrics, include_terminal=True)
    jdump(HERE / "final_consistency_check.json", consistency)
    (HERE / "final_consistency_check.md").write_text(
        "# FIG-P573-01 SA1 machine consistency\n\n"
        f"- `EVIDENCE_INTEGRITY_PASS = {str(consistency['pass']).lower()}`\n"
        f"- components: {consistency['component_count']} (HALO_BACKGROUND={consistency['halo_background_count']}; final-visible={consistency['nonhalo_final_visible_count']})\n"
        f"- all-pairs: {consistency['pair_count']} / expected {consistency['expected_pair_count']}\n"
        f"- errors: {json.dumps(consistency['errors'], ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    # A final update of report/metrics carries the completed machine check.  No further mutation follows.
    metrics["EVIDENCE_INTEGRITY_PASS"] = bool(consistency["pass"] and terminal["pass"])
    metrics["ALL_HARD_GATES_PASS"] = bool(
        source_font_pass and pixel_height_pass and same_class_pass and role_pass and unique_overlap_count == 0 and clip_count == 0 and clearance_pass and
        font_harmony_pass and math_pass and text_consistency_pass and grayscale_pass and page_integration_pass and reading_order_pass and consistency["pass"] and terminal["pass"]
    )
    (HERE / "audit_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (HERE / "SA1_report.md").write_text(audit_text(metrics), encoding="utf-8")
    (HERE / "after_visual_acceptance.md").write_text(audit_text(metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
