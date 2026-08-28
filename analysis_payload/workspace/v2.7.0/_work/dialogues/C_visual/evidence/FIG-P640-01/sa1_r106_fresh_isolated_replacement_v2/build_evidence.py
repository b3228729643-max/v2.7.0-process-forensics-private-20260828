from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C04.tex")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r106_fresh_isolated_replacement_v2")
PAGE_INDEX = 689
PHYSICAL_PAGE = 690
PRINTED_PAGE = 677
SCALE = 300.0 / 72.0
FIGURE_CLIP_PT = (85.0, 65.0, 523.0, 294.0)
BODY_CLIP_PT = (85.0, 65.0, 523.0, 258.0)
PANEL_BOUNDS_PT = {
    "A": (85.0, 65.0, 360.0, 258.0),
    "B": (365.0, 65.0, 523.0, 220.0),
    "CAPTION": (85.0, 258.0, 523.0, 294.0),
}


def ensure_dirs() -> None:
    for name in (
        "glyph_masks",
        "glyph_rois_1x",
        "glyph_rois_8x",
        "glyph_contact_sheets_8x",
        "object_masks",
        "critical_pair_rois_1x",
        "critical_pair_rois_8x",
        "critical_pair_contact_sheets_8x",
    ):
        (OUT / name).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def bbox_union(boxes):
    boxes = [tuple(float(v) for v in b) for b in boxes]
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def bbox_intersection_area(a, b) -> float:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def bbox_clearance(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def pt_bbox_to_crop_px(box, pix_x: int, pix_y: int):
    x0 = math.floor(float(box[0]) * SCALE) - pix_x
    y0 = math.floor(float(box[1]) * SCALE) - pix_y
    x1 = math.ceil(float(box[2]) * SCALE) - pix_x
    y1 = math.ceil(float(box[3]) * SCALE) - pix_y
    return (x0, y0, x1, y1)


def clip_px_box(box, width: int, height: int, pad: int = 0):
    return (
        max(0, int(box[0]) - pad),
        max(0, int(box[1]) - pad),
        min(width, int(box[2]) + pad),
        min(height, int(box[3]) + pad),
    )


def foreground_from_white(rgb: np.ndarray) -> np.ndarray:
    return np.max(255 - rgb.astype(np.int16), axis=2) >= 20


def segment_expected_color(rgb: np.ndarray, color01) -> np.ndarray:
    c = np.array([round(255 * float(v)) for v in color01], dtype=np.float32)
    p = rgb.astype(np.float32)
    denom = 255.0 - c
    valid = denom > 8.0
    alpha = (255.0 - p[..., valid]) / denom[valid]
    mean = np.mean(alpha, axis=2)
    spread = np.max(alpha, axis=2) - np.min(alpha, axis=2)
    return (mean >= 0.085) & (mean <= 1.18) & (spread <= 0.11)


def color_fit(rgb: np.ndarray, color01):
    c = np.array([round(255 * float(v)) for v in color01], dtype=np.float32)
    p = rgb.astype(np.float32)
    direction = 255.0 - c
    denom = float(np.dot(direction, direction))
    alpha = np.sum((255.0 - p) * direction, axis=2) / max(denom, 1.0)
    alpha_clip = np.clip(alpha, 0.0, 1.0)
    recon = 255.0 - alpha_clip[..., None] * direction[None, None, :]
    residual = np.sqrt(np.sum((p - recon) ** 2, axis=2))
    valid = (alpha >= 0.085) & (alpha <= 1.15) & (residual <= 14.0)
    return residual, valid


def segment_expected_color_nearest(rgb: np.ndarray, color01, palette) -> np.ndarray:
    fits = [color_fit(rgb, c) for c in palette]
    residuals = np.stack([x[0] for x in fits], axis=2)
    valids = np.stack([x[1] for x in fits], axis=2)
    residuals = np.where(valids, residuals, np.inf)
    best = np.argmin(residuals, axis=2)
    best_residual = np.min(residuals, axis=2)
    target = palette.index(tuple(color01))
    return (best == target) & np.isfinite(best_residual)


def role_source(role: str):
    if role == "TICK":
        return 5, 9.6
    if role in {"AXIS_LABEL", "FORMULA_AXIS_LABEL"}:
        return 6, 9.8
    if role in {"PANEL_TITLE", "FORMULA_TITLE"}:
        return 7, 9.6
    if role == "LEGEND":
        return 22, 9.6
    if role in {"ANNOTATION", "POINT_LABEL"}:
        return 45 if role == "POINT_LABEL" else 47, 9.6
    if role == "CAPTION":
        return 52, 9.96
    return 0, 9.6


TEXT_SPECS = [
    ("T001", "A", "TICK", "A_XTICK_0", [(1, 0)]),
    ("T002", "A", "TICK", "A_XTICK_2", [(1, 1)]),
    ("T003", "A", "TICK", "A_XTICK_4", [(1, 2)]),
    ("T004", "A", "TICK", "A_XTICK_6", [(1, 3)]),
    ("T005", "A", "TICK", "A_XTICK_8", [(1, 4)]),
    ("T006", "A", "TICK", "A_XTICK_10", [(1, 5)]),
    ("T007", "A", "TICK", "A_XTICK_12", [(1, 6)]),
    ("T008", "A", "TICK", "A_YTICK_0", [(1, 7)]),
    ("T009", "A", "TICK", "A_YTICK_025", [(2, 0)]),
    ("T010", "A", "TICK", "A_YTICK_05", [(3, 0)]),
    ("T011", "A", "TICK", "A_YTICK_075", [(4, 0)]),
    ("T012", "A", "TICK", "A_YTICK_1", [(5, 0)]),
    ("T013", "A", "AXIS_LABEL", "A_XLABEL", [(6, 0)]),
    ("T014", "A", "FORMULA_AXIS_LABEL", "A_YLABEL", [(7, 0), (8, 0), (8, 1), (8, 2)]),
    ("T015", "A", "PANEL_TITLE", "A_TITLE", [(9, 0)]),
    ("T016", "A", "LEGEND", "A_LEGEND_095", [(10, 0)]),
    ("T017", "A", "LEGEND", "A_LEGEND_070", [(10, 1)]),
    ("T018", "A", "LEGEND", "A_LEGEND_020", [(10, 2)]),
    ("T019", "B", "TICK", "B_XTICK_0", [(11, 0)]),
    ("T020", "B", "TICK", "B_XTICK_05", [(11, 1)]),
    ("T021", "B", "TICK", "B_XTICK_099", [(11, 2)]),
    ("T022", "B", "TICK", "B_YTICK_0", [(11, 3)]),
    ("T023", "B", "TICK", "B_YTICK_05", [(12, 0)]),
    ("T024", "B", "TICK", "B_YTICK_1", [(13, 0)]),
    ("T025", "B", "POINT_LABEL", "B_POINT_099_0010", [(14, 0)]),
    ("T026", "B", "ANNOTATION", "B_LIMIT_NOTE", [(15, 0), (15, 1)]),
    ("T027", "B", "FORMULA_AXIS_LABEL", "B_XLABEL", [(16, 0)]),
    ("T028", "B", "FORMULA_AXIS_LABEL", "B_YLABEL", [(17, 0)]),
    ("T029", "B", "PANEL_TITLE", "B_TITLE_TEXT", [(18, 0)]),
    ("T030", "B", "FORMULA_TITLE", "B_TITLE_NUMERATOR", [(19, 0)]),
    ("T031", "B", "FORMULA_TITLE", "B_TITLE_DENOMINATOR", [(20, 0)]),
    ("T032", "CAPTION", "CAPTION", "FIGURE_CAPTION", [(21, 0), (21, 1), (21, 2)]),
]


GRAPHIC_SPECS = [
    ("G001", "A", "PANEL_AXIS_TICKS", "A_AXIS_FRAME_TICKS", [3, 4, 5], True),
    ("G002", "A", "DATA_CURVE", "A_CURVE_RHO095", [18], True),
    ("G003", "A", "DATA_CURVE", "A_CURVE_RHO070", [19], True),
    ("G004", "A", "DATA_CURVE", "A_CURVE_RHO020", [20], True),
    ("G005", "A", "LEGEND_SAMPLE", "A_LEGEND_SAMPLE_095", [24], True),
    ("G006", "A", "LEGEND_SAMPLE", "A_LEGEND_SAMPLE_070", [26], True),
    ("G007", "A", "LEGEND_SAMPLE", "A_LEGEND_SAMPLE_020", [28], True),
    ("G008", "B", "PANEL_AXIS_TICKS", "B_AXES_TICKS_ARROWS", [30, 31, 32, 33, 34, 35], True),
    ("G009", "B", "DATA_CURVE", "B_ESS_CURVE", [42], True),
    ("G010", "B", "OPAQUE_BACKGROUND", "B_POINT_LABEL_HALO", [43], False),
    ("G011", "B", "OPAQUE_BACKGROUND", "B_LIMIT_NOTE_HALO", [45], False),
    ("G012", "B", "MARKER", "B_ENDPOINT_MARKER", [47], True),
    ("G013", "B", "MATH_RULE", "B_TITLE_FRACTION_RULE", [52], True),
]


def make_text_objects(raw):
    line_lookup = {}
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block["lines"]):
            line_lookup[(bi, li)] = line

    objects = []
    line_to_parent = {}
    for oid, panel, role, semantic, keys in TEXT_SPECS:
        lines = [line_lookup[k] for k in keys]
        spans = [s for line in lines for s in line["spans"]]
        chars = [c for s in spans for c in s["chars"] if c["c"].strip()]
        text = "".join(c["c"] for c in chars)
        bbox = bbox_union([c["bbox"] for c in chars])
        source_line, declared_pt = role_source(role)
        objects.append(
            {
                "object_id": oid,
                "object_type": "TEXT",
                "panel_id": panel,
                "role": role,
                "semantic_name": semantic,
                "text": text,
                "bbox_pt": bbox,
                "source_line": source_line,
                "declared_pt": declared_pt,
                "graphics_scale": 1.0,
                "effective_pt": declared_pt,
                "foreground": True,
                "chars": chars,
                "spans": spans,
            }
        )
        for key in keys:
            line_to_parent[key] = oid
    return objects, line_to_parent


def make_graphics(drawings):
    by_seq = {int(d.get("seqno")): d for d in drawings}
    primitives = []
    for idx, d in enumerate(drawings):
        seq = int(d.get("seqno"))
        rect = tuple(float(v) for v in d["rect"])
        if bbox_intersection_area(rect, BODY_CLIP_PT) == 0 and not (
            rect[0] <= BODY_CLIP_PT[2] and rect[2] >= BODY_CLIP_PT[0] and rect[1] <= BODY_CLIP_PT[3] and rect[3] >= BODY_CLIP_PT[1]
        ):
            continue
        op_counts = defaultdict(int)
        for item in d["items"]:
            op_counts[item[0]] += 1
        primitives.append(
            {
                "primitive_index": idx,
                "seqno": seq,
                "bbox_x0_pt": rect[0],
                "bbox_y0_pt": rect[1],
                "bbox_x1_pt": rect[2],
                "bbox_y1_pt": rect[3],
                "stroke_width_pt": d.get("width"),
                "stroke_color": json.dumps(d.get("color")),
                "fill_color": json.dumps(d.get("fill")),
                "dashes": d.get("dashes"),
                "item_count": len(d["items"]),
                "operator_counts": json.dumps(dict(op_counts), sort_keys=True),
            }
        )

    objects = []
    for oid, panel, role, semantic, seqnos, foreground in GRAPHIC_SPECS:
        ds = [by_seq[s] for s in seqnos]
        bbox = bbox_union([tuple(float(v) for v in d["rect"]) for d in ds])
        colors = []
        for d in ds:
            if d.get("color") is not None:
                colors.append(tuple(d["color"]))
            if d.get("fill") is not None and tuple(d["fill"]) != (1.0, 1.0, 1.0):
                colors.append(tuple(d["fill"]))
        objects.append(
            {
                "object_id": oid,
                "object_type": "GRAPHIC",
                "panel_id": panel,
                "role": role,
                "semantic_name": semantic,
                "text": "",
                "bbox_pt": bbox,
                "source_line": 0,
                "declared_pt": "",
                "graphics_scale": "",
                "effective_pt": "",
                "foreground": foreground,
                "seqnos": seqnos,
                "colors": colors,
            }
        )
    return objects, primitives


def classify_char(char: str, font_size: float, base_pt: float, role: str) -> tuple[str, int | None]:
    cp = ord(char)
    if font_size < 0.80 * base_pt:
        return "NATURAL_SCRIPT", 15
    if char in ".,，。、：；;∶":
        return "LOW_PROFILE_PUNCTUATION", None
    if 0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_FULL", 30
    if char.isdigit() or ("A" <= char <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if char.islower() or char in "𝑘𝑡𝜌":
        return "LATIN_GREEK_LOWER", 17
    if char in "+−-=→/|()[]{}<>∣":
        return "MATH_OPERATOR_OR_DELIMITER", 22
    return "MATH_OR_OTHER", 22


def font_for_labels(size=18):
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def triple_view(original: Image.Image, mask: np.ndarray, title: str) -> Image.Image:
    rgb = np.array(original.convert("RGB"))
    overlay = rgb.copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_img = np.full_like(rgb, 255)
    mask_img[mask] = np.array([0, 0, 0], dtype=np.uint8)
    pad = 4
    label_h = 24
    w, h = original.size
    canvas = Image.new("RGB", (w * 3 + pad * 4, h + label_h + pad * 2), "white")
    canvas.paste(original, (pad, label_h + pad))
    canvas.paste(Image.fromarray(overlay), (w + pad * 2, label_h + pad))
    canvas.paste(Image.fromarray(mask_img), (w * 2 + pad * 3, label_h + pad))
    d = ImageDraw.Draw(canvas)
    f = font_for_labels(14)
    d.text((pad, 2), f"{title} | ORIGINAL", fill="black", font=f)
    d.text((w + pad * 2, 2), "TARGET OVERLAY", fill="black", font=f)
    d.text((w * 2 + pad * 3, 2), "MASK ONLY", fill="black", font=f)
    return canvas


def make_contact_sheets(files: list[Path], out_dir: Path, prefix: str, per_sheet: int = 12):
    font = font_for_labels(18)
    for sheet_idx, start in enumerate(range(0, len(files), per_sheet), 1):
        group = files[start : start + per_sheet]
        images = [Image.open(p).convert("RGB") for p in group]
        cell_w = max(im.width for im in images) + 20
        cell_h = max(im.height for im in images) + 44
        cols = 3
        rows = math.ceil(len(images) / cols)
        sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), "white")
        d = ImageDraw.Draw(sheet)
        for j, (p, im) in enumerate(zip(group, images)):
            x = (j % cols) * cell_w
            y = (j // cols) * cell_h
            d.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(160, 160, 160), width=1)
            d.text((x + 6, y + 4), p.stem, fill="black", font=font)
            sheet.paste(im, (x + 6, y + 34))
        sheet.save(out_dir / f"{prefix}_{sheet_idx:03d}.png")


def mask_bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def object_mask_crop(mask: np.ndarray, path: Path):
    bb = mask_bbox(mask)
    if bb is None:
        return None
    x0, y0, x1, y1 = bb
    Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8)).save(path)
    return bb


def pair_relation(a, b):
    if a["object_type"] == "TEXT" and b["object_type"] == "TEXT":
        return "TEXT-TEXT"
    if a["object_type"] == "TEXT" or b["object_type"] == "TEXT":
        t = a if a["object_type"] == "TEXT" else b
        g = b if a["object_type"] == "TEXT" else a
        return f"TEXT/{t['role']}-{g['role']}"
    return f"{a['role']}-{b['role']}"


def crop_relation_roi(rgb, mask_a, mask_b, a, b, pad=10):
    union = mask_a | mask_b
    bb = mask_bbox(union)
    if bb is None:
        boxes = [a["bbox_px"], b["bbox_px"]]
        bb = (
            min(x[0] for x in boxes),
            min(x[1] for x in boxes),
            max(x[2] for x in boxes),
            max(x[3] for x in boxes),
        )
    # Localize very large graphic objects to the smaller object's neighborhood.
    areas = []
    for obj in (a, b):
        ob = obj["bbox_px"]
        areas.append(max(1, (ob[2] - ob[0]) * (ob[3] - ob[1])))
    small = a if areas[0] <= areas[1] else b
    sb = small["bbox_px"]
    if (bb[2] - bb[0]) > 700 or (bb[3] - bb[1]) > 500:
        bb = (sb[0] - 20, sb[1] - 20, sb[2] + 20, sb[3] + 20)
    bb = clip_px_box(bb, rgb.shape[1], rgb.shape[0], pad=pad)
    x0, y0, x1, y1 = bb
    base = rgb[y0:y1, x0:x1].copy()
    ma = mask_a[y0:y1, x0:x1]
    mb = mask_b[y0:y1, x0:x1]
    views = []
    views.append(base)
    va = base.copy(); va[ma] = np.array([255, 0, 0], dtype=np.uint8); views.append(va)
    vb = base.copy(); vb[mb] = np.array([0, 80, 255], dtype=np.uint8); views.append(vb)
    vi = base.copy(); vi[ma & mb] = np.array([255, 0, 255], dtype=np.uint8); views.append(vi)
    h, w = base.shape[:2]
    canvas = Image.new("RGB", (w * 4 + 20, h + 28), "white")
    for i, v in enumerate(views):
        canvas.paste(Image.fromarray(v), (5 + i * (w + 5), 24))
    d = ImageDraw.Draw(canvas)
    d.text((5, 2), f"{a['object_id']} + {b['object_id']} | ORIGINAL / A RED / B BLUE / INTERSECTION MAGENTA", fill="black", font=font_for_labels(14))
    return canvas, bb


def main():
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()
    text_objects, _ = make_text_objects(raw)
    graphic_objects, primitive_rows = make_graphics(drawings)

    clip = fitz.Rect(*FIGURE_CLIP_PT)
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=False, colorspace=fitz.csRGB)
    rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3].copy()
    height, width = rgb.shape[:2]
    Image.fromarray(rgb).save(OUT / "figure_crop_300dpi.png")
    Image.fromarray(rgb).convert("L").save(OUT / "grayscale_300dpi.png")

    identity = {
        "uid": "FIG-P640-01",
        "handoff_id": "C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-REPLACEMENT-V2",
        "agent_identity": "/root/sa1_fig_p640_r106_fresh_isolated_replacement_v2",
        "model": "gpt-5.6-sol",
        "reasoning": "xhigh",
        "fork_turns": "none",
        "pdf": str(PDF),
        "pdf_pages": doc.page_count,
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_size_pt": [page.rect.width, page.rect.height],
        "figure_clip_pt": list(FIGURE_CLIP_PT),
        "figure_crop_native_px": [width, height],
        "figure_crop_page_pixel_origin": [pix.x, pix.y],
        "render_dpi": 300,
        "mapping_method": "unique current-caption text hit found by scanning the allowed official PDF from the allowed current source text",
    }
    (OUT / "identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

    primitive_fields = [
        "primitive_index", "seqno", "bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt",
        "stroke_width_pt", "stroke_color", "fill_color", "dashes", "item_count", "operator_counts",
    ]
    write_csv(OUT / "drawing_primitives_machine.csv", primitive_rows, primitive_fields)

    object_by_id = {}
    glyph_rows = []
    glyph_masks_full = {}
    parent_glyph_ids = defaultdict(list)
    glyph_roi8_files = []
    gid_counter = 0

    for obj in text_objects:
        obj["bbox_px"] = pt_bbox_to_crop_px(obj["bbox_pt"], pix.x, pix.y)
        object_by_id[obj["object_id"]] = obj
        for span in obj["spans"]:
            for char_info in span["chars"]:
                char = char_info["c"]
                if not char.strip():
                    continue
                gid_counter += 1
                gid = f"C{gid_counter:04d}"
                bbox_pt = tuple(float(v) for v in char_info["bbox"])
                bbox_px = clip_px_box(pt_bbox_to_crop_px(bbox_pt, pix.x, pix.y), width, height, pad=0)
                x0, y0, x1, y1 = bbox_px
                local_rgb = rgb[y0:y1, x0:x1]
                local_mask = foreground_from_white(local_rgb) if local_rgb.size else np.zeros((0, 0), dtype=bool)
                full_mask = np.zeros((height, width), dtype=bool)
                if local_mask.size:
                    full_mask[y0:y1, x0:x1] = local_mask
                glyph_masks_full[gid] = full_mask
                parent_glyph_ids[obj["object_id"]].append(gid)
                mb = mask_bbox(local_mask)
                h_ink = 0 if mb is None else mb[3] - mb[1]
                w_ink = 0 if mb is None else mb[2] - mb[0]
                mask_pixels = int(local_mask.sum())
                script_class, legacy_threshold = classify_char(
                    char, float(span["size"]), float(obj["effective_pt"]), obj["role"]
                )
                if legacy_threshold is None:
                    legacy_status = "CALIBRATION_ADVISORY"
                else:
                    legacy_status = "LEGACY_MET" if h_ink >= legacy_threshold else "LEGACY_BELOW"
                mask_path = OUT / "glyph_masks" / f"{gid}.png"
                Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8)).save(mask_path)
                roi_box = clip_px_box(bbox_px, width, height, pad=4)
                rx0, ry0, rx1, ry1 = roi_box
                roi_rgb = rgb[ry0:ry1, rx0:rx1]
                roi_mask = full_mask[ry0:ry1, rx0:rx1]
                roi1 = triple_view(Image.fromarray(roi_rgb), roi_mask, gid)
                roi1_path = OUT / "glyph_rois_1x" / f"{gid}.png"
                roi8_path = OUT / "glyph_rois_8x" / f"{gid}.png"
                roi1.save(roi1_path)
                roi1.resize((roi1.width * 8, roi1.height * 8), Image.Resampling.NEAREST).save(roi8_path)
                glyph_roi8_files.append(roi8_path)
                glyph_rows.append(
                    {
                        "glyph_id": gid,
                        "safe_filename": f"{gid}.png",
                        "parent_object_id": obj["object_id"],
                        "panel_id": obj["panel_id"],
                        "role": obj["role"],
                        "char": char,
                        "codepoint": f"U+{ord(char):04X}",
                        "font": span["font"],
                        "pdf_font_size_pt": float(span["size"]),
                        "source_base_pt": obj["effective_pt"],
                        "script_class_machine": script_class,
                        "bbox_x0_px": x0,
                        "bbox_y0_px": y0,
                        "bbox_x1_px": x1,
                        "bbox_y1_px": y1,
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "mask_pixel_count": mask_pixels,
                        "legacy_threshold_px_advisory": "" if legacy_threshold is None else legacy_threshold,
                        "legacy_threshold_status_advisory": legacy_status,
                        "mask_path": str(mask_path.relative_to(OUT)).replace("\\", "/"),
                        "roi_1x_path": str(roi1_path.relative_to(OUT)).replace("\\", "/"),
                        "roi_8x_path": str(roi8_path.relative_to(OUT)).replace("\\", "/"),
                    }
                )

    # A raw PDF character bbox can overlap its neighbour by a boundary raster row.
    # Allocate every claimed final-visible pixel to exactly one glyph using the
    # nearest normalized glyph-bbox centre. This is a traceable subtraction,
    # not morphological growth, and prevents one page pixel being counted twice.
    claim_count = np.zeros((height, width), dtype=np.uint16)
    for m in glyph_masks_full.values():
        claim_count += m.astype(np.uint16)
    oy, ox = np.nonzero(claim_count > 1)
    glyph_order = [r["glyph_id"] for r in glyph_rows]
    row_by_gid = {r["glyph_id"]: r for r in glyph_rows}
    for y, x in zip(oy.tolist(), ox.tolist()):
        candidates = [gid for gid in glyph_order if glyph_masks_full[gid][y, x]]
        scored = []
        for gid in candidates:
            r = row_by_gid[gid]
            cx = (r["bbox_x0_px"] + r["bbox_x1_px"] - 1) / 2.0
            cy = (r["bbox_y0_px"] + r["bbox_y1_px"] - 1) / 2.0
            sx = max(1.0, r["bbox_x1_px"] - r["bbox_x0_px"])
            sy = max(1.0, r["bbox_y1_px"] - r["bbox_y0_px"])
            scored.append((((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2, gid))
        winner = min(scored)[1]
        for gid in candidates:
            if gid != winner:
                glyph_masks_full[gid][y, x] = False

    # Refresh all machine measurements and visual evidence after unique-pixel allocation.
    for r in glyph_rows:
        gid = r["glyph_id"]
        full_mask = glyph_masks_full[gid]
        x0, y0, x1, y1 = (r["bbox_x0_px"], r["bbox_y0_px"], r["bbox_x1_px"], r["bbox_y1_px"])
        local_mask = full_mask[y0:y1, x0:x1]
        mb = mask_bbox(local_mask)
        r["h_ink_px"] = 0 if mb is None else mb[3] - mb[1]
        r["w_ink_px"] = 0 if mb is None else mb[2] - mb[0]
        r["mask_pixel_count"] = int(local_mask.sum())
        threshold = r["legacy_threshold_px_advisory"]
        if threshold != "":
            r["legacy_threshold_status_advisory"] = "LEGACY_MET" if r["h_ink_px"] >= int(threshold) else "LEGACY_BELOW"
        mask_path = OUT / r["mask_path"]
        Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8)).save(mask_path)
        roi_box = clip_px_box((x0, y0, x1, y1), width, height, pad=4)
        rx0, ry0, rx1, ry1 = roi_box
        roi1 = triple_view(Image.fromarray(rgb[ry0:ry1, rx0:rx1]), full_mask[ry0:ry1, rx0:rx1], gid)
        roi1_path = OUT / r["roi_1x_path"]
        roi8_path = OUT / r["roi_8x_path"]
        roi1.save(roi1_path)
        roi1.resize((roi1.width * 8, roi1.height * 8), Image.Resampling.NEAREST).save(roi8_path)

    make_contact_sheets(glyph_roi8_files, OUT / "glyph_contact_sheets_8x", "glyph_contact", per_sheet=12)

    glyph_fields = [
        "glyph_id", "safe_filename", "parent_object_id", "panel_id", "role", "char", "codepoint",
        "font", "pdf_font_size_pt", "source_base_pt", "script_class_machine", "bbox_x0_px", "bbox_y0_px",
        "bbox_x1_px", "bbox_y1_px", "h_ink_px", "w_ink_px", "mask_pixel_count",
        "legacy_threshold_px_advisory", "legacy_threshold_status_advisory", "mask_path", "roi_1x_path", "roi_8x_path",
    ]
    write_csv(OUT / "glyph_machine.csv", glyph_rows, glyph_fields)

    # Build one final-visible raw mask per semantic text object as the union of its glyph masks.
    object_masks = {}
    text_union = np.zeros((height, width), dtype=bool)
    for obj in text_objects:
        m = np.zeros((height, width), dtype=bool)
        for gid in parent_glyph_ids[obj["object_id"]]:
            m |= glyph_masks_full[gid]
        object_masks[obj["object_id"]] = m
        text_union |= m

    # Segment semantic graphic groups by the nearest exact PDF stroke/fill
    # colour, then allocate each final-visible pixel to the latest graphic
    # sequence. This preserves paint order and prevents broad-bbox colour
    # masks from duplicating another curve or axis.
    for obj in graphic_objects:
        obj["bbox_px"] = pt_bbox_to_crop_px(obj["bbox_pt"], pix.x, pix.y)
        object_by_id[obj["object_id"]] = obj
    palette = []
    for obj in graphic_objects:
        for color in obj["colors"]:
            color = tuple(color)
            if color not in palette:
                palette.append(color)
    claimed_graphic = np.zeros((height, width), dtype=bool)
    opaque_layers = []
    for bg in graphic_objects:
        if bg["foreground"]:
            continue
        bx0, by0, bx1, by1 = clip_px_box(bg["bbox_px"], width, height, pad=0)
        bm = np.zeros((height, width), dtype=bool)
        bm[by0:by1, bx0:bx1] = True
        opaque_layers.append((max(bg["seqnos"]), bm))
    for obj in sorted(graphic_objects, key=lambda x: max(x["seqnos"]), reverse=True):
        m = np.zeros((height, width), dtype=bool)
        if obj["foreground"]:
            x0, y0, x1, y1 = clip_px_box(obj["bbox_px"], width, height, pad=3)
            patch = rgb[y0:y1, x0:x1]
            local = np.zeros(patch.shape[:2], dtype=bool)
            for color in obj["colors"]:
                local |= segment_expected_color_nearest(patch, tuple(color), palette)
            m[y0:y1, x0:x1] = local
            m &= ~text_union
            for opaque_seq, opaque_mask in opaque_layers:
                if opaque_seq > max(obj["seqnos"]):
                    m &= ~opaque_mask
            m &= ~claimed_graphic
            claimed_graphic |= m
        object_masks[obj["object_id"]] = m

    all_objects = text_objects + graphic_objects
    inventory_rows = []
    font_rows = []
    for obj in all_objects:
        m = object_masks[obj["object_id"]]
        mask_path = OUT / "object_masks" / f"{obj['object_id']}.png"
        saved_bb = object_mask_crop(m, mask_path) if obj["foreground"] else None
        inv = {
            "object_id": obj["object_id"],
            "safe_filename": f"{obj['object_id']}.png",
            "object_type": obj["object_type"],
            "panel_id": obj["panel_id"],
            "role_machine": obj["role"],
            "semantic_name": obj["semantic_name"],
            "text": obj["text"],
            "foreground_kind": "FOREGROUND" if obj["foreground"] else "OPAQUE_BACKGROUND",
            "bbox_x0_pt": obj["bbox_pt"][0],
            "bbox_y0_pt": obj["bbox_pt"][1],
            "bbox_x1_pt": obj["bbox_pt"][2],
            "bbox_y1_pt": obj["bbox_pt"][3],
            "bbox_x0_px": obj["bbox_px"][0],
            "bbox_y0_px": obj["bbox_px"][1],
            "bbox_x1_px": obj["bbox_px"][2],
            "bbox_y1_px": obj["bbox_px"][3],
            "raw_mask_pixel_count": int(m.sum()),
            "raw_mask_saved_bbox_px": json.dumps(saved_bb),
            "raw_mask_path": str(mask_path.relative_to(OUT)).replace("\\", "/") if saved_bb is not None else "N/A_BACKGROUND",
            "primitive_seqnos": json.dumps(obj.get("seqnos", [])),
            "glyph_count": len(parent_glyph_ids.get(obj["object_id"], [])),
        }
        inventory_rows.append(inv)
        if obj["object_type"] == "TEXT":
            heights = [r["h_ink_px"] for r in glyph_rows if r["parent_object_id"] == obj["object_id"] and r["h_ink_px"] > 0]
            font_rows.append(
                {
                    "element_id": obj["object_id"],
                    "panel_id": obj["panel_id"],
                    "role_machine": obj["role"],
                    "semantic_name": obj["semantic_name"],
                    "source_file": str(SOURCE),
                    "source_line": obj["source_line"],
                    "declared_pt": obj["declared_pt"],
                    "graphics_scale": obj["graphics_scale"],
                    "effective_pt": obj["effective_pt"],
                    "pdf_visible_text": obj["text"],
                    "glyph_count": len(heights),
                    "glyph_h_median_px": float(np.median(heights)) if heights else "",
                    "glyph_h_min_px": min(heights) if heights else "",
                    "glyph_h_max_px": max(heights) if heights else "",
                }
            )

    inv_fields = [
        "object_id", "safe_filename", "object_type", "panel_id", "role_machine", "semantic_name", "text",
        "foreground_kind", "bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt", "bbox_x0_px", "bbox_y0_px",
        "bbox_x1_px", "bbox_y1_px", "raw_mask_pixel_count", "raw_mask_saved_bbox_px", "raw_mask_path",
        "primitive_seqnos", "glyph_count",
    ]
    write_csv(OUT / "object_inventory_machine.csv", inventory_rows, inv_fields)
    font_fields = [
        "element_id", "panel_id", "role_machine", "semantic_name", "source_file", "source_line", "declared_pt",
        "graphics_scale", "effective_pt", "pdf_visible_text", "glyph_count", "glyph_h_median_px", "glyph_h_min_px", "glyph_h_max_px",
    ]
    write_csv(OUT / "source_font_audit_machine.csv", font_rows, font_fields)

    # Precompute nearest-ink distance transforms for all foreground objects.
    distance_maps = {}
    for obj in all_objects:
        if obj["foreground"] and object_masks[obj["object_id"]].any():
            distance_maps[obj["object_id"]] = distance_transform_edt(~object_masks[obj["object_id"]])

    pair_rows = []
    critical_rows = []
    critical_roi8_files = []
    for pair_index, (a, b) in enumerate(itertools.combinations(all_objects, 2), 1):
        pid = f"P{pair_index:04d}"
        ma = object_masks[a["object_id"]]
        mb = object_masks[b["object_id"]]
        intersection = int(np.logical_and(ma, mb).sum()) if a["foreground"] and b["foreground"] else 0
        mask_distance = ""
        empty_clearance = ""
        if a["foreground"] and b["foreground"] and ma.any() and mb.any():
            d1 = float(distance_maps[a["object_id"]][mb].min())
            d2 = float(distance_maps[b["object_id"]][ma].min())
            mask_distance = min(d1, d2)
            empty_clearance = max(0, math.floor(mask_distance) - 1)
        bclear = bbox_clearance(a["bbox_px"], b["bbox_px"])
        relation = pair_relation(a, b)
        same_panel = a["panel_id"] == b["panel_id"]
        required_combo = (
            ("LEGEND" in {a["role"], b["role"]} and "DATA_CURVE" in {a["role"], b["role"]})
            or ("ANNOTATION" in {a["role"], b["role"]} and "DATA_CURVE" in {a["role"], b["role"]})
            or ("POINT_LABEL" in {a["role"], b["role"]} and ({a["role"], b["role"]} & {"DATA_CURVE", "MARKER"}))
            or ("FORMULA_TITLE" in {a["role"], b["role"]} and "MATH_RULE" in {a["role"], b["role"]})
        )
        near = same_panel and a["foreground"] and b["foreground"] and (
            intersection > 0
            or (empty_clearance != "" and empty_clearance <= 12)
            or (a["object_type"] == "TEXT" and b["object_type"] == "TEXT" and bclear <= 12)
        )
        critical_kind = "NEAR_PIXEL_RELATION" if near else ("REQUIRED_SEMANTIC_COMBO" if required_combo else "")
        row = {
            "pair_id": pid,
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "panel_a": a["panel_id"],
            "panel_b": b["panel_id"],
            "role_a": a["role"],
            "role_b": b["role"],
            "relation_class_machine": relation,
            "bbox_intersection_area_px2": bbox_intersection_area(a["bbox_px"], b["bbox_px"]),
            "bbox_clearance_px": bclear,
            "raw_mask_intersection_px": intersection,
            "mask_center_distance_px": mask_distance,
            "empty_pixel_clearance_px": empty_clearance,
            "same_panel": "YES" if same_panel else "NO",
            "critical_kind_machine": critical_kind,
        }
        pair_rows.append(row)
        if critical_kind:
            critical_rows.append(row.copy())
        if near:
            roi1, roi_box = crop_relation_roi(rgb, ma, mb, a, b)
            roi1_path = OUT / "critical_pair_rois_1x" / f"{pid}.png"
            roi8_path = OUT / "critical_pair_rois_8x" / f"{pid}.png"
            roi1.save(roi1_path)
            roi1.resize((roi1.width * 8, roi1.height * 8), Image.Resampling.NEAREST).save(roi8_path)
            critical_roi8_files.append(roi8_path)
            critical_rows[-1]["roi_box_px"] = json.dumps(roi_box)
            critical_rows[-1]["roi_1x_path"] = str(roi1_path.relative_to(OUT)).replace("\\", "/")
            critical_rows[-1]["roi_8x_path"] = str(roi8_path.relative_to(OUT)).replace("\\", "/")

    pair_fields = [
        "pair_id", "object_a", "object_b", "panel_a", "panel_b", "role_a", "role_b", "relation_class_machine",
        "bbox_intersection_area_px2", "bbox_clearance_px", "raw_mask_intersection_px", "mask_center_distance_px",
        "empty_pixel_clearance_px", "same_panel", "critical_kind_machine",
    ]
    write_csv(OUT / "all_unordered_pairs_machine.csv", pair_rows, pair_fields)
    critical_fields = pair_fields + ["roi_box_px", "roi_1x_path", "roi_8x_path"]
    write_csv(OUT / "critical_relations_machine.csv", critical_rows, critical_fields)
    make_contact_sheets(critical_roi8_files, OUT / "critical_pair_contact_sheets_8x", "critical_pair_contact", per_sheet=6)

    # Machine-only clip and crop-edge geometry.
    clip_rows = []
    for obj in all_objects:
        bounds_pt = PANEL_BOUNDS_PT[obj["panel_id"]]
        bounds_px = pt_bbox_to_crop_px(bounds_pt, pix.x, pix.y)
        b = obj["bbox_px"]
        edge_clearances = {
            "left": b[0] - bounds_px[0],
            "top": b[1] - bounds_px[1],
            "right": bounds_px[2] - b[2],
            "bottom": bounds_px[3] - b[3],
        }
        clip_rows.append(
            {
                "object_id": obj["object_id"],
                "panel_id": obj["panel_id"],
                "foreground_kind": "FOREGROUND" if obj["foreground"] else "OPAQUE_BACKGROUND",
                "panel_bounds_px": json.dumps(bounds_px),
                "object_bbox_px": json.dumps(b),
                "left_edge_clearance_px": edge_clearances["left"],
                "top_edge_clearance_px": edge_clearances["top"],
                "right_edge_clearance_px": edge_clearances["right"],
                "bottom_edge_clearance_px": edge_clearances["bottom"],
                "minimum_bbox_edge_clearance_px": min(edge_clearances.values()),
            }
        )
    clip_fields = [
        "object_id", "panel_id", "foreground_kind", "panel_bounds_px", "object_bbox_px",
        "left_edge_clearance_px", "top_edge_clearance_px", "right_edge_clearance_px", "bottom_edge_clearance_px",
        "minimum_bbox_edge_clearance_px",
    ]
    write_csv(OUT / "clip_geometry_machine.csv", clip_rows, clip_fields)

    # Object measurement overlay.
    overlay = Image.fromarray(rgb).convert("RGB")
    od = ImageDraw.Draw(overlay)
    colors = {"A": (0, 90, 220), "B": (220, 60, 0), "CAPTION": (120, 0, 160)}
    labelfont = font_for_labels(14)
    for obj in all_objects:
        x0, y0, x1, y1 = obj["bbox_px"]
        color = colors[obj["panel_id"]]
        od.rectangle((x0, y0, x1, y1), outline=color, width=1)
        od.text((x0, max(0, y0 - 16)), obj["object_id"], fill=color, font=labelfont)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    machine_counts = {
        "semantic_text_objects": len(text_objects),
        "semantic_graphic_objects": len(graphic_objects),
        "semantic_objects_total_N": len(all_objects),
        "unordered_pairs_expected_C_N_2": len(all_objects) * (len(all_objects) - 1) // 2,
        "unordered_pairs_actual": len(pair_rows),
        "visible_nonspace_glyphs": len(glyph_rows),
        "body_glyphs": sum(1 for r in glyph_rows if r["panel_id"] in {"A", "B"}),
        "caption_glyphs": sum(1 for r in glyph_rows if r["panel_id"] == "CAPTION"),
        "drawing_primitives": len(primitive_rows),
        "foreground_objects": sum(1 for o in all_objects if o["foreground"]),
        "opaque_background_objects": sum(1 for o in all_objects if not o["foreground"]),
        "empty_foreground_object_masks": sum(1 for o in all_objects if o["foreground"] and not object_masks[o["object_id"]].any()),
        "empty_glyph_masks": sum(1 for r in glyph_rows if r["mask_pixel_count"] == 0),
        "critical_relations_total": len(critical_rows),
        "critical_near_relations_with_roi": len(critical_roi8_files),
        "pair_raw_intersection_nonzero_rows": sum(1 for r in pair_rows if int(r["raw_mask_intersection_px"]) > 0),
        "glyph_legacy_below_advisory_rows": sum(1 for r in glyph_rows if r["legacy_threshold_status_advisory"] == "LEGACY_BELOW"),
    }
    (OUT / "machine_counts.json").write_text(json.dumps(machine_counts, ensure_ascii=False, indent=2), encoding="utf-8")

    view_rows = [
        {"view_id": "V01", "path": "full_page_200dpi.png", "purpose": "page integration", "native_width_px": 1654, "native_height_px": 2339},
        {"view_id": "V02", "path": "figure_crop_300dpi.png", "purpose": "official figure plus caption", "native_width_px": width, "native_height_px": height},
        {"view_id": "V03", "path": "standalone_300dpi.png", "purpose": "official figure body", "native_width_px": 1826, "native_height_px": 805},
        {"view_id": "V04", "path": "grayscale_300dpi.png", "purpose": "grayscale legibility", "native_width_px": width, "native_height_px": height},
        {"view_id": "V05", "path": "panel_a_300dpi.png", "purpose": "panel A detailed inspection", "native_width_px": 1146, "native_height_px": 805},
        {"view_id": "V06", "path": "panel_b_300dpi.png", "purpose": "panel B detailed inspection", "native_width_px": 660, "native_height_px": 647},
    ]
    write_csv(OUT / "views_machine.csv", view_rows, ["view_id", "path", "purpose", "native_width_px", "native_height_px"])
    doc.close()
    print(json.dumps(machine_counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
