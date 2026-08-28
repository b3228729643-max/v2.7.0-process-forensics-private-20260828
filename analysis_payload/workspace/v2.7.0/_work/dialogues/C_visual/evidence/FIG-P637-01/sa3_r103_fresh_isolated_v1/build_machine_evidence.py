from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


HANDOFF_ID = "C-FIG-P637-01-R103-SA3-FRESH-ISOLATED-V1"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_gibbs_axis_path.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa3_r103_fresh_isolated_v1")
RENDERS = ROOT / "renders"
MACHINE = ROOT / "machine"
MASKS = ROOT / "masks"
CARDS = ROOT / "cards"
PAIRS = ROOT / "pairs"

EXPECTED_SHA256 = "9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23"
EXPECTED_BYTES = 4_967_184
EXPECTED_PAGES = 817
TARGET_PHYSICAL_PAGE = 687
PRINTED_PAGE = 674
FIGURE_NUMBER = "33.4"
UID = "FIG-P637-01"
DPI300 = 300
DPI200 = 200
SCALE300 = DPI300 / 72.0

# These integer crop rectangles are derived from the vector/text extents on the
# independently located official PDF page. They are intentionally padded and
# are not copied from any prior evidence.
BODY_RECT_PT = fitz.Rect(153.0, 61.0, 430.0, 314.0)
FIGURE_RECT_PT = fitz.Rect(56.0, 61.0, 528.0, 349.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pt_rect_to_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE300),
        math.floor(rect.y0 * SCALE300),
        math.ceil(rect.x1 * SCALE300),
        math.ceil(rect.y1 * SCALE300),
    )


def bbox_union(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def rgb_from_pdf_color(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def mask_intersection(a: dict, b: dict) -> int:
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["mask_array"][y0 - ay0 : y1 - ay0, x0 - ax0 : x1 - ax0]
    bm = b["mask_array"][y0 - by0 : y1 - by0, x0 - bx0 : x1 - bx0]
    return int(np.count_nonzero(am & bm))


def exact_mask_distance(a: dict, b: dict) -> float:
    abox = a["mask_bbox_px"]
    bbox = b["mask_bbox_px"]
    rough = rect_distance(abox, bbox)
    if rough > 80:
        return rough
    ay, ax = np.nonzero(a["mask_array"])
    by, bx = np.nonzero(b["mask_array"])
    if len(ax) == 0 or len(bx) == 0:
        return float("nan")
    ax = ax + abox[0]
    ay = ay + abox[1]
    bx = bx + bbox[0]
    by = by + bbox[1]
    # Bounding boxes and native masks are small in all near-pair cases here.
    # Chunk the exact Euclidean computation to keep memory bounded.
    best2 = float("inf")
    bxy = np.column_stack([bx, by]).astype(np.int32)
    axy = np.column_stack([ax, ay]).astype(np.int32)
    for start in range(0, len(axy), 256):
        q = axy[start : start + 256]
        d2 = ((q[:, None, :] - bxy[None, :, :]) ** 2).sum(axis=2)
        best2 = min(best2, float(d2.min()))
        if best2 == 0:
            break
    return math.sqrt(best2)


def local_background(arr: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    pad = 3
    xx0, yy0 = max(0, x0 - pad), max(0, y0 - pad)
    xx1, yy1 = min(arr.shape[1], x1 + pad), min(arr.shape[0], y1 + pad)
    patch = arr[yy0:yy1, xx0:xx1]
    edge = np.concatenate([patch[0], patch[-1], patch[:, 0], patch[:, -1]], axis=0)
    counts = Counter(map(tuple, edge.tolist()))
    return np.array(counts.most_common(1)[0][0], dtype=np.float32)


def quad_inside_mask(box: tuple[int, int, int, int], quad_pt: list[list[float]]) -> np.ndarray:
    x0, y0, x1, y1 = box
    # recover_char_quad returns ul, ur, ll, lr. Reorder to a perimeter polygon.
    q = np.array([quad_pt[0], quad_pt[1], quad_pt[3], quad_pt[2]], dtype=np.float64) * SCALE300
    xs = np.arange(x0, x1, dtype=np.float64) + 0.5
    ys = np.arange(y0, y1, dtype=np.float64) + 0.5
    gx, gy = np.meshgrid(xs, ys)
    inside_pos = np.ones(gx.shape, dtype=bool)
    inside_neg = np.ones(gx.shape, dtype=bool)
    for i in range(4):
        p1, p2 = q[i], q[(i + 1) % 4]
        cross = (p2[0] - p1[0]) * (gy - p1[1]) - (p2[1] - p1[1]) * (gx - p1[0])
        inside_pos &= cross >= 1e-7
        inside_neg &= cross <= -1e-7
    return inside_pos | inside_neg


def char_mask(full_arr: np.ndarray, box: tuple[int, int, int, int], target_rgb: tuple[int, int, int], quad_pt: list[list[float]]) -> tuple[np.ndarray, tuple[int, int, int]]:
    x0, y0, x1, y1 = box
    patch = full_arr[y0:y1, x0:x1].astype(np.float32)
    bg = local_background(full_arr, box)
    target = np.array(target_rgb, dtype=np.float32)
    direction = bg - target
    denom = float(np.dot(direction, direction))
    if denom < 1:
        delta = np.max(np.abs(patch - bg), axis=2)
        return delta >= 20, tuple(map(int, bg))
    alpha = np.tensordot(bg - patch, direction, axes=([2], [0])) / denom
    alpha_clamped = np.clip(alpha, 0.0, 1.25)
    recon = bg[None, None, :] - alpha_clamped[:, :, None] * direction[None, None, :]
    residual = np.max(np.abs(patch - recon), axis=2)
    contrast = np.max(np.abs(patch - bg), axis=2)
    mask = (alpha > 0.0) & (alpha < 1.35) & (contrast >= 20.0) & (residual <= 18.0)
    # The recovered character quad closes rotated-glyph and adjacent-glyph
    # ownership. Pixel centres on shared quad edges are excluded from both sides
    # instead of being duplicated into two glyph masks.
    mask &= quad_inside_mask(box, quad_pt)
    return mask, tuple(map(int, bg))


def ink_stats(mask: np.ndarray) -> tuple[int, int, int, int]:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return 0, 0, 0, 0
    return int(yy.max() - yy.min() + 1), int(xx.max() - xx.min() + 1), int(len(xx)), int(len(np.unique(np.column_stack([xx, yy]), axis=0)))


def save_small_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def build_triptych_card(
    full_img: Image.Image,
    mask: np.ndarray,
    mask_bbox: tuple[int, int, int, int],
    label: str,
    out: Path,
    pad: int = 4,
) -> None:
    x0, y0, x1, y1 = mask_bbox
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(full_img.width, x1 + pad), min(full_img.height, y1 + pad)
    original = full_img.crop((cx0, cy0, cx1, cy1)).convert("RGB")
    placed = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
    placed[y0 - cy0 : y1 - cy0, x0 - cx0 : x1 - cx0] = mask
    overlay = np.array(original).copy()
    overlay[placed] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(overlay, 255)
    mask_only[placed] = np.array([0, 0, 0], dtype=np.uint8)
    panels = [original, Image.fromarray(overlay), Image.fromarray(mask_only)]
    enlarged = [p.resize((p.width * 8, p.height * 8), Image.Resampling.NEAREST) for p in panels]
    title_h = 30
    gap = 12
    width = sum(p.width for p in enlarged) + gap * 2
    height = title_h + max(p.height for p in enlarged) + 24
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((4, 4), f"{label} | native bbox={mask_bbox} | 8x nearest: ORIGINAL / TARGET OVERLAY / MASK ONLY", fill="black")
    x = 0
    for idx, p in enumerate(enlarged):
        canvas.paste(p, (x, title_h))
        draw.text((x + 2, height - 18), ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"][idx], fill="black")
        x += p.width + gap
    canvas.save(out)


def parent_for_char(rect: fitz.Rect) -> tuple[str, str]:
    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
    parents = [
        ("T_AXIS_X", "AXIS_TITLE", fitz.Rect(405, 168, 431, 192)),
        ("T_AXIS_Y", "AXIS_TITLE", fitz.Rect(268, 60, 294, 82)),
        ("T_UPDATE_X1", "ANNOTATION", fitz.Rect(174, 251, 220, 273)),
        ("T_UPDATE_X2", "ANNOTATION", fitz.Rect(228, 251, 270, 274)),
        ("T_STATE_0", "STATE_LABEL", fitz.Rect(170, 230, 187, 250)),
        ("T_STATE_1", "STATE_LABEL", fitz.Rect(248, 209, 264, 228)),
        ("T_STATE_2", "STATE_LABEL", fitz.Rect(228, 185, 244, 204)),
        ("T_STATE_3", "STATE_LABEL", fitz.Rect(314, 202, 330, 222)),
        ("T_STATE_4", "STATE_LABEL", fitz.Rect(317, 155, 333, 175)),
        ("T_STATE_5", "STATE_LABEL", fitz.Rect(345, 147, 361, 166)),
        ("T_STATE_6", "STATE_LABEL", fitz.Rect(330, 120, 346, 140)),
        ("T_LONG_AXIS", "ANNOTATION", fitz.Rect(213, 136, 246, 168)),
        ("T_SHORT_AXIS", "ANNOTATION", fitz.Rect(316, 224, 347, 244)),
        ("T_NOTE", "NOTE", fitz.Rect(202, 282, 362, 313)),
        ("T_CAPTION_LABEL", "CAPTION_LABEL", fitz.Rect(55, 312, 98, 345)),
        ("T_CAPTION", "CAPTION", fitz.Rect(98, 312, 529, 345)),
    ]
    for pid, role, area in parents:
        if area.contains(fitz.Point(cx, cy)):
            return pid, role
    raise ValueError(f"Visible character outside declared figure parents: {rect}")


def script_class(ch: str, parent_id: str, size: float, font: str) -> str:
    cp = ord(ch)
    if ch in "，。、；：,.·":
        return "LOW_PROFILE_PUNCTUATION"
    if 0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F:
        return "CJK_OR_FULLWIDTH"
    if ch.isdigit():
        if parent_id in {"T_AXIS_X", "T_AXIS_Y", "T_UPDATE_X1", "T_UPDATE_X2"} or (parent_id == "T_CAPTION" and size < 9.5):
            return "NATURAL_SCRIPT"
        return "LATIN_UPPER_OR_DIGIT"
    if "Math" in font:
        if size < 8.5:
            return "NATURAL_SCRIPT"
        return "BASE_MATH"
    if ch.isupper():
        return "LATIN_UPPER_OR_DIGIT"
    if ch.islower():
        return "LATIN_OR_GREEK_LOWER"
    return "BASE_MATH"


def source_line_map() -> dict[str, int]:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    needles = {
        "style_9_2": "slfig-FIG-P637-01/.style={font=\\fontsize{9.2pt}",
        "every_node_9_2": "every node/.style={font=\\fontsize{9.2pt}",
        "axis_x": "node[right=3pt] {$x_1$}",
        "axis_y": "node[above=3pt] {$x_2$}",
        "update_x1": "{更新$x_1$}",
        "update_x2": "{更新$x_2$}",
        "state_font_8_8": "font=\\fontsize{8.8pt}",
        "long_axis": "{长轴}",
        "short_axis": "{短轴}",
        "note": "{固定教学示意：",
        "caption": "\\caption{二维Gibbs轨迹",
    }
    out = {}
    for key, needle in needles.items():
        hits = [i + 1 for i, line in enumerate(lines) if needle in line]
        if len(hits) != 1:
            raise ValueError((key, needle, hits))
        out[key] = hits[0]
    return out


def source_info(parent_id: str, pdf_size: float, lines: dict[str, int]) -> tuple[str, int, float, float, float, str]:
    if parent_id.startswith("T_STATE_"):
        return str(SOURCE), lines["state_font_8_8"], 8.8, 1.0, 8.8, "explicit local fontsize"
    if parent_id == "T_CAPTION" or parent_id == "T_CAPTION_LABEL":
        return str(SOURCE), lines["caption"], round(pdf_size, 2), 1.0, round(pdf_size, 2), "caption font resolved from official PDF span"
    key_map = {
        "T_AXIS_X": "axis_x",
        "T_AXIS_Y": "axis_y",
        "T_UPDATE_X1": "update_x1",
        "T_UPDATE_X2": "update_x2",
        "T_LONG_AXIS": "long_axis",
        "T_SHORT_AXIS": "short_axis",
        "T_NOTE": "note",
    }
    return str(SOURCE), lines[key_map[parent_id]], 9.2, 1.0, 9.2, "figure/every-node fontsize"


def draw_paths_to_mask(page_rect: fitz.Rect, drawings: list[dict], components: list[tuple[int, bool, bool]]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    tmp = fitz.open()
    pg = tmp.new_page(width=page_rect.width, height=page_rect.height)
    shape = pg.new_shape()
    for index, do_stroke, do_fill in components:
        d = drawings[index]
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
                raise ValueError(f"Unhandled drawing item {op}")
        shape.finish(
            color=(0, 0, 0) if do_stroke else None,
            fill=(0, 0, 0) if do_fill else None,
            width=float(d.get("width") or 0.0),
            closePath=bool(d.get("closePath")),
            lineCap=int(max(d.get("lineCap") or (0,))),
            lineJoin=int(d.get("lineJoin") or 0),
        )
    shape.commit()
    pix = pg.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), alpha=False, colorspace=fitz.csGRAY)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    mask_full = arr < 235
    yy, xx = np.nonzero(mask_full)
    if len(xx) == 0:
        raise ValueError("Empty reconstructed graphic mask")
    box = (int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1))
    return mask_full[box[1] : box[3], box[0] : box[2]], box


def graphic_definitions() -> list[dict]:
    return [
        {"id": "D_AXIS_X", "kind": "LINE_ARROW", "role": "AXIS", "indices": [(1, True, False), (2, True, True)]},
        {"id": "D_AXIS_Y", "kind": "LINE_ARROW", "role": "AXIS", "indices": [(3, True, False), (4, True, True)]},
        {"id": "D_ELLIPSE_OUTER", "kind": "DATA_CURVE", "role": "DENSITY_CONTOUR", "indices": [(5, True, False)]},
        {"id": "D_ELLIPSE_MIDDLE", "kind": "DATA_CURVE", "role": "DENSITY_CONTOUR", "indices": [(6, True, False)]},
        {"id": "D_ELLIPSE_INNER", "kind": "DATA_CURVE", "role": "DENSITY_CONTOUR", "indices": [(7, True, False)]},
        {"id": "D_STEP_01", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X1", "indices": [(8, True, False), (9, True, True)]},
        {"id": "D_STEP_12", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X2", "indices": [(10, True, False), (11, True, True)]},
        {"id": "D_STEP_23", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X1", "indices": [(12, True, False), (13, True, True)]},
        {"id": "D_STEP_34", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X2", "indices": [(14, True, False), (15, True, True)]},
        {"id": "D_STEP_45", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X1", "indices": [(16, True, False), (17, True, True)]},
        {"id": "D_STEP_56", "kind": "LINE_ARROW", "role": "GIBBS_MOVE_X2", "indices": [(18, True, False), (19, True, True)]},
        *[
            {"id": f"D_MARKER_{i}", "kind": "MARKER", "role": "STATE_MARKER", "indices": [(20 + i, False, True)]}
            for i in range(7)
        ],
        {"id": "D_LONG_AXIS", "kind": "LINE_ARROW", "role": "GEOMETRIC_ANNOTATION", "indices": [(27, True, False), (28, True, True)]},
        {"id": "D_SHORT_AXIS", "kind": "LINE_ARROW", "role": "GEOMETRIC_ANNOTATION", "indices": [(29, True, False), (30, True, True)]},
        {"id": "D_NOTE_BORDER", "kind": "NODE_BORDER", "role": "NOTE_BORDER", "indices": [(31, True, False)]},
        {"id": "X_BG_ELLIPSE_FILL", "kind": "BACKGROUND_FILL", "role": "BACKGROUND", "indices": [(5, False, True)], "excluded": True, "exclude_reason": "non-semantic translucent background fill"},
        {"id": "X_BG_NOTE_FILL", "kind": "BACKGROUND_FILL", "role": "BACKGROUND", "indices": [(31, False, True)], "excluded": True, "exclude_reason": "opaque note-card background; not a foreground collision object"},
    ]


def relation_class(a: dict, b: dict) -> tuple[str, float | None]:
    ak, bk = a["kind"], b["kind"]
    if ak == "GLYPH" and bk == "GLYPH":
        if a["parent_id"] == b["parent_id"]:
            return "SAME_TEXT_PARENT", None
        return "TEXT_TEXT", 4.0
    glyph, other = (a, b) if ak == "GLYPH" else ((b, a) if bk == "GLYPH" else (None, None))
    if glyph is not None:
        if other["kind"] == "NODE_BORDER":
            return "TEXT_NODE_BORDER", 5.0
        if other["kind"] in {"LINE_ARROW", "MARKER", "DATA_CURVE"}:
            return "TEXT_GRAPHIC", 3.0
        return "TEXT_OTHER", 3.0
    return "GRAPHIC_GRAPHIC", None


def pair_evidence(full_img: Image.Image, a: dict, b: dict, pair_id: str, out_dir: Path) -> None:
    boxes = [a["mask_bbox_px"], b["mask_bbox_px"]]
    x0, y0, x1, y1 = bbox_union(boxes)
    pad = 8
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(full_img.width, x1 + pad), min(full_img.height, y1 + pad)
    # For long crossing curves, a tight union can be huge. Use the intersection
    # neighborhood if masks actually overlap.
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if ix0 < ix1 and iy0 < iy1:
        am = a["mask_array"][iy0 - ay0 : iy1 - ay0, ix0 - ax0 : ix1 - ax0]
        bm = b["mask_array"][iy0 - by0 : iy1 - by0, ix0 - bx0 : ix1 - bx0]
        iy, ix = np.nonzero(am & bm)
        if len(ix):
            cx0, cy0, cx1, cy1 = int(ix.min() + ix0), int(iy.min() + iy0), int(ix.max() + ix0 + 1), int(iy.max() + iy0 + 1)
            x0, y0, x1, y1 = max(0, cx0 - 18), max(0, cy0 - 18), min(full_img.width, cx1 + 18), min(full_img.height, cy1 + 18)
    # If there is no intersection and the union is huge, retain a bounded region
    # around the nearest bbox edges; all coordinates remain native page pixels.
    if x1 - x0 > 320 or y1 - y0 > 320:
        acx, acy = (max(ax0, min((bx0 + bx1) // 2, ax1 - 1)), max(ay0, min((by0 + by1) // 2, ay1 - 1)))
        bcx, bcy = (max(bx0, min((ax0 + ax1) // 2, bx1 - 1)), max(by0, min((ay0 + ay1) // 2, by1 - 1)))
        mx, my = (acx + bcx) // 2, (acy + bcy) // 2
        x0, y0, x1, y1 = max(0, mx - 80), max(0, my - 80), min(full_img.width, mx + 80), min(full_img.height, my + 80)
    h, w = y1 - y0, x1 - x0
    ma = np.zeros((h, w), dtype=bool)
    mb = np.zeros((h, w), dtype=bool)
    for target, obj in ((ma, a), (mb, b)):
        ox0, oy0, ox1, oy1 = obj["mask_bbox_px"]
        xx0, yy0, xx1, yy1 = max(x0, ox0), max(y0, oy0), min(x1, ox1), min(y1, oy1)
        if xx0 < xx1 and yy0 < yy1:
            target[yy0 - y0 : yy1 - y0, xx0 - x0 : xx1 - x0] = obj["mask_array"][yy0 - oy0 : yy1 - oy0, xx0 - ox0 : xx1 - ox0]
    raw = full_img.crop((x0, y0, x1, y1)).convert("RGB")
    raw_arr = np.array(raw)
    over = raw_arr.copy()
    over[ma] = [255, 0, 0]
    over[mb] = [0, 180, 255]
    over[ma & mb] = [255, 255, 0]
    only_a = np.where(ma[:, :, None], 0, 255).astype(np.uint8)
    only_a = np.repeat(only_a, 3, axis=2) if only_a.shape[2] == 1 else only_a
    only_b = np.where(mb[:, :, None], 0, 255).astype(np.uint8)
    only_b = np.repeat(only_b, 3, axis=2) if only_b.shape[2] == 1 else only_b
    inter = np.where((ma & mb)[:, :, None], 0, 255).astype(np.uint8)
    inter = np.repeat(inter, 3, axis=2) if inter.shape[2] == 1 else inter
    out_dir.mkdir(parents=True, exist_ok=True)
    raw.save(out_dir / "raw_1x.png")
    Image.fromarray(only_a).save(out_dir / "mask_a_1x.png")
    Image.fromarray(only_b).save(out_dir / "mask_b_1x.png")
    Image.fromarray(inter).save(out_dir / "intersection_1x.png")
    Image.fromarray(over).save(out_dir / "overlay_1x.png")
    panels = [raw_arr, only_a, only_b, inter, over]
    labels = ["RAW", "MASK A", "MASK B", "INTERSECTION", "OVERLAY"]
    scale = 8
    gap, title_h, footer_h = 8, 34, 20
    imgs = [Image.fromarray(p).resize((w * scale, h * scale), Image.Resampling.NEAREST) for p in panels]
    canvas = Image.new("RGB", (sum(i.width for i in imgs) + gap * 4, title_h + h * scale + footer_h), "white")
    d = ImageDraw.Draw(canvas)
    d.text((4, 4), f"{pair_id} | page ROI=({x0},{y0},{x1},{y1}) | 8x nearest", fill="black")
    xpos = 0
    for lab, im in zip(labels, imgs):
        canvas.paste(im, (xpos, title_h))
        d.text((xpos + 2, title_h + h * scale + 2), lab, fill="black")
        xpos += im.width + gap
    canvas.save(out_dir / "card_8x_nearest.png")


def main() -> None:
    # Rebuild only machine-owned directories. The manual/ and seal/ trees are
    # deliberately never created, filled, or overwritten by this script.
    for owned in (RENDERS, MACHINE, MASKS, CARDS, PAIRS):
        resolved = owned.resolve()
        if ROOT.resolve() not in resolved.parents:
            raise RuntimeError(f"Refusing to clear path outside evidence root: {resolved}")
        if owned.exists():
            shutil.rmtree(owned)
    for p in (RENDERS, MACHINE, MASKS / "glyph", MASKS / "graphic", CARDS / "glyph", CARDS / "graphic", CARDS / "glyph_contact_sheets", PAIRS):
        p.mkdir(parents=True, exist_ok=True)

    identity = {
        "uid": UID,
        "handoff_id": HANDOFF_ID,
        "pdf_resolved_path": str(PDF.resolve()),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "expected_pdf_bytes": EXPECTED_BYTES,
        "expected_pdf_sha256": EXPECTED_SHA256,
        "source_resolved_path": str(SOURCE.resolve()),
        "tex_execution": "DISABLED",
        "source_writer": "NONE",
        "reviewer_role": "SA3 fresh isolated",
        "business_inputs": [str(PDF), str(SOURCE)],
    }
    if identity["pdf_bytes"] != EXPECTED_BYTES or identity["pdf_sha256"] != EXPECTED_SHA256:
        raise RuntimeError("Official PDF identity mismatch")

    doc = fitz.open(PDF)
    if doc.page_count != EXPECTED_PAGES:
        raise RuntimeError("Unexpected page count")
    query = "二维Gibbs 轨迹"
    hits = []
    for i in range(doc.page_count):
        text = doc[i].get_text()
        normalized = "".join(text.split())
        if "二维Gibbs轨迹" in normalized and "轴向短步" in normalized:
            hits.append(i + 1)
    if hits != [TARGET_PHYSICAL_PAGE]:
        raise RuntimeError(f"Independent PDF location is not unique: {hits}")
    page = doc[TARGET_PHYSICAL_PAGE - 1]
    identity.update(
        {
            "pdf_pages": doc.page_count,
            "physical_page": TARGET_PHYSICAL_PAGE,
            "printed_page": PRINTED_PAGE,
            "figure_number": FIGURE_NUMBER,
            "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
            "page_rotation": page.rotation,
            "page_search_hits": hits,
            "page_search_query_normalized": "二维Gibbs轨迹 + 轴向短步",
            "figure_rect_pt": list(FIGURE_RECT_PT),
            "body_rect_pt": list(BODY_RECT_PT),
            "figure_rect_px_300dpi": list(pt_rect_to_px(FIGURE_RECT_PT)),
            "body_rect_px_300dpi": list(pt_rect_to_px(BODY_RECT_PT)),
        }
    )
    write_json(MACHINE / "candidate_identity.json", identity)

    # Use Poppler directly for the authoritative rendering path. Existing files
    # from an earlier invocation are overwritten only by this machine stage.
    subprocess.run(
        ["pdftoppm", "-f", str(TARGET_PHYSICAL_PAGE), "-l", str(TARGET_PHYSICAL_PAGE), "-r", "200", "-png", "-singlefile", str(PDF), str(RENDERS / "full_page_200dpi")],
        check=True,
    )
    subprocess.run(
        ["pdftoppm", "-f", str(TARGET_PHYSICAL_PAGE), "-l", str(TARGET_PHYSICAL_PAGE), "-r", "300", "-png", "-singlefile", str(PDF), str(RENDERS / "full_page_300dpi")],
        check=True,
    )
    full_img = Image.open(RENDERS / "full_page_300dpi.png").convert("RGB")
    if full_img.size != (2481, 3508):
        raise RuntimeError(f"Unexpected 300 dpi page grid: {full_img.size}")
    full_arr = np.array(full_img)
    fbox = pt_rect_to_px(FIGURE_RECT_PT)
    bbox = pt_rect_to_px(BODY_RECT_PT)
    figure_crop = full_img.crop(fbox)
    standalone = full_img.crop(bbox)
    figure_crop.save(RENDERS / "figure_crop_300dpi.png")
    standalone.save(RENDERS / "standalone_300dpi.png")
    figure_crop.convert("L").save(RENDERS / "grayscale_300dpi.png")

    render_rows = [
        {"view_id": "V01", "path": str((RENDERS / "full_page_200dpi.png").resolve()), "dpi": 200, "native_width_px": Image.open(RENDERS / "full_page_200dpi.png").width, "native_height_px": Image.open(RENDERS / "full_page_200dpi.png").height, "crop_rect_page_px": "FULL", "derivation": "pdftoppm direct from official PDF physical page 687; no resize"},
        {"view_id": "V02", "path": str((RENDERS / "full_page_300dpi.png").resolve()), "dpi": 300, "native_width_px": full_img.width, "native_height_px": full_img.height, "crop_rect_page_px": "FULL", "derivation": "pdftoppm direct from official PDF physical page 687; no resize"},
        {"view_id": "V03", "path": str((RENDERS / "figure_crop_300dpi.png").resolve()), "dpi": 300, "native_width_px": figure_crop.width, "native_height_px": figure_crop.height, "crop_rect_page_px": json.dumps(fbox), "derivation": "integer crop of V02; no resize"},
        {"view_id": "V04", "path": str((RENDERS / "standalone_300dpi.png").resolve()), "dpi": 300, "native_width_px": standalone.width, "native_height_px": standalone.height, "crop_rect_page_px": json.dumps(bbox), "derivation": "integer body crop of V02; no resize; PDF-derived standalone"},
        {"view_id": "V05", "path": str((RENDERS / "grayscale_300dpi.png").resolve()), "dpi": 300, "native_width_px": figure_crop.width, "native_height_px": figure_crop.height, "crop_rect_page_px": json.dumps(fbox), "derivation": "grayscale color conversion of V03; no resize"},
    ]
    write_csv(MACHINE / "render_inventory.csv", render_rows)

    lines = source_line_map()
    raw = page.get_text("rawdict")
    chars = []
    excluded_chars = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    rect = fitz.Rect(ch["bbox"])
                    center = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    in_scope = FIGURE_RECT_PT.contains(center)
                    if not in_scope:
                        continue
                    if ch["c"].isspace():
                        excluded_chars.append({"char": ch["c"], "bbox_pt": list(rect), "reason": "whitespace has no visible foreground"})
                        continue
                    pid, role = parent_for_char(rect)
                    quad = fitz.recover_char_quad(line["dir"], span, ch)
                    chars.append(
                        {
                            "char": ch["c"],
                            "bbox_pt": list(rect),
                            "origin_pt": list(ch["origin"]),
                            "font": span["font"],
                            "pdf_size_pt": float(span["size"]),
                            "pdf_color_int": int(span["color"]),
                            "parent_id": pid,
                            "role": role,
                            "quad_pt": [[float(p.x), float(p.y)] for p in (quad.ul, quad.ur, quad.ll, quad.lr)],
                        }
                    )
    parent_rank = {
        "T_AXIS_Y": 1, "T_AXIS_X": 2, "T_STATE_6": 3, "T_STATE_5": 4, "T_STATE_4": 5,
        "T_LONG_AXIS": 6, "T_STATE_2": 7, "T_STATE_3": 8, "T_STATE_1": 9, "T_STATE_0": 10,
        "T_SHORT_AXIS": 11, "T_UPDATE_X1": 12, "T_UPDATE_X2": 13, "T_NOTE": 14,
        "T_CAPTION_LABEL": 15, "T_CAPTION": 16,
    }
    chars.sort(key=lambda x: (parent_rank[x["parent_id"]], x["bbox_pt"][1], x["bbox_pt"][0]))
    objects: list[dict] = []
    glyph_rows = []
    source_rows_by_parent: dict[str, dict] = {}
    for idx, ch in enumerate(chars, 1):
        gid = f"G{idx:03d}"
        safe = f"{gid}_U{ord(ch['char']):04X}"
        rect = fitz.Rect(ch["bbox_pt"])
        pxbox = pt_rect_to_px(rect)
        target = rgb_from_pdf_color(ch["pdf_color_int"])
        mask, bg = char_mask(full_arr, pxbox, target, ch["quad_pt"])
        h_ink, w_ink, area, unique_px = ink_stats(mask)
        mask_path = MASKS / "glyph" / f"{safe}.png"
        card_path = CARDS / "glyph" / f"{safe}.png"
        save_small_mask(mask, mask_path)
        build_triptych_card(full_img, mask, pxbox, f"{gid} {ch['char']} U+{ord(ch['char']):04X} parent={ch['parent_id']}", card_path)
        klass = script_class(ch["char"], ch["parent_id"], ch["pdf_size_pt"], ch["font"])
        src_file, src_line, declared, scale, effective, src_basis = source_info(ch["parent_id"], ch["pdf_size_pt"], lines)
        if ch["parent_id"] not in source_rows_by_parent:
            source_rows_by_parent[ch["parent_id"]] = {
                "parent_id": ch["parent_id"], "role": ch["role"], "source_file": src_file, "source_line": src_line,
                "declared_pt": declared, "graphics_scale": scale, "effective_pt": effective, "basis": src_basis,
                "strict_9_5_delta_pt": round(effective - 9.5, 2), "r168_machine_note": "numeric threshold only; manual readability/semantic verdict required",
            }
        row = {
            "glyph_id": gid,
            "safe_filename": safe,
            "parent_id": ch["parent_id"],
            "role": ch["role"],
            "char": ch["char"],
            "codepoint": f"U+{ord(ch['char']):04X}",
            "font": ch["font"],
            "script_class": klass,
            "pdf_span_size_pt": round(ch["pdf_size_pt"], 4),
            "source_file": src_file,
            "source_line": src_line,
            "declared_pt": declared,
            "graphics_scale": scale,
            "effective_pt": effective,
            "bbox_pt": json.dumps([round(v, 4) for v in ch["bbox_pt"]]),
            "quad_pt": json.dumps([[round(v, 4) for v in p] for p in ch["quad_pt"]]),
            "bbox_px_page": json.dumps(pxbox),
            "target_rgb": json.dumps(target),
            "local_background_rgb": json.dumps(bg),
            "h_ink_px": h_ink,
            "w_ink_px": w_ink,
            "ink_area_px": area,
            "mask_nonempty": area > 0,
            "mask_path": str(mask_path.resolve()),
            "card_path": str(card_path.resolve()),
        }
        glyph_rows.append(row)
        objects.append(
            {
                "object_id": gid,
                "kind": "GLYPH",
                "role": ch["role"],
                "parent_id": ch["parent_id"],
                "mask_bbox_px": pxbox,
                "mask_array": mask,
                "mask_path": str(mask_path.resolve()),
                "char": ch["char"],
            }
        )
    write_csv(MACHINE / "glyph_inventory.csv", glyph_rows)
    write_csv(MACHINE / "source_font_inventory.csv", list(source_rows_by_parent.values()))
    write_json(MACHINE / "excluded_whitespace.json", excluded_chars)

    # Contact sheets are exact concatenations of 8x cards; the cards are never
    # resampled while assembling the sheets.
    glyph_card_paths = [Path(r["card_path"]) for r in glyph_rows]
    sheet_rows = []
    for sheet_idx in range(0, len(glyph_card_paths), 4):
        batch = glyph_card_paths[sheet_idx : sheet_idx + 4]
        images = [Image.open(p).convert("RGB") for p in batch]
        width = max(i.width for i in images)
        height = sum(i.height for i in images) + 8 * (len(images) - 1)
        sheet = Image.new("RGB", (width, height), "white")
        y = 0
        for im in images:
            sheet.paste(im, (0, y))
            y += im.height + 8
        sheet_no = sheet_idx // 4 + 1
        path = CARDS / "glyph_contact_sheets" / f"glyph_contact_sheet_{sheet_no:03d}.png"
        sheet.save(path)
        for cell, r in enumerate(glyph_rows[sheet_idx : sheet_idx + 4], 1):
            sheet_rows.append({"glyph_id": r["glyph_id"], "sheet": path.name, "cell": cell, "card_path": r["card_path"]})
    write_csv(MACHINE / "glyph_contact_sheet_index.csv", sheet_rows)

    drawings = page.get_drawings()
    graphic_rows = []
    excluded_graphics = []
    for gd in graphic_definitions():
        mask, mbox = draw_paths_to_mask(page.rect, drawings, gd["indices"])
        safe = gd["id"]
        mask_path = MASKS / "graphic" / f"{safe}.png"
        save_small_mask(mask, mask_path)
        h, w, area, _ = ink_stats(mask)
        row = {
            "object_id": gd["id"],
            "safe_filename": safe,
            "kind": gd["kind"],
            "role": gd["role"],
            "pdf_drawing_indices": json.dumps([c[0] for c in gd["indices"]]),
            "component_modes": json.dumps([{"drawing_index": c[0], "stroke": c[1], "fill": c[2]} for c in gd["indices"]]),
            "mask_bbox_px": json.dumps(mbox),
            "mask_width_px": w,
            "mask_height_px": h,
            "mask_area_px": area,
            "mask_nonempty": area > 0,
            "mask_path": str(mask_path.resolve()),
            "pair_denominator_included": not gd.get("excluded", False),
            "exclusion_reason": gd.get("exclude_reason", ""),
        }
        graphic_rows.append(row)
        if gd.get("excluded", False):
            excluded_graphics.append(row)
            continue
        objects.append(
            {
                "object_id": gd["id"],
                "kind": gd["kind"],
                "role": gd["role"],
                "parent_id": gd["id"],
                "mask_bbox_px": mbox,
                "mask_array": mask,
                "mask_path": str(mask_path.resolve()),
            }
        )
    write_csv(MACHINE / "graphic_inventory.csv", graphic_rows)

    # Machine overlay: every foreground glyph bbox and every graphic bbox.
    overlay = full_img.crop(fbox).convert("RGB")
    od = ImageDraw.Draw(overlay)
    colors = {"GLYPH": (220, 30, 30), "LINE_ARROW": (0, 120, 255), "DATA_CURVE": (0, 150, 80), "MARKER": (150, 0, 200), "NODE_BORDER": (255, 120, 0)}
    for obj in objects:
        x0, y0, x1, y1 = obj["mask_bbox_px"]
        rel = (x0 - fbox[0], y0 - fbox[1], x1 - fbox[0], y1 - fbox[1])
        od.rectangle(rel, outline=colors.get(obj["kind"], (0, 0, 0)), width=1)
        if obj["kind"] != "GLYPH":
            od.text((rel[0] + 1, rel[1] + 1), obj["object_id"], fill=colors.get(obj["kind"], (0, 0, 0)))
    overlay.save(RENDERS / "text_and_object_measurement_overlay_300dpi.png")
    render_rows.append({"view_id": "V06", "path": str((RENDERS / "text_and_object_measurement_overlay_300dpi.png").resolve()), "dpi": 300, "native_width_px": overlay.width, "native_height_px": overlay.height, "crop_rect_page_px": json.dumps(fbox), "derivation": "bbox overlay on V03; native grid preserved"})
    write_csv(MACHINE / "render_inventory.csv", render_rows)

    # All unordered foreground pairs. No manual/decision fields are generated.
    pair_rows = []
    critical_rows = []
    for pair_no, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        pid = f"P{pair_no:05d}"
        rclass, threshold = relation_class(a, b)
        inter = mask_intersection(a, b)
        rough = rect_distance(a["mask_bbox_px"], b["mask_bbox_px"])
        need_exact = inter > 0 or (threshold is not None and rough < threshold + 8) or (rclass == "GRAPHIC_GRAPHIC" and rough < 4)
        exact = exact_mask_distance(a, b) if need_exact else rough
        if rclass == "SAME_TEXT_PARENT":
            machine_flag = "DESIGN_INTERNAL_INTERSECTION" if inter else "SAME_PARENT_SEPARATE"
        elif inter > 0:
            machine_flag = "INTERSECTION_CANDIDATE"
        elif threshold is not None and exact < threshold:
            machine_flag = "BELOW_CLASS_CLEARANCE"
        else:
            machine_flag = "SEPARATE"
        critical = machine_flag in {"INTERSECTION_CANDIDATE", "BELOW_CLASS_CLEARANCE", "DESIGN_INTERNAL_INTERSECTION"} or (
            threshold is not None and exact < threshold + 2 and rclass != "SAME_TEXT_PARENT"
        )
        row = {
            "pair_id": pid,
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "kind_a": a["kind"],
            "kind_b": b["kind"],
            "relation_class": rclass,
            "same_parent": a["parent_id"] == b["parent_id"],
            "bbox_distance_px": round(rough, 4),
            "raw_mask_intersection_px": inter,
            "exact_raw_mask_distance_px": round(exact, 4) if not math.isnan(exact) else "",
            "class_clearance_threshold_px": "" if threshold is None else threshold,
            "machine_flag": machine_flag,
            "critical_evidence_generated": critical,
        }
        pair_rows.append(row)
        if critical:
            out_dir = PAIRS / pid
            pair_evidence(full_img, a, b, pid, out_dir)
            crow = dict(row)
            crow["evidence_dir"] = str(out_dir.resolve())
            critical_rows.append(crow)
    write_csv(MACHINE / "all_unordered_pairs.csv", pair_rows)
    write_csv(MACHINE / "critical_pair_inventory.csv", critical_rows)

    # Clip and crop-edge machine measurements. Caption glyphs use the complete
    # figure crop; body glyphs and all graphics use the standalone crop.
    clip_rows = []
    for obj in objects:
        container = fbox if (obj["kind"] == "GLYPH" and obj["parent_id"].startswith("T_CAPTION")) else bbox
        x0, y0, x1, y1 = obj["mask_bbox_px"]
        edge = min(x0 - container[0], y0 - container[1], container[2] - x1, container[3] - y1)
        clip_rows.append(
            {
                "object_id": obj["object_id"],
                "container": "FIGURE_CROP" if container == fbox else "STANDALONE_BODY",
                "container_rect_px": json.dumps(container),
                "mask_bbox_px": json.dumps(obj["mask_bbox_px"]),
                "min_bbox_to_crop_edge_px": edge,
                "mask_nonempty": int(np.count_nonzero(obj["mask_array"])) > 0,
                "touches_crop_edge": edge <= 0,
            }
        )
    write_csv(MACHINE / "clip_inventory.csv", clip_rows)

    # Parent / role peer measurements are numeric only; no PASS/FAIL is emitted.
    peer_rows = []
    for (parent, klass), group in itertools.groupby(sorted(glyph_rows, key=lambda r: (r["parent_id"], r["script_class"])), key=lambda r: (r["parent_id"], r["script_class"])):
        vals = [int(r["h_ink_px"]) for r in group]
        vals_nonzero = [v for v in vals if v > 0]
        median = float(np.median(vals_nonzero)) if vals_nonzero else float("nan")
        peer_rows.append({"parent_id": parent, "script_class": klass, "count": len(vals), "median_h_ink_px": median, "min_h_ink_px": min(vals) if vals else "", "max_h_ink_px": max(vals) if vals else "", "max_min_ratio": round(max(vals_nonzero) / min(vals_nonzero), 4) if vals_nonzero and min(vals_nonzero) else ""})
    write_csv(MACHINE / "peer_role_measurements.csv", peer_rows)

    # Pair denominator and dual PDF/path inventory accounting.
    expected_pairs = len(objects) * (len(objects) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise RuntimeError("Pair denominator mismatch")
    covered_drawing_indices = sorted({i for r in graphic_definitions() for i, _, _ in r["indices"]})
    figure_drawing_indices = []
    for i, d in enumerate(drawings):
        r = fitz.Rect(d["rect"])
        r = fitz.Rect(r.x0 - 0.01, r.y0 - 0.01, r.x1 + 0.01, r.y1 + 0.01)
        if r.intersects(BODY_RECT_PT):
            figure_drawing_indices.append(i)
    unmapped = sorted(set(figure_drawing_indices) - set(covered_drawing_indices))
    extra = sorted(set(covered_drawing_indices) - set(figure_drawing_indices))
    summary = {
        "uid": UID,
        "handoff_id": HANDOFF_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "glyph_count": len(glyph_rows),
        "text_parent_count": len({r["parent_id"] for r in glyph_rows}),
        "foreground_graphic_count": len(objects) - len(glyph_rows),
        "excluded_background_graphic_count": len(excluded_graphics),
        "foreground_object_count_n": len(objects),
        "unordered_pair_expected_c_n_2": expected_pairs,
        "unordered_pair_rows": len(pair_rows),
        "critical_pair_rows": len(critical_rows),
        "empty_glyph_masks": sum(not bool(r["mask_nonempty"]) for r in glyph_rows),
        "empty_graphic_masks": sum(not bool(r["mask_nonempty"]) for r in graphic_rows),
        "clip_edge_touch_candidates": sum(bool(r["touches_crop_edge"]) for r in clip_rows),
        "figure_pdf_drawing_indices": figure_drawing_indices,
        "mapped_pdf_drawing_indices": covered_drawing_indices,
        "unmapped_pdf_drawing_indices": unmapped,
        "mapped_indices_not_in_body_intersection": extra,
        "visible_whitespace_exclusions": len(excluded_chars),
        "machine_decisions_generated": False,
        "manual_fields_generated": False,
    }
    if unmapped:
        raise RuntimeError(f"Unmapped foreground drawing indices: {unmapped}")
    write_json(MACHINE / "machine_summary.json", summary)

    # Safe filename inventory: all referenced ordinary files must be portable.
    safe_rows = []
    for r in glyph_rows:
        safe_rows.append({"object_id": r["glyph_id"], "safe_filename": Path(r["mask_path"]).name, "ordinary_file": True, "path": r["mask_path"]})
        safe_rows.append({"object_id": r["glyph_id"], "safe_filename": Path(r["card_path"]).name, "ordinary_file": True, "path": r["card_path"]})
    for r in graphic_rows:
        safe_rows.append({"object_id": r["object_id"], "safe_filename": Path(r["mask_path"]).name, "ordinary_file": True, "path": r["mask_path"]})
    write_csv(MACHINE / "safe_filename_inventory.csv", safe_rows)


if __name__ == "__main__":
    main()
