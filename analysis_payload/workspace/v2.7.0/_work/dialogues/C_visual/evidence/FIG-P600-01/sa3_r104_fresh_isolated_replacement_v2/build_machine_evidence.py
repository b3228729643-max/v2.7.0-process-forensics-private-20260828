from __future__ import annotations

import csv
import json
import math
import os
import re
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
PHYSICAL_PAGE = 651
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0
FIGURE_CROP_PX = (217, 1867, 2217, 2755)  # x0,y0,x1,y1; direct Poppler crop already materialized
STANDALONE_CROP_PX = (500, 1875, 1935, 2615)


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rect_union(rects):
    rects = [tuple(map(float, r)) for r in rects]
    return (
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    )


def pt_rect_to_px(rect):
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def mask_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def crop_pad(box, width, height, pad=10):
    x0, y0, x1, y1 = box
    return max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad)


def color_contrast_mask(arr: np.ndarray, box, threshold=20):
    x0, y0, x1, y1 = box
    tile = arr[y0:y1, x0:x1].astype(np.int16)
    if tile.size == 0:
        return np.zeros((max(0, y1-y0), max(0, x1-x0)), dtype=bool), (255, 255, 255)
    edge = np.concatenate((tile[0], tile[-1], tile[:, 0], tile[:, -1]), axis=0)
    bg = np.median(edge, axis=0)
    contrast = np.max(np.abs(tile - bg[None, None, :]), axis=2)
    return contrast >= threshold, tuple(int(round(x)) for x in bg)


def classify_char(ch: str):
    cp = ord(ch)
    name = unicodedata.name(ch, "UNKNOWN")
    cat = unicodedata.category(ch)
    if cat.startswith("Z") or ch.isspace():
        return "WHITESPACE", 0
    if (0x3400 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF) or "CJK" in name:
        return "CJK_FULL", 30
    if ch in ".,;:，。；：、…⋯":
        return "LOW_PROFILE_PUNCTUATION", 0
    if "MATHEMATICAL" in name or ch in "πΠαα→⇒=()+−-∶":
        return "MATH_BASE", 22
    if ch.isdigit() or (ch.isalpha() and ch.upper() == ch and ch.lower() != ch):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ch.isalpha():
        return "LATIN_OR_GREEK_LOWER", 17
    if cat.startswith("P"):
        return "LOW_PROFILE_PUNCTUATION", 0
    return "MATH_BASE", 22


def parent_for_char(cx, cy):
    if 456 <= cy < 474:
        return "T001_TITLE"
    if 476 <= cy < 503:
        return "T002_FORMULA_A" if cx < 292 else "T003_FORMULA_B"
    if 508 <= cy < 532:
        return "T004_MIN"
    if 535 <= cy < 565:
        return "T005_STATE_X" if cx < 292 else "T006_STATE_Y"
    if 565 <= cy < 580:
        return "T007_EQ_LINE_XY"
    if 580 <= cy < 596:
        return "T008_EQ_LINE_YX"
    if 596 <= cy < 614:
        return "T009_NOTE_LINE1"
    if 614 <= cy < 628:
        return "T010_NOTE_LINE2"
    if 628 <= cy < 660:
        return "T011_CAPTION"
    return None


TEXT_META = {
    "T001_TITLE": ("TEXT", "ANNOTATION", "CJK+PUNCT", "proposal-flow heading"),
    "T002_FORMULA_A": ("FORMULA", "PROPOSAL_FORMULA", "MATH", "a=pi(x)q(x,y)"),
    "T003_FORMULA_B": ("FORMULA", "PROPOSAL_FORMULA", "MATH", "b=pi(y)q(y,x)"),
    "T004_MIN": ("FORMULA", "CLIP_FORMULA", "MATH", "min(a,b)"),
    "T005_STATE_X": ("FORMULA", "STATE_LABEL", "MATH", "x"),
    "T006_STATE_Y": ("FORMULA", "STATE_LABEL", "MATH", "y"),
    "T007_EQ_LINE_XY": ("FORMULA", "ACCEPTED_FLOW_FORMULA", "MATH", "x-to-y accepted flow"),
    "T008_EQ_LINE_YX": ("FORMULA", "ACCEPTED_FLOW_FORMULA", "MATH", "y-to-x accepted flow"),
    "T009_NOTE_LINE1": ("TEXT", "CONCLUSION_NOTE", "CJK+MATH", "detailed-balance conclusion line 1"),
    "T010_NOTE_LINE2": ("TEXT", "CONCLUSION_NOTE", "CJK+MATH", "stationarity caveat line 2"),
    "T011_CAPTION": ("TEXT", "CAPTION", "CJK+MATH+LATIN", "Figure 32.4 caption natural paragraph"),
}


GRAPHIC_GROUPS = {
    "G001_MAINFLOW_XY": ([16, 17], "LINE_ARROW", "MAIN_ACCEPTED_FLOW", "x-to-y curved arrow; intentional endpoint contact"),
    "G002_MAINFLOW_YX": ([19, 20], "LINE_ARROW", "MAIN_ACCEPTED_FLOW", "y-to-x curved arrow; intentional endpoint contact"),
    "G003_STATE_X_BORDER": ([22], "NODE_BORDER", "STATE_BORDER", "x circular state border"),
    "G004_STATE_Y_BORDER": ([25], "NODE_BORDER", "STATE_BORDER", "y circular state border"),
    "G005_PROPOSAL_A_BOX": ([28], "NODE_BORDER", "PROPOSAL_BORDER", "proposal a rounded box"),
    "G006_PROPOSAL_B_BOX": ([31], "NODE_BORDER", "PROPOSAL_BORDER", "proposal b rounded box"),
    "G007_CLIP_BOX": ([34], "NODE_BORDER", "CLIP_BORDER", "min(a,b) rounded box"),
    "G008_THINFLOW_X_A": ([38, 39], "LINE_ARROW", "PROPOSAL_FLOW", "x-to-a connector; intentional endpoint contact"),
    "G009_THINFLOW_Y_B": ([41, 42], "LINE_ARROW", "PROPOSAL_FLOW", "y-to-b connector; intentional endpoint contact"),
    "G010_THINFLOW_A_M": ([44, 45], "LINE_ARROW", "PROPOSAL_FLOW", "a-to-min connector; intentional endpoint contact"),
    "G011_THINFLOW_B_M": ([47, 48], "LINE_ARROW", "PROPOSAL_FLOW", "b-to-min connector; intentional endpoint contact"),
    "G012_NOTE_BOX": ([51], "NODE_BORDER", "CONCLUSION_BORDER", "conclusion rounded box"),
}


DESIGN_CONTACT = {
    # The two accepted-flow arrows intentionally converge on the same east/west
    # state ports; their six antialiased shared pixels are a bidirectional-flow
    # topology cue, not an illegal crossing of unrelated objects.
    frozenset(("G001_MAINFLOW_XY", "G002_MAINFLOW_YX")),
    frozenset(("G001_MAINFLOW_XY", "G003_STATE_X_BORDER")),
    frozenset(("G001_MAINFLOW_XY", "G004_STATE_Y_BORDER")),
    frozenset(("G002_MAINFLOW_YX", "G003_STATE_X_BORDER")),
    frozenset(("G002_MAINFLOW_YX", "G004_STATE_Y_BORDER")),
    frozenset(("G008_THINFLOW_X_A", "G003_STATE_X_BORDER")),
    frozenset(("G008_THINFLOW_X_A", "G005_PROPOSAL_A_BOX")),
    frozenset(("G009_THINFLOW_Y_B", "G004_STATE_Y_BORDER")),
    frozenset(("G009_THINFLOW_Y_B", "G006_PROPOSAL_B_BOX")),
    frozenset(("G010_THINFLOW_A_M", "G005_PROPOSAL_A_BOX")),
    frozenset(("G010_THINFLOW_A_M", "G007_CLIP_BOX")),
    frozenset(("G011_THINFLOW_B_M", "G006_PROPOSAL_B_BOX")),
    frozenset(("G011_THINFLOW_B_M", "G007_CLIP_BOX")),
}


CONTAINER_PAIRS = {
    frozenset(("T002_FORMULA_A", "G005_PROPOSAL_A_BOX")),
    frozenset(("T003_FORMULA_B", "G006_PROPOSAL_B_BOX")),
    frozenset(("T004_MIN", "G007_CLIP_BOX")),
    frozenset(("T005_STATE_X", "G003_STATE_X_BORDER")),
    frozenset(("T006_STATE_Y", "G004_STATE_Y_BORDER")),
    frozenset(("T009_NOTE_LINE1", "G012_NOTE_BOX")),
    frozenset(("T010_NOTE_LINE2", "G012_NOTE_BOX")),
}


def replay_drawing(page_rect, drawing, stroke=True, fill=True):
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            shape.draw_line(item[1], item[2])
        elif kind == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif kind == "re":
            shape.draw_rect(item[1])
        elif kind == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing item kind: {kind}")
    use_stroke = stroke and drawing.get("color") is not None
    use_fill = fill and drawing.get("fill") is not None
    shape.finish(
        color=(0, 0, 0) if use_stroke else None,
        fill=(0, 0, 0) if use_fill else None,
        width=max(float(drawing.get("width") or 0.2), 0.2),
        lineCap=int((drawing.get("lineCap") or (0,))[0] if isinstance(drawing.get("lineCap"), tuple) else (drawing.get("lineCap") or 0)),
        lineJoin=int((drawing.get("lineJoin") or (0,))[0] if isinstance(drawing.get("lineJoin"), tuple) else (drawing.get("lineJoin") or 0)),
        closePath=bool(drawing.get("closePath")),
        even_odd=bool(drawing.get("even_odd")),
        stroke_opacity=1,
        fill_opacity=1,
    )
    shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    doc.close()
    return arr < 235


def pair_clearance(mask_a, mask_b):
    inter = int(np.count_nonzero(mask_a & mask_b))
    if inter:
        return inter, 0.0
    if not mask_a.any() or not mask_b.any():
        return inter, None
    ys_a, xs_a = np.where(mask_a)
    ys_b, xs_b = np.where(mask_b)
    x0 = max(0, min(xs_a.min(), xs_b.min()) - 3)
    y0 = max(0, min(ys_a.min(), ys_b.min()) - 3)
    x1 = min(mask_a.shape[1], max(xs_a.max(), xs_b.max()) + 4)
    y1 = min(mask_a.shape[0], max(ys_a.max(), ys_b.max()) + 4)
    a = mask_a[y0:y1, x0:x1]
    b = mask_b[y0:y1, x0:x1]
    d = distance_transform_edt(~a)
    center_distance = float(d[b].min())
    return 0, max(0.0, center_distance - 1.0)


def save_binary_mask(path: Path, mask: np.ndarray, box=None):
    if box is None:
        box = mask_bbox(mask)
    if box is None:
        Image.new("L", (1, 1), 255).save(path)
        return
    x0, y0, x1, y1 = box
    tile = np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    Image.fromarray(tile, mode="L").save(path)


def add_text(draw, xy, text, fill=(0, 0, 0)):
    draw.text(xy, text, fill=fill)


def make_glyph_contact_sheets(base: np.ndarray, glyphs: list[dict], masks: dict[str, np.ndarray]):
    sheets_dir = ROOT / "glyph_contact_sheets"
    nearest_dir = ROOT / "glyph_8x_nearest"
    safe_mkdir(sheets_dir)
    safe_mkdir(nearest_dir)
    per_sheet = 12
    cols, rows = 4, 3
    cell_w, cell_h = 650, 470
    for sidx in range(math.ceil(len(glyphs) / per_sheet)):
        chunk = glyphs[sidx*per_sheet:(sidx+1)*per_sheet]
        sheet = Image.new("RGB", (cols*cell_w, rows*cell_h), "white")
        sd = ImageDraw.Draw(sheet)
        for idx, g in enumerate(chunk):
            col, row = idx % cols, idx // cols
            ox, oy = col*cell_w, row*cell_h
            mask = masks[g["GLYPH_ID"]]
            bbox = mask_bbox(mask) or tuple(json.loads(g["BBOX_PX_JSON"]))
            roi = crop_pad(bbox, base.shape[1], base.shape[0], pad=4)
            x0,y0,x1,y1 = roi
            original = Image.fromarray(base[y0:y1, x0:x1])
            mm = mask[y0:y1, x0:x1]
            overlay_arr = np.array(original).copy()
            overlay_arr[mm] = (230, 0, 0)
            overlay = Image.fromarray(overlay_arr)
            only = Image.fromarray(np.where(mm, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            # Native 1x evidence is pasted without scaling; 8x is nearest-neighbour only.
            ch_repr = g["CHAR"] if g["CHAR"].isprintable() else f"U+{ord(g['CHAR']):04X}"
            add_text(sd, (ox+5, oy+2), f"{g['GLYPH_ID']} {ch_repr} U+{ord(g['CHAR']):04X} {g['PARENT_OBJECT_ID']}")
            panels = [("ORIG 1x", original), ("OVER 1x", overlay), ("MASK 1x", only)]
            px = ox + 5
            for label, im in panels:
                add_text(sd, (px, oy+22), label)
                sheet.paste(im, (px, oy+38))
                px += max(im.width, 55) + 8
            # The 8x panel is always exactly 8x nearest-neighbour, never capped or resampled again.
            tx0,ty0,tx1,ty1 = crop_pad(bbox, base.shape[1], base.shape[0], pad=2)
            tight_original = Image.fromarray(base[ty0:ty1,tx0:tx1])
            tight_mask = mask[ty0:ty1,tx0:tx1]
            tight_overlay_arr = np.array(tight_original).copy()
            tight_overlay_arr[tight_mask] = (230,0,0)
            nearest = Image.fromarray(tight_overlay_arr).resize(
                ((tx1-tx0)*8,(ty1-ty0)*8), Image.Resampling.NEAREST
            )
            add_text(sd, (ox+230, oy+22), "8x NEAREST (exact)")
            sheet.paste(nearest, (ox+230, oy+38))
            nearest.save(nearest_dir / f"{g['GLYPH_ID']}_8x_nearest.png")
            g["EVIDENCE_8X"] = f"glyph_8x_nearest/{g['GLYPH_ID']}_8x_nearest.png"
            g["CONTACT_SHEET"] = f"glyph_contact_sheets/contact_sheet_{sidx+1:02d}.png"
            g["CONTACT_CELL"] = f"r{row+1}c{col+1}"
        sheet.save(sheets_dir / f"contact_sheet_{sidx+1:02d}.png")


def make_object_overlay(base, objects):
    x0,y0,x1,y1 = FIGURE_CROP_PX
    img = Image.fromarray(base[y0:y1, x0:x1]).copy()
    draw = ImageDraw.Draw(img)
    colors = [(220,0,0),(0,100,220),(0,150,70),(190,90,0),(120,0,170)]
    for idx, obj in enumerate(objects):
        bx0,by0,bx1,by1 = json.loads(obj["BBOX_PX_JSON"])
        c=colors[idx%len(colors)]
        draw.rectangle((bx0-x0,by0-y0,bx1-x0,by1-y0), outline=c, width=2)
        draw.text((bx0-x0+2,by0-y0+2), obj["OBJECT_ID"], fill=c)
    img.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def make_critical_roi(base, row, mask_a, mask_b):
    outdir = ROOT / "critical_rois" / row["PAIR_ID"]
    safe_mkdir(outdir)
    ba = mask_bbox(mask_a)
    bb = mask_bbox(mask_b)
    union = rect_union((ba, bb))
    roi = crop_pad(union, base.shape[1], base.shape[0], pad=12)
    x0,y0,x1,y1 = (int(round(v)) for v in roi)
    raw = Image.fromarray(base[y0:y1,x0:x1])
    a = mask_a[y0:y1,x0:x1]
    b = mask_b[y0:y1,x0:x1]
    inter = a & b
    overlay = np.array(raw).copy()
    overlay[a] = (220,0,0)
    overlay[b] = (0,80,230)
    overlay[inter] = (220,0,220)
    raw.save(outdir / "raw_1x.png")
    Image.fromarray(np.where(a,0,255).astype(np.uint8),mode="L").save(outdir / "mask_A_1x.png")
    Image.fromarray(np.where(b,0,255).astype(np.uint8),mode="L").save(outdir / "mask_B_1x.png")
    Image.fromarray(np.where(inter,0,255).astype(np.uint8),mode="L").save(outdir / "intersection_1x.png")
    ov=Image.fromarray(overlay)
    ov.save(outdir / "overlay_1x.png")
    ov.resize((ov.width*8,ov.height*8),Image.Resampling.NEAREST).save(outdir / "overlay_8x_nearest.png")


def main():
    glyph_mask_dir = ROOT / "glyph_masks"
    object_mask_dir = ROOT / "object_masks"
    safe_mkdir(glyph_mask_dir)
    safe_mkdir(object_mask_dir)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
    base = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).copy()
    Image.fromarray(base).save(ROOT / "machine_native_full_page_300dpi.png")

    raw = page.get_text("rawdict")
    glyphs = []
    glyph_masks = {}
    parent_rects = defaultdict(list)
    parent_chars = defaultdict(list)
    gid = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    ch = char.get("c", "")
                    bbox_pt = tuple(map(float, char["bbox"]))
                    cx = (bbox_pt[0]+bbox_pt[2])/2
                    cy = (bbox_pt[1]+bbox_pt[3])/2
                    parent = parent_for_char(cx, cy)
                    if not parent or ch.isspace():
                        continue
                    gid += 1
                    glyph_id = f"GLY{gid:04d}"
                    bbox_px = pt_rect_to_px(bbox_pt)
                    x0,y0,x1,y1 = bbox_px
                    # Tighten to final-visible contrast while retaining the canonical char bbox.
                    local, bg = color_contrast_mask(base, bbox_px, threshold=20)
                    full = np.zeros((pix.height, pix.width), dtype=bool)
                    full[y0:y1,x0:x1] = local
                    tight = mask_bbox(full)
                    category, threshold = classify_char(ch)
                    h = 0 if tight is None else tight[3]-tight[1]
                    w = 0 if tight is None else tight[2]-tight[0]
                    area = int(full.sum())
                    advisory = "CALIBRATION_REQUIRED" if threshold == 0 else ("PASS" if h >= threshold else "FAIL")
                    font_name = span.get("font", "")
                    font_size = float(span.get("size", 0))
                    row = {
                        "GLYPH_ID": glyph_id,
                        "SAFE_FILENAME": f"{glyph_id}.png",
                        "PARENT_OBJECT_ID": parent,
                        "CHAR": ch,
                        "CODEPOINT": f"U+{ord(ch):04X}",
                        "UNICODE_NAME": unicodedata.name(ch, "UNKNOWN"),
                        "FONT": font_name,
                        "PDF_SPAN_SIZE_PT": f"{font_size:.4f}",
                        "BBOX_PT_JSON": json.dumps([round(x,4) for x in bbox_pt]),
                        "BBOX_PX_JSON": json.dumps(list(bbox_px)),
                        "TIGHT_MASK_BBOX_PX_JSON": json.dumps(list(tight) if tight else None),
                        "MASK_BG_RGB": json.dumps(list(bg)),
                        "MASK_AREA_PX": area,
                        "H_INK_PX": h,
                        "W_INK_PX": w,
                        "CATEGORY": category,
                        "LEGACY_PROTOCOL_THRESHOLD_PX": threshold if threshold else "N/A_CALIBRATION",
                        "LEGACY_PIXEL_MACHINE_STATUS": advisory,
                        "R168_HARD_FONT_SIGNAL": "NONE_MACHINE_OBSERVED" if area > 0 else "EMPTY_MASK",
                        "CONTACT_SHEET": "",
                        "CONTACT_CELL": "",
                    }
                    glyphs.append(row)
                    glyph_masks[glyph_id] = full
                    parent_rects[parent].append(bbox_pt)
                    parent_chars[parent].append(ch)
                    save_binary_mask(glyph_mask_dir / f"{glyph_id}.png", full, bbox_px)

    make_glyph_contact_sheets(base, glyphs, glyph_masks)
    write_csv(ROOT / "glyph_id_safe_filename_map.csv", ["GLYPH_ID","SAFE_FILENAME","PARENT_OBJECT_ID","CHAR","CODEPOINT"], glyphs)
    glyph_fields = list(glyphs[0].keys())
    write_csv(ROOT / "after_pixel_measurements.csv", glyph_fields, glyphs)

    # Semantic text objects are unions of all mapped glyph masks.
    object_masks = {}
    objects = []
    for oid, meta in TEXT_META.items():
        mask = np.zeros((pix.height,pix.width),dtype=bool)
        members=[g for g in glyphs if g["PARENT_OBJECT_ID"]==oid]
        for g in members:
            mask |= glyph_masks[g["GLYPH_ID"]]
        bbox=mask_bbox(mask)
        object_masks[oid]=mask
        typ,role,script,note=meta
        objects.append({
            "OBJECT_ID":oid,"SAFE_FILENAME":f"{oid}.png","OBJECT_CLASS":typ,"ROLE":role,"SCRIPT":script,
            "SEMANTIC_NOTE":note,"SOURCE_KIND":"PDF_TEXT_CHAR_UNION","SOURCE_SEQNOS":"",
            "MEMBER_COUNT":len(members),"BBOX_PX_JSON":json.dumps(list(bbox) if bbox else None),
            "MASK_AREA_PX":int(mask.sum()),"EMPTY_MASK":str(not mask.any()).upper(),
        })
        save_binary_mask(object_mask_dir/f"{oid}.png",mask,bbox)

    # Map every visible foreground drawing/path within the figure body.
    drawings=page.get_drawings(extended=True)
    by_seq={int(d["seqno"]):d for d in drawings if d.get("seqno") is not None}
    drawing_rows=[]
    seq_to_group={seq:oid for oid,(seqs,*_) in GRAPHIC_GROUPS.items() for seq in seqs}
    for seq in sorted(seq_to_group):
        d=by_seq[seq]
        r=d["rect"]
        drawing_rows.append({
            "DRAWING_SEQNO":seq,"PARENT_OBJECT_ID":seq_to_group[seq],"DRAW_TYPE":d.get("type"),
            "BBOX_PT_JSON":json.dumps([round(r.x0,4),round(r.y0,4),round(r.x1,4),round(r.y1,4)]),
            "STROKE_RGB01_JSON":json.dumps(d.get("color")),"FILL_RGB01_JSON":json.dumps(d.get("fill")),
            "WIDTH_PT":d.get("width"),"ITEM_KINDS":" ".join(it[0] for it in d.get("items",[])),
            "IS_MATH_RULE":"FALSE","MACHINE_MAPPING_STATUS":"ACCOUNTED",
        })
    write_csv(ROOT/"drawing_map_machine.csv",list(drawing_rows[0].keys()),drawing_rows)

    # Replay individual vector records; boxes contribute stroke only, arrowheads include fill.
    record_stroke={}
    record_fill={}
    for seq in sorted(seq_to_group):
        d=by_seq[seq]
        record_stroke[seq]=replay_drawing(page.rect,d,stroke=True,fill=False)
        record_fill[seq]=replay_drawing(page.rect,d,stroke=False,fill=True) if d.get("fill") is not None else np.zeros((pix.height,pix.width),bool)

    for oid,(seqs,objclass,role,note) in GRAPHIC_GROUPS.items():
        mask=np.zeros((pix.height,pix.width),bool)
        for seq in seqs:
            d=by_seq[seq]
            mask |= record_stroke[seq]
            # Filled arrowheads are foreground; filled nodes/boxes are background only.
            if objclass=="LINE_ARROW":
                mask |= record_fill[seq]
        # Background main arrows are finally occluded by later opaque state fills.
        if oid in {"G001_MAINFLOW_XY","G002_MAINFLOW_YX"}:
            mask &= ~(record_fill[22] | record_fill[25])
        bbox=mask_bbox(mask)
        object_masks[oid]=mask
        objects.append({
            "OBJECT_ID":oid,"SAFE_FILENAME":f"{oid}.png","OBJECT_CLASS":objclass,"ROLE":role,"SCRIPT":"N/A",
            "SEMANTIC_NOTE":note,"SOURCE_KIND":"PDF_DRAWING_REPLAY_FINAL_VISIBLE","SOURCE_SEQNOS":" ".join(map(str,seqs)),
            "MEMBER_COUNT":len(seqs),"BBOX_PX_JSON":json.dumps(list(bbox) if bbox else None),
            "MASK_AREA_PX":int(mask.sum()),"EMPTY_MASK":str(not mask.any()).upper(),
        })
        save_binary_mask(object_mask_dir/f"{oid}.png",mask,bbox)

    objects.sort(key=lambda r:r["OBJECT_ID"])
    write_csv(ROOT/"object_manifest_machine.csv",list(objects[0].keys()),objects)
    make_object_overlay(base,objects)

    pair_rows=[]
    critical=[]
    for pidx,(a,b) in enumerate(combinations(objects,2),1):
        aid,bid=a["OBJECT_ID"],b["OBJECT_ID"]
        inter,clearance=pair_clearance(object_masks[aid],object_masks[bid])
        fs=frozenset((aid,bid))
        if fs in DESIGN_CONTACT:
            relation="INTENTIONAL_GRAPHIC_CONNECTION"
            threshold="N/A_DESIGN_CONTACT"
            mstatus="DESIGN_CONTACT_REQUIRES_MANUAL_CONFIRMATION"
        elif fs in CONTAINER_PAIRS:
            relation="TEXT_TO_OWN_NODE_BORDER"
            threshold=5
            mstatus="PASS" if inter==0 and clearance is not None and clearance>=5 else "FAIL"
        elif a["OBJECT_CLASS"] in {"TEXT","FORMULA"} and b["OBJECT_CLASS"] in {"TEXT","FORMULA"}:
            relation="TEXT_TEXT_INDEPENDENT_PARENT"
            threshold=4
            mstatus="PASS" if inter==0 and clearance is not None and clearance>=4 else "FAIL"
        elif "TEXT" in a["OBJECT_CLASS"] or "FORMULA" in a["OBJECT_CLASS"] or "TEXT" in b["OBJECT_CLASS"] or "FORMULA" in b["OBJECT_CLASS"]:
            relation="TEXT_FORMULA_TO_GRAPHIC"
            threshold=3
            mstatus="PASS" if inter==0 and clearance is not None and clearance>=3 else "FAIL"
        else:
            relation="GRAPHIC_GRAPHIC_INDEPENDENT"
            threshold=0
            mstatus="PASS" if inter==0 else "FAIL"
        row={
            "PAIR_ID":f"PAIR{pidx:04d}","OBJECT_A":aid,"OBJECT_B":bid,"RELATION_CLASS":relation,
            "INTERSECTION_PX":inter,"CLEARANCE_PX":None if clearance is None else round(clearance,3),
            "HARD_THRESHOLD_PX":threshold,"MACHINE_STATUS":mstatus,
            "CRITICAL_MACHINE_FLAG":str(inter>0 or clearance is None or clearance<12).upper(),
        }
        pair_rows.append(row)
        if row["CRITICAL_MACHINE_FLAG"]=="TRUE":
            critical.append(row)
            make_critical_roi(base,row,object_masks[aid],object_masks[bid])
    write_csv(ROOT/"all_pairs_machine.csv",list(pair_rows[0].keys()),pair_rows)
    write_csv(ROOT/"critical_relations_machine.csv",list(pair_rows[0].keys()),critical)

    # Clip checks use semantic foreground masks only, not filled backgrounds.
    fx0,fy0,fx1,fy1=FIGURE_CROP_PX
    sx0,sy0,sx1,sy1=STANDALONE_CROP_PX
    clip_rows=[]
    for obj in objects:
        oid=obj["OBJECT_ID"]
        m=object_masks[oid]
        bbox=mask_bbox(m)
        if oid=="T011_CAPTION":
            crop=(fx0,fy0,fx1,fy1); crop_name="FIGURE_WITH_CAPTION"
        else:
            crop=(sx0,sy0,sx1,sy1); crop_name="STANDALONE_BODY"
        x0,y0,x1,y1=crop
        outside=int(m[:y0,:].sum()+m[y1:,:].sum()+m[y0:y1,:x0].sum()+m[y0:y1,x1:].sum())
        edge=int(m[y0:min(y0+1,m.shape[0]),x0:x1].sum()+m[max(y1-1,0):y1,x0:x1].sum()+m[y0:y1,x0:min(x0+1,m.shape[1])].sum()+m[y0:y1,max(x1-1,0):x1].sum())
        clip_rows.append({"OBJECT_ID":oid,"CROP":crop_name,"CROP_PX_JSON":json.dumps(list(crop)),"OUTSIDE_PIXEL_COUNT":outside,"EDGE_TOUCH_PIXEL_COUNT":edge,"MACHINE_CLIP_STATUS":"PASS" if outside==0 and edge==0 else "FAIL"})
    write_csv(ROOT/"clip_report_machine.csv",list(clip_rows[0].keys()),clip_rows)

    # Legacy source audit is factual; R168 adjudication is deliberately absent here.
    source_rows=[
        {"SOURCE_RULE_ID":"SRC01","SELECTOR":"slfig-FIG-P600-01","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"global figure font"},
        {"SOURCE_RULE_ID":"SRC02","SELECTOR":"state","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"state label font"},
        {"SOURCE_RULE_ID":"SRC03","SELECTOR":"proposal","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"proposal formula font"},
        {"SOURCE_RULE_ID":"SRC04","SELECTOR":"clipbox","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"clip formula font"},
        {"SOURCE_RULE_ID":"SRC05","SELECTOR":"heading node","DECLARED_PT":"8.6","LINE_SPACING_PT":"10.2","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"8.6","FACT":"heading annotation font"},
        {"SOURCE_RULE_ID":"SRC06","SELECTOR":"accepted-flow formula block","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"two-line formula block"},
        {"SOURCE_RULE_ID":"SRC07","SELECTOR":"conclusion node","DECLARED_PT":"9.2","LINE_SPACING_PT":"11.0","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"9.2","FACT":"conclusion note font"},
        {"SOURCE_RULE_ID":"SRC08","SELECTOR":"whole tikzpicture","DECLARED_PT":"N/A","LINE_SPACING_PT":"N/A","GRAPHICS_SCALE":"1.0","EFFECTIVE_PT":"N/A","FACT":"no resizebox/scalebox/transform shape/graphic scale"},
    ]
    write_csv(ROOT/"after_font_audit.csv",list(source_rows[0].keys()),source_rows)

    texttrace=page.get_texttrace()
    trace_in_figure=[t for t in texttrace if t.get("bbox") and t["bbox"][1] < 660 and t["bbox"][3] > 456]
    all_visible_drawings=[d for d in drawings if d.get("rect") and d["rect"].y0>=450 and d["rect"].y1<=630]
    summary={
        "handoff_id":"C-FIG-P600-01-R104-SA3-FRESH-ISOLATED-REPLACEMENT-V2",
        "uid":"FIG-P600-01","official_pdf":str(PDF),"physical_page":PHYSICAL_PAGE,"printed_page":638,"figure_number":"32.4",
        "page_pt":[page.rect.width,page.rect.height],"machine_renderer":"PyMuPDF 1.28.0","machine_dpi":DPI,
        "machine_native_grid_px":[pix.width,pix.height],"poppler_full_page_grid_px":[2481,3508],
        "figure_crop_px":list(FIGURE_CROP_PX),"standalone_crop_px":list(STANDALONE_CROP_PX),
        "text_parent_object_count":len(TEXT_META),"graphic_object_count":len(GRAPHIC_GROUPS),"total_object_count":len(objects),
        "expected_unordered_pair_count":len(objects)*(len(objects)-1)//2,"actual_unordered_pair_count":len(pair_rows),
        "drawing_record_count":len(drawing_rows),"visible_foreground_drawing_records_in_body":len(all_visible_drawings),
        "math_rule_count":0,"math_rule_basis":"No overline/underline/accent/radical/fraction/cancel rule appears in source or visible PDF drawing set.",
        "glyph_count":len(glyphs),"glyph_nonempty_mask_count":sum(int(g["MASK_AREA_PX"])>0 for g in glyphs),
        "contact_sheet_count":len({g["CONTACT_SHEET"] for g in glyphs}),
        "texttrace_span_count_in_figure_region":len(trace_in_figure),
        "empty_object_mask_count":sum(o["EMPTY_MASK"]=="TRUE" for o in objects),
        "machine_pair_fail_count":sum(r["MACHINE_STATUS"]=="FAIL" for r in pair_rows),
        "machine_design_contact_count":sum(r["MACHINE_STATUS"].startswith("DESIGN_CONTACT") for r in pair_rows),
        "critical_pair_count":len(critical),
        "clip_machine_fail_count":sum(r["MACHINE_CLIP_STATUS"]=="FAIL" for r in clip_rows),
        "manual_decision_files_generated_by_script":0,
    }
    (ROOT/"machine_crosscheck.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    doc.close()
    print(json.dumps(summary,ensure_ascii=True,indent=2))


if __name__ == "__main__":
    main()
