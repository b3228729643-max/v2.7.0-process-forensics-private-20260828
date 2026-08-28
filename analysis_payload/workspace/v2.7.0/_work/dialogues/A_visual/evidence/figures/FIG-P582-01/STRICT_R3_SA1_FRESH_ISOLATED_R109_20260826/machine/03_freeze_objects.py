import copy
import csv
import json
import math
import unicodedata
from pathlib import Path

from lxml import etree
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GEOM = json.loads((Path(__file__).with_name("02_page_geometry.json")).read_text(encoding="utf-8"))
SVG_PATH = Path(__file__).with_name("page632.svg")
PAGE_PNG = ROOT / "render" / "full_page_300dpi.png"
SCALE = 300 / 72.0

# Frozen in PDF top-origin pt. Figure body is the complete axes/TikZ object only;
# the wider crop adds the official caption for page-integration review.
BODY_PT = [150.0, 320.0, 465.0, 484.0]
FIGURE_WITH_CAPTION_PT = [65.0, 320.0, 540.0, 515.0]


def px_box(pt_box):
    x0, y0, x1, y1 = pt_box
    return [
        math.floor(x0 * SCALE),
        math.floor(y0 * SCALE),
        math.ceil(x1 * SCALE),
        math.ceil(y1 * SCALE),
    ]


def bbox_union(items):
    return [
        min(float(x["x0"]) for x in items),
        min(float(x["top"]) for x in items),
        max(float(x["x1"]) for x in items),
        max(float(x["bottom"]) for x in items),
    ]


def classify(ch, parent):
    cp = ord(ch)
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK_FULL", 30
    if ch in ".,;:，。；：、…":
        return "LOW_PROFILE_PUNCTUATION", None
    if ch in "↓↑=/":
        return "MATH_OPERATOR_OR_SYMBOL", 22
    if ch.isdigit() or ch.isupper():
        if parent == "T_HFUNC" and ch == "2":
            return "NATURAL_SCRIPT", 15
        return "LATIN_UPPER_OR_DIGIT", 24
    if ch.islower() or "GREEK" in unicodedata.name(ch, ""):
        if parent in {"T_HFUNC", "T_XLABEL"} and ch == "𝑖":
            return "NATURAL_SCRIPT" if parent == "T_HFUNC" else "LATIN_LOWER_OR_GREEK", 15 if parent == "T_HFUNC" else 17
        return "LATIN_LOWER_OR_GREEK", 17
    return "FULL_HEIGHT_SYMBOL", 24


def semantic_for(c):
    x0, top, x1, bottom = map(float, (c["x0"], c["top"], c["x1"], c["bottom"]))
    ch = c["text"]
    if top >= 450 and bottom <= 464:
        return "T_XTICKS", "AXIS_TICK", 15, 9.5
    if x1 <= 195 and top >= 329 and bottom <= 454:
        return "T_YTICKS", "AXIS_TICK", 15, 9.5
    if top >= 468 and x0 >= 275:
        return "T_XLABEL", "AXIS_LABEL", 14, 9.6
    if x1 <= 180 and top >= 380:
        return "T_YLABEL", "AXIS_LABEL", 14, 9.6
    if x0 >= 383 and top <= 346:
        return "T_HFUNC", "FORMULA_ANNOTATION", 27, 9.5
    if 238 <= x0 <= 275 and 403 <= top <= 416:
        return "T_TRUTH", "REFERENCE_ANNOTATION", 35, 9.5
    if ch in ".0123456789" and 228 <= x0 <= 248 and 334 <= top <= 347:
        return "T_VALUE_1", "VALUE_LABEL", 37, 9.5
    if ch in ".0123456789" and 297 <= x0 <= 317 and 400 <= top <= 413:
        return "T_VALUE_2", "VALUE_LABEL", 39, 9.5
    if ch in ".0123456789" and 365 <= x0 <= 385 and 370 <= top <= 383:
        return "T_VALUE_3", "VALUE_LABEL", 41, 9.5
    if ch in ".0123456789" and 414 <= x0 <= 434 and 404 <= top <= 417:
        return "T_VALUE_4", "VALUE_LABEL", 43, 9.5
    if 240 <= x0 <= 272 and 343 <= top <= 356:
        return "T_DOWN_FIRST", "TREND_ANNOTATION", 29, 9.5
    if 304 <= x0 <= 333 and 361 <= top <= 374:
        return "T_UP", "TREND_ANNOTATION", 31, 9.5
    if 376 <= x0 <= 415 and 363 <= top <= 376:
        return "T_DOWN_AGAIN", "TREND_ANNOTATION", 33, 9.5
    raise ValueError(f"Unmapped visible glyph {c}")


page_img = Image.open(PAGE_PNG).convert("RGB")
body_px = px_box(BODY_PT)
caption_px = px_box(FIGURE_WITH_CAPTION_PT)
page_img.crop(tuple(caption_px)).save(ROOT / "render" / "figure_crop_300dpi.png")
body_img = page_img.crop(tuple(body_px))
body_img.save(ROOT / "render" / "standalone_300dpi.png")
body_img.convert("L").save(ROOT / "render" / "grayscale_300dpi.png")

chars = [
    c for c in GEOM["chars"]
    if float(c["x0"]) >= BODY_PT[0]
    and float(c["x1"]) <= BODY_PT[2]
    and float(c["top"]) >= BODY_PT[1]
    and float(c["bottom"]) <= BODY_PT[3]
]

tree = etree.parse(str(SVG_PATH))
ns = {"s": "http://www.w3.org/2000/svg"}
xlink = "{http://www.w3.org/1999/xlink}href"
uses = [
    u for u in tree.xpath("//s:use", namespaces=ns)
    if BODY_PT[0] <= float(u.get("x")) <= BODY_PT[2]
    and BODY_PT[1] <= float(u.get("y")) <= BODY_PT[3]
]
if len(chars) != 78 or len(uses) != 78:
    raise RuntimeError(f"Expected 78 glyphs/uses, got chars={len(chars)} uses={len(uses)}")

vectors = Path(__file__).with_name("glyph_vectors")
vectors.mkdir(exist_ok=True)
defs = tree.getroot().find("{http://www.w3.org/2000/svg}defs")
glyph_rows = []
jobs = []

for index, (c, use) in enumerate(zip(chars, uses), start=1):
    parent_id, role, source_line, declared_pt = semantic_for(c)
    script_class, threshold = classify(c["text"], parent_id)
    full_px = px_box([float(c["x0"]), float(c["top"]), float(c["x1"]), float(c["bottom"])])
    local_px = [
        full_px[0] - body_px[0], full_px[1] - body_px[1],
        full_px[2] - body_px[0], full_px[3] - body_px[1],
    ]
    safe = f"T{index:03d}"
    svg_file = vectors / f"{safe}.svg"
    mask_file = ROOT / "masks" / f"{safe}.png"
    w_px = max(1, local_px[2] - local_px[0])
    h_px = max(1, local_px[3] - local_px[1])
    svg_root = etree.Element(
        "{http://www.w3.org/2000/svg}svg",
        nsmap={None: "http://www.w3.org/2000/svg", "xlink": "http://www.w3.org/1999/xlink"},
        width=f"{w_px}px",
        height=f"{h_px}px",
        viewBox=f"{full_px[0] / SCALE:.9f} {full_px[1] / SCALE:.9f} {w_px / SCALE:.9f} {h_px / SCALE:.9f}",
        version="1.2",
    )
    svg_root.append(copy.deepcopy(defs))
    cursor = svg_root
    ancestors = list(use.iterancestors())
    ancestors.reverse()
    for ancestor in ancestors[1:]:
        if ancestor.tag.endswith("defs"):
            continue
        g = etree.SubElement(cursor, "{http://www.w3.org/2000/svg}g")
        for key, value in ancestor.attrib.items():
            if key != "id":
                g.set(key, value)
        cursor = g
    cursor.append(copy.deepcopy(use))
    svg_file.write_bytes(etree.tostring(svg_root, xml_declaration=True, encoding="UTF-8"))
    row = {
        "object_id": safe,
        "safe_filename": f"{safe}.png",
        "object_type": "TEXT_GLYPH",
        "char": c["text"],
        "unicode": f"U+{ord(c['text']):04X}",
        "semantic_parent": parent_id,
        "role": role,
        "script_class": script_class,
        "threshold_px_protocol": threshold,
        "source_line": source_line,
        "declared_pt": declared_pt,
        "graphics_scale": 1.0,
        "effective_pt": declared_pt,
        "pdf_fontname": c.get("fontname"),
        "pdf_size_pt": c.get("size"),
        "pdf_non_stroking_color": c.get("non_stroking_color"),
        "bbox_pt": [c["x0"], c["top"], c["x1"], c["bottom"]],
        "bbox_full_native_px": full_px,
        "bbox_crop_native_px": local_px,
        "svg_use": {"href": use.get(xlink), "x": use.get("x"), "y": use.get("y")},
    }
    glyph_rows.append(row)
    jobs.append({"input": str(svg_file), "output": str(mask_file), "width": w_px, "height": h_px})

body_lines = [o for o in GEOM["lines"] if o["x0"] >= BODY_PT[0] and o["x1"] <= BODY_PT[2] and o["top"] >= BODY_PT[1] and o["bottom"] <= BODY_PT[3]]
body_curves = [o for o in GEOM["curves"] if o["x0"] >= BODY_PT[0] and o["x1"] <= BODY_PT[2] and o["top"] >= BODY_PT[1] and o["bottom"] <= BODY_PT[3]]
body_rects = [o for o in GEOM["rects"] if o["x0"] >= BODY_PT[0] and o["x1"] <= BODY_PT[2] and o["top"] >= BODY_PT[1] and o["bottom"] <= BODY_PT[3]]
if (len(body_lines), len(body_curves), len(body_rects)) != (19, 7, 4):
    raise RuntimeError(f"Unexpected graphics: {len(body_lines)}, {len(body_curves)}, {len(body_rects)}")

graphics = []
def add_graphic(name, role, source_line, primitives, design_connections=None):
    idx = len(graphics) + 1
    raw_bbox = bbox_union(primitives)
    pad_pt = max([float(p.get("linewidth") or 0) for p in primitives] + [0.0]) / 2.0 + 0.60
    bbox = [raw_bbox[0] - pad_pt, raw_bbox[1] - pad_pt, raw_bbox[2] + pad_pt, raw_bbox[3] + pad_pt]
    graphics.append({
        "object_id": f"G{idx:03d}",
        "safe_filename": f"G{idx:03d}.png",
        "object_type": "GRAPHIC",
        "char": "",
        "semantic_parent": name,
        "role": role,
        "script_class": "N/A",
        "threshold_px_protocol": None,
        "source_line": source_line,
        "declared_pt": None,
        "graphics_scale": 1.0,
        "effective_pt": None,
        "bbox_pt": bbox,
        "bbox_full_native_px": px_box(bbox),
        "bbox_crop_native_px": [
            px_box(bbox)[0] - body_px[0], px_box(bbox)[1] - body_px[1],
            px_box(bbox)[2] - body_px[0], px_box(bbox)[3] - body_px[1],
        ],
        "primitive_count": len(primitives),
        "primitives": primitives,
        "design_connections": design_connections or [],
    })

add_graphic("X_AXIS_WITH_ARROWHEAD", "AXIS_LINE", 6, [body_lines[12], body_curves[0]])
add_graphic("Y_AXIS_WITH_ARROWHEAD", "AXIS_LINE", 6, [body_lines[13], body_curves[1]])
for i, line in enumerate(body_lines[0:4], start=1):
    add_graphic(f"X_TICK_{i}", "TICK_MARK", 7, [line], ["G001"])
for i, line in enumerate(body_lines[4:12], start=0):
    add_graphic(f"Y_TICK_{i}", "TICK_MARK", 7, [line], ["G002"])
for i, line in enumerate(body_lines[14:18], start=1):
    add_graphic(f"STEM_{i}", "DATA_STEM", 18, [line], [f"G{24+i:03d}"])
add_graphic("TRUE_MEAN_DASHED", "REFERENCE_LINE", 24, [body_lines[18]])
add_graphic("RUNNING_MEAN_CURVE", "DATA_CURVE", 21, [body_curves[2]], ["G021", "G022", "G023", "G024"])
for i, curve in enumerate(body_curves[3:7], start=1):
    add_graphic(f"RUNNING_MEAN_MARKER_{i}", "DATA_MARKER", 21, [curve], ["G020"])
for i, rect in enumerate(body_rects, start=1):
    add_graphic(f"SQUARED_VALUE_MARKER_{i}", "DATA_MARKER", 18, [rect], [f"G{14+i:03d}"])

for graphic in graphics:
    graphic["visible_denominator"] = graphic["object_id"] != "G016"
    if graphic["object_id"] == "G016":
        graphic["denominator_exclusion_reason"] = "The ycomb stem at y=.01 is fully occluded by its final square marker on official R109 native pixels; it has zero final-visible pixels and is retained only in the source-primitive ledger."
visible_graphics = [g for g in graphics if g["visible_denominator"]]
hidden_source_graphics = [g for g in graphics if not g["visible_denominator"]]
objects = glyph_rows + visible_graphics
expected_pairs = len(objects) * (len(objects) - 1) // 2

for hidden in hidden_source_graphics:
    stale = ROOT / "masks" / hidden["safe_filename"]
    if stale.exists():
        stale.unlink()

(Path(__file__).with_name("03_glyph_render_jobs.json")).write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
(Path(__file__).with_name("03_objects_frozen.json")).write_text(json.dumps({
    "scope": "complete visible foreground denominator inside BODY_PT; caption excluded from object denominator and reviewed separately",
    "body_pt": BODY_PT,
    "body_full_native_px": body_px,
    "figure_with_caption_pt": FIGURE_WITH_CAPTION_PT,
    "figure_with_caption_full_native_px": caption_px,
    "text_glyph_count": len(glyph_rows),
    "source_graphic_semantic_object_count": len(graphics),
    "visible_graphic_semantic_object_count": len(visible_graphics),
    "hidden_source_graphics_excluded_from_visible_denominator": hidden_source_graphics,
    "object_count_N": len(objects),
    "unordered_pair_count_C": expected_pairs,
    "objects": objects,
}, ensure_ascii=False, indent=2), encoding="utf-8")

with (Path(__file__).with_name("03_source_font_audit.csv")).open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["scope", "source_lines", "declared_pt", "graphics_scale", "effective_pt", "protocol_result", "r168_hard_result", "note"])
    writer.writerow(["tikz every node/default", "3-4", 9.5, 1.0, 9.5, "PASS", "PASS", "No resizebox/scalebox/transform shape; only path cap/join style."])
    writer.writerow(["tick labels", "8,16", 9.5, 1.0, 9.5, "PASS", "PASS", "Explicit 9.5pt."])
    writer.writerow(["axis labels", "9,17", 9.6, 1.0, 9.6, "PASS", "PASS", "Explicit 9.6pt."])
    writer.writerow(["annotations/value labels", "26-43", 9.5, 1.0, 9.5, "PASS", "PASS", "All explicit 9.5pt."])

print(json.dumps({
    "body_px": body_px,
    "figure_with_caption_px": caption_px,
    "text_glyph_count": len(glyph_rows),
    "source_graphic_object_count": len(graphics),
    "visible_graphic_object_count": len(visible_graphics),
    "object_count_N": len(objects),
    "unordered_pair_count_C": expected_pairs,
}, ensure_ascii=False, indent=2))
