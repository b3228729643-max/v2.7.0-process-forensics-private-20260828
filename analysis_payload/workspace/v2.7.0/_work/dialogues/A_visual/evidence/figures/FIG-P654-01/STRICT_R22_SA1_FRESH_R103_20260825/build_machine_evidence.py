from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
EXPECTED_SHA256 = "9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23"
EXPECTED_BYTES = 4_967_184
PAGE_INDEX = 703
PHYSICAL_PAGE = 704
SCALE300 = 300.0 / 72.0
SCALE200 = 200.0 / 72.0
# Integer coordinates in the direct full-page 300 dpi raster. No resizing occurs.
FIGURE_CROP = (292, 250, 2234, 900)
STANDALONE_CROP = (310, 273, 2218, 900)
FIGURE_PT = (70.0, 60.0, 536.0, 216.0)
THRESHOLD_CONTRAST = 20
HANDOFF_ID = "A-R103-P654-SA1-FRESH-20260825"


NODE_DRAWINGS = {
    "G001": ("NODE_BORDER", "trial", [3]),
    "G002": ("NODE_BORDER", "gamma", [6]),
    "G003": ("NODE_BORDER", "families", [9]),
    "G004": ("NODE_BORDER", "posterior", [12]),
    "G005": ("NODE_BORDER", "predictive", [15]),
    "G006": ("NODE_BORDER", "simplex", [20]),
    "G007": ("NODE_BORDER", "mom", [23]),
    "G008": ("NODE_BORDER", "lda", [26]),
}
REL_DRAWINGS = {
    "G009": ("RELATION", "R1_trial_to_families", [29, 30]),
    "G010": ("RELATION", "R2_gamma_to_families", [32, 33]),
    "G011": ("RELATION", "R3_families_to_posterior", [35, 36]),
    "G012": ("RELATION", "R4_posterior_to_predictive", [38, 39]),
    "G013": ("RELATION", "R5_families_to_simplex", [41]),
    "G014": ("RELATION", "R6_posterior_to_mom", [42]),
    "G015": ("RELATION", "R7_predictive_to_lda", [43, 44]),
}
RULE_DRAWINGS = {"G016": ("MATH_RULE", "predictive_fraction_rule", [18])}
GRAPHIC_DEFS = {**NODE_DRAWINGS, **REL_DRAWINGS, **RULE_DRAWINGS}
REL_ENDPOINTS = {
    "G009": {"trial", "families"},
    "G010": {"gamma", "families"},
    "G011": {"families", "posterior"},
    "G012": {"posterior", "predictive"},
    "G013": {"families", "simplex"},
    "G014": {"posterior", "mom"},
    "G015": {"predictive", "lda"},
}
NODE_RECTS_PT = {
    "trial": (77.312, 68.454, 164.654, 102.471),
    "gamma": (77.312, 133.652, 164.654, 167.668),
    "families": (175.647, 99.636, 271.493, 136.486),
    "posterior": (282.377, 92.549, 393.238, 143.573),
    "predictive": (401.434, 75.541, 529.303, 160.581),
    "simplex": (201.095, 161.148, 272.691, 195.164),
    "mom": (297.757, 161.148, 369.354, 195.164),
    "lda": (421.066, 179.007, 492.663, 213.023),
}
EXPECTED_PARENT_TEXT = {
    "trial": "类别计数𝑛",
    "gamma": "Gamma与贝塔规范因子",
    "families": "多项分布与狄利克雷先验",
    "posterior": "共轭狄利克雷后验参数𝛼+𝑛",
    "predictive": "后验预测概率新增观测取指定类别𝛼𝑖+𝑛𝑖𝛼0+N",
    "simplex": "单纯形几何",
    "mom": "均值与浓度及对数矩",
    "lda": "后续主题模型伪计数与平滑",
    "R7_label": "应用",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_dirs() -> None:
    for rel in (
        "renders",
        "masks/glyph",
        "masks/graphic",
        "objects/glyph",
        "objects/graphic",
        "contact_sheets/glyph",
        "contact_sheets/graphic",
        "contact_sheets/critical",
        "overlays",
        "tables",
    ):
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def pix_to_array(pix: fitz.Pixmap) -> np.ndarray:
    arr = np.frombuffer(pix.samples, dtype=np.uint8)
    return arr.reshape(pix.height, pix.width, pix.n)[..., :3].copy()


def pix_to_gray(pix: fitz.Pixmap) -> np.ndarray:
    arr = np.frombuffer(pix.samples, dtype=np.uint8)
    return arr.reshape(pix.height, pix.width, pix.n)[..., 0].copy()


def save_rgb(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr.astype(np.uint8), "RGB").save(path)


def save_gray(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr.astype(np.uint8), "L").save(path)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def page_bbox_to_crop_px(bbox: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, math.floor(x0 * SCALE300) - FIGURE_CROP[0]),
        max(0, math.floor(y0 * SCALE300) - FIGURE_CROP[1]),
        min(FIGURE_CROP[2] - FIGURE_CROP[0], math.ceil(x1 * SCALE300) - FIGURE_CROP[0]),
        min(FIGURE_CROP[3] - FIGURE_CROP[1], math.ceil(y1 * SCALE300) - FIGURE_CROP[1]),
    )


def render_graphic_mask(page_rect: fitz.Rect, drawings_by_seq: dict[int, dict], seqnos: list[int], border_only: bool) -> np.ndarray:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for seq in seqnos:
        d = drawings_by_seq[seq]
        for item in d["items"]:
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
                raise RuntimeError(f"unsupported drawing operator {op!r} in seq {seq}")
        line_cap = d.get("lineCap", 0)
        if isinstance(line_cap, (tuple, list)):
            line_cap = max(line_cap)
        shape.finish(
            color=d.get("color"),
            fill=None if border_only else d.get("fill"),
            width=d.get("width", 1.0),
            dashes=d.get("dashes"),
            lineCap=int(line_cap or 0),
            lineJoin=int(d.get("lineJoin", 0) or 0),
            closePath=bool(d.get("closePath", False)),
            even_odd=bool(d.get("even_odd", False)),
            stroke_opacity=float(d.get("stroke_opacity", 1.0) or 1.0),
            fill_opacity=float(d.get("fill_opacity", 1.0) or 1.0),
        )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), colorspace=fitz.csGRAY, alpha=False)
    gray = pix_to_gray(pix)
    x0, y0, x1, y1 = FIGURE_CROP
    return gray[y0:y1, x0:x1] <= (255 - THRESHOLD_CONTRAST)


def parent_for_char(bbox: tuple[float, float, float, float]) -> str:
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    for parent, rect in NODE_RECTS_PT.items():
        if rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]:
            return parent
    if 462 <= cx <= 492 and 160 <= cy <= 179:
        return "R7_label"
    raise RuntimeError(f"unassigned visible glyph center {(cx, cy)} bbox={bbox}")


def classify_glyph(char: str, font: str, size: float) -> tuple[str, int, bool]:
    natural_script = size < 9.5
    cp = ord(char)
    if natural_script:
        return "NATURAL_SCRIPT", 15, True
    if "NotoSerifSC" in font or 0x3400 <= cp <= 0x9FFF:
        return "CJK", 30, False
    if char in {"+", "−", "=", "𝛼", "𝑛", "N"} or "Math" in font or "Mezenets" in font:
        return "BASE_MATH", 22, False
    if char.isupper() or char.isdigit():
        return "LATIN_UPPER_DIGIT", 24, False
    if char.islower():
        return "LATIN_LOWER", 17, False
    return "BASE_MATH", 22, False


def expected_text_rgb(color_int: int) -> tuple[int, int, int]:
    return tuple(int(v) for v in fitz.sRGB_to_rgb(color_int))


def extract_glyph_rows(page: fitz.Page, full_rgb: np.ndarray, graphic_union: np.ndarray) -> tuple[list[dict], dict[str, np.ndarray]]:
    rows: list[dict] = []
    masks: dict[str, np.ndarray] = {}
    h, w = graphic_union.shape
    figure_rgb = full_rgb[FIGURE_CROP[1]:FIGURE_CROP[3], FIGURE_CROP[0]:FIGURE_CROP[2]]
    idx = 0
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    c = ch["c"]
                    bbox = tuple(float(v) for v in ch["bbox"])
                    if c.isspace():
                        continue
                    if not (bbox[2] >= FIGURE_PT[0] and bbox[0] <= FIGURE_PT[2] and bbox[3] >= FIGURE_PT[1] and bbox[1] <= FIGURE_PT[3]):
                        continue
                    idx += 1
                    eid = f"T{idx:03d}"
                    x0, y0, x1, y1 = page_bbox_to_crop_px(bbox)
                    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
                        raise RuntimeError(f"bad glyph bbox {eid}: {(x0,y0,x1,y1)}")
                    pad = 3
                    px0, py0, px1, py1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
                    patch = figure_rgb[py0:py1, px0:px1]
                    # 90th percentile is a stable local paper/node-fill estimate.
                    bg = np.percentile(patch.reshape(-1, 3), 90, axis=0)
                    glyph_patch = figure_rgb[y0:y1, x0:x1]
                    dark_contrast = np.max(bg.reshape(1, 1, 3) - glyph_patch.astype(float), axis=2)
                    candidate = dark_contrast >= THRESHOLD_CONTRAST
                    candidate_full = np.zeros((h, w), dtype=bool)
                    candidate_full[y0:y1, x0:x1] = candidate
                    candidate_graphic_intersection = int(np.count_nonzero(candidate_full & graphic_union))
                    final = candidate_full & ~graphic_union
                    masks[eid] = final
                    mb = mask_bbox(final)
                    if mb is None:
                        ink_h = ink_w = ink_area = 0
                    else:
                        ink_w, ink_h = mb[2] - mb[0], mb[3] - mb[1]
                        ink_area = int(np.count_nonzero(final))
                    role, threshold, natural_script = classify_glyph(c, span["font"], float(span["size"]))
                    parent = parent_for_char(bbox)
                    rows.append({
                        "element_id": eid,
                        "safe_filename": f"{eid}.png",
                        "kind": "GLYPH",
                        "char": c,
                        "codepoint": f"U+{ord(c):04X}",
                        "parent": parent,
                        "font": span["font"],
                        "pdf_size_pt": round(float(span["size"]), 6),
                        "source_effective_pt": 11.6 if float(span["size"]) > 10.5 else 10.1,
                        "natural_script": natural_script,
                        "role": role,
                        "bbox_pt": [round(v, 6) for v in bbox],
                        "bbox_crop_px": [x0, y0, x1, y1],
                        "mask_bbox_crop_px": list(mb) if mb else None,
                        "h_ink_px": ink_h,
                        "w_ink_px": ink_w,
                        "ink_area_px": ink_area,
                        "protocol_threshold_px": threshold,
                        "protocol_pixel_pass": ink_h >= threshold,
                        "candidate_graphic_intersection_px": candidate_graphic_intersection,
                        "separation_method": "tracked vector-graphic subtraction" if candidate_graphic_intersection else "bbox + local-background contrast",
                        "final_graphic_contamination_px": int(np.count_nonzero(final & graphic_union)),
                        "mask_nonempty": bool(ink_area),
                        "expected_rgb": list(expected_text_rgb(span["color"])),
                        "preownership_shared_px": 0,
                        "ownership_removed_px": 0,
                        "ownership_method": "unique",
                    })

    # PDF character bboxes may overlap across adjacent glyphs or natural line
    # spacing.  A raw page pixel must belong to exactly one glyph mask.  Resolve
    # only genuinely shared candidate pixels, assigning each to the connected
    # glyph component that continues most strongly beyond the shared pixel.
    # This is a traceable ownership split; no unshared target pixel is removed.
    ids = [r["element_id"] for r in rows]
    stack = np.stack([masks[eid] for eid in ids], axis=0)
    shared_yx = np.argwhere(stack.sum(axis=0) > 1)
    component_labels: dict[str, np.ndarray] = {}
    component_sizes: dict[str, np.ndarray] = {}
    for eid in ids:
        nlab, labs, stats, _ = cv2.connectedComponentsWithStats(masks[eid].astype(np.uint8), connectivity=8)
        component_labels[eid] = labs
        component_sizes[eid] = stats[:, cv2.CC_STAT_AREA] if nlab else np.zeros(1, dtype=int)
    shared_by_id = Counter()
    removed_by_id = Counter()
    for y, x in shared_yx:
        owners_idx = np.flatnonzero(stack[:, y, x])
        owners = [ids[int(i)] for i in owners_idx]
        for eid in owners:
            shared_by_id[eid] += 1
        scored = []
        for eid in owners:
            lab = int(component_labels[eid][y, x])
            size = int(component_sizes[eid][lab]) if lab < len(component_sizes[eid]) else 0
            scored.append((size, eid))
        winner = max(scored)[1]
        for eid in owners:
            if eid != winner:
                masks[eid][y, x] = False
                removed_by_id[eid] += 1
    row_by_id = {r["element_id"]: r for r in rows}
    for eid in ids:
        row = row_by_id[eid]
        final = masks[eid]
        mb = mask_bbox(final)
        row["mask_bbox_crop_px"] = list(mb) if mb else None
        row["h_ink_px"] = (mb[3] - mb[1]) if mb else 0
        row["w_ink_px"] = (mb[2] - mb[0]) if mb else 0
        row["ink_area_px"] = int(np.count_nonzero(final))
        row["protocol_pixel_pass"] = row["h_ink_px"] >= row["protocol_threshold_px"]
        row["mask_nonempty"] = bool(row["ink_area_px"])
        row["preownership_shared_px"] = int(shared_by_id[eid])
        row["ownership_removed_px"] = int(removed_by_id[eid])
        row["ownership_method"] = "shared-pixel connected-component continuation" if shared_by_id[eid] else "unique"
    return rows, masks


def edge_clearance(mask: np.ndarray) -> int:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return -1
    h, w = mask.shape
    return int(min(xs.min(), ys.min(), w - 1 - xs.max(), h - 1 - ys.max()))


def closest_points(a: np.ndarray, b: np.ndarray) -> tuple[tuple[int, int], tuple[int, int], float]:
    ayx = np.argwhere(a)
    byx = np.argwhere(b)
    if len(ayx) == 0 or len(byx) == 0:
        return (0, 0), (0, 0), float("inf")
    inter = np.argwhere(a & b)
    if len(inter):
        y, x = inter[len(inter) // 2]
        return (int(x), int(y)), (int(x), int(y)), 0.0
    tree = cKDTree(ayx)
    dist, ix = tree.query(byx, k=1)
    j = int(np.argmin(dist))
    ap = ayx[int(ix[j])]
    bp = byx[j]
    return (int(ap[1]), int(ap[0])), (int(bp[1]), int(bp[0])), float(dist[j])


def pair_rule(a: dict, b: dict) -> tuple[str, float, bool]:
    ka, kb = a["kind"], b["kind"]
    kinds = {ka, kb}
    if ka == kb == "GLYPH":
        if a["parent"] == b["parent"]:
            return "INTRA_PARENT_GLYPH_INTEGRITY", 0.0, False
        return "TEXT_TEXT_INDEPENDENT", 4.0, False
    if kinds == {"GLYPH", "NODE_BORDER"}:
        g = a if ka == "GLYPH" else b
        n = b if ka == "GLYPH" else a
        return ("TEXT_OWN_NODE_BORDER", 5.0, False) if g["parent"] == n["parent"] else ("TEXT_OTHER_NODE_BORDER", 3.0, False)
    if kinds == {"GLYPH", "RELATION"}:
        return "TEXT_RELATION_LINE_ARROW", 3.0, False
    if kinds == {"GLYPH", "MATH_RULE"}:
        g = a if ka == "GLYPH" else b
        if g["parent"] == "predictive" and (g["role"].startswith("BASE_MATH") or g["role"] == "NATURAL_SCRIPT"):
            return "DESIGN_SAME_FORMULA_RULE", 0.0, True
        return "TEXT_OTHER_MATH_RULE", 3.0, False
    if kinds == {"NODE_BORDER", "RELATION"}:
        n = a if ka == "NODE_BORDER" else b
        r = b if ka == "NODE_BORDER" else a
        if n["parent"] in REL_ENDPOINTS.get(r["element_id"], set()):
            return "DESIGN_RELATION_ENDPOINT", 0.0, True
        return "INDEPENDENT_BORDER_RELATION", 0.0, False
    return "GRAPHIC_GRAPHIC_OR_BACKGROUND", 0.0, False


def make_pair_rows(objects: list[dict], masks: dict[str, np.ndarray]) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    critical: list[dict] = []
    for a, b in itertools.combinations(objects, 2):
        ma, mb = masks[a["element_id"]], masks[b["element_id"]]
        inter = int(np.count_nonzero(ma & mb))
        ap, bp, center_dist = closest_points(ma, mb)
        clearance = max(0.0, center_dist - 1.0) if math.isfinite(center_dist) else -1.0
        relation_class, threshold, design = pair_rule(a, b)
        if design:
            hard_fail = False
            status = "DESIGN_WHITELIST"
        elif inter > 0:
            hard_fail = True
            status = "HARD_FAIL_ILLEGAL_OVERLAP"
        elif threshold > 0 and clearance + 1e-6 < threshold:
            hard_fail = True
            status = "HARD_FAIL_CLEARANCE"
        else:
            hard_fail = False
            status = "PASS"
        advisory = False
        if not hard_fail and not design and threshold > 0 and clearance < threshold + 3:
            advisory = True
            status = "PASS_NEAR_THRESHOLD_ADVISORY"
        row = {
            "pair_id": f"P-{a['element_id']}-{b['element_id']}",
            "a_id": a["element_id"],
            "b_id": b["element_id"],
            "a_kind": a["kind"],
            "b_kind": b["kind"],
            "a_parent": a["parent"],
            "b_parent": b["parent"],
            "relation_class": relation_class,
            "threshold_px": threshold,
            "intersection_px": inter,
            "center_distance_px": round(center_dist, 4) if math.isfinite(center_dist) else None,
            "clearance_px": round(clearance, 4) if clearance >= 0 else None,
            "closest_a_crop_px": list(ap),
            "closest_b_crop_px": list(bp),
            "design_whitelist": design,
            "machine_hard_fail": hard_fail,
            "r168_advisory": advisory,
            "machine_status": status,
        }
        rows.append(row)
        if hard_fail or advisory or design or (threshold > 0 and clearance <= max(12, threshold + 5)):
            critical.append(row)
    return rows, critical


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def label_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def save_object_evidence(objects: list[dict], masks: dict[str, np.ndarray]) -> None:
    for obj in objects:
        eid = obj["element_id"]
        sub = "glyph" if obj["kind"] == "GLYPH" else "graphic"
        save_gray((masks[eid].astype(np.uint8) * 255), ROOT / "masks" / sub / f"{eid}.png")
        with (ROOT / "objects" / sub / f"{eid}.json").open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)


def make_text_overlay(figure_rgb: np.ndarray, glyphs: list[dict]) -> None:
    im = Image.fromarray(figure_rgb.copy(), "RGB")
    dr = ImageDraw.Draw(im)
    font = label_font(13)
    for g in glyphs:
        x0, y0, x1, y1 = g["bbox_crop_px"]
        dr.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 0, 0), width=1)
        dr.text((x0, max(0, y0 - 13)), g["element_id"], fill=(180, 0, 0), font=font)
    im.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def contact_cell(base: np.ndarray, mask: np.ndarray, obj: dict, eight_x: bool = True) -> Image.Image:
    bb = mask_bbox(mask)
    if bb is None:
        bb = tuple(obj.get("bbox_crop_px") or (0, 0, 20, 20))
    x0, y0, x1, y1 = bb
    pad = 6
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(base.shape[1], x1 + pad), min(base.shape[0], y1 + pad)
    raw = base[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1]
    over = raw.copy()
    over[m] = np.array([255, 0, 0], np.uint8)
    only = np.zeros_like(raw)
    only[m] = np.array([255, 255, 255], np.uint8)
    scale = 8 if eight_x else max(1, min(4, 500 // max(1, raw.shape[1])))
    views = []
    for arr in (raw, over, only):
        im = Image.fromarray(arr, "RGB")
        views.append(im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST))
    vw = max(i.width for i in views)
    vh = max(i.height for i in views)
    cell = Image.new("RGB", (vw * 3 + 40, vh + 70), "white")
    dr = ImageDraw.Draw(cell)
    title = f"{obj['element_id']}  {obj.get('char','')}  {obj['parent']}  {obj['kind']}"
    dr.text((8, 6), title, fill="black", font=label_font(18))
    for j, (name, im) in enumerate(zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), views)):
        xx = j * vw + 8
        cell.paste(im, (xx, 40))
        dr.text((xx, vh + 45), name, fill="black", font=label_font(14))
    return cell


def make_contact_sheets(base: np.ndarray, objects: list[dict], masks: dict[str, np.ndarray], sub: str, per_sheet: int, eight_x: bool) -> list[str]:
    out: list[str] = []
    for si in range(0, len(objects), per_sheet):
        batch = objects[si:si + per_sheet]
        cells = [contact_cell(base, masks[o["element_id"]], o, eight_x=eight_x) for o in batch]
        cols = 2
        rows = math.ceil(len(cells) / cols)
        cw = max(c.width for c in cells)
        ch = max(c.height for c in cells)
        sheet = Image.new("RGB", (cols * cw, rows * ch + 38), (235, 235, 235))
        dr = ImageDraw.Draw(sheet)
        sheet_no = si // per_sheet + 1
        dr.text((10, 8), f"{sub.upper()} CONTACT SHEET {sheet_no} — native ROI / 8x nearest as labeled", fill="black", font=label_font(20))
        for j, cell in enumerate(cells):
            sheet.paste(cell, ((j % cols) * cw, 38 + (j // cols) * ch))
        name = f"{sub}_contact_{sheet_no:02d}.png"
        sheet.save(ROOT / "contact_sheets" / sub / name)
        out.append(f"contact_sheets/{sub}/{name}")
    return out


def make_pair_matrix(objects: list[dict], pairs: list[dict]) -> None:
    n = len(objects)
    cell = 24
    margin = 260
    im = Image.new("RGB", (margin + n * cell + 20, margin + n * cell + 90), "white")
    dr = ImageDraw.Draw(im)
    font = label_font(12)
    id_to_i = {o["element_id"]: i for i, o in enumerate(objects)}
    colors = {
        "PASS": (198, 239, 206),
        "PASS_NEAR_THRESHOLD_ADVISORY": (255, 222, 140),
        "DESIGN_WHITELIST": (176, 215, 255),
        "HARD_FAIL_ILLEGAL_OVERLAP": (255, 80, 80),
        "HARD_FAIL_CLEARANCE": (255, 80, 80),
    }
    for i in range(n):
        x = margin + i * cell
        y = margin + i * cell
        dr.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(205, 205, 205), outline=(160, 160, 160))
    for r in pairs:
        i, j = id_to_i[r["a_id"]], id_to_i[r["b_id"]]
        col = colors[r["machine_status"]]
        for a, b in ((i, j), (j, i)):
            x = margin + b * cell
            y = margin + a * cell
            dr.rectangle((x, y, x + cell - 1, y + cell - 1), fill=col, outline=(230, 230, 230))
    for i, o in enumerate(objects):
        x = margin + i * cell
        y = margin + i * cell
        dr.text((x + 2, 8), o["element_id"], fill="black", font=font)
        dr.text((8, y + 2), o["element_id"], fill="black", font=font)
    dr.text((10, im.height - 70), "green=PASS  amber=R168 advisory/near  blue=design whitelist  red=hard FAIL  gray=diagonal", fill="black", font=label_font(18))
    dr.text((10, im.height - 42), f"N={n}; unordered pairs={len(pairs)}=C({n},2)", fill="black", font=label_font(18))
    im.save(ROOT / "overlays" / "complete_pair_matrix.png")


def make_critical_sheets(base: np.ndarray, critical: list[dict], objects_by_id: dict[str, dict], masks: dict[str, np.ndarray]) -> list[str]:
    cells: list[Image.Image] = []
    for r in critical:
        ma, mb = masks[r["a_id"]], masks[r["b_id"]]
        ax, ay = r["closest_a_crop_px"]
        bx, by = r["closest_b_crop_px"]
        cx, cy = (ax + bx) // 2, (ay + by) // 2
        rad = 28
        x0, y0 = max(0, cx - rad), max(0, cy - rad)
        x1, y1 = min(base.shape[1], cx + rad + 1), min(base.shape[0], cy + rad + 1)
        raw = base[y0:y1, x0:x1].copy()
        a = ma[y0:y1, x0:x1]
        b = mb[y0:y1, x0:x1]
        inter = a & b
        over = raw.copy()
        over[a] = np.array([255, 0, 0], np.uint8)
        over[b] = np.array([0, 90, 255], np.uint8)
        over[inter] = np.array([255, 0, 255], np.uint8)
        aonly = np.zeros_like(raw); aonly[a] = 255
        bonly = np.zeros_like(raw); bonly[b] = 255
        ionly = np.zeros_like(raw); ionly[inter] = 255
        views = [raw, over, aonly, bonly, ionly]
        scale = 8
        ims = [Image.fromarray(v, "RGB").resize((v.shape[1] * scale, v.shape[0] * scale), Image.Resampling.NEAREST) for v in views]
        vw, vh = ims[0].size
        cell = Image.new("RGB", (vw * 5 + 20, vh + 78), "white")
        dr = ImageDraw.Draw(cell)
        title = f"{r['pair_id']} {r['relation_class']} clr={r['clearance_px']} int={r['intersection_px']} {r['machine_status']}"
        dr.text((6, 5), title, fill="black", font=label_font(15))
        for j, (name, im) in enumerate(zip(("RAW", "A(red)/B(blue)", "A MASK", "B MASK", "INTERSECTION"), ims)):
            cell.paste(im, (j * vw + 4, 36))
            dr.text((j * vw + 4, vh + 42), name, fill="black", font=label_font(12))
        cells.append(cell)
    out: list[str] = []
    per_sheet = 4
    for si in range(0, len(cells), per_sheet):
        batch = cells[si:si + per_sheet]
        cw = max(c.width for c in batch)
        ch = max(c.height for c in batch)
        sheet = Image.new("RGB", (cw, ch * len(batch) + 36), (235, 235, 235))
        dr = ImageDraw.Draw(sheet)
        sn = si // per_sheet + 1
        dr.text((8, 6), f"CRITICAL PAIR SHEET {sn} — all views are 8x nearest from native 1x masks", fill="black", font=label_font(18))
        for j, c in enumerate(batch):
            sheet.paste(c, (0, 36 + j * ch))
        name = f"critical_pairs_{sn:02d}.png"
        sheet.save(ROOT / "contact_sheets" / "critical" / name)
        out.append(f"contact_sheets/critical/{name}")
    return out


def make_relationship_overlay(base: np.ndarray, graphics: list[dict], masks: dict[str, np.ndarray]) -> None:
    im = Image.fromarray(base.copy(), "RGB")
    arr = np.array(im)
    palette = [(220, 20, 60), (0, 120, 255), (255, 140, 0), (128, 0, 200), (0, 150, 70), (200, 70, 170), (40, 40, 40)]
    dr = ImageDraw.Draw(im)
    font = label_font(16)
    for col, obj in zip(palette, [o for o in graphics if o["kind"] == "RELATION"]):
        m = masks[obj["element_id"]]
        arr[m] = np.array(col, np.uint8)
    im = Image.fromarray(arr, "RGB")
    dr = ImageDraw.Draw(im)
    for col, obj in zip(palette, [o for o in graphics if o["kind"] == "RELATION"]):
        bb = mask_bbox(masks[obj["element_id"]])
        if bb:
            dr.text((bb[0], max(0, bb[1] - 18)), f"{obj['element_id']} {obj['parent']}", fill=col, font=font)
    im.save(ROOT / "overlays" / "seven_relationships_overlay_300dpi.png")


def main() -> None:
    ensure_dirs()
    pdf_hash = sha256(PDF)
    if PDF.stat().st_size != EXPECTED_BYTES or pdf_hash != EXPECTED_SHA256:
        raise RuntimeError("official R103 identity mismatch")
    doc = fitz.open(PDF)
    if doc.page_count != 817:
        raise RuntimeError(f"expected 817 pages, got {doc.page_count}")
    page = doc[PAGE_INDEX]
    if abs(page.rect.width - 595.276) > 0.01 or abs(page.rect.height - 841.89) > 0.01:
        raise RuntimeError(f"physical page {PHYSICAL_PAGE} is not expected A4 point size: {page.rect}")
    source_text = SOURCE.read_text(encoding="utf-8")
    if "FIG-P654-01" not in source_text or "fontsize{10.1pt}" not in source_text or "at 11.6pt" not in source_text:
        raise RuntimeError("source identity/font declarations not found")

    m300 = fitz.Matrix(SCALE300, SCALE300)
    m200 = fitz.Matrix(SCALE200, SCALE200)
    pix300 = page.get_pixmap(matrix=m300, colorspace=fitz.csRGB, alpha=False)
    full300 = pix_to_array(pix300)
    if (pix300.width, pix300.height) != (2481, 3508):
        raise RuntimeError(f"unexpected 300dpi grid {(pix300.width,pix300.height)}")
    pix200 = page.get_pixmap(matrix=m200, colorspace=fitz.csRGB, alpha=False)
    full200 = pix_to_array(pix200)
    save_rgb(full200, ROOT / "full_page_200dpi.png")
    x0, y0, x1, y1 = FIGURE_CROP
    figure_rgb = full300[y0:y1, x0:x1].copy()
    save_rgb(figure_rgb, ROOT / "figure_crop_300dpi.png")
    sx0, sy0, sx1, sy1 = STANDALONE_CROP
    save_rgb(full300[sy0:sy1, sx0:sx1].copy(), ROOT / "standalone_300dpi.png")
    pix300g = page.get_pixmap(matrix=m300, colorspace=fitz.csGRAY, alpha=False)
    full300g = pix_to_gray(pix300g)
    save_gray(full300g[y0:y1, x0:x1].copy(), ROOT / "grayscale_300dpi.png")

    drawings = page.get_drawings()
    by_seq = {int(d["seqno"]): d for d in drawings}
    expected_seqs = sorted(s for _, _, seqs in GRAPHIC_DEFS.values() for s in seqs)
    observed_figure_seqs = sorted(int(d["seqno"]) for d in drawings if d["rect"].x1 >= 70 and d["rect"].x0 <= 536 and d["rect"].y1 >= 60 and d["rect"].y0 <= 216)
    if observed_figure_seqs != expected_seqs:
        raise RuntimeError(f"drawing/path coverage mismatch expected={expected_seqs} observed={observed_figure_seqs}")

    graphic_rows: list[dict] = []
    graphic_masks: dict[str, np.ndarray] = {}
    drawing_ledger: list[dict] = []
    for eid, (kind, parent, seqnos) in GRAPHIC_DEFS.items():
        border_only = kind == "NODE_BORDER"
        mask = render_graphic_mask(page.rect, by_seq, seqnos, border_only=border_only)
        graphic_masks[eid] = mask
        mb = mask_bbox(mask)
        row = {
            "element_id": eid,
            "safe_filename": f"{eid}.png",
            "kind": kind,
            "char": "",
            "codepoint": "",
            "parent": parent,
            "font": "",
            "pdf_size_pt": "",
            "source_effective_pt": "",
            "natural_script": False,
            "role": kind,
            "bbox_pt": [round(v, 6) for v in fitz.Rect(*(by_seq[seqnos[0]]["rect"]))],
            "bbox_crop_px": list(mb) if mb else None,
            "mask_bbox_crop_px": list(mb) if mb else None,
            "h_ink_px": (mb[3] - mb[1]) if mb else 0,
            "w_ink_px": (mb[2] - mb[0]) if mb else 0,
            "ink_area_px": int(np.count_nonzero(mask)),
            "protocol_threshold_px": 1,
            "protocol_pixel_pass": bool(np.count_nonzero(mask)),
            "candidate_graphic_intersection_px": 0,
            "separation_method": "replayed exact PDF drawing/path at 300 dpi; node fills excluded",
            "final_graphic_contamination_px": 0,
            "mask_nonempty": bool(np.count_nonzero(mask)),
            "expected_rgb": "",
            "drawing_seqnos": seqnos,
        }
        graphic_rows.append(row)
        for seq in seqnos:
            d = by_seq[seq]
            drawing_ledger.append({
                "drawing_seqno": seq,
                "semantic_graphic_id": eid,
                "kind": kind,
                "parent": parent,
                "pdf_type": d["type"],
                "bbox_pt": ";".join(f"{v:.6f}" for v in d["rect"]),
                "width_pt": d.get("width"),
                "mapped": True,
            })
    graphic_union = np.logical_or.reduce(list(graphic_masks.values()))
    glyph_rows, glyph_masks = extract_glyph_rows(page, full300, graphic_union)
    if len(glyph_rows) != 93:
        raise RuntimeError(f"visible glyph denominator mismatch: expected 93, got {len(glyph_rows)}")
    parent_text = defaultdict(str)
    for g in glyph_rows:
        parent_text[g["parent"]] += g["char"]
    text_semantic_pass = dict(parent_text) == EXPECTED_PARENT_TEXT
    if not text_semantic_pass:
        raise RuntimeError(f"semantic text mismatch actual={dict(parent_text)!r}")

    objects = glyph_rows + graphic_rows
    masks = {**glyph_masks, **graphic_masks}
    for obj in objects:
        obj["edge_clearance_crop_px"] = edge_clearance(masks[obj["element_id"]])
        obj["clip_pixel_count"] = int(
            np.count_nonzero(masks[obj["element_id"]][0, :])
            + np.count_nonzero(masks[obj["element_id"]][-1, :])
            + np.count_nonzero(masks[obj["element_id"]][:, 0])
            + np.count_nonzero(masks[obj["element_id"]][:, -1])
        )

    pairs, critical = make_pair_rows(objects, masks)
    expected_pairs = len(objects) * (len(objects) - 1) // 2
    if len(pairs) != expected_pairs:
        raise RuntimeError("unordered pair denominator mismatch")

    write_csv(ROOT / "after_font_audit.csv", glyph_rows)
    write_csv(ROOT / "after_pixel_measurements.csv", objects)
    write_csv(ROOT / "after_overlap_report.csv", pairs)
    write_csv(ROOT / "tables" / "object_manifest.csv", objects)
    write_csv(ROOT / "tables" / "critical_pairs.csv", critical)
    write_csv(ROOT / "tables" / "drawing_path_ledger.csv", drawing_ledger)
    write_csv(ROOT / "tables" / "id_filename_map.csv", [
        {"element_id": o["element_id"], "safe_filename": o["safe_filename"], "ordinary_png": f"masks/{'glyph' if o['kind']=='GLYPH' else 'graphic'}/{o['safe_filename']}", "ordinary_json": f"objects/{'glyph' if o['kind']=='GLYPH' else 'graphic'}/{o['element_id']}.json"}
        for o in objects
    ])
    source_audit = [
        {"source_scope": "tikzset/every node", "declared_pt": 10.1, "graphics_scale": 1.0, "effective_pt": 10.1, "classification": "BASE_TEXT", "hard_gate": ">=9.5pt", "status": "PASS"},
        {"source_scope": "trial count n", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "classification": "BASE_MATH", "hard_gate": ">=9.5pt", "status": "PASS"},
        {"source_scope": "posterior formula", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "classification": "FORMULA_BLOCK", "hard_gate": ">=9.5pt", "status": "PASS"},
        {"source_scope": "predictive fraction base", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "classification": "FORMULA_BLOCK", "hard_gate": ">=9.5pt; natural scripts excepted", "status": "PASS"},
        {"source_scope": "application edge label", "declared_pt": 10.1, "graphics_scale": 1.0, "effective_pt": 10.1, "classification": "ANNOTATION", "hard_gate": ">=9.5pt", "status": "PASS"},
    ]
    write_csv(ROOT / "tables" / "source_font_audit.csv", source_audit)

    save_object_evidence(objects, masks)
    make_text_overlay(figure_rgb, glyph_rows)
    glyph_sheets = make_contact_sheets(figure_rgb, glyph_rows, masks, "glyph", per_sheet=8, eight_x=True)
    graphic_sheets = make_contact_sheets(figure_rgb, graphic_rows, masks, "graphic", per_sheet=4, eight_x=False)
    make_pair_matrix(objects, pairs)
    critical_sheets = make_critical_sheets(figure_rgb, critical, {o["element_id"]: o for o in objects}, masks)
    make_relationship_overlay(figure_rgb, graphic_rows, masks)

    protocol_pixel_failures = [g["element_id"] for g in glyph_rows if not g["protocol_pixel_pass"]]
    empty_masks = [o["element_id"] for o in objects if not o["mask_nonempty"]]
    illegal_overlap_pairs = [r["pair_id"] for r in pairs if r["machine_status"] == "HARD_FAIL_ILLEGAL_OVERLAP"]
    hard_clearance_pairs = [r["pair_id"] for r in pairs if r["machine_status"] == "HARD_FAIL_CLEARANCE"]
    clip_pixels = sum(int(o["clip_pixel_count"]) for o in objects)
    machine_hard_pass = not (empty_masks or illegal_overlap_pairs or hard_clearance_pairs or clip_pixels or not text_semantic_pass)
    summary = {
        "handoff_id": HANDOFF_ID,
        "uid": "FIG-P654-01",
        "candidate": "R103",
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": pdf_hash,
        "physical_page": PHYSICAL_PAGE,
        "page_count": doc.page_count,
        "page_pt": [round(page.rect.width, 6), round(page.rect.height, 6)],
        "native_300dpi_page_px": [pix300.width, pix300.height],
        "native_200dpi_page_px": [pix200.width, pix200.height],
        "figure_crop_fullpage_px": list(FIGURE_CROP),
        "figure_crop_native_px": [FIGURE_CROP[2] - FIGURE_CROP[0], FIGURE_CROP[3] - FIGURE_CROP[1]],
        "standalone_crop_fullpage_px": list(STANDALONE_CROP),
        "standalone_native_px": [STANDALONE_CROP[2] - STANDALONE_CROP[0], STANDALONE_CROP[3] - STANDALONE_CROP[1]],
        "glyph_denominator": len(glyph_rows),
        "graphic_denominator": len(graphic_rows),
        "graphic_breakdown": dict(Counter(o["kind"] for o in graphic_rows)),
        "total_object_denominator": len(objects),
        "unordered_pair_denominator": len(pairs),
        "unordered_pair_formula": f"C({len(objects)},2)={expected_pairs}",
        "critical_pair_denominator": len(critical),
        "drawing_path_denominator": len(observed_figure_seqs),
        "drawing_path_mapped": len(drawing_ledger),
        "glyph_contact_sheets": glyph_sheets,
        "graphic_contact_sheets": graphic_sheets,
        "critical_contact_sheets": critical_sheets,
        "text_semantic_actual": dict(parent_text),
        "text_semantic_expected": EXPECTED_PARENT_TEXT,
        "text_semantic_pass": text_semantic_pass,
        "formula_semantics": {
            "posterior": "参数 U+1D6FC U+002B U+1D45B",
            "predictive_numerator": "U+1D6FC U+1D456 U+002B U+1D45B U+1D456",
            "predictive_denominator": "U+1D6FC U+0030 U+002B U+004E",
            "fraction_rule_graphic": "G016 / PDF drawing seqno 18",
            "seven_source_relations": [f"G{i:03d}" for i in range(9, 16)],
        },
        "empty_masks": empty_masks,
        "illegal_overlap_pairs": illegal_overlap_pairs,
        "hard_clearance_pairs": hard_clearance_pairs,
        "clip_pixel_count": clip_pixels,
        "protocol_pixel_threshold_failures": protocol_pixel_failures,
        "r168_note": "[0.92,1.08] micro-ratios, taxonomy/peer detail, font metadata micro-differences and 1–2 px raster differences are advisory only; hard font failures are limited to tofu/wrong codepoint or math semantics/actual unreadability/obvious severe imbalance/true clipping or overlap.",
        "machine_hard_gate_pass": machine_hard_pass,
        "manual_fields_generated_by_machine": False,
    }
    with (ROOT / "machine_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with (ROOT / "machine_crosscheck.md").open("w", encoding="utf-8") as f:
        f.write("# FIG-P654-01 R103 machine cross-check\n\n")
        f.write(f"- PDF identity: `{pdf_hash}` / `{PDF.stat().st_size}` bytes / 817 pages / physical page 704 A4: PASS\n")
        f.write(f"- Native grids: 300 dpi `{pix300.width}×{pix300.height}`; 200 dpi `{pix200.width}×{pix200.height}`; figure crop `{FIGURE_CROP}`: PASS\n")
        f.write(f"- Objects: {len(glyph_rows)} visible glyphs + {len(graphic_rows)} graphic objects = {len(objects)}; drawing paths {len(drawing_ledger)}/{len(observed_figure_seqs)} mapped.\n")
        f.write(f"- Complete unordered pairs: C({len(objects)},2)={len(pairs)}; critical={len(critical)}.\n")
        f.write(f"- Empty masks={len(empty_masks)}; illegal overlap pairs={len(illegal_overlap_pairs)}; hard-clearance pairs={len(hard_clearance_pairs)}; clip pixels={clip_pixels}.\n")
        f.write(f"- Protocol raw pixel threshold deviations={len(protocol_pixel_failures)} (`{','.join(protocol_pixel_failures) or 'none'}`); these remain distinct from the R168 hard-font verdict.\n")
        f.write(f"- Semantic glyph/codepoint/formula reconstruction: {'PASS' if text_semantic_pass else 'FAIL'}.\n")
        f.write(f"- Machine hard gate: **{'PASS' if machine_hard_pass else 'FAIL'}**. Machine output does not populate reviewer/visual/decision/note fields.\n")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
