from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_balance_flux.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa3_r104_fresh_isolated_replacement_v1")
PAGE_INDEX = 650
PHYSICAL_PAGE = 651
PRINTED_PAGE = 638
UID = "FIG-P600-01"
HANDOFF_ID = "C-FIG-P600-01-R104-SA3-FRESH-ISOLATED-REPLACEMENT-V1"
EXPECTED_BYTES = 4_967_222
EXPECTED_SHA256 = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0

RENDER_DIR = ROOT / "renders"
MACHINE_DIR = ROOT / "machine"
MASK_DIR = ROOT / "masks"
CARD_DIR = ROOT / "cards"
PAIR_DIR = ROOT / "pairs"
for directory in (RENDER_DIR, MACHINE_DIR, MASK_DIR, CARD_DIR, CARD_DIR / "objects", PAIR_DIR, PAIR_DIR / "critical"):
    directory.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def px_box(rect: fitz.Rect, scale: float = SCALE_300, pad: int = 0) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * scale) - pad,
        math.floor(rect.y0 * scale) - pad,
        math.ceil(rect.x1 * scale) + pad,
        math.ceil(rect.y1 * scale) + pad,
    )


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return (value >> 16 & 255, value >> 8 & 255, value & 255)


def dominant_rgb(arr: np.ndarray) -> np.ndarray:
    flat = arr.reshape(-1, 3)
    counts = Counter(map(tuple, flat.tolist()))
    return np.array(counts.most_common(1)[0][0], dtype=np.float32)


def blend_mask(arr: np.ndarray, foreground: tuple[int, int, int], backgrounds: list[tuple[int, int, int]] | None = None) -> np.ndarray:
    pixels = arr.astype(np.float32)
    fg = np.array(foreground, dtype=np.float32)
    if backgrounds is None:
        backgrounds = [tuple(map(int, dominant_rgb(arr)))]
    accepted = np.zeros(arr.shape[:2], dtype=bool)
    for bg_tuple in backgrounds:
        bg = np.array(bg_tuple, dtype=np.float32)
        direction = fg - bg
        denom = float(np.dot(direction, direction))
        if denom < 1.0:
            continue
        alpha = np.sum((pixels - bg) * direction, axis=2) / denom
        fitted = bg + alpha[..., None] * direction
        residual = np.linalg.norm(pixels - fitted, axis=2)
        contrast = np.max(np.abs(pixels - bg), axis=2)
        accepted |= (alpha >= 0.02) & (alpha <= 1.30) & (residual <= 24.0) & (contrast >= 20.0)
    return accepted


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def write_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


pdf_size = PDF.stat().st_size
pdf_hash = sha256(PDF)
doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
if pdf_size != EXPECTED_BYTES or pdf_hash != EXPECTED_SHA256:
    raise RuntimeError("official PDF identity mismatch")
if len(doc) != 817:
    raise RuntimeError("official PDF page count mismatch")
if not (abs(page.rect.width - 595.276) < 0.01 and abs(page.rect.height - 841.89) < 0.01):
    raise RuntimeError("official PDF page geometry mismatch")

pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False)
full300 = Image.frombytes("RGB", (pix300.width, pix300.height), pix300.samples)
full300.save(RENDER_DIR / "full_page_300dpi.png", dpi=(300, 300))
pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False)
full200 = Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples)
full200.save(RENDER_DIR / "full_page_200dpi.png", dpi=(200, 200))

standalone_rect_pt = fitz.Rect(120, 452, 464, 628)
figure_rect_pt = fitz.Rect(58, 452, 526, 661)
standalone_box = clamp_box(px_box(standalone_rect_pt), *full300.size)
figure_box = clamp_box(px_box(figure_rect_pt), *full300.size)
standalone = full300.crop(standalone_box)
figure_crop = full300.crop(figure_box)
standalone.save(RENDER_DIR / "standalone_300dpi.png", dpi=(300, 300))
figure_crop.save(RENDER_DIR / "figure_crop_300dpi.png", dpi=(300, 300))
ImageOps.grayscale(figure_crop).convert("RGB").save(RENDER_DIR / "grayscale_300dpi.png", dpi=(300, 300))
standalone.resize((standalone.width * 8, standalone.height * 8), Image.Resampling.NEAREST).save(RENDER_DIR / "standalone_8x_nearest.png")

identity = {
    "UID": UID,
    "HANDOFF_ID": HANDOFF_ID,
    "candidate": "R104 official fullbook",
    "pdf_path": str(PDF.resolve()),
    "pdf_bytes": pdf_size,
    "pdf_sha256": pdf_hash,
    "pdf_pages": len(doc),
    "physical_page": PHYSICAL_PAGE,
    "printed_page": PRINTED_PAGE,
    "figure_number": "32.4",
    "page_pt": [page.rect.width, page.rect.height],
    "full_page_300dpi_native_px": [full300.width, full300.height],
    "full_page_200dpi_native_px": [full200.width, full200.height],
    "standalone_crop_pt": list(standalone_rect_pt),
    "standalone_crop_fullpage_px": list(standalone_box),
    "standalone_native_px": [standalone.width, standalone.height],
    "figure_crop_pt": list(figure_rect_pt),
    "figure_crop_fullpage_px": list(figure_box),
    "figure_crop_native_px": [figure_crop.width, figure_crop.height],
    "render_derivation": "direct PyMuPDF rasterization of official R104 PDF; all crop coordinates are integer full-page native 300 dpi pixels; no post-render resize except explicitly labeled 8x nearest review view",
    "tex_execution": "DISABLED",
    "source_writer": "NONE",
}
(MACHINE_DIR / "candidate_identity_and_render.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")


PARENT_META = {
    "T_TITLE": {"role": "ANNOTATION_TITLE", "kind": "TEXT", "source_line": 26, "declared_pt": 8.6, "semantic_group": "TITLE"},
    "F_A": {"role": "PROPOSAL_FORMULA", "kind": "FORMULA", "source_line": 20, "declared_pt": 9.2, "semantic_group": "PROPOSAL_A"},
    "F_B": {"role": "PROPOSAL_FORMULA", "kind": "FORMULA", "source_line": 22, "declared_pt": 9.2, "semantic_group": "PROPOSAL_B"},
    "F_MIN": {"role": "CLIP_FORMULA", "kind": "FORMULA", "source_line": 24, "declared_pt": 9.2, "semantic_group": "MINIMUM"},
    "F_X": {"role": "STATE_LABEL", "kind": "FORMULA", "source_line": 17, "declared_pt": 9.2, "semantic_group": "STATE_X"},
    "F_Y": {"role": "STATE_LABEL", "kind": "FORMULA", "source_line": 18, "declared_pt": 9.2, "semantic_group": "STATE_Y"},
    "F_FLOW_XY": {"role": "KEY_MATH_LINE", "kind": "FORMULA", "source_line": 37, "declared_pt": 9.2, "semantic_group": "FLOW_BLOCK"},
    "F_FLOW_YX": {"role": "KEY_MATH_LINE", "kind": "FORMULA", "source_line": 38, "declared_pt": 9.2, "semantic_group": "FLOW_BLOCK"},
    "T_NOTE_L1": {"role": "CONCLUSION_NOTE", "kind": "TEXT_FORMULA", "source_line": 42, "declared_pt": 9.2, "semantic_group": "NOTE_BLOCK"},
    "T_NOTE_L2": {"role": "CONCLUSION_NOTE", "kind": "TEXT_FORMULA", "source_line": 42, "declared_pt": 9.2, "semantic_group": "NOTE_BLOCK"},
    "CAPTION": {"role": "CAPTION", "kind": "TEXT_FORMULA", "source_line": 44, "declared_pt": None, "semantic_group": "CAPTION"},
}


def classify_parent(cx: float, cy: float) -> str | None:
    if not (55 <= cx <= 530 and 455 <= cy <= 660):
        return None
    if cy < 476:
        return "T_TITLE"
    if cy < 506:
        return "F_A" if cx < 292 else "F_B"
    if cy < 536:
        return "F_MIN"
    if cy < 560:
        return "F_X" if cx < 292 else "F_Y"
    if cy < 580:
        return "F_FLOW_XY"
    if cy < 598:
        return "F_FLOW_YX"
    if cy < 613:
        return "T_NOTE_L1"
    if cy < 628:
        return "T_NOTE_L2"
    return "CAPTION"


def script_class(char: str, font: str) -> str:
    cp = ord(char)
    name = unicodedata.name(char, "")
    if char in ".,;:。，；：、…":
        return "LOW_PROFILE_PUNCTUATION"
    if "CJK" in name or 0x3400 <= cp <= 0x9FFF or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_FULL"
    if char.isdigit() or (char.isalpha() and char.upper() == char and char.lower() != char):
        return "LATIN_UPPER_DIGIT"
    if char.isalpha() or "GREEK" in name or "MATHEMATICAL" in name and "SMALL" in name:
        return "LATIN_GREEK_LOWER"
    if char in "=+−⇒→∶⊗∫":
        return "MATH_OPERATOR"
    return "MATH_BASE_SYMBOL"


raw = page.get_text("rawdict")
page_arr = np.array(full300)
glyph_rows: list[dict] = []
glyph_masks_global: dict[str, np.ndarray] = {}
parent_glyphs: dict[str, list[str]] = defaultdict(list)
parent_counts = Counter()
excluded_chars: list[dict] = []

for block in raw["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            font = span.get("font", "")
            pdf_size_pt = float(span.get("size", 0))
            text_color = rgb_from_int(int(span.get("color", 0)))
            for char_rec in span.get("chars", []):
                char = char_rec["c"]
                rect = fitz.Rect(char_rec["bbox"])
                cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
                parent = classify_parent(cx, cy)
                if parent is None:
                    continue
                if char.isspace():
                    excluded_chars.append({
                        "exclusion_id": f"EXC_SPACE_{len(excluded_chars)+1:03d}",
                        "char_repr": repr(char),
                        "parent_id": parent,
                        "bbox_pt": json.dumps(list(rect)),
                        "reason": "non-visible spacing codepoint; no foreground path or glyph mask",
                    })
                    continue
                parent_counts[parent] += 1
                gid = f"GLY_{parent}_{parent_counts[parent]:03d}"
                box = clamp_box(px_box(rect), full300.width, full300.height)
                arr = page_arr[box[1]:box[3], box[0]:box[2], :]
                mask_local = blend_mask(arr, text_color)
                tb = tight_bbox(mask_local)
                global_mask = np.zeros((full300.height, full300.width), dtype=bool)
                global_mask[box[1]:box[3], box[0]:box[2]] = mask_local
                glyph_masks_global[gid] = global_mask
                parent_glyphs[parent].append(gid)
                mask_path = MASK_DIR / f"{gid}.png"
                write_mask(mask_path, mask_local)
                if tb:
                    ink_bbox = [box[0] + tb[0], box[1] + tb[1], box[0] + tb[2], box[1] + tb[3]]
                    h_ink = tb[3] - tb[1]
                    ink_pixels = int(mask_local.sum())
                else:
                    ink_bbox = [None, None, None, None]
                    h_ink = 0
                    ink_pixels = 0
                meta = PARENT_META[parent]
                declared = meta["declared_pt"]
                effective = declared if declared is not None else pdf_size_pt
                glyph_rows.append({
                    "glyph_id": gid,
                    "parent_id": parent,
                    "semantic_group": meta["semantic_group"],
                    "role": meta["role"],
                    "source_file": str(FIG_SOURCE.resolve()),
                    "source_line": meta["source_line"],
                    "char": char,
                    "codepoint": f"U+{ord(char):04X}",
                    "unicode_name": unicodedata.name(char, "UNKNOWN"),
                    "font": font,
                    "pdf_vector_size_pt": f"{pdf_size_pt:.6f}",
                    "declared_pt": "PDF_VECTOR" if declared is None else f"{declared:.3f}",
                    "graphics_scale": "1.000000",
                    "effective_pt": f"{effective:.6f}",
                    "script_class": script_class(char, font),
                    "char_bbox_pt": json.dumps([round(v, 6) for v in rect]),
                    "char_bbox_fullpage_px": json.dumps(list(box)),
                    "ink_bbox_fullpage_px": json.dumps(ink_bbox),
                    "h_ink_px": h_ink,
                    "ink_pixel_count": ink_pixels,
                    "declared_rgb": json.dumps(text_color),
                    "mask_path": str(mask_path.resolve()),
                    "machine_mask_nonempty": str(bool(ink_pixels)).lower(),
                })

save_csv(MACHINE_DIR / "glyph_inventory_and_measurements.csv", glyph_rows)
save_csv(MACHINE_DIR / "excluded_nonvisible_characters.csv", excluded_chars)


source_font_rows = []
for parent_id, meta in PARENT_META.items():
    member_rows = [row for row in glyph_rows if row["parent_id"] == parent_id]
    sizes = [float(row["pdf_vector_size_pt"]) for row in member_rows]
    declared = meta["declared_pt"]
    source_font_rows.append({
        "element_id": parent_id,
        "role": meta["role"],
        "source_file": str(FIG_SOURCE.resolve()),
        "source_line": meta["source_line"],
        "declared_pt": "PDF_VECTOR" if declared is None else f"{declared:.3f}",
        "graphics_scale": "1.000000",
        "effective_pt": f"{(declared if declared is not None else min(sizes)):.6f}",
        "pdf_vector_size_min_pt": f"{min(sizes):.6f}",
        "pdf_vector_size_max_pt": f"{max(sizes):.6f}",
        "glyph_count": len(member_rows),
        "legacy_9_5pt_threshold_machine_flag": "BELOW_LEGACY_THRESHOLD" if (declared is not None and declared < 9.5) else "NOT_BELOW",
        "r168_scope": "font ratio/metadata/nominal-size variance is advisory unless actually unreadable, wrong glyph/codepoint/math semantics, tofu, severe visible imbalance, real clipping, or illegal overlap",
    })
save_csv(MACHINE_DIR / "source_font_inventory.csv", source_font_rows)


GRAPHICS = [
    {"id": "G_MAIN_LOWER_SHAFT", "seqno": 16, "kind": "LINE_ARROW", "edge_group": "MAIN_LOWER", "owner": "", "source_line": 32, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_MAIN_LOWER_HEAD", "seqno": 17, "kind": "ARROWHEAD", "edge_group": "MAIN_LOWER", "owner": "", "source_line": 32, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_MAIN_UPPER_SHAFT", "seqno": 19, "kind": "LINE_ARROW", "edge_group": "MAIN_UPPER", "owner": "", "source_line": 33, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_MAIN_UPPER_HEAD", "seqno": 20, "kind": "ARROWHEAD", "edge_group": "MAIN_UPPER", "owner": "", "source_line": 33, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_BORDER_X", "seqno": 22, "kind": "NODE_BORDER", "edge_group": "", "owner": "F_X", "source_line": 17, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_BORDER_Y", "seqno": 25, "kind": "NODE_BORDER", "edge_group": "", "owner": "F_Y", "source_line": 18, "fg": (31, 78, 121), "bgs": [(255, 255, 255)]},
    {"id": "G_BORDER_A", "seqno": 28, "kind": "NODE_BORDER", "edge_group": "", "owner": "F_A", "source_line": 19, "fg": (184, 192, 200), "bgs": [(255, 255, 255), (246, 247, 248)]},
    {"id": "G_BORDER_B", "seqno": 31, "kind": "NODE_BORDER", "edge_group": "", "owner": "F_B", "source_line": 21, "fg": (184, 192, 200), "bgs": [(255, 255, 255), (246, 247, 248)]},
    {"id": "G_BORDER_MIN", "seqno": 34, "kind": "NODE_BORDER", "edge_group": "", "owner": "F_MIN", "source_line": 23, "fg": (183, 121, 31), "bgs": [(255, 255, 255), (249, 244, 237)]},
    {"id": "G_X_A_SHAFT", "seqno": 38, "kind": "LINE_ARROW", "edge_group": "X_A", "owner": "", "source_line": 27, "fg": (107, 114, 128), "bgs": [(255, 255, 255)]},
    {"id": "G_X_A_HEAD", "seqno": 39, "kind": "ARROWHEAD", "edge_group": "X_A", "owner": "", "source_line": 27, "fg": (107, 114, 128), "bgs": [(255, 255, 255), (246, 247, 248)]},
    {"id": "G_Y_B_SHAFT", "seqno": 41, "kind": "LINE_ARROW", "edge_group": "Y_B", "owner": "", "source_line": 28, "fg": (107, 114, 128), "bgs": [(255, 255, 255)]},
    {"id": "G_Y_B_HEAD", "seqno": 42, "kind": "ARROWHEAD", "edge_group": "Y_B", "owner": "", "source_line": 28, "fg": (107, 114, 128), "bgs": [(255, 255, 255), (246, 247, 248)]},
    {"id": "G_A_MIN_SHAFT", "seqno": 44, "kind": "LINE_ARROW", "edge_group": "A_MIN", "owner": "", "source_line": 29, "fg": (107, 114, 128), "bgs": [(255, 255, 255)]},
    {"id": "G_A_MIN_HEAD", "seqno": 45, "kind": "ARROWHEAD", "edge_group": "A_MIN", "owner": "", "source_line": 29, "fg": (107, 114, 128), "bgs": [(255, 255, 255), (249, 244, 237)]},
    {"id": "G_B_MIN_SHAFT", "seqno": 47, "kind": "LINE_ARROW", "edge_group": "B_MIN", "owner": "", "source_line": 30, "fg": (107, 114, 128), "bgs": [(255, 255, 255)]},
    {"id": "G_B_MIN_HEAD", "seqno": 48, "kind": "ARROWHEAD", "edge_group": "B_MIN", "owner": "", "source_line": 30, "fg": (107, 114, 128), "bgs": [(255, 255, 255), (249, 244, 237)]},
    {"id": "G_BORDER_NOTE", "seqno": 51, "kind": "NODE_BORDER", "edge_group": "", "owner": "NOTE_BLOCK", "source_line": 39, "fg": (184, 192, 200), "bgs": [(255, 255, 255)]},
]

drawings = {int(d["seqno"]): d for d in page.get_drawings()}
graphic_rows: list[dict] = []
graphic_masks_global: dict[str, np.ndarray] = {}
render_path_rows: list[dict] = []


def cubic_points(p0, p1, p2, p3, steps: int = 96) -> list[tuple[float, float]]:
    result = []
    for t in np.linspace(0.0, 1.0, steps):
        u = 1.0 - t
        x = u**3*p0.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t**3*p3.x
        y = u**3*p0.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t**3*p3.y
        result.append((x*SCALE_300, y*SCALE_300))
    return result


def vector_path_support(drawing: dict, kind: str) -> np.ndarray:
    """Raster support from this drawing's own PDF path; used only to reject same-color neighbors."""
    support_img = Image.new("L", full300.size, 0)
    draw = ImageDraw.Draw(support_img)
    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for item in drawing.get("items", []):
        code = item[0]
        if code == "l":
            p0, p1 = item[1], item[2]
            start = (p0.x*SCALE_300, p0.y*SCALE_300)
            end = (p1.x*SCALE_300, p1.y*SCALE_300)
            if current and math.dist(current[-1], start) > 2.0:
                subpaths.append(current)
                current = []
            if not current:
                current.append(start)
            current.append(end)
        elif code == "c":
            pts = cubic_points(item[1], item[2], item[3], item[4])
            if current and math.dist(current[-1], pts[0]) > 2.0:
                subpaths.append(current)
                current = []
            if not current:
                current.append(pts[0])
            current.extend(pts[1:])
        elif code == "re":
            rect = item[1]
            pts = [
                (rect.x0*SCALE_300, rect.y0*SCALE_300),
                (rect.x1*SCALE_300, rect.y0*SCALE_300),
                (rect.x1*SCALE_300, rect.y1*SCALE_300),
                (rect.x0*SCALE_300, rect.y1*SCALE_300),
                (rect.x0*SCALE_300, rect.y0*SCALE_300),
            ]
            if current:
                subpaths.append(current)
                current = []
            subpaths.append(pts)
        else:
            raise RuntimeError(f"unsupported drawing path item {code!r} in seqno {drawing['seqno']}")
    if current:
        subpaths.append(current)
    stroke_width = max(2, int(math.ceil(float(drawing.get("width") or 0.7) * SCALE_300)) + 2)
    for points in subpaths:
        if kind == "ARROWHEAD":
            draw.polygon(points, fill=255)
            draw.line(points, fill=255, width=stroke_width, joint="curve")
        else:
            draw.line(points, fill=255, width=stroke_width, joint="curve")
    return np.array(support_img) > 0

for spec in GRAPHICS:
    drawing = drawings[spec["seqno"]]
    rect = fitz.Rect(drawing["rect"])
    box = clamp_box(px_box(rect, pad=3), full300.width, full300.height)
    arr = page_arr[box[1]:box[3], box[0]:box[2], :]
    mask_local = blend_mask(arr, spec["fg"], spec["bgs"])
    support_global = vector_path_support(drawing, spec["kind"])
    mask_local &= support_global[box[1]:box[3], box[0]:box[2]]
    global_mask = np.zeros((full300.height, full300.width), dtype=bool)
    global_mask[box[1]:box[3], box[0]:box[2]] = mask_local
    graphic_masks_global[spec["id"]] = global_mask
    mask_path = MASK_DIR / f"{spec['id']}.png"
    write_mask(mask_path, mask_local)
    tb = tight_bbox(mask_local)
    if tb:
        ink_bbox = [box[0] + tb[0], box[1] + tb[1], box[0] + tb[2], box[1] + tb[3]]
    else:
        ink_bbox = [None, None, None, None]
    graphic_rows.append({
        "object_id": spec["id"],
        "object_type": spec["kind"],
        "pdf_drawing_seqno": spec["seqno"],
        "edge_group": spec["edge_group"],
        "owner": spec["owner"],
        "source_file": str(FIG_SOURCE.resolve()),
        "source_line": spec["source_line"],
        "vector_bbox_pt": json.dumps([round(v, 6) for v in rect]),
        "mask_bbox_fullpage_px": json.dumps(list(box)),
        "ink_bbox_fullpage_px": json.dumps(ink_bbox),
        "ink_pixel_count": int(mask_local.sum()),
        "expected_rgb": json.dumps(spec["fg"]),
        "mask_path": str(mask_path.resolve()),
        "machine_mask_nonempty": str(bool(mask_local.sum())).lower(),
    })
    render_path_rows.append({
        "render_path_id": f"SEQ{spec['seqno']}_FOREGROUND",
        "pdf_drawing_seqno": spec["seqno"],
        "component": "stroke_or_filled_arrowhead_foreground",
        "mapped_object_id": spec["id"],
        "disposition": "INCLUDED_AS_FOREGROUND_OBJECT",
        "reason": "reader-visible border, edge shaft, or arrowhead",
    })
    if drawing.get("fill") is not None and spec["kind"] == "NODE_BORDER":
        render_path_rows.append({
            "render_path_id": f"SEQ{spec['seqno']}_FILL",
            "pdf_drawing_seqno": spec["seqno"],
            "component": "node_fill",
            "mapped_object_id": "",
            "disposition": "EXCLUDED_BACKGROUND",
            "reason": "node/card fill is background under the strict schema and is not an independent foreground collision object",
        })

save_csv(MACHINE_DIR / "graphic_objects.csv", graphic_rows)
save_csv(MACHINE_DIR / "render_path_mapping_and_exclusions.csv", render_path_rows)


parent_masks_global: dict[str, np.ndarray] = {}
parent_rows: list[dict] = []
for parent_id, meta in PARENT_META.items():
    mask = np.zeros((full300.height, full300.width), dtype=bool)
    for gid in parent_glyphs[parent_id]:
        mask |= glyph_masks_global[gid]
    parent_masks_global[parent_id] = mask
    tb = tight_bbox(mask)
    if tb:
        ink_bbox = list(tb)
        min_edge = min(
            tb[0] - figure_box[0],
            tb[1] - figure_box[1],
            figure_box[2] - tb[2],
            figure_box[3] - tb[3],
        )
    else:
        ink_bbox = [None, None, None, None]
        min_edge = None
    mask_path = MASK_DIR / f"PARENT_{parent_id}.png"
    write_mask(mask_path, mask[figure_box[1]:figure_box[3], figure_box[0]:figure_box[2]])
    chars = "".join(row["char"] for row in glyph_rows if row["parent_id"] == parent_id)
    parent_rows.append({
        "object_id": parent_id,
        "object_type": meta["kind"],
        "role": meta["role"],
        "semantic_group": meta["semantic_group"],
        "text": chars,
        "glyph_count": len(parent_glyphs[parent_id]),
        "ink_bbox_fullpage_px": json.dumps(ink_bbox),
        "ink_pixel_count": int(mask.sum()),
        "min_ink_to_figure_crop_edge_px": min_edge,
        "mask_path": str(mask_path.resolve()),
    })
save_csv(MACHINE_DIR / "semantic_text_formula_objects.csv", parent_rows)


objects: list[dict] = []
object_masks: dict[str, np.ndarray] = {}
for row in parent_rows:
    oid = row["object_id"]
    objects.append({
        "object_id": oid,
        "object_type": row["object_type"],
        "role": row["role"],
        "semantic_group": row["semantic_group"],
        "owner": "",
        "edge_group": "",
        "mask_path": row["mask_path"],
    })
    object_masks[oid] = parent_masks_global[oid]
for row in graphic_rows:
    oid = row["object_id"]
    objects.append({
        "object_id": oid,
        "object_type": row["object_type"],
        "role": row["object_type"],
        "semantic_group": row["edge_group"] or oid,
        "owner": row["owner"],
        "edge_group": row["edge_group"],
        "mask_path": row["mask_path"],
    })
    object_masks[oid] = graphic_masks_global[oid]
save_csv(MACHINE_DIR / "pair_universe_objects.csv", objects)


GRAPH_CONNECTIONS = {
    "MAIN_LOWER": {"G_BORDER_X", "G_BORDER_Y"},
    "MAIN_UPPER": {"G_BORDER_X", "G_BORDER_Y"},
    "X_A": {"G_BORDER_X", "G_BORDER_A"},
    "Y_B": {"G_BORDER_Y", "G_BORDER_B"},
    "A_MIN": {"G_BORDER_A", "G_BORDER_MIN"},
    "B_MIN": {"G_BORDER_B", "G_BORDER_MIN"},
}


def pair_rule(a: dict, b: dict) -> tuple[str, str, float]:
    text_types = {"TEXT", "FORMULA", "TEXT_FORMULA", "CAPTION"}
    a_text = a["object_type"] in text_types
    b_text = b["object_type"] in text_types
    if a_text and b_text:
        if a["semantic_group"] == b["semantic_group"]:
            return "INTRA_SEMANTIC_PARENT_LAYOUT", "DESIGN_INTERNAL", 0.0
        return "TEXT_TEXT", "HARD_CLEARANCE", 4.0
    if a_text != b_text:
        text_obj, graph_obj = (a, b) if a_text else (b, a)
        owner = graph_obj.get("owner", "")
        if owner == text_obj["object_id"] or owner == text_obj["semantic_group"]:
            return "TEXT_OWN_NODE_BORDER", "HARD_CLEARANCE", 5.0
        if graph_obj["object_type"] in {"LINE_ARROW", "ARROWHEAD"}:
            return "TEXT_LINE_ARROW", "HARD_CLEARANCE", 3.0
        return "TEXT_OTHER_NODE_BORDER", "HARD_CLEARANCE", 3.0
    if a.get("edge_group") and a.get("edge_group") == b.get("edge_group"):
        return "SHAFT_ARROWHEAD_ASSEMBLY", "DESIGN_CONNECTION", 0.0
    for edge_group, borders in GRAPH_CONNECTIONS.items():
        edge_ids = {o["object_id"] for o in objects if o.get("edge_group") == edge_group}
        if (a["object_id"] in edge_ids and b["object_id"] in borders) or (b["object_id"] in edge_ids and a["object_id"] in borders):
            return "EDGE_NODE_CONNECTION", "DESIGN_CONNECTION", 0.0
    return "GRAPHIC_GRAPHIC_UNRELATED", "HARD_NO_OVERLAP", 0.0


def global_points(mask: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    return np.column_stack((xs, ys)).astype(np.float32)


object_points = {oid: global_points(mask) for oid, mask in object_masks.items()}
object_trees = {oid: cKDTree(points) if len(points) else None for oid, points in object_points.items()}


def intersection_count(mask_a: np.ndarray, mask_b: np.ndarray) -> int:
    return int(np.logical_and(mask_a, mask_b).sum())


def min_distance(oid_a: str, oid_b: str) -> float | None:
    pa = object_points[oid_a]
    pb = object_points[oid_b]
    if not len(pa) or not len(pb):
        return None
    if len(pa) > len(pb):
        pa, pb = pb, pa
        tree = object_trees[oid_a]
        if len(object_points[oid_a]) <= len(object_points[oid_b]):
            tree = object_trees[oid_b]
    else:
        tree = object_trees[oid_b]
    distances, _ = tree.query(pa, k=1)
    return float(np.min(distances))


def make_pair_card(pair_id: str, oid_a: str, oid_b: str, mask_a: np.ndarray, mask_b: np.ndarray, out_path: Path) -> None:
    pa = global_points(mask_a)
    pb = global_points(mask_b)
    if not len(pa) or not len(pb):
        return
    overlap_y, overlap_x = np.nonzero(mask_a & mask_b)
    if len(overlap_x):
        cx = float(np.median(overlap_x))
        cy = float(np.median(overlap_y))
        nearest_a = nearest_b = (cx, cy)
    else:
        tree_b = cKDTree(pb)
        distances, indices = tree_b.query(pa, k=1)
        best = int(np.argmin(distances))
        nearest_a = tuple(pa[best])
        nearest_b = tuple(pb[int(indices[best])])
        cx = (nearest_a[0] + nearest_b[0]) / 2
        cy = (nearest_a[1] + nearest_b[1]) / 2
    half_w, half_h = 44, 34
    box = clamp_box((int(cx-half_w), int(cy-half_h), int(cx+half_w), int(cy+half_h)), full300.width, full300.height)
    original = np.array(full300.crop(box))
    aa = mask_a[box[1]:box[3], box[0]:box[2]]
    bb = mask_b[box[1]:box[3], box[0]:box[2]]
    overlay = original.copy()
    overlay[aa] = [255, 0, 0]
    overlay[bb] = [0, 110, 255]
    both = aa & bb
    overlay[both] = [255, 0, 255]
    mask_view = np.full_like(original, 255)
    mask_view[aa] = [255, 0, 0]
    mask_view[bb] = [0, 110, 255]
    mask_view[both] = [255, 0, 255]
    views = [Image.fromarray(original), Image.fromarray(overlay), Image.fromarray(mask_view)]
    views = [im.resize((im.width*4, im.height*4), Image.Resampling.NEAREST) for im in views]
    width = sum(im.width for im in views)
    height = max(im.height for im in views) + 38
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 4), f"{pair_id}: {oid_a} [red] / {oid_b} [blue] | tight full-page ROI px={box} | nearest A={nearest_a}, B={nearest_b} | 4x nearest", fill="black")
    x = 0
    for label, im in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), views):
        canvas.paste(im, (x, 38))
        draw.text((x + 4, 20), label, fill="black")
        x += im.width
    canvas.save(out_path)


pair_rows: list[dict] = []
critical_pair_rows: list[dict] = []
for idx, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
    pair_id = f"PAIR_{idx:04d}"
    relation, gate, threshold = pair_rule(a, b)
    inter = intersection_count(object_masks[a["object_id"]], object_masks[b["object_id"]])
    distance = min_distance(a["object_id"], b["object_id"])
    machine_flag = "MEASURED"
    if distance is None:
        machine_flag = "EMPTY_MASK"
    elif gate == "HARD_CLEARANCE" and distance < threshold:
        machine_flag = "BELOW_MACHINE_THRESHOLD"
    elif gate in {"HARD_CLEARANCE", "HARD_NO_OVERLAP"} and inter > 0:
        machine_flag = "MACHINE_INTERSECTION"
    critical = bool(gate.startswith("HARD") and (inter > 0 or distance is None or distance < threshold + 8.0))
    evidence_path = ""
    if critical:
        evidence = PAIR_DIR / "critical" / f"{pair_id}_{a['object_id']}__{b['object_id']}.png"
        make_pair_card(pair_id, a["object_id"], b["object_id"], object_masks[a["object_id"]], object_masks[b["object_id"]], evidence)
        evidence_path = str(evidence.resolve())
    row = {
        "pair_id": pair_id,
        "object_a": a["object_id"],
        "object_b": b["object_id"],
        "relation_class": relation,
        "gate_class": gate,
        "threshold_px": f"{threshold:.3f}",
        "raw_mask_intersection_px": inter,
        "min_raw_mask_distance_px": "" if distance is None else f"{distance:.6f}",
        "machine_threshold_flag": machine_flag,
        "critical_review_required": str(critical).lower(),
        "critical_pair_card_path": evidence_path,
    }
    pair_rows.append(row)
    if critical:
        critical_pair_rows.append(row)

save_csv(MACHINE_DIR / "all_unordered_pairs.csv", pair_rows)
save_csv(MACHINE_DIR / "critical_pair_index.csv", critical_pair_rows)


def target_card(original_full: Image.Image, mask: np.ndarray, oid: str, box: tuple[int, int, int, int], scale: int = 8) -> Image.Image:
    pad = 5
    view_box = clamp_box((box[0]-pad, box[1]-pad, box[2]+pad, box[3]+pad), original_full.width, original_full.height)
    original = np.array(original_full.crop(view_box))
    local_mask = mask[view_box[1]:view_box[3], view_box[0]:view_box[2]]
    overlay = original.copy()
    overlay[local_mask] = [255, 0, 0]
    mask_only = np.full_like(original, 255)
    mask_only[local_mask] = [0, 0, 0]
    ims = [Image.fromarray(original), Image.fromarray(overlay), Image.fromarray(mask_only)]
    ims = [im.resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST) for im in ims]
    w = sum(im.width for im in ims)
    h = max(im.height for im in ims) + 52
    canvas = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((4, 2), f"{oid} | native full-page bbox={box} | panels shown at {scale}x nearest", fill="black")
    x = 0
    for label, im in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), ims):
        canvas.paste(im, (x, 52))
        draw.text((x+4, 30), label, fill="black")
        x += im.width
    return canvas


glyph_card_index = []
glyph_cards = []
for row in glyph_rows:
    gid = row["glyph_id"]
    box = tuple(json.loads(row["char_bbox_fullpage_px"]))
    card = target_card(full300, glyph_masks_global[gid], gid, box, scale=8)
    glyph_cards.append((gid, card))

sheet_cols, sheet_rows = 2, 8
per_sheet = sheet_cols * sheet_rows
for sheet_no in range(math.ceil(len(glyph_cards) / per_sheet)):
    chunk = glyph_cards[sheet_no*per_sheet:(sheet_no+1)*per_sheet]
    cell_w = max(card.width for _, card in chunk) + 12
    cell_h = max(card.height for _, card in chunk) + 12
    sheet = Image.new("RGB", (cell_w*sheet_cols, cell_h*sheet_rows), (238, 238, 238))
    for cell_no, (gid, card) in enumerate(chunk, start=1):
        col = (cell_no-1) % sheet_cols
        rowno = (cell_no-1) // sheet_cols
        sheet.paste(card, (col*cell_w+6, rowno*cell_h+6))
        glyph_card_index.append({
            "glyph_id": gid,
            "sheet_id": f"GLYPH_SHEET_{sheet_no+1:02d}",
            "cell_id": f"CELL_{cell_no:02d}",
            "sheet_path": str((CARD_DIR / f"glyph_contact_sheet_{sheet_no+1:02d}.png").resolve()),
        })
    sheet.save(CARD_DIR / f"glyph_contact_sheet_{sheet_no+1:02d}.png")
save_csv(MACHINE_DIR / "glyph_contact_sheet_index.csv", glyph_card_index)


object_card_index = []
object_cards = []
for obj in objects:
    oid = obj["object_id"]
    tb = tight_bbox(object_masks[oid])
    if tb is None:
        continue
    card = target_card(full300, object_masks[oid], oid, tb, scale=4)
    card.save(CARD_DIR / "objects" / f"{oid}.png")
    object_cards.append((oid, card))
for sheet_no in range(math.ceil(len(object_cards) / 8)):
    chunk = object_cards[sheet_no*8:(sheet_no+1)*8]
    cell_w = max(card.width for _, card in chunk) + 12
    cell_h = max(card.height for _, card in chunk) + 12
    sheet = Image.new("RGB", (cell_w*2, cell_h*4), (238, 238, 238))
    for cell_no, (oid, card) in enumerate(chunk, start=1):
        col = (cell_no-1) % 2
        rowno = (cell_no-1) // 2
        sheet.paste(card, (col*cell_w+6, rowno*cell_h+6))
        object_card_index.append({
            "object_id": oid,
            "sheet_id": f"OBJECT_SHEET_{sheet_no+1:02d}",
            "cell_id": f"CELL_{cell_no:02d}",
            "sheet_path": str((CARD_DIR / f"object_contact_sheet_{sheet_no+1:02d}.png").resolve()),
        })
    sheet.save(CARD_DIR / f"object_contact_sheet_{sheet_no+1:02d}.png")
save_csv(MACHINE_DIR / "object_contact_sheet_index.csv", object_card_index)


summary = {
    "glyph_count": len(glyph_rows),
    "excluded_nonvisible_space_count": len(excluded_chars),
    "semantic_text_formula_object_count": len(parent_rows),
    "graphic_foreground_object_count": len(graphic_rows),
    "pair_universe_object_count": len(objects),
    "expected_unordered_pair_count": len(objects) * (len(objects)-1) // 2,
    "actual_unordered_pair_count": len(pair_rows),
    "critical_pair_count": len(critical_pair_rows),
    "empty_glyph_mask_count": sum(1 for row in glyph_rows if row["machine_mask_nonempty"] != "true"),
    "empty_graphic_mask_count": sum(1 for row in graphic_rows if row["machine_mask_nonempty"] != "true"),
    "machine_pair_intersection_flags": sum(1 for row in pair_rows if row["machine_threshold_flag"] == "MACHINE_INTERSECTION"),
    "machine_pair_below_threshold_flags": sum(1 for row in pair_rows if row["machine_threshold_flag"] == "BELOW_MACHINE_THRESHOLD"),
    "render_path_component_count": len(render_path_rows),
    "included_render_path_component_count": sum(1 for row in render_path_rows if row["disposition"] == "INCLUDED_AS_FOREGROUND_OBJECT"),
    "excluded_background_component_count": sum(1 for row in render_path_rows if row["disposition"] == "EXCLUDED_BACKGROUND"),
}
if summary["expected_unordered_pair_count"] != summary["actual_unordered_pair_count"]:
    raise RuntimeError("unordered pair denominator mismatch")
(MACHINE_DIR / "machine_inventory_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
