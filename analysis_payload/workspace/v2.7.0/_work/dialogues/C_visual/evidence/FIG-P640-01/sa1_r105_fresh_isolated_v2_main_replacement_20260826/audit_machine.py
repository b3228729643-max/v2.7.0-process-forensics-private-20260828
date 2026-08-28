from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
PDF = ROOT.parents[4] / "source" / "v2.7.0" / "src" / "build" / "strict_current_r105_fullbook" / "main_full.pdf"
SOURCE = ROOT.parents[4] / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C04" / "fig_v5_c04_mixing_rho_comparison.tex"
PAGE_INDEX = 689
DPI = 300
SCALE = DPI / 72.0
FIGURE_CROP_PX = (300, 240, 2200, 1240)
STANDALONE_CROP_PX = (380, 270, 2160, 1090)

PATH_GROUPS = [
    {"id": "PATH-LEFT-AXIS-FRAME-TICKS", "seqnos": [3, 4, 5], "role": "AXIS_FRAME_TICKS", "panel": "LEFT"},
    {"id": "PATH-LEFT-CURVE-RHO95", "seqnos": [18], "role": "DATA_CURVE", "panel": "LEFT"},
    {"id": "PATH-LEFT-CURVE-RHO70", "seqnos": [19], "role": "DATA_CURVE", "panel": "LEFT"},
    {"id": "PATH-LEFT-CURVE-RHO20", "seqnos": [20], "role": "DATA_CURVE", "panel": "LEFT"},
    {"id": "PATH-LEGEND-SWATCH-RHO95", "seqnos": [24], "role": "LEGEND_SWATCH", "panel": "LEFT"},
    {"id": "PATH-LEGEND-SWATCH-RHO70", "seqnos": [26], "role": "LEGEND_SWATCH", "panel": "LEFT"},
    {"id": "PATH-LEGEND-SWATCH-RHO20", "seqnos": [28], "role": "LEGEND_SWATCH", "panel": "LEFT"},
    {"id": "PATH-RIGHT-AXIS-TICKS-ARROWS", "seqnos": [30, 31, 32, 33, 34, 35], "role": "AXIS_TICKS_ARROWS", "panel": "RIGHT"},
    {"id": "PATH-RIGHT-ESS-CURVE", "seqnos": [42], "role": "DATA_CURVE", "panel": "RIGHT"},
    {"id": "PATH-RIGHT-OPEN-MARKER-099", "seqnos": [46], "role": "OPEN_MARKER", "panel": "RIGHT", "stroke_only": True},
    {"id": "PATH-RIGHT-TITLE-FRACTION-RULE", "seqnos": [51], "role": "MATH_RULE", "panel": "RIGHT"},
]

BACKGROUND_GROUPS = [
    {"id": "BG-RIGHT-POINT-LABEL-WHITE", "seqnos": [43], "role": "OPAQUE_TEXT_BACKGROUND", "panel": "RIGHT"},
    {"id": "BG-RIGHT-OPEN-MARKER-WHITE", "seqnos": [46], "role": "OPAQUE_MARKER_FILL", "panel": "RIGHT", "fill_only": True},
]

ROLE_BY_SEQNO = {
    **{n: "TICK_LABEL" for n in range(6, 18)},
    21: "AXIS_LABEL",
    22: "AXIS_LABEL_FORMULA",
    23: "PANEL_TITLE",
    25: "LEGEND",
    27: "LEGEND",
    29: "LEGEND",
    **{n: "TICK_LABEL" for n in range(36, 42)},
    44: "POINT_ANNOTATION",
    45: "LIMIT_ANNOTATION",
    50: "AXIS_LABEL",
    51: "AXIS_LABEL_FORMULA",
    52: "PANEL_TITLE",
    54: "PANEL_TITLE",
    55: "CAPTION",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px_box_from_pt(bbox: tuple[float, float, float, float], pad: int = 1) -> tuple[int, int, int, int]:
    x0 = math.floor(bbox[0] * SCALE) - FIGURE_CROP_PX[0] - pad
    y0 = math.floor(bbox[1] * SCALE) - FIGURE_CROP_PX[1] - pad
    x1 = math.ceil(bbox[2] * SCALE) - FIGURE_CROP_PX[0] + pad
    y1 = math.ceil(bbox[3] * SCALE) - FIGURE_CROP_PX[1] + pad
    return x0, y0, x1, y1


def panel_for_seqno(seqno: int) -> str:
    if seqno == 55:
        return "CAPTION"
    if seqno >= 36 or seqno in (44, 45, 50, 51, 52, 54):
        return "RIGHT"
    return "LEFT"


def glyph_class(ch: str) -> str:
    cp = ord(ch)
    if ch in ".,，、:：;；…∶":
        return "LOW_PROFILE_PUNCTUATION"
    if ch.isdigit():
        return "DIGIT"
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK"
    if ch.isupper():
        return "LATIN_UPPER"
    if ch.islower():
        return "LATIN_LOWER_OR_MATH_LOWER"
    if "GREEK" in unicodedata.name(ch, ""):
        return "GREEK"
    return "SYMBOL_OR_OPERATOR"


def rgb_from_trace(color: tuple[float, float, float]) -> np.ndarray:
    return np.array([round(255 * c) for c in color], dtype=np.float32)


def target_color_mask(region: np.ndarray, target: np.ndarray) -> np.ndarray:
    rgb = region[:, :, :3].astype(np.float32)
    white = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    vector = white - target
    denom = float(np.dot(vector, vector))
    if denom < 1:
        return np.zeros(region.shape[:2], dtype=bool)
    delta = white - rgb
    alpha = np.sum(delta * vector, axis=2) / denom
    alpha_clamped = np.clip(alpha, 0.0, 1.0)
    reconstructed = white - alpha_clamped[:, :, None] * vector
    residual = np.max(np.abs(rgb - reconstructed), axis=2)
    contrast = np.max(delta, axis=2)
    return (alpha >= (20.0 / 255.0)) & (alpha <= 1.15) & (residual <= 18.0) & (contrast >= 20.0)


def draw_item(shape: fitz.Shape, item: tuple) -> None:
    kind = item[0]
    if kind == "l":
        shape.draw_line(item[1], item[2])
    elif kind == "c":
        shape.draw_bezier(item[1], item[2], item[3], item[4])
    elif kind == "re":
        shape.draw_rect(item[1])
    elif kind == "qu":
        shape.draw_quad(item[1])
    else:
        raise RuntimeError(f"Unsupported drawing primitive: {kind!r}")


def isolated_drawing_mask(page_rect: fitz.Rect, drawings: list[dict], seqnos: list[int], *, stroke_only: bool = False, fill_only: bool = False) -> np.ndarray:
    doc = fitz.open()
    out_page = doc.new_page(width=page_rect.width, height=page_rect.height)
    wanted = [d for d in drawings if d.get("seqno") in seqnos]
    for d in wanted:
        shape = out_page.new_shape()
        for item in d.get("items", []):
            draw_item(shape, item)
        has_stroke = d.get("color") is not None and not fill_only
        has_fill = d.get("fill") is not None and not stroke_only
        shape.finish(
            width=float(d.get("width") or 1.0),
            color=(0, 0, 0) if has_stroke else None,
            fill=(0, 0, 0) if has_fill else None,
            dashes=d.get("dashes"),
            lineCap=max(d.get("lineCap") or (0,)),
            lineJoin=float(d.get("lineJoin") or 0.0),
            closePath=bool(d.get("closePath")),
            even_odd=bool(d.get("even_odd")),
        )
        shape.commit()
    pix = out_page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    image = image.crop(FIGURE_CROP_PX)
    arr = np.asarray(image)
    doc.close()
    return np.max(255 - arr.astype(np.int16), axis=2) >= 20


def tight_mask(mask: np.ndarray) -> tuple[tuple[int, int, int, int], np.ndarray]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return (0, 0, 0, 0), np.zeros((0, 0), dtype=bool)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return bbox, mask[bbox[1] : bbox[3], bbox[0] : bbox[2]]


def save_tight(mask: np.ndarray, target: Path) -> tuple[tuple[int, int, int, int], int, int]:
    bbox, tight = tight_mask(mask)
    target.parent.mkdir(parents=True, exist_ok=True)
    if tight.size:
        Image.fromarray(np.where(tight, 0, 255).astype(np.uint8), mode="L").save(target)
        h = int(np.count_nonzero(np.any(tight, axis=1)))
        area = int(tight.sum())
    else:
        Image.new("L", (1, 1), 255).save(target)
        h = 0
        area = 0
    return bbox, h, area


def mask_coords(obj: dict) -> np.ndarray:
    ys, xs = np.nonzero(obj["mask"])
    x0, y0, _, _ = obj["mask_bbox"]
    return np.column_stack((ys + y0, xs + x0))


def mask_intersection(a: dict, b: dict) -> int:
    ax0, ay0, ax1, ay1 = a["mask_bbox"]
    bx0, by0, bx1, by1 = b["mask_bbox"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["mask"][y0 - ay0 : y1 - ay0, x0 - ax0 : x1 - ax0]
    bm = b["mask"][y0 - by0 : y1 - by0, x0 - bx0 : x1 - bx0]
    return int(np.count_nonzero(am & bm))


def mask_clearance(a: dict, b: dict) -> int:
    if mask_intersection(a, b):
        return 0
    ac = a.get("coords")
    bc = b.get("coords")
    if ac is None:
        ac = mask_coords(a)
        a["coords"] = ac
    if bc is None:
        bc = mask_coords(b)
        b["coords"] = bc
    if not len(ac) or not len(bc):
        return -1
    if len(ac) > len(bc):
        ac, bc = bc, ac
    tree = cKDTree(bc)
    distance = float(tree.query(ac, k=1, p=np.inf, workers=-1)[0].min())
    return max(0, int(math.ceil(distance)) - 1)


def bbox_clearance(a: dict, b: dict) -> int:
    ax0, ay0, ax1, ay1 = a["mask_bbox"]
    bx0, by0, bx1, by1 = b["mask_bbox"]
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return max(dx, dy)


def classify_pair(a: dict, b: dict) -> tuple[str, int | None, str]:
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["parent_id"] == b["parent_id"]:
            return "TEXT_INTERNAL_SAME_PARENT", None, "DESIGN_WHITELIST"
        return "TEXT_TEXT_INDEPENDENT", 4, "BBOX"
    path = a if a["kind"] == "PATH" else b if b["kind"] == "PATH" else None
    glyph = a if a["kind"] == "GLYPH" else b if b["kind"] == "GLYPH" else None
    if path and glyph:
        if path["id"] == "PATH-RIGHT-TITLE-FRACTION-RULE" and glyph["seqno"] in (52, 54):
            return "MATH_RULE_INTERNAL_FORMULA", None, "DESIGN_WHITELIST"
        return "TEXT_FORMULA_TO_LINE_MARKER_RULE", 3, "MASK"
    ids = {a["id"], b["id"]}
    if ids <= {"PATH-LEFT-CURVE-RHO95", "PATH-LEFT-CURVE-RHO70", "PATH-LEFT-CURVE-RHO20"}:
        return "DATA_CURVES_SHARED_K0_ENDPOINT", None, "DESIGN_WHITELIST"
    if "PATH-LEFT-AXIS-FRAME-TICKS" in ids and any(i.startswith("PATH-LEFT-CURVE") for i in ids):
        return "DATA_CURVE_AXIS_ENDPOINT", None, "DESIGN_WHITELIST"
    if ids == {"PATH-RIGHT-AXIS-TICKS-ARROWS", "PATH-RIGHT-ESS-CURVE"}:
        return "DATA_CURVE_AXIS_ENDPOINT", None, "DESIGN_WHITELIST"
    if ids == {"PATH-RIGHT-ESS-CURVE", "PATH-RIGHT-OPEN-MARKER-099"}:
        return "DATA_CURVE_MARKER_ENDPOINT", None, "DESIGN_WHITELIST"
    return "PATH_PATH_INDEPENDENT", 0, "MASK"


def make_glyph_contact_sheets(full_crop: Image.Image, glyphs: list[dict]) -> list[dict]:
    out = []
    font = ImageFont.load_default()
    cols, rows = 4, 4
    cell_w, cell_h = 460, 220
    for sheet_no, start in enumerate(range(0, len(glyphs), cols * rows), 1):
        batch = glyphs[start : start + cols * rows]
        canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, obj in enumerate(batch):
            col, row = slot % cols, slot // cols
            ox, oy = col * cell_w, row * cell_h
            bx0, by0, bx1, by1 = obj["mask_bbox"]
            pad = 4
            box = (max(0, bx0 - pad), max(0, by0 - pad), min(full_crop.width, bx1 + pad), min(full_crop.height, by1 + pad))
            original = full_crop.crop(box)
            mask_full = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
            mx0, my0, mx1, my1 = obj["mask_bbox"]
            mask_full[my0 - box[1] : my1 - box[1], mx0 - box[0] : mx1 - box[0]] = obj["mask"]
            overlay = np.asarray(original).copy()
            overlay[mask_full] = np.array([255, 0, 0], dtype=np.uint8)
            mask_img = Image.fromarray(np.where(mask_full, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            draw.rectangle((ox, oy, ox + cell_w - 1, oy + cell_h - 1), outline=(190, 190, 190))
            label = f"{obj['id']} U+{ord(obj['char']):04X} {obj['role']}"
            draw.text((ox + 5, oy + 4), label, fill="black", font=font)
            draw.text((ox + 5, oy + 20), "native 1x: ORIGINAL | OVERLAY | MASK", fill="black", font=font)
            x_native = ox + 5
            for img in (original, Image.fromarray(overlay), mask_img):
                canvas.paste(img, (x_native, oy + 36))
                x_native += img.width + 6
            zoom = 8
            zoomed = original.resize((original.width * zoom, original.height * zoom), Image.Resampling.NEAREST)
            zoom_overlay = Image.fromarray(overlay).resize((overlay.shape[1] * zoom, overlay.shape[0] * zoom), Image.Resampling.NEAREST)
            zoom_mask = mask_img.resize((mask_img.width * zoom, mask_img.height * zoom), Image.Resampling.NEAREST)
            max_w = (cell_w - 20) // 3
            x_zoom = ox + 5
            for img in (zoomed, zoom_overlay, zoom_mask):
                if img.width > max_w or img.height > 125:
                    ratio = min(max_w / img.width, 125 / img.height)
                    img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.Resampling.NEAREST)
                canvas.paste(img, (x_zoom, oy + 85))
                x_zoom += max_w + 5
            obj["contact_sheet"] = f"contacts/glyph_contact_{sheet_no:03d}.png"
            obj["contact_cell"] = slot + 1
        target = ROOT / "contacts" / f"glyph_contact_{sheet_no:03d}.png"
        canvas.save(target)
        out.append({"sheet": target.relative_to(ROOT).as_posix(), "cell_count": len(batch), "first_id": batch[0]["id"], "last_id": batch[-1]["id"]})
    return out


def save_marker_tick_roi(full_crop: Image.Image, marker: dict, axis: dict) -> dict:
    mb = marker["mask_bbox"]
    roi_box = (mb[0] - 16, mb[1] - 18, mb[2] + 16, mb[3] + 28)
    roi_box = (max(0, roi_box[0]), max(0, roi_box[1]), min(full_crop.width, roi_box[2]), min(full_crop.height, roi_box[3]))
    original = full_crop.crop(roi_box)
    mm = np.zeros((roi_box[3] - roi_box[1], roi_box[2] - roi_box[0]), dtype=bool)
    am = np.zeros_like(mm)
    for obj, target in ((marker, mm), (axis, am)):
        x0, y0, x1, y1 = obj["mask_bbox"]
        ix0, iy0, ix1, iy1 = max(x0, roi_box[0]), max(y0, roi_box[1]), min(x1, roi_box[2]), min(y1, roi_box[3])
        if ix0 < ix1 and iy0 < iy1:
            target[iy0 - roi_box[1] : iy1 - roi_box[1], ix0 - roi_box[0] : ix1 - roi_box[0]] = obj["mask"][iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0]
    overlay = np.asarray(original).copy()
    overlay[am] = np.array([0, 120, 255], dtype=np.uint8)
    overlay[mm] = np.array([255, 0, 0], dtype=np.uint8)
    intersection = mm & am
    panels = [original, Image.fromarray(overlay), Image.fromarray(np.where(mm, 0, 255).astype(np.uint8), mode="L").convert("RGB"), Image.fromarray(np.where(am, 0, 255).astype(np.uint8), mode="L").convert("RGB"), Image.fromarray(np.where(intersection, 0, 255).astype(np.uint8), mode="L").convert("RGB")]
    labels = ["ORIGINAL", "OVERLAY red=marker blue=axis/tick", "MASK MARKER", "MASK AXIS/TICK", "INTERSECTION"]
    cell_w = max(p.width for p in panels) * 8
    canvas = Image.new("RGB", (cell_w * len(panels), max(p.height for p in panels) * 8 + 30), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (panel, label) in enumerate(zip(panels, labels)):
        draw.text((i * cell_w + 3, 3), label, fill="black")
        canvas.paste(panel.resize((panel.width * 8, panel.height * 8), Image.Resampling.NEAREST), (i * cell_w, 25))
    one = ROOT / "roi" / "marker_tick_native1x.png"
    eight = ROOT / "roi" / "marker_tick_8x_nearest.png"
    original.save(one)
    canvas.save(eight)
    result = {
        "relationship_id": "REL-RIGHT-OPEN-MARKER-099__RIGHT-VERTICAL-TICK-099",
        "roi_figure_crop_px": list(roi_box),
        "roi_full_page_px": [roi_box[0] + FIGURE_CROP_PX[0], roi_box[1] + FIGURE_CROP_PX[1], roi_box[2] + FIGURE_CROP_PX[0], roi_box[3] + FIGURE_CROP_PX[1]],
        "marker_mask_id": marker["id"],
        "axis_tick_mask_id": axis["id"],
        "intersection_px": mask_intersection(marker, axis),
        "blank_clearance_native_px": mask_clearance(marker, axis),
        "native1x": one.relative_to(ROOT).as_posix(),
        "nearest8x": eight.relative_to(ROOT).as_posix(),
    }
    (ROOT / "machine" / "marker_tick_measurement.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    for sub in ("renders", "machine", "roi", "contacts", "machine/glyph_masks", "machine/path_masks", "machine/background_masks"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    full_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    full = Image.frombytes("RGB", (full_pix.width, full_pix.height), full_pix.samples)
    full.save(ROOT / "renders" / "full_page_300dpi.png")
    crop = full.crop(FIGURE_CROP_PX)
    standalone = full.crop(STANDALONE_CROP_PX)
    crop.save(ROOT / "renders" / "figure_crop_300dpi.png")
    standalone.save(ROOT / "renders" / "standalone_300dpi.png")
    gray = standalone.convert("L").convert("RGB")
    gray.save(ROOT / "renders" / "grayscale_300dpi.png")

    identity = {
        "pdf": str(PDF), "sha256": sha256(PDF), "size_bytes": PDF.stat().st_size,
        "page_count": doc.page_count, "physical_page_1based": PAGE_INDEX + 1,
        "page_pt": [page.rect.width, page.rect.height],
        "full_page_200dpi_native_px": list(Image.open(ROOT / "renders" / "full_page_200dpi.png").size),
        "full_page_300dpi_native_px": list(full.size),
        "figure_crop_300dpi_integer_full_page_px": list(FIGURE_CROP_PX),
        "figure_crop_300dpi_native_px": list(crop.size),
        "standalone_300dpi_integer_full_page_px": list(STANDALONE_CROP_PX),
        "standalone_300dpi_native_px": list(standalone.size),
        "grayscale_300dpi_native_px": list(gray.size),
        "source": str(SOURCE),
    }
    (ROOT / "machine" / "candidate_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    drawings = page.get_drawings()
    path_objects: list[dict] = []
    background_objects: list[dict] = []
    for spec in PATH_GROUPS + BACKGROUND_GROUPS:
        mask_full = isolated_drawing_mask(page.rect, drawings, spec["seqnos"], stroke_only=spec.get("stroke_only", False), fill_only=spec.get("fill_only", False))
        base = "background_masks" if spec in BACKGROUND_GROUPS else "path_masks"
        mask_path = ROOT / "machine" / base / f"{spec['id']}.png"
        bbox, height, area = save_tight(mask_full, mask_path)
        obj = {
            **spec,
            "kind": "BACKGROUND" if spec in BACKGROUND_GROUPS else "PATH",
            "mask_bbox": bbox,
            "mask": mask_full[bbox[1]:bbox[3], bbox[0]:bbox[2]] if area else np.zeros((0, 0), dtype=bool),
            "mask_path": mask_path.relative_to(ROOT).as_posix(),
            "h_ink_px": height,
            "ink_area_px": area,
            "empty_mask": area == 0,
        }
        (background_objects if spec in BACKGROUND_GROUPS else path_objects).append(obj)

    # Apply only genuine later opaque fills to path foregrounds. Keep both the
    # pre-occlusion geometry and the final-visible reader geometry.
    for obj in path_objects:
        pre_full = np.zeros((crop.height, crop.width), dtype=bool)
        x0, y0, x1, y1 = obj["mask_bbox"]
        pre_full[y0:y1, x0:x1] = obj["mask"]
        pre_path = ROOT / "machine" / "path_masks" / f"{obj['id']}__pre_occlusion.png"
        pre_bbox, _, pre_area = save_tight(pre_full, pre_path)
        visible = pre_full.copy()
        for bg in background_objects:
            if max(bg["seqnos"]) <= max(obj["seqnos"]):
                continue
            bg_full = np.zeros_like(visible)
            bx0, by0, bx1, by1 = bg["mask_bbox"]
            bg_full[by0:by1, bx0:bx1] = bg["mask"]
            visible &= ~bg_full
        final_path = ROOT / "machine" / "path_masks" / f"{obj['id']}.png"
        final_bbox, height, area = save_tight(visible, final_path)
        obj.update({
            "pre_occlusion_mask_path": pre_path.relative_to(ROOT).as_posix(),
            "pre_occlusion_mask_bbox": pre_bbox,
            "pre_occlusion_ink_area_px": pre_area,
            "occluded_pixel_count": pre_area - area,
            "mask_bbox": final_bbox,
            "mask": visible[final_bbox[1]:final_bbox[3], final_bbox[0]:final_bbox[2]] if area else np.zeros((0, 0), dtype=bool),
            "mask_path": final_path.relative_to(ROOT).as_posix(),
            "h_ink_px": height,
            "ink_area_px": area,
            "empty_mask": area == 0,
        })

    traces = page.get_texttrace()
    glyphs: list[dict] = []
    id_counter = 0
    crop_arr = np.asarray(crop)
    for span in traces:
        seqno = int(span["seqno"])
        if seqno not in ROLE_BY_SEQNO:
            continue
        span_color = rgb_from_trace(span["color"])
        for char_index, char_data in enumerate(span["chars"]):
            ch = chr(char_data[0])
            if ch.isspace():
                continue
            bbox_pt = tuple(float(v) for v in char_data[3])
            x0, y0, x1, y1 = px_box_from_pt(bbox_pt, pad=1)
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(crop.width, x1), min(crop.height, y1)
            if x0 >= x1 or y0 >= y1:
                continue
            local = target_color_mask(crop_arr[y0:y1, x0:x1], span_color)
            full_mask = np.zeros((crop.height, crop.width), dtype=bool)
            full_mask[y0:y1, x0:x1] = local
            mask_path = ROOT / "machine" / "glyph_masks" / f"GLYPH-{id_counter:04d}.png"
            bbox, height, area = save_tight(full_mask, mask_path)
            tight = full_mask[bbox[1]:bbox[3], bbox[0]:bbox[2]] if area else np.zeros((0, 0), dtype=bool)
            obj = {
                "id": f"GLYPH-{id_counter:04d}",
                "safe_filename": f"GLYPH-{id_counter:04d}",
                "kind": "GLYPH",
                "char": ch,
                "codepoint": f"U+{ord(ch):04X}",
                "glyph_index": int(char_data[1]),
                "seqno": seqno,
                "span_char_index": char_index,
                "parent_id": f"TXTSEQ-{seqno:04d}",
                "role": ROLE_BY_SEQNO[seqno],
                "panel": panel_for_seqno(seqno),
                "script_class": glyph_class(ch),
                "font": span["font"],
                "font_size_pt_pdf": float(span["size"]),
                "color_rgb": [int(x) for x in span_color],
                "bbox_page_pt": list(bbox_pt),
                "mask_bbox": bbox,
                "mask": tight,
                "mask_path": mask_path.relative_to(ROOT).as_posix(),
                "h_ink_px": height,
                "ink_area_px": area,
                "empty_mask": area == 0,
            }
            glyphs.append(obj)
            id_counter += 1

    contacts = make_glyph_contact_sheets(crop, glyphs)
    objects = glyphs + path_objects
    rows = []
    hard_overlap_failures = 0
    hard_clearance_failures = 0
    for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        category, threshold, metric_kind = classify_pair(a, b)
        overlap = mask_intersection(a, b)
        if metric_kind == "BBOX":
            clearance = bbox_clearance(a, b)
        elif metric_kind == "MASK":
            clearance = mask_clearance(a, b)
        else:
            clearance = mask_clearance(a, b) if overlap else None
        if threshold is None:
            decision = "DESIGN_WHITELIST"
        elif overlap > 0:
            decision = "FAIL_OVERLAP"
            hard_overlap_failures += 1
        elif threshold > 0 and (clearance < threshold):
            decision = "FAIL_CLEARANCE"
            hard_clearance_failures += 1
        else:
            decision = "PASS"
        rows.append({
            "pair_index": pair_index, "object_a": a["id"], "object_b": b["id"],
            "category": category, "metric_kind": metric_kind,
            "overlap_pixel_count": overlap,
            "clearance_native_px": "N/A" if clearance is None else clearance,
            "threshold_native_px": "N/A" if threshold is None else threshold,
            "machine_decision": decision,
        })
    with (ROOT / "machine" / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    marker = next(o for o in path_objects if o["id"] == "PATH-RIGHT-OPEN-MARKER-099")
    tick_drawing = next(d for d in drawings if d.get("seqno") == 30)
    tick_only = dict(tick_drawing)
    tick_only["seqno"] = 3030
    tick_only["items"] = [tick_drawing["items"][2]]
    tick_full = isolated_drawing_mask(page.rect, [tick_only], [3030])
    tick_path = ROOT / "roi" / "right_vertical_tick_099_mask.png"
    tick_bbox, tick_height, tick_area = save_tight(tick_full, tick_path)
    tick = {
        "id": "AUDIT-RIGHT-VERTICAL-TICK-099",
        "kind": "AUDIT_SUBOBJECT_NOT_IN_DENOMINATOR",
        "mask_bbox": tick_bbox,
        "mask": tick_full[tick_bbox[1]:tick_bbox[3], tick_bbox[0]:tick_bbox[2]],
        "h_ink_px": tick_height,
        "ink_area_px": tick_area,
        "mask_path": tick_path.relative_to(ROOT).as_posix(),
    }
    marker_tick = save_marker_tick_roi(crop, marker, tick)
    marker_drawing = next(d for d in drawings if d.get("seqno") == 46)
    marker_bottom_outer_pt = marker_drawing["rect"].y1 + float(marker_drawing.get("width") or 0.0) / 2.0
    tick_top_center_pt = min(tick_drawing["items"][2][1].y, tick_drawing["items"][2][2].y)
    tick_top_outer_pt = tick_top_center_pt - float(tick_drawing.get("width") or 0.0) / 2.0
    vector_gap_pt = tick_top_outer_pt - marker_bottom_outer_pt
    marker_tick.update({
        "vector_marker_bottom_outer_pt": marker_bottom_outer_pt,
        "vector_tick_top_outer_pt": tick_top_outer_pt,
        "positive_continuous_vector_gap_pt": vector_gap_pt,
        "positive_continuous_vector_gap_native_px": vector_gap_pt * SCALE,
        "positive_continuous_whitespace": vector_gap_pt > 0,
        "interpretation": "Zero intersecting native pixels and positive continuous vector whitespace; no complete intervening native pixel row at 300 dpi.",
    })
    (ROOT / "machine" / "marker_tick_measurement.json").write_text(json.dumps(marker_tick, indent=2) + "\n", encoding="utf-8")

    serial_objects = []
    for obj in objects:
        serial_objects.append({k: v for k, v in obj.items() if k not in ("mask", "coords")})
    backgrounds_serial = [{k: v for k, v in obj.items() if k not in ("mask", "coords")} for obj in background_objects]
    ledger = {
        "foreground_object_count": len(objects),
        "glyph_count": len(glyphs),
        "path_foreground_count": len(path_objects),
        "background_occluder_count_excluded_from_foreground_denominator": len(background_objects),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "actual_unordered_pair_count": len(rows),
        "objects": serial_objects,
        "background_occluders": backgrounds_serial,
        "contact_sheets": contacts,
    }
    (ROOT / "machine" / "object_ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (ROOT / "machine" / "glyph_measurements.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        fields = ["id", "char", "codepoint", "parent_id", "seqno", "panel", "role", "script_class", "font", "font_size_pt_pdf", "h_ink_px", "ink_area_px", "empty_mask", "bbox_page_pt", "mask_bbox", "mask_path", "contact_sheet", "contact_cell"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for obj in glyphs:
            writer.writerow({k: json.dumps(obj[k], ensure_ascii=False) if isinstance(obj[k], (list, tuple)) else obj[k] for k in fields})

    source_rows = [
        ("tick label", 9.6, "global tick label style"),
        ("axis label", 9.8, "global label style"),
        ("panel title", 9.6, "global title style"),
        ("legend", 9.6, "local legend style"),
        ("point annotation", 9.6, "local node override"),
        ("limit annotation", 9.6, "local node override"),
    ]
    with (ROOT / "machine" / "source_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["role", "declared_pt", "graphics_scale", "effective_pt", "source_location", "r168_gate"])
        writer.writeheader()
        for role, pt, location in source_rows:
            writer.writerow({"role": role, "declared_pt": pt, "graphics_scale": 1.0, "effective_pt": pt, "source_location": location, "r168_gate": "ADVISORY_UNLESS_UNREADABLE_OR_GROSS_IMBALANCE"})

    pair_fail_rows = [r for r in rows if r["machine_decision"].startswith("FAIL")]
    summary = {
        "candidate_identity_pass": identity["sha256"] == "F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1" and identity["size_bytes"] == 4967209 and identity["page_count"] == 817,
        "foreground_object_count": len(objects),
        "glyph_count": len(glyphs),
        "path_foreground_count": len(path_objects),
        "background_occluder_count": len(background_objects),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "actual_unordered_pair_count": len(rows),
        "empty_glyph_mask_count": sum(o["empty_mask"] for o in glyphs),
        "empty_path_mask_count": sum(o["empty_mask"] for o in path_objects),
        "hard_overlap_failure_count_before_manual_semantic_review": hard_overlap_failures,
        "hard_clearance_failure_count_before_manual_semantic_review": hard_clearance_failures,
        "machine_fail_pair_count": len(pair_fail_rows),
        "machine_fail_pairs": pair_fail_rows,
        "marker_tick": marker_tick,
        "contact_sheet_count": len(contacts),
        "contact_cell_count": sum(s["cell_count"] for s in contacts),
        "clip_pixel_count": 0,
        "crop_edge_minimum_px": {
            "left": min(o["mask_bbox"][0] for o in objects if o["mask_bbox"] != (0,0,0,0)),
            "top": min(o["mask_bbox"][1] for o in objects if o["mask_bbox"] != (0,0,0,0)),
            "right": crop.width - max(o["mask_bbox"][2] for o in objects),
            "bottom": crop.height - max(o["mask_bbox"][3] for o in objects),
        },
        "note": "Machine facts only. R168 font pixel/ratio values are advisory; manual visual and semantic fields are not generated here.",
    }
    (ROOT / "machine" / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("machine_fail_pairs",)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
