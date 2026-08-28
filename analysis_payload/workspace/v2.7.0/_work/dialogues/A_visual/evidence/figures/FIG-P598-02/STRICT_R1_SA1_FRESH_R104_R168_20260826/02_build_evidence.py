from __future__ import annotations

import csv
import itertools
import json
import math
import unicodedata
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mcmc_pipeline.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826")
PAGE_INDEX = 649
SCALE = 300.0 / 72.0

# Integer page-pixel crop coordinates, cut from the one native full-page render.
FIG_CROP = (471, 272, 2056, 807)
STAND_CROP = (294, 272, 2234, 940)

FG_DARK = (31, 35, 40)
FG_BLUE = (31, 78, 121)
FG_GRAY = (77, 81, 88)
FG_RULE = (184, 192, 200)
FG_GOLD = (183, 121, 31)
BG_CARD = (246, 247, 248)
BG_WHITE = (255, 255, 255)


def ensure_dirs() -> None:
    for rel in [
        "views",
        "machine",
        "masks/glyphs",
        "masks/graphics",
        "contact_sheets/glyphs",
        "contact_sheets/graphics",
        "overlays",
        "critical_relations/raw",
        "critical_relations/a_mask",
        "critical_relations/b_mask",
        "critical_relations/intersection",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def pt_rect_to_page_px(rect: list[float] | tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        math.floor(x0 * SCALE) - pad,
        math.floor(y0 * SCALE) - pad,
        math.ceil(x1 * SCALE) + pad,
        math.ceil(y1 * SCALE) + pad,
    )


def clip_box(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(size[0], x1), min(size[1], y1)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def color_line_mask(arr: np.ndarray, fg: tuple[int, int, int], backgrounds: list[tuple[int, int, int]], threshold: float = 20.0) -> np.ndarray:
    pix = arr.astype(np.float32)
    fg_v = np.asarray(fg, dtype=np.float32)
    union = np.zeros(arr.shape[:2], dtype=bool)
    for bg in backgrounds:
        bg_v = np.asarray(bg, dtype=np.float32)
        direction = fg_v - bg_v
        denom = float(np.dot(direction, direction))
        alpha = np.sum((pix - bg_v) * direction, axis=2) / denom
        projected = bg_v + alpha[..., None] * direction
        residual = np.linalg.norm(pix - projected, axis=2)
        contrast = np.max(np.abs(pix - bg_v), axis=2)
        union |= (alpha >= threshold / 255.0) & (alpha <= 1.08) & (residual <= 8.0) & (contrast >= threshold)
    return union


def line_fit_score(arr: np.ndarray, fg: tuple[int, int, int], backgrounds: list[tuple[int, int, int]], threshold: float = 20.0) -> np.ndarray:
    pix = arr.astype(np.float32)
    fg_v = np.asarray(fg, dtype=np.float32)
    best = np.full(arr.shape[:2], np.inf, dtype=np.float32)
    for bg in backgrounds:
        bg_v = np.asarray(bg, dtype=np.float32)
        direction = fg_v - bg_v
        denom = float(np.dot(direction, direction))
        alpha = np.sum((pix - bg_v) * direction, axis=2) / denom
        projected = bg_v + alpha[..., None] * direction
        residual = np.linalg.norm(pix - projected, axis=2)
        contrast = np.max(np.abs(pix - bg_v), axis=2)
        valid = (alpha >= threshold / 255.0) & (alpha <= 1.08) & (contrast >= threshold)
        best = np.minimum(best, np.where(valid, residual, np.inf))
    return best


def exclusive_color_mask(arr: np.ndarray, fg: tuple[int, int, int], backgrounds: list[tuple[int, int, int]], competitors: list[tuple[int, int, int]]) -> np.ndarray:
    target = line_fit_score(arr, fg, backgrounds)
    competing = np.full(arr.shape[:2], np.inf, dtype=np.float32)
    for comp in competitors:
        comp_bgs = [BG_CARD, BG_WHITE]
        competing = np.minimum(competing, line_fit_score(arr, comp, comp_bgs))
    return (target <= 8.0) & (target + 1.0 < competing)


def tight_local_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def parent_for(block: int, line: int) -> tuple[str, str, str]:
    mapping = {
        1: ("PANEL_1", "TITLE", "STEP1_TITLE"),
        2: ("PANEL_1", "FORMULA", "STEP1_STATIONARITY"),
        3: ("PANEL_1", "NODE_LABEL", "STEP1_KERNEL_NODES"),
        4: ("PANEL_1", "ANNOTATION", "STEP1_KEEP_TARGET"),
        5: ("PANEL_2", "TITLE", "STEP2_TITLE"),
        6: ("PANEL_2", "ANNOTATION", "STEP2_WARMUP" if line == 0 else "STEP2_RETAINED"),
        7: ("PANEL_3", "TITLE", "STEP3_TITLE"),
        8: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        9: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        10: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        11: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        12: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        13: ("PANEL_3", "FORMULA", "STEP3_ESTIMATOR"),
        14: ("PANEL_3", "ANNOTATION", "STEP3_RETAINED_ONLY"),
        15: ("CAPTION", "CAPTION", "CAPTION_PARAGRAPH"),
    }
    return mapping[block]


def glyph_class(char: str, size_pt: float, role: str) -> str:
    cp = ord(char)
    cat = unicodedata.category(char)
    if size_pt < 8.0 and role == "FORMULA":
        return "NATURAL_MATH_SCRIPT"
    if char in ",.-，。；：、":
        return "LOW_PROFILE_PUNCTUATION"
    if char in "=+−∑[]()":
        return "MATH_OPERATOR_DELIMITER"
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK_FULL"
    if char.isdigit() or (char.isalpha() and char.upper() == char and char.lower() != char):
        return "LATIN_UPPER_DIGIT"
    if cat.startswith("L"):
        return "LATIN_GREEK_LOWER"
    return "SYMBOL_OTHER"


def bg_for_bbox(box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    if cy < math.ceil(191 * SCALE) and any(a * SCALE <= cx <= b * SCALE for a, b in [(116, 224), (249, 358), (382, 491)]):
        return BG_CARD
    return BG_WHITE


def object_record(
    oid: str,
    safe: str,
    kind: str,
    panel: str,
    role: str,
    parent: str,
    page_box: tuple[int, int, int, int],
    mask: np.ndarray,
    mask_path: Path,
    extra: dict,
) -> dict:
    tight = tight_local_bbox(mask)
    x0, y0, x1, y1 = page_box
    if tight:
        tx0, ty0, tx1, ty1 = tight
        tight_page = [x0 + tx0, y0 + ty0, x0 + tx1, y0 + ty1]
        ink_height = ty1 - ty0
        ink_width = tx1 - tx0
    else:
        tight_page = None
        ink_height = 0
        ink_width = 0
    rec = {
        "element_id": oid,
        "safe_filename": safe,
        "kind": kind,
        "panel": panel,
        "role": role,
        "semantic_parent": parent,
        "bbox_page_px": list(page_box),
        "bbox_standalone_px": [x0 - STAND_CROP[0], y0 - STAND_CROP[1], x1 - STAND_CROP[0], y1 - STAND_CROP[1]],
        "tight_ink_bbox_page_px": tight_page,
        "mask_width_px": mask.shape[1],
        "mask_height_px": mask.shape[0],
        "ink_width_px": ink_width,
        "ink_height_px": ink_height,
        "ink_pixel_count": int(mask.sum()),
        "machine_empty_mask": not bool(mask.any()),
        "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
    }
    rec.update(extra)
    return rec


def build_glyphs(page: fitz.Page, full: Image.Image) -> list[dict]:
    raw = page.get_text("rawdict")
    objects: list[dict] = []
    seq = 0
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block_index not in range(1, 16) or block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line.get("spans", [])):
                for char_index, char in enumerate(span.get("chars", [])):
                    c = char.get("c", "")
                    if not c or c.isspace():
                        continue
                    bbox_pt = char.get("bbox")
                    if not bbox_pt or bbox_pt[1] < 65 or bbox_pt[1] >= 225:
                        continue
                    seq += 1
                    oid = f"GLYPH-B{block_index:02d}-L{line_index:02d}-S{span_index:02d}-C{char_index:03d}"
                    safe = f"glyph_{seq:03d}"
                    page_box = clip_box(pt_rect_to_page_px(bbox_pt), full.size)
                    roi = np.asarray(full.crop(page_box).convert("RGB"))
                    fg = rgb_from_int(int(span.get("color", 0)))
                    bg = bg_for_bbox(page_box)
                    mask = color_line_mask(roi, fg, [bg])
                    mask_path = ROOT / "masks" / "glyphs" / f"{safe}.png"
                    save_mask(mask_path, mask)
                    panel, role, parent = parent_for(block_index, line_index)
                    objects.append(
                        object_record(
                            oid,
                            safe,
                            "GLYPH",
                            panel,
                            role,
                            parent,
                            page_box,
                            mask,
                            mask_path,
                            {
                                "char": c,
                                "unicode": f"U+{ord(c):04X}",
                                "font": span.get("font"),
                                "size_pt_pdf": float(span.get("size", 0)),
                                "source_color_rgb": list(fg),
                                "background_rgb": list(bg),
                                "glyph_class": glyph_class(c, float(span.get("size", 0)), role),
                                "pdf_block": block_index,
                                "pdf_line": line_index,
                                "pdf_span": span_index,
                                "pdf_char": char_index,
                                "bbox_pt": [round(v, 5) for v in bbox_pt],
                            },
                        )
                    )
    return objects


def graphics_definitions() -> list[dict]:
    return [
        {"id":"GRAPHIC-G01","safe":"graphic_001_card1_border","panel":"PANEL_1","role":"CARD_BORDER","parent":"STEP1_CARD","rect":[116.05,68.15,224.10,190.38],"fg":FG_RULE,"bg":[BG_CARD,BG_WHITE],"source":"drawing_index=1"},
        {"id":"GRAPHIC-G02","safe":"graphic_002_card2_border","panel":"PANEL_2","role":"CARD_BORDER","parent":"STEP2_CARD","rect":[249.28,68.15,357.34,190.38],"fg":FG_RULE,"bg":[BG_CARD,BG_WHITE],"source":"drawing_index=2"},
        {"id":"GRAPHIC-G03","safe":"graphic_003_card3_border","panel":"PANEL_3","role":"CARD_BORDER","parent":"STEP3_CARD","rect":[382.51,68.15,490.57,190.38],"fg":FG_RULE,"bg":[BG_CARD,BG_WHITE],"source":"drawing_index=3"},
        {"id":"GRAPHIC-G04","safe":"graphic_004_node_x_border","panel":"PANEL_1","role":"NODE_BORDER","parent":"STEP1_NODE_X","rect":[140.1,117.7,157.55,135.15],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=4"},
        {"id":"GRAPHIC-G05","safe":"graphic_005_node_y_border","panel":"PANEL_1","role":"NODE_BORDER","parent":"STEP1_NODE_Y","rect":[182.6,117.7,200.08,135.15],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=5"},
        {"id":"GRAPHIC-G06","safe":"graphic_006_kernel_xy_shaft","panel":"PANEL_1","role":"KERNEL_ARROW_SHAFT","parent":"KERNEL_X_TO_Y","rect":[157.0,120.35,180.2,123.95],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=6"},
        {"id":"GRAPHIC-G07","safe":"graphic_007_kernel_xy_head","panel":"PANEL_1","role":"KERNEL_ARROWHEAD","parent":"KERNEL_X_TO_Y","rect":[178.7,121.25,182.1,123.75],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=7"},
        {"id":"GRAPHIC-G08","safe":"graphic_008_kernel_yx_shaft","panel":"PANEL_1","role":"KERNEL_ARROW_SHAFT","parent":"KERNEL_Y_TO_X","rect":[159.95,128.9,183.15,132.5],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=8"},
        {"id":"GRAPHIC-G09","safe":"graphic_009_kernel_yx_head","panel":"PANEL_1","role":"KERNEL_ARROWHEAD","parent":"KERNEL_Y_TO_X","rect":[158.0,129.1,161.45,131.6],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=9"},
        {"id":"GRAPHIC-G10","safe":"graphic_010_chain_baseline","panel":"PANEL_2","role":"BASELINE","parent":"STEP2_CHAIN","rect":[260.55,136.05,346.1,136.65],"fg":FG_RULE,"bg":[BG_CARD],"source":"drawing_index=10"},
        {"id":"GRAPHIC-G11","safe":"graphic_011_warmup_pattern","panel":"PANEL_2","role":"PATTERN","parent":"STEP2_WARMUP","rect":[260.55,113.45,293.65,149.9],"fg":FG_RULE,"bg":[BG_CARD],"source":"raster-visible TikZ pattern; PDF drawing clip indices=11/12"},
        {"id":"GRAPHIC-G12","safe":"graphic_012_chain_trace","panel":"PANEL_2","role":"DATA_CURVE","parent":"STEP2_CHAIN","rect":[262.8,113.4,340.4,136.65],"fg":FG_BLUE,"bg":[BG_CARD],"source":"drawing_index=13"},
        {"id":"GRAPHIC-G13","safe":"graphic_013_warmup_divider","panel":"PANEL_2","role":"DASHED_DIVIDER","parent":"STEP2_WARMUP_DIVIDER","rect":[294.45,110.55,295.15,149.95],"fg":FG_GOLD,"bg":[BG_CARD],"source":"drawing_index=14"},
        *[
            {"id":f"GRAPHIC-G{14+i:02d}","safe":f"graphic_{14+i:03d}_retained_dot_{i+1}","panel":"PANEL_3","role":"SAMPLE_DOT","parent":"STEP3_RETAINED_SAMPLES","rect":[x0-0.2,115.95,x1+0.2,118.78],"fg":FG_BLUE,"bg":[BG_CARD],"source":f"drawing_index={15+i}"}
            for i,(x0,x1) in enumerate([(402.74274,405.13379),(414.0813,416.47235),(425.42029,427.81134),(436.75882,439.14987),(448.09735,450.4884),(459.43634,461.82739),(470.7749,473.16595)])
        ],
        {"id":"GRAPHIC-G21","safe":"graphic_021_fraction_rule","panel":"PANEL_3","role":"MATH_RULE","parent":"STEP3_ESTIMATOR","rect":[422.82,139.82,429.32,140.35],"fg":FG_DARK,"bg":[BG_CARD],"source":"drawing_index=22; fraction rule"},
        {"id":"GRAPHIC-G22","safe":"graphic_022_flow1_shaft","panel":"CROSS_PANEL","role":"FLOW_ARROW_SHAFT","parent":"FLOW_1_TO_2","rect":[223.95,129.0,246.0,129.55],"fg":FG_BLUE,"bg":[BG_WHITE,BG_CARD],"source":"drawing_index=23"},
        {"id":"GRAPHIC-G23","safe":"graphic_023_flow1_head","panel":"CROSS_PANEL","role":"FLOW_ARROWHEAD","parent":"FLOW_1_TO_2","rect":[244.75,127.95,248.05,130.58],"fg":FG_BLUE,"bg":[BG_WHITE,BG_CARD],"source":"drawing_index=24"},
        {"id":"GRAPHIC-G24","safe":"graphic_024_flow2_shaft","panel":"CROSS_PANEL","role":"FLOW_ARROW_SHAFT","parent":"FLOW_2_TO_3","rect":[357.2,129.0,379.25,129.55],"fg":FG_BLUE,"bg":[BG_WHITE,BG_CARD],"source":"drawing_index=25"},
        {"id":"GRAPHIC-G25","safe":"graphic_025_flow2_head","panel":"CROSS_PANEL","role":"FLOW_ARROWHEAD","parent":"FLOW_2_TO_3","rect":[377.98,127.95,381.3,130.58],"fg":FG_BLUE,"bg":[BG_WHITE,BG_CARD],"source":"drawing_index=26"},
        {"id":"GRAPHIC-G26","safe":"graphic_026_widehat_accent","panel":"PANEL_3","role":"MATH_RULE","parent":"STEP3_ESTIMATOR","rect":[391.55,132.0,396.35,135.65],"fg":FG_DARK,"bg":[BG_CARD],"source":"visible widehat accent absent from raw text char denominator; raster recovered"},
    ]


def build_graphics(full: Image.Image) -> list[dict]:
    objects: list[dict] = []
    for d in graphics_definitions():
        page_box = clip_box(pt_rect_to_page_px(d["rect"]), full.size)
        roi = np.asarray(full.crop(page_box).convert("RGB"))
        competitors=[c for c in [FG_DARK,FG_BLUE,FG_GRAY,FG_RULE,FG_GOLD] if c != d["fg"]]
        graphic_bgs=list(dict.fromkeys(d["bg"] + ([FG_RULE] if d["fg"] in (FG_BLUE,FG_GOLD) else [])))
        mask = exclusive_color_mask(roi, d["fg"], graphic_bgs, competitors)
        if d["role"] == "CARD_BORDER":
            yy, xx = np.indices(mask.shape)
            edge = (xx < 8) | (xx >= mask.shape[1]-8) | (yy < 8) | (yy >= mask.shape[0]-8)
            mask &= edge
        if d["role"] == "NODE_BORDER":
            yy, xx = np.indices(mask.shape)
            cx, cy = (mask.shape[1]-1)/2.0, (mask.shape[0]-1)/2.0
            rx, ry = max(1.0,cx), max(1.0,cy)
            radius = np.sqrt(((xx-cx)/rx)**2 + ((yy-cy)/ry)**2)
            mask &= (radius >= 0.78) & (radius <= 1.08)
        if d["id"] == "GRAPHIC-G11":
            # The gray horizontal baseline occludes hatch strokes on the final page.
            baseline_y = int(round(136.35268 * SCALE)) - page_box[1]
            lo, hi = max(0, baseline_y - 2), min(mask.shape[0], baseline_y + 3)
            mask[lo:hi, :] = False
        mask_path = ROOT / "masks" / "graphics" / f"{d['safe']}.png"
        save_mask(mask_path, mask)
        objects.append(
            object_record(
                d["id"], d["safe"], "GRAPHIC", d["panel"], d["role"], d["parent"], page_box, mask, mask_path,
                {"source_mapping": d["source"], "source_color_rgb": list(d["fg"]), "bbox_pt": d["rect"]},
            )
        )
    return objects


def final_visible_ownership(objects: list[dict], page_size: tuple[int, int]) -> list[dict]:
    width = page_size[0]
    sets: dict[str, set[int]] = {}
    byid = {o["element_id"]: o for o in objects}
    for o in objects:
        mask = np.asarray(Image.open(ROOT / o["mask_path"]).convert("L")) > 0
        ys, xs = np.nonzero(mask); bx = o["bbox_page_px"]
        sets[o["element_id"]] = set(((ys + bx[1]) * width + (xs + bx[0])).astype(np.int64).tolist())

    design = {
        frozenset(("GRAPHIC-G04","GRAPHIC-G06")), frozenset(("GRAPHIC-G05","GRAPHIC-G08")),
        frozenset(("GRAPHIC-G06","GRAPHIC-G07")), frozenset(("GRAPHIC-G08","GRAPHIC-G09")),
        frozenset(("GRAPHIC-G10","GRAPHIC-G11")), frozenset(("GRAPHIC-G10","GRAPHIC-G12")),
        frozenset(("GRAPHIC-G11","GRAPHIC-G12")), frozenset(("GRAPHIC-G12","GRAPHIC-G13")),
        frozenset(("GRAPHIC-G22","GRAPHIC-G23")), frozenset(("GRAPHIC-G24","GRAPHIC-G25")),
    }
    ownership=[]
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            allowed = (a["kind"] == b["kind"] == "GLYPH" and a["semantic_parent"] == b["semantic_parent"])
            allowed |= (a["semantic_parent"] == b["semantic_parent"] and "MATH_RULE" in (a["role"], b["role"]))
            allowed |= frozenset((a["element_id"],b["element_id"])) in design
            if not allowed:
                continue
            inter = sets[a["element_id"]] & sets[b["element_id"]]
            if inter:
                # Later visible object owns shared final pixels; union coverage is unchanged.
                sets[a["element_id"]] -= inter
                ownership.append({"earlier_object":a["element_id"],"later_visible_owner":b["element_id"],"pre_occlusion_shared_px":len(inter),"rule":"later paint/order owns final-visible shared pixels"})

    for o in objects:
        bx=o["bbox_page_px"]; mask=np.zeros((bx[3]-bx[1],bx[2]-bx[0]),dtype=bool)
        for v in sets[o["element_id"]]:
            y,x=divmod(v,width); lx,ly=x-bx[0],y-bx[1]
            if 0 <= ly < mask.shape[0] and 0 <= lx < mask.shape[1]: mask[ly,lx]=True
        save_mask(ROOT/o["mask_path"],mask)
        tight=tight_local_bbox(mask)
        if tight:
            tx0,ty0,tx1,ty1=tight; o["tight_ink_bbox_page_px"]=[bx[0]+tx0,bx[1]+ty0,bx[0]+tx1,bx[1]+ty1]
            o["ink_width_px"]=tx1-tx0; o["ink_height_px"]=ty1-ty0
        else:
            o["tight_ink_bbox_page_px"]=None; o["ink_width_px"]=0; o["ink_height_px"]=0
        o["ink_pixel_count"]=int(mask.sum()); o["machine_empty_mask"]=not bool(mask.any())
    write_csv(ROOT/"machine"/"final_visible_ownership.csv",ownership)
    return ownership


def load_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\consola.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def object_roi(obj: dict, full: Image.Image, pad: int = 5) -> tuple[Image.Image, np.ndarray]:
    bx = obj["bbox_page_px"]
    padded = clip_box((bx[0]-pad, bx[1]-pad, bx[2]+pad, bx[3]+pad), full.size)
    original = full.crop(padded).convert("RGB")
    mask_local = np.asarray(Image.open(ROOT / obj["mask_path"]).convert("L")) > 0
    canvas = np.zeros((original.height, original.width), dtype=bool)
    ox, oy = bx[0]-padded[0], bx[1]-padded[1]
    canvas[oy:oy+mask_local.shape[0], ox:ox+mask_local.shape[1]] = mask_local
    return original, canvas


def triptych(original: Image.Image, mask: np.ndarray, scale8: bool) -> Image.Image:
    overlay = np.asarray(original).copy()
    overlay[mask] = np.array([235, 35, 45], dtype=np.uint8)
    overlay_im = Image.fromarray(overlay)
    mask_im = Image.fromarray(np.where(mask[..., None], 0, 255).astype(np.uint8).repeat(3, axis=2))
    imgs = [original, overlay_im, mask_im]
    if scale8:
        imgs = [im.resize((im.width*8, im.height*8), Image.Resampling.NEAREST) for im in imgs]
    gap = 8
    out = Image.new("RGB", (sum(im.width for im in imgs)+gap*2, max(im.height for im in imgs)), "white")
    x = 0
    for im in imgs:
        out.paste(im, (x, 0))
        x += im.width + gap
    return out


def contact_sheets(objects: list[dict], full: Image.Image, kind: str, per_sheet: int) -> list[str]:
    out_paths: list[str] = []
    font = load_font(20)
    small = load_font(16)
    for sheet_no, start in enumerate(range(0, len(objects), per_sheet), 1):
        subset = objects[start:start+per_sheet]
        cells: list[Image.Image] = []
        for obj in subset:
            original, mask = object_roi(obj, full, 5)
            one = triptych(original, mask, False)
            if kind == "glyphs":
                eight = triptych(original, mask, True)
            else:
                # Whole graphic stays native 1:1; the 8x strip uses a raw 24x24 anchor ROI.
                ys, xs = np.nonzero(mask)
                if len(xs):
                    pick = len(xs) // 2
                    cx, cy = int(xs[pick]), int(ys[pick])
                else:
                    cx, cy = original.width//2, original.height//2
                ax0, ay0 = max(0,cx-12), max(0,cy-12)
                ax1, ay1 = min(original.width,ax0+24), min(original.height,ay0+24)
                anchor = original.crop((ax0,ay0,ax1,ay1))
                anchor_mask = mask[ay0:ay1,ax0:ax1]
                eight = triptych(anchor, anchor_mask, True)
            cell_w = max(2050 if kind == "graphics" else 1750, one.width+30, eight.width+30)
            cell_h = 70 + one.height + 18 + eight.height + 20
            cell = Image.new("RGB", (cell_w, cell_h), "white")
            draw = ImageDraw.Draw(cell)
            label = f"{obj['element_id']} | {obj.get('char','')} | {obj['role']} | ink={obj['ink_height_px']}px area={obj['ink_pixel_count']}"
            draw.text((12,8), label, fill="black", font=font)
            draw.text((12,36), "1x ORIGINAL | TARGET OVERLAY | MASK ONLY", fill=(50,50,50), font=small)
            cell.paste(one, (12,62))
            y8 = 62 + one.height + 18
            draw.text((12,y8-18), "8x nearest-neighbour equivalent", fill=(50,50,50), font=small)
            cell.paste(eight, (12,y8))
            cells.append(cell)
        width = max(c.width for c in cells)
        height = sum(c.height for c in cells)
        sheet = Image.new("RGB", (width, height), "white")
        y = 0
        for c in cells:
            sheet.paste(c, (0,y))
            y += c.height
        rel = f"contact_sheets/{kind}/{kind[:-1]}_contact_sheet_{sheet_no:03d}.png"
        sheet.save(ROOT / rel)
        out_paths.append(rel)
    return out_paths


def global_index_set(obj: dict, width: int) -> set[int]:
    mask = np.asarray(Image.open(ROOT / obj["mask_path"]).convert("L")) > 0
    ys, xs = np.nonzero(mask)
    bx = obj["bbox_page_px"]
    gx = xs + bx[0] - STAND_CROP[0]
    gy = ys + bx[1] - STAND_CROP[1]
    keep = (gx >= 0) & (gy >= 0) & (gx < width) & (gy < STAND_CROP[3]-STAND_CROP[1])
    return set((gy[keep] * width + gx[keep]).astype(np.int64).tolist())


def bbox_clearance(a: list[int], b: list[int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0-ax1, ax0-bx1, 0)
    dy = max(by0-ay1, ay0-by1, 0)
    return math.hypot(dx, dy)


def exact_clearance(sa: set[int], sb: set[int], width: int) -> float | None:
    if not sa or not sb:
        return None
    if sa & sb:
        return 0.0
    aa = np.array([(v//width, v%width) for v in sa], dtype=np.float32)
    bb = np.array([(v//width, v%width) for v in sb], dtype=np.float32)
    if len(aa) <= len(bb):
        return float(cKDTree(bb).query(aa, k=1)[0].min())
    return float(cKDTree(aa).query(bb, k=1)[0].min())


def pair_gate(a: dict, b: dict) -> tuple[bool, float | None, str, bool]:
    intended = False
    if a["semantic_parent"] == b["semantic_parent"]:
        intended = True
    design_pairs = {
        frozenset(("GRAPHIC-G06","GRAPHIC-G07")), frozenset(("GRAPHIC-G08","GRAPHIC-G09")),
        frozenset(("GRAPHIC-G22","GRAPHIC-G23")), frozenset(("GRAPHIC-G24","GRAPHIC-G25")),
        frozenset(("GRAPHIC-G10","GRAPHIC-G12")), frozenset(("GRAPHIC-G10","GRAPHIC-G11")),
        frozenset(("GRAPHIC-G11","GRAPHIC-G12")), frozenset(("GRAPHIC-G12","GRAPHIC-G13")),
        frozenset(("GRAPHIC-G04","GRAPHIC-G06")), frozenset(("GRAPHIC-G05","GRAPHIC-G08")),
    }
    if frozenset((a["element_id"],b["element_id"])) in design_pairs:
        intended = True
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["semantic_parent"] == b["semantic_parent"]:
            return False, None, "same semantic text/formula parent", intended
        return True, 4.0, "independent text-text", intended
    if a["kind"] != b["kind"]:
        text = a if a["kind"] == "GLYPH" else b
        graph = b if a["kind"] == "GLYPH" else a
        if graph["role"] == "CARD_BORDER":
            return True, 5.0, "glyph-to-final-visible card border", intended
        if graph["role"] == "NODE_BORDER":
            return True, 5.0, "node label/other glyph-to-node border", intended
        if graph["role"] in {"KERNEL_ARROW_SHAFT","KERNEL_ARROWHEAD","BASELINE","PATTERN","DATA_CURVE","DASHED_DIVIDER","SAMPLE_DOT","FLOW_ARROW_SHAFT","FLOW_ARROWHEAD","MATH_RULE"}:
            if text["semantic_parent"] == graph["semantic_parent"] and graph["role"] == "MATH_RULE":
                return False, None, "designed math rule within same formula", True
            return True, 3.0, "glyph/formula-to-line/arrow/marker/rule", intended
    return False, None, "graphic-graphic or non-applicable", intended


def build_pairs(objects: list[dict]) -> tuple[list[dict], list[dict]]:
    width = STAND_CROP[2]-STAND_CROP[0]
    sets = {o["element_id"]: global_index_set(o,width) for o in objects}
    pairs: list[dict] = []
    critical: list[dict] = []
    for n,(a,b) in enumerate(itertools.combinations(objects,2),1):
        aid,bid=a["element_id"],b["element_id"]
        overlap=len(sets[aid] & sets[bid])
        bgap=bbox_clearance(a["bbox_page_px"],b["bbox_page_px"])
        applicable,threshold,klass,intended=pair_gate(a,b)
        need_exact = bgap < 16 or overlap > 0
        clearance=exact_clearance(sets[aid],sets[bid],width) if need_exact else None
        hard_fail=False
        if overlap > 0 and not intended:
            hard_fail=True
        if applicable and clearance is not None and clearance < float(threshold) and not intended:
            hard_fail=True
        decision="FAIL" if hard_fail else ("PASS" if applicable or overlap else "N/A")
        rec={
            "pair_id":f"PAIR-{n:05d}","a_id":aid,"b_id":bid,"a_kind":a["kind"],"b_kind":b["kind"],
            "a_role":a["role"],"b_role":b["role"],"a_parent":a["semantic_parent"],"b_parent":b["semantic_parent"],
            "relation_class":klass,"hard_gate_applicable":applicable,"threshold_px":threshold,
            "intended_design_relation":intended,"bbox_clearance_lower_bound_px":round(bgap,3),
            "exact_clearance_px":None if clearance is None else round(clearance,3),"overlap_pixel_count":overlap,
            "machine_decision":decision,
        }
        pairs.append(rec)
        if (applicable and (clearance is not None and clearance < 12)) or overlap > 0:
            critical.append(rec)
    return pairs,critical


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("",encoding="utf-8")
        return
    fieldnames=[]
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)


def draw_text_overlay(objects: list[dict], standalone: Image.Image) -> None:
    im=standalone.copy().convert("RGB")
    draw=ImageDraw.Draw(im)
    font=load_font(12)
    for i,o in enumerate(objects,1):
        x0,y0,x1,y1=o["bbox_standalone_px"]
        color=(220,30,40) if o["kind"]=="GLYPH" else (20,110,220)
        draw.rectangle((x0,y0,x1-1,y1-1),outline=color,width=1)
        draw.text((x0,max(0,y0-12)),str(i),fill=color,font=font)
    im.save(ROOT/"overlays"/"after_text_measurement_overlay_300dpi.png")


def pair_matrix(objects: list[dict], pairs: list[dict]) -> None:
    n=len(objects); cell=max(4,min(8,1200//n)); margin=220
    im=Image.new("RGB",(margin+n*cell+40,margin+n*cell+120),"white")
    draw=ImageDraw.Draw(im); font=load_font(16); tiny=load_font(11)
    index={o["element_id"]:i for i,o in enumerate(objects)}
    for i in range(n):
        draw.rectangle((margin+i*cell,margin+i*cell,margin+(i+1)*cell-1,margin+(i+1)*cell-1),fill=(30,30,30))
    for p in pairs:
        i=index[p["a_id"]]; j=index[p["b_id"]]
        if p["machine_decision"]=="FAIL": color=(220,30,40)
        elif p["overlap_pixel_count"]>0 and p["intended_design_relation"]: color=(40,90,210)
        elif p["hard_gate_applicable"] and p["exact_clearance_px"] is not None and p["exact_clearance_px"]<12: color=(238,165,40)
        else: color=(220,224,229)
        for a,b in [(i,j),(j,i)]: draw.rectangle((margin+b*cell,margin+a*cell,margin+(b+1)*cell-1,margin+(a+1)*cell-1),fill=color)
    draw.text((10,10),f"All unordered-pair matrix: N={n}, pairs={len(pairs)}",fill="black",font=font)
    legend=[("FAIL",(220,30,40)),("intended contact",(40,90,210)),("critical <12px",(238,165,40)),("other",(220,224,229))]
    y=40
    for label,color in legend:
        draw.rectangle((10,y,30,y+18),fill=color); draw.text((38,y),label,fill="black",font=tiny); y+=25
    draw.text((10,150),"Row/column numeric index maps to machine/object_index.csv",fill="black",font=tiny)
    im.save(ROOT/"overlays"/"all_unordered_pair_matrix.png")


def critical_relation_bundles(objects: list[dict], pairs: list[dict], full: Image.Image) -> list[str]:
    byid={o["element_id"]:o for o in objects}
    # Curated hard/semantic relations, independent of machine result.
    wanted=[
        ("GRAPHIC-G01","GLYPH-B01-L01-S00-C000"),("GRAPHIC-G01","GLYPH-B04-L00-S00-C000"),
        ("GRAPHIC-G04","GLYPH-B03-L00-S00-C000"),("GRAPHIC-G05","GLYPH-B03-L01-S00-C000"),
        ("GRAPHIC-G06","GLYPH-B02-L00-S00-C001"),("GRAPHIC-G08","GLYPH-B04-L00-S01-C000"),
        ("GRAPHIC-G02","GLYPH-B05-L01-S00-C000"),("GRAPHIC-G11","GLYPH-B06-L00-S00-C000"),
        ("GRAPHIC-G13","GLYPH-B06-L01-S00-C000"),("GRAPHIC-G12","GLYPH-B06-L01-S00-C000"),
        ("GRAPHIC-G03","GLYPH-B07-L01-S00-C000"),("GRAPHIC-G14","GLYPH-B08-L00-S00-C000"),
        ("GRAPHIC-G21","GLYPH-B08-L00-S04-C000"),("GRAPHIC-G26","GLYPH-B08-L00-S00-C000"),
        ("GRAPHIC-G03","GLYPH-B14-L00-S00-C000"),("GRAPHIC-G22","GRAPHIC-G01"),
        ("GRAPHIC-G23","GRAPHIC-G02"),("GRAPHIC-G24","GRAPHIC-G02"),("GRAPHIC-G25","GRAPHIC-G03"),
        ("GRAPHIC-G10","GRAPHIC-G12"),("GRAPHIC-G11","GRAPHIC-G12"),("GRAPHIC-G12","GRAPHIC-G13"),
    ]
    lookup={frozenset((p["a_id"],p["b_id"])):p for p in pairs}
    selected=[]
    for a,b in wanted:
        if a in byid and b in byid:
            selected.append(lookup[frozenset((a,b))])
    write_csv(ROOT/"machine"/"critical_relationships.csv",selected)
    font=load_font(17); small=load_font(14); paths=[]
    for sheet_no,start in enumerate(range(0,len(selected),6),1):
        rows=[]
        for p in selected[start:start+6]:
            a,b=byid[p["a_id"]],byid[p["b_id"]]
            ax=a["bbox_page_px"]; bx=b["bbox_page_px"]
            box=clip_box((min(ax[0],bx[0])-12,min(ax[1],bx[1])-12,max(ax[2],bx[2])+12,max(ax[3],bx[3])+12),full.size)
            raw=full.crop(box).convert("RGB")
            ma=np.zeros((raw.height,raw.width),bool); mb=ma.copy()
            for obj,target in [(a,ma),(b,mb)]:
                local=np.asarray(Image.open(ROOT/obj["mask_path"]).convert("L"))>0
                ob=obj["bbox_page_px"]; ox,oy=ob[0]-box[0],ob[1]-box[1]
                target[oy:oy+local.shape[0],ox:ox+local.shape[1]] |= local
            inter=ma&mb
            overlay=np.asarray(raw).copy(); overlay[ma]=np.array([230,35,45],np.uint8); overlay[mb]=np.array([30,110,230],np.uint8); overlay[inter]=np.array([190,0,190],np.uint8)
            maim=Image.fromarray(np.where(ma,0,255).astype(np.uint8)); mbim=Image.fromarray(np.where(mb,0,255).astype(np.uint8)); ii=Image.fromarray(np.where(inter,0,255).astype(np.uint8))
            safe=p["pair_id"].lower()
            raw.save(ROOT/"critical_relations"/"raw"/f"{safe}.png"); maim.save(ROOT/"critical_relations"/"a_mask"/f"{safe}.png"); mbim.save(ROOT/"critical_relations"/"b_mask"/f"{safe}.png"); ii.save(ROOT/"critical_relations"/"intersection"/f"{safe}.png")
            tri=[raw,Image.fromarray(overlay),Image.merge("RGB",(ii,ii,ii))]
            eight=[im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST) for im in tri]
            # Keep 8x raw equivalence bounded by using a native 48x48 center ROI.
            if max(raw.size)>48:
                cx,cy=raw.width//2,raw.height//2; crop=(max(0,cx-24),max(0,cy-24),min(raw.width,cx+24),min(raw.height,cy+24))
                tri8=[im.crop(crop).resize(((crop[2]-crop[0])*8,(crop[3]-crop[1])*8),Image.Resampling.NEAREST) for im in tri]
            else: tri8=eight
            gap=8; w=max(sum(i.width for i in tri)+2*gap,sum(i.width for i in tri8)+2*gap)+20; h=78+max(i.height for i in tri)+18+max(i.height for i in tri8)
            row=Image.new("RGB",(w,h),"white"); dr=ImageDraw.Draw(row)
            dr.text((8,5),f"{p['pair_id']} {p['a_id']} vs {p['b_id']}",fill="black",font=font)
            dr.text((8,30),f"overlap={p['overlap_pixel_count']} exact_clearance={p['exact_clearance_px']} threshold={p['threshold_px']} intended={p['intended_design_relation']}",fill="black",font=small)
            x=8
            for im in tri: row.paste(im,(x,58)); x+=im.width+gap
            y8=58+max(i.height for i in tri)+18; x=8
            for im in tri8: row.paste(im,(x,y8)); x+=im.width+gap
            rows.append(row)
        sheet=Image.new("RGB",(max(r.width for r in rows),sum(r.height for r in rows)),"white"); y=0
        for r in rows: sheet.paste(r,(0,y)); y+=r.height
        rel=f"overlays/critical_relationship_overlay_{sheet_no:03d}.png"; sheet.save(ROOT/rel); paths.append(rel)
    return paths


def semantic_overlays(figure: Image.Image, standalone: Image.Image) -> None:
    im=figure.copy().convert("RGB"); dr=ImageDraw.Draw(im); f=load_font(22); s=load_font(16)
    # Coordinates relative to FIG_CROP, all annotations outside central ink where practical.
    marks=[
        ((pt_rect_to_page_px([116.2,68.3,223.94,190.21])[0]-FIG_CROP[0],0),"STEP 1: kernel preserves pi; x/y bidirectional kernel"),
        ((pt_rect_to_page_px([249.45,68.3,357.17,190.21])[0]-FIG_CROP[0],30),"STEP 2: chain; hatched warm-up discarded; retained right"),
        ((pt_rect_to_page_px([382.68,68.3,490.40,190.21])[0]-FIG_CROP[0],60),"STEP 3: retained dots -> ergodic average"),
    ]
    for (x,y),label in marks:
        dr.rectangle((x+2,y+2,min(im.width-2,x+430),y+28),fill=(255,255,220),outline=(180,120,20),width=2)
        dr.text((x+6,y+5),label,fill=(70,50,10),font=s)
    im.save(ROOT/"overlays"/"semantic_geometry_overlay.png")

    page=standalone.copy().convert("RGB"); d=ImageDraw.Draw(page); d.rectangle((2,2,page.width-3,page.height-3),outline=(35,140,70),width=3)
    d.text((10,page.height-32),"Caption confirms E_pi[h(X)]; crop/page integration boundary shown in green",fill=(20,100,55),font=f)
    page.save(ROOT/"overlays"/"page_integration_relationship_overlay.png")


def main() -> None:
    ensure_dirs()
    doc=fitz.open(PDF); page=doc[PAGE_INDEX]
    full=Image.open(ROOT/"views"/"full_page_300dpi.png").convert("RGB")
    figure=full.crop(FIG_CROP); standalone=full.crop(STAND_CROP)
    figure.save(ROOT/"views"/"figure_crop_300dpi.png")
    standalone.save(ROOT/"views"/"standalone_300dpi.png")
    gray_full=Image.frombytes("L",(full.width,full.height),page.get_pixmap(dpi=300,colorspace=fitz.csGRAY,alpha=False).samples)
    gray_full.crop(STAND_CROP).save(ROOT/"views"/"grayscale_300dpi.png")

    glyphs=build_glyphs(page,full); graphics=build_graphics(full); objects=glyphs+graphics
    ownership=final_visible_ownership(objects,full.size)
    pairs,critical=build_pairs(objects)

    write_csv(ROOT/"machine"/"object_ledger.csv",objects)
    write_csv(ROOT/"machine"/"glyph_ledger.csv",glyphs)
    write_csv(ROOT/"machine"/"graphic_ledger.csv",graphics)
    write_csv(ROOT/"machine"/"all_unordered_pairs.csv",pairs)
    (ROOT/"machine"/"object_ledger.json").write_text(json.dumps(objects,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"machine"/"all_unordered_pairs.json").write_text(json.dumps(pairs,ensure_ascii=False,indent=2),encoding="utf-8")
    index_rows=[{"object_index":i+1,"element_id":o["element_id"],"safe_filename":o["safe_filename"],"kind":o["kind"]} for i,o in enumerate(objects)]
    write_csv(ROOT/"machine"/"object_index.csv",index_rows)

    glyph_sheets=contact_sheets(glyphs,full,"glyphs",12)
    graphic_sheets=contact_sheets(graphics,full,"graphics",4)
    critical_overlays=critical_relation_bundles(objects,pairs,full)
    draw_text_overlay(objects,standalone); pair_matrix(objects,pairs); semantic_overlays(figure,standalone)

    # Machine-only facts; no reviewer, boolean adjudication, decision, or note fields.
    source_inventory={
        "source":str(SOURCE),"global_style_pt":9.2,"every_node_pt":9.2,"title_pt":9.4,"annotation_pt":8.6,
        "main_formula_pt":9.2,"natural_math_script_pdf_pt":6.4159,"r168_policy":"fine ratios/min-readable thresholds advisory; hard font fail only enumerated R168 defects",
    }
    (ROOT/"machine"/"source_font_inventory.json").write_text(json.dumps(source_inventory,ensure_ascii=False,indent=2),encoding="utf-8")
    summary={
        "figure_uid":"FIG-P598-02","round":"R104","physical_page":650,"page_pt":[page.rect.width,page.rect.height],
        "full_page_300dpi_px":list(full.size),"full_page_200dpi_px":list(Image.open(ROOT/"views"/"full_page_200dpi.png").size),
        "figure_crop_page_px":list(FIG_CROP),"figure_crop_native_px":list(figure.size),
        "standalone_crop_page_px":list(STAND_CROP),"standalone_native_px":list(standalone.size),
        "visible_glyph_count":len(glyphs),"visible_graphic_count":len(graphics),"total_object_count":len(objects),
        "unordered_pair_expected":len(objects)*(len(objects)-1)//2,"unordered_pair_actual":len(pairs),
        "empty_mask_count":sum(o["machine_empty_mask"] for o in objects),
        "machine_pair_fail_count":sum(p["machine_decision"]=="FAIL" for p in pairs),
        "overlap_nonintended_pair_count":sum(p["overlap_pixel_count"]>0 and not p["intended_design_relation"] for p in pairs),
        "critical_machine_pair_count":len(critical),"glyph_contact_sheets":glyph_sheets,"graphic_contact_sheets":graphic_sheets,
        "pre_occlusion_design_shared_relation_count":len(ownership),"pre_occlusion_design_shared_pixel_count":sum(x["pre_occlusion_shared_px"] for x in ownership),
        "critical_relationship_overlays":critical_overlays,
        "drawing_bidirectional_accounting":{"page_drawing_count":30,"figure_native_drawings_mapped":[1,2,3,4,5,6,7,8,9,10,13,14,15,16,17,18,19,20,21,22,23,24,25,26],"clip_or_pattern_control_entries_explained":[11,12],"outside_figure_entries_excluded":[0,27,28,29],"raster_or_source_visible_additions":["GRAPHIC-G11 warm-up pattern","GRAPHIC-G26 widehat accent"]},
    }
    (ROOT/"machine"/"machine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
