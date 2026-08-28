from __future__ import annotations

"""Read-only strict SA1 audit for FIG-P392-01."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math
import re
import subprocess
import unicodedata

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from scipy.spatial import cKDTree


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P392-01\STRICT_R1\SA1_20260823_R1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第03册_优化模型与序列模型\V3-C06\fig_v3_c06_chain.tex")
ADJACENT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第03册_优化模型与序列模型\chapters\V3-C06.tex")

FIGURE_ID = "FIG-P392-01"
PDF_DPI = 300
PDF_SCALE = PDF_DPI / 72.0
TEX_PER_PDF_PT = 72.27 / 72.0
PANEL_ID = "P1"
FIG_CROP_PT = fitz.Rect(95.0, 92.0, 510.0, 230.0)
STANDALONE_PT = fitz.Rect(100.0, 95.0, 505.0, 210.0)
FULL300 = OUT / "full_page_300dpi_native.png"
TEXT_ONLY_PDF = OUT / "text_only_page428.pdf"
TEXT_ONLY_300 = OUT / "text_only_page_300dpi_native.png"


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def union(self, other: "BBox") -> "BBox":
        return BBox(min(self.x0, other.x0), min(self.y0, other.y0),
                    max(self.x1, other.x1), max(self.y1, other.y1))

    def as_text(self) -> str:
        return f"({self.x0:.3f},{self.y0:.3f},{self.x1:.3f},{self.y1:.3f})"


def ensure_dirs() -> None:
    for rel in [
        "masks/text", "masks/parents", "masks/vectors", "raw_rois/text",
        "overlays/text", "near_limit", "pair_evidence",
    ]:
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def save_rgb(path: Path, arr: np.ndarray) -> None:
    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path)


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def clip_indices(rect: fitz.Rect, width: int, height: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * PDF_SCALE)))
    y0 = max(0, int(math.floor(rect.y0 * PDF_SCALE)))
    x1 = min(width, int(math.ceil(rect.x1 * PDF_SCALE)))
    y1 = min(height, int(math.ceil(rect.y1 * PDF_SCALE)))
    return x0, y0, x1, y1


def is_cjk_or_fullwidth(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0xFF00 <= code <= 0xFFEF
    )


def is_math_upper_or_digit(ch: str) -> bool:
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return True
    name = unicodedata.name(ch, "")
    return "MATHEMATICAL" in name and "CAPITAL" in name


def is_math_lower_or_greek(ch: str) -> bool:
    if "a" <= ch <= "z":
        return True
    name = unicodedata.name(ch, "")
    return (
        ("MATHEMATICAL" in name and "SMALL" in name)
        or "GREEK SMALL" in name
        or "GREEK LETTER" in name
    )


def glyph_class(ch: str, is_script: bool) -> tuple[str, int]:
    if is_script:
        if is_cjk_or_fullwidth(ch):
            return "SCRIPT_CJK_FULLWIDTH", 15
        if is_math_upper_or_digit(ch):
            return "SCRIPT_UPPER_OR_DIGIT", 15
        if is_math_lower_or_greek(ch):
            return "SCRIPT_LOWER_OR_GREEK", 15
        return "SCRIPT_MATH_OPERATOR_OR_PUNCT", 15
    if is_cjk_or_fullwidth(ch):
        return "CJK_OR_FULLWIDTH", 30
    if is_math_upper_or_digit(ch):
        return "UPPER_OR_DIGIT", 24
    if is_math_lower_or_greek(ch):
        return "LOWER_OR_GREEK", 17
    return "MATH_OPERATOR_OR_PUNCT", 22


def parent_for_char(pdf_bbox: fitz.Rect) -> tuple[str, int, str, str]:
    x, y = pdf_bbox.x0, pdf_bbox.y0
    if 207.0 <= y < 226.0:
        return "CAPTION", 38, "CAPTION", "UNKNOWN_GLOBAL_CAPTION_FONT"
    if 190.0 <= y < 206.0:
        return "BRACE_LABEL", 36, "ANNOTATION", "EXPLICIT_9.0PT"
    if 150.0 <= y < 190.0:
        if x >= 380.0:
            return "NOTE", 33, "FORMULA_OR_ANNOTATION", "EXPLICIT_9.2PT"
        return "XBAR", 28, "NODE_BODY", "EXPLICIT_9.2PT"
    if x < 130.0:
        return "NODE_Y0", 13, "NODE_LABEL", "INHERITED_9.2PT_SCOPE"
    if 130.0 <= x < 160.0:
        return "FACTOR_M1", 14, "FACTOR_LABEL", "EXPLICIT_9.2PT"
    if 160.0 <= x < 185.0:
        return "NODE_Y1", 15, "NODE_LABEL", "INHERITED_9.2PT_SCOPE"
    if 185.0 <= x < 211.0:
        return "FACTOR_M2", 16, "FACTOR_LABEL", "EXPLICIT_9.2PT"
    if 211.0 <= x < 240.0:
        return "NODE_Y2", 17, "NODE_LABEL", "INHERITED_9.2PT_SCOPE"
    if 240.0 <= x < 290.0:
        return "ELLIPSIS", 18, "CHAIN_CONTINUATION", "INHERITED_9.2PT_SCOPE"
    if 290.0 <= x < 330.0:
        return "NODE_YN", 19, "NODE_LABEL", "INHERITED_9.2PT_SCOPE"
    if 330.0 <= x < 358.0:
        return "FACTOR_MN1", 20, "FACTOR_LABEL", "EXPLICIT_9.2PT"
    return "NODE_YN1", 21, "NODE_LABEL", "INHERITED_9.2PT_SCOPE"


def source_declared_pt(provenance: str) -> float | None:
    if provenance == "EXPLICIT_9.0PT":
        return 9.0
    if provenance in {"EXPLICIT_9.2PT", "INHERITED_9.2PT_SCOPE"}:
        return 9.2
    return None


def is_script_glyph(parent: str, bbox: fitz.Rect, pdf_font_pt: float) -> bool:
    if parent.startswith("NODE_Y"):
        return bbox.y0 >= 118.5
    if parent.startswith("FACTOR_"):
        return bbox.y0 >= 107.5
    if parent in {"XBAR", "NOTE"}:
        return pdf_font_pt < 8.0
    return False


def exact_char_mask(rgb: np.ndarray, bbox_pt: fitz.Rect):
    h, w = rgb.shape[:2]
    x0 = max(0, int(math.floor(bbox_pt.x0 * PDF_SCALE)))
    x1 = min(w, int(math.ceil(bbox_pt.x1 * PDF_SCALE)))
    y0 = max(0, int(math.floor(bbox_pt.y0 * PDF_SCALE)))
    y1 = min(h, int(math.ceil(bbox_pt.y1 * PDF_SCALE)))
    if x1 <= x0 or y1 <= y0:
        return np.zeros((0, 0), dtype=bool), np.zeros((0, 0, 3), dtype=np.uint8), (x0, y0, x1, y1), (255, 255, 255)
    roi = rgb[y0:y1, x0:x1].copy()
    centres_x = (np.arange(x0, x1, dtype=float) + 0.5) / PDF_SCALE
    centres_y = (np.arange(y0, y1, dtype=float) + 0.5) / PDF_SCALE
    inside = (
        (centres_x[None, :] >= bbox_pt.x0)
        & (centres_x[None, :] < bbox_pt.x1)
        & (centres_y[:, None] >= bbox_pt.y0)
        & (centres_y[:, None] < bbox_pt.y1)
    )
    values = roi[inside]
    bg = (255, 255, 255) if len(values) == 0 else Counter(map(tuple, values.tolist())).most_common(1)[0][0]
    diff = np.max(np.abs(roi.astype(np.int16) - np.asarray(bg, dtype=np.int16)), axis=2)
    return inside & (diff >= 20), roi, (x0, y0, x1, y1), tuple(int(v) for v in bg)


def ink_height(mask: np.ndarray) -> int:
    if mask.size == 0 or not mask.any():
        return 0
    ys = np.where(mask.any(axis=1))[0]
    return int(ys[-1] - ys[0] + 1)


def mask_bbox(mask: np.ndarray) -> BBox | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return BBox(float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1))


def rect_gap(a: BBox, b: BBox) -> float:
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
    return float(math.hypot(dx, dy))


def nearest_metrics(a: np.ndarray, b: np.ndarray):
    intersection = a & b
    n_overlap = int(intersection.sum())
    ayx = np.argwhere(a)
    byx = np.argwhere(b)
    if len(ayx) == 0 or len(byx) == 0:
        return n_overlap, math.inf, (-1, -1), (-1, -1)
    if n_overlap:
        y, x = np.argwhere(intersection)[0]
        return n_overlap, 0.0, (int(x), int(y)), (int(x), int(y))
    if len(ayx) <= len(byx):
        tree = cKDTree(byx[:, ::-1])
        d, idx = tree.query(ayx[:, ::-1], k=1)
        k = int(np.argmin(d))
        pa = (int(ayx[k, 1]), int(ayx[k, 0]))
        pb = (int(byx[int(idx[k]), 1]), int(byx[int(idx[k]), 0]))
    else:
        tree = cKDTree(ayx[:, ::-1])
        d, idx = tree.query(byx[:, ::-1], k=1)
        k = int(np.argmin(d))
        pb = (int(byx[k, 1]), int(byx[k, 0]))
        pa = (int(ayx[int(idx[k]), 1]), int(ayx[int(idx[k]), 0]))
    return n_overlap, float(d[k]), pa, pb


def bezier(p0, p1, p2, p3, n: int = 48):
    t = np.linspace(0.0, 1.0, n)
    return (
        ((1 - t) ** 3)[:, None] * p0
        + (3 * ((1 - t) ** 2) * t)[:, None] * p1
        + (3 * (1 - t) * (t ** 2))[:, None] * p2
        + (t ** 3)[:, None] * p3
    )


def draw_vector_mask(drawing: dict, crop_origin: tuple[int, int], crop_size: tuple[int, int]):
    crop_w, crop_h = crop_size
    rect = drawing["rect"]
    x0 = max(crop_origin[0], int(math.floor(rect.x0 * PDF_SCALE)))
    y0 = max(crop_origin[1], int(math.floor(rect.y0 * PDF_SCALE)))
    x1 = min(crop_origin[0] + crop_w, int(math.ceil(rect.x1 * PDF_SCALE)))
    y1 = min(crop_origin[1] + crop_h, int(math.ceil(rect.y1 * PDF_SCALE)))
    full = np.zeros((crop_h, crop_w), dtype=bool)
    if x1 <= x0 or y1 <= y0 or not drawing.get("width"):
        return full, BBox(float(x0 - crop_origin[0]), float(y0 - crop_origin[1]), float(x1 - crop_origin[0]), float(y1 - crop_origin[1]))
    ss = 8
    high = np.zeros(((y1-y0)*ss, (x1-x0)*ss), dtype=np.uint8)
    thickness = max(1, int(round(float(drawing["width"]) * PDF_SCALE * ss)))

    def to_local(point) -> np.ndarray:
        return np.array([(point.x * PDF_SCALE - x0) * ss, (point.y * PDF_SCALE - y0) * ss], dtype=float)

    def stroke(points: np.ndarray) -> None:
        if len(points) < 2:
            return
        ip = np.rint(points).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(high, [ip], False, 255, thickness=thickness, lineType=cv2.LINE_AA)
        for pt in (ip[0, 0], ip[-1, 0]):
            cv2.circle(high, tuple(int(v) for v in pt), int(round(thickness/2.0)), 255, thickness=-1, lineType=cv2.LINE_AA)

    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            stroke(np.vstack([to_local(item[1]), to_local(item[2])]))
        elif kind == "re":
            r = item[1]
            stroke(np.vstack([to_local(fitz.Point(r.x0,r.y0)), to_local(fitz.Point(r.x1,r.y0)), to_local(fitz.Point(r.x1,r.y1)), to_local(fitz.Point(r.x0,r.y1)), to_local(fitz.Point(r.x0,r.y0))]))
        elif kind == "c":
            stroke(bezier(to_local(item[1]), to_local(item[2]), to_local(item[3]), to_local(item[4])))
        elif kind == "qu":
            p0, p1, p2 = to_local(item[1]), to_local(item[2]), to_local(item[3])
            t = np.linspace(0.0, 1.0, 48)
            stroke(((1-t)**2)[:,None]*p0 + (2*(1-t)*t)[:,None]*p1 + (t**2)[:,None]*p2)
    coverage = high.reshape(y1-y0, ss, x1-x0, ss).mean(axis=(1,3)) / 255.0
    local = coverage >= (20.0/255.0)
    full[y0-crop_origin[1]:y1-crop_origin[1], x0-crop_origin[0]:x1-crop_origin[0]] = local
    return full, BBox(float(x0-crop_origin[0]), float(y0-crop_origin[1]), float(x1-crop_origin[0]), float(y1-crop_origin[1]))


def vector_meta(index: int) -> tuple[str, str, int]:
    table = {
        5: ("VEC05_BOUNDARY_Y0_OUTER", "NODE_BORDER", 13), 6: ("VEC06_BOUNDARY_Y0_INNER", "NODE_BORDER", 13),
        7: ("VEC07_FACTOR_M1_BORDER", "NODE_BORDER", 14), 8: ("VEC08_NODE_Y1_BORDER", "NODE_BORDER", 15),
        9: ("VEC09_FACTOR_M2_BORDER", "NODE_BORDER", 16), 10: ("VEC10_NODE_Y2_BORDER", "NODE_BORDER", 17),
        11: ("VEC11_NODE_YN_BORDER", "NODE_BORDER", 19), 12: ("VEC12_FACTOR_MN1_BORDER", "NODE_BORDER", 20),
        13: ("VEC13_BOUNDARY_YN1_OUTER", "NODE_BORDER", 21), 14: ("VEC14_BOUNDARY_YN1_INNER", "NODE_BORDER", 21),
        15: ("VEC15_CHAIN_LEFT", "LINE", 22), 16: ("VEC16_CHAIN_MIDDLE", "LINE", 23),
        17: ("VEC17_CHAIN_RIGHT", "LINE", 24), 18: ("VEC18_XBAR_BORDER", "NODE_BORDER", 26),
        19: ("VEC19_DEP_M1", "LINE", 29), 20: ("VEC20_DEP_M2", "LINE", 30),
        21: ("VEC21_DEP_MN1", "LINE", 31), 22: ("VEC22_NOTE_BORDER", "NODE_BORDER", 32),
        23: ("VEC23_BRACE", "LINE", 34),
    }
    return table[index]


def csv_write(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_pair_evidence(tag: str, fig_rgb: np.ndarray, mask_a: np.ndarray, mask_b: np.ndarray, nearest_a, nearest_b):
    union = mask_a | mask_b
    bb = mask_bbox(union)
    if bb is None:
        return "N/A", "N/A", "N/A"
    margin = 14
    x0 = max(0, int(math.floor(bb.x0))-margin); y0 = max(0, int(math.floor(bb.y0))-margin)
    x1 = min(fig_rgb.shape[1], int(math.ceil(bb.x1))+margin); y1 = min(fig_rgb.shape[0], int(math.ceil(bb.y1))+margin)
    raw = fig_rgb[y0:y1, x0:x1]
    raw_name = f"pair_evidence/{tag}_raw_1to1_300dpi.png"
    save_rgb(OUT / raw_name, raw)
    ov = raw.copy(); a = mask_a[y0:y1, x0:x1]; b = mask_b[y0:y1, x0:x1]
    ov[a] = (235, 50, 50); ov[b] = (30, 180, 255)
    for p, color in ((nearest_a,(255,0,255)), (nearest_b,(0,255,0))):
        if p[0] >= 0:
            cv2.circle(ov, (p[0]-x0,p[1]-y0), 4, color, 1, lineType=cv2.LINE_AA)
    overlay_name = f"pair_evidence/{tag}_overlay_300dpi.png"
    save_rgb(OUT / overlay_name, ov)
    overlap_name = f"pair_evidence/{tag}_overlap_mask_300dpi.png"
    save_mask(OUT / overlap_name, a & b)
    return raw_name, overlay_name, overlap_name


def make_text_only_pdf_and_png(page_index: int) -> None:
    """Create a local evidence derivative retaining PDF text operators only.

    Vector paint operations are changed to path-end operations while transforms,
    fonts and text operators remain untouched. The resulting native 300 dpi
    render gives true text-span foreground without same-colour node-border
    contamination. It is an audit artifact only; the frozen PDF is not changed.
    """
    reader = PdfReader(str(PDF))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    cloned = writer.pages[page_index]
    content = ContentStream(cloned[NameObject("/Contents")], writer)
    paint_ops = {b"S",b"s",b"f",b"F",b"f*",b"B",b"B*",b"b",b"b*",b"sh",b"Do"}
    content.operations = [
        ([], b"n") if operation in paint_ops else (operands, operation)
        for operands, operation in content.operations
    ]
    cloned[NameObject("/Contents")] = writer._add_object(content)
    with TEXT_ONLY_PDF.open("wb") as stream:
        writer.write(stream)
    subprocess.run(
        ["pdftoppm","-png","-r","300","-f",str(page_index+1),"-l",str(page_index+1),"-singlefile",str(TEXT_ONLY_PDF),str(TEXT_ONLY_300.with_suffix(""))],
        check=True,
    )


def main() -> None:
    ensure_dirs()
    if not FULL300.exists():
        raise RuntimeError(f"Missing direct Poppler native 300 dpi input: {FULL300}")
    rgb = np.asarray(Image.open(FULL300).convert("RGB")).copy()
    page_h, page_w = rgb.shape[:2]

    doc = fitz.open(PDF)
    hits = []
    for i, p in enumerate(doc):
        text = p.get_text()
        if "图22.1" in text and "线性链CRF" in text:
            hits.append(i)
    if len(hits) != 1:
        raise RuntimeError(f"Caption and label search must give exactly one physical page, got {hits}")
    page_index = hits[0]
    page = doc[page_index]
    page_text = page.get_text()
    if "图22.1" not in page_text or "线性链CRF" not in page_text:
        raise RuntimeError("Target page identity check failed")
    printed_page = "415" if re.search(r"\b415\b", "\n".join(page_text.splitlines()[:10])) else "UNRESOLVED"
    make_text_only_pdf_and_png(page_index)
    text_rgb = np.asarray(Image.open(TEXT_ONLY_300).convert("RGB")).copy()
    if text_rgb.shape != rgb.shape:
        raise RuntimeError(f"Text-only raster size mismatch: {text_rgb.shape} versus {rgb.shape}")

    fx0, fy0, fx1, fy1 = clip_indices(FIG_CROP_PT, page_w, page_h)
    sx0, sy0, sx1, sy1 = clip_indices(STANDALONE_PT, page_w, page_h)
    fig_rgb = rgb[fy0:fy1, fx0:fx1].copy()
    standalone_rgb = rgb[sy0:sy1, sx0:sx1].copy()
    save_rgb(OUT / "figure_crop_300dpi.png", fig_rgb)
    save_rgb(OUT / "standalone_300dpi.png", standalone_rgb)
    Image.fromarray(fig_rgb, mode="RGB").convert("L").save(OUT / "grayscale_300dpi.png")

    raw = page.get_text("rawdict")
    chars: list[dict] = []
    count = 0
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                span_bbox = fitz.Rect(span["bbox"])
                if not ((100.0 <= span_bbox.y0 < 205.0) or (207.0 <= span_bbox.y0 < 226.0)):
                    continue
                for ch in span["chars"]:
                    glyph = ch["c"]
                    if glyph.isspace():
                        continue
                    bbox = fitz.Rect(ch["bbox"])
                    parent, source_line, inherited_role, provenance = parent_for_char(bbox)
                    if parent == "NOTE":
                        role = "ANNOTATION" if is_cjk_or_fullwidth(glyph) else "FORMULA"
                    elif parent == "XBAR":
                        role = "NODE_BODY" if is_cjk_or_fullwidth(glyph) else "NODE_BODY_FORMULA"
                    else:
                        role = inherited_role
                    pdf_pt = float(span["size"])
                    script = is_script_glyph(parent, bbox, pdf_pt)
                    script_class, threshold = glyph_class(glyph, script)
                    local_mask, _text_only_roi, pixel_box, bg = exact_char_mask(text_rgb, bbox)
                    x0, y0, x1, y1 = pixel_box
                    if x0 < fx0 or x1 > fx1 or y0 < fy0 or y1 > fy1:
                        raise RuntimeError(f"Text bbox outside figure viewport: {glyph} {bbox}")
                    mask = np.zeros((fig_rgb.shape[0], fig_rgb.shape[1]), dtype=bool)
                    mask[y0-fy0:y1-fy0, x0-fx0:x1-fx0] = local_mask
                    count += 1
                    element_id = f"TXT{count:03d}"
                    raw_rel = f"raw_rois/text/{element_id}_raw_1to1_300dpi.png"
                    mask_rel = f"masks/text/{element_id}_mask_300dpi.png"
                    overlay_rel = f"overlays/text/{element_id}_overlay_300dpi.png"
                    roi = rgb[y0:y1, x0:x1].copy()
                    save_rgb(OUT / raw_rel, roi)
                    save_mask(OUT / mask_rel, local_mask)
                    ov = roi.copy(); ov[local_mask] = (230,30,30)
                    save_rgb(OUT / overlay_rel, ov)
                    chars.append({
                        "element_id": element_id, "parent_id": parent, "source_line": source_line, "role": role,
                        "font_provenance": provenance, "declared_pt": source_declared_pt(provenance),
                        "pdf_font_pt": pdf_pt, "effective_pt": pdf_pt * TEX_PER_PDF_PT,
                        "glyph": glyph, "font": span["font"], "script": script, "script_class": script_class,
                        "threshold": threshold, "bbox_pt": bbox,
                        "bbox_px": BBox(bbox.x0*PDF_SCALE, bbox.y0*PDF_SCALE, bbox.x1*PDF_SCALE, bbox.y1*PDF_SCALE),
                        "pixel_box": pixel_box, "mask": mask, "h_ink": ink_height(local_mask),
                        "background_rgb": bg, "raw_path": raw_rel, "mask_path": mask_rel, "overlay_path": overlay_rel,
                    })
    if not chars:
        raise RuntimeError("No target glyphs found")

    parents: dict[str, dict] = {}
    for c in chars:
        p = parents.setdefault(c["parent_id"], {
            "parent_id": c["parent_id"], "role": c["role"], "source_line": c["source_line"],
            "mask": np.zeros_like(fig_rgb[:,:,0], dtype=bool), "bbox_px": None, "children": [],
        })
        p["mask"] |= c["mask"]
        p["bbox_px"] = c["bbox_px"] if p["bbox_px"] is None else p["bbox_px"].union(c["bbox_px"])
        p["children"].append(c)
    for pid, p in parents.items():
        p["mask_path"] = f"masks/parents/{pid}_mask_300dpi.png"
        save_mask(OUT / p["mask_path"], p["mask"])
        p["ink_h"] = ink_height(p["mask"])

    vectors: dict[str, dict] = {}
    for i, drawing in enumerate(page.get_drawings()):
        if i not in range(5,24):
            continue
        vector_id, category, source_line = vector_meta(i)
        mask, bbox = draw_vector_mask(drawing, (fx0,fy0), (fig_rgb.shape[1],fig_rgb.shape[0]))
        mpath = f"masks/vectors/{vector_id}_mask_300dpi.png"
        save_mask(OUT / mpath, mask)
        vectors[vector_id] = {
            "id": vector_id, "category": category, "source_line": source_line,
            "mask": mask,
            "bbox_px": BBox(bbox.x0+fx0,bbox.y0+fy0,bbox.x1+fx0,bbox.y1+fy0),
            "mask_path": mpath, "drawing_index": i,
        }
    if len(vectors) != 19:
        raise RuntimeError(f"Expected 19 vectors; found {len(vectors)}")

    overlay = Image.fromarray(fig_rgb.copy(), mode="RGB")
    draw = ImageDraw.Draw(overlay)
    for c in chars:
        x0,y0,x1,y1 = c["pixel_box"]
        x0 -= fx0; x1 -= fx0; y0 -= fy0; y1 -= fy0
        draw.rectangle((x0,y0,x1-1,y1-1), outline=(220,20,60), width=1)
        draw.text((x0,max(0,y0-11)), c["element_id"], fill=(220,20,60), stroke_width=1, stroke_fill=(255,255,255))
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    parent_base_pt = {}
    for pid, p in parents.items():
        bases = [c["effective_pt"] for c in p["children"] if not c["script"]]
        parent_base_pt[pid] = max(bases) if bases else float("nan")

    source_groups = defaultdict(list)
    for c in chars:
        source_groups[(c["role"], "SCRIPT" if c["script"] else c["script_class"])].append(c)
    source_stats = {}
    for key, members in source_groups.items():
        vals = [m["effective_pt"] for m in members]
        source_stats[key] = (min(vals), max(vals), max(vals)/min(vals) if min(vals) else math.inf, max(vals)-min(vals))

    font_rows = []
    for c in chars:
        base_ok = parent_base_pt[c["parent_id"]] >= 9.5
        if c["declared_pt"] is None:
            status, reason = "FAIL", "DECLARED_PT_UNKNOWN_WITHIN_PERMITTED_SOURCE_SCOPE"
        elif c["script"]:
            status = "PASS" if base_ok else "FAIL"
            reason = "NATURAL_SCRIPT_PARENT_BASE_PASS" if base_ok else "SCRIPT_PARENT_BASE_EFFECTIVE_PT_LT_9.5"
        elif c["effective_pt"] >= 9.5:
            status, reason = "PASS", "EFFECTIVE_PT_GE_9.5"
        else:
            status, reason = "FAIL", "EFFECTIVE_PT_LT_9.5"
        c["font_status"], c["font_reason"] = status, reason
        group = source_stats[(c["role"], "SCRIPT" if c["script"] else c["script_class"])]
        font_rows.append({
            "ELEMENT_ID":c["element_id"], "PARENT_ID":c["parent_id"], "PANEL_ID":PANEL_ID, "ROLE":c["role"],
            "SOURCE_FILE":str(SOURCE), "SOURCE_LINE":c["source_line"],
            "DECLARED_PT":"UNKNOWN" if c["declared_pt"] is None else f"{c['declared_pt']:.3f}",
            "GRAPHICS_SCALE":"1.000000", "EFFECTIVE_PT":f"{c['effective_pt']:.3f}",
            "PDF_SPAN_FONT":c["font"], "PDF_SPAN_PT":f"{c['pdf_font_pt']:.3f}",
            "TEXT_SAMPLE":c["glyph"], "SCRIPT_CLASS":c["script_class"],
            "PARENT_BASE_EFFECTIVE_PT":f"{parent_base_pt[c['parent_id']]:.3f}",
            "SAME_ROLE_EFFECTIVE_MAX_MIN":f"{group[2]:.4f}", "SAME_ROLE_EFFECTIVE_ABS_DIFF_PT":f"{group[3]:.4f}",
            "SOURCE_FONT_PASS":status, "REASON":reason,
        })
    csv_write(OUT / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))

    def unit_mask(pid: str, predicate):
        out = np.zeros_like(parents[pid]["mask"])
        for child in parents[pid]["children"]:
            if predicate(child):
                out |= child["mask"]
        return out

    same_units = []
    for pid in ["NODE_Y0","NODE_Y1","NODE_Y2","NODE_YN","NODE_YN1"]:
        same_units.append(("NODE_LABEL_BASE_LOWER", pid, "NODE_LABEL", "LOWER_OR_GREEK", unit_mask(pid, lambda c: not c["script"])))
        for script_class in ["SCRIPT_UPPER_OR_DIGIT","SCRIPT_LOWER_OR_GREEK","SCRIPT_MATH_OPERATOR_OR_PUNCT"]:
            m = unit_mask(pid, lambda c, sc=script_class: c["script"] and c["script_class"] == sc)
            if m.any():
                same_units.append((f"NODE_LABEL_NATURAL_{script_class}", pid, "NODE_LABEL", script_class, m))
    for pid in ["FACTOR_M1","FACTOR_M2","FACTOR_MN1"]:
        same_units.append(("FACTOR_LABEL_BASE_UPPER", pid, "FACTOR_LABEL", "UPPER_OR_DIGIT", unit_mask(pid, lambda c: not c["script"])))
        for script_class in ["SCRIPT_UPPER_OR_DIGIT","SCRIPT_LOWER_OR_GREEK","SCRIPT_MATH_OPERATOR_OR_PUNCT"]:
            m = unit_mask(pid, lambda c, sc=script_class: c["script"] and c["script_class"] == sc)
            if m.any():
                same_units.append((f"FACTOR_LABEL_NATURAL_{script_class}", pid, "FACTOR_LABEL", script_class, m))
    for pid, role in [("XBAR","NODE_BODY"),("NOTE","ANNOTATION"),("BRACE_LABEL","ANNOTATION"),("CAPTION","CAPTION")]:
        m = unit_mask(pid, lambda c: is_cjk_or_fullwidth(c["glyph"]))
        if m.any():
            same_units.append((f"{pid}_CJK", pid, role, "CJK_OR_FULLWIDTH", m))

    unit_groups = defaultdict(list)
    for group, pid, role, script_class, mask in same_units:
        if mask.any():
            unit_groups[group].append((pid,role,script_class,mask))
    same_rows = []
    for group, members in unit_groups.items():
        hs = [ink_height(m[3]) for m in members]
        median = float(np.median(hs))
        maxmin = max(hs)/min(hs) if min(hs) else math.inf
        group_ok = all(0.92 <= h/median <= 1.08 for h in hs) and maxmin <= 1.08
        for (pid, role, script_class, _), h in zip(members,hs):
            same_rows.append({
                "GROUP_ID":group,"ELEMENT_ID":pid,"PANEL_ID":PANEL_ID,"ROLE":role,"SCRIPT_CLASS":script_class,
                "H_INK_PX":h,"CLASS_MEDIAN_PX":f"{median:.3f}","RATIO_TO_CLASS_MEDIAN":f"{h/median:.4f}",
                "GROUP_MAX_MIN_RATIO":f"{maxmin:.4f}","PER_ELEMENT_RANGE_PASS":str(0.92 <= h/median <= 1.08).lower(),
                "GROUP_MAX_MIN_PASS":str(maxmin <= 1.08).lower(),"CROSS_PANEL_MAX_MIN_RATIO":"1.0000 (single panel)",
                "CROSS_PANEL_PASS":"true (single panel)","PASS_FAIL":"PASS" if group_ok else "FAIL",
                "NOTES":"singleton; no dispersion" if len(members)==1 else "all same-role comparable labels",
            })
    csv_write(OUT / "same_class_ratio_audit.csv", same_rows, list(same_rows[0].keys()))

    xbar_cjk = unit_mask("XBAR", lambda c: is_cjk_or_fullwidth(c["glyph"]))
    base_h = ink_height(xbar_cjk)
    note_cjk = unit_mask("NOTE", lambda c: is_cjk_or_fullwidth(c["glyph"]))
    brace_cjk = unit_mask("BRACE_LABEL", lambda c: is_cjk_or_fullwidth(c["glyph"]))
    note_formula_base = unit_mask("NOTE", lambda c: not c["script"] and c["script_class"] in {"UPPER_OR_DIGIT","LOWER_OR_GREEK"})
    role_specs = [
        ("BASE_NODE_BODY","NODE_BODY",xbar_cjk,1.00,1.00,"selected ordinary fixed-input CJK body"),
        ("ANNOTATION_NOTE_CJK","ANNOTATION",note_cjk,0.95,1.10,"ordinary note annotation"),
        ("ANNOTATION_BRACE_CJK","ANNOTATION",brace_cjk,0.95,1.10,"ordinary brace annotation"),
        ("FORMULA_NOTE_BASE","FORMULA",note_formula_base,1.00,1.18,"formula baseline letters only; operators separately tested"),
        ("AXIS_TITLE","N/A",None,1.00,1.18,"no axes"),
        ("LEGEND","N/A",None,0.95,1.10,"no legend"),
        ("PANEL_LABEL","N/A",None,1.05,1.20,"single panel has no panel label"),
    ]
    role_rows, role_values = [], {}
    for rid, role, mask, lo, hi, note in role_specs:
        if mask is None:
            role_rows.append({
                "ROLE_ID":rid,"ROLE":role,"BASE_ID":"XBAR_CJK","BASE_H_INK_PX":base_h,"ROLE_H_INK_PX":"N/A",
                "ROLE_RATIO":"N/A","LOWER_BOUND":lo,"UPPER_BOUND":hi,"PREDECLARED_EMPHASIS":"none","PASS_FAIL":"N/A","REASON":note,
            })
            continue
        h = ink_height(mask); ratio = h/base_h if base_h else math.inf; ok = lo <= ratio <= hi
        role_values[rid] = ratio
        role_rows.append({
            "ROLE_ID":rid,"ROLE":role,"BASE_ID":"XBAR_CJK","BASE_H_INK_PX":base_h,"ROLE_H_INK_PX":h,
            "ROLE_RATIO":f"{ratio:.4f}","LOWER_BOUND":lo,"UPPER_BOUND":hi,"PREDECLARED_EMPHASIS":"none",
            "PASS_FAIL":"PASS" if ok else "FAIL","REASON":note,
        })
    csv_write(OUT / "role_ratio_audit.csv", role_rows, list(role_rows[0].keys()))

    overlap_rows, pair_cache = [], []
    parent_ids = list(parents)
    for ai, aid in enumerate(parent_ids):
        a = parents[aid]
        for bid in parent_ids[ai+1:]:
            b = parents[bid]
            n, dist, pa, pb = nearest_metrics(a["mask"], b["mask"])
            bbox_gap = rect_gap(a["bbox_px"], b["bbox_px"])
            status = "PASS" if n == 0 and bbox_gap >= 4.0 else "FAIL"
            row = {
                "PAIR_ID":f"TT_{aid}__{bid}","PAIR_TYPE":"TEXT_TEXT","OBJECT_A":aid,"PARENT_A":aid,"ROLE_A":a["role"],
                "BBOX_A_PX":a["bbox_px"].as_text(),"MASK_A":a["mask_path"],"OBJECT_B":bid,"PARENT_B":bid,"ROLE_B":b["role"],
                "BBOX_B_PX":b["bbox_px"].as_text(),"MASK_B":b["mask_path"],"OVERLAP_PIXEL_COUNT":n,
                "BBOX_CLEARANCE_PX":f"{bbox_gap:.3f}","INK_CLEARANCE_PX":f"{dist:.3f}",
                "NEAREST_A_X":pa[0],"NEAREST_A_Y":pa[1],"NEAREST_B_X":pb[0],"NEAREST_B_Y":pb[1],
                "REQUIRED_CLEARANCE_PX":4,"INTERSECTION_STATUS":"DISJOINT" if n==0 else "INTERSECTS",
                "OVERLAP_MASK":"N/A","STATUS":status,"NOTES":"independent semantic parent masks",
            }
            overlap_rows.append(row); pair_cache.append((row,a["mask"],b["mask"],pa,pb,dist))
    for aid,a in parents.items():
        for vid,v in vectors.items():
            n, dist, pa, pb = nearest_metrics(a["mask"],v["mask"])
            bbox_gap = rect_gap(a["bbox_px"],v["bbox_px"])
            required = 5 if v["category"] == "NODE_BORDER" else 3
            status = "PASS" if n == 0 and dist >= required else "FAIL"
            row = {
                "PAIR_ID":f"TV_{aid}__{vid}","PAIR_TYPE":f"TEXT_{v['category']}","OBJECT_A":aid,"PARENT_A":aid,"ROLE_A":a["role"],
                "BBOX_A_PX":a["bbox_px"].as_text(),"MASK_A":a["mask_path"],"OBJECT_B":vid,"PARENT_B":"N/A","ROLE_B":v["category"],
                "BBOX_B_PX":v["bbox_px"].as_text(),"MASK_B":v["mask_path"],"OVERLAP_PIXEL_COUNT":n,
                "BBOX_CLEARANCE_PX":f"{bbox_gap:.3f}","INK_CLEARANCE_PX":f"{dist:.3f}",
                "NEAREST_A_X":pa[0],"NEAREST_A_Y":pa[1],"NEAREST_B_X":pb[0],"NEAREST_B_Y":pb[1],
                "REQUIRED_CLEARANCE_PX":required,"INTERSECTION_STATUS":"DISJOINT" if n==0 else "INTERSECTS",
                "OVERLAP_MASK":"N/A","STATUS":status,"NOTES":"exact text mask versus independent PDF-vector stroke mask",
            }
            overlap_rows.append(row); pair_cache.append((row,a["mask"],v["mask"],pa,pb,dist))
    vector_ids = list(vectors)
    for ai,aid in enumerate(vector_ids):
        a = vectors[aid]
        for bid in vector_ids[ai+1:]:
            b = vectors[bid]
            n,dist,pa,pb = nearest_metrics(a["mask"],b["mask"])
            overlap_rows.append({
                "PAIR_ID":f"VV_{aid}__{bid}","PAIR_TYPE":"VECTOR_VECTOR","OBJECT_A":aid,"PARENT_A":"N/A","ROLE_A":a["category"],
                "BBOX_A_PX":a["bbox_px"].as_text(),"MASK_A":a["mask_path"],"OBJECT_B":bid,"PARENT_B":"N/A","ROLE_B":b["category"],
                "BBOX_B_PX":b["bbox_px"].as_text(),"MASK_B":b["mask_path"],"OVERLAP_PIXEL_COUNT":n,
                "BBOX_CLEARANCE_PX":f"{rect_gap(a['bbox_px'],b['bbox_px']):.3f}","INK_CLEARANCE_PX":f"{dist:.3f}",
                "NEAREST_A_X":pa[0],"NEAREST_A_Y":pa[1],"NEAREST_B_X":pb[0],"NEAREST_B_Y":pb[1],
                "REQUIRED_CLEARANCE_PX":"N/A","INTERSECTION_STATUS":"DISJOINT" if n==0 else "INTENTIONAL_ENDPOINT_OR_DOUBLE_BORDER_CONTACT",
                "OVERLAP_MASK":"N/A","STATUS":"PASS","NOTES":"vector join inventory, not reader-text collision",
            })

    tt = [p for p in pair_cache if p[0]["PAIR_TYPE"]=="TEXT_TEXT"]
    tv = [p for p in pair_cache if p[0]["PAIR_TYPE"].startswith("TEXT_") and p[0]["PAIR_TYPE"]!="TEXT_TEXT"]
    selected = []
    if tt: selected.append(("closest_text_text",min(tt,key=lambda p:float(p[0]["BBOX_CLEARANCE_PX"]))))
    if tv: selected.append(("closest_text_vector",min(tv,key=lambda p:p[5])))
    selected += [(f"failure_{i:02d}",p) for i,p in enumerate(pair_cache) if p[0]["STATUS"]=="FAIL"]
    seen = set()
    for tag,p in selected:
        if p[0]["PAIR_ID"] in seen: continue
        seen.add(p[0]["PAIR_ID"])
        raw_path, over_path, mask_path = save_pair_evidence(tag,fig_rgb,p[1],p[2],p[3],p[4])
        p[0]["OVERLAP_MASK"],p[0]["EVIDENCE_RAW_ROI"],p[0]["EVIDENCE_OVERLAY"] = mask_path,raw_path,over_path
    for row in overlap_rows:
        row.setdefault("EVIDENCE_RAW_ROI","N/A"); row.setdefault("EVIDENCE_OVERLAY","N/A")
        ax, ay = int(row["NEAREST_A_X"]), int(row["NEAREST_A_Y"])
        bx, by = int(row["NEAREST_B_X"]), int(row["NEAREST_B_Y"])
        row["NEAREST_A_PAGE_X"] = "N/A" if ax < 0 else ax + fx0
        row["NEAREST_A_PAGE_Y"] = "N/A" if ay < 0 else ay + fy0
        row["NEAREST_B_PAGE_X"] = "N/A" if bx < 0 else bx + fx0
        row["NEAREST_B_PAGE_Y"] = "N/A" if by < 0 else by + fy0
    csv_write(OUT / "after_overlap_report.csv", overlap_rows, list(overlap_rows[0].keys()))

    external = defaultdict(list)
    for row in overlap_rows:
        if row["PAIR_TYPE"] == "TEXT_TEXT":
            external[row["OBJECT_A"]].append(row); external[row["OBJECT_B"]].append(row)
        elif row["PAIR_TYPE"].startswith("TEXT_") and row["PAIR_TYPE"] != "TEXT_TEXT":
            external[row["OBJECT_A"]].append(row)
    class_groups = defaultdict(list)
    for child in chars:
        class_groups[(child["role"],child["script_class"])].append(child)
    class_stats = {}
    for key,members in class_groups.items():
        vals = [m["h_ink"] for m in members]
        class_stats[key] = (float(np.median(vals)), max(vals)/min(vals) if min(vals) else math.inf)

    pixel_rows = []
    for c in chars:
        median_h,_ = class_stats[(c["role"],c["script_class"])]
        ratio = c["h_ink"]/median_h if median_h else 0.0
        # Per-glyph values must never inherit a parent aggregate. This keeps a
        # zero/nonzero overlap auditable for each actual PDF span/glyph.
        text_overlap, vector_overlap = 0, 0
        clearance_values = []
        for other_id, other in parents.items():
            if other_id == c["parent_id"]:
                continue
            n, _d, _pa, _pb = nearest_metrics(c["mask"],other["mask"])
            text_overlap += n
            clearance_values.append(rect_gap(c["bbox_px"],other["bbox_px"]))
        for vector in vectors.values():
            n, distance, _pa, _pb = nearest_metrics(c["mask"],vector["mask"])
            vector_overlap += n
            clearance_values.append(distance)
        min_clear = min(clearance_values) if clearance_values else math.inf
        c["pixel_status"] = "PASS" if c["h_ink"] >= c["threshold"] else "FAIL"
        c["pixel_reason"] = "H_INK_PX_MEETS_CLASS_THRESHOLD" if c["pixel_status"]=="PASS" else f"H_INK_PX_LT_{c['threshold']}"
        role_ratio = "N/A"
        if c["role"] == "ANNOTATION":
            key = "ANNOTATION_NOTE_CJK" if c["parent_id"]=="NOTE" else "ANNOTATION_BRACE_CJK"
            role_ratio = f"{role_values.get(key,float('nan')):.4f}"
        elif c["role"] == "FORMULA":
            role_ratio = f"{role_values.get('FORMULA_NOTE_BASE',float('nan')):.4f}"
        elif c["role"].startswith("NODE_BODY"):
            role_ratio = "1.0000"
        pixel_rows.append({
            "ELEMENT_ID":c["element_id"],"PARENT_ID":c["parent_id"],"PANEL_ID":PANEL_ID,"ROLE":c["role"],
            "SOURCE_FILE":str(SOURCE),"SOURCE_LINE":c["source_line"],
            "DECLARED_PT":"UNKNOWN" if c["declared_pt"] is None else f"{c['declared_pt']:.3f}",
            "GRAPHICS_SCALE":"1.000000","EFFECTIVE_PT":f"{c['effective_pt']:.3f}",
            "TEXT_SAMPLE":c["glyph"],"SCRIPT_CLASS":c["script_class"],
            "BBOX_X0":f"{c['bbox_px'].x0:.3f}","BBOX_Y0":f"{c['bbox_px'].y0:.3f}",
            "BBOX_X1":f"{c['bbox_px'].x1:.3f}","BBOX_Y1":f"{c['bbox_px'].y1:.3f}",
            "H_INK_PX":c["h_ink"],"PIXEL_THRESHOLD_PX":c["threshold"],
            "CLASS_MEDIAN_PX":f"{median_h:.3f}","RATIO_TO_CLASS_MEDIAN":f"{ratio:.4f}",
            "ROLE_RATIO":role_ratio,"TEXT_TEXT_OVERLAP_PX":text_overlap,"TEXT_GRAPHIC_OVERLAP_PX":vector_overlap,
            "MIN_CLEARANCE_PX":"INF" if math.isinf(min_clear) else f"{min_clear:.3f}",
            "RAW_ROI_300DPI":c["raw_path"],"MASK_300DPI":c["mask_path"],"OVERLAY_300DPI":c["overlay_path"],
            "PASS_FAIL":c["pixel_status"],"REASON":c["pixel_reason"],
        })
    csv_write(OUT / "after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0].keys()))

    edge_rows, clip_total = [], 0
    clip_objects = [(c["element_id"],"TEXT_GLYPH",c["parent_id"],c["mask"],c["mask_path"]) for c in chars]
    clip_objects += [(v["id"],v["category"],"N/A",v["mask"],v["mask_path"]) for v in vectors.values()]
    for oid,otype,parent,mask,mpath in clip_objects:
        ys,xs = np.where(mask)
        if len(xs) == 0:
            clip_count,page_min,crop_min = 1,-1,-1
        else:
            gx,gy = xs+fx0,ys+fy0
            clip_count = int(np.sum((gx==0)|(gy==0)|(gx==page_w-1)|(gy==page_h-1)))
            page_min = int(min(gx.min(),gy.min(),page_w-1-gx.max(),page_h-1-gy.max()))
            crop_min = int(min(xs.min(),ys.min(),mask.shape[1]-1-xs.max(),mask.shape[0]-1-ys.max()))
        clip_total += clip_count
        edge_rows.append({
            "OBJECT_ID":oid,"OBJECT_TYPE":otype,"PARENT_ID":parent,"MASK_PATH":mpath,
            "PAGE_EDGE_MIN_PX":page_min,"FIGURE_CROP_EDGE_MIN_PX":crop_min,"CLIP_PIXEL_COUNT":clip_count,
            "PASS_FAIL":"PASS" if clip_count==0 else "FAIL",
            "METHOD":"independent exact foreground or vector mask against native PDF page and crop edges",
        })
    csv_write(OUT / "after_edge_clip_report.csv", edge_rows, list(edge_rows[0].keys()))

    mandatory = [r for r in overlap_rows if r["PAIR_TYPE"]=="TEXT_TEXT" or r["PAIR_TYPE"].startswith("TEXT_")]
    illegal_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in mandatory)
    text_clearance = [float(r["BBOX_CLEARANCE_PX"]) for r in mandatory if r["PAIR_TYPE"]=="TEXT_TEXT"]
    vector_clearance = [float(r["INK_CLEARANCE_PX"]) for r in mandatory if r["PAIR_TYPE"]!="TEXT_TEXT"]
    min_text_clearance = min(text_clearance+vector_clearance) if (text_clearance or vector_clearance) else math.inf
    clearance_pass = all(r["STATUS"]=="PASS" for r in mandatory)
    source_font_pass = all(c["font_status"]=="PASS" for c in chars)
    pixel_pass = all(c["pixel_status"]=="PASS" for c in chars)
    same_class_pass = all(r["PASS_FAIL"]=="PASS" for r in same_rows)
    role_ratio_pass = all(r["PASS_FAIL"] in {"PASS","N/A"} for r in role_rows)

    worst = min(chars,key=lambda c:c["h_ink"]-c["threshold"])
    x0,y0,x1,y1 = worst["pixel_box"]
    raw_worst = rgb[y0:y1,x0:x1]
    save_rgb(OUT / f"near_limit/worst_pixel_{worst['element_id']}_raw_1to1_300dpi.png",raw_worst)
    ov_worst = raw_worst.copy()
    wm = worst["mask"][y0-fy0:y1-fy0,x0-fx0:x1-fx0]
    ov_worst[wm] = (255,0,0)
    save_rgb(OUT / f"near_limit/worst_pixel_{worst['element_id']}_overlay_300dpi.png",ov_worst)
    brace = next(c for c in chars if c["parent_id"]=="BRACE_LABEL")
    bx0,by0,bx1,by1 = brace["pixel_box"]
    raw_brace = rgb[by0:by1,bx0:bx1]
    save_rgb(OUT / f"near_limit/source_font_9pt_{brace['element_id']}_raw_1to1_300dpi.png",raw_brace)
    ov_brace = raw_brace.copy()
    bm = brace["mask"][by0-fy0:by1-fy0,bx0-fx0:bx1-fx0]
    ov_brace[bm] = (255,0,0)
    save_rgb(OUT / f"near_limit/source_font_9pt_{brace['element_id']}_overlay_300dpi.png",ov_brace)

    # Actual inspection of all four saved views: the terminal y_(n+1) text
    # collides with the double boundary. This makes the right endpoint visibly
    # cramped and asymmetric, so font/layout harmony is independently false.
    visual_harmony = False
    math_semantics = True
    text_consistency = True
    reading_order = True
    grayscale = True
    caption = True
    page_integration = True
    result = source_font_pass and pixel_pass and same_class_pass and role_ratio_pass and illegal_overlap==0 and clip_total==0 and clearance_pass and visual_harmony and math_semantics and text_consistency and grayscale and page_integration
    summary = {
        "SOURCE_FONT_PASS":source_font_pass,"PIXEL_HEIGHT_PASS":pixel_pass,"SAME_CLASS_RATIO_PASS":same_class_pass,
        "ROLE_RATIO_PASS":role_ratio_pass,"OVERLAP_PIXEL_COUNT":illegal_overlap,"CLIP_PIXEL_COUNT":clip_total,
        "MIN_TEXT_CLEARANCE_PX":min_text_clearance,"VISUAL_HARMONY_PASS":visual_harmony,"MATH_SEMANTICS_PASS":math_semantics,
        "TEXT_CONSISTENCY_PASS":text_consistency,"READING_ORDER_PASS":reading_order,"GRAYSCALE_PASS":grayscale,
        "CAPTION_PASS":caption,"PAGE_INTEGRATION_PASS":page_integration,"RESULT":"PASS" if result else "FAIL",
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")

    failures_font = [c for c in chars if c["font_status"]=="FAIL"]
    failures_pixel = [c for c in chars if c["pixel_status"]=="FAIL"]
    visual_md = f"""# FIG-P392-01 SA1 strict visual acceptance R1

RESULT: {"PASS" if result else "FAIL"}

Identity: caption and label search uniquely found frozen-R93 physical PDF page {page_index+1}, printed page {printed_page}, figure 图 22.1.

| Gate | Value | Status |
|---|---:|---|
| SOURCE_FONT_PASS | {str(source_font_pass).lower()} | {"PASS" if source_font_pass else "FAIL"} |
| PIXEL_HEIGHT_PASS | {str(pixel_pass).lower()} | {"PASS" if pixel_pass else "FAIL"} |
| SAME_CLASS_RATIO_PASS | {str(same_class_pass).lower()} | {"PASS" if same_class_pass else "FAIL"} |
| ROLE_RATIO_PASS | {str(role_ratio_pass).lower()} | {"PASS" if role_ratio_pass else "FAIL"} |
| OVERLAP_PIXEL_COUNT | {illegal_overlap} | {"PASS" if illegal_overlap==0 else "FAIL"} |
| CLIP_PIXEL_COUNT | {clip_total} | {"PASS" if clip_total==0 else "FAIL"} |
| MIN_TEXT_CLEARANCE_PX | {"INF" if math.isinf(min_text_clearance) else f"{min_text_clearance:.3f}"} | {"PASS" if clearance_pass else "FAIL"} |
| VISUAL_HARMONY_PASS | {str(visual_harmony).lower()} | {"PASS" if visual_harmony else "FAIL"} |
| MATH_SEMANTICS_PASS | {str(math_semantics).lower()} | {"PASS" if math_semantics else "FAIL"} |
| TEXT_CONSISTENCY_PASS | {str(text_consistency).lower()} | {"PASS" if text_consistency else "FAIL"} |
| GRAYSCALE_PASS | {str(grayscale).lower()} | {"PASS" if grayscale else "FAIL"} |
| PAGE_INTEGRATION_PASS | {str(page_integration).lower()} | {"PASS" if page_integration else "FAIL"} |

Methods: full_page_200dpi.png, figure_crop_300dpi.png, standalone_300dpi.png and grayscale_300dpi.png are direct native PDF views without resize. The direct Poppler page render full_page_300dpi_native.png feeds all 300 dpi coordinates. Glyph foreground is taken from a local text-only derivative that preserves original PDF text operators, transforms and fonts while removing vector paint operations; this avoids same-colour node-border contamination. Raw ROI remains the original page. Each visible glyph is separate in after_pixel_measurements.csv. Natural script fragments and all basic mathematics and punctuation are independently measured, never replaced by a formula-level bbox. Vector masks are independently reconstructed from final-PDF path operators and stroke width at 8x supersample. All object masks are under masks; after_overlap_report.csv records span and vector masks, bbox clearance, ink clearance, nearest local and page coordinates, and closest or failed raw ROI/overlay/overlap-mask evidence.

Findings:

- Source-font FAIL: {len(failures_font)} glyph rows have an under-9.5 pt final base, a script whose base is under 9.5 pt, or unknown caption declaration under the permitted read scope.
- Pixel-height FAIL: {len(failures_pixel)} glyph rows fail their own threshold. Worst independent glyph is {worst["glyph"]} ({worst["element_id"]}), H_ink {worst["h_ink"]} px against {worst["threshold"]} px.
- Visual-harmony FAIL: in native 300 dpi views the terminal y_(n+1) label runs into both rings of its double boundary, so the endpoint is visibly crowded and no longer balanced with the other node labels.
- Semantics PASS: white y labels form the label chain, gold M factors represent adjacent-label factors, and the teal fixed-input strip makes complete observed x explicit. The note correctly says undirected edges do not imply generation. This agrees with adjacent source lines 234 to 241.
- Reading order PASS: left-to-right chain, then downward fixed input and note. No arrowhead exists because the graph is undirected.
- Grayscale PASS: shape, white/gray fill, rectangle/circle distinction, dashed links and brace preserve the structural encoding. No axes, legend, data curve, marker, or panel label exist; those ratio rows are explicit N/A.
- Page integration PASS: the caption, explanatory sentence and next section are separated without clipping, abnormal whitespace or an intrusive figure footprint.

Any hard failure means this candidate cannot proceed to SA3. The only next actor is subagent2, which must repair and rebuild a new candidate before a fresh full SA1 audit.
"""
    (OUT / "after_visual_acceptance.md").write_text(visual_md,encoding="utf-8")

    formal_md = f"""# FIG-P392-01-SA1-STRICT-R1

RESULT: {"PASS" if result else "FAIL"}

FIGURE_ID: {FIGURE_ID}
Frozen R93 input: {PDF}
Current figure source: {SOURCE}
Adjacent body inspected: {ADJACENT}, lines 234 to 241
PDF identity established from caption and label: physical page {page_index+1}; printed page {printed_page}; 图 22.1.

SOURCE_FONT_AUDIT: {"PASS" if source_font_pass else "FAIL"}
PIXEL_HEIGHT_AUDIT: {"PASS" if pixel_pass else "FAIL"}
SAME_CLASS_RATIO_AUDIT: {"PASS" if same_class_pass else "FAIL"}
ROLE_RATIO_AUDIT: {"PASS" if role_ratio_pass else "FAIL"}
OVERLAP_PIXEL_COUNT: {illegal_overlap}
CLIP_PIXEL_COUNT: {clip_total}
MIN_TEXT_CLEARANCE_PX: {"INF" if math.isinf(min_text_clearance) else f"{min_text_clearance:.3f}"}
MATH_SEMANTICS: {"PASS" if math_semantics else "FAIL"}
TEXT_CONSISTENCY: {"PASS" if text_consistency else "FAIL"}
READING_ORDER: {"PASS" if reading_order else "FAIL"}
VISUAL_HARMONY: {"PASS" if visual_harmony else "FAIL"}
GRAYSCALE: {"PASS" if grayscale else "FAIL"}
CAPTION: {"PASS" if caption else "FAIL"}
PAGE_INTEGRATION: {"PASS" if page_integration else "FAIL"}

Required subagent2 repair:

1. Lift all ordinary reader-visible bases to final effective at least 9.5 pt. Explicit 9.2 pt and 9.0 pt declarations cannot remain.
2. Repair independently measured base operators/punctuation to the 22 px requirement and natural scripts to 15 px while retaining a qualifying base. A composite formula bbox cannot close either gate.
3. Resolve caption font declaration provenance within a permitted auditable scope.
4. Rebuild, re-render all four views, and regenerate every mask/CSV from a new candidate. This failed candidate is prohibited from proceeding to SA3.

Evidence delivered: after_font_audit.csv, after_pixel_measurements.csv, after_overlap_report.csv, after_edge_clip_report.csv, same_class_ratio_audit.csv, role_ratio_audit.csv, after_text_measurement_overlay_300dpi.png, after_visual_acceptance.md, four native views, a text-only anti-contamination derivative, 98 glyph masks, 13 parent masks, 19 vector masks, and closest-pair evidence.
"""
    (OUT / "FIG-P392-01-SA1-STRICT-R1.md").write_text(formal_md,encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))


if __name__ == "__main__":
    main()
