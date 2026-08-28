from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex")
PAGE_NUMBER = 48
PAGE_INDEX = PAGE_NUMBER - 1
CROP_PT = (115.0, 60.0, 485.0, 250.0)
PDF_EXPECTED = (4_967_076, "DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6")
TEX_EXPECTED = (4_189, "27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def inside(obj: dict) -> bool:
    x0 = float(obj.get("x0", 0.0))
    x1 = float(obj.get("x1", x0))
    top = float(obj.get("top", 0.0))
    bottom = float(obj.get("bottom", top))
    a, b, c, d = CROP_PT
    return not (x1 < a or x0 > c or bottom < b or top > d)


def glyph_role(c: dict) -> str:
    x0, top = float(c["x0"]), float(c["top"])
    if top >= 230:
        return "caption"
    if 67 <= top <= 82 and 250 <= x0 <= 275:
        return "axis_x2"
    if 145 <= top <= 162 and x0 >= 405:
        return "axis_x1"
    if top < 93 and x0 >= 368:
        return "note_1"
    if 93 <= top < 113 and x0 >= 368:
        return "note_2"
    if 113 <= top < 132 and x0 >= 368:
        return "note_3"
    if 90 <= top < 107 and 309 <= x0 < 340:
        return "gradient_label"
    if 98 <= top < 112 and 294 <= x0 < 312:
        return "tangent_label"
    if 133 <= top < 151 and 255 <= x0 < 320:
        return "point_label"
    if 130 <= top < 152 and x0 < 225:
        if x0 < 175:
            return "contour_c3_label"
        if x0 < 200:
            return "contour_c2_label"
        return "contour_c1_label"
    if 210 <= top < 230 and x0 < 225:
        return "contour_order"
    if 170 <= top < 190 and 330 <= x0 < 370:
        return "increase_label"
    if 210 <= top < 230 and 225 <= x0 < 350:
        return "function_formula"
    return "unclassified_figure_glyph"


def path_role(obj: dict) -> str:
    t = obj["object_type"]
    x0, x1 = float(obj["x0"]), float(obj["x1"])
    top, bottom = float(obj["top"]), float(obj["bottom"])
    w, h = x1 - x0, bottom - top
    npts = len(obj.get("pts", []))
    if t == "line":
        if h < 0.1 and 160 < top < 164:
            return "axis_x_shaft"
        if w < 0.1 and 68 < top < 72:
            return "axis_y_shaft"
        if x0 > 320 and top < 135 and w < 25:
            return "gradient_arrow_shaft"
        if 295 < x0 < 300 and w > 50:
            return "tangent_line"
        if x0 > 340 and top > 170:
            return "increase_arrow_shaft"
    if t == "curve":
        if npts > 200:
            if w < 100:
                return "contour_c1"
            if w < 150:
                return "contour_c2"
            return "contour_c3"
        if x0 > 420 and 158 < top < 165:
            return "axis_x_arrowhead"
        if 250 < x0 < 260 and top < 75:
            return "axis_y_arrowhead"
        if 320 < x0 < 328 and 127 < top < 136:
            return "point_marker"
        if npts == 5 and 339 < x0 < 345 and top < 112:
            return "gradient_arrowhead"
        if npts == 3 and w < 15 and 329 < x0 < 340 and 120 < top < 140:
            return "right_angle_marker"
        if npts == 5 and 355 < x0 < 361 and 170 < top < 176:
            return "increase_arrowhead"
        if npts == 3 and x0 < 300 and top < 95:
            return "guide_1"
        if npts == 3 and 343 < x0 < 350 and top < 110:
            return "guide_2"
        if npts == 3 and 330 < x0 < 335 and top > 118:
            return "guide_3"
    return "unclassified_foreground_path"


PATH_ORDER = [
    "axis_x_shaft", "axis_x_arrowhead", "axis_y_shaft", "axis_y_arrowhead",
    "contour_c1", "contour_c2", "contour_c3", "point_marker",
    "gradient_arrow_shaft", "gradient_arrowhead", "tangent_line",
    "right_angle_marker", "increase_arrow_shaft", "increase_arrowhead",
    "guide_1", "guide_2", "guide_3",
]


def rect_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def rect_intersection_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, tuple[float, float]]:
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    if denom == 0:
        return math.hypot(px - ax, py - ay), (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / denom))
    qx, qy = ax + t * vx, ay + t * vy
    return math.hypot(px - qx, py - qy), (qx, qy)


def segment_intersection(a, b, c, d):
    def cross(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    ab1, ab2 = cross(a, b, c), cross(a, b, d)
    cd1, cd2 = cross(c, d, a), cross(c, d, b)
    if ((ab1 <= 0 <= ab2) or (ab2 <= 0 <= ab1)) and ((cd1 <= 0 <= cd2) or (cd2 <= 0 <= cd1)):
        return True
    return False


def segment_distance(a, b, c, d):
    if segment_intersection(a, b, c, d):
        return 0.0, ((a[0] + b[0] + c[0] + d[0]) / 4.0, (a[1] + b[1] + c[1] + d[1]) / 4.0)
    candidates = []
    for p, u, v in ((a, c, d), (b, c, d), (c, a, b), (d, a, b)):
        dist, q = point_segment_distance(p[0], p[1], u[0], u[1], v[0], v[1])
        candidates.append((dist, ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)))
    return min(candidates, key=lambda x: x[0])


def polyline_segments(points):
    return list(zip(points[:-1], points[1:])) if len(points) >= 2 else []


def path_distance(a: dict, b: dict):
    best = (float("inf"), (0.0, 0.0))
    for s1 in polyline_segments(a["points_pt"]):
        for s2 in polyline_segments(b["points_pt"]):
            cand = segment_distance(s1[0], s1[1], s2[0], s2[1])
            if cand[0] < best[0]:
                best = cand
                if best[0] == 0:
                    return best
    return best


def rect_path_distance(rect, path):
    x0, y0, x1, y1 = rect
    border = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    best = (float("inf"), ((x0 + x1) / 2.0, (y0 + y1) / 2.0))
    for seg in polyline_segments(path["points_pt"]):
        if x0 <= seg[0][0] <= x1 and y0 <= seg[0][1] <= y1:
            return 0.0, seg[0]
        if x0 <= seg[1][0] <= x1 and y0 <= seg[1][1] <= y1:
            return 0.0, seg[1]
        for edge in border:
            cand = segment_distance(seg[0], seg[1], edge[0], edge[1])
            if cand[0] < best[0]:
                best = cand
                if best[0] == 0:
                    return best
    return best


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def make_glyph_sheets(crop: Image.Image, glyphs: list[dict]):
    font = ImageFont.load_default()
    native_cells = []
    zoom_cells = []
    for g in glyphs:
        x0, y0, x1, y1 = g["crop_bbox_px"]
        pad = 3
        box = (max(0, x0 - pad), max(0, y0 - pad), min(crop.width, x1 + pad), min(crop.height, y1 + pad))
        patch = crop.crop(box)
        native_cells.append((g["object_id"], g["glyph"], patch))
        zoom_cells.append((g["object_id"], g["glyph"], patch.resize((patch.width * 8, patch.height * 8), Image.Resampling.NEAREST)))

    cols = 12
    cell_w, cell_h = 110, 82
    rows = math.ceil(len(native_cells) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (oid, glyph, patch) in enumerate(native_cells):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        draw.text((x + 3, y + 2), f"{oid} U+{ord(glyph):04X}", fill="black", font=font)
        sheet.paste(patch, (x + (cell_w - patch.width) // 2, y + 22))
    sheet.save(ROOT / "glyph_sheet_native1x.png", dpi=(300, 300))

    part_size = 36
    for part_index in range(math.ceil(len(zoom_cells) / part_size)):
        chunk = zoom_cells[part_index * part_size:(part_index + 1) * part_size]
        cols2 = 6
        cell_w2 = max(420, max(p.width for _, _, p in chunk) + 20)
        cell_h2 = max(420, max(p.height for _, _, p in chunk) + 42)
        rows2 = math.ceil(len(chunk) / cols2)
        zsheet = Image.new("RGB", (cols2 * cell_w2, rows2 * cell_h2), "white")
        zd = ImageDraw.Draw(zsheet)
        for j, (oid, glyph, patch) in enumerate(chunk):
            x, y = (j % cols2) * cell_w2, (j // cols2) * cell_h2
            zd.text((x + 4, y + 4), f"{oid} U+{ord(glyph):04X}", fill="black", font=font)
            zsheet.paste(patch, (x + (cell_w2 - patch.width) // 2, y + 28))
        zsheet.save(ROOT / f"glyph_sheet_nearest8x_part{part_index + 1:02d}.png")


def make_overlays(crop: Image.Image, glyphs: list[dict], paths: list[dict]):
    overlay = crop.copy()
    d = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for g in glyphs:
        x0, y0, x1, y1 = g["crop_bbox_px"]
        d.rectangle((x0, y0, x1, y1), outline=(210, 40, 40), width=1)
    for p in paths:
        x0, y0, x1, y1 = p["crop_bbox_px"]
        d.rectangle((x0, y0, x1, y1), outline=(30, 80, 220), width=2)
        d.text((x0 + 2, max(0, y0 - 12)), p["object_id"], fill=(0, 40, 180), font=font)
    overlay.save(ROOT / "atomic_overlay_native1x.png", dpi=(300, 300))
    overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(ROOT / "atomic_overlay_nearest8x.png")


def make_relation_sheets(crop: Image.Image, candidates: list[dict]):
    font = ImageFont.load_default()
    cells = []
    for row in candidates:
        cx, cy = row["hotspot_crop_px"]
        half = 28
        box = (max(0, cx - half), max(0, cy - half), min(crop.width, cx + half), min(crop.height, cy + half))
        patch = crop.crop(box)
        cells.append((row["pair_id"], row["machine_relation_kind"], patch))
    part_size = 30
    for part_index in range(math.ceil(len(cells) / part_size)):
        chunk = cells[part_index * part_size:(part_index + 1) * part_size]
        cols = 5
        cell_w, cell_h = 500, 520
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        d = ImageDraw.Draw(sheet)
        for j, (pid, kind, patch) in enumerate(chunk):
            x, y = (j % cols) * cell_w, (j // cols) * cell_h
            d.text((x + 4, y + 4), f"{pid} {kind}", fill="black", font=font)
            z = patch.resize((patch.width * 8, patch.height * 8), Image.Resampling.NEAREST)
            sheet.paste(z, (x + (cell_w - z.width) // 2, y + 30))
        sheet.save(ROOT / f"relation_hotspots_nearest8x_part{part_index + 1:02d}.png")


def main():
    page_png = ROOT / "page_048_native300dpi.png"
    image = Image.open(page_png).convert("RGB")
    with pdfplumber.open(PDF) as doc:
        page = doc.pages[PAGE_INDEX]
        sx, sy = image.width / float(page.width), image.height / float(page.height)
        crop_px = (
            math.floor(CROP_PT[0] * sx), math.floor(CROP_PT[1] * sy),
            math.ceil(CROP_PT[2] * sx), math.ceil(CROP_PT[3] * sy),
        )
        crop = image.crop(crop_px)
        crop.save(ROOT / "figure_crop_native300dpi.png", dpi=(300, 300))
        crop.save(ROOT / "figure_crop_native1x.png", dpi=(300, 300))

        raw_chars = [(i, c) for i, c in enumerate(page.chars) if inside(c) and c.get("text", "").strip()]
        glyphs = []
        for serial, (source_index, c) in enumerate(raw_chars, start=1):
            bbox_pt = (float(c["x0"]), float(c["top"]), float(c["x1"]), float(c["bottom"]))
            page_bbox_px = (
                math.floor(bbox_pt[0] * sx), math.floor(bbox_pt[1] * sy),
                math.ceil(bbox_pt[2] * sx), math.ceil(bbox_pt[3] * sy),
            )
            crop_bbox = (
                page_bbox_px[0] - crop_px[0], page_bbox_px[1] - crop_px[1],
                page_bbox_px[2] - crop_px[0], page_bbox_px[3] - crop_px[1],
            )
            patch = image.crop(page_bbox_px)
            pixels = list(patch.getdata())
            ink_pixels = sum(1 for rgb in pixels if max(abs(int(v) - 255) for v in rgb) >= 20)
            glyphs.append({
                "object_id": f"G{serial:03d}", "kind": "GLYPH", "role": glyph_role(c),
                "glyph": c["text"], "codepoint": f"U+{ord(c['text']):04X}",
                "source_object_index": source_index, "page_number": PAGE_NUMBER,
                "bbox_x0_pt": round(bbox_pt[0], 4), "bbox_top_pt": round(bbox_pt[1], 4),
                "bbox_x1_pt": round(bbox_pt[2], 4), "bbox_bottom_pt": round(bbox_pt[3], 4),
                "font_size_pt_pdf": round(float(c["size"]), 4),
                "raster_ink_pixel_count": ink_pixels,
                "machine_missing_or_tofu_flag": c["text"] in {"\ufffd", "\u25a1", "\u25a0"} or ink_pixels == 0,
                "crop_bbox_px": crop_bbox, "bbox_pt": bbox_pt,
            })

        raw_paths = [o for o in page.lines + page.curves if inside(o)]
        classified = []
        for source_index, o in enumerate(raw_paths):
            role = path_role(o)
            points = [(float(p[0]), float(p[1])) for p in o.get("pts", [])]
            classified.append((PATH_ORDER.index(role) if role in PATH_ORDER else 999, source_index, role, o, points))
        classified.sort(key=lambda x: (x[0], x[1]))
        paths = []
        for serial, (_, source_index, role, o, points) in enumerate(classified, start=1):
            bbox_pt = (float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"]))
            page_bbox_px = (
                math.floor(bbox_pt[0] * sx), math.floor(bbox_pt[1] * sy),
                math.ceil(bbox_pt[2] * sx), math.ceil(bbox_pt[3] * sy),
            )
            crop_bbox = (
                page_bbox_px[0] - crop_px[0], page_bbox_px[1] - crop_px[1],
                page_bbox_px[2] - crop_px[0], page_bbox_px[3] - crop_px[1],
            )
            paths.append({
                "object_id": f"P{serial:03d}", "kind": "PATH", "role": role,
                "path_subtype": o["object_type"], "source_object_index": source_index,
                "page_number": PAGE_NUMBER, "bbox_x0_pt": round(bbox_pt[0], 4),
                "bbox_top_pt": round(bbox_pt[1], 4), "bbox_x1_pt": round(bbox_pt[2], 4),
                "bbox_bottom_pt": round(bbox_pt[3], 4), "linewidth_pt": round(float(o.get("linewidth", 0.0)), 4),
                "point_count": len(points), "dash": json.dumps(o.get("dash"), ensure_ascii=False),
                "crop_bbox_px": crop_bbox, "bbox_pt": bbox_pt, "points_pt": points,
            })

        backgrounds = []
        for serial, o in enumerate([o for o in page.rects if inside(o)], start=1):
            backgrounds.append({
                "exclusion_id": f"B{serial:03d}", "object_type": "RECT_FILL",
                "bbox_x0_pt": round(float(o["x0"]), 4), "bbox_top_pt": round(float(o["top"]), 4),
                "bbox_x1_pt": round(float(o["x1"]), 4), "bbox_bottom_pt": round(float(o["bottom"]), 4),
                "fill_color": json.dumps(o.get("non_stroking_color"), ensure_ascii=False),
                "stroke_enabled": bool(o.get("stroke")), "fill_enabled": bool(o.get("fill")),
                "machine_exclusion_basis": "opaque white label/callout knockout background; no foreground stroke",
            })

    role_text = {}
    for g in glyphs:
        role_text.setdefault(g["role"], "")
        role_text[g["role"]] += g["glyph"]
    expected = {
        "axis_x2": "𝑥2", "axis_x1": "𝑥1", "contour_c1_label": "𝑐1",
        "contour_c2_label": "𝑐2", "contour_c3_label": "𝑐3",
        "contour_order": "𝑐1<𝑐2<𝑐3", "point_label": "𝑃=(2.4,1.08)",
        "gradient_label": "∇𝑓(𝑃)", "tangent_label": "𝑣tan", "increase_label": "𝑓增大",
        "note_1": "1.定位𝑃所在等值线", "note_2": "2.梯度指向函数增大",
        "note_3": "3.∇𝑓(𝑃)T𝑣tan=0",
        "function_formula": "𝑓(𝑥1,𝑥2)=𝑥21/9+𝑥22/3.24",
        "caption": "图3.1梯度与等值线。箭头在该点垂直于局部切线，并指向函数值增加的方向。",
    }
    text_mismatches = {k: {"expected": v, "extracted": role_text.get(k, "")} for k, v in expected.items() if role_text.get(k, "") != v}

    objects = glyphs + paths
    object_by_id = {o["object_id"]: o for o in objects}
    background_rects = [
        (float(r["bbox_x0_pt"]), float(r["bbox_top_pt"]), float(r["bbox_x1_pt"]), float(r["bbox_bottom_pt"]))
        for r in backgrounds
    ]
    allowed_path_contacts = {
        frozenset(("axis_x_shaft", "axis_y_shaft")),
        frozenset(("axis_x_shaft", "axis_x_arrowhead")), frozenset(("axis_y_shaft", "axis_y_arrowhead")),
        frozenset(("axis_x_shaft", "contour_c1")), frozenset(("axis_x_shaft", "contour_c2")), frozenset(("axis_x_shaft", "contour_c3")),
        frozenset(("axis_y_shaft", "contour_c1")), frozenset(("axis_y_shaft", "contour_c2")), frozenset(("axis_y_shaft", "contour_c3")),
        frozenset(("contour_c3", "point_marker")), frozenset(("point_marker", "gradient_arrow_shaft")),
        frozenset(("gradient_arrow_shaft", "gradient_arrowhead")), frozenset(("point_marker", "tangent_line")),
        frozenset(("gradient_arrow_shaft", "right_angle_marker")), frozenset(("tangent_line", "right_angle_marker")),
        frozenset(("increase_arrow_shaft", "increase_arrowhead")), frozenset(("guide_1", "contour_c3")),
        frozenset(("guide_2", "gradient_arrowhead")), frozenset(("guide_3", "right_angle_marker")),
    }

    pair_rows = []
    candidates = []
    for index, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        abox, bbox = a["bbox_pt"], b["bbox_pt"]
        bbox_gap = rect_distance(abox, bbox)
        bbox_intersection = rect_intersection_area(abox, bbox)
        hotspot = ((max(abox[0], bbox[0]) + min(abox[2], bbox[2])) / 2.0,
                   (max(abox[1], bbox[1]) + min(abox[3], bbox[3])) / 2.0)
        if a["kind"] == "PATH" and b["kind"] == "PATH":
            distance, hotspot = path_distance(a, b)
            relation_kind = "path_path_geometry"
            expected_relation = "intentional_semantic_contact" if frozenset((a["role"], b["role"])) in allowed_path_contacts else "independent_paths"
            candidate = distance * sx <= 2.5
        elif a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
            distance = bbox_gap
            if a["role"] == b["role"] and distance * sx <= 3.0:
                expected_relation = "same_text_typographic_adjacency_or_stack"
            else:
                expected_relation = "independent_glyphs"
            relation_kind = "glyph_glyph_bbox"
            candidate = bbox_intersection > 0 or distance * sx <= 1.0
        else:
            glyph = a if a["kind"] == "GLYPH" else b
            path = b if a["kind"] == "GLYPH" else a
            distance, hotspot = rect_path_distance(glyph["bbox_pt"], path)
            knockout = any(
                r[0] <= glyph["bbox_pt"][0] and r[1] <= glyph["bbox_pt"][1]
                and r[2] >= glyph["bbox_pt"][2] and r[3] >= glyph["bbox_pt"][3]
                for r in background_rects
            )
            expected_relation = "opaque_knockout_separates_text_from_path" if knockout and distance * sx <= 3.0 else "independent_text_and_path"
            relation_kind = "glyph_path_geometry"
            candidate = distance * sx <= 3.0
        row = {
            "pair_id": f"R{index:05d}", "object_a_id": a["object_id"], "object_b_id": b["object_id"],
            "pair_kind": f"{a['kind']}-{b['kind']}", "object_a_role": a["role"], "object_b_role": b["role"],
            "machine_relation_kind": relation_kind, "machine_expected_relation": expected_relation,
            "machine_min_geometry_distance_pt": round(distance, 5),
            "machine_min_geometry_distance_px": round(distance * (sx + sy) / 2.0, 3),
            "machine_bbox_intersection_area_pt2": round(bbox_intersection, 5),
            "machine_review_candidate": candidate,
        }
        pair_rows.append(row)
        if candidate:
            cx = int(round(hotspot[0] * sx)) - crop_px[0]
            cy = int(round(hotspot[1] * sy)) - crop_px[1]
            candidates.append({**row, "hotspot_crop_px": (cx, cy)})

    denominator_fields = [
        "object_id", "kind", "role", "glyph", "codepoint", "path_subtype", "source_object_index", "page_number",
        "bbox_x0_pt", "bbox_top_pt", "bbox_x1_pt", "bbox_bottom_pt", "font_size_pt_pdf", "raster_ink_pixel_count",
        "machine_missing_or_tofu_flag", "linewidth_pt", "point_count", "dash",
    ]
    denominator_rows = []
    for o in objects:
        denominator_rows.append({k: o.get(k, "") for k in denominator_fields})
    write_csv(ROOT / "machine_atomic_denominator.csv", denominator_fields, denominator_rows)
    write_csv(ROOT / "machine_background_exclusions.csv", list(backgrounds[0].keys()), backgrounds)
    pair_fields = list(pair_rows[0].keys())
    write_csv(ROOT / "machine_all_unordered_pairs.csv", pair_fields, pair_rows)
    candidate_fields = pair_fields + ["hotspot_crop_x_px", "hotspot_crop_y_px"]
    write_csv(ROOT / "machine_relation_candidates.csv", candidate_fields, [
        {**{k: v for k, v in c.items() if k != "hotspot_crop_px"},
         "hotspot_crop_x_px": c["hotspot_crop_px"][0], "hotspot_crop_y_px": c["hotspot_crop_px"][1]}
        for c in candidates
    ])

    visible_bbox = (
        min(o["bbox_pt"][0] for o in objects), min(o["bbox_pt"][1] for o in objects),
        max(o["bbox_pt"][2] for o in objects), max(o["bbox_pt"][3] for o in objects),
    )
    clipped = [
        o["object_id"] for o in objects
        if o["bbox_pt"][0] < CROP_PT[0] or o["bbox_pt"][1] < CROP_PT[1]
        or o["bbox_pt"][2] > CROP_PT[2] or o["bbox_pt"][3] > CROP_PT[3]
    ]
    no_ink = [g["object_id"] for g in glyphs if g["raster_ink_pixel_count"] == 0]
    tofu = [g["object_id"] for g in glyphs if g["machine_missing_or_tofu_flag"]]
    pair_keys = [(r["object_a_id"], r["object_b_id"]) for r in pair_rows]

    p = (2.4, 1.08)
    g = (3.12, 1.98)
    tm = (1.46, 1.83)
    t = (3.34, 0.33)
    grad = (2 * p[0] / 9.0, 2 * p[1] / 3.24)
    gv = (g[0] - p[0], g[1] - p[1])
    tv = (t[0] - tm[0], t[1] - tm[1])
    right_v = (t[0] - p[0], t[1] - p[1])
    semantics = {
        "contour_levels": {"c1": 1.5**2 / 9, "c2": 2.4**2 / 9, "c3": 3.0**2 / 9},
        "point_P_f": p[0]**2 / 9 + p[1]**2 / 3.24,
        "guide_1_endpoint_f": 0.84**2 / 9 + 1.728**2 / 3.24,
        "analytic_gradient_at_P": grad,
        "drawn_gradient_vector": gv,
        "gradient_parallel_cross": grad[0] * gv[1] - grad[1] * gv[0],
        "gradient_tangent_dot": grad[0] * tv[0] + grad[1] * tv[1],
        "drawn_right_angle_dot": gv[0] * right_v[0] + gv[1] * right_v[1],
        "guide_2_endpoint_equals_G": True,
        "guide_3_endpoint": [2.67, 1.23],
    }
    hard_clear = (
        PDF.stat().st_size == PDF_EXPECTED[0] and sha256(PDF) == PDF_EXPECTED[1]
        and TEX.stat().st_size == TEX_EXPECTED[0] and sha256(TEX) == TEX_EXPECTED[1]
        and len(glyphs) == 135 and len(paths) == 17 and len(backgrounds) == 11
        and len(pair_rows) == len(objects) * (len(objects) - 1) // 2
        and len(set(pair_keys)) == len(pair_keys) and not clipped and not no_ink and not tofu
        and not text_mismatches and set(p["role"] for p in paths) == set(PATH_ORDER)
        and abs(semantics["point_P_f"] - 1.0) < 1e-12
        and abs(semantics["guide_1_endpoint_f"] - 1.0) < 1e-12
        and abs(semantics["gradient_parallel_cross"]) < 1e-12
        and abs(semantics["gradient_tangent_dot"]) < 0.01
        and abs(semantics["drawn_right_angle_dot"]) < 0.01
    )
    gates = {
        "uid": "FIG-P049-01", "handoff_id": "A-R111-P049-SA3-FRESH-ISOLATED-20260827",
        "pdf_page_number": PAGE_NUMBER, "printed_page_number": 35,
        "pdf_identity": {"bytes": PDF.stat().st_size, "sha256": sha256(PDF), "expected_match": PDF.stat().st_size == PDF_EXPECTED[0] and sha256(PDF) == PDF_EXPECTED[1]},
        "tex_identity": {"bytes": TEX.stat().st_size, "sha256": sha256(TEX), "expected_match": TEX.stat().st_size == TEX_EXPECTED[0] and sha256(TEX) == TEX_EXPECTED[1]},
        "crop_points": CROP_PT, "crop_pixels": crop_px, "crop_dimensions_pixels": [crop.width, crop.height],
        "visible_bbox_points": [round(x, 4) for x in visible_bbox],
        "machine_glyph_count": len(glyphs), "machine_foreground_path_count": len(paths),
        "machine_background_exclusion_count": len(backgrounds), "machine_atomic_denominator_N": len(objects),
        "machine_expected_unordered_pair_count_C": len(objects) * (len(objects) - 1) // 2,
        "machine_enumerated_unordered_pair_count": len(pair_rows), "machine_unique_pair_count": len(set(pair_keys)),
        "machine_relation_candidate_count": len(candidates), "machine_clipped_object_ids": clipped,
        "machine_zero_ink_glyph_ids": no_ink, "machine_missing_or_tofu_glyph_ids": tofu,
        "machine_text_group_mismatches": text_mismatches,
        "machine_unclassified_glyph_ids": [g["object_id"] for g in glyphs if g["role"].startswith("unclassified")],
        "machine_unclassified_path_ids": [p["object_id"] for p in paths if p["role"].startswith("unclassified")],
        "machine_semantic_numeric_checks": semantics,
        "r168_advisories": [
            "Source label style declares 9.4 pt, note/increase/formula styles 9.2 pt, and axis tick style 8.8 pt; no ticks are rendered. Under R168 these micro font differences are advisory and require direct readability review.",
            "Raster ink-height variation is advisory under R168 unless it creates actual unreadability, missing/tofu/wrong codepoint, clipping, illegal overlap, or obvious visible imbalance."
        ],
        "machine_hard_gate_state": "CLEAR" if hard_clear else "NOT_CLEAR",
    }
    (ROOT / "machine_hard_gates.json").write_text(json.dumps(gates, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "machine_semantic_checks.json").write_text(json.dumps(semantics, ensure_ascii=False, indent=2), encoding="utf-8")

    make_glyph_sheets(crop, glyphs)
    make_overlays(crop, glyphs, paths)
    make_relation_sheets(crop, candidates)

    print(json.dumps({
        "N": len(objects), "C": len(pair_rows), "glyphs": len(glyphs), "paths": len(paths),
        "background_exclusions": len(backgrounds), "relation_candidates": len(candidates),
        "hard_gate": gates["machine_hard_gate_state"], "text_mismatches": text_mismatches,
        "unclassified_glyphs": gates["machine_unclassified_glyph_ids"],
        "unclassified_paths": gates["machine_unclassified_path_ids"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
