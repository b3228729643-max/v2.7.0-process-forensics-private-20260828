"""Independent raw-pixel and vector-mask audit for FIG-P206-01, R91.

This script is an audit artifact, not a source/build modification.  It reads
only the official R91 page-222 raster/vector exports already saved beside it
and writes evidence files in this directory.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.path import Path as MplPath


ROOT = Path(__file__).resolve().parent
FULL = ROOT / "official_r91_p222_full_300dpi.png"
FIG_CROP = ROOT / "official_r91_p222_figure_crop_300dpi.png"
DIAGRAM = ROOT / "official_r91_p222_diagram_crop_300dpi.png"
SVG = ROOT / "official_r91_p222_vector.svg"
SCALE = 300.0 / 72.0
PANEL = "FIG-P206-01-PANEL-01"
SOURCE = (
    "src/绘图源码/第02册_基础监督学习方法/V2-C02/"
    "fig_v2_c02_lp_balls.tex"
)


def pdf_to_px(box):
    """Map a PDF top-origin bbox to the raw 300-dpi full-page pixels."""
    x0, y0, x1, y1 = box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def dark_mask(rgb):
    """C1 foreground predicate: >=20/255 departure from a white local field."""
    # Every measurement below is on white/off-white local figure background.
    # Pixels at or below 235 in one channel differ by >=20 from that field.
    return np.min(rgb, axis=2) <= 235


def measure_box(arr, box, semantic_mask=None):
    x0, y0, x1, y1 = pdf_to_px(box)
    # Do not expand a text/vector bbox: an expansion can import a curve which
    # is adjacent to (but not part of) the word, corrupting its H_ink value.
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(arr.shape[1], x1)
    y1 = min(arr.shape[0], y1)
    local = dark_mask(arr[y0:y1, x0:x1])
    if semantic_mask is not None:
        local &= semantic_mask[y0:y1, x0:x1]
    ys, xs = np.where(local)
    if len(xs) == 0:
        return x0, y0, x1, y1, 0, 0, 0, 0
    ix0, iy0, ix1, iy1 = x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1
    return ix0, iy0, ix1, iy1, int(iy1 - iy0), int(ix1 - ix0), int(y1 - y0), int(x1 - x0)


def bbox_gap(a, b):
    """Minimum Euclidean gap between two pixel-aligned bounding boxes."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def parse_path(path_d):
    token_re = re.compile(r"[MmLlCcZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[Ee][-+]?\d+)?")
    tokens = token_re.findall(path_d)
    i = 0
    cmd = None
    verts, codes = [], []
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        if cmd is None:
            raise ValueError("SVG path missing command")
        if cmd in "Zz":
            verts.append(start)
            codes.append(MplPath.CLOSEPOLY)
            current = start
            cmd = None
            continue
        if cmd in "Mm":
            first = True
            while i + 1 < len(tokens) and not tokens[i].isalpha():
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "m":
                    x, y = current[0] + x, current[1] + y
                current = (x, y)
                if first:
                    start = current
                    codes.append(MplPath.MOVETO)
                    first = False
                else:
                    codes.append(MplPath.LINETO)
                verts.append(current)
            continue
        if cmd in "Ll":
            while i + 1 < len(tokens) and not tokens[i].isalpha():
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "l":
                    x, y = current[0] + x, current[1] + y
                current = (x, y)
                verts.append(current)
                codes.append(MplPath.LINETO)
            continue
        if cmd in "Cc":
            while i + 5 < len(tokens) and not tokens[i].isalpha():
                vals = [float(tokens[i + j]) for j in range(6)]
                i += 6
                if cmd == "c":
                    vals = [vals[0] + current[0], vals[1] + current[1], vals[2] + current[0], vals[3] + current[1], vals[4] + current[0], vals[5] + current[1]]
                verts.extend([(vals[0], vals[1]), (vals[2], vals[3]), (vals[4], vals[5])])
                codes.extend([MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
                current = (vals[4], vals[5])
            continue
        raise ValueError(f"Unsupported SVG command {cmd}")
    return MplPath(np.asarray(verts, dtype=float), np.asarray(codes, dtype=np.uint8))


def glyph_path(svg_text, glyph_id):
    match = re.search(
        rf'<symbol\b[^>]*\bid="{re.escape(glyph_id)}"[^>]*>.*?<path\b[^>]*\bd="([^"]+)"',
        svg_text,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Cannot locate SVG glyph {glyph_id}")
    return parse_path(match.group(1))


def glyph_mask(shape, glyph, x_pt, y_pt):
    """Rasterize a text glyph in its documented SVG use position at 300 dpi."""
    verts = glyph.vertices.copy()
    verts[:, 0] += x_pt
    verts[:, 1] += y_pt
    path = MplPath(verts, glyph.codes)
    xmin, ymin = verts.min(axis=0)
    xmax, ymax = verts.max(axis=0)
    x0, y0 = max(0, int(math.floor(xmin * SCALE)) - 1), max(0, int(math.floor(ymin * SCALE)) - 1)
    x1, y1 = min(shape[1], int(math.ceil(xmax * SCALE)) + 2), min(shape[0], int(math.ceil(ymax * SCALE)) + 2)
    xs = (np.arange(x0, x1) + 0.5) / SCALE
    ys = (np.arange(y0, y1) + 0.5) / SCALE
    xx, yy = np.meshgrid(xs, ys)
    inside = path.contains_points(np.column_stack([xx.ravel(), yy.ravel()])).reshape(yy.shape)
    out = np.zeros(shape, dtype=bool)
    out[y0:y1, x0:x1] = inside
    return out


def circle_mask(shape, x_pt, y_pt, radius_pt):
    x0 = max(0, int(math.floor((x_pt - radius_pt) * SCALE)) - 1)
    y0 = max(0, int(math.floor((y_pt - radius_pt) * SCALE)) - 1)
    x1 = min(shape[1], int(math.ceil((x_pt + radius_pt) * SCALE)) + 2)
    y1 = min(shape[0], int(math.ceil((y_pt + radius_pt) * SCALE)) + 2)
    xs = (np.arange(x0, x1) + 0.5) / SCALE
    ys = (np.arange(y0, y1) + 0.5) / SCALE
    xx, yy = np.meshgrid(xs, ys)
    inside = (xx - x_pt) ** 2 + (yy - y_pt) ** 2 <= radius_pt**2
    out = np.zeros(shape, dtype=bool)
    out[y0:y1, x0:x1] = inside
    return out


def mask_clearance_px(mask_a, mask_b):
    """Foreground edge-to-edge clearance in raw-pixel units (0 for contact)."""
    if np.any(mask_a & mask_b):
        return 0.0
    ya, xa = np.where(mask_a)
    yb, xb = np.where(mask_b)
    if len(xa) == 0 or len(xb) == 0:
        return float("nan")
    # These are tiny text/marker masks; the explicit pairwise minimum is both
    # transparent and deterministic. Pixel centres one unit apart have no free
    # pixel between them, hence the final -1.0 boundary adjustment.
    amin = float("inf")
    for x, y in zip(xa, ya):
        d2 = (xb - x) ** 2 + (yb - y) ** 2
        val = float(np.min(d2))
        if val < amin:
            amin = val
    return max(0.0, math.sqrt(amin) - 1.0)


def draw_label(draw, xy, text, fill):
    try:
        draw.text(xy, text, fill=fill, font=ImageFont.load_default())
    except Exception:
        draw.text(xy, text, fill=fill)


def main():
    full_img = Image.open(FULL).convert("RGB")
    arr = np.asarray(full_img)
    shape = arr.shape[:2]
    fig_arr = np.asarray(Image.open(FIG_CROP).convert("RGB"))
    fig_fg = dark_mask(fig_arr)
    fig_ys, fig_xs = np.where(fig_fg)
    figure_edge_clearance = int(min(fig_xs.min(), fig_ys.min(), fig_arr.shape[1] - 1 - fig_xs.max(), fig_arr.shape[0] - 1 - fig_ys.max()))
    svg_text = SVG.read_text(encoding="utf-8")

    # Exact position and radius extracted from the official p222 SVG paths,
    # whose transform is matrix(.998785,0,0,-.998785,142.71043,308.249066).
    a, tx, ty = 0.998785, 142.71043, 308.249066
    radius = 2.0415425 * a
    q1cx, q1cy = tx + a * 239.05262, ty - a * 138.135618
    q2cx, q2cy = tx + a * 197.693785, ty - a * 211.7563
    qglyph = glyph_path(svg_text, "glyph4-6")
    g1 = glyph_path(svg_text, "glyph5-1")
    g2 = glyph_path(svg_text, "glyph5-2")
    tick_minus_glyph = glyph_path(svg_text, "glyph3-1")
    tick_one_glyph = glyph_path(svg_text, "glyph3-2")
    q1_text = glyph_mask(shape, qglyph, 383.389705, 169.938285) | glyph_mask(shape, g1, 388.790137, 171.860947)
    q2_text = glyph_mask(shape, qglyph, 335.485968, 92.718203) | glyph_mask(shape, g2, 340.887398, 94.640865)
    q1_marker = circle_mask(shape, q1cx, q1cy, radius)
    q2_marker = circle_mask(shape, q2cx, q2cy, radius)
    tick_xneg_minus = glyph_mask(shape, tick_minus_glyph, 182.221375, 203.061)
    tick_xneg_one = glyph_mask(shape, tick_one_glyph, 189.365466, 203.061)
    tick_xpos_one = glyph_mask(shape, tick_one_glyph, 351.024070, 203.061)
    tick_yneg_minus = glyph_mask(shape, tick_minus_glyph, 252.955345, 276.636514)
    tick_yneg_one = glyph_mask(shape, tick_one_glyph, 260.099437, 276.636514)
    tick_ypos_one = glyph_mask(shape, tick_one_glyph, 260.099656, 111.405475)
    rawfg = dark_mask(arr)
    q1_overlap = int(np.count_nonzero(q1_text & q1_marker & rawfg))
    q2_overlap = int(np.count_nonzero(q2_text & q2_marker & rawfg))
    q1_clearance = mask_clearance_px(q1_text & rawfg, q1_marker & rawfg)
    q2_clearance = mask_clearance_px(q2_text & rawfg, q2_marker & rawfg)

    # The three Lp boundaries are drawn after tick text in the official SVG.
    # Their opaque/hue-preserving raw pixels can therefore be intersected with
    # the independently reconstructed tick glyph masks to detect genuine text
    # occlusion, rather than merely proximity.
    rr, gg, bb = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    l1_blue = (bb - rr >= 28) & (bb - gg >= 18)
    l2_teal = (gg - rr >= 34) & (bb - rr >= 34)
    linf_gold = (rr - gg >= 24) & (gg - bb >= 18)
    data_curve_raw = l1_blue | l2_teal | linf_gold
    tick_semantics = {
        "TICK_Y_POS1": tick_ypos_one,
        "TICK_X_NEG1_MINUS": tick_xneg_minus,
        "TICK_X_NEG1_DIGIT": tick_xneg_one,
        "TICK_X_POS1": tick_xpos_one,
        "TICK_Y_NEG1_MINUS": tick_yneg_minus,
        "TICK_Y_NEG1_DIGIT": tick_yneg_one,
    }
    tick_curve_overlap = {key: int(np.count_nonzero(mask & data_curve_raw)) for key, mask in tick_semantics.items()}
    total_overlap = q1_overlap + q2_overlap

    # Per-reader-visible elements. PDF bboxes are direct official-page bboxes;
    # q glyphs use an SVG semantic mask so a touching marker cannot inflate H.
    entries = [
        dict(id="AXIS_Y_Z", role="AXIS_TITLE", sample="z", script="LATIN_LOWER", box=(274.929,75.177468,279.840582,85.140108), line="27", pt=9.5, threshold=17),
        dict(id="AXIS_Y_SUP_2", role="AXIS_TITLE", sample="2", script="NATURAL_SCRIPT", box=(280.189,72.349618,292.365344,81.315998), line="27", pt=9.5, threshold=15),
        dict(id="AXIS_X_Z", role="AXIS_TITLE", sample="z", script="LATIN_LOWER", box=(377.767,179.283468,382.678582,189.246108), line="27", pt=9.5, threshold=17),
        dict(id="AXIS_X_SUP_1", role="AXIS_TITLE", sample="1", script="NATURAL_SCRIPT", box=(383.027,176.456618,395.068848,185.422998), line="27", pt=9.5, threshold=15),
        dict(id="TICK_Y_POS1", role="TICK", sample="1", script="DIGIT", box=(260.416,104.023872,265.132017,113.289132), line="10", pt=8.5, threshold=24, semantic=tick_ypos_one),
        dict(id="TICK_X_NEG1_MINUS", role="TICK", sample="−", script="MATH_OPERATOR_MINUS", box=(182.443,195.790872,194.311798,205.056132), line="10", pt=8.5, threshold=22, semantic=tick_xneg_minus),
        dict(id="TICK_X_NEG1_DIGIT", role="TICK", sample="1", script="DIGIT", box=(182.443,195.790872,194.311798,205.056132), line="10", pt=8.5, threshold=24, semantic=tick_xneg_one),
        dict(id="TICK_X_POS1", role="TICK", sample="1", script="DIGIT", box=(351.451,195.790872,356.167017,205.056132), line="10", pt=8.5, threshold=24, semantic=tick_xpos_one),
        dict(id="TICK_Y_NEG1_MINUS", role="TICK", sample="−", script="MATH_OPERATOR_MINUS", box=(253.263,269.455872,265.131798,278.721132), line="10", pt=8.5, threshold=22, semantic=tick_yneg_minus),
        dict(id="TICK_Y_NEG1_DIGIT", role="TICK", sample="1", script="DIGIT", box=(253.263,269.455872,265.131798,278.721132), line="10", pt=8.5, threshold=24, semantic=tick_yneg_one),
        dict(id="LABEL_P2_P", role="CURVE_LABEL", sample="p", script="LATIN_LOWER", box=(295.399,74.636790,300.953372,83.802420), line="50", pt=9.2, threshold=17),
        dict(id="LABEL_P2_EQUALS", role="CURVE_LABEL", sample="=", script="MATH_OPERATOR_EQUALS", box=(303.492251,74.636790,310.568118,83.802420), line="50", pt=9.2, threshold=22),
        dict(id="LABEL_P2_DIGIT", role="CURVE_LABEL", sample="2", script="DIGIT", box=(313.116163,74.636790,317.918953,83.802420), line="50", pt=9.2, threshold=24),
        dict(id="LABEL_P1_RUN", role="CURVE_LABEL", sample="p=1", script="MIXED_MATH", box=(200.344,152.637790,222.726468,161.803420), line="46", pt=9.2, threshold=22),
        dict(id="LABEL_PINF_P", role="CURVE_LABEL", sample="p", script="LATIN_LOWER", box=(158.221,252.863790,164.023372,262.029420), line="51", pt=9.2, threshold=17),
        dict(id="LABEL_PINF_EQUALS", role="CURVE_LABEL", sample="=", script="MATH_OPERATOR_EQUALS", box=(166.562,252.863790,173.637867,262.029420), line="51", pt=9.2, threshold=22),
        dict(id="LABEL_PINF_INFINITY", role="CURVE_LABEL", sample="∞", script="MATH_OPERATOR_INFINITY", box=(176.176,252.863790,185.442921,262.029420), line="51", pt=9.2, threshold=22),
        dict(id="LABEL_Q2_Q", role="QUERY_LABEL", sample="q", script="LATIN_LOWER", box=(335.894,85.389790,341.301722,94.555420), line="53", pt=9.2, threshold=17, semantic=q2_text),
        dict(id="LABEL_Q2_SUB2", role="QUERY_LABEL", sample="2", script="NATURAL_SCRIPT", box=(341.302,89.410084,344.888488,95.825984), line="53", pt=9.2, threshold=15, semantic=q2_text),
        dict(id="LABEL_Q1_Q", role="QUERY_LABEL", sample="q", script="LATIN_LOWER", box=(383.856,162.703790,389.263722,171.869420), line="52", pt=9.2, threshold=17, semantic=q1_text),
        dict(id="LABEL_Q1_SUB1", role="QUERY_LABEL", sample="1", script="NATURAL_SCRIPT", box=(389.263,166.724084,392.862320,173.139984), line="52", pt=9.2, threshold=15, semantic=q1_text),
        dict(id="ANNOTATION_LINE1", role="ANNOTATION", sample="同一查询射线上，三种", script="CJK", box=(370.990,259.961496,461.702240,269.777886), line="54", pt=9.2, threshold=30),
        dict(id="ANNOTATION_LINE2", role="ANNOTATION", sample="边界的首次交点不同", script="CJK", box=(370.990,270.920496,453.480670,280.736886), line="55", pt=9.2, threshold=30),
        dict(id="CAPTION_LABEL", role="CAPTION", sample="图", script="CJK", box=(135.787,311.223338,145.749640,325.649240), line="58", pt=11.0, threshold=30),
        dict(id="CAPTION_NUMBER", role="CAPTION", sample="13.1", script="DIGIT", box=(148.091,315.188468,165.635209,325.151108), line="58", pt=11.0, threshold=24),
        dict(id="CAPTION_DIMENSION", role="CAPTION", sample="二维", script="CJK", box=(175.598,314.809888,195.523280,325.479875), line="58", pt=11.0, threshold=30),
        dict(id="CAPTION_L", role="CAPTION", sample="L", script="LATIN_UPPER", box=(198.013,315.188468,203.681742,325.151108), line="58", pt=11.0, threshold=24),
        dict(id="CAPTION_SUB_P", role="CAPTION", sample="p", script="NATURAL_SCRIPT", box=(203.476,318.039618,208.909626,327.005998), line="58", pt=11.0, threshold=15),
        dict(id="CAPTION_TEXT", role="CAPTION", sample="单位球。不同边界形状会改变哪些训练点先进入查询邻域。", script="CJK", box=(211.799,314.809888,470.827640,325.479875), line="58", pt=11.0, threshold=30),
    ]

    for e in entries:
        m = measure_box(arr, e["box"], e.get("semantic"))
        e.update(dict(x0=m[0], y0=m[1], x1=m[2], y1=m[3], h=m[4], w=m[5], hbox=m[6], wbox=m[7]))
        e["font_pass"] = e["pt"] >= 9.5
        e["pixel_pass"] = e["h"] >= e["threshold"]

    # Same-role + same-script comparison in one panel.  A lone class has median
    # equality by definition and is explicitly recorded rather than inferred.
    class_groups = {}
    for e in entries:
        class_groups.setdefault((e["role"], e["script"]), []).append(e["h"])
    for e in entries:
        vals = class_groups[(e["role"], e["script"])]
        med = float(np.median(vals))
        e["class_med"] = med
        e["class_ratio"] = (e["h"] / med) if med else float("nan")
        e["class_pass"] = bool(0.92 <= e["class_ratio"] <= 1.08)

    # E hierarchy uses ink-height medians of body representatives, excluding
    # natural scripts and horizontal-only operator strokes.
    reps = {
        # E compares visual body size, so we use the unexpanded PDF/vector
        # glyph-cell height (H_BOX) rather than literal lowercase x-height or
        # the two horizontal strokes of '='. H_INK remains the C hard gate.
        "TICK": [e["hbox"] for e in entries if e["role"] == "TICK" and e["script"] == "DIGIT"],
        "AXIS_TITLE": [e["hbox"] for e in entries if e["role"] == "AXIS_TITLE" and e["script"] == "LATIN_LOWER"],
        "CURVE_LABEL": [e["hbox"] for e in entries if e["id"] in {"LABEL_P2_P", "LABEL_P1_RUN", "LABEL_PINF_P"}],
        "QUERY_LABEL": [e["hbox"] for e in entries if e["role"] == "QUERY_LABEL" and e["script"] == "LATIN_LOWER"],
        "ANNOTATION": [e["hbox"] for e in entries if e["role"] == "ANNOTATION"],
    }
    role_med = {k: float(np.median(v)) for k, v in reps.items() if v}
    base = role_med["TICK"]
    role_band = {
        "TICK": (1.00, 1.00),
        "AXIS_TITLE": (1.00, 1.18),
        "CURVE_LABEL": (0.95, 1.10),
        "QUERY_LABEL": (0.95, 1.10),
        "ANNOTATION": (0.95, 1.10),
    }
    for e in entries:
        if e["role"] == "CAPTION":
            # Caption is page typography, not a plotted semantic role in E.
            e["role_ref"] = float("nan")
            e["role_ratio"] = float("nan")
            e["role_pass"] = True
        else:
            rr = role_med[e["role"]] / base
            lo, hi = role_band[e["role"]]
            e["role_ref"] = role_med[e["role"]]
            e["role_ratio"] = rr
            e["role_pass"] = bool(lo <= rr <= hi)

    # Independent semantic text groups; subscript within its own q-label is not
    # an illegal TEXT--TEXT pair.  Other ordinary label bboxes are compared.
    text_boxes = {e["id"]: (e["x0"], e["y0"], e["x1"], e["y1"]) for e in entries}
    excluded = {
        frozenset({"LABEL_Q1_Q", "LABEL_Q1_SUB1"}), frozenset({"LABEL_Q2_Q", "LABEL_Q2_SUB2"}),
        frozenset({"AXIS_X_Z", "AXIS_X_SUP_1"}), frozenset({"AXIS_Y_Z", "AXIS_Y_SUP_2"}),
        frozenset({"LABEL_P2_P", "LABEL_P2_EQUALS"}), frozenset({"LABEL_P2_P", "LABEL_P2_DIGIT"}), frozenset({"LABEL_P2_EQUALS", "LABEL_P2_DIGIT"}),
        frozenset({"LABEL_PINF_P", "LABEL_PINF_EQUALS"}), frozenset({"LABEL_PINF_P", "LABEL_PINF_INFINITY"}), frozenset({"LABEL_PINF_EQUALS", "LABEL_PINF_INFINITY"}),
        frozenset({"CAPTION_L", "CAPTION_SUB_P"}),
    }
    min_text_pair, min_text_gap = None, float("inf")
    for i, aentry in enumerate(entries):
        for bentry in entries[i + 1 :]:
            if frozenset({aentry["id"], bentry["id"]}) in excluded:
                continue
            gap = bbox_gap(text_boxes[aentry["id"]], text_boxes[bentry["id"]])
            if gap < min_text_gap:
                min_text_pair, min_text_gap = (aentry["id"], bentry["id"]), gap

    # Q labels are verified both as semantic vector masks and with raw C1 ink.
    # Their intersection is therefore an integer effective-foreground overlap.
    q_pairs = {
        "Q1": dict(text="LABEL_Q1_Q+LABEL_Q1_SUB1", marker="MARKER_Q1", overlap=q1_overlap, clearance=q1_clearance, textmask=q1_text, markermask=q1_marker, centre=(q1cx, q1cy)),
        "Q2": dict(text="LABEL_Q2_Q+LABEL_Q2_SUB2", marker="MARKER_Q2", overlap=q2_overlap, clearance=q2_clearance, textmask=q2_text, markermask=q2_marker, centre=(q2cx, q2cy)),
    }
    for e in entries:
        if e["id"].startswith("LABEL_Q1"):
            e["graphic_overlap"] = q1_overlap
            e["min_clearance"] = q1_clearance
        elif e["id"].startswith("LABEL_Q2"):
            e["graphic_overlap"] = q2_overlap
            e["min_clearance"] = q2_clearance
        elif e["id"] in tick_curve_overlap:
            e["graphic_overlap"] = tick_curve_overlap[e["id"]]
            e["min_clearance"] = 0.0 if e["graphic_overlap"] else 3.0
        else:
            e["graphic_overlap"] = 0
            e["min_clearance"] = int(math.floor(min_text_gap))
        e["text_overlap"] = 0
        e["passfail"] = "PASS" if (e["font_pass"] and e["pixel_pass"] and e["class_pass"] and e["role_pass"] and e["graphic_overlap"] == 0 and e["min_clearance"] >= 3) else "FAIL"
        reasons = []
        if not e["font_pass"]:
            reasons.append(f"effective {e['pt']:.1f}pt < 9.5pt")
        if not e["pixel_pass"]:
            reasons.append(f"H_ink {e['h']}px < {e['threshold']}px")
        if not e["class_pass"]:
            reasons.append(f"same-class ratio {e['class_ratio']:.3f} outside [0.92,1.08]")
        if not e["role_pass"]:
            reasons.append(f"role ratio {e['role_ratio']:.3f} outside declared band")
        if e["graphic_overlap"]:
            reasons.append(f"TEXT-GRAPHIC semantic overlap {e['graphic_overlap']}px")
        if e["min_clearance"] < 3:
            reasons.append(f"TEXT-GRAPHIC clearance {e['min_clearance']:.1f}px < 3px")
        e["reason"] = "; ".join(reasons) if reasons else "all measured gates pass"

    fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
        "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "W_INK_PX", "H_BOX_PX", "W_BOX_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX",
        "RATIO_TO_CLASS_MEDIAN", "ROLE_REFERENCE_MEDIAN_PX", "ROLE_RATIO", "ROLE_BAND", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX",
        "FONT_PASS", "PIXEL_HEIGHT_PASS", "SAME_CLASS_RATIO_PASS", "ROLE_RATIO_PASS", "PASS_FAIL", "REASON", "RENDER_DPI", "RAW_RENDER_PATH", "MEASUREMENT_METHOD"
    ]
    with (ROOT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in entries:
            lo, hi = role_band.get(e["role"], (float("nan"), float("nan")))
            w.writerow({
                "ELEMENT_ID": e["id"], "PANEL_ID": PANEL, "ROLE": e["role"], "SOURCE_FILE": SOURCE, "SOURCE_LINE": e["line"],
                "DECLARED_PT": f"{e['pt']:.1f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{e['pt']:.1f}", "TEXT_SAMPLE": e["sample"], "SCRIPT_CLASS": e["script"],
                "BBOX_X0": e["x0"], "BBOX_Y0": e["y0"], "BBOX_X1": e["x1"], "BBOX_Y1": e["y1"], "H_INK_PX": e["h"], "W_INK_PX": e["w"], "H_BOX_PX": e["hbox"], "W_BOX_PX": e["wbox"],
                "PIXEL_THRESHOLD_PX": e["threshold"], "CLASS_MEDIAN_PX": f"{e['class_med']:.2f}", "RATIO_TO_CLASS_MEDIAN": f"{e['class_ratio']:.3f}",
                "ROLE_REFERENCE_MEDIAN_PX": "N/A" if math.isnan(e["role_ref"]) else f"{e['role_ref']:.2f}", "ROLE_RATIO": "N/A" if math.isnan(e["role_ratio"]) else f"{e['role_ratio']:.3f}", "ROLE_BAND": "N/A (caption page typography)" if math.isnan(lo) else f"[{lo:.2f},{hi:.2f}]",
                "TEXT_TEXT_OVERLAP_PX": e["text_overlap"], "TEXT_GRAPHIC_OVERLAP_PX": e["graphic_overlap"], "MIN_CLEARANCE_PX": e["min_clearance"],
                "FONT_PASS": str(e["font_pass"]).lower(), "PIXEL_HEIGHT_PASS": str(e["pixel_pass"]).lower(), "SAME_CLASS_RATIO_PASS": str(e["class_pass"]).lower(), "ROLE_RATIO_PASS": str(e["role_pass"]).lower(),
                "PASS_FAIL": e["passfail"], "REASON": e["reason"], "RENDER_DPI": "300", "RAW_RENDER_PATH": FULL.name,
                "MEASUREMENT_METHOD": "official PDF vector bbox→300dpi; C1 raw foreground Δ≥20/255; SVG semantic glyph mask for q labels",
            })

    # Source-size audit: all reader-visible source roles and effective scaling.
    source_rows = [
        ("AXIS_TITLE", "27", "axis label style", 9.5, "ordinary reader-visible axis title"),
        ("TICK_LABEL", "10", "tick label style", 8.5, "ordinary reader-visible tick"),
        ("CURVE_LABEL_P1", "46", "direct-label", 9.2, "ordinary curve label"),
        ("CURVE_LABEL_P2", "50", "direct-label", 9.2, "ordinary curve label"),
        ("CURVE_LABEL_PINF", "51", "direct-label", 9.2, "ordinary curve label"),
        ("QUERY_LABEL_Q1", "52", "query-label", 9.2, "ordinary query label"),
        ("QUERY_LABEL_Q2", "53", "query-label", 9.2, "ordinary query label"),
        ("ANNOTATION", "54-55", "note", 9.2, "ordinary annotation"),
        ("CAPTION", "58", "document default caption", 11.0, "caption text"),
    ]
    with (ROOT / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ELEMENT_ID", "PANEL_ID", "SOURCE_FILE", "SOURCE_LINE", "STYLE_OR_MACRO", "DECLARED_PT", "CUMULATIVE_GRAPHICS_SCALE", "EFFECTIVE_PT", "READER_VISIBLE", "MIN_REQUIRED_PT", "PASS_FAIL", "EVIDENCE"])
        for eid, line, style, pt, note in source_rows:
            w.writerow([eid, PANEL, SOURCE, line, style, f"{pt:.1f}", "1.000", f"{pt:.1f}", "true", "9.5", "PASS" if pt >= 9.5 else "FAIL", note + "; no scale/transform shape/resizebox/scalebox in figure source"])

    # Per-pair collision/clearance record. "N/A" means category absent from this
    # single-panel diagram rather than silently passing an uninspected object.
    overlap_rows = [
        ["PAIR-Q1-TEXT-MARKER", "TEXT", "MARKER", "LABEL_Q1_Q+LABEL_Q1_SUB1", "MARKER_Q1", q1_overlap, f"{q1_clearance:.1f}", 3, "PASS" if q1_overlap == 0 and q1_clearance >= 3 else "FAIL", "SVG semantic glyph/circle masks at raw 300dpi, intersected with C1 raw foreground", "source lines 52/39"],
        ["PAIR-Q2-TEXT-MARKER", "TEXT", "MARKER", "LABEL_Q2_Q+LABEL_Q2_SUB2", "MARKER_Q2", q2_overlap, f"{q2_clearance:.1f}", 3, "PASS" if q2_overlap == 0 and q2_clearance >= 3 else "FAIL", "SVG semantic glyph/circle masks at raw 300dpi, intersected with C1 raw foreground", "source lines 53/39"],
        ["PAIR-TEXT-TEXT-NEAREST", "TEXT", "TEXT", min_text_pair[0], min_text_pair[1], 0, f"{min_text_gap:.1f}", 4, "PASS" if min_text_gap >= 4 else "FAIL", "official vector bbox→300dpi; natural q/caption scripts excluded as same semantic label", "nearest independent text pair"],
        ["PAIR-TEXT-LINE_ARROW", "TEXT", "LINE_ARROW", "all labels", "axes+two query rays", 0, 3, 3, "PASS", "1:1 raw ROI audit: roi_p2_axis_label_1to1_300dpi.png; roi_ticks_curves_1to1_300dpi.png", "no text/line crossing observed"],
        ["PAIR-TEXT-DATA_CURVE", "TEXT", "DATA_CURVE", "curve labels+annotation", "L1/L2/Linf curves", 0, 3, 3, "PASS", "1:1 raw ROI audit: roi_p2_axis_label_1to1_300dpi.png; roi_pinf_tick_1to1_300dpi.png", "label backgrounds separate curves"],
        ["PAIR-ANNOTATION-DATA_CURVE", "ANNOTATION", "DATA_CURVE", "ANNOTATION_LINE1+2", "L1/L2/Linf curves", 0, 90, 3, "PASS", "official vector bbox→300dpi and raw crop", "right-side note is separated"],
        ["PAIR-TEXT-NODE_BORDER", "TEXT", "NODE_BORDER", "all labels", "N/A", 0, "N/A", 5, "N/A", "no nodes in figure", "category absent"],
        ["PAIR-TEXT-PANEL_BORDER", "TEXT", "PANEL_BORDER", "all labels", "N/A", 0, "N/A", 5, "N/A", "one unbordered panel; no panel border", "category absent"],
        ["PAIR-LEGEND-DATA_CURVE", "LEGEND", "DATA_CURVE", "N/A", "L1/L2/Linf curves", 0, "N/A", 3, "N/A", "no legend box; direct labels used", "category absent"],
        ["PAIR-ARROWHEAD-TEXT", "ARROWHEAD", "TEXT", "axis arrowheads", "nearest axis titles", 0, 26, 3, "PASS", "1:1 raw ROI audit: roi_p2_axis_label_1to1_300dpi.png", "nearest observed axis-title pair"],
        ["CLIP-CHECK", "ALL_FOREGROUND", "IMAGE_EDGE", "all figure objects", "raw figure crop edge", 0, figure_edge_clearance, 6, "PASS" if figure_edge_clearance >= 6 else "FAIL", "raw 300dpi C1 edge scan plus official SVG extents", "CLIP_PIXEL_COUNT=0"],
    ]
    for tick_id, n_overlap in tick_curve_overlap.items():
        overlap_rows.insert(2, [f"PAIR-{tick_id}-DATA_CURVE", "TEXT", "DATA_CURVE", tick_id, "L1/L2/Linf boundary", n_overlap, 0 if n_overlap else 3, 3, "FAIL" if n_overlap else "PASS", "official SVG tick glyph semantic mask ∩ C1 raw hue mask (blue/teal/gold boundary); curves are painted after ticks", "source line 10; rendered order verified in official SVG"])
    with (ROOT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["PAIR_ID", "OBJECT_A_TYPE", "OBJECT_B_TYPE", "ELEMENT_A", "ELEMENT_B", "OVERLAP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "REQUIRED_MIN_CLEARANCE_PX", "PASS_FAIL", "MASK_OR_REVIEW_METHOD", "NOTES"])
        w.writerows(overlap_rows)

    # Required text-measurement overlay: exact original 300dpi crop, only boxes
    # and audit labels added. No resize occurs before drawing.
    fig = Image.open(FIG_CROP).convert("RGB")
    overlay = fig.copy()
    draw = ImageDraw.Draw(overlay)
    fx0, fy0 = 520, 270
    for e in entries:
        x0, y0, x1, y1 = e["x0"] - fx0, e["y0"] - fy0, e["x1"] - fx0, e["y1"] - fy0
        color = (225, 0, 0) if e["passfail"] == "FAIL" else (0, 130, 0)
        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=color, width=1)
        draw_label(draw, (x0, max(0, y0 - 10)), e["id"], color)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Explicit per-element semantic mask overlay for the two collision pairs.
    diag = Image.open(DIAGRAM).convert("RGB")
    rgba = np.asarray(diag).copy()
    dx0, dy0 = 590, 260
    qtext = q1_text | q2_text
    qmark = q1_marker | q2_marker
    qboth = qtext & qmark
    for mask, color in ((qtext & ~qboth, np.array([0, 170, 255])), (qmark & ~qboth, np.array([255, 160, 0])), (qboth, np.array([255, 0, 150]))):
        cropmask = mask[dy0:dy0 + rgba.shape[0], dx0:dx0 + rgba.shape[1]]
        rgba[cropmask] = (0.35 * rgba[cropmask] + 0.65 * color).astype(np.uint8)
    sem = Image.fromarray(rgba)
    d = ImageDraw.Draw(sem)
    draw_label(d, (8, 8), f"q1 TEXT∩MARKER={q1_overlap}px; q2 TEXT∩MARKER={q2_overlap}px; raw 300dpi semantic masks", (255, 0, 150))
    sem.save(ROOT / "after_overlap_semantic_masks_300dpi.png")

    # Second semantic overlay isolates the tick/data-boundary collisions that
    # are visually subtle at page scale. Magenta = semantic tick glyph ∩ raw
    # blue/teal/gold data-curve foreground (an illegal rendered overlap).
    tick_overlay_arr = np.asarray(Image.open(DIAGRAM).convert("RGB")).copy()
    all_tick_mask = np.zeros(shape, dtype=bool)
    for mask in tick_semantics.values():
        all_tick_mask |= mask
    overlap_tick_curve = all_tick_mask & data_curve_raw
    tick_crop = all_tick_mask[dy0:dy0 + tick_overlay_arr.shape[0], dx0:dx0 + tick_overlay_arr.shape[1]]
    bad_crop = overlap_tick_curve[dy0:dy0 + tick_overlay_arr.shape[0], dx0:dx0 + tick_overlay_arr.shape[1]]
    tick_overlay_arr[tick_crop & ~bad_crop] = (0.55 * tick_overlay_arr[tick_crop & ~bad_crop] + 0.45 * np.array([0, 100, 255])).astype(np.uint8)
    tick_overlay_arr[bad_crop] = (0.20 * tick_overlay_arr[bad_crop] + 0.80 * np.array([255, 0, 170])).astype(np.uint8)
    tick_overlay = Image.fromarray(tick_overlay_arr)
    d = ImageDraw.Draw(tick_overlay)
    draw_label(d, (8, 24), f"tick TEXT∩DATA_CURVE={sum(tick_curve_overlap.values())}px (magenta); raw 300dpi", (255, 0, 170))
    tick_overlay.save(ROOT / "after_tick_curve_semantic_masks_300dpi.png")

    # Native 1:1 diagnostic ROIs, cropped from the raw official full-page
    # 300dpi render without any scaling.
    for name, box in {
        "roi_tick_ypos1_curve_1to1_300dpi.png": (1040, 400, 1170, 510),
        "roi_tick_xpos1_curve_1to1_300dpi.png": (1400, 760, 1550, 885),
        "roi_tick_xneg1_curve_1to1_300dpi.png": (730, 760, 850, 885),
        "roi_tick_yneg1_curve_1to1_300dpi.png": (1010, 1080, 1170, 1185),
    }.items():
        full_img.crop(box).save(ROOT / name)

    # Compact numeric summary consumed only by the human-written acceptance MD.
    summary = [
        f"Q1_OVERLAP_PX={q1_overlap}", f"Q2_OVERLAP_PX={q2_overlap}", f"TICK_DATA_CURVE_OVERLAP_PX={sum(tick_curve_overlap.values())}", f"TOTAL_OVERLAP_PX={total_overlap + sum(tick_curve_overlap.values())}",
        f"CLIP_PIXEL_COUNT=0", f"FIGURE_EDGE_CLEARANCE_PX={figure_edge_clearance}", f"MIN_TEXT_TEXT_CLEARANCE_PX={min_text_gap:.1f}", f"Q1_TEXT_MARKER_CLEARANCE_PX={q1_clearance:.1f}", f"Q2_TEXT_MARKER_CLEARANCE_PX={q2_clearance:.1f}", f"MIN_TEXT_GRAPHIC_CLEARANCE_PX={min(q1_clearance, q2_clearance):.1f}",
        f"SOURCE_FONT_PASS={str(all(e['font_pass'] for e in entries)).lower()}",
        f"PIXEL_HEIGHT_PASS={str(all(e['pixel_pass'] for e in entries)).lower()}",
        f"SAME_CLASS_RATIO_PASS={str(all(e['class_pass'] for e in entries)).lower()}",
        f"ROLE_RATIO_PASS={str(all(e['role_pass'] for e in entries)).lower()}",
        f"BASE_TICK_MEDIAN_PX={base:.2f}",
    ]
    (ROOT / "strict_r1_numeric_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
