from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_balance_flux.tex")
ROOT = Path(__file__).resolve().parents[1]
PAGE_INDEX = 650
PHYSICAL_PAGE = 651
PRINTED_PAGE = 638
UID = "FIG-P600-01"
HANDOFF_ID = "C-FIG-P600-01-R104-SA3-FRESH-ISOLATED-V1"
SCALE = 300.0 / 72.0
FIGURE_CROP = (240, 1870, 2210, 2760)
STANDALONE_CROP = (500, 1875, 1935, 2625)


TEXT_SPECS = [
    ("T01", "STATE_X_LABEL", 20, 0, "P_STATE_X"),
    ("T02", "STATE_Y_LABEL", 20, 1, "P_STATE_Y"),
    ("T03", "PROPOSAL_A_FORMULA", 21, 0, "P_PROPOSAL_A"),
    ("T04", "PROPOSAL_B_FORMULA", 21, 1, "P_PROPOSAL_B"),
    ("T05", "MIN_FORMULA", 22, 0, "P_MIN"),
    ("T06", "TOP_ANNOTATION", 23, 0, "P_ANNOTATION"),
    ("T07", "ACCEPTED_FLOW_XY_FORMULA", 24, 0, "P_FLOW_EQUATIONS"),
    ("T08", "ACCEPTED_FLOW_YX_FORMULA", 24, 1, "P_FLOW_EQUATIONS"),
    ("T09", "CONCLUSION_LINE_1", 25, 0, "P_CONCLUSION"),
    ("T10", "CONCLUSION_LINE_2", 26, 0, "P_CONCLUSION"),
    ("T11", "CAPTION_LABEL", 27, 0, "P_CAPTION_LABEL"),
    ("T12", "CAPTION_LINE_1", 27, 1, "P_CAPTION"),
    ("T13", "CAPTION_LINE_2", 27, 2, "P_CAPTION"),
]


GRAPHIC_SPECS = [
    ("G01", "STATE_X_BORDER", [8], []),
    ("G02", "STATE_Y_BORDER", [9], []),
    ("G03", "PROPOSAL_A_BORDER", [10], []),
    ("G04", "PROPOSAL_B_BORDER", [11], []),
    ("G05", "MIN_BORDER", [12], []),
    ("G06", "EDGE_X_TO_A", [13, 14], [14]),
    ("G07", "EDGE_Y_TO_B", [15, 16], [16]),
    ("G08", "EDGE_A_TO_MIN", [17, 18], [18]),
    ("G09", "EDGE_B_TO_MIN", [19, 20], [20]),
    ("G10", "MAIN_LOOP_X_TO_Y", [4, 5], [5]),
    ("G11", "MAIN_LOOP_Y_TO_X", [6, 7], [7]),
    ("G12", "CONCLUSION_BORDER", [21], []),
]


INTENTIONAL_CONNECTIONS = {
    frozenset(("G01", "G06")), frozenset(("G03", "G06")),
    frozenset(("G02", "G07")), frozenset(("G04", "G07")),
    frozenset(("G03", "G08")), frozenset(("G05", "G08")),
    frozenset(("G04", "G09")), frozenset(("G05", "G09")),
    frozenset(("G01", "G10")), frozenset(("G02", "G10")),
    frozenset(("G01", "G11")), frozenset(("G02", "G11")),
}


NODE_INTERNAL = {
    frozenset(("T01", "G01")), frozenset(("T02", "G02")),
    frozenset(("T03", "G03")), frozenset(("T04", "G04")),
    frozenset(("T05", "G05")), frozenset(("T09", "G12")),
    frozenset(("T10", "G12")),
}


def ensure_dirs() -> None:
    for rel in [
        "renders", "machine", "masks/glyph", "masks/graphic", "masks/object",
        "cards/glyph", "cards/pair", "contacts/glyph", "contacts/pair", "critical_pairs",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def union_bbox(boxes):
    return (
        min(b[0] for b in boxes), min(b[1] for b in boxes),
        max(b[2] for b in boxes), max(b[3] for b in boxes),
    )


def px_bbox(pt_bbox, pad=0):
    return (
        max(0, math.floor(pt_bbox[0] * SCALE) - pad),
        max(0, math.floor(pt_bbox[1] * SCALE) - pad),
        min(2481, math.ceil(pt_bbox[2] * SCALE) + pad),
        min(3508, math.ceil(pt_bbox[3] * SCALE) + pad),
    )


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def render_page(page):
    p300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
    full = Image.frombytes("RGB", (p300.width, p300.height), p300.samples)
    full.save(ROOT / "renders/full_page_300dpi.png", dpi=(300, 300))
    p200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), colorspace=fitz.csRGB, alpha=False)
    Image.frombytes("RGB", (p200.width, p200.height), p200.samples).save(
        ROOT / "renders/full_page_200dpi.png", dpi=(200, 200)
    )
    fig = full.crop(FIGURE_CROP)
    fig.save(ROOT / "renders/figure_crop_300dpi.png", dpi=(300, 300))
    fig.convert("L").save(ROOT / "renders/grayscale_300dpi.png", dpi=(300, 300))
    full.crop(STANDALONE_CROP).save(ROOT / "renders/standalone_300dpi.png", dpi=(300, 300))
    return full


def iter_line_chars(raw, block_i, line_i):
    line = raw["blocks"][block_i]["lines"][line_i]
    for span_i, span in enumerate(line["spans"]):
        for char_i, char in enumerate(span["chars"]):
            yield span_i, char_i, span, char


def glyph_mask(full_np, bbox, expected_fg):
    x0, y0, x1, y1 = bbox
    crop = full_np[y0:y1, x0:x1].astype(np.float32)
    pixels = crop.reshape(-1, 3).astype(np.uint8)
    common = Counter(map(tuple, pixels.tolist())).most_common(1)[0][0]
    bg = np.array(common, dtype=np.float32)
    fg = np.array(expected_fg, dtype=np.float32)
    v = fg - bg
    denom = float(np.dot(v, v))
    contrast = np.max(np.abs(crop - bg), axis=2)
    if denom < 25:
        mask = contrast >= 20
    else:
        alpha = np.tensordot(crop - bg, v, axes=([2], [0])) / denom
        projection = bg + alpha[..., None] * v
        residual = np.linalg.norm(crop - projection, axis=2)
        mask = (contrast >= 20) & (alpha >= 0.06) & (alpha <= 1.35) & (residual <= 18)
    return mask, tuple(int(x) for x in bg)


def bbox_from_mask(mask, offset):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min() + offset[0]), int(ys.min() + offset[1]), int(xs.max() + 1 + offset[0]), int(ys.max() + 1 + offset[1]))


def save_local_mask(path, mask):
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def panel_fit(img, size, resample=Image.Resampling.NEAREST, bg=(255, 255, 255)):
    canvas = Image.new("RGB", size, bg)
    if img.width == 0 or img.height == 0:
        return canvas
    ratio = min(size[0] / img.width, size[1] / img.height)
    new = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), resample)
    canvas.paste(new, ((size[0] - new.width) // 2, (size[1] - new.height) // 2))
    return canvas


def font():
    candidates = [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arial.ttf"]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, 18)
    return ImageFont.load_default()


FONT = font()


def glyph_card(full, row, mask):
    x0, y0, x1, y1 = [int(row[k]) for k in ("bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1")]
    context_box = (max(0, x0 - 8), max(0, y0 - 8), min(full.width, x1 + 8), min(full.height, y1 + 8))
    ctx = full.crop(context_box)
    local = full.crop((x0, y0, x1, y1))
    ov = local.copy()
    ov_np = np.array(ov)
    ov_np[mask] = (255, 0, 0)
    ov = Image.fromarray(ov_np)
    mo = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    native = Image.new("RGB", (170, 205), "white")
    native.paste(ctx, (5, 30))
    draw = ImageDraw.Draw(native)
    draw.rectangle((4, 29, 5 + ctx.width, 30 + ctx.height), outline=(0, 0, 0))
    panels = [
        native,
        panel_fit(ctx.resize((ctx.width * 8, ctx.height * 8), Image.Resampling.NEAREST), (240, 205)),
        panel_fit(ov.resize((ov.width * 8, ov.height * 8), Image.Resampling.NEAREST), (240, 205)),
        panel_fit(mo.resize((mo.width * 8, mo.height * 8), Image.Resampling.NEAREST), (240, 205)),
    ]
    card = Image.new("RGB", (940, 260), "white")
    d = ImageDraw.Draw(card)
    labels = ["ORIGINAL 1x", "CONTEXT 8x", "TARGET OVERLAY 8x", "MASK ONLY 8x"]
    x = 0
    for lab, panel in zip(labels, panels):
        d.text((x + 4, 4), lab, fill="black", font=FONT)
        card.paste(panel, (x, 28))
        x += panel.width
    title = f"{row['glyph_id']} cell={row['cell']} U+{row['codepoint']} char={row['char']} h={row['h_ink_px']}px"
    d.rectangle((0, 232, 939, 259), fill=(245, 245, 245))
    d.text((4, 236), title, fill="black", font=FONT)
    return card


def draw_item(shape, item):
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
        raise RuntimeError(f"Unsupported drawing item: {op!r}")


def graphic_group_mask(page, drawings, indices, fill_indices, actual_nonwhite):
    tmp = fitz.open()
    p = tmp.new_page(width=page.rect.width, height=page.rect.height)
    for idx in indices:
        d = drawings[idx]
        shape = p.new_shape()
        for item in d["items"]:
            draw_item(shape, item)
        use_fill = idx in fill_indices
        width = d.get("width") or 0.1
        shape.finish(
            color=(0, 0, 0), fill=(0, 0, 0) if use_fill else None,
            width=width, closePath=d.get("closePath", False),
            lineCap=1, lineJoin=1, even_odd=d.get("even_odd", False),
        )
        shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    mask = (arr < 245) & actual_nonwhite
    tmp.close()
    return mask


def localize_full_mask(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0), np.zeros((0, 0), dtype=bool)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
    return bbox, mask[bbox[1]:bbox[3], bbox[0]:bbox[2]]


def paste_mask(canvas, bbox, mask):
    x0, y0, x1, y1 = bbox
    if x1 > x0 and y1 > y0:
        canvas[y0:y1, x0:x1] |= mask


def overlap_count(a, b):
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return 0
    am = a["mask"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bm = b["mask"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(am & bm))


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def object_coords(obj):
    ys, xs = np.where(obj["mask"])
    return np.column_stack((xs + obj["bbox"][0], ys + obj["bbox"][1]))


def nearest_metrics(a, b):
    ca, cb = a["coords"], b["coords"]
    if not len(ca) or not len(cb):
        return None, None, None
    if len(ca) <= len(cb):
        dist, idx = b["tree"].query(ca, k=1)
        j = int(np.argmin(dist))
        return float(dist[j]), (int(ca[j, 0]), int(ca[j, 1])), (int(cb[int(idx[j]), 0]), int(cb[int(idx[j]), 1]))
    dist, idx = a["tree"].query(cb, k=1)
    j = int(np.argmin(dist))
    return float(dist[j]), (int(ca[int(idx[j]), 0]), int(ca[int(idx[j]), 1])), (int(cb[j, 0]), int(cb[j, 1]))


def build_pair_card(full, a, b, row):
    fig = full.crop(FIGURE_CROP).copy()
    d = ImageDraw.Draw(fig)
    for obj, color in ((a, (255, 0, 0)), (b, (0, 70, 255))):
        bb = obj["bbox"]
        d.rectangle((bb[0] - FIGURE_CROP[0], bb[1] - FIGURE_CROP[1], bb[2] - FIGURE_CROP[0], bb[3] - FIGURE_CROP[1]), outline=color, width=3)
    overview = panel_fit(fig, (480, 205), Image.Resampling.LANCZOS)
    ux0 = max(0, min(a["bbox"][0], b["bbox"][0]) - 8)
    uy0 = max(0, min(a["bbox"][1], b["bbox"][1]) - 8)
    ux1 = min(full.width, max(a["bbox"][2], b["bbox"][2]) + 8)
    uy1 = min(full.height, max(a["bbox"][3], b["bbox"][3]) + 8)
    if ux1 - ux0 <= 260 and uy1 - uy0 <= 180:
        roi = full.crop((ux0, uy0, ux1, uy1))
        roi_np = np.array(roi)
        for obj, color in ((a, (255, 0, 0)), (b, (0, 70, 255))):
            x0, y0, x1, y1 = obj["bbox"]
            ix0, iy0, ix1, iy1 = max(x0, ux0), max(y0, uy0), min(x1, ux1), min(y1, uy1)
            if ix1 > ix0 and iy1 > iy0:
                local = obj["mask"][iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0]
                sub = roi_np[iy0 - uy0:iy1 - uy0, ix0 - ux0:ix1 - ux0]
                sub[local] = color
        roi = Image.fromarray(roi_np)
        detail = panel_fit(roi.resize((roi.width * 4, roi.height * 4), Image.Resampling.NEAREST), (480, 205))
    else:
        detail = overview.copy()
        ImageDraw.Draw(detail).text((5, 5), "REMOTE PAIR: overview repeated", fill="black", font=FONT)
    card = Image.new("RGB", (960, 250), "white")
    card.paste(overview, (0, 25))
    card.paste(detail, (480, 25))
    dd = ImageDraw.Draw(card)
    dd.text((5, 3), f"{row['pair_id']} overview", fill="black", font=FONT)
    dd.text((485, 3), f"detail clearance={row['clearance_px']} overlap={row['overlap_px']}", fill="black", font=FONT)
    dd.rectangle((0, 225, 959, 249), fill=(245, 245, 245))
    dd.text((4, 228), f"A={a['id']} {a['role']} | B={b['id']} {b['role']} | machine_relation={row['machine_relation']}", fill="black", font=FONT)
    return card


def build_contact_sheets(card_paths, out_dir, prefix, cols, rows):
    per = cols * rows
    outputs = []
    for si in range(0, len(card_paths), per):
        subset = card_paths[si:si + per]
        imgs = [Image.open(p).convert("RGB") for p in subset]
        w = max(i.width for i in imgs)
        h = max(i.height for i in imgs)
        sheet = Image.new("RGB", (w * cols, h * rows), (225, 225, 225))
        for j, img in enumerate(imgs):
            sheet.paste(img, ((j % cols) * w, (j // cols) * h))
        path = out_dir / f"{prefix}_{si // per + 1:03d}.png"
        sheet.save(path)
        outputs.append(path)
    return outputs


def main():
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    if len(doc) != 817 or tuple(round(x, 3) for x in page.rect) != (0.0, 0.0, 595.276, 841.89):
        raise RuntimeError("Official PDF identity/page geometry mismatch")
    if PDF.stat().st_size != 4_967_222 or sha256(PDF) != "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641":
        raise RuntimeError("Official PDF byte/hash mismatch")
    full = render_page(page)
    full_np = np.array(full)
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()

    glyph_rows = []
    whitespace_rows = []
    text_objects = []
    glyph_cards = []
    object_masks = {}
    glyph_sequence = 0
    for obj_id, role, bi, li, parent_id in TEXT_SPECS:
        chars = list(iter_line_chars(raw, bi, li))
        text = "".join(ch[3]["c"] for ch in chars)
        parent_boxes = []
        parent_mask_full = np.zeros((full.height, full.width), dtype=bool)
        visible_counter = 0
        for span_i, char_i, span, ch in chars:
            c = ch["c"]
            if c.isspace():
                whitespace_rows.append({
                    "object_id": obj_id, "block": bi, "line": li, "span": span_i,
                    "char_index": char_i, "codepoint": f"{ord(c):04X}", "reason": "WHITESPACE_NOT_VISIBLE_FOREGROUND",
                })
                continue
            visible_counter += 1
            glyph_sequence += 1
            cb = tuple(float(v) for v in ch["bbox"])
            # Raw PDF glyph bbox only: padding admits adjacent anti-aliased ink and
            # would violate the one-glyph-per-mask purity requirement.
            bb = px_bbox(cb, pad=0)
            fg = rgb_from_int(int(span["color"]))
            mask, bg = glyph_mask(full_np, bb, fg)
            ink_bbox = bbox_from_mask(mask, (bb[0], bb[1]))
            ys, xs = np.where(mask)
            h_ink = int(ys.max() - ys.min() + 1) if len(ys) else 0
            w_ink = int(xs.max() - xs.min() + 1) if len(xs) else 0
            gid = f"GLY_{obj_id}_{visible_counter:03d}_U{ord(c):04X}"
            safe = gid + ".png"
            save_local_mask(ROOT / "masks/glyph" / safe, mask)
            row = {
                "glyph_id": gid, "safe_filename": safe, "parent_object_id": obj_id,
                "semantic_parent_id": parent_id, "sequence": glyph_sequence, "cell": visible_counter,
                "char": c, "codepoint": f"{ord(c):04X}", "unicode_name": unicodedata.name(c, "UNNAMED"),
                "block": bi, "line": li, "span": span_i, "char_index": char_i,
                "font": span["font"], "pdf_size_pt": round(float(span["size"]), 6),
                "expected_fg_rgb": ",".join(map(str, fg)), "local_bg_rgb": ",".join(map(str, bg)),
                "bbox_x0": bb[0], "bbox_y0": bb[1], "bbox_x1": bb[2], "bbox_y1": bb[3],
                "ink_bbox": ",".join(map(str, ink_bbox)) if ink_bbox else "",
                "mask_pixels": int(mask.sum()), "h_ink_px": h_ink, "w_ink_px": w_ink,
                "empty_mask": str(not bool(mask.any())).upper(),
                "mask_path": str((ROOT / "masks/glyph" / safe).resolve()),
            }
            glyph_rows.append(row)
            card = glyph_card(full, row, mask)
            card_path = ROOT / "cards/glyph" / f"{gid}.png"
            card.save(card_path)
            glyph_cards.append(card_path)
            parent_boxes.append(bb)
            parent_mask_full[bb[1]:bb[3], bb[0]:bb[2]] |= mask
        pb, pm = localize_full_mask(parent_mask_full)
        if not pm.any():
            raise RuntimeError(f"Empty text object mask: {obj_id}")
        save_local_mask(ROOT / "masks/object" / f"{obj_id}.png", pm)
        object_masks[obj_id] = {"id": obj_id, "role": role, "kind": "TEXT", "parent": parent_id, "bbox": pb, "mask": pm, "text": text}
        text_objects.append({
            "object_id": obj_id, "kind": "TEXT", "role": role, "semantic_parent_id": parent_id,
            "text": text, "bbox_x0": pb[0], "bbox_y0": pb[1], "bbox_x1": pb[2], "bbox_y1": pb[3],
            "visible_glyph_count": visible_counter, "mask_path": str((ROOT / "masks/object" / f"{obj_id}.png").resolve()),
            "source_mapping": f"rawdict block={bi},line={li}", "in_pair_denominator": "TRUE",
        })

    actual_nonwhite = np.max(255 - full_np, axis=2) >= 20
    graphic_rows = []
    for gid, role, draw_ids, fill_ids in GRAPHIC_SPECS:
        fm = graphic_group_mask(page, drawings, draw_ids, fill_ids, actual_nonwhite)
        bb, lm = localize_full_mask(fm)
        save_local_mask(ROOT / "masks/graphic" / f"{gid}.png", lm)
        object_masks[gid] = {"id": gid, "role": role, "kind": "GRAPHIC", "parent": gid, "bbox": bb, "mask": lm, "text": ""}
        graphic_rows.append({
            "object_id": gid, "kind": "GRAPHIC", "role": role,
            "drawing_indices": ";".join(map(str, draw_ids)), "fill_indices": ";".join(map(str, fill_ids)),
            "bbox_x0": bb[0], "bbox_y0": bb[1], "bbox_x1": bb[2], "bbox_y1": bb[3],
            "mask_pixels": int(lm.sum()), "empty_mask": str(not bool(lm.any())).upper(),
            "mask_path": str((ROOT / "masks/graphic" / f"{gid}.png").resolve()),
            "in_pair_denominator": "TRUE",
        })

    object_rows = text_objects + graphic_rows
    object_rows.sort(key=lambda r: r["object_id"])
    for obj in object_masks.values():
        obj["coords"] = object_coords(obj)
        obj["tree"] = cKDTree(obj["coords"]) if len(obj["coords"]) else None

    pair_rows = []
    pair_cards = []
    ids = sorted(object_masks)
    for i, aid in enumerate(ids):
        for bid in ids[i + 1:]:
            a, b = object_masks[aid], object_masks[bid]
            pair_id = f"PAIR_{aid}_{bid}"
            overlap = overlap_count(a, b)
            center_dist, pa, pb = nearest_metrics(a, b)
            clearance = None if center_dist is None else max(0.0, center_dist - 1.0)
            key = frozenset((aid, bid))
            if key in INTENTIONAL_CONNECTIONS:
                rel = "INTENTIONAL_EDGE_BORDER_CONNECTION"
            elif key in NODE_INTERNAL:
                rel = "NODE_TEXT_TO_FINAL_VISIBLE_BORDER"
            elif a["parent"] == b["parent"] and a["parent"] in {"P_FLOW_EQUATIONS", "P_CONCLUSION", "P_CAPTION"}:
                rel = "SAME_SEMANTIC_PARENT_NATURAL_LAYOUT"
            elif a["kind"] == "TEXT" and b["kind"] == "TEXT":
                rel = "INDEPENDENT_TEXT_TEXT"
            elif a["kind"] == "TEXT" or b["kind"] == "TEXT":
                rel = "TEXT_GRAPHIC"
            else:
                rel = "GRAPHIC_GRAPHIC"
            critical = overlap > 0 or (clearance is not None and clearance <= 25.0) or rel in {
                "INTENTIONAL_EDGE_BORDER_CONNECTION", "NODE_TEXT_TO_FINAL_VISIBLE_BORDER", "SAME_SEMANTIC_PARENT_NATURAL_LAYOUT"
            }
            row = {
                "pair_id": pair_id, "object_a": aid, "role_a": a["role"], "kind_a": a["kind"],
                "object_b": bid, "role_b": b["role"], "kind_b": b["kind"],
                "machine_relation": rel, "bbox_gap_px": round(bbox_gap(a["bbox"], b["bbox"]), 3),
                "min_center_distance_px": "" if center_dist is None else round(center_dist, 3),
                "clearance_px": "" if clearance is None else round(clearance, 3),
                "overlap_px": overlap, "nearest_a_x": "" if pa is None else pa[0], "nearest_a_y": "" if pa is None else pa[1],
                "nearest_b_x": "" if pb is None else pb[0], "nearest_b_y": "" if pb is None else pb[1],
                "critical": str(critical).upper(), "pair_card_path": str((ROOT / "cards/pair" / f"{pair_id}.png").resolve()),
            }
            card = build_pair_card(full, a, b, row)
            cpath = ROOT / "cards/pair" / f"{pair_id}.png"
            card.save(cpath)
            pair_cards.append(cpath)
            if critical:
                cdir = ROOT / "critical_pairs" / pair_id
                cdir.mkdir(parents=True, exist_ok=True)
                ux0 = max(0, min(a["bbox"][0], b["bbox"][0]) - 10)
                uy0 = max(0, min(a["bbox"][1], b["bbox"][1]) - 10)
                ux1 = min(full.width, max(a["bbox"][2], b["bbox"][2]) + 10)
                uy1 = min(full.height, max(a["bbox"][3], b["bbox"][3]) + 10)
                roi = full.crop((ux0, uy0, ux1, uy1))
                am = np.zeros((uy1 - uy0, ux1 - ux0), dtype=bool)
                bm = np.zeros_like(am)
                for obj, target in ((a, am), (b, bm)):
                    ox0, oy0, ox1, oy1 = obj["bbox"]
                    ix0, iy0, ix1, iy1 = max(ox0, ux0), max(oy0, uy0), min(ox1, ux1), min(oy1, uy1)
                    if ix1 > ix0 and iy1 > iy0:
                        target[iy0 - uy0:iy1 - uy0, ix0 - ux0:ix1 - ux0] = obj["mask"][iy0 - oy0:iy1 - oy0, ix0 - ox0:ix1 - ox0]
                inter = am & bm
                ov = np.array(roi)
                ov[am] = (255, 0, 0)
                ov[bm] = (0, 70, 255)
                ov[inter] = (255, 0, 255)
                roi.save(cdir / "raw_1x.png")
                save_local_mask(cdir / "mask_A_1x.png", am)
                save_local_mask(cdir / "mask_B_1x.png", bm)
                save_local_mask(cdir / "intersection_1x.png", inter)
                Image.fromarray(ov).save(cdir / "overlay_1x.png")
                Image.fromarray(ov).resize((ov.shape[1] * 8, ov.shape[0] * 8), Image.Resampling.NEAREST).save(cdir / "overlay_8x_nearest.png")
                save_json(cdir / "machine_metrics.json", {**row, "roi": [ux0, uy0, ux1, uy1]})
            pair_rows.append(row)

    glyph_sheets = build_contact_sheets(glyph_cards, ROOT / "contacts/glyph", "glyph_contact_sheet", 2, 5)
    pair_sheets = build_contact_sheets(pair_cards, ROOT / "contacts/pair", "pair_contact_sheet", 4, 5)

    # Object overlay on the official-pdf-derived crop.
    overlay = full.crop(FIGURE_CROP).copy()
    od = ImageDraw.Draw(overlay)
    colors = [(255, 0, 0), (0, 70, 255), (0, 145, 75), (180, 0, 180), (230, 120, 0)]
    for idx, oid in enumerate(ids):
        obj = object_masks[oid]
        bb = obj["bbox"]
        color = colors[idx % len(colors)]
        r = (bb[0] - FIGURE_CROP[0], bb[1] - FIGURE_CROP[1], bb[2] - FIGURE_CROP[0], bb[3] - FIGURE_CROP[1])
        od.rectangle(r, outline=color, width=2)
        od.text((r[0] + 2, r[1] + 2), oid, fill=color, font=FONT)
    overlay.save(ROOT / "renders/object_overlay_300dpi.png", dpi=(300, 300))

    drawing_map = []
    included = {idx: oid for oid, _, indices, _ in GRAPHIC_SPECS for idx in indices}
    for idx, d in enumerate(drawings):
        drawing_map.append({
            "drawing_index": idx, "mapped_object_id": included.get(idx, ""),
            "status": "INCLUDED" if idx in included else "EXCLUDED_OUTSIDE_FIGURE_SCOPE",
            "reason": "" if idx in included else "Page furniture/body box outside FIG-P600-01 figure+caption crop",
            "rect_pt": ",".join(str(round(v, 6)) for v in d["rect"]), "type": d["type"],
            "item_count": len(d["items"]),
        })

    source_text = SOURCE.read_text(encoding="utf-8")
    source_fonts = []
    for idx, m in enumerate(re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", source_text), start=1):
        source_fonts.append({
            "occurrence": idx, "declared_pt": float(m.group(1)), "leading_pt": float(m.group(2)),
            "graphics_scale": 1.0, "effective_pt": float(m.group(1)), "source_offset": m.start(),
            "source_excerpt": source_text[max(0, m.start()-50):min(len(source_text),m.end()+70)].replace("\n", " "),
        })

    save_csv(ROOT / "machine/machine_glyph_inventory.csv", glyph_rows)
    save_json(ROOT / "machine/machine_glyph_inventory.json", glyph_rows)
    save_csv(ROOT / "machine/machine_whitespace_exclusions.csv", whitespace_rows)
    save_csv(ROOT / "machine/machine_text_object_inventory.csv", text_objects)
    save_csv(ROOT / "machine/machine_graphic_inventory.csv", graphic_rows)
    save_csv(ROOT / "machine/machine_object_inventory.csv", object_rows)
    save_json(ROOT / "machine/machine_object_inventory.json", object_rows)
    save_csv(ROOT / "machine/machine_pair_inventory.csv", pair_rows)
    save_json(ROOT / "machine/machine_pair_inventory.json", pair_rows)
    save_csv(ROOT / "machine/machine_drawing_map.csv", drawing_map)
    save_csv(ROOT / "machine/machine_source_font_inventory.csv", source_fonts)
    save_json(ROOT / "machine/machine_render_inventory.json", {
        "uid": UID, "handoff_id": HANDOFF_ID, "pdf": str(PDF), "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF), "pdf_pages": len(doc), "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE, "figure_number": "32.4", "page_pt": list(page.rect),
        "native_300dpi": [full.width, full.height], "figure_crop_px": list(FIGURE_CROP),
        "standalone_crop_px": list(STANDALONE_CROP), "object_count": len(ids),
        "pair_count": len(pair_rows), "pair_expected_c_n_2": len(ids) * (len(ids) - 1) // 2,
        "glyph_count": len(glyph_rows), "whitespace_exclusion_count": len(whitespace_rows),
        "drawing_count_page": len(drawings), "drawing_included_count": len(included),
        "drawing_excluded_count": len(drawings) - len(included), "glyph_contact_sheet_count": len(glyph_sheets),
        "pair_contact_sheet_count": len(pair_sheets), "critical_pair_count": sum(r["critical"] == "TRUE" for r in pair_rows),
        "empty_glyph_masks": sum(r["empty_mask"] == "TRUE" for r in glyph_rows),
        "empty_graphic_masks": sum(r["empty_mask"] == "TRUE" for r in graphic_rows),
        "machine_only_no_manual_fields": True,
    })
    save_json(ROOT / "machine/machine_generation_summary.json", {
        "status": "MACHINE_GENERATION_COMPLETE", "manual_reviewer_fields_written": False,
        "manual_boolean_fields_written": False, "manual_decision_fields_written": False,
        "manual_note_fields_written": False,
    })
    print(json.dumps(json.loads((ROOT / "machine/machine_render_inventory.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
