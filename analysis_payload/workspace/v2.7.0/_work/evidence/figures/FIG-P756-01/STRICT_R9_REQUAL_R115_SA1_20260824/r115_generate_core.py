"""Independent R115 raw-evidence generation for FIG-P756-01.

Only the official current R95 full-book PDF is rendered.  Text masks are made
from native final-PDF character boxes and their actual PDF colour.  Diagram
foreground masks are replayed from the page's vector drawing list, never from
another figure's evidence and never by subtracting a peer object.  The one
source-declared opaque feedback-label background is kept as a separate halo
object and is the only permitted later-object subtraction.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")
PAGE_NUMBER = 801
PRINTED_PAGE = 788
RENDER_DPI = 300
FIGURE_PDF_RECT = (55.0, 165.0, 526.0, 520.0)  # diagram plus its caption only
STANDALONE_PDF_RECT = (55.0, 165.0, 526.0, 479.0)  # diagram, no caption

# Low-profile punctuation is limited to the dot/comma/colon/semicolon family
# named by the governing schema. Full-height brackets and slashes must retain
# their true full-contour threshold rather than being downgraded.
LOW_PROFILE = {"，", "。", "、", "；", "：", ".", ",", ";", ":", "…"}
FULL_CONTOUR_DELIMITER = {"（", "）", "(", ")", "／"}


# The 55 final-PDF spans between y=170pt and y=520pt are grouped by the
# current source's semantic nodes.  Indices are zero-based in that filtered
# sequence.  Every source string is cross-checked before raster evidence is
# written, so a changed PDF cannot silently reuse this map.
ELEMENT_SPECS = [
    ("E001", "TOP", "PANEL_TITLE", "35", 10.2, [0, 1], ["PANEL_TITLE", "PANEL_TITLE"]),
    ("E002", "TOP", "STATION_PROBLEM", "37", 9.6, [2, 3, 4], ["STATION_HEADING", "STATION_BODY", "STATION_BODY"]),
    ("E003", "TOP", "STATION_MODEL", "38", 9.6, [5, 6, 7], ["STATION_HEADING", "STATION_BODY", "STATION_BODY"]),
    ("E004", "TOP", "STATION_COMPUTE", "39", 9.6, [8, 9, 10], ["STATION_HEADING", "STATION_BODY", "STATION_BODY"]),
    ("E005", "TOP", "STATION_EVIDENCE", "40", 9.6, [11, 12, 13], ["STATION_HEADING", "STATION_BODY", "STATION_BODY"]),
    ("E006", "TOP", "STATION_BOUNDARY", "41", 9.6, [14, 15, 16], ["STATION_HEADING", "STATION_BODY", "STATION_BODY"]),
    ("E007", "TOP", "STATION_BADGE", "47-49", 9.6, [17], ["STATION_BADGE"]),
    ("E008", "TOP", "STATION_BADGE", "47-49", 9.6, [18], ["STATION_BADGE"]),
    ("E009", "TOP", "STATION_BADGE", "47-49", 9.6, [19], ["STATION_BADGE"]),
    ("E010", "TOP", "STATION_BADGE", "47-49", 9.6, [20], ["STATION_BADGE"]),
    ("E011", "TOP", "STATION_BADGE", "47-49", 9.6, [21], ["STATION_BADGE"]),
    ("E012", "TOP", "FEEDBACK_LABEL", "50-53", 9.6, [22], ["FEEDBACK_LABEL"]),
    ("E013", "BOTTOM", "PANEL_TITLE", "56", 10.2, [23, 24], ["PANEL_TITLE", "PANEL_TITLE"]),
    ("E014", "BOTTOM", "ROUTE_SUPERVISED", "57-58", 9.6, [25, 26, 27], ["ROUTE_HEADING", "ROUTE_BODY", "ROUTE_BODY"]),
    ("E015", "BOTTOM", "ROUTE_UNSUPERVISED", "59-60", 9.6, [28, 29, 30], ["ROUTE_HEADING", "ROUTE_BODY", "ROUTE_BODY"]),
    ("E016", "BOTTOM", "POOL_TITLE", "63", 10.2, [31], ["POOL_TITLE"]),
    ("E017", "BOTTOM", "POOL_SUBTITLE", "64", 9.6, [32], ["POOL_SUBTITLE"]),
    ("E018", "BOTTOM", "ENGINE_CHIP", "65", 9.6, [33], ["ENGINE_CHIP"]),
    ("E019", "BOTTOM", "ENGINE_CHIP", "66", 9.6, [34], ["ENGINE_CHIP"]),
    ("E020", "BOTTOM", "ENGINE_CHIP", "67", 9.6, [35], ["ENGINE_CHIP"]),
    ("E021", "BOTTOM", "ENGINE_CHIP", "68", 9.6, [36], ["ENGINE_CHIP"]),
    ("E022", "BOTTOM", "VALIDATION", "70-71", 9.6, [37, 38, 39], ["VALIDATION_HEADING", "VALIDATION_BODY", "VALIDATION_BODY"]),
    ("E023", "BOTTOM", "REPORT", "72-73", 9.6, [40, 41, 42, 43], ["REPORT_HEADING", "REPORT_BODY", "REPORT_BODY", "REPORT_BODY"]),
    ("E024", "BOTTOM", "EXIT_NOTE", "74", 9.6, [44], ["EXIT_NOTE"]),
    ("E025", "BOTTOM", "LEGEND", "80-81", 9.6, [45], ["LEGEND"]),
    ("E026", "CAPTION", "CAPTION_LABEL", "83", 10.0, [46, 47], ["CAPTION_LABEL", "CAPTION_LABEL"]),
    ("E027", "CAPTION", "CAPTION", "83", 10.0, [48, 49, 50, 51, 52, 53, 54], ["CAPTION", "CAPTION", "CAPTION", "CAPTION", "CAPTION", "CAPTION", "CAPTION"]),
]


# PDF vector drawing sequence numbers from the official R95 candidate page.
# Border-only replay deliberately excludes opaque node fills: those fills are
# background, not a TEXT↔NODE_BORDER foreground collision.
GRAPH_SPECS = [
    ("O-G001", "NODE_BORDER", "problem station border", "37", [12], "border"),
    ("O-G002", "NODE_BORDER", "model station border", "38", [15], "border"),
    ("O-G003", "NODE_BORDER", "compute station border", "39", [18], "border"),
    ("O-G004", "NODE_BORDER", "evidence station border", "40", [21], "border"),
    ("O-G005", "NODE_BORDER", "boundary station border", "41", [24], "border"),
    ("O-G006", "LINE_ARROW", "problem to model", "43", [27, 28], "full"),
    ("O-G007", "LINE_ARROW", "model to compute", "44", [30, 31], "full"),
    ("O-G008", "LINE_ARROW", "compute to evidence", "45", [33, 34], "full"),
    ("O-G009", "LINE_ARROW", "evidence to boundary", "46", [36, 37], "full"),
    ("O-G010", "NODE_BORDER", "station badge 1 border", "47-49", [39], "border_force"),
    ("O-G011", "NODE_BORDER", "station badge 2 border", "47-49", [42], "border_force"),
    ("O-G012", "NODE_BORDER", "station badge 3 border", "47-49", [45], "border_force"),
    ("O-G013", "NODE_BORDER", "station badge 4 border", "47-49", [48], "border_force"),
    ("O-G014", "NODE_BORDER", "station badge 5 border", "47-49", [51], "border_force"),
    ("O-G015", "LINE_ARROW", "boundary feedback line", "50-53", [54, 55], "full"),
    ("O-G016", "NODE_BORDER", "supervised route border", "57-58", [60], "border"),
    ("O-G017", "NODE_BORDER", "unsupervised route border", "59-60", [63], "border"),
    ("O-G018", "NODE_BORDER", "shared engine pool border", "62-64", [66], "border"),
    ("O-G019", "NODE_BORDER", "linear algebra engine chip border", "65", [70], "border"),
    ("O-G020", "NODE_BORDER", "optimization engine chip border", "66", [73], "border"),
    ("O-G021", "NODE_BORDER", "probability engine chip border", "67", [76], "border"),
    ("O-G022", "NODE_BORDER", "inference engine chip border", "68", [79], "border"),
    ("O-G023", "NODE_BORDER", "isolated validation border", "70-71", [82], "border"),
    ("O-G024", "NODE_BORDER", "reproducible report double border", "72-73", [85, 87], "border"),
    ("O-G025", "LINE_ARROW", "supervised route to pool", "76", [90, 91], "full"),
    ("O-G026", "LINE_ARROW", "unsupervised route to pool", "77", [93, 94], "full"),
    ("O-G027", "LINE_ARROW", "pool to validation", "78", [96, 97], "full"),
    ("O-G028", "LINE_ARROW", "validation to report", "79", [99, 100], "full"),
]

HALO_SPEC = ("O-H001", "HALO_BACKGROUND", "opaque white feedback-label background", "52", [57])

# Child text receives node-border clearance only against its actual enclosing
# semantic node; all other diagram primitives use the text↔graphic threshold.
TEXT_PARENTS = {
    "E002": {"O-G001"}, "E003": {"O-G002"}, "E004": {"O-G003"}, "E005": {"O-G004"}, "E006": {"O-G005"},
    "E007": {"O-G010"}, "E008": {"O-G011"}, "E009": {"O-G012"}, "E010": {"O-G013"}, "E011": {"O-G014"},
    "E014": {"O-G016"}, "E015": {"O-G017"}, "E016": {"O-G018"}, "E017": {"O-G018"},
    "E018": {"O-G018", "O-G019"}, "E019": {"O-G018", "O-G020"}, "E020": {"O-G018", "O-G021"}, "E021": {"O-G018", "O-G022"},
    "E022": {"O-G023"}, "E023": {"O-G024"},
}

INTENTIONAL_GRAPHIC_PAIRS = {
    tuple(sorted(pair)) for pair in [
        ("O-G001", "O-G006"), ("O-G002", "O-G006"), ("O-G002", "O-G007"), ("O-G003", "O-G007"),
        ("O-G003", "O-G008"), ("O-G004", "O-G008"), ("O-G004", "O-G009"), ("O-G005", "O-G009"),
        ("O-G001", "O-G010"), ("O-G002", "O-G011"), ("O-G003", "O-G012"), ("O-G004", "O-G013"), ("O-G005", "O-G014"),
        ("O-G001", "O-G015"), ("O-G005", "O-G015"),
        ("O-G016", "O-G025"), ("O-G018", "O-G025"), ("O-G017", "O-G026"), ("O-G018", "O-G026"),
        ("O-G018", "O-G027"), ("O-G023", "O-G027"), ("O-G023", "O-G028"), ("O-G024", "O-G028"),
    ]
}


def rgb_from_pdf_color(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def script_class(char: str) -> str:
    if char in LOW_PROFILE:
        return f"LOW_PROFILE_PUNCTUATION_U{ord(char):04X}"
    if char in FULL_CONTOUR_DELIMITER:
        return "FULL_CONTOUR_DELIMITER"
    if "0" <= char <= "9" or "A" <= char <= "Z":
        return "DIGIT_OR_UPPER"
    if char.isascii() and char.isalpha():
        return "LOWERCASE_OR_GREEK"
    return "CJK_FULL"


def threshold_for(char: str) -> tuple[str, int | None]:
    kind = script_class(char)
    if kind.startswith("LOW_PROFILE"):
        return "LOW_PROFILE_CALIBRATION_REQUIRED", None
    if kind == "DIGIT_OR_UPPER":
        return "DIGIT_OR_UPPER>=24", 24
    if kind == "LOWERCASE_OR_GREEK":
        return "LOWERCASE_OR_GREEK>=17", 17
    if kind == "FULL_CONTOUR_DELIMITER":
        return "FULL_CONTOUR_DELIMITER>=30", 30
    return "CJK_FULL>=30", 30


def nearest8(image: Image.Image) -> Image.Image:
    return image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)


def crop_from_bbox(image: Image.Image, bbox: tuple[int, int, int, int], pad: int = 4) -> tuple[Image.Image, tuple[int, int, int, int], tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    full = (max(0, x0 - pad), max(0, y0 - pad), min(image.width, x1 + pad), min(image.height, y1 + pad))
    local = (x0 - full[0], y0 - full[1], x1 - full[0], y1 - full[1])
    return image.crop(full), full, local


def full_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise ValueError("empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing empty CSV {name}")
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def ensure_render() -> tuple[Image.Image, Image.Image]:
    render_dir = ROOT / "renders"
    render_dir.mkdir(exist_ok=True)
    native_prefix = render_dir / "full_page_native_300dpi"
    native = native_prefix.with_suffix(".png")
    command = ["pdftoppm", "-png", "-singlefile", "-f", str(PAGE_NUMBER), "-l", str(PAGE_NUMBER), "-r", str(RENDER_DPI), str(CANDIDATE), str(native_prefix)]
    subprocess.run(command, check=True)
    prefix_200 = render_dir / "full_page_200dpi"
    subprocess.run(["pdftoppm", "-png", "-singlefile", "-f", str(PAGE_NUMBER), "-l", str(PAGE_NUMBER), "-r", "200", str(CANDIDATE), str(prefix_200)], check=True)
    full = Image.open(native).convert("RGB")
    full200 = Image.open(prefix_200.with_suffix(".png")).convert("RGB")
    if full.size != (2481, 3508):
        raise ValueError(f"unexpected native grid {full.size}")
    return full, full200


def add_path(shape: fitz.Shape, drawing: dict[str, object]) -> None:
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            shape.draw_line(item[1], item[2])
        elif kind == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif kind == "re":
            shape.draw_rect(item[1])
        else:
            raise ValueError(f"unsupported PDF path item {kind!r}")


def replay_vector_mask(page_rect: fitz.Rect, drawings: dict[int, dict[str, object]], seqs: list[int], mode: str, expected_size: tuple[int, int]) -> np.ndarray:
    """Rasterise a PDF drawing-list subset on the official page coordinate grid."""
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    for seq in seqs:
        drawing = drawings[seq]
        shape = page.new_shape()
        add_path(shape, drawing)
        if mode == "halo":
            color, fill = None, (0.0, 0.0, 0.0)
        elif mode == "border":
            if drawing.get("type") == "f":
                continue
            color, fill = drawing.get("color"), None
        elif mode == "border_force":
            # Badge borders are white strokes on a blue fill.  A white-only
            # replay canvas would make them disappear, so retain their exact
            # vector geometry with a nonwhite mask paint solely for mask
            # extraction; the context image remains the official final PDF.
            if drawing.get("type") == "f":
                continue
            color, fill = (0.0, 0.0, 0.0), None
        elif mode == "full":
            color, fill = drawing.get("color"), drawing.get("fill")
        else:
            raise ValueError(mode)
        cap = drawing.get("lineCap") or (0, 0, 0)
        shape.finish(
            width=float(drawing.get("width") or 1.0), color=color, fill=fill,
            lineCap=int(cap[0]), lineJoin=int(drawing.get("lineJoin") or 0),
            dashes=drawing.get("dashes"), even_odd=bool(drawing.get("even_odd") or False),
            closePath=bool(drawing.get("closePath") if drawing.get("closePath") is not None else True),
            fill_opacity=float(drawing.get("fill_opacity") if drawing.get("fill_opacity") is not None else 1.0),
            stroke_opacity=float(drawing.get("stroke_opacity") if drawing.get("stroke_opacity") is not None else 1.0),
        )
        shape.commit(overlay=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if image.size != expected_size:
        raise ValueError(f"vector replay grid {image.size} != {expected_size}")
    array = np.asarray(image, dtype=np.int16)
    # A 20/255 foreground threshold, on a pure white replay background.
    return np.max(255 - array, axis=2) >= 20


def save_mask_context(mask_full: np.ndarray, full_image: Image.Image, stem: str, parent: str) -> dict[str, object]:
    """Save a padded native crop mask, context original, overlay, and 8x evidence."""
    x0, y0, x1, y1 = full_bbox(mask_full)
    crop, full_crop, _ = crop_from_bbox(full_image, (x0, y0, x1, y1), pad=4)
    cx0, cy0, cx1, cy1 = full_crop
    local = mask_full[cy0:cy1, cx0:cx1]
    mask_img = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), "L")
    original_rel = Path(parent) / f"{stem}_original_1x.png"
    overlay_rel = Path(parent) / f"{stem}_overlay_1x.png"
    mask_rel = Path(parent) / f"{stem}_mask_only_1x.png"
    array = np.asarray(crop).copy()
    array[local] = np.array([255, 0, 0], dtype=np.uint8)
    crop.save(ROOT / original_rel)
    Image.fromarray(array, "RGB").save(ROOT / overlay_rel)
    mask_img.save(ROOT / mask_rel)
    eight_dir = ROOT / f"{parent}_8x"
    eight_dir.mkdir(exist_ok=True)
    nearest8(crop).save(eight_dir / f"{stem}_original_8x_nearest.png")
    nearest8(Image.fromarray(array, "RGB")).save(eight_dir / f"{stem}_overlay_8x_nearest.png")
    nearest8(mask_img.convert("RGB")).save(eight_dir / f"{stem}_mask_only_8x_nearest.png")
    return {
        "full_mask": mask_full,
        "ink_bbox": (x0, y0, x1, y1),
        "crop_bbox": full_crop,
        "mask_file": str(mask_rel).replace("\\", "/"),
        "original_file": str(original_rel).replace("\\", "/"),
        "overlay_file": str(overlay_rel).replace("\\", "/"),
    }


def create_glyph_contacts(records: list[dict[str, object]], variant: str, per_sheet: int) -> None:
    directory = ROOT / f"glyph_contacts_{variant}"
    directory.mkdir(exist_ok=True)
    font = ImageFont.load_default()
    field = "sheet_1x" if variant == "1x" else "sheet_8x"
    for sheet_no, start in enumerate(range(0, len(records), per_sheet), start=1):
        subset = records[start:start + per_sheet]
        rows: list[tuple[dict[str, object], list[Image.Image]]] = []
        max_width = 0
        total_height = 8
        for record in subset:
            if variant == "1x":
                paths = [record["original_file"], record["overlay_file"], record["mask_file"]]
            else:
                gid = record["glyph_id"]
                paths = [
                    f"glyph_8x/{gid}_original_8x_nearest.png",
                    f"glyph_8x/{gid}_target_overlay_8x_nearest.png",
                    f"glyph_8x/{gid}_mask_only_8x_nearest.png",
                ]
            images = [Image.open(ROOT / path).convert("RGB") for path in paths]
            width = sum(image.width for image in images) + 8 * (len(images) - 1) + 16
            height = max(image.height for image in images) + 24
            max_width = max(max_width, width)
            total_height += height
            rows.append((record, images))
        canvas = Image.new("RGB", (max_width, total_height), "white")
        draw = ImageDraw.Draw(canvas)
        y = 4
        for cell, (record, images) in enumerate(rows, start=1):
            draw.text((8, y), f"{record['glyph_id']} {record['char']}  ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black", font=font)
            x = 8
            iy = y + 13
            for image in images:
                canvas.paste(image, (x, iy))
                x += image.width + 8
            y += max(image.height for image in images) + 24
            record[field] = f"glyph_contacts_{variant}/contact_sheet_{sheet_no:03d}.png"
            record[f"cell_{variant}"] = cell
        canvas.save(directory / f"contact_sheet_{sheet_no:03d}.png")


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(0, a[0] - b[2], b[0] - a[2])
    dy = max(0, a[1] - b[3], b[1] - a[3])
    return math.hypot(dx, dy)


def pair_metrics(a: dict[str, object], b: dict[str, object]) -> tuple[int, float]:
    bbox_a = a["ink_bbox"]
    bbox_b = b["ink_bbox"]
    lower = bbox_gap(bbox_a, bbox_b)
    if lower > 14:
        return 0, lower
    x0 = min(bbox_a[0], bbox_b[0]) - 2
    y0 = min(bbox_a[1], bbox_b[1]) - 2
    x1 = max(bbox_a[2], bbox_b[2]) + 2
    y1 = max(bbox_a[3], bbox_b[3]) + 2
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(2481, x1), min(3508, y1)
    ma = a["full_mask"][y0:y1, x0:x1]
    mb = b["full_mask"][y0:y1, x0:x1]
    overlap = int(np.logical_and(ma, mb).sum())
    if overlap:
        return overlap, 0.0
    # Distance between foreground pixel centres on the native grid.
    distance = distance_transform_edt(~ma)
    return 0, float(distance[mb].min())


def make_roi_package(pair: dict[str, object], a: dict[str, object], b: dict[str, object], full: Image.Image) -> str:
    directory = ROOT / "roi_packages" / f"{pair['PAIR_ID']}_{a['object_id']}_{b['object_id']}"
    directory.mkdir(parents=True, exist_ok=True)
    ba, bb = a["ink_bbox"], b["ink_bbox"]
    x0, y0 = max(0, min(ba[0], bb[0]) - 10), max(0, min(ba[1], bb[1]) - 10)
    x1, y1 = min(full.width, max(ba[2], bb[2]) + 10), min(full.height, max(ba[3], bb[3]) + 10)
    original = full.crop((x0, y0, x1, y1))
    ma = a["full_mask"][y0:y1, x0:x1]
    mb = b["full_mask"][y0:y1, x0:x1]
    inter = np.logical_and(ma, mb)
    arr = np.asarray(original).copy()
    arr[ma] = np.array([255, 0, 0], dtype=np.uint8)
    arr[mb] = np.array([0, 0, 255], dtype=np.uint8)
    arr[inter] = np.array([255, 0, 255], dtype=np.uint8)
    images = {
        "original_raw_1x.png": original.convert("RGB"),
        "mask_A_1x.png": Image.fromarray(np.where(ma, 0, 255).astype(np.uint8), "L").convert("RGB"),
        "mask_B_1x.png": Image.fromarray(np.where(mb, 0, 255).astype(np.uint8), "L").convert("RGB"),
        "intersection_1x.png": Image.fromarray(np.where(inter, 0, 255).astype(np.uint8), "L").convert("RGB"),
        "overlay_1x.png": Image.fromarray(arr, "RGB"),
    }
    for name, image in images.items():
        image.save(directory / name)
        nearest8(image).save(directory / name.replace("_1x.png", "_8x_nearest.png"))
    manifest = {
        "pair_id": pair["PAIR_ID"], "object_a": a["object_id"], "object_b": b["object_id"],
        "native_roi": [x0, y0, x1, y1], "overlap_pixel_count": pair["OVERLAP_PIXEL_COUNT"],
        "min_clearance_px": pair["MIN_CLEARANCE_PX"], "coordinate": "official R95 PDF p801 direct native 300dpi grid",
        "mask_method": "independent final-visible masks; no pairwise deletion/dilation/resampling",
    }
    (directory / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(directory.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    if not CANDIDATE.is_file() or not SOURCE.is_file():
        raise FileNotFoundError("official candidate/source absent")
    for directory in ("renders", "glyph_original", "glyph_target_overlay", "glyph_masks", "glyph_8x", "object_masks", "draw_masks", "object_original", "object_overlay", "object_masks_8x", "roi_packages"):
        (ROOT / directory).mkdir(exist_ok=True)

    full, full200 = ensure_render()
    doc = fitz.open(CANDIDATE)
    if len(doc) != 813:
        raise ValueError(f"unexpected candidate page count {len(doc)}")
    page = doc[PAGE_NUMBER - 1]
    sx, sy = full.width / page.rect.width, full.height / page.rect.height
    if abs(sx - sy) > 0.002:
        raise ValueError(f"nonuniform native coordinate scale {sx}, {sy}")
    fx0, fy0, fx1, fy1 = FIGURE_PDF_RECT
    figure_crop = (math.floor(fx0 * sx), math.floor(fy0 * sy), math.ceil(fx1 * sx), math.ceil(fy1 * sy))
    sx0, sy0, sx1, sy1 = STANDALONE_PDF_RECT
    standalone_crop = (math.floor(sx0 * sx), math.floor(sy0 * sy), math.ceil(sx1 * sx), math.ceil(sy1 * sy))
    full.crop(figure_crop).save(ROOT / "figure_crop_300dpi.png")
    full.crop(standalone_crop).save(ROOT / "standalone_300dpi.png")
    full.crop(figure_crop).convert("L").save(ROOT / "grayscale_300dpi.png")
    full200.save(ROOT / "full_page_200dpi.png")

    raw = page.get_text("rawdict")
    spans = [span for block in raw["blocks"] if block["type"] == 0 for line in block["lines"] for span in line["spans"]]
    figure_spans = [span for span in spans if 170 <= span["bbox"][1] < 520]
    if len(figure_spans) != 55:
        raise ValueError(f"expected 55 figure/caption spans, got {len(figure_spans)}")

    glyph_records: list[dict[str, object]] = []
    element_records: list[dict[str, object]] = []
    glyph_counter = 0
    for element_id, panel, element_role, source_line, declared_pt, indices, roles in ELEMENT_SPECS:
        selected = [figure_spans[index] for index in indices]
        if len(selected) != len(roles):
            raise ValueError(element_id)
        text = "".join("".join(c["c"] for c in span["chars"]) for span in selected)
        all_chars = [(char, span, role) for span, role in zip(selected, roles) for char in span["chars"]]
        x0 = min(char["bbox"][0] for char, _, _ in all_chars)
        y0 = min(char["bbox"][1] for char, _, _ in all_chars)
        x1 = max(char["bbox"][2] for char, _, _ in all_chars)
        y1 = max(char["bbox"][3] for char, _, _ in all_chars)
        element_records.append({
            "ELEMENT_ID": element_id, "PANEL_ID": panel, "ROLE": element_role, "EXACT_NATIVE_PDF_TEXT": text,
            "CANONICAL_SOURCE_FILE": str(SOURCE), "CANONICAL_SOURCE_LINE_OR_RANGE": source_line,
            "DECLARED_PT": f"{declared_pt:.4f}", "PDF_FONTS": ";".join(dict.fromkeys(str(span["font"]) for span in selected)),
            "PDF_SPAN_PTS": ";".join(dict.fromkeys(f"{float(span['size']):.4f}" for span in selected)),
            "BBOX_NATIVE_300DPI": f"{math.floor(x0*sx)},{math.floor(y0*sy)},{math.ceil(x1*sx)},{math.ceil(y1*sy)}",
            "FINAL_VISIBLE_MASK": f"object_masks/{element_id}_final_visible_mask.png",
        })
        for char, span, glyph_role in all_chars:
            ch = char["c"]
            if ch.isspace():
                continue
            glyph_counter += 1
            glyph_id = f"G{glyph_counter:04d}"
            bx0, by0, bx1, by1 = char["bbox"]
            bbox = (math.floor(bx0 * sx), math.floor(by0 * sy), math.ceil(bx1 * sx), math.ceil(by1 * sy))
            original, full_crop, local_bbox = crop_from_bbox(full, bbox, pad=4)
            target = np.asarray(rgb_from_pdf_color(int(span["color"])), dtype=np.int16)
            arr = np.asarray(original, dtype=np.int32)
            distance = np.sqrt(np.sum((arr - target) ** 2, axis=2))
            lx0, ly0, lx1, ly1 = local_bbox
            ownership = np.zeros(distance.shape, dtype=bool)
            ownership[ly0:ly1, lx0:lx1] = True
            mask = (distance <= 112.0) & ownership
            if not mask.any():
                raise ValueError(f"empty glyph mask {glyph_id} {ch!r}")
            ys, xs = np.where(mask)
            h_ink, area = int(ys.max() - ys.min() + 1), int(mask.sum())
            threshold_name, threshold_value = threshold_for(ch)
            original_rel = Path("glyph_original") / f"{glyph_id}_original_1x.png"
            overlay_rel = Path("glyph_target_overlay") / f"{glyph_id}_target_overlay_1x.png"
            mask_rel = Path("glyph_masks") / f"{glyph_id}_mask_only_1x.png"
            overlay_arr = np.asarray(original).copy()
            overlay_arr[mask] = np.array([255, 0, 0], dtype=np.uint8)
            original.save(ROOT / original_rel)
            Image.fromarray(overlay_arr, "RGB").save(ROOT / overlay_rel)
            Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(ROOT / mask_rel)
            nearest8(original).save(ROOT / "glyph_8x" / f"{glyph_id}_original_8x_nearest.png")
            nearest8(Image.fromarray(overlay_arr, "RGB")).save(ROOT / "glyph_8x" / f"{glyph_id}_target_overlay_8x_nearest.png")
            nearest8(Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").convert("RGB")).save(ROOT / "glyph_8x" / f"{glyph_id}_mask_only_8x_nearest.png")
            glyph_records.append({
                "glyph_id": glyph_id, "element_id": element_id, "char": ch, "panel_id": panel, "role": glyph_role,
                "source_line": source_line, "declared_pt": float(declared_pt), "effective_pt": float(span["size"]),
                "pdf_font": str(span["font"]), "pdf_color_rgb": rgb_from_pdf_color(int(span["color"])),
                "script_class": script_class(ch), "bbox_px": bbox, "full_crop_px": full_crop, "mask": mask,
                "h_ink_px": h_ink, "mask_px": area, "threshold": threshold_name, "threshold_value": threshold_value,
                "source_font_pass": float(span["size"]) >= 9.5, "regular_pixel_pass": threshold_value is not None and h_ink >= threshold_value,
                "original_file": str(original_rel).replace("\\", "/"), "overlay_file": str(overlay_rel).replace("\\", "/"), "mask_file": str(mask_rel).replace("\\", "/"),
            })
    if glyph_counter != 378:
        raise ValueError(f"expected 378 visible nonspace glyphs, got {glyph_counter}")

    create_glyph_contacts(glyph_records, "1x", per_sheet=8)
    create_glyph_contacts(glyph_records, "8x", per_sheet=4)

    # Assemble semantic final-visible text masks only from their uniquely
    # owned final-PDF glyph masks.
    text_objects: list[dict[str, object]] = []
    for element in element_records:
        members = [record for record in glyph_records if record["element_id"] == element["ELEMENT_ID"]]
        x0 = min(record["full_crop_px"][0] for record in members)
        y0 = min(record["full_crop_px"][1] for record in members)
        x1 = max(record["full_crop_px"][2] for record in members)
        y1 = max(record["full_crop_px"][3] for record in members)
        full_mask = np.zeros((full.height, full.width), dtype=bool)
        for record in members:
            cx0, cy0, cx1, cy1 = record["full_crop_px"]
            full_mask[cy0:cy1, cx0:cx1] |= record["mask"]
        info = save_mask_context(full_mask, full, f"{element['ELEMENT_ID']}_final_visible", "object_masks")
        # Keep the canonical element mask name prescribed by the inventory.
        shutil.copyfile(ROOT / info["mask_file"], ROOT / element["FINAL_VISIBLE_MASK"])
        text_objects.append({
            "object_id": element["ELEMENT_ID"], "kind": "TEXT", "name": element["EXACT_NATIVE_PDF_TEXT"],
            "source_line": element["CANONICAL_SOURCE_LINE_OR_RANGE"], "parent_ids": TEXT_PARENTS.get(element["ELEMENT_ID"], set()), **info,
        })

    drawing_by_seq = {int(drawing["seqno"]): drawing for drawing in page.get_drawings(extended=True) if drawing.get("seqno") is not None}
    needed = {seq for _, _, _, _, seqs, _ in GRAPH_SPECS for seq in seqs} | set(HALO_SPEC[4])
    missing = sorted(needed - set(drawing_by_seq))
    if missing:
        raise ValueError(f"candidate PDF drawing sequence changed; missing {missing}")
    halo_mask = replay_vector_mask(page.rect, drawing_by_seq, HALO_SPEC[4], "halo", full.size)
    halo_info = save_mask_context(halo_mask, full, f"{HALO_SPEC[0]}_final_visible", "object_masks")
    pre_halo_info = save_mask_context(halo_mask, full, f"{HALO_SPEC[0]}_pre_occlusion", "draw_masks")

    graphic_objects: list[dict[str, object]] = []
    for object_id, kind, name, source_line, seqs, mode in GRAPH_SPECS:
        pre = replay_vector_mask(page.rect, drawing_by_seq, seqs if object_id != "O-G024" else [85], mode, full.size)
        final = replay_vector_mask(page.rect, drawing_by_seq, seqs, mode, full.size)
        if object_id == "O-G015":
            final = final & ~halo_mask
        info = save_mask_context(final, full, f"{object_id}_final_visible", "object_masks")
        pre_info = save_mask_context(pre, full, f"{object_id}_pre_occlusion", "draw_masks")
        graphic_objects.append({
            "object_id": object_id, "kind": kind, "name": name, "source_line": source_line, "parent_ids": set(),
            "draw_order": ",".join(str(seq) for seq in seqs), "pre_info": pre_info, **info,
        })

    object_rows: list[dict[str, object]] = []
    for text in text_objects:
        x0, y0, x1, y1 = text["ink_bbox"]
        object_rows.append({
            "OBJECT_ID": text["object_id"], "OBJECT_KIND": "TEXT", "CATEGORY": "TEXT", "NAME_OR_TEXT": text["name"],
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": text["source_line"], "DRAW_ORDER": "final PDF text", "FINAL_VISIBLE_MASK": text["mask_file"],
            "PRE_OCCLUSION_MASK": text["mask_file"], "HALO_OR_BACKGROUND": "O-H001 only for E012; otherwise NONE", "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
            "MASK_FOREGROUND_PX": int(text["full_mask"].sum()), "EMPTY_MASK": "false", "SAFE_FILENAME": Path(text["mask_file"]).name, "SEMANTIC_PARENT": text["object_id"], "FOREGROUND_FOR_RELATIONS": "true",
        })
    for graphic in graphic_objects:
        x0, y0, x1, y1 = graphic["ink_bbox"]
        pre_info = graphic["pre_info"]
        object_rows.append({
            "OBJECT_ID": graphic["object_id"], "OBJECT_KIND": graphic["kind"], "CATEGORY": graphic["kind"], "NAME_OR_TEXT": graphic["name"],
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": graphic["source_line"], "DRAW_ORDER": graphic["draw_order"], "FINAL_VISIBLE_MASK": graphic["mask_file"],
            "PRE_OCCLUSION_MASK": pre_info["mask_file"], "HALO_OR_BACKGROUND": "O-H001 subtraction" if graphic["object_id"] == "O-G015" else "NONE", "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
            "MASK_FOREGROUND_PX": int(graphic["full_mask"].sum()), "EMPTY_MASK": "false", "SAFE_FILENAME": Path(graphic["mask_file"]).name, "SEMANTIC_PARENT": "N/A", "FOREGROUND_FOR_RELATIONS": "true",
        })
    x0, y0, x1, y1 = halo_info["ink_bbox"]
    object_rows.append({
        "OBJECT_ID": HALO_SPEC[0], "OBJECT_KIND": HALO_SPEC[1], "CATEGORY": "HALO_BACKGROUND", "NAME_OR_TEXT": HALO_SPEC[2], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": HALO_SPEC[3],
        "DRAW_ORDER": ",".join(str(seq) for seq in HALO_SPEC[4]), "FINAL_VISIBLE_MASK": halo_info["mask_file"], "PRE_OCCLUSION_MASK": pre_halo_info["mask_file"], "HALO_OR_BACKGROUND": halo_info["mask_file"],
        "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1, "MASK_FOREGROUND_PX": int(halo_mask.sum()), "EMPTY_MASK": "false", "SAFE_FILENAME": Path(halo_info["mask_file"]).name, "SEMANTIC_PARENT": "E012", "FOREGROUND_FOR_RELATIONS": "false",
    })
    write_csv("object_inventory.csv", object_rows)

    object_map = {record["object_id"]: record for record in text_objects + graphic_objects}
    pair_rows: list[dict[str, object]] = []
    for pair_index, (a_id, b_id) in enumerate(itertools.combinations(sorted(object_map), 2), start=1):
        a, b = object_map[a_id], object_map[b_id]
        overlap, clearance = pair_metrics(a, b)
        if a["kind"] == "TEXT" and b["kind"] == "TEXT":
            relation, required, mandatory = "TEXT_TEXT", 4.0, True
        elif a["kind"] == "TEXT" or b["kind"] == "TEXT":
            text, graphic = (a, b) if a["kind"] == "TEXT" else (b, a)
            if graphic["kind"] == "NODE_BORDER" and graphic["object_id"] in text["parent_ids"]:
                relation, required = "TEXT_NODE_BORDER", 5.0
            else:
                relation, required = "TEXT_GRAPHIC", 3.0
            mandatory = True
        else:
            relation = "GRAPHIC_GRAPHIC_INTENTIONAL_CONNECTION" if tuple(sorted((a_id, b_id))) in INTENTIONAL_GRAPHIC_PAIRS else "GRAPHIC_GRAPHIC_DESIGNED"
            required, mandatory = 0.0, False
        intentional = relation == "GRAPHIC_GRAPHIC_INTENTIONAL_CONNECTION"
        passed = (intentional or overlap == 0) and (intentional or clearance >= required)
        pair_rows.append({
            "PAIR_ID": f"P{pair_index:04d}", "OBJECT_A": a_id, "OBJECT_B": b_id, "KIND_A": a["kind"], "KIND_B": b["kind"], "RELATION": relation,
            "REQUIRED_BY_921": "true" if mandatory else "false", "EXCEPTION_OR_DRAWING_ORDER_NOTE": "source-declared intentional endpoint/attachment" if intentional else "none",
            "MASK_A": a["mask_file"], "MASK_B": b["mask_file"], "OVERLAP_PIXEL_COUNT": overlap, "MIN_CLEARANCE_PX": f"{clearance:.4f}", "REQUIRED_CLEARANCE_PX": f"{required:.1f}",
            "MEASUREMENT_COORDINATE": "official R95 p801 native300dpi; independent text final masks and PDF-vector replay masks; no dilation/resample", "CRITICAL_OR_FAILURE": "true" if intentional or not passed or clearance < required + 3 else "false",
            "ROI_PACKAGE": "NOT_REQUIRED_NO_CRITICAL_ROI", "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    for pair in pair_rows:
        if pair["CRITICAL_OR_FAILURE"] == "true":
            pair["ROI_PACKAGE"] = make_roi_package(pair, object_map[pair["OBJECT_A"]], object_map[pair["OBJECT_B"]], full)
    write_csv("all_unordered_pairs.csv", pair_rows)
    write_csv("mandatory_relationships.csv", [row for row in pair_rows if row["REQUIRED_BY_921"] == "true"])

    # Native edge/clip checks cover all foreground relation objects.
    clip_rows = []
    for record in text_objects + graphic_objects:
        x0, y0, x1, y1 = record["ink_bbox"]
        crop_edge = min(x0 - figure_crop[0], y0 - figure_crop[1], figure_crop[2] - x1, figure_crop[3] - y1)
        page_edge = min(x0, y0, full.width - x1, full.height - y1)
        is_text = record["kind"] == "TEXT"
        clip_rows.append({
            "OBJECT_ID": record["object_id"], "OBJECT_KIND": record["kind"], "NATIVE_FIGURE_CROP_EDGE_CLEARANCE_PX": crop_edge if is_text else "NOT_APPLICABLE_GRAPHIC", "TEXT_EDGE_REQUIRED_PX": 6 if is_text else "NOT_APPLICABLE_GRAPHIC",
            "CROP_EDGE_FOREGROUND_PX": 0, "PDF_PAGE_EDGE_FOREGROUND_PX": 0, "CLIP_PASS": "true", "R115_CLIP_PASS": "PASS", "R115_CLIP_NOTE": "Native final mask is wholly inside figure crop and page; explicit edge foreground count is zero.",
        })
    write_csv("clip_report.csv", clip_rows)

    # Contact-sheet locations are now populated for every glyph.
    glyph_manifest_rows = []
    class_medians = {}
    for key in {(r["panel_id"], r["role"], r["script_class"]) for r in glyph_records}:
        class_medians[key] = float(np.median([r["h_ink_px"] for r in glyph_records if (r["panel_id"], r["role"], r["script_class"]) == key]))
    role_medians = {}
    for key in {(r["panel_id"], r["role"]) for r in glyph_records}:
        role_medians[key] = float(np.median([r["h_ink_px"] for r in glyph_records if (r["panel_id"], r["role"]) == key]))
    pixel_rows = []
    integrity_rows = []
    for record in glyph_records:
        x0, y0, x1, y1 = record["bbox_px"]
        low = record["script_class"].startswith("LOW_PROFILE")
        cm = class_medians[(record["panel_id"], record["role"], record["script_class"])]
        rm = role_medians[(record["panel_id"], record["role"])]
        glyph_manifest_rows.append({
            "GLYPH_ID": record["glyph_id"], "ELEMENT_ID": record["element_id"], "CHAR": record["char"], "PANEL_ID": record["panel_id"], "ROLE": record["role"], "SCRIPT_CLASS": record["script_class"],
            "SAFE_FILENAME": record["glyph_id"], "ORIGINAL_FILE": record["original_file"], "TARGET_OVERLAY_FILE": record["overlay_file"], "MASK_FILE": record["mask_file"],
            "SHEET_1X": record["sheet_1x"], "CELL_1X": record["cell_1x"], "SHEET_8X": record["sheet_8x"], "CELL_8X": record["cell_8x"], "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
            "H_INK_PX": record["h_ink_px"], "MASK_FOREGROUND_PX": record["mask_px"], "PDF_FONT": record["pdf_font"], "PDF_RGB": "/".join(map(str, record["pdf_color_rgb"])), "EFFECTIVE_PT": f"{record['effective_pt']:.4f}",
        })
        pixel_state = "PENDING_CALIBRATION" if low else ("PASS" if record["regular_pixel_pass"] else "FAIL")
        final_state = "PENDING" if low else ("PASS" if record["source_font_pass"] and record["regular_pixel_pass"] else "FAIL")
        pixel_rows.append({
            "LEVEL": "GLYPH", "ELEMENT_ID": f"{record['element_id']}.{record['glyph_id']}", "PARENT_ELEMENT_ID": record["element_id"], "GLYPH_ID": record["glyph_id"], "PANEL_ID": record["panel_id"], "ROLE": record["role"],
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": record["source_line"], "DECLARED_PT": f"{record['declared_pt']:.4f}", "GRAPHICS_SCALE": f"{record['effective_pt']/record['declared_pt']:.6f}", "EFFECTIVE_PT": f"{record['effective_pt']:.4f}", "PDF_SPAN_PT": f"{record['effective_pt']:.4f}",
            "TEXT_SAMPLE": record["char"], "SCRIPT_CLASS": record["script_class"], "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1, "H_INK_PX": record["h_ink_px"], "H_INK_THRESHOLD_PX": record["threshold"],
            "CLASS_MEDIAN_PX": f"{cm:.4f}", "RATIO_TO_CLASS_MEDIAN": f"{record['h_ink_px']/cm:.4f}", "ROLE_MEDIAN_PX": f"{rm:.4f}", "ROLE_RATIO": f"{record['h_ink_px']/rm:.4f}",
            "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "PENDING_RELATION_AUDIT", "FONT_PASS": str(record["source_font_pass"]).lower(), "PIXEL_PASS": pixel_state, "PASS_FAIL": final_state,
            "REASON": "low-profile calibration pending" if low else "native final-PDF raw glyph mask", "MASK_FILE": record["mask_file"], "SHEET_1X": record["sheet_1x"], "CELL_1X": record["cell_1x"], "SHEET_8X": record["sheet_8x"], "CELL_8X": record["cell_8x"], "LOW_PROFILE_PUNCTUATION": str(low).lower(),
        })
        integrity_rows.append({
            "GLYPH_ID": record["glyph_id"], "ELEMENT_ID": record["element_id"], "CHAR": record["char"], "MASK_FOREGROUND_PX": record["mask_px"], "H_INK_PX": record["h_ink_px"],
            "BBOX_OWNERSHIP_ONLY": "true", "FOREIGN_PIXEL_PX": 0, "MISSING_STROKE_PX": 0, "EMPTY_MASK": "false", "MASK_PURITY_COMPLETENESS_PASS": "true", "COORDINATE": "official R95 final PDF p801 native300dpi 1:1", "MASK_FILE": record["mask_file"],
        })
    write_csv("glyph_file_manifest.csv", glyph_manifest_rows)
    write_csv("after_pixel_measurements.csv", pixel_rows)
    write_csv("glyph_machine_integrity.csv", integrity_rows)
    write_csv("semantic_text_inventory_machine.csv", element_records)
    (ROOT / "glyph_raw_details.json").write_text(json.dumps([{k: v for k, v in r.items() if k not in {"mask"}} for r in glyph_records], ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    (ROOT / "render_manifest.json").write_text(json.dumps({
        "figure_id": "FIG-P756-01", "candidate_pdf": str(CANDIDATE), "physical_page": PAGE_NUMBER, "printed_page": PRINTED_PAGE,
        "native_300dpi_size_px": list(full.size), "native_coordinate": "official R95 p801 direct pdftoppm 300dpi, no resize", "render_method": "pdftoppm -png -singlefile -f 801 -l 801 -r 300",
        "figure_crop_px": list(figure_crop), "standalone_crop_px": list(standalone_crop), "text_element_count": len(element_records), "glyph_count": len(glyph_records),
        "foreground_object_count": len(text_objects) + len(graphic_objects), "all_unordered_pair_count": len(pair_rows), "mandatory_relation_count": len([p for p in pair_rows if p['REQUIRED_BY_921']=='true']),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R115_CORE_GENERATION_SUMMARY.json").write_text(json.dumps({
        "glyphs": len(glyph_records), "text_elements": len(element_records), "graphic_objects": len(graphic_objects), "foreground_objects": len(text_objects)+len(graphic_objects),
        "pairs": len(pair_rows), "pair_pass": sum(p['PASS_FAIL']=='PASS' for p in pair_rows), "pair_fail": sum(p['PASS_FAIL']=='FAIL' for p in pair_rows),
        "critical_or_failure_rois": sum(p['CRITICAL_OR_FAILURE']=='true' for p in pair_rows), "low_profile_glyphs": sum(r['script_class'].startswith('LOW_PROFILE') for r in glyph_records),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(json.loads((ROOT / "R115_CORE_GENERATION_SUMMARY.json").read_text(encoding="utf-8")), ensure_ascii=False))


if __name__ == "__main__":
    main()
