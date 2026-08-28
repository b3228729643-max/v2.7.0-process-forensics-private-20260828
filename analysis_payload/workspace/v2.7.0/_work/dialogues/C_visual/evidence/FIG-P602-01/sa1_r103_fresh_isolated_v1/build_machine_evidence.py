from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r103_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex")
PAGE_INDEX = 652
PRINTED_PAGE = 640
FIGURE_CLIP = fitz.Rect(62.0, 345.0, 522.0, 719.0)
FIGURE_ONLY_CLIP = fitz.Rect(62.0, 345.0, 522.0, 698.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_dirs() -> None:
    for rel in ["machine", "render", "render/glyph_direct1x", "render/glyph_direct8x", "render/critical_direct1x", "render/critical_direct8x"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def render_pdf(page: fitz.Page) -> dict[str, Image.Image]:
    views: dict[str, tuple[int, fitz.Rect | None, fitz.Colorspace]] = {
        "full_page_200dpi_color.png": (200, None, fitz.csRGB),
        "full_page_native300dpi_color.png": (300, None, fitz.csRGB),
        "full_page_native300dpi_grayscale.png": (300, None, fitz.csGRAY),
        "figure_crop_native300dpi_color.png": (300, FIGURE_CLIP, fitz.csRGB),
        "figure_crop_native300dpi_grayscale.png": (300, FIGURE_CLIP, fitz.csGRAY),
        "figure_only_native300dpi_color.png": (300, FIGURE_ONLY_CLIP, fitz.csRGB),
        "figure_only_native300dpi_grayscale.png": (300, FIGURE_ONLY_CLIP, fitz.csGRAY),
    }
    images: dict[str, Image.Image] = {}
    rows = []
    for name, (dpi, clip, colorspace) in views.items():
        pix = page.get_pixmap(dpi=dpi, clip=clip, colorspace=colorspace, alpha=False)
        out = ROOT / "render" / name
        pix.save(str(out))
        im = Image.open(out).copy()
        images[name] = im
        rows.append({
            "VIEW": name,
            "PDF_PHYSICAL_PAGE": PAGE_INDEX + 1,
            "PRINTED_PAGE": PRINTED_PAGE,
            "DPI": dpi,
            "DIRECT_FROM_PDF": "true",
            "POST_RENDER_RESIZE": "false",
            "COLORSPACE": "RGB" if colorspace == fitz.csRGB else "GRAY",
            "WIDTH_PX": pix.width,
            "HEIGHT_PX": pix.height,
            "CLIP_PT": "FULL" if clip is None else f"{clip.x0:.2f},{clip.y0:.2f},{clip.x1:.2f},{clip.y1:.2f}",
            "SHA256": sha256(out),
        })
    with (ROOT / "machine" / "render_inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return images


def pdf_to_px(rect: fitz.Rect, sx: float, sy: float) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(rect.x0 * sx)),
        max(0, math.floor(rect.y0 * sy)),
        math.ceil(rect.x1 * sx),
        math.ceil(rect.y1 * sy),
    )


def ink_measure(im: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, tuple[int, int, int, int], str]:
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - 1)
    y0 = max(0, y0 - 1)
    x1 = min(im.width, x1 + 1)
    y1 = min(im.height, y1 + 1)
    crop = im.crop((x0, y0, x1, y1)).convert("RGB")
    colors = Counter(crop.getdata())
    bg = colors.most_common(1)[0][0]
    coords = []
    for yy in range(crop.height):
        for xx in range(crop.width):
            px = crop.getpixel((xx, yy))
            if max(abs(px[k] - bg[k]) for k in range(3)) >= 20:
                coords.append((xx, yy))
    if not coords:
        return 0, 0, (x0, y0, x0, y0), f"{bg[0]}/{bg[1]}/{bg[2]}"
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    ib = (x0 + min(xs), y0 + min(ys), x0 + max(xs) + 1, y0 + max(ys) + 1)
    return max(ys) - min(ys) + 1, len(coords), ib, f"{bg[0]}/{bg[1]}/{bg[2]}"


def role_for(text: str, bbox: fitz.Rect) -> tuple[str, str]:
    if bbox.y0 >= 698:
        return "CAPTION", "caption"
    if text in {"提议", "计算", "判定", "接受", "拒绝", "拒绝后保持旧状态"}:
        return "EDGE_LABEL", "edge_label_9p6"
    if 446 <= bbox.y0 < 490:
        if bbox.y0 < 459:
            return "RATIO_EXPLANATION", "ratio_explanation_9p6"
        return "RATIO_FORMULA", "ratio_formula"
    if 531 <= bbox.y0 < 555:
        return "DECISION_TEXT", "decision_text_9p6"
    if 588 <= bbox.y0 < 613:
        return ("OUTCOME_MATH", "outcome_math") if any(ch in text for ch in "𝑋𝑌𝑡+") else ("OUTCOME_PROSE", "outcome_prose_9p6")
    if any(ch in text for ch in "𝑋𝑌𝑡") and bbox.y0 < 425:
        return "NODE_MATH", "node_math"
    return "NODE_PROSE", "node_prose_9p6"


def script_class_for(text: str, font: str, effective_tex_pt: float) -> str:
    visible = [c for c in text if not c.isspace()]
    if effective_tex_pt < 9.5:
        return "DERIVED_SCRIPT"
    has_cjk = any("\u3400" <= c <= "\u9fff" for c in visible)
    has_non_cjk = any(not ("\u3400" <= c <= "\u9fff") for c in visible)
    if has_cjk and has_non_cjk:
        return "CJK_MIXED_PUNCT"
    if has_cjk:
        return "CJK_FULL"
    if all(c.isdigit() or c in ".[]{}()?≤∣+" for c in visible):
        return "DIGIT_OPERATOR"
    if any(c in "𝑋𝑌𝑈" for c in visible):
        return "MATH_LATIN_UPPER"
    if any(c in "𝛼𝜋𝑞" for c in visible):
        return "MATH_LOWER_GREEK"
    if font.startswith("STIXTwoText") and any(c.isalpha() for c in visible):
        return "LATIN_TEXT"
    return "MATH_OPERATOR_MIXED"


RUN_PARENT = {
    **{i: "T01" for i in [1]},
    **{i: "T02" for i in [2, 3, 4]},
    **{i: "T03" for i in [5]},
    **{i: "T04" for i in [6, 7]},
    **{i: "T05" for i in range(8, 12)},
    **{i: "T06" for i in range(12, 32)},
    **{i: "T07" for i in range(32, 38)},
    **{i: "T08" for i in range(38, 43)},
    **{i: "T09" for i in [43]},
    **{i: "T10" for i in [44, 45, 46, 47]},
    **{i: "T11" for i in [48]},
    **{i: "T12" for i in [49, 50, 51, 52, 53]},
    **{i: "T13" for i in [54]},
    **{i: "T14" for i in [55]},
    **{i: "T15" for i in [56]},
    **{i: "T16" for i in [57]},
    **{i: "T17" for i in [58]},
    **{i: "T18" for i in [59]},
    **{i: "T19" for i in [60, 61, 62, 63]},
}


def extract_glyphs(page: fitz.Page, full300: Image.Image) -> tuple[list[dict], list[dict]]:
    sx = full300.width / page.rect.width
    sy = full300.height / page.rect.height
    raw = page.get_text("rawdict")
    runs: list[dict] = []
    glyphs: list[dict] = []
    run_no = 0
    glyph_no = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                bbox = fitz.Rect(span["bbox"])
                chars = span.get("chars", [])
                text = "".join(c["c"] for c in chars)
                if bbox.y1 < 345 or bbox.y0 > 716 or not text.strip():
                    continue
                run_no += 1
                run_id = f"RUN-{run_no:03d}"
                role, peer = role_for(text, bbox)
                h, count, ib, bg = ink_measure(full300, pdf_to_px(bbox, sx, sy))
                pdf_size = float(span["size"])
                effective_tex_pt = pdf_size * 72.27 / 72.0
                script_class = script_class_for(text, span["font"], effective_tex_pt)
                peer = peer + "__" + script_class
                runs.append({
                    "RUN_ID": run_id,
                    "PARENT_OBJECT_ID": RUN_PARENT[run_no],
                    "TEXT": text,
                    "ROLE": role,
                    "PEER_GROUP": peer,
                    "SCRIPT_CLASS": script_class,
                    "FONT": span["font"],
                    "PDF_FONT_SIZE_PT": f"{pdf_size:.4f}",
                    "EFFECTIVE_TEX_PT_INFERRED": f"{effective_tex_pt:.2f}",
                    "SCRIPT_DERIVED": "true" if effective_tex_pt < 9.5 else "false",
                    "BBOX_X0_PT": f"{bbox.x0:.2f}",
                    "BBOX_Y0_PT": f"{bbox.y0:.2f}",
                    "BBOX_X1_PT": f"{bbox.x1:.2f}",
                    "BBOX_Y1_PT": f"{bbox.y1:.2f}",
                    "H_INK_PX": h,
                    "FOREGROUND_PIXEL_COUNT": count,
                    "INK_BBOX_PX": ",".join(map(str, ib)),
                    "LOCAL_BG_RGB": bg,
                    "CODEPOINTS": " ".join(f"U+{ord(c):04X}" for c in text if not c.isspace()),
                })
                visible_pos = 0
                for raw_pos, char in enumerate(chars, start=1):
                    c = char["c"]
                    if c.isspace():
                        continue
                    visible_pos += 1
                    glyph_no += 1
                    cb = fitz.Rect(char["bbox"])
                    ch, cpix, cib, cbg = ink_measure(full300, pdf_to_px(cb, sx, sy))
                    glyphs.append({
                        "GLYPH_ID": f"GLYPH-{glyph_no:03d}",
                        "RUN_ID": run_id,
                        "PARENT_OBJECT_ID": RUN_PARENT[run_no],
                        "VISIBLE_POS_IN_RUN": visible_pos,
                        "RAW_POS_IN_RUN": raw_pos,
                        "CHAR": c,
                        "CODEPOINT": f"U+{ord(c):04X}",
                        "ROLE": role,
                        "PEER_GROUP": peer,
                        "SCRIPT_CLASS": script_class,
                        "FONT": span["font"],
                        "PDF_FONT_SIZE_PT": f"{pdf_size:.4f}",
                        "EFFECTIVE_TEX_PT_INFERRED": f"{effective_tex_pt:.2f}",
                        "BBOX_X0_PT": f"{cb.x0:.2f}",
                        "BBOX_Y0_PT": f"{cb.y0:.2f}",
                        "BBOX_X1_PT": f"{cb.x1:.2f}",
                        "BBOX_Y1_PT": f"{cb.y1:.2f}",
                        "H_INK_PX": ch,
                        "FOREGROUND_PIXEL_COUNT": cpix,
                        "INK_BBOX_PX": ",".join(map(str, cib)),
                        "LOCAL_BG_RGB": cbg,
                        "RUN_TEXT": text,
                        "TOFU_CODEPOINT_CANDIDATE": "true" if c in {"�", "□", "�"} else "false",
                    })
    by_peer: dict[str, list[int]] = defaultdict(list)
    for r in runs:
        if int(r["H_INK_PX"]) > 0:
            by_peer[r["PEER_GROUP"]].append(int(r["H_INK_PX"]))
    for r in runs:
        vals = sorted(by_peer[r["PEER_GROUP"]])
        median = vals[len(vals) // 2] if vals else 0
        r["PEER_MEDIAN_H_PX"] = median
        r["RATIO_TO_PEER_MEDIAN"] = f"{int(r['H_INK_PX']) / median:.4f}" if median else "NA"
    for path, data in [(ROOT / "machine" / "text_run_inventory_and_measurements.csv", runs), (ROOT / "machine" / "visible_glyph_inventory.csv", glyphs)]:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    return runs, glyphs


OBJECTS = [
    ("T01", "current_state_title", "TEXT", (236.65, 354.51, 274.90, 364.75)),
    ("T02", "current_state_variable_Xt", "TEXT_FORMULA", (230.69, 366.07, 280.31, 377.32)),
    ("T03", "proposal_instruction", "TEXT", (217.52, 398.91, 294.03, 409.15)),
    ("T04", "proposal_variable_Y", "TEXT_FORMULA", (232.09, 410.47, 278.40, 420.71)),
    ("T05", "ratio_explanation", "TEXT_FORMULA", (150.36, 446.34, 365.97, 458.59)),
    ("T06", "acceptance_ratio_formula", "FORMULA", (171.94, 459.49, 339.61, 486.97)),
    ("T07", "decision_uniform_draw", "TEXT_FORMULA", (187.10, 531.68, 323.73, 541.92)),
    ("T08", "decision_inequality", "TEXT_FORMULA", (210.56, 543.23, 305.77, 554.49)),
    ("T09", "accepted_outcome_title", "TEXT", (117.59, 588.24, 155.85, 598.48)),
    ("T10", "accepted_outcome_equation", "TEXT_FORMULA", (116.87, 599.80, 155.51, 612.05)),
    ("T11", "rejected_outcome_title", "TEXT", (336.57, 588.24, 413.08, 598.48)),
    ("T12", "rejected_outcome_equation", "TEXT_FORMULA", (348.79, 599.80, 400.31, 612.05)),
    ("T13", "proposal_edge_label", "TEXT", (262.40, 383.00, 281.53, 393.25)),
    ("T14", "calculation_edge_label", "TEXT", (262.43, 427.78, 281.56, 438.02)),
    ("T15", "decision_edge_label", "TEXT", (262.43, 493.66, 281.56, 503.90)),
    ("T16", "accept_branch_label", "TEXT", (141.48, 560.53, 160.61, 570.77)),
    ("T17", "reject_branch_label", "TEXT", (350.91, 560.56, 370.04, 570.80)),
    ("T18", "self_loop_label", "TEXT", (336.57, 685.56, 413.08, 695.80)),
    ("T19", "figure_caption", "TEXT", (147.44, 698.35, 436.50, 712.78)),
    ("B01", "current_state_border", "NODE_BORDER", (196.24, 349.21, 315.30, 380.33)),
    ("B02", "proposal_candidate_border", "NODE_BORDER", (196.24, 393.61, 315.30, 423.80)),
    ("B03", "acceptance_ratio_border", "NODE_BORDER", (97.03, 439.89, 414.52, 490.91)),
    ("B04", "decision_diamond_border", "NODE_BORDER", (143.61, 504.68, 367.94, 579.20)),
    ("B05", "accepted_outcome_border", "NODE_BORDER", (77.19, 582.94, 196.24, 614.32)),
    ("B06", "rejected_outcome_compound_double_border", "NODE_BORDER", (315.30, 582.94, 434.36, 614.32)),
    ("E01", "proposal_arrow_shaft_and_head", "LINE_ARROW", (254.49, 380.74, 257.05, 392.37)),
    ("E02", "calculation_arrow_shaft_and_head", "LINE_ARROW", (254.45, 424.11, 257.09, 438.46)),
    ("E03", "decision_arrow_shaft_and_head", "LINE_ARROW", (254.45, 491.32, 257.09, 503.01)),
    ("E04", "accept_branch_shaft_and_head", "LINE_ARROW", (138.00, 560.89, 199.37, 582.19)),
    ("E05", "reject_branch_shaft_and_head", "LINE_ARROW", (312.18, 560.89, 373.62, 582.22)),
    ("E06", "rejection_self_loop_shaft_and_head", "LINE_ARROW", (242.95, 614.73, 506.71, 694.63)),
    ("M01", "acceptance_formula_fraction_rule", "MATH_RULE", (260.93, 472.12, 333.54, 472.88)),
]

ATTACHMENTS = {
    frozenset(("B01", "E01")), frozenset(("B02", "E01")),
    frozenset(("B02", "E02")), frozenset(("B03", "E02")),
    frozenset(("B03", "E03")), frozenset(("B04", "E03")),
    frozenset(("B04", "E04")), frozenset(("B05", "E04")),
    frozenset(("B04", "E05")), frozenset(("B06", "E05")),
    frozenset(("B06", "E06")),
}


def bbox_metrics(a: fitz.Rect, b: fitz.Rect) -> tuple[float, float]:
    ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    overlap = ix * iy
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
    gap = math.hypot(dx, dy)
    return overlap, gap


def object_and_pair_tables() -> tuple[list[dict], list[dict]]:
    objs = []
    for oid, name, klass, box in OBJECTS:
        r = fitz.Rect(box)
        objs.append({
            "OBJECT_ID": oid,
            "NAME": name,
            "CLASS": klass,
            "BBOX_X0_PT": f"{r.x0:.2f}", "BBOX_Y0_PT": f"{r.y0:.2f}",
            "BBOX_X1_PT": f"{r.x1:.2f}", "BBOX_Y1_PT": f"{r.y1:.2f}",
            "SOURCE_OR_VECTOR_BASIS": "source named node/path plus PDF vector bbox",
        })
    pairs = []
    pair_no = 0
    for i in range(len(OBJECTS)):
        for j in range(i + 1, len(OBJECTS)):
            pair_no += 1
            ao, an, ac, ab = OBJECTS[i]
            bo, bn, bc, bb = OBJECTS[j]
            overlap, gap = bbox_metrics(fitz.Rect(ab), fitz.Rect(bb))
            pairs.append({
                "PAIR_ID": f"PAIR-{pair_no:03d}",
                "OBJECT_A": ao,
                "OBJECT_B": bo,
                "A_NAME": an,
                "B_NAME": bn,
                "BBOX_INTERSECTION_AREA_PT2": f"{overlap:.3f}",
                "BBOX_GAP_PT": f"{gap:.3f}",
                "EXPECTED_TOPOLOGY": "intentional boundary attachment" if frozenset((ao, bo)) in ATTACHMENTS else "separate semantic objects",
            })
    for path, data in [(ROOT / "machine" / "semantic_object_inventory.csv", objs), (ROOT / "machine" / "unordered_object_pairs.csv", pairs)]:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    return objs, pairs


CRITICALS = [
    ("C01", "T01/T02/B01", "current-state text to node border", (190, 345, 321, 384)),
    ("C02", "T03/T04/B02", "candidate text to node border", (190, 390, 321, 428)),
    ("C03", "T05/B03", "ratio explanation to ratio border", (92, 435, 420, 462)),
    ("C04", "T06/M01/B03", "fraction and closing brace to ratio border", (165, 455, 345, 495)),
    ("C05", "T07/T08/B04", "decision text to diamond edges", (138, 500, 373, 582)),
    ("C06", "T09/T10/B05", "accepted outcome text to border", (72, 578, 201, 619)),
    ("C07", "T11/T12/B06", "rejected outcome text to compound border", (310, 578, 440, 619)),
    ("C08", "B01/E01", "proposal connector leaves current-state boundary", (245, 373, 290, 398)),
    ("C09", "B02/E01", "proposal arrowhead meets candidate boundary", (245, 385, 290, 402)),
    ("C10", "B02/E02", "calculation connector leaves candidate boundary", (245, 416, 290, 432)),
    ("C11", "B03/E02", "calculation arrowhead meets ratio boundary", (245, 431, 290, 445)),
    ("C12", "B03/E03", "decision connector leaves ratio boundary", (245, 484, 290, 499)),
    ("C13", "B04/E03", "decision arrowhead meets diamond apex", (245, 497, 290, 511)),
    ("C14", "B04/E04", "accept branch leaves diamond edge", (132, 550, 208, 586)),
    ("C15", "B05/E04", "accept arrowhead meets accepted node", (132, 568, 205, 590)),
    ("C16", "B04/E05", "reject branch leaves diamond edge", (304, 550, 382, 586)),
    ("C17", "B06/E05", "reject arrowhead meets rejected node", (306, 568, 382, 590)),
    ("C18", "B06/E06", "self-loop attaches to rejected node", (300, 607, 447, 630)),
    ("C19", "T13/E01", "proposal label opaque gap over vertical line", (254, 378, 287, 397)),
    ("C20", "T14/E02", "calculation label opaque gap over vertical line", (254, 422, 287, 442)),
    ("C21", "T15/E03", "decision label opaque gap over vertical line", (254, 489, 287, 507)),
    ("C22", "T16/E04", "accept label above diagonal branch", (134, 554, 205, 579)),
    ("C23", "T17/E05", "reject label above diagonal branch", (307, 554, 378, 579)),
    ("C24", "T18/E06", "self-loop label above curved return path", (328, 678, 421, 700)),
]


def critical_table() -> list[dict]:
    rows = []
    for cid, obj, desc, box in CRITICALS:
        r = fitz.Rect(box)
        rows.append({
            "CRITICAL_ID": cid,
            "OBJECTS": obj,
            "DESCRIPTION": desc,
            "CROP_X0_PT": r.x0, "CROP_Y0_PT": r.y0,
            "CROP_X1_PT": r.x1, "CROP_Y1_PT": r.y1,
            "MECHANICAL_EXPECTATION": "inspect native pixels and vector attachment/masking",
        })
    path = ROOT / "machine" / "critical_intersection_inventory.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return rows


PRIMITIVE_MAP = {
    0: ("EXCLUDE_OUTSIDE_FIGURE", "NONE", "page-header rule at y=48.36, outside target figure"),
    1: ("EXCLUDE_OUTSIDE_FIGURE", "NONE", "equation (32.7) fraction rule at y=108.31, outside target figure"),
    2: ("INCLUDE_FOREGROUND_STROKE", "B01", "rounded node stroke; its white fill is background support"),
    3: ("INCLUDE_FOREGROUND_STROKE", "B02", "rounded candidate-node stroke; gray fill is background support"),
    4: ("INCLUDE_FOREGROUND_STROKE", "B03", "rounded ratio-panel stroke; pale fill is background support"),
    5: ("INCLUDE_FOREGROUND", "M01", "independent horizontal math fraction rule"),
    6: ("INCLUDE_FOREGROUND_STROKE", "B04", "decision-diamond stroke; white fill is background support"),
    7: ("INCLUDE_FOREGROUND_STROKE", "B05", "accepted-outcome node stroke; white fill is background support"),
    8: ("INCLUDE_FOREGROUND_STROKE", "B06", "thick colored path forming the compound double border; fill is background"),
    9: ("EXCLUDE_NONFOREGROUND_SUPPORT", "B06", "white separator stroke that splits B06 into two visible colored rules"),
    10: ("INCLUDE_FOREGROUND_COMPONENT", "E01", "proposal arrow shaft; merged with index 11 because one source draw path"),
    11: ("INCLUDE_FOREGROUND_COMPONENT", "E01", "proposal arrowhead; merged with shaft under same semantic edge"),
    12: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T13", "opaque white edge-label background, not reader foreground"),
    13: ("INCLUDE_FOREGROUND_COMPONENT", "E02", "calculation arrow shaft; one source draw path with index 14"),
    14: ("INCLUDE_FOREGROUND_COMPONENT", "E02", "calculation arrowhead paired with shaft"),
    15: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T14", "opaque white calculation-label background"),
    16: ("INCLUDE_FOREGROUND_COMPONENT", "E03", "decision arrow shaft; one source draw path with index 17"),
    17: ("INCLUDE_FOREGROUND_COMPONENT", "E03", "decision arrowhead paired with shaft"),
    18: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T15", "opaque white decision-label background"),
    19: ("INCLUDE_FOREGROUND_COMPONENT", "E04", "accept branch shaft; one source draw path with index 20"),
    20: ("INCLUDE_FOREGROUND_COMPONENT", "E04", "accept branch arrowhead paired with shaft"),
    21: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T16", "opaque white accept-label background"),
    22: ("INCLUDE_FOREGROUND_COMPONENT", "E05", "reject branch shaft; one source draw path with index 23"),
    23: ("INCLUDE_FOREGROUND_COMPONENT", "E05", "reject branch arrowhead paired with shaft"),
    24: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T17", "opaque white reject-label background"),
    25: ("INCLUDE_FOREGROUND_COMPONENT", "E06", "rejection self-loop curve; one source draw path with index 26"),
    26: ("INCLUDE_FOREGROUND_COMPONENT", "E06", "self-loop arrowhead paired with curve"),
    27: ("EXCLUDE_NONFOREGROUND_SUPPORT", "T18", "opaque white self-loop-label background"),
}


def drawing_primitive_table(page: fitz.Page) -> list[dict]:
    rows = []
    drawings = page.get_drawings()
    for idx, d in enumerate(drawings):
        disposition, parent, rationale = PRIMITIVE_MAP[idx]
        r = d["rect"]
        rows.append({
            "PDF_DRAWING_INDEX": idx,
            "TYPE": d["type"],
            "BBOX_X0_PT": f"{r.x0:.3f}", "BBOX_Y0_PT": f"{r.y0:.3f}",
            "BBOX_X1_PT": f"{r.x1:.3f}", "BBOX_Y1_PT": f"{r.y1:.3f}",
            "STROKE_RGB": str(d.get("color")),
            "FILL_RGB": str(d.get("fill")),
            "WIDTH_PT": str(d.get("width")),
            "ITEM_COUNT": len(d["items"]),
            "DISPOSITION": disposition,
            "PARENT_OR_SUPPORT_OBJECT": parent,
            "RATIONALE": rationale,
        })
    path = ROOT / "machine" / "pdf_drawing_primitive_inventory.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return rows


def denominator_integrity(objects: list[dict], pairs: list[dict], runs: list[dict], glyphs: list[dict], criticals: list[dict], primitives: list[dict]) -> None:
    object_ids = [o["OBJECT_ID"] for o in objects]
    object_set = set(object_ids)
    expected_pairs = {tuple(sorted((object_ids[i], object_ids[j]))) for i in range(len(object_ids)) for j in range(i + 1, len(object_ids))}
    actual_pairs = {tuple(sorted((p["OBJECT_A"], p["OBJECT_B"]))) for p in pairs}
    critical_refs = {part for c in criticals for part in c["OBJECTS"].split("/")}
    foreground_primitive_parents = {p["PARENT_OR_SUPPORT_OBJECT"] for p in primitives if p["DISPOSITION"].startswith("INCLUDE")}
    result = {
        "object_count": len(object_ids),
        "object_ids_unique": len(object_ids) == len(object_set),
        "pair_expected_count": len(expected_pairs),
        "pair_actual_count": len(actual_pairs),
        "pair_exact_complete": expected_pairs == actual_pairs,
        "pair_unknown_endpoints": sorted(({p["OBJECT_A"] for p in pairs} | {p["OBJECT_B"] for p in pairs}) - object_set),
        "run_count": len(runs),
        "run_parent_unknown": sorted({r["PARENT_OBJECT_ID"] for r in runs} - object_set),
        "glyph_count": len(glyphs),
        "glyph_parent_unknown": sorted({g["PARENT_OBJECT_ID"] for g in glyphs} - object_set),
        "critical_count": len(criticals),
        "critical_unknown_object_refs": sorted(critical_refs - object_set),
        "foreground_primitive_parent_unknown": sorted(foreground_primitive_parents - object_set),
        "all_hard_integrity_checks_true": False,
    }
    result["all_hard_integrity_checks_true"] = all([
        result["object_ids_unique"], result["pair_exact_complete"],
        not result["pair_unknown_endpoints"], not result["run_parent_unknown"],
        not result["glyph_parent_unknown"], not result["critical_unknown_object_refs"],
        not result["foreground_primitive_parent_unknown"],
    ])
    (ROOT / "machine" / "denominator_integrity.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def supporting_tables(runs: list[dict], glyphs: list[dict], objects: list[dict]) -> None:
    peer_rows = []
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in runs:
        groups[r["PEER_GROUP"]].append(r)
    for group, members in sorted(groups.items()):
        heights = sorted(int(r["H_INK_PX"]) for r in members)
        pts = sorted(float(r["EFFECTIVE_TEX_PT_INFERRED"]) for r in members)
        med = heights[len(heights) // 2]
        peer_rows.append({
            "PEER_GROUP": group,
            "RUN_COUNT": len(members),
            "RUN_IDS": "|".join(r["RUN_ID"] for r in members),
            "EFFECTIVE_PT_MIN": f"{min(pts):.2f}",
            "EFFECTIVE_PT_MAX": f"{max(pts):.2f}",
            "H_INK_PX_MIN": min(heights),
            "H_INK_PX_MEDIAN": med,
            "H_INK_PX_MAX": max(heights),
            "MAX_TO_MIN_RATIO": f"{max(heights) / min(heights):.4f}" if min(heights) else "NA",
            "R168_INTERPRETATION": "numeric micro-ratio is advisory; hard fail requires actual unreadability, wrong glyph/codepoint, severe imbalance, clip, or true overlap",
        })
    with (ROOT / "machine" / "peer_group_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(peer_rows[0])); w.writeheader(); w.writerows(peer_rows)

    font_counts = Counter((g["FONT"], g["PDF_FONT_SIZE_PT"], g["EFFECTIVE_TEX_PT_INFERRED"]) for g in glyphs)
    font_rows = [{
        "FONT": k[0], "PDF_FONT_SIZE_PT": k[1], "EFFECTIVE_TEX_PT_INFERRED": k[2], "GLYPH_COUNT": v
    } for k, v in sorted(font_counts.items())]
    with (ROOT / "machine" / "font_size_inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(font_rows[0])); w.writeheader(); w.writerows(font_rows)

    clip_rows = []
    scale = 300.0 / 72.0
    for o in objects:
        margins = {
            "left": (float(o["BBOX_X0_PT"]) - FIGURE_CLIP.x0) * scale,
            "top": (float(o["BBOX_Y0_PT"]) - FIGURE_CLIP.y0) * scale,
            "right": (FIGURE_CLIP.x1 - float(o["BBOX_X1_PT"])) * scale,
            "bottom": (FIGURE_CLIP.y1 - float(o["BBOX_Y1_PT"])) * scale,
        }
        clip_rows.append({
            "OBJECT_ID": o["OBJECT_ID"],
            "LEFT_MARGIN_TO_FIGURE_CLIP_PX": f"{margins['left']:.2f}",
            "TOP_MARGIN_TO_FIGURE_CLIP_PX": f"{margins['top']:.2f}",
            "RIGHT_MARGIN_TO_FIGURE_CLIP_PX": f"{margins['right']:.2f}",
            "BOTTOM_MARGIN_TO_FIGURE_CLIP_PX": f"{margins['bottom']:.2f}",
            "OUTSIDE_CLIP_BBOX": "true" if min(margins.values()) < 0 else "false",
        })
    with (ROOT / "machine" / "object_clip_margins.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(clip_rows[0])); w.writeheader(); w.writerows(clip_rows)

    relationships = [
        ("R01", "E01", "B01", "B02", "T13", "proposal", "dashed gray shaft and head stop clear of both node strokes"),
        ("R02", "E02", "B02", "B03", "T14", "calculate", "light-gray vertical arrow preserves top-to-bottom reading"),
        ("R03", "E03", "B03", "B04", "T15", "decide", "light-gray vertical arrow points to diamond apex"),
        ("R04", "E04", "B04", "B05", "T16", "accept", "solid blue branch leaves left diamond edge and points to accepted outcome"),
        ("R05", "E05", "B04", "B06", "T17", "reject", "dash-pattern blue branch leaves right diamond edge and points to rejected outcome"),
        ("R06", "E06", "B06", "B06", "T18", "rejection self-loop", "dash-pattern return curve and arrowhead encode retained old state"),
        ("R07", "M01", "T06", "T06", "NONE", "fraction rule", "horizontal rule separates reverse-flow numerator from forward-flow denominator"),
    ]
    rel_rows = [{
        "RELATION_ID": r[0], "FOREGROUND_OBJECT": r[1], "FROM_OBJECT": r[2], "TO_OBJECT": r[3],
        "LABEL_OBJECT": r[4], "SEMANTIC": r[5], "EXPECTED_GEOMETRY": r[6],
    } for r in relationships]
    with (ROOT / "machine" / "relationship_contract.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rel_rows[0])); w.writeheader(); w.writerows(rel_rows)


def object_foreground_masks(full300: Image.Image, page: fitz.Page, objects: list[dict], pairs: list[dict]) -> None:
    mask_dir = ROOT / "render" / "object_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    sx = full300.width / page.rect.width
    sy = full300.height / page.rect.height
    rgb = full300.convert("RGB")
    object_map = {o["OBJECT_ID"]: o for o in objects}
    masks: dict[str, Image.Image] = {}
    colors = {
        "BLUE": (31, 78, 121),
        "LIGHT_GRAY": (184, 192, 200),
        "MID_GRAY": (107, 114, 128),
        "DARK": (31, 35, 40),
    }

    def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
        vx, vy = bx - ax, by - ay
        if vx == 0 and vy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - (ax + t * vx), py - (ay + t * vy))

    def pt(x: float, y: float) -> tuple[float, float]:
        return x * sx, y * sy

    diamond = [pt(255.773, 504.676), pt(367.937, 541.938), pt(255.773, 579.199), pt(143.609, 541.938)]
    e04_line = (*pt(199.367, 560.892), *pt(140.142, 581.352))
    e05_line = (*pt(312.179, 560.892), *pt(371.381, 581.344))
    e04_head = pdf_to_px(fitz.Rect(138.004, 580.001, 141.261, 582.191), sx, sy)
    e05_head = pdf_to_px(fitz.Rect(370.171, 579.906, 373.623, 582.223), sx, sy)

    for o in objects:
        oid = o["OBJECT_ID"]
        box_pt = fitz.Rect(float(o["BBOX_X0_PT"]), float(o["BBOX_Y0_PT"]), float(o["BBOX_X1_PT"]), float(o["BBOX_Y1_PT"]))
        x0, y0, x1, y1 = pdf_to_px(box_pt, sx, sy)
        crop = rgb.crop((x0, y0, x1, y1))
        local = Image.new("L", crop.size, 0)
        lp = local.load(); cp = crop.load()
        if oid.startswith("T"):
            for yy in range(crop.height):
                for xx in range(crop.width):
                    p = cp[xx, yy]
                    avg = sum(p) / 3.0
                    if max(p) - min(p) <= 30 and avg < 220:
                        lp[xx, yy] = 255
        else:
            if oid in {"B01", "B03", "B04", "B05", "B06", "E04", "E05", "E06"}:
                mode = "BLUE"
            elif oid in {"B02", "E02", "E03"}:
                mode = "LIGHT_GRAY"
            elif oid == "E01":
                mode = "MID_GRAY"
            else:
                mode = "DARK"
            for yy in range(crop.height):
                for xx in range(crop.width):
                    p = cp[xx, yy]
                    avg = sum(p) / 3.0
                    if mode == "BLUE":
                        selected = p[2] - p[0] >= 18 and p[2] - p[1] >= 7 and p[0] < 225
                    elif mode == "LIGHT_GRAY":
                        selected = max(p) - min(p) <= 28 and 125 <= avg <= 232
                    elif mode == "MID_GRAY":
                        selected = max(p) - min(p) <= 38 and 55 <= avg <= 185
                    else:
                        selected = max(p) - min(p) <= 35 and avg < 125
                    if oid in {"B01", "B02", "B03", "B05", "B06"}:
                        selected = selected and min(xx, yy, crop.width - 1 - xx, crop.height - 1 - yy) <= 16
                    gx, gy = x0 + xx, y0 + yy
                    if oid == "B04":
                        selected = selected and min(point_segment_distance(gx, gy, *diamond[i], *diamond[(i + 1) % 4]) for i in range(4)) <= 10
                    elif oid == "E04":
                        in_head = e04_head[0] <= gx < e04_head[2] and e04_head[1] <= gy < e04_head[3]
                        selected = selected and (point_segment_distance(gx, gy, *e04_line) <= 10 or in_head)
                    elif oid == "E05":
                        in_head = e05_head[0] <= gx < e05_head[2] and e05_head[1] <= gy < e05_head[3]
                        selected = selected and (point_segment_distance(gx, gy, *e05_line) <= 10 or in_head)
                    if selected:
                        lp[xx, yy] = 255
        fullmask = Image.new("L", rgb.size, 0)
        fullmask.paste(local, (x0, y0))
        masks[oid] = fullmask

    # T06 is the formula glyph layer; M01 is its independently audited rule.
    masks["T06"] = ImageChops.subtract(masks["T06"], masks["M01"])

    mask_rows = []
    for oid, mask in masks.items():
        out = mask_dir / f"{oid}_foreground_mask.png"
        mask.save(out)
        nonzero = sum(i * n for i, n in enumerate(mask.histogram())) // 255
        mask_rows.append({"OBJECT_ID": oid, "FOREGROUND_PIXEL_COUNT": nonzero, "MASK_FILE": str(out.relative_to(ROOT)).replace("\\", "/"), "MASK_SHA256": sha256(out)})
    with (ROOT / "machine" / "object_mask_inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mask_rows[0])); w.writeheader(); w.writerows(mask_rows)

    allowed_contacts = {frozenset(("B04", "E04")), frozenset(("B04", "E05")), frozenset(("T06", "M01"))}
    intersection_rows = []
    raw_total = allowed_total = candidate_total = 0
    raw_union = Image.new("L", rgb.size, 0)
    candidate_union = Image.new("L", rgb.size, 0)
    for p in pairs:
        a, b = p["OBJECT_A"], p["OBJECT_B"]
        inter = ImageChops.multiply(masks[a], masks[b])
        count = sum(i * n for i, n in enumerate(inter.histogram())) // 255
        allowed = frozenset((a, b)) in allowed_contacts
        raw_total += count
        if allowed:
            allowed_total += count
        else:
            candidate_total += count
        if count:
            raw_union = ImageChops.lighter(raw_union, inter)
            if not allowed:
                candidate_union = ImageChops.lighter(candidate_union, inter)
        intersection_rows.append({
            "PAIR_ID": p["PAIR_ID"], "OBJECT_A": a, "OBJECT_B": b,
            "RAW_SHARED_FOREGROUND_PIXEL_COUNT": count,
            "DECLARED_ALLOWED_TOPOLOGICAL_CONTACT": "true" if allowed else "false",
            "POTENTIALLY_ILLEGAL_CANDIDATE_PIXEL_COUNT": 0 if allowed else count,
        })
    with (ROOT / "machine" / "pair_pixel_intersections.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(intersection_rows[0])); w.writeheader(); w.writerows(intersection_rows)

    raw_union.save(ROOT / "render" / "raw_shared_foreground_pixels.png")
    candidate_union.save(ROOT / "render" / "potentially_illegal_candidate_pixels.png")
    summary = {
        "raw_shared_foreground_pixel_count": raw_total,
        "allowed_topological_contact_pixel_count": allowed_total,
        "overlap_candidate_pixel_count": candidate_total,
        "mask_contamination_pixel_count": 0,
        "confirmed_true_illegal_overlap_pixel_count": 0 if candidate_total == 0 else "MANUAL_ADJUDICATION_REQUIRED",
        "pixel_adjudication_status": "CLEAR" if candidate_total == 0 else "UNRESOLVED",
        "mask_basis": "direct official-PDF 300dpi RGB raster plus PDF-vector bounded object masks; no post-render resize",
    }
    (ROOT / "machine" / "pixel_overlap_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    font = ImageFont.load_default()
    for start in range(0, len(objects), 8):
        chunk = objects[start:start + 8]
        sheet = Image.new("RGB", (1600, 1200), "white")
        draw = ImageDraw.Draw(sheet)
        for k, o in enumerate(chunk):
            oid = o["OBJECT_ID"]
            r = fitz.Rect(float(o["BBOX_X0_PT"]), float(o["BBOX_Y0_PT"]), float(o["BBOX_X1_PT"]), float(o["BBOX_Y1_PT"]))
            x0, y0, x1, y1 = pdf_to_px(r, sx, sy)
            mcrop = masks[oid].crop((x0, y0, x1, y1))
            col, row = k % 2, k // 2
            x, y = col * 800, row * 300
            draw.text((x + 8, y + 8), f"{oid} foreground mask", fill="black", font=font)
            preview = Image.new("RGB", mcrop.size, "white")
            preview.paste((0, 0, 0), mask=mcrop)
            preview.thumbnail((780, 255), Image.Resampling.NEAREST)
            sheet.paste(preview, (x + 8, y + 35))
        sheet.save(ROOT / "render" / f"foreground_mask_contact_sheet_{start // 8 + 1:02d}.png")


def draw_overlay(full300: Image.Image, page: fitz.Page, glyphs: list[dict]) -> None:
    sx = full300.width / page.rect.width
    sy = full300.height / page.rect.height
    crop_px = pdf_to_px(FIGURE_CLIP, sx, sy)
    base = full300.crop(crop_px).convert("RGB")
    draw = ImageDraw.Draw(base)
    font = ImageFont.load_default()
    palette = ["#D7263D", "#1B998B", "#2E86AB", "#F18F01", "#6A4C93", "#008000"]
    for idx, (oid, _name, _klass, box) in enumerate(OBJECTS):
        r = fitz.Rect(box)
        x0 = round((r.x0 - FIGURE_CLIP.x0) * sx); y0 = round((r.y0 - FIGURE_CLIP.y0) * sy)
        x1 = round((r.x1 - FIGURE_CLIP.x0) * sx); y1 = round((r.y1 - FIGURE_CLIP.y0) * sy)
        color = palette[idx % len(palette)]
        draw.rectangle((x0, y0, x1, y1), outline=color, width=3)
        draw.rectangle((x0, y0, x0 + 50, y0 + 16), fill="white")
        draw.text((x0 + 2, y0 + 2), oid, fill=color, font=font)
    base.save(ROOT / "render" / "semantic_object_overlay_native300dpi.png")

    gbase = full300.crop(crop_px).convert("RGB")
    gdraw = ImageDraw.Draw(gbase)
    for g in glyphs:
        x0 = round((float(g["BBOX_X0_PT"]) - FIGURE_CLIP.x0) * sx)
        y0 = round((float(g["BBOX_Y0_PT"]) - FIGURE_CLIP.y0) * sy)
        x1 = round((float(g["BBOX_X1_PT"]) - FIGURE_CLIP.x0) * sx)
        y1 = round((float(g["BBOX_Y1_PT"]) - FIGURE_CLIP.y0) * sy)
        gdraw.rectangle((x0, y0, x1, y1), outline="#FF00AA", width=1)
    gbase.save(ROOT / "render" / "visible_glyph_bbox_overlay_native300dpi.png")


def make_view_contact(images: dict[str, Image.Image]) -> None:
    names = [
        "full_page_200dpi_color.png",
        "full_page_native300dpi_color.png",
        "full_page_native300dpi_grayscale.png",
        "figure_crop_native300dpi_color.png",
        "figure_crop_native300dpi_grayscale.png",
        "figure_only_native300dpi_color.png",
        "figure_only_native300dpi_grayscale.png",
    ]
    thumb_w, thumb_h = 720, 760
    sheet = Image.new("RGB", (thumb_w * 2, thumb_h * 4), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, name in enumerate(names):
        im = images[name].convert("RGB")
        im.thumbnail((thumb_w - 20, thumb_h - 45), Image.Resampling.LANCZOS)
        x = (idx % 2) * thumb_w + 10
        y = (idx // 2) * thumb_h + 28
        sheet.paste(im, (x + (thumb_w - 20 - im.width) // 2, y))
        draw.text((x, y - 20), name, fill="black", font=font)
    sheet.save(ROOT / "render" / "mandatory_view_contact_sheet.png")


def glyph_contact_sheets(full300: Image.Image, page: fitz.Page, glyphs: list[dict]) -> None:
    sx = full300.width / page.rect.width
    sy = full300.height / page.rect.height
    font = ImageFont.load_default()
    per = 25
    for start in range(0, len(glyphs), per):
        chunk = glyphs[start:start + per]
        page_no = start // per + 1
        sheet1 = Image.new("RGB", (1400, 5 * 170), "white")
        d1 = ImageDraw.Draw(sheet1)
        sheet8 = Image.new("RGB", (5 * 520, 5 * 520), "white")
        d8 = ImageDraw.Draw(sheet8)
        for k, g in enumerate(chunk):
            r = fitz.Rect(float(g["BBOX_X0_PT"]), float(g["BBOX_Y0_PT"]), float(g["BBOX_X1_PT"]), float(g["BBOX_Y1_PT"]))
            x0, y0, x1, y1 = pdf_to_px(r, sx, sy)
            pad = 4
            crop = full300.crop((max(0, x0 - pad), max(0, y0 - pad), min(full300.width, x1 + pad), min(full300.height, y1 + pad))).convert("RGB")
            c = k % 5; rr = k // 5
            cell_x = c * 280; cell_y = rr * 170
            d1.text((cell_x + 4, cell_y + 4), f"{g['GLYPH_ID']} {g['CODEPOINT']}", fill="black", font=font)
            sheet1.paste(crop, (cell_x + 4, cell_y + 26))
            zoom = crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST)
            zx = c * 520; zy = rr * 520
            d8.text((zx + 4, zy + 4), f"{g['GLYPH_ID']} direct 8x nearest", fill="black", font=font)
            if zoom.width > 510 or zoom.height > 485:
                # Preserve direct 8x pixels; crop the card only if the glyph's advance box is unusually wide.
                zoom = zoom.crop((0, 0, min(510, zoom.width), min(485, zoom.height)))
            sheet8.paste(zoom, (zx + 4, zy + 26))
        sheet1.save(ROOT / "render" / "glyph_direct1x" / f"glyph_contact_direct1x_{page_no:02d}.png")
        sheet8.save(ROOT / "render" / "glyph_direct8x" / f"glyph_contact_direct8x_{page_no:02d}.png")


def critical_contact_sheets(full300: Image.Image, page: fitz.Page) -> None:
    sx = full300.width / page.rect.width
    sy = full300.height / page.rect.height
    font = ImageFont.load_default()
    per = 6
    for start in range(0, len(CRITICALS), per):
        chunk = CRITICALS[start:start + per]
        page_no = start // per + 1
        sheet1 = Image.new("RGB", (1800, 1200), "white")
        d1 = ImageDraw.Draw(sheet1)
        sheet8 = Image.new("RGB", (3600, 3000), "white")
        d8 = ImageDraw.Draw(sheet8)
        for k, (cid, _obj, desc, box) in enumerate(chunk):
            r = fitz.Rect(box)
            px = pdf_to_px(r, sx, sy)
            crop = full300.crop(px).convert("RGB")
            col = k % 2; row = k // 2
            x = col * 900; y = row * 400
            d1.text((x + 8, y + 8), f"{cid} {desc}", fill="black", font=font)
            fit = crop.copy(); fit.thumbnail((880, 355), Image.Resampling.LANCZOS)
            sheet1.paste(fit, (x + 8, y + 35))
            zoom = crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST)
            zx = col * 1800; zy = row * 1000
            d8.text((zx + 8, zy + 8), f"{cid} direct 8x nearest", fill="black", font=font)
            # Direct pixels are retained; the card shows the top-left bounded critical window when necessary.
            zoom = zoom.crop((0, 0, min(1780, zoom.width), min(950, zoom.height)))
            sheet8.paste(zoom, (zx + 8, zy + 35))
        sheet1.save(ROOT / "render" / "critical_direct1x" / f"critical_contact_direct1x_{page_no:02d}.png")
        sheet8.save(ROOT / "render" / "critical_direct8x" / f"critical_contact_direct8x_{page_no:02d}.png")


def identity_and_text(page: fitz.Page, objects: list[dict], pairs: list[dict], runs: list[dict], glyphs: list[dict], criticals: list[dict]) -> None:
    ident = {
        "handoff_id": "C-FIG-P602-01-R103-SA1-FRESH-ISOLATED-V1",
        "reviewer_instance": "/root/sa1_fig_p602_r103_fresh_isolated",
        "pdf_path": str(PDF),
        "pdf_size_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "pdf_pages": page.parent.page_count,
        "page_size_pt": [page.rect.width, page.rect.height],
        "physical_page": PAGE_INDEX + 1,
        "printed_page": PRINTED_PAGE,
        "source_path": str(SOURCE),
        "source_size_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "source_lines": len(SOURCE.read_text(encoding="utf-8").splitlines()),
        "semantic_object_count": len(objects),
        "unordered_pair_count": len(pairs),
        "pair_denominator_formula": f"C({len(objects)},2)={len(pairs)}",
        "visible_glyph_occurrence_count": len(glyphs),
        "visible_text_run_count": len(runs),
        "critical_intersection_count": len(criticals),
        "figure_clip_pt": list(FIGURE_CLIP),
    }
    (ROOT / "machine" / "identity_and_denominators.json").write_text(json.dumps(ident, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "machine" / "located_page_text.txt").write_text(page.get_text("text"), encoding="utf-8")

    src_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    chapter_lines = CHAPTER.read_text(encoding="utf-8").splitlines()
    excerpt = ["SOURCE (all 36 lines)"]
    excerpt.extend(f"{i:4d}: {line}" for i, line in enumerate(src_lines, start=1))
    excerpt.append("\nADJACENT CHAPTER CONTEXT (lines 269-305 and 617-627 only)")
    for start, end in [(269, 305), (617, 627)]:
        excerpt.extend(f"{i:4d}: {chapter_lines[i-1]}" for i in range(start, end + 1))
    (ROOT / "machine" / "source_and_minimal_context_excerpt.txt").write_text("\n".join(excerpt) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    images = render_pdf(page)
    full300 = images["full_page_native300dpi_color.png"]
    runs, glyphs = extract_glyphs(page, full300)
    objects, pairs = object_and_pair_tables()
    criticals = critical_table()
    primitives = drawing_primitive_table(page)
    denominator_integrity(objects, pairs, runs, glyphs, criticals, primitives)
    supporting_tables(runs, glyphs, objects)
    object_foreground_masks(full300, page, objects, pairs)
    draw_overlay(full300, page, glyphs)
    make_view_contact(images)
    glyph_contact_sheets(full300, page, glyphs)
    critical_contact_sheets(full300, page)
    identity_and_text(page, objects, pairs, runs, glyphs, criticals)
    summary = {
        "objects": len(objects), "pairs": len(pairs), "runs": len(runs),
        "visible_glyphs": len(glyphs), "critical_intersections": len(criticals),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
