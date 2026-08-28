from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa1_r108_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_multinomial_counts.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C05.tex")
PAGE_INDEX = 704
FIG_RECT_PT = (78.0, 562.0, 503.0, 681.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def rect_to_px(rect, sx: float, sy: float, origin_x: int = 0, origin_y: int = 0):
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * sx)) - origin_x,
        int(math.floor(y0 * sy)) - origin_y,
        int(math.ceil(x1 * sx)) - origin_x,
        int(math.ceil(y1 * sy)) - origin_y,
    )


def clamp_box(box, width: int, height: int):
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def text_role(text: str, bbox) -> str:
    x0, y0, x1, y1 = bbox
    if y0 < 586:
        return "TITLE"
    if x1 < 211 and y0 >= 587:
        return "SEQUENCE_TOKEN"
    if 210 <= x0 <= 255 and 598 <= y0 <= 615:
        return "ARROW_LABEL"
    if 260 <= x0 <= 370 and 608 <= y0 <= 625:
        return "COUNT_VECTOR_FORMULA"
    if 260 <= x0 <= 370 and 642 <= y0 <= 660:
        return "SUPPORT_FORMULA"
    if 260 <= x0 <= 375 and y0 >= 663:
        return "WARNING_TEXT"
    if x0 >= 390 and y0 < 613:
        return "COEFFICIENT_LABEL"
    if x0 >= 418 and y0 >= 613:
        return "COEFFICIENT_FORMULA"
    return "TEXT_OTHER"


def drawing_role(index: int) -> str:
    if index < 18:
        return f"SEQUENCE_MARKER_{index + 1:02d}"
    return {
        18: "COUNT_BOX_BORDER",
        19: "ARROW_1_SHAFT",
        20: "ARROW_1_HEAD",
        21: "WARNING_BOX_BORDER",
        22: "COEFFICIENT_BOX_BORDER",
        23: "ARROW_2_SHAFT",
        24: "ARROW_2_HEAD",
    }[index]


def semantic_class(role: str) -> str:
    if role.startswith("ARROW_"):
        return "LINE_ARROW"
    if role.startswith("SEQUENCE_MARKER"):
        return "MARKER"
    if role.endswith("BOX_BORDER"):
        return "NODE_BORDER"
    if "FORMULA" in role:
        return "FORMULA"
    return "TEXT"


def pair_family(a: dict, b: dict) -> str:
    ca, cb = sorted((a["semantic_class"], b["semantic_class"]))
    return f"{ca}--{cb}"


def local_text_mask(rgb: np.ndarray, box):
    h, w, _ = rgb.shape
    x0, y0, x1, y1 = clamp_box(box, w, h)
    ex0, ey0, ex1, ey1 = clamp_box((x0 - 4, y0 - 4, x1 + 4, y1 + 4), w, h)
    patch = rgb[ey0:ey1, ex0:ex1].astype(np.int16)
    if patch.size == 0:
        return np.zeros((h, w), dtype=bool)
    border = np.concatenate(
        [patch[:2].reshape(-1, 3), patch[-2:].reshape(-1, 3), patch[:, :2].reshape(-1, 3), patch[:, -2:].reshape(-1, 3)],
        axis=0,
    )
    bg = np.median(border, axis=0)
    diff = np.max(np.abs(patch - bg), axis=2)
    pmask = diff >= 20
    result = np.zeros((h, w), dtype=bool)
    result[ey0:ey1, ex0:ex1] = pmask
    gate = np.zeros((h, w), dtype=bool)
    gate[y0:y1, x0:x1] = True
    return result & gate


def local_color_mask(rgb: np.ndarray, box, color):
    h, w, _ = rgb.shape
    x0, y0, x1, y1 = clamp_box(box, w, h)
    result = np.zeros((h, w), dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return result
    target = np.array(color, dtype=np.float32) * 255.0
    patch = rgb[y0:y1, x0:x1].astype(np.float32)
    dist = np.linalg.norm(patch - target, axis=2)
    saturation = patch.max(axis=2) - patch.min(axis=2)
    pmask = (dist <= 78.0) & ((saturation >= 8.0) | (target.max() - target.min() < 30.0))
    result[y0:y1, x0:x1] = pmask
    return result


def mask_tight_bbox(mask: np.ndarray):
    yy, xx = np.where(mask)
    if len(xx) == 0:
        return None
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def mask_intersection(a_mask, b_mask):
    return int(np.count_nonzero(a_mask & b_mask))


def mask_distance(coords_a, coords_b, fallback):
    if len(coords_a) == 0 or len(coords_b) == 0:
        return float("nan")
    if fallback > 70:
        return float(fallback)
    if len(coords_a) <= len(coords_b):
        tree = cKDTree(coords_b)
        dist, _ = tree.query(coords_a, k=1)
    else:
        tree = cKDTree(coords_a)
        dist, _ = tree.query(coords_b, k=1)
    return float(np.min(dist))


def make_overlay(base: Image.Image, objects, text_only: bool, output: Path):
    im = base.convert("RGB").copy()
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    for obj in objects:
        if text_only and obj["kind"] != "TEXT_SPAN":
            continue
        x0, y0, x1, y1 = obj["bbox_px"]
        color = (214, 39, 40) if obj["kind"] == "TEXT_SPAN" else (44, 160, 44)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        label = obj["object_id"]
        tw = draw.textbbox((0, 0), label, font=font)[2]
        ly = max(0, y0 - 11)
        draw.rectangle((x0, ly, x0 + tw + 2, ly + 10), fill=(255, 255, 255))
        draw.text((x0 + 1, ly), label, fill=color, font=font)
    im.save(output)


def make_contact_sheet(paths, labels, output):
    tiles = []
    font = ImageFont.load_default()
    for path, label in zip(paths, labels):
        im = Image.open(path).convert("RGB")
        im.thumbnail((900, 700), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (920, 740), "white")
        tile.paste(im, ((920 - im.width) // 2, 28 + (700 - im.height) // 2))
        ImageDraw.Draw(tile).text((10, 8), label, fill="black", font=font)
        tiles.append(tile)
    sheet = Image.new("RGB", (1840, 1480), (230, 230, 230))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % 2) * 920, (i // 2) * 740))
    sheet.save(output)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    pdf_doc = fitz.open(PDF)
    page = pdf_doc[PAGE_INDEX]
    identity = {
        "pdf_path": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "pdf_pages": pdf_doc.page_count,
        "physical_page": PAGE_INDEX + 1,
        "printed_page": 692,
        "figure_caption_number": "34.2",
        "source_path": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "chapter_path": str(CHAPTER),
        "chapter_sha256": sha256(CHAPTER),
        "figure_rect_pt": FIG_RECT_PT,
    }
    (ROOT / "identity_mechanical.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

    full_300_path = ROOT / "full_page_300dpi.png"
    full_300 = Image.open(full_300_path).convert("RGB")
    sx = full_300.width / page.rect.width
    sy = full_300.height / page.rect.height
    crop_box_full = rect_to_px(FIG_RECT_PT, sx, sy)
    crop = full_300.crop(crop_box_full)
    crop.save(ROOT / "figure_crop_300dpi.png")
    crop.convert("L").save(ROOT / "figure_grayscale_300dpi.png")

    pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
    fitz_full = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    fitz_full.save(ROOT / "full_page_300dpi_fitz.png")
    fitz_crop_box = rect_to_px(FIG_RECT_PT, pix.width / page.rect.width, pix.height / page.rect.height)
    fitz_crop = fitz_full.crop(fitz_crop_box)
    fitz_crop.save(ROOT / "figure_crop_300dpi_fitz.png")

    rgb = np.asarray(crop).copy()
    height, width, _ = rgb.shape
    crop_x0, crop_y0, _, _ = crop_box_full

    spans = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                x0, y0, x1, y1 = span["bbox"]
                if y0 >= 560 and y1 <= 680:
                    spans.append(span)
    spans.sort(key=lambda s: (round(s["bbox"][1], 2), s["bbox"][0]))

    drawings = [d for d in page.get_drawings() if d["rect"].y0 >= 560 and d["rect"].y1 <= 680]
    if len(spans) != 45 or len(drawings) != 25:
        raise RuntimeError(f"unexpected denominator: spans={len(spans)}, drawings={len(drawings)}")

    objects = []
    masks = {}
    for i, span in enumerate(spans, 1):
        role = text_role(span["text"], span["bbox"])
        bbox_px = rect_to_px(span["bbox"], sx, sy, crop_x0, crop_y0)
        obj = {
            "object_id": f"T{i:03d}",
            "kind": "TEXT_SPAN",
            "role": role,
            "semantic_class": semantic_class(role),
            "text": span["text"],
            "font": span["font"],
            "size_bp": float(span["size"]),
            "interpreted_tex_pt": float(span["size"]) * 72.27 / 72.0,
            "bbox_pt": tuple(float(v) for v in span["bbox"]),
            "bbox_px": bbox_px,
        }
        objects.append(obj)
        masks[obj["object_id"]] = local_text_mask(rgb, bbox_px)

    for i, drawing in enumerate(drawings):
        role = drawing_role(i)
        bbox_pt = tuple(float(v) for v in drawing["rect"])
        bbox_px = rect_to_px(bbox_pt, sx, sy, crop_x0, crop_y0)
        obj = {
            "object_id": f"G{i + 1:03d}",
            "kind": "VECTOR_DRAWING",
            "role": role,
            "semantic_class": semantic_class(role),
            "text": "",
            "font": "",
            "size_bp": "",
            "interpreted_tex_pt": "",
            "bbox_pt": bbox_pt,
            "bbox_px": bbox_px,
            "stroke_rgb_unit": drawing.get("color"),
            "fill_rgb_unit": drawing.get("fill"),
            "stroke_width_bp": float(drawing.get("width") or 0.0),
            "path_item_count": len(drawing["items"]),
        }
        objects.append(obj)
        color = drawing.get("color") or drawing.get("fill") or (0.0, 0.0, 0.0)
        masks[obj["object_id"]] = local_color_mask(rgb, bbox_px, color)

    fieldnames = [
        "object_id", "kind", "role", "semantic_class", "text", "font", "size_bp", "interpreted_tex_pt",
        "bbox_pt", "bbox_px", "stroke_rgb_unit", "fill_rgb_unit", "stroke_width_bp", "path_item_count",
        "mask_pixel_count", "mask_tight_bbox_px", "ink_height_px",
    ]
    for obj in objects:
        mask = masks[obj["object_id"]]
        tight = mask_tight_bbox(mask)
        obj["mask_pixel_count"] = int(np.count_nonzero(mask))
        obj["mask_tight_bbox_px"] = tight or ""
        obj["ink_height_px"] = (tight[3] - tight[1]) if tight else ""
        for key in fieldnames:
            obj.setdefault(key, "")
    with (ROOT / "visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(objects)

    raw = page.get_text("rawdict")
    glyph_rows = []
    gid = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    c = char["c"]
                    x0, y0, x1, y1 = char["bbox"]
                    if y0 >= 560 and y1 <= 680 and not c.isspace():
                        gid += 1
                        glyph_rows.append({
                            "glyph_id": f"Y{gid:03d}",
                            "char": c,
                            "codepoint": f"U+{ord(c):04X}",
                            "font": span["font"],
                            "size_bp": float(span["size"]),
                            "interpreted_tex_pt": float(span["size"]) * 72.27 / 72.0,
                            "bbox_pt": tuple(float(v) for v in char["bbox"]),
                            "bbox_px": rect_to_px(char["bbox"], sx, sy, crop_x0, crop_y0),
                        })
    with (ROOT / "glyph_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(glyph_rows[0]))
        writer.writeheader()
        writer.writerows(glyph_rows)

    coords = {}
    for obj in objects:
        yy, xx = np.where(masks[obj["object_id"]])
        coords[obj["object_id"]] = np.column_stack((yy, xx))

    pair_rows = []
    for pidx, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        aid, bid = a["object_id"], b["object_id"]
        a_tight = a["mask_tight_bbox_px"] or a["bbox_px"]
        b_tight = b["mask_tight_bbox_px"] or b["bbox_px"]
        bgap = bbox_gap(a_tight, b_tight)
        inter = mask_intersection(masks[aid], masks[bid])
        distance = 0.0 if inter else mask_distance(coords[aid], coords[bid], bgap)
        pair_rows.append({
            "pair_id": f"P{pidx:04d}",
            "object_a": aid,
            "object_b": bid,
            "role_a": a["role"],
            "role_b": b["role"],
            "family": pair_family(a, b),
            "bbox_gap_px": f"{bgap:.3f}",
            "mask_intersection_px": inter,
            "min_ink_distance_px": "" if math.isnan(distance) else f"{distance:.3f}",
            "evidence_basis": "independent per-object raster ink/stroke masks plus PDF-vector bboxes",
        })
    with (ROOT / "unordered_pair_ledger.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    family_summary = {}
    for row in pair_rows:
        rec = family_summary.setdefault(row["family"], {"pair_count": 0, "intersection_pair_count": 0, "intersection_pixel_sum": 0, "min_distance_px": float("inf")})
        rec["pair_count"] += 1
        if int(row["mask_intersection_px"]):
            rec["intersection_pair_count"] += 1
            rec["intersection_pixel_sum"] += int(row["mask_intersection_px"])
        if row["min_ink_distance_px"]:
            rec["min_distance_px"] = min(rec["min_distance_px"], float(row["min_ink_distance_px"]))
    with (ROOT / "pair_family_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["family", "pair_count", "intersection_pair_count", "intersection_pixel_sum", "min_distance_px"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for family in sorted(family_summary):
            rec = family_summary[family]
            writer.writerow({"family": family, **rec, "min_distance_px": "" if rec["min_distance_px"] == float("inf") else f"{rec['min_distance_px']:.3f}"})

    text_union = np.zeros((height, width), dtype=bool)
    graphic_union = np.zeros((height, width), dtype=bool)
    for obj in objects:
        if obj["kind"] == "TEXT_SPAN":
            text_union |= masks[obj["object_id"]]
        else:
            graphic_union |= masks[obj["object_id"]]
    Image.fromarray(np.where(text_union, 0, 255).astype(np.uint8)).save(ROOT / "mask_text_ink_raster.png")
    Image.fromarray(np.where(graphic_union, 0, 255).astype(np.uint8)).save(ROOT / "mask_graphic_stroke_color.png")
    overlap_union = text_union & graphic_union
    Image.fromarray(np.where(overlap_union, 0, 255).astype(np.uint8)).save(ROOT / "mask_text_graphic_candidate_intersections.png")

    make_overlay(crop, objects, False, ROOT / "overlay_all_objects_300dpi.png")
    make_overlay(crop, objects, True, ROOT / "overlay_text_measurements_300dpi.png")

    risk_rects = [
        ("risk01_arrow_label", (205.0, 593.0, 260.0, 624.0)),
        ("risk02_count_box", (252.0, 587.0, 381.0, 644.0)),
        ("risk03_support_warning", (252.0, 639.0, 381.0, 681.0)),
        ("risk04_coefficient_box", (386.0, 591.0, 501.0, 640.0)),
    ]
    risk_rows = []
    for name, rect_pt in risk_rects:
        full_box = rect_to_px(rect_pt, sx, sy)
        one = full_300.crop(full_box)
        one_path = ROOT / f"{name}_1x_native300dpi.png"
        eight_path = ROOT / f"{name}_8x_nearest.png"
        one.save(one_path)
        eight = one.resize((one.width * 8, one.height * 8), Image.Resampling.NEAREST)
        eight.save(eight_path)
        risk_rows.append({
            "roi_id": name,
            "rect_pt": rect_pt,
            "source_full_page_pixel_box": full_box,
            "one_x_dimensions": f"{one.width}x{one.height}",
            "eight_x_dimensions": f"{eight.width}x{eight.height}",
            "scale_method": "8x nearest-neighbor from untouched 300 dpi ROI; 1x is exact crop",
        })
    with (ROOT / "risk_roi_ledger.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(risk_rows[0]))
        writer.writeheader()
        writer.writerows(risk_rows)

    make_contact_sheet(
        [
            ROOT / "full_page_200dpi.png",
            ROOT / "figure_crop_300dpi.png",
            ROOT / "figure_grayscale_300dpi.png",
            ROOT / "overlay_text_measurements_300dpi.png",
        ],
        ["full page 200 dpi", "figure crop native 300 dpi", "grayscale native 300 dpi", "text measurement overlay 300 dpi"],
        ROOT / "contact_sheet_four_principal_views.png",
    )

    pop = np.asarray(crop.convert("RGB"), dtype=np.int16)
    fitz_arr = np.asarray(fitz_crop.convert("RGB"), dtype=np.int16)
    min_h = min(pop.shape[0], fitz_arr.shape[0])
    min_w = min(pop.shape[1], fitz_arr.shape[1])
    diff = np.abs(pop[:min_h, :min_w] - fitz_arr[:min_h, :min_w])
    renderer = {
        "poppler_crop_dimensions": [crop.width, crop.height],
        "fitz_crop_dimensions": [fitz_crop.width, fitz_crop.height],
        "common_dimensions": [min_w, min_h],
        "mean_absolute_channel_difference": float(diff.mean()),
        "max_absolute_channel_difference": int(diff.max()),
        "pixels_with_any_channel_difference_ge_20": int(np.count_nonzero(np.max(diff, axis=2) >= 20)),
        "common_pixel_count": int(min_w * min_h),
    }
    (ROOT / "renderer_comparison_mechanical.json").write_text(json.dumps(renderer, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "visible_object_count": len(objects),
        "text_span_object_count": len(spans),
        "vector_drawing_object_count": len(drawings),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "visible_glyph_count_excluding_whitespace": len(glyph_rows),
        "text_graphic_candidate_intersection_pixels": int(np.count_nonzero(overlap_union)),
        "figure_crop_dimensions_px": [crop.width, crop.height],
        "full_page_300dpi_dimensions_px": [full_300.width, full_300.height],
        "poppler_scale_px_per_pdf_bp": [sx, sy],
    }
    (ROOT / "mechanical_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
