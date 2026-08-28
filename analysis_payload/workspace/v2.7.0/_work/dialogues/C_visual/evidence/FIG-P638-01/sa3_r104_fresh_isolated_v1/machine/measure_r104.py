from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P638-01\sa3_r104_fresh_isolated_v1")
RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
PAGE_INDEX = 687
PAGE_NUMBER = 688
SCALE_300 = 300.0 / 72.0

# Page-coordinate regions established from the R104 PDF's own text geometry.
DIAGRAM_RECT = fitz.Rect(128.0, 243.0, 478.0, 347.0)
FIGURE_RECT = fitz.Rect(80.0, 245.0, 523.0, 380.0)

# Semantic text objects from the current figure source. Coordinates are in PDF points.
ELEMENTS = [
    {"id": "T01", "role": "STEP_TITLE", "class": "TEXT", "rect": (144.0, 257.8, 224.0, 269.6), "expected": "1 精确满条件提议"},
    {"id": "F01", "role": "CONDITION_FORMULA", "class": "FORMULA", "rect": (144.0, 268.8, 224.0, 281.2), "expected": "q_j=pi(x_j|x_-j)"},
    {"id": "T02", "role": "STEP_TITLE", "class": "TEXT", "rect": (259.0, 251.8, 348.0, 261.2), "expected": "2 MH 比值逐项抵消"},
    {"id": "F02", "role": "RATIO_FORMULA", "class": "FORMULA", "rect": (247.0, 262.0, 359.0, 287.6), "expected": "R=pi(y)pi_j(x_j|x_-j)/(pi(x)pi_j(y_j|x_-j))=1"},
    {"id": "F03", "role": "ACCEPT_FORMULA", "class": "FORMULA", "rect": (384.0, 257.3, 461.5, 266.0), "expected": "3 alpha=1"},
    {"id": "T03", "role": "STEP_ACTION", "class": "TEXT", "rect": (384.0, 267.8, 461.5, 281.5), "expected": "直接接受 x_j<-y_j"},
    {"id": "T04", "role": "EXCEPTION_TEXT", "class": "TEXT", "rect": (210.0, 313.8, 402.0, 325.6), "expected": "近似满条件 / 其他提议 q_j"},
    {"id": "T05", "role": "EXCEPTION_TEXT", "class": "TEXT", "rect": (210.0, 326.8, 402.0, 339.5), "expected": "恢复 MH 接受率校正；拒绝时保持 x_j（自环）"},
]

# Graphic objects are color-separated from the native 300 dpi raster.
GRAPHICS = [
    {"id": "G01", "role": "FLOW_CONNECTOR", "class": "LINE_ARROW", "rect": (236.0, 268.0, 244.2, 271.0), "color": "blue"},
    {"id": "G02", "role": "FLOW_ARROW", "class": "LINE_ARROW", "rect": (362.5, 267.5, 369.2, 271.2), "color": "blue"},
    {"id": "G03", "role": "SEPARATOR", "class": "PANEL_BORDER", "rect": (130.0, 292.7, 477.0, 294.4), "color": "gray"},
    {"id": "G04", "role": "WARNING_ARROW", "class": "LINE_ARROW", "rect": (183.5, 288.5, 192.2, 306.7), "color": "red"},
    {"id": "G05", "role": "WARNING_ARROW", "class": "LINE_ARROW", "rect": (415.0, 288.5, 423.2, 306.7), "color": "red"},
    {"id": "G06", "role": "EXCEPTION_BORDER", "class": "NODE_BORDER", "rect": (192.0, 307.0, 414.7, 345.2), "color": "red"},
]


def ensure_dirs() -> None:
    RENDER.mkdir(parents=True, exist_ok=True)
    MACHINE.mkdir(parents=True, exist_ok=True)


def render_page(page: fitz.Page, dpi: int, clip: fitz.Rect | None, target: Path) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False, colorspace=fitz.csRGB)
    pix.save(str(target))
    return Image.open(target).convert("RGB")


def page_rect_to_px(rect: tuple[float, float, float, float], clip: fitz.Rect = DIAGRAM_RECT) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        int(math.floor((x0 - clip.x0) * SCALE_300)),
        int(math.floor((y0 - clip.y0) * SCALE_300)),
        int(math.ceil((x1 - clip.x0) * SCALE_300)),
        int(math.ceil((y1 - clip.y0) * SCALE_300)),
    )


def ink_mask(rgb: np.ndarray, rect_px: tuple[int, int, int, int]) -> np.ndarray:
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = rect_px
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    out = np.zeros((h, w), dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return out
    roi = rgb[y0:y1, x0:x1].astype(np.int16)
    # Local backgrounds are white or the pale warning fill. Pixel range >=20 is
    # the protocol's native-ink threshold, robust to both backgrounds.
    rng = roi.max(axis=2) - roi.min(axis=2)
    dark = roi.mean(axis=2) < 220
    colored = rng >= 20
    fg = dark | colored
    out[y0:y1, x0:x1] = fg
    return out


def color_mask(rgb: np.ndarray, rect_px: tuple[int, int, int, int], kind: str) -> np.ndarray:
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = rect_px
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    out = np.zeros((h, w), dtype=bool)
    roi = rgb[y0:y1, x0:x1].astype(np.int16)
    r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    if kind == "blue":
        fg = (b - r >= 18) & (b - g >= 4) & (r < 230)
    elif kind == "red":
        fg = (r - g >= 18) & (r - b >= 18) & (r < 250)
    else:
        spread = np.maximum(np.maximum(abs(r - g), abs(g - b)), abs(r - b))
        fg = (spread <= 12) & (r >= 90) & (r <= 245)
    out[y0:y1, x0:x1] = fg
    return out


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def pixel_clearance(a: np.ndarray, b: np.ndarray) -> float:
    ay, ax = np.nonzero(a)
    by, bx = np.nonzero(b)
    if len(ax) == 0 or len(bx) == 0:
        return float("nan")
    # Chunked exact Euclidean minimum over native foreground pixels.
    best2 = float("inf")
    bp = np.stack([bx, by], axis=1).astype(np.int32)
    ap = np.stack([ax, ay], axis=1).astype(np.int32)
    for start in range(0, len(ap), 256):
        chunk = ap[start : start + 256]
        d = chunk[:, None, :] - bp[None, :, :]
        d2 = np.sum(d * d, axis=2)
        m = float(d2.min())
        if m < best2:
            best2 = m
            if best2 == 0:
                return 0.0
    return math.sqrt(best2)


def save_mask(mask: np.ndarray, target: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(target)


def draw_overlay(img: Image.Image, objects: list[dict], target: Path) -> None:
    out = img.copy()
    d = ImageDraw.Draw(out)
    colors = {"TEXT": "#00A060", "FORMULA": "#7B2CBF", "LINE_ARROW": "#FF8C00", "PANEL_BORDER": "#5C677D", "NODE_BORDER": "#D00000"}
    for obj in objects:
        box = obj["bbox_px"]
        if box is None:
            continue
        d.rectangle(box, outline=colors.get(obj["class"], "#000000"), width=2)
        d.text((box[0] + 2, max(0, box[1] - 12)), obj["id"], fill=colors.get(obj["class"], "#000000"))
    out.save(target)


def make_contact_sheet(img: Image.Image, objects: list[dict], zoom: int, target: Path) -> None:
    panels = []
    for obj in objects:
        box = obj["bbox_px"]
        if box is None:
            continue
        pad = 8
        crop_box = (max(0, box[0] - pad), max(0, box[1] - pad), min(img.width, box[2] + pad), min(img.height, box[3] + pad))
        crop = img.crop(crop_box)
        if zoom != 1:
            crop = crop.resize((crop.width * zoom, crop.height * zoom), Image.Resampling.NEAREST)
        panels.append((obj["id"], crop))
    width = max((p.width for _, p in panels), default=1) + 24
    height = sum(p.height + 28 for _, p in panels) + 12
    sheet = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(sheet)
    y = 8
    for ident, panel in panels:
        d.text((8, y), f"{ident}  native pixels x{zoom}", fill="black")
        y += 18
        sheet.paste(panel, (8, y))
        y += panel.height + 10
    sheet.save(target)


def make_glyph_sheet(img: Image.Image, glyphs: list[dict], zoom: int, target: Path) -> None:
    panels = []
    for glyph in glyphs:
        box = (glyph["bbox_px_x0"], glyph["bbox_px_y0"], glyph["bbox_px_x1"], glyph["bbox_px_y1"])
        box = (max(0, box[0] - 2), max(0, box[1] - 2), min(img.width, box[2] + 2), min(img.height, box[3] + 2))
        crop = img.crop(box)
        if zoom != 1:
            crop = crop.resize((crop.width * zoom, crop.height * zoom), Image.Resampling.NEAREST)
        panels.append((f"{glyph['glyph_id']} {glyph['codepoint']} {glyph['char']}", crop))
    cols = 5
    cell_w = max((p.width for _, p in panels), default=1) + 18
    cell_h = max((p.height for _, p in panels), default=1) + 32
    rows = math.ceil(len(panels) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    d = ImageDraw.Draw(sheet)
    for i, (label, panel) in enumerate(panels):
        x = (i % cols) * cell_w + 6
        y = (i // cols) * cell_h + 4
        d.text((x, y), label, fill="black")
        sheet.paste(panel, (x, y + 18))
    sheet.save(target)


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]

    full300 = render_page(page, 300, None, RENDER / "r104_p688_full_page_300dpi.png")
    render_page(page, 200, None, RENDER / "r104_p688_full_page_200dpi.png")
    figure = render_page(page, 300, FIGURE_RECT, RENDER / "r104_p688_figure_crop_300dpi.png")
    diagram = render_page(page, 300, DIAGRAM_RECT, RENDER / "r104_p688_standalone_equivalent_300dpi.png")
    diagram.save(RENDER / "r104_p688_actual_objects_1x_300dpi.png")
    gray = Image.fromarray(np.asarray(diagram.convert("L")), mode="L")
    gray.save(RENDER / "r104_p688_grayscale_300dpi.png")

    rgb = np.asarray(diagram).copy()
    objects: list[dict] = []
    masks: dict[str, np.ndarray] = {}
    for element in ELEMENTS:
        rect_px = page_rect_to_px(element["rect"])
        mask = ink_mask(rgb, rect_px)
        mask_file = MACHINE / f"mask_{element['id']}.png"
        save_mask(mask, mask_file)
        box = bbox_of(mask)
        record = {**element, "rect_px": rect_px, "bbox_px": box, "ink_pixels": int(mask.sum()), "mask_file": mask_file.name}
        objects.append(record)
        masks[element["id"]] = mask
    for graphic in GRAPHICS:
        rect_px = page_rect_to_px(graphic["rect"])
        mask = color_mask(rgb, rect_px, graphic["color"])
        mask_file = MACHINE / f"mask_{graphic['id']}.png"
        save_mask(mask, mask_file)
        box = bbox_of(mask)
        record = {**graphic, "rect_px": rect_px, "bbox_px": box, "ink_pixels": int(mask.sum()), "mask_file": mask_file.name}
        objects.append(record)
        masks[graphic["id"]] = mask

    # Vector spans and glyph/codepoint inventory inside the figure diagram.
    glyph_rows = []
    raw = page.get_text("rawdict", clip=DIAGRAM_RECT)
    gid = 0
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    c = char.get("c", "")
                    if not c or c.isspace():
                        continue
                    gid += 1
                    x0, y0, x1, y1 = char["bbox"]
                    pxbox = (
                        int(math.floor((x0 - DIAGRAM_RECT.x0) * SCALE_300)),
                        int(math.floor((y0 - DIAGRAM_RECT.y0) * SCALE_300)),
                        int(math.ceil((x1 - DIAGRAM_RECT.x0) * SCALE_300)),
                        int(math.ceil((y1 - DIAGRAM_RECT.y0) * SCALE_300)),
                    )
                    gm = ink_mask(rgb, pxbox)
                    gb = bbox_of(gm)
                    glyph_rows.append({
                        "glyph_id": f"GL{gid:03d}", "char": c, "codepoint": f"U+{ord(c):04X}", "font": span.get("font", ""),
                        "size_pt": span.get("size", ""), "bbox_page_x0": x0, "bbox_page_y0": y0, "bbox_page_x1": x1, "bbox_page_y1": y1,
                        "bbox_px_x0": pxbox[0], "bbox_px_y0": pxbox[1], "bbox_px_x1": pxbox[2], "bbox_px_y1": pxbox[3],
                        "ink_bbox_px": gb, "h_ink_px": 0 if gb is None else gb[3] - gb[1], "ink_pixels": int(gm.sum()),
                    })
    with (MACHINE / "glyph_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(glyph_rows[0].keys()))
        w.writeheader(); w.writerows(glyph_rows)

    with (MACHINE / "object_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["id", "role", "class", "expected", "color", "rect", "rect_px", "bbox_px", "ink_pixels", "mask_file"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(objects)

    pair_rows = []
    for a, b in itertools.combinations(objects, 2):
        ma, mb = masks[a["id"]], masks[b["id"]]
        overlap = int(np.logical_and(ma, mb).sum())
        clearance = pixel_clearance(ma, mb)
        pair_rows.append({
            "pair_id": f"{a['id']}__{b['id']}", "a_id": a["id"], "a_class": a["class"], "a_role": a["role"],
            "b_id": b["id"], "b_class": b["class"], "b_role": b["role"], "native_overlap_px": overlap,
            "native_min_ink_clearance_px": "" if math.isnan(clearance) else f"{clearance:.3f}",
        })
    with (MACHINE / "all_unordered_object_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0].keys()))
        w.writeheader(); w.writerows(pair_rows)

    critical_rows = []
    for row in pair_rows:
        ca, cb = row["a_class"], row["b_class"]
        text_a, text_b = ca in {"TEXT", "FORMULA"}, cb in {"TEXT", "FORMULA"}
        requirement = None
        kind = None
        if text_a and text_b:
            kind, requirement = "TEXT_TEXT", 4
        elif (text_a and cb == "LINE_ARROW") or (text_b and ca == "LINE_ARROW"):
            kind, requirement = "TEXT_GRAPHIC", 3
        elif (text_a and cb == "NODE_BORDER") or (text_b and ca == "NODE_BORDER"):
            kind, requirement = "TEXT_NODE_BORDER", 5
        if requirement is not None:
            critical_rows.append({**row, "critical_kind": kind, "required_clearance_px": requirement})
    with (MACHINE / "critical_pair_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(critical_rows[0].keys()))
        w.writeheader(); w.writerows(critical_rows)

    # Element pixel-height measurements. Multiple disconnected lines/substrings are
    # retained as a conservative total ink bbox plus native vector metadata.
    measurement_rows = []
    for obj in objects:
        if obj["class"] not in {"TEXT", "FORMULA"}:
            continue
        box = obj["bbox_px"]
        h = 0 if box is None else box[3] - box[1]
        measurement_rows.append({
            "element_id": obj["id"], "role": obj["role"], "class": obj["class"], "expected": obj["expected"],
            "declared_pt_from_source": "9.2", "graphics_scale": "1.0", "effective_pt": "9.2", "bbox_px": obj["bbox_px"],
            "h_ink_bbox_px": h, "ink_pixels": obj["ink_pixels"],
        })
    with (MACHINE / "pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(measurement_rows[0].keys()))
        w.writeheader(); w.writerows(measurement_rows)

    # Peer-role machine ratios: advisory under R168; no PASS/FAIL is generated.
    role_rows = []
    for role in sorted({r["role"] for r in measurement_rows}):
        members = [r for r in measurement_rows if r["role"] == role]
        vals = [float(r["h_ink_bbox_px"]) for r in members if float(r["h_ink_bbox_px"]) > 0]
        med = float(np.median(vals)) if vals else float("nan")
        for r in members:
            val = float(r["h_ink_bbox_px"])
            role_rows.append({"element_id": r["element_id"], "role": role, "h_ink_bbox_px": val, "role_median_px": med, "ratio_to_role_median": val / med if med else ""})
    with (MACHINE / "peer_role_ratios.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(role_rows[0].keys()))
        w.writeheader(); w.writerows(role_rows)

    # Native clipping check against the diagram clip boundary.
    clip_rows = []
    for obj in objects:
        box = obj["bbox_px"]
        touches = bool(box and (box[0] <= 0 or box[1] <= 0 or box[2] >= diagram.width or box[3] >= diagram.height))
        edge_clearance = None if box is None else min(box[0], box[1], diagram.width - box[2], diagram.height - box[3])
        clip_rows.append({"object_id": obj["id"], "bbox_px": box, "touches_diagram_clip_boundary": touches, "min_to_diagram_crop_edge_px": edge_clearance})
    with (MACHINE / "clip_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(clip_rows[0].keys()))
        w.writeheader(); w.writerows(clip_rows)

    draw_overlay(diagram, objects, RENDER / "r104_p688_object_overlay_300dpi.png")
    make_contact_sheet(diagram, objects, 1, RENDER / "r104_p688_object_contact_sheet_1x.png")
    make_contact_sheet(diagram, objects, 8, RENDER / "r104_p688_object_contact_sheet_8x.png")
    make_glyph_sheet(diagram, glyph_rows, 1, RENDER / "r104_p688_glyph_contact_sheet_1x.png")
    make_glyph_sheet(diagram, glyph_rows, 8, RENDER / "r104_p688_glyph_contact_sheet_8x.png")

    vector_rows = []
    for i, drawing in enumerate(page.get_drawings()):
        rect = drawing["rect"]
        if rect.y1 < DIAGRAM_RECT.y0 or rect.y0 > DIAGRAM_RECT.y1 or rect.x1 < DIAGRAM_RECT.x0 or rect.x0 > DIAGRAM_RECT.x1:
            continue
        vector_rows.append({
            "page_drawing_index": i, "rect_pdf_pt": tuple(round(v, 6) for v in rect),
            "stroke_rgb": drawing.get("color"), "fill_rgb": drawing.get("fill"), "line_width_pt": drawing.get("width"),
            "items": repr(drawing.get("items")),
        })
    with (MACHINE / "vector_geometry_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(vector_rows[0].keys()))
        w.writeheader(); w.writerows(vector_rows)

    multiview_rows = [
        ("FULL_PAGE_NATIVE", "render/r104_p688_full_page_300dpi.png", "300", "direct PDF render; no resize"),
        ("FULL_PAGE_CONTEXT", "render/r104_p688_full_page_200dpi.png", "200", "direct PDF render; no resize"),
        ("FIGURE_CROP_NATIVE", "render/r104_p688_figure_crop_300dpi.png", "300", "direct clipped PDF render; no resize"),
        ("STANDALONE_EQUIVALENT_NATIVE", "render/r104_p688_standalone_equivalent_300dpi.png", "300", "direct diagram-only clipped PDF render; no resize"),
        ("GRAYSCALE_NATIVE", "render/r104_p688_grayscale_300dpi.png", "300", "L conversion of native 300 dpi diagram; no resize"),
        ("OBJECT_1X", "render/r104_p688_object_contact_sheet_1x.png", "300", "native pixel crops assembled without object scaling"),
        ("OBJECT_8X", "render/r104_p688_object_contact_sheet_8x.png", "300", "derived nearest-neighbor 8x diagnostic zoom"),
        ("GLYPH_1X", "render/r104_p688_glyph_contact_sheet_1x.png", "300", "native pixel glyph crops assembled without glyph scaling"),
        ("GLYPH_8X", "render/r104_p688_glyph_contact_sheet_8x.png", "300", "derived nearest-neighbor 8x diagnostic zoom"),
    ]
    with (MACHINE / "multiview_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["view_id", "relative_path", "source_dpi", "derivation"]); w.writerows(multiview_rows)

    page_text = page.get_text()
    anchor = page_text.find("图33.5")
    (MACHINE / "r104_page_anchor_excerpt.txt").write_text(page_text[max(0, anchor - 500): anchor + 900], encoding="utf-8")

    summary = {
        "pdf_page_1_based": PAGE_NUMBER,
        "pdf_page_label": page.get_label(),
        "page_size_pt": [page.rect.width, page.rect.height],
        "full_page_300dpi_px": list(full300.size),
        "figure_crop_300dpi_px": list(figure.size),
        "standalone_equivalent_300dpi_px": list(diagram.size),
        "diagram_rect_pdf_pt": list(DIAGRAM_RECT),
        "figure_rect_pdf_pt": list(FIGURE_RECT),
        "object_count": len(objects),
        "glyph_count": len(glyph_rows),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "native_overlap_sum_px": sum(int(r["native_overlap_px"]) for r in pair_rows),
        "critical_pair_count": len(critical_rows),
        "vector_drawing_count_in_diagram": len(vector_rows),
    }
    (MACHINE / "mechanical_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
