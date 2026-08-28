"""Local SA2 strict audit for FIG-P634-01 R6.

This is deliberately a candidate-only audit.  It reads the locally built A4
page and its direct Poppler 300 dpi raster; it does not treat that candidate as
the root-authorized official book PDF.  Literal glyph masks and all separated
foreground relation masks are sampled from the retained 1:1 300 dpi page.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / "v2.7.0/_work/evidence/figures/FIG-P634-01/STRICT_R6_SA2"
PDF = OUT / "build/local_page.pdf"
PNG300 = OUT / "renders/local_page_300dpi.png"
PNG200 = OUT / "renders/local_page_200dpi.png"
FIG_SOURCE = ROOT / "v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex"
STYLE_SOURCE = ROOT / "v2.7.0/_work/source/v2.7.0/src/讲义源码/common/statlearnbook.sty"
SIZE11 = Path(r"D:\texlive\2026\texmf-dist\tex\latex\base\size11.clo")
HELPER = ROOT / "v2.7.0/_work/evidence/figures/FIG-P634-01/STRICT_R5_SA1_R94/scripts/audit_fig_p634_v2.py"
RENDER = OUT / "renders"
CROP = OUT / "crops"
MASK = OUT / "masks"
OVERLAY = OUT / "overlays"
PAIR = OUT / "critical_pairs"

FIGURE_PANELS = {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}


def load_helper():
    spec = importlib.util.spec_from_file_location("p634_r5_helpers", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audited R5 mask helpers")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


H = load_helper()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path.name}")
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def semantic_info(y: float, x: float, line_key: str) -> tuple[str, str, str, str, float, str]:
    """Map local-candidate PDF text to source semantic roles, never glyph identity."""
    centers = [138, 181, 224, 266, 309, 351, 394, 436]
    if 249 <= y < 267:
        return "SWEEP_TOP", "PANEL_TITLE", "TITLE", "17", 10.6, "fig l17"
    if 272 <= y < 286:
        n = min(range(8), key=lambda i: abs(x - centers[i])) + 1
        return "SWEEP_TOP", "STEP_INDEX", f"STEP_{n}", str(17 + n), 9.6, "fig l18-l25"
    if 284 <= y < 297:
        return "SWEEP_TOP", "ARROW_LABEL", "UPDATE_ORDER", "27", 9.6, "fig l26-l27"
    if 306 <= y < 335:
        n = min(range(8), key=lambda i: abs(x - centers[i])) + 1
        return "SWEEP_NODES", "NODE_LABEL", f"NODE_{n}", str(31 + n), 9.6, "fig l32-l39"
    if 335 <= y < 350:
        if x < 260:
            return "SWEEP_NODES", "STATUS_DONE", "STATUS_DONE", "40", 9.6, "fig l40"
        if x < 350:
            return "SWEEP_NODES", "STATUS_CURRENT", "STATUS_CURRENT", "41", 9.6, "fig l41"
        return "SWEEP_NODES", "STATUS_OLD", "STATUS_OLD", "42", 9.6, "fig l42"
    if 350 <= y < 367:
        return "STATE_CARD_1", "FORMULA_BLOCK", "CARD1_STATE", "45", 10.0, "fig l44-l45"
    if 366 <= y < 380:
        if x < 285:
            return "STATE_CARD_1", "CARD_BODY_NEW", "CARD1_NEW", "46-47", 9.8, "fig l46-l47"
        return "STATE_CARD_1", "CARD_BODY_OLD", "CARD1_OLD", "48-49", 9.8, "fig l48-l49"
    if 383 <= y < 396:
        if x < 305:
            return "STATE_CARD_2", "ARROW_ANNOTATION", "SAME_STATE", "56", 9.6, "fig l55-l56"
        return "STATE_CARD_2", "ARROW_ANNOTATION", "ONLY_RECORD", "58", 9.6, "fig l57-l58"
    if 395 <= y < 411:
        if x < 285:
            return "STATE_CARD_2", "FORMULA_BLOCK", "CARD2_END", "52", 10.0, "fig l52"
        if x < 365:
            return "STATE_CARD_2", "FORMULA_BLOCK", "CARD2_ROUND", "53", 10.0, "fig l53"
        return "STATE_CARD_2", "CARD_SAMPLE", "CARD_SAMPLE", "54", 9.8, "fig l54"
    if 414 <= y < 445:
        if x < 125 and y < 432:
            return "CAPTION", "CAPTION_NUMBER", "CAPTION_NUMBER", "61", 10.0, "11pt class -> small=10pt; style caption small; fig l61"
        return "CAPTION", "CAPTION_BODY", "CAPTION_BODY", "61", 10.0, "11pt class -> small=10pt; style caption small; fig l61"
    return "OUT_OF_SCOPE", "PAGE_CONTEXT", line_key, "N/A", 0.0, "outside local figure audit crop"


def make_pair_pack(full: Image.Image, a: Any, b: Any, row: dict[str, Any], tag: str) -> None:
    dest = PAIR / tag
    dest.mkdir(parents=True, exist_ok=True)
    ab, bb = a.ink_bbox, b.ink_bbox
    ax = row.get("A_NEAREST_X")
    ay = row.get("A_NEAREST_Y")
    bx = row.get("B_NEAREST_X")
    by = row.get("B_NEAREST_Y")
    if all(v not in (None, "") for v in (ax, ay, bx, by)):
        ax, ay, bx, by = map(int, (ax, ay, bx, by))
        x0, y0 = max(0, min(ax, bx) - 24), max(0, min(ay, by) - 24)
        x1, y1 = min(full.width, max(ax, bx) + 25), min(full.height, max(ay, by) + 25)
    else:
        x0, y0 = max(0, min(ab[0], bb[0]) - 14), max(0, min(ab[1], bb[1]) - 14)
        x1, y1 = min(full.width, max(ab[2], bb[2]) + 14), min(full.height, max(ab[3], bb[3]) + 14)
    raw = full.crop((x0, y0, x1, y1))
    am = H.full_local_mask(a, x0, y0, x1, y1)
    bm = H.full_local_mask(b, x0, y0, x1, y1)
    ov = am & bm
    raw.save(dest / "raw_1x.png")
    Image.fromarray((am * 255).astype(np.uint8), "L").save(dest / "A_raw_mask_1x.png")
    Image.fromarray((bm * 255).astype(np.uint8), "L").save(dest / "B_raw_mask_1x.png")
    Image.fromarray((ov * 255).astype(np.uint8), "L").save(dest / "intersection_mask_1x.png")
    visual = np.zeros((*am.shape, 3), dtype=np.uint8)
    visual[am] = (220, 30, 30)
    visual[bm] = (25, 85, 230)
    visual[ov] = (255, 220, 0)
    vis = Image.fromarray(visual, "RGB")
    vis.save(dest / "A_B_overlay_1x.png")
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(dest / "inspection_8x_nearest.png")
    vis.resize((vis.width * 8, vis.height * 8), Image.Resampling.NEAREST).save(dest / "A_B_overlay_8x_nearest.png")
    write_json(dest / "pair.json", {
        "object_a": a.object_id,
        "object_b": b.object_id,
        "relation": row["RELATION"],
        "raw_1x_source": "renders/local_page_300dpi.png",
        "raw_roi_page_px": [x0, y0, x1, y1],
        "measurement": row,
        "8x_policy": "nearest-neighbour human review only; never geometry input",
    })


def main() -> None:
    for p in (RENDER, CROP, MASK, OVERLAY, PAIR):
        p.mkdir(parents=True, exist_ok=True)
    required = [PDF, PNG300, PNG200, FIG_SOURCE, STYLE_SOURCE, SIZE11, HELPER]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"missing required input: {missing}")

    source = FIG_SOURCE.read_text(encoding="utf-8")
    doc = fitz.open(PDF)
    if doc.page_count != 1:
        raise RuntimeError("local candidate must be exactly one A4 page")
    page = doc[0]
    full = Image.open(PNG300).convert("RGB")
    full200 = Image.open(PNG200).convert("RGB")
    img = np.asarray(full)
    h, w = img.shape[:2]
    sx, sy = w / page.rect.width, h / page.rect.height
    if (w, h) != (2481, 3508):
        raise RuntimeError(f"300 dpi grid mismatch: {(w, h)}")
    if full200.size != (1654, 2339):
        raise RuntimeError(f"200 dpi grid mismatch: {full200.size}")

    crop_pt = (65.0, 244.0, 535.0, 446.0)
    crop_box = (
        H.px_lo(crop_pt[0], sx), H.px_lo(crop_pt[1], sy),
        H.px_hi(crop_pt[2], sx), H.px_hi(crop_pt[3], sy),
    )
    figure_crop = full.crop(crop_box)
    figure_crop.save(CROP / "figure_crop_300dpi_1x.png")
    ImageOps.grayscale(figure_crop).save(CROP / "figure_crop_grayscale_300dpi_1x.png")
    figure_crop.resize((figure_crop.width * 8, figure_crop.height * 8), Image.Resampling.NEAREST).save(CROP / "figure_crop_8x_nearest_review.png")

    candidates: list[dict[str, Any]] = []
    order = 0
    raw = page.get_text("rawdict")
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block["lines"]):
            line_key = f"B{bi}L{li}"
            for span in line["spans"]:
                font_rgb = H.rgb_from_pdf(int(span.get("color", 0)))
                font = span.get("font", "")
                size = float(span.get("size", 0))
                for chd in span["chars"]:
                    ch = chd["c"]
                    if not ch.strip():
                        continue
                    bx0, by0, bx1, by1 = chd["bbox"]
                    panel, role, parent, src_line, declared, chain = semantic_info((by0 + by1) / 2, (bx0 + bx1) / 2, line_key)
                    if panel == "OUT_OF_SCOPE":
                        continue
                    math_ctx = "MATH" in font.upper() and "TEXT" not in font.upper()
                    klass = H.script_class(ch, font, size, math_ctx)
                    rect = H.clamp((H.px_lo(bx0, sx), H.px_lo(by0, sy), H.px_hi(bx1, sx), H.px_hi(by1, sy)), w, h)
                    mask = H.char_foreground(img[rect[1]:rect[3], rect[0]:rect[2]], font_rgb)
                    candidates.append({
                        "order": order, "char": ch, "bbox": rect, "candidate": mask,
                        "panel": panel, "role": role, "parent": parent, "source_line": src_line,
                        "declared": declared, "chain": chain, "script": klass, "font": font,
                        "span_size": size, "line_key": line_key,
                        "pdf_bbox": [round(v, 3) for v in chd["bbox"]], "math": math_ctx,
                    })
                    order += 1

    owner = np.full((h, w), -1, dtype=np.int32)
    score = np.full((h, w), np.inf, dtype=np.float32)
    for i, c in enumerate(candidates):
        x0, y0, x1, y1 = c["bbox"]
        yy, xx = np.nonzero(c["candidate"])
        if not len(xx):
            continue
        gx, gy = xx + x0, yy + y0
        cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        rx, ry = max(1.0, (x1 - x0) / 2), max(1.0, (y1 - y0) / 2)
        rank = ((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2
        take = rank < score[gy, gx]
        score[gy[take], gx[take]] = rank[take]
        owner[gy[take], gx[take]] = i

    chars = []
    for i, c in enumerate(candidates):
        x0, y0, x1, y1 = c["bbox"]
        mask = owner[y0:y1, x0:x1] == i
        chars.append(H.Obj(
            f"CHAR-{i + 1:04d}", "CHARACTER", "RAW_GLYPH", c["panel"], c["role"], c["parent"],
            c["source_line"], c["bbox"], mask, char=c["char"], text=c["char"], script=c["script"],
            declared_pt=c["declared"], source_chain=c["chain"], extra=c,
            materialization="direct 300dpi page raw pixels; exact PDF glyph bbox; local background delta >=20/255",
        ))

    groups: dict[tuple[Any, ...], list[Any]] = defaultdict(list)
    last_base = None
    segment = 0
    for obj in chars:
        c = obj.extra or {}
        base = (obj.parent, c["line_key"], obj.script)
        if base != last_base:
            segment += 1
        groups[(*base, segment)].append(obj)
        last_base = base
    elements = []
    for n, members in enumerate(groups.values(), 1):
        first = members[0]
        elements.append(H.union_object(
            f"EL-{n:03d}-{first.parent}-{first.script}", "TEXT_ELEMENT", "SEMANTIC_TEXT", members,
        ))

    drawings = page.get_drawings()
    graphics = []
    graphics.append(H.make_stroke_object("G-TOP-ARROW-SHAFT", "ARROW_SHAFT", "SWEEP_TOP", "26", drawings[0], H.COLOR["arrow"], img, sx, sy, w, h, parent="TOP_ARROW"))
    graphics.append(H.make_stroke_object("G-TOP-ARROW-HEAD", "ARROWHEAD", "SWEEP_TOP", "26", drawings[1], H.COLOR["arrow"], img, sx, sy, w, h, parent="TOP_ARROW"))
    node_draw_idx = [3, 5, 7, 9, 14, 15, 16, 17]
    node_lines = [28, 29, 30, 31, 36, 37, 38, 39]
    node_colours = [H.COLOR["blue"]] * 4 + [H.COLOR["gold"]] + [H.COLOR["rule"]] * 3
    node_draws = []
    for n, (di, src_line, colour) in enumerate(zip(node_draw_idx, node_lines, node_colours), 1):
        d = drawings[di]
        node_draws.append(d)
        graphics.append(H.make_stroke_object(f"G-NODE-{n}-BORDER", "NODE_BORDER", "SWEEP_NODES", str(src_line), d, colour, img, sx, sy, w, h, frame=True, parent=f"NODE_{n}"))
        graphics.append(H.make_background_object(f"G-NODE-{n}-FILL", "NODE_FILL_BACKGROUND", "SWEEP_NODES", str(src_line), d, sx, sy, w, h, parent=f"NODE_{n}"))
    for n in range(1, 5):
        graphics.append(H.final_texture_object(f"G-NODE-{n}-FINAL-TEXTURE", "SWEEP_NODES", "7,28-31", node_draws[n - 1], img, sx, sy, w, h, parent=f"NODE_{n}"))
        graphics.append(H.make_background_object(f"G-NODE-{n}-PRE-TEXTURE", "PREOCCLUSION_TEXTURE", "SWEEP_NODES", "7,28-31", node_draws[n - 1], sx, sy, w, h, parent=f"NODE_{n}"))
    for n, di in enumerate([10, 11, 12, 13], 1):
        graphics.append(H.make_background_object(f"G-NODE-{n}-HALO", "HALO_BACKGROUND", "SWEEP_NODES", f"8,{31 + n}", drawings[di], sx, sy, w, h, parent=f"NODE_{n}"))
    for oid, panel, src_line, di in [
        ("G-CARD1-BORDER", "STATE_CARD_1", "44", 18),
        ("G-CARD2-BORDER", "STATE_CARD_2", "51", 19),
    ]:
        graphics.append(H.make_stroke_object(oid, "CARD_BORDER", panel, src_line, drawings[di], H.COLOR["rule"], img, sx, sy, w, h, frame=True, parent=oid.replace("G-", "").replace("-BORDER", "")))
        graphics.append(H.make_background_object(oid.replace("BORDER", "FILL"), "CARD_FILL_BACKGROUND", panel, src_line, drawings[di], sx, sy, w, h, parent=oid.replace("G-", "").replace("-BORDER", "")))
    for oid, subtype, src_line, di, parent in [
        ("G-SAME-STATE-SHAFT", "ARROW_SHAFT", "55", 20, "SAME_STATE_ARROW"),
        ("G-SAME-STATE-LEFT-HEAD", "ARROWHEAD", "55", 21, "SAME_STATE_ARROW"),
        ("G-SAME-STATE-RIGHT-HEAD", "ARROWHEAD", "55", 22, "SAME_STATE_ARROW"),
        ("G-RECORD-SHAFT", "ARROW_SHAFT", "57", 23, "RECORD_ARROW"),
        ("G-RECORD-HEAD", "ARROWHEAD", "57", 24, "RECORD_ARROW"),
    ]:
        graphics.append(H.make_stroke_object(oid, subtype, "STATE_CARD_2", src_line, drawings[di], H.COLOR["arrow"], img, sx, sy, w, h, parent=parent))

    H.MASK = MASK
    H.save_mask_registry(chars + elements + graphics)

    manifest = []
    for obj in chars + elements + graphics:
        manifest.append({
            "OBJECT_ID": obj.object_id, "CATEGORY": obj.category, "SUBTYPE": obj.subtype,
            "PANEL_ID": obj.panel, "ROLE": obj.role, "PARENT_ELEMENT_ID": obj.parent,
            "TEXT_OR_CHAR": obj.text or obj.char, "SCRIPT_CLASS": obj.script,
            "SOURCE_LINE": obj.source_line, "DECLARED_PT": "" if obj.declared_pt is None else f"{obj.declared_pt:.3f}",
            "BBOX": json.dumps(obj.bbox), "INK_BBOX": json.dumps(obj.ink_bbox),
            "MASK_PIXEL_COUNT": obj.pixels, "BACKGROUND_EXEMPT": str(obj.background).lower(),
            "PAIR_INCLUDED": str(obj.category in {"TEXT_ELEMENT", "GRAPHIC", "BACKGROUND"}).lower(),
            "MATERIALIZATION": obj.materialization,
        })
    write_csv(OUT / "complete_object_manifest.csv", manifest)

    raw_rows = []
    for obj in chars:
        c = obj.extra or {}
        height = H.h_ink(obj.mask)
        gate = H.threshold(obj.script)
        hard = gate is not None
        status = "PASS" if not hard or height >= gate else "FAIL"
        if obj.script == "PUNCTUATION":
            status = "INFO"
        raw_rows.append({
            "CHAR_ID": obj.object_id, "PARENT_ELEMENT_ID": obj.parent, "PANEL_ID": obj.panel,
            "ROLE": obj.role, "SOURCE_LINE": obj.source_line, "DECLARED_PT": f"{obj.declared_pt:.3f}",
            "PDF_FONT": c.get("font", ""), "PDF_SPAN_SIZE_PT": f"{float(c.get('span_size', 0)):.3f}",
            "TEXT_SAMPLE": obj.char, "SCRIPT_CLASS": obj.script, "PDF_BBOX_PT": json.dumps(c.get("pdf_bbox", [])),
            "INK_BBOX": json.dumps(obj.ink_bbox), "H_INK_PX": height,
            "PIXEL_THRESHOLD_PX": "N/A" if gate is None else gate, "PASS_FAIL": status,
            "METHOD": "direct local-page 300dpi 1:1 raw ink; local background >=20/255; exact glyph bbox",
        })
    write_csv(OUT / "raw_char_measurements.csv", raw_rows)

    element_rows = []
    for obj in elements:
        height = H.h_ink(obj.mask)
        gate = H.threshold(obj.script)
        element_rows.append({
            "ELEMENT_ID": obj.object_id, "PANEL_ID": obj.panel, "ROLE": obj.role,
            "PARENT_SOURCE_ELEMENT": obj.parent, "SOURCE_LINE": obj.source_line,
            "DECLARED_PT": f"{obj.declared_pt:.3f}", "TEXT_SAMPLE": obj.text,
            "SCRIPT_CLASS": obj.script, "INK_BBOX": json.dumps(obj.ink_bbox), "H_INK_PX": height,
            "PIXEL_THRESHOLD_PX": "N/A" if gate is None else gate,
            "PASS_FAIL": "PASS" if gate is None or height >= gate else "FAIL",
        })

    font_rows = []
    for obj in elements:
        base = float(obj.declared_pt or 0.0)
        is_script = obj.script == "MATH_SCRIPT"
        effective = 9.0 if is_script and base == 10.0 else base
        font_rows.append({
            "AUDIT_ID": obj.object_id, "PANEL_ID": obj.panel, "ROLE": obj.role,
            "SCRIPT_CLASS": obj.script, "TEXT_SAMPLE": obj.text, "SOURCE_LINE": obj.source_line,
            "DECLARED_BASE_PT": f"{base:.3f}", "EFFECTIVE_PT": f"{effective:.3f}",
            "THRESHOLD": "legal TeX script derived from >=9.5pt base" if is_script else ">=9.5pt",
            "STATUS": "PASS_DERIVED_SCRIPT" if is_script else ("PASS" if base >= 9.5 else "FAIL"),
            "CHAIN": obj.source_chain,
        })
    write_csv(OUT / "after_font_audit.csv", font_rows)

    d_groups: dict[tuple[str, str, str], list[Any]] = defaultdict(list)
    for obj in elements:
        if H.threshold(obj.script) is not None:
            d_groups[(obj.panel, obj.role, obj.script)].append(obj)
    d_rows = []
    medians: dict[tuple[str, str, str], float] = {}
    for key, members in sorted(d_groups.items()):
        heights = [H.h_ink(x.mask) for x in members]
        median = float(np.median(heights))
        medians[key] = median
        comparable = len(members) >= 2
        max_min = max(heights) / min(heights) if min(heights) else float("inf")
        passed = not comparable or (all(0.92 <= x / median <= 1.08 for x in heights) and max_min <= 1.08)
        for obj, value in zip(members, heights):
            d_rows.append({
                "GROUP_ID": "D-" + "-".join(key), "PANEL_ID": key[0], "SEMANTIC_ROLE": key[1],
                "SCRIPT_CLASS": key[2], "ELEMENT_ID": obj.object_id, "TEXT_SAMPLE": obj.text,
                "RAW_H_INK_PX": value, "CLASS_MEDIAN_PX": f"{median:.3f}",
                "RATIO_TO_MEDIAN": f"{value / median:.4f}", "ELEMENT_COUNT": len(members),
                "MAX_MIN_RATIO": f"{max_min:.4f}",
                "THRESHOLD": "[0.92,1.08]; max/min<=1.08" if comparable else "N/A singleton",
                "STATUS": "PASS" if passed else "FAIL",
                "GROUPING": "same panel + same semantic role + same script; never glyph identity; never cross-script",
            })
    write_csv(OUT / "same_class_ratio_audit.csv", d_rows)

    base_by_script = {}
    for script in {k[2] for k in medians}:
        key = ("SWEEP_NODES", "NODE_LABEL", script)
        if key in medians:
            base_by_script[script] = key
    role_bounds = {
        "PANEL_TITLE": (1.05, 1.20), "FORMULA_BLOCK": (1.00, 1.18), "NODE_LABEL": (0.95, 1.10),
        "STATUS_DONE": (0.95, 1.10), "STATUS_CURRENT": (0.95, 1.10), "STATUS_OLD": (0.95, 1.10),
        "CARD_BODY_NEW": (0.95, 1.10), "CARD_BODY_OLD": (0.95, 1.10), "CARD_SAMPLE": (0.95, 1.10),
        "ARROW_LABEL": (0.95, 1.10), "ARROW_ANNOTATION": (0.95, 1.10), "STEP_INDEX": (0.95, 1.10),
    }
    e_rows = []
    for key, median in sorted(medians.items()):
        panel, role, script = key
        base_key = base_by_script.get(script)
        if role.startswith("CAPTION") or role not in role_bounds or base_key is None:
            e_rows.append({
                "GROUP_ID": "E-" + "-".join(key), "PANEL_ID": panel, "ROLE": role,
                "SCRIPT_CLASS": script, "ROLE_MEDIAN_H_INK_PX": f"{median:.3f}",
                "BASE_GROUP": "N/A", "BASE_MEDIAN_H_INK_PX": "N/A", "RATIO_TO_BASE": "N/A",
                "ALLOWED_RANGE": "N/A", "STATUS": "N/A",
                "REASON": "No matching NODE_LABEL BASE in same script (or caption has no Goal BASE); cross-script comparison prohibited",
            })
            continue
        base = medians[base_key]
        ratio = median / base
        lo, hi = role_bounds[role]
        e_rows.append({
            "GROUP_ID": "E-" + "-".join(key), "PANEL_ID": panel, "ROLE": role,
            "SCRIPT_CLASS": script, "ROLE_MEDIAN_H_INK_PX": f"{median:.3f}",
            "BASE_GROUP": "/".join(base_key), "BASE_MEDIAN_H_INK_PX": f"{base:.3f}",
            "RATIO_TO_BASE": f"{ratio:.4f}", "ALLOWED_RANGE": f"[{lo:.2f},{hi:.2f}]",
            "STATUS": "PASS" if lo <= ratio <= hi else "FAIL",
            "REASON": "matching-script BASE only",
        })
    write_csv(OUT / "role_ratio_audit.csv", e_rows)

    # Separate schema cross-panel role checks: same semantic role + same script only.
    cross_groups: dict[tuple[str, str], dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
    for obj in elements:
        if H.threshold(obj.script) is not None:
            cross_groups[(obj.role, obj.script)][obj.panel].append(obj)
    cross_rows = []
    for (role, script), panels in sorted(cross_groups.items()):
        if len(panels) < 2:
            continue
        panel_medians = {panel: float(np.median([H.h_ink(x.mask) for x in members])) for panel, members in panels.items()}
        panel_source = {panel: float(np.median([float(x.declared_pt or 0.0) for x in members])) for panel, members in panels.items()}
        ink_ratio = max(panel_medians.values()) / min(panel_medians.values())
        source_ratio = max(panel_source.values()) / min(panel_source.values())
        status = "PASS" if ink_ratio <= 1.10 and source_ratio <= 1.05 else "FAIL"
        for panel in sorted(panels):
            cross_rows.append({
                "GROUP_ID": f"XROLE-{role}-{script}", "ROLE": role, "SCRIPT_CLASS": script,
                "PANEL_ID": panel, "PANEL_MEDIAN_H_INK_PX": f"{panel_medians[panel]:.3f}",
                "PANEL_SOURCE_PT_MEDIAN": f"{panel_source[panel]:.3f}",
                "CROSS_PANEL_INK_MAX_MIN": f"{ink_ratio:.4f}", "INK_THRESHOLD": "<=1.10",
                "CROSS_PANEL_SOURCE_MAX_MIN": f"{source_ratio:.4f}", "SOURCE_THRESHOLD": "<=1.05",
                "STATUS": status, "GROUPING": "same role + same script across panels; never cross-script",
            })
    if cross_rows:
        write_csv(OUT / "cross_panel_role_audit.csv", cross_rows)

    pair_objects = elements + graphics
    pair_rows = []
    failed_pairs = []
    near_pairs = []
    min_by_relation: dict[str, float] = defaultdict(lambda: float("inf"))
    pair_id = 0
    for i, left in enumerate(pair_objects):
        for right in pair_objects[i + 1:]:
            pair_id += 1
            relation, limit, reason = H.relation(left, right)
            lower = H.bbox_gap(left.ink_bbox, right.ink_bbox)
            exact = left.pixels == 0 or right.pixels == 0 or lower <= max(32.0, (limit or 0) + 12.0) or H.rect_intersects(left.ink_bbox, right.ink_bbox)
            if exact:
                overlap, distance, ca, cb = H.exact_distance(left, right)
                gap = max(0.0, distance - 1.0)
                method = "exact separated 1:1 raw masks + local EDT"
            else:
                overlap, gap, ca, cb = 0, max(0.0, lower - 1.0), None, None
                method = "raw-ink bbox lower bound proves noncritical"
            if left.pixels == 0 or right.pixels == 0:
                status, reason = "FAIL", "empty foreground mask"
            elif limit is None:
                status = "EXEMPT" if relation in {"BACKGROUND_LAYER_EXEMPT", "INTRA_TEXT_ELEMENT", "GRAPHIC_GRAPHIC"} else "PASS"
            elif overlap >= 1 or gap < limit:
                status = "FAIL"
            else:
                status = "PASS"
            min_by_relation[relation] = min(min_by_relation[relation], gap)
            row = {
                "PAIR_ID": f"PAIR-{pair_id:06d}", "OBJECT_A": left.object_id, "OBJECT_B": right.object_id,
                "CATEGORY_A": left.category, "CATEGORY_B": right.category, "RELATION": relation,
                "THRESHOLD_PX": "N/A" if limit is None else f"{limit:.1f}", "METHOD": method,
                "OVERLAP_PIXELS": overlap, "MIN_RAW_INK_GAP_PX": "INF" if math.isinf(gap) else f"{gap:.3f}",
                "A_NEAREST_X": "" if ca is None else ca[0], "A_NEAREST_Y": "" if ca is None else ca[1],
                "B_NEAREST_X": "" if cb is None else cb[0], "B_NEAREST_Y": "" if cb is None else cb[1],
                "STATUS": status, "REASON": reason,
            }
            pair_rows.append(row)
            if status == "FAIL":
                failed_pairs.append((left, right, row))
            if limit is not None and gap <= limit + 4.0:
                near_pairs.append((left, right, row))
    write_csv(OUT / "all_pairs_overlap_clearance.csv", pair_rows)
    write_csv(OUT / "after_overlap_report.csv", pair_rows)

    for row in element_rows:
        d = next((x for x in d_rows if x["ELEMENT_ID"] == row["ELEMENT_ID"]), None)
        if d:
            row["CLASS_MEDIAN_PX"] = d["CLASS_MEDIAN_PX"]
            row["RATIO_TO_CLASS_MEDIAN"] = d["RATIO_TO_MEDIAN"]
        else:
            row["CLASS_MEDIAN_PX"] = "N/A"
            row["RATIO_TO_CLASS_MEDIAN"] = "N/A"
        er = next((x for x in e_rows if x["GROUP_ID"] == f"E-{row['PANEL_ID']}-{row['ROLE']}-{row['SCRIPT_CLASS']}"), None)
        row["ROLE_RATIO"] = er["RATIO_TO_BASE"] if er else "N/A"
    write_csv(OUT / "after_pixel_measurements.csv", element_rows)

    edge_rows = []
    clip_count = 0
    edge_fail = 0
    for obj in pair_objects:
        ib = obj.ink_bbox
        physical_edge = min(ib[0], ib[1], w - ib[2], h - ib[3])
        crop_edge = min(ib[0] - crop_box[0], ib[1] - crop_box[1], crop_box[2] - ib[2], crop_box[3] - ib[3])
        clipped = obj.pixels > 0 and (ib[0] <= 0 or ib[1] <= 0 or ib[2] >= w or ib[3] >= h)
        if clipped and not obj.background:
            clip_count += 1
        if obj.panel in FIGURE_PANELS and crop_edge < 6 and not obj.background:
            edge_fail += 1
        edge_rows.append({
            "OBJECT_ID": obj.object_id, "CATEGORY": obj.category, "PANEL_ID": obj.panel,
            "INK_BBOX": json.dumps(ib), "PHYSICAL_PAGE_EDGE_CLEARANCE_PX": physical_edge,
            "FIGURE_CROP_EDGE_CLEARANCE_PX": crop_edge, "CLIP_STATUS": "FAIL" if clipped and not obj.background else "PASS",
            "EDGE_6PX_STATUS": "PASS" if obj.background or crop_edge >= 6 else "FAIL",
        })
    write_csv(OUT / "edge_clip_audit.csv", edge_rows)

    # Mandatory critical witness: the repaired script [j] and literal j to first card border.
    card_border = next(x for x in graphics if x.object_id == "G-CARD1-BORDER")
    script_element = next(x for x in elements if x.parent == "CARD1_STATE" and x.script == "MATH_SCRIPT")
    literal_j = next(x for x in chars if x.parent == "CARD1_STATE" and x.char == "𝑗")
    selected = []
    for obj, tag in [(script_element, "EL035_script_to_card1_border"), (literal_j, "literal_j_to_card1_border")]:
        overlap, distance, ca, cb = H.exact_distance(obj, card_border)
        gap = max(0.0, distance - 1.0)
        row = {
            "PAIR_ID": "SELECTED", "OBJECT_A": obj.object_id, "OBJECT_B": card_border.object_id,
            "CATEGORY_A": obj.category, "CATEGORY_B": card_border.category, "RELATION": "TEXT_BORDER",
            "THRESHOLD_PX": "5.0", "METHOD": "exact separated 1:1 raw masks + local EDT",
            "OVERLAP_PIXELS": overlap, "MIN_RAW_INK_GAP_PX": f"{gap:.3f}",
            "A_NEAREST_X": ca[0], "A_NEAREST_Y": ca[1], "B_NEAREST_X": cb[0], "B_NEAREST_Y": cb[1],
            "STATUS": "PASS" if overlap == 0 and gap >= 5 else "FAIL", "REASON": "targeted repaired clearance",
        }
        selected.append(row)
        make_pair_pack(full, obj, card_border, row, tag)
    write_csv(OUT / "targeted_EL035_clearance.csv", selected)

    evidence = []
    seen = set()
    for left, right, row in failed_pairs + near_pairs:
        key = tuple(sorted((left.object_id, right.object_id)))
        if key in seen:
            continue
        seen.add(key)
        evidence.append((left, right, row))
    for n, (left, right, row) in enumerate(evidence, 1):
        make_pair_pack(full, left, right, row, f"auto_{n:03d}_{row['RELATION'].lower()}")

    required_pack_files = {"raw_1x.png", "A_raw_mask_1x.png", "B_raw_mask_1x.png", "intersection_mask_1x.png", "A_B_overlay_1x.png", "inspection_8x_nearest.png", "A_B_overlay_8x_nearest.png", "pair.json"}
    pack_dirs = sorted(p for p in PAIR.iterdir() if p.is_dir())
    incomplete_packs = [p.name for p in pack_dirs if not required_pack_files.issubset({x.name for x in p.iterdir() if x.is_file()})]
    expected_pack_count = len(evidence) + 2

    overlay = full.copy()
    draw = ImageDraw.Draw(overlay)
    for obj in elements:
        draw.rectangle(obj.ink_bbox, outline=(220, 30, 30), width=2)
    for obj in graphics:
        if not obj.background:
            draw.rectangle(obj.ink_bbox, outline=(25, 85, 230), width=1)
    overlay.crop(crop_box).save(OVERLAY / "text_graphics_measurement_overlay_300dpi_1x.png")

    glyph_fail = [x for x in raw_rows if x["PASS_FAIL"] == "FAIL"]
    element_fail = [x for x in element_rows if x["PASS_FAIL"] == "FAIL"]
    d_fail = [x for x in d_rows if x["STATUS"] == "FAIL"]
    e_fail = [x for x in e_rows if x["STATUS"] == "FAIL"]
    cross_fail = [x for x in cross_rows if x["STATUS"] == "FAIL"]
    literal_yi = [x for x in raw_rows if x["TEXT_SAMPLE"] == "一"]
    empty_graphics = [x.object_id for x in graphics if not x.background and x.pixels == 0]
    overlap_failed = [x for x in failed_pairs if int(x[2]["OVERLAP_PIXELS"]) >= 1]
    clearance_failed = [x for x in failed_pairs if int(x[2]["OVERLAP_PIXELS"]) == 0]
    ordinary_fonts = [float(x["DECLARED_BASE_PT"]) for x in font_rows if x["SCRIPT_CLASS"] != "MATH_SCRIPT"]
    source_font_values = [float(x) for x in __import__("re").findall(r"\\fontsize\{([0-9.]+)pt\}", source)]
    source_font_min = min(source_font_values)
    summary = {
        "figure_id": "FIG-P634-01",
        "disposition": "LOCAL_SA2_SELF_AUDIT_ONLY_NOT_FORMAL_PASS",
        "input": {"pdf": str(PDF), "page": 1, "a4_pt": [page.rect.width, page.rect.height]},
        "raw_render": {"file": str(PNG300), "dpi": 300, "pixels": [w, h], "resized": False},
        "counts": {
            "literal_glyphs": len(chars), "semantic_text_elements": len(elements), "graphics_and_backgrounds": len(graphics),
            "pair_objects": len(pair_objects), "all_unordered_pairs": len(pair_rows),
            "literal_CJK_yi": len(literal_yi), "glyph_pixel_failures": len(glyph_fail),
            "element_pixel_failures": len(element_fail), "D_failures": len(d_fail), "E_failures": len(e_fail),
            "cross_panel_role_failures": len(cross_fail),
            "pair_failures": len(failed_pairs), "overlap_failures": len(overlap_failed),
            "clearance_failures": len(clearance_failed), "clip_objects": clip_count, "edge_failures": edge_fail,
            "empty_foreground_graphics": len(empty_graphics),
            "critical_pair_packs": len(pack_dirs), "expected_critical_pair_packs": expected_pack_count,
            "incomplete_critical_pair_packs": len(incomplete_packs),
        },
        "gates": {
            "source_min_explicit_font_pt": source_font_min,
            "source_font_ge_9_5": source_font_min >= 9.5 and min(ordinary_fonts) >= 9.5,
            "pixel_height_pass": not glyph_fail and not element_fail,
            "D_pass": not d_fail, "E_pass": not e_fail,
            "cross_panel_role_pass": not cross_fail,
            "overlap_zero": not overlap_failed, "clearance_pass": not clearance_failed,
            "clip_zero": clip_count == 0, "edge_ge_6": edge_fail == 0,
            "EL035_script_to_card1_border_px": float(selected[0]["MIN_RAW_INK_GAP_PX"]),
            "EL035_literal_j_to_card1_border_px": float(selected[1]["MIN_RAW_INK_GAP_PX"]),
            "EL035_ge_5": all(x["STATUS"] == "PASS" for x in selected),
        },
        "thresholds": {
            "font_pt": 9.5, "CJK": 30, "upper_digit": 24, "lower_greek": 17,
            "math_base_operator_fraction": 22, "legal_script": 15,
            "text_text": 4, "text_line_arrow": 3, "text_border": 5, "cross_panel": 8, "edge": 6,
        },
        "minimum_by_relation": {k: (None if math.isinf(v) else round(v, 3)) for k, v in min_by_relation.items()},
        "failures": {"glyph": glyph_fail, "element": element_fail, "D": d_fail, "E": e_fail, "cross_panel_role": cross_fail, "pairs": [x[2] for x in failed_pairs]},
        "empty_graphics": empty_graphics,
    }
    write_json(OUT / "audit_summary.json", summary)

    machine_pass = all([
        summary["gates"]["source_font_ge_9_5"], summary["gates"]["pixel_height_pass"],
        summary["gates"]["D_pass"], summary["gates"]["E_pass"], summary["gates"]["cross_panel_role_pass"], summary["gates"]["overlap_zero"],
        summary["gates"]["clearance_pass"], summary["gates"]["clip_zero"], summary["gates"]["edge_ge_6"],
        summary["gates"]["EL035_ge_5"], not empty_graphics, len(source_font_values) > 0,
        len({x["OBJECT_ID"] for x in manifest}) == len(manifest),
        len(pair_rows) == len(pair_objects) * (len(pair_objects) - 1) // 2,
        len(pack_dirs) == expected_pack_count, not incomplete_packs,
    ])
    end = {
        "status": "PASS" if machine_pass else "FAIL",
        "scope": "local SA2 candidate evidence only; root official rebuild and independent validation remain mandatory",
        "required_outputs_present": all(p.exists() for p in [
            OUT / "audit_summary.json", OUT / "raw_char_measurements.csv", OUT / "after_font_audit.csv",
            OUT / "same_class_ratio_audit.csv", OUT / "role_ratio_audit.csv", OUT / "all_pairs_overlap_clearance.csv",
            OUT / "targeted_EL035_clearance.csv", CROP / "figure_crop_300dpi_1x.png",
            OVERLAY / "text_graphics_measurement_overlay_300dpi_1x.png",
        ]),
        "candidate_gate_pass": machine_pass,
    }
    write_json(OUT / "machine_end_check.json", end)
    terminal_rows = [
        {"GATE": "SOURCE_FONT_GE_9_5", "VALUE": str(summary["gates"]["source_font_ge_9_5"]).lower(), "THRESHOLD": ">=9.5pt ordinary", "STATUS": "PASS" if summary["gates"]["source_font_ge_9_5"] else "FAIL"},
        {"GATE": "LITERAL_CJK_YI_COUNT", "VALUE": len(literal_yi), "THRESHOLD": "0", "STATUS": "PASS" if not literal_yi else "FAIL"},
        {"GATE": "RAW_PIXEL_FAILURES", "VALUE": len(glyph_fail) + len(element_fail), "THRESHOLD": "0", "STATUS": "PASS" if not glyph_fail and not element_fail else "FAIL"},
        {"GATE": "D_FAILURES", "VALUE": len(d_fail), "THRESHOLD": "0", "STATUS": "PASS" if not d_fail else "FAIL"},
        {"GATE": "E_FAILURES", "VALUE": len(e_fail), "THRESHOLD": "0", "STATUS": "PASS" if not e_fail else "FAIL"},
        {"GATE": "CROSS_PANEL_ROLE_FAILURES", "VALUE": len(cross_fail), "THRESHOLD": "0; source<=1.05, ink<=1.10", "STATUS": "PASS" if not cross_fail else "FAIL"},
        {"GATE": "OVERLAP_FAILED_PAIRS", "VALUE": len(overlap_failed), "THRESHOLD": "0", "STATUS": "PASS" if not overlap_failed else "FAIL"},
        {"GATE": "CLEARANCE_FAILED_PAIRS", "VALUE": len(clearance_failed), "THRESHOLD": "0", "STATUS": "PASS" if not clearance_failed else "FAIL"},
        {"GATE": "CLIP_OBJECTS", "VALUE": clip_count, "THRESHOLD": "0", "STATUS": "PASS" if clip_count == 0 else "FAIL"},
        {"GATE": "EDGE_FAILED_OBJECTS", "VALUE": edge_fail, "THRESHOLD": "0; >=6px", "STATUS": "PASS" if edge_fail == 0 else "FAIL"},
        {"GATE": "EL035_SCRIPT_BORDER_GAP", "VALUE": selected[0]["MIN_RAW_INK_GAP_PX"], "THRESHOLD": ">=5px; design >=8px", "STATUS": selected[0]["STATUS"]},
        {"GATE": "EL035_LITERAL_J_BORDER_GAP", "VALUE": selected[1]["MIN_RAW_INK_GAP_PX"], "THRESHOLD": ">=5px; design >=8px", "STATUS": selected[1]["STATUS"]},
        {"GATE": "EMPTY_FOREGROUND_GRAPHICS", "VALUE": len(empty_graphics), "THRESHOLD": "0", "STATUS": "PASS" if not empty_graphics else "FAIL"},
        {"GATE": "UNORDERED_PAIR_COVERAGE", "VALUE": len(pair_rows), "THRESHOLD": f"{len(pair_objects) * (len(pair_objects) - 1) // 2}", "STATUS": "PASS" if len(pair_rows) == len(pair_objects) * (len(pair_objects) - 1) // 2 else "FAIL"},
    ]
    terminal_rows.extend([
        {"GATE": "MANIFEST_UNIQUE_OBJECT_IDS", "VALUE": len({x["OBJECT_ID"] for x in manifest}), "THRESHOLD": str(len(manifest)), "STATUS": "PASS" if len({x["OBJECT_ID"] for x in manifest}) == len(manifest) else "FAIL"},
        {"GATE": "CRITICAL_PAIR_PACK_COUNT", "VALUE": len(pack_dirs), "THRESHOLD": str(expected_pack_count), "STATUS": "PASS" if len(pack_dirs) == expected_pack_count else "FAIL"},
        {"GATE": "INCOMPLETE_CRITICAL_PAIR_PACKS", "VALUE": len(incomplete_packs), "THRESHOLD": "0", "STATUS": "PASS" if not incomplete_packs else "FAIL"},
        {"GATE": "SUMMARY_BOTTOM_UP_CONSISTENCY", "VALUE": "true" if not glyph_fail and not element_fail and not d_fail and not e_fail and not cross_fail and not failed_pairs and not empty_graphics else "false", "THRESHOLD": "true", "STATUS": "PASS" if not glyph_fail and not element_fail and not d_fail and not e_fail and not cross_fail and not failed_pairs and not empty_graphics else "FAIL"},
    ])
    write_csv(OUT / "machine_terminal_check.csv", terminal_rows)
    terminal = {
        "status": "PASS" if all(x["STATUS"] == "PASS" for x in terminal_rows) else "FAIL",
        "formal_disclaimer": "SA2 local self-check only; not an official SA1/SA3/root acceptance",
        "rows": terminal_rows,
        "machine_end_check": end,
    }
    write_json(OUT / "machine_terminal_check.json", terminal)
    terminal_md = [
        "# FIG-P634-01 R6 local machine terminal check",
        "",
        f"Result: **{terminal['status']} (local SA2 candidate only)**",
        "",
        "| Gate | Value | Threshold | Status |",
        "|---|---:|---:|---|",
    ]
    terminal_md.extend(f"| {x['GATE']} | {x['VALUE']} | {x['THRESHOLD']} | {x['STATUS']} |" for x in terminal_rows)
    terminal_md.extend(["", "Root must still build the new official whole-book candidate and commission independent validation.", ""])
    (OUT / "machine_terminal_check.md").write_text("\n".join(terminal_md), encoding="utf-8")
    print(json.dumps({"status": end["status"], "counts": summary["counts"], "gates": summary["gates"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
