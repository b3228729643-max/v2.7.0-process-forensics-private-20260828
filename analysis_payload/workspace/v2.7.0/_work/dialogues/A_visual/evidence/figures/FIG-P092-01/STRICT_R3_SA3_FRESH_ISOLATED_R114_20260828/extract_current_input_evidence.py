from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r114_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第01册_数学基础与统计学习基本理论\V1-C06\fig_v1_c06_binary_entropy.tex"
)
OUT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P092-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828"
)

EXPECTED = {
    PDF: (4_967_122, "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"),
    SOURCE: (2_094, "EA3FB7B92ED3B7B2755D513B5F3DEECF7D7114E8DC711F3AB2FE50E9C7EE8608"),
}

FIGURE_CLIP = fitz.Rect(120.0, 160.0, 482.0, 360.0)
CRITICAL_CLIPS = {
    "peak_and_symmetry": fitz.Rect(260.0, 168.0, 410.0, 258.0),
    "left_endpoint": fitz.Rect(145.0, 265.0, 225.0, 323.0),
    "right_endpoint": fitz.Rect(415.0, 265.0, 479.0, 323.0),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize_text(value: str) -> str:
    value = value.replace("𝑝", "p").replace("𝐻", "H")
    return re.sub(r"\s+", "", value)


def render(page: fitz.Page, dpi: int, clip: fitz.Rect | None = None) -> Image.Image:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def bbox_to_crop_px(bbox: tuple[float, float, float, float], dpi: int = 300) -> tuple[int, int, int, int]:
    scale = dpi / 72.0
    return tuple(round((v - (FIGURE_CLIP.x0 if i % 2 == 0 else FIGURE_CLIP.y0)) * scale) for i, v in enumerate(bbox))


def ink_height(image: Image.Image, bbox_px: tuple[int, int, int, int], orientation: int = 0) -> int:
    x0, y0, x1, y1 = bbox_px
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(image.width, x1 + 2)
    y1 = min(image.height, y1 + 2)
    arr = np.asarray(image.crop((x0, y0, x1, y1))).astype(np.int16)
    # The figure and annotation boxes use a white local background. A pixel is
    # effective ink when at least one RGB channel differs from white by >=20.
    mask = np.max(255 - arr, axis=2) >= 20
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return 0
    return int((xs.max() - xs.min() + 1) if orientation == 90 else (ys.max() - ys.min() + 1))


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    overlap_w = max(0, min(ax1, bx1) - max(ax0, bx0))
    overlap_h = max(0, min(ay1, by1) - max(ay0, by0))
    overlap_area = overlap_w * overlap_h
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return int(round(math.hypot(dx, dy))), int(overlap_area)


def main() -> None:
    OUT.mkdir(parents=False, exist_ok=True)
    identity_rows = []
    for path, (expected_size, expected_hash) in EXPECTED.items():
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if actual_size != expected_size or actual_hash != expected_hash:
            raise RuntimeError(f"identity mismatch: {path}")
        identity_rows.append(
            {
                "path": str(path),
                "bytes": actual_size,
                "sha256": actual_hash,
                "identity_match": True,
            }
        )

    source_text = SOURCE.read_text(encoding="utf-8")
    caption_match = re.search(r"\\caption\{(.+?)\}\\label", source_text)
    if not caption_match:
        raise RuntimeError("source caption not found")
    source_caption_tex = caption_match.group(1)
    expected_caption_key = normalize_text("二元熵在p=1/2处达到1比特，在确定分布两端趋于0")

    document = fitz.open(PDF)
    hits = []
    for page_index in range(len(document)):
        page_text = document[page_index].get_text("text")
        normalized = normalize_text(page_text)
        if expected_caption_key in normalized:
            hits.append(page_index)
    if hits != [95]:
        raise RuntimeError(f"caption location not unique: {hits}")

    page = document[hits[0]]
    full_200 = render(page, 200)
    full_300 = render(page, 300)
    crop_300 = render(page, 300, FIGURE_CLIP)
    crop_gray = crop_300.convert("L")
    full_200.save(OUT / "full_page_200dpi.png")
    full_300.save(OUT / "official_pdf_native_full_page_300dpi.png")
    crop_300.save(OUT / "official_pdf_figure_crop_300dpi.png")
    crop_gray.save(OUT / "official_pdf_figure_crop_grayscale_300dpi.png")

    for name, clip in CRITICAL_CLIPS.items():
        native = render(page, 72, clip)
        nearest = native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST)
        native.save(OUT / f"critical_{name}_native1x.png")
        nearest.save(OUT / f"critical_{name}_nearest8x.png")

    elements = [
        {"id": "E01", "role": "AXIS_LABEL_X", "text": "p", "source_line": 19, "declared_pt": 9.4, "pdf_size_pt": 9.963, "bbox": (316.26, 320.81, 322.22, 330.77), "orientation": 0},
        {"id": "E02", "role": "AXIS_LABEL_Y", "text": "H_2(p)", "source_line": 19, "declared_pt": 9.4, "pdf_size_pt": 9.963, "bbox": (133.82, 220.53, 145.89, 246.24), "orientation": 90},
        {"id": "E03", "role": "X_TICK", "text": "0", "source_line": 21, "declared_pt": 8.8, "pdf_size_pt": 9.265, "bbox": (171.48, 298.28, 176.86, 307.54), "orientation": 0},
        {"id": "E04", "role": "X_TICK", "text": "1/2", "source_line": 21, "declared_pt": 8.8, "pdf_size_pt": 9.265, "bbox": (316.81, 298.26, 321.67, 318.37), "orientation": 0},
        {"id": "E05", "role": "X_TICK", "text": "1", "source_line": 21, "declared_pt": 8.8, "pdf_size_pt": 9.265, "bbox": (461.95, 298.26, 466.67, 307.53), "orientation": 0},
        {"id": "E06", "role": "Y_TICK", "text": "0", "source_line": 22, "declared_pt": 8.8, "pdf_size_pt": 9.265, "bbox": (151.23, 285.14, 156.60, 294.40), "orientation": 0},
        {"id": "E07", "role": "Y_TICK", "text": "1", "source_line": 22, "declared_pt": 8.8, "pdf_size_pt": 9.265, "bbox": (151.89, 184.70, 156.60, 193.97), "orientation": 0},
        {"id": "E08", "role": "ANNOTATION_MAXIMUM", "text": "最大不确定性：1 比特", "source_line": 32, "declared_pt": 9.2, "pdf_size_pt": 9.166, "bbox": (274.58, 176.33, 363.90, 186.15), "orientation": 0},
        {"id": "E09", "role": "ANNOTATION_ENDPOINT", "text": "确定性（左）", "source_line": 34, "declared_pt": 9.2, "pdf_size_pt": 9.166, "bbox": (181.37, 276.30, 208.86, 286.12), "orientation": 0},
        {"id": "E10", "role": "ANNOTATION_ENDPOINT", "text": "确定性（右）", "source_line": 36, "declared_pt": 9.2, "pdf_size_pt": 9.166, "bbox": (429.62, 276.30, 457.11, 286.12), "orientation": 0},
        {"id": "E11", "role": "FORMULA_ANNOTATION", "text": "H_2(p)=H_2(1-p)", "source_line": 39, "declared_pt": 9.2, "pdf_size_pt": 9.166, "bbox": (323.50, 239.50, 402.02, 249.94), "orientation": 0},
        {"id": "E12", "role": "CAPTION_LABEL", "text": "图 6.1", "source_line": 42, "declared_pt": None, "pdf_size_pt": 9.963, "bbox": (163.88, 337.03, 188.79, 351.45), "orientation": 0},
        {"id": "E13", "role": "CAPTION_TEXT", "text": "二元熵在 p=1/2 处达到1比特，在确定分布两端趋于0", "source_line": 42, "declared_pt": None, "pdf_size_pt": 9.963, "bbox": (198.76, 340.61, 442.74, 351.28), "orientation": 0},
    ]

    overlay = crop_300.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for element in elements:
        bbox_px = bbox_to_crop_px(element["bbox"])
        element["bbox_px"] = bbox_px
        element["h_ink_px"] = ink_height(crop_300, bbox_px, element["orientation"])
        draw.rectangle(bbox_px, outline=(230, 25, 75), width=3)
        label_x = max(0, bbox_px[0])
        label_y = max(0, bbox_px[1] - 13)
        draw.rectangle((label_x, label_y, label_x + 25, label_y + 12), fill=(255, 255, 255))
        draw.text((label_x, label_y), element["id"], fill=(190, 0, 35), font=font)

    graphics = [
        ("G01_DATA_CURVE", (174.46, 188.67, 464.03, 288.01)),
        ("G02_GUIDE_VERTICAL", (319.24, 188.67, 319.24, 289.16)),
        ("G03_GUIDE_HORIZONTAL", (174.17, 188.67, 319.24, 188.67)),
        ("G04_AXIS_X", (162.56, 293.18, 475.92, 294.92)),
        ("G05_AXIS_Y", (160.83, 173.60, 164.69, 293.18)),
        ("G06_MARKER_LEFT", (172.03, 287.02, 176.31, 291.30)),
        ("G07_MARKER_PEAK", (317.10, 186.53, 321.38, 190.81)),
        ("G08_MARKER_RIGHT", (462.17, 287.02, 466.46, 291.30)),
    ]
    for graphic_id, graphic_bbox in graphics:
        bbox_px = bbox_to_crop_px(graphic_bbox)
        draw.rectangle(bbox_px, outline=(0, 105, 210), width=2)
        draw.text((max(0, bbox_px[0]), max(0, bbox_px[1] - 10)), graphic_id, fill=(0, 70, 160), font=font)
    overlay.save(OUT / "object_overlay_300dpi.png")

    object_fields = [
        "element_id", "panel_id", "role", "text_sample", "source_file", "source_line",
        "declared_pt", "graphics_scale", "source_local_effective_pt", "pdf_extracted_size_pt",
        "orientation_degrees", "bbox_pdf_x0", "bbox_pdf_y0", "bbox_pdf_x1", "bbox_pdf_y1",
        "bbox_px_x0", "bbox_px_y0", "bbox_px_x1", "bbox_px_y1", "h_ink_px",
    ]
    with (OUT / "object_registry_mechanical.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=object_fields)
        writer.writeheader()
        for element in elements:
            bbox = element["bbox"]
            bbox_px = element["bbox_px"]
            writer.writerow(
                {
                    "element_id": element["id"],
                    "panel_id": "PANEL_MAIN",
                    "role": element["role"],
                    "text_sample": element["text"],
                    "source_file": str(SOURCE),
                    "source_line": element["source_line"],
                    "declared_pt": "" if element["declared_pt"] is None else element["declared_pt"],
                    "graphics_scale": 1.0,
                    "source_local_effective_pt": "" if element["declared_pt"] is None else element["declared_pt"],
                    "pdf_extracted_size_pt": element["pdf_size_pt"],
                    "orientation_degrees": element["orientation"],
                    "bbox_pdf_x0": bbox[0], "bbox_pdf_y0": bbox[1],
                    "bbox_pdf_x1": bbox[2], "bbox_pdf_y1": bbox[3],
                    "bbox_px_x0": bbox_px[0], "bbox_px_y0": bbox_px[1],
                    "bbox_px_x1": bbox_px[2], "bbox_px_y1": bbox_px[3],
                    "h_ink_px": element["h_ink_px"],
                }
            )

    pair_fields = ["pair_id", "element_a", "element_b", "bbox_gap_px", "bbox_overlap_area_px"]
    with (OUT / "pair_registry_mechanical.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=pair_fields)
        writer.writeheader()
        for pair_number, (a, b) in enumerate(itertools.combinations(elements, 2), start=1):
            gap, overlap = bbox_gap(a["bbox_px"], b["bbox_px"])
            writer.writerow(
                {
                    "pair_id": f"PAIR-{pair_number:03d}",
                    "element_a": a["id"],
                    "element_b": b["id"],
                    "bbox_gap_px": gap,
                    "bbox_overlap_area_px": overlap,
                }
            )

    math_rows = []
    for p in (0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999):
        entropy = -(p * math.log(p) + (1 - p) * math.log(1 - p)) / math.log(2)
        symmetric = -((1 - p) * math.log(1 - p) + p * math.log(p)) / math.log(2)
        math_rows.append({"p": p, "H2_p": entropy, "H2_1_minus_p": symmetric, "symmetry_abs_error": abs(entropy - symmetric)})
    with (OUT / "math_samples_mechanical.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["p", "H2_p", "H2_1_minus_p", "symmetry_abs_error"])
        writer.writeheader()
        writer.writerows(math_rows)

    identity = {
        "handoff_id": "A-R114-P092-SA3-FRESH-ISOLATED-20260828",
        "canonical_instance": "/root/p092_r114_fresh_sa3",
        "figure_uid": "FIG-P092-01",
        "inputs": identity_rows,
        "pdf_page_count": len(document),
        "located_page_index0": hits[0],
        "located_physical_page": hits[0] + 1,
        "source_caption_tex": source_caption_tex,
        "figure_clip_pdf_points": [FIGURE_CLIP.x0, FIGURE_CLIP.y0, FIGURE_CLIP.x1, FIGURE_CLIP.y1],
        "reader_visible_element_count": len(elements),
        "unordered_pair_count": len(elements) * (len(elements) - 1) // 2,
    }
    (OUT / "current_input_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
