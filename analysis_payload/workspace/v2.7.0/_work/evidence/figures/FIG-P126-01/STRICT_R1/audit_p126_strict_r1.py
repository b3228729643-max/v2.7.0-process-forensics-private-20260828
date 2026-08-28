from __future__ import annotations

import copy
import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from scipy.spatial import cKDTree


EVIDENCE_DIR = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P126-01\STRICT_R1")
OFFICIAL_PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r90_fullbook\main_full.pdf")
SOURCE_FILE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex")
CONTEXT_FILE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C08.tex")
STANDALONE_PDF = EVIDENCE_DIR / "standalone_wrapper.pdf"
PAGE_INDEX = 136
PAGE_NUMBER = 137
SCALE_300 = 300.0 / 72.0


@dataclass
class Mask:
    element_id: str
    obj_class: str
    bbox: tuple[int, int, int, int]
    pixels: np.ndarray

    def coordinates(self) -> np.ndarray:
        yy, xx = np.nonzero(self.pixels)
        return np.column_stack((yy + self.bbox[1], xx + self.bbox[0]))


TEXT_ELEMENTS = [
    dict(element_id="T-X0-BASE", indices=[63], panel="P1", role="ANNOTATION", source_line=44,
         source_declared_pt=9.2, resolved_pt=9.2, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="X0"),
    dict(element_id="T-X0-SCRIPT", indices=[64, 65, 66], panel="P1", role="ANNOTATION_SCRIPT", source_line=44,
         source_declared_pt=9.2, resolved_pt=6.44, text="(0)", script_class="NATURAL_SCRIPT_DIGIT", threshold=15,
         semantic_group="X0"),
    *[
        dict(element_id=f"T-STEP-{n}", indices=[66 + n], panel="P1", role="STEP_NUMBER", source_line=source_line,
             source_declared_pt=8.6, resolved_pt=8.6, text=str(n), script_class="DIGIT", threshold=24,
             semantic_group=f"STEP{n}")
        for n, source_line in [(1, 45), (2, 46), (3, 47), (4, 48), (5, 49), (6, 50), (7, 52)]
    ],
    dict(element_id="T-XSTAR-BASE", indices=[79], panel="P1", role="ANNOTATION", source_line=61,
         source_declared_pt=9.2, resolved_pt=9.2, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="XSTAR"),
    dict(element_id="T-XSTAR-SCRIPT", indices=[80], panel="P1", role="ANNOTATION_SCRIPT", source_line=61,
         source_declared_pt=9.2, resolved_pt=6.44, text="*", script_class="NATURAL_SCRIPT_OPERATOR", threshold=15,
         semantic_group="XSTAR"),
    dict(element_id="T-XAXIS-BASE", indices=[91], panel="P1", role="AXIS_LABEL", source_line=16,
         source_declared_pt=9.4, resolved_pt=10.0, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="XAXIS"),
    dict(element_id="T-XAXIS-SUB", indices=[92], panel="P1", role="AXIS_LABEL_SCRIPT", source_line=16,
         source_declared_pt=9.4, resolved_pt=9.0, text="1", script_class="NATURAL_SCRIPT_DIGIT", threshold=15,
         semantic_group="XAXIS"),
    dict(element_id="T-YAXIS-BASE", indices=[93], panel="P1", role="AXIS_LABEL", source_line=16,
         source_declared_pt=9.4, resolved_pt=10.0, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="YAXIS"),
    dict(element_id="T-YAXIS-SUB", indices=[94], panel="P1", role="AXIS_LABEL_SCRIPT", source_line=16,
         source_declared_pt=9.4, resolved_pt=9.0, text="2", script_class="NATURAL_SCRIPT_DIGIT", threshold=15,
         semantic_group="YAXIS"),
    dict(element_id="T-LEG1-CJK", indices=[96, 97], panel="P1", role="LEGEND", source_line=64,
         source_declared_pt=9.2, resolved_pt=10.0, text="更新", script_class="CJK", threshold=30,
         semantic_group="LEG1"),
    dict(element_id="T-LEG1-X", indices=[98], panel="P1", role="LEGEND", source_line=64,
         source_declared_pt=9.2, resolved_pt=10.0, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="LEG1"),
    dict(element_id="T-LEG1-SUB", indices=[99], panel="P1", role="LEGEND_SCRIPT", source_line=64,
         source_declared_pt=9.2, resolved_pt=9.0, text="1", script_class="NATURAL_SCRIPT_DIGIT", threshold=15,
         semantic_group="LEG1"),
    dict(element_id="T-LEG2-CJK", indices=[101, 102], panel="P1", role="LEGEND", source_line=66,
         source_declared_pt=9.2, resolved_pt=10.0, text="更新", script_class="CJK", threshold=30,
         semantic_group="LEG2"),
    dict(element_id="T-LEG2-X", indices=[103], panel="P1", role="LEGEND", source_line=66,
         source_declared_pt=9.2, resolved_pt=10.0, text="x", script_class="LATIN_LOWER", threshold=17,
         semantic_group="LEG2"),
    dict(element_id="T-LEG2-SUB", indices=[104], panel="P1", role="LEGEND_SCRIPT", source_line=66,
         source_declared_pt=9.2, resolved_pt=9.0, text="2", script_class="NATURAL_SCRIPT_DIGIT", threshold=15,
         semantic_group="LEG2"),
    dict(element_id="T-CAP-LABEL-CJK", indices=[105], panel="CAPTION", role="CAPTION_LABEL", source_line=69,
         source_declared_pt=10.0, resolved_pt=10.0, text="图", script_class="CJK", threshold=30,
         semantic_group="CAPLABEL"),
    dict(element_id="T-CAP-LABEL-DIGITS", indices=[106, 107, 108], panel="CAPTION", role="CAPTION_LABEL", source_line=69,
         source_declared_pt=10.0, resolved_pt=10.0, text="8.1", script_class="DIGIT", threshold=24,
         semantic_group="CAPLABEL"),
    dict(element_id="T-CAP-TEXT", indices=list(range(109, 141)), panel="CAPTION", role="CAPTION_TEXT", source_line=69,
         source_declared_pt=10.0, resolved_pt=10.0,
         text="坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。",
         script_class="CJK", threshold=30, semantic_group="CAPTEXT"),
]


GRAPHIC_ELEMENTS = [
    dict(element_id="G-AXIS-X", indices=[33, 34], obj_class="LINE_ARROW", role="AXIS"),
    dict(element_id="G-AXIS-Y", indices=[35, 36], obj_class="LINE_ARROW", role="AXIS"),
    dict(element_id="G-CONTOUR-OUTER", indices=[37], obj_class="DATA_CURVE", role="CONTOUR"),
    dict(element_id="G-CONTOUR-2", indices=[38], obj_class="DATA_CURVE", role="CONTOUR"),
    dict(element_id="G-CONTOUR-3", indices=[39], obj_class="DATA_CURVE", role="CONTOUR"),
    dict(element_id="G-CONTOUR-INNER", indices=[40], obj_class="DATA_CURVE", role="CONTOUR"),
    dict(element_id="G-X1-ARROW-1", indices=[41, 42, 43], obj_class="LINE_ARROW", role="X1_UPDATE"),
    dict(element_id="G-X1-ARROW-2", indices=[44, 45, 46], obj_class="LINE_ARROW", role="X1_UPDATE"),
    dict(element_id="G-X1-ARROW-3", indices=[47, 48, 49], obj_class="LINE_ARROW", role="X1_UPDATE"),
    dict(element_id="G-X2-ARROW-1", indices=[50, 51, 52], obj_class="LINE_ARROW", role="X2_UPDATE"),
    dict(element_id="G-X2-ARROW-2", indices=[53, 54, 55], obj_class="LINE_ARROW", role="X2_UPDATE"),
    dict(element_id="G-X2-ARROW-3", indices=[56, 57, 58], obj_class="LINE_ARROW", role="X2_UPDATE"),
    dict(element_id="G-X2-ARROW-4", indices=[59, 60, 61], obj_class="LINE_ARROW", role="X2_UPDATE"),
    dict(element_id="G-MARK-Q0", indices=[62], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q2", indices=[74], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q4", indices=[75], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q6", indices=[76], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-OPTIMUM", indices=[77, 78], obj_class="MARKER", role="OPTIMUM_MARKER"),
    dict(element_id="G-MARK-Q1", indices=[81, 82], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q3", indices=[83, 84], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q5", indices=[85, 86], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-MARK-Q7", indices=[87, 88], obj_class="MARKER", role="ITERATE_MARKER"),
    dict(element_id="G-LEGEND-SAMPLE-1", indices=[95], obj_class="LINE_ARROW", role="LEGEND_SAMPLE"),
    dict(element_id="G-LEGEND-SAMPLE-2", indices=[100], obj_class="LINE_ARROW", role="LEGEND_SAMPLE"),
]


ROLE_COMPOSITES = [
    dict(element_id="R-STEP-BASE", members=[f"T-STEP-{n}" for n in range(1, 8)], role="BASE", limits=(1.0, 1.0)),
    dict(element_id="R-AXIS-X", members=["T-XAXIS-BASE", "T-XAXIS-SUB"], role="AXIS_LABEL", limits=(1.0, 1.18)),
    dict(element_id="R-AXIS-Y", members=["T-YAXIS-BASE", "T-YAXIS-SUB"], role="AXIS_LABEL", limits=(1.0, 1.18)),
    dict(element_id="R-LEGEND-1", members=["T-LEG1-CJK", "T-LEG1-X", "T-LEG1-SUB"], role="LEGEND", limits=(0.95, 1.10)),
    dict(element_id="R-LEGEND-2", members=["T-LEG2-CJK", "T-LEG2-X", "T-LEG2-SUB"], role="LEGEND", limits=(0.95, 1.10)),
    dict(element_id="R-X0", members=["T-X0-BASE"], role="ANNOTATION", limits=(0.95, 1.10)),
    dict(element_id="R-XSTAR", members=["T-XSTAR-BASE"], role="ANNOTATION", limits=(0.95, 1.10)),
]

SCRIPT_PARENT_PT = {
    "T-X0-SCRIPT": 9.2,
    "T-XSTAR-SCRIPT": 9.2,
    "T-XAXIS-SUB": 10.0,
    "T-YAXIS-SUB": 10.0,
    "T-LEG1-SUB": 10.0,
    "T-LEG2-SUB": 10.0,
}


def save_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pixmap_rgb(page: fitz.Page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def px_rect(rect_pt: tuple[float, float, float, float], dpi: int = 300) -> tuple[int, int, int, int]:
    scale = dpi / 72.0
    x0, y0, x1, y1 = rect_pt
    return (math.floor(x0 * scale), math.floor(y0 * scale), math.ceil(x1 * scale), math.ceil(y1 * scale))


def threshold_mask(rgb: np.ndarray) -> np.ndarray:
    return np.max(255 - rgb.astype(np.int16), axis=2) >= 20


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return (0, 0, 0, 0)
    return (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)


def render_selected_svg(root: etree._Element, indices: list[int], element_id: str, obj_class: str) -> Mask:
    ns = "http://www.w3.org/2000/svg"
    selected = etree.Element(
        f"{{{ns}}}svg",
        nsmap=root.nsmap,
        version="1.1",
        width="595.276pt",
        height="841.89pt",
        viewBox="0 0 595.276 841.89",
    )
    selected.append(copy.deepcopy(root[0]))
    for index in indices:
        selected.append(copy.deepcopy(root[index]))
    svg_bytes = etree.tostring(selected)
    svg_doc = fitz.open(stream=svg_bytes, filetype="svg")
    pix = svg_doc[0].get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False)
    rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    full_mask = threshold_mask(rgb)
    bbox = tight_bbox(full_mask)
    if bbox == (0, 0, 0, 0):
        cropped = np.zeros((0, 0), dtype=bool)
    else:
        x0, y0, x1, y1 = bbox
        cropped = full_mask[y0:y1, x0:x1].copy()
    return Mask(element_id, obj_class, bbox, cropped)


def overlap_and_clearance(a: Mask, b: Mask) -> tuple[int, float, float]:
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    overlap = 0
    if ix0 < ix1 and iy0 < iy1:
        ac = a.pixels[iy0 - ay0:iy1 - ay0, ix0 - ax0:ix1 - ax0]
        bc = b.pixels[iy0 - by0:iy1 - by0, ix0 - bx0:ix1 - bx0]
        overlap = int(np.count_nonzero(ac & bc))
    if overlap:
        return overlap, 0.0, 0.0
    ca = a.coordinates()
    cb = b.coordinates()
    if not len(ca) or not len(cb):
        return overlap, math.inf, math.inf
    if len(ca) > len(cb):
        ca, cb = cb, ca
    tree = cKDTree(cb)
    center_distance = float(np.min(tree.query(ca, k=1, workers=1)[0]))
    conservative_empty_gap = max(0.0, center_distance - 1.0)
    return overlap, center_distance, conservative_empty_gap


def union_mask(masks: dict[str, Mask], members: list[str], element_id: str, obj_class: str = "TEXT") -> Mask:
    selected = [masks[m] for m in members]
    x0 = min(m.bbox[0] for m in selected)
    y0 = min(m.bbox[1] for m in selected)
    x1 = max(m.bbox[2] for m in selected)
    y1 = max(m.bbox[3] for m in selected)
    result = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for m in selected:
        mx0, my0, mx1, my1 = m.bbox
        result[my0 - y0:my1 - y0, mx0 - x0:mx1 - x0] |= m.pixels
    return Mask(element_id, obj_class, (x0, y0, x1, y1), result)


def save_mask_png(mask: Mask, path: Path, pad: int = 4) -> None:
    if mask.pixels.size == 0:
        Image.new("L", (1, 1), 255).save(path)
        return
    image = np.full((mask.pixels.shape[0] + 2 * pad, mask.pixels.shape[1] + 2 * pad), 255, dtype=np.uint8)
    image[pad:-pad, pad:-pad][mask.pixels] = 0
    Image.fromarray(image, "L").save(path)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    mask_dir = EVIDENCE_DIR / "masks"
    mask_dir.mkdir(exist_ok=True)

    reader = PdfReader(str(OFFICIAL_PDF))
    writer = PdfWriter()
    writer.add_page(reader.pages[PAGE_INDEX])
    with (EVIDENCE_DIR / "official_page_137.pdf").open("wb") as stream:
        writer.write(stream)

    official_doc = fitz.open(OFFICIAL_PDF)
    page = official_doc[PAGE_INDEX]
    full_200 = pixmap_rgb(page, 200)
    full_300 = pixmap_rgb(page, 300)
    full_200.save(EVIDENCE_DIR / "full_page_200dpi.png")
    full_300.save(EVIDENCE_DIR / "full_page_300dpi.png")

    figure_with_caption_pt = (105.0, 55.0, 475.0, 263.0)
    figure_only_pt = (145.0, 55.0, 440.0, 243.0)
    figure_with_caption_px = px_rect(figure_with_caption_pt)
    figure_only_px = px_rect(figure_only_pt)
    figure_crop = full_300.crop(figure_with_caption_px)
    figure_crop.save(EVIDENCE_DIR / "figure_crop_300dpi.png")
    full_300.crop(figure_only_px).save(EVIDENCE_DIR / "figure_only_300dpi.png")
    figure_crop.convert("L").save(EVIDENCE_DIR / "grayscale_300dpi.png")

    roi_specs = {
        "roi_x0_300dpi_1to1.png": (175.0, 67.0, 222.0, 131.0),
        "roi_steps_300dpi_1to1.png": (175.0, 98.0, 316.0, 168.0),
        "roi_xstar_300dpi_1to1.png": (278.0, 126.0, 322.0, 172.0),
        "roi_axes_300dpi_1to1.png": (286.0, 60.0, 380.0, 160.0),
        "roi_legend_300dpi_1to1.png": (202.0, 218.0, 326.0, 243.0),
    }
    for name, rect in roi_specs.items():
        full_300.crop(px_rect(rect)).save(EVIDENCE_DIR / name)

    svg_text = page.get_svg_image(matrix=fitz.Matrix(1, 1), text_as_path=True)
    svg_path = EVIDENCE_DIR / "official_page_137.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    root = etree.fromstring(svg_text.encode("utf-8"))

    masks: dict[str, Mask] = {}
    for element in TEXT_ELEMENTS:
        m = render_selected_svg(root, element["indices"], element["element_id"], "TEXT")
        masks[m.element_id] = m
        save_mask_png(m, mask_dir / f"{m.element_id}.png")
    for element in GRAPHIC_ELEMENTS:
        m = render_selected_svg(root, element["indices"], element["element_id"], element["obj_class"])
        masks[m.element_id] = m
        save_mask_png(m, mask_dir / f"{m.element_id}.png")

    # Render the independently compiled source page and crop its only foreground region without resizing.
    standalone_doc = fitz.open(STANDALONE_PDF)
    standalone_full = pixmap_rgb(standalone_doc[0], 300)
    standalone_full.save(EVIDENCE_DIR / "standalone_full_page_300dpi.png")
    standalone_np = np.asarray(standalone_full)
    standalone_fg = threshold_mask(standalone_np)
    sx0, sy0, sx1, sy1 = tight_bbox(standalone_fg)
    margin = 24
    sx0, sy0 = max(0, sx0 - margin), max(0, sy0 - margin)
    sx1, sy1 = min(standalone_full.width, sx1 + margin), min(standalone_full.height, sy1 + margin)
    standalone_full.crop((sx0, sy0, sx1, sy1)).save(EVIDENCE_DIR / "standalone_300dpi.png")

    # Exact PDF text-span metadata, independent of source declarations.
    span_rows = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if 55 <= y0 <= 263:
                    span_rows.append({
                        "TEXT": span["text"], "PDF_FONT_SIZE_BP": f"{span['size']:.6f}",
                        "FONT": span["font"], "COLOR": f"0x{span['color']:06x}",
                        "BBOX_X0_PT": f"{x0:.6f}", "BBOX_Y0_PT": f"{y0:.6f}",
                        "BBOX_X1_PT": f"{x1:.6f}", "BBOX_Y1_PT": f"{y1:.6f}",
                    })
    save_csv(EVIDENCE_DIR / "official_pdf_text_spans.csv",
             ["TEXT", "PDF_FONT_SIZE_BP", "FONT", "COLOR", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT"],
             span_rows)

    graphic_rows = []
    for element in GRAPHIC_ELEMENTS:
        m = masks[element["element_id"]]
        graphic_rows.append({
            "ELEMENT_ID": m.element_id, "CLASS": element["obj_class"], "ROLE": element["role"],
            "SVG_CHILD_INDICES": " ".join(map(str, element["indices"])),
            "BBOX_X0_PX": m.bbox[0], "BBOX_Y0_PX": m.bbox[1], "BBOX_X1_PX": m.bbox[2], "BBOX_Y1_PX": m.bbox[3],
            "MASK_FILE": f"masks/{m.element_id}.png", "FOREGROUND_PIXEL_COUNT": int(m.pixels.sum()),
        })
    save_csv(EVIDENCE_DIR / "graphic_elements.csv",
             ["ELEMENT_ID", "CLASS", "ROLE", "SVG_CHILD_INDICES", "BBOX_X0_PX", "BBOX_Y0_PX", "BBOX_X1_PX", "BBOX_Y1_PX", "MASK_FILE", "FOREGROUND_PIXEL_COUNT"],
             graphic_rows)

    text_ids = [e["element_id"] for e in TEXT_ELEMENTS]
    graphic_ids = [e["element_id"] for e in GRAPHIC_ELEMENTS]
    text_meta = {e["element_id"]: e for e in TEXT_ELEMENTS}
    graphic_meta = {e["element_id"]: e for e in GRAPHIC_ELEMENTS}
    pair_rows = []

    for i, a_id in enumerate(text_ids):
        for b_id in text_ids[i + 1:]:
            a_meta, b_meta = text_meta[a_id], text_meta[b_id]
            same_semantic = a_meta["semantic_group"] == b_meta["semantic_group"]
            overlap, center, gap = overlap_and_clearance(masks[a_id], masks[b_id])
            threshold = 0 if same_semantic else 4
            pair_rows.append({
                "A_ID": a_id, "A_CLASS": "TEXT", "B_ID": b_id, "B_CLASS": "TEXT",
                "RELATION": "SAME_COMPOSITE" if same_semantic else "INDEPENDENT_TEXT",
                "OVERLAP_PIXEL_COUNT": overlap, "CENTER_DISTANCE_PX": f"{center:.3f}",
                "CONSERVATIVE_EMPTY_CLEARANCE_PX": f"{gap:.3f}", "REQUIRED_CLEARANCE_PX": threshold,
                "PASS_FAIL": "N/A" if same_semantic else ("PASS" if overlap == 0 and gap >= threshold else "FAIL"),
                "EVIDENCE_ROI": "",
            })
        for b_id in graphic_ids:
            overlap, center, gap = overlap_and_clearance(masks[a_id], masks[b_id])
            pair_rows.append({
                "A_ID": a_id, "A_CLASS": "TEXT", "B_ID": b_id, "B_CLASS": graphic_meta[b_id]["obj_class"],
                "RELATION": "TEXT_GRAPHIC", "OVERLAP_PIXEL_COUNT": overlap,
                "CENTER_DISTANCE_PX": f"{center:.3f}", "CONSERVATIVE_EMPTY_CLEARANCE_PX": f"{gap:.3f}",
                "REQUIRED_CLEARANCE_PX": 3,
                "PASS_FAIL": "PASS" if overlap == 0 and gap >= 3 else "FAIL", "EVIDENCE_ROI": "",
            })
    # Native 1:1 risk overlays: red=A mask, blue=B mask, yellow=intersection.
    risk_dir = EVIDENCE_DIR / "risk_rois"
    risk_dir.mkdir(exist_ok=True)
    for row in pair_rows:
        if row["PASS_FAIL"] != "FAIL":
            continue
        a, b = masks[row["A_ID"]], masks[row["B_ID"]]
        margin = 16
        x0 = max(0, min(a.bbox[0], b.bbox[0]) - margin)
        y0 = max(0, min(a.bbox[1], b.bbox[1]) - margin)
        x1 = min(full_300.width, max(a.bbox[2], b.bbox[2]) + margin)
        y1 = min(full_300.height, max(a.bbox[3], b.bbox[3]) + margin)
        roi = np.asarray(full_300.crop((x0, y0, x1, y1))).copy()
        am = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        bm = np.zeros_like(am)
        ax0, ay0, ax1, ay1 = a.bbox
        bx0, by0, bx1, by1 = b.bbox
        am[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = a.pixels
        bm[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0] = b.pixels
        roi[am & ~bm] = np.array([230, 30, 30], dtype=np.uint8)
        roi[bm & ~am] = np.array([20, 80, 230], dtype=np.uint8)
        roi[am & bm] = np.array([255, 210, 0], dtype=np.uint8)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{row['A_ID']}__{row['B_ID']}")
        roi_name = f"risk_{safe_name}_300dpi_1to1.png"
        roi_image = Image.fromarray(roi, "RGB")
        roi_draw = ImageDraw.Draw(roi_image)
        roi_draw.text((3, 3), f"A={row['A_ID']} (red); B={row['B_ID']} (blue); overlap=yellow", fill=(0, 0, 0), font=ImageFont.load_default())
        roi_image.save(risk_dir / roi_name)
        row["EVIDENCE_ROI"] = f"risk_rois/{roi_name}"
    pair_fields = ["A_ID", "A_CLASS", "B_ID", "B_CLASS", "RELATION", "OVERLAP_PIXEL_COUNT", "CENTER_DISTANCE_PX",
                   "CONSERVATIVE_EMPTY_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX", "PASS_FAIL", "EVIDENCE_ROI"]
    save_csv(EVIDENCE_DIR / "pairwise_object_checks.csv", pair_fields, pair_rows)

    hard_pairs = [r for r in pair_rows if r["PASS_FAIL"] == "FAIL"]
    near_pairs = sorted(
        [r for r in pair_rows if r["PASS_FAIL"] not in ("N/A", "FAIL")],
        key=lambda r: float(r["CONSERVATIVE_EMPTY_CLEARANCE_PX"]),
    )[:40]
    save_csv(EVIDENCE_DIR / "high_risk_pairs.csv", pair_fields, hard_pairs + near_pairs)

    class_groups: dict[tuple[str, str], list[int]] = {}
    for element in TEXT_ELEMENTS:
        h = masks[element["element_id"]].bbox[3] - masks[element["element_id"]].bbox[1]
        class_groups.setdefault((element["role"], element["script_class"]), []).append(h)

    source_rows = []
    for element in TEXT_ELEMENTS:
        m = masks[element["element_id"]]
        h = m.bbox[3] - m.bbox[1]
        group = class_groups[(element["role"], element["script_class"])]
        median = float(np.median(group))
        ratio = h / median if median else math.nan
        relevant = [r for r in pair_rows if r["A_ID"] == element["element_id"] and r["PASS_FAIL"] != "N/A"]
        max_tt_overlap = max([int(r["OVERLAP_PIXEL_COUNT"]) for r in relevant if r["B_CLASS"] == "TEXT"] or [0])
        max_tg_overlap = max([int(r["OVERLAP_PIXEL_COUNT"]) for r in relevant if r["B_CLASS"] != "TEXT"] or [0])
        min_gap = min([float(r["CONSERVATIVE_EMPTY_CLEARANCE_PX"]) for r in relevant] or [math.inf])
        if "SCRIPT" in element["role"]:
            parent_pt = SCRIPT_PARENT_PT[element["element_id"]]
            source_pass = parent_pt >= 9.5
            source_reason = (f"natural script from parent base {parent_pt:.2f}pt >= 9.5pt" if source_pass
                             else f"parent base {parent_pt:.2f}pt < 9.5pt")
        else:
            source_pass = element["resolved_pt"] >= 9.5
            source_reason = (f"effective {element['resolved_pt']:.2f}pt >= 9.5pt" if source_pass
                             else f"effective {element['resolved_pt']:.2f}pt < 9.5pt")
        pixel_pass = h >= element["threshold"]
        ratio_pass = 0.92 <= ratio <= 1.08
        reasons = []
        if not source_pass:
            reasons.append(source_reason)
        if not pixel_pass:
            reasons.append(f"H_ink {h}px < {element['threshold']}px")
        if not ratio_pass:
            reasons.append(f"same-role/class ratio {ratio:.3f} outside [0.92,1.08]")
        if max_tt_overlap or max_tg_overlap:
            reasons.append(f"illegal overlap max(text={max_tt_overlap}, graphic={max_tg_overlap})")
        source_rows.append({
            "ELEMENT_ID": element["element_id"], "PANEL_ID": element["panel"], "ROLE": element["role"],
            "SOURCE_FILE": str(SOURCE_FILE), "SOURCE_LINE": element["source_line"],
            "SOURCE_DECLARED_PT": f"{element['source_declared_pt']:.2f}", "DECLARED_PT": f"{element['resolved_pt']:.2f}",
            "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{element['resolved_pt']:.2f}",
            "TEXT_SAMPLE": element["text"], "SCRIPT_CLASS": element["script_class"],
            "BBOX_X0": m.bbox[0], "BBOX_Y0": m.bbox[1], "BBOX_X1": m.bbox[2], "BBOX_Y1": m.bbox[3],
            "H_INK_PX": h, "PIXEL_THRESHOLD_PX": element["threshold"], "CLASS_MEDIAN_PX": f"{median:.3f}",
            "RATIO_TO_CLASS_MEDIAN": f"{ratio:.3f}", "ROLE_RATIO": "see role_ratio_checks.csv",
            "TEXT_TEXT_OVERLAP_PX": max_tt_overlap, "TEXT_GRAPHIC_OVERLAP_PX": max_tg_overlap,
            "MIN_CLEARANCE_PX": f"{min_gap:.3f}",
            "SOURCE_FONT_PASS": "true" if source_pass else "false", "SOURCE_FONT_REASON": source_reason,
            "PASS_FAIL": "PASS" if source_pass and pixel_pass and ratio_pass and max_tt_overlap == 0 and max_tg_overlap == 0 else "FAIL",
            "REASON": "; ".join(reasons) if reasons else "all per-element gates pass",
            "MASK_FILE": f"masks/{element['element_id']}.png",
        })
    source_fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "SOURCE_DECLARED_PT", "DECLARED_PT",
        "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1",
        "H_INK_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO",
        "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "SOURCE_FONT_PASS", "SOURCE_FONT_REASON",
        "PASS_FAIL", "REASON", "MASK_FILE",
    ]
    save_csv(EVIDENCE_DIR / "after_pixel_measurements.csv", source_fields, source_rows)
    font_rows = [{
        "ELEMENT_ID": row["ELEMENT_ID"], "SOURCE_LINE": row["SOURCE_LINE"],
        "SOURCE_DECLARED_PT": row["SOURCE_DECLARED_PT"], "DECLARED_PT": row["DECLARED_PT"],
        "GRAPHICS_SCALE": row["GRAPHICS_SCALE"], "EFFECTIVE_PT": row["EFFECTIVE_PT"],
        "PARENT_BASE_PT": f"{SCRIPT_PARENT_PT[row['ELEMENT_ID']]:.2f}" if row["ELEMENT_ID"] in SCRIPT_PARENT_PT else "",
        "PASS_FAIL": "PASS" if row["SOURCE_FONT_PASS"] == "true" else "FAIL", "REASON": row["SOURCE_FONT_REASON"],
    } for row in source_rows]
    save_csv(EVIDENCE_DIR / "source_font_audit.csv",
             ["ELEMENT_ID", "SOURCE_LINE", "SOURCE_DECLARED_PT", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PARENT_BASE_PT", "PASS_FAIL", "REASON"],
             font_rows)

    # Same-class source and pixel ratios.
    same_class_rows = []
    for (role, script_class), values in sorted(class_groups.items()):
        ids = [e["element_id"] for e in TEXT_ELEMENTS if e["role"] == role and e["script_class"] == script_class]
        effective = [text_meta[i]["resolved_pt"] for i in ids]
        source_ratio = max(effective) / min(effective) if effective else math.nan
        source_delta = max(effective) - min(effective) if effective else math.nan
        median = float(np.median(values))
        ratios = [(masks[i].bbox[3] - masks[i].bbox[1]) / median for i in ids]
        same_class_rows.append({
            "ROLE": role, "SCRIPT_CLASS": script_class, "ELEMENT_IDS": " ".join(ids),
            "SOURCE_MAX_MIN_RATIO": f"{source_ratio:.3f}", "SOURCE_DELTA_PT": f"{source_delta:.3f}",
            "PIXEL_HEIGHTS": " ".join(str(masks[i].bbox[3] - masks[i].bbox[1]) for i in ids),
            "PIXEL_RATIO_MIN": f"{min(ratios):.3f}", "PIXEL_RATIO_MAX": f"{max(ratios):.3f}",
            "PASS_FAIL": "PASS" if source_ratio <= 1.03 and source_delta <= 0.25 and min(ratios) >= 0.92 and max(ratios) <= 1.08 else "FAIL",
        })
    save_csv(EVIDENCE_DIR / "same_class_ratio_checks.csv",
             ["ROLE", "SCRIPT_CLASS", "ELEMENT_IDS", "SOURCE_MAX_MIN_RATIO", "SOURCE_DELTA_PT", "PIXEL_HEIGHTS", "PIXEL_RATIO_MIN", "PIXEL_RATIO_MAX", "PASS_FAIL"],
             same_class_rows)

    # Composite role heights are used for hierarchy; BASE is the median of step-number ink heights.
    base_height = float(np.median([masks[f"T-STEP-{n}"].bbox[3] - masks[f"T-STEP-{n}"].bbox[1] for n in range(1, 8)]))
    role_rows = []
    for spec in ROLE_COMPOSITES:
        if spec["element_id"] == "R-STEP-BASE":
            height = base_height
        else:
            composite = union_mask(masks, spec["members"], spec["element_id"])
            height = composite.bbox[3] - composite.bbox[1]
        ratio = height / base_height
        low, high = spec["limits"]
        role_rows.append({
            "ELEMENT_ID": spec["element_id"], "ROLE": spec["role"], "MEMBERS": " ".join(spec["members"]),
            "H_INK_PX": f"{height:.3f}", "BASE_H_INK_PX": f"{base_height:.3f}", "ROLE_RATIO": f"{ratio:.3f}",
            "ALLOWED_MIN": f"{low:.2f}", "ALLOWED_MAX": f"{high:.2f}",
            "PASS_FAIL": "PASS" if low <= ratio <= high else "FAIL",
        })
    save_csv(EVIDENCE_DIR / "role_ratio_checks.csv",
             ["ELEMENT_ID", "ROLE", "MEMBERS", "H_INK_PX", "BASE_H_INK_PX", "ROLE_RATIO", "ALLOWED_MIN", "ALLOWED_MAX", "PASS_FAIL"],
             role_rows)

    # Overlay on the unscaled native 300 dpi crop; labels are evidence annotations only.
    overlay = full_300.crop(figure_with_caption_px).copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    ox, oy = figure_with_caption_px[0], figure_with_caption_px[1]
    colors = {"TEXT": (210, 0, 0), "LINE_ARROW": (0, 90, 210), "DATA_CURVE": (125, 0, 180), "MARKER": (0, 130, 60)}
    for element_id, m in masks.items():
        x0, y0, x1, y1 = m.bbox
        if x1 < ox or x0 > figure_with_caption_px[2] or y1 < oy or y0 > figure_with_caption_px[3]:
            continue
        color = colors.get(m.obj_class, (0, 0, 0))
        box = (x0 - ox, y0 - oy, x1 - ox, y1 - oy)
        draw.rectangle(box, outline=color, width=1)
        draw.text((box[0], max(0, box[1] - 10)), element_id, fill=color, font=font)
    overlay.save(EVIDENCE_DIR / "element_bbox_overlay_300dpi_1to1.png")

    source_lines = SOURCE_FILE.read_text(encoding="utf-8").splitlines()
    context_lines = CONTEXT_FILE.read_text(encoding="utf-8").splitlines()
    log_text = (EVIDENCE_DIR / "standalone_wrapper.log").read_text(encoding="utf-8", errors="replace")
    hard_patterns = [r"LaTeX Error", r"Package .* Error", r"Undefined control sequence", r"Emergency stop", r"Fatal error", r"Float\(s\) lost", r"Overfull \\hbox", r"Underfull \\hbox"]
    hard_counts = {pattern: len(re.findall(pattern, log_text, flags=re.IGNORECASE)) for pattern in hard_patterns}

    min_pair_gap = min(float(r["CONSERVATIVE_EMPTY_CLEARANCE_PX"]) for r in pair_rows if r["PASS_FAIL"] != "N/A")
    min_text_text_gap = min(float(r["CONSERVATIVE_EMPTY_CLEARANCE_PX"]) for r in pair_rows if r["RELATION"] == "INDEPENDENT_TEXT")
    total_overlap_pairs = [r for r in pair_rows if int(r["OVERLAP_PIXEL_COUNT"]) > 0]
    total_failed_pairs = [r for r in pair_rows if r["PASS_FAIL"] == "FAIL"]
    total_overlap_pixels = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in total_overlap_pairs)
    all_masks = list(masks.values())
    min_text_to_page_edge = min(
        min(m.bbox[0], m.bbox[1], full_300.width - m.bbox[2], full_300.height - m.bbox[3])
        for m in (masks[e["element_id"]] for e in TEXT_ELEMENTS)
    )
    clip_pixel_count = 0 if all(
        0 <= m.bbox[0] < m.bbox[2] <= full_300.width and 0 <= m.bbox[1] < m.bbox[3] <= full_300.height
        for m in all_masks
    ) else -1
    render_manifest = [
        "FIGURE_ID=FIG-P126-01",
        f"OFFICIAL_PDF={OFFICIAL_PDF}",
        f"PHYSICAL_PAGE={PAGE_NUMBER}",
        "PAGE_INDEX_ZERO_BASED=136",
        f"OFFICIAL_PAGE_SIZE_PT={page.rect.width:.6f}x{page.rect.height:.6f}",
        f"FULL_PAGE_200DPI_PIXELS={full_200.width}x{full_200.height}",
        f"FULL_PAGE_300DPI_PIXELS={full_300.width}x{full_300.height}",
        "FULL_PAGE_RENDER=PyMuPDF get_pixmap matrix=(300/72,300/72), alpha=false; no resize",
        f"FIGURE_WITH_CAPTION_CROP_PT={figure_with_caption_pt}",
        f"FIGURE_WITH_CAPTION_CROP_PX={figure_with_caption_px}",
        f"FIGURE_ONLY_CROP_PT={figure_only_pt}",
        f"FIGURE_ONLY_CROP_PX={figure_only_px}",
        "MASK_RENDER=official PDF -> MuPDF SVG paths -> selected-object SVG -> MuPDF 300dpi; local background difference >=20/255",
        "CLEARANCE=Euclidean foreground-center distance minus 1 pixel (conservative empty-pixel gap)",
        f"STANDALONE_FULL_300DPI_PIXELS={standalone_full.width}x{standalone_full.height}",
        f"STANDALONE_TIGHT_CROP_PX={(sx0, sy0, sx1, sy1)}",
        f"TOTAL_ILLEGAL_OVERLAP_PAIRS={len(total_overlap_pairs)}",
        f"TOTAL_ILLEGAL_OVERLAP_PIXEL_INTERSECTIONS={total_overlap_pixels}",
        f"TOTAL_FAILED_OVERLAP_OR_CLEARANCE_PAIRS={len(total_failed_pairs)}",
        f"MIN_CONSERVATIVE_CLEARANCE_PX={min_pair_gap:.3f}",
        f"MIN_INDEPENDENT_TEXT_TEXT_CLEARANCE_PX={min_text_text_gap:.3f}",
        f"MIN_TEXT_TO_OFFICIAL_PAGE_EDGE_PX={min_text_to_page_edge}",
        f"CLIP_PIXEL_COUNT={clip_pixel_count}",
        f"STANDALONE_LOG_HARD_PATTERN_COUNTS={hard_counts}",
        "ROI_CROPS_PT=" + repr(roi_specs),
        "SOURCE_LINES_1_70_CAPTURED_IN=source_excerpt_numbered.txt",
        "CONTEXT_LINES_341_356_CAPTURED_IN=context_excerpt_numbered.txt",
    ]
    (EVIDENCE_DIR / "render_manifest.txt").write_text("\n".join(render_manifest) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "source_excerpt_numbered.txt").write_text(
        "\n".join(f"{i + 1}: {line}" for i, line in enumerate(source_lines)) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "context_excerpt_numbered.txt").write_text(
        "\n".join(f"{i + 1}: {context_lines[i]}" for i in range(340, 356)) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "standalone_log_hard_scan.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in hard_counts.items()) + "\n", encoding="utf-8")

    print(f"rendered official page {PAGE_NUMBER}: {full_300.width}x{full_300.height} at native 300dpi")
    print(f"text elements: {len(TEXT_ELEMENTS)}; graphic elements: {len(GRAPHIC_ELEMENTS)}")
    print(f"illegal overlap pairs: {len(total_overlap_pairs)}")
    print(f"minimum conservative clearance: {min_pair_gap:.3f}px")
    print(f"source-font gate failures: {sum(r['SOURCE_FONT_PASS'] == 'false' for r in source_rows)}")
    print(f"total per-element hard-gate failures: {sum(r['PASS_FAIL'] == 'FAIL' for r in source_rows)}")
    print(f"same-class failures: {sum(r['PASS_FAIL'] == 'FAIL' for r in same_class_rows)}")
    print(f"role-ratio failures: {sum(r['PASS_FAIL'] == 'FAIL' for r in role_rows)}")


if __name__ == "__main__":
    main()
