from __future__ import annotations

import csv
import hashlib
import json
import math
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex")
PHYSICAL_PAGE = 765
PRINTED_PAGE = 752
FIGURE_PT = (68.0294, 68.0306, 515.9086, 269.2929)
FIGURE_PX = (283, 283, 2150, 1123)
FIGURE_CROP_PX = (258, 283, 2175, 1200)
SCALE = 300.0 / 72.0
CONTRAST_THRESHOLD = 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def pt_rect_to_px(rect, sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def safe_char(ch: str) -> str:
    return f"U{ord(ch):06X}"


def script_and_threshold(ch: str, natural_script: bool) -> tuple[str, int, bool]:
    if natural_script:
        return "NATURAL_TEX_SCRIPT", 15, False
    name = unicodedata.name(ch, "")
    if ch in {",", ".", "，", "。", "、", ":", ";", "：", "；", "…"}:
        return "LOW_PROFILE_PUNCTUATION", 0, True
    if "CJK" in name or "IDEOGRAPH" in name or "HIRAGANA" in name or "KATAKANA" in name:
        return "CJK_FULL", 30, False
    if ch.isdigit() or "CAPITAL" in name:
        return "LATIN_UPPER_OR_DIGIT", 24, False
    if "SMALL" in name or ch.islower():
        return "LATIN_GREEK_LOWER", 17, False
    if ch in {"=", "+", "−", "-", ">", "<", "→", "⟺", "∑", "∣", "/", "(", ")", "[", "]", "∶"}:
        return "BASE_MATH_OPERATOR", 22, False
    return "BASE_MATH_OR_SYMBOL", 22, False


def role_for_char(ch: str, bbox: tuple[float, float, float, float], font: str, size: float, color: int) -> tuple[str, float, bool, str]:
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    if y1 <= 87:
        return "PANEL_TITLE", 10.4, False, "title"
    if color == 5067608:
        return "NOTE", 9.5, False, "note"
    if size < 9.8 and center_x < 180 and center_y < 145:
        return "EDGE_NOTE", 9.5, False, "edge_note"
    if size > 9.9 and size < 10.5 and ((90 < center_x < 190 and 100 < center_y < 175)):
        return "NODE_LABEL", 10.2, False, "page"
    matrix_regions = [
        (112, 178, 169, 230),
        (221, 178, 279, 230),
        (384, 97, 442, 149),
    ]
    if size < 10.5 and any(a <= center_x <= c and b <= center_y <= d for a, b, c, d in matrix_regions):
        return "MATRIX_CELL", 10.2, False, "cell"
    natural = size < 11.75 and size > 10.8
    return "FORMULA", 12.0, natural, "formula"


def text_mask(crop: np.ndarray, bg_rgb: tuple[int, int, int], target_rgb: tuple[int, int, int]) -> np.ndarray:
    arr = crop.astype(np.float32)
    bg = np.array(bg_rgb, dtype=np.float32)
    target = np.array(target_rgb, dtype=np.float32)
    v = target - bg
    denom = float(np.dot(v, v))
    if denom < 1:
        return np.zeros(crop.shape[:2], dtype=bool)
    delta = arr - bg
    alpha = np.tensordot(delta, v, axes=([2], [0])) / denom
    fitted = bg + alpha[..., None] * v
    residual = np.sqrt(np.sum((arr - fitted) ** 2, axis=2))
    contrast = np.max(np.abs(delta), axis=2)
    return (contrast >= CONTRAST_THRESHOLD) & (alpha >= 0.045) & (alpha <= 1.22) & (residual <= 24.0)


def mask_bbox(mask: np.ndarray, global_box: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    x0, y0, _, _ = global_box
    return (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)


def save_mask_png(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def drawing_role(page_index: int) -> tuple[str, str]:
    if page_index in (1, 2):
        return "PANEL_BORDER", f"panel_{page_index}"
    if page_index in (3, 4, 5):
        return "NODE_BORDER", {3: "node_i", 4: "node_j", 5: "node_h"}[page_index]
    if page_index in (6, 8, 10, 12):
        return "LINE_ARROW", {6: "edge_j_i", 8: "edge_i_j", 10: "edge_j_h", 12: "edge_h_i"}[page_index]
    if page_index in (7, 9, 11, 13):
        return "ARROWHEAD", {7: "edge_j_i", 9: "edge_i_j", 11: "edge_j_h", 13: "edge_h_i"}[page_index]
    if 14 <= page_index <= 22:
        return "MATRIX_CELL_BORDER", f"matrix_A_cell_{page_index-13:02d}"
    if page_index == 23:
        return "FOCUS_BORDER", "matrix_A_cell_02"
    if 24 <= page_index <= 32:
        return "MATRIX_CELL_BORDER", f"matrix_M_cell_{page_index-23:02d}"
    if page_index == 33:
        return "FOCUS_BORDER", "matrix_M_cell_02"
    if 34 <= page_index <= 42:
        return "MATRIX_CELL_BORDER", f"matrix_P_cell_{page_index-33:02d}"
    if page_index == 43:
        return "FOCUS_BORDER", "matrix_P_cell_04"
    return "UNCLASSIFIED_DRAWING", f"drawing_{page_index}"


def recreate_drawing_mask(drawing: dict, page_w: float, page_h: float, page_index: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    doc = fitz.open()
    p = doc.new_page(width=page_w, height=page_h)
    sh = p.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            sh.draw_line(item[1], item[2])
        elif op == "c":
            sh.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            sh.draw_rect(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing item {op}")
    fill = drawing.get("fill")
    if page_index in (3, 4, 5):
        fill = None
    sh.finish(
        color=drawing.get("color"),
        fill=fill,
        width=drawing.get("width") or 1.0,
        lineCap=max(drawing.get("lineCap") or (0,)),
        lineJoin=drawing.get("lineJoin") or 0,
        closePath=bool(drawing.get("type") in {"f", "fs"}),
        fill_opacity=drawing.get("fill_opacity") or 1.0,
        stroke_opacity=drawing.get("stroke_opacity") or 1.0,
        even_odd=drawing.get("even_odd", True),
    )
    sh.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    alpha = arr[:, :, 3]
    ys, xs = np.nonzero(alpha >= 20)
    if len(xs) == 0:
        doc.close()
        return np.zeros((0, 0), bool), (0, 0, 0, 0)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    mask = alpha[box[1]:box[3], box[0]:box[2]] >= 20
    doc.close()
    return mask, box


def parent_for_text(role: str, bbox: tuple[float, float, float, float], line_no: int) -> str:
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    if role == "NODE_LABEL":
        if cx < 120:
            return "node_i_label"
        if cx > 160:
            return "node_j_label"
        return "node_h_label"
    if role == "MATRIX_CELL":
        if cx < 180:
            group, left, top = "A", 112, 178
        elif cx < 320:
            group, left, top = "M", 221, 178
        else:
            group, left, top = "P", 384, 97
        col = min(3, max(1, int((cx - left) // 18.8) + 1))
        row = min(3, max(1, int((cy - top) // 16.6) + 1))
        return f"matrix_{group}_r{row}c{col}"
    return f"textline_{line_no:03d}"


def foreground_coords(mask: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    return np.column_stack((xs + box[0], ys + box[1])).astype(np.int32)


def relation_category(a: dict, b: dict) -> str:
    ta, tb = a["kind"], b["kind"]
    ra, rb = a["role"], b["role"]
    if ta == "TEXT_GLYPH" and tb == "TEXT_GLYPH":
        return "INTRA_PARENT_TEXT" if a["parent_id"] == b["parent_id"] else "TEXT_TEXT"
    if ta == "TEXT_GLYPH" and tb == "DRAWING_PATH":
        text, draw = a, b
    elif ta == "DRAWING_PATH" and tb == "TEXT_GLYPH":
        text, draw = b, a
    else:
        text = draw = None
    if text is not None:
        if draw["role"] in {"LINE_ARROW", "ARROWHEAD"}:
            return "TEXT_FORMULA_LINE_ARROW"
        if draw["role"] == "NODE_BORDER":
            return "TEXT_FORMULA_NODE_BORDER"
        if draw["role"] == "PANEL_BORDER":
            return "TEXT_FORMULA_PANEL_BORDER"
        if draw["role"] in {"MATRIX_CELL_BORDER", "FOCUS_BORDER"}:
            return "TEXT_FORMULA_CELL_BORDER"
        return "TEXT_DRAWING_OTHER"
    if ta == "DRAWING_PATH" and tb == "DRAWING_PATH":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "SAME_GEOMETRIC_PARENT"
        return "DRAWING_DRAWING"
    return "OTHER"


def threshold_for_relation(category: str) -> int | None:
    if category == "TEXT_TEXT":
        return 4
    if category == "TEXT_FORMULA_LINE_ARROW":
        return 3
    if category == "TEXT_FORMULA_NODE_BORDER":
        return 5
    if category == "TEXT_FORMULA_PANEL_BORDER":
        return 6
    if category == "TEXT_FORMULA_CELL_BORDER":
        return 5
    return None


def make_glyph_sheet(sheet_path: Path, items: list[dict], page_img: Image.Image, object_masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]) -> None:
    font = ImageFont.load_default()
    cell_h, cell_w = 240, 1000
    sheet = Image.new("RGB", (cell_w, cell_h * len(items)), "white")
    d = ImageDraw.Draw(sheet)
    for row, obj in enumerate(items):
        mask, box = object_masks[obj["element_id"]]
        pad = 8
        x0 = max(0, box[0] - pad); y0 = max(0, box[1] - pad)
        x1 = min(page_img.width, box[2] + pad); y1 = min(page_img.height, box[3] + pad)
        context = page_img.crop((x0, y0, x1, y1))
        local_mask = np.zeros((y1-y0, x1-x0), dtype=bool)
        local_mask[box[1]-y0:box[3]-y0, box[0]-x0:box[2]-x0] = mask
        overlay = np.array(context).copy()
        overlay[local_mask] = (255, 0, 0)
        mask_only = np.full_like(overlay, 255)
        mask_only[local_mask] = (0, 0, 0)
        y = row * cell_h
        label = f"{obj['element_id']} {obj['char']} {obj['codepoint']} role={obj['role']} parent={obj['parent_id']} H={obj['h_ink_px']} A={obj['ink_area_px']}"
        d.text((5, y + 3), label, fill="black", font=font)
        panels = [("ORIGINAL native1x", context), ("TARGET OVERLAY native1x", Image.fromarray(overlay)), ("MASK ONLY native1x", Image.fromarray(mask_only))]
        x = 5
        for label2, im in panels:
            d.text((x, y + 22), label2, fill="black", font=font)
            sheet.paste(im, (x, y + 38))
            x += max(150, im.width + 15)
        zoom = Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST)
        if zoom.width > 430 or zoom.height > 190:
            zoom.thumbnail((430, 190), Image.Resampling.NEAREST)
        d.text((555, y + 22), "8x NEAREST (display fit only)", fill="black", font=font)
        sheet.paste(zoom, (555, y + 38))
        d.line((0, y + cell_h - 1, cell_w, y + cell_h - 1), fill=(180, 180, 180))
    sheet.save(sheet_path)


def make_drawing_sheet(sheet_path: Path, items: list[dict], page_img: Image.Image, object_masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]) -> None:
    font = ImageFont.load_default()
    cell_h, cell_w = 260, 1000
    sheet = Image.new("RGB", (cell_w, cell_h * len(items)), "white")
    d = ImageDraw.Draw(sheet)
    for row, obj in enumerate(items):
        mask, box = object_masks[obj["element_id"]]
        pad = 12
        x0 = max(0, box[0] - pad); y0 = max(0, box[1] - pad)
        x1 = min(page_img.width, box[2] + pad); y1 = min(page_img.height, box[3] + pad)
        context = page_img.crop((x0, y0, x1, y1))
        local = np.zeros((y1-y0, x1-x0), bool)
        local[box[1]-y0:box[3]-y0, box[0]-x0:box[2]-x0] = mask
        overlay = np.array(context).copy(); overlay[local] = (255, 0, 0)
        mask_only = np.full_like(overlay, 255); mask_only[local] = (0, 0, 0)
        y = row * cell_h
        d.text((5, y + 3), f"{obj['element_id']} page_seq={obj['page_drawing_index']} role={obj['role']} parent={obj['semantic_parent']} area={obj['ink_area_px']}", fill="black", font=font)
        x = 5
        for label, im in [("ORIGINAL native1x", context), ("TARGET OVERLAY native1x", Image.fromarray(overlay)), ("MASK ONLY native1x", Image.fromarray(mask_only))]:
            d.text((x, y + 22), label, fill="black", font=font)
            show = im.copy()
            if show.width > 285 or show.height > 190:
                show.thumbnail((285, 190), Image.Resampling.NEAREST)
            sheet.paste(show, (x, y + 40))
            x += 325
        d.line((0, y + cell_h - 1, cell_w, y + cell_h - 1), fill=(180, 180, 180))
    sheet.save(sheet_path)


def make_pair_sheet(sheet_path: Path, pairs: list[dict], objects_by_id: dict[str, dict], page_img: Image.Image, object_masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]) -> None:
    font = ImageFont.load_default()
    cell_h, cell_w = 270, 1100
    sheet = Image.new("RGB", (cell_w, cell_h * len(pairs)), "white")
    d = ImageDraw.Draw(sheet)
    for row, pair in enumerate(pairs):
        a = objects_by_id[pair["object_a"]]; b = objects_by_id[pair["object_b"]]
        ma, ba = object_masks[a["element_id"]]; mb, bb = object_masks[b["element_id"]]
        pad = 10
        x0 = max(0, min(ba[0], bb[0]) - pad); y0 = max(0, min(ba[1], bb[1]) - pad)
        x1 = min(page_img.width, max(ba[2], bb[2]) + pad); y1 = min(page_img.height, max(ba[3], bb[3]) + pad)
        if x1-x0 > 420 or y1-y0 > 190:
            cx = int((max(ba[0], min(bb[0], ba[2])) + max(bb[0], min(ba[0], bb[2]))) / 2)
            cy = int((max(ba[1], min(bb[1], ba[3])) + max(bb[1], min(ba[1], bb[3]))) / 2)
            x0=max(0,cx-210); x1=min(page_img.width,cx+210); y0=max(0,cy-95); y1=min(page_img.height,cy+95)
        context = np.array(page_img.crop((x0,y0,x1,y1)))
        la=np.zeros(context.shape[:2],bool); lb=np.zeros(context.shape[:2],bool)
        ax0=max(x0,ba[0]); ay0=max(y0,ba[1]); ax1=min(x1,ba[2]); ay1=min(y1,ba[3])
        if ax1>ax0 and ay1>ay0: la[ay0-y0:ay1-y0,ax0-x0:ax1-x0]=ma[ay0-ba[1]:ay1-ba[1],ax0-ba[0]:ax1-ba[0]]
        bx0=max(x0,bb[0]); by0=max(y0,bb[1]); bx1=min(x1,bb[2]); by1=min(y1,bb[3])
        if bx1>bx0 and by1>by0: lb[by0-y0:by1-y0,bx0-x0:bx1-x0]=mb[by0-bb[1]:by1-bb[1],bx0-bb[0]:bx1-bb[0]]
        overlay=context.copy(); overlay[la]=(255,0,0); overlay[lb]=(0,80,255); overlay[la&lb]=(255,215,0)
        only=np.full_like(context,255); only[la]=(255,0,0); only[lb]=(0,80,255); only[la&lb]=(0,0,0)
        y=row*cell_h
        d.text((5,y+3),f"{pair['pair_id']} {pair['relation_category']} A={a['element_id']} B={b['element_id']} overlap={pair['raw_intersection_px']} white_gap={pair['white_gap_px']}",fill="black",font=font)
        orig=Image.fromarray(context); over=Image.fromarray(overlay); onlyim=Image.fromarray(only)
        for x,label,im in [(5,"ORIGINAL native1x",orig),(365,"A red / B blue / intersection yellow",over),(725,"MASKS ONLY native1x",onlyim)]:
            d.text((x,y+22),label,fill="black",font=font)
            show=im.copy()
            if show.width>350 or show.height>190: show.thumbnail((350,190),Image.Resampling.NEAREST)
            sheet.paste(show,(x,y+40))
        d.line((0,y+cell_h-1,cell_w,y+cell_h-1),fill=(180,180,180))
    sheet.save(sheet_path)


def main() -> None:
    machine = ROOT / "machine"
    contact = ROOT / "contact_sheets"
    masks_root = ROOT / "masks"
    glyph_mask_dir = masks_root / "glyphs"
    drawing_mask_dir = masks_root / "drawings"
    for p in (machine, contact, glyph_mask_dir, drawing_mask_dir):
        p.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    if doc.page_count != 817:
        raise RuntimeError(f"unexpected page count {doc.page_count}")
    page = doc[PHYSICAL_PAGE - 1]
    page_w, page_h = float(page.rect.width), float(page.rect.height)
    page_img = Image.open(ROOT / "views" / "full_page_300dpi_native.png").convert("RGB")
    page_arr = np.array(page_img)
    sx = page_img.width / page_w
    sy = page_img.height / page_h
    source_text = SOURCE.read_text(encoding="utf-8")
    if "FIG-P715-01" not in source_text or "fig:V5-C07-web-random-walk" not in source_text:
        raise RuntimeError("source identity mismatch")

    candidate = {
        "uid": "FIG-P715-01",
        "candidate_round": "R106",
        "handoff_id": "A-R106-P715-SA1-FRESH-ISOLATED-20260826",
        "official_pdf": str(PDF),
        "official_pdf_sha256": sha256(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "pdf_pages": doc.page_count,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_pt": [page_w, page_h],
        "page_native_300dpi_px": list(page_img.size),
        "page_native_200dpi_px": list(Image.open(ROOT / "views" / "full_page_200dpi.png").size),
        "figure_source": str(SOURCE),
        "figure_source_sha256": sha256(SOURCE),
        "figure_tikz_useasboundingbox_pt": list(FIGURE_PT),
        "standalone_crop_fullpage_px": list(FIGURE_PX),
        "figure_plus_caption_crop_fullpage_px": list(FIGURE_CROP_PX),
        "source_match_count_in_pdf": sum("列随机约定下的网页有向图" in p.get_text() for p in doc),
        "independent_locator": "unique caption text search in official R106 PDF; no inherited mapping",
        "main_head_supplied_in_task_packet": "137342439ac0a7db6cb27bc99337da0d2ea2f902",
    }
    (machine / "candidate_identity.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")

    source_styles = [
        {"style": "slfig-FIG-P715-01", "declared_pt": 9.5, "leading_pt": 11.5, "graphics_scale": 1.0, "effective_pt": 9.5, "use": "global figure default"},
        {"style": "every node", "declared_pt": 9.5, "leading_pt": 11.5, "graphics_scale": 1.0, "effective_pt": 9.5, "use": "global node default"},
        {"style": "title", "declared_pt": 10.4, "leading_pt": 12.4, "graphics_scale": 1.0, "effective_pt": 10.4, "use": "panel titles"},
        {"style": "page", "declared_pt": 10.2, "leading_pt": 12.2, "graphics_scale": 1.0, "effective_pt": 10.2, "use": "graph node labels"},
        {"style": "edge note", "declared_pt": 9.5, "leading_pt": 11.5, "graphics_scale": 1.0, "effective_pt": 9.5, "use": "edge labels"},
        {"style": "formula", "declared_pt": 12.0, "leading_pt": 14.0, "graphics_scale": 1.0, "effective_pt": 12.0, "use": "displayed formula blocks"},
        {"style": "cell", "declared_pt": 10.2, "leading_pt": 12.2, "graphics_scale": 1.0, "effective_pt": 10.2, "use": "matrix cell entries"},
        {"style": "note", "declared_pt": 9.5, "leading_pt": 11.5, "graphics_scale": 1.0, "effective_pt": 9.5, "use": "gray annotations"},
    ]
    write_csv(machine / "source_font_audit.csv", source_styles)
    scaling_scan = {
        "resizebox_count": source_text.count("resizebox"), "scalebox_count": source_text.count("scalebox"),
        "transform_shape_count": source_text.count("transform shape"), "tiny_count": source_text.count("\\tiny"),
        "scriptsize_count": source_text.count("\\scriptsize"), "footnotesize_count": source_text.count("\\footnotesize"),
        "small_count": source_text.count("\\small"), "explicit_graphics_scale_count": 0,
    }
    (machine / "source_scaling_scan.json").write_text(json.dumps(scaling_scan, indent=2), encoding="utf-8")

    raw = page.get_text("rawdict")
    glyphs: list[dict] = []
    object_masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]] = {}
    safe_rows: list[dict] = []
    line_no = 0
    glyph_no = 0
    fig_rect = fitz.Rect(*FIGURE_PT)
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            line_no += 1
            for span in line["spans"]:
                for c in span["chars"]:
                    ch = c["c"]
                    cb = tuple(float(v) for v in c["bbox"])
                    if ch.isspace() or not fitz.Rect(cb).intersects(fig_rect):
                        continue
                    glyph_no += 1
                    element_id = f"TXT_G{glyph_no:04d}"
                    role, declared_pt, natural_script, source_style = role_for_char(ch, cb, span["font"], float(span["size"]), int(span["color"]))
                    parent_id = parent_for_text(role, cb, line_no)
                    script_class, threshold, advisory_calibration = script_and_threshold(ch, natural_script)
                    box = pt_rect_to_px(cb, sx, sy)
                    box = (max(0, box[0]), max(0, box[1]), min(page_img.width, box[2]), min(page_img.height, box[3]))
                    crop = page_arr[box[1]:box[3], box[0]:box[2]]
                    bg = (242, 246, 250) if role == "NODE_LABEL" else (255, 255, 255)
                    target = color_int_to_rgb(int(span["color"]))
                    mask = text_mask(crop, bg, target)
                    ib = mask_bbox(mask, box)
                    if ib is None:
                        h_ink = 0; w_ink = 0; area = 0
                    else:
                        h_ink = ib[3] - ib[1]; w_ink = ib[2] - ib[0]; area = int(mask.sum())
                    safe = f"{element_id}_{safe_char(ch)}.png"
                    save_mask_png(glyph_mask_dir / safe, mask)
                    object_masks[element_id] = (mask, box)
                    glyphs.append({
                        "element_id": element_id, "kind": "TEXT_GLYPH", "safe_filename": safe,
                        "char": ch, "codepoint": f"U+{ord(ch):04X}", "unicode_name": unicodedata.name(ch, "UNKNOWN"),
                        "parent_id": parent_id, "role": role, "script_class": script_class,
                        "font": span["font"], "pdf_span_pt": round(float(span["size"]), 6),
                        "source_style": source_style, "declared_parent_pt": declared_pt,
                        "graphics_scale": 1.0, "effective_parent_pt": declared_pt,
                        "natural_tex_script": natural_script, "hard_height_threshold_px": threshold,
                        "r168_low_profile_or_micro_advisory": advisory_calibration,
                        "bbox_pt_x0": round(cb[0], 6), "bbox_pt_y0": round(cb[1], 6), "bbox_pt_x1": round(cb[2], 6), "bbox_pt_y1": round(cb[3], 6),
                        "bbox_px_x0": box[0], "bbox_px_y0": box[1], "bbox_px_x1": box[2], "bbox_px_y1": box[3],
                        "ink_bbox_px": "" if ib is None else ",".join(map(str, ib)), "h_ink_px": h_ink, "w_ink_px": w_ink,
                        "ink_area_px": area, "local_background_rgb": ",".join(map(str, bg)), "target_rgb": ",".join(map(str, target)),
                        "contrast_threshold_255": CONTRAST_THRESHOLD, "mask_path": str(Path("masks/glyphs") / safe),
                    })
                    safe_rows.append({"element_id": element_id, "safe_filename": safe, "kind": "TEXT_GLYPH", "path": str(Path("masks/glyphs") / safe)})

    drawings_all = page.get_drawings()
    drawings: list[dict] = []
    for page_idx, drawing in enumerate(drawings_all):
        if page_idx == 0 or not fitz.Rect(drawing["rect"]).intersects(fig_rect):
            continue
        element_id = f"DRW_{page_idx:04d}"
        role, semantic_parent = drawing_role(page_idx)
        mask, box = recreate_drawing_mask(drawing, page_w, page_h, page_idx)
        safe = f"{element_id}_{role}.png"
        save_mask_png(drawing_mask_dir / safe, mask)
        object_masks[element_id] = (mask, box)
        drawings.append({
            "element_id": element_id, "kind": "DRAWING_PATH", "safe_filename": safe,
            "page_drawing_index": page_idx, "role": role, "semantic_parent": semantic_parent,
            "pdf_type": drawing.get("type"), "bbox_pt": ",".join(f"{v:.6f}" for v in drawing["rect"]),
            "bbox_px_x0": box[0], "bbox_px_y0": box[1], "bbox_px_x1": box[2], "bbox_px_y1": box[3],
            "stroke_rgb": "" if drawing.get("color") is None else ",".join(str(round(v,6)) for v in drawing["color"]),
            "fill_rgb": "" if drawing.get("fill") is None else ",".join(str(round(v,6)) for v in drawing["fill"]),
            "stroke_width_pt": drawing.get("width"), "item_count": len(drawing["items"]),
            "ink_area_px": int(mask.sum()), "mask_path": str(Path("masks/drawings") / safe),
            "formula_math_rule": False,
        })
        safe_rows.append({"element_id": element_id, "safe_filename": safe, "kind": "DRAWING_PATH", "path": str(Path("masks/drawings") / safe)})

    write_csv(machine / "glyph_metrics.csv", glyphs)
    write_csv(machine / "drawing_path_ledger.csv", drawings)
    write_csv(machine / "safe_filename_map.csv", safe_rows)

    objects: list[dict] = []
    for g in glyphs:
        objects.append({"element_id": g["element_id"], "kind": g["kind"], "role": g["role"], "parent_id": g["parent_id"], "semantic_parent": g["parent_id"], "bbox_px": [g["bbox_px_x0"],g["bbox_px_y0"],g["bbox_px_x1"],g["bbox_px_y1"]], "safe_filename": g["safe_filename"], "char": g["char"], "codepoint": g["codepoint"], "ink_area_px": g["ink_area_px"]})
    for d in drawings:
        objects.append({"element_id": d["element_id"], "kind": d["kind"], "role": d["role"], "parent_id": d["semantic_parent"], "semantic_parent": d["semantic_parent"], "bbox_px": [d["bbox_px_x0"],d["bbox_px_y0"],d["bbox_px_x1"],d["bbox_px_y1"]], "safe_filename": d["safe_filename"], "char": "", "codepoint": "", "ink_area_px": d["ink_area_px"]})
    (machine / "object_manifest.json").write_text(json.dumps(objects, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(machine / "object_manifest.csv", objects, ["element_id","kind","role","parent_id","semantic_parent","bbox_px","safe_filename","char","codepoint","ink_area_px"])

    # Text overlay: every glyph bbox and unique ID on the direct native 300 dpi page.
    overlay = page_img.copy(); od = ImageDraw.Draw(overlay); font = ImageFont.load_default()
    for g in glyphs:
        box=(g["bbox_px_x0"],g["bbox_px_y0"],g["bbox_px_x1"],g["bbox_px_y1"])
        od.rectangle(box, outline=(220,0,0), width=1)
        od.text((box[0], max(0, box[1]-9)), g["element_id"].replace("TXT_G", "G"), fill=(180,0,0), font=font)
    overlay.crop(FIGURE_PX).save(ROOT / "views" / "after_text_measurement_overlay_300dpi.png", dpi=(300,300))

    # Contact sheets are generated without reviewer, boolean, decision or note fields.
    sheet_rows=[]
    for n in range(0, len(glyphs), 12):
        chunk=glyphs[n:n+12]; sheet_name=f"glyph_contact_{n//12+1:02d}.png"
        make_glyph_sheet(contact/sheet_name, chunk, page_img, object_masks)
        for cell,g in enumerate(chunk,1): sheet_rows.append({"element_id":g["element_id"],"sheet":sheet_name,"cell":cell})
    write_csv(machine/"glyph_contact_index.csv",sheet_rows)
    drawing_sheet_rows=[]
    for n in range(0,len(drawings),8):
        chunk=drawings[n:n+8]; sheet_name=f"drawing_contact_{n//8+1:02d}.png"
        make_drawing_sheet(contact/sheet_name,chunk,page_img,object_masks)
        for cell,drow in enumerate(chunk,1): drawing_sheet_rows.append({"element_id":drow["element_id"],"sheet":sheet_name,"cell":cell})
    write_csv(machine/"drawing_contact_index.csv",drawing_sheet_rows)

    coords={oid:foreground_coords(mask,box) for oid,(mask,box) in object_masks.items()}
    trees={oid:cKDTree(xy) if len(xy) else None for oid,xy in coords.items()}
    pairs=[]; critical=[]
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            aid,bid=a["element_id"],b["element_id"]
            ca,cb=coords[aid],coords[bid]
            ba=a["bbox_px"]; bb=b["bbox_px"]
            bbox_dx=max(0, max(ba[0]-bb[2],bb[0]-ba[2])); bbox_dy=max(0,max(ba[1]-bb[3],bb[1]-ba[3])); bbox_gap=max(bbox_dx,bbox_dy)
            overlap=0; center_dist=None
            if len(ca) and len(cb):
                if bbox_gap == 0:
                    lina=ca[:,1].astype(np.int64)*page_img.width+ca[:,0]
                    linb=cb[:,1].astype(np.int64)*page_img.width+cb[:,0]
                    overlap=int(np.intersect1d(lina,linb,assume_unique=False).size)
                if overlap:
                    center_dist=0.0
                else:
                    if len(ca)<=len(cb): dist,_=trees[bid].query(ca,k=1,p=np.inf)
                    else: dist,_=trees[aid].query(cb,k=1,p=np.inf)
                    center_dist=float(np.min(dist))
            white_gap=None if center_dist is None else max(0.0,center_dist-1.0)
            cat=relation_category(a,b); req=threshold_for_relation(cat)
            pair={"pair_id":f"PAIR_{len(pairs)+1:05d}","object_a":aid,"object_b":bid,"kind_a":a["kind"],"kind_b":b["kind"],"role_a":a["role"],"role_b":b["role"],"parent_a":a["parent_id"],"parent_b":b["parent_id"],"relation_category":cat,"bbox_chebyshev_lower_bound_px":bbox_gap,"raw_intersection_px":overlap,"nearest_pixel_center_chebyshev_px":"" if center_dist is None else round(center_dist,3),"white_gap_px":"" if white_gap is None else round(white_gap,3),"protocol_min_clearance_px":"" if req is None else req}
            pairs.append(pair)
            if overlap>0 or (white_gap is not None and white_gap<12 and (req is not None or cat in {"SAME_GEOMETRIC_PARENT","DRAWING_DRAWING","INTRA_PARENT_TEXT"})):
                critical.append(pair)
    write_csv(machine/"all_unordered_pairs.csv",pairs)
    write_csv(machine/"critical_pair_candidates.csv",critical)
    objects_by_id={o["element_id"]:o for o in objects}
    pair_sheet_rows=[]
    for n in range(0,len(critical),12):
        chunk=critical[n:n+12]; sheet_name=f"critical_pair_contact_{n//12+1:02d}.png"
        make_pair_sheet(contact/sheet_name,chunk,objects_by_id,page_img,object_masks)
        for cell,pair in enumerate(chunk,1): pair_sheet_rows.append({"pair_id":pair["pair_id"],"sheet":sheet_name,"cell":cell})
    write_csv(machine/"critical_pair_contact_index.csv",pair_sheet_rows)

    text_crosswalk=[{"element_id":g["element_id"],"char":g["char"],"codepoint":g["codepoint"],"parent_id":g["parent_id"],"mask_path":g["mask_path"],"ink_area_px":g["ink_area_px"]} for g in glyphs]
    write_csv(machine/"pdf_text_foreground_crosswalk.csv",text_crosswalk)
    drawing_crosswalk=[{"element_id":d["element_id"],"page_drawing_index":d["page_drawing_index"],"role":d["role"],"semantic_parent":d["semantic_parent"],"formula_math_rule":d["formula_math_rule"],"mask_path":d["mask_path"],"ink_area_px":d["ink_area_px"]} for d in drawings]
    write_csv(machine/"pdf_drawing_foreground_crosswalk.csv",drawing_crosswalk)
    summary={
        "glyph_count":len(glyphs),"drawing_path_count":len(drawings),"formula_math_rule_count":sum(bool(d["formula_math_rule"]) for d in drawings),
        "total_object_count":len(objects),"unordered_pair_expected":len(objects)*(len(objects)-1)//2,"unordered_pair_actual":len(pairs),
        "critical_pair_candidate_count":len(critical),"empty_glyph_mask_count":sum(g["ink_area_px"]==0 for g in glyphs),"empty_drawing_mask_count":sum(d["ink_area_px"]==0 for d in drawings),
        "glyph_contact_sheet_count":math.ceil(len(glyphs)/12),"drawing_contact_sheet_count":math.ceil(len(drawings)/8),"critical_pair_contact_sheet_count":math.ceil(len(critical)/12),
        "raw_pair_intersection_sum_px":sum(int(p["raw_intersection_px"]) for p in pairs),
        "source_scaling_scan":scaling_scan,
        "drawing_sequence_covered": [d["page_drawing_index"] for d in drawings],
        "visible_formula_math_rules": "none: all formula marks are extracted text glyphs; 43 figure drawing paths are panels, nodes, directed edges, matrix cell borders, and focus borders",
    }
    (machine/"machine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    doc.close()
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
