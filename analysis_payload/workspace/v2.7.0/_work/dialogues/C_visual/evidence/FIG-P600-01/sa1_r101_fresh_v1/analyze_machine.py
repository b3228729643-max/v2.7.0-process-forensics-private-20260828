from __future__ import annotations

import csv
import math
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r101_fresh_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf")
PAGE_INDEX = 648
SCALE_300 = 300.0 / 72.0
SCALE_2400 = 2400.0 / 72.0
FIG_RECT = fitz.Rect(120.0, 450.0, 475.0, 630.0)


# This is a mechanical inventory only.  Human decisions live in separate ledgers.
OBJECTS = [
    ("O01", "X_STATE_BORDER", "NODE_BORDER", (131.81, 535.84, 157.32, 561.35), (8,)),
    ("O02", "X_STATE_LABEL", "TEXT_FORMULA", (141.61, 543.94, 147.43, 553.10), ()),
    ("O03", "Y_STATE_BORDER", "NODE_BORDER", (426.62, 535.84, 452.13, 561.35), (9,)),
    ("O04", "Y_STATE_LABEL", "TEXT_FORMULA", (436.53, 542.99, 441.93, 552.16), ()),
    ("O05", "A_PROPOSAL_BORDER", "NODE_BORDER", (174.33, 474.90, 273.54, 500.41), (10,)),
    ("O06", "A_PROPOSAL_FORMULA", "TEXT_FORMULA", (190.59, 483.22, 257.28, 492.38), ()),
    ("O07", "B_PROPOSAL_BORDER", "NODE_BORDER", (310.39, 474.90, 409.61, 500.41), (11,)),
    ("O08", "B_PROPOSAL_FORMULA", "TEXT_FORMULA", (326.85, 483.22, 393.15, 492.38), ()),
    ("O09", "MIN_CLIP_BORDER", "NODE_BORDER", (246.61, 506.08, 337.32, 534.42), (12,)),
    ("O10", "MIN_CLIP_FORMULA", "TEXT_FORMULA", (272.72, 515.93, 311.21, 525.10), ()),
    ("O11", "PROPOSAL_FLOW_HEADING", "TEXT_ANNOTATION", (244.85, 461.38, 339.09, 470.55), ()),
    ("O12", "X_TO_A_THINFLOW", "LINE_ARROW", (153.86, 488.58, 173.68, 539.30), (13, 14)),
    ("O13", "Y_TO_B_THINFLOW", "LINE_ARROW", (410.26, 488.58, 430.08, 539.30), (15, 16)),
    ("O14", "A_TO_MIN_THINFLOW", "LINE_ARROW", (247.20, 500.70, 273.83, 506.15), (17, 18)),
    ("O15", "B_TO_MIN_THINFLOW", "LINE_ARROW", (310.11, 500.70, 336.74, 506.15), (19, 20)),
    ("O16", "ACCEPTED_FLOW_X_TO_Y", "LINE_ARROW", (157.68, 548.71, 424.84, 556.82), (4, 5)),
    ("O17", "ACCEPTED_FLOW_Y_TO_X", "LINE_ARROW", (159.09, 540.37, 426.26, 548.49), (6, 7)),
    ("O18", "ACCEPTED_FORMULA_X_TO_Y", "TEXT_FORMULA", (208.34, 569.86, 375.59, 579.03), ()),
    ("O19", "ACCEPTED_FORMULA_Y_TO_X", "TEXT_FORMULA", (208.46, 580.82, 375.47, 589.99), ()),
    ("O20", "CONCLUSION_BORDER", "NODE_BORDER", (212.03, 599.13, 371.91, 625.63), (21,)),
    ("O21", "CONCLUSION_LINE_1", "TEXT_MIXED", (217.01, 603.05, 366.93, 612.86), ()),
    ("O22", "CONCLUSION_LINE_2", "TEXT_MIXED", (226.93, 614.01, 357.00, 623.82), ()),
]

TEXT_META = {
    "O02": ("$x$", 17, 9.2, 1.0),
    "O04": ("$y$", 18, 9.2, 1.0),
    "O06": ("$a=\\pi(x)q(x,y)$", 20, 9.2, 1.0),
    "O08": ("$b=\\pi(y)q(y,x)$", 22, 9.2, 1.0),
    "O10": ("$\\min(a,b)$", 24, 9.2, 1.0),
    "O11": ("提议流：两方向一般不等", 26, 8.6, 1.0),
    "O18": ("$x\\to y:\\pi(x)q(x,y)\\alpha(x,y)=\\min(a,b)$", 37, 9.2, 1.0),
    "O19": ("$y\\to x:\\pi(y)q(y,x)\\alpha(y,x)=\\min(a,b)$", 38, 9.2, 1.0),
    "O21": ("接受后双向流等宽、等值⇒细致平衡", 42, 9.2, 1.0),
    "O22": ("充分推出π平稳，但非必要条件", 42, 9.2, 1.0),
}


def rect_distance(a: fitz.Rect, b: fitz.Rect) -> float:
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
    return math.hypot(dx, dy)


def rect_intersection_area(a: fitz.Rect, b: fitz.Rect) -> float:
    x0, y0 = max(a.x0, b.x0), max(a.y0, b.y0)
    x1, y1 = min(a.x1, b.x1), min(a.y1, b.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def find_font(size: int = 18):
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_path_mask(mask: np.ndarray, drawing: dict, scale: float) -> None:
    thickness = max(1, int(round(float(drawing.get("width") or 0.5) * scale)))

    def pt(p):
        return int(round(p.x * scale)), int(round(p.y * scale))

    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            cv2.line(mask, pt(item[1]), pt(item[2]), 255, thickness, cv2.LINE_AA)
        elif kind == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            points = []
            for t in np.linspace(0.0, 1.0, 81):
                q = ((1-t)**3) * np.array([p0.x, p0.y]) + 3*((1-t)**2)*t*np.array([p1.x, p1.y]) + 3*(1-t)*(t**2)*np.array([p2.x, p2.y]) + (t**3)*np.array([p3.x, p3.y])
                points.append((int(round(q[0]*scale)), int(round(q[1]*scale))))
            cv2.polylines(mask, [np.asarray(points, dtype=np.int32)], False, 255, thickness, cv2.LINE_AA)
        elif kind == "re":
            r = item[1]
            cv2.rectangle(mask, pt(r.tl), pt(r.br), 255, thickness, cv2.LINE_AA)
        elif kind == "qu":
            q = item[1]
            points = np.asarray([pt(q.ul), pt(q.ur), pt(q.lr), pt(q.ll)], dtype=np.int32)
            cv2.polylines(mask, [points], True, 255, thickness, cv2.LINE_AA)
    if drawing.get("fill") is not None and len(drawing["items"]) <= 5:
        # Filled arrowheads are foreground.  The node/background fills are not.
        if drawing["rect"].width < 8 and drawing["rect"].height < 8:
            r = drawing["rect"]
            x0, y0 = pt(r.tl)
            x1, y1 = pt(r.br)
            cv2.rectangle(mask, (x0, y0), (x1, y1), 255, -1)


def make_text_mask(full_rgb: np.ndarray, rect: fitz.Rect) -> np.ndarray:
    mask = np.zeros(full_rgb.shape[:2], dtype=np.uint8)
    x0 = max(0, int(math.floor(rect.x0 * SCALE_300)))
    y0 = max(0, int(math.floor(rect.y0 * SCALE_300)))
    x1 = min(full_rgb.shape[1], int(math.ceil(rect.x1 * SCALE_300)))
    y1 = min(full_rgb.shape[0], int(math.ceil(rect.y1 * SCALE_300)))
    roi = full_rgb[y0:y1, x0:x1]
    if roi.size == 0:
        return mask
    lum = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    local = np.where(lum < 215, 255, 0).astype(np.uint8)
    mask[y0:y1, x0:x1] = local
    return mask


def collect_chars(page: fitz.Page):
    text_objects = [(oid, name, fitz.Rect(box)) for oid, name, kind, box, _ in OBJECTS if kind.startswith("TEXT")]
    chars = []
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    c = ch.get("c", "")
                    if not c or c.isspace():
                        continue
                    r = fitz.Rect(ch["bbox"])
                    center = ((r.x0 + r.x1) / 2.0, (r.y0 + r.y1) / 2.0)
                    owner = None
                    for oid, name, box in text_objects:
                        expanded = fitz.Rect(box.x0 - 1.5, box.y0 - 1.5, box.x1 + 1.5, box.y1 + 1.5)
                        if expanded.contains(center):
                            owner = (oid, name)
                            break
                    if owner:
                        chars.append({
                            "object_id": owner[0],
                            "object_name": owner[1],
                            "char": c,
                            "bbox": r,
                            "font": span.get("font", ""),
                            "font_size_pt": float(span.get("size", 0.0)),
                        })
    chars.sort(key=lambda x: (int(x["object_id"][1:]), x["bbox"].y0, x["bbox"].x0))
    for idx, item in enumerate(chars, start=1):
        item["glyph_id"] = f"G{idx:03d}"
    return chars


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ink_metrics(full_rgb: np.ndarray, rect: fitz.Rect):
    x0 = max(0, int(math.floor(rect.x0 * SCALE_300)) - 2)
    y0 = max(0, int(math.floor(rect.y0 * SCALE_300)) - 2)
    x1 = min(full_rgb.shape[1], int(math.ceil(rect.x1 * SCALE_300)) + 2)
    y1 = min(full_rgb.shape[0], int(math.ceil(rect.y1 * SCALE_300)) + 2)
    roi = full_rgb[y0:y1, x0:x1]
    lum = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    dark = lum < 215
    ys, xs = np.where(dark)
    if len(xs) == 0:
        return 0, 0, 0, 0, 0
    return int(xs.min()+x0), int(ys.min()+y0), int(xs.max()+1+x0), int(ys.max()+1+y0), int(ys.max()-ys.min()+1)


def build_contact_sheet(cards, out_path: Path, cols: int, card_size, title: str):
    font = find_font(18)
    label_h = 30
    cw, ch = card_size
    rows = math.ceil(len(cards) / cols)
    canvas = Image.new("RGB", (cols*cw, 42 + rows*(ch+label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 8), title, fill="black", font=font)
    for idx, (label, img) in enumerate(cards):
        col, row = idx % cols, idx // cols
        x, y = col*cw, 42 + row*(ch+label_h)
        tile = Image.new("RGB", (cw, ch), "white")
        iw, ih = img.size
        scale = min((cw-12)/max(1, iw), (ch-12)/max(1, ih), 1.0)
        if scale < 1.0:
            img = img.resize((max(1, int(iw*scale)), max(1, int(ih*scale))), Image.Resampling.LANCZOS)
        tile.paste(img, ((cw-img.width)//2, (ch-img.height)//2))
        canvas.paste(tile, (x, y))
        draw.rectangle((x, y, x+cw-1, y+ch-1), outline=(170,170,170), width=1)
        draw.text((x+5, y+ch+4), label, fill="black", font=font)
    canvas.save(out_path)


def main():
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    drawings = page.get_drawings()
    full = np.asarray(Image.open(ROOT / "full_page_300dpi.png").convert("RGB"))
    direct_2400 = Image.open(ROOT / "figure_only_direct_2400dpi.png").convert("RGB")

    object_rows = []
    object_masks = {}
    for oid, name, kind, box_tuple, drawing_ids in OBJECTS:
        rect = fitz.Rect(box_tuple)
        object_rows.append({
            "object_id": oid,
            "name": name,
            "class": kind,
            "pdf_x0": f"{rect.x0:.2f}",
            "pdf_y0": f"{rect.y0:.2f}",
            "pdf_x1": f"{rect.x1:.2f}",
            "pdf_y1": f"{rect.y1:.2f}",
            "bbox_width_pt": f"{rect.width:.2f}",
            "bbox_height_pt": f"{rect.height:.2f}",
            "drawing_indices": ";".join(str(i) for i in drawing_ids),
        })
        if kind.startswith("TEXT"):
            object_masks[oid] = make_text_mask(full, rect)
        else:
            mask = np.zeros(full.shape[:2], dtype=np.uint8)
            for drawing_id in drawing_ids:
                draw_path_mask(mask, drawings[drawing_id], SCALE_300)
            object_masks[oid] = mask
    write_csv(ROOT / "machine_object_inventory.csv", object_rows[0].keys(), object_rows)

    clip_rows = []
    page_rect = page.rect
    for oid, name, kind, box_tuple, drawing_ids in OBJECTS:
        r = fitz.Rect(box_tuple)
        clip_rows.append({
            "object_id": oid,
            "name": name,
            "left_page_margin_px": f"{(r.x0-page_rect.x0)*SCALE_300:.2f}",
            "top_page_margin_px": f"{(r.y0-page_rect.y0)*SCALE_300:.2f}",
            "right_page_margin_px": f"{(page_rect.x1-r.x1)*SCALE_300:.2f}",
            "bottom_page_margin_px": f"{(page_rect.y1-r.y1)*SCALE_300:.2f}",
            "left_figure_review_margin_px": f"{(r.x0-FIG_RECT.x0)*SCALE_300:.2f}",
            "top_figure_review_margin_px": f"{(r.y0-FIG_RECT.y0)*SCALE_300:.2f}",
            "right_figure_review_margin_px": f"{(FIG_RECT.x1-r.x1)*SCALE_300:.2f}",
            "bottom_figure_review_margin_px": f"{(FIG_RECT.y1-r.y1)*SCALE_300:.2f}",
            "outside_page_bbox_area_pt2": f"{rect_intersection_area(r, page_rect)-r.width*r.height:.3f}",
        })
    write_csv(ROOT / "machine_clip_geometry.csv", clip_rows[0].keys(), clip_rows)

    text_element_rows = []
    for oid, name, kind, box_tuple, drawing_ids in OBJECTS:
        if oid not in TEXT_META:
            continue
        sample, line_no, declared_pt, graphics_scale = TEXT_META[oid]
        r = fitz.Rect(box_tuple)
        ix0, iy0, ix1, iy1, ink_h = ink_metrics(full, r)
        text_element_rows.append({
            "element_id": oid,
            "name": name,
            "source_line": line_no,
            "text_sample": sample,
            "declared_pt": f"{declared_pt:.2f}",
            "graphics_scale": f"{graphics_scale:.3f}",
            "effective_pt": f"{declared_pt*graphics_scale:.2f}",
            "pdf_bbox_h_pt": f"{r.height:.2f}",
            "threshold_ink_h_px_300dpi": ink_h,
            "ink_x0_px": ix0,
            "ink_y0_px": iy0,
            "ink_x1_px": ix1,
            "ink_y1_px": iy1,
        })
    write_csv(ROOT / "machine_text_element_measurements.csv", text_element_rows[0].keys(), text_element_rows)

    pair_rows = []
    pair_index = 0
    for i in range(len(OBJECTS)):
        for j in range(i+1, len(OBJECTS)):
            pair_index += 1
            oa, ob = OBJECTS[i], OBJECTS[j]
            ra, rb = fitz.Rect(oa[3]), fitz.Rect(ob[3])
            intersection = cv2.bitwise_and(object_masks[oa[0]], object_masks[ob[0]])
            mask_px = int(np.count_nonzero(intersection > 0))
            pair_rows.append({
                "pair_id": f"P{pair_index:03d}",
                "object_a": oa[0],
                "object_b": ob[0],
                "class_a": oa[2],
                "class_b": ob[2],
                "bbox_distance_pt": f"{rect_distance(ra, rb):.3f}",
                "bbox_distance_px_300dpi": f"{rect_distance(ra, rb)*SCALE_300:.2f}",
                "bbox_intersection_area_pt2": f"{rect_intersection_area(ra, rb):.3f}",
                "machine_mask_shared_px": mask_px,
                "machine_candidate": "YES" if mask_px > 0 or rect_distance(ra, rb)*SCALE_300 < 8 else "NO",
            })
    write_csv(ROOT / "machine_unordered_pairs.csv", pair_rows[0].keys(), pair_rows)

    critical_rows = [dict(row) for row in pair_rows if row["machine_candidate"] == "YES"]
    write_csv(ROOT / "machine_critical_intersections.csv", critical_rows[0].keys(), critical_rows)

    chars = collect_chars(page)
    glyph_rows = []
    glyph_cards_1x = []
    glyph_cards_8x = []
    for item in chars:
        r = item["bbox"]
        ix0, iy0, ix1, iy1, ink_h = ink_metrics(full, r)
        row = {
            "glyph_id": item["glyph_id"],
            "object_id": item["object_id"],
            "object_name": item["object_name"],
            "glyph": item["char"],
            "unicode": "+".join(f"U+{ord(c):04X}" for c in item["char"]),
            "font": item["font"],
            "font_size_pt": f"{item['font_size_pt']:.3f}",
            "pdf_x0": f"{r.x0:.3f}",
            "pdf_y0": f"{r.y0:.3f}",
            "pdf_x1": f"{r.x1:.3f}",
            "pdf_y1": f"{r.y1:.3f}",
            "raw_bbox_h_px_300dpi": f"{r.height*SCALE_300:.2f}",
            "ink_x0_px": ix0,
            "ink_y0_px": iy0,
            "ink_x1_px": ix1,
            "ink_y1_px": iy1,
            "threshold_ink_h_px": ink_h,
        }
        glyph_rows.append(row)
        pad_300 = 5
        x0 = max(0, int(math.floor(r.x0*SCALE_300))-pad_300)
        y0 = max(0, int(math.floor(r.y0*SCALE_300))-pad_300)
        x1 = min(full.shape[1], int(math.ceil(r.x1*SCALE_300))+pad_300)
        y1 = min(full.shape[0], int(math.ceil(r.y1*SCALE_300))+pad_300)
        glyph_cards_1x.append((f"{item['glyph_id']} {item['object_id']} {item['char']}", Image.fromarray(full[y0:y1, x0:x1])))
        # Direct 2400 dpi source; map from PDF page coordinates into the direct clip.
        fx0 = int(math.floor((r.x0-FIG_RECT.x0)*SCALE_2400))-20
        fy0 = int(math.floor((r.y0-FIG_RECT.y0)*SCALE_2400))-20
        fx1 = int(math.ceil((r.x1-FIG_RECT.x0)*SCALE_2400))+20
        fy1 = int(math.ceil((r.y1-FIG_RECT.y0)*SCALE_2400))+20
        fx0, fy0 = max(0, fx0), max(0, fy0)
        fx1, fy1 = min(direct_2400.width, fx1), min(direct_2400.height, fy1)
        glyph_cards_8x.append((f"{item['glyph_id']} {item['object_id']} {item['char']}", direct_2400.crop((fx0, fy0, fx1, fy1))))
    write_csv(ROOT / "machine_glyph_inventory.csv", glyph_rows[0].keys(), glyph_rows)

    # Object overlay on the native 300 dpi page crop.
    overlay = Image.open(ROOT / "figure_only_native_300dpi.png").convert("RGB")
    odraw = ImageDraw.Draw(overlay)
    font = find_font(17)
    crop_x, crop_y = 500, 1878
    colors = [(200,0,0),(0,120,0),(0,70,210),(180,90,0),(140,0,160)]
    for idx, (oid, name, kind, box_tuple, drawing_ids) in enumerate(OBJECTS):
        r = fitz.Rect(box_tuple)
        box = (r.x0*SCALE_300-crop_x, r.y0*SCALE_300-crop_y, r.x1*SCALE_300-crop_x, r.y1*SCALE_300-crop_y)
        color = colors[idx % len(colors)]
        odraw.rectangle(box, outline=color, width=2)
        odraw.text((box[0]+2, max(0, box[1]-19)), oid, fill=color, font=font)
    overlay.save(ROOT / "object_bbox_overlay_native_300dpi.png")

    # Contact sheets.  The direct-2400 glyph cards are downsampled only to fit a review sheet;
    # the source file remains available as a direct vector render.
    build_contact_sheet(glyph_cards_1x, ROOT / "glyph_contact_1x_native300.png", 10, (150, 95), "All visible glyphs: native 300 dpi cards")
    chunk_size = 32
    for chunk_no in range(math.ceil(len(glyph_cards_8x)/chunk_size)):
        chunk = glyph_cards_8x[chunk_no*chunk_size:(chunk_no+1)*chunk_size]
        build_contact_sheet(chunk, ROOT / f"glyph_contact_8x_direct2400_{chunk_no+1:02d}.png", 4, (330, 260), f"Direct 2400 dpi glyph cards {chunk_no+1}")

    object_cards = []
    figure_img = Image.open(ROOT / "figure_only_native_300dpi.png").convert("RGB")
    for oid, name, kind, box_tuple, drawing_ids in OBJECTS:
        r = fitz.Rect(box_tuple)
        x0 = max(0, int(math.floor(r.x0*SCALE_300))-500-18)
        y0 = max(0, int(math.floor(r.y0*SCALE_300))-1878-18)
        x1 = min(figure_img.width, int(math.ceil(r.x1*SCALE_300))-500+18)
        y1 = min(figure_img.height, int(math.ceil(r.y1*SCALE_300))-1878+18)
        object_cards.append((f"{oid} {name}", figure_img.crop((x0,y0,x1,y1))))
    build_contact_sheet(object_cards, ROOT / "object_contact_1x_native300.png", 4, (360, 180), "All semantic objects: native 300 dpi cards")

    critical_cards = []
    object_by_id = {o[0]: o for o in OBJECTS}
    for row in critical_rows:
        oa = object_by_id[row["object_a"]]
        ob = object_by_id[row["object_b"]]
        ra, rb = fitz.Rect(oa[3]), fitz.Rect(ob[3])
        union = fitz.Rect(min(ra.x0, rb.x0)-5, min(ra.y0, rb.y0)-5, max(ra.x1, rb.x1)+5, max(ra.y1, rb.y1)+5)
        fx0 = max(0, int(math.floor((union.x0-FIG_RECT.x0)*SCALE_2400)))
        fy0 = max(0, int(math.floor((union.y0-FIG_RECT.y0)*SCALE_2400)))
        fx1 = min(direct_2400.width, int(math.ceil((union.x1-FIG_RECT.x0)*SCALE_2400)))
        fy1 = min(direct_2400.height, int(math.ceil((union.y1-FIG_RECT.y0)*SCALE_2400)))
        critical_cards.append((f"{row['pair_id']} {row['object_a']}--{row['object_b']} mask={row['machine_mask_shared_px']}", direct_2400.crop((fx0,fy0,fx1,fy1))))
    for chunk_no in range(math.ceil(len(critical_cards)/12)):
        chunk = critical_cards[chunk_no*12:(chunk_no+1)*12]
        build_contact_sheet(chunk, ROOT / f"critical_contact_8x_direct2400_{chunk_no+1:02d}.png", 3, (440, 300), f"Machine critical pair candidates: direct 2400 dpi {chunk_no+1}")

    # Machine summary has no human verdicts.
    candidate_pairs = [r for r in pair_rows if r["machine_candidate"] == "YES"]
    with (ROOT / "machine_summary.txt").open("w", encoding="utf-8") as f:
        f.write(f"semantic_object_count={len(OBJECTS)}\n")
        f.write(f"unordered_pair_count={len(pair_rows)}\n")
        f.write(f"glyph_count={len(chars)}\n")
        f.write(f"machine_candidate_pair_count={len(candidate_pairs)}\n")
        f.write("machine_candidate_pair_ids=" + ",".join(r["pair_id"] for r in candidate_pairs) + "\n")


if __name__ == "__main__":
    main()
