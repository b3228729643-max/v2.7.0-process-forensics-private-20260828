from __future__ import annotations

import csv
import itertools
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa2_r110_r168_readonly_adjudication_v1")
PAGE_PATH = ROOT / "renders" / "full_page_300dpi.png"
MASK_DIR = ROOT / "masks"
CONTACT_DIR = ROOT / "contact_sheets"
TABLE_DIR = ROOT / "tables"
REL_DIR = ROOT / "critical_relations"

PAGE_W_PT = 595.276
PAGE_H_PT = 841.890
SCALE = 300.0 / 72.0


def top_bbox_to_px(box: tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        math.floor(x0 * SCALE) - pad,
        math.floor(y0 * SCALE) - pad,
        math.ceil(x1 * SCALE) + pad,
        math.ceil(y1 * SCALE) + pad,
    )


def bottom_bbox_to_top(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return x0, PAGE_H_PT - y1, x1, PAGE_H_PT - y0


@dataclass(frozen=True)
class Obj:
    object_id: str
    object_class: str
    role: str
    parent: str
    source_line: str
    bbox_pt_top: tuple[float, float, float, float]
    text: str = ""
    declared_pt: str = ""
    pdf_font_pt: str = ""
    fg: tuple[int, int, int] = (31, 35, 40)
    bg: tuple[int, int, int] = (255, 255, 255)
    vector_seq: int | None = None


TEXT_OBJECTS = [
    Obj("T01", "TEXT", "factor_label", "fa", "24", (154.674, 614.130043, 172.628175, 623.594553), "𝑝(𝛼)", "9.5", "9.46451", bg=(246, 247, 248)),
    Obj("T02", "TEXT", "variable_label", "alpha", "25", (207.655, 613.889043, 213.191738, 623.353553), "𝛼", "9.5", "9.46451", bg=(242, 246, 250)),
    Obj("T03", "TEXT", "active_factor_label", "ft", "26", (247.987, 614.130043, 278.869696, 623.594553), "𝑝(𝜃∣𝛼)", "9.5", "9.46451", bg=(242, 246, 250)),
    Obj("T04", "TEXT", "focus_variable_label", "theta", "27", (317.007, 615.015043, 321.871758, 624.479553), "𝜃", "9.5", "9.46451", fg=(255, 255, 255), bg=(31, 78, 121)),
    Obj("T05", "TEXT", "active_factor_label", "fzy", "28", (362.432, 614.130043, 401.406852, 623.594553), "𝑝(𝑧,𝑦∣𝜃)", "9.5", "9.46451", bg=(242, 246, 250)),
    Obj("T06", "TEXT", "variable_label", "z", "29", (441.902, 581.158043, 446.568003, 590.622553), "𝑧", "9.5", "9.46451", bg=(242, 246, 250)),
    Obj("T07", "TEXT", "variable_label", "y", "30", (441.798, 645.669043, 446.624900, 655.133553), "𝑦", "9.5", "9.46451", bg=(242, 246, 250)),
    Obj("T08", "TEXT", "blanket_annotation", "annotation_blanket", "40-41", (288.654, 558.475496, 412.545451, 568.291886), "虚线圈：Markov 毯变量 𝛼,𝑧,𝑦", "9.2", "9.16563", fg=(15, 118, 110)),
    Obj("T09", "FORMULA", "full_conditional", "formula", "42-44", (253.425, 681.170043, 385.682063, 690.634553), "𝜋(𝜃∣𝛼,𝑧,𝑦)∝𝑝(𝜃∣𝛼)𝑝(𝑧,𝑦∣𝜃)", "9.5", "9.46451"),
    Obj("T10", "TEXT", "cancel_annotation_line1", "annotation_cancel", "45-46", (145.291, 655.394392, 203.839020, 665.530882), "𝑝(𝛼)与𝜃无关", "9.5", "9.46451", fg=(77, 83, 88)),
    Obj("T11", "TEXT", "cancel_annotation_line2", "annotation_cancel", "45-46", (122.510, 666.752392, 226.619610, 676.888882), "置于毯变量标记外并消去", "9.5", "9.46451", fg=(77, 83, 88)),
    Obj("T12", "TEXT", "caption_label", "caption", "50", (76.138, 696.897338, 107.011093, 711.323240), "图33.8", "inherited", "9.96264"),
    Obj("T13", "TEXT", "caption_line1", "caption", "50", (116.974, 700.483888, 507.799468, 711.153875), "因子图中更新𝜃只需读取与𝜃相连的两个因子𝑝(𝜃∣𝛼)和𝑝(𝑧,𝑦∣𝜃)；Markov毯变量为", "inherited", "9.96264"),
    Obj("T14", "TEXT", "caption_line2", "caption", "50", (76.138, 713.873888, 304.006760, 724.543875), "𝛼,𝑧,𝑦，而与𝜃无关的因子𝑝(𝛼)可从满条件核中消去", "inherited", "9.96264"),
]


# One record per visible foreground PDF drawing/path. The seven B operators also
# have fills, inventoried separately as protocol-defined backgrounds.
GRAPHIC_SPECS = [
    ("G01", "NODE_BORDER", "factor_p_alpha_border", "fa", "13-14,24", 14, (150.687, 214.485, 176.612, 231.493), (184, 192, 200), 0.797, "rect"),
    ("G02", "NODE_BORDER", "alpha_border", "alpha", "10,25", 15, (193.414, 205.981, 227.430, 239.997), (47, 125, 109), 0.797, "ellipse"),
    ("G03", "NODE_BORDER", "factor_theta_alpha_border", "ft", "15-16,26", 16, (244.002, 213.068, 282.860, 232.910), (47, 125, 109), 0.797, "rect"),
    ("G04", "NODE_BORDER", "theta_focus_boundary", "theta", "11-12,27", 17, (301.133, 204.564, 337.983, 241.414), (31, 78, 121), 0.797, "ellipse"),
    ("G05", "NODE_BORDER", "factor_zy_theta_border", "fzy", "15-16,28", 18, (358.448, 213.068, 405.395, 232.910), (47, 125, 109), 0.797, "rect"),
    ("G06", "NODE_BORDER", "z_border", "z", "10,29", 19, (427.277, 238.722, 461.293, 272.738), (47, 125, 109), 0.797, "ellipse"),
    ("G07", "NODE_BORDER", "y_border", "y", "10,30", 20, (427.277, 173.240, 461.293, 207.256), (47, 125, 109), 0.797, "ellipse"),
    ("G08", "LINE", "edge_p_alpha_to_alpha", "factor_graph", "17,32", 21, (176.991, 222.989, 192.998, 222.989), (107, 114, 128), 0.6476, "segments"),
    ("G09", "LINE", "active_chain_alpha_ft_theta_fzy_z", "factor_graph", "18,33", 22, (227.816, 222.989, 428.889, 247.642), (31, 78, 121), 0.9465, "segments"),
    ("G10", "LINE", "active_branch_fzy_y", "factor_graph", "18,34", 23, (401.590, 198.336, 428.889, 212.668), (31, 78, 121), 0.9465, "segments"),
    ("G11", "BLANKET_BORDER", "alpha_dashed_outline", "alpha", "36-39", 24, (189.995, 202.591, 230.790, 243.387), (15, 118, 110), 0.6974, "rounded_dash"),
    ("G12", "BLANKET_BORDER", "z_dashed_outline", "z", "36-39", 25, (423.921, 235.341, 464.717, 276.137), (15, 118, 110), 0.6974, "rounded_dash"),
    ("G13", "BLANKET_BORDER", "y_dashed_outline", "y", "36-39", 26, (423.921, 169.841, 464.717, 210.637), (15, 118, 110), 0.6974, "rounded_dash"),
    ("G14", "LINE_ARROW", "cancel_arrow_shaft", "annotation_cancel", "47", 27, (165.060, 193.367, 171.445, 210.292), (77, 83, 88), 0.797, "segments"),
    ("G15", "ARROWHEAD", "cancel_arrowhead", "annotation_cancel", "47", 28, (164.057, 208.760, 166.751, 212.950), (77, 83, 88), 0.797, "polygon"),
]

GRAPHIC_OBJECTS = [
    Obj(gid, gclass, role, parent, source_line, bottom_bbox_to_top(bbox), vector_seq=seq, fg=color)
    for gid, gclass, role, parent, source_line, seq, bbox, color, width, geometry in GRAPHIC_SPECS
]
OBJECTS = TEXT_OBJECTS + GRAPHIC_OBJECTS

BACKGROUND_FILLS = [
    ("BG01", "fa_fill", 14, (246, 247, 248)),
    ("BG02", "alpha_fill", 15, (242, 246, 250)),
    ("BG03", "ft_fill", 16, (242, 246, 250)),
    ("BG04", "theta_fill", 17, (31, 78, 121)),
    ("BG05", "fzy_fill", 18, (242, 246, 250)),
    ("BG06", "z_fill", 19, (242, 246, 250)),
    ("BG07", "y_fill", 20, (242, 246, 250)),
]

SEGMENTS_PT = {
    "G08": [((176.991, 222.989), (192.998, 222.989))],
    "G09": [
        ((227.816, 222.989), (243.593, 222.989)),
        ((283.254, 222.989), (300.732, 222.989)),
        ((338.384, 222.989), (358.054, 222.989)),
        ((401.590, 233.310), (428.889, 247.642)),
    ],
    "G10": [((401.590, 212.668), (428.889, 198.336))],
    "G14": [((171.445, 193.367), (165.060, 210.292))],
}

ARROWHEAD_PT = [(164.057, 212.950), (164.154, 208.760), (164.989, 210.478), (166.751, 209.740)]

CRITICAL_PAIRS = [
    ("R01", "T01", "G01"), ("R02", "T02", "G02"), ("R03", "T03", "G03"),
    ("R04", "T04", "G04"), ("R05", "T05", "G05"), ("R06", "T06", "G06"),
    ("R07", "T07", "G07"), ("R08", "T08", "G12"), ("R09", "T10", "G14"),
    ("R10", "T10", "G15"), ("R11", "G15", "G01"), ("R12", "G08", "G01"),
    ("R13", "G08", "G02"), ("R14", "G09", "G02"), ("R15", "G09", "G03"),
    ("R16", "G09", "G04"), ("R17", "G09", "G05"), ("R18", "G09", "G06"),
    ("R19", "G10", "G05"), ("R20", "G10", "G07"), ("R21", "G11", "G02"),
    ("R22", "G12", "G06"), ("R23", "G13", "G07"), ("R24", "T11", "T09"),
    ("R25", "T09", "T12"), ("R26", "T09", "T13"), ("R27", "T12", "T13"),
    ("R28", "T13", "T14"), ("R29", "T10", "G01"), ("R30", "T11", "G14"),
    ("R31", "T08", "G09"), ("R32", "T09", "G13"),
    ("R33", "G08", "G11"), ("R34", "G09", "G11"), ("R35", "G09", "G12"),
    ("R36", "G10", "G13"), ("R37", "G14", "G15"),
]


def clip_box(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    return max(0, box[0]), max(0, box[1]), min(size[0], box[2]), min(size[1], box[3])


def color_text_mask(arr: np.ndarray, obj: Obj) -> np.ndarray:
    mask = np.zeros(arr.shape[:2], dtype=bool)
    x0, y0, x1, y1 = clip_box(top_bbox_to_px(obj.bbox_pt_top, 2), (arr.shape[1], arr.shape[0]))
    region = arr[y0:y1, x0:x1].astype(np.int16)
    fg = np.array(obj.fg, dtype=np.int16)
    bg = np.array(obj.bg, dtype=np.int16)
    d_fg = np.linalg.norm(region - fg, axis=2)
    d_bg = np.linalg.norm(region - bg, axis=2)
    contrast = np.max(np.abs(region - bg), axis=2)
    local = (d_fg <= d_bg) & (contrast >= 20)
    mask[y0:y1, x0:x1] = local
    return mask


def pdf_bottom_point_to_px(p: tuple[float, float]) -> tuple[int, int]:
    return round(p[0] * SCALE), round((PAGE_H_PT - p[1]) * SCALE)


def corridor_mask(size: tuple[int, int], segments, width_pt: float) -> np.ndarray:
    image = Image.new("1", size, 0)
    draw = ImageDraw.Draw(image)
    width = max(1, round(width_pt * SCALE) + 2)
    for a, b in segments:
        draw.line([pdf_bottom_point_to_px(a), pdf_bottom_point_to_px(b)], fill=1, width=width)
    return np.array(image, dtype=bool)


def graphic_mask(arr: np.ndarray, spec) -> np.ndarray:
    gid, gclass, role, parent, source_line, seq, bbox_bottom, color, width_pt, geometry = spec
    h, w = arr.shape[:2]
    analytic = Image.new("1", (w, h), 0)
    draw = ImageDraw.Draw(analytic)
    x0, yt0, x1, yt1 = top_bbox_to_px(bottom_bbox_to_top(bbox_bottom), 1)
    stroke_px = max(2, round(width_pt * SCALE) + 2)
    if geometry == "rect":
        draw.rectangle((x0, yt0, x1, yt1), outline=1, width=stroke_px)
    elif geometry == "ellipse":
        draw.ellipse((x0, yt0, x1, yt1), outline=1, width=stroke_px)
    elif geometry == "segments":
        return corridor_mask((w, h), SEGMENTS_PT[gid], width_pt)
    elif geometry == "polygon":
        draw.polygon([pdf_bottom_point_to_px(p) for p in ARROWHEAD_PT], fill=1)
    elif geometry == "rounded_dash":
        # Preserve the actual dash phase and antialiasing by color-selecting only
        # inside a narrow vector bbox corridor.
        draw.rounded_rectangle((x0, yt0, x1, yt1), radius=round(7 * SCALE), outline=1, width=stroke_px + 4)
    else:
        raise ValueError(geometry)
    geo = np.array(analytic, dtype=bool)
    target = np.array(color, dtype=np.int16)
    pixels = arr.astype(np.int16)
    d_target = np.linalg.norm(pixels - target, axis=2)
    d_white = np.linalg.norm(pixels - np.array((255, 255, 255), dtype=np.int16), axis=2)
    color_like = d_target <= d_white
    if geometry == "ellipse" and gid == "G04":
        # The focus border and fill share a color; keep the geometric boundary.
        return geo
    return geo & color_like


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def save_overlay(page: Image.Image, mask: np.ndarray, path: Path, color=(255, 0, 0), alpha=150) -> None:
    overlay = page.convert("RGBA")
    tint = Image.new("RGBA", page.size, color + (0,))
    tint.putalpha(Image.fromarray(np.where(mask, alpha, 0).astype(np.uint8), mode="L"))
    Image.alpha_composite(overlay, tint).convert("RGB").save(path)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_intersection(a, b) -> int:
    x0 = max(a[0], b[0]); y0 = max(a[1], b[1]); x1 = min(a[2], b[2]); y1 = min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def bbox_clearance(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def min_mask_distance(a: np.ndarray, b: np.ndarray) -> tuple[float | None, int | None]:
    overlap = int(np.count_nonzero(a & b))
    if overlap:
        return 0.0, 0
    ya, xa = np.nonzero(a); yb, xb = np.nonzero(b)
    if len(xa) == 0 or len(xb) == 0:
        return None, None
    pa = np.column_stack((xa, ya)).astype(np.int32)
    pb = np.column_stack((xb, yb)).astype(np.int32)
    if len(pa) > len(pb):
        pa, pb = pb, pa
    best2 = np.iinfo(np.int64).max
    for start in range(0, len(pa), 256):
        chunk = pa[start:start + 256]
        d = chunk[:, None, :] - pb[None, :, :]
        best2 = min(best2, int(np.min(np.sum(d.astype(np.int64) ** 2, axis=2))))
    dist = math.sqrt(best2)
    return dist, max(0, math.ceil(dist) - 1)


def safe_crop_union(mask_a, mask_b, pad=12):
    ba = mask_bbox(mask_a); bb = mask_bbox(mask_b)
    boxes = [x for x in (ba, bb) if x is not None]
    if not boxes:
        return (0, 0, 1, 1)
    return (
        max(0, min(x[0] for x in boxes) - pad),
        max(0, min(x[1] for x in boxes) - pad),
        min(mask_a.shape[1], max(x[2] for x in boxes) + pad),
        min(mask_a.shape[0], max(x[3] for x in boxes) + pad),
    )


def build_contact_parts(page: Image.Image, mask: np.ndarray, obj: Obj, index_rows: list[dict]) -> None:
    box = clip_box(top_bbox_to_px(obj.bbox_pt_top, 8), page.size)
    max_native_width = 480
    total = box[2] - box[0]
    parts = max(1, math.ceil(total / max_native_width))
    # Balance the strips so a few padding-only pixels never become a final part.
    part_width = math.ceil(total / parts)
    for part in range(parts):
        x0 = box[0] + part * part_width
        x1 = min(box[2], x0 + part_width)
        sub = (x0, box[1], x1, box[3])
        original = page.crop(sub).convert("RGB")
        local_mask = mask[sub[1]:sub[3], sub[0]:sub[2]]
        over = original.convert("RGBA")
        tint = Image.new("RGBA", original.size, (255, 0, 0, 0))
        tint.putalpha(Image.fromarray(np.where(local_mask, 170, 0).astype(np.uint8), mode="L"))
        over = Image.alpha_composite(over, tint).convert("RGB")
        only = Image.new("RGB", original.size, "white")
        only_arr = np.array(only)
        only_arr[local_mask] = (0, 0, 0)
        only = Image.fromarray(only_arr)
        gap = Image.new("RGB", (8, original.height), "white")
        contact = Image.new("RGB", (original.width * 3 + 16, original.height), "white")
        contact.paste(original, (0, 0)); contact.paste(gap, (original.width, 0))
        contact.paste(over, (original.width + 8, 0)); contact.paste(gap, (original.width * 2 + 8, 0))
        contact.paste(only, (original.width * 2 + 16, 0))
        contact8 = contact.resize((contact.width * 8, contact.height * 8), Image.Resampling.NEAREST)
        name = f"{obj.object_id}_part{part + 1:02d}_original_overlay_mask_8x.png"
        contact8.save(CONTACT_DIR / name)
        index_rows.append({
            "object_id": obj.object_id,
            "part": part + 1,
            "part_count": parts,
            "native_crop_x0": sub[0], "native_crop_y0": sub[1],
            "native_crop_x1": sub[2], "native_crop_y1": sub[3],
            "file": f"contact_sheets/{name}",
        })


def main() -> None:
    for d in (MASK_DIR, CONTACT_DIR, TABLE_DIR, REL_DIR):
        d.mkdir(parents=True, exist_ok=True)
    page = Image.open(PAGE_PATH).convert("RGB")
    arr = np.array(page)
    assert page.size == (2481, 3508), page.size
    assert len(OBJECTS) == 29
    assert len({o.object_id for o in OBJECTS}) == 29

    masks: dict[str, np.ndarray] = {}
    for obj in TEXT_OBJECTS:
        masks[obj.object_id] = color_text_mask(arr, obj)
    for spec in GRAPHIC_SPECS:
        masks[spec[0]] = graphic_mask(arr, spec)

    # Node-border masks must not absorb the text glyph masks they enclose.
    contained = {"G01": "T01", "G02": "T02", "G03": "T03", "G04": "T04", "G05": "T05", "G06": "T06", "G07": "T07"}
    for gid, tid in contained.items():
        masks[gid] &= ~masks[tid]

    # Save native masks and overlays.
    mask_rows = []
    for obj in OBJECTS:
        mask = masks[obj.object_id]
        raw_name = f"{obj.object_id}_raw_mask.png"
        overlay_name = f"{obj.object_id}_overlay.png"
        save_mask(mask, MASK_DIR / raw_name)
        save_overlay(page, mask, MASK_DIR / overlay_name)
        mb = mask_bbox(mask)
        mask_rows.append({
            "object_id": obj.object_id,
            "raw_mask": f"masks/{raw_name}",
            "overlay": f"masks/{overlay_name}",
            "mask_pixel_count": int(np.count_nonzero(mask)),
            "mask_bbox_px": "" if mb is None else ",".join(map(str, mb)),
        })

    with (TABLE_DIR / "mask_index.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(mask_rows[0]))
        writer.writeheader(); writer.writerows(mask_rows)

    # Foreground object denominator.
    rows = []
    for obj in OBJECTS:
        px = top_bbox_to_px(obj.bbox_pt_top)
        rows.append({
            "object_id": obj.object_id, "object_class": obj.object_class, "role": obj.role,
            "semantic_parent": obj.parent, "source_line": obj.source_line,
            "bbox_pt_top": ",".join(f"{v:.6f}" for v in obj.bbox_pt_top),
            "bbox_px_300dpi": ",".join(map(str, px)), "text": obj.text,
            "declared_pt": obj.declared_pt, "graphics_scale": "1.0",
            "effective_pt": obj.declared_pt, "pdf_font_pt": obj.pdf_font_pt,
            "vector_sequence": "" if obj.vector_seq is None else obj.vector_seq,
            "mask_pixel_count": int(np.count_nonzero(masks[obj.object_id])),
        })
    with (TABLE_DIR / "visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    with (TABLE_DIR / "background_fill_inventory.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.writer(fobj)
        writer.writerow(["background_id", "role", "pdf_vector_sequence", "rgb", "pair_denominator_exclusion_basis"])
        for bgid, role, seq, rgb in BACKGROUND_FILLS:
            writer.writerow([bgid, role, seq, ",".join(map(str, rgb)), "protocol: node fill is background, not independent foreground"])

    # Glyph/codepoint denominator (visible non-whitespace characters only).
    glyph_rows = []
    glyph_n = 0
    for obj in TEXT_OBJECTS:
        visible_seq = 0
        for source_index, ch in enumerate(obj.text, 1):
            if ch.isspace():
                continue
            visible_seq += 1; glyph_n += 1
            glyph_rows.append({
                "glyph_id": f"{obj.object_id}_C{visible_seq:03d}", "parent_object_id": obj.object_id,
                "parent_source_index": source_index, "visible_sequence": visible_seq, "char": ch,
                "codepoint": f"U+{ord(ch):04X}", "unicode_name": unicodedata.name(ch, "UNNAMED"),
                "source_line": obj.source_line, "parent_bbox_px": ",".join(map(str, top_bbox_to_px(obj.bbox_pt_top))),
            })
    with (TABLE_DIR / "glyph_codepoint_denominator.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(glyph_rows[0]))
        writer.writeheader(); writer.writerows(glyph_rows)

    # All C(N,2) unordered pairs, machine facts only.
    pair_rows = []
    for index, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
        ba = top_bbox_to_px(a.bbox_pt_top); bb = top_bbox_to_px(b.bbox_pt_top)
        pair_rows.append({
            "pair_id": f"P{index:03d}", "object_a": a.object_id, "object_b": b.object_id,
            "class_a": a.object_class, "class_b": b.object_class,
            "bbox_intersection_area_px": bbox_intersection(ba, bb),
            "bbox_clearance_px": f"{bbox_clearance(ba, bb):.3f}",
            "raw_mask_intersection_px": int(np.count_nonzero(masks[a.object_id] & masks[b.object_id])),
        })
    assert len(pair_rows) == 406
    with (TABLE_DIR / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(pair_rows[0]))
        writer.writeheader(); writer.writerows(pair_rows)

    # Overall measurement overlay.
    overlay = page.copy()
    draw = ImageDraw.Draw(overlay)
    for obj in OBJECTS:
        box = top_bbox_to_px(obj.bbox_pt_top)
        color = (210, 0, 0) if obj.object_class in {"TEXT", "FORMULA"} else (0, 80, 220)
        draw.rectangle(box, outline=color, width=2)
        draw.text((box[0] + 2, max(0, box[1] - 12)), obj.object_id, fill=color)
    overlay.crop((250, 2260, 2220, 3060)).save(ROOT / "renders" / "after_text_measurement_overlay_300dpi.png")

    # Text-parent contact evidence.
    stale_contact = CONTACT_DIR / "T14_part03_original_overlay_mask_8x.png"
    if stale_contact.exists():
        stale_contact.unlink()
    contact_rows = []
    for obj in TEXT_OBJECTS:
        build_contact_parts(page, masks[obj.object_id], obj, contact_rows)
    with (TABLE_DIR / "contact_sheet_index.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(contact_rows[0]))
        writer.writeheader(); writer.writerows(contact_rows)

    # Critical relation machine evidence and tight 1x / 8x-nearest ROIs.
    relation_rows = []
    object_map = {o.object_id: o for o in OBJECTS}
    for rid, aid, bid in CRITICAL_PAIRS:
        ma, mb = masks[aid], masks[bid]
        overlap = ma & mb
        distance, blank = min_mask_distance(ma, mb)
        crop_box = safe_crop_union(ma, mb, pad=12)
        raw = page.crop(crop_box).convert("RGB")
        local_a = ma[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
        local_b = mb[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
        local_o = overlap[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
        over = raw.convert("RGBA")
        ta = Image.new("RGBA", raw.size, (255, 0, 0, 0)); ta.putalpha(Image.fromarray(np.where(local_a, 150, 0).astype(np.uint8)))
        tb = Image.new("RGBA", raw.size, (0, 80, 255, 0)); tb.putalpha(Image.fromarray(np.where(local_b, 150, 0).astype(np.uint8)))
        over = Image.alpha_composite(Image.alpha_composite(over, ta), tb).convert("RGB")
        if np.any(local_o):
            tm = Image.new("RGBA", raw.size, (255, 0, 255, 0)); tm.putalpha(Image.fromarray(np.where(local_o, 255, 0).astype(np.uint8)))
            over = Image.alpha_composite(over.convert("RGBA"), tm).convert("RGB")
        raw_name = f"{rid}_{aid}_{bid}_1x.png"
        over_name = f"{rid}_{aid}_{bid}_overlay_1x.png"
        over8_name = f"{rid}_{aid}_{bid}_overlay_8x_nearest.png"
        raw.save(REL_DIR / raw_name); over.save(REL_DIR / over_name)
        over.resize((over.width * 8, over.height * 8), Image.Resampling.NEAREST).save(REL_DIR / over8_name)
        relation_rows.append({
            "relation_id": rid, "object_a": aid, "object_b": bid,
            "class_a": object_map[aid].object_class, "class_b": object_map[bid].object_class,
            "raw_mask_intersection_px": int(np.count_nonzero(overlap)),
            "mask_center_distance_px": "" if distance is None else f"{distance:.3f}",
            "blank_clearance_px": "" if blank is None else blank,
            "roi_x0": crop_box[0], "roi_y0": crop_box[1], "roi_x1": crop_box[2], "roi_y1": crop_box[3],
            "raw_1x": f"critical_relations/{raw_name}",
            "overlay_1x": f"critical_relations/{over_name}",
            "overlay_8x_nearest": f"critical_relations/{over8_name}",
        })
    with (TABLE_DIR / "critical_relation_machine.csv").open("w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=list(relation_rows[0]))
        writer.writeheader(); writer.writerows(relation_rows)

    counts = {
        "foreground_object_count": len(OBJECTS),
        "text_parent_object_count": len(TEXT_OBJECTS),
        "graphic_foreground_path_count": len(GRAPHIC_OBJECTS),
        "protocol_background_fill_count": len(BACKGROUND_FILLS),
        "unordered_pair_count": len(pair_rows),
        "glyph_codepoint_count_non_whitespace": glyph_n,
        "critical_relation_count": len(CRITICAL_PAIRS),
        "empty_mask_count": sum(not np.any(masks[o.object_id]) for o in OBJECTS),
        "all_pair_raw_mask_intersection_nonzero_count": sum(int(r["raw_mask_intersection_px"] > 0) for r in pair_rows),
    }
    (TABLE_DIR / "machine_counts.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
