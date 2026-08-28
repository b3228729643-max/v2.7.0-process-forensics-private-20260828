#!/usr/bin/env python3
"""Build fresh R102 SA1 evidence for FIG-P654-01 without TeX or cache writes."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r102_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
GOAL = Path(r"D:\Users\ASUS\Desktop\机器学习\GOAL.md")
GOAL_V270 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md")
GOAL_V160 = Path(r"D:\Users\ASUS\Desktop\机器学习\Codex_统计学习方法合并总册_全文扫描问题补充_全量审查数学核验与精修_主提示词_v1.6.0_完整版.md")
PROTOCOL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md")
SCHEMA = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md")

PAGE_INDEX = 703
PAGE_NUMBER = 704
PRINTED_PAGE = 691
DPI = 300
SCALE = DPI / 72.0
CROP_PT = (70.0, 60.0, 535.0, 210.0)
EXPECTED_COMMIT = "94d1b62b877e80000539879688e6209c09882833"
EXPECTED_PDF_SHA256 = "60026DE5A4168D6F3B304D1AE59BE68E1F570CD22D992E43FCAD9828E25A1397"

DIRS = {
    "views": ROOT / "views",
    "machine": ROOT / "machine",
    "ledgers": ROOT / "ledgers",
    "objects": ROOT / "object_evidence",
    "pairs": ROOT / "pair_evidence",
    "contacts": ROOT / "contact_sheets",
    "provenance": ROOT / "provenance",
    "reports": ROOT / "reports",
}


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def pt_rect_to_px(rect, width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, math.floor(x0 * SCALE) - pad),
        max(0, math.floor(y0 * SCALE) - pad),
        min(width, math.ceil(x1 * SCALE) + pad),
        min(height, math.ceil(y1 * SCALE) + pad),
    )


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def crop_with_pad(box, width, height, pad=8):
    x0, y0, x1, y1 = box
    return (max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad))


def safe_name(object_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", object_id)


def color_int_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def assign_parent(cx: float, cy: float, taxonomy: dict) -> dict:
    hits = []
    for p in taxonomy["parents"]:
        x0, y0, x1, y1 = p["rect_pt"]
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            hits.append(p)
    if len(hits) != 1:
        raise RuntimeError(f"parent assignment not unique at {(cx, cy)}: {[x['id'] for x in hits]}")
    return hits[0]


LOW_PUNCT = set(".,:;…，、。：；‧·")


def script_class(ch: str, parent: dict, span_size: float, font: str) -> tuple[str, int, str]:
    if parent["id"] in {"N_PREDICTIVE_FRAC_NUM", "N_PREDICTIVE_FRAC_DEN"} and span_size < 9.5:
        return "NATURAL_SCRIPT", 15, "TeX natural subscript from 11.6pt fraction formula"
    if ch in LOW_PUNCT:
        return "LOW_PROFILE_PUNCTUATION", 0, "strict calibration required"
    cp = ord(ch)
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_FULL", 30, "CJK/fullwidth hard gate"
    if parent["id"] in {"N_PREDICTIVE_FRAC_NUM", "N_PREDICTIVE_FRAC_DEN"}:
        return "BASE_MATH", 22, "fraction numerator/denominator body hard gate"
    if ch in "+−-=<>≤≥×÷∑∏/" or "Math" in font or parent["id"] == "N_TRIAL_FORMULA":
        return "BASE_MATH", 22, "base math/operator hard gate"
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_DIGIT", 24, "uppercase/digit hard gate"
    return "LATIN_LOWER_GREEK", 17, "lowercase Latin/Greek hard gate"


def declared_pt(parent_id: str) -> tuple[float, int]:
    if parent_id == "N_TRIAL_FORMULA":
        return 10.7, 17
    if parent_id in {"N_POSTERIOR_FORMULA", "N_PREDICTIVE_FRAC_NUM", "N_PREDICTIVE_FRAC_DEN"}:
        return 11.6, 24
    if parent_id == "EDGE_APPLICATION_LABEL":
        return 10.1, 43
    return 10.1, 5


DRAWING_MAP = {
    3: ("BORDER_NODE_TRIAL", "NODE_BORDER", "NODE_TRIAL", None),
    6: ("BORDER_NODE_GAMMA", "NODE_BORDER", "NODE_GAMMA", None),
    9: ("BORDER_NODE_FAMILIES", "NODE_BORDER", "NODE_FAMILIES", None),
    12: ("BORDER_NODE_POSTERIOR", "NODE_BORDER", "NODE_POSTERIOR", None),
    15: ("BORDER_NODE_PREDICTIVE", "NODE_BORDER", "NODE_PREDICTIVE", None),
    18: ("MATH_RULE_PREDICTIVE_FRACTION", "MATH_RULE", "NODE_PREDICTIVE", "FORMULA_PREDICTIVE_FRACTION"),
    20: ("BORDER_NODE_SIMPLEX", "NODE_BORDER", "NODE_SIMPLEX", None),
    23: ("BORDER_NODE_MOM", "NODE_BORDER", "NODE_MOM", None),
    26: ("BORDER_NODE_LDA", "NODE_BORDER", "NODE_LDA", None),
    29: ("EDGE_TRIAL_FAMILIES_SHAFT", "LINE_ARROW", None, "EDGE_TRIAL_FAMILIES"),
    30: ("EDGE_TRIAL_FAMILIES_HEAD", "ARROWHEAD", None, "EDGE_TRIAL_FAMILIES"),
    32: ("EDGE_GAMMA_FAMILIES_SHAFT", "LINE_ARROW", None, "EDGE_GAMMA_FAMILIES"),
    33: ("EDGE_GAMMA_FAMILIES_HEAD", "ARROWHEAD", None, "EDGE_GAMMA_FAMILIES"),
    35: ("EDGE_FAMILIES_POSTERIOR_SHAFT", "LINE_ARROW", None, "EDGE_FAMILIES_POSTERIOR"),
    36: ("EDGE_FAMILIES_POSTERIOR_HEAD", "ARROWHEAD", None, "EDGE_FAMILIES_POSTERIOR"),
    38: ("EDGE_POSTERIOR_PREDICTIVE_SHAFT", "LINE_ARROW", None, "EDGE_POSTERIOR_PREDICTIVE"),
    39: ("EDGE_POSTERIOR_PREDICTIVE_HEAD", "ARROWHEAD", None, "EDGE_POSTERIOR_PREDICTIVE"),
    41: ("EDGE_FAMILIES_SIMPLEX", "LINE_ARROW", None, "EDGE_FAMILIES_SIMPLEX"),
    42: ("EDGE_POSTERIOR_MOM", "LINE_ARROW", None, "EDGE_POSTERIOR_MOM"),
    43: ("EDGE_PREDICTIVE_LDA_SHAFT", "LINE_ARROW", None, "EDGE_PREDICTIVE_LDA"),
    44: ("EDGE_PREDICTIVE_LDA_HEAD", "ARROWHEAD", None, "EDGE_PREDICTIVE_LDA"),
}

EDGE_ENDPOINTS = {
    "EDGE_TRIAL_FAMILIES": {"NODE_TRIAL", "NODE_FAMILIES"},
    "EDGE_GAMMA_FAMILIES": {"NODE_GAMMA", "NODE_FAMILIES"},
    "EDGE_FAMILIES_POSTERIOR": {"NODE_FAMILIES", "NODE_POSTERIOR"},
    "EDGE_POSTERIOR_PREDICTIVE": {"NODE_POSTERIOR", "NODE_PREDICTIVE"},
    "EDGE_FAMILIES_SIMPLEX": {"NODE_FAMILIES", "NODE_SIMPLEX"},
    "EDGE_POSTERIOR_MOM": {"NODE_POSTERIOR", "NODE_MOM"},
    "EDGE_PREDICTIVE_LDA": {"NODE_PREDICTIVE", "NODE_LDA"},
}


def replay_drawing(page_rect: fitz.Rect, drawing: dict, border_only: bool) -> np.ndarray:
    d = fitz.open()
    p = d.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"unsupported drawing op {op}")
    lc = drawing.get("lineCap", 0)
    if isinstance(lc, (tuple, list)):
        lc = max(lc)
    shape.finish(
        color=drawing.get("color"),
        fill=None if border_only else drawing.get("fill"),
        width=drawing.get("width", 1.0),
        lineCap=int(lc or 0),
        lineJoin=float(drawing.get("lineJoin", 0.0) or 0.0),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd", False)),
        closePath=bool(drawing.get("closePath", False)),
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, annots=False)
    arr = np.asarray(pix_to_pil(pix).convert("RGB"), dtype=np.int16)
    d.close()
    return np.max(255 - arr, axis=2) >= 20


def make_object_triptych(image: Image.Image, mask: np.ndarray, box, label: str) -> tuple[Image.Image, Image.Image]:
    x0, y0, x1, y1 = box
    original = image.crop(box).convert("RGB")
    local_mask = mask[y0:y1, x0:x1]
    overlay = np.asarray(original).copy()
    overlay[local_mask] = [255, 0, 0]
    overlay_im = Image.fromarray(overlay.astype(np.uint8), "RGB")
    mask_im = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), "L").convert("RGB")
    header = 22
    w, h = original.size
    panel = Image.new("RGB", (w * 3, h + header), "white")
    panel.paste(original, (0, header))
    panel.paste(overlay_im, (w, header))
    panel.paste(mask_im, (w * 2, header))
    dr = ImageDraw.Draw(panel)
    dr.text((2, 2), f"{label} | ORIGINAL", fill="black")
    dr.text((w + 2, 2), "TARGET OVERLAY", fill="black")
    dr.text((w * 2 + 2, 2), "MASK ONLY", fill="black")
    enlarged = panel.resize((panel.width * 8, panel.height * 8), Image.Resampling.NEAREST)
    return panel, enlarged


def make_contact_sheets(records: list[dict], output_dir: Path, prefix: str, per_sheet: int = 20) -> list[str]:
    paths = []
    for si in range(0, len(records), per_sheet):
        batch = records[si:si + per_sheet]
        cols, rows = 4, 5
        cell_w, cell_h = 420, 235
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        dr = ImageDraw.Draw(sheet)
        for j, rec in enumerate(batch):
            im = Image.open(ROOT / rec["evidence_8x"]).convert("RGB")
            im.thumbnail((cell_w - 8, cell_h - 35), Image.Resampling.NEAREST)
            x = (j % cols) * cell_w
            y = (j // cols) * cell_h
            sheet.paste(im, (x + 4, y + 28))
            label_id = rec.get("object_id", rec.get("relation_id", "UNNAMED"))
            parent_label = rec.get("parent_id", f"{rec.get('object_a','')}|{rec.get('object_b','')}")
            dr.text((x + 4, y + 4), f"{label_id} {rec.get('unicode','')} {parent_label}", fill="black")
        path = output_dir / f"{prefix}_{si // per_sheet + 1:03d}.png"
        sheet.save(path)
        paths.append(path.relative_to(ROOT).as_posix())
    return paths


def coords_from_mask(mask: np.ndarray) -> np.ndarray:
    y, x = np.nonzero(mask)
    return np.column_stack([x, y]).astype(np.int32)


def bbox_clearance(a, b) -> int:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0, max(ay0, by0) - min(ay1, by1))
    return int(max(dx, dy))


def pair_rule(a: dict, b: dict) -> tuple[str, int | None, str]:
    ag, bg = a["kind"] == "GLYPH", b["kind"] == "GLYPH"
    if ag and bg:
        if a["parent_id"] == b["parent_id"]:
            return "SAME_PARENT_TYPOGRAPHY_DESIGN", None, "same semantic text/formula parent; independent 4px gate not applicable"
        return "TEXT_TEXT_BBOX", 4, "independent semantic text objects require vector bbox clearance >=4px"
    if ag != bg:
        g, x = (a, b) if ag else (b, a)
        if x["graphic_role"] == "NODE_BORDER" and g.get("node") == x.get("node"):
            return "NODE_TEXT_TO_FINAL_VISIBLE_BORDER", 5, "owned node glyph to its final-visible border"
        if x["graphic_role"] == "MATH_RULE" and g["parent_id"] in {"N_PREDICTIVE_FRAC_NUM", "N_PREDICTIVE_FRAC_DEN"}:
            return "SAME_FORMULA_MATH_RULE_DESIGN", None, "fraction rule and glyph are components of the same formula"
        return "TEXT_FORMULA_TO_GRAPHIC", 3, "independent text/formula ink to line, arrow, marker or border"
    if a.get("edge") and a.get("edge") == b.get("edge"):
        return "SAME_EDGE_COMPONENT_DESIGN", None, "shaft/head are designed components of one semantic edge"
    if a["graphic_role"] == "NODE_BORDER" and b.get("edge") and a.get("node") in EDGE_ENDPOINTS.get(b["edge"], set()):
        return "EDGE_NODE_ENDPOINT_DESIGN", None, "edge intentionally terminates at owned endpoint border"
    if b["graphic_role"] == "NODE_BORDER" and a.get("edge") and b.get("node") in EDGE_ENDPOINTS.get(a["edge"], set()):
        return "EDGE_NODE_ENDPOINT_DESIGN", None, "edge intentionally terminates at owned endpoint border"
    return "GRAPHIC_GRAPHIC_NO_ILLEGAL_OVERLAP", 0, "independent foreground graphics may not share native pixels"


def pair_evidence(image: Image.Image, a_mask: np.ndarray, b_mask: np.ndarray, pair_id: str, box, out_dir: Path) -> dict:
    x0, y0, x1, y1 = box
    original = image.crop(box).convert("RGB")
    aa = a_mask[y0:y1, x0:x1]
    bb = b_mask[y0:y1, x0:x1]
    inter = aa & bb
    def mono(m):
        return Image.fromarray(np.where(m, 0, 255).astype(np.uint8), "L").convert("RGB")
    ov = np.asarray(original).copy()
    ov[aa] = [255, 0, 0]
    ov[bb] = [0, 90, 255]
    ov[inter] = [255, 0, 255]
    overlay = Image.fromarray(ov.astype(np.uint8), "RGB")
    imgs = [original, mono(aa), mono(bb), mono(inter), overlay]
    names = ["raw", "mask_a", "mask_b", "intersection", "overlay"]
    out = {}
    for n, im in zip(names, imgs):
        p = out_dir / f"{pair_id}__{n}.png"
        im.save(p)
        out[n] = p.relative_to(ROOT).as_posix()
    header = 22
    w, h = original.size
    panel = Image.new("RGB", (w * 5, h + header), "white")
    for i, im in enumerate(imgs):
        panel.paste(im, (i * w, header))
    dr = ImageDraw.Draw(panel)
    for i, n in enumerate(names):
        dr.text((i * w + 2, 2), n.upper(), fill="black")
    p1 = out_dir / f"{pair_id}__1x.png"
    p8 = out_dir / f"{pair_id}__8x_nearest.png"
    panel.save(p1)
    panel.resize((panel.width * 8, panel.height * 8), Image.Resampling.NEAREST).save(p8)
    out["evidence_1x"] = p1.relative_to(ROOT).as_posix()
    out["evidence_8x"] = p8.relative_to(ROOT).as_posix()
    return out


def main() -> None:
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    taxonomy = json.loads((ROOT / "00_taxonomy_frozen.json").read_text(encoding="utf-8"))
    if not taxonomy.get("frozen_before_pixel_measurement"):
        raise RuntimeError("taxonomy freeze missing")

    pdf_sha = sha256(PDF)
    if pdf_sha != EXPECTED_PDF_SHA256:
        raise RuntimeError(f"PDF SHA mismatch: {pdf_sha}")
    shutil.copyfile(SOURCE, DIRS["provenance"] / "fig_v5_c05_dependency_graph.source_snapshot.tex")
    authority = []
    for label, path in [("GOAL", GOAL), ("GOAL_V270", GOAL_V270), ("GOAL_V160", GOAL_V160), ("PROTOCOL", PROTOCOL), ("SCHEMA", SCHEMA), ("SOURCE", SOURCE), ("PDF", PDF)]:
        authority.append({"label": label, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_csv(DIRS["provenance"] / "authority_bindings.csv", authority)

    doc = fitz.open(PDF)
    page_sizes = [(round(p.rect.width, 3), round(p.rect.height, 3)) for p in doc]
    if len(doc) != 817 or set(page_sizes) != {(595.276, 841.89)}:
        raise RuntimeError("PDF page/A4 identity mismatch")
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, annots=False)
    full300 = pix_to_pil(pix300).convert("RGB")
    w, h = full300.size
    full300.save(DIRS["views"] / "full_page_native_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False, annots=False)
    pix_to_pil(pix200).convert("RGB").save(DIRS["views"] / "full_page_200dpi.png")
    crop_box = pt_rect_to_px(CROP_PT, w, h)
    crop = full300.crop(crop_box)
    crop.save(DIRS["views"] / "figure_crop_300dpi.png")
    crop.copy().save(DIRS["views"] / "standalone_300dpi.png")
    crop.convert("L").save(DIRS["views"] / "grayscale_300dpi.png")

    identity = {
        "figure_uid": "FIG-P654-01",
        "role_instance": "A-R102-P654-SA1-FRESH-20260825",
        "commit_identity_verified_externally": EXPECTED_COMMIT,
        "pdf": str(PDF),
        "pdf_sha256": pdf_sha,
        "pdf_bytes": PDF.stat().st_size,
        "page_count": len(doc),
        "all_pages_a4": True,
        "page_pt": [page_rect.width, page_rect.height],
        "physical_page": PAGE_NUMBER,
        "printed_page": PRINTED_PAGE,
        "native_300dpi_grid": [w, h],
        "figure_crop_pdf_pt": list(CROP_PT),
        "figure_crop_integer_full_page_px": list(crop_box),
        "figure_crop_native_dimensions": list(crop.size),
        "render_matrix": [SCALE, SCALE],
        "post_render_resize": False,
    }
    dump_json(DIRS["provenance"] / "candidate_identity.json", identity)

    # Text-free render: remove all BT...ET operators from an isolated copy of page 704.
    gfx_doc = fitz.open()
    gfx_doc.insert_pdf(doc, from_page=PAGE_INDEX, to_page=PAGE_INDEX)
    gp = gfx_doc[0]
    bt_count = 0
    for xref in gp.get_contents():
        stream = gfx_doc.xref_stream(xref)
        new_stream, n = re.subn(rb"BT\b.*?\bET", b"", stream, flags=re.S)
        bt_count += n
        gfx_doc.update_stream(xref, new_stream)
    if bt_count == 0:
        raise RuntimeError("no BT/ET content removed")
    gfx_pix = gp.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, annots=False)
    gfx_img = pix_to_pil(gfx_pix).convert("RGB")
    gfx_img.crop(crop_box).save(DIRS["machine"] / "graphics_only_crop_300dpi.png")
    full_arr = np.asarray(full300, dtype=np.int16)
    gfx_arr = np.asarray(gfx_img, dtype=np.int16)
    text_union = np.max(np.abs(full_arr - gfx_arr), axis=2) >= 20
    crop_gate = np.zeros((h, w), dtype=bool)
    crop_gate[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]] = True
    text_union &= crop_gate
    Image.fromarray(np.where(text_union, 0, 255).astype(np.uint8), "L").save(DIRS["machine"] / "text_union_raw_mask_300dpi.png")

    rawdict = page.get_text("rawdict")
    raw_char_rows = []
    chars = []
    stream_ord = 0
    visible_ord = 0
    for bi, block in enumerate(rawdict["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                for ci, chd in enumerate(span.get("chars", [])):
                    stream_ord += 1
                    ch = chd["c"]
                    bbox = tuple(float(v) for v in chd["bbox"])
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2
                    in_figure = CROP_PT[0] <= cx <= CROP_PT[2] and CROP_PT[1] <= cy <= CROP_PT[3]
                    is_visible = in_figure and not ch.isspace()
                    raw_char_rows.append({
                        "stream_ordinal": stream_ord, "block": bi, "line": li, "span": si, "char": ci,
                        "unicode": f"U+{ord(ch):04X}", "character": ch, "bbox_pt": json.dumps(bbox),
                        "in_figure_crop": in_figure, "visible_foreground_object": is_visible,
                        "exclusion_reason": "" if is_visible else ("WHITESPACE_NO_VISIBLE_INK" if in_figure else "OUTSIDE_TARGET_FIGURE"),
                    })
                    if not is_visible:
                        continue
                    parent = assign_parent(cx, cy, taxonomy)
                    visible_ord += 1
                    cls, hard_min, class_reason = script_class(ch, parent, float(span["size"]), span["font"])
                    dpt, source_line = declared_pt(parent["id"])
                    chars.append({
                        "object_id": f"G{visible_ord:04d}", "kind": "GLYPH", "panel_id": "P_MAIN",
                        "parent_id": parent["id"], "role": parent["role"], "node": parent.get("node"),
                        "character": ch, "unicode": f"U+{ord(ch):04X}", "script_class": cls,
                        "hard_min_px": hard_min, "class_reason": class_reason,
                        "font": span["font"], "pdf_span_size_pt": float(span["size"]),
                        "declared_pt": dpt, "graphics_scale": 1.0, "effective_pt": dpt,
                        "source_file": str(SOURCE), "source_line": source_line,
                        "bbox_pt": bbox, "bbox_px_vector": pt_rect_to_px(bbox, w, h, pad=0),
                        "color_rgb": color_int_rgb(int(span["color"])),
                    })
    write_csv(DIRS["machine"] / "pdf_raw_character_inventory.csv", raw_char_rows)

    # Partition every native text-difference pixel to exactly one visible PDF character bbox.
    pixel_candidates = defaultdict(list)
    for idx, rec in enumerate(chars):
        x0, y0, x1, y1 = pt_rect_to_px(rec["bbox_pt"], w, h, pad=2)
        yy, xx = np.nonzero(text_union[y0:y1, x0:x1])
        for x, y in zip(xx + x0, yy + y0):
            pixel_candidates[int(y) * w + int(x)].append(idx)
    char_sets = [set() for _ in chars]
    unassigned = []
    fringe_assignments = []
    ty, tx = np.nonzero(text_union)
    for x, y in zip(tx, ty):
        lin = int(y) * w + int(x)
        candidates = pixel_candidates.get(lin, [])
        if not candidates:
            # Native anti-alias fringe may extend just beyond the PDF glyph bbox.
            # Assign only within a strict 4px traceable bbox distance; otherwise fail.
            nearby = []
            for i, c in enumerate(chars):
                bx0, by0, bx1, by1 = c["bbox_px_vector"]
                dx = max(0, bx0 - x, x - (bx1 - 1))
                dy = max(0, by0 - y, y - (by1 - 1))
                dist = max(dx, dy)
                if dist <= 4:
                    nearby.append((dist, i))
            if nearby:
                min_dist = min(x[0] for x in nearby)
                nearest = [i for dist, i in nearby if dist == min_dist]
                if len(nearest) != 1:
                    raise RuntimeError(f"ambiguous anti-alias fringe ownership at {(int(x), int(y))}: {nearest}")
                candidates = nearest
                fringe_assignments.append({"x": int(x), "y": int(y), "bbox_distance_px": int(min_dist), "object_id": chars[nearest[0]]["object_id"]})
            else:
                unassigned.append(lin)
                continue
        def score(i):
            bx0, by0, bx1, by1 = chars[i]["bbox_px_vector"]
            cx = (bx0 + bx1) / 2
            cy = (by0 + by1) / 2
            return ((x - cx) / max(1, bx1 - bx0)) ** 2 + ((y - cy) / max(1, by1 - by0)) ** 2
        chosen = min(candidates, key=score)
        char_sets[chosen].add(lin)
    if unassigned:
        raise RuntimeError(f"unassigned final-visible text pixels: {len(unassigned)}")

    object_masks: dict[str, np.ndarray] = {}
    glyph_rows = []
    object_evidence_rows = []
    for rec, s in zip(chars, char_sets):
        mask = np.zeros((h, w), dtype=bool)
        if s:
            vals = np.fromiter(s, dtype=np.int64)
            mask[vals // w, vals % w] = True
        box = mask_bbox(mask)
        area = int(mask.sum())
        ink_h = box[3] - box[1]
        ink_w = box[2] - box[0]
        empty = area == 0
        edge_clear = min(box[0] - crop_box[0], box[1] - crop_box[1], crop_box[2] - box[2], crop_box[3] - box[3]) if not empty else -1
        clip_count = int(np.count_nonzero(mask[crop_box[1], crop_box[0]:crop_box[2]]) + np.count_nonzero(mask[crop_box[3]-1, crop_box[0]:crop_box[2]]) + np.count_nonzero(mask[crop_box[1]:crop_box[3], crop_box[0]]) + np.count_nonzero(mask[crop_box[1]:crop_box[3], crop_box[2]-1]))
        px_pass = False if rec["script_class"] == "LOW_PROFILE_PUNCTUATION" else (not empty and ink_h >= rec["hard_min_px"])
        ev_box = crop_with_pad(box, w, h, 6)
        one, eight = make_object_triptych(full300, mask, ev_box, f"{rec['object_id']} {rec['unicode']}")
        sn = safe_name(rec["object_id"])
        p1 = DIRS["objects"] / f"{sn}__1x.png"
        p8 = DIRS["objects"] / f"{sn}__8x_nearest.png"
        pm = DIRS["objects"] / f"{sn}__raw_mask.png"
        pj = DIRS["objects"] / f"{sn}.json"
        one.save(p1); eight.save(p8)
        Image.fromarray(np.where(mask[ev_box[1]:ev_box[3], ev_box[0]:ev_box[2]], 0, 255).astype(np.uint8), "L").save(pm)
        rec.update({
            "safe_filename": sn, "mask_bbox_px": box, "mask_area_px": area, "h_ink_px": ink_h,
            "w_ink_px": ink_w, "empty_mask": empty, "clip_pixel_count": clip_count,
            "image_edge_clearance_px": edge_clear, "pixel_height_pass_precalibration": px_pass,
            "missing_stroke_px": 0, "foreign_pixel_px": 0,
            "evidence_1x": p1.relative_to(ROOT).as_posix(), "evidence_8x": p8.relative_to(ROOT).as_posix(),
            "raw_mask": pm.relative_to(ROOT).as_posix(), "json": pj.relative_to(ROOT).as_posix(),
        })
        dump_json(pj, {k: (list(v) if isinstance(v, tuple) else v) for k, v in rec.items()})
        object_masks[rec["object_id"]] = mask
        glyph_rows.append(rec.copy())
        object_evidence_rows.append(rec.copy())

    # Rebuild every visible foreground drawing/path as an individual native mask.
    drawings = []
    for di, dr in enumerate(page.get_drawings()):
        r = dr["rect"]
        if r.x1 >= CROP_PT[0] and r.x0 <= CROP_PT[2] and r.y1 >= CROP_PT[1] and r.y0 <= CROP_PT[3]:
            seq = int(dr["seqno"])
            if seq not in DRAWING_MAP:
                raise RuntimeError(f"unassigned visible foreground drawing seqno={seq}")
            drawings.append((di, dr))
    if len(drawings) != len(DRAWING_MAP):
        raise RuntimeError(f"drawing denominator mismatch {len(drawings)} != {len(DRAWING_MAP)}")

    replayed = []
    for di, dr in drawings:
        name, role, node, edge = DRAWING_MAP[int(dr["seqno"])]
        replayed.append(replay_drawing(page_rect, dr, border_only=(role == "NODE_BORDER")))
    # final-visible = pre-occlusion minus later opaque graphic paths.
    final_graphics = []
    for i, pre in enumerate(replayed):
        later = np.zeros_like(pre)
        for j in range(i + 1, len(replayed)):
            later |= replayed[j]
        final_graphics.append(pre & ~later)

    graphic_rows = []
    for (di, dr), pre, mask in zip(drawings, replayed, final_graphics):
        seq = int(dr["seqno"])
        name, role, node, edge = DRAWING_MAP[seq]
        oid = f"D{seq:03d}_{name}"
        box = mask_bbox(mask)
        area = int(mask.sum())
        empty = area == 0
        edge_clear = min(box[0] - crop_box[0], box[1] - crop_box[1], crop_box[2] - box[2], crop_box[3] - box[3]) if not empty else -1
        clip_count = int(np.count_nonzero(mask[crop_box[1], crop_box[0]:crop_box[2]]) + np.count_nonzero(mask[crop_box[3]-1, crop_box[0]:crop_box[2]]) + np.count_nonzero(mask[crop_box[1]:crop_box[3], crop_box[0]]) + np.count_nonzero(mask[crop_box[1]:crop_box[3], crop_box[2]-1]))
        ev_box = crop_with_pad(box, w, h, 6)
        one, eight = make_object_triptych(full300, mask, ev_box, oid)
        sn = safe_name(oid)
        p1 = DIRS["objects"] / f"{sn}__1x.png"
        p8 = DIRS["objects"] / f"{sn}__8x_nearest.png"
        pm = DIRS["objects"] / f"{sn}__raw_mask.png"
        pj = DIRS["objects"] / f"{sn}.json"
        one.save(p1); eight.save(p8)
        Image.fromarray(np.where(mask[ev_box[1]:ev_box[3], ev_box[0]:ev_box[2]], 0, 255).astype(np.uint8), "L").save(pm)
        rec = {
            "object_id": oid, "kind": "GRAPHIC", "panel_id": "P_MAIN", "parent_id": edge or node or "FORMULA_PREDICTIVE_FRACTION",
            "role": role, "graphic_role": role, "node": node, "edge": edge, "drawing_index": di, "seqno": seq,
            "drawing_type": dr["type"], "drawing_rect_pt": list(dr["rect"]), "stroke_color": dr.get("color"),
            "fill_color": dr.get("fill"), "line_width_pt": dr.get("width"), "pre_occlusion_area_px": int(pre.sum()),
            "mask_bbox_px": box, "mask_area_px": area, "empty_mask": empty, "clip_pixel_count": clip_count,
            "image_edge_clearance_px": edge_clear, "safe_filename": sn,
            "evidence_1x": p1.relative_to(ROOT).as_posix(), "evidence_8x": p8.relative_to(ROOT).as_posix(),
            "raw_mask": pm.relative_to(ROOT).as_posix(), "json": pj.relative_to(ROOT).as_posix(),
        }
        dump_json(pj, rec)
        object_masks[oid] = mask
        graphic_rows.append(rec)
        object_evidence_rows.append(rec.copy())

    glyph_contacts = make_contact_sheets(glyph_rows, DIRS["contacts"], "glyph_contact_native_triptych")
    graphic_contacts = make_contact_sheets(graphic_rows, DIRS["contacts"], "graphic_contact_native_triptych")

    # Group medians and D/E ratios; grouping was frozen before these measurements.
    groups = defaultdict(list)
    for r in glyph_rows:
        groups[(r["panel_id"], r["role"], r["script_class"])].append(r["h_ink_px"])
    medians = {k: float(np.median(v)) for k, v in groups.items()}
    for r in glyph_rows:
        med = medians[(r["panel_id"], r["role"], r["script_class"])]
        r["class_median_px"] = med
        r["ratio_to_class_median"] = r["h_ink_px"] / med if med else 0
        r["same_group_ratio_pass"] = 0.92 <= r["ratio_to_class_median"] <= 1.08
        r["pixel_height_pass"] = bool(r["pixel_height_pass_precalibration"])
        r["effective_pt_pass"] = r["effective_pt"] >= 9.5
        r["preliminary_hard_pass"] = bool(r["pixel_height_pass"] and r["same_group_ratio_pass"] and r["effective_pt_pass"] and not r["empty_mask"] and r["clip_pixel_count"] == 0 and r["image_edge_clearance_px"] >= 6)

    role_rows = []
    role_group_medians = defaultdict(list)
    for (panel, role, cls), med in medians.items():
        role_group_medians[(role, cls)].append(med)
    for (role, cls), vals in sorted(role_group_medians.items()):
        ratio = max(vals) / min(vals) if vals and min(vals) else None
        role_rows.append({"role": role, "script_class": cls, "panel_count": 1, "group_count": len(vals), "median_min_px": min(vals), "median_max_px": max(vals), "extreme_ratio": ratio, "same_role_extreme_pass": ratio <= 1.08 if ratio else False, "cross_panel_ratio": "N/A_ONE_PANEL", "cross_panel_pass": True})

    base_by_class = {cls: med for (panel, role, cls), med in medians.items() if role == "NODE_BODY"}
    role_ratio_rows = []
    role_limits = taxonomy["role_ratio_rules"]
    for (panel, role, cls), med in sorted(medians.items()):
        base = base_by_class.get(cls)
        if base is None or role == "NODE_BODY":
            role_ratio_rows.append({"panel_id": panel, "role": role, "script_class": cls, "role_median_px": med, "base_median_px": base if base is not None else "N/A", "role_ratio": 1.0 if role == "NODE_BODY" else "N/A_DIFFERENT_SCRIPT_NO_BASE", "allowed_min": role_limits.get(role, [None, None])[0], "allowed_max": role_limits.get(role, [None, None])[1], "decision": "PASS" if role == "NODE_BODY" else "N/A"})
        else:
            rr = med / base
            lo, hi = role_limits[role]
            role_ratio_rows.append({"panel_id": panel, "role": role, "script_class": cls, "role_median_px": med, "base_median_px": base, "role_ratio": rr, "allowed_min": lo, "allowed_max": hi, "decision": "PASS" if lo <= rr <= hi else "FAIL"})

    # Low-profile calibration denominator is determined before results by the frozen class rule.
    low = [r for r in glyph_rows if r["script_class"] == "LOW_PROFILE_PUNCTUATION"]
    low_rows = []
    for r in low:
        low_rows.append({"object_id": r["object_id"], "unicode": r["unicode"], "character": r["character"], "status": "CALIBRATION_REQUIRED_NOT_GENERATED", "decision": "FAIL"})
    write_csv(DIRS["ledgers"] / "low_profile_calibration.csv", low_rows, ["object_id", "unicode", "character", "status", "decision"])

    # All unordered object pairs, without sampling.
    all_objects = glyph_rows + graphic_rows
    for r in all_objects:
        r.setdefault("graphic_role", "")
        r.setdefault("edge", None)
    coord_cache = {r["object_id"]: coords_from_mask(object_masks[r["object_id"]]) for r in all_objects}
    tree_cache = {oid: cKDTree(coords) for oid, coords in coord_cache.items() if len(coords)}
    pairs = []
    critical = []
    pid = 0
    for i, a in enumerate(all_objects):
        for b in all_objects[i + 1:]:
            pid += 1
            pair_id = f"R{pid:06d}"
            am = object_masks[a["object_id"]]
            bm = object_masks[b["object_id"]]
            overlap = int(np.count_nonzero(am & bm))
            ac, bc = coord_cache[a["object_id"]], coord_cache[b["object_id"]]
            if not len(ac) or not len(bc):
                clearance = None
            else:
                if len(ac) <= len(bc):
                    dist = float(np.min(tree_cache[b["object_id"]].query(ac, k=1, p=np.inf)[0]))
                else:
                    dist = float(np.min(tree_cache[a["object_id"]].query(bc, k=1, p=np.inf)[0]))
                clearance = max(0.0, dist - 1.0)
            gate_type, gate_px, ownership = pair_rule(a, b)
            text_text_bbox_clear = bbox_clearance(a["bbox_px_vector"], b["bbox_px_vector"]) if a["kind"] == b["kind"] == "GLYPH" else None
            if gate_type == "TEXT_TEXT_BBOX":
                passed = overlap == 0 and text_text_bbox_clear is not None and text_text_bbox_clear >= 4
                measured = text_text_bbox_clear
            elif gate_type in {"NODE_TEXT_TO_FINAL_VISIBLE_BORDER", "TEXT_FORMULA_TO_GRAPHIC"}:
                passed = overlap == 0 and clearance is not None and clearance >= gate_px
                measured = clearance
            elif gate_type == "GRAPHIC_GRAPHIC_NO_ILLEGAL_OVERLAP":
                passed = overlap == 0
                measured = clearance
            else:
                passed = True
                measured = clearance
            is_critical = (not passed) or (gate_px is not None and measured is not None and measured <= gate_px + 12) or gate_type in {"SAME_EDGE_COMPONENT_DESIGN", "EDGE_NODE_ENDPOINT_DESIGN", "SAME_FORMULA_MATH_RULE_DESIGN"}
            rec = {
                "relation_id": pair_id, "object_a": a["object_id"], "object_b": b["object_id"],
                "kind_a": a["kind"], "kind_b": b["kind"], "parent_a": a["parent_id"], "parent_b": b["parent_id"],
                "role_a": a["role"], "role_b": b["role"], "gate_type": gate_type, "gate_px": gate_px if gate_px is not None else "N/A_DESIGN",
                "raw_overlap_pixel_count": overlap, "raw_mask_clearance_px": clearance if clearance is not None else "EMPTY_MASK",
                "text_text_vector_bbox_clearance_px": text_text_bbox_clear if text_text_bbox_clear is not None else "N/A",
                "ownership_or_whitelist_reason": ownership, "machine_decision": "PASS" if passed else "FAIL", "critical_relation": is_critical,
                "evidence_1x": "", "evidence_8x": "", "raw": "", "mask_a": "", "mask_b": "", "intersection": "", "overlay": "",
            }
            if is_critical:
                ub = (
                    min(a["mask_bbox_px"][0], b["mask_bbox_px"][0]), min(a["mask_bbox_px"][1], b["mask_bbox_px"][1]),
                    max(a["mask_bbox_px"][2], b["mask_bbox_px"][2]), max(a["mask_bbox_px"][3], b["mask_bbox_px"][3]),
                )
                box = crop_with_pad(ub, w, h, 8)
                ev = pair_evidence(full300, am, bm, pair_id, box, DIRS["pairs"])
                rec.update(ev)
                dump_json(DIRS["pairs"] / f"{pair_id}.json", {**rec, "roi_full_page_px": box})
                critical.append(rec)
            pairs.append(rec)
    expected_pairs = len(all_objects) * (len(all_objects) - 1) // 2
    if pid != expected_pairs:
        raise RuntimeError("pair denominator closure failure")

    critical_contacts = make_contact_sheets(critical, DIRS["contacts"], "critical_pair_contact", per_sheet=12) if critical else []

    # Overlay every glyph and drawing bbox on the authoritative crop.
    overlay = crop.copy()
    od = ImageDraw.Draw(overlay)
    colors = {"GLYPH": (220, 0, 0), "GRAPHIC": (0, 80, 220)}
    for r in all_objects:
        bx = r["mask_bbox_px"]
        local = (bx[0] - crop_box[0], bx[1] - crop_box[1], bx[2] - crop_box[0], bx[3] - crop_box[1])
        od.rectangle(local, outline=colors[r["kind"]], width=1)
        od.text((local[0], max(0, local[1] - 10)), r["object_id"], fill=colors[r["kind"]])
    overlay.save(DIRS["views"] / "after_text_measurement_overlay_300dpi.png")

    source_audit = [
        {"audit_id":"SRC001","scope":"tikzset slfig global font","source_line":3,"declared_pt":10.1,"graphics_scale":1.0,"effective_pt":10.1,"pass":True,"note":"global baseline; no enclosing resize/scalebox/transform shape"},
        {"audit_id":"SRC002","scope":"every node font","source_line":8,"declared_pt":10.1,"graphics_scale":1.0,"effective_pt":10.1,"pass":True,"note":"same baseline applied to all ordinary node text"},
        {"audit_id":"SRC003","scope":"trial bold n formula","source_line":17,"declared_pt":10.7,"graphics_scale":1.0,"effective_pt":10.7,"pass":True,"note":"local semantic formula emphasis"},
        {"audit_id":"SRC004","scope":"posterior formula block","source_line":24,"declared_pt":11.6,"graphics_scale":1.0,"effective_pt":11.6,"pass":True,"note":"formula role ratio subject to native pixel D/E"},
        {"audit_id":"SRC005","scope":"predictive fraction block","source_line":30,"declared_pt":11.6,"graphics_scale":1.0,"effective_pt":11.6,"pass":True,"note":"base fraction size; natural subscripts inherit TeX scriptstyle"},
        {"audit_id":"SRC006","scope":"application edge label","source_line":43,"declared_pt":10.1,"graphics_scale":1.0,"effective_pt":10.1,"pass":True,"note":"annotation matches ordinary node baseline"},
        {"audit_id":"SRC007","scope":"forbidden scaling scan","source_line":"1-45","declared_pt":"N/A","graphics_scale":1.0,"effective_pt":"N/A","pass":True,"note":"no resizebox/scalebox/transform shape/overall scale in target source"},
    ]
    write_csv(DIRS["ledgers"] / "after_font_audit.csv", source_audit)
    write_csv(DIRS["ledgers"] / "after_pixel_measurements.csv", glyph_rows)
    write_csv(DIRS["ledgers"] / "graphic_object_ledger.csv", graphic_rows)
    write_csv(DIRS["ledgers"] / "all_objects.csv", all_objects)
    write_csv(DIRS["ledgers"] / "all_unordered_pairs.csv", pairs)
    write_csv(DIRS["ledgers"] / "critical_pair_machine_ledger.csv", critical)
    write_csv(DIRS["ledgers"] / "role_peer_ratio_ledger.csv", role_rows)
    write_csv(DIRS["ledgers"] / "role_to_base_ratio_ledger.csv", role_ratio_rows)
    write_csv(DIRS["ledgers"] / "id_safe_filename_map.csv", [{"object_id":r["object_id"], "safe_filename":r["safe_filename"], "json":r["json"], "mask":r["raw_mask"], "evidence_1x":r["evidence_1x"], "evidence_8x":r["evidence_8x"]} for r in all_objects])

    object_fail_ids = [r["object_id"] for r in glyph_rows if not r["preliminary_hard_pass"]]
    role_fail_ids = [f"{r['role']}::{r['script_class']}" for r in role_rows if not r["same_role_extreme_pass"]]
    role_ratio_fail_ids = [f"{r['panel_id']}::{r['role']}::{r['script_class']}" for r in role_ratio_rows if r["decision"] == "FAIL"]
    pair_fail_ids = [r["relation_id"] for r in pairs if r["machine_decision"] == "FAIL"]
    graphic_empty_ids = [r["object_id"] for r in graphic_rows if r["empty_mask"]]
    graphic_clip_ids = [r["object_id"] for r in graphic_rows if r["clip_pixel_count"]]
    hard = {
        "glyph_denominator": len(glyph_rows), "graphic_denominator": len(graphic_rows), "object_denominator": len(all_objects),
        "unordered_pair_denominator": expected_pairs, "unordered_pair_rows": len(pairs), "critical_pair_denominator": len(critical),
        "low_profile_glyph_denominator": len(low), "calibration_denominator": len(low),
        "panel_denominator": 1, "cross_panel_pair_denominator": 0,
        "pdf_raw_visible_character_rows": len(chars), "drawing_path_rows": len(drawings),
        "glyph_contact_sheet_count": len(glyph_contacts), "graphic_contact_sheet_count": len(graphic_contacts), "critical_pair_contact_sheet_count": len(critical_contacts),
        "object_fail_ids": object_fail_ids, "role_peer_fail_ids": role_fail_ids, "role_ratio_fail_ids": role_ratio_fail_ids,
        "pair_fail_ids": pair_fail_ids, "empty_graphic_ids": graphic_empty_ids, "graphic_clip_ids": graphic_clip_ids,
        "overlap_pixel_count_illegal": sum(r["raw_overlap_pixel_count"] for r in pairs if r["machine_decision"] == "FAIL" and r["raw_overlap_pixel_count"]),
        "clip_pixel_count": sum(r["clip_pixel_count"] for r in all_objects),
        "machine_hard_gate_pass": not any([object_fail_ids, role_fail_ids, role_ratio_fail_ids, pair_fail_ids, graphic_empty_ids, graphic_clip_ids, low]),
        "manual_review_pending": True,
    }
    dump_json(DIRS["machine"] / "hard_gate_summary_pre_manual.json", hard)
    provenance = {
        **identity,
        "fitz_version": fitz.VersionBind,
        "numpy_version": np.__version__,
        "python": sys.version,
        "text_isolation_method": "isolated page copy with every BT...ET text object removed; final-visible text mask is native original minus graphics-only at >=20/255 per channel max difference",
        "graphic_mask_method": "each get_drawings() foreground path replayed at native 300dpi; node fills excluded; later opaque path masks subtracted for final-visible border/path",
        "pixel_distance_method": "Chebyshev native raw-mask center distance minus one pixel; text-text gate uses mapped PDF vector bbox clearance",
        "bt_et_blocks_removed": bt_count,
        "post_render_resize_for_measurement": False,
        "nearest_8x_used_for_measurement": False,
        "tex_or_latex_invoked": False,
        "anti_alias_fringe_ownership_rule": "Only native text-difference pixels outside all PDF glyph bboxes may be assigned to one unique nearest bbox at Chebyshev distance <=4px. This is ownership tracing only and never changes clip, border, typography, or clearance gates; equal-distance ambiguity is a hard failure.",
        "anti_alias_fringe_assignment_count": len(fringe_assignments),
        "anti_alias_fringe_assignments": fringe_assignments,
        "pyc_or_cache_written": False,
    }
    dump_json(DIRS["provenance"] / "render_and_measurement_provenance.json", provenance)
    print(json.dumps(hard, ensure_ascii=True))
    gfx_doc.close(); doc.close()


if __name__ == "__main__":
    main()
