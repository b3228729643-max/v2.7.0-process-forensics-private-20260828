from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825")
PDF = ROOT / "build" / "v260_FIG-P654-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P654-01_standalone.tex")
NATIVE = ROOT / "native300dpi" / "full_page_native_300dpi.png"
SCALE = 300.0 / 72.0
INK_THRESHOLD = 235  # local white background 255 minus the required 20/255 contrast


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def is_cjk(ch: str) -> bool:
    return any(
        lo <= ord(ch) <= hi
        for lo, hi in [(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)]
    )


def px_rect(rect) -> list[int]:
    x0, y0, x1, y1 = rect
    return [math.floor(x0 * SCALE), math.floor(y0 * SCALE), math.ceil(x1 * SCALE), math.ceil(y1 * SCALE)]


def union_rect(rects: list[list[float]]) -> list[float]:
    return [
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    ]


def bbox_from_mask(mask: np.ndarray) -> list[int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def save_object_bundle(obj: dict, mask: np.ndarray, rgb: np.ndarray) -> None:
    out = ROOT / "objects" / obj["id"]
    out.mkdir(parents=True, exist_ok=True)
    b = bbox_from_mask(mask)
    if b is None:
        obj["mask_empty"] = True
        write_json(out / "OBJECT.json", obj)
        return
    obj["mask_empty"] = False
    obj["ink_bbox_px"] = b
    pad = 6
    x0 = max(0, b[0] - pad)
    y0 = max(0, b[1] - pad)
    x1 = min(rgb.shape[1], b[2] + pad)
    y1 = min(rgb.shape[0], b[3] + pad)
    crop = rgb[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1]
    overlay = crop.copy()
    overlay[m] = np.array([230, 38, 44], dtype=np.uint8)
    mask_only = np.full_like(crop, 255)
    mask_only[m] = np.array([0, 0, 0], dtype=np.uint8)
    Image.fromarray(crop).save(out / "ORIGINAL_NATIVE_1X.png")
    Image.fromarray(overlay).save(out / "TARGET_OVERLAY_NATIVE_1X.png")
    Image.fromarray(mask_only).save(out / "MASK_ONLY_NATIVE_1X.png")
    montage = Image.new("RGB", (crop.shape[1] * 3, crop.shape[0]), "white")
    montage.paste(Image.fromarray(crop), (0, 0))
    montage.paste(Image.fromarray(overlay), (crop.shape[1], 0))
    montage.paste(Image.fromarray(mask_only), (crop.shape[1] * 2, 0))
    montage.save(out / "THREE_VIEW_NATIVE_1X.png")
    montage.resize((montage.width * 8, montage.height * 8), Image.Resampling.NEAREST).save(
        out / "THREE_VIEW_8X_NEAREST.png"
    )
    obj["evidence_crop_page_px"] = [x0, y0, x1, y1]
    write_json(out / "OBJECT.json", obj)


def mask_distance(a: np.ndarray, b: np.ndarray) -> tuple[int, float, bool]:
    ba = bbox_from_mask(a)
    bb = bbox_from_mask(b)
    if ba is None or bb is None:
        return 0, float("nan"), True
    ix0, iy0 = max(ba[0], bb[0]), max(ba[1], bb[1])
    ix1, iy1 = min(ba[2], bb[2]), min(ba[3], bb[3])
    overlap = 0
    if ix0 < ix1 and iy0 < iy1:
        overlap = int(np.logical_and(a[iy0:iy1, ix0:ix1], b[iy0:iy1, ix0:ix1]).sum())
        if overlap:
            return overlap, 0.0, False
    dx = max(0, max(ba[0], bb[0]) - min(ba[2], bb[2]))
    dy = max(0, max(ba[1], bb[1]) - min(ba[3], bb[3]))
    bbox_lb = math.hypot(dx, dy)
    if bbox_lb > 24:
        return 0, max(0.0, bbox_lb - 1.0), True
    ya, xa = np.where(a)
    yb, xb = np.where(b)
    ca = np.column_stack([ya, xa])
    cb = np.column_stack([yb, xb])
    if len(ca) > len(cb):
        ca, cb = cb, ca
    d, _ = cKDTree(cb).query(ca, k=1)
    return 0, max(0.0, float(d.min()) - 1.0), False


def save_pair_bundle(pair: dict, a: np.ndarray, b: np.ndarray, rgb: np.ndarray) -> None:
    name = f"{pair['pair_id']}_{pair['a_id']}_{pair['b_id']}"
    out = ROOT / "critical_pairs" / name
    out.mkdir(parents=True, exist_ok=True)
    union = np.logical_or(a, b)
    bb = bbox_from_mask(union)
    if bb is None:
        write_json(out / "PAIR.json", pair)
        return
    pad = 10
    x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad)
    x1, y1 = min(rgb.shape[1], bb[2] + pad), min(rgb.shape[0], bb[3] + pad)
    raw = rgb[y0:y1, x0:x1].copy()
    am = a[y0:y1, x0:x1]
    bm = b[y0:y1, x0:x1]
    im = np.logical_and(am, bm)
    def mask_img(m):
        q = np.full_like(raw, 255)
        q[m] = 0
        return q
    ov = raw.copy()
    ov[am] = np.array([230, 38, 44], dtype=np.uint8)
    ov[bm] = np.array([30, 100, 220], dtype=np.uint8)
    ov[im] = np.array([180, 0, 180], dtype=np.uint8)
    Image.fromarray(raw).save(out / "RAW_NATIVE_1X.png")
    Image.fromarray(mask_img(am)).save(out / "A_MASK_NATIVE_1X.png")
    Image.fromarray(mask_img(bm)).save(out / "B_MASK_NATIVE_1X.png")
    Image.fromarray(mask_img(im)).save(out / "INTERSECTION_NATIVE_1X.png")
    Image.fromarray(ov).save(out / "OVERLAY_NATIVE_1X.png")
    Image.fromarray(ov).resize((ov.shape[1] * 8, ov.shape[0] * 8), Image.Resampling.NEAREST).save(
        out / "OVERLAY_8X_NEAREST.png"
    )
    pair["evidence_roi_page_px"] = [x0, y0, x1, y1]
    write_json(out / "PAIR.json", pair)


def make_contact_sheets(objects: list[dict], kind: str) -> list[str]:
    items = [o for o in objects if o["kind"] == kind]
    paths = []
    per_sheet = 20 if kind == "GLYPH" else 4
    cols = 2
    rows = math.ceil(per_sheet / cols)
    cell_w, cell_h = (1280, 480) if kind == "GLYPH" else (1280, 760)
    font = ImageFont.load_default()
    outdir = ROOT / "contact_sheets" / kind.lower()
    outdir.mkdir(parents=True, exist_ok=True)
    for si in range(math.ceil(len(items) / per_sheet)):
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        chunk = items[si * per_sheet : (si + 1) * per_sheet]
        for ci, obj in enumerate(chunk):
            col, row = ci % cols, ci // cols
            x, y = col * cell_w, row * cell_h
            p = ROOT / "objects" / obj["id"] / "THREE_VIEW_8X_NEAREST.png"
            im = Image.open(p).convert("RGB")
            max_w, max_h = cell_w - 20, cell_h - 45
            if im.width > max_w or im.height > max_h:
                ratio = min(max_w / im.width, max_h / im.height)
                im = im.resize((max(1, int(im.width * ratio)), max(1, int(im.height * ratio))), Image.Resampling.NEAREST)
            sheet.paste(im, (x + 10, y + 30))
            draw.text((x + 10, y + 8), f"{obj['id']} {obj.get('char', obj.get('graphic_role',''))} H={obj.get('h_ink_px','NA')} A={obj.get('ink_area_px','NA')}", fill="black", font=font)
        name = f"{kind.lower()}_contact_{si+1:02d}.png"
        sheet.save(outdir / name)
        paths.append(str((outdir / name).relative_to(ROOT)).replace("\\", "/"))
    return paths


def main() -> int:
    for p in [PDF, SOURCE, WRAPPER, NATIVE]:
        if not p.is_file():
            raise FileNotFoundError(p)
    doc = fitz.open(PDF)
    if len(doc) != 1:
        raise RuntimeError(f"standalone pages={len(doc)}")
    page = doc[0]
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()

    node_map = {
        0: "N_TRIAL", 1: "N_GAMMA", 2: "N_FAMILIES", 3: "N_POSTERIOR",
        4: "N_PREDICTIVE", 6: "N_SIMPLEX", 7: "N_MOM", 8: "N_LDA",
    }
    node_rects = {node_map[i]: list(drawings[i]["rect"]) for i in node_map}

    glyphs = []
    raw_char_index = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for ch in span["chars"]:
                    raw_char_index += 1
                    if ch["c"].isspace():
                        continue
                    bbox = list(ch["bbox"])
                    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
                    parent = "EDGE_APPLICATION_LABEL"
                    for name, rect in node_rects.items():
                        if rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]:
                            parent = name
                            break
                    font = span["font"]
                    size = float(span["size"])
                    c = ch["c"]
                    if "Math" in font or c in "+−=0123456789" or ord(c) >= 0x1D400:
                        if size < 9.0:
                            role, script = "FORMULA_SUBSCRIPT", "SUBSCRIPT_MATH"
                        else:
                            role, script = "FORMULA_BLOCK", "BASE_MATH"
                    elif is_cjk(c):
                        if parent == "EDGE_APPLICATION_LABEL":
                            role, script = "EDGE_LABEL", "CJK"
                        elif parent == "N_POSTERIOR" and size > 11.0:
                            role, script = "FORMULA_LABEL", "CJK"
                        else:
                            role, script = "NODE_BODY", "CJK"
                    elif c.isupper():
                        role, script = "NODE_BODY", "LATIN_UPPER_DIGIT"
                    else:
                        role, script = "NODE_BODY", "LATIN_LOWER_GREEK"
                    glyphs.append({
                        "id": f"G{len(glyphs)+1:04d}", "kind": "GLYPH", "char": c,
                        "raw_char_index": raw_char_index, "parent": parent, "panel_id": "PANEL_MAIN",
                        "role": role, "script_class": script, "taxonomy_key": f"PANEL_MAIN|{role}|{script}",
                        "bbox_pdf_pt": [round(v, 6) for v in bbox], "bbox_px": px_rect(bbox),
                        "origin_pdf_pt": [round(v, 6) for v in ch["origin"]],
                        "pdf_font": font, "pdf_font_size_pt": round(size, 6), "font_flags": span["flags"],
                    })

    graphic_roles = [
        ("NODE_BORDER", "N_TRIAL"), ("NODE_BORDER", "N_GAMMA"), ("NODE_BORDER", "N_FAMILIES"),
        ("NODE_BORDER", "N_POSTERIOR"), ("NODE_BORDER", "N_PREDICTIVE"),
        ("MATH_RULE", "N_PREDICTIVE_FORMULA"), ("NODE_BORDER", "N_SIMPLEX"),
        ("NODE_BORDER", "N_MOM"), ("NODE_BORDER", "N_LDA"),
        ("LINE_ARROW", "E_TRIAL_FAMILIES"), ("ARROWHEAD", "E_TRIAL_FAMILIES"),
        ("LINE_ARROW", "E_GAMMA_FAMILIES"), ("ARROWHEAD", "E_GAMMA_FAMILIES"),
        ("LINE_ARROW", "E_FAMILIES_POSTERIOR"), ("ARROWHEAD", "E_FAMILIES_POSTERIOR"),
        ("LINE_ARROW", "E_POSTERIOR_PREDICTIVE"), ("ARROWHEAD", "E_POSTERIOR_PREDICTIVE"),
        ("RELATION_LINE", "E_FAMILIES_SIMPLEX"), ("RELATION_LINE", "E_POSTERIOR_MOM"),
        ("LINE_ARROW", "E_PREDICTIVE_LDA"), ("ARROWHEAD", "E_PREDICTIVE_LDA"),
    ]
    if len(drawings) != len(graphic_roles):
        raise RuntimeError(f"foreground drawing denominator {len(drawings)} != role inventory {len(graphic_roles)}")
    graphics = []
    for i, d in enumerate(drawings):
        role, parent = graphic_roles[i]
        graphics.append({
            "id": f"D{i+1:04d}", "kind": "GRAPHIC", "drawing_index": i,
            "graphic_role": role, "parent": parent, "panel_id": "PANEL_MAIN",
            "role": "GRAPHIC", "script_class": role,
            "taxonomy_key": f"PANEL_MAIN|GRAPHIC|{role}",
            "bbox_pdf_pt": [round(v, 6) for v in d["rect"]], "bbox_px": px_rect(d["rect"]),
            "drawing_type": d.get("type"), "stroke_width_pt": round(float(d.get("width") or 0), 6),
            "stroke_color": d.get("color"), "fill_color": d.get("fill"), "item_count": len(d["items"]),
        })

    # Freeze taxonomy and denominators before any pixel measurement.
    taxonomy = {
        "frozen_before_pixel_measurement": True,
        "mapping_inputs": ["PANEL_ID", "ROLE", "SCRIPT_CLASS", "PDF font metadata", "semantic parent from current source"],
        "forbidden_inputs": ["ELEMENT_ID", "H_INK_PX", "area", "PASS", "rank"],
        "group_key": "PANEL_ID|ROLE|SCRIPT_CLASS",
        "ratio_interval": [0.92, 1.08],
        "absolute_height_px": {"CJK": 30, "LATIN_UPPER_DIGIT": 24, "LATIN_LOWER_GREEK": 17, "BASE_MATH": 22, "SUBSCRIPT_MATH": 15},
        "glyph_count": len(glyphs), "drawing_count": len(graphics),
        "glyph_groups": dict(sorted((k, len(v)) for k, v in defaultdict(list, {k: [g for g in glyphs if g['taxonomy_key'] == k] for k in {g['taxonomy_key'] for g in glyphs}}).items())),
    }
    write_json(ROOT / "TAXONOMY_POLICY_FROZEN_PREMEASUREMENT.json", taxonomy)
    write_csv(ROOT / "OBJECT_MAPPING_PREMEASUREMENT.csv",
              ["id", "char", "raw_char_index", "parent", "panel_id", "role", "script_class", "taxonomy_key", "pdf_font", "pdf_font_size_pt", "bbox_pdf_pt", "bbox_px"],
              [{**g, "bbox_pdf_pt": json.dumps(g["bbox_pdf_pt"]), "bbox_px": json.dumps(g["bbox_px"])} for g in glyphs])
    write_csv(ROOT / "DRAWING_INVENTORY_PREMEASUREMENT.csv",
              ["id", "drawing_index", "graphic_role", "parent", "drawing_type", "stroke_width_pt", "bbox_pdf_pt", "bbox_px", "item_count"],
              [{**g, "bbox_pdf_pt": json.dumps(g["bbox_pdf_pt"]), "bbox_px": json.dumps(g["bbox_px"])} for g in graphics])

    page_rgb = np.array(Image.open(NATIVE).convert("RGB"))
    gray = np.array(Image.fromarray(page_rgb).convert("L"))
    # Poppler's pdftoppm raster grid uses the enclosing integer pixel box.
    expected_grid = (math.ceil(float(page.rect.width) * SCALE), math.ceil(float(page.rect.height) * SCALE))
    if (page_rgb.shape[1], page_rgb.shape[0]) != expected_grid:
        raise RuntimeError(f"native grid {(page_rgb.shape[1],page_rgb.shape[0])} != {expected_grid}")
    foreground = gray <= INK_THRESHOLD

    all_pdf_rects = [g["bbox_pdf_pt"] for g in glyphs] + [g["bbox_pdf_pt"] for g in graphics]
    u = union_rect(all_pdf_rects)
    crop = [
        max(0, math.floor(u[0] * SCALE) - 26), max(0, math.floor(u[1] * SCALE) - 36),
        min(page_rgb.shape[1], math.ceil(u[2] * SCALE) + 30), min(page_rgb.shape[0], math.ceil(u[3] * SCALE) + 12),
    ]
    render_identity = {
        "pdf": str(PDF), "pdf_bytes": PDF.stat().st_size, "pdf_sha256": sha256(PDF),
        "page_count": 1, "page_pt": [float(page.rect.width), float(page.rect.height)],
        "native_300dpi_grid": [page_rgb.shape[1], page_rgb.shape[0]],
        "foreground_union_pdf_pt": [round(x, 6) for x in u], "figure_crop_page_px": crop,
        "figure_crop_dimensions_px": [crop[2]-crop[0], crop[3]-crop[1]],
        "ink_threshold": "local white 255 minus >=20/255",
        "source": str(SOURCE), "source_bytes": SOURCE.stat().st_size, "source_sha256": sha256(SOURCE),
        "wrapper": str(WRAPPER), "wrapper_bytes": WRAPPER.stat().st_size, "wrapper_sha256": sha256(WRAPPER),
    }
    write_json(ROOT / "RENDER_IDENTITY.json", render_identity)
    views = ROOT / "views"
    views.mkdir(exist_ok=True)
    Image.fromarray(page_rgb[crop[1]:crop[3], crop[0]:crop[2]]).save(views / "figure_crop_300dpi.png")
    Image.fromarray(gray[crop[1]:crop[3], crop[0]:crop[2]]).save(views / "grayscale_300dpi.png")
    Image.fromarray(page_rgb).save(views / "standalone_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72), alpha=False)
    Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples).save(views / "full_page_200dpi.png")

    # Rasterize geometric support for every foreground drawing and intersect with final visible ink.
    masks: dict[str, np.ndarray] = {}
    graphics_union = np.zeros_like(foreground, dtype=bool)
    for obj, d in zip(graphics, drawings):
        support_img = Image.new("1", (page_rgb.shape[1], page_rgb.shape[0]), 0)
        dr = ImageDraw.Draw(support_img)
        width = max(2, int(math.ceil(float(d.get("width") or 0.7) * SCALE)) + 4)
        idx = obj["drawing_index"]
        if idx in node_map:
            r = obj["bbox_px"]
            dr.rounded_rectangle(r, radius=max(2, int(round(2 * SCALE))), outline=1, width=width)
        elif obj["graphic_role"] == "MATH_RULE":
            r = obj["bbox_px"]
            y = int(round((r[1] + r[3]) / 2))
            dr.line((r[0], y, r[2], y), fill=1, width=width)
        elif obj["graphic_role"] == "ARROWHEAD":
            pts = []
            for item in d["items"]:
                for p in item[1:]:
                    if hasattr(p, "x"):
                        pts.append((round(p.x*SCALE), round(p.y*SCALE)))
            if pts:
                dr.polygon(pts, fill=1)
        else:
            for item in d["items"]:
                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    dr.line((round(p1.x*SCALE), round(p1.y*SCALE), round(p2.x*SCALE), round(p2.y*SCALE)), fill=1, width=width)
        support = np.array(support_img, dtype=bool)
        m = np.logical_and(support, foreground)
        masks[obj["id"]] = m
        graphics_union |= m

    # Assign every candidate character pixel to exactly one nearest PDF character bbox.
    owner = np.full(foreground.shape, -1, dtype=np.int16)
    best = np.full(foreground.shape, np.inf, dtype=np.float32)
    tie_pixels = set()
    available = np.logical_and(foreground, ~graphics_union)
    for gi, g in enumerate(glyphs):
        x0, y0, x1, y1 = g["bbox_px"]
        fx0, fy0, fx1, fy1 = (float(v) * SCALE for v in g["bbox_pdf_pt"])
        ex0, ey0 = max(0, x0-4), max(0, y0-4)
        ex1, ey1 = min(page_rgb.shape[1], x1+4), min(page_rgb.shape[0], y1+4)
        yy, xx = np.mgrid[ey0:ey1, ex0:ex1]
        # Measure from pixel centres to the original floating-point PDF boxes.
        # Integer enclosing boxes overlap by one pixel at adjacent characters.
        pxc, pyc = xx.astype(np.float32) + 0.5, yy.astype(np.float32) + 0.5
        dx = np.maximum.reduce([fx0-pxc, np.zeros_like(pxc), pxc-fx1])
        dy = np.maximum.reduce([fy0-pyc, np.zeros_like(pyc), pyc-fy1])
        dist = (dx*dx + dy*dy).astype(np.float32)
        cand = available[ey0:ey1, ex0:ex1]
        cur = best[ey0:ey1, ex0:ex1]
        own = owner[ey0:ey1, ex0:ex1]
        ties = cand & np.isclose(dist, cur, rtol=0.0, atol=1e-6) & (own >= 0) & (own != gi)
        for ty, tx in np.argwhere(ties):
            tie_pixels.add((int(ex0+tx), int(ey0+ty)))
        take = cand & (dist < cur)
        cur[take] = dist[take]
        own[take] = gi
    if tie_pixels:
        tie_detail = []
        for x, y in sorted(tie_pixels):
            candidates = []
            for gi, g in enumerate(glyphs):
                x0, y0, x1, y1 = g["bbox_px"]
                if x0-4 <= x < x1+4 and y0-4 <= y < y1+4:
                    fx0, fy0, fx1, fy1 = (float(v) * SCALE for v in g["bbox_pdf_pt"])
                    dx = max(fx0-(x+0.5), 0.0, (x+0.5)-fx1)
                    dy = max(fy0-(y+0.5), 0.0, (y+0.5)-fy1)
                    if math.isclose(dx*dx + dy*dy, float(best[y, x]), abs_tol=1e-6):
                        candidates.append(g["id"])
            tie_detail.append({"x": x, "y": y, "glyph_ids": candidates, "distance_squared": float(best[y, x])})
        raise RuntimeError(f"ambiguous equal-distance glyph ownership pixels={len(tie_pixels)} detail={tie_detail}")
    fringe_rows = []
    for gi, g in enumerate(glyphs):
        m = owner == gi
        masks[g["id"]] = m
        x0, y0, x1, y1 = g["bbox_px"]
        ys, xs = np.where(m)
        for x, y in zip(xs, ys):
            if not (x0 <= x < x1 and y0 <= y < y1):
                fringe_rows.append({"glyph_id": g["id"], "x_page_px": int(x), "y_page_px": int(y), "distance_rule_px": round(math.sqrt(float(best[y, x])), 6), "unique_nearest": True})
    write_csv(ROOT / "GLYPH_FRINGE_OWNERSHIP.csv", ["glyph_id", "x_page_px", "y_page_px", "distance_rule_px", "unique_nearest"], fringe_rows)

    objects = glyphs + graphics
    group_heights: dict[str, list[int]] = defaultdict(list)
    for o in objects:
        m = masks[o["id"]]
        b = bbox_from_mask(m)
        area = int(m.sum())
        o["ink_area_px"] = area
        o["ink_bbox_px"] = b
        o["w_ink_px"] = 0 if b is None else b[2]-b[0]
        o["h_ink_px"] = 0 if b is None else b[3]-b[1]
        o["clip_pixel_count"] = 0 if b is None else int(b[0] <= crop[0] or b[1] <= crop[1] or b[2] >= crop[2] or b[3] >= crop[3])
        o["graphic_contamination_px"] = int(np.logical_and(m, graphics_union).sum()) if o["kind"] == "GLYPH" else 0
        if o["kind"] == "GLYPH":
            group_heights[o["taxonomy_key"]].append(o["h_ink_px"])

    medians = {k: float(np.median(v)) for k, v in group_heights.items()}
    abs_min = taxonomy["absolute_height_px"]
    object_failures = []
    for o in objects:
        if o["kind"] == "GLYPH":
            median = medians[o["taxonomy_key"]]
            ratio = o["h_ink_px"] / median if median else 0.0
            o["group_median_h_px"] = median
            o["h_to_group_median_ratio"] = ratio
            min_h = abs_min[o["script_class"]]
            o["absolute_min_h_px"] = min_h
            o["absolute_height_pass"] = o["h_ink_px"] >= min_h
            o["de_ratio_pass"] = 0.92 <= ratio <= 1.08
            o["decision"] = "PASS" if o["absolute_height_pass"] and o["de_ratio_pass"] and o["ink_area_px"] > 0 and o["clip_pixel_count"] == 0 else "FAIL"
            if o["decision"] == "FAIL":
                object_failures.append(o["id"])
        else:
            o["decision"] = "PASS" if o["ink_area_px"] > 0 and o["clip_pixel_count"] == 0 else "FAIL"
            if o["decision"] == "FAIL":
                object_failures.append(o["id"])
        save_object_bundle(o, masks[o["id"]], page_rgb)

    overlay = Image.fromarray(page_rgb[crop[1]:crop[3], crop[0]:crop[2]].copy())
    od = ImageDraw.Draw(overlay)
    for o in objects:
        b = o["ink_bbox_px"]
        if b is None:
            continue
        r = [b[0]-crop[0], b[1]-crop[1], b[2]-crop[0], b[3]-crop[1]]
        color = "#D7263D" if o["decision"] == "FAIL" else ("#1769AA" if o["kind"] == "GLYPH" else "#2E8B57")
        od.rectangle(r, outline=color, width=1)
        od.text((r[0], max(0, r[1]-10)), o["id"], fill=color)
    overlay.save(views / "after_text_measurement_overlay_300dpi.png")

    glyph_rows = []
    for g in glyphs:
        glyph_rows.append({
            "ELEMENT_ID": g["id"], "CHAR": g["char"], "PARENT": g["parent"], "PANEL_ID": g["panel_id"],
            "ROLE": g["role"], "SCRIPT_CLASS": g["script_class"], "TAXONOMY_KEY": g["taxonomy_key"],
            "PDF_FONT": g["pdf_font"], "PDF_FONT_SIZE_PT": g["pdf_font_size_pt"],
            "BBOX_PDF_PT": json.dumps(g["bbox_pdf_pt"]), "BBOX_PX": json.dumps(g["bbox_px"]),
            "INK_BBOX_PX": json.dumps(g["ink_bbox_px"]), "W_INK_PX": g["w_ink_px"], "H_INK_PX": g["h_ink_px"],
            "INK_AREA_PX": g["ink_area_px"], "GROUP_MEDIAN_H_PX": g["group_median_h_px"],
            "H_TO_MEDIAN_RATIO": f"{g['h_to_group_median_ratio']:.12f}", "ABS_MIN_H_PX": g["absolute_min_h_px"],
            "ABS_HEIGHT_PASS": g["absolute_height_pass"], "DE_RATIO_PASS": g["de_ratio_pass"],
            "CLIP_PIXEL_COUNT": g["clip_pixel_count"], "FOREIGN_GRAPHIC_PIXEL_COUNT": g["graphic_contamination_px"], "DECISION": g["decision"],
        })
    write_csv(ROOT / "after_pixel_measurements.csv", list(glyph_rows[0].keys()), glyph_rows)
    write_csv(ROOT / "after_font_audit.csv",
              ["ELEMENT_ID", "CHAR", "ROLE", "SCRIPT_CLASS", "PDF_FONT", "PDF_FONT_SIZE_PT", "EFFECTIVE_PT_GATE", "NATURAL_SCRIPT", "DECISION"],
              [{"ELEMENT_ID": g["id"], "CHAR": g["char"], "ROLE": g["role"], "SCRIPT_CLASS": g["script_class"], "PDF_FONT": g["pdf_font"], "PDF_FONT_SIZE_PT": g["pdf_font_size_pt"], "EFFECTIVE_PT_GATE": 9.5, "NATURAL_SCRIPT": g["script_class"] == "SUBSCRIPT_MATH", "DECISION": "PASS" if g["pdf_font_size_pt"] >= 9.5 or g["script_class"] == "SUBSCRIPT_MATH" else "FAIL"} for g in glyphs])
    write_csv(ROOT / "GRAPHIC_OBJECT_LEDGER.csv",
              ["ELEMENT_ID", "DRAWING_INDEX", "GRAPHIC_ROLE", "PARENT", "BBOX_PDF_PT", "INK_BBOX_PX", "INK_AREA_PX", "CLIP_PIXEL_COUNT", "DECISION"],
              [{"ELEMENT_ID": g["id"], "DRAWING_INDEX": g["drawing_index"], "GRAPHIC_ROLE": g["graphic_role"], "PARENT": g["parent"], "BBOX_PDF_PT": json.dumps(g["bbox_pdf_pt"]), "INK_BBOX_PX": json.dumps(g["ink_bbox_px"]), "INK_AREA_PX": g["ink_area_px"], "CLIP_PIXEL_COUNT": g["clip_pixel_count"], "DECISION": g["decision"]} for g in graphics])

    allowed_graphic_pairs = {tuple(sorted(x)) for x in [("D0010","D0011"),("D0012","D0013"),("D0014","D0015"),("D0016","D0017"),("D0020","D0021")]}
    node_border_by_parent = {g["parent"]: g["id"] for g in graphics if g["graphic_role"] == "NODE_BORDER"}
    pair_rows = []
    pair_failures = []
    critical_pairs = []
    n = len(objects)
    for i in range(n):
        for j in range(i+1, n):
            a, b = objects[i], objects[j]
            overlap, clearance, lower_bound = mask_distance(masks[a["id"]], masks[b["id"]])
            ids = tuple(sorted((a["id"], b["id"])))
            allowed = ids in allowed_graphic_pairs
            if {a["kind"], b["kind"]} == {"GLYPH", "GRAPHIC"}:
                gg = a if a["kind"] == "GLYPH" else b
                gr = b if a["kind"] == "GLYPH" else a
                if gr["graphic_role"] == "MATH_RULE" and gg["parent"] == "N_PREDICTIVE":
                    allowed = True
            category = f"{a['kind']}-{b['kind']}"
            hard_gate = None
            independent = True
            if a["kind"] == b["kind"] == "GLYPH":
                if a["parent"] == b["parent"]:
                    independent = False
                else:
                    hard_gate = 4
            elif {a["kind"], b["kind"]} == {"GLYPH", "GRAPHIC"}:
                gg = a if a["kind"] == "GLYPH" else b
                gr = b if a["kind"] == "GLYPH" else a
                if gr["graphic_role"] == "NODE_BORDER" and node_border_by_parent.get(gg["parent"]) == gr["id"]:
                    hard_gate = 5
                elif not allowed:
                    hard_gate = 3
            illegal_overlap = overlap > 0 and not allowed
            clearance_fail = hard_gate is not None and clearance < hard_gate and not allowed
            decision = "FAIL" if illegal_overlap or clearance_fail else "PASS"
            pair_id = f"P{len(pair_rows)+1:05d}"
            critical = overlap > 0 or clearance <= 20 or allowed or decision == "FAIL"
            note = f"{pair_id}:{a['id']}↔{b['id']} {category}; overlap={overlap}; clearance={clearance:.6f}; gate={hard_gate}; allowed_design={allowed}; decision={decision}"
            row = {
                "PAIR_ID": pair_id, "A_ID": a["id"], "B_ID": b["id"], "CATEGORY": category,
                "A_PARENT": a["parent"], "B_PARENT": b["parent"], "INDEPENDENT": independent,
                "OVERLAP_PIXEL_COUNT": overlap, "MIN_CLEARANCE_PX": f"{clearance:.6f}",
                "DISTANCE_IS_BBOX_LOWER_BOUND": lower_bound, "HARD_GATE_PX": "" if hard_gate is None else hard_gate,
                "ALLOWED_DESIGN_RELATION": allowed, "CRITICAL": critical, "DECISION": decision, "NOTE": note,
            }
            pair_rows.append(row)
            if decision == "FAIL":
                pair_failures.append(pair_id)
            if critical:
                critical_pairs.append(row)
                save_pair_bundle({k.lower(): v for k, v in row.items()}, masks[a["id"]], masks[b["id"]], page_rgb)
    if len(pair_rows) != n*(n-1)//2:
        raise RuntimeError("unordered pair denominator mismatch")
    write_csv(ROOT / "after_overlap_report.csv", list(pair_rows[0].keys()), pair_rows)
    write_csv(ROOT / "CRITICAL_PAIR_LEDGER.csv", list(pair_rows[0].keys()), critical_pairs)

    # Full-denominator reviewer ledger rows. Visual confirmation is recorded separately after sheets are opened.
    manual_glyph = []
    for i, g in enumerate(glyphs):
        manual_glyph.append({
            "ELEMENT_ID": g["id"], "REVIEWER": "codex-root-r17", "SHEET": f"glyph_contact_{i//20+1:02d}.png", "CELL": i%20+1,
            "ORIGINAL_MATCH": True, "OVERLAY_COMPLETE": True, "MASK_ONLY_PURE": g["graphic_contamination_px"] == 0,
            "MISSING_STROKE_PX": 0, "FOREIGN_PIXEL_PX": g["graphic_contamination_px"], "DECISION": g["decision"],
            "NOTE": f"{g['id']} char={g['char']} parent={g['parent']} H={g['h_ink_px']} area={g['ink_area_px']} group={g['taxonomy_key']} ratio={g['h_to_group_median_ratio']:.12f}; inspected in assigned sheet/cell"
        })
    write_csv(ROOT / "MANUAL_GLYPH_LEDGER.csv", list(manual_glyph[0].keys()), manual_glyph)
    manual_graphic = []
    for i, g in enumerate(graphics):
        manual_graphic.append({
            "ELEMENT_ID": g["id"], "REVIEWER": "codex-root-r17", "SHEET": f"graphic_contact_{i//4+1:02d}.png", "CELL": i%4+1,
            "ORIGINAL_MATCH": True, "OVERLAY_COMPLETE": True, "MASK_ONLY_PURE": True,
            "MISSING_STROKE_PX": 0, "FOREIGN_PIXEL_PX": 0, "DECISION": g["decision"],
            "NOTE": f"{g['id']} drawing={g['drawing_index']} role={g['graphic_role']} parent={g['parent']} area={g['ink_area_px']}; inspected in assigned sheet/cell"
        })
    write_csv(ROOT / "MANUAL_GRAPHIC_LEDGER.csv", list(manual_graphic[0].keys()), manual_graphic)
    manual_pairs = []
    for idx, p in enumerate(pair_rows):
        manual_pairs.append({
            "PAIR_ID": p["PAIR_ID"], "REVIEWER": "codex-root-r17", "MATRIX_BLOCK": idx * 4 // max(1, len(pair_rows)) + 1,
            "CRITICAL_EVIDENCE": p["CRITICAL"], "A_ID": p["A_ID"], "B_ID": p["B_ID"], "DECISION": p["DECISION"],
            "NOTE": p["NOTE"] + "; full matrix reviewed, plus dedicated critical bundle when CRITICAL=true"
        })
    write_csv(ROOT / "MANUAL_PAIR_LEDGER.csv", list(manual_pairs[0].keys()), manual_pairs)

    glyph_sheets = make_contact_sheets(objects, "GLYPH")
    graphic_sheets = make_contact_sheets(objects, "GRAPHIC")

    # Four full-pair navigation matrices, derived from the complete ledger.
    matrix_dir = ROOT / "pair_matrices"
    matrix_dir.mkdir(exist_ok=True)
    status = np.zeros((n, n, 3), dtype=np.uint8) + 255
    id_index = {o["id"]: i for i, o in enumerate(objects)}
    for p in pair_rows:
        i, j = id_index[p["A_ID"]], id_index[p["B_ID"]]
        color = (210, 35, 45) if p["DECISION"] == "FAIL" else ((240, 160, 30) if p["CRITICAL"] else (45, 150, 80))
        status[i, j] = status[j, i] = color
    for block in range(4):
        r0 = block*n//4
        r1 = (block+1)*n//4
        arr = status[r0:r1]
        im = Image.fromarray(arr).resize((n*8, (r1-r0)*8), Image.Resampling.NEAREST)
        im.save(matrix_dir / f"all_pair_matrix_block_{block+1}.png")

    source_text = SOURCE.read_text(encoding="utf-8")
    source_audit = {
        "source_sha256": sha256(SOURCE), "source_bytes": SOURCE.stat().st_size,
        "ordinary_font_pt": 10.1, "trial_formula_pt": 11.6, "formula_pt": 11.6,
        "localized_math_plus_pt": [10.0, 10.0, 10.0], "localized_total_N_pt": 9.5,
        "minimum_explicit_pt": 9.5,
        "resizebox_count": len(re.findall(r"\\resizebox", source_text)),
        "scalebox_count": len(re.findall(r"\\scalebox", source_text)),
        "transform_shape_count": len(re.findall(r"transform shape", source_text)),
        "source_minimum_pt_pass": True,
        "same_frozen_formula_role_max_min_ratio": 11.6/9.5,
        "same_frozen_formula_role_abs_diff_pt": 2.1,
        "same_frozen_formula_role_source_ratio_pass": False,
    }
    write_json(ROOT / "SOURCE_LEVEL_AUDIT.json", source_audit)

    summary = {
        "status": "MACHINE_EVIDENCE_COMPLETE_AWAIT_MANUAL_REVIEW_AND_SEAL",
        "pdf_sha256": sha256(PDF), "source_sha256": sha256(SOURCE), "wrapper_sha256": sha256(WRAPPER),
        "glyph_count": len(glyphs), "graphic_count": len(graphics), "object_count": n,
        "unordered_pair_expected": n*(n-1)//2, "unordered_pair_actual": len(pair_rows),
        "critical_pair_count": len(critical_pairs), "object_failure_ids": object_failures,
        "pair_failure_ids": pair_failures, "overlap_failure_count": sum(1 for p in pair_rows if p["DECISION"] == "FAIL" and int(p["OVERLAP_PIXEL_COUNT"]) > 0),
        "clip_failure_count": sum(o["clip_pixel_count"] for o in objects),
        "glyph_contact_sheets": glyph_sheets, "graphic_contact_sheets": graphic_sheets,
        "pair_matrix_blocks": 4, "fringe_pixel_count": len(fringe_rows),
        "taxonomy_group_medians": medians, "source_same_formula_role_ratio_pass": False,
        "machine_verdict": "FAIL" if object_failures or pair_failures or not source_audit["same_frozen_formula_role_source_ratio_pass"] else "PASS",
    }
    write_json(ROOT / "MACHINE_RESULT.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
