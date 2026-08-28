from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa3_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_componentwise_sweep.tex")
BODY = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex")
HANDOFF_ID = "C-FIG-P605-01-R104-SA3-FRESH-ISOLATED-V1"
UID = "FIG-P605-01"
PAGE_INDEX = 657
PHYSICAL_PAGE = 658
PRINTED_PAGE = 645
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0

# Both are direct clips of the official page; the first contains the body only,
# the second contains body plus caption. Padding prevents crop-induced clipping.
STANDALONE_CLIP_PT = fitz.Rect(85.0, 60.0, 521.5, 221.5)
FIGURE_CLIP_PT = fitz.Rect(65.0, 60.0, 540.0, 252.5)
TARGET_TEXT_BLOCKS = set(range(1, 12))
TARGET_DRAWINGS = set(range(1, 24))

TEXT_PARENT = {
    1: ("TXT_LEFT_TITLE", "PANEL_TITLE", "LEFT"),
    2: ("TXT_LEFT_KERNEL_ROW", "NODE_LABEL", "LEFT"),
    3: ("TXT_LEFT_FORMULA", "FORMULA", "LEFT"),
    4: ("TXT_LEFT_NOTE", "ANNOTATION", "LEFT"),
    5: ("TXT_RIGHT_TITLE", "PANEL_TITLE", "RIGHT"),
    6: ("TXT_RIGHT_PICK", "FORMULA", "RIGHT"),
    7: ("TXT_RIGHT_KERNEL_ROW", "NODE_LABEL", "RIGHT"),
    8: ("TXT_RIGHT_FORMULA", "FORMULA", "RIGHT"),
    9: ("TXT_RIGHT_FORMULA", "FORMULA", "RIGHT"),
    10: ("TXT_RIGHT_NOTE", "ANNOTATION", "RIGHT"),
    11: ("TXT_CAPTION", "CAPTION", "PAGE"),
}

DRAWING_META = {
    1: ("G_PANEL_LEFT", "PANEL_BORDER", "PANEL_LEFT"),
    2: ("G_PANEL_RIGHT", "PANEL_BORDER", "PANEL_RIGHT"),
    3: ("G_NODE_K1_LEFT", "NODE_BORDER", "NODE_K1_LEFT"),
    4: ("G_NODE_K2_LEFT", "NODE_BORDER", "NODE_K2_LEFT"),
    5: ("G_NODE_KD_LEFT", "NODE_BORDER", "NODE_KD_LEFT"),
    6: ("G_EDGE_L1_LINE", "EDGE_LINE", "EDGE_L1"),
    7: ("G_EDGE_L1_ARROW", "ARROWHEAD", "EDGE_L1"),
    8: ("G_EDGE_L2_LINE", "EDGE_LINE", "EDGE_L2"),
    9: ("G_EDGE_L2_ARROW", "ARROWHEAD", "EDGE_L2"),
    10: ("G_EDGE_L3_LINE", "EDGE_LINE", "EDGE_L3"),
    11: ("G_EDGE_L3_ARROW", "ARROWHEAD", "EDGE_L3"),
    12: ("G_NOTE_LEFT", "NODE_BORDER", "NOTE_LEFT"),
    13: ("G_PICK_DIAMOND", "NODE_BORDER", "PICK_DIAMOND"),
    14: ("G_NODE_K1_RIGHT", "NODE_BORDER", "NODE_K1_RIGHT"),
    15: ("G_NODE_KJ_RIGHT", "NODE_BORDER", "NODE_KJ_RIGHT"),
    16: ("G_NODE_KD_RIGHT", "NODE_BORDER", "NODE_KD_RIGHT"),
    17: ("G_EDGE_R1_LINE", "EDGE_LINE", "EDGE_R1"),
    18: ("G_EDGE_R1_ARROW", "ARROWHEAD", "EDGE_R1"),
    19: ("G_EDGE_R2_LINE", "EDGE_LINE", "EDGE_R2"),
    20: ("G_EDGE_R2_ARROW", "ARROWHEAD", "EDGE_R2"),
    21: ("G_EDGE_R3_LINE", "EDGE_LINE", "EDGE_R3"),
    22: ("G_EDGE_R3_ARROW", "ARROWHEAD", "EDGE_R3"),
    23: ("G_NOTE_RIGHT", "NODE_BORDER", "NOTE_RIGHT"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGB" if pix.n >= 3 else "L"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_float(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(v) * 255)) for v in value)


def pt_bbox_to_px(bbox, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(math.floor(x0 * SCALE_300)) - pad),
        max(0, int(math.floor(y0 * SCALE_300)) - pad),
        int(math.ceil(x1 * SCALE_300)) + pad,
        int(math.ceil(y1 * SCALE_300)) + pad,
    )


def classify_char(ch: str, pt: float, parent_role: str) -> tuple[str, int | str]:
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if pt < 8.7 and parent_role in {"FORMULA", "NODE_LABEL"}:
        return "NATURAL_SCRIPT", 15
    if "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf":
        return "CJK", 30
    if ch in ".,，。；;：:、…⋯":
        return "LOW_PROFILE_PUNCTUATION", "CALIBRATION"
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_CAP_DIGIT", 24
    if ch.islower() or 0x0370 <= cp <= 0x03FF:
        return "LATIN_LOWER_GREEK", 17
    if cat.startswith("S") or ch in "=+-−∼~()[]{}":
        return "MATH_BASE", 22
    if cat.startswith("P"):
        return "PUNCTUATION", 17
    return "FULL_HEIGHT_OTHER", 24


def local_contrast_mask(page_rgb: np.ndarray, bbox_px: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox_px
    crop = page_rgb[y0:y1, x0:x1]
    if crop.size == 0:
        return np.zeros((0, 0), dtype=bool)
    border = np.concatenate(
        [crop[0].reshape(-1, 3), crop[-1].reshape(-1, 3), crop[:, 0].reshape(-1, 3), crop[:, -1].reshape(-1, 3)],
        axis=0,
    )
    bg = np.median(border, axis=0)
    diff = np.max(np.abs(crop.astype(np.int16) - bg.astype(np.int16)), axis=2)
    return diff >= 20


def drawing_mask(page_rgb: np.ndarray, bbox_px: tuple[int, int, int, int], stroke_rgb, fill_rgb, kind: str, items) -> np.ndarray:
    x0, y0, x1, y1 = bbox_px
    crop = page_rgb[y0:y1, x0:x1]
    if crop.size == 0 or stroke_rgb is None:
        return np.zeros(crop.shape[:2], dtype=bool)
    # int32 is required: squaring an int16 RGB delta can overflow and create
    # false foreground throughout a container interior.
    px = crop.astype(np.int32)
    stroke = np.array(stroke_rgb, dtype=np.int32)
    ds = np.sqrt(np.sum((px - stroke) ** 2, axis=2))
    border = np.concatenate(
        [crop[0].reshape(-1, 3), crop[-1].reshape(-1, 3), crop[:, 0].reshape(-1, 3), crop[:, -1].reshape(-1, 3)],
        axis=0,
    )
    bg = np.median(border, axis=0).astype(np.int32)
    db = np.sqrt(np.sum((px - bg) ** 2, axis=2))
    mask = (ds < db) & (db >= 20)
    if fill_rgb is not None:
        fill = np.array(fill_rgb, dtype=np.int32)
        df = np.sqrt(np.sum((px - fill) ** 2, axis=2))
        mask &= ds <= df
    if kind == "EDGE_LINE":
        # Restrict to the vector segment tube. This prevents the padded raster
        # bbox from borrowing pixels from the connected node border / arrowhead.
        line_items = [it for it in items if it and it[0] == "l"]
        if line_items:
            _, p0, p1 = line_items[0]
            ax, ay = float(p0.x) * SCALE_300, float(p0.y) * SCALE_300
            bx, by = float(p1.x) * SCALE_300, float(p1.y) * SCALE_300
            yy, xx = np.indices(mask.shape)
            gx = xx + x0
            gy = yy + y0
            vx, vy = bx - ax, by - ay
            denom = vx * vx + vy * vy
            t = ((gx - ax) * vx + (gy - ay) * vy) / denom if denom else np.zeros_like(gx, dtype=float)
            projx = ax + np.clip(t, 0, 1) * vx
            projy = ay + np.clip(t, 0, 1) * vy
            dist = np.hypot(gx - projx, gy - projy)
            mask &= (t >= -0.02) & (t <= 1.02) & (dist <= 4.0)
            if max(stroke_rgb) - min(stroke_rgb) < 45:
                spread = px.max(axis=2) - px.min(axis=2)
                mask &= spread <= 45
    # For border containers, only the real perimeter stroke is foreground.
    if kind in {"PANEL_BORDER", "NODE_BORDER"} and crop.shape[0] > 8 and crop.shape[1] > 8:
        yy, xx = np.indices(mask.shape)
        band = 10
        perimeter = (xx < band) | (xx >= mask.shape[1] - band) | (yy < band) | (yy >= mask.shape[0] - band)
        if kind == "NODE_BORDER" and stroke_rgb[0] > stroke_rgb[2]:
            # The only gold node is the diamond: color selection is unique and
            # its sloped perimeter must not be replaced by a rectangular band.
            perimeter = np.ones(mask.shape, dtype=bool)
            # Exclude black formula ink, which is numerically closer to the
            # dark gold stroke than to the pale gold fill but is not gold-hued.
            perimeter &= (px[:, :, 0] > px[:, :, 1] + 10) & (px[:, :, 1] > px[:, :, 2] + 10)
        mask &= perimeter
    return mask


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def sparse_coords(mask: np.ndarray, bbox_px: tuple[int, int, int, int]) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    return np.column_stack([xs + bbox_px[0], ys + bbox_px[1]]).astype(np.int32)


def exact_clearance(a: np.ndarray, b: np.ndarray, bbox_clearance: float) -> float | None:
    if len(a) == 0 or len(b) == 0:
        return None
    if bbox_clearance > 40:
        return float(bbox_clearance)
    # Nearby objects are small in this figure. Chunked exact Euclidean distance avoids a scipy dependency.
    best2 = float("inf")
    small, other = (a, b) if len(a) <= len(b) else (b, a)
    for start in range(0, len(small), 256):
        q = small[start : start + 256].astype(np.int32)
        for ostart in range(0, len(other), 4096):
            r = other[ostart : ostart + 4096].astype(np.int32)
            d = q[:, None, :] - r[None, :, :]
            m = int(np.min(np.sum(d * d, axis=2)))
            if m < best2:
                best2 = m
            if best2 == 0:
                return 0.0
    return math.sqrt(best2)


def bbox_distance(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def intersection_count(a: np.ndarray, b: np.ndarray) -> int:
    if len(a) == 0 or len(b) == 0:
        return 0
    sa = {int(y) << 32 | int(x) for x, y in a}
    return sum(1 for x, y in b if (int(y) << 32 | int(x)) in sa)


def pair_class(a: dict, b: dict) -> tuple[str, int, str]:
    if a["object_type"] == "GLYPH" and b["object_type"] == "GLYPH":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "SAME_SEMANTIC_TEXT_PARENT", 0, "DESIGN_INTERNAL_EXEMPT"
        return "TEXT_TEXT", 4, "HARD_GEOMETRY"
    if a["object_type"] == "GRAPHIC" and b["object_type"] == "GRAPHIC":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "SAME_STRUCTURAL_PARENT", 0, "DESIGN_CONNECTION_EXEMPT"
        return "GRAPHIC_GRAPHIC", 0, "STRUCTURAL_REVIEW"
    glyph = a if a["object_type"] == "GLYPH" else b
    graphic = b if a["object_type"] == "GLYPH" else a
    role = graphic["role"]
    if role == "PANEL_BORDER":
        return "TEXT_PANEL_BORDER", 6, "HARD_GEOMETRY"
    if role == "NODE_BORDER":
        return "TEXT_NODE_BORDER", 5, "HARD_GEOMETRY"
    if role in {"EDGE_LINE", "ARROWHEAD"}:
        return "TEXT_LINE_ARROW", 3, "HARD_GEOMETRY"
    return "TEXT_GRAPHIC", 3, "HARD_GEOMETRY"


def make_contact(obj: dict, page_img: Image.Image, out_1x: Path, out_8x: Path) -> None:
    x0, y0, x1, y1 = obj["bbox_px"]
    pad = 5
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(page_img.width, x1 + pad), min(page_img.height, y1 + pad)
    original = page_img.crop((rx0, ry0, rx1, ry1)).convert("RGB")
    overlay = original.copy()
    mask_full = Image.new("L", original.size, 0)
    local_mask = Image.open(obj["mask_path_abs"]).convert("L")
    mask_full.paste(local_mask, (x0 - rx0, y0 - ry0))
    oa = np.asarray(overlay).copy()
    mm = np.asarray(mask_full) > 0
    oa[mm] = [255, 0, 0]
    overlay = Image.fromarray(oa)
    mask_only = Image.new("RGB", original.size, "white")
    ma = np.asarray(mask_only).copy()
    ma[mm] = [0, 0, 0]
    mask_only = Image.fromarray(ma)
    label_h = 18
    sheet = Image.new("RGB", (original.width * 3, original.height + label_h), "white")
    sheet.paste(original, (0, label_h))
    sheet.paste(overlay, (original.width, label_h))
    sheet.paste(mask_only, (original.width * 2, label_h))
    draw = ImageDraw.Draw(sheet)
    draw.text((1, 1), "ORIGINAL", fill="black")
    draw.text((original.width + 1, 1), "TARGET OVERLAY", fill="black")
    draw.text((original.width * 2 + 1, 1), "MASK ONLY", fill="black")
    sheet.save(out_1x)
    sheet.resize((sheet.width * 8, sheet.height * 8), Image.Resampling.NEAREST).save(out_8x)


def montage(paths: list[Path], labels: list[str], out: Path, columns: int = 2) -> None:
    imgs = [Image.open(p).convert("RGB") for p in paths]
    label_h = 32
    cell_w = max(im.width for im in imgs)
    cell_h = max(im.height for im in imgs) + label_h
    rows = math.ceil(len(imgs) / columns)
    canvas = Image.new("RGB", (cell_w * columns, cell_h * rows), "white")
    d = ImageDraw.Draw(canvas)
    for i, (im, label) in enumerate(zip(imgs, labels)):
        x = (i % columns) * cell_w
        y = (i // columns) * cell_h
        d.text((x + 3, y + 3), label, fill="black")
        canvas.paste(im, (x, y + label_h))
    canvas.save(out)


def make_pair_roi(pair: dict, a: dict, b: dict, page_img: Image.Image) -> str:
    x0 = max(0, min(a["bbox_px"][0], b["bbox_px"][0]) - 8)
    y0 = max(0, min(a["bbox_px"][1], b["bbox_px"][1]) - 8)
    x1 = min(page_img.width, max(a["bbox_px"][2], b["bbox_px"][2]) + 8)
    y1 = min(page_img.height, max(a["bbox_px"][3], b["bbox_px"][3]) + 8)
    w, h = x1 - x0, y1 - y0
    original = page_img.crop((x0, y0, x1, y1)).convert("RGB")
    ma = np.zeros((h, w), dtype=bool)
    mb = np.zeros((h, w), dtype=bool)
    if len(a["coords"]):
        ma[a["coords"][:, 1] - y0, a["coords"][:, 0] - x0] = True
    if len(b["coords"]):
        mb[b["coords"][:, 1] - y0, b["coords"][:, 0] - x0] = True
    inter = ma & mb
    prefix = pair["pair_id"]
    base = ROOT / "roi" / prefix
    original.save(base.with_name(prefix + "_original_1x.png"))
    Image.fromarray(ma.astype(np.uint8) * 255, mode="L").save(base.with_name(prefix + "_mask_a_1x.png"))
    Image.fromarray(mb.astype(np.uint8) * 255, mode="L").save(base.with_name(prefix + "_mask_b_1x.png"))
    Image.fromarray(inter.astype(np.uint8) * 255, mode="L").save(base.with_name(prefix + "_intersection_1x.png"))
    oa = np.asarray(original).copy()
    oa[ma] = [255, 0, 0]
    oa[mb] = [0, 80, 255]
    oa[inter] = [255, 0, 255]
    overlay = Image.fromarray(oa)
    overlay.save(base.with_name(prefix + "_overlay_1x.png"))
    mask_a_rgb = Image.fromarray(np.where(ma[:, :, None], np.array([0, 0, 0], dtype=np.uint8), np.array([255, 255, 255], dtype=np.uint8)))
    mask_b_rgb = Image.fromarray(np.where(mb[:, :, None], np.array([0, 0, 0], dtype=np.uint8), np.array([255, 255, 255], dtype=np.uint8)))
    inter_rgb = Image.fromarray(np.where(inter[:, :, None], np.array([255, 0, 255], dtype=np.uint8), np.array([255, 255, 255], dtype=np.uint8)))
    quad = Image.new("RGB", (w * 5, h + 20), "white")
    qd = ImageDraw.Draw(quad)
    for i, label in enumerate(["ORIGINAL", "A MASK", "B MASK", "INTERSECTION", "OVERLAY"]):
        qd.text((i * w + 1, 1), label, fill="black")
    for i, im in enumerate([original, mask_a_rgb, mask_b_rgb, inter_rgb, overlay]):
        quad.paste(im, (i * w, 20))
    quad.save(base.with_name(prefix + "_quint_1x.png"))
    quad.resize((quad.width * 8, quad.height * 8), Image.Resampling.NEAREST).save(base.with_name(prefix + "_quint_8x_nearest.png"))
    return f"roi/{prefix}"


def main() -> None:
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    for name in ["masks/glyph", "masks/graphic", "contacts/glyph/one_x", "contacts/glyph/eight_x", "contacts/graphic/one_x", "contacts/graphic/eight_x", "contact_sheets", "roi"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    page_300_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, colorspace=fitz.csRGB)
    page_300 = pix_to_pil(page_300_pix).convert("RGB")
    page_rgb = np.asarray(page_300)
    page_200 = pix_to_pil(page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False, colorspace=fitz.csRGB))
    page_200.save(ROOT / "full_page_200dpi.png")
    fig_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), clip=FIGURE_CLIP_PT, alpha=False, colorspace=fitz.csRGB)
    fig_img = pix_to_pil(fig_pix).convert("RGB")
    fig_img.save(ROOT / "figure_crop_300dpi.png")
    stand_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), clip=STANDALONE_CLIP_PT, alpha=False, colorspace=fitz.csRGB)
    pix_to_pil(stand_pix).convert("RGB").save(ROOT / "standalone_300dpi.png")
    gray_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), clip=FIGURE_CLIP_PT, alpha=False, colorspace=fitz.csGRAY)
    pix_to_pil(gray_pix).save(ROOT / "grayscale_300dpi.png")

    identity = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "role": "SA3 fresh isolated",
        "source_writer": "NONE",
        "tex_execution": "DISABLED",
        "official_pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "pdf_pages": len(doc),
        "page_size_pt": [page_rect.width, page_rect.height],
        "page_size_name": "A4",
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_index_zero_based": PAGE_INDEX,
        "figure_number": "32.7",
        "figure_label": "fig:V5-C03-componentwise-sweep",
        "location_method": "Independent text match in official R104 PDF for both panel titles and current caption; no inherited evidence.",
        "source_path": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "body_path": str(BODY),
        "body_bytes": BODY.stat().st_size,
        "body_sha256": sha256(BODY),
        "native_page_300dpi_px": [page_300.width, page_300.height],
        "native_page_200dpi_px": [page_200.width, page_200.height],
        "figure_clip_pt": list(FIGURE_CLIP_PT),
        "figure_crop_300dpi_px": [fig_img.width, fig_img.height],
        "figure_clip_page_px": list(pt_bbox_to_px(FIGURE_CLIP_PT)),
        "standalone_clip_pt": list(STANDALONE_CLIP_PT),
        "standalone_300dpi_px": [stand_pix.width, stand_pix.height],
        "standalone_clip_page_px": list(pt_bbox_to_px(STANDALONE_CLIP_PT)),
        "render_engine": f"PyMuPDF {fitz.VersionBind}",
        "render_contract": "Direct official-PDF rasterization; 300 dpi views were not resized; 8x artifacts use nearest-neighbour only for review.",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    write_json(ROOT / "IDENTITY.json", identity)

    blocks = page.get_text("rawdict")["blocks"]
    objects: list[dict] = []
    excluded: list[dict] = []
    glyph_rows: list[dict] = []
    gid = 0
    for bi, block in enumerate(blocks):
        if block.get("type") != 0 or bi not in TARGET_TEXT_BLOCKS:
            continue
        parent, role, panel = TEXT_PARENT[bi]
        visible_index = 0
        for li, line in enumerate(block["lines"]):
            for si, span in enumerate(line["spans"]):
                span_rgb = rgb_from_int(span.get("color", 0))
                for ci, ch in enumerate(span.get("chars", [])):
                    c = ch["c"]
                    if c.isspace():
                        excluded.append({
                            "source_kind": "CHAR",
                            "source_index": f"block={bi};line={li};span={si};char={ci}",
                            "value": repr(c),
                            "reason": "WHITESPACE_HAS_NO_VISIBLE_INK",
                            "semantic_parent": parent,
                        })
                        continue
                    gid += 1
                    visible_index += 1
                    oid = f"T{bi:02d}-G{visible_index:03d}"
                    safe = f"glyph_{gid:04d}.png"
                    bbox_pt = tuple(float(v) for v in ch["bbox"])
                    bbox_px = pt_bbox_to_px(bbox_pt)
                    mask = local_contrast_mask(page_rgb, bbox_px)
                    mask_path = ROOT / "masks" / "glyph" / safe
                    save_mask(mask, mask_path)
                    coords = sparse_coords(mask, bbox_px)
                    h_ink = int(coords[:, 1].max() - coords[:, 1].min() + 1) if len(coords) else 0
                    w_ink = int(coords[:, 0].max() - coords[:, 0].min() + 1) if len(coords) else 0
                    category, threshold = classify_char(c, float(span["size"]), role)
                    legacy_status = "CALIBRATION_REQUIRED" if threshold == "CALIBRATION" else ("PASS" if h_ink >= int(threshold) else "BELOW_LEGACY_THRESHOLD")
                    codepoint_ok = c != "\ufffd" and not (0xD800 <= ord(c) <= 0xDFFF)
                    row = {
                        "object_id": oid,
                        "safe_filename": safe,
                        "object_type": "GLYPH",
                        "semantic_parent": parent,
                        "role": role,
                        "panel": panel,
                        "source_pdf_block": bi,
                        "source_pdf_line": li,
                        "source_pdf_span": si,
                        "source_pdf_char": ci,
                        "char": c,
                        "unicode": f"U+{ord(c):04X}",
                        "unicode_name": unicodedata.name(c, "UNNAMED"),
                        "font": span.get("font", ""),
                        "span_size_pt": float(span["size"]),
                        "span_color_rgb": list(span_rgb),
                        "bbox_pt": list(bbox_pt),
                        "bbox_px": list(bbox_px),
                        "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
                        "mask_path_abs": str(mask_path),
                        "mask_pixel_count": int(mask.sum()),
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "glyph_category": category,
                        "legacy_threshold": threshold,
                        "legacy_machine_status": legacy_status,
                        "codepoint_extractable": codepoint_ok,
                        "empty_mask": len(coords) == 0,
                        "coords": coords,
                    }
                    objects.append(row)
                    glyph_rows.append({k: v for k, v in row.items() if k not in {"coords", "mask_path_abs"}})

    drawings = page.get_drawings()
    graphic_rows: list[dict] = []
    for di in sorted(TARGET_DRAWINGS):
        d = drawings[di]
        oid, role, parent = DRAWING_META[di]
        bbox_pt = tuple(float(v) for v in d["rect"])
        pad = 2 if role == "EDGE_LINE" else (1 if role == "ARROWHEAD" else 3)
        bbox_px = pt_bbox_to_px(bbox_pt, pad=pad)
        stroke_rgb = rgb_from_float(d.get("color"))
        fill_rgb = rgb_from_float(d.get("fill"))
        mask = drawing_mask(page_rgb, bbox_px, stroke_rgb, fill_rgb, role, d.get("items", []))
        safe = f"graphic_{di:03d}.png"
        mask_path = ROOT / "masks" / "graphic" / safe
        save_mask(mask, mask_path)
        coords = sparse_coords(mask, bbox_px)
        row = {
            "object_id": oid,
            "safe_filename": safe,
            "object_type": "GRAPHIC",
            "semantic_parent": parent,
            "role": role,
            "panel": "LEFT" if (bbox_pt[0] + bbox_pt[2]) / 2 < page_rect.width / 2 else "RIGHT",
            "source_pdf_drawing_index": di,
            "drawing_type": d.get("type"),
            "item_count": len(d.get("items", [])),
            "stroke_rgb": list(stroke_rgb) if stroke_rgb else None,
            "fill_rgb": list(fill_rgb) if fill_rgb else None,
            "line_width_pt": d.get("width"),
            "bbox_pt": list(bbox_pt),
            "bbox_px": list(bbox_px),
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "mask_path_abs": str(mask_path),
            "mask_pixel_count": int(mask.sum()),
            "empty_mask": len(coords) == 0,
            "coords": coords,
        }
        objects.append(row)
        graphic_rows.append({k: v for k, v in row.items() if k not in {"coords", "mask_path_abs"}})

    # Contact evidence: every atomic object gets its own independent 1x and 8x triptych.
    for obj in objects:
        kind_dir = "glyph" if obj["object_type"] == "GLYPH" else "graphic"
        stem = Path(obj["safe_filename"]).stem
        p1 = ROOT / "contacts" / kind_dir / "one_x" / f"{stem}_1x.png"
        p8 = ROOT / "contacts" / kind_dir / "eight_x" / f"{stem}_8x_nearest.png"
        make_contact(obj, page_300, p1, p8)
        obj["contact_1x"] = str(p1.relative_to(ROOT)).replace("\\", "/")
        obj["contact_8x"] = str(p8.relative_to(ROOT)).replace("\\", "/")

    # Full target overlay: body and caption, with unique atomic-object IDs.
    overlay = fig_img.copy()
    od = ImageDraw.Draw(overlay)
    fx0, fy0, _, _ = pt_bbox_to_px(FIGURE_CLIP_PT)
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox_px"]
        color = "#cc0000" if obj["object_type"] == "GLYPH" else "#0066cc"
        od.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=color, width=1)
        od.text((x0 - fx0, y0 - fy0), obj["object_id"], fill=color)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Build montages solely for navigation; per-object native triptychs remain authoritative.
    for kind in ["glyph", "graphic"]:
        subset = [o for o in objects if o["object_type"].lower() == kind]
        for start in range(0, len(subset), 12):
            chunk = subset[start : start + 12]
            paths = [ROOT / o["contact_8x"] for o in chunk]
            labels = [o["object_id"] for o in chunk]
            montage(paths, labels, ROOT / "contact_sheets" / f"{kind}_8x_sheet_{start // 12 + 1:03d}.png", columns=2)

    pair_rows: list[dict] = []
    overlap_candidates = 0
    clearance_candidates = 0
    for pi, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        bc = bbox_distance(a["bbox_px"], b["bbox_px"])
        inter = intersection_count(a["coords"], b["coords"])
        clearance = exact_clearance(a["coords"], b["coords"], bc)
        relation, required, policy = pair_class(a, b)
        candidate = inter > 0 or (required > 0 and clearance is not None and clearance < required)
        overlap_candidates += int(inter > 0)
        clearance_candidates += int(required > 0 and clearance is not None and clearance < required)
        pair_rows.append({
            "pair_id": f"P{pi:06d}",
            "a_id": a["object_id"],
            "b_id": b["object_id"],
            "a_type": a["object_type"],
            "b_type": b["object_type"],
            "a_parent": a["semantic_parent"],
            "b_parent": b["semantic_parent"],
            "relation_class": relation,
            "policy": policy,
            "required_clearance_px": required,
            "bbox_clearance_px": round(bc, 3),
            "raw_mask_intersection_px": inter,
            "raw_mask_clearance_px": "" if clearance is None else round(clearance, 3),
            "machine_candidate": candidate,
            "roi_bundle_prefix": "",
        })

    by_id = {o["object_id"]: o for o in objects}
    for pair in pair_rows:
        if pair["machine_candidate"]:
            pair["roi_bundle_prefix"] = make_pair_roi(pair, by_id[pair["a_id"]], by_id[pair["b_id"]], page_300)

    object_export = []
    for o in objects:
        object_export.append({k: v for k, v in o.items() if k not in {"coords", "mask_path_abs"}})
    write_csv(ROOT / "machine_object_inventory.csv", object_export)
    write_csv(ROOT / "after_pixel_measurements.csv", glyph_rows)
    write_csv(ROOT / "machine_graphic_inventory.csv", graphic_rows)
    write_csv(ROOT / "machine_excluded_elements.csv", excluded)
    write_csv(ROOT / "machine_pair_inventory.csv", pair_rows)
    write_csv(ROOT / "after_overlap_report.csv", [r for r in pair_rows if str(r["machine_candidate"]).lower() == "true"], list(pair_rows[0].keys()))
    write_csv(
        ROOT / "id_safe_filename_map.csv",
        [{"object_id": o["object_id"], "safe_filename": o["safe_filename"], "mask_path": o["mask_path"], "contact_1x": o["contact_1x"], "contact_8x": o["contact_8x"]} for o in objects],
    )

    n = len(objects)
    summary = {
        "uid": UID,
        "physical_page": PHYSICAL_PAGE,
        "glyph_object_count": len(glyph_rows),
        "graphic_object_count": len(graphic_rows),
        "total_atomic_foreground_object_count": n,
        "complete_unordered_pair_denominator_C_n_2": n * (n - 1) // 2,
        "pair_rows_written": len(pair_rows),
        "pair_denominator_complete": len(pair_rows) == n * (n - 1) // 2,
        "empty_mask_count": sum(bool(o["empty_mask"]) for o in objects),
        "replacement_character_count": sum(o.get("char") == "\ufffd" for o in objects),
        "machine_raw_overlap_candidate_pair_count": overlap_candidates,
        "machine_clearance_candidate_pair_count": clearance_candidates,
        "visible_math_rule_count": 0,
        "visible_math_rule_basis": "Formulae contain font glyphs (including SUM); no overline/underline/hat/root/fraction/cancel path is present in target drawings 1-23.",
        "excluded_whitespace_char_count": len(excluded),
        "target_pdf_text_block_indices": sorted(TARGET_TEXT_BLOCKS),
        "target_pdf_drawing_indices": sorted(TARGET_DRAWINGS),
        "source_effective_font_inventory": {
            "global_slfig": "9.2pt / 11.0pt; no graphics scale",
            "every_node": "9.2pt / 11.0pt; no graphics scale",
            "panel_titles": "9.8pt / 11.8pt bold",
            "caption": "document caption style not declared in the single-source figure file; measured from official PDF",
            "resizebox_scalebox_scale_transform_shape": "none",
        },
        "r168_font_policy": "9.2pt vs legacy 9.5pt and micro-ratio/taxonomy findings are advisory unless actual unreadability, severe imbalance, tofu/wrong glyph/codepoint/math semantics, real clip, or illegal overlap is found.",
    }
    write_json(ROOT / "machine_summary.json", summary)

    # Source-only font inventory: factual declarations, no reviewer judgement.
    src = SOURCE.read_text(encoding="utf-8")
    font_rows = [
        {"scope": "slfig-FIG-P605-01", "declared_pt": 9.2, "leading_pt": 11.0, "graphics_scale": 1.0, "effective_pt": 9.2, "source_token": "font=\\fontsize{9.2pt}{11.0pt}\\selectfont"},
        {"scope": "tikz every node", "declared_pt": 9.2, "leading_pt": 11.0, "graphics_scale": 1.0, "effective_pt": 9.2, "source_token": "every node/.style={font=\\fontsize{9.2pt}{11.0pt}\\selectfont}"},
        {"scope": "left panel title", "declared_pt": 9.8, "leading_pt": 11.8, "graphics_scale": 1.0, "effective_pt": 9.8, "source_token": "font=\\fontsize{9.8pt}{11.8pt}\\selectfont\\bfseries"},
        {"scope": "right panel title", "declared_pt": 9.8, "leading_pt": 11.8, "graphics_scale": 1.0, "effective_pt": 9.8, "source_token": "font=\\fontsize{9.8pt}{11.8pt}\\selectfont\\bfseries"},
        {"scope": "caption", "declared_pt": "NOT_IN_SINGLE_SOURCE", "leading_pt": "NOT_IN_SINGLE_SOURCE", "graphics_scale": 1.0, "effective_pt": "MEASURED_FROM_PDF", "source_token": "\\caption{...}"},
    ]
    write_csv(ROOT / "after_font_audit.csv", font_rows)
    write_json(
        ROOT / "machine_source_scan.json",
        {
            "source_path": str(SOURCE),
            "fontsize_tokens": re.findall(r"\\fontsize\{[^}]+\}\{[^}]+\}", src),
            "tiny_count": src.count("\\tiny"),
            "scriptsize_count": src.count("\\scriptsize"),
            "footnotesize_count": src.count("\\footnotesize"),
            "small_count": src.count("\\small"),
            "large_count": src.count("\\large"),
            "resizebox_count": src.count("\\resizebox"),
            "scalebox_count": src.count("\\scalebox"),
            "scale_option_count": len(re.findall(r"(?:^|[,\[])\s*scale\s*=", src)),
            "transform_shape_count": src.count("transform shape"),
        },
    )

    # Clip check against official page and padded evidence clips.
    clip_rows = []
    for o in objects:
        x0, y0, x1, y1 = o["bbox_px"]
        page_touch = x0 <= 0 or y0 <= 0 or x1 >= page_300.width or y1 >= page_300.height
        clip_rows.append({
            "object_id": o["object_id"],
            "page_edge_touch": page_touch,
            "page_clip_pixel_candidate": 1 if page_touch else 0,
            "bbox_px": json.dumps(o["bbox_px"]),
        })
    write_csv(ROOT / "machine_clip_inventory.csv", clip_rows)

    # A compact mechanical integrity report. Manual decision fields are intentionally absent.
    report = [
        "# Machine evidence integrity report",
        "",
        f"- HANDOFF_ID: `{HANDOFF_ID}`",
        f"- UID: `{UID}`",
        f"- Official PDF physical page: `{PHYSICAL_PAGE}` (printed `{PRINTED_PAGE}`)",
        f"- Atomic objects: `{n}` = glyphs `{len(glyph_rows)}` + graphics `{len(graphic_rows)}`",
        f"- Complete unordered pairs: `{len(pair_rows)}` = C({n},2)",
        f"- Empty masks: `{summary['empty_mask_count']}`",
        f"- Replacement-codepoint candidates: `{summary['replacement_character_count']}`",
        f"- Machine raw-overlap candidate pairs: `{overlap_candidates}`",
        f"- Machine clearance candidate pairs: `{clearance_candidates}`",
        "- TeX execution: `DISABLED`; source writer: `NONE`.",
        "- This file contains no manual reviewer boolean, decision, or note.",
    ]
    (ROOT / "MACHINE_INTEGRITY.md").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
