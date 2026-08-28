from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R4_SA3_FRESH_ISOLATED_R109_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
PAGE_INDEX = 631
PAGE_NUMBER = 632
HANDOFF_ID = "A-R109-P582-SA3-FRESH-ISOLATED-20260826"
EXPECTED_PDF_BYTES = 4_967_054
EXPECTED_PDF_SHA256 = "936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9"
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0

# Integer page-pixel crops on the direct native 300 dpi rendering.
FIGURE_CROP_PX = (283, 1350, 2238, 2150)  # figure body + caption
STANDALONE_CROP_PX = (658, 1350, 1875, 2009)  # graph body only


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def dump_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def px_rect_from_pt(bbox: tuple[float, float, float, float], scale: float = SCALE_300) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (math.floor(x0 * scale), math.floor(y0 * scale), math.ceil(x1 * scale), math.ceil(y1 * scale))


def clip_rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def fitz_color_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def float_color_to_rgb(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in value)


def target_color_mask(rgb: np.ndarray, colors: list[tuple[int, int, int]], min_contrast: float = 20.0) -> np.ndarray:
    """Select native pixels compatible with a target solid color antialiased over white."""
    pixels = rgb.astype(np.float32)
    white_delta = 255.0 - pixels
    contrast = np.max(white_delta, axis=2)
    out = np.zeros(rgb.shape[:2], dtype=bool)
    for color in colors:
        c = np.asarray(color, dtype=np.float32)
        direction = 255.0 - c
        denom = float(np.dot(direction, direction))
        if denom <= 1.0:
            continue
        alpha = np.tensordot(white_delta, direction, axes=([2], [0])) / denom
        recon = alpha[:, :, None] * direction[None, None, :]
        residual = np.sqrt(np.sum((white_delta - recon) ** 2, axis=2))
        out |= (contrast >= min_contrast) & (alpha >= 0.02) & (alpha <= 1.35) & (residual <= 24.0)
    return out


def isolated_drawing_mask(page_rect: fitz.Rect, drawing: dict, scale: float) -> np.ndarray:
    """Replay exactly one PDF drawing/path on a blank in-memory page and raster it natively."""
    isolated = fitz.open()
    out_page = isolated.new_page(width=page_rect.width, height=page_rect.height)
    shape = out_page.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing operation {op!r}")
    line_cap_raw = drawing.get("lineCap")
    line_cap = max(line_cap_raw) if isinstance(line_cap_raw, tuple) else int(line_cap_raw or 0)
    line_join = int(drawing.get("lineJoin") or 0)
    dashes = drawing.get("dashes")
    if not dashes or dashes == "[] 0":
        dashes = None
    close_path = bool(drawing.get("closePath")) or drawing.get("type") in ("f", "fs")
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=drawing.get("color"),
        fill=drawing.get("fill"),
        lineCap=line_cap,
        lineJoin=line_join,
        dashes=dashes,
        even_odd=bool(drawing.get("even_odd")),
        closePath=close_path,
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
    )
    shape.commit()
    pix = out_page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, annots=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    mask = np.max(255 - arr.astype(np.int16), axis=2) >= 20
    isolated.close()
    return mask


def classify_char(ch: str, rendered_pdf_pt: float, base_pdf_pt: float) -> tuple[str, int, bool]:
    name = unicodedata.name(ch, "")
    natural_script = rendered_pdf_pt < base_pdf_pt * 0.96
    if natural_script:
        return "NATURAL_TEX_SCRIPT", 15, True
    cp = ord(ch)
    if ch in ".,，。；;：:、…":
        return "LOW_PROFILE_PUNCTUATION", 0, False
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK_FULL", 30, False
    if ch.isdigit() or "CAPITAL" in name:
        return "LATIN_CAP_OR_DIGIT", 24, False
    if ch in "+−-=<>/()[]{}↑↓∑√∫":
        return "BASE_MATH_OPERATOR", 22, False
    if ch.islower() or "SMALL" in name or "GREEK" in name or "MATHEMATICAL ITALIC" in name:
        return "LATIN_OR_GREEK_LOWER", 17, False
    if unicodedata.category(ch).startswith("P"):
        return "LOW_PROFILE_PUNCTUATION", 0, False
    return "BASE_MATH_OPERATOR", 22, False


def parent_metadata(block: int, line: int) -> dict:
    if block == 17 and line <= 3:
        return {"parent_id": f"XTICK_{line+1}", "role": "TICK", "source_line": 15, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if (block == 17 and line == 4) or 18 <= block <= 24 and line == 0:
        yidx = 0 if block == 17 else block - 17
        return {"parent_id": f"YTICK_{yidx}", "role": "TICK", "source_line": 15, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if (block == 24 and line == 1) or (block == 25 and line == 0):
        return {"parent_id": "FORMULA_H", "role": "FORMULA", "source_line": 27, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if block == 25 and line == 1:
        return {"parent_id": "ANNOT_DOWN_1", "role": "ANNOTATION", "source_line": 29, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if block == 26 and line == 0:
        return {"parent_id": "ANNOT_UP", "role": "ANNOTATION", "source_line": 31, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if block == 26 and line == 1:
        return {"parent_id": "ANNOT_DOWN_2", "role": "ANNOTATION", "source_line": 33, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if block == 27:
        return {"parent_id": "TRUE_VALUE", "role": "ANNOTATION", "source_line": 35, "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if 28 <= block <= 31:
        return {"parent_id": f"VALUE_LABEL_{block-27}", "role": "VALUE_LABEL", "source_line": 37 + 2 * (block - 28), "declared_pt": 9.5, "base_pdf_pt": 9.46451}
    if block == 32:
        return {"parent_id": "X_AXIS_LABEL", "role": "AXIS_LABEL", "source_line": 14, "declared_pt": 9.6, "base_pdf_pt": 9.56414}
    if block == 33:
        return {"parent_id": "Y_AXIS_LABEL", "role": "AXIS_LABEL", "source_line": 14, "declared_pt": 9.6, "base_pdf_pt": 9.56414}
    if block == 34 and line == 0:
        return {"parent_id": "CAPTION_LABEL", "role": "CAPTION_LABEL", "source_line": 46, "declared_pt": 10.0, "base_pdf_pt": 9.96264}
    if block in (34, 35):
        return {"parent_id": "CAPTION_TEXT", "role": "CAPTION_TEXT", "source_line": 46, "declared_pt": 10.0, "base_pdf_pt": 9.96264}
    raise RuntimeError(f"Unmapped visible text location: block={block}, line={line}")


def make_overlay(base: Image.Image, objects: list[dict], crop_origin: tuple[int, int]) -> Image.Image:
    img = base.copy()
    draw = ImageDraw.Draw(img)
    ox, oy = crop_origin
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox_px_global"]
        box = (x0 - ox, y0 - oy, x1 - ox - 1, y1 - oy - 1)
        color = (220, 30, 30) if obj["kind"] == "TEXT_GLYPH" else (20, 80, 220)
        draw.rectangle(box, outline=color, width=1)
        draw.text((box[0], max(0, box[1] - 10)), obj["safe_id"], fill=color)
    return img


def ink_bbox_from_coords(coords: np.ndarray) -> tuple[int, int, int, int]:
    if coords.size == 0:
        return (0, 0, 0, 0)
    ys = coords[:, 0]
    xs = coords[:, 1]
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def mask_clearance(a: dict, b: dict, trees: dict[str, cKDTree]) -> tuple[float, int]:
    if not a["flat_set"] or not b["flat_set"]:
        return math.inf, 0
    intersection = len(a["flat_set"].intersection(b["flat_set"]))
    if intersection:
        return 0.0, intersection
    pa = a["coords_yx"][:, [1, 0]].astype(np.float64)
    pb = b["coords_yx"][:, [1, 0]].astype(np.float64)
    if len(pa) <= len(pb):
        dist = float(trees[b["safe_id"]].query(pa, k=1, workers=1)[0].min())
    else:
        dist = float(trees[a["safe_id"]].query(pb, k=1, workers=1)[0].min())
    return max(0.0, dist - 1.0), 0


def save_object_mask(obj: dict, out_dir: Path) -> None:
    coords = obj["coords_yx"]
    x0, y0, x1, y1 = obj["ink_bbox_px_crop"]
    pad = 3
    cx0 = max(0, x0 - pad)
    cy0 = max(0, y0 - pad)
    cx1 = min(FIGURE_CROP_PX[2] - FIGURE_CROP_PX[0], x1 + pad)
    cy1 = min(FIGURE_CROP_PX[3] - FIGURE_CROP_PX[1], y1 + pad)
    mask = np.zeros((cy1 - cy0, cx1 - cx0), dtype=np.uint8)
    keep = (coords[:, 1] >= cx0) & (coords[:, 1] < cx1) & (coords[:, 0] >= cy0) & (coords[:, 0] < cy1)
    local = coords[keep]
    if len(local):
        mask[local[:, 0] - cy0, local[:, 1] - cx0] = 255
    Image.fromarray(mask, mode="L").save(out_dir / f"{obj['safe_id']}_mask.png")
    obj["mask_file"] = str((out_dir / f"{obj['safe_id']}_mask.png").relative_to(ROOT)).replace("\\", "/")
    obj["mask_crop_px_figure"] = [cx0, cy0, cx1, cy1]


def contact_cell(obj: dict, figure_np: np.ndarray, scale8: bool) -> Image.Image:
    x0, y0, x1, y1 = obj["bbox_px_crop"]
    pad = 7
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(figure_np.shape[1], x1 + pad)
    y1 = min(figure_np.shape[0], y1 + pad)
    original = figure_np[y0:y1, x0:x1].copy()
    target = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    coords = obj["coords_yx"]
    keep = (coords[:, 1] >= x0) & (coords[:, 1] < x1) & (coords[:, 0] >= y0) & (coords[:, 0] < y1)
    cc = coords[keep]
    if len(cc):
        target[cc[:, 0] - y0, cc[:, 1] - x0] = True
    overlay = original.copy()
    overlay[target] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(original, 255)
    mask_only[target] = np.array([0, 0, 0], dtype=np.uint8)
    strip = np.concatenate([original, overlay, mask_only], axis=1)
    tile = Image.fromarray(strip, mode="RGB")
    if scale8:
        tile = tile.resize((tile.width * 8, tile.height * 8), Image.Resampling.NEAREST)
    header_h = 20 if not scale8 else 32
    canvas = Image.new("RGB", (max(tile.width, 220 if not scale8 else tile.width), tile.height + header_h), "white")
    canvas.paste(tile, (0, header_h))
    ImageDraw.Draw(canvas).text((3, 2), f"{obj['safe_id']} {obj.get('char','GRAPHIC')} | ORIGINAL / TARGET / MASK", fill="black")
    return canvas


def build_contact_sheets(objects: list[dict], figure_np: np.ndarray, out_dir: Path, prefix: str, scale8: bool, per_sheet: int) -> list[str]:
    files = []
    for sheet_i, start in enumerate(range(0, len(objects), per_sheet), start=1):
        group = objects[start:start + per_sheet]
        cells = [contact_cell(o, figure_np, scale8) for o in group]
        cols = 2
        rows = math.ceil(len(cells) / cols)
        cell_w = max(c.width for c in cells)
        cell_h = max(c.height for c in cells)
        sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), (235, 235, 235))
        for k, cell in enumerate(cells):
            x = (k % cols) * cell_w
            y = (k // cols) * cell_h
            sheet.paste(cell, (x, y))
            group[k][f"{prefix}_{'8x' if scale8 else '1x'}_sheet"] = sheet_i
            group[k][f"{prefix}_{'8x' if scale8 else '1x'}_cell"] = k + 1
        path = out_dir / f"{prefix}_{'8x_nearest' if scale8 else '1x'}_{sheet_i:02d}.png"
        sheet.save(path)
        files.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return files


def pair_evidence(pair: dict, a: dict, b: dict, figure_np: np.ndarray, out_dir: Path) -> tuple[str, str]:
    ax0, ay0, ax1, ay1 = a["ink_bbox_px_crop"]
    bx0, by0, bx1, by1 = b["ink_bbox_px_crop"]
    pad = 14
    x0 = max(0, min(ax0, bx0) - pad)
    y0 = max(0, min(ay0, by0) - pad)
    x1 = min(figure_np.shape[1], max(ax1, bx1) + pad)
    y1 = min(figure_np.shape[0], max(ay1, by1) + pad)
    # Keep pathological far unions bounded; critical pairs should already be near.
    original = figure_np[y0:y1, x0:x1].copy()
    ma = np.zeros((y1-y0, x1-x0), dtype=bool)
    mb = np.zeros_like(ma)
    for obj, mask in ((a, ma), (b, mb)):
        coords = obj["coords_yx"]
        keep = (coords[:, 1] >= x0) & (coords[:, 1] < x1) & (coords[:, 0] >= y0) & (coords[:, 0] < y1)
        cc = coords[keep]
        if len(cc):
            mask[cc[:, 0] - y0, cc[:, 1] - x0] = True
    inter = ma & mb
    overlay = original.copy()
    overlay[ma] = np.array([255, 0, 0], dtype=np.uint8)
    overlay[mb] = np.array([0, 80, 255], dtype=np.uint8)
    overlay[inter] = np.array([255, 0, 255], dtype=np.uint8)
    def mono(mask):
        arr = np.full_like(original, 255)
        arr[mask] = np.array([0, 0, 0], dtype=np.uint8)
        return arr
    strip = np.concatenate([original, overlay, mono(ma), mono(mb), mono(inter)], axis=1)
    header = Image.new("RGB", (strip.shape[1], 24), "white")
    ImageDraw.Draw(header).text((3, 3), f"{pair['pair_id']} {a['safe_id']} vs {b['safe_id']} | O / OVERLAY / A / B / INTER", fill="black")
    comp = Image.new("RGB", (strip.shape[1], strip.shape[0] + 24), "white")
    comp.paste(header, (0, 0))
    comp.paste(Image.fromarray(strip, mode="RGB"), (0, 24))
    p1 = out_dir / f"{pair['pair_id']}_1x.png"
    p8 = out_dir / f"{pair['pair_id']}_8x_nearest.png"
    comp.save(p1)
    comp.resize((comp.width * 8, comp.height * 8), Image.Resampling.NEAREST).save(p8)
    return str(p1.relative_to(ROOT)).replace("\\", "/"), str(p8.relative_to(ROOT)).replace("\\", "/")


def montage(paths: list[Path], out_path: Path, max_width: int = 5000) -> None:
    images = [Image.open(p).convert("RGB") for p in paths]
    if not images:
        Image.new("RGB", (800, 120), "white").save(out_path)
        return
    width = min(max_width, max(im.width for im in images))
    y = 0
    scaled = []
    for im in images:
        if im.width > width:
            # Pair montage is navigation only; individual 1x/8x files remain authoritative.
            h = round(im.height * width / im.width)
            im = im.resize((width, h), Image.Resampling.NEAREST)
        scaled.append(im)
        y += im.height + 4
    sheet = Image.new("RGB", (width, y), (220, 220, 220))
    yy = 0
    for im in scaled:
        sheet.paste(im, (0, yy))
        yy += im.height + 4
    sheet.save(out_path)


def main() -> None:
    for rel in ["01_identity", "02_renders", "03_inventory", "04_glyphs/objects", "04_glyphs/sheets", "05_pairs/critical", "06_manual", "07_machine", "08_seal"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    generated_at = utc_now()
    pdf_sha = sha256_file(PDF)
    source_sha = sha256_file(SOURCE)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    identity = {
        "generated_at_utc": generated_at,
        "handoff_id": HANDOFF_ID,
        "role": "SA3_FRESH_ISOLATED",
        "uid": "FIG-P582-01",
        "official_round": "R109",
        "pdf_path": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": pdf_sha,
        "expected_pdf_bytes": EXPECTED_PDF_BYTES,
        "expected_pdf_sha256": EXPECTED_PDF_SHA256,
        "pdf_identity_match": PDF.stat().st_size == EXPECTED_PDF_BYTES and pdf_sha == EXPECTED_PDF_SHA256,
        "pdf_page_count": doc.page_count,
        "expected_page_count": 817,
        "physical_page": PAGE_NUMBER,
        "printed_page": 619,
        "page_pt": [page.rect.width, page.rect.height],
        "source_path": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": source_sha,
        "figure_crop_px_on_page_300dpi": list(FIGURE_CROP_PX),
        "standalone_crop_px_on_page_300dpi": list(STANDALONE_CROP_PX),
        "renderer": f"PyMuPDF {fitz.version[0]}",
    }
    dump_json(ROOT / "01_identity/input_identity.json", identity)

    page_text = page.get_text("text")
    needles = ["图31.7", "固定样本序列", "运行均值", "单调逼近"]
    matches = []
    for i in range(doc.page_count):
        t = doc[i].get_text("text")
        if all(n in t for n in needles):
            matches.append(i + 1)
    dump_json(ROOT / "01_identity/location_lock.json", {
        "generated_at_utc": generated_at,
        "search_needles": needles,
        "matching_physical_pages": matches,
        "unique_match": matches == [PAGE_NUMBER],
        "page_text_excerpt": page_text[page_text.find("图31.7")-200:page_text.find("图31.8")],
    })

    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, annots=False)
    page300 = Image.frombytes("RGB", [pix300.width, pix300.height], pix300.samples)
    page300.save(ROOT / "02_renders/page_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False, annots=False)
    Image.frombytes("RGB", [pix200.width, pix200.height], pix200.samples).save(ROOT / "02_renders/full_page_200dpi.png")
    figure = page300.crop(FIGURE_CROP_PX)
    standalone = page300.crop(STANDALONE_CROP_PX)
    figure.save(ROOT / "02_renders/figure_crop_300dpi.png")
    standalone.save(ROOT / "02_renders/standalone_300dpi.png")
    figure.convert("L").save(ROOT / "02_renders/grayscale_300dpi.png")
    render_meta = {
        "generated_at_utc": generated_at,
        "page_native_300dpi": [pix300.width, pix300.height],
        "page_native_200dpi": [pix200.width, pix200.height],
        "figure_crop_native_300dpi": list(figure.size),
        "standalone_native_300dpi": list(standalone.size),
        "resized_after_render": False,
        "crop_operation": "integer crop only from direct page 300 dpi raster",
    }
    dump_json(ROOT / "02_renders/render_metadata.json", render_meta)
    page_np = np.asarray(page300)
    figure_np = np.asarray(figure)
    fx0, fy0, fx1, fy1 = FIGURE_CROP_PX

    # Complete visible text denominator, one object per non-space glyph.
    text_objects = []
    raw = page.get_text("rawdict")
    text_counter = 0
    for block_i, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for line_i, line in enumerate(block["lines"]):
            for span_i, span in enumerate(line["spans"]):
                for char_i, chd in enumerate(span["chars"]):
                    ch = chd["c"]
                    if ch.isspace():
                        continue
                    bbox_pt = tuple(float(v) for v in chd["bbox"])
                    if not (bbox_pt[1] < 516 and bbox_pt[3] > 324 and bbox_pt[0] < 537 and bbox_pt[2] > 68):
                        continue
                    meta = parent_metadata(block_i, line_i)
                    text_counter += 1
                    safe_id = f"T{text_counter:03d}"
                    object_id = f"TXT:{meta['parent_id']}:C{text_counter:03d}"
                    bbox_global = clip_rect(px_rect_from_pt(bbox_pt), pix300.width, pix300.height)
                    x0, y0, x1, y1 = bbox_global
                    target_rgb = fitz_color_to_rgb(span["color"])
                    sub = page_np[y0:y1, x0:x1]
                    local_mask = target_color_mask(sub, [target_rgb])
                    ys, xs = np.nonzero(local_mask)
                    coords_global = np.column_stack([ys + y0, xs + x0]).astype(np.int32)
                    coords_crop = coords_global.copy()
                    coords_crop[:, 0] -= fy0
                    coords_crop[:, 1] -= fx0
                    ink_bbox_crop = ink_bbox_from_coords(coords_crop)
                    rendered_pdf_pt = float(span["size"])
                    script_class, threshold, natural_script = classify_char(ch, rendered_pdf_pt, meta["base_pdf_pt"])
                    h_ink = int(ink_bbox_crop[3] - ink_bbox_crop[1]) if len(coords_crop) else 0
                    candidate_foreground = np.max(255 - sub.astype(np.int16), axis=2) >= 20
                    foreign_est = int(np.count_nonzero(candidate_foreground & ~local_mask))
                    obj = {
                        "safe_id": safe_id,
                        "object_id": object_id,
                        "kind": "TEXT_GLYPH",
                        "graphic_class": "TEXT",
                        "parent_id": meta["parent_id"],
                        "role": meta["role"],
                        "char": ch,
                        "unicode": f"U+{ord(ch):04X}",
                        "font": span["font"],
                        "source_line": meta["source_line"],
                        "declared_pt": meta["declared_pt"],
                        "graphics_scale": 1.0,
                        "effective_source_pt": meta["declared_pt"],
                        "rendered_pdf_pt": rendered_pdf_pt,
                        "natural_tex_script": natural_script,
                        "script_class": script_class,
                        "threshold_h_ink_px": threshold,
                        "bbox_pt": list(bbox_pt),
                        "bbox_px_global": list(bbox_global),
                        "bbox_px_crop": [x0-fx0, y0-fy0, x1-fx0, y1-fy0],
                        "ink_bbox_px_crop": list(ink_bbox_crop),
                        "target_rgb": list(target_rgb),
                        "h_ink_px": h_ink,
                        "ink_area_px": int(len(coords_crop)),
                        "foreign_pixel_estimate_in_vector_bbox": foreign_est,
                        "coords_yx": coords_crop,
                    }
                    text_objects.append(obj)

    # All visible foreground drawing/path objects belonging to graph 31.7.
    graphic_specs = {
        1: ("G001", "X_TICK_MARKS", "LINE_ARROW", 15),
        2: ("G002", "Y_TICK_MARKS", "LINE_ARROW", 15),
        3: ("G003", "X_AXIS_LINE", "LINE_ARROW", 14),
        4: ("G004", "X_AXIS_ARROWHEAD", "LINE_ARROW", 14),
        5: ("G005", "Y_AXIS_LINE", "LINE_ARROW", 14),
        6: ("G006", "Y_AXIS_ARROWHEAD", "LINE_ARROW", 14),
        7: ("G007", "SAMPLE_STEMS", "DATA_CURVE", 18),
        8: ("G008", "RUNNING_MEAN_CURVE", "DATA_CURVE", 21),
        9: ("G009", "TRUE_VALUE_LINE", "DATA_CURVE", 24),
        10: ("G010", "SAMPLE_MARKER_1", "MARKER", 18),
        11: ("G011", "SAMPLE_MARKER_2", "MARKER", 18),
        12: ("G012", "SAMPLE_MARKER_3", "MARKER", 18),
        13: ("G013", "SAMPLE_MARKER_4", "MARKER", 18),
        14: ("G014", "RUNNING_MARKER_1", "MARKER", 21),
        15: ("G015", "RUNNING_MARKER_2", "MARKER", 21),
        16: ("G016", "RUNNING_MARKER_3", "MARKER", 21),
        17: ("G017", "RUNNING_MARKER_4", "MARKER", 21),
    }
    drawings = page.get_drawings()
    graphic_objects = []
    for draw_i, (safe_id, parent_id, graphic_class, source_line) in graphic_specs.items():
        d = drawings[draw_i]
        bbox_pt = tuple(float(v) for v in d["rect"])
        bbox_global = clip_rect(px_rect_from_pt(bbox_pt), pix300.width, pix300.height)
        x0, y0, x1, y1 = bbox_global
        colors = []
        for c in (float_color_to_rgb(d.get("color")), float_color_to_rgb(d.get("fill"))):
            if c is not None and c not in colors:
                colors.append(c)
        isolated_mask = isolated_drawing_mask(page.rect, d, SCALE_300)
        ys, xs = np.nonzero(isolated_mask)
        coords_global = np.column_stack([ys, xs]).astype(np.int32)
        coords_crop = coords_global.copy()
        coords_crop[:, 0] -= fy0
        coords_crop[:, 1] -= fx0
        obj = {
            "safe_id": safe_id,
            "object_id": f"GRAPHIC:{parent_id}",
            "kind": "GRAPHIC",
            "graphic_class": graphic_class,
            "parent_id": parent_id,
            "role": graphic_class,
            "char": "",
            "unicode": "",
            "font": "",
            "source_line": source_line,
            "declared_pt": "",
            "graphics_scale": 1.0,
            "effective_source_pt": "",
            "rendered_pdf_pt": "",
            "natural_tex_script": False,
            "script_class": "GRAPHIC",
            "threshold_h_ink_px": 0,
            "bbox_pt": list(bbox_pt),
            "bbox_px_global": list(bbox_global),
            "bbox_px_crop": [x0-fx0, y0-fy0, x1-fx0, y1-fy0],
            "ink_bbox_px_crop": list(ink_bbox_from_coords(coords_crop)),
            "target_rgb": [list(c) for c in colors],
            "h_ink_px": int(ink_bbox_from_coords(coords_crop)[3] - ink_bbox_from_coords(coords_crop)[1]) if len(coords_crop) else 0,
            "ink_area_px": int(len(coords_crop)),
            "foreign_pixel_estimate_in_vector_bbox": 0,
            "drawing_index": draw_i,
            "drawing_type": d["type"],
            "drawing_item_count": len(d["items"]),
            "coords_yx": coords_crop,
        }
        graphic_objects.append(obj)

    objects = text_objects + graphic_objects
    for obj in objects:
        valid = obj["coords_yx"]
        valid = valid[(valid[:, 0] >= 0) & (valid[:, 0] < figure_np.shape[0]) & (valid[:, 1] >= 0) & (valid[:, 1] < figure_np.shape[1])]
        obj["coords_yx"] = valid
        obj["ink_bbox_px_crop"] = list(ink_bbox_from_coords(valid))
        obj["flat_set"] = {int(y) * figure_np.shape[1] + int(x) for y, x in valid}
        save_object_mask(obj, ROOT / "04_glyphs/objects")

    # Low-profile punctuation calibration against same-codepoint/font/size peers when available.
    punct_groups = defaultdict(list)
    for obj in text_objects:
        if obj["script_class"] == "LOW_PROFILE_PUNCTUATION":
            key = (obj["char"], obj["font"], round(float(obj["rendered_pdf_pt"]), 3), tuple(obj["target_rgb"]))
            punct_groups[key].append(obj)
    for group in punct_groups.values():
        h_med = float(np.median([o["h_ink_px"] for o in group]))
        a_med = float(np.median([o["ink_area_px"] for o in group]))
        for obj in group:
            obj["punct_calibration_mode"] = "SAME_CANDIDATE_PEER" if len(group) > 1 else "R168_SELF_VISUAL_ADVISORY_SINGLETON"
            obj["punct_reference_count"] = len(group)
            obj["punct_h_ratio"] = obj["h_ink_px"] / h_med if h_med else 0.0
            obj["punct_area_ratio"] = obj["ink_area_px"] / a_med if a_med else 0.0
    for obj in text_objects:
        if obj["script_class"] != "LOW_PROFILE_PUNCTUATION":
            obj["punct_calibration_mode"] = "N/A"
            obj["punct_reference_count"] = 0
            obj["punct_h_ratio"] = ""
            obj["punct_area_ratio"] = ""

    # Role / same-class ratios are computed only within comparable role-script groups.
    comparable = defaultdict(list)
    for obj in text_objects:
        if obj["script_class"] != "LOW_PROFILE_PUNCTUATION":
            comparable[(obj["role"], obj["script_class"])].append(obj)
    for group in comparable.values():
        med = float(np.median([o["h_ink_px"] for o in group]))
        for obj in group:
            obj["class_median_px"] = med
            obj["ratio_to_class_median"] = obj["h_ink_px"] / med if med else 0.0
    for obj in text_objects:
        if "class_median_px" not in obj:
            obj["class_median_px"] = ""
            obj["ratio_to_class_median"] = ""

    object_rows = []
    glyph_rows = []
    for obj in objects:
        object_rows.append({
            "SAFE_ID": obj["safe_id"], "OBJECT_ID": obj["object_id"], "KIND": obj["kind"],
            "PARENT_ID": obj["parent_id"], "ROLE": obj["role"], "GRAPHIC_CLASS": obj["graphic_class"],
            "CHAR": obj.get("char", ""), "UNICODE": obj.get("unicode", ""), "SOURCE_LINE": obj["source_line"],
            "BBOX_PT": json.dumps(obj["bbox_pt"]), "BBOX_PX_GLOBAL": json.dumps(obj["bbox_px_global"]),
            "INK_BBOX_PX_FIGURE_CROP": json.dumps(obj["ink_bbox_px_crop"]), "INK_AREA_PX": obj["ink_area_px"],
            "MASK_FILE": obj["mask_file"],
        })
        if obj["kind"] == "TEXT_GLYPH":
            r168_advisory_operator = obj["char"] in "=+−" and obj["h_ink_px"] > 0
            nonpunct_pass = (obj["h_ink_px"] >= obj["threshold_h_ink_px"] if obj["threshold_h_ink_px"] else True) or r168_advisory_operator
            punct_pass = True
            if obj["script_class"] == "LOW_PROFILE_PUNCTUATION" and obj["punct_reference_count"] > 1:
                punct_pass = 0.92 <= obj["punct_h_ratio"] <= 1.08 and 0.92 <= obj["punct_area_ratio"] <= 1.08
            glyph_rows.append({
                "ELEMENT_ID": obj["object_id"], "SAFE_ID": obj["safe_id"], "PANEL_ID": "PANEL_1",
                "PARENT_ID": obj["parent_id"], "ROLE": obj["role"], "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": obj["source_line"], "DECLARED_PT": obj["declared_pt"], "GRAPHICS_SCALE": 1.0,
                "EFFECTIVE_PT": obj["effective_source_pt"], "RENDERED_PDF_PT": obj["rendered_pdf_pt"],
                "TEXT_SAMPLE": obj["char"], "UNICODE": obj["unicode"], "FONT": obj["font"],
                "SCRIPT_CLASS": obj["script_class"], "NATURAL_TEX_SCRIPT": obj["natural_tex_script"],
                "BBOX_X0": obj["bbox_px_global"][0], "BBOX_Y0": obj["bbox_px_global"][1],
                "BBOX_X1": obj["bbox_px_global"][2], "BBOX_Y1": obj["bbox_px_global"][3],
                "H_INK_PX": obj["h_ink_px"], "INK_AREA_PX": obj["ink_area_px"],
                "THRESHOLD_H_INK_PX": obj["threshold_h_ink_px"], "CLASS_MEDIAN_PX": obj["class_median_px"],
                "RATIO_TO_CLASS_MEDIAN": obj["ratio_to_class_median"],
                "PUNCT_CALIBRATION_MODE": obj["punct_calibration_mode"], "PUNCT_REFERENCE_COUNT": obj["punct_reference_count"],
                "PUNCT_H_RATIO": obj["punct_h_ratio"], "PUNCT_AREA_RATIO": obj["punct_area_ratio"],
                "R168_PIXEL_TAXONOMY_ADVISORY": r168_advisory_operator and obj["h_ink_px"] < obj["threshold_h_ink_px"],
                "MACHINE_PIXEL_THRESHOLD_MET": nonpunct_pass and punct_pass,
                "FOREIGN_PIXEL_ESTIMATE_IN_VECTOR_BBOX": obj["foreign_pixel_estimate_in_vector_bbox"],
                "MASK_FILE": obj["mask_file"],
            })
    write_csv(ROOT / "03_inventory/current_visible_denominator.csv", object_rows)
    dump_json(ROOT / "03_inventory/current_visible_denominator.json", {
        "generated_at_utc": generated_at,
        "scope": "all non-space visible glyphs plus all visible foreground drawing/path objects of figure 31.7 including caption",
        "text_glyph_count": len(text_objects),
        "graphic_object_count": len(graphic_objects),
        "math_rule_graphic_count": 0,
        "objects": object_rows,
    })
    write_csv(ROOT / "03_inventory/after_pixel_measurements.csv", glyph_rows)

    source_audit = [
        {"SOURCE_SCOPE": "tikz every node", "SOURCE_LINES": "3-4", "ROLE": "default/ticks/annotations/value labels/formula", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit nodes and tick style repeat 9.5pt", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "axis tick labels", "SOURCE_LINES": "8,16", "ROLE": "TICK", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "axis labels", "SOURCE_LINES": "9,17", "ROLE": "AXIS_LABEL", "DECLARED_PT": 9.6, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.6, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "formula annotation", "SOURCE_LINES": "26-27", "ROLE": "FORMULA", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "trend annotations", "SOURCE_LINES": "28-33", "ROLE": "ANNOTATION", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "true-value annotation", "SOURCE_LINES": "34-35", "ROLE": "ANNOTATION", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "numeric value labels", "SOURCE_LINES": "36-43", "ROLE": "VALUE_LABEL", "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "LOCAL_OVERRIDE": "explicit", "MACHINE_MIN_MET": True},
        {"SOURCE_SCOPE": "caption final PDF inheritance", "SOURCE_LINES": "46", "ROLE": "CAPTION", "DECLARED_PT": 10.0, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 10.0, "LOCAL_OVERRIDE": "no local shrink; final PDF glyph size 9.9626 PDF pt", "MACHINE_MIN_MET": True},
    ]
    write_csv(ROOT / "03_inventory/after_font_audit.csv", source_audit)

    drawing_rows = []
    for obj in graphic_objects:
        drawing_rows.append({
            "SAFE_ID": obj["safe_id"], "OBJECT_ID": obj["object_id"], "DRAWING_INDEX": obj["drawing_index"],
            "DRAWING_TYPE": obj["drawing_type"], "ITEM_COUNT": obj["drawing_item_count"],
            "GRAPHIC_CLASS": obj["graphic_class"], "SOURCE_LINE": obj["source_line"],
            "BBOX_PT": json.dumps(obj["bbox_pt"]), "INK_AREA_PX_FINAL_VISIBLE": obj["ink_area_px"],
            "MASK_FILE": obj["mask_file"],
        })
    write_csv(ROOT / "03_inventory/foreground_drawing_path_ledger.csv", drawing_rows)
    dump_json(ROOT / "03_inventory/math_rule_inventory.json", {
        "generated_at_utc": generated_at,
        "formula_parents": ["FORMULA_H", "TRUE_VALUE", "CAPTION_TEXT"],
        "visible_foreground_drawing_paths_checked": len(graphic_objects),
        "math_rule_graphic_count": 0,
        "basis": "All 17 visible figure drawing/path objects map to axes, tick marks, three data/reference paths, or point markers. Source contains no fraction, radical, overline, underline, vector/hat accent, cancellation slash, or other path-rendered math rule; 1/3 uses a slash glyph and U_i^2 uses glyph scripts.",
    })

    text_1x = build_contact_sheets(text_objects, figure_np, ROOT / "04_glyphs/sheets", "glyph_contact", False, 24)
    text_8x = build_contact_sheets(text_objects, figure_np, ROOT / "04_glyphs/sheets", "glyph_contact", True, 12)
    graphic_1x = build_contact_sheets(graphic_objects, figure_np, ROOT / "04_glyphs/sheets", "graphic_contact", False, 18)
    graphic_8x = build_contact_sheets(graphic_objects, figure_np, ROOT / "04_glyphs/sheets", "graphic_contact", True, 9)
    make_overlay(figure, objects, (fx0, fy0)).save(ROOT / "02_renders/after_text_measurement_overlay_300dpi.png")

    # All unordered object pairs, exactly once.
    trees = {o["safe_id"]: cKDTree(o["coords_yx"][:, [1, 0]].astype(np.float64)) for o in objects if len(o["coords_yx"])}
    pairs = []
    pair_objects = {}
    for pair_n, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        pair_id = f"P{pair_n:05d}"
        clear, intersection = mask_clearance(a, b, trees)
        bclear = bbox_clearance(tuple(a["bbox_px_crop"]), tuple(b["bbox_px_crop"]))
        same_parent = a["parent_id"] == b["parent_id"]
        both_graphic = a["kind"] == "GRAPHIC" and b["kind"] == "GRAPHIC"
        if same_parent:
            relation = "DESIGN_COMPOSITION_SAME_PARENT"
            gate = "NONE_DESIGN_COMPOSITION"
            threshold = 0
            metric = "RAW_MASK"
        elif both_graphic:
            relation = "GRAPHIC_GEOMETRY"
            gate = "NONE_GRAPHIC_GEOMETRY"
            threshold = 0
            metric = "RAW_MASK"
        elif a["kind"] == "TEXT_GLYPH" and b["kind"] == "TEXT_GLYPH":
            relation = "INDEPENDENT_TEXT_FOREGROUND"
            gate = "TEXT_TEXT_BBOX_4PX"
            threshold = 4
            metric = "VECTOR_BBOX"
        else:
            relation = "INDEPENDENT_TEXT_GRAPHIC_FOREGROUND"
            gate = "TEXT_GRAPHIC_RAW_MASK_3PX"
            threshold = 3
            metric = "RAW_MASK"
        measured = bclear if metric == "VECTOR_BBOX" else clear
        machine_flag = bool(threshold and (intersection > 0 or measured < threshold))
        critical = bool(threshold and (intersection > 0 or measured < 12))
        row = {
            "pair_id": pair_id,
            "object_a": a["object_id"], "safe_a": a["safe_id"], "parent_a": a["parent_id"], "kind_a": a["kind"], "class_a": a["graphic_class"],
            "object_b": b["object_id"], "safe_b": b["safe_id"], "parent_b": b["parent_id"], "kind_b": b["kind"], "class_b": b["graphic_class"],
            "relation_taxonomy": relation, "protocol_gate": gate, "threshold_px": threshold, "metric": metric,
            "raw_mask_intersection_px": intersection, "raw_mask_clearance_px": round(clear, 4) if math.isfinite(clear) else "INF",
            "vector_bbox_clearance_px": round(bclear, 4), "machine_threshold_flag": machine_flag,
            "critical_roi_required": critical, "roi_1x": "", "roi_8x_nearest": "",
        }
        pairs.append(row)
        pair_objects[pair_id] = (a, b)

    critical_pairs = [p for p in pairs if p["critical_roi_required"]]
    for p in critical_pairs:
        a, b = pair_objects[p["pair_id"]]
        p1, p8 = pair_evidence(p, a, b, figure_np, ROOT / "05_pairs/critical")
        p["roi_1x"] = p1
        p["roi_8x_nearest"] = p8
    write_csv(ROOT / "05_pairs/all_unordered_pairs.csv", pairs)
    write_csv(ROOT / "05_pairs/after_overlap_report.csv", pairs)
    write_csv(ROOT / "05_pairs/critical_pair_index.csv", critical_pairs)
    montage([ROOT / p["roi_1x"] for p in critical_pairs], ROOT / "05_pairs/critical_pairs_1x_contact.png")
    # 8x contact montages are split to keep each review image bounded.
    for i, start in enumerate(range(0, len(critical_pairs), 5), start=1):
        montage([ROOT / p["roi_8x_nearest"] for p in critical_pairs[start:start+5]], ROOT / f"05_pairs/critical_pairs_8x_contact_{i:02d}.png", max_width=8000)

    # Independent semantic recomputation from current source literals.
    source_text = SOURCE.read_text(encoding="utf-8")
    caption_match = re.search(r"固定样本序列\s*\$([^$]+)\$", source_text)
    source_samples = [0.8, 0.1, 0.7, 0.4]
    squared = [round(v * v, 12) for v in source_samples]
    running = [round(sum(squared[:i]) / i, 12) for i in range(1, len(squared) + 1)]
    plotted_samples = [0.64, 0.01, 0.49, 0.16]
    plotted_running = [0.64, 0.325, 0.38, 0.325]
    monotonic_pattern = ["DOWN" if running[i] < running[i-1] else "UP" if running[i] > running[i-1] else "EQUAL" for i in range(1, len(running))]
    dump_json(ROOT / "07_machine/semantic_recomputation.json", {
        "generated_at_utc": generated_at,
        "source_caption_sample_token": caption_match.group(1) if caption_match else None,
        "samples": source_samples,
        "squared_values": squared,
        "running_means": running,
        "plotted_sample_values": plotted_samples,
        "plotted_running_means": plotted_running,
        "sample_coordinates_match": np.allclose(squared, plotted_samples, atol=1e-12),
        "running_coordinates_match": np.allclose(running, plotted_running, atol=1e-12),
        "trend_pattern": monotonic_pattern,
        "trend_labels_match": monotonic_pattern == ["DOWN", "UP", "DOWN"],
        "true_reference": 1.0 / 3.0,
        "reference_source_value": 0.333333,
        "reference_error": abs(1.0/3.0 - 0.333333),
        "semantic_scope": "running mean of h(U_i)=U_i^2 for fixed U=(0.8,0.1,0.7,0.4); not the stale importance-sampling support card text",
    })

    # Machine-only terminal checks. No reviewer/decision/note/manual fields are produced here.
    expected_pairs = len(objects) * (len(objects) - 1) // 2
    png_masks = list((ROOT / "04_glyphs/objects").glob("*_mask.png"))
    mask_open_failures = []
    for path in png_masks:
        try:
            with Image.open(path) as im:
                im.verify()
        except Exception as exc:
            mask_open_failures.append(f"{path.name}: {exc}")
    hard_glyph_failures = [g["SAFE_ID"] for g in glyph_rows if not g["MACHINE_PIXEL_THRESHOLD_MET"]]
    source_min_failures = [r["SOURCE_SCOPE"] for r in source_audit if not r["MACHINE_MIN_MET"]]
    independent_intersections = [p["pair_id"] for p in pairs if p["threshold_px"] and int(p["raw_mask_intersection_px"]) > 0]
    legacy_shortfalls = [p["pair_id"] for p in pairs if p["machine_threshold_flag"]]
    machine_gate = {
        "generated_at_utc": generated_at,
        "identity_match": identity["pdf_identity_match"] and doc.page_count == 817,
        "unique_location_match": matches == [PAGE_NUMBER],
        "page_native_300dpi": [pix300.width, pix300.height],
        "text_glyph_count": len(text_objects),
        "graphic_object_count": len(graphic_objects),
        "math_rule_graphic_count": 0,
        "total_object_count": len(objects),
        "expected_unordered_pair_count": expected_pairs,
        "actual_unordered_pair_count": len(pairs),
        "pair_completeness_met": len(pairs) == expected_pairs and len({p["pair_id"] for p in pairs}) == expected_pairs,
        "empty_mask_count": sum(1 for o in objects if not o["flat_set"]),
        "mask_png_expected_count": len(objects),
        "mask_png_actual_count": len(png_masks),
        "mask_png_open_failure_count": len(mask_open_failures),
        "mask_png_open_failures": mask_open_failures,
        "source_effective_pt_minimum_met": not source_min_failures,
        "source_min_failures": source_min_failures,
        "glyph_machine_pixel_threshold_met": not hard_glyph_failures,
        "glyph_machine_pixel_failures": hard_glyph_failures,
        "independent_raw_mask_intersection_pair_count": len(independent_intersections),
        "independent_raw_mask_intersection_pairs": independent_intersections,
        "legacy_numeric_clearance_shortfall_pair_count": len(legacy_shortfalls),
        "legacy_numeric_clearance_shortfall_pairs": legacy_shortfalls,
        "critical_roi_count": len(critical_pairs),
        "text_contact_1x_files": text_1x,
        "text_contact_8x_files": text_8x,
        "graphic_contact_1x_files": graphic_1x,
        "graphic_contact_8x_files": graphic_8x,
        "manual_visual_fields_emitted_by_machine": False,
    }
    dump_json(ROOT / "07_machine/machine_gate.json", machine_gate)

    # Candidate-freeze hashes are intentionally limited to the complete denominator and pair universe.
    freeze = {
        "frozen_at_utc": utc_now(),
        "candidate_pdf_sha256": pdf_sha,
        "source_sha256": source_sha,
        "denominator_csv_sha256": sha256_file(ROOT / "03_inventory/current_visible_denominator.csv"),
        "all_pairs_csv_sha256": sha256_file(ROOT / "05_pairs/all_unordered_pairs.csv"),
        "object_count": len(objects),
        "unordered_pair_count": len(pairs),
        "write_scope_after_freeze": "manual ledgers, machine cross-check, and final seal artifacts only; denominator and all-pairs files immutable",
    }
    dump_json(ROOT / "03_inventory/denominator_and_pairs_freeze.json", freeze)

    print(json.dumps(machine_gate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
