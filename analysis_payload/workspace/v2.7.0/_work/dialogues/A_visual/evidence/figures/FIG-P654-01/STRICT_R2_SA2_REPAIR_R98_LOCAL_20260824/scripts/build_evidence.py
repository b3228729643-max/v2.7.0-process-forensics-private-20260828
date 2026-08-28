from __future__ import annotations

import csv
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label as component_label
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R2_SA2_REPAIR_R98_LOCAL_20260824")
PDF = ROOT / "build" / "page" / "v260_FIG-P654-01_page.pdf"
PHYSICAL_PAGE = 1
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0

# Strict final-pixel union of the TikZ picture on the local native 300 dpi page.
# The rectangle includes a five-native-pixel safety pad around every visible path.
CROP = (310, 428, 2245, 1032)
CROP_X0, CROP_Y0, CROP_X1, CROP_Y1 = CROP
CW, CH = CROP_X1 - CROP_X0, CROP_Y1 - CROP_Y0
CLIP_PT = fitz.Rect(CROP_X0 / SCALE, CROP_Y0 / SCALE, CROP_X1 / SCALE, CROP_Y1 / SCALE)

RENDERS = ROOT / "renders"
INVENTORY = ROOT / "inventory"
GLYPHS = ROOT / "glyphs"
GRAPHICS = ROOT / "graphics"
CONTACTS = ROOT / "contacts"
CRITICAL = ROOT / "critical"
LEDGERS = ROOT / "ledgers"
REPORTS = ROOT / "reports"
for directory in (RENDERS, INVENTORY, GLYPHS, GRAPHICS, CONTACTS, CRITICAL, LEDGERS, REPORTS):
    directory.mkdir(parents=True, exist_ok=True)

NODE_SEQ = {4, 7, 10, 13, 16, 21, 24, 27}
GRAPHIC_SPECS = {
    4: ("NODE_BORDER_TRIAL", "NODE_BORDER", "trial", "trial rounded border; fill excluded as semantic background"),
    7: ("NODE_BORDER_GAMMA", "NODE_BORDER", "gamma", "Gamma/Beta rounded border; fill excluded as semantic background"),
    10: ("NODE_BORDER_FAMILIES", "NODE_BORDER", "families", "likelihood/prior rounded border; fill excluded as semantic background"),
    13: ("NODE_BORDER_POSTERIOR", "NODE_BORDER", "posterior", "posterior rounded border; white fill excluded as semantic background"),
    16: ("NODE_BORDER_PREDICTIVE", "NODE_BORDER", "predictive", "predictive rounded border; white fill excluded as semantic background"),
    19: ("MATH_RULE_PREDICTIVE_FRACTION", "MATH_RULE", "predictive_formula", "fraction rule belonging to predictive formula"),
    21: ("NODE_BORDER_SIMPLEX", "NODE_BORDER", "simplex", "simplex explanation rounded border; fill excluded as semantic background"),
    24: ("NODE_BORDER_MOM", "NODE_BORDER", "mom", "moment explanation rounded border; fill excluded as semantic background"),
    27: ("NODE_BORDER_LDA", "NODE_BORDER", "lda", "application rounded border; fill excluded as semantic background"),
    30: ("ARROW_TRIAL_FAMILIES_SHAFT", "LINE_ARROW", "edge_trial_families", "main-chain directed edge shaft"),
    31: ("ARROW_TRIAL_FAMILIES_HEAD", "ARROWHEAD", "edge_trial_families", "main-chain directed edge head"),
    33: ("ARROW_GAMMA_FAMILIES_SHAFT", "LINE_ARROW", "edge_gamma_families", "main-chain directed edge shaft"),
    34: ("ARROW_GAMMA_FAMILIES_HEAD", "ARROWHEAD", "edge_gamma_families", "main-chain directed edge head"),
    36: ("ARROW_FAMILIES_POSTERIOR_SHAFT", "LINE_ARROW", "edge_families_posterior", "main-chain directed edge shaft"),
    37: ("ARROW_FAMILIES_POSTERIOR_HEAD", "ARROWHEAD", "edge_families_posterior", "main-chain directed edge head"),
    39: ("ARROW_POSTERIOR_PREDICTIVE_SHAFT", "LINE_ARROW", "edge_posterior_predictive", "main-chain directed edge shaft"),
    40: ("ARROW_POSTERIOR_PREDICTIVE_HEAD", "ARROWHEAD", "edge_posterior_predictive", "main-chain directed edge head"),
    42: ("INTERP_FAMILIES_SIMPLEX", "LINE_ARROW", "edge_families_simplex", "undirected interpretation edge"),
    43: ("INTERP_POSTERIOR_MOM", "LINE_ARROW", "edge_posterior_mom", "undirected interpretation edge"),
    44: ("APPLICATION_PREDICTIVE_LDA_SHAFT", "LINE_ARROW", "edge_predictive_lda", "dashed directed application edge shaft"),
    45: ("APPLICATION_PREDICTIVE_LDA_HEAD", "ARROWHEAD", "edge_predictive_lda", "dashed directed application edge head"),
}

# Source-level explicit contacts. All are pair-specific; no category exemption is used.
INTENTIONAL_CONTACT_NAMES = {
    frozenset(("ARROW_TRIAL_FAMILIES_SHAFT", "ARROW_TRIAL_FAMILIES_HEAD")),
    frozenset(("ARROW_GAMMA_FAMILIES_SHAFT", "ARROW_GAMMA_FAMILIES_HEAD")),
    frozenset(("ARROW_FAMILIES_POSTERIOR_SHAFT", "ARROW_FAMILIES_POSTERIOR_HEAD")),
    frozenset(("ARROW_POSTERIOR_PREDICTIVE_SHAFT", "ARROW_POSTERIOR_PREDICTIVE_HEAD")),
    frozenset(("APPLICATION_PREDICTIVE_LDA_SHAFT", "APPLICATION_PREDICTIVE_LDA_HEAD")),
    # Each edge endpoint is intentionally incident on the relevant node border.
    # These are exact source-semantic pairs, not class-wide exemptions.
    frozenset(("NODE_BORDER_TRIAL", "ARROW_TRIAL_FAMILIES_SHAFT")),
    frozenset(("NODE_BORDER_GAMMA", "ARROW_GAMMA_FAMILIES_SHAFT")),
    frozenset(("NODE_BORDER_FAMILIES", "ARROW_TRIAL_FAMILIES_HEAD")),
    frozenset(("NODE_BORDER_FAMILIES", "ARROW_GAMMA_FAMILIES_HEAD")),
    frozenset(("NODE_BORDER_FAMILIES", "ARROW_FAMILIES_POSTERIOR_SHAFT")),
    frozenset(("NODE_BORDER_POSTERIOR", "ARROW_FAMILIES_POSTERIOR_HEAD")),
    frozenset(("NODE_BORDER_FAMILIES", "INTERP_FAMILIES_SIMPLEX")),
    frozenset(("NODE_BORDER_POSTERIOR", "ARROW_POSTERIOR_PREDICTIVE_SHAFT")),
    frozenset(("NODE_BORDER_POSTERIOR", "INTERP_POSTERIOR_MOM")),
    frozenset(("NODE_BORDER_PREDICTIVE", "ARROW_POSTERIOR_PREDICTIVE_HEAD")),
    frozenset(("NODE_BORDER_PREDICTIVE", "APPLICATION_PREDICTIVE_LDA_SHAFT")),
    frozenset(("NODE_BORDER_SIMPLEX", "INTERP_FAMILIES_SIMPLEX")),
    frozenset(("NODE_BORDER_MOM", "INTERP_POSTERIOR_MOM")),
    frozenset(("NODE_BORDER_LDA", "APPLICATION_PREDICTIVE_LDA_HEAD")),
}


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb_int_to_tuple(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def color_float_to_tuple(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(255 * float(x))) for x in value)


def shifted_point(p: fitz.Point) -> fitz.Point:
    return fitz.Point(p.x - CLIP_PT.x0, p.y - CLIP_PT.y0)


def add_drawing(shape: fitz.Shape, drawing: dict) -> None:
    items = drawing["items"]
    # Filled TikZ arrowheads arrive as one closed, contiguous line polygon.  Calling
    # draw_line once per edge creates independent subpaths and loses the interior fill,
    # which was the exact source of the superseded arrow fragments in node masks.
    # Preserve the PDF path as one polyline whenever every operation is a line.
    if items and all(item[0] == "l" for item in items):
        points = [shifted_point(items[0][1])]
        points.extend(shifted_point(item[2]) for item in items)
        shape.draw_polyline(points)
        return
    for item in items:
        op = item[0]
        if op == "l":
            shape.draw_line(shifted_point(item[1]), shifted_point(item[2]))
        elif op == "c":
            shape.draw_bezier(
                shifted_point(item[1]), shifted_point(item[2]),
                shifted_point(item[3]), shifted_point(item[4]),
            )
        elif op == "re":
            rect = item[1]
            shape.draw_rect(fitz.Rect(rect.x0 - CLIP_PT.x0, rect.y0 - CLIP_PT.y0,
                                     rect.x1 - CLIP_PT.x0, rect.y1 - CLIP_PT.y0))
        elif op == "qu":
            quad = item[1]
            shape.draw_quad(fitz.Quad(*(shifted_point(x) for x in quad)))
        else:
            raise RuntimeError(f"Unsupported drawing operator: {op}")


def render_synthetic(drawings: list[tuple[dict, str]], output: Path | None = None) -> np.ndarray:
    """Render selected paths on a crop-sized white page using MuPDF at the native grid.

    mode is 'fill', 'stroke', 'both', 'actual_stroke', 'actual_both', or
    'background'.  Black modes are diagnostic geometry only.  Evidence masks use
    actual colors over the exact fill-only background so the 20/255 antialias
    footprint matches the frozen local candidate render rather than expanding around dark replay.
    """
    doc = fitz.open()
    page = doc.new_page(width=CW / SCALE, height=CH / SCALE)
    for drawing, mode in drawings:
        shape = page.new_shape()
        add_drawing(shape, drawing)
        if mode == "background":
            color, fill, width = None, drawing.get("fill"), 0
        elif mode == "fill":
            color, fill, width = None, (0, 0, 0), 0
        elif mode == "stroke":
            color, fill, width = (0, 0, 0), None, drawing.get("width") or 0.5
        elif mode == "actual_stroke":
            color, fill, width = drawing.get("color"), None, drawing.get("width") or 0.5
        elif mode == "actual_both":
            color = drawing.get("color")
            fill = drawing.get("fill")
            width = drawing.get("width") or 0.5
        else:
            color, fill, width = (0, 0, 0), (0, 0, 0), drawing.get("width") or 0.5
        line_cap = drawing.get("lineCap", 0)
        if isinstance(line_cap, (list, tuple)):
            line_cap = max(line_cap) if line_cap else 0
        shape.finish(
            color=color,
            fill=fill,
            width=width,
            lineCap=int(line_cap or 0),
            lineJoin=int(round(drawing.get("lineJoin") or 0)),
            dashes=drawing.get("dashes"),
            closePath=("f" in str(drawing.get("type", ""))),
        )
        shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3].copy()
    if arr.shape[:2] != (CH, CW):
        raise RuntimeError(f"Synthetic raster grid mismatch: {arr.shape[:2]} != {(CH, CW)}")
    if output:
        Image.fromarray(arr).save(output)
    doc.close()
    return arr


def mode_rgb(arr: np.ndarray) -> np.ndarray:
    flat = arr.reshape(-1, 3)
    packed = (flat[:, 0].astype(np.uint32) << 16) | (flat[:, 1].astype(np.uint32) << 8) | flat[:, 2]
    value = int(np.bincount(packed).argmax())
    return np.array(rgb_int_to_tuple(value), dtype=np.int16)


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def expand_bbox(bbox: tuple[int, int, int, int], pad: int = 4) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return max(0, x0 - pad), max(0, y0 - pad), min(CW, x1 + pad), min(CH, y1 + pad)


def overlay_roi(original: np.ndarray, mask: np.ndarray, roi: tuple[int, int, int, int]) -> tuple[Image.Image, Image.Image, Image.Image]:
    x0, y0, x1, y1 = roi
    source = original[y0:y1, x0:x1].copy()
    local = mask[y0:y1, x0:x1]
    over = source.copy()
    red = np.array([255, 0, 0], dtype=np.float32)
    over[local] = np.clip(0.30 * over[local].astype(np.float32) + 0.70 * red, 0, 255).astype(np.uint8)
    only = np.full_like(source, 255)
    only[local] = 0
    return Image.fromarray(source), Image.fromarray(over), Image.fromarray(only)


def save_three_views(prefix: Path, original: np.ndarray, mask: np.ndarray,
                     roi: tuple[int, int, int, int], label: str) -> tuple[str, str, str, str]:
    a, b, c = overlay_roi(original, mask, roi)
    p1 = prefix.with_name(prefix.name + "_original_1x.png")
    p2 = prefix.with_name(prefix.name + "_overlay_1x.png")
    p3 = prefix.with_name(prefix.name + "_mask_only_1x.png")
    p8 = prefix.with_name(prefix.name + "_card_8x.png")
    a.save(p1); b.save(p2); c.save(p3)
    views = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in (a, b, c)]
    title_h = 34
    card = Image.new("RGB", (sum(im.width for im in views), max(im.height for im in views) + title_h), "white")
    draw = ImageDraw.Draw(card)
    draw.text((8, 8), label + " | ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black")
    x = 0
    for im in views:
        card.paste(im, (x, title_h)); x += im.width
    card.save(p8)
    return tuple(str(p.relative_to(ROOT)).replace("\\", "/") for p in (p1, p2, p3, p8))


def parent_for(cx: float, cy: float, text: str, size: float) -> tuple[str, str, str]:
    if cx < 175 and cy < 150:
        return "TRIAL_LABEL", "NODE_LABEL", "trial"
    if cx < 175 and cy >= 150:
        return "GAMMA_LABEL", "NODE_LABEL", "gamma"
    if 175 <= cx < 280:
        if cy >= 190:
            return "SIMPLEX_LABEL", "NODE_LABEL", "simplex"
        return "FAMILIES_LABEL", "NODE_LABEL", "families"
    if 280 <= cx < 400:
        if cy < 190:
            return ("POSTERIOR_FORMULA" if size > 11.0 else "POSTERIOR_TITLE",
                    "FORMULA_BLOCK" if size > 11.0 else "NODE_LABEL", "posterior")
        return "MOM_LABEL", "NODE_LABEL", "mom"
    if cx >= 400 and cy < 195:
        return ("PREDICTIVE_FORMULA" if cy >= 154 else "PREDICTIVE_TITLE",
                "FORMULA_BLOCK" if cy >= 154 else "NODE_LABEL", "predictive")
    if 465 <= cx <= 510 and 195 <= cy <= 215:
        return "APPLICATION_EDGE_LABEL", "EDGE_LABEL", "application_edge"
    return "LDA_LABEL", "NODE_LABEL", "lda"


LOW_PROFILE = {",", "\u3001", ".", "\u3002", ":", ";", "\uff0c", "\uff1a", "\uff1b", "\u2026"}


def classify_char(char: str, font: str, trace_size: float, role: str) -> tuple[str, int, str]:
    if trace_size < 9.0 and role == "FORMULA_BLOCK":
        return "NATURAL_SCRIPT", 15, "legal TeX sub/superscript from 11.8pt base formula"
    if char in LOW_PROFILE:
        return "LOW_PROFILE_PUNCTUATION", -1, "H and area require same-codepoint frozen-candidate reference"
    cp = ord(char)
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK_FULL", 30, "CJK remains CJK even for low-stroke glyphs"
    name = unicodedata.name(char, "")
    if char.isdigit() or ("LATIN CAPITAL" in name):
        return "LATIN_UPPER_DIGIT", 24, "Latin uppercase/digit"
    if "SMALL" in name or "GREEK SMALL" in name or char.islower():
        return "LATIN_GREEK_XHEIGHT", 17, "Latin/Greek lowercase x-height"
    if char in {"+", "=", "-", "\u2212", "\u2223", "/", "(", ")", "[", "]"}:
        return "BASE_MATH_OPERATOR", 22, "baseline mathematical/operator glyph"
    return "BASE_MATH_SYMBOL", 22, "visible base symbol"


def pair_clearance(mask_a: np.ndarray, mask_b: np.ndarray) -> float | None:
    ya, xa = np.where(mask_a)
    yb, xb = np.where(mask_b)
    if not len(xa) or not len(xb):
        return None
    if len(xa) <= len(xb):
        query = np.column_stack((ya, xa)); target = np.column_stack((yb, xb))
    else:
        query = np.column_stack((yb, xb)); target = np.column_stack((ya, xa))
    dist = float(np.min(cKDTree(target).query(query, k=1, workers=-1)[0]))
    return max(0.0, dist - 1.0)


def bbox_clearance(bbox_a: list[int], bbox_b: list[int]) -> float:
    """Euclidean edge clearance between two native-grid, half-open text bboxes."""
    ax0, ay0, ax1, ay1 = bbox_a
    bx0, by0, bx1, by1 = bbox_b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return float(math.hypot(dx, dy))


def make_pair_card(pair_id: str, name_a: str, name_b: str, original: np.ndarray,
                   mask_a: np.ndarray, mask_b: np.ndarray) -> dict:
    union = mask_a | mask_b
    bb = bbox_from_mask(union)
    if bb is None:
        return {}
    roi = expand_bbox(bb, 8)
    x0, y0, x1, y1 = roi
    src = original[y0:y1, x0:x1].copy()
    a = mask_a[y0:y1, x0:x1]
    b = mask_b[y0:y1, x0:x1]
    inter = a & b
    over = src.copy()
    over[a] = np.array([255, 0, 0], dtype=np.uint8)
    over[b] = np.array([0, 90, 255], dtype=np.uint8)
    over[inter] = np.array([255, 0, 255], dtype=np.uint8)
    a_only = np.full_like(src, 255); a_only[a] = 0
    b_only = np.full_like(src, 255); b_only[b] = 0
    i_only = np.full_like(src, 255); i_only[inter] = 0
    images = [Image.fromarray(src), Image.fromarray(over), Image.fromarray(a_only),
              Image.fromarray(b_only), Image.fromarray(i_only)]
    labels = ["raw", "overlay R=A B=B M=intersection", "A", "B", "intersection"]
    out_paths = []
    for im, suffix in zip(images, ("raw_1x", "overlay_1x", "A_mask_1x", "B_mask_1x", "intersection_1x")):
        path = CRITICAL / f"{pair_id}_{suffix}.png"; im.save(path); out_paths.append(path)
    views = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in images]
    title_h = 48
    card = Image.new("RGB", (sum(im.width for im in views), max(im.height for im in views) + title_h), "white")
    draw = ImageDraw.Draw(card)
    draw.text((8, 6), f"{pair_id}: {name_a} <> {name_b}", fill="black")
    draw.text((8, 24), " | ".join(labels), fill="black")
    x = 0
    for im in views:
        card.paste(im, (x, title_h)); x += im.width
    card_path = CRITICAL / f"{pair_id}_card_8x.png"; card.save(card_path); out_paths.append(card_path)
    return {
        "critical_roi": json.dumps([x0, y0, x1 - x0, y1 - y0]),
        "critical_files": "|".join(str(p.relative_to(ROOT)).replace("\\", "/") for p in out_paths),
    }


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
if page.get_label() != "685":
    raise RuntimeError(f"Page-label mismatch: physical {PHYSICAL_PAGE} has {page.get_label()}")

# Native MuPDF renders direct from the frozen local SA2 candidate.
pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
full300 = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, pix300.n)[..., :3].copy()
Image.fromarray(full300).save(RENDERS / "full_page_300dpi.png")
pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), colorspace=fitz.csRGB, alpha=False)
pix200.save(RENDERS / "full_page_200dpi.png")
figure = full300[CROP_Y0:CROP_Y1, CROP_X0:CROP_X1].copy()
Image.fromarray(figure).save(RENDERS / "figure_crop_300dpi.png")
gray = np.dot(figure[..., :3], np.array([0.299, 0.587, 0.114])).round().clip(0, 255).astype(np.uint8)
Image.fromarray(gray, mode="L").save(RENDERS / "grayscale_300dpi.png")

# Vector-preserving local-candidate standalone extraction; rendered without resampling.
standalone_pdf = RENDERS / "standalone_local_vector_crop.pdf"
standalone_doc = fitz.open()
standalone_page = standalone_doc.new_page(width=CW / SCALE, height=CH / SCALE)
standalone_page.show_pdf_page(standalone_page.rect, doc, PAGE_INDEX, clip=CLIP_PT, keep_proportion=False)
standalone_doc.save(standalone_pdf)
standalone_pix = standalone_page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
standalone_arr = np.frombuffer(standalone_pix.samples, dtype=np.uint8).reshape(
    standalone_pix.height, standalone_pix.width, standalone_pix.n)[..., :3].copy()
Image.fromarray(standalone_arr).save(RENDERS / "standalone_300dpi.png")
standalone_doc.close()

# Target PDF drawings, including zero-height/width rules that Rect.intersects omits.
all_drawings = {int(d.get("seqno")): d for d in page.get_drawings() if d.get("seqno") is not None}
missing_seq = sorted(set(GRAPHIC_SPECS) - set(all_drawings))
if missing_seq:
    raise RuntimeError(f"Required drawing seqno missing: {missing_seq}")
target_drawings = {seq: all_drawings[seq] for seq in GRAPHIC_SPECS}

# Actual fills alone are the explicit background model. White page remains background.
background_draws = [(target_drawings[s], "background") for s in sorted(NODE_SEQ)]
background = render_synthetic(background_draws, RENDERS / "background_exclusion_model_300dpi.png")
foreground_all = np.max(np.abs(figure.astype(np.int16) - background.astype(np.int16)), axis=2) >= 20
Image.fromarray(np.where(foreground_all, 0, 255).astype(np.uint8), mode="L").save(
    RENDERS / "all_foreground_raw_mask_300dpi.png")

# Extract the 100% visible texttrace glyph population.
trace_chars: list[dict] = []
space_rows: list[dict] = []
for span in page.get_texttrace():
    seqno = int(span.get("seqno", -1))
    font = span.get("font", "")
    size = float(span.get("size", 0.0))
    color_tuple = color_float_to_tuple(span.get("color"))
    for char_tuple in span.get("chars", []):
        cp, _, origin, bbox = char_tuple
        char = chr(cp)
        b = fitz.Rect(bbox)
        cx, cy = (b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2
        if not CLIP_PT.contains(fitz.Point(cx, cy)):
            continue
        raw_record = {
            "char": char, "codepoint": f"U+{cp:04X}", "font": font,
            "trace_size_bp": size, "seqno": seqno, "bbox_pt": list(b),
            "origin_pt": list(origin), "color_rgb": list(color_tuple or (0, 0, 0)),
        }
        if char.isspace():
            raw_record.update({"exclusion": "INVISIBLE_SPACE", "basis": "no reader-visible ink; excluded before glyph denominator"})
            space_rows.append(raw_record)
        else:
            trace_chars.append(raw_record)

glyph_rows: list[dict] = []
pre_masks: dict[str, np.ndarray] = {}
for index, rec in enumerate(trace_chars, 1):
    gid = f"G{index:04d}"
    b = fitz.Rect(rec["bbox_pt"])
    cx, cy = (b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2
    parent, role, panel = parent_for(cx, cy, rec["char"], rec["trace_size_bp"])
    declared = 11.6 if role == "FORMULA_BLOCK" else 10.1
    effective = declared * 0.70 if rec["trace_size_bp"] < 9 else declared
    script_class, threshold, basis = classify_char(rec["char"], rec["font"], rec["trace_size_bp"], role)
    px0 = max(0, math.floor(b.x0 * SCALE) - CROP_X0 - 1)
    py0 = max(0, math.floor(b.y0 * SCALE) - CROP_Y0 - 1)
    px1 = min(CW, math.ceil(b.x1 * SCALE) - CROP_X0 + 1)
    py1 = min(CH, math.ceil(b.y1 * SCALE) - CROP_Y0 + 1)
    glyph_rows.append({
        "object_id": gid, "safe_filename": gid, "object_type": "GLYPH", "char": rec["char"],
        "codepoint": rec["codepoint"], "parent_id": parent, "role": role, "panel_id": panel,
        "font": rec["font"], "seqno": rec["seqno"], "declared_pt": declared,
        "graphics_scale": 1.0, "effective_pt": round(effective, 4),
        "trace_size_bp": round(rec["trace_size_bp"], 6), "script_class": script_class,
        "h_threshold_px": threshold, "classification_basis": basis,
        "bbox_pt": json.dumps([round(x, 6) for x in rec["bbox_pt"]]),
        "bbox_px": json.dumps([px0, py0, px1, py1]), "color_rgb": json.dumps(rec["color_rgb"]),
        "low_profile_reference_id": "", "low_profile_h_ratio": "", "low_profile_area_ratio": "",
    })

# Render and isolate every visible foreground path.  Each seqno is replayed alone in
# its actual PDF color over the fill-only background.  This prevents a black synthetic
# stroke from acquiring a wider antialias fringe and accidentally claiming pixels from
# a neighboring later path at an anchor.
graphic_rows: list[dict] = []
graphic_replay_delta: dict[str, np.ndarray] = {}
for index, seq in enumerate(GRAPHIC_SPECS, 1):
    name, category, parent, semantic = GRAPHIC_SPECS[seq]
    drawing = target_drawings[seq]
    mode = "actual_stroke" if seq in NODE_SEQ or drawing.get("type") == "s" else "actual_both"
    replay = render_synthetic(background_draws + [(drawing, mode)])
    replay_delta = np.max(np.abs(replay.astype(np.int16) - background.astype(np.int16)), axis=2)
    # Visibility and ownership are separate questions.  The frozen local candidate must
    # satisfy the 20/255 visible-foreground gate.  Ownership then belongs to this seqno
    # whenever its isolated replay has any non-zero response at that already-visible
    # pixel.  Using 20 a second time on the isolated replay drops antialiased edge pixels
    # from later arrowheads, allowing an earlier same-colour node border to retain them.
    # The non-zero seqno response plus the later z-order subtraction below is the exact
    # ownership proof; no final-page bbox or connected-component guess participates.
    mask = (replay_delta > 0) & foreground_all
    oid = f"P{index:03d}"
    graphic_replay_delta[oid] = replay_delta
    pre_masks[oid] = mask
    rect = drawing["rect"]
    graphic_rows.append({
        "object_id": oid, "safe_filename": oid, "object_type": "GRAPHIC", "graphic_name": name,
        "graphic_class": category, "parent_id": parent, "seqno": seq,
        "bbox_pt": json.dumps([round(v, 6) for v in rect]),
        "path_item_count": len(drawing.get("items", [])), "pdf_type": drawing.get("type"),
        "stroke_width_pt": drawing.get("width"), "stroke_rgb": json.dumps(color_float_to_tuple(drawing.get("color"))),
        "fill_rgb": json.dumps(color_float_to_tuple(drawing.get("fill"))),
        "foreground_basis": (
            "candidate foreground >=20/255 and non-zero single-seqno actual-color stroke replay response over fill-only background; node fill excluded"
            if seq in NODE_SEQ else
            "candidate foreground >=20/255 and non-zero single-seqno actual-color stroke/fill replay response over fill-only background"
        ),
        "source_semantics": semantic,
    })

# Isolate reader-visible text pixels only after every foreground path is known.
# A logical glyph bbox is not itself a glyph mask: adjacent baselines and math rules can
# enter it.  Removing the exact reconstructed path union first prevents such pollution.
# Each remaining connected text component is then assigned as a whole to the glyph whose
# logical bbox contains most of that component.  Ambiguous genuinely touching components
# are split pixelwise by normalized glyph-center distance and remain detectable as zero-
# clearance glyph pairs.  This creates a unique, exhaustive ownership partition.
#
# No residual component may be reassigned to a graphic by bbox proximity or nearest-
# component guessing.  Graphic ownership comes exclusively from the isolated replay of
# its own PDF seqno above.  A component outside every glyph bbox therefore remains an
# explicit closure failure instead of contaminating a path mask.
glyph_ids = [r["object_id"] for r in glyph_rows]
glyph_bbox = {r["object_id"]: tuple(json.loads(r["bbox_px"])) for r in glyph_rows}
centers = {
    gid: ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2,
          max(1, bb[2] - bb[0]), max(1, bb[3] - bb[1]))
    for gid, bb in glyph_bbox.items()
}
graphic_union = np.zeros((CH, CW), dtype=bool)
for row in graphic_rows:
    graphic_union |= pre_masks[row["object_id"]]
text_visible = foreground_all & ~graphic_union
Image.fromarray(np.where(text_visible, 0, 255).astype(np.uint8), mode="L").save(
    RENDERS / "text_only_reader_visible_mask_300dpi.png")
for gid in glyph_ids:
    pre_masks[gid] = np.zeros((CH, CW), dtype=bool)

labels, component_count = component_label(text_visible, structure=np.ones((3, 3), dtype=np.uint8))
component_rows: list[dict] = []
unassigned_text = np.zeros((CH, CW), dtype=bool)
for component_id in range(1, component_count + 1):
    ys, xs = np.where(labels == component_id)
    if not len(xs):
        continue
    cb = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    overlaps: list[tuple[str, int]] = []
    for gid, bb in glyph_bbox.items():
        if cb[2] <= bb[0] or cb[0] >= bb[2] or cb[3] <= bb[1] or cb[1] >= bb[3]:
            continue
        inside = (xs >= bb[0]) & (xs < bb[2]) & (ys >= bb[1]) & (ys < bb[3])
        count = int(inside.sum())
        if count:
            overlaps.append((gid, count))
    overlaps.sort(key=lambda item: (-item[1], item[0]))
    if not overlaps:
        unassigned_text[ys, xs] = True
        assignment = "UNASSIGNED"
        basis = "no logical glyph bbox intersection; graphic reassignment forbidden because seqno replay is sole path owner"
        component_rows.append({
            "component_id": component_id, "area_px": len(xs), "bbox_px": json.dumps(cb),
            "candidate_glyphs": "", "assignment": assignment, "basis": basis,
        })
        continue
    best_gid, best_count = overlaps[0]
    second_count = overlaps[1][1] if len(overlaps) > 1 else 0
    if len(overlaps) == 1 or best_count >= 4 * max(1, second_count):
        pre_masks[best_gid][ys, xs] = True
        assignment = best_gid
        basis = "whole connected component assigned by dominant logical-bbox overlap"
    else:
        # A component truly spans more than one glyph.  Split only this component,
        # preserving deterministic unique ownership while recording the ambiguity.
        assigned = defaultdict(int)
        candidates = [gid for gid, _ in overlaps]
        for y, x in zip(ys, xs):
            containing = [gid for gid in candidates
                          if glyph_bbox[gid][0] <= x < glyph_bbox[gid][2]
                          and glyph_bbox[gid][1] <= y < glyph_bbox[gid][3]]
            pool = containing or candidates
            owner = min(pool, key=lambda gid: (
                ((x - centers[gid][0]) / centers[gid][2]) ** 2
                + ((y - centers[gid][1]) / centers[gid][3]) ** 2,
                gid,
            ))
            pre_masks[owner][y, x] = True
            assigned[owner] += 1
        assignment = "|".join(f"{gid}:{assigned[gid]}" for gid in sorted(assigned))
        basis = "multi-glyph connected component split by normalized center distance"
    component_rows.append({
        "component_id": component_id, "area_px": len(xs), "bbox_px": json.dumps(cb),
        "candidate_glyphs": "|".join(f"{gid}:{count}" for gid, count in overlaps),
        "assignment": assignment, "basis": basis,
    })

glyph_union = np.zeros((CH, CW), dtype=bool)
for gid in glyph_ids:
    glyph_union |= pre_masks[gid]
graphic_union = np.zeros((CH, CW), dtype=bool)
for row in graphic_rows:
    graphic_union |= pre_masks[row["object_id"]]
coverage_union = glyph_union | graphic_union
coverage_residual = foreground_all & ~coverage_union
coverage_excess = coverage_union & ~foreground_all
Image.fromarray(np.where(coverage_residual, 0, 255).astype(np.uint8), mode="L").save(
    RENDERS / "foreground_coverage_residual_mask_300dpi.png")
if int(unassigned_text.sum()) or int(coverage_residual.sum()) or int(coverage_excess.sum()):
    residual_labels, residual_count = component_label(
        coverage_residual, structure=np.ones((3, 3), dtype=np.uint8))
    residual_components = []
    for residual_id in range(1, residual_count + 1):
        rys, rxs = np.where(residual_labels == residual_id)
        pixels = []
        for ry, rx in zip(rys, rxs):
            responses = sorted(
                ((int(delta[ry, rx]), oid) for oid, delta in graphic_replay_delta.items()),
                reverse=True,
            )
            glyph_candidates = [gid for gid, bb in glyph_bbox.items()
                                if bb[0] <= rx < bb[2] and bb[1] <= ry < bb[3]]
            pixels.append({
                "xy": [int(rx), int(ry)],
                "official_rgb": figure[ry, rx].tolist(),
                "background_rgb": background[ry, rx].tolist(),
                "top_seqno_replay_responses": responses[:4],
                "glyph_bbox_candidates": glyph_candidates,
            })
        residual_components.append({
            "component_id": residual_id,
            "area_px": len(rxs),
            "bbox_px": [int(rxs.min()), int(rys.min()), int(rxs.max()) + 1, int(rys.max()) + 1],
            "pixels": pixels,
        })
    (REPORTS / "seqno_replay_residual_diagnostic.json").write_text(
        json.dumps(residual_components, ensure_ascii=False, indent=2), encoding="utf-8")
    raise RuntimeError(
        "Foreground ownership did not close: "
        f"unassigned_text={int(unassigned_text.sum())}, "
        f"coverage_residual={int(coverage_residual.sum())}, coverage_excess={int(coverage_excess.sum())}"
    )

# Model final visibility using PDF sequence order; later visible foreground owns shared pixels.
all_rows = glyph_rows + graphic_rows
row_by_id = {r["object_id"]: r for r in all_rows}
ordered = sorted(all_rows, key=lambda r: (int(r["seqno"]), r["object_id"]))
final_masks: dict[str, np.ndarray] = {}
later_union = np.zeros((CH, CW), dtype=bool)
for row in reversed(ordered):
    oid = row["object_id"]
    final_masks[oid] = pre_masks[oid] & ~later_union
    later_union |= pre_masks[oid]

# Per-glyph measurements, files, and contact cards.
manual_glyph_rows: list[dict] = []
for row in glyph_rows:
    oid = row["object_id"]
    mask = final_masks[oid]
    mb = bbox_from_mask(mask)
    area = int(mask.sum())
    h = 0 if mb is None else mb[3] - mb[1]
    w = 0 if mb is None else mb[2] - mb[0]
    row.update({"mask_bbox_px": json.dumps(mb) if mb else "", "h_ink_px": h, "w_ink_px": w,
                "ink_area_px": area, "empty_mask": int(area == 0),
                "foreign_pixel_px": 0, "missing_stroke_px": "MANUAL_REVIEW_REQUIRED"})
    threshold = int(row["h_threshold_px"])
    if row["script_class"] == "LOW_PROFILE_PUNCTUATION":
        status, reason = "PENDING_REFERENCE", "same-codepoint H/area calibration required"
    elif area == 0:
        status, reason = "FAIL", "empty glyph mask"
    elif h < threshold:
        status, reason = "FAIL", f"H_INK {h} < {threshold}"
    else:
        status, reason = "PASS_NUMERIC", f"H_INK {h} >= {threshold}"
    if float(row["effective_pt"]) < 9.5 and row["script_class"] != "NATURAL_SCRIPT":
        status, reason = "FAIL", f"effective_pt {row['effective_pt']} < 9.5"
    row.update({"numeric_status": status, "numeric_reason": reason})
    bb_for_roi = mb or tuple(json.loads(row["bbox_px"]))
    roi = expand_bbox(bb_for_roi, 5)
    paths = save_three_views(GLYPHS / oid, figure, mask, roi,
                             f"{oid} {row['codepoint']} {row['char']} H={h} area={area}")
    row.update({"original_1x": paths[0], "overlay_1x": paths[1], "mask_only_1x": paths[2], "card_8x": paths[3],
                "roi_px": json.dumps([roi[0], roi[1], roi[2] - roi[0], roi[3] - roi[1]])})
    sheet_no = (int(oid[1:]) - 1) // 4 + 1
    cell_no = (int(oid[1:]) - 1) % 4 + 1
    manual_glyph_rows.append({
        "object_id": oid, "sheet": f"glyph_sheet_{sheet_no:03d}.png", "cell": cell_no,
        "reviewer": "PENDING", "opened_native_1x": "PENDING", "opened_8x": "PENDING",
        "original_match": "PENDING", "overlay_complete": "PENDING", "mask_only_pure": "PENDING",
        "missing_stroke_px": "PENDING", "foreign_pixel_px": "PENDING", "decision": "PENDING", "note": "",
    })

# Assemble glyph contact sheets with four individually labeled 8x cards per sheet.
for sheet_no in range(1, math.ceil(len(glyph_rows) / 4) + 1):
    chunk = glyph_rows[(sheet_no - 1) * 4: sheet_no * 4]
    cards = [Image.open(ROOT / row["card_8x"]).convert("RGB") for row in chunk]
    width = max(im.width for im in cards)
    height = sum(im.height for im in cards)
    sheet = Image.new("RGB", (width, height), "white")
    y = 0
    for im in cards:
        sheet.paste(im, (0, y)); y += im.height
    sheet.save(CONTACTS / f"glyph_sheet_{sheet_no:03d}.png")

# Per-graphic files/cards.
manual_graphic_rows: list[dict] = []
for row in graphic_rows:
    oid = row["object_id"]
    mask = final_masks[oid]
    pre = pre_masks[oid]
    mb = bbox_from_mask(mask)
    pmb = bbox_from_mask(pre)
    area = int(mask.sum())
    row.update({"pre_mask_area_px": int(pre.sum()), "final_mask_area_px": area,
                "occluded_px": int(pre.sum() - area), "mask_bbox_px": json.dumps(mb) if mb else "",
                "empty_mask": int(area == 0), "graphic_status": "FAIL" if area == 0 else "PASS_NUMERIC",
                "foreign_pixel_px": 0, "missing_stroke_px": 0})
    roi = expand_bbox(pmb or (0, 0, 1, 1), 6)
    paths = save_three_views(GRAPHICS / oid, figure, mask, roi,
                             f"{oid} {row['graphic_name']} seq={row['seqno']} area={area}")
    row.update({"original_1x": paths[0], "overlay_1x": paths[1], "mask_only_1x": paths[2], "card_8x": paths[3],
                "roi_px": json.dumps([roi[0], roi[1], roi[2] - roi[0], roi[3] - roi[1]])})
    manual_graphic_rows.append({
        "object_id": oid, "graphic_name": row["graphic_name"], "sheet": Path(paths[3]).name, "cell": 1,
        "reviewer": "PENDING", "opened_native_1x": "PENDING", "opened_8x": "PENDING",
        "original_match": "PENDING", "overlay_complete": "PENDING", "mask_only_pure": "PENDING",
        "missing_stroke_px": "PENDING", "foreign_pixel_px": "PENDING", "decision": "PENDING", "note": "",
    })

# Full bbox overlay.
overlay = Image.fromarray(figure.copy())
draw = ImageDraw.Draw(overlay)
for row in glyph_rows:
    x0, y0, x1, y1 = json.loads(row["bbox_px"])
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 0, 0), width=1)
    draw.text((x0, max(0, y0 - 10)), row["object_id"], fill=(180, 0, 0))
for row in graphic_rows:
    bb = bbox_from_mask(final_masks[row["object_id"]])
    if bb:
        draw.rectangle((bb[0], bb[1], bb[2] - 1, bb[3] - 1), outline=(0, 70, 220), width=1)
overlay.save(RENDERS / "after_text_measurement_overlay_300dpi.png")

# All unordered pairs over the frozen foreground object set.
pair_rows: list[dict] = []
critical_pair_rows: list[dict] = []
for ia in range(len(all_rows)):
    a = all_rows[ia]; aid = a["object_id"]
    for ib in range(ia + 1, len(all_rows)):
        b = all_rows[ib]; bid = b["object_id"]
        pair_id = f"PAIR_{ia + 1:03d}_{ib + 1:03d}"
        pre_overlap = int(np.logical_and(pre_masks[aid], pre_masks[bid]).sum())
        final_overlap = int(np.logical_and(final_masks[aid], final_masks[bid]).sum())
        clearance = pair_clearance(final_masks[aid], final_masks[bid])
        a_type, b_type = a["object_type"], b["object_type"]
        required = 0
        policy = "ALL_FOREGROUND_NO_ILLEGAL_OVERLAP"
        if a_type == b_type == "GLYPH":
            if a["parent_id"] != b["parent_id"]:
                required = 4; policy = "INDEPENDENT_TEXT_TEXT_BBOX_AND_INK"
                clearance = bbox_clearance(json.loads(a["bbox_px"]), json.loads(b["bbox_px"]))
            else:
                policy = "SAME_SEMANTIC_PARENT_INTERNAL_LAYOUT_STILL_ZERO_NONDESIGN_OVERLAP"
        elif {a_type, b_type} == {"GLYPH", "GRAPHIC"}:
            g = a if a_type == "GLYPH" else b
            p = b if a_type == "GLYPH" else a
            if p.get("graphic_class") == "NODE_BORDER" and g.get("panel_id") == p.get("parent_id"):
                required = 5; policy = "NODE_TEXT_TO_OWN_FINAL_VISIBLE_BORDER"
            elif p.get("graphic_class") == "MATH_RULE" and g.get("parent_id") == "PREDICTIVE_FORMULA":
                required = 0; policy = "SAME_FORMULA_MATH_RULE_INTERNAL_RELATION"
            else:
                required = 3; policy = "TEXT_FORMULA_TO_LINE_ARROW_MARKER_OR_FOREIGN_BORDER"
        names = frozenset((a.get("graphic_name", aid), b.get("graphic_name", bid)))
        intentional = names in INTENTIONAL_CONTACT_NAMES
        if pre_overlap > 0 and intentional:
            status = "PASS_INTENTIONAL_CONTACT_REQUIRES_MANUAL_CARD"
            reason = "explicit source-semantic edge connection; pair-specific whitelist"
        elif pre_overlap > 0:
            status = "FAIL"
            reason = f"unwhitelisted separated raw-mask intersection {pre_overlap}px"
        elif clearance is None:
            status = "FAIL"
            reason = "empty mask prevents pair measurement"
        elif clearance + 1e-9 < required:
            status = "FAIL"
            reason = f"clearance {clearance:.3f}px < required {required}px"
        else:
            status = "PASS_MACHINE"
            reason = f"zero raw overlap; clearance {clearance:.3f}px >= required {required}px"
        critical = pre_overlap > 0 or status == "FAIL" or (required > 0 and clearance is not None and clearance < required + 2)
        pair = {
            "pair_id": pair_id, "object_a": aid, "object_b": bid,
            "name_a": a.get("graphic_name", a.get("char", aid)),
            "name_b": b.get("graphic_name", b.get("char", bid)),
            "type_a": a_type, "type_b": b_type, "parent_a": a.get("parent_id"), "parent_b": b.get("parent_id"),
            "seqno_a": a.get("seqno"), "seqno_b": b.get("seqno"), "z_order_later": bid if int(b.get("seqno", -1)) >= int(a.get("seqno", -1)) else aid,
            "raw_pre_overlap_px": pre_overlap, "final_overlap_px": final_overlap,
            "clearance_px": "" if clearance is None else round(clearance, 6), "required_clearance_px": required,
            "policy": policy, "intentional_contact": int(intentional), "status": status, "reason": reason,
            "critical_roi": "", "critical_files": "",
        }
        if critical:
            card = make_pair_card(pair_id, str(pair["name_a"]), str(pair["name_b"]), figure,
                                  pre_masks[aid], pre_masks[bid])
            pair.update(card)
            critical_pair_rows.append({
                "pair_id": pair_id, "object_a": aid, "object_b": bid,
                "reviewer": "PENDING", "opened_native_1x": "PENDING", "opened_8x": "PENDING",
                "source_semantics_checked": "PENDING", "z_order_checked": "PENDING",
                "decision": "PENDING", "note": "", "card_8x": (pair.get("critical_files", "").split("|")[-1] if pair.get("critical_files") else ""),
            })
        pair_rows.append(pair)

# Semantic-element D/E summaries use per-parent/script medians, never cross-script comparisons.
elements: list[dict] = []
groups = defaultdict(list)
for row in glyph_rows:
    groups[(row["parent_id"], row["role"], row["panel_id"], row["script_class"])].append(row)
for (parent, role, panel, script), rows in groups.items():
    hs = [int(r["h_ink_px"]) for r in rows if int(r["h_ink_px"]) > 0 and script != "LOW_PROFILE_PUNCTUATION"]
    median = float(np.median(hs)) if hs else None
    elements.append({
        "element_id": f"E{len(elements) + 1:03d}", "parent_id": parent, "role": role, "panel_id": panel,
        "script_class": script, "glyph_count": len(rows), "glyph_ids": "|".join(r["object_id"] for r in rows),
        "median_h_ink_px": "" if median is None else round(median, 6),
        "min_h_ink_px": min((int(r["h_ink_px"]) for r in rows), default=""),
        "max_h_ink_px": max((int(r["h_ink_px"]) for r in rows), default=""),
        "declared_pt_min": min(float(r["declared_pt"]) for r in rows),
        "declared_pt_max": max(float(r["declared_pt"]) for r in rows),
        "source_same_role_ratio": 1.0, "D_status": "PENDING_COMPARISON", "E_role_ratio": "", "E_status": "PENDING_COMPARISON",
    })

# Compare same role/script medians and formula role against node-label BASE of the same script family.
for elem in elements:
    comparable = [e for e in elements if e["role"] == elem["role"] and e["script_class"] == elem["script_class"] and e["median_h_ink_px"] != ""]
    if comparable and elem["median_h_ink_px"] != "":
        meds = [float(e["median_h_ink_px"]) for e in comparable]
        med = float(elem["median_h_ink_px"])
        ratio = med / float(np.median(meds))
        elem["same_role_ratio_to_median"] = round(ratio, 6)
        elem["D_status"] = "PASS" if 0.92 <= ratio <= 1.08 and max(meds) / min(meds) <= 1.10 else "FAIL"
    else:
        elem["same_role_ratio_to_median"] = "N/A"
        elem["D_status"] = "N/A_INCOMPARABLE"
    if elem["role"] == "FORMULA_BLOCK" and elem["median_h_ink_px"] != "":
        bases = [e for e in elements if e["role"] == "NODE_LABEL" and e["script_class"] == elem["script_class"] and e["median_h_ink_px"] != ""]
        if bases:
            base = float(np.median([float(e["median_h_ink_px"]) for e in bases]))
            ratio = float(elem["median_h_ink_px"]) / base
            elem["E_role_ratio"] = round(ratio, 6)
            elem["E_status"] = "PASS" if 1.00 <= ratio <= 1.18 else "FAIL"
        else:
            elem["E_role_ratio"] = "N/A"
            elem["E_status"] = "N/A_INCOMPARABLE_SCRIPT"
    else:
        elem["E_role_ratio"] = 1.0
        elem["E_status"] = "PASS_BASE_OR_SAME_ROLE"

# Persist inventories and pending manual ledgers.
write_csv(INVENTORY / "background_exclusions.csv", [
    {"seqno": seq, "path_name": GRAPHIC_SPECS[seq][0], "excluded_component": "FILL",
     "basis": "semantic node/card background; only actual vector stroke remains foreground",
     "fill_rgb": json.dumps(color_float_to_tuple(target_drawings[seq].get("fill")))}
    for seq in sorted(NODE_SEQ)
])
write_csv(INVENTORY / "invisible_rawdict_exclusions.csv", space_rows)
write_csv(INVENTORY / "text_component_assignment.csv", component_rows)
write_csv(INVENTORY / "glyph_inventory.csv", glyph_rows)
write_csv(INVENTORY / "graphic_path_inventory.csv", graphic_rows)
write_csv(INVENTORY / "semantic_elements.csv", elements)
write_csv(LEDGERS / "glyph_manual_review.csv", manual_glyph_rows)
write_csv(LEDGERS / "graphic_manual_review.csv", manual_graphic_rows)
write_csv(LEDGERS / "all_unordered_pairs.csv", pair_rows)
write_csv(LEDGERS / "critical_pair_manual_review.csv", critical_pair_rows)

summary = {
    "candidate_pdf": str(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": page.get_label(),
    "page_pt": [page.rect.width, page.rect.height], "full_300dpi_grid": [pix300.width, pix300.height],
    "strict_crop_fullpage_px": list(CROP), "strict_crop_grid": [CW, CH], "strict_clip_pt": list(CLIP_PT),
    "raw_trace_character_slots_in_crop": len(trace_chars) + len(space_rows),
    "invisible_space_exclusions": len(space_rows), "visible_glyph_objects": len(glyph_rows),
    "foreground_graphic_path_objects": len(graphic_rows), "math_rule_objects": sum(r["graphic_class"] == "MATH_RULE" for r in graphic_rows),
    "foreground_object_denominator_N": len(all_rows),
    "unordered_pair_denominator_C_N_2": len(pair_rows),
    "expected_C_N_2": len(all_rows) * (len(all_rows) - 1) // 2,
    "text_connected_components": component_count,
    "unassigned_text_pixels": int(unassigned_text.sum()),
    "foreground_coverage_residual_pixels": int(coverage_residual.sum()),
    "foreground_coverage_excess_pixels": int(coverage_excess.sum()),
    "empty_glyph_masks": sum(int(r["empty_mask"]) for r in glyph_rows),
    "empty_graphic_masks": sum(int(r["empty_mask"]) for r in graphic_rows),
    "glyph_numeric_failures_pre_reference": [r["object_id"] for r in glyph_rows if r["numeric_status"] == "FAIL"],
    "low_profile_reference_pending": [r["object_id"] for r in glyph_rows if r["numeric_status"] == "PENDING_REFERENCE"],
    "pair_failures": [r["pair_id"] for r in pair_rows if r["status"] == "FAIL"],
    "intentional_contact_pairs": [r["pair_id"] for r in pair_rows if r["intentional_contact"]],
    "critical_pair_cards": len(critical_pair_rows),
    "glyph_contact_sheets": math.ceil(len(glyph_rows) / 4), "graphic_contact_cards": len(graphic_rows),
    "manual_state": "PENDING; no manual PASS generated by script",
}
if summary["unordered_pair_denominator_C_N_2"] != summary["expected_C_N_2"]:
    raise RuntimeError("Pair denominator closure failed")
(REPORTS / "denominator_and_machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

doc.close()
print(json.dumps(summary, ensure_ascii=True))
