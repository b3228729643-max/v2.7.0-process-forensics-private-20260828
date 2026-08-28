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


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_balance_flux.tex")
PHYSICAL_PAGE = 651
PRINTED_PAGE = 638
PAGE_INDEX = PHYSICAL_PAGE - 1
HANDOFF_ID = "C-FIG-P600-01-R104-SA1-FRESH-ISOLATED-V1"
UID = "FIG-P600-01"
PDF_SHA256 = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"
DPI = 300
SCALE = DPI / 72.0
BODY_PT = fitz.Rect(126.0, 455.0, 458.0, 628.0)
FIGURE_PT = fitz.Rect(58.0, 455.0, 526.0, 661.0)
DRAWING_INDEXES = list(range(4, 22))


def ensure_dirs() -> None:
    for name in (
        "renders",
        "glyph_native",
        "glyph_cards",
        "glyph_contact_sheets",
        "graphic_native",
        "graphic_cards",
        "graphic_contact_sheets",
        "pair_cards",
        "pair_native",
        "ledgers",
        "machine",
    ):
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pt_rect_to_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE),
        math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE),
        math.ceil(rect.y1 * SCALE),
    )


def local_px_rect(rect: fitz.Rect, crop_px: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pt_rect_to_px(rect)
    return x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0], y1 - crop_px[1]


def safe_text(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ")


def parent_for_char(ch: str, bbox: fitz.Rect) -> str:
    cx = (bbox.x0 + bbox.x1) / 2
    cy = (bbox.y0 + bbox.y1) / 2
    if 459 <= cy < 474:
        return "T001_TOP_PROPOSAL_FLOW_LABEL"
    if 478 <= cy < 500:
        return "T002_A_FORMULA" if cx < 292 else "T003_B_FORMULA"
    if 510 <= cy < 532:
        return "T004_MIN_FORMULA"
    if 536 <= cy < 563:
        return "T005_STATE_X" if cx < 292 else "T006_STATE_Y"
    if 565 <= cy < 582:
        return "T007_ACCEPTED_FLOW_X_TO_Y"
    if 582 <= cy < 598:
        return "T008_ACCEPTED_FLOW_Y_TO_X"
    if 598 <= cy < 614:
        return "T009_BALANCE_EXPLANATION_LINE1"
    if 614 <= cy < 628:
        return "T010_BALANCE_EXPLANATION_LINE2"
    if 628 <= cy <= 662:
        return "T011_CAPTION"
    raise ValueError(f"unmapped visible character {ch!r} at {tuple(bbox)}")


PARENT_ROLES = {
    "T001_TOP_PROPOSAL_FLOW_LABEL": "ANNOTATION",
    "T002_A_FORMULA": "FORMULA_BLOCK",
    "T003_B_FORMULA": "FORMULA_BLOCK",
    "T004_MIN_FORMULA": "FORMULA_BLOCK",
    "T005_STATE_X": "NODE_LABEL",
    "T006_STATE_Y": "NODE_LABEL",
    "T007_ACCEPTED_FLOW_X_TO_Y": "KEY_MATH_LINE",
    "T008_ACCEPTED_FLOW_Y_TO_X": "KEY_MATH_LINE",
    "T009_BALANCE_EXPLANATION_LINE1": "ANNOTATION",
    "T010_BALANCE_EXPLANATION_LINE2": "ANNOTATION",
    "T011_CAPTION": "CAPTION",
}


GRAPHICS = {
    4: ("G001_MAINFLOW_X_TO_Y_CURVE", "EDGE_CURVE", "intended curved accepted-flow edge x to y"),
    5: ("G002_MAINFLOW_X_TO_Y_ARROWHEAD", "ARROWHEAD", "arrowhead for G001"),
    6: ("G003_MAINFLOW_Y_TO_X_CURVE", "EDGE_CURVE", "intended curved accepted-flow edge y to x"),
    7: ("G004_MAINFLOW_Y_TO_X_ARROWHEAD", "ARROWHEAD", "arrowhead for G003"),
    8: ("G005_STATE_X_BORDER", "NODE_BORDER", "final-visible blue circular border for state x"),
    9: ("G006_STATE_Y_BORDER", "NODE_BORDER", "final-visible blue circular border for state y"),
    10: ("G007_A_PROPOSAL_BOX_BORDER", "NODE_BORDER", "final-visible rounded border; soft-gray fill excluded as background"),
    11: ("G008_B_PROPOSAL_BOX_BORDER", "NODE_BORDER", "final-visible rounded border; soft-gray fill excluded as background"),
    12: ("G009_MIN_BOX_BORDER", "NODE_BORDER", "final-visible gold rounded border; pale fill excluded as background"),
    13: ("G010_X_TO_A_CONNECTOR", "LINE_ARROW", "connector stroke from state x to proposal a"),
    14: ("G011_X_TO_A_ARROWHEAD", "ARROWHEAD", "arrowhead for G010"),
    15: ("G012_Y_TO_B_CONNECTOR", "LINE_ARROW", "connector stroke from state y to proposal b"),
    16: ("G013_Y_TO_B_ARROWHEAD", "ARROWHEAD", "arrowhead for G012"),
    17: ("G014_A_TO_MIN_CONNECTOR", "LINE_ARROW", "connector stroke from proposal a to min box"),
    18: ("G015_A_TO_MIN_ARROWHEAD", "ARROWHEAD", "arrowhead for G014"),
    19: ("G016_B_TO_MIN_CONNECTOR", "LINE_ARROW", "connector stroke from proposal b to min box"),
    20: ("G017_B_TO_MIN_ARROWHEAD", "ARROWHEAD", "arrowhead for G016"),
    21: ("G018_EXPLANATION_BOX_BORDER", "NODE_BORDER", "final-visible rounded border for two-line explanation"),
}


def classify_glyph(ch: str, parent: str) -> tuple[str, int]:
    name = unicodedata.name(ch, "")
    cat = unicodedata.category(ch)
    if "CJK UNIFIED" in name or "IDEOGRAPH" in name:
        return "CJK_FULL", 30
    if ch in ".,，。；;：:、…":
        return "LOW_PROFILE_PUNCTUATION", 0
    if ch.isdigit() or (ch.isalpha() and (ch.isupper() or "CAPITAL" in name)):
        return "LATIN_UPPER_OR_DIGIT", 24
    if cat.startswith("S") or ch in "=()+−-∶⇒":
        return "BASE_MATH_OPERATOR", 22
    if ch.isalpha() or "SMALL" in name or ch in "π𝜋𝛼":
        return "LATIN_GREEK_LOWER", 17
    if cat.startswith("P"):
        return "PUNCTUATION_OR_DELIMITER", 17
    return "VISIBLE_OTHER", 17


def foreground_mask(arr: np.ndarray) -> np.ndarray:
    return np.max(np.abs(arr.astype(np.int16) - 255), axis=2) >= 20


def make_glyph_card(base: Image.Image, mask: np.ndarray, bbox: tuple[int, int, int, int], gid: str, out_dir: Path) -> Path:
    x0, y0, x1, y1 = bbox
    pad = 4
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(base.width, x1 + pad), min(base.height, y1 + pad)
    original = base.crop((rx0, ry0, rx1, ry1)).convert("RGB")
    local_mask = mask[ry0:ry1, rx0:rx1]
    overlay = np.array(original).copy()
    overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
    overlay_img = Image.fromarray(overlay)
    mask_img = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    original.save(out_dir / f"{gid}_original_1x.png")
    overlay_img.save(out_dir / f"{gid}_target_overlay_1x.png")
    mask_img.save(out_dir / f"{gid}_mask_only_1x.png")
    eight = overlay_img.resize((max(1, overlay_img.width * 8), max(1, overlay_img.height * 8)), Image.Resampling.NEAREST)
    eight.save(out_dir / f"{gid}_target_overlay_8x_nearest.png")

    panel_w, panel_h = 150, 120
    card = Image.new("RGB", (panel_w * 4, panel_h + 28), "white")
    draw = ImageDraw.Draw(card)
    draw.text((4, 4), gid, fill="black")
    labels = ["ORIGINAL 1x", "OVERLAY 1x", "MASK 1x", "OVERLAY 8x"]
    images = [original, overlay_img, mask_img, eight]
    for i, (label, im) in enumerate(zip(labels, images)):
        draw.text((i * panel_w + 3, 18), label, fill="black")
        thumb = im.copy()
        thumb.thumbnail((panel_w - 8, panel_h - 18), Image.Resampling.NEAREST)
        card.paste(thumb, (i * panel_w + (panel_w - thumb.width) // 2, 32 + (panel_h - 18 - thumb.height) // 2))
    card_dir = ROOT / ("graphic_cards" if out_dir.name == "graphic_native" else "glyph_cards")
    path = card_dir / f"{gid}.png"
    card.save(path)
    return path


def contact_sheets(card_paths: list[Path], out_dir: Path, prefix: str, per_sheet: int = 12) -> list[Path]:
    result: list[Path] = []
    for sheet_idx in range(math.ceil(len(card_paths) / per_sheet)):
        subset = card_paths[sheet_idx * per_sheet : (sheet_idx + 1) * per_sheet]
        sheet = Image.new("RGB", (1200, math.ceil(len(subset) / 2) * 176), "white")
        for cell, path in enumerate(subset):
            im = Image.open(path).convert("RGB")
            im.thumbnail((590, 168), Image.Resampling.LANCZOS)
            x = (cell % 2) * 600 + 5
            y = (cell // 2) * 176 + 4
            sheet.paste(im, (x, y))
        out = out_dir / f"{prefix}_{sheet_idx + 1:03d}.png"
        sheet.save(out)
        result.append(out)
    return result


def polyline_points(items: list[tuple], crop_px: tuple[int, int, int, int]) -> list[list[tuple[float, float]]]:
    paths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    ox, oy = crop_px[0], crop_px[1]

    def cv(p: fitz.Point) -> tuple[float, float]:
        return p.x * SCALE - ox, p.y * SCALE - oy

    for item in items:
        kind = item[0]
        if kind == "l":
            p0, p1 = cv(item[1]), cv(item[2])
            if not current or math.dist(current[-1], p0) > 0.5:
                if current:
                    paths.append(current)
                current = [p0]
            current.append(p1)
        elif kind == "c":
            p0, p1, p2, p3 = map(cv, item[1:5])
            if not current or math.dist(current[-1], p0) > 0.5:
                if current:
                    paths.append(current)
                current = [p0]
            for j in range(1, 65):
                t = j / 64
                mt = 1 - t
                x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
                y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
                current.append((x, y))
        elif kind == "re":
            r = item[1]
            pts = [cv(fitz.Point(r.x0, r.y0)), cv(fitz.Point(r.x1, r.y0)), cv(fitz.Point(r.x1, r.y1)), cv(fitz.Point(r.x0, r.y1)), cv(fitz.Point(r.x0, r.y0))]
            if current:
                paths.append(current)
                current = []
            paths.append(pts)
        elif kind == "qu":
            q = item[1]
            pts = [cv(q.ul), cv(q.ur), cv(q.lr), cv(q.ll), cv(q.ul)]
            if current:
                paths.append(current)
                current = []
            paths.append(pts)
    if current:
        paths.append(current)
    return paths


def drawing_mask(drawing: dict, crop_img: Image.Image, crop_px: tuple[int, int, int, int], arrowhead: bool) -> np.ndarray:
    factor = 4
    canvas = Image.new("L", (crop_img.width * factor, crop_img.height * factor), 0)
    draw = ImageDraw.Draw(canvas)
    paths = polyline_points(drawing["items"], crop_px)
    width = max(1, round(float(drawing["width"]) * SCALE * factor + 2))
    for pts in paths:
        hi = [(round(x * factor), round(y * factor)) for x, y in pts]
        if arrowhead and len(hi) >= 3:
            draw.polygon(hi, fill=255)
            draw.line(hi + [hi[0]], fill=255, width=width, joint="curve")
        else:
            draw.line(hi, fill=255, width=width, joint="curve")
    vector = np.array(canvas.resize(crop_img.size, Image.Resampling.LANCZOS)) > 0
    actual_fg = foreground_mask(np.array(crop_img.convert("RGB")))
    return vector & actual_fg


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def pair_clearance(a: np.ndarray, b: np.ndarray) -> tuple[int, float | None]:
    inter = int(np.count_nonzero(a & b))
    if inter:
        return inter, 0.0
    ay, ax = np.where(a)
    by, bx = np.where(b)
    if len(ax) == 0 or len(bx) == 0:
        return inter, None
    # Exact nearest-center distance through a spatial index; subtract one pixel
    # to report edge-to-edge raw-mask clearance.
    if len(ax) > len(bx):
        ax, bx = bx, ax
        ay, by = by, ay
    axy = np.column_stack((ax, ay)).astype(np.float32)
    bxy = np.column_stack((bx, by)).astype(np.float32)
    distance, _ = cKDTree(bxy).query(axy, k=1)
    return inter, max(0.0, float(distance.min()) - 1.0)


def pair_category(a: dict, b: dict) -> str:
    ra, rb = a["role"], b["role"]
    ta, tb = a["kind"], b["kind"]
    if ta == tb == "TEXT_PARENT":
        return "TEXT_TEXT"
    roles = {ra, rb}
    if "NODE_BORDER" in roles and (ta == "TEXT_PARENT" or tb == "TEXT_PARENT"):
        return "TEXT_FORMULA_NODE_BORDER"
    if ("LINE_ARROW" in roles or "EDGE_CURVE" in roles or "ARROWHEAD" in roles) and (ta == "TEXT_PARENT" or tb == "TEXT_PARENT"):
        return "TEXT_FORMULA_LINE_ARROW"
    if ta == tb == "GRAPHIC":
        return "GRAPHIC_GRAPHIC"
    return "TEXT_GRAPHIC_OTHER"


def make_pair_card(base: Image.Image, a: np.ndarray, b: np.ndarray, aid: str, bid: str, pid: str) -> Path:
    union = a | b
    bb = mask_bbox(union)
    if bb is None:
        bb = (0, 0, min(50, base.width), min(50, base.height))
    x0, y0, x1, y1 = bb
    pad = 12
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(base.width, x1 + pad), min(base.height, y1 + pad)
    original = base.crop((x0, y0, x1, y1)).convert("RGB")
    aa = a[y0:y1, x0:x1]
    bbm = b[y0:y1, x0:x1]
    inter = aa & bbm
    overlay = np.array(original).copy()
    overlay[aa] = [255, 0, 0]
    overlay[bbm] = [0, 80, 255]
    overlay[inter] = [255, 0, 255]
    overlay_img = Image.fromarray(overlay)
    a_img = Image.fromarray(np.where(aa, 0, 255).astype(np.uint8), "L").convert("RGB")
    b_img = Image.fromarray(np.where(bbm, 0, 255).astype(np.uint8), "L").convert("RGB")
    i_img = Image.fromarray(np.where(inter, 0, 255).astype(np.uint8), "L").convert("RGB")
    eight = overlay_img.resize((max(1, overlay_img.width * 8), max(1, overlay_img.height * 8)), Image.Resampling.NEAREST)
    native_dir = ROOT / "pair_native"
    original.save(native_dir / f"{pid}_original_1x.png")
    a_img.save(native_dir / f"{pid}_a_mask_1x.png")
    b_img.save(native_dir / f"{pid}_b_mask_1x.png")
    i_img.save(native_dir / f"{pid}_intersection_1x.png")
    overlay_img.save(native_dir / f"{pid}_overlay_1x.png")
    eight.save(native_dir / f"{pid}_overlay_8x_nearest.png")
    card = Image.new("RGB", (1000, 430), "white")
    dr = ImageDraw.Draw(card)
    dr.text((5, 4), f"{pid} | A={aid} red | B={bid} blue | overlap=magenta", fill="black")
    ims = [("ORIGINAL", original), ("A MASK", a_img), ("B MASK", b_img), ("INTERSECTION", i_img), ("OVERLAY 1x", overlay_img), ("OVERLAY 8x", eight)]
    for idx, (label, im) in enumerate(ims):
        col, row = idx % 3, idx // 3
        px, py = col * 333, 24 + row * 200
        dr.text((px + 4, py), label, fill="black")
        thumb = im.copy()
        thumb.thumbnail((325, 170), Image.Resampling.NEAREST)
        card.paste(thumb, (px + (333 - thumb.width) // 2, py + 20 + (170 - thumb.height) // 2))
    out = ROOT / "pair_cards" / f"{pid}.png"
    card.save(out)
    return out


def main() -> None:
    ensure_dirs()
    assert PDF.exists() and SOURCE.exists()
    assert PDF.stat().st_size == 4_967_222
    assert sha256(PDF) == PDF_SHA256

    doc = fitz.open(PDF)
    assert doc.page_count == 817
    page = doc[PAGE_INDEX]
    assert abs(page.rect.width - 595.276) < 0.01 and abs(page.rect.height - 841.89) < 0.01

    pix300 = page.get_pixmap(dpi=300, alpha=False)
    full300 = Image.frombytes("RGB", (pix300.width, pix300.height), pix300.samples)
    full300.save(ROOT / "renders" / "full_page_300dpi_machine.png")
    pix200 = page.get_pixmap(dpi=200, alpha=False)
    full200 = Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples)
    full200.save(ROOT / "renders" / "full_page_200dpi.png")

    figure_px = pt_rect_to_px(FIGURE_PT)
    body_px = pt_rect_to_px(BODY_PT)
    figure = full300.crop(figure_px)
    body = full300.crop(body_px)
    figure.save(ROOT / "renders" / "figure_crop_300dpi.png")
    body.save(ROOT / "renders" / "standalone_300dpi.png")
    figure.convert("L").save(ROOT / "renders" / "grayscale_300dpi.png")

    raw = page.get_text("rawdict")
    glyphs: list[dict] = []
    exclusions: list[dict] = []
    parent_chars: dict[str, list[str]] = defaultdict(list)
    parent_masks: dict[str, np.ndarray] = {}
    glyph_cards: list[Path] = []
    fig_arr = np.array(figure.convert("RGB"))
    fg = foreground_mask(fig_arr)

    serial = 0
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for chd in span.get("chars", []):
                    ch = chd.get("c", "")
                    rect = fitz.Rect(chd["bbox"])
                    center = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    if not FIGURE_PT.contains(center):
                        continue
                    if ch.isspace():
                        exclusions.append({"EXCLUSION_ID": f"EXC{len(exclusions)+1:04d}", "CHAR": repr(ch), "BBOX_PT": json.dumps(list(rect)), "REASON": "whitespace has no visible foreground ink; retained in parent text but excluded from visible-glyph denominator"})
                        continue
                    serial += 1
                    gid = f"GLY{serial:04d}"
                    parent = parent_for_char(ch, rect)
                    parent_chars[parent].append(ch)
                    local = local_px_rect(rect, figure_px)
                    x0, y0, x1, y1 = local
                    x0, y0 = max(0, x0), max(0, y0)
                    x1, y1 = min(figure.width, x1), min(figure.height, y1)
                    gmask = np.zeros((figure.height, figure.width), dtype=bool)
                    if x1 > x0 and y1 > y0:
                        gmask[y0:y1, x0:x1] = fg[y0:y1, x0:x1]
                    if parent not in parent_masks:
                        parent_masks[parent] = np.zeros_like(gmask)
                    parent_masks[parent] |= gmask
                    ys, xs = np.where(gmask)
                    if len(xs):
                        h_ink = int(ys.max() - ys.min() + 1)
                        w_ink = int(xs.max() - xs.min() + 1)
                        area = int(len(xs))
                    else:
                        h_ink = w_ink = area = 0
                    gclass, threshold = classify_glyph(ch, parent)
                    card = make_glyph_card(figure, gmask, (x0, y0, x1, y1), gid, ROOT / "glyph_native")
                    glyph_cards.append(card)
                    glyphs.append({
                        "GLYPH_ID": gid,
                        "CHAR": ch,
                        "CODEPOINT": f"U+{ord(ch):04X}",
                        "UNICODE_NAME": unicodedata.name(ch, "UNKNOWN"),
                        "PARENT_ID": parent,
                        "ROLE": PARENT_ROLES[parent],
                        "BBOX_PT": json.dumps([round(v, 4) for v in rect]),
                        "BBOX_PX_LOCAL": json.dumps([x0, y0, x1, y1]),
                        "PDF_SPAN_SIZE_PT": round(float(span.get("size", 0)), 4),
                        "FONT": span.get("font", ""),
                        "COLOR": span.get("color", ""),
                        "GLYPH_CLASS": gclass,
                        "PROTOCOL_H_THRESHOLD_PX": threshold,
                        "H_INK_PX": h_ink,
                        "W_INK_PX": w_ink,
                        "INK_AREA_PX": area,
                        "MASK_PIXEL_COUNT": int(np.count_nonzero(gmask)),
                        "MACHINE_EMPTY_MASK": h_ink == 0,
                        "PROTOCOL_NUMERIC_STATUS": "CALIBRATION_REQUIRED" if threshold == 0 else ("PASS" if h_ink >= threshold else "BELOW_LEGACY_THRESHOLD"),
                        "CARD": str(card.relative_to(ROOT)).replace("\\", "/"),
                    })

    glyph_sheets = contact_sheets(glyph_cards, ROOT / "glyph_contact_sheets", "glyph_contact_sheet")
    glyph_sheet_by_id: dict[str, tuple[str, int]] = {}
    for idx, g in enumerate(glyphs):
        sheet = glyph_sheets[idx // 12]
        glyph_sheet_by_id[g["GLYPH_ID"]] = (str(sheet.relative_to(ROOT)).replace("\\", "/"), idx % 12 + 1)

    graphics_rows: list[dict] = []
    graphic_masks: dict[str, np.ndarray] = {}
    graphic_cards: list[Path] = []
    drawings = page.get_drawings()
    pre_graphic_masks: dict[int, np.ndarray] = {}
    for drawing_index in DRAWING_INDEXES:
        d = drawings[drawing_index]
        gid, role, note = GRAPHICS[drawing_index]
        arrowhead = role == "ARROWHEAD"
        pre_graphic_masks[drawing_index] = drawing_mask(d, figure, figure_px, arrowhead)

    # PDF paint order is authoritative. A later opaque foreground drawing owns
    # shared final-visible pixels; earlier drawing masks retain only what the
    # reader can still see. Pre-occlusion masks are also preserved for audit.
    for drawing_index in DRAWING_INDEXES:
        d = drawings[drawing_index]
        gid, role, note = GRAPHICS[drawing_index]
        pre = pre_graphic_masks[drawing_index]
        later = np.zeros_like(pre)
        for later_index in DRAWING_INDEXES:
            if later_index > drawing_index:
                later |= pre_graphic_masks[later_index]
        mask = pre & ~later
        graphic_masks[gid] = mask
        Image.fromarray(np.where(pre, 0, 255).astype(np.uint8), "L").save(ROOT / "graphic_native" / f"{gid}_pre_occlusion_mask_1x.png")
        bb = mask_bbox(mask)
        if bb is None:
            bb = (0, 0, 1, 1)
        card = make_glyph_card(figure, mask, bb, gid, ROOT / "graphic_native")
        graphic_cards.append(card)
        graphics_rows.append({
            "GRAPHIC_ID": gid,
            "PDF_DRAWING_INDEX": drawing_index,
            "ROLE": role,
            "DRAWING_TYPE": d["type"],
            "BBOX_PT": json.dumps([round(v, 4) for v in d["rect"]]),
            "BBOX_PX_LOCAL": json.dumps(list(bb)),
            "RAW_MASK_PIXEL_COUNT": int(np.count_nonzero(mask)),
            "PRE_OCCLUSION_MASK_PIXEL_COUNT": int(np.count_nonzero(pre)),
            "OCCLUDED_BY_LATER_DRAWINGS_PX": int(np.count_nonzero(pre & later)),
            "EMPTY_MASK": int(np.count_nonzero(mask)) == 0,
            "SOURCE_SEMANTICS": note,
            "FILL_TREATMENT": "foreground included" if role == "ARROWHEAD" else "fill excluded as background; final-visible stroke only",
            "PAINT_ORDER_TREATMENT": "final-visible = pre-occlusion mask minus later opaque drawing masks; pre-occlusion mask preserved",
            "CARD": str(card.relative_to(ROOT)).replace("\\", "/"),
        })
    graphic_sheets = contact_sheets(graphic_cards, ROOT / "graphic_contact_sheets", "graphic_contact_sheet")

    # Parent object ledger and masks.
    objects: list[dict] = []
    all_masks: dict[str, np.ndarray] = {}
    for pid in PARENT_ROLES:
        mask = parent_masks.get(pid, np.zeros((figure.height, figure.width), dtype=bool))
        all_masks[pid] = mask
        bb = mask_bbox(mask)
        objects.append({
            "OBJECT_ID": pid,
            "KIND": "TEXT_PARENT",
            "ROLE": PARENT_ROLES[pid],
            "VISIBLE_TEXT": "".join(parent_chars.get(pid, [])),
            "BBOX_PX_LOCAL": json.dumps(list(bb) if bb else []),
            "RAW_MASK_PIXEL_COUNT": int(np.count_nonzero(mask)),
            "SEMANTIC_SCOPE": "single semantic parent; internal glyph typography excluded from independent TEXT-TEXT clearance but checked glyph-by-glyph",
        })
    for grow in graphics_rows:
        gid = grow["GRAPHIC_ID"]
        all_masks[gid] = graphic_masks[gid]
        objects.append({
            "OBJECT_ID": gid,
            "KIND": "GRAPHIC",
            "ROLE": grow["ROLE"],
            "VISIBLE_TEXT": "",
            "BBOX_PX_LOCAL": grow["BBOX_PX_LOCAL"],
            "RAW_MASK_PIXEL_COUNT": grow["RAW_MASK_PIXEL_COUNT"],
            "SEMANTIC_SCOPE": grow["SOURCE_SEMANTICS"],
        })

    pair_rows: list[dict] = []
    critical_cards: dict[str, str] = {}
    obj_by_id = {o["OBJECT_ID"]: {"kind": o["KIND"], "role": o["ROLE"]} for o in objects}
    for idx, (aobj, bobj) in enumerate(itertools.combinations(objects, 2), start=1):
        aid, bid = aobj["OBJECT_ID"], bobj["OBJECT_ID"]
        pid = f"PAIR{idx:04d}"
        inter, clearance = pair_clearance(all_masks[aid], all_masks[bid])
        category = pair_category(obj_by_id[aid], obj_by_id[bid])
        critical = inter > 0 or clearance is None or clearance < 12.0
        card_rel = ""
        if critical:
            card = make_pair_card(figure, all_masks[aid], all_masks[bid], aid, bid, pid)
            card_rel = str(card.relative_to(ROOT)).replace("\\", "/")
            critical_cards[pid] = card_rel
        pair_rows.append({
            "PAIR_ID": pid,
            "OBJECT_A": aid,
            "OBJECT_B": bid,
            "CATEGORY": category,
            "RAW_INTERSECTION_PIXEL_COUNT": inter,
            "MIN_RAW_MASK_CLEARANCE_PX": "" if clearance is None else round(clearance, 4),
            "MACHINE_CRITICAL_LT12_OR_INTERSECTION": critical,
            "CRITICAL_CARD": card_rel,
            "CRITICAL_NATIVE_PREFIX": f"pair_native/{pid}_" if critical else "",
        })

    # All-glyph measurement overlay.
    overlay = figure.copy().convert("RGB")
    od = ImageDraw.Draw(overlay)
    for g in glyphs:
        x0, y0, x1, y1 = json.loads(g["BBOX_PX_LOCAL"])
        od.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 0, 0), width=1)
    for o in objects:
        if o["KIND"] != "TEXT_PARENT":
            continue
        bb = json.loads(o["BBOX_PX_LOCAL"])
        if bb:
            od.rectangle(tuple(bb), outline=(0, 80, 255), width=2)
            od.text((bb[0], max(0, bb[1] - 11)), o["OBJECT_ID"].split("_")[0], fill=(0, 80, 255))
    overlay.save(ROOT / "renders" / "after_text_measurement_overlay_300dpi.png")

    source_font_rows = [
        {"SOURCE_ID": "SRC001", "SCOPE": "slfig-FIG-P600-01 global style", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "default nodes/paths", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC002", "SCOPE": "state style override", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "T005,T006", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC003", "SCOPE": "proposal style override", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "T002,T003", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC004", "SCOPE": "clipbox style override", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "T004", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC005", "SCOPE": "top proposal-flow annotation local override", "DECLARED_PT": 8.6, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 8.6, "VISIBLE_OBJECTS": "T001", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC006", "SCOPE": "accepted-flow equation block local override", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "T007,T008", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC007", "SCOPE": "bottom explanation card local override", "DECLARED_PT": 9.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.2, "VISIBLE_OBJECTS": "T009,T010", "LEGACY_9_5_NUMERIC": "BELOW_LEGACY_THRESHOLD", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
        {"SOURCE_ID": "SRC008", "SCOPE": "caption controlled by book class; measured from official PDF spans", "DECLARED_PT": "PDF_MEASURED", "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": "SEE_GLYPH_LEDGER", "VISIBLE_OBJECTS": "T011", "LEGACY_9_5_NUMERIC": "MEASURED_ONLY", "R168_DISPOSITION": "MANUAL_REVIEW_REQUIRED"},
    ]

    glyph_manual = []
    for g in glyphs:
        sheet, cell = glyph_sheet_by_id[g["GLYPH_ID"]]
        glyph_manual.append({
            "GLYPH_ID": g["GLYPH_ID"],
            "CHAR": g["CHAR"],
            "CODEPOINT": g["CODEPOINT"],
            "SHEET": sheet,
            "CELL": cell,
            "REVIEWER": "",
            "ACTUALLY_OPENED": "",
            "ORIGINAL_MATCH": "",
            "OVERLAY_COMPLETE": "",
            "MASK_ONLY_PURE": "",
            "MISSING_STROKE_PX": "",
            "FOREIGN_PIXEL_PX": "",
            "TOFU_OR_WRONG_GLYPH": "",
            "ACTUAL_READABILITY": "",
            "R168_DECISION": "",
            "NOTE": "",
        })

    graphic_manual = []
    for idx, g in enumerate(graphics_rows):
        graphic_manual.append({
            "GRAPHIC_ID": g["GRAPHIC_ID"],
            "ROLE": g["ROLE"],
            "SHEET": str(graphic_sheets[idx // 12].relative_to(ROOT)).replace("\\", "/"),
            "CELL": idx % 12 + 1,
            "REVIEWER": "",
            "ACTUALLY_OPENED": "",
            "SOURCE_IDENTITY_MATCH": "",
            "ORIGINAL_MATCH": "",
            "OVERLAY_COMPLETE": "",
            "MASK_ONLY_PURE": "",
            "EMPTY_MASK": "",
            "GEOMETRY_SEMANTICS": "",
            "DECISION": "",
            "NOTE": "",
        })

    pair_manual = []
    for p in pair_rows:
        pair_manual.append({
            "PAIR_ID": p["PAIR_ID"],
            "OBJECT_A": p["OBJECT_A"],
            "OBJECT_B": p["OBJECT_B"],
            "CATEGORY": p["CATEGORY"],
            "MACHINE_INTERSECTION_PX": p["RAW_INTERSECTION_PIXEL_COUNT"],
            "MACHINE_CLEARANCE_PX": p["MIN_RAW_MASK_CLEARANCE_PX"],
            "CRITICAL_CARD": p["CRITICAL_CARD"],
            "REVIEWER": "",
            "ACTUALLY_REVIEWED": "",
            "INTENDED_RELATION": "",
            "ILLEGAL_OVERLAP_PX": "",
            "HARD_CLEARANCE_GATE_APPLIES": "",
            "HARD_CLEARANCE_THRESHOLD_PX": "",
            "MANUAL_DECISION": "",
            "NOTE": "",
        })

    view_rows = [
        {"VIEW_ID": "VIEW001", "PATH": "renders/full_page_200dpi.png", "PURPOSE": "page integration only"},
        {"VIEW_ID": "VIEW002", "PATH": "renders/figure_crop_300dpi.png", "PURPOSE": "official 300 dpi figure+caption"},
        {"VIEW_ID": "VIEW003", "PATH": "renders/standalone_300dpi.png", "PURPOSE": "official-PDF-derived figure body"},
        {"VIEW_ID": "VIEW004", "PATH": "renders/grayscale_300dpi.png", "PURPOSE": "grayscale hierarchy"},
        {"VIEW_ID": "VIEW005", "PATH": "renders/after_text_measurement_overlay_300dpi.png", "PURPOSE": "all-glyph and parent mapping overlay"},
    ]
    view_manual = [{**r, "REVIEWER": "", "ACTUALLY_OPENED": "", "IDENTITY_MATCH": "", "READABLE": "", "CLIPPED": "", "ILLEGAL_OVERLAP_VISIBLE": "", "FONT_HARMONY": "", "GRAYSCALE_OR_PAGE_FUSION": "", "DECISION": "", "NOTE": ""} for r in view_rows]

    write_csv(ROOT / "machine" / "glyph_machine_inventory.csv", glyphs)
    write_csv(ROOT / "machine" / "visible_whitespace_exclusions.csv", exclusions)
    write_csv(ROOT / "machine" / "graphic_machine_inventory.csv", graphics_rows)
    write_csv(ROOT / "machine" / "object_machine_inventory.csv", objects)
    write_csv(ROOT / "machine" / "all_unordered_pairs_machine.csv", pair_rows)
    write_csv(ROOT / "machine" / "source_font_machine_inventory.csv", source_font_rows)
    write_csv(ROOT / "ledgers" / "glyph_manual_review.csv", glyph_manual)
    write_csv(ROOT / "ledgers" / "graphic_manual_review.csv", graphic_manual)
    write_csv(ROOT / "ledgers" / "pair_manual_review.csv", pair_manual)
    write_csv(ROOT / "ledgers" / "view_manual_review.csv", view_manual)

    metadata = {
        "uid": UID,
        "handoff_id": HANDOFF_ID,
        "review_role": "SA1 fresh isolated",
        "tex": "DISABLED",
        "source_writer": "NONE",
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": PDF_SHA256,
        "official_pdf_pages": doc.page_count,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "figure_number": "32.4",
        "page_pt": [page.rect.width, page.rect.height],
        "page_300dpi_px": [full300.width, full300.height],
        "full_page_200dpi_px": [full200.width, full200.height],
        "figure_crop_pt": list(FIGURE_PT),
        "figure_crop_px_on_page": list(figure_px),
        "figure_crop_native_px": [figure.width, figure.height],
        "standalone_crop_pt": list(BODY_PT),
        "standalone_crop_px_on_page": list(body_px),
        "standalone_native_px": [body.width, body.height],
        "render_rule": "direct PyMuPDF render of official PDF page at native requested DPI; crop is integer-coordinate extraction only; no resize",
        "glyph_denominator": len(glyphs),
        "whitespace_exclusion_denominator": len(exclusions),
        "text_parent_denominator": len(PARENT_ROLES),
        "graphic_denominator": len(graphics_rows),
        "object_denominator": len(objects),
        "all_unordered_pair_denominator": len(pair_rows),
        "expected_pair_denominator": len(objects) * (len(objects) - 1) // 2,
        "critical_pair_card_denominator": len(critical_cards),
        "glyph_contact_sheet_denominator": len(glyph_sheets),
        "graphic_contact_sheet_denominator": len(graphic_sheets),
        "math_rule_denominator": 0,
        "math_rule_explanation": "source and PDF drawing inventory contain no overline/underline/radical/fraction/accent/cancellation rule in this figure; arrows and borders are separately mapped as GRAPHIC objects",
    }
    assert metadata["all_unordered_pair_denominator"] == metadata["expected_pair_denominator"]
    (ROOT / "machine" / "candidate_identity_and_denominators.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "machine" / "machine_generation_summary.json").write_text(json.dumps({
        "status": "MACHINE_EVIDENCE_COMPLETE_MANUAL_COLUMNS_BLANK",
        "manual_pass_fail_generated": False,
        "glyph_masks_nonempty": sum(not g["MACHINE_EMPTY_MASK"] for g in glyphs),
        "glyph_masks_empty": sum(g["MACHINE_EMPTY_MASK"] for g in glyphs),
        "graphic_masks_nonempty": sum(not g["EMPTY_MASK"] for g in graphics_rows),
        "graphic_masks_empty": sum(g["EMPTY_MASK"] for g in graphics_rows),
        "pair_intersection_candidates": sum(p["RAW_INTERSECTION_PIXEL_COUNT"] > 0 for p in pair_rows),
        "critical_pair_cards": len(critical_cards),
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
