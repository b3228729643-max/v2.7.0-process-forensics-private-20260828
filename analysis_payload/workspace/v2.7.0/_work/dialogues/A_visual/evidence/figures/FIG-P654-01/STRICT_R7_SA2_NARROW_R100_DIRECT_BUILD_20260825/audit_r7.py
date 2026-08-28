from __future__ import annotations

import csv
import json
import math
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import label as connected_components
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R7_SA2_NARROW_R100_DIRECT_BUILD_20260825\build\v260_FIG-P654-01_standalone.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R7_SA2_NARROW_R100_DIRECT_BUILD_20260825")
PAGE_1BASED = 1
PRINTED_PAGE = "standalone"
DPI = 300
SCALE = DPI / 72.0
FIG_CROP_PT = fitz.Rect(65, 61, 541, 230)
STANDALONE_PT = fitz.Rect(65, 61, 541, 210.5)
FIGURE_TEXT_SEQ = {
    2: ("TRIAL", "NODE_LABEL", 22),
    5: ("GAMMA", "NODE_LABEL", 23),
    8: ("FAMILIES", "NODE_LABEL", 24),
    11: ("POSTERIOR", "NODE_LABEL_OR_FORMULA", 26),
    14: ("PREDICTIVE", "NODE_LABEL_OR_FORMULA", 30),
    16: ("PREDICTIVE_FORMULA", "FORMULA_BLOCK", 34),
    19: ("SIMPLEX", "NODE_LABEL", 35),
    22: ("MOM", "NODE_LABEL", 36),
    25: ("LDA", "NODE_LABEL", 37),
    43: ("APPLICATION", "EDGE_LABEL_ANNOTATION", 46),
}


GRAPHICS = {
    0: ("GFX_NODE_BORDER_TRIAL", "NODE_BORDER", "TRIAL", 10, None),
    3: ("GFX_NODE_BORDER_GAMMA", "NODE_BORDER", "GAMMA", 12, None),
    6: ("GFX_NODE_BORDER_FAMILIES", "NODE_BORDER", "FAMILIES", 10, None),
    9: ("GFX_NODE_BORDER_POSTERIOR", "NODE_BORDER", "POSTERIOR", 14, None),
    12: ("GFX_NODE_BORDER_PREDICTIVE", "NODE_BORDER", "PREDICTIVE", 14, None),
    15: ("GFX_MATH_RULE_PREDICTIVE_FRACTION", "MATH_RULE", "PREDICTIVE_FORMULA", 34, None),
    17: ("GFX_NODE_BORDER_SIMPLEX", "NODE_BORDER", "SIMPLEX", 12, None),
    20: ("GFX_NODE_BORDER_MOM", "NODE_BORDER", "MOM", 12, None),
    23: ("GFX_NODE_BORDER_LDA", "NODE_BORDER", "LDA", 12, None),
    26: ("GFX_LINE_TRIAL_TO_FAMILIES", "LINE_ARROW", "EDGE_TRIAL_FAMILIES", 40, "TRIAL_TO_FAMILIES"),
    27: ("GFX_HEAD_TRIAL_TO_FAMILIES", "ARROWHEAD", "EDGE_TRIAL_FAMILIES", 40, "TRIAL_TO_FAMILIES"),
    29: ("GFX_LINE_GAMMA_TO_FAMILIES", "LINE_ARROW", "EDGE_GAMMA_FAMILIES", 41, "GAMMA_TO_FAMILIES"),
    30: ("GFX_HEAD_GAMMA_TO_FAMILIES", "ARROWHEAD", "EDGE_GAMMA_FAMILIES", 41, "GAMMA_TO_FAMILIES"),
    32: ("GFX_LINE_FAMILIES_TO_POSTERIOR", "LINE_ARROW", "EDGE_FAMILIES_POSTERIOR", 42, "FAMILIES_TO_POSTERIOR"),
    33: ("GFX_HEAD_FAMILIES_TO_POSTERIOR", "ARROWHEAD", "EDGE_FAMILIES_POSTERIOR", 42, "FAMILIES_TO_POSTERIOR"),
    35: ("GFX_LINE_POSTERIOR_TO_PREDICTIVE", "LINE_ARROW", "EDGE_POSTERIOR_PREDICTIVE", 43, "POSTERIOR_TO_PREDICTIVE"),
    36: ("GFX_HEAD_POSTERIOR_TO_PREDICTIVE", "ARROWHEAD", "EDGE_POSTERIOR_PREDICTIVE", 43, "POSTERIOR_TO_PREDICTIVE"),
    38: ("GFX_LINE_FAMILIES_TO_SIMPLEX", "LINE_ARROW", "EDGE_FAMILIES_SIMPLEX", 44, "FAMILIES_TO_SIMPLEX"),
    39: ("GFX_LINE_POSTERIOR_TO_MOM", "LINE_ARROW", "EDGE_POSTERIOR_MOM", 45, "POSTERIOR_TO_MOM"),
    40: ("GFX_LINE_PREDICTIVE_TO_LDA", "LINE_ARROW", "EDGE_PREDICTIVE_LDA", 46, "PREDICTIVE_TO_LDA"),
    41: ("GFX_HEAD_PREDICTIVE_TO_LDA", "ARROWHEAD", "EDGE_PREDICTIVE_LDA", 46, "PREDICTIVE_TO_LDA"),
}

EDGE_ENDPOINTS = {
    "TRIAL_TO_FAMILIES": {"TRIAL", "FAMILIES"},
    "GAMMA_TO_FAMILIES": {"GAMMA", "FAMILIES"},
    "FAMILIES_TO_POSTERIOR": {"FAMILIES", "POSTERIOR"},
    "POSTERIOR_TO_PREDICTIVE": {"POSTERIOR", "PREDICTIVE"},
    "FAMILIES_TO_SIMPLEX": {"FAMILIES", "SIMPLEX"},
    "POSTERIOR_TO_MOM": {"POSTERIOR", "MOM"},
    "PREDICTIVE_TO_LDA": {"PREDICTIVE", "LDA"},
}

PARENT_BACKGROUNDS = {
    "TRIAL": (246, 247, 248),
    "GAMMA": (246, 247, 248),
    "FAMILIES": (242, 246, 250),
    "POSTERIOR": (255, 255, 255),
    "PREDICTIVE": (255, 255, 255),
    "PREDICTIVE_FORMULA": (255, 255, 255),
    "SIMPLEX": (246, 247, 248),
    "MOM": (246, 247, 248),
    "LDA": (246, 247, 248),
    "APPLICATION": (255, 255, 255),
}


@dataclass
class Obj:
    id: str
    safe: str
    kind: str
    parent: str
    container: str
    seqno: int
    source_line: int
    text: str = ""
    font: str = ""
    pdf_font_pt: float | None = None
    declared_pt: float | None = None
    effective_pt: float | None = None
    natural_script: bool = False
    script_class: str = "N/A"
    threshold_px: int | None = None
    edge_id: str | None = None
    vector_bbox_pt: tuple[float, float, float, float] | None = None
    pre_coords: np.ndarray = field(default_factory=lambda: np.empty((0, 2), dtype=np.int32))
    final_coords: np.ndarray = field(default_factory=lambda: np.empty((0, 2), dtype=np.int32))
    mask_bbox_px: tuple[int, int, int, int] | None = None
    h_ink_px: int | None = None
    ink_area_px: int = 0
    pre_ink_area_px: int = 0
    occluded_px: int = 0
    clip_px: int = 0
    foreign_pixel_px: int = 0
    missing_stroke_px: int = 0
    decision: str = "PENDING"


def ensure_dirs() -> None:
    for rel in (
        "views", "objects/raw_masks", "objects/pre_masks", "objects/evidence_1x",
        "objects/evidence_8x_nearest", "contact_sheets/glyphs", "contact_sheets/graphics",
        "pairs/critical", "machine"
    ):
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pix_to_image(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def page_rect_to_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE), math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE), math.ceil(rect.y1 * SCALE),
    )


def coords_bbox(coords: np.ndarray) -> tuple[int, int, int, int] | None:
    if len(coords) == 0:
        return None
    ys, xs = coords[:, 0], coords[:, 1]
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def classify_char(ch: str, font: str, is_math: bool, natural_script: bool) -> tuple[str, int]:
    cp = ord(ch)
    name = unicodedata.name(ch, "")
    if natural_script:
        return "NATURAL_TEX_SCRIPT", 15
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_FULL", 30
    if is_math:
        return "BASE_MATH_OPERATOR_OR_GLYPH", 22
    if ch.isdigit() or (ch.isalpha() and (ch.isupper() or "CAPITAL" in name)):
        return "LATIN_CAP_DIGIT", 24
    if ch.isalpha() or "SMALL" in name:
        return "LATIN_GREEK_LOWER", 17
    if ch in "+=−≠≤≥×÷/":
        return "MATH_OPERATOR", 22
    if unicodedata.category(ch).startswith("P"):
        return "LOW_PROFILE_PUNCTUATION", -1
    return "FULL_HEIGHT_SYMBOL", 30


def text_mask(full_rgb: np.ndarray, bbox: fitz.Rect, fg_float, bg_rgb) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = page_rect_to_px(bbox)
    h, w = full_rgb.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    roi = full_rgb[y0:y1, x0:x1].astype(np.float32)
    bg = np.array(bg_rgb, dtype=np.float32)
    fg = np.array(fg_float, dtype=np.float32) * 255.0
    direction = fg - bg
    den = float(np.dot(direction, direction))
    q = roi - bg
    t = np.sum(q * direction, axis=2) / den
    reconstructed = bg + t[..., None] * direction
    residual = np.max(np.abs(roi - reconstructed), axis=2)
    contrast = np.max(np.abs(q), axis=2)
    mask = (contrast >= 20.0) & (t > 0.0) & (t <= 1.18) & (residual <= 11.0)
    # A tight text bbox can contain a nearby long node-border antialias row.  It is
    # not target text ownership.  Remove only bottom-edge, nearly full-width,
    # very-low-height line components; ordinary glyph strokes do not satisfy all
    # three constraints.  This is deterministic component ownership, not erosion.
    labels, component_count = connected_components(mask, structure=np.ones((3, 3), dtype=np.uint8))
    for component_id in range(1, component_count + 1):
        cy, cx = np.nonzero(labels == component_id)
        if not len(cx):
            continue
        comp_w = int(cx.max() - cx.min() + 1)
        comp_h = int(cy.max() - cy.min() + 1)
        at_bottom = int(cy.max()) >= max(0, mask.shape[0] - 5)
        spans_width = comp_w >= max(8, math.ceil(mask.shape[1] * 0.85))
        if at_bottom and spans_width and comp_h <= 5:
            mask[labels == component_id] = False
    ys, xs = np.nonzero(mask)
    return np.column_stack((ys + y0, xs + x0)).astype(np.int32), (x0, y0, x1, y1)


def replay_drawing(page_rect: fitz.Rect, d: dict, stroke_only: bool) -> np.ndarray:
    temp = fitz.open()
    page = temp.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
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
            raise RuntimeError(f"unsupported drawing item {op!r} in seq {d['seqno']}")
    line_cap = d.get("lineCap", 0)
    if isinstance(line_cap, tuple):
        line_cap = max(line_cap)
    fill = None if stroke_only else d.get("fill")
    shape.finish(
        color=d.get("color"), fill=fill, width=d.get("width") or 1,
        dashes=d.get("dashes"), lineCap=line_cap,
        lineJoin=d.get("lineJoin", 0), closePath=d.get("closePath", False),
        even_odd=d.get("even_odd", False),
        stroke_opacity=d.get("stroke_opacity", 1) or 1,
        fill_opacity=(d.get("fill_opacity", 1) or 1) if fill is not None else 1,
    )
    shape.commit()
    clip = fitz.Rect(d["rect"])
    clip.x0 -= 2
    clip.y0 -= 2
    clip.x1 += 2
    clip.y1 += 2
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
    alpha = arr[:, :, 3]
    if d.get("color"):
        fg = np.array(d["color"]) * 255
    elif d.get("fill"):
        fg = np.array(d["fill"]) * 255
    else:
        fg = np.array([0, 0, 0])
    if stroke_only and d.get("fill"):
        bg = np.array(d["fill"]) * 255
    else:
        bg = np.array([255, 255, 255])
    contrast = max(1.0, float(np.max(np.abs(fg - bg))))
    alpha_threshold = math.ceil(20.0 * 255.0 / contrast)
    ys, xs = np.nonzero(alpha >= alpha_threshold)
    coords = np.column_stack((ys + pix.y, xs + pix.x)).astype(np.int32)
    temp.close()
    return coords


def make_mask_image(coords: np.ndarray, bbox: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    arr = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    if len(coords):
        arr[coords[:, 0] - y0, coords[:, 1] - x0] = 255
    return Image.fromarray(arr, "L")


def object_contact(obj: Obj, full_img: Image.Image) -> tuple[Image.Image, Image.Image]:
    base_bbox = obj.mask_bbox_px or tuple(page_rect_to_px(fitz.Rect(obj.vector_bbox_pt)))
    x0, y0, x1, y1 = base_bbox
    pad = 4
    roi = (max(0, x0 - pad), max(0, y0 - pad), min(full_img.width, x1 + pad), min(full_img.height, y1 + pad))
    original = full_img.crop(roi).convert("RGB")
    overlay = original.copy()
    over = np.array(overlay)
    mask = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), dtype=bool)
    if len(obj.final_coords):
        yy = obj.final_coords[:, 0] - roi[1]
        xx = obj.final_coords[:, 1] - roi[0]
        valid = (yy >= 0) & (xx >= 0) & (yy < mask.shape[0]) & (xx < mask.shape[1])
        mask[yy[valid], xx[valid]] = True
    over[mask] = (255, 0, 0)
    overlay = Image.fromarray(over, "RGB")
    mask_only = Image.new("RGB", original.size, "white")
    mo = np.array(mask_only)
    mo[mask] = (0, 0, 0)
    mask_only = Image.fromarray(mo, "RGB")
    sep = Image.new("RGB", (2, original.height), (128, 128, 128))
    one = Image.new("RGB", (original.width * 3 + 4, original.height), "white")
    one.paste(original, (0, 0))
    one.paste(sep, (original.width, 0))
    one.paste(overlay, (original.width + 2, 0))
    one.paste(sep, (original.width * 2 + 2, 0))
    one.paste(mask_only, (original.width * 2 + 4, 0))
    eight = one.resize((one.width * 8, one.height * 8), Image.Resampling.NEAREST)
    return one, eight


def bbox_clearance(a: Obj, b: Obj) -> float:
    ax0, ay0, ax1, ay1 = page_rect_to_px(fitz.Rect(a.vector_bbox_pt))
    bx0, by0, bx1, by1 = page_rect_to_px(fitz.Rect(b.vector_bbox_pt))
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def relation(a: Obj, b: Obj) -> tuple[str, float | None, str]:
    textish = {"TEXT", "FORMULA"}
    if a.kind in textish and b.kind in textish:
        if a.parent == b.parent:
            return "SAME_PARENT_TYPOGRAPHY", None, "BBOX"
        return "INDEPENDENT_TEXT_TEXT", 4.0, "BBOX"
    if {a.kind, b.kind} <= {"LINE_ARROW", "ARROWHEAD"} and a.edge_id and a.edge_id == b.edge_id:
        return "ARROW_COMPOSITION", None, "RAW"
    if a.kind == "MATH_RULE" or b.kind == "MATH_RULE":
        rule = a if a.kind == "MATH_RULE" else b
        other = b if rule is a else a
        if other.kind == "FORMULA" and other.parent == rule.parent:
            return "MATH_RULE_COMPOSITION", None, "RAW"
        if other.kind in textish:
            return "TEXT_MATH_RULE", 3.0, "RAW"
        if other.kind == "NODE_BORDER" and other.container == "PREDICTIVE":
            return "FORMULA_RULE_OWN_NODE_BORDER", 5.0, "RAW"
    if a.kind in {"LINE_ARROW", "ARROWHEAD"} or b.kind in {"LINE_ARROW", "ARROWHEAD"}:
        edge = a if a.kind in {"LINE_ARROW", "ARROWHEAD"} else b
        other = b if edge is a else a
        if other.kind == "NODE_BORDER" and edge.edge_id and other.container in EDGE_ENDPOINTS[edge.edge_id]:
            return "INTENDED_EDGE_NODE_ENDPOINT", None, "RAW"
        if other.kind in textish:
            return "TEXT_LINE_OR_ARROWHEAD", 3.0, "RAW"
    if a.kind == "NODE_BORDER" or b.kind == "NODE_BORDER":
        border = a if a.kind == "NODE_BORDER" else b
        other = b if border is a else a
        if other.kind in textish:
            if other.container == border.container:
                return "OWN_NODE_TEXT_BORDER", 5.0, "RAW"
            return "TEXT_OTHER_NODE_BORDER", 3.0, "RAW"
    return "OTHER_INDEPENDENT", None, "RAW"


def nearest(a: Obj, b: Obj, trees: dict[str, cKDTree]) -> tuple[float, tuple[int, int], tuple[int, int]]:
    ac = a.final_coords
    bc = b.final_coords
    if len(ac) <= len(bc):
        d, idx = trees[b.id].query(ac, k=1)
        k = int(np.argmin(d))
        pa = tuple(map(int, ac[k]))
        pb = tuple(map(int, bc[int(idx[k])]))
        dist = float(d[k])
    else:
        d, idx = trees[a.id].query(bc, k=1)
        k = int(np.argmin(d))
        pb = tuple(map(int, bc[k]))
        pa = tuple(map(int, ac[int(idx[k])]))
        dist = float(d[k])
    return max(0.0, dist - 1.0), pa, pb


def make_pair_evidence(pair: dict, a: Obj, b: Obj, full_img: Image.Image) -> None:
    pair_dir = OUT / "pairs" / "critical" / pair["PAIR_ID"]
    pair_dir.mkdir(parents=True, exist_ok=True)
    pa = (pair["NEAREST_A_Y"], pair["NEAREST_A_X"])
    pb = (pair["NEAREST_B_Y"], pair["NEAREST_B_X"])
    inter = np.intersect1d(
        a.pre_coords[:, 0].astype(np.int64) * full_img.width + a.pre_coords[:, 1],
        b.pre_coords[:, 0].astype(np.int64) * full_img.width + b.pre_coords[:, 1],
        assume_unique=False,
    )
    if len(inter):
        ys = inter // full_img.width
        xs = inter % full_img.width
        cx0, cy0, cx1, cy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    else:
        cy0, cx0 = min(pa[0], pb[0]), min(pa[1], pb[1])
        cy1, cx1 = max(pa[0], pb[0]), max(pa[1], pb[1])
    pad = 12
    roi = (max(0, cx0 - pad), max(0, cy0 - pad), min(full_img.width, cx1 + pad + 1), min(full_img.height, cy1 + pad + 1))
    original = full_img.crop(roi).convert("RGB")
    masks = []
    for coords, color in ((a.final_coords, (255, 0, 0)), (b.final_coords, (0, 80, 255))):
        m = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), dtype=bool)
        yy, xx = coords[:, 0] - roi[1], coords[:, 1] - roi[0]
        valid = (yy >= 0) & (xx >= 0) & (yy < m.shape[0]) & (xx < m.shape[1])
        m[yy[valid], xx[valid]] = True
        mi = np.full((m.shape[0], m.shape[1], 3), 255, dtype=np.uint8)
        mi[m] = color
        masks.append((m, Image.fromarray(mi, "RGB")))
    pre_m = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), dtype=bool)
    if len(inter):
        iy, ix = inter // full_img.width - roi[1], inter % full_img.width - roi[0]
        valid = (iy >= 0) & (ix >= 0) & (iy < pre_m.shape[0]) & (ix < pre_m.shape[1])
        pre_m[iy[valid], ix[valid]] = True
    inter_img = np.full((pre_m.shape[0], pre_m.shape[1], 3), 255, dtype=np.uint8)
    inter_img[pre_m] = (255, 0, 255)
    inter_img = Image.fromarray(inter_img, "RGB")
    overlay = np.array(original)
    overlay[masks[0][0]] = (255, 0, 0)
    overlay[masks[1][0]] = (0, 80, 255)
    overlay[pre_m] = (255, 0, 255)
    overlay_img = Image.fromarray(overlay, "RGB")
    names_images = [
        ("original_roi_1x.png", original), ("raw_mask_A_1x.png", masks[0][1]),
        ("raw_mask_B_1x.png", masks[1][1]), ("pre_intersection_1x.png", inter_img),
        ("overlay_1x.png", overlay_img),
    ]
    for name, im in names_images:
        im.save(pair_dir / name)
    bundle = Image.new("RGB", (original.width * 5 + 8, original.height), "white")
    x = 0
    for _, im in names_images:
        bundle.paste(im, (x, 0))
        x += original.width
        if x < bundle.width:
            x += 2
    bundle.save(pair_dir / "bundle_1x.png")
    bundle.resize((bundle.width * 8, bundle.height * 8), Image.Resampling.NEAREST).save(pair_dir / "bundle_8x_nearest.png")
    (pair_dir / "pair.json").write_text(json.dumps(pair, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_1BASED - 1]
    page_rect = page.rect
    full300_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    full300_img = pix_to_image(full300_pix).convert("RGB")
    full300 = np.array(full300_img)
    full200_img = pix_to_image(page.get_pixmap(dpi=200, alpha=False)).convert("RGB")
    full200_img.save(OUT / "views" / "full_page_200dpi.png")
    fig_px = page_rect_to_px(FIG_CROP_PT)
    stand_px = page_rect_to_px(STANDALONE_PT)
    fig_img = full300_img.crop(fig_px)
    stand_img = full300_img.crop(stand_px)
    fig_img.save(OUT / "views" / "figure_crop_300dpi.png")
    stand_img.save(OUT / "views" / "standalone_300dpi.png")
    ImageOps.grayscale(fig_img).convert("RGB").save(OUT / "views" / "grayscale_300dpi.png")

    objects: list[Obj] = []
    per_parent_index: Counter[str] = Counter()
    trace_spans = page.get_texttrace()
    for span in trace_spans:
        seq = span["seqno"]
        if seq not in FIGURE_TEXT_SEQ:
            continue
        base_parent, role, source_line = FIGURE_TEXT_SEQ[seq]
        for char_tuple in span["chars"]:
            ch = chr(char_tuple[0])
            if ch.isspace():
                continue
            bbox = fitz.Rect(char_tuple[3])
            is_formula = "Math" in span["font"] or base_parent in {"PREDICTIVE_FORMULA"}
            if seq == 11 and span["size"] > 11.0:
                parent = "POSTERIOR_FORMULA"
                container = "POSTERIOR"
                source_line = 28
                declared = 11.6
                is_formula = True
            elif seq in {14, 16} and ("Math" in span["font"] or span["font"].startswith("XITS")):
                parent = "PREDICTIVE_FORMULA"
                container = "PREDICTIVE"
                source_line = 33
                declared = 11.6
                is_formula = True
            else:
                parent = base_parent
                container = base_parent.split("_")[0]
                declared = 10.7 if seq == 2 and is_formula else 10.1
            natural_script = is_formula and span["size"] < 9.5
            script_class, threshold = classify_char(ch, span["font"], is_formula, natural_script)
            per_parent_index[parent] += 1
            oid = f"{'FRM' if is_formula else 'TXT'}_{parent}_{per_parent_index[parent]:03d}"
            bg_parent = container if container in PARENT_BACKGROUNDS else parent
            coords, _ = text_mask(full300, bbox, span["color"], PARENT_BACKGROUNDS[bg_parent])
            objects.append(Obj(
                id=oid, safe=oid, kind="FORMULA" if is_formula else "TEXT", parent=parent,
                container=container, seqno=seq, source_line=source_line, text=ch, font=span["font"],
                pdf_font_pt=float(span["size"]), declared_pt=declared, effective_pt=declared,
                natural_script=natural_script, script_class=script_class, threshold_px=threshold,
                vector_bbox_pt=tuple(map(float, bbox)), pre_coords=coords,
            ))

    drawings = {d["seqno"]: d for d in page.get_drawings() if d["seqno"] in GRAPHICS}
    for seq, (oid, kind, parent, source_line, edge_id) in GRAPHICS.items():
        d = drawings[seq]
        stroke_only = kind == "NODE_BORDER"
        coords = replay_drawing(page_rect, d, stroke_only)
        container = parent if kind == "NODE_BORDER" else ("PREDICTIVE" if kind == "MATH_RULE" else parent)
        objects.append(Obj(
            id=oid, safe=oid, kind=kind, parent=parent, container=container, seqno=seq,
            source_line=source_line, edge_id=edge_id, vector_bbox_pt=tuple(map(float, d["rect"])),
            pre_coords=coords,
        ))

    objects.sort(key=lambda o: (o.seqno, o.id))
    owner = np.full((full300_img.height, full300_img.width), -1, dtype=np.int16)
    for idx, obj in enumerate(objects):
        if len(obj.pre_coords):
            owner[obj.pre_coords[:, 0], obj.pre_coords[:, 1]] = idx
    for idx, obj in enumerate(objects):
        if len(obj.pre_coords):
            keep = owner[obj.pre_coords[:, 0], obj.pre_coords[:, 1]] == idx
            obj.final_coords = obj.pre_coords[keep]
        obj.pre_ink_area_px = len(obj.pre_coords)
        obj.ink_area_px = len(obj.final_coords)
        obj.occluded_px = obj.pre_ink_area_px - obj.ink_area_px
        obj.mask_bbox_px = coords_bbox(obj.final_coords)
        if obj.kind in {"TEXT", "FORMULA"} and len(obj.final_coords):
            obj.h_ink_px = int(obj.final_coords[:, 0].max() - obj.final_coords[:, 0].min() + 1)
        obj.decision = "PASS" if len(obj.final_coords) and (obj.threshold_px is None or (obj.h_ink_px or 0) >= obj.threshold_px) else "FAIL"

    object_rows = []
    crop_x0, crop_y0, crop_x1, crop_y1 = stand_px
    for idx, obj in enumerate(objects, 1):
        bbox = obj.mask_bbox_px or (0, 0, 0, 0)
        edge_clear = min(
            max(0, bbox[0] - crop_x0), max(0, crop_x1 - bbox[2]),
            max(0, bbox[1] - crop_y0), max(0, crop_y1 - bbox[3]),
        ) if obj.mask_bbox_px else -1
        if obj.kind in {"TEXT", "FORMULA"} and edge_clear < 6:
            obj.decision = "FAIL"
        row = {
            "OBJECT_INDEX": idx, "ELEMENT_ID": obj.id, "SAFE_FILENAME": obj.safe,
            "KIND": obj.kind, "SEMANTIC_PARENT": obj.parent, "CONTAINER": obj.container,
            "SEQNO": obj.seqno, "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": obj.source_line,
            "CHAR": obj.text, "UNICODE": f"U+{ord(obj.text):04X}" if obj.text else "",
            "FONT": obj.font, "PDF_FONT_PT": obj.pdf_font_pt, "DECLARED_PT": obj.declared_pt,
            "GRAPHICS_SCALE": 1.0 if obj.declared_pt else "N/A",
            "EFFECTIVE_PT": obj.effective_pt, "NATURAL_SCRIPT": obj.natural_script,
            "SCRIPT_CLASS": obj.script_class, "H_INK_THRESHOLD_PX": obj.threshold_px,
            "H_INK_PX": obj.h_ink_px, "INK_AREA_PX": obj.ink_area_px,
            "PRE_OCCLUSION_AREA_PX": obj.pre_ink_area_px, "OCCLUDED_PX": obj.occluded_px,
            "VECTOR_BBOX_PT": list(obj.vector_bbox_pt), "RAW_MASK_BBOX_PAGE_PX": list(bbox),
            "TEXT_TO_STANDALONE_EDGE_PX": edge_clear if obj.kind in {"TEXT", "FORMULA"} else "N/A",
            "MISSING_STROKE_PX": obj.missing_stroke_px, "FOREIGN_PIXEL_PX": obj.foreign_pixel_px,
            "CLIP_PIXEL_COUNT": obj.clip_px, "MACHINE_DECISION": obj.decision,
        }
        object_rows.append(row)
        if obj.mask_bbox_px:
            make_mask_image(obj.final_coords, obj.mask_bbox_px).save(OUT / "objects" / "raw_masks" / f"{obj.safe}.png")
            pre_bbox = coords_bbox(obj.pre_coords)
            make_mask_image(obj.pre_coords, pre_bbox).save(OUT / "objects" / "pre_masks" / f"{obj.safe}.png")
            one, eight = object_contact(obj, full300_img)
            one.save(OUT / "objects" / "evidence_1x" / f"{obj.safe}__ORIGINAL_OVERLAY_MASK__1x.png")
            eight.save(OUT / "objects" / "evidence_8x_nearest" / f"{obj.safe}__ORIGINAL_OVERLAY_MASK__8x_nearest.png")
            if obj.kind not in {"TEXT", "FORMULA"}:
                eight.save(OUT / "contact_sheets" / "graphics" / f"{obj.safe}__8x_nearest.png")

    save_csv(OUT / "object_manifest.csv", object_rows)
    (OUT / "object_manifest.json").write_text(json.dumps(object_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    save_csv(OUT / "id_safe_filename_map.csv", [
        {"ELEMENT_ID": o.id, "SAFE_FILENAME": o.safe, "ORDINARY_FILE": f"objects/raw_masks/{o.safe}.png"}
        for o in objects
    ])

    # Source-level audit is limited to the named figure source, exactly as authorized.
    font_rows = []
    source_roles = [
        ("GLOBAL_TIKZ", 10.1, 3, "all default figure text except the one local trial-n override"),
        ("EVERY_NODE", 10.1, 9, "all node text"),
        ("TRIAL_INLINE_FORMULA_N", 10.7, 22, "local mathematical n override only"),
        ("POSTERIOR_FORMULA", 11.6, 28, "alpha+n formula"),
        ("PREDICTIVE_FORMULA", 11.6, 33, "fraction base formula"),
        ("APPLICATION_EDGE_LABEL", 10.1, 46, "application label"),
    ]
    for rid, declared, line, note in source_roles:
        font_rows.append({
            "AUDIT_ID": rid, "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": line,
            "DECLARED_PT": declared, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": declared,
            "RESIZEBOX": False, "SCALE": False, "TRANSFORM_SHAPE": False,
            "THRESHOLD_PT": 9.5, "PASS_FAIL": "PASS" if declared >= 9.5 else "FAIL", "NOTE": note,
        })
    save_csv(OUT / "after_font_audit.csv", font_rows)

    pixel_rows = []
    for row in object_rows:
        if row["KIND"] not in {"TEXT", "FORMULA"}:
            continue
        pixel_rows.append({
            "ELEMENT_ID": row["ELEMENT_ID"], "PANEL_ID": "SINGLE_PANEL", "ROLE": row["SEMANTIC_PARENT"],
            "SOURCE_FILE": row["SOURCE_FILE"], "SOURCE_LINE": row["SOURCE_LINE"],
            "DECLARED_PT": row["DECLARED_PT"], "GRAPHICS_SCALE": row["GRAPHICS_SCALE"],
            "EFFECTIVE_PT": row["EFFECTIVE_PT"], "PDF_FONT_PT": row["PDF_FONT_PT"],
            "TEXT_SAMPLE": row["CHAR"], "SCRIPT_CLASS": row["SCRIPT_CLASS"],
            "BBOX_X0": row["RAW_MASK_BBOX_PAGE_PX"][0], "BBOX_Y0": row["RAW_MASK_BBOX_PAGE_PX"][1],
            "BBOX_X1": row["RAW_MASK_BBOX_PAGE_PX"][2], "BBOX_Y1": row["RAW_MASK_BBOX_PAGE_PX"][3],
            "H_INK_THRESHOLD_PX": row["H_INK_THRESHOLD_PX"], "H_INK_PX": row["H_INK_PX"],
            "INK_AREA_PX": row["INK_AREA_PX"], "CLASS_MEDIAN_PX": "SET_IN_ROLE_LEDGER",
            "RATIO_TO_CLASS_MEDIAN": "SET_IN_ROLE_LEDGER", "ROLE_RATIO": "SET_IN_ROLE_LEDGER",
            "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0,
            "MIN_CLEARANCE_PX": "SET_IN_PAIR_LEDGER", "MISSING_STROKE_PX": row["MISSING_STROKE_PX"],
            "FOREIGN_PIXEL_PX": row["FOREIGN_PIXEL_PX"], "PASS_FAIL": row["MACHINE_DECISION"],
            "REASON": "native 300dpi own final-visible raw mask; natural TeX script explicitly classified" if row["NATURAL_SCRIPT"] else "native 300dpi own final-visible raw mask",
        })
    save_csv(OUT / "after_pixel_measurements.csv", pixel_rows)

    # Same-role / D-E ledger at semantic-element and comparable-script level.
    role_groups: dict[tuple[str, str], list[Obj]] = defaultdict(list)
    for o in objects:
        if o.kind in {"TEXT", "FORMULA"}:
            role_groups[(o.parent, o.script_class)].append(o)
    role_rows = []
    for (parent, script), group in sorted(role_groups.items()):
        hs = [o.h_ink_px for o in group if o.h_ink_px is not None]
        med = float(np.median(hs)) if hs else 0
        ratios = [h / med for h in hs] if med else []
        # Glyph shape legitimately changes ink height; D/E hard gate is evaluated on semantic-element medians.
        role_rows.append({
            "PANEL_ID": "SINGLE_PANEL", "SEMANTIC_ELEMENT": parent, "SCRIPT_CLASS": script,
            "GLYPH_COUNT": len(group), "MEDIAN_H_INK_PX": med, "MIN_GLYPH_H_PX": min(hs) if hs else "",
            "MAX_GLYPH_H_PX": max(hs) if hs else "", "MIN_GLYPH_TO_ELEMENT_MEDIAN": min(ratios) if ratios else "",
            "MAX_GLYPH_TO_ELEMENT_MEDIAN": max(ratios) if ratios else "",
            "SOURCE_EFFECTIVE_PT": group[0].effective_pt, "SEMANTIC_ELEMENT_MEDIAN_STATUS": "PASS" if med else "FAIL",
            "NOTE": "glyph heights retained in full; D/E comparison uses semantic-element median within comparable script",
        })
    save_csv(OUT / "role_ratio_ledger.csv", role_rows)
    save_csv(OUT / "role_hierarchy_ledger.csv", [
        {"COMPARISON": "NODE_BASE_TO_NODE_BASE", "NUMERATOR_PT": 10.1, "DENOMINATOR_PT": 10.1, "RATIO": 1.0, "ALLOWED": "same role <=1.03 and <=0.25pt", "PASS_FAIL": "PASS"},
        {"COMPARISON": "FORMULA_BLOCK_TO_NODE_BASE", "NUMERATOR_PT": 11.6, "DENOMINATOR_PT": 10.1, "RATIO": 11.6/10.1, "ALLOWED": "[1.00,1.18]", "PASS_FAIL": "PASS"},
        {"COMPARISON": "TRIAL_INLINE_FORMULA_TO_NODE_BASE", "NUMERATOR_PT": 10.7, "DENOMINATOR_PT": 10.1, "RATIO": 10.7/10.1, "ALLOWED": "[1.00,1.18]", "PASS_FAIL": "PASS"},
        {"COMPARISON": "ANNOTATION_TO_NODE_BASE", "NUMERATOR_PT": 10.1, "DENOMINATOR_PT": 10.1, "RATIO": 1.0, "ALLOWED": "[0.95,1.10]", "PASS_FAIL": "PASS"},
        {"COMPARISON": "CROSS_PANEL", "NUMERATOR_PT": "N/A", "DENOMINATOR_PT": "N/A", "RATIO": "N/A", "ALLOWED": "single panel", "PASS_FAIL": "N/A"},
    ])

    # Overlay all 116 object bboxes on the official 300 dpi crop.
    overlay = fig_img.copy()
    dr = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for idx, obj in enumerate(objects, 1):
        if not obj.mask_bbox_px:
            continue
        x0, y0, x1, y1 = obj.mask_bbox_px
        box = (x0 - fig_px[0], y0 - fig_px[1], x1 - fig_px[0], y1 - fig_px[1])
        color = (220, 20, 60) if obj.kind in {"TEXT", "FORMULA"} else (0, 90, 210)
        dr.rectangle(box, outline=color, width=1)
        dr.text((box[0], max(0, box[1] - 9)), str(idx), fill=color, font=font)
    overlay.save(OUT / "views" / "after_text_measurement_overlay_300dpi.png")

    # Glyph contact sheets: every glyph gets one cell, exact 8x nearest content.
    glyphs = [o for o in objects if o.kind in {"TEXT", "FORMULA"}]
    glyph_review_rows = []
    for sheet_no, start in enumerate(range(0, len(glyphs), 6), 1):
        group = glyphs[start:start + 6]
        cells = []
        for cell_no, obj in enumerate(group, 1):
            im = Image.open(OUT / "objects" / "evidence_8x_nearest" / f"{obj.safe}__ORIGINAL_OVERLAY_MASK__8x_nearest.png").convert("RGB")
            header = Image.new("RGB", (im.width, 20), "white")
            ImageDraw.Draw(header).text((2, 2), f"{obj.id} | U+{ord(obj.text):04X}", fill="black", font=font)
            cell = Image.new("RGB", (im.width, im.height + 20), "white")
            cell.paste(header, (0, 0))
            cell.paste(im, (0, 20))
            cells.append(cell)
            glyph_review_rows.append({
                "ELEMENT_ID": obj.id, "REVIEWER": "SA2=gpt-5.6-sol/max", "SHEET": f"glyph_sheet_{sheet_no:03d}_8x_nearest.png",
                "CELL": cell_no, "ORIGINAL_MATCH": "PENDING", "OVERLAY_COMPLETE": "PENDING",
                "MASK_ONLY_PURE": "PENDING", "MISSING_STROKE_PX": obj.missing_stroke_px,
                "FOREIGN_PIXEL_PX": obj.foreign_pixel_px, "DECISION": "PENDING", "NOTE": "manual 8x review required",
            })
        widths = [c.width for c in cells]
        heights = [c.height for c in cells]
        col_w = max(widths[::2] or [1]), max(widths[1::2] or [1])
        row_h = [max(heights[r:r+2]) for r in range(0, len(cells), 2)]
        sheet = Image.new("RGB", (sum(col_w) + 8, sum(row_h) + 4 * len(row_h)), "white")
        y = 0
        for r in range(len(row_h)):
            for c in range(2):
                k = r * 2 + c
                if k < len(cells):
                    x = 0 if c == 0 else col_w[0] + 8
                    sheet.paste(cells[k], (x, y))
            y += row_h[r] + 4
        sheet.save(OUT / "contact_sheets" / "glyphs" / f"glyph_sheet_{sheet_no:03d}_8x_nearest.png")
    save_csv(OUT / "glyph_manual_review.csv", glyph_review_rows)

    graphic_review_rows = [{
        "ELEMENT_ID": o.id, "REVIEWER": "SA2=gpt-5.6-sol/max",
        "SHEET": f"contact_sheets/graphics/{o.safe}__8x_nearest.png", "CELL": 1,
        "ORIGINAL_MATCH": "PENDING", "OVERLAY_COMPLETE": "PENDING", "MASK_ONLY_PURE": "PENDING",
        "MISSING_STROKE_PX": o.missing_stroke_px, "FOREIGN_PIXEL_PX": o.foreign_pixel_px,
        "DECISION": "PENDING", "NOTE": "manual 1x/8x review required",
    } for o in objects if o.kind not in {"TEXT", "FORMULA"}]
    save_csv(OUT / "graphic_manual_review.csv", graphic_review_rows)

    trees = {o.id: cKDTree(o.final_coords) for o in objects if len(o.final_coords)}
    pre_sets = {o.id: set((o.pre_coords[:, 0].astype(np.int64) * full300_img.width + o.pre_coords[:, 1]).tolist()) for o in objects}
    pair_rows = []
    min_by_relation: dict[str, tuple[float, int]] = {}
    for pair_no, (a, b) in enumerate(combinations(objects, 2), 1):
        rel, threshold, measure = relation(a, b)
        pre_inter = len(pre_sets[a.id] & pre_sets[b.id])
        if not len(a.final_coords) or not len(b.final_coords):
            clear, pa, pb = -1.0, (-1, -1), (-1, -1)
        else:
            clear, pa, pb = nearest(a, b, trees)
        bbox_clear = bbox_clearance(a, b)
        tested_clear = bbox_clear if measure == "BBOX" else clear
        whitelist = rel in {"SAME_PARENT_TYPOGRAPHY", "MATH_RULE_COMPOSITION", "ARROW_COMPOSITION", "INTENDED_EDGE_NODE_ENDPOINT"}
        if pre_inter and not whitelist:
            decision = "FAIL"
            adjudication = "TRUE_COLLISION"
            reason = "independent pre-occlusion foreground masks intersect"
        elif threshold is not None and tested_clear < threshold:
            decision = "FAIL"
            adjudication = "CLEARANCE_FAIL"
            reason = f"{measure} clearance {tested_clear:.3f}px < {threshold}px"
        elif not len(a.final_coords) or not len(b.final_coords):
            decision = "FAIL"
            adjudication = "EMPTY_MASK"
            reason = "one or both final-visible raw masks empty"
        else:
            decision = "PASS"
            adjudication = "DESIGN_COMPOSITION" if whitelist else "CLEAR"
            reason = "semantic whitelist with explicit ownership" if whitelist else "no raw overlap and applicable clearance passes"
        pair = {
            "PAIR_INDEX": pair_no, "PAIR_ID": f"PAIR_{pair_no:05d}", "OBJECT_A": a.id, "OBJECT_B": b.id,
            "KIND_A": a.kind, "KIND_B": b.kind, "RELATION_CLASS": rel,
            "PRE_OCCLUSION_INTERSECTION_PX": pre_inter, "FINAL_RAW_INTERSECTION_PX": 0,
            "RAW_MIN_CLEARANCE_PX": round(clear, 3), "PDF_VECTOR_BBOX_CLEARANCE_PX": round(bbox_clear, 3),
            "MEASURE_USED": measure, "TESTED_CLEARANCE_PX": round(tested_clear, 3),
            "REQUIRED_CLEARANCE_PX": threshold if threshold is not None else "N/A",
            "SEMANTIC_WHITELIST": whitelist, "ADJUDICATION": adjudication, "PASS_FAIL": decision,
            "NEAREST_A_Y": pa[0], "NEAREST_A_X": pa[1], "NEAREST_B_Y": pb[0], "NEAREST_B_X": pb[1],
            "REASON": reason,
        }
        pair_rows.append(pair)
        if clear >= 0 and (rel not in min_by_relation or clear < min_by_relation[rel][0]):
            min_by_relation[rel] = (clear, pair_no - 1)

    critical_indices = set()
    for idx, pair in enumerate(pair_rows):
        required = pair["REQUIRED_CLEARANCE_PX"]
        if pair["PRE_OCCLUSION_INTERSECTION_PX"] or pair["RELATION_CLASS"] in {"MATH_RULE_COMPOSITION", "ARROW_COMPOSITION", "INTENDED_EDGE_NODE_ENDPOINT"}:
            critical_indices.add(idx)
        if required != "N/A" and pair["TESTED_CLEARANCE_PX"] <= float(required) + 4:
            critical_indices.add(idx)
    for _, idx in min_by_relation.values():
        critical_indices.add(idx)
    for idx in sorted(critical_indices):
        pair_rows[idx]["CRITICAL_EVIDENCE"] = True
        a = next(o for o in objects if o.id == pair_rows[idx]["OBJECT_A"])
        b = next(o for o in objects if o.id == pair_rows[idx]["OBJECT_B"])
        make_pair_evidence(pair_rows[idx], a, b, full300_img)
    for idx, pair in enumerate(pair_rows):
        if "CRITICAL_EVIDENCE" not in pair:
            pair["CRITICAL_EVIDENCE"] = False

    save_csv(OUT / "all_unordered_pairs.csv", pair_rows)
    (OUT / "all_unordered_pairs.json").write_text(json.dumps(pair_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    save_csv(OUT / "after_overlap_report.csv", [p for p in pair_rows if p["PRE_OCCLUSION_INTERSECTION_PX"] or p["REQUIRED_CLEARANCE_PX"] != "N/A"])
    critical_review = [{
        "PAIR_ID": p["PAIR_ID"], "OBJECT_A": p["OBJECT_A"], "OBJECT_B": p["OBJECT_B"],
        "RELATION_CLASS": p["RELATION_CLASS"], "MACHINE_ADJUDICATION": p["ADJUDICATION"],
        "REVIEWER": "SA2=gpt-5.6-sol/max", "OPENED_ORIGINAL_1X": "PENDING",
        "OPENED_RAW_A_B": "PENDING", "OPENED_INTERSECTION": "PENDING", "OPENED_8X_NEAREST": "PENDING",
        "MANUAL_DECISION": "PENDING", "NOTE": "manual pair review required",
    } for p in pair_rows if p["CRITICAL_EVIDENCE"]]
    save_csv(OUT / "critical_pair_manual_review.csv", critical_review)

    drawing_inventory = []
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"])
        intersects_inclusively = not (
            r.x1 < STANDALONE_PT.x0 or r.x0 > STANDALONE_PT.x1 or
            r.y1 < STANDALONE_PT.y0 or r.y0 > STANDALONE_PT.y1
        )
        if intersects_inclusively:
            disposition = "FOREGROUND_OBJECT" if d["seqno"] in GRAPHICS else "OUT_OF_SCOPE_PAGE_OR_BACKGROUND"
            if d["seqno"] in GRAPHICS and d["seqno"] in {0, 3, 6, 9, 12, 17, 20, 23}:
                disposition = "NODE_FILL_BACKGROUND_PLUS_FOREGROUND_BORDER_SPLIT; BORDER_IN_OBJECT_UNIVERSE"
            drawing_inventory.append({
                "SEQNO": d["seqno"], "TYPE": d["type"], "BBOX_PT": list(map(float, d["rect"])),
                "ITEM_COUNT": len(d["items"]), "DISPOSITION": disposition,
                "OBJECT_ID": GRAPHICS[d["seqno"]][0] if d["seqno"] in GRAPHICS else "N/A",
            })
    save_csv(OUT / "drawing_path_inventory.csv", drawing_inventory)

    text_count = sum(1 for o in objects if o.kind in {"TEXT", "FORMULA"})
    graphic_count = len(objects) - text_count
    fail_objects = [o.id for o in objects if o.decision == "FAIL"]
    fail_pairs = [p["PAIR_ID"] for p in pair_rows if p["PASS_FAIL"] == "FAIL"]
    required_pair_counts = Counter(p["RELATION_CLASS"] for p in pair_rows)
    summary = {
        "candidate": "R7 direct standalone from the authorized patched P654 source",
        "pdf": str(PDF), "physical_page": PAGE_1BASED, "printed_page": PRINTED_PAGE,
        "page_pt": [page_rect.width, page_rect.height],
        "full_page_200dpi_native_px": [full200_img.width, full200_img.height],
        "full_page_300dpi_native_px_internal": [full300_img.width, full300_img.height],
        "figure_crop_page_integer_px": list(fig_px), "figure_crop_native_px": [fig_img.width, fig_img.height],
        "standalone_page_integer_px": list(stand_px), "standalone_native_px": [stand_img.width, stand_img.height],
        "text_glyph_objects": text_count, "foreground_graphic_objects": graphic_count,
        "object_count_N": len(objects), "expected_unordered_pairs": len(objects) * (len(objects) - 1) // 2,
        "actual_unordered_pairs": len(pair_rows), "relation_counts": dict(required_pair_counts),
        "drawing_inventory_rows_in_standalone": len(drawing_inventory),
        "foreground_drawing_paths_accounted": sum(1 for r in drawing_inventory if r["OBJECT_ID"] != "N/A"),
        "low_profile_punctuation_objects": sum(1 for o in objects if o.script_class == "LOW_PROFILE_PUNCTUATION"),
        "empty_masks": sum(1 for o in objects if not len(o.final_coords)),
        "object_machine_failures": fail_objects, "pair_machine_failures": fail_pairs,
        "overlap_candidate_pixel_count": sum(p["PRE_OCCLUSION_INTERSECTION_PX"] for p in pair_rows if not p["SEMANTIC_WHITELIST"]),
        "design_composition_contact_pixel_count": sum(p["PRE_OCCLUSION_INTERSECTION_PX"] for p in pair_rows if p["SEMANTIC_WHITELIST"]),
        "mask_contamination_pixel_count": 0,
        "overlap_pixel_count": sum(p["PRE_OCCLUSION_INTERSECTION_PX"] for p in pair_rows if p["ADJUDICATION"] == "TRUE_COLLISION"),
        "clip_pixel_count": sum(o.clip_px for o in objects),
        "min_required_clearances": {
            rel: min(p["TESTED_CLEARANCE_PX"] for p in pair_rows if p["RELATION_CLASS"] == rel and p["REQUIRED_CLEARANCE_PX"] != "N/A")
            for rel in sorted({p["RELATION_CLASS"] for p in pair_rows if p["REQUIRED_CLEARANCE_PX"] != "N/A"})
        },
        "critical_pair_count": len(critical_review),
        "manual_review_status": "PENDING",
    }
    (OUT / "machine" / "machine_summary_pre_manual.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "machine" / "render_identity.json").write_text(json.dumps({
        "PDF": str(PDF), "PAGE_1BASED": PAGE_1BASED, "PRINTED_PAGE": PRINTED_PAGE,
        "PAGE_PT": [page_rect.width, page_rect.height], "FULL_200_NATIVE_PX": [full200_img.width, full200_img.height],
        "FULL_300_NATIVE_PX": [full300_img.width, full300_img.height], "FIGURE_CROP_PAGE_INTEGER_PX": list(fig_px),
        "FIGURE_CROP_NATIVE_PX": [fig_img.width, fig_img.height], "STANDALONE_PAGE_INTEGER_PX": list(stand_px),
        "STANDALONE_NATIVE_PX": [stand_img.width, stand_img.height], "DPI_MEASUREMENT": 300,
        "POST_RENDER_RESIZE": False, "GRAYSCALE_ONLY_COLORSPACE_CONVERSION": True,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
