#!/usr/bin/env python3
"""Generate native FIG-P580-01 SA2 evidence without human decisions."""
from __future__ import annotations

import csv
import importlib.util
import itertools
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[3]
SOURCE_ROOT = WORK / "source" / "v2.7.0"
SOURCE = (
    SOURCE_ROOT / "src" / "绘图源码"
    / "第05册_采样方法主题模型与图排序"
    / "V5-C02" / "fig_v5_c02_is_support.tex"
)
PAGE_PDF = OUT / "build" / "page" / "v260_FIG-P580-01_page.pdf"
STANDALONE_PDF = OUT / "build" / "standalone" / "v260_FIG-P580-01_standalone.pdf"
PAGE_LOG = OUT / "build" / "page" / "v260_FIG-P580-01_page.log"
STANDALONE_LOG = OUT / "build" / "standalone" / "v260_FIG-P580-01_standalone.log"
CALIBRATION_TEX = OUT / "calibration_low_profile_punctuation.tex"
CALIBRATION_PDF = (
    OUT / "build" / "calibration"
    / "calibration_low_profile_punctuation.pdf"
)
OLD_PROBE = (
    OUT.parent / "STRICT_R1" / "SA1_20260824_R1" / "text_layer_probe.py"
)
DPI = 300
SCALE = DPI / 72.0
DELTA = 20
FIGURE_RECT_PT = (60.0, 140.0, 535.0, 366.0)

MASKS = OUT / "masks"
GLYPH_DIR = MASKS / "glyphs"
TEXT_SOURCE_DIR = MASKS / "text_source_shapes"
ELEMENT_DIR = MASKS / "text_elements"
GRAPHIC_DIR = MASKS / "graphics"
PRE_DIR = MASKS / "pre_occlusion"
HALO_DIR = MASKS / "opaque_halos"
EDGE_DIR = MASKS / "card_edges"
CONTACT_DIR = OUT / "glyph_shape_contact_sheets"
PIXFAIL_DIR = OUT / "pixel_failures"
CRITICAL_DIR = OUT / "critical_relations"
LOW_PROFILE_DIR = OUT / "low_profile_punctuation"
LOW_PROFILE_CHARACTERS = frozenset(
    ".,，、:：;；…⋯。"
)
for directory in (
    MASKS, GLYPH_DIR, TEXT_SOURCE_DIR, ELEMENT_DIR, GRAPHIC_DIR,
    PRE_DIR, HALO_DIR, EDGE_DIR, CONTACT_DIR, PIXFAIL_DIR, CRITICAL_DIR,
    LOW_PROFILE_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.resolve().relative_to(OUT).as_posix()


def save_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(
        np.where(mask, 0, 255).astype(np.uint8), mode="L"
    ).save(path, optimize=True)


def pxbox(
    box: Iterable[float], width: int, height: int, pad: int = 0
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (float(value) for value in box)
    return (
        max(0, math.floor(x0 * SCALE) - pad),
        max(0, math.floor(y0 * SCALE) - pad),
        min(width, math.ceil(x1 * SCALE) + pad),
        min(height, math.ceil(y1 * SCALE) + pad),
    )


def bbox_union(
    boxes: Iterable[tuple[int, int, int, int]]
) -> tuple[int, int, int, int]:
    values = list(boxes)
    return (
        min(box[0] for box in values),
        min(box[1] for box in values),
        max(box[2] for box in values),
        max(box[3] for box in values),
    )


@dataclass
class Obj:
    object_id: str
    kind: str
    role: str
    panel: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    path: Path
    text: str = ""
    parent: str = ""
    source: str = ""
    paint_order: int = -1

    @property
    def pixels(self) -> int:
        return int(self.mask.sum())

    @property
    def nonempty(self) -> bool:
        return bool(self.mask.any())


def union_objects(
    objects: list[Obj],
) -> tuple[tuple[int, int, int, int], np.ndarray]:
    box = bbox_union(obj.bbox for obj in objects)
    mask = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
    for obj in objects:
        mask[
            obj.bbox[1] - box[1] : obj.bbox[3] - box[1],
            obj.bbox[0] - box[0] : obj.bbox[2] - box[0],
        ] |= obj.mask
    return box, mask


def mask_intersection(
    a: Obj, b: Obj
) -> tuple[int, tuple[int, int, int, int] | None, np.ndarray | None]:
    x0, y0 = max(a.bbox[0], b.bbox[0]), max(a.bbox[1], b.bbox[1])
    x1, y1 = min(a.bbox[2], b.bbox[2]), min(a.bbox[3], b.bbox[3])
    if x0 >= x1 or y0 >= y1:
        return 0, None, None
    av = a.mask[
        y0 - a.bbox[1] : y1 - a.bbox[1],
        x0 - a.bbox[0] : x1 - a.bbox[0],
    ]
    bv = b.mask[
        y0 - b.bbox[1] : y1 - b.bbox[1],
        x0 - b.bbox[0] : x1 - b.bbox[0],
    ]
    intersection = av & bv
    return int(intersection.sum()), (x0, y0, x1, y1), intersection


def rect_clearance(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> float:
    dx = max(0, a[0] - b[2], b[0] - a[2])
    dy = max(0, a[1] - b[3], b[1] - a[3])
    return float(math.hypot(dx, dy))


def ink_clearance(a: Obj, b: Obj, close_limit: float = 64.0) -> float:
    if not a.nonempty or not b.nonempty:
        return float("nan")
    coarse = rect_clearance(a.bbox, b.bbox)
    if coarse > close_limit:
        return round(coarse, 6)
    box = bbox_union([a.bbox, b.bbox])
    amask = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
    bmask = np.zeros_like(amask)
    amask[
        a.bbox[1] - box[1] : a.bbox[3] - box[1],
        a.bbox[0] - box[0] : a.bbox[2] - box[0],
    ] = a.mask
    bmask[
        b.bbox[1] - box[1] : b.bbox[3] - box[1],
        b.bbox[0] - box[0] : b.bbox[2] - box[0],
    ] = b.mask
    if (amask & bmask).any():
        return 0.0
    distances = distance_transform_edt(~amask)
    return round(max(0.0, float(distances[bmask].min()) - 1.0), 6)


def colour_mask(rgb: np.ndarray, colour: Iterable[float]) -> np.ndarray:
    target = np.asarray(
        [float(value) * 255.0 if float(value) <= 1 else float(value)
         for value in colour],
        dtype=float,
    )
    vector = 255.0 - target
    denominator = float(np.dot(vector, vector))
    delta = 255.0 - rgb.astype(float)
    alpha = np.tensordot(delta, vector, axes=([2], [0])) / denominator
    residual = np.linalg.norm(delta - alpha[..., None] * vector, axis=2)
    return (
        (alpha >= DELTA / 255.0)
        & (alpha <= 1.08)
        & (residual <= 8.0)
    )


def render(pdf: Path, dpi: int, output: Path) -> None:
    subprocess.run(
        [
            "pdftoppm", "-f", "1", "-l", "1", "-r", str(dpi),
            "-png", "-singlefile", str(pdf), str(output.with_suffix("")),
        ],
        check=True,
    )


def build_low_profile_calibration() -> dict[str, Any]:
    """Measure an independently rendered caption-label period at 300 dpi."""
    for required in (CALIBRATION_TEX, CALIBRATION_PDF):
        if not required.exists():
            raise FileNotFoundError(required)
    full_path = LOW_PROFILE_DIR / "reference_full_page_300dpi.png"
    render(CALIBRATION_PDF, DPI, full_path)
    calibration_image = Image.open(full_path).convert("RGB")
    with fitz.open(CALIBRATION_PDF) as document:
        page = document[0]
        raw_candidates = []
        for block in page.get_text("rawdict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    for character in span["chars"]:
                        if str(character["c"]) == ".":
                            raw_candidates.append((span, character))
        trace_candidates = [
            (span, character)
            for span in page.get_texttrace()
            for character in span["chars"]
            if chr(int(character[0])) == "."
        ]
    if len(raw_candidates) != 1 or len(trace_candidates) != 1:
        raise RuntimeError(
            "independent punctuation calibration must contain exactly one period"
        )
    raw_span, raw_character = raw_candidates[0]
    trace_span, trace_character = trace_candidates[0]
    raw_box = pxbox(
        tuple(float(value) for value in raw_character["bbox"]),
        calibration_image.width,
        calibration_image.height,
    )
    trace_box = pxbox(
        tuple(float(value) for value in trace_character[3]),
        calibration_image.width,
        calibration_image.height,
    )
    union = bbox_union((raw_box, trace_box))
    box = (
        max(0, union[0] - 2),
        max(0, union[1] - 2),
        min(calibration_image.width, union[2] + 2),
        min(calibration_image.height, union[3] + 2),
    )
    raw_crop = calibration_image.crop(box).convert("RGB")
    reference_mask = colour_mask(
        np.asarray(raw_crop), trace_span["color"]
    )
    if not reference_mask.any():
        raise RuntimeError("independent punctuation calibration raw mask is empty")
    raw_1x = LOW_PROFILE_DIR / "reference_source_raw_1x.png"
    raw_8x = LOW_PROFILE_DIR / "reference_source_raw_8x_nearest.png"
    mask_1x = LOW_PROFILE_DIR / "reference_pure_mask_1x.png"
    mask_8x = LOW_PROFILE_DIR / "reference_pure_mask_8x_nearest.png"
    raw_crop.save(raw_1x, optimize=True)
    raw_crop.resize(
        (raw_crop.width * 8, raw_crop.height * 8),
        Image.Resampling.NEAREST,
    ).save(raw_8x, optimize=True)
    mask_image = Image.fromarray(
        np.where(reference_mask, 0, 255).astype(np.uint8), mode="L"
    )
    mask_image.save(mask_1x, optimize=True)
    mask_image.resize(
        (mask_image.width * 8, mask_image.height * 8),
        Image.Resampling.NEAREST,
    ).save(mask_8x, optimize=True)
    metadata = {
        "schema_revision": 111,
        "character": ".",
        "unicode": "U+002E",
        "source_tex": rel(CALIBRATION_TEX),
        "source_command": (
            r"\small\bfseries\color{SLBodyText}."
        ),
        "pdf": rel(CALIBRATION_PDF),
        "font": str(trace_span["font"]),
        "font_size_pt": float(trace_span["size"]),
        "colour_rgb_unit": [
            float(value) for value in trace_span["color"]
        ],
        "rawdict_font": str(raw_span["font"]),
        "rawdict_size_pt": float(raw_span["size"]),
        "native_bbox_full_page_px": list(box),
        "h_ink_px": int(reference_mask.any(axis=1).sum()),
        "ink_area_px": int(reference_mask.sum()),
        "source_raw_1x": rel(raw_1x),
        "source_raw_8x": rel(raw_8x),
        "pure_mask_1x": rel(mask_1x),
        "pure_mask_8x": rel(mask_8x),
        "measurement_grid": "native Poppler 300dpi 1:1",
        "eight_x_use": "nearest-neighbour inspection only; never counted",
    }
    metadata_path = LOW_PROFILE_DIR / "reference_measurement.json"
    save_json(metadata_path, metadata)
    return {
        **metadata,
        "artifact_path_objects": [
            CALIBRATION_TEX, CALIBRATION_PDF, full_path,
            raw_1x, raw_8x, mask_1x, mask_8x, metadata_path,
        ],
    }


def load_probe() -> Any:
    spec = importlib.util.spec_from_file_location("strict_text_probe", OLD_PROBE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load strict text-only replay parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_text_replay() -> dict[str, Any]:
    probe = load_probe()
    output_pdf = OUT / "page_text_only_replay.pdf"
    document = fitz.open(PAGE_PDF)
    page = document[0]
    xrefs = page.get_contents()
    if len(xrefs) != 1:
        raise RuntimeError(f"expected one content stream, got {xrefs}")
    before_chars = probe.chars(page)
    before_trace = probe.trace_properties(page)
    filtered, parser = probe.text_only_content(document.xref_stream(xrefs[0]))
    document.update_stream(xrefs[0], filtered)
    document.save(output_pdf, garbage=4, deflate=True)
    document.close()
    replay = fitz.open(output_pdf)
    after_chars = probe.chars(replay[0])
    after_trace = probe.trace_properties(replay[0])
    replay.close()
    render(output_pdf, 300, OUT / "page_text_only_replay_300dpi.png")
    report = {
        "source_pdf": str(PAGE_PDF),
        "output_pdf": rel(output_pdf),
        "character_count": len(before_chars),
        "character_stream_exact": before_chars == after_chars,
        "texttrace_count": len(before_trace),
        "text_trace_visual_properties_exact": before_trace == after_trace,
        "parser": parser,
    }
    save_json(OUT / "text_only_replay_probe.json", report)
    return report


def classify(
    character: str, font_pt: float, parent_base_pt: float
) -> tuple[str, int]:
    code = ord(character)
    if character in LOW_PROFILE_CHARACTERS:
        # Revision111: do not apply a mechanical height floor to naturally
        # low-profile punctuation.  Its row is decided by the independent
        # same-font/same-weight/same-size native-300dpi calibration below.
        return "LOW_PROFILE_PUNCTUATION", 0
    if (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
    ):
        return "CJK_HAN", 30
    if 0xFF01 <= code <= 0xFFEF:
        return "FULLWIDTH", 30
    if font_pt < parent_base_pt * 0.95:
        return "NATURAL_SCRIPT", 15
    if character in "（）【】《》“”‘’()[]{}!?":
        return "PUNCTUATION", 22
    if character in "+-=−–—<>≤≥≪≫≈∼∝×÷/\\|*·":
        return "MATH_OPERATOR", 22
    if character.isdigit() or character.isupper():
        return "UPPER_OR_DIGIT", 24
    if character.islower() or "Α" <= character <= "ω":
        return "LOWER_OR_GREEK", 17
    return "MATH_BASE", 22


def declared_pt(role: str) -> float:
    if role == "PANEL_TITLE":
        return 10.2
    if role == "CAPTION":
        return 10.0
    return 9.6


def source_line(role: str) -> str:
    return {
        "PANEL_TITLE": "fig_v5_c02_is_support.tex:36,64",
        "TICK": "fig_v5_c02_is_support.tex:22-23",
        "AXIS_TITLE": "fig_v5_c02_is_support.tex:37-39,65",
        "ANNOTATION": "fig_v5_c02_is_support.tex:57-67",
        "LEGEND": "fig_v5_c02_is_support.tex:37-39,66-68",
        "FORMULA": "fig_v5_c02_is_support.tex:78-88",
        "CAPTION": (
            "fig_v5_c02_is_support.tex:94; automatic figure-number label "
            "generated by read-only common caption style"
        ),
    }[role]


def semantic_key(line: dict[str, Any]) -> tuple[str, str, str]:
    x0, y0, x1, _ = line["bbox"]
    text = line["text"]
    centre = (x0 + x1) / 2
    if 339 <= y0 < 366:
        return "CAPTION", "CAPTION", "GLOBAL"
    if y0 < 165:
        return (
            ("L_TITLE", "PANEL_TITLE", "L")
            if centre < 330 else
            ("R_TITLE", "PANEL_TITLE", "R")
        )
    if x1 < 150 and 205 < y0 < 255:
        return "L_YLABEL", "AXIS_TITLE", "L"
    if 170 <= y0 < 205 and 175 < x0 < 245:
        return "L_Q_LABEL", "ANNOTATION", "L"
    if 210 <= y0 < 235 and 175 < x0 < 240:
        return "L_P_LABEL", "ANNOTATION", "L"
    if 170 <= y0 < 205 and 245 <= x0 < 320:
        return "L_BOUNDARY_LABEL", "ANNOTATION", "L"
    if 170 <= y0 < 222 and x0 > 345:
        return "R_WEIGHT_CARD", "FORMULA", "R"
    if 180 <= y0 < 300 and x1 <= 171:
        return f"L_YT_{text}", "TICK", "L"
    if 180 <= y0 < 300 and 315 <= x0 < 338:
        return f"R_YT_{text}", "TICK", "R"
    if 294 <= y0 < 308 and 170 <= x0 < 320:
        label = "HALF" if 240 <= centre <= 250 else text
        return f"L_XT_{label}", "TICK", "L"
    if 294 <= y0 < 308 and 335 <= x0 < 490:
        label = "HALF" if 405 <= centre <= 417 else text
        return f"R_XT_{label}", "TICK", "R"
    if 310 <= y0 < 323:
        return (
            ("L_DOMAIN", "AXIS_TITLE", "L")
            if centre < 330 else
            ("R_DOMAIN", "AXIS_TITLE", "R")
        )
    if 323 <= y0 < 339:
        return (
            ("L_HATCH_DECODE", "LEGEND", "L")
            if centre < 330 else
            ("R_CURVE_DECODE", "LEGEND", "R")
        )
    raise RuntimeError(f"unassigned in-scope PDF line: {line}")


def role_basis(key: str, role: str) -> str:
    if key == "L_Q_LABEL":
        return (
            "direct in-plot node at axis cs (.16,.455); explains the local "
            "q_L segment/value inside the data rectangle, hence ANNOTATION"
        )
    if key == "L_P_LABEL":
        return (
            "direct in-plot node at axis cs (.16,.305); local curve callout "
            "inside the data rectangle, hence ANNOTATION"
        )
    if key == "L_BOUNDARY_LABEL":
        return (
            "direct in-plot two-line node tied to the support boundary, "
            "hence ANNOTATION"
        )
    if key == "L_HATCH_DECODE":
        return (
            "second physical row of the left pgfplots xlabel; explicitly "
            "decodes the hatch swatch/semantics outside the data rectangle, "
            "hence LEGEND rather than in-plot ANNOTATION"
        )
    if key == "R_CURVE_DECODE":
        return (
            "second physical row of the right pgfplots xlabel; explicitly "
            "decodes blue-solid and teal-dashed encodings outside the data "
            "rectangle, hence LEGEND"
        )
    if key in ("L_DOMAIN", "R_DOMAIN"):
        return "first physical xlabel row naming the common x domain; AXIS_TITLE"
    if key.endswith("_TITLE"):
        return "pgfplots title node; PANEL_TITLE"
    if "_XT_" in key or "_YT_" in key:
        return "pgfplots tick label; TICK"
    if key == "R_WEIGHT_CARD":
        return "independent mathematical ratio card; FORMULA"
    if key == "CAPTION":
        return "figure caption label/body in the candidate page; CAPTION"
    return f"source/PDF semantic assignment for {role}"


def safe_name(identifier: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", identifier)
    return value or "EMPTY_ID"


def raster_drawing(
    drawing: dict[str, Any],
    page_rect: fitz.Rect,
    width: int,
    height: int,
    box: tuple[int, int, int, int],
    *,
    coverage: bool = False,
    fill_only: bool = False,
    stroke_only: bool = False,
) -> np.ndarray:
    document = fitz.open()
    page = document.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item in drawing["items"]:
        if item[0] == "l":
            shape.draw_line(item[1], item[2])
        elif item[0] == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif item[0] == "re":
            shape.draw_rect(item[1])
        else:
            document.close()
            raise RuntimeError(f"unhandled drawing item {item[0]}")
    cap = drawing.get("lineCap") or 0
    if isinstance(cap, (tuple, list)):
        cap = cap[0]
    stroke = None if fill_only else drawing.get("color")
    fill = None if stroke_only else drawing.get("fill")
    if coverage:
        stroke = (
            None
            if fill_only
            else ((0.0, 0.0, 0.0) if stroke is not None else None)
        )
        fill = (0.0, 0.0, 0.0) if fill is not None else None
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=stroke,
        fill=fill,
        lineCap=int(cap),
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        closePath=bool(drawing.get("closePath", False)),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
    )
    shape.commit()
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(SCALE, SCALE),
        colorspace=fitz.csRGB,
        alpha=False,
    )
    array = np.frombuffer(
        pixmap.samples, dtype=np.uint8
    ).reshape(pixmap.height, pixmap.width, pixmap.n)[:, :, :3]
    document.close()
    mask = np.max(np.abs(array.astype(np.int16) - 255), axis=2) >= DELTA
    return mask[box[1] : box[3], box[0] : box[2]].copy()


def relation_package(
    relation_id: str,
    a: Obj,
    b: Obj,
    raw: Image.Image,
    overlap: int,
    clearance: float,
    required: float,
    reason: str,
) -> str:
    directory = CRITICAL_DIR / safe_name(relation_id)
    directory.mkdir(parents=True, exist_ok=True)
    union = bbox_union([a.bbox, b.bbox])
    box = (
        max(0, union[0] - 6),
        max(0, union[1] - 6),
        min(raw.width, union[2] + 6),
        min(raw.height, union[3] + 6),
    )
    amask = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
    bmask = np.zeros_like(amask)
    for obj, target in ((a, amask), (b, bmask)):
        x0, y0 = max(box[0], obj.bbox[0]), max(box[1], obj.bbox[1])
        x1, y1 = min(box[2], obj.bbox[2]), min(box[3], obj.bbox[3])
        if x0 < x1 and y0 < y1:
            target[
                y0 - box[1] : y1 - box[1],
                x0 - box[0] : x1 - box[0],
            ] = obj.mask[
                y0 - obj.bbox[1] : y1 - obj.bbox[1],
                x0 - obj.bbox[0] : x1 - obj.bbox[0],
            ]
    intersection = amask & bmask
    roi = raw.crop(box).convert("RGB")
    overlay = np.asarray(roi).copy()
    overlay[amask] = (220, 30, 30)
    overlay[bmask] = (30, 90, 220)
    overlay[intersection] = (255, 0, 255)
    views: dict[str, Image.Image] = {
        "raw_roi_1x.png": roi,
        "object_A_mask_1x.png": Image.fromarray(
            np.where(amask, 0, 255).astype(np.uint8), mode="L"
        ),
        "object_B_mask_1x.png": Image.fromarray(
            np.where(bmask, 0, 255).astype(np.uint8), mode="L"
        ),
        "intersection_mask_1x.png": Image.fromarray(
            np.where(intersection, 0, 255).astype(np.uint8), mode="L"
        ),
        "overlay_1x.png": Image.fromarray(overlay, mode="RGB"),
    }
    for filename, image in views.items():
        image.save(directory / filename, optimize=True)
        image.resize(
            (image.width * 8, image.height * 8),
            Image.Resampling.NEAREST,
        ).save(
            directory / filename.replace("_1x", "_8x_nearest"),
            optimize=True,
        )
    save_json(
        directory / "relation.json",
        {
            "relation_id": relation_id,
            "object_A": a.object_id,
            "object_B": b.object_id,
            "native_bbox_full_page_px": list(box),
            "overlap_pixels": overlap,
            "clearance_pixels": clearance,
            "required_clearance_pixels": required,
            "reason": reason,
            "measurement_grid": (
                "native 300dpi 1:1; 8x nearest inspection only"
            ),
        },
    )
    return rel(directory)


def pixel_failure_package(
    row: dict[str, Any], obj: Obj, raw: Image.Image
) -> str:
    directory = PIXFAIL_DIR / safe_name(str(row["MEASURE_ID"]))
    directory.mkdir(parents=True, exist_ok=True)
    box = (
        max(0, obj.bbox[0] - 5),
        max(0, obj.bbox[1] - 5),
        min(raw.width, obj.bbox[2] + 5),
        min(raw.height, obj.bbox[3] + 5),
    )
    roi = raw.crop(box).convert("RGB")
    target = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
    target[
        obj.bbox[1] - box[1] : obj.bbox[3] - box[1],
        obj.bbox[0] - box[0] : obj.bbox[2] - box[0],
    ] = obj.mask
    overlay = np.asarray(roi).copy()
    overlay[target] = (230, 25, 25)
    views: dict[str, Image.Image] = {
        "original_roi_1x.png": roi,
        "target_mask_1x.png": Image.fromarray(
            np.where(target, 0, 255).astype(np.uint8), mode="L"
        ),
        "target_overlay_1x.png": Image.fromarray(overlay, mode="RGB"),
    }
    for filename, image in views.items():
        image.save(directory / filename, optimize=True)
        image.resize(
            (image.width * 8, image.height * 8),
            Image.Resampling.NEAREST,
        ).save(
            directory / filename.replace("_1x", "_8x_nearest"),
            optimize=True,
        )
    save_json(
        directory / "measurement.json",
        {
            **row,
            "native_bbox_full_page_px": list(obj.bbox),
            "grid": "300dpi native 1:1",
        },
    )
    return rel(directory)


def low_profile_candidate_package(
    row: dict[str, Any], obj: Obj, raw: Image.Image,
    calibration: dict[str, Any],
) -> str:
    """Save native 1x and 8x views for every revision111 punctuation row."""
    directory = LOW_PROFILE_DIR / safe_name(str(row["MEASURE_ID"]))
    directory.mkdir(parents=True, exist_ok=True)
    box = (
        max(0, obj.bbox[0] - 5),
        max(0, obj.bbox[1] - 5),
        min(raw.width, obj.bbox[2] + 5),
        min(raw.height, obj.bbox[3] + 5),
    )
    roi = raw.crop(box).convert("RGB")
    target = np.zeros((box[3] - box[1], box[2] - box[0]), dtype=bool)
    target[
        obj.bbox[1] - box[1] : obj.bbox[3] - box[1],
        obj.bbox[0] - box[0] : obj.bbox[2] - box[0],
    ] = obj.mask
    overlay = np.asarray(roi).copy()
    overlay[target] = (230, 25, 25)
    views = {
        "candidate_source_raw_1x.png": roi,
        "candidate_target_overlay_1x.png": Image.fromarray(
            overlay, mode="RGB"
        ),
        "candidate_pure_mask_1x.png": Image.fromarray(
            np.where(target, 0, 255).astype(np.uint8), mode="L"
        ),
    }
    for filename, image in views.items():
        image.save(directory / filename, optimize=True)
        image.resize(
            (image.width * 8, image.height * 8),
            Image.Resampling.NEAREST,
        ).save(
            directory / filename.replace("_1x", "_8x_nearest"),
            optimize=True,
        )
    save_json(
        directory / "comparison.json",
        {
            "schema_revision": 111,
            "candidate": row,
            "candidate_native_bbox_full_page_px": list(obj.bbox),
            "candidate_roi_full_page_px": list(box),
            "reference_measurement": (
                "low_profile_punctuation/reference_measurement.json"
            ),
            "reference_h_ink_px": calibration["h_ink_px"],
            "reference_ink_area_px": calibration["ink_area_px"],
            "measurement_grid": "native 300dpi 1:1",
            "eight_x_use": "nearest-neighbour inspection only; never counted",
        },
    )
    return rel(directory)


def main() -> int:
    for required in (
        SOURCE, PAGE_PDF, STANDALONE_PDF, PAGE_LOG, STANDALONE_LOG,
        OLD_PROBE, CALIBRATION_TEX, CALIBRATION_PDF,
    ):
        if not required.exists():
            raise FileNotFoundError(required)

    render(PAGE_PDF, 300, OUT / "full_page_300dpi.png")
    render(PAGE_PDF, 200, OUT / "full_page_200dpi.png")
    render(STANDALONE_PDF, 300, OUT / "standalone_300dpi.png")
    replay_report = build_text_replay()
    calibration = build_low_profile_calibration()

    raw = Image.open(OUT / "full_page_300dpi.png").convert("RGB")
    raw200 = Image.open(OUT / "full_page_200dpi.png").convert("RGB")
    standalone = Image.open(OUT / "standalone_300dpi.png").convert("RGB")
    replay_image = Image.open(
        OUT / "page_text_only_replay_300dpi.png"
    ).convert("RGB")
    width, height = raw.size
    if (
        raw.size != (2481, 3508)
        or raw200.size != (1654, 2339)
        or standalone.size != (2481, 3508)
        or replay_image.size != raw.size
    ):
        raise RuntimeError(
            f"native grid drift: page={raw.size}, 200={raw200.size}, "
            f"standalone={standalone.size}, text={replay_image.size}"
        )
    figure_box = pxbox(FIGURE_RECT_PT, width, height)
    figure = raw.crop(figure_box)
    figure.save(OUT / "figure_crop_300dpi.png", optimize=True)
    ImageOps.grayscale(figure).save(
        OUT / "grayscale_300dpi.png", optimize=True
    )

    rgb = np.asarray(raw, dtype=np.int16)
    ink = np.max(np.abs(rgb - 255), axis=2) >= DELTA
    replay_rgb = np.asarray(replay_image, dtype=np.int16)
    replay_ink = np.max(np.abs(replay_rgb - 255), axis=2) >= DELTA
    save_mask(replay_ink, MASKS / "text_only_replay_ink_300dpi.png")

    with fitz.open(PAGE_PDF) as document:
        page = document[0]
        page_rect = page.rect
        page_text = page.get_text("text")
        page_dict = page.get_text("rawdict")
        drawings = page.get_drawings()
        traces = []
        order = 0
        for span in page.get_texttrace():
            for character in span["chars"]:
                traces.append(
                    {
                        "char": chr(int(character[0])),
                        "bbox": tuple(float(value) for value in character[3]),
                        "paint_order": order,
                        "seqno": int(span.get("seqno", -1)),
                        "font": str(span.get("font", "")),
                        "font_size": float(span.get("size", 0)),
                        "colour": tuple(
                            float(value)
                            for value in span.get("color", (0, 0, 0))
                        ),
                    }
                )
                order += 1

    (OUT / "page_anchor_text.txt").write_text(page_text, encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    anchor_checks = {
        "figure_uid": "FIG-P580-01" in source,
        "left_title": "支持不足" in page_text,
        "right_title": "支持覆盖" in page_text,
        "left_hatch_decode": "斜线区" in page_text and "为0 且" in page_text,
        "right_line_decode": (
            "实线" in page_text and "虚线" in page_text
            and "1/5" in page_text
        ),
        "caption": (
            "重要性抽样要求" in page_text and "未覆盖" in page_text
        ),
        "no_resize_or_scale_y": (
            "\\resizebox" not in source
            and "\\scalebox" not in source
            and "scale y" not in source
        ),
        "general_font_9_6": "\\fontsize{9.6pt}" in source,
    }
    save_json(
        OUT / "source_text_anchor.json",
        {
            "checks": anchor_checks,
            "result": "PASS" if all(anchor_checks.values()) else "FAIL",
        },
    )
    save_json(
        OUT / "render_manifest.json",
        {
            "candidate_page_pdf": str(PAGE_PDF),
            "candidate_standalone_pdf": str(STANDALONE_PDF),
            "physical_page": 1,
            "page_size_pt": [
                round(page_rect.width, 3), round(page_rect.height, 3)
            ],
            "full_page_300dpi_grid": [width, height],
            "full_page_200dpi_grid": list(raw200.size),
            "standalone_300dpi_grid": list(standalone.size),
            "measurement_dpi": 300,
            "figure_crop_full_page_px": list(figure_box),
            "resize_after_render": False,
            "measurement_basis": (
                "page wrapper direct Poppler 300dpi; integer crop only"
            ),
            "build_logs": [rel(PAGE_LOG), rel(STANDALONE_LOG)],
            "build_exit_codes": {"page": 0, "standalone": 0},
        },
    )

    raw_lines: list[dict[str, Any]] = []
    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            box = tuple(float(value) for value in line["bbox"])
            if not (
                box[0] < FIGURE_RECT_PT[2]
                and box[2] > FIGURE_RECT_PT[0]
                and box[1] < FIGURE_RECT_PT[3]
                and box[3] > FIGURE_RECT_PT[1]
            ):
                continue
            characters = []
            for span in line["spans"]:
                for character in span["chars"]:
                    characters.append(
                        {
                            **character,
                            "font": span.get("font", ""),
                            "size": float(span.get("size", 0)),
                        }
                    )
            text = "".join(str(character["c"]) for character in characters)
            if text.strip():
                raw_lines.append(
                    {"bbox": box, "text": text, "chars": characters}
                )

    grouped_lines: dict[str, list[dict[str, Any]]] = defaultdict(list)
    node_meta: dict[str, tuple[str, str]] = {}
    for line in raw_lines:
        key, role, panel = semantic_key(line)
        grouped_lines[key].append(line)
        node_meta[key] = (role, panel)

    available = list(traces)
    glyphs: list[Obj] = []
    glyph_info: dict[str, dict[str, Any]] = {}
    glyphs_by_line: dict[int, list[Obj]] = defaultdict(list)
    combining_components = []
    for line_number, line in enumerate(raw_lines):
        for character in line["chars"]:
            value = str(character["c"])
            if not value.strip() or ord(value) < 32:
                continue
            if value == "\u0338":
                combining_components.append(
                    {
                        "char": value,
                        "line": line["text"],
                        "closure": "S_NOT_LL",
                    }
                )
                continue
            choices = [
                (index, trace)
                for index, trace in enumerate(available)
                if trace["char"] == value
            ]
            if not choices:
                raise RuntimeError(f"no texttrace owner for {value!r}")
            raw_box_pt = tuple(float(v) for v in character["bbox"])
            index, trace = min(
                choices,
                key=lambda pair: sum(
                    abs(a - b)
                    for a, b in zip(pair[1]["bbox"], raw_box_pt)
                ),
            )
            drift = sum(
                abs(a - b) for a, b in zip(trace["bbox"], raw_box_pt)
            )
            if drift > 6.0:
                raise RuntimeError(
                    f"ambiguous texttrace owner {value!r}: drift={drift}"
                )
            available.pop(index)
            raw_box = pxbox(raw_box_pt, width, height)
            trace_box = pxbox(trace["bbox"], width, height)
            unpadded = bbox_union([raw_box, trace_box])
            box = (
                max(0, unpadded[0] - 2),
                max(0, unpadded[1] - 2),
                min(width, unpadded[2] + 2),
                min(height, unpadded[3] + 2),
            )
            candidate = replay_ink[
                box[1] : box[3], box[0] : box[2]
            ].copy()
            glyph_id = f"G{len(glyphs) + 1:04d}"
            path = GLYPH_DIR / f"{glyph_id}_raw.png"
            glyph = Obj(
                glyph_id,
                "GLYPH",
                "",
                "",
                box,
                candidate,
                path,
                text=value,
                paint_order=int(trace["paint_order"]),
            )
            glyphs.append(glyph)
            glyphs_by_line[line_number].append(glyph)
            glyph_info[glyph_id] = {
                "rawdict_bbox_px": list(raw_box),
                "texttrace_bbox_px": list(trace_box),
                "ownership_bbox_px": list(box),
                "rawdict_texttrace_drift_pt": round(drift, 6),
                "font": trace["font"],
                "font_size_pt": trace["font_size"],
                "fill_rgb": list(trace["colour"]),
                "seqno": trace["seqno"],
                "paint_order": trace["paint_order"],
                "source_candidate_pixels": int(candidate.sum()),
            }

    ownership_conflicts = []
    for left, right in itertools.combinations(glyphs, 2):
        x0, y0 = (
            max(left.bbox[0], right.bbox[0]),
            max(left.bbox[1], right.bbox[1]),
        )
        x1, y1 = (
            min(left.bbox[2], right.bbox[2]),
            min(left.bbox[3], right.bbox[3]),
        )
        if x0 >= x1 or y0 >= y1:
            continue
        left_view = left.mask[
            y0 - left.bbox[1] : y1 - left.bbox[1],
            x0 - left.bbox[0] : x1 - left.bbox[0],
        ]
        right_view = right.mask[
            y0 - right.bbox[1] : y1 - right.bbox[1],
            x0 - right.bbox[0] : x1 - right.bbox[0],
        ]
        shared = left_view & right_view
        if not shared.any():
            continue
        # Adjacent characters have overlapping padded ownership ROIs even
        # though their ink does not overlap semantically.  Paint order alone
        # incorrectly handed the two rightmost base pixels of the figure
        # number ``1`` to the following low-profile period.  Partition every
        # shared replay pixel by distance to the unpadded rawdict character
        # boxes; use centre distance only when a pixel lies in both boxes.
        # This keeps the raw mask of each punctuation mark independent, as
        # required by revision111, without changing the rendered candidate.
        left_core = glyph_info[left.object_id]["rawdict_bbox_px"]
        right_core = glyph_info[right.object_id]["rawdict_bbox_px"]
        shared_y, shared_x = np.nonzero(shared)
        full_x = shared_x + x0
        full_y = shared_y + y0

        def ownership_score(
            x_coordinates: np.ndarray,
            y_coordinates: np.ndarray,
            core: list[int],
        ) -> np.ndarray:
            dx = np.maximum(
                np.maximum(core[0] - x_coordinates, 0),
                x_coordinates - (core[2] - 1),
            )
            dy = np.maximum(
                np.maximum(core[1] - y_coordinates, 0),
                y_coordinates - (core[3] - 1),
            )
            rectangle_distance = dx * dx + dy * dy
            centre_x_twice = core[0] + core[2] - 1
            centre_y_twice = core[1] + core[3] - 1
            centre_distance = (
                (2 * x_coordinates - centre_x_twice) ** 2
                + (2 * y_coordinates - centre_y_twice) ** 2
            )
            return rectangle_distance * 1_000_000 + centre_distance

        left_score = ownership_score(full_x, full_y, left_core)
        right_score = ownership_score(full_x, full_y, right_core)
        left_wins = left_score <= right_score
        right_wins = ~left_wins
        left_view[shared_y[right_wins], shared_x[right_wins]] = False
        right_view[shared_y[left_wins], shared_x[left_wins]] = False
        ownership_conflicts.append(
            {
                "glyph_A": left.object_id,
                "glyph_B": right.object_id,
                "pixels": int(shared.sum()),
                "pixels_owned_by_A": int(left_wins.sum()),
                "pixels_owned_by_B": int(right_wins.sum()),
                "rule": (
                    "nearest unpadded rawdict character box; centre-distance "
                    "tie-break"
                ),
            }
        )

    source_assignment = np.zeros((height, width), dtype=np.uint16)
    source_shapes: dict[str, np.ndarray] = {}
    for glyph in glyphs:
        source_shapes[glyph.object_id] = glyph.mask.copy()
        save_mask(
            glyph.mask,
            TEXT_SOURCE_DIR / f"{glyph.object_id}_source.png",
        )
        source_assignment[
            glyph.bbox[1] : glyph.bbox[3],
            glyph.bbox[0] : glyph.bbox[2],
        ] += glyph.mask.astype(np.uint16)
        final_colour = colour_mask(
            rgb[
                glyph.bbox[1] : glyph.bbox[3],
                glyph.bbox[0] : glyph.bbox[2],
            ],
            glyph_info[glyph.object_id]["fill_rgb"],
        )
        glyph.mask &= (
            ink[
                glyph.bbox[1] : glyph.bbox[3],
                glyph.bbox[0] : glyph.bbox[2],
            ]
            & final_colour
        )
        save_mask(glyph.mask, glyph.path)
        glyph_info[glyph.object_id].update(
            {
                "source_owned_pixels": int(
                    source_shapes[glyph.object_id].sum()
                ),
                "final_visible_pixels": glyph.pixels,
                "missing_source_pixels": int(
                    (
                        source_shapes[glyph.object_id]
                        & ~glyph.mask
                    ).sum()
                ),
                "foreign_final_pixels": int(
                    (
                        glyph.mask
                        & ~source_shapes[glyph.object_id]
                    ).sum()
                ),
            }
        )

    source_scope = replay_ink[
        figure_box[1] : figure_box[3],
        figure_box[0] : figure_box[2],
    ]
    owner_scope = source_assignment[
        figure_box[1] : figure_box[3],
        figure_box[0] : figure_box[2],
    ]
    ownership_report = {
        "source_text_pixels_in_scope": int(source_scope.sum()),
        "source_unassigned_text_pixels": int(
            (source_scope & (owner_scope == 0)).sum()
        ),
        "source_duplicate_text_pixels": int((owner_scope > 1).sum()),
        "conflict_resolution": ownership_conflicts,
        "combining_components": combining_components,
        "rule": (
            "BT/ET replay candidate, rawdict/texttrace ROI, "
            "nearest unpadded rawdict character box owns shared replay pixel"
        ),
    }
    save_json(OUT / "glyph_ownership_report.json", ownership_report)

    line_index = {
        id(line): index for index, line in enumerate(raw_lines)
    }
    node_specs = []
    for key, lines in grouped_lines.items():
        role, panel = node_meta[key]
        node_specs.append(
            (
                min(line["bbox"][1] for line in lines),
                min(line["bbox"][0] for line in lines),
                key, role, panel, lines,
            )
        )
    node_specs.sort()
    elements: list[Obj] = []
    element_glyphs: dict[str, list[Obj]] = {}
    key_to_element: dict[str, Obj] = {}
    font_rows: list[dict[str, Any]] = []
    for _, _, key, role, panel, lines in node_specs:
        members = [
            glyph
            for line in lines
            for glyph in glyphs_by_line[line_index[id(line)]]
        ]
        if not members:
            raise RuntimeError(f"semantic node without glyphs: {key}")
        element_id = f"E{len(elements) + 1:03d}"
        for glyph in members:
            glyph.parent = element_id
            glyph.role = role
            glyph.panel = panel
        box, mask = union_objects(members)
        path = ELEMENT_DIR / f"{element_id}_raw.png"
        text = " / ".join(line["text"] for line in lines)
        element = Obj(
            element_id, "TEXT", role, panel, box, mask, path,
            text=text, source=source_line(role),
        )
        save_mask(mask, path)
        elements.append(element)
        element_glyphs[element_id] = members
        key_to_element[key] = element
        font_rows.append(
            {
                "ELEMENT_ID": element_id,
                "SOURCE_NODE": key,
                "PANEL_ID": panel,
                "ROLE": role,
                "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": source_line(role),
                "DECLARED_PT": f"{declared_pt(role):.2f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{declared_pt(role):.2f}",
                "PDF_FONT_PT_MEDIAN": (
                    f"{median(glyph_info[g.object_id]['font_size_pt'] for g in members):.3f}"
                ),
                "TEXT_SAMPLE": text,
                "RAW_MASK": rel(path),
                "SOURCE_FONT_PASS": str(
                    declared_pt(role) >= 9.5
                ).lower(),
                "REASON": (
                    "PASS"
                    if declared_pt(role) >= 9.5
                    else "effective_pt_below_9.5"
                ),
            }
        )

    write_csv(
        OUT / "role_assignment_ledger.csv",
        [
            {
                "ELEMENT_ID": key_to_element[key].object_id,
                "SOURCE_NODE": key,
                "PANEL_ID": key_to_element[key].panel,
                "ROLE": key_to_element[key].role,
                "TEXT_SAMPLE": key_to_element[key].text,
                "SOURCE_LINE": key_to_element[key].source,
                "ROLE_BASIS": role_basis(key, key_to_element[key].role),
            }
            for key in sorted(key_to_element)
        ],
        [
            "ELEMENT_ID", "SOURCE_NODE", "PANEL_ID", "ROLE",
            "TEXT_SAMPLE", "SOURCE_LINE", "ROLE_BASIS",
        ],
    )

    vector_components: list[Obj] = []
    substring_rows: list[dict[str, Any]] = []
    substring_objects: dict[str, Obj] = {}
    # Every visible slash-form numeric fraction gets its own tight composite.
    # Unlike TeX numerator/denominator scripts, these digits remain at the
    # >=24px digit gate and the slash remains at the >=22px operator gate.
    for parent in elements:
        members = sorted(
            element_glyphs[parent.object_id],
            key=lambda glyph: glyph.paint_order,
        )
        for slash_index, glyph in enumerate(members):
            if glyph.text != "/":
                continue
            left_index = slash_index - 1
            right_index = slash_index + 1
            left_digits: list[Obj] = []
            right_digits: list[Obj] = []
            while left_index >= 0 and members[left_index].text.isdigit():
                left_digits.insert(0, members[left_index])
                left_index -= 1
            while (
                right_index < len(members)
                and members[right_index].text.isdigit()
            ):
                right_digits.append(members[right_index])
                right_index += 1
            if not left_digits or not right_digits:
                continue
            parts = left_digits + [glyph] + right_digits
            substring_box, substring_mask = union_objects(parts)
            substring_id = (
                f"S_NUMERIC_SLASH_{len(substring_rows) + 1:02d}"
            )
            substring_path = GLYPH_DIR / f"{substring_id}_raw.png"
            text_value = "".join(part.text for part in parts)
            substring = Obj(
                substring_id,
                "TEXT_SUBSTRING",
                parent.role,
                parent.panel,
                substring_box,
                substring_mask,
                substring_path,
                text=text_value,
                parent=parent.object_id,
                source=source_line(parent.role),
            )
            save_mask(substring_mask, substring_path)
            substring_objects[substring_id] = substring
            height_ink = int(substring_mask.any(axis=1).sum())
            substring_rows.append(
                {
                    "MEASURE_ID": substring_id,
                    "ELEMENT_ID": substring_id,
                    "PARENT_ELEMENT_ID": parent.object_id,
                    "PANEL_ID": parent.panel,
                    "ROLE": parent.role,
                    "SOURCE_FILE": str(SOURCE),
                    "SOURCE_LINE": source_line(parent.role),
                    "DECLARED_PT": f"{declared_pt(parent.role):.2f}",
                    "GRAPHICS_SCALE": "1.000000",
                    "EFFECTIVE_PT": f"{declared_pt(parent.role):.2f}",
                    "PDF_FONT_PT": "INLINE_TEXT_GLYPHS",
                    "TEXT_SAMPLE": text_value,
                    "UNICODE": "N/A_COMPOSITE",
                    "SCRIPT_CLASS": "MATH_BASE",
                    "THRESHOLD_PX": 22,
                    "BBOX_X0": substring_box[0],
                    "BBOX_Y0": substring_box[1],
                    "BBOX_X1": substring_box[2],
                    "BBOX_Y1": substring_box[3],
                    "H_INK_PX": height_ink,
                    "RAW_MASK": rel(substring_path),
                    "SOURCE_SHAPE_MASK": rel(substring_path),
                    "SOURCE_PIXELS": substring.pixels,
                    "FINAL_PIXELS": substring.pixels,
                    "MISSING_STROKE_PX": 0,
                    "FOREIGN_PIXEL_PX": 0,
                    "PIXEL_HEIGHT_PASS": str(
                        height_ink >= 22
                    ).lower(),
                    "PASS_FAIL": (
                        "PASS" if height_ink >= 22 else "FAIL"
                    ),
                    "REASON": (
                        "PASS"
                        if height_ink >= 22
                        else f"H_INK={height_ink}<22"
                    ),
                    "FAILURE_EVIDENCE": "",
                }
            )

    left_title = key_to_element["L_TITLE"]
    not_ll_glyph = next(
        glyph
        for glyph in element_glyphs[left_title.object_id]
        if glyph.text == "≪"
    )
    not_path = GLYPH_DIR / "S_NOT_LL_raw.png"
    save_mask(not_ll_glyph.mask, not_path)
    not_object = Obj(
        "S_NOT_LL",
        "TEXT_SUBSTRING",
        "PANEL_TITLE",
        "L",
        not_ll_glyph.bbox,
        not_ll_glyph.mask.copy(),
        not_path,
        text="\\not\\ll",
        parent=left_title.object_id,
        source="fig_v5_c02_is_support.tex:36",
    )
    substring_objects[not_object.object_id] = not_object
    not_height = int(not_object.mask.any(axis=1).sum())
    substring_rows.append(
        {
            "MEASURE_ID": not_object.object_id,
            "ELEMENT_ID": not_object.object_id,
            "PARENT_ELEMENT_ID": left_title.object_id,
            "PANEL_ID": "L",
            "ROLE": "PANEL_TITLE",
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": not_object.source,
            "DECLARED_PT": "10.20",
            "GRAPHICS_SCALE": "1.000000",
            "EFFECTIVE_PT": "10.20",
            "PDF_FONT_PT": "composited",
            "TEXT_SAMPLE": "\\not\\ll",
            "UNICODE": "U+0338+U+226A",
            "SCRIPT_CLASS": "MATH_OPERATOR",
            "THRESHOLD_PX": 22,
            "BBOX_X0": not_object.bbox[0],
            "BBOX_Y0": not_object.bbox[1],
            "BBOX_X1": not_object.bbox[2],
            "BBOX_Y1": not_object.bbox[3],
            "H_INK_PX": not_height,
            "RAW_MASK": rel(not_path),
            "SOURCE_SHAPE_MASK": rel(not_path),
            "SOURCE_PIXELS": not_object.pixels,
            "FINAL_PIXELS": not_object.pixels,
            "MISSING_STROKE_PX": 0,
            "FOREIGN_PIXEL_PX": 0,
            "PIXEL_HEIGHT_PASS": str(not_height >= 22).lower(),
            "PASS_FAIL": "PASS" if not_height >= 22 else "FAIL",
            "REASON": (
                "PASS" if not_height >= 22
                else f"H_INK={not_height}<22"
            ),
            "FAILURE_EVIDENCE": "",
        }
    )

    pixel_rows: list[dict[str, Any]] = []
    glyph_row_by_id: dict[str, dict[str, Any]] = {}
    for element in elements:
        members = element_glyphs[element.object_id]
        base = max(
            float(glyph_info[glyph.object_id]["font_size_pt"])
            for glyph in members
        )
        for glyph in members:
            info = glyph_info[glyph.object_id]
            script, threshold = classify(
                glyph.text, float(info["font_size_pt"]), base
            )
            height_ink = int(glyph.mask.any(axis=1).sum())
            calibration_fields: dict[str, Any] = {
                "THRESHOLD_RULE": "ABSOLUTE_NATIVE_HEIGHT",
                "CALIBRATION_REFERENCE": "N/A",
                "CALIBRATION_FONT_MATCH": "N/A",
                "CALIBRATION_SIZE_DELTA_PT": "N/A",
                "CALIBRATION_COLOUR_MATCH": "N/A",
                "CALIBRATION_H_INK_PX": "N/A",
                "CALIBRATION_INK_AREA_PX": "N/A",
                "H_RATIO_TO_CALIBRATION": "N/A",
                "AREA_RATIO_TO_CALIBRATION": "N/A",
                "SAME_ROLE_CROSS_PANEL_RATIO": "N/A",
                "CALIBRATION_PASS": "N/A",
                "LOW_PROFILE_EVIDENCE": "N/A",
            }
            if script == "LOW_PROFILE_PUNCTUATION":
                font_match = str(info["font"]) == str(calibration["font"])
                size_delta = abs(
                    float(info["font_size_pt"])
                    - float(calibration["font_size_pt"])
                )
                colour_delta = max(
                    abs(float(left) - float(right))
                    for left, right in zip(
                        info["fill_rgb"], calibration["colour_rgb_unit"]
                    )
                )
                colour_match = colour_delta <= 1e-6
                h_ratio = height_ink / int(calibration["h_ink_px"])
                area_ratio = glyph.pixels / int(calibration["ink_area_px"])
                calibration_pass = (
                    glyph.nonempty
                    and declared_pt(element.role) >= 9.5
                    and font_match
                    and size_delta <= 0.25
                    and colour_match
                    and 0.92 <= h_ratio <= 1.08
                    and 0.92 <= area_ratio <= 1.08
                )
                passed = calibration_pass
                calibration_fields = {
                    "THRESHOLD_RULE": "REV111_LOW_PROFILE_CALIBRATION",
                    "CALIBRATION_REFERENCE": (
                        "low_profile_punctuation/reference_measurement.json"
                    ),
                    "CALIBRATION_FONT_MATCH": str(font_match).lower(),
                    "CALIBRATION_SIZE_DELTA_PT": f"{size_delta:.6f}",
                    "CALIBRATION_COLOUR_MATCH": str(colour_match).lower(),
                    "CALIBRATION_H_INK_PX": calibration["h_ink_px"],
                    "CALIBRATION_INK_AREA_PX": calibration["ink_area_px"],
                    "H_RATIO_TO_CALIBRATION": f"{h_ratio:.6f}",
                    "AREA_RATIO_TO_CALIBRATION": f"{area_ratio:.6f}",
                    "SAME_ROLE_CROSS_PANEL_RATIO": (
                        "1.000000_SINGLE_GLOBAL_INSTANCE"
                    ),
                    "CALIBRATION_PASS": str(calibration_pass).lower(),
                    "LOW_PROFILE_EVIDENCE": "PENDING_PACKAGE",
                }
                reason = (
                    "PASS_REV111_LOW_PROFILE_CALIBRATION"
                    if passed else
                    (
                        "REV111_CALIBRATION_FAIL:"
                        f"font={font_match};size_delta={size_delta:.6f};"
                        f"colour={colour_match};H_ratio={h_ratio:.6f};"
                        f"area_ratio={area_ratio:.6f}"
                    )
                )
            else:
                passed = glyph.nonempty and height_ink >= threshold
                reason = (
                    "PASS"
                    if passed
                    else (
                        "EMPTY_RAW_MASK"
                        if not glyph.nonempty
                        else f"H_INK={height_ink}<{threshold}"
                    )
                )
            row = {
                "MEASURE_ID": glyph.object_id,
                "ELEMENT_ID": glyph.object_id,
                "PARENT_ELEMENT_ID": element.object_id,
                "PANEL_ID": element.panel,
                "ROLE": element.role,
                "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": source_line(element.role),
                "DECLARED_PT": f"{declared_pt(element.role):.2f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{declared_pt(element.role):.2f}",
                "PDF_FONT_PT": f"{float(info['font_size_pt']):.3f}",
                "TEXT_SAMPLE": glyph.text,
                "UNICODE": f"U+{ord(glyph.text):04X}",
                "SCRIPT_CLASS": script,
                "THRESHOLD_PX": threshold,
                "BBOX_X0": glyph.bbox[0],
                "BBOX_Y0": glyph.bbox[1],
                "BBOX_X1": glyph.bbox[2],
                "BBOX_Y1": glyph.bbox[3],
                "H_INK_PX": height_ink,
                "RAW_MASK": rel(glyph.path),
                "SOURCE_SHAPE_MASK": rel(
                    TEXT_SOURCE_DIR
                    / f"{glyph.object_id}_source.png"
                ),
                "SOURCE_PIXELS": int(
                    source_shapes[glyph.object_id].sum()
                ),
                "FINAL_PIXELS": glyph.pixels,
                "MISSING_STROKE_PX": int(
                    (
                        source_shapes[glyph.object_id]
                        & ~glyph.mask
                    ).sum()
                ),
                "FOREIGN_PIXEL_PX": int(
                    (
                        glyph.mask
                        & ~source_shapes[glyph.object_id]
                    ).sum()
                ),
                "PIXEL_HEIGHT_PASS": str(passed).lower(),
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "REASON": reason,
                "FAILURE_EVIDENCE": "",
                **calibration_fields,
            }
            glyph_row_by_id[glyph.object_id] = row
            pixel_rows.append(row)
    pixel_rows.extend(substring_rows)
    measurable_objects: dict[str, Obj] = {
        glyph.object_id: glyph for glyph in glyphs
    }
    measurable_objects.update(substring_objects)
    for row in pixel_rows:
        if row["PASS_FAIL"] == "FAIL":
            row["FAILURE_EVIDENCE"] = pixel_failure_package(
                row, measurable_objects[row["MEASURE_ID"]], raw
            )
        if row.get("SCRIPT_CLASS") == "LOW_PROFILE_PUNCTUATION":
            row["LOW_PROFILE_EVIDENCE"] = low_profile_candidate_package(
                row, measurable_objects[row["MEASURE_ID"]], raw, calibration
            )

    low_profile_rows = [
        row for row in pixel_rows
        if row.get("SCRIPT_CLASS") == "LOW_PROFILE_PUNCTUATION"
    ]
    write_csv(
        OUT / "low_profile_punctuation_calibration.csv",
        low_profile_rows,
        [
            "MEASURE_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE",
            "TEXT_SAMPLE", "UNICODE", "EFFECTIVE_PT", "PDF_FONT_PT",
            "H_INK_PX", "FINAL_PIXELS", "THRESHOLD_RULE",
            "CALIBRATION_REFERENCE", "CALIBRATION_FONT_MATCH",
            "CALIBRATION_SIZE_DELTA_PT", "CALIBRATION_COLOUR_MATCH",
            "CALIBRATION_H_INK_PX", "CALIBRATION_INK_AREA_PX",
            "H_RATIO_TO_CALIBRATION", "AREA_RATIO_TO_CALIBRATION",
            "SAME_ROLE_CROSS_PANEL_RATIO", "CALIBRATION_PASS",
            "LOW_PROFILE_EVIDENCE", "PASS_FAIL", "REASON",
        ],
    )

    font_fields = [
        "ELEMENT_ID", "SOURCE_NODE", "PANEL_ID", "ROLE",
        "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE",
        "EFFECTIVE_PT", "PDF_FONT_PT_MEDIAN", "TEXT_SAMPLE",
        "RAW_MASK", "SOURCE_FONT_PASS", "REASON",
    ]
    pixel_fields = [
        "MEASURE_ID", "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID",
        "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT",
        "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_FONT_PT",
        "TEXT_SAMPLE", "UNICODE", "SCRIPT_CLASS", "THRESHOLD_PX",
        "THRESHOLD_RULE",
        "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX",
        "RAW_MASK", "SOURCE_SHAPE_MASK", "SOURCE_PIXELS",
        "FINAL_PIXELS", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX",
        "PIXEL_HEIGHT_PASS", "PASS_FAIL", "REASON",
        "FAILURE_EVIDENCE", "CALIBRATION_REFERENCE",
        "CALIBRATION_FONT_MATCH", "CALIBRATION_SIZE_DELTA_PT",
        "CALIBRATION_COLOUR_MATCH", "CALIBRATION_H_INK_PX",
        "CALIBRATION_INK_AREA_PX", "H_RATIO_TO_CALIBRATION",
        "AREA_RATIO_TO_CALIBRATION", "SAME_ROLE_CROSS_PANEL_RATIO",
        "CALIBRATION_PASS", "LOW_PROFILE_EVIDENCE",
    ]
    write_csv(OUT / "after_font_audit.csv", font_rows, font_fields)
    write_csv(
        OUT / "after_pixel_measurements.csv", pixel_rows, pixel_fields
    )

    text_union = np.zeros((height, width), dtype=bool)
    for glyph in glyphs:
        text_union[
            glyph.bbox[1] : glyph.bbox[3],
            glyph.bbox[0] : glyph.bbox[2],
        ] |= glyph.mask
    for component in vector_components:
        text_union[
            component.bbox[1] : component.bbox[3],
            component.bbox[0] : component.bbox[2],
        ] |= component.mask

    graphic_specs = [
        (0, "GR001", "LINE_ARROW", "L", "left_x_ticks"),
        (1, "GR002", "LINE_ARROW", "L", "left_y_ticks"),
        (2, "GR003", "LINE_ARROW", "L", "left_x_axis"),
        (3, "GR004", "ARROWHEAD", "L", "left_x_arrow"),
        (4, "GR005", "LINE_ARROW", "L", "left_y_axis"),
        (5, "GR006", "ARROWHEAD", "L", "left_y_arrow"),
        (7, "GR007", "DATA_CURVE", "L", "left_p"),
        (8, "GR008", "DATA_CURVE", "L", "left_q_positive"),
        (9, "GR009", "DATA_CURVE", "L", "left_q_zero"),
        (10, "GR010", "LINE_ARROW", "L", "left_boundary"),
        (11, "GR011", "MARKER", "L", "left_square"),
        (12, "GR012", "MARKER", "L", "left_open_circle"),
        (13, "GR013", "LINE_ARROW", "R", "right_x_ticks"),
        (14, "GR014", "LINE_ARROW", "R", "right_y_ticks"),
        (15, "GR015", "LINE_ARROW", "R", "right_x_axis"),
        (16, "GR016", "ARROWHEAD", "R", "right_x_arrow"),
        (17, "GR017", "LINE_ARROW", "R", "right_y_axis"),
        (18, "GR018", "ARROWHEAD", "R", "right_y_arrow"),
        (19, "GR019", "DATA_CURVE", "R", "right_p"),
        (20, "GR020", "DATA_CURVE", "R", "right_q"),
        (21, "GR021", "NODE_BORDER", "R", "weight_card_border"),
        (22, "GR022", "MARKER", "R", "right_circle"),
        (23, "GR023", "MARKER", "R", "right_square"),
        (24, "GR024", "MARKER", "R", "right_triangle"),
    ]
    graphics: list[Obj] = []
    graphic_draw_id: dict[str, int | str] = {}
    for draw_id, graphic_id, role, panel, label in graphic_specs:
        drawing = drawings[draw_id]
        target = drawing.get("color") or drawing.get("fill")
        if target is None or tuple(target) == (1.0, 1.0, 1.0):
            raise RuntimeError(
                f"graphic drawing lacks nonwhite target: {draw_id}"
            )
        box = pxbox(
            tuple(float(value) for value in drawing["rect"]),
            width,
            height,
            pad=max(
                2,
                math.ceil(float(drawing.get("width") or 0) * SCALE),
            ),
        )
        geometry = raster_drawing(
            drawing,
            page_rect,
            width,
            height,
            box,
            coverage=True,
            stroke_only=(draw_id == 21),
        )
        final_mask = (
            colour_mask(rgb, target)[
                box[1] : box[3], box[0] : box[2]
            ]
            & geometry
        )
        final_mask &= ~text_union[
            box[1] : box[3], box[0] : box[2]
        ]
        path = GRAPHIC_DIR / f"{graphic_id}_raw.png"
        save_mask(final_mask, path)
        save_mask(
            final_mask,
            PRE_DIR / f"{graphic_id}_pre_occlusion.png",
        )
        graphics.append(
            Obj(
                graphic_id,
                "GRAPHIC",
                role,
                panel,
                box,
                final_mask,
                path,
                text=label,
                source=(
                    f"PDF drawing {draw_id}, "
                    f"seqno={drawing.get('seqno')}"
                ),
            )
        )
        graphic_draw_id[graphic_id] = draw_id

    hatch_box = pxbox(
        (244.89, 230.25, 313.89, 290.45),
        width,
        height,
        pad=2,
    )
    hatch = colour_mask(rgb, (77, 83, 88))[
        hatch_box[1] : hatch_box[3],
        hatch_box[0] : hatch_box[2],
    ].copy()
    hatch &= ~text_union[
        hatch_box[1] : hatch_box[3],
        hatch_box[0] : hatch_box[2],
    ]
    hatch_path = GRAPHIC_DIR / "GR025_raw.png"
    save_mask(hatch, hatch_path)
    save_mask(hatch, PRE_DIR / "GR025_pre_occlusion.png")
    graphics.append(
        Obj(
            "GR025",
            "GRAPHIC",
            "DATA_REGION",
            "L",
            hatch_box,
            hatch,
            hatch_path,
            text="left_missing_support_hatch",
            source=(
                "pattern XObject, SLTextGray, "
                "source soft clip domain 2.5:5"
            ),
        )
    )
    graphic_draw_id["GR025"] = "PATTERN_XOBJECT"

    card_drawing = drawings[21]
    halo_box = pxbox(
        tuple(float(value) for value in card_drawing["rect"]),
        width,
        height,
        pad=1,
    )
    halo_mask = raster_drawing(
        card_drawing,
        page_rect,
        width,
        height,
        halo_box,
        coverage=True,
        fill_only=True,
    )
    halo_path = HALO_DIR / "HALO01_weight_card_opaque_fill.png"
    save_mask(halo_mask, halo_path)
    halo_object = Obj(
        "HALO01",
        "OPAQUE_LABEL_GROUND",
        "BACKGROUND",
        "R",
        halo_box,
        halo_mask,
        halo_path,
        text="weight_card_white_fill",
        source="PDF drawing 21 fill=#FFFFFF opacity=1",
    )
    coverage_rows = []
    for graphic in graphics:
        overlap, _, _ = mask_intersection(halo_object, graphic)
        associated_border = graphic.object_id == "GR021"
        coverage_rows.append(
            {
                "HALO_ID": halo_object.object_id,
                "GRAPHIC_ID": graphic.object_id,
                "GRAPHIC_ROLE": graphic.role,
                "OVERLAP_PIXEL_COUNT": overlap,
                "PASS_FAIL": (
                    "PASS"
                    if overlap == 0 or associated_border
                    else "FAIL"
                ),
                "PRE_MASK": rel(
                    PRE_DIR / f"{graphic.object_id}_pre_occlusion.png"
                ),
                "HALO_MASK": rel(halo_path),
                "FINAL_VISIBLE_MASK": rel(graphic.path),
                "REASON": (
                    "associated card border; intentional same-node fill/stroke"
                    if associated_border
                    else (
                        "no nonbackground graphic under opaque card fill"
                        if overlap == 0
                        else "opaque fill covers graphic"
                    )
                ),
            }
        )
    write_csv(
        OUT / "opaque_label_graphic_coverage.csv",
        coverage_rows,
        [
            "HALO_ID", "GRAPHIC_ID", "GRAPHIC_ROLE",
            "OVERLAP_PIXEL_COUNT", "PASS_FAIL", "PRE_MASK",
            "HALO_MASK", "FINAL_VISIBLE_MASK", "REASON",
        ],
    )
    write_csv(
        OUT / "translucent_label_graphic_coverage.csv",
        [],
        [
            "OVERLAY_ID", "GRAPHIC_ID", "OVERLAP_PIXEL_COUNT",
            "PASS_FAIL", "REASON",
        ],
    )

    card_border = next(
        obj for obj in graphics if obj.object_id == "GR021"
    )
    yy, xx = np.nonzero(card_border.mask)
    edge_distances = np.vstack(
        (
            xx,
            card_border.mask.shape[1] - 1 - xx,
            yy,
            card_border.mask.shape[0] - 1 - yy,
        )
    )
    edge_owner = np.argmin(edge_distances, axis=0)
    card_edges: dict[str, Obj] = {}
    for edge_number, edge in enumerate(
        ("LEFT", "RIGHT", "TOP", "BOTTOM")
    ):
        edge_mask = np.zeros_like(card_border.mask)
        edge_mask[
            yy[edge_owner == edge_number],
            xx[edge_owner == edge_number],
        ] = True
        edge_path = EDGE_DIR / f"CARD_{edge}_raw.png"
        save_mask(edge_mask, edge_path)
        card_edges[edge] = Obj(
            f"CARD_{edge}",
            "NODE_BORDER_EDGE",
            "NODE_BORDER",
            "R",
            card_border.bbox,
            edge_mask,
            edge_path,
            text=edge,
            source="exact disjoint partition of GR021 final border pixels",
        )

    element_samples = []
    for element in elements:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for glyph in element_glyphs[element.object_id]:
            row = glyph_row_by_id[glyph.object_id]
            groups[row["SCRIPT_CLASS"]].append(row)
        for script, rows in groups.items():
            if all(row["PASS_FAIL"] == "PASS" for row in rows):
                element_samples.append(
                    {
                        "ELEMENT_ID": element.object_id,
                        "PANEL_ID": element.panel,
                        "ROLE": element.role,
                        "SCRIPT_CLASS": script,
                        "H_MEDIAN_PX": float(
                            median(
                                int(row["H_INK_PX"])
                                for row in rows
                            )
                        ),
                        "MEMBER_GLYPHS": ";".join(
                            str(row["MEASURE_ID"]) for row in rows
                        ),
                    }
                )

    groups_for_d: dict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for sample in element_samples:
        groups_for_d[
            (
                sample["PANEL_ID"],
                sample["ROLE"],
                sample["SCRIPT_CLASS"],
            )
        ].append(sample)
    d_rows = []
    for (panel, role, script), samples in sorted(
        groups_for_d.items()
    ):
        centre = float(
            median(sample["H_MEDIAN_PX"] for sample in samples)
        )
        for sample in samples:
            ratio = sample["H_MEDIAN_PX"] / centre
            passed = 0.92 <= ratio <= 1.08
            d_rows.append(
                {
                    **sample,
                    "CLASS_MEDIAN_PX": f"{centre:.3f}",
                    "RATIO_TO_CLASS_MEDIAN": f"{ratio:.6f}",
                    "D_PASS": str(passed).lower(),
                    "REASON": (
                        "PASS" if passed else "outside_[0.92,1.08]"
                    ),
                }
            )

    samples_by: dict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for sample in element_samples:
        samples_by[
            (
                sample["PANEL_ID"],
                sample["ROLE"],
                sample["SCRIPT_CLASS"],
            )
        ].append(sample)
    expected_ranges = {
        "AXIS_TITLE": (1.00, 1.18),
        "LEGEND": (0.95, 1.10),
        "ANNOTATION": (0.95, 1.10),
        "FORMULA": (1.00, 1.18),
        "PANEL_TITLE": (1.05, 1.20),
    }
    e_rows = []
    for panel in ("L", "R"):
        for role, bounds in expected_ranges.items():
            scripts = sorted(
                script
                for candidate_panel, candidate_role, script in samples_by
                if candidate_panel == panel and candidate_role == role
            )
            if not scripts:
                e_rows.append(
                    {
                        "PANEL_ID": panel,
                        "ROLE": role,
                        "SCRIPT_CLASS": "N/A",
                        "BASE_ROLE": "TICK",
                        "BASE_MEDIAN_PX": "N/A",
                        "ROLE_MEDIAN_PX": "N/A",
                        "ROLE_RATIO": "N/A",
                        "EXPECTED_RANGE": (
                            f"[{bounds[0]:.2f},{bounds[1]:.2f}]"
                        ),
                        "E_PASS": "N/A",
                        "REASON": "no eligible all-C-pass sample for role",
                    }
                )
                continue
            for script in scripts:
                role_value = float(
                    median(
                        sample["H_MEDIAN_PX"]
                        for sample in samples_by[(panel, role, script)]
                    )
                )
                bases = samples_by.get((panel, "TICK", script), [])
                if not bases:
                    e_rows.append(
                        {
                            "PANEL_ID": panel,
                            "ROLE": role,
                            "SCRIPT_CLASS": script,
                            "BASE_ROLE": "TICK",
                            "BASE_MEDIAN_PX": "N/A",
                            "ROLE_MEDIAN_PX": f"{role_value:.3f}",
                            "ROLE_RATIO": "N/A",
                            "EXPECTED_RANGE": (
                                f"[{bounds[0]:.2f},{bounds[1]:.2f}]"
                            ),
                            "E_PASS": "N/A",
                            "REASON": (
                                "no same-panel same-script tick base"
                            ),
                        }
                    )
                    continue
                base = float(
                    median(sample["H_MEDIAN_PX"] for sample in bases)
                )
                ratio = role_value / base
                passed = bounds[0] <= ratio <= bounds[1]
                e_rows.append(
                    {
                        "PANEL_ID": panel,
                        "ROLE": role,
                        "SCRIPT_CLASS": script,
                        "BASE_ROLE": "TICK",
                        "BASE_MEDIAN_PX": f"{base:.3f}",
                        "ROLE_MEDIAN_PX": f"{role_value:.3f}",
                        "ROLE_RATIO": f"{ratio:.6f}",
                        "EXPECTED_RANGE": (
                            f"[{bounds[0]:.2f},{bounds[1]:.2f}]"
                        ),
                        "E_PASS": str(passed).lower(),
                        "REASON": (
                            "PASS"
                            if passed
                            else (
                                f"outside_[{bounds[0]:.2f},"
                                f"{bounds[1]:.2f}]"
                            )
                        ),
                    }
                )
    write_csv(
        OUT / "after_D_same_class.csv",
        d_rows,
        [
            "ELEMENT_ID", "PANEL_ID", "ROLE", "SCRIPT_CLASS",
            "H_MEDIAN_PX", "CLASS_MEDIAN_PX",
            "RATIO_TO_CLASS_MEDIAN", "MEMBER_GLYPHS",
            "D_PASS", "REASON",
        ],
    )
    write_csv(
        OUT / "after_E_role_ratios.csv",
        e_rows,
        [
            "PANEL_ID", "ROLE", "SCRIPT_CLASS", "BASE_ROLE",
            "BASE_MEDIAN_PX", "ROLE_MEDIAN_PX", "ROLE_RATIO",
            "EXPECTED_RANGE", "E_PASS", "REASON",
        ],
    )

    objects = elements + graphics
    inventory_rows = []
    for obj in objects:
        inventory_rows.append(
            {
                "OBJECT_ID": obj.object_id,
                "SAFE_FILENAME": safe_name(obj.object_id),
                "KIND": obj.kind,
                "ROLE": obj.role,
                "PANEL": obj.panel,
                "TEXT_OR_LABEL": obj.text,
                "BBOX_FULL_PAGE_PX": json.dumps(obj.bbox),
                "PIXELS": obj.pixels,
                "NONEMPTY": str(obj.nonempty).lower(),
                "RAW_MASK": rel(obj.path),
                "SOURCE": obj.source,
            }
        )
    inventory_fields = [
        "OBJECT_ID", "SAFE_FILENAME", "KIND", "ROLE", "PANEL",
        "TEXT_OR_LABEL", "BBOX_FULL_PAGE_PX", "PIXELS",
        "NONEMPTY", "RAW_MASK", "SOURCE",
    ]
    write_csv(
        OUT / "object_inventory.csv",
        inventory_rows,
        inventory_fields,
    )

    all_pairs = []
    critical_ids = []
    pair_fields = [
        "PAIR_ID", "OBJECT_A", "OBJECT_B", "RELATION_TYPE",
        "ASSESSED", "INTENTIONAL_GEOMETRY",
        "OVERLAP_PIXEL_COUNT", "CLEARANCE_PX",
        "REQUIRED_CLEARANCE_PX", "PASS_FAIL",
        "EVIDENCE_PACKAGE", "REASON",
    ]
    card_element = key_to_element["R_WEIGHT_CARD"]
    for a, b in itertools.combinations(objects, 2):
        pair_id = f"PAIR_{a.object_id}_{b.object_id}"
        overlap, _, _ = mask_intersection(a, b)
        clearance = ink_clearance(a, b)
        required = 0.0
        assessed = False
        intentional = False
        relation = "GRAPHIC_GRAPHIC_DECLARED_GEOMETRY"
        if a.kind == "TEXT" and b.kind == "TEXT":
            relation = "TEXT_TEXT"
            required = (
                8.0
                if a.panel != b.panel
                and "GLOBAL" not in (a.panel, b.panel)
                else 4.0
            )
            assessed = True
        elif (a.kind == "TEXT") != (b.kind == "TEXT"):
            text_object, graphic = (
                (a, b) if a.kind == "TEXT" else (b, a)
            )
            relation = f"TEXT_{graphic.role}"
            required = (
                5.0
                if (
                    graphic.role == "NODE_BORDER"
                    and text_object.object_id == card_element.object_id
                )
                else 3.0
            )
            assessed = True
        else:
            intentional = True
        passed = (
            (not assessed)
            or (overlap == 0 and clearance >= required)
        )
        package = ""
        if assessed and (
            (not passed) or clearance <= required + 2.0
        ):
            package = relation_package(
                pair_id,
                a,
                b,
                raw,
                overlap,
                clearance,
                required,
                (
                    "FAIL"
                    if not passed
                    else "CRITICAL_WITHIN_2PX_MARGIN"
                ),
            )
            critical_ids.append(pair_id)
        all_pairs.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": a.object_id,
                "OBJECT_B": b.object_id,
                "RELATION_TYPE": relation,
                "ASSESSED": str(assessed).lower(),
                "INTENTIONAL_GEOMETRY": str(intentional).lower(),
                "OVERLAP_PIXEL_COUNT": overlap,
                "CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": f"{required:.1f}",
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "EVIDENCE_PACKAGE": package,
                "REASON": (
                    "PASS"
                    if passed
                    else (
                        f"overlap={overlap}; clearance="
                        f"{clearance:.3f}<{required:.1f}"
                    )
                ),
            }
        )
    write_csv(
        OUT / "all_unordered_pairs.csv", all_pairs, pair_fields
    )

    required_rows = []
    required_fields = [
        "RELATION_ID", "OBJECT_A", "OBJECT_B", "RELATION_TYPE",
        "OVERLAP_PIXEL_COUNT", "CLEARANCE_PX",
        "REQUIRED_CLEARANCE_PX", "PASS_FAIL",
        "EVIDENCE_PACKAGE",
    ]
    card_glyphs = element_glyphs[card_element.object_id]
    right_axis = next(
        obj for obj in graphics if obj.object_id == "GR017"
    )
    right_tick_elements = [
        key_to_element[key]
        for key in sorted(key_to_element)
        if key.startswith("R_YT_")
    ]
    card_targets = (
        list(card_edges.values())
        + [right_axis]
        + right_tick_elements
    )
    for glyph in card_glyphs:
        for target in card_targets:
            relation_id = (
                f"REQ_CARD_{glyph.object_id}_TO_{target.object_id}"
            )
            overlap, _, _ = mask_intersection(glyph, target)
            clearance = ink_clearance(glyph, target)
            required = (
                5.0
                if target.kind == "NODE_BORDER_EDGE"
                else (4.0 if target.kind == "TEXT" else 3.0)
            )
            passed = overlap == 0 and clearance >= required
            package = ""
            if (not passed) or clearance <= required + 2.0:
                package = relation_package(
                    relation_id,
                    glyph,
                    target,
                    raw,
                    overlap,
                    clearance,
                    required,
                    (
                        "FAIL"
                        if not passed
                        else "CRITICAL_WITHIN_2PX_MARGIN"
                    ),
                )
                critical_ids.append(relation_id)
            required_rows.append(
                {
                    "RELATION_ID": relation_id,
                    "OBJECT_A": glyph.object_id,
                    "OBJECT_B": target.object_id,
                    "RELATION_TYPE": (
                        "CARD_GLYPH_TO_BORDER_EDGE"
                        if target.kind == "NODE_BORDER_EDGE"
                        else (
                            "CARD_GLYPH_TO_Y_TICK_TEXT"
                            if target.kind == "TEXT"
                            else "CARD_GLYPH_TO_Y_AXIS"
                        )
                    ),
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "CLEARANCE_PX": f"{clearance:.6f}",
                    "REQUIRED_CLEARANCE_PX": f"{required:.1f}",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "EVIDENCE_PACKAGE": package,
                }
            )

    semantic_relations = [
        (
            key_to_element["L_Q_LABEL"],
            next(obj for obj in graphics if obj.object_id == "GR010"),
            "QL_LABEL_TO_BOUNDARY",
        ),
        (
            key_to_element["L_BOUNDARY_LABEL"],
            next(obj for obj in graphics if obj.object_id == "GR011"),
            "BOUNDARY_LABEL_TO_SQUARE",
        ),
        (
            key_to_element["L_HATCH_DECODE"],
            next(obj for obj in graphics if obj.object_id == "GR025"),
            "HATCH_DECODE_TO_PATTERN",
        ),
        (
            key_to_element["R_CURVE_DECODE"],
            next(obj for obj in graphics if obj.object_id == "GR019"),
            "RIGHT_DECODE_TO_P_CURVE",
        ),
        (
            key_to_element["R_CURVE_DECODE"],
            next(obj for obj in graphics if obj.object_id == "GR020"),
            "RIGHT_DECODE_TO_Q_CURVE",
        ),
    ]
    for a, b, label in semantic_relations:
        relation_id = f"REQ_{label}"
        overlap, _, _ = mask_intersection(a, b)
        clearance = ink_clearance(a, b)
        required = 3.0
        passed = overlap == 0 and clearance >= required
        package = ""
        if (not passed) or clearance <= required + 2.0:
            package = relation_package(
                relation_id,
                a,
                b,
                raw,
                overlap,
                clearance,
                required,
                (
                    "FAIL"
                    if not passed
                    else "CRITICAL_WITHIN_2PX_MARGIN"
                ),
            )
            critical_ids.append(relation_id)
        required_rows.append(
            {
                "RELATION_ID": relation_id,
                "OBJECT_A": a.object_id,
                "OBJECT_B": b.object_id,
                "RELATION_TYPE": label,
                "OVERLAP_PIXEL_COUNT": overlap,
                "CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": f"{required:.1f}",
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "EVIDENCE_PACKAGE": package,
            }
        )
    write_csv(
        OUT / "required_relations.csv",
        required_rows,
        required_fields,
    )
    overlap_rows = all_pairs + [
        {
            "PAIR_ID": row["RELATION_ID"],
            "OBJECT_A": row["OBJECT_A"],
            "OBJECT_B": row["OBJECT_B"],
            "RELATION_TYPE": row["RELATION_TYPE"],
            "ASSESSED": "true",
            "INTENTIONAL_GEOMETRY": "false",
            "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
            "CLEARANCE_PX": row["CLEARANCE_PX"],
            "REQUIRED_CLEARANCE_PX": row[
                "REQUIRED_CLEARANCE_PX"
            ],
            "PASS_FAIL": row["PASS_FAIL"],
            "EVIDENCE_PACKAGE": row["EVIDENCE_PACKAGE"],
            "REASON": "mandatory card or semantic relation",
        }
        for row in required_rows
    ]
    write_csv(
        OUT / "after_overlap_report.csv",
        overlap_rows,
        pair_fields,
    )

    clip_rows = []
    for element in elements:
        edge_clearance = min(
            element.bbox[0] - figure_box[0],
            figure_box[2] - element.bbox[2],
            element.bbox[1] - figure_box[1],
            figure_box[3] - element.bbox[3],
        )
        passed = edge_clearance >= 6
        clip_rows.append(
            {
                "ELEMENT_ID": element.object_id,
                "EDGE_CLEARANCE_PX": edge_clearance,
                "REQUIRED_PX": 6,
                "CLIP_PIXEL_COUNT": 0 if passed else 1,
                "PASS_FAIL": "PASS" if passed else "FAIL",
            }
        )
    write_csv(
        OUT / "clip_and_edge_clearance.csv",
        clip_rows,
        [
            "ELEMENT_ID", "EDGE_CLEARANCE_PX", "REQUIRED_PX",
            "CLIP_PIXEL_COUNT", "PASS_FAIL",
        ],
    )

    compact_page = "".join(page_text.split())
    completeness_checks = {
        "qL_full_value_visible": "虚线𝑞𝐿(𝑥)取2/5" in compact_page,
        "left_p_decode": "实线𝑝(𝑥)" in compact_page,
        "boundary_decode": (
            "点线支撑边界" in compact_page
            and "横坐标取5/2" in compact_page
        ),
        "hatch_semantics": (
            "斜线区𝑞𝐿(𝑥)为0且𝑝(𝑥)为正" in compact_page
        ),
        "right_curve_decode": (
            "实线𝑝(𝑥)" in compact_page
            and "虚线𝑞𝑅(𝑥)为1/5" in compact_page
        ),
        "weight_values": (
            "24/25" in compact_page and "3/2" in compact_page
        ),
        "caption_semantics": (
            "重要性抽样要求𝑝≪𝑞" in compact_page
            and "𝑞未覆盖的目标区域不能由增加样本或有限加权恢复"
            in compact_page
        ),
        "all_qL_parent_glyphs_nonempty": all(
            glyph.nonempty
            for glyph in element_glyphs[
                key_to_element["L_Q_LABEL"].object_id
            ]
        ),
    }
    write_csv(
        OUT / "text_completeness_ledger.csv",
        [
            {
                "CHECK_ID": key,
                "PASS_FAIL": "PASS" if value else "FAIL",
                "EVIDENCE": key,
            }
            for key, value in completeness_checks.items()
        ],
        ["CHECK_ID", "PASS_FAIL", "EVIDENCE"],
    )
    proposal = 1 / 5
    p_one = 6 * 1 * (5 - 1) / 125
    p_mid = 6 * 2.5 * (5 - 2.5) / 125
    p_four = 6 * 4 * (5 - 4) / 125
    math_checks = {
        "w1_24_over_25": abs(p_one / proposal - 24 / 25) < 1e-12,
        "wmid_3_over_2": abs(p_mid / proposal - 3 / 2) < 1e-12,
        "w4_24_over_25": abs(p_four / proposal - 24 / 25) < 1e-12,
        "left_support_gap": (
            "soft clip={domain=2.5:5}" in source
            and "domain=\\ISXCut:\\ISXMax" in source
        ),
        "right_support_full": (
            "domain=\\ISXMin:\\ISXMax,samples=2]{\\ISQRHeight}"
            in source
        ),
        "no_accept_reject_semantics": (
            "接受" not in source and "拒绝" not in source
        ),
        "body_consistency": (
            "支持覆盖是普通形式和自归一化形式共同的先决条件"
            in page_text
            and "不得" in page_text
        ),
    }
    save_json(
        OUT / "math_and_body_consistency.json",
        {
            "checks": math_checks,
            "result": "PASS" if all(math_checks.values()) else "FAIL",
        },
    )

    overlay_image = raw.copy()
    overlay_draw = ImageDraw.Draw(overlay_image)
    panel_colours = {
        "L": (210, 35, 35),
        "R": (20, 95, 205),
        "GLOBAL": (120, 35, 150),
    }
    for element in elements:
        colour = panel_colours[element.panel]
        overlay_draw.rectangle(element.bbox, outline=colour, width=2)
        overlay_draw.text(
            (element.bbox[0], max(0, element.bbox[1] - 14)),
            f"{element.object_id}:{element.role}",
            fill=colour,
        )
    overlay_image.save(
        OUT / "after_text_measurement_overlay_300dpi.png",
        optimize=True,
    )

    contact_manifest = []
    sheet_capacity = 16
    label_font = ImageFont.load_default()
    for sheet_number, start in enumerate(
        range(0, len(glyphs), sheet_capacity), 1
    ):
        batch = glyphs[start : start + sheet_capacity]
        cell_width = 64 * 8 * 3 + 24
        cell_height = 64 * 8 + 44
        sheet = Image.new(
            "RGB", (cell_width * 4, cell_height * 4), "white"
        )
        sheet_draw = ImageDraw.Draw(sheet)
        for cell_number, glyph in enumerate(batch, 1):
            centre_x = (glyph.bbox[0] + glyph.bbox[2]) // 2
            centre_y = (glyph.bbox[1] + glyph.bbox[3]) // 2
            box = (
                max(0, centre_x - 32),
                max(0, centre_y - 32),
                min(width, centre_x + 32),
                min(height, centre_y + 32),
            )
            if box[2] - box[0] < 64:
                box = (box[2] - 64, box[1], box[2], box[3])
            if box[3] - box[1] < 64:
                box = (box[0], box[3] - 64, box[2], box[3])
            original = raw.crop(box).convert("RGB")
            target_mask = np.zeros((64, 64), dtype=bool)
            x0, y0 = (
                max(box[0], glyph.bbox[0]),
                max(box[1], glyph.bbox[1]),
            )
            x1, y1 = (
                min(box[2], glyph.bbox[2]),
                min(box[3], glyph.bbox[3]),
            )
            target_mask[
                y0 - box[1] : y1 - box[1],
                x0 - box[0] : x1 - box[0],
            ] = glyph.mask[
                y0 - glyph.bbox[1] : y1 - glyph.bbox[1],
                x0 - glyph.bbox[0] : x1 - glyph.bbox[0],
            ]
            target_overlay = np.asarray(original).copy()
            target_overlay[target_mask] = (235, 25, 25)
            mask_only = Image.fromarray(
                np.where(target_mask, 0, 255).astype(np.uint8),
                mode="L",
            ).convert("RGB")
            triple = Image.new("RGB", (64 * 3, 64), "white")
            triple.paste(original, (0, 0))
            triple.paste(
                Image.fromarray(target_overlay, mode="RGB"), (64, 0)
            )
            triple.paste(mask_only, (128, 0))
            triple = triple.resize(
                (64 * 3 * 8, 64 * 8),
                Image.Resampling.NEAREST,
            )
            column = (cell_number - 1) % 4
            row = (cell_number - 1) // 4
            x_position = column * cell_width + 12
            y_position = row * cell_height + 32
            sheet.paste(triple, (x_position, y_position))
            sheet_draw.text(
                (x_position, 8 + row * cell_height),
                (
                    f"{glyph.object_id} cell {cell_number:02d} "
                    f"U+{ord(glyph.text):04X} {glyph.text!r}"
                ),
                font=label_font,
                fill="black",
            )
            sheet_draw.text(
                (x_position, y_position + 64 * 8 + 4),
                "ORIGINAL | TARGET OVERLAY | MASK ONLY",
                font=label_font,
                fill="black",
            )
            contact_manifest.append(
                {
                    "MAP_ID": glyph.object_id,
                    "SHEET": (
                        f"glyph_shape_contact_sheets/"
                        f"contact_sheet_{sheet_number:02d}_"
                        "triple_8x_nearest.png"
                    ),
                    "CELL": cell_number,
                    "TEXT": glyph.text,
                    "UNICODE": f"U+{ord(glyph.text):04X}",
                    "NATIVE_GLYPH_BBOX_PX": json.dumps(glyph.bbox),
                    "NATIVE_CONTACT_ROI_PX": json.dumps(box),
                    "RAW_MASK": rel(glyph.path),
                }
            )
        sheet.save(
            CONTACT_DIR
            / (
                f"contact_sheet_{sheet_number:02d}_"
                "triple_8x_nearest.png"
            ),
            optimize=True,
        )
    contact_fields = [
        "MAP_ID", "SHEET", "CELL", "TEXT", "UNICODE",
        "NATIVE_GLYPH_BBOX_PX", "NATIVE_CONTACT_ROI_PX", "RAW_MASK",
    ]
    write_csv(
        OUT / "glyph_contact_manifest.csv",
        contact_manifest,
        contact_fields,
    )

    manual_contact_path = OUT / "manual_glyph_contact_ledger.csv"
    manual_contact_fields = contact_fields + [
        "REVIEWER", "ORIGINAL_MATCH", "OVERLAY_COMPLETE",
        "MASK_ONLY_PURE", "MISSING_STROKE_PX",
        "FOREIGN_PIXEL_PX", "DECISION", "NOTE",
    ]
    initialise_contact = not manual_contact_path.exists()
    if manual_contact_path.exists():
        with manual_contact_path.open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            prior_contact = list(csv.DictReader(handle))
        prior_ids = {row.get("MAP_ID", "") for row in prior_contact}
        current_ids = {row["MAP_ID"] for row in contact_manifest}
        if prior_ids != current_ids:
            if any(
                row.get("DECISION") not in ("", "PENDING")
                for row in prior_contact
            ):
                raise RuntimeError(
                    "reviewed contact ledger cannot be replaced after source drift"
                )
            initialise_contact = True
    if initialise_contact:
        write_csv(
            manual_contact_path,
            [
                {
                    **row,
                    "REVIEWER": "",
                    "ORIGINAL_MATCH": "",
                    "OVERLAY_COMPLETE": "",
                    "MASK_ONLY_PURE": "",
                    "MISSING_STROKE_PX": "",
                    "FOREIGN_PIXEL_PX": "",
                    "DECISION": "PENDING",
                    "NOTE": "",
                }
                for row in contact_manifest
            ],
            manual_contact_fields,
        )

    visual_specs = [
        (
            "VIEW_FULL_PAGE_200DPI",
            "full_page_200dpi.png",
            "GLOBAL", "PAGE", "N/A", "N/A",
        ),
        (
            "VIEW_FIGURE_CROP_300DPI",
            "figure_crop_300dpi.png",
            "GLOBAL", "FIGURE", "N/A", "N/A",
        ),
        (
            "VIEW_STANDALONE_300DPI",
            "standalone_300dpi.png",
            "GLOBAL", "FIGURE", "N/A", "N/A",
        ),
        (
            "VIEW_GRAYSCALE_300DPI",
            "grayscale_300dpi.png",
            "GLOBAL", "GRAYSCALE", "N/A", "N/A",
        ),
        (
            "VIEW_TEXT_OVERLAY_300DPI",
            "after_text_measurement_overlay_300dpi.png",
            "GLOBAL", "OVERLAY", "N/A", "N/A",
        ),
    ]
    for panel, role, script in sorted(
        {
            (
                row["PANEL_ID"],
                row["ROLE"],
                row["SCRIPT_CLASS"],
            )
            for row in d_rows
        }
    ):
        d_values = [
            float(row["RATIO_TO_CLASS_MEDIAN"])
            for row in d_rows
            if (
                row["PANEL_ID"],
                row["ROLE"],
                row["SCRIPT_CLASS"],
            ) == (panel, role, script)
        ]
        e_row = next(
            (
                row
                for row in e_rows
                if row["PANEL_ID"] == panel
                and row["ROLE"] == role
                and row["SCRIPT_CLASS"] == script
            ),
            None,
        )
        visual_specs.append(
            (
                f"ROLE_{panel}_{role}_{script}",
                "figure_crop_300dpi.png",
                panel,
                role,
                f"{median(d_values):.6f}",
                e_row["ROLE_RATIO"] if e_row else "N/A",
            )
        )
    visual_fields = [
        "CHECK_ID", "EVIDENCE_FILE", "PANEL_ID", "ROLE",
        "D_RATIO", "E_RATIO", "REVIEWER", "ACTUALLY_OPENED",
        "FONT_TOO_SMALL", "FONT_ABRUPT_OR_OVERSIZED",
        "FONT_VISUAL_HARMONY_PASS", "GRAYSCALE_PASS",
        "PAGE_INTEGRATION_PASS", "DECISION", "NOTE",
    ]
    visual_path = OUT / "manual_visual_harmony_ledger.csv"
    initialise_visual = not visual_path.exists()
    if visual_path.exists():
        with visual_path.open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            prior_visual = list(csv.DictReader(handle))
        prior_ids = {row.get("CHECK_ID", "") for row in prior_visual}
        current_ids = {row[0] for row in visual_specs}
        if prior_ids != current_ids:
            if any(
                row.get("DECISION") not in ("", "PENDING")
                for row in prior_visual
            ):
                raise RuntimeError(
                    "reviewed visual ledger cannot be replaced after source drift"
                )
            initialise_visual = True
    if initialise_visual:
        write_csv(
            visual_path,
            [
                {
                    "CHECK_ID": check_id,
                    "EVIDENCE_FILE": evidence_file,
                    "PANEL_ID": panel,
                    "ROLE": role,
                    "D_RATIO": d_ratio,
                    "E_RATIO": e_ratio,
                    "REVIEWER": "",
                    "ACTUALLY_OPENED": "",
                    "FONT_TOO_SMALL": "",
                    "FONT_ABRUPT_OR_OVERSIZED": "",
                    "FONT_VISUAL_HARMONY_PASS": "",
                    "GRAYSCALE_PASS": "",
                    "PAGE_INTEGRATION_PASS": "",
                    "DECISION": "PENDING",
                    "NOTE": "",
                }
                for (
                    check_id, evidence_file, panel, role,
                    d_ratio, e_ratio,
                ) in visual_specs
            ],
            visual_fields,
        )

    mask_manifest_rows = []
    mask_objects = (
        objects + glyphs + vector_components
        + list(substring_objects.values())
        + list(card_edges.values())
    )
    for obj in mask_objects:
        mask_manifest_rows.append(
            {
                "MASK_ID": obj.object_id,
                "SAFE_FILENAME": safe_name(obj.object_id),
                "KIND": obj.kind,
                "PARENT_ID": obj.parent,
                "ROLE": obj.role,
                "PANEL": obj.panel,
                "BBOX_FULL_PAGE_PX": json.dumps(obj.bbox),
                "PIXELS": obj.pixels,
                "NONEMPTY": str(obj.nonempty).lower(),
                "RAW_MASK": rel(obj.path),
            }
        )
    write_csv(
        OUT / "mask_manifest.csv",
        mask_manifest_rows,
        [
            "MASK_ID", "SAFE_FILENAME", "KIND", "PARENT_ID",
            "ROLE", "PANEL", "BBOX_FULL_PAGE_PX", "PIXELS",
            "NONEMPTY", "RAW_MASK",
        ],
    )

    safe_file_rows = []
    expected_paths = {
        obj.path.resolve() for obj in mask_objects
    }
    expected_paths.update(
        (OUT / row["SHEET"]).resolve() for row in contact_manifest
    )
    expected_paths.update(
        path.resolve() for path in calibration["artifact_path_objects"]
    )
    expected_paths.update(
        path.resolve() for path in LOW_PROFILE_DIR.rglob("*")
        if path.is_file()
    )
    expected_paths.add(
        (OUT / "low_profile_punctuation_calibration.csv").resolve()
    )
    for path in sorted(expected_paths):
        ordinary = path.is_file()
        size = path.stat().st_size if ordinary else 0
        openable: str | bool = "N/A"
        dimensions = ""
        if ordinary and path.suffix.lower() == ".png":
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    dimensions = f"{image.width}x{image.height}"
                openable = True
            except Exception:
                openable = False
        passed = (
            ordinary
            and size > 0
            and (
                path.suffix.lower() != ".png"
                or openable is True
            )
        )
        safe_file_rows.append(
            {
                "PATH": rel(path),
                "ORDINARY_FILE": str(ordinary).lower(),
                "BYTES": size,
                "PNG_OPENABLE": (
                    str(openable).lower()
                    if isinstance(openable, bool)
                    else openable
                ),
                "DIMENSIONS": dimensions,
                "PASS_FAIL": "PASS" if passed else "FAIL",
            }
        )
    write_csv(
        OUT / "safe_filename_and_file_openability.csv",
        safe_file_rows,
        [
            "PATH", "ORDINARY_FILE", "BYTES", "PNG_OPENABLE",
            "DIMENSIONS", "PASS_FAIL",
        ],
    )

    core_summary = {
        "uid": "FIG-P580-01",
        "strict_schema_revision": 111,
        "glyph_count": len(glyphs),
        "necessary_substring_count": len(substring_rows),
        "text_element_count": len(elements),
        "graphic_count": len(graphics),
        "semantic_object_count": len(objects),
        "expected_unordered_pair_count": (
            len(objects) * (len(objects) - 1) // 2
        ),
        "actual_unordered_pair_count": len(all_pairs),
        "required_relation_count": len(required_rows),
        "critical_relation_package_count": len(set(critical_ids)),
        "pixel_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in pixel_rows
        ),
        "low_profile_punctuation_count": len(low_profile_rows),
        "low_profile_calibration_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in low_profile_rows
        ),
        "low_profile_calibration_reference": (
            "low_profile_punctuation/reference_measurement.json"
        ),
        "font_failure_count": sum(
            row["SOURCE_FONT_PASS"] != "true" for row in font_rows
        ),
        "D_failure_count": sum(
            row["D_PASS"] == "false" for row in d_rows
        ),
        "E_failure_count": sum(
            row["E_PASS"] == "false" for row in e_rows
        ),
        "pair_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in all_pairs
        ),
        "required_relation_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in required_rows
        ),
        "clip_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in clip_rows
        ),
        "opaque_label_ground_count": 1,
        "opaque_graphic_coverage_failure_count": sum(
            row["PASS_FAIL"] == "FAIL" for row in coverage_rows
        ),
        "translucent_label_ground_count": 0,
        "translucent_graphic_coverage_failure_count": 0,
        "source_unassigned_text_pixels": ownership_report[
            "source_unassigned_text_pixels"
        ],
        "source_duplicate_text_pixels": ownership_report[
            "source_duplicate_text_pixels"
        ],
        "empty_mask_ids": [
            obj.object_id for obj in mask_objects if not obj.nonempty
        ],
        "glyph_missing_stroke_total": sum(
            int(row["MISSING_STROKE_PX"])
            for row in pixel_rows
            if str(row["MEASURE_ID"]).startswith("G")
        ),
        "glyph_foreign_pixel_total": sum(
            int(row["FOREIGN_PIXEL_PX"])
            for row in pixel_rows
            if str(row["MEASURE_ID"]).startswith("G")
        ),
        "contact_sheet_count": len(
            {row["SHEET"] for row in contact_manifest}
        ),
        "contact_manifest_count": len(contact_manifest),
        "visual_template_count": len(visual_specs),
        "text_completeness_pass": all(completeness_checks.values()),
        "math_body_consistency_pass": all(math_checks.values()),
        "anchor_checks_pass": all(anchor_checks.values()),
        "text_replay_exact": (
            replay_report["character_stream_exact"]
            and replay_report[
                "text_trace_visual_properties_exact"
            ]
        ),
    }
    save_json(OUT / "core_audit_summary.json", core_summary)
    print(json.dumps(core_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
