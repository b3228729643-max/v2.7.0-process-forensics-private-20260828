from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa3_r101_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf")
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex")
CHAPTER_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex")
PAGE_INDEX = 650
PHYSICAL_PAGE = 651
PRINTED_PAGE = 638
FIGURE_CROP = (300, 1430, 2135, 2995)
STANDALONE_CROP = (300, 1430, 2135, 2910)
DPI = 300

for d in (
    "identity",
    "objects/masks_1x",
    "objects/cards",
    "objects/contact_sheets",
    "glyphs/masks_1x",
    "glyphs/cards",
    "glyphs/contact_sheets",
    "glyphs/calibration",
    "pairs/cards",
    "pairs/contact_sheets",
    "pairs/critical",
    "ledgers",
    "qa",
    "render",
):
    (ROOT / d).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def px_box(pdf_box, sx: float, sy: float, crop=FIGURE_CROP, pad: int = 0):
    x0, y0, x1, y1 = pdf_box
    return (
        math.floor(x0 * sx) - crop[0] - pad,
        math.floor(y0 * sy) - crop[1] - pad,
        math.ceil(x1 * sx) - crop[0] + pad,
        math.ceil(y1 * sy) - crop[1] + pad,
    )


def clip_box(box, width: int, height: int):
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def tight_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


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


def bbox_clearance(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float(math.hypot(dx, dy))


def local_color_mask(region: np.ndarray, target_rgb) -> np.ndarray:
    if region.size == 0:
        return np.zeros(region.shape[:2], dtype=bool)
    p = region.astype(np.float32)
    bg = np.median(p.reshape(-1, 3), axis=0)
    target = np.asarray(target_rgb, dtype=np.float32)
    v = bg - target
    denom = float(np.dot(v, v))
    if denom < 1.0:
        return np.zeros(region.shape[:2], dtype=bool)
    alpha = np.tensordot(bg - p, v, axes=([2], [0])) / denom
    recon = bg[None, None, :] - alpha[:, :, None] * v[None, None, :]
    residual = np.max(np.abs(p - recon), axis=2)
    contrast = np.max(np.abs(p - bg[None, None, :]), axis=2)
    return (contrast >= 20.0) & (alpha >= 0.045) & (alpha <= 1.35) & (residual <= 22.0)


def mask_from_color(arr: np.ndarray, box, target_rgb, pad=1) -> np.ndarray:
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = clip_box((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad), w, h)
    out = np.zeros((h, w), dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return out
    out[y0:y1, x0:x1] = local_color_mask(arr[y0:y1, x0:x1], target_rgb)
    return out


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path, dpi=(300, 300), optimize=True)


def overlay_image(base: Image.Image, mask: np.ndarray, color=(255, 0, 0), alpha=0.65) -> Image.Image:
    a = np.asarray(base.convert("RGB"), dtype=np.float32).copy()
    c = np.asarray(color, dtype=np.float32)
    a[mask] = a[mask] * (1.0 - alpha) + c * alpha
    return Image.fromarray(np.uint8(np.clip(a, 0, 255)), mode="RGB")


def paste_with_label(canvas, im, xy, label):
    canvas.paste(im, xy)
    d = ImageDraw.Draw(canvas)
    d.rectangle((xy[0], xy[1], xy[0] + max(110, len(label) * 7), xy[1] + 18), fill="white")
    d.text((xy[0] + 2, xy[1] + 2), label, fill="black")


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
matrix = fitz.Matrix(DPI / 72.0, DPI / 72.0)
pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
measure_full_path = ROOT / "render" / "measurement_base_page_651_300dpi_fitz_native.png"
pix.save(measure_full_path)
measure_full = Image.open(measure_full_path).convert("RGB")
base = measure_full.crop(FIGURE_CROP)
base.save(ROOT / "render" / "measurement_figure_crop_300dpi_fitz_native.png", dpi=(300, 300))
base_arr = np.asarray(base)
H, W = base_arr.shape[:2]
sx = pix.width / page.rect.width
sy = pix.height / page.rect.height

pdf_stat = PDF.stat()
source_stat = FIG_SOURCE.stat()
chapter_stat = CHAPTER_SOURCE.stat()
identity = {
    "uid": "FIG-P602-01",
    "official_round": "R101",
    "pdf_path": str(PDF),
    "pdf_bytes": pdf_stat.st_size,
    "pdf_sha256": sha256(PDF),
    "pdf_mtime_ns": pdf_stat.st_mtime_ns,
    "pdf_page_count": doc.page_count,
    "page_size_pt": [page.rect.width, page.rect.height],
    "physical_page": PHYSICAL_PAGE,
    "printed_page_verified_from_header": PRINTED_PAGE,
    "figure_number_verified_from_page_text": "32.5",
    "page_text_identity_tokens": ["638", "图32.5", "Metropolis–Hastings", "自环：保留"],
    "figure_source_path": str(FIG_SOURCE),
    "figure_source_bytes": source_stat.st_size,
    "figure_source_sha256": sha256(FIG_SOURCE),
    "figure_source_mtime_ns": source_stat.st_mtime_ns,
    "chapter_source_path": str(CHAPTER_SOURCE),
    "chapter_source_bytes": chapter_stat.st_size,
    "chapter_source_sha256": sha256(CHAPTER_SOURCE),
    "chapter_source_mtime_ns": chapter_stat.st_mtime_ns,
    "native_page_300_dimensions": [pix.width, pix.height],
    "native_page_200_dimensions": list(Image.open(ROOT / "render" / "full_page_200dpi.png").size),
    "figure_crop_300_integer_xyxy": list(FIGURE_CROP),
    "figure_crop_300_dimensions": [W, H],
    "standalone_crop_300_integer_xyxy": list(STANDALONE_CROP),
    "renderer_measurement": "PyMuPDF 1.28.0 direct PDF pixmap at Matrix(300/72), no resize",
    "renderer_mandatory_views": "Poppler pdftoppm direct PDF native rendering; integer crop only; no resize",
}
write_json(ROOT / "identity" / "official_candidate_identity.json", identity)

page_text = page.get_text("text")
loc_rows = []
for token in identity["page_text_identity_tokens"]:
    loc_rows.append({"token": token, "present": token.replace(" ", "") in page_text.replace(" ", ""), "basis": "official PDF page 651 text layer"})
write_csv(ROOT / "identity" / "page_location_checks.csv", loc_rows)


TEXT_OBJECTS = {
    "O-T01": ("TEXT", "NODE_TEXT", "current_state_title", "当前状态", 17, 9.6),
    "O-T02": ("FORMULA", "NODE_FORMULA", "current_state_formula", "X_t=x", 17, 9.6),
    "O-T03": ("TEXT", "EDGE_LABEL", "proposal_edge_label", "提议", 27, 9.6),
    "O-T04": ("TEXT_FORMULA", "NODE_TEXT", "proposal_node_text", "按 q(x,·) 提出候选", 18, 9.6),
    "O-T05": ("FORMULA", "NODE_FORMULA", "proposal_node_formula", "Y=y", 18, 9.6),
    "O-T06": ("TEXT", "EDGE_LABEL", "calculate_edge_label", "计算", 28, 9.6),
    "O-T07": ("TEXT_FORMULA", "ANNOTATION", "ratio_heading", "计算接受率（g(x,y)>0）", 19, 9.6),
    "O-T08": ("FORMULA", "FORMULA_BLOCK", "acceptance_ratio_formula", "alpha(x,y)=min{1,pi~.../pi~...}", 20, 11.2),
    "O-T09": ("TEXT", "EDGE_LABEL", "decision_edge_label", "判定", 29, 9.6),
    "O-T10": ("TEXT_FORMULA", "NODE_TEXT", "decision_node_text", "抽取 U~U(0,1) 并判定 U<=alpha(x,y)?", 23, 9.6),
    "O-T11": ("TEXT", "EDGE_LABEL", "accept_edge_label", "接受", 30, 9.6),
    "O-T12": ("TEXT", "EDGE_LABEL", "reject_edge_label", "拒绝", 31, 9.6),
    "O-T13": ("TEXT", "NODE_TEXT", "accepted_node_title", "接受候选", 24, 9.6),
    "O-T14": ("FORMULA", "NODE_FORMULA", "accepted_node_formula", "X_{t+1}=y", 24, 9.6),
    "O-T15": ("TEXT", "NODE_TEXT", "rejected_node_title", "拒绝并记录旧状态", 25, 9.6),
    "O-T16": ("FORMULA", "NODE_FORMULA", "rejected_node_formula", "X_{t+1}=x", 25, 9.6),
    "O-T17": ("TEXT_FORMULA", "EDGE_LABEL", "self_loop_label", "自环：保留 x", 33, 9.6),
    "O-T18": ("TEXT", "CAPTION_LABEL", "caption_figure_label", "图32.5", 35, 9.96264),
    "O-T19": ("TEXT", "CAPTION", "caption_text", "Metropolis-Hastings 一步更新：提议、接受与拒绝自环。", 35, 9.96264),
}


def parent_for(seqno, font, bbox):
    y0 = bbox[1]
    x0 = bbox[0]
    if seqno == 10:
        return "O-T01" if font.startswith("Noto") else "O-T02"
    if seqno == 13:
        return "O-T04" if y0 < 409 else "O-T05"
    if seqno == 16:
        return "O-T07" if y0 < 458 else "O-T08"
    if seqno == 18:
        return "O-T08"
    if seqno == 21:
        return "O-T10"
    if seqno == 24:
        return "O-T13" if font.startswith("Noto") else "O-T14"
    if seqno == 28:
        return "O-T15" if font.startswith("Noto") else "O-T16"
    if seqno == 33:
        return "O-T03"
    if seqno == 38:
        return "O-T06"
    if seqno == 43:
        return "O-T09"
    if seqno == 48:
        return "O-T11"
    if seqno == 53:
        return "O-T12"
    if seqno == 58:
        return "O-T17"
    if seqno == 59:
        return "O-T18" if x0 < 180 else "O-T19"
    raise RuntimeError(f"Unmapped figure char seqno={seqno} font={font} bbox={bbox}")


glyphs = []
for trace_index, trace in enumerate(page.get_texttrace()):
    for char_index, ch in enumerate(trace["chars"]):
        cp, gid, origin, bbox = ch
        if bbox[1] >= 345 and bbox[3] <= 718:
            parent = parent_for(trace["seqno"], trace["font"], bbox)
            glyphs.append(
                {
                    "trace_index": trace_index,
                    "char_index": char_index,
                    "seqno": trace["seqno"],
                    "font": trace["font"],
                    "pdf_glyph_pt": float(trace["size"]),
                    "color": tuple(float(v) for v in trace["color"]),
                    "char": chr(cp),
                    "codepoint": cp,
                    "gid": gid,
                    "origin": tuple(float(v) for v in origin),
                    "pdf_bbox": tuple(float(v) for v in bbox),
                    "parent_object_id": parent,
                }
            )

if len(glyphs) != 175:
    raise RuntimeError(f"Expected 175 visible glyphs, found {len(glyphs)}")

glyph_masks = []
for g in glyphs:
    box = px_box(g["pdf_bbox"], sx, sy, pad=1)
    color = tuple(round(v * 255) for v in g["color"])
    m = mask_from_color(base_arr, box, color, pad=0)
    glyph_masks.append(m)
    g["vector_bbox_px"] = px_box(g["pdf_bbox"], sx, sy, pad=0)

# The two \widetilde pi pairs are emitted as overlapping font glyph boxes. Split their
# shared native pixels by connected-component vertical position, preserving the top
# accent as its own glyph and the lower pi contour as the base glyph.
accent_pairs = []
for i in range(len(glyphs) - 1):
    if glyphs[i]["char"] == "˜" and glyphs[i + 1]["char"] == "𝜋" and glyphs[i]["parent_object_id"] == glyphs[i + 1]["parent_object_id"]:
        accent_pairs.append((i, i + 1))
for ai, pi_i in accent_pairs:
    union = glyph_masks[ai] | glyph_masks[pi_i]
    bb = tight_bbox(union)
    if bb is None:
        continue
    x0, y0, x1, y1 = bb
    lab, nlab = ndimage.label(union[y0:y1, x0:x1], structure=np.ones((3, 3), dtype=int))
    top = np.zeros_like(union)
    bottom = np.zeros_like(union)
    split_y = y0 + 0.38 * (y1 - y0)
    for k in range(1, nlab + 1):
        ys, xs = np.where(lab == k)
        target = top if float(ys.mean() + y0) < split_y else bottom
        target[ys + y0, xs + x0] = True
    glyph_masks[ai] = top
    glyph_masks[pi_i] = bottom

# Resolve any remaining same-pixel attribution by assigning each final-visible pixel
# to the closest glyph vector box centre. This enforces a unique glyph raw-mask map.
owners = defaultdict(list)
for i, m in enumerate(glyph_masks):
    ys, xs = np.where(m)
    for flat in ys.astype(np.int64) * W + xs.astype(np.int64):
        owners[int(flat)].append(i)
for flat, ids in owners.items():
    if len(ids) <= 1:
        continue
    y, x = divmod(flat, W)
    best = None
    best_score = float("inf")
    for i in ids:
        b = glyphs[i]["vector_bbox_px"]
        cx = (b[0] + b[2]) / 2.0
        cy = (b[1] + b[3]) / 2.0
        score = ((x - cx) / max(1.0, b[2] - b[0])) ** 2 + ((y - cy) / max(1.0, b[3] - b[1])) ** 2
        if score < best_score:
            best_score = score
            best = i
    for i in ids:
        if i != best:
            glyph_masks[i][y, x] = False


LOW_PUNCT = {",", ".", "：", "、", "。", "–"}
MATH_OPS = {"=", "+", ">", "≤", "∼", "⋅", "{", "}", "(", ")"}


def glyph_class(g):
    ch = g["char"]
    if g["pdf_glyph_pt"] < 8.0 and g["parent_object_id"] in {"O-T02", "O-T14", "O-T16"}:
        return "NATURAL_SCRIPT", 15
    if ch in LOW_PUNCT:
        return "LOW_PROFILE_PUNCTUATION", None
    if ch == "˜":
        return "MATH_ACCENT", 22
    cp = ord(ch)
    if (0x4E00 <= cp <= 0x9FFF) or ch in {"（", "）", "？"}:
        return "CJK_FULL", 30
    if ch.isdigit() or ch in {"𝑋", "𝑌", "𝑈"} or (ch.isascii() and ch.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ch in MATH_OPS:
        return "MATH_OPERATOR", 22
    if ch.isalpha() or ch in {"𝛼", "𝜋", "𝑥", "𝑦", "𝑞", "𝑔", "𝑡"}:
        return "LATIN_GREEK_LOWER", 17
    return "MATH_SYMBOL", 22


for i, (g, m) in enumerate(zip(glyphs, glyph_masks), start=1):
    gid = f"G{i:03d}"
    g["glyph_id"] = gid
    g["safe_filename"] = gid
    bb = tight_bbox(m)
    g["ink_bbox_px"] = bb
    g["ink_pixel_count"] = int(m.sum())
    g["h_ink_px"] = 0 if bb is None else bb[3] - bb[1]
    g["w_ink_px"] = 0 if bb is None else bb[2] - bb[0]
    cls, threshold = glyph_class(g)
    g["script_class"] = cls
    g["threshold_px"] = threshold
    parent = TEXT_OBJECTS[g["parent_object_id"]]
    g["role"] = parent[1]
    g["source_line"] = parent[4]
    g["declared_base_pt"] = parent[5]
    g["graphics_scale"] = 1.0
    g["effective_base_pt"] = parent[5]
    save_mask(ROOT / "glyphs" / "masks_1x" / f"{gid}.png", m)


def calibration_key(g):
    return (
        g["char"],
        g["font"],
        round(g["pdf_glyph_pt"], 3),
        tuple(round(v, 3) for v in g["color"]),
    )


punct_groups = defaultdict(list)
for i, g in enumerate(glyphs):
    if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
        punct_groups[calibration_key(g)].append(i)

external_needed = {k for k, ids in punct_groups.items() if len(ids) == 1}
external_matches = {}
if external_needed:
    for pno in range(doc.page_count):
        if pno == PAGE_INDEX:
            continue
        raw = doc[pno].get_text("rawdict")
        for block in raw["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    rgb255 = fitz.sRGB_to_rgb(span["color"])
                    color = tuple(round(float(v) / 255.0, 3) for v in rgb255)
                    for ch in span.get("chars", []):
                        key = (ch["c"], span["font"], round(float(span["size"]), 3), color)
                        if key in external_needed and key not in external_matches:
                            external_matches[key] = {
                                "page_index": pno,
                                "font": span["font"],
                                "size": float(span["size"]),
                                "color": tuple(float(v) / 255.0 for v in rgb255),
                                "bbox": tuple(float(v) for v in ch["bbox"]),
                                "char": ch["c"],
                            }
        if len(external_matches) == len(external_needed):
            break

calibration_rows = []
calibration_cache = {}
for key, ids in punct_groups.items():
    if len(ids) >= 2:
        heights = [glyphs[j]["h_ink_px"] for j in ids]
        areas = [glyphs[j]["ink_pixel_count"] for j in ids]
        for j in ids:
            peer_h = [glyphs[k]["h_ink_px"] for k in ids if k != j]
            peer_a = [glyphs[k]["ink_pixel_count"] for k in ids if k != j]
            glyphs[j]["calibration_source"] = "same-figure same-codepoint/font/size peers: " + ";".join(glyphs[k]["glyph_id"] for k in ids if k != j)
            glyphs[j]["calibration_h_px"] = float(np.median(peer_h))
            glyphs[j]["calibration_area_px"] = float(np.median(peer_a))
    else:
        j = ids[0]
        match = external_matches.get(key)
        if match is None:
            glyphs[j]["calibration_source"] = "MISSING"
            glyphs[j]["calibration_h_px"] = None
            glyphs[j]["calibration_area_px"] = None
            continue
        pno = match["page_index"]
        if pno not in calibration_cache:
            cpix = doc[pno].get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
            calibration_cache[pno] = (cpix, Image.frombytes("RGB", (cpix.width, cpix.height), cpix.samples))
        cpix, cim = calibration_cache[pno]
        ch_bbox = match["bbox"]
        box = (
            math.floor(ch_bbox[0] * cpix.width / doc[pno].rect.width) - 1,
            math.floor(ch_bbox[1] * cpix.height / doc[pno].rect.height) - 1,
            math.ceil(ch_bbox[2] * cpix.width / doc[pno].rect.width) + 1,
            math.ceil(ch_bbox[3] * cpix.height / doc[pno].rect.height) + 1,
        )
        box = clip_box(box, cpix.width, cpix.height)
        roi = np.asarray(cim)[box[1]:box[3], box[0]:box[2]]
        cm = local_color_mask(roi, tuple(round(float(v) * 255) for v in match["color"]))
        cbb = tight_bbox(cm)
        chh = 0 if cbb is None else cbb[3] - cbb[1]
        ca = int(cm.sum())
        source = f"official PDF physical page {pno + 1}, same codepoint/font/color/size, bbox={tuple(round(v,3) for v in ch_bbox)}"
        glyphs[j]["calibration_source"] = source
        glyphs[j]["calibration_h_px"] = chh
        glyphs[j]["calibration_area_px"] = ca
        cbase = Image.fromarray(roi, mode="RGB")
        cover = overlay_image(cbase, cm)
        monly = Image.fromarray(np.where(cm, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        scale8 = (max(1, cbase.width * 8), max(1, cbase.height * 8))
        card = Image.new("RGB", (scale8[0] * 3, scale8[1] + 24), "white")
        paste_with_label(card, cbase.resize(scale8, Image.Resampling.NEAREST), (0, 24), "ORIGINAL 8x")
        paste_with_label(card, cover.resize(scale8, Image.Resampling.NEAREST), (scale8[0], 24), "OVERLAY 8x")
        paste_with_label(card, monly.resize(scale8, Image.Resampling.NEAREST), (scale8[0] * 2, 24), "MASK ONLY 8x")
        card.save(ROOT / "glyphs" / "calibration" / f"{glyphs[j]['glyph_id']}_calibration.png", optimize=True)
        calibration_rows.append(
            {
                "target_glyph_id": glyphs[j]["glyph_id"],
                "codepoint": f"U+{glyphs[j]['codepoint']:04X}",
                "font": glyphs[j]["font"],
                "size_pt": glyphs[j]["pdf_glyph_pt"],
                "calibration_physical_page": pno + 1,
                "calibration_bbox_pdf": json.dumps(ch_bbox),
                "calibration_h_ink_px": chh,
                "calibration_area_px": ca,
                "card": f"glyphs/calibration/{glyphs[j]['glyph_id']}_calibration.png",
            }
        )

for g in glyphs:
    if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
        ch = g.get("calibration_h_px")
        ca = g.get("calibration_area_px")
        g["calibration_h_ratio"] = None if not ch else g["h_ink_px"] / ch
        g["calibration_area_ratio"] = None if not ca else g["ink_pixel_count"] / ca
        g["machine_threshold_pass"] = bool(
            g["ink_pixel_count"] > 0
            and g["calibration_h_ratio"] is not None
            and 0.92 <= g["calibration_h_ratio"] <= 1.08
            and 0.92 <= g["calibration_area_ratio"] <= 1.08
        )
    else:
        g["calibration_source"] = "N/A"
        g["calibration_h_px"] = None
        g["calibration_area_px"] = None
        g["calibration_h_ratio"] = None
        g["calibration_area_ratio"] = None
        g["machine_threshold_pass"] = bool(g["ink_pixel_count"] > 0 and g["h_ink_px"] >= g["threshold_px"])


# Glyph cards and 100% contact sheets.
glyph_card_paths = []
for g, m in zip(glyphs, glyph_masks):
    b = g["vector_bbox_px"]
    rb = clip_box((b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4), W, H)
    ori = base.crop(rb)
    lm = m[rb[1]:rb[3], rb[0]:rb[2]]
    over = overlay_image(ori, lm)
    only = Image.fromarray(np.where(lm, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    scale8 = (max(1, ori.width * 8), max(1, ori.height * 8))
    panels = [ori.resize(scale8, Image.Resampling.NEAREST), over.resize(scale8, Image.Resampling.NEAREST), only.resize(scale8, Image.Resampling.NEAREST)]
    card = Image.new("RGB", (scale8[0] * 3, scale8[1] + 28), "white")
    d = ImageDraw.Draw(card)
    d.text((2, 2), f"{g['glyph_id']} U+{g['codepoint']:04X} parent={g['parent_object_id']} H={g['h_ink_px']} area={g['ink_pixel_count']} threshold={g['threshold_px']}", fill="black")
    for k, (panel, label) in enumerate(zip(panels, ("ORIGINAL 8x", "TARGET OVERLAY 8x", "MASK ONLY 8x"))):
        paste_with_label(card, panel, (k * scale8[0], 28), label)
    cpath = ROOT / "glyphs" / "cards" / f"{g['glyph_id']}.png"
    card.save(cpath, optimize=True)
    glyph_card_paths.append(cpath)

for sheet_no, start in enumerate(range(0, len(glyph_card_paths), 12), start=1):
    paths = glyph_card_paths[start:start + 12]
    cells = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        thumb = im.copy()
        thumb.thumbnail((1230, 430), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (1240, 440), "white")
        cell.paste(thumb, (5, 5))
        cells.append(cell)
    sheet = Image.new("RGB", (2480, 2640), "white")
    for k, cell in enumerate(cells):
        sheet.paste(cell, ((k % 2) * 1240, (k // 2) * 440))
    sheet.save(ROOT / "glyphs" / "contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png", optimize=True)


drawings = page.get_drawings()


GRAPHIC_OBJECTS = {
    "O-G01": ("NODE_BORDER", "current_state_border", [2]),
    "O-G02": ("NODE_BORDER", "proposal_node_border", [3]),
    "O-G03": ("NODE_BORDER", "ratio_node_border", [4]),
    "O-G04": ("MATH_RULE", "acceptance_ratio_fraction_rule", [5]),
    "O-G05": ("NODE_BORDER", "decision_diamond_border", [6]),
    "O-G06": ("NODE_BORDER", "accepted_node_border", [7]),
    "O-G07": ("NODE_BORDER", "rejected_double_node_border_final_visible", [8, 9]),
    "O-G08": ("LINE_ARROW", "proposal_arrow", [10, 11]),
    "O-G09": ("LINE_ARROW", "calculate_arrow", [13, 14]),
    "O-G10": ("LINE_ARROW", "decision_arrow", [16, 17]),
    "O-G11": ("LINE_ARROW", "accept_arrow", [19, 20]),
    "O-G12": ("LINE_ARROW", "reject_arrow", [22, 23]),
    "O-G13": ("LINE_ARROW", "rejection_self_loop_arrow", [25, 26]),
}


def pxy(p):
    return (p.x * sx - FIGURE_CROP[0], p.y * sy - FIGURE_CROP[1])


def cubic_points(p0, p1, p2, p3, n=80):
    out = []
    for t in np.linspace(0.0, 1.0, n):
        q = (1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1) + 3 * (1 - t) * t ** 2 * np.array(p2) + t ** 3 * np.array(p3)
        out.append(tuple(float(v) for v in q))
    return out


def drawing_support(indices):
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for idx in indices:
        dr = drawings[idx]
        width = max(2, int(math.ceil((dr.get("width") or 0.7) * sx)) + 3)
        arrowhead = idx in {11, 14, 17, 20, 23, 26}
        poly_points = []
        for item in dr["items"]:
            kind = item[0]
            if kind == "l":
                a, b = pxy(item[1]), pxy(item[2])
                d.line([a, b], fill=255, width=width, joint="curve")
                poly_points.extend([a, b])
            elif kind == "c":
                pts = cubic_points(pxy(item[1]), pxy(item[2]), pxy(item[3]), pxy(item[4]))
                d.line(pts, fill=255, width=width, joint="curve")
                poly_points.extend(pts)
            elif kind == "re":
                r = item[1]
                box = [r.x0 * sx - FIGURE_CROP[0], r.y0 * sy - FIGURE_CROP[1], r.x1 * sx - FIGURE_CROP[0], r.y1 * sy - FIGURE_CROP[1]]
                d.rectangle(box, outline=255, width=width)
            elif kind == "qu":
                q = item[1]
                pts = [pxy(q.ul), pxy(q.ur), pxy(q.lr), pxy(q.ll), pxy(q.ul)]
                d.line(pts, fill=255, width=width, joint="curve")
                poly_points.extend(pts)
        if arrowhead and len(poly_points) >= 3:
            d.polygon(poly_points, fill=255)
    return np.asarray(img) > 0


object_masks = {}
object_rows = []
object_pdf_boxes = {}
for oid, (otype, role, desc, text_sample, source_line, declared) in [
    (k, (v[0], v[1], v[2], v[3], v[4], v[5])) for k, v in TEXT_OBJECTS.items()
]:
    inds = [i for i, g in enumerate(glyphs) if g["parent_object_id"] == oid]
    m = np.zeros((H, W), dtype=bool)
    pdf_boxes = []
    for i in inds:
        m |= glyph_masks[i]
        pdf_boxes.append(glyphs[i]["pdf_bbox"])
    object_masks[oid] = m
    object_pdf_boxes[oid] = bbox_union(pdf_boxes)
    object_rows.append(
        {
            "object_id": oid,
            "safe_filename": oid.replace("-", "_"),
            "object_type": otype,
            "role": role,
            "description": desc,
            "semantic_parent": oid,
            "text_sample": text_sample,
            "source_line": source_line,
            "declared_pt": declared,
            "graphics_scale": 1.0,
            "effective_pt": declared,
            "pdf_bbox": json.dumps(object_pdf_boxes[oid]),
            "drawing_indices": "",
            "glyph_count": len(inds),
        }
    )

all_text_mask = np.zeros((H, W), dtype=bool)
for oid in TEXT_OBJECTS:
    all_text_mask |= object_masks[oid]

graphic_raw_candidates = {}
for oid, (otype, desc, indices) in GRAPHIC_OBJECTS.items():
    support = drawing_support(indices)
    stroke_drawing = next((drawings[i] for i in indices if drawings[i].get("color") is not None and tuple(drawings[i].get("color")) != (1.0, 1.0, 1.0)), drawings[indices[0]])
    target = tuple(round(float(v) * 255) for v in (stroke_drawing.get("color") or (0, 0, 0)))
    pdf_rects = [tuple(drawings[i]["rect"]) for i in indices]
    pdf_box = bbox_union(pdf_rects)
    pbox = px_box(pdf_box, sx, sy, pad=4)
    candidate = mask_from_color(base_arr, pbox, target, pad=0)
    raw_m = candidate & ndimage.binary_dilation(support, iterations=2)
    graphic_raw_candidates[oid] = raw_m
    m = raw_m.copy()
    m &= ~all_text_mask
    object_masks[oid] = m
    object_pdf_boxes[oid] = pdf_box
    object_rows.append(
        {
            "object_id": oid,
            "safe_filename": oid.replace("-", "_"),
            "object_type": otype,
            "role": otype,
            "description": desc,
            "semantic_parent": "O-T08" if oid == "O-G04" else "FIG-P602-01",
            "text_sample": "",
            "source_line": 21 if oid == "O-G04" else "",
            "declared_pt": "",
            "graphics_scale": 1.0,
            "effective_pt": "",
            "pdf_bbox": json.dumps(pdf_box),
            "drawing_indices": ";".join(str(i) for i in indices),
            "glyph_count": 0,
        }
    )

# Enforce glyph-mask purity against every visible vector foreground path. The first
# graphic pass intentionally kept a pre-text-subtraction candidate so a gray glyph
# near a gray border cannot absorb a border anti-alias pixel. Rebuild text parents and
# then rebuild final-visible graphics after this subtraction.
raw_graphic_union = np.zeros((H, W), dtype=bool)
for m in graphic_raw_candidates.values():
    raw_graphic_union |= m
for g, m in zip(glyphs, glyph_masks):
    m &= ~raw_graphic_union
    bb = tight_bbox(m)
    g["ink_bbox_px"] = bb
    g["ink_pixel_count"] = int(m.sum())
    g["h_ink_px"] = 0 if bb is None else bb[3] - bb[1]
    g["w_ink_px"] = 0 if bb is None else bb[2] - bb[0]
    if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
        ch = g.get("calibration_h_px")
        ca = g.get("calibration_area_px")
        g["calibration_h_ratio"] = None if not ch else g["h_ink_px"] / ch
        g["calibration_area_ratio"] = None if not ca else g["ink_pixel_count"] / ca
        g["machine_threshold_pass"] = bool(
            g["ink_pixel_count"] > 0
            and g["calibration_h_ratio"] is not None
            and 0.92 <= g["calibration_h_ratio"] <= 1.08
            and 0.92 <= g["calibration_area_ratio"] <= 1.08
        )
    else:
        g["machine_threshold_pass"] = bool(g["ink_pixel_count"] > 0 and g["h_ink_px"] >= g["threshold_px"])
    save_mask(ROOT / "glyphs" / "masks_1x" / f"{g['glyph_id']}.png", m)

for oid in TEXT_OBJECTS:
    inds = [i for i, g in enumerate(glyphs) if g["parent_object_id"] == oid]
    m = np.zeros((H, W), dtype=bool)
    for i in inds:
        m |= glyph_masks[i]
    object_masks[oid] = m

clean_text_mask = np.zeros((H, W), dtype=bool)
for oid in TEXT_OBJECTS:
    clean_text_mask |= object_masks[oid]
for oid in GRAPHIC_OBJECTS:
    object_masks[oid] = graphic_raw_candidates[oid] & ~clean_text_mask

# Overwrite glyph cards and 100% contact sheets with the purified masks.
glyph_card_paths = []
for g, m in zip(glyphs, glyph_masks):
    b = g["vector_bbox_px"]
    rb = clip_box((b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4), W, H)
    ori = base.crop(rb)
    lm = m[rb[1]:rb[3], rb[0]:rb[2]]
    over = overlay_image(ori, lm)
    only = Image.fromarray(np.where(lm, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    scale8 = (max(1, ori.width * 8), max(1, ori.height * 8))
    panels = [ori.resize(scale8, Image.Resampling.NEAREST), over.resize(scale8, Image.Resampling.NEAREST), only.resize(scale8, Image.Resampling.NEAREST)]
    card = Image.new("RGB", (scale8[0] * 3, scale8[1] + 28), "white")
    d = ImageDraw.Draw(card)
    d.text((2, 2), f"{g['glyph_id']} U+{g['codepoint']:04X} parent={g['parent_object_id']} H={g['h_ink_px']} area={g['ink_pixel_count']} threshold={g['threshold_px']}", fill="black")
    for k, (panel, label) in enumerate(zip(panels, ("ORIGINAL 8x", "TARGET OVERLAY 8x", "MASK ONLY 8x"))):
        paste_with_label(card, panel, (k * scale8[0], 28), label)
    cpath = ROOT / "glyphs" / "cards" / f"{g['glyph_id']}.png"
    card.save(cpath, optimize=True)
    glyph_card_paths.append(cpath)

for sheet_no, start in enumerate(range(0, len(glyph_card_paths), 12), start=1):
    paths = glyph_card_paths[start:start + 12]
    cells = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        thumb = im.copy()
        thumb.thumbnail((1230, 430), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (1240, 440), "white")
        cell.paste(thumb, (5, 5))
        cells.append(cell)
    sheet = Image.new("RGB", (2480, 2640), "white")
    for k, cell in enumerate(cells):
        sheet.paste(cell, ((k % 2) * 1240, (k // 2) * 440))
    sheet.save(ROOT / "glyphs" / "contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png", optimize=True)

object_rows.sort(key=lambda r: r["object_id"])
for r in object_rows:
    oid = r["object_id"]
    m = object_masks[oid]
    bb = tight_bbox(m)
    r["mask_bbox_px"] = json.dumps(bb)
    r["mask_pixel_count"] = int(m.sum())
    r["empty_mask"] = bb is None
    if bb is None:
        r["clip_edge_distance_px"] = -1
        r["clip_pixel_count"] = -1
    else:
        r["clip_edge_distance_px"] = min(bb[0], bb[1], W - bb[2], H - bb[3])
        r["clip_pixel_count"] = int(np.count_nonzero(m[0, :]) + np.count_nonzero(m[-1, :]) + np.count_nonzero(m[:, 0]) + np.count_nonzero(m[:, -1]))
    save_mask(ROOT / "objects" / "masks_1x" / f"{r['safe_filename']}.png", m)

object_card_paths = []
for r in object_rows:
    oid = r["object_id"]
    m = object_masks[oid]
    bb = tight_bbox(m) or (0, 0, 1, 1)
    rb = clip_box((bb[0] - 8, bb[1] - 8, bb[2] + 8, bb[3] + 8), W, H)
    ori = base.crop(rb)
    lm = m[rb[1]:rb[3], rb[0]:rb[2]]
    over = overlay_image(ori, lm)
    only = Image.fromarray(np.where(lm, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    patch = clip_box((bb[0] - 4, bb[1] - 4, min(bb[0] + 44, bb[2] + 4), min(bb[1] + 44, bb[3] + 4)), W, H)
    pbase = base.crop(patch)
    pm = m[patch[1]:patch[3], patch[0]:patch[2]]
    pover = overlay_image(pbase, pm).resize((pbase.width * 8, pbase.height * 8), Image.Resampling.NEAREST)
    width = max(ori.width, pover.width)
    card = Image.new("RGB", (width, 32 + ori.height * 3 + pover.height), "white")
    d = ImageDraw.Draw(card)
    d.text((2, 2), f"{oid} {r['description']} pixels={r['mask_pixel_count']} bbox={bb}", fill="black")
    paste_with_label(card, ori, (0, 32), "ORIGINAL 1x")
    paste_with_label(card, over, (0, 32 + ori.height), "TARGET OVERLAY 1x")
    paste_with_label(card, only, (0, 32 + ori.height * 2), "MASK ONLY 1x")
    paste_with_label(card, pover, (0, 32 + ori.height * 3), "DETAIL 8x nearest")
    cpath = ROOT / "objects" / "cards" / f"{r['safe_filename']}.png"
    card.save(cpath, optimize=True)
    object_card_paths.append(cpath)

for sheet_no, start in enumerate(range(0, len(object_card_paths), 8), start=1):
    paths = object_card_paths[start:start + 8]
    sheet = Image.new("RGB", (2400, 2400), "white")
    for k, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        im.thumbnail((1180, 580), Image.Resampling.LANCZOS)
        sheet.paste(im, ((k % 2) * 1200 + 10, (k // 2) * 600 + 10))
    sheet.save(ROOT / "objects" / "contact_sheets" / f"object_contact_sheet_{sheet_no:02d}.png", optimize=True)


# Measurement overlay with every glyph and semantic object ID.
ov = base.copy()
od = ImageDraw.Draw(ov)
for g in glyphs:
    b = g["vector_bbox_px"]
    od.rectangle(b, outline=(230, 40, 40), width=1)
    od.text((b[0], max(0, b[1] - 9)), g["glyph_id"], fill=(180, 0, 0))
for r in object_rows:
    bb = tight_bbox(object_masks[r["object_id"]])
    if bb:
        od.rectangle(bb, outline=(0, 120, 220), width=2)
        od.text((bb[0], bb[1]), r["object_id"], fill=(0, 70, 160))
ov.save(ROOT / "render" / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300), optimize=True)


# Machine source-font audit.
font_rows = []
for r in object_rows:
    if not r["object_id"].startswith("O-T"):
        continue
    effective = float(r["effective_pt"])
    font_rows.append(
        {
            "element_id": r["object_id"],
            "role": r["role"],
            "source_file": str(FIG_SOURCE),
            "source_line": r["source_line"],
            "declared_pt": r["declared_pt"],
            "graphics_scale": r["graphics_scale"],
            "effective_pt": effective,
            "pdf_trace_size_range_pt": f"{min(g['pdf_glyph_pt'] for g in glyphs if g['parent_object_id']==r['object_id']):.5f}-{max(g['pdf_glyph_pt'] for g in glyphs if g['parent_object_id']==r['object_id']):.5f}",
            "source_font_pass": effective >= 9.5,
            "reason": "explicit 9.6pt every-node / 11.2pt local formula / native PDF caption trace; graphics scale 1.0; natural scripts separately allowed",
        }
    )


# Glyph machine ledger.
glyph_rows = []
for g in glyphs:
    glyph_rows.append(
        {
            "glyph_id": g["glyph_id"],
            "safe_filename": g["safe_filename"],
            "parent_object_id": g["parent_object_id"],
            "role": g["role"],
            "char": g["char"],
            "codepoint": f"U+{g['codepoint']:04X}",
            "font": g["font"],
            "gid": g["gid"],
            "source_line": g["source_line"],
            "declared_base_pt": g["declared_base_pt"],
            "graphics_scale": g["graphics_scale"],
            "effective_base_pt": g["effective_base_pt"],
            "pdf_glyph_pt": g["pdf_glyph_pt"],
            "script_class": g["script_class"],
            "pdf_bbox": json.dumps(g["pdf_bbox"]),
            "vector_bbox_px": json.dumps(g["vector_bbox_px"]),
            "ink_bbox_px": json.dumps(g["ink_bbox_px"]),
            "h_ink_px": g["h_ink_px"],
            "w_ink_px": g["w_ink_px"],
            "ink_pixel_count": g["ink_pixel_count"],
            "threshold_px": g["threshold_px"],
            "calibration_source": g["calibration_source"],
            "calibration_h_px": g["calibration_h_px"],
            "calibration_area_px": g["calibration_area_px"],
            "calibration_h_ratio": g["calibration_h_ratio"],
            "calibration_area_ratio": g["calibration_area_ratio"],
            "empty_mask": g["ink_pixel_count"] == 0,
            "machine_threshold_pass": g["machine_threshold_pass"],
            "mask_path": f"glyphs/masks_1x/{g['glyph_id']}.png",
            "card_path": f"glyphs/cards/{g['glyph_id']}.png",
        }
    )


# Peer and role machine measurements use semantic-element medians per comparable
# glyph class, excluding low-profile punctuation and natural scripts.
peer_class_map = {
    "CJK_FULL": "CJK",
    "LATIN_UPPER_OR_DIGIT": "LATIN_UPPER_DIGIT",
    "LATIN_GREEK_LOWER": "LATIN_GREEK_LOWER",
    "MATH_OPERATOR": "MATH_OPERATOR",
    "MATH_ACCENT": "MATH_ACCENT",
    "MATH_SYMBOL": "MATH_SYMBOL",
}
element_medians = []
for oid in TEXT_OBJECTS:
    by_class = defaultdict(list)
    for g in glyphs:
        if g["parent_object_id"] == oid and g["script_class"] in peer_class_map:
            by_class[peer_class_map[g["script_class"]]].append(g["h_ink_px"])
    for pc, vals in by_class.items():
        element_medians.append(
            {
                "element_id": oid,
                "role": TEXT_OBJECTS[oid][1],
                "peer_class": pc,
                "glyph_count": len(vals),
                "median_h_px": float(np.median(vals)),
            }
        )

role_groups = defaultdict(list)
for row in element_medians:
    role_groups[(row["role"], row["peer_class"])].append(row)
peer_rows = []
for key, rows in sorted(role_groups.items()):
    med = float(np.median([r["median_h_px"] for r in rows]))
    extreme = max(r["median_h_px"] for r in rows) / min(r["median_h_px"] for r in rows)
    for r in rows:
        ratio = r["median_h_px"] / med
        peer_rows.append(
            {
                **r,
                "group_median_h_px": med,
                "ratio_to_group_median": ratio,
                "group_extreme_ratio": extreme,
                "machine_peer_pass": 0.92 <= ratio <= 1.08 and extreme <= 1.08,
            }
        )

def median_for(role, pc):
    vals = [r["median_h_px"] for r in element_medians if r["role"] == role and r["peer_class"] == pc]
    return None if not vals else float(np.median(vals))

role_rows = []
base_cjk = median_for("NODE_TEXT", "CJK")
base_math = float(np.median([v for pc in ("LATIN_UPPER_DIGIT", "LATIN_GREEK_LOWER", "MATH_OPERATOR") if (v := median_for("NODE_FORMULA", pc)) is not None]))
role_specs = [
    ("EDGE_LABEL", "CJK", base_cjk, 0.95, 1.10, "ordinary edge annotation vs CJK node-text BASE"),
    ("ANNOTATION", "CJK", base_cjk, 0.95, 1.10, "ratio heading ordinary annotation vs CJK node-text BASE"),
]
for role, pc, basev, lo, hi, reason in role_specs:
    val = median_for(role, pc)
    ratio = None if val is None or basev is None else val / basev
    role_rows.append({"role": role, "peer_class": pc, "role_median_h_px": val, "base_role": "NODE_TEXT", "base_median_h_px": basev, "ratio": ratio, "allowed_min": lo, "allowed_max": hi, "machine_role_pass": ratio is not None and lo <= ratio <= hi, "reason": reason})
formula_vals = [r["median_h_px"] for r in element_medians if r["role"] == "FORMULA_BLOCK" and r["peer_class"] in {"LATIN_UPPER_DIGIT", "LATIN_GREEK_LOWER", "MATH_OPERATOR"}]
formula_med = None if not formula_vals else float(np.median(formula_vals))
formula_ratio = None if formula_med is None else formula_med / base_math
role_rows.append({"role": "FORMULA_BLOCK", "peer_class": "MATH_COMPARABLE", "role_median_h_px": formula_med, "base_role": "NODE_FORMULA", "base_median_h_px": base_math, "ratio": formula_ratio, "allowed_min": 1.00, "allowed_max": 1.18, "machine_role_pass": formula_ratio is not None and 1.00 <= formula_ratio <= 1.18, "reason": "11.2pt formula block vs 9.6pt ordinary node formula BASE"})


# Complete object pair ledger and cards.
object_ids = sorted(object_masks)
if len(object_ids) != 32:
    raise RuntimeError(f"Expected 32 objects, found {len(object_ids)}")
pair_total_expected = len(object_ids) * (len(object_ids) - 1) // 2

coords = {oid: np.argwhere(object_masks[oid]) for oid in object_ids}
trees = {oid: cKDTree(coords[oid]) if len(coords[oid]) else None for oid in object_ids}
text_ids = set(TEXT_OBJECTS)
border_ids = {"O-G01", "O-G02", "O-G03", "O-G05", "O-G06", "O-G07"}
edge_ids = {"O-G08", "O-G09", "O-G10", "O-G11", "O-G12", "O-G13"}
design_pairs = {
    frozenset(("O-T08", "O-G04")): "same-parent fraction rule",
    frozenset(("O-G08", "O-G01")): "proposal arrow starts at current-state border",
    frozenset(("O-G08", "O-G02")): "proposal arrow terminates at proposal border",
    frozenset(("O-G09", "O-G02")): "calculate arrow starts at proposal border",
    frozenset(("O-G09", "O-G03")): "calculate arrow terminates at ratio border",
    frozenset(("O-G10", "O-G03")): "decision arrow starts at ratio border",
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
        ds, inds = trees[bid].query(ca, k=1)
        k = int(np.argmin(ds))
        return float(ds[k]), tuple(int(v) for v in ca[k]), tuple(int(v) for v in cb[int(inds[k])])
    ds, inds = trees[aid].query(cb, k=1)
    k = int(np.argmin(ds))
    return float(ds[k]), tuple(int(v) for v in ca[int(inds[k])]), tuple(int(v) for v in cb[k])


def relation_rule(aid, bid):
    pair = frozenset((aid, bid))
    if pair in design_pairs:
        return "DESIGN_WHITELIST", 0, design_pairs[pair]
    a_text, b_text = aid in text_ids, bid in text_ids
    if a_text and b_text:
        return "TEXT_TEXT_BBOX", 4, "independent text/formula semantic parents"
    other = bid if a_text else aid if b_text else None
    if other in border_ids:
        return "TEXT_FORMULA_NODE_BORDER", 5, "text/formula raw ink to final-visible node border"
    if other in edge_ids or other == "O-G04":
        return "TEXT_FORMULA_LINE_ARROW_RULE", 3, "text/formula raw ink to line/arrow/math-rule"
    return "INDEPENDENT_FOREGROUND", 0, "independent non-text foregrounds require zero illegal intersection"


def pair_card(pair_id, aid, bid, ma, mb, pta, ptb, meta):
    bba = tight_bbox(ma) or (0, 0, 1, 1)
    bbb = tight_bbox(mb) or (0, 0, 1, 1)
    ub = bbox_union((bba, bbb))
    ub = clip_box((ub[0] - 8, ub[1] - 8, ub[2] + 8, ub[3] + 8), W, H)
    ori = base.crop(ub)
    la = ma[ub[1]:ub[3], ub[0]:ub[2]]
    lb = mb[ub[1]:ub[3], ub[0]:ub[2]]
    arr = np.asarray(ori.convert("RGB"), dtype=np.float32).copy()
    arr[la] = arr[la] * 0.35 + np.array([255, 30, 30]) * 0.65
    arr[lb] = arr[lb] * 0.35 + np.array([20, 210, 255]) * 0.65
    arr[la & lb] = np.array([255, 220, 0])
    over = Image.fromarray(np.uint8(np.clip(arr, 0, 255)), mode="RGB")
    centres = [pta, ptb]
    patches = []
    for cy, cx in centres:
        pb = clip_box((cx - 14, cy - 14, cx + 15, cy + 15), W, H)
        po = base.crop(pb)
        pa = ma[pb[1]:pb[3], pb[0]:pb[2]]
        pbb = mb[pb[1]:pb[3], pb[0]:pb[2]]
        parr = np.asarray(po.convert("RGB"), dtype=np.float32).copy()
        parr[pa] = parr[pa] * 0.25 + np.array([255, 20, 20]) * 0.75
        parr[pbb] = parr[pbb] * 0.25 + np.array([20, 210, 255]) * 0.75
        parr[pa & pbb] = np.array([255, 220, 0])
        patches.append(Image.fromarray(np.uint8(np.clip(parr, 0, 255)), mode="RGB").resize((po.width * 8, po.height * 8), Image.Resampling.NEAREST))
    width = max(over.width, sum(p.width for p in patches))
    height = 38 + over.height + max(p.height for p in patches)
    card = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(card)
    d.text((2, 2), f"{pair_id} {aid} vs {bid} {meta}", fill="black")
    paste_with_label(card, over, (0, 38), "1x native pair overlay: A red, B cyan, intersection yellow")
    x = 0
    for k, p in enumerate(patches):
        paste_with_label(card, p, (x, 38 + over.height), f"closest endpoint {k+1}, 8x nearest")
        x += p.width
    return card


pair_rows = []
critical_rows = []
pair_card_paths = []
for pair_index, (aid, bid) in enumerate(itertools.combinations(object_ids, 2), start=1):
    pair_id = f"P{pair_index:04d}"
    ma, mb = object_masks[aid], object_masks[bid]
    overlap = int(np.count_nonzero(ma & mb))
    dist, pta, ptb = closest_points(aid, bid)
    raw_clear = float("inf") if not math.isfinite(dist) else max(0.0, dist - 1.0)
    rule, threshold, rule_note = relation_rule(aid, bid)
    arow = next(r for r in object_rows if r["object_id"] == aid)
    brow = next(r for r in object_rows if r["object_id"] == bid)
    if rule == "TEXT_TEXT_BBOX":
        av = px_box(object_pdf_boxes[aid], sx, sy, pad=0)
        bv = px_box(object_pdf_boxes[bid], sx, sy, pad=0)
        metric_clear = bbox_clearance(av, bv)
        metric = "vector_bbox_clearance_px"
    else:
        metric_clear = raw_clear
        metric = "raw_mask_pixel_square_clearance_px"
    design = rule == "DESIGN_WHITELIST"
    illegal_overlap = overlap if not design else 0
    machine_pass = bool(arow["mask_pixel_count"] > 0 and brow["mask_pixel_count"] > 0 and illegal_overlap == 0 and (design or metric_clear >= threshold))
    critical = bool(not machine_pass or design or (threshold > 0 and metric_clear < threshold + 3.0))
    meta = f"rule={rule} overlap={overlap} illegal={illegal_overlap} clearance={metric_clear:.3f} threshold={threshold} machine={'PASS' if machine_pass else 'FAIL'}"
    card = pair_card(pair_id, aid, bid, ma, mb, pta, ptb, meta)
    cpath = ROOT / "pairs" / "cards" / f"{pair_id}.png"
    card.save(cpath, optimize=True)
    pair_card_paths.append(cpath)
    if critical:
        crit_path = ROOT / "pairs" / "critical" / f"{pair_id}_critical.png"
        card.save(crit_path, optimize=True)
        critical_rows.append({"pair_id": pair_id, "object_a": aid, "object_b": bid, "reason_for_critical": meta, "card_path": f"pairs/critical/{pair_id}_critical.png"})
    pair_rows.append(
        {
            "pair_id": pair_id,
            "object_a": aid,
            "object_b": bid,
            "type_a": arow["object_type"],
            "type_b": brow["object_type"],
            "relation_rule": rule,
            "rule_note": rule_note,
            "design_whitelist": design,
            "raw_overlap_pixel_count": overlap,
            "illegal_overlap_pixel_count": illegal_overlap,
            "raw_mask_clearance_px": raw_clear,
            "metric": metric,
            "metric_clearance_px": metric_clear,
            "required_clearance_px": threshold,
            "closest_a_yx": json.dumps(pta),
            "closest_b_yx": json.dumps(ptb),
            "machine_decision": "PASS" if machine_pass else "FAIL",
            "critical": critical,
            "mask_a_path": f"objects/masks_1x/{arow['safe_filename']}.png",
            "mask_b_path": f"objects/masks_1x/{brow['safe_filename']}.png",
            "pair_card_path": f"pairs/cards/{pair_id}.png",
            "critical_card_path": f"pairs/critical/{pair_id}_critical.png" if critical else "N/A",
        }
    )
    if pair_index % 50 == 0:
        print(f"pair cards {pair_index}/{pair_total_expected}", flush=True)

if len(pair_rows) != pair_total_expected or len({r["pair_id"] for r in pair_rows}) != pair_total_expected:
    raise RuntimeError("Pair denominator or unique ID closure failed")

for sheet_no, start in enumerate(range(0, len(pair_card_paths), 25), start=1):
    paths = pair_card_paths[start:start + 25]
    sheet = Image.new("RGB", (2500, 2500), "white")
    for k, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        im.thumbnail((490, 490), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (500, 500), "white")
        cell.paste(im, ((500 - im.width) // 2, (500 - im.height) // 2))
        ImageDraw.Draw(cell).text((4, 4), p.stem, fill="black")
        sheet.paste(cell, ((k % 5) * 500, (k // 5) * 500))
    sheet.save(ROOT / "pairs" / "contact_sheets" / f"pair_contact_sheet_{sheet_no:02d}.png", optimize=True)


# Clip ledger per object, plus cross-platform safe filename map.
clip_rows = []
safe_rows = []
for r in object_rows:
    clip_rows.append({"object_id": r["object_id"], "mask_pixel_count": r["mask_pixel_count"], "clip_edge_distance_px": r["clip_edge_distance_px"], "clip_pixel_count": r["clip_pixel_count"], "machine_clip_pass": r["mask_pixel_count"] > 0 and r["clip_pixel_count"] == 0, "mask_path": f"objects/masks_1x/{r['safe_filename']}.png"})
    safe_rows.append({"id": r["object_id"], "safe_filename": r["safe_filename"], "kind": "OBJECT", "ordinary_file": f"objects/masks_1x/{r['safe_filename']}.png"})
for g in glyphs:
    safe_rows.append({"id": g["glyph_id"], "safe_filename": g["safe_filename"], "kind": "GLYPH", "ordinary_file": f"glyphs/masks_1x/{g['glyph_id']}.png"})
for r in pair_rows:
    safe_rows.append({"id": r["pair_id"], "safe_filename": r["pair_id"], "kind": "PAIR", "ordinary_file": r["pair_card_path"]})


write_csv(ROOT / "objects" / "object_manifest.csv", object_rows)
write_csv(ROOT / "objects" / "source_font_audit.csv", font_rows)
write_csv(ROOT / "glyphs" / "glyph_machine_measurements.csv", glyph_rows)
write_csv(ROOT / "glyphs" / "calibration_manifest.csv", calibration_rows)
write_csv(ROOT / "pairs" / "all_pairs_machine.csv", pair_rows)
write_csv(ROOT / "pairs" / "critical_machine_index.csv", critical_rows)
write_csv(ROOT / "ledgers" / "peer_machine.csv", peer_rows)
write_csv(ROOT / "ledgers" / "role_machine.csv", role_rows)
write_csv(ROOT / "ledgers" / "clip_machine.csv", clip_rows)
write_csv(ROOT / "identity" / "id_safe_filename_map.csv", safe_rows)

summary = {
    "uid": "FIG-P602-01",
    "objects": len(object_rows),
    "text_formula_objects": len(TEXT_OBJECTS),
    "graphic_math_rule_objects": len(GRAPHIC_OBJECTS),
    "glyphs": len(glyph_rows),
    "pairs_expected_c_n_2": pair_total_expected,
    "pairs_actual": len(pair_rows),
    "critical_pairs": len(critical_rows),
    "glyph_machine_failures": sum(not r["machine_threshold_pass"] for r in glyph_rows),
    "empty_glyph_masks": sum(r["empty_mask"] for r in glyph_rows),
    "empty_object_masks": sum(r["empty_mask"] for r in object_rows),
    "pair_machine_failures": sum(r["machine_decision"] == "FAIL" for r in pair_rows),
    "pair_illegal_overlap_pixels_sum": sum(r["illegal_overlap_pixel_count"] for r in pair_rows),
    "object_clip_pixels_sum": sum(max(0, int(r["clip_pixel_count"])) for r in object_rows),
    "source_font_failures": sum(not r["source_font_pass"] for r in font_rows),
    "peer_machine_failures": sum(not r["machine_peer_pass"] for r in peer_rows),
    "role_machine_failures": sum(not r["machine_role_pass"] for r in role_rows),
    "glyph_contact_sheets": math.ceil(len(glyph_rows) / 12),
    "object_contact_sheets": math.ceil(len(object_rows) / 8),
    "pair_contact_sheets": math.ceil(len(pair_rows) / 25),
}
write_json(ROOT / "qa" / "machine_summary.json", summary)

# Coverage and ordinary-file openability check before manual ledgers.
expected_pngs = []
expected_pngs += [ROOT / r["mask_path"] for r in glyph_rows]
expected_pngs += [ROOT / "glyphs" / "cards" / f"{r['glyph_id']}.png" for r in glyph_rows]
expected_pngs += [ROOT / "objects" / "masks_1x" / f"{r['safe_filename']}.png" for r in object_rows]
expected_pngs += [ROOT / "objects" / "cards" / f"{r['safe_filename']}.png" for r in object_rows]
expected_pngs += [ROOT / r["pair_card_path"] for r in pair_rows]
open_failures = []
for p in expected_pngs:
    try:
        with Image.open(p) as im:
            im.verify()
    except Exception as exc:
        open_failures.append({"path": str(p), "error": repr(exc)})
coverage = {
    "expected_png_count_checked": len(expected_pngs),
    "ordinary_png_open_failures": open_failures,
    "object_ids_unique": len({r["object_id"] for r in object_rows}) == len(object_rows),
    "glyph_ids_unique": len({r["glyph_id"] for r in glyph_rows}) == len(glyph_rows),
    "pair_ids_unique": len({r["pair_id"] for r in pair_rows}) == len(pair_rows),
    "glyph_parent_ids_all_exist": all(r["parent_object_id"] in TEXT_OBJECTS for r in glyph_rows),
    "pair_denominator_formula": f"C({len(object_rows)},2)={pair_total_expected}",
    "pair_denominator_closed": len(pair_rows) == pair_total_expected,
    "foreground_drawing_indices_accounted": sorted(i for v in GRAPHIC_OBJECTS.values() for i in v[2]),
    "background_fill_drawing_indices_excluded_with_reason": {"12": "proposal label white background", "15": "calculate label white background", "18": "decision label white background", "21": "accept label white background", "24": "reject label white background", "27": "self-loop label white background"},
}
write_json(ROOT / "qa" / "machine_coverage_check.json", coverage)

print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
