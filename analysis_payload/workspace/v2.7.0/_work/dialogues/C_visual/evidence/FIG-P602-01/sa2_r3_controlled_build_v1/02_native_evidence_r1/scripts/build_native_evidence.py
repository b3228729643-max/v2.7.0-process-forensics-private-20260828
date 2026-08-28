from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r3_controlled_build_v1\02_native_evidence_r1")
BUILD_ROOT = ROOT.parent
PDF = BUILD_ROOT / "01_build" / "v260_FIG-P602-01_standalone.pdf"
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\合并总册\v260_FIG-P602-01_standalone.tex")
BUILD_RESULT = BUILD_ROOT / "00_control" / "DIRECT_INVOCATION_RESULT.json"
BUILD_START = BUILD_ROOT / "00_control" / "DIRECT_INVOCATION_START.json"
PDF_SHA_EXPECTED = "68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7"
SOURCE_SHA_EXPECTED = "6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D"
PAGE_INDEX = 0
DPI = 300

for rel in (
    "identity",
    "render",
    "render/landmarks_8x",
    "objects/masks_1x",
    "objects/cards",
    "objects/contact_sheets",
    "glyphs/masks_1x",
    "glyphs/cards",
    "glyphs/contact_sheets",
    "pairs/cards",
    "pairs/contact_sheets",
    "pairs/critical",
    "ledgers",
    "qa",
):
    (ROOT / rel).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def bbox_union(boxes):
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def clip_box(box, width: int, height: int):
    x0, y0, x1, y1 = (int(v) for v in box)
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def tight_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_clearance(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float(math.hypot(dx, dy))


def local_color_mask(region: np.ndarray, target_rgb) -> np.ndarray:
    if region.size == 0:
        return np.zeros(region.shape[:2], dtype=bool)
    pixels = region.astype(np.float32)
    background = np.median(pixels.reshape(-1, 3), axis=0)
    target = np.asarray(target_rgb, dtype=np.float32)
    vector = background - target
    denominator = float(np.dot(vector, vector))
    if denominator < 1.0:
        return np.zeros(region.shape[:2], dtype=bool)
    alpha = np.tensordot(background - pixels, vector, axes=([2], [0])) / denominator
    reconstruction = background[None, None, :] - alpha[:, :, None] * vector[None, None, :]
    residual = np.max(np.abs(pixels - reconstruction), axis=2)
    contrast = np.max(np.abs(pixels - background[None, None, :]), axis=2)
    return (contrast >= 20.0) & (alpha >= 0.045) & (alpha <= 1.35) & (residual <= 22.0)


def mask_from_color(arr: np.ndarray, box, target_rgb, pad=1) -> np.ndarray:
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = clip_box((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad), w, h)
    out = np.zeros((h, w), dtype=bool)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = local_color_mask(arr[y0:y1, x0:x1], target_rgb)
    return out


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(path, dpi=(DPI, DPI), optimize=True)


def overlay(base: Image.Image, mask: np.ndarray, color=(255, 25, 25), alpha=0.66) -> Image.Image:
    arr = np.asarray(base.convert("RGB"), dtype=np.float32).copy()
    c = np.asarray(color, dtype=np.float32)
    arr[mask] = arr[mask] * (1.0 - alpha) + c * alpha
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)), mode="RGB")


def px_box(pdf_box, sx: float, sy: float, crop, pad: int = 0):
    x0, y0, x1, y1 = pdf_box
    return (
        math.floor(x0 * sx) - crop[0] - pad,
        math.floor(y0 * sy) - crop[1] - pad,
        math.ceil(x1 * sx) - crop[0] + pad,
        math.ceil(y1 * sy) - crop[1] + pad,
    )


def fit_thumbnail(image: Image.Image, size=(1180, 420)) -> Image.Image:
    out = image.copy()
    out.thumbnail(size, Image.Resampling.LANCZOS)
    return out


assert sha256(PDF) == PDF_SHA_EXPECTED, "candidate PDF identity drift"
assert sha256(FIG_SOURCE) == SOURCE_SHA_EXPECTED, "P602 source identity drift"
assert BUILD_START.is_file() and BUILD_RESULT.is_file(), "accepted R3 v1 control records missing"

doc = fitz.open(PDF)
assert doc.page_count == 1, f"standalone PDF page count drift: {doc.page_count}"
page = doc[PAGE_INDEX]
matrix = fitz.Matrix(DPI / 72.0, DPI / 72.0)
pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
fitz_full = ROOT / "render" / "full_page_fitz_native_300dpi.png"
pix.save(fitz_full)
full = Image.open(fitz_full).convert("RGB")
sx = pix.width / page.rect.width
sy = pix.height / page.rect.height

poppler_prefix = ROOT / "render" / "full_page_poppler_native_300dpi"
poppler_cmd = [
    r"D:\texlive\2026\bin\windows\pdftoppm.exe",
    "-f", "1", "-l", "1", "-singlefile", "-r", str(DPI), "-png",
    str(PDF), str(poppler_prefix),
]
poppler_run = subprocess.run(poppler_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
poppler_png = poppler_prefix.with_suffix(".png")
if poppler_run.returncode != 0 or not poppler_png.is_file():
    raise RuntimeError(f"pdftoppm native render failed: {poppler_run.returncode} {poppler_run.stderr}")

traces = page.get_texttrace()
drawings = page.get_drawings()
assert len(traces) == 56, f"texttrace record count drift: {len(traces)}"
assert sum(len(t["chars"]) for t in traces) == 154, "visible glyph denominator drift"
assert len(drawings) == 26, f"drawing denominator drift: {len(drawings)}"

text_boxes = [tuple(ch[3]) for t in traces for ch in t["chars"]]
drawing_boxes = [tuple(d["rect"]) for d in drawings]
content_pdf_box = bbox_union(text_boxes + drawing_boxes)
margin_pt = 8.0
crop = clip_box(
    (
        math.floor((content_pdf_box[0] - margin_pt) * sx),
        math.floor((content_pdf_box[1] - margin_pt) * sy),
        math.ceil((content_pdf_box[2] + margin_pt) * sx),
        math.ceil((content_pdf_box[3] + margin_pt) * sy),
    ),
    pix.width,
    pix.height,
)
base = full.crop(crop)
base.save(ROOT / "render" / "figure_fitz_native_300dpi_1x.png", dpi=(DPI, DPI), optimize=True)
poppler_full = Image.open(poppler_png).convert("RGB")
poppler_crop = poppler_full.crop(crop)
poppler_crop.save(ROOT / "render" / "figure_poppler_native_300dpi_1x.png", dpi=(DPI, DPI), optimize=True)
base.convert("L").save(ROOT / "render" / "figure_grayscale_native_300dpi_1x.png", dpi=(DPI, DPI), optimize=True)
base_arr = np.asarray(base)
H, W = base_arr.shape[:2]

landmark_pdf_boxes = [
    (198, 66, 334, 147),
    (102, 155, 430, 214),
    (147, 220, 384, 302),
    (82, 298, 450, 337),
    (245, 330, 523, 419),
]
landmark_rows = []
for index, pdf_box in enumerate(landmark_pdf_boxes, start=1):
    pbox = clip_box(px_box(pdf_box, sx, sy, crop, pad=0), W, H)
    native_patch = base.crop(pbox)
    enlarged = native_patch.resize((native_patch.width * 8, native_patch.height * 8), Image.Resampling.NEAREST)
    target = ROOT / "render" / "landmarks_8x" / f"LANDMARK{index:02d}_native_nearest_8x.png"
    enlarged.save(target, optimize=True)
    landmark_rows.append({
        "landmark_id": f"LANDMARK{index:02d}",
        "pdf_box": json.dumps(pdf_box),
        "crop_1x_xyxy": json.dumps(pbox),
        "scale": 8,
        "resampler": "NEAREST",
        "path": str(target.relative_to(ROOT)).replace("\\", "/"),
        "dimensions": json.dumps(enlarged.size),
    })
write_csv(ROOT / "render" / "landmarks_8x_index.csv", landmark_rows)

TEXT_OBJECTS = {
    "O-T01": ("TEXT", "NODE_TEXT", "current_state_title", "当前状态", 17, 9.6),
    "O-T02": ("TEXT_FORMULA", "NODE_FORMULA", "current_state_variable", "状态变量 X_t", 17, 9.6),
    "O-T03": ("TEXT", "EDGE_LABEL", "proposal_edge_label", "提议", 27, 9.6),
    "O-T04": ("TEXT", "NODE_TEXT", "proposal_instruction", "按提议核抽取候选", 18, 9.6),
    "O-T05": ("TEXT_FORMULA", "NODE_FORMULA", "proposal_variable", "候选变量 Y", 18, 9.6),
    "O-T06": ("TEXT", "EDGE_LABEL", "calculate_edge_label", "计算", 28, 9.6),
    "O-T07": ("TEXT_FORMULA", "ANNOTATION", "acceptance_heading", "计算接受率（未归一化目标记为 pi_u 且正向流为正）", 19, 9.6),
    "O-T08": ("TEXT_FORMULA", "FORMULA_BLOCK", "acceptance_ratio_formula", "alpha_t(Y) 取 min{1 与 pi_u(Y)q(X_t|Y)/pi_u(X_t)q(Y|X_t)}", 20, 11.2),
    "O-T09": ("TEXT", "EDGE_LABEL", "decision_edge_label", "判定", 29, 9.6),
    "O-T10": ("TEXT_FORMULA", "NODE_TEXT", "decision_node", "抽取区间[0到1]的均匀变量U并判定U<=alpha_t(Y)?", 23, 9.6),
    "O-T11": ("TEXT", "EDGE_LABEL", "accept_edge_label", "接受", 30, 9.6),
    "O-T12": ("TEXT", "EDGE_LABEL", "reject_edge_label", "拒绝", 31, 9.6),
    "O-T13": ("TEXT", "NODE_TEXT", "accepted_node_title", "接受候选", 24, 9.6),
    "O-T14": ("TEXT_FORMULA", "NODE_FORMULA", "accepted_state_update", "X_{t+1} 取 Y", 24, 9.6),
    "O-T15": ("TEXT", "NODE_TEXT", "rejected_node_title", "拒绝并记录旧状态", 25, 9.6),
    "O-T16": ("TEXT_FORMULA", "NODE_FORMULA", "rejected_state_update", "X_{t+1} 保持 X_t", 25, 9.6),
    "O-T17": ("TEXT", "EDGE_LABEL", "self_loop_label", "拒绝后保持旧状态", 33, 9.6),
}


def glyph_parent(seqno: int, bbox) -> str:
    y0 = bbox[1]
    if seqno == 2:
        return "O-T01" if y0 < 82.0 else "O-T02"
    if seqno == 5:
        return "O-T04" if y0 < 127.0 else "O-T05"
    if seqno == 8:
        return "O-T07" if y0 < 178.0 else "O-T08"
    if seqno == 10:
        return "O-T08"
    if seqno == 13:
        return "O-T10"
    if seqno == 16:
        return "O-T13" if y0 < 318.0 else "O-T14"
    if seqno == 20:
        return "O-T15" if y0 < 318.0 else "O-T16"
    label_map = {25: "O-T03", 30: "O-T06", 35: "O-T09", 40: "O-T11", 45: "O-T12", 50: "O-T17"}
    if seqno in label_map:
        return label_map[seqno]
    raise RuntimeError(f"unmapped current-PDF glyph seqno={seqno} bbox={bbox}")


glyphs = []
for trace_index, trace in enumerate(traces):
    for char_index, ch in enumerate(trace["chars"]):
        cp, pdf_gid, origin, bbox = ch
        glyphs.append({
            "trace_index": trace_index,
            "char_index": char_index,
            "seqno": trace["seqno"],
            "font": trace["font"],
            "pdf_glyph_pt": float(trace["size"]),
            "color": tuple(float(v) for v in trace["color"]),
            "char": chr(cp),
            "codepoint": cp,
            "pdf_gid": pdf_gid,
            "origin": tuple(float(v) for v in origin),
            "pdf_bbox": tuple(float(v) for v in bbox),
            "parent_object_id": glyph_parent(trace["seqno"], bbox),
        })
assert len(glyphs) == 154
assert set(g["parent_object_id"] for g in glyphs) == set(TEXT_OBJECTS)

glyph_masks = []
for g in glyphs:
    pbox = px_box(g["pdf_bbox"], sx, sy, crop, pad=1)
    target = tuple(round(v * 255) for v in g["color"])
    glyph_masks.append(mask_from_color(base_arr, pbox, target, pad=0))
    g["vector_bbox_px"] = px_box(g["pdf_bbox"], sx, sy, crop, pad=0)

# Make every final-visible native pixel have at most one glyph owner.
owners = defaultdict(list)
for gi, mask in enumerate(glyph_masks):
    ys, xs = np.where(mask)
    for flat in ys.astype(np.int64) * W + xs.astype(np.int64):
        owners[int(flat)].append(gi)
for flat, gids in owners.items():
    if len(gids) < 2:
        continue
    y, x = divmod(flat, W)
    winner = min(
        gids,
        key=lambda gi: (
            ((x - (glyphs[gi]["vector_bbox_px"][0] + glyphs[gi]["vector_bbox_px"][2]) / 2) / max(1, glyphs[gi]["vector_bbox_px"][2] - glyphs[gi]["vector_bbox_px"][0])) ** 2
            + ((y - (glyphs[gi]["vector_bbox_px"][1] + glyphs[gi]["vector_bbox_px"][3]) / 2) / max(1, glyphs[gi]["vector_bbox_px"][3] - glyphs[gi]["vector_bbox_px"][1])) ** 2
        ),
    )
    for gi in gids:
        if gi != winner:
            glyph_masks[gi][y, x] = False

GRAPHIC_OBJECTS = {
    "O-G01": ("NODE_BORDER", "current_state_border", [0]),
    "O-G02": ("NODE_BORDER", "proposal_node_border", [1]),
    "O-G03": ("NODE_BORDER", "acceptance_ratio_border", [2]),
    "O-G04": ("MATH_RULE", "acceptance_ratio_fraction_rule", [3]),
    "O-G05": ("NODE_BORDER", "decision_diamond_border", [4]),
    "O-G06": ("NODE_BORDER", "accepted_node_border", [5]),
    "O-G07": ("NODE_BORDER", "rejected_double_node_border_final_visible", [6, 7]),
    "O-G08": ("LINE_ARROW", "proposal_arrow", [8, 9]),
    "O-G09": ("LINE_ARROW", "calculate_arrow", [11, 12]),
    "O-G10": ("LINE_ARROW", "decision_arrow", [14, 15]),
    "O-G11": ("LINE_ARROW", "accept_arrow", [17, 18]),
    "O-G12": ("LINE_ARROW", "reject_arrow", [20, 21]),
    "O-G13": ("LINE_ARROW", "rejection_self_loop_arrow", [23, 24]),
}
EXCLUDED_DRAWINGS = {10: "proposal label white background", 13: "calculate label white background", 16: "decision label white background", 19: "accept label white background", 22: "reject label white background", 25: "self-loop label white background"}
assert sorted([i for v in GRAPHIC_OBJECTS.values() for i in v[2]] + list(EXCLUDED_DRAWINGS)) == list(range(26))


def pxy(point):
    return point.x * sx - crop[0], point.y * sy - crop[1]


def cubic_points(p0, p1, p2, p3, count=96):
    result = []
    for t in np.linspace(0.0, 1.0, count):
        q = (1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1) + 3 * (1 - t) * t**2 * np.array(p2) + t**3 * np.array(p3)
        result.append(tuple(float(v) for v in q))
    return result


ARROWHEAD_DRAWING_INDICES = {9, 12, 15, 18, 21, 24}


def drawing_support(indices):
    image = Image.new("L", (W, H), 0)
    painter = ImageDraw.Draw(image)
    for drawing_index in indices:
        drawing = drawings[drawing_index]
        width = max(2, int(math.ceil((drawing.get("width") or 0.7) * sx)) + 3)
        polygon_points = []
        for item in drawing["items"]:
            kind = item[0]
            if kind == "l":
                a, b = pxy(item[1]), pxy(item[2])
                painter.line([a, b], fill=255, width=width, joint="curve")
                polygon_points.extend([a, b])
            elif kind == "c":
                points = cubic_points(pxy(item[1]), pxy(item[2]), pxy(item[3]), pxy(item[4]))
                painter.line(points, fill=255, width=width, joint="curve")
                polygon_points.extend(points)
            elif kind == "re":
                r = item[1]
                painter.rectangle([r.x0 * sx - crop[0], r.y0 * sy - crop[1], r.x1 * sx - crop[0], r.y1 * sy - crop[1]], outline=255, width=width)
            elif kind == "qu":
                q = item[1]
                points = [pxy(q.ul), pxy(q.ur), pxy(q.lr), pxy(q.ll), pxy(q.ul)]
                painter.line(points, fill=255, width=width, joint="curve")
                polygon_points.extend(points)
        if drawing_index in ARROWHEAD_DRAWING_INDICES and len(polygon_points) >= 3:
            painter.polygon(polygon_points, fill=255)
    return np.asarray(image) > 0


graphic_raw_candidates = {}
object_pdf_boxes = {}
for object_id, (_, _, indices) in GRAPHIC_OBJECTS.items():
    support = drawing_support(indices)
    stroke = next((drawings[i] for i in indices if drawings[i].get("color") is not None and tuple(drawings[i]["color"]) != (1.0, 1.0, 1.0)), drawings[indices[0]])
    target = tuple(round(float(v) * 255) for v in (stroke.get("color") or (0, 0, 0)))
    pdf_box = bbox_union([tuple(drawings[i]["rect"]) for i in indices])
    candidate = mask_from_color(base_arr, px_box(pdf_box, sx, sy, crop, pad=4), target, pad=0)
    graphic_raw_candidates[object_id] = candidate & ndimage.binary_dilation(support, iterations=2)
    object_pdf_boxes[object_id] = pdf_box

raw_graphic_union = np.zeros((H, W), dtype=bool)
for mask in graphic_raw_candidates.values():
    raw_graphic_union |= mask
for index, mask in enumerate(glyph_masks):
    glyph_masks[index] = mask & ~raw_graphic_union

LOW_PUNCTUATION = {",", ".", "：", "、", "。", "–"}
MATH_OPERATORS = {"=", "+", ">", "≤", "∣", "{", "}", "(", ")", "[", "]"}


def glyph_class(g):
    ch = g["char"]
    if g["pdf_glyph_pt"] < 8.0:
        return "NATURAL_SCRIPT", 15
    if ch in LOW_PUNCTUATION:
        return "LOW_PROFILE_PUNCTUATION", 4
    cp = ord(ch)
    if 0x4E00 <= cp <= 0x9FFF or ch in {"（", "）", "？"}:
        return "CJK_FULL", 30
    if ch.isdigit() or ch in {"𝑋", "𝑌", "𝑈"} or (ch.isascii() and ch.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ch in MATH_OPERATORS:
        return "MATH_OPERATOR", 22
    if ch.isalpha() or ch in {"𝛼", "𝜋", "𝑞", "𝑡"}:
        return "LATIN_GREEK_LOWER", 17
    return "MATH_SYMBOL", 22


glyph_rows = []
glyph_card_paths = []
for number, (g, mask) in enumerate(zip(glyphs, glyph_masks), start=1):
    glyph_id = f"G{number:03d}"
    klass, threshold = glyph_class(g)
    box = tight_bbox(mask)
    height = 0 if box is None else box[3] - box[1]
    width = 0 if box is None else box[2] - box[0]
    pixels = int(mask.sum())
    decision = pixels > 0 and height >= threshold
    mask_rel = f"glyphs/masks_1x/{glyph_id}.png"
    card_rel = f"glyphs/cards/{glyph_id}.png"
    save_mask(ROOT / mask_rel, mask)
    vector_box = clip_box(px_box(g["pdf_bbox"], sx, sy, crop, pad=8), W, H)
    patch = base.crop(vector_box)
    local = mask[vector_box[1]:vector_box[3], vector_box[0]:vector_box[2]]
    patch_overlay = overlay(patch, local)
    nearest = patch_overlay.resize((patch_overlay.width * 8, patch_overlay.height * 8), Image.Resampling.NEAREST)
    card = Image.new("RGB", (1100, 420), "white")
    painter = ImageDraw.Draw(card)
    painter.text((8, 8), f"{glyph_id} U+{g['codepoint']:04X} parent={g['parent_object_id']} class={klass} ink={width}x{height}px pixels={pixels} threshold={threshold}px machine={'PASS' if decision else 'FAIL'}", fill="black")
    card.paste(patch_overlay, (8, 52))
    thumb = fit_thumbnail(nearest, (1020, 350))
    card.paste(thumb, (70, 52))
    card.save(ROOT / card_rel, optimize=True)
    glyph_card_paths.append(ROOT / card_rel)
    glyph_rows.append({
        "glyph_id": glyph_id,
        "parent_object_id": g["parent_object_id"],
        "char": g["char"],
        "unicode": f"U+{g['codepoint']:04X}",
        "font": g["font"],
        "pdf_glyph_pt": g["pdf_glyph_pt"],
        "seqno": g["seqno"],
        "trace_index": g["trace_index"],
        "char_index": g["char_index"],
        "pdf_bbox": json.dumps(g["pdf_bbox"]),
        "ink_bbox_px": json.dumps(box),
        "ink_width_px": width,
        "ink_height_px": height,
        "ink_pixel_count": pixels,
        "script_class": klass,
        "threshold_px": threshold,
        "empty_mask": box is None,
        "machine_threshold_pass": decision,
        "mask_path": mask_rel,
        "card_path": card_rel,
    })

for sheet_no, start in enumerate(range(0, len(glyph_card_paths), 12), start=1):
    sheet = Image.new("RGB", (2400, 2520), "white")
    for k, path in enumerate(glyph_card_paths[start:start + 12]):
        im = Image.open(path).convert("RGB")
        im.thumbnail((1190, 410), Image.Resampling.LANCZOS)
        sheet.paste(im, ((k % 2) * 1200 + 5, (k // 2) * 420 + 5))
    sheet.save(ROOT / "glyphs" / "contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png", optimize=True)

object_masks = {}
for object_id in TEXT_OBJECTS:
    mask = np.zeros((H, W), dtype=bool)
    boxes = []
    for g, glyph_mask in zip(glyphs, glyph_masks):
        if g["parent_object_id"] == object_id:
            mask |= glyph_mask
            boxes.append(g["pdf_bbox"])
    object_masks[object_id] = mask
    object_pdf_boxes[object_id] = bbox_union(boxes)
clean_text_union = np.zeros((H, W), dtype=bool)
for object_id in TEXT_OBJECTS:
    clean_text_union |= object_masks[object_id]
for object_id in GRAPHIC_OBJECTS:
    object_masks[object_id] = graphic_raw_candidates[object_id] & ~clean_text_union

object_rows = []
object_card_paths = []
for object_id in sorted(object_masks):
    is_text = object_id in TEXT_OBJECTS
    if is_text:
        object_type, role, description, sample, source_line, declared_pt = TEXT_OBJECTS[object_id]
        drawing_indices = ""
        glyph_count = sum(g["parent_object_id"] == object_id for g in glyphs)
    else:
        object_type, description, indices = GRAPHIC_OBJECTS[object_id]
        role, sample, declared_pt = object_type, "", ""
        source_line = 21 if object_id == "O-G04" else ""
        drawing_indices = ";".join(str(i) for i in indices)
        glyph_count = 0
    mask = object_masks[object_id]
    box = tight_bbox(mask)
    pixels = int(mask.sum())
    if box is None:
        edge_distance, clip_pixels = -1, -1
        card_box = (0, 0, 1, 1)
    else:
        edge_distance = min(box[0], box[1], W - box[2], H - box[3])
        clip_pixels = int(np.count_nonzero(mask[0, :]) + np.count_nonzero(mask[-1, :]) + np.count_nonzero(mask[:, 0]) + np.count_nonzero(mask[:, -1]))
        card_box = clip_box((box[0] - 10, box[1] - 10, box[2] + 10, box[3] + 10), W, H)
    safe_name = object_id.replace("-", "_")
    mask_rel = f"objects/masks_1x/{safe_name}.png"
    card_rel = f"objects/cards/{safe_name}.png"
    save_mask(ROOT / mask_rel, mask)
    patch = base.crop(card_box)
    local_mask = mask[card_box[1]:card_box[3], card_box[0]:card_box[2]]
    patch_overlay = overlay(patch, local_mask)
    zoom_box = clip_box((card_box[0], card_box[1], min(card_box[0] + 48, card_box[2]), min(card_box[1] + 48, card_box[3])), W, H)
    zoom = base.crop(zoom_box)
    zoom_mask = mask[zoom_box[1]:zoom_box[3], zoom_box[0]:zoom_box[2]]
    zoom_overlay = overlay(zoom, zoom_mask).resize((zoom.width * 8, zoom.height * 8), Image.Resampling.NEAREST)
    width = max(900, patch_overlay.width, zoom_overlay.width)
    card = Image.new("RGB", (width, 66 + patch_overlay.height + zoom_overlay.height), "white")
    painter = ImageDraw.Draw(card)
    painter.text((8, 8), f"{object_id} {description} type={object_type} role={role} glyphs={glyph_count} ink_pixels={pixels} edge={edge_distance}px", fill="black")
    card.paste(patch_overlay, (0, 44))
    card.paste(zoom_overlay, (0, 44 + patch_overlay.height))
    card.save(ROOT / card_rel, optimize=True)
    object_card_paths.append(ROOT / card_rel)
    object_rows.append({
        "object_id": object_id,
        "safe_filename": safe_name,
        "object_type": object_type,
        "role": role,
        "description": description,
        "text_sample": sample,
        "source_line": source_line,
        "declared_pt": declared_pt,
        "pdf_bbox": json.dumps(object_pdf_boxes[object_id]),
        "drawing_indices": drawing_indices,
        "glyph_count": glyph_count,
        "ink_bbox_px": json.dumps(box),
        "mask_pixel_count": pixels,
        "clip_edge_distance_px": edge_distance,
        "clip_pixel_count": clip_pixels,
        "empty_mask": box is None,
        "mask_path": mask_rel,
        "card_path": card_rel,
    })

assert len(object_rows) == 30
assert sum(1 for r in object_rows if r["object_id"].startswith("O-T")) == 17
assert sum(1 for r in object_rows if r["object_id"].startswith("O-G")) == 13

for sheet_no, start in enumerate(range(0, len(object_card_paths), 8), start=1):
    sheet = Image.new("RGB", (2400, 2400), "white")
    for k, path in enumerate(object_card_paths[start:start + 8]):
        im = Image.open(path).convert("RGB")
        im.thumbnail((1180, 580), Image.Resampling.LANCZOS)
        sheet.paste(im, ((k % 2) * 1200 + 10, (k // 2) * 600 + 10))
    sheet.save(ROOT / "objects" / "contact_sheets" / f"object_contact_sheet_{sheet_no:02d}.png", optimize=True)

object_by_id = {r["object_id"]: r for r in object_rows}
peer_class_map = {
    "CJK_FULL": "CJK",
    "LATIN_UPPER_OR_DIGIT": "LATIN_UPPER_DIGIT",
    "LATIN_GREEK_LOWER": "LATIN_GREEK_LOWER",
    "MATH_OPERATOR": "MATH_OPERATOR",
    "MATH_SYMBOL": "MATH_SYMBOL",
}
element_medians = []
for object_id in TEXT_OBJECTS:
    by_class = defaultdict(list)
    for row in glyph_rows:
        if row["parent_object_id"] == object_id and row["script_class"] in peer_class_map:
            by_class[peer_class_map[row["script_class"]]].append(row["ink_height_px"])
    for peer_class, values in sorted(by_class.items()):
        element_medians.append({
            "element_id": object_id,
            "role": TEXT_OBJECTS[object_id][1],
            "peer_class": peer_class,
            "glyph_count": len(values),
            "median_h_px": float(np.median(values)),
        })

peer_groups = defaultdict(list)
for row in element_medians:
    peer_groups[(row["role"], row["peer_class"])].append(row)
peer_rows = []
for (role, peer_class), rows in sorted(peer_groups.items()):
    group_median = float(np.median([r["median_h_px"] for r in rows]))
    extreme = max(r["median_h_px"] for r in rows) / min(r["median_h_px"] for r in rows)
    for row in rows:
        ratio = row["median_h_px"] / group_median
        peer_rows.append({
            **row,
            "group_size": len(rows),
            "group_median_h_px": group_median,
            "ratio_to_group_median": ratio,
            "group_extreme_ratio": extreme,
            "machine_peer_pass": 0.92 <= ratio <= 1.08 and extreme <= 1.08,
        })


def median_for(role, peer_class):
    values = [r["median_h_px"] for r in element_medians if r["role"] == role and r["peer_class"] == peer_class]
    return None if not values else float(np.median(values))


base_cjk = median_for("NODE_TEXT", "CJK")
base_math_values = [v for pc in ("LATIN_UPPER_DIGIT", "LATIN_GREEK_LOWER", "MATH_OPERATOR") if (v := median_for("NODE_FORMULA", pc)) is not None]
base_math = None if not base_math_values else float(np.median(base_math_values))
role_specs = [
    ("EDGE_LABEL", "CJK", "NODE_TEXT", base_cjk, 0.95, 1.10, "ordinary edge annotation vs current node text"),
    ("ANNOTATION", "CJK", "NODE_TEXT", base_cjk, 0.95, 1.10, "ratio heading vs current node text"),
]
role_rows = []
for role, peer_class, base_role, base_value, lo, hi, reason in role_specs:
    value = median_for(role, peer_class)
    ratio = None if value is None or base_value is None else value / base_value
    role_rows.append({
        "role_id": f"ROLE{len(role_rows)+1:02d}",
        "role": role,
        "peer_class": peer_class,
        "role_median_h_px": value,
        "base_role": base_role,
        "base_median_h_px": base_value,
        "ratio": ratio,
        "allowed_min": lo,
        "allowed_max": hi,
        "machine_role_pass": ratio is not None and lo <= ratio <= hi,
        "reason": reason,
    })
formula_values = [r["median_h_px"] for r in element_medians if r["role"] == "FORMULA_BLOCK" and r["peer_class"] in {"LATIN_UPPER_DIGIT", "LATIN_GREEK_LOWER", "MATH_OPERATOR"}]
formula_median = None if not formula_values else float(np.median(formula_values))
formula_ratio = None if formula_median is None or base_math is None else formula_median / base_math
role_rows.append({
    "role_id": "ROLE03",
    "role": "FORMULA_BLOCK",
    "peer_class": "MATH_COMPARABLE",
    "role_median_h_px": formula_median,
    "base_role": "NODE_FORMULA",
    "base_median_h_px": base_math,
    "ratio": formula_ratio,
    "allowed_min": 1.00,
    "allowed_max": 1.18,
    "machine_role_pass": formula_ratio is not None and 1.00 <= formula_ratio <= 1.18,
    "reason": "11.2pt acceptance formula vs 9.6pt current node formulas",
})

object_ids = sorted(object_masks)
pair_expected = len(object_ids) * (len(object_ids) - 1) // 2
assert pair_expected == 435
coords = {object_id: np.argwhere(object_masks[object_id]) for object_id in object_ids}
trees = {object_id: cKDTree(coords[object_id]) if len(coords[object_id]) else None for object_id in object_ids}
text_ids = set(TEXT_OBJECTS)
border_ids = {"O-G01", "O-G02", "O-G03", "O-G05", "O-G06", "O-G07"}
edge_ids = {"O-G08", "O-G09", "O-G10", "O-G11", "O-G12", "O-G13"}
design_pairs = {
    frozenset(("O-T08", "O-G04")): "same-parent fraction rule",
    frozenset(("O-G08", "O-G01")): "proposal arrow starts at current-state border",
    frozenset(("O-G08", "O-G02")): "proposal arrow terminates at proposal border",
    frozenset(("O-G09", "O-G02")): "calculate arrow starts at proposal border",
    frozenset(("O-G09", "O-G03")): "calculate arrow terminates at acceptance border",
    frozenset(("O-G10", "O-G03")): "decision arrow starts at acceptance border",
    frozenset(("O-G10", "O-G05")): "decision arrow terminates at diamond border",
    frozenset(("O-G11", "O-G05")): "accept arrow starts at diamond border",
    frozenset(("O-G11", "O-G06")): "accept arrow terminates at accepted border",
    frozenset(("O-G12", "O-G05")): "reject arrow starts at diamond border",
    frozenset(("O-G12", "O-G07")): "reject arrow terminates at rejected border",
    frozenset(("O-G13", "O-G07")): "self-loop starts and terminates at rejected border",
}


def closest_points(aid, bid):
    ca, cb = coords[aid], coords[bid]
    if len(ca) == 0 or len(cb) == 0:
        return float("inf"), (0, 0), (0, 0)
    if len(ca) <= len(cb):
        distances, indices = trees[bid].query(ca, k=1)
        k = int(np.argmin(distances))
        return float(distances[k]), tuple(int(v) for v in ca[k]), tuple(int(v) for v in cb[int(indices[k])])
    distances, indices = trees[aid].query(cb, k=1)
    k = int(np.argmin(distances))
    return float(distances[k]), tuple(int(v) for v in ca[int(indices[k])]), tuple(int(v) for v in cb[k])


def relation_rule(aid, bid):
    pair = frozenset((aid, bid))
    if pair in design_pairs:
        return "DESIGN_WHITELIST", 0, design_pairs[pair]
    a_text, b_text = aid in text_ids, bid in text_ids
    if a_text and b_text:
        return "TEXT_TEXT_BBOX", 4, "independent text/formula semantic parents"
    other = bid if a_text else aid if b_text else None
    if other in border_ids:
        return "TEXT_FORMULA_NODE_BORDER", 5, "text/formula ink to final-visible node border"
    if other in edge_ids or other == "O-G04":
        return "TEXT_FORMULA_LINE_ARROW_RULE", 3, "text/formula ink to line/arrow/math rule"
    return "INDEPENDENT_FOREGROUND", 0, "independent non-text foregrounds require zero illegal intersection"


def pair_card(pair_id, aid, bid, ma, mb, point_a, point_b, metadata):
    box_a = tight_bbox(ma) or (0, 0, 1, 1)
    box_b = tight_bbox(mb) or (0, 0, 1, 1)
    union_box = clip_box(tuple(v for v in (min(box_a[0], box_b[0]) - 8, min(box_a[1], box_b[1]) - 8, max(box_a[2], box_b[2]) + 8, max(box_a[3], box_b[3]) + 8)), W, H)
    original = base.crop(union_box)
    local_a = ma[union_box[1]:union_box[3], union_box[0]:union_box[2]]
    local_b = mb[union_box[1]:union_box[3], union_box[0]:union_box[2]]
    arr = np.asarray(original.convert("RGB"), dtype=np.float32).copy()
    arr[local_a] = arr[local_a] * 0.35 + np.array([255, 30, 30]) * 0.65
    arr[local_b] = arr[local_b] * 0.35 + np.array([20, 210, 255]) * 0.65
    arr[local_a & local_b] = np.array([255, 220, 0])
    overview = Image.fromarray(np.uint8(np.clip(arr, 0, 255)), mode="RGB")
    overview.thumbnail((1180, 700), Image.Resampling.LANCZOS)
    endpoint_patches = []
    for cy, cx in (point_a, point_b):
        patch_box = clip_box((cx - 14, cy - 14, cx + 15, cy + 15), W, H)
        patch = base.crop(patch_box)
        patch_a = ma[patch_box[1]:patch_box[3], patch_box[0]:patch_box[2]]
        patch_b = mb[patch_box[1]:patch_box[3], patch_box[0]:patch_box[2]]
        patch_arr = np.asarray(patch.convert("RGB"), dtype=np.float32).copy()
        patch_arr[patch_a] = patch_arr[patch_a] * 0.25 + np.array([255, 20, 20]) * 0.75
        patch_arr[patch_b] = patch_arr[patch_b] * 0.25 + np.array([20, 210, 255]) * 0.75
        patch_arr[patch_a & patch_b] = np.array([255, 220, 0])
        endpoint_patches.append(Image.fromarray(np.uint8(np.clip(patch_arr, 0, 255)), mode="RGB").resize((patch.width * 8, patch.height * 8), Image.Resampling.NEAREST))
    card = Image.new("RGB", (1200, 54 + overview.height + max(p.height for p in endpoint_patches)), "white")
    painter = ImageDraw.Draw(card)
    painter.text((6, 6), f"{pair_id} {aid} vs {bid} {metadata}", fill="black")
    card.paste(overview, ((1200 - overview.width) // 2, 42))
    x = (1200 - sum(p.width for p in endpoint_patches)) // 2
    for patch in endpoint_patches:
        card.paste(patch, (x, 42 + overview.height))
        x += patch.width
    return card


pair_rows = []
critical_rows = []
pair_card_paths = []
for pair_index, (aid, bid) in enumerate(itertools.combinations(object_ids, 2), start=1):
    pair_id = f"P{pair_index:04d}"
    mask_a, mask_b = object_masks[aid], object_masks[bid]
    overlap_pixels = int(np.count_nonzero(mask_a & mask_b))
    distance, point_a, point_b = closest_points(aid, bid)
    raw_clearance = float("inf") if not math.isfinite(distance) else max(0.0, distance - 1.0)
    rule, threshold, rule_note = relation_rule(aid, bid)
    if rule == "TEXT_TEXT_BBOX":
        a_box = px_box(object_pdf_boxes[aid], sx, sy, crop, pad=0)
        b_box = px_box(object_pdf_boxes[bid], sx, sy, crop, pad=0)
        metric_clearance = bbox_clearance(a_box, b_box)
        metric = "vector_bbox_clearance_px"
    else:
        metric_clearance = raw_clearance
        metric = "raw_mask_pixel_square_clearance_px"
    design = rule == "DESIGN_WHITELIST"
    illegal_overlap = 0 if design else overlap_pixels
    machine_pass = bool(object_by_id[aid]["mask_pixel_count"] > 0 and object_by_id[bid]["mask_pixel_count"] > 0 and illegal_overlap == 0 and (design or metric_clearance >= threshold))
    critical = bool(not machine_pass or design or (threshold > 0 and metric_clearance < threshold + 3.0))
    metadata = f"rule={rule} overlap={overlap_pixels} illegal={illegal_overlap} clearance={metric_clearance:.3f} threshold={threshold} machine={'PASS' if machine_pass else 'FAIL'}"
    card_rel = f"pairs/cards/{pair_id}.png"
    card = pair_card(pair_id, aid, bid, mask_a, mask_b, point_a, point_b, metadata)
    card.save(ROOT / card_rel, optimize=True)
    pair_card_paths.append(ROOT / card_rel)
    critical_rel = "N/A"
    if critical:
        critical_rel = f"pairs/critical/{pair_id}_critical.png"
        card.save(ROOT / critical_rel, optimize=True)
        critical_rows.append({
            "pair_id": pair_id,
            "object_a": aid,
            "object_b": bid,
            "reason_for_critical": metadata,
            "card_path": critical_rel,
        })
    pair_rows.append({
        "pair_id": pair_id,
        "object_a": aid,
        "object_b": bid,
        "type_a": object_by_id[aid]["object_type"],
        "type_b": object_by_id[bid]["object_type"],
        "relation_rule": rule,
        "rule_note": rule_note,
        "design_whitelist": design,
        "raw_overlap_pixel_count": overlap_pixels,
        "illegal_overlap_pixel_count": illegal_overlap,
        "raw_mask_clearance_px": raw_clearance,
        "metric": metric,
        "metric_clearance_px": metric_clearance,
        "required_clearance_px": threshold,
        "closest_a_yx": json.dumps(point_a),
        "closest_b_yx": json.dumps(point_b),
        "machine_decision": "PASS" if machine_pass else "FAIL",
        "critical": critical,
        "mask_a_path": object_by_id[aid]["mask_path"],
        "mask_b_path": object_by_id[bid]["mask_path"],
        "pair_card_path": card_rel,
        "critical_card_path": critical_rel,
    })
    if pair_index % 50 == 0:
        print(f"pair cards {pair_index}/{pair_expected}", flush=True)

assert len(pair_rows) == pair_expected == len({row["pair_id"] for row in pair_rows})

for sheet_no, start in enumerate(range(0, len(pair_card_paths), 25), start=1):
    sheet = Image.new("RGB", (2500, 2500), "white")
    for k, path in enumerate(pair_card_paths[start:start + 25]):
        im = Image.open(path).convert("RGB")
        im.thumbnail((490, 490), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (500, 500), "white")
        cell.paste(im, ((500 - im.width) // 2, (500 - im.height) // 2))
        ImageDraw.Draw(cell).text((4, 4), path.stem, fill="black")
        sheet.paste(cell, ((k % 5) * 500, (k // 5) * 500))
    sheet.save(ROOT / "pairs" / "contact_sheets" / f"pair_contact_sheet_{sheet_no:02d}.png", optimize=True)

clip_rows = [{
    "object_id": row["object_id"],
    "mask_pixel_count": row["mask_pixel_count"],
    "clip_edge_distance_px": row["clip_edge_distance_px"],
    "clip_pixel_count": row["clip_pixel_count"],
    "machine_clip_pass": row["mask_pixel_count"] > 0 and row["clip_pixel_count"] == 0,
    "mask_path": row["mask_path"],
} for row in object_rows]

view_rows = [
    {"view_id": "VIEW01", "view_kind": "FULL_PAGE_NATIVE", "scale": "1x", "dpi": 300, "path": "render/full_page_fitz_native_300dpi.png", "machine_identity": sha256(fitz_full)},
    {"view_id": "VIEW02", "view_kind": "FIGURE_POPPLER_NATIVE", "scale": "1x", "dpi": 300, "path": "render/figure_poppler_native_300dpi_1x.png", "machine_identity": sha256(ROOT / "render" / "figure_poppler_native_300dpi_1x.png")},
    {"view_id": "VIEW03", "view_kind": "FIGURE_GRAYSCALE_NATIVE", "scale": "1x", "dpi": 300, "path": "render/figure_grayscale_native_300dpi_1x.png", "machine_identity": sha256(ROOT / "render" / "figure_grayscale_native_300dpi_1x.png")},
    {"view_id": "VIEW04", "view_kind": "NATIVE_LANDMARKS_NEAREST", "scale": "8x", "dpi": "native pixels enlarged by 8", "path": "render/landmarks_8x_index.csv", "machine_identity": sha256(ROOT / "render" / "landmarks_8x_index.csv")},
]

identity = {
    "uid": "FIG-P602-01",
    "evidence_round": "SA2_R3_V1_NATIVE_R1",
    "candidate_pdf_path": str(PDF.resolve()),
    "candidate_pdf_bytes": PDF.stat().st_size,
    "candidate_pdf_sha256": sha256(PDF),
    "candidate_pdf_mtime_ns": PDF.stat().st_mtime_ns,
    "source_path": str(FIG_SOURCE.resolve()),
    "source_bytes": FIG_SOURCE.stat().st_size,
    "source_sha256": sha256(FIG_SOURCE),
    "source_mtime_ns": FIG_SOURCE.stat().st_mtime_ns,
    "wrapper_path": str(WRAPPER.resolve()),
    "wrapper_bytes": WRAPPER.stat().st_size,
    "wrapper_sha256": sha256(WRAPPER),
    "build_start_path": str(BUILD_START.resolve()),
    "build_start_sha256": sha256(BUILD_START),
    "build_result_path": str(BUILD_RESULT.resolve()),
    "build_result_sha256": sha256(BUILD_RESULT),
    "pdf_page_count": doc.page_count,
    "page_size_pt": [page.rect.width, page.rect.height],
    "native_page_300_dimensions": [pix.width, pix.height],
    "figure_content_pdf_box": list(content_pdf_box),
    "figure_crop_margin_pt": margin_pt,
    "figure_crop_300_integer_xyxy": list(crop),
    "figure_crop_300_dimensions": [W, H],
    "renderer_measurement": "PyMuPDF 1.28.0 direct page pixmap at Matrix(300/72), no resize before integer crop",
    "renderer_crosscheck": "Poppler pdftoppm direct 300 dpi page render; same integer crop; no resize",
    "denominator_origin": "fresh enumeration of current one-page R3 v1 standalone candidate; caption is absent from this wrapper output",
}
write_json(ROOT / "identity" / "candidate_and_source_identity.json", identity)
write_json(ROOT / "identity" / "denominator_provenance.json", {
    "texttrace_records": len(traces),
    "visible_glyphs": len(glyph_rows),
    "drawing_records": len(drawings),
    "text_formula_semantic_objects": len(TEXT_OBJECTS),
    "graphic_semantic_objects": len(GRAPHIC_OBJECTS),
    "objects_total": len(object_rows),
    "pairs_formula": f"C({len(object_rows)},2)",
    "pairs_expected": pair_expected,
    "pairs_actual": len(pair_rows),
    "drawing_indices_accounted": sorted(i for v in GRAPHIC_OBJECTS.values() for i in v[2]),
    "drawing_indices_excluded_as_white_label_backgrounds": EXCLUDED_DRAWINGS,
    "caption_objects": 0,
    "caption_absence_basis": "current standalone PDF text layer and all texttrace records contain only the diagram body; wrapper suppresses the figure caption",
    "old_denominator_reused": False,
    "old_manual_judgments_reused": False,
})

write_csv(ROOT / "objects" / "object_manifest.csv", object_rows)
write_csv(ROOT / "glyphs" / "glyph_machine_measurements.csv", glyph_rows)
write_csv(ROOT / "pairs" / "all_pairs_machine.csv", pair_rows)
write_csv(ROOT / "pairs" / "critical_machine_index.csv", critical_rows, fields=["pair_id", "object_a", "object_b", "reason_for_critical", "card_path"])
write_csv(ROOT / "ledgers" / "peer_machine.csv", peer_rows)
write_csv(ROOT / "ledgers" / "role_machine.csv", role_rows)
write_csv(ROOT / "ledgers" / "clip_machine.csv", clip_rows)
write_csv(ROOT / "ledgers" / "view_machine.csv", view_rows)

expected_pngs = []
expected_pngs.extend(ROOT / row["mask_path"] for row in glyph_rows)
expected_pngs.extend(ROOT / row["card_path"] for row in glyph_rows)
expected_pngs.extend(ROOT / row["mask_path"] for row in object_rows)
expected_pngs.extend(ROOT / row["card_path"] for row in object_rows)
expected_pngs.extend(ROOT / row["pair_card_path"] for row in pair_rows)
png_open_failures = []
for path in expected_pngs:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_open_failures.append({"path": str(path), "error": repr(exc)})

summary = {
    "objects": len(object_rows),
    "text_formula_objects": len(TEXT_OBJECTS),
    "graphic_objects": len(GRAPHIC_OBJECTS),
    "glyphs": len(glyph_rows),
    "glyph_machine_failures": sum(not row["machine_threshold_pass"] for row in glyph_rows),
    "empty_glyph_masks": sum(row["empty_mask"] for row in glyph_rows),
    "pairs_expected": pair_expected,
    "pairs_actual": len(pair_rows),
    "pair_machine_failures": sum(row["machine_decision"] == "FAIL" for row in pair_rows),
    "critical_pairs": len(critical_rows),
    "empty_object_masks": sum(row["empty_mask"] for row in object_rows),
    "object_clip_failures": sum(not row["machine_clip_pass"] for row in clip_rows),
    "peer_rows": len(peer_rows),
    "peer_machine_failures": sum(not row["machine_peer_pass"] for row in peer_rows),
    "role_rows": len(role_rows),
    "role_machine_failures": sum(not row["machine_role_pass"] for row in role_rows),
    "views": len(view_rows),
    "glyph_contact_sheets": math.ceil(len(glyph_rows) / 12),
    "object_contact_sheets": math.ceil(len(object_rows) / 8),
    "pair_contact_sheets": math.ceil(len(pair_rows) / 25),
}
write_json(ROOT / "qa" / "machine_summary.json", summary)
write_json(ROOT / "qa" / "machine_coverage_check.json", {
    "png_files_checked": len(expected_pngs),
    "png_open_failures": png_open_failures,
    "object_ids_unique": len({r["object_id"] for r in object_rows}) == len(object_rows),
    "glyph_ids_unique": len({r["glyph_id"] for r in glyph_rows}) == len(glyph_rows),
    "pair_ids_unique": len({r["pair_id"] for r in pair_rows}) == len(pair_rows),
    "glyph_parent_ids_all_exist": all(r["parent_object_id"] in TEXT_OBJECTS for r in glyph_rows),
    "pair_denominator_closed": len(pair_rows) == pair_expected,
    "pair_denominator_formula": f"C({len(object_rows)},2)={pair_expected}",
    "foreground_drawing_indices_accounted": sorted(i for v in GRAPHIC_OBJECTS.values() for i in v[2]),
    "excluded_white_background_drawings": EXCLUDED_DRAWINGS,
})

print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
